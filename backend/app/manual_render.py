"""Render a manually collected sample's ``page.mhtml`` into safe, servable HTML.

Kept independent from the phishdecloaker kit100 serving path in
``backend/app/main.py``'s ``proxy_get`` (which forwards to a live upstream
container instead). Every subresource (CSS, images, fonts) is inlined as a
data URI, and the page is made fully inert so it can be served directly with
no sandbox: original scripts and inline event handlers are removed, and form
submissions / links are neutralized so nothing can reach the original site.
A small PhishGate-owned offline runtime restores only structural overlay
dismissal; no original site code is executed.
"""

import base64
import os
import re
from email import message_from_bytes
from email.policy import default
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup


DEFAULT_SAMPLES_DIR = "/app/data/manual/samples"

_SAFE_OVERLAY_RUNTIME = r"""
(() => {
  const controlSelector = [
    "button",
    "[role='button']",
    "input[type='button']",
    "input[type='submit']",
    "a[href='#']",
  ].join(",");
  const overlaySelector = [
    "dialog",
    "[role='dialog']",
    "[aria-modal='true']",
    "[id*='cookie' i]",
    "[class*='cookie' i]",
    "[id*='consent' i]",
    "[class*='consent' i]",
    "[id*='modal' i]",
    "[class*='modal' i]",
    "[id*='overlay' i]",
    "[class*='overlay' i]",
    "[id*='popup' i]",
    "[class*='popup' i]",
  ].join(",");
  const dismissIntent = /(?:^|[\s_-])(accept|agree|allow(?:\s+all)?|reject|decline|close|dismiss|continue(?:\s+without)?|got(?:\s+it)?|save(?:\s+preferences)?|confirm(?:\s+choices)?)(?:$|[\s_-])/i;

  // Frozen G2/G3 samples must never navigate, open a tab, download a file,
  // or invoke an external protocol. Overlay dismissal below still works
  // because preventing the browser default does not stop event propagation.
  document.addEventListener("click", (event) => {
    if (event.target instanceof Element && event.target.closest("a")) {
      event.preventDefault();
    }
  }, true);

  function describe(control) {
    return [
      control.id,
      control.className,
      control.getAttribute("aria-label"),
      control.getAttribute("title"),
      control.getAttribute("value"),
      control.textContent,
    ].filter(Boolean).join(" ").replace(/\s+/g, " ").trim();
  }

  function hideOverlay(overlay) {
    if (overlay instanceof HTMLDialogElement && overlay.open) {
      overlay.close();
    }
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
    overlay.style.setProperty("display", "none", "important");

    document.querySelectorAll(".modal-backdrop, [class*='backdrop' i]").forEach((backdrop) => {
      if (getComputedStyle(backdrop).position === "fixed") {
        backdrop.hidden = true;
        backdrop.style.setProperty("display", "none", "important");
      }
    });
    document.documentElement.style.removeProperty("overflow");
    document.body?.style.removeProperty("overflow");
    document.body?.classList.remove("modal-open", "no-scroll", "overflow-hidden");
  }

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const control = event.target.closest(controlSelector);
    if (!control) return;

    const hasDismissAttribute = control.hasAttribute("data-dismiss")
      || control.hasAttribute("data-bs-dismiss");
    if (!hasDismissAttribute && !dismissIntent.test(describe(control))) return;

    const controlledId = control.getAttribute("aria-controls");
    const controlled = controlledId ? document.getElementById(controlledId) : null;
    let overlay = controlled?.matches(overlaySelector) ? controlled : null;
    if (!overlay) {
      let ancestor = control.parentElement;
      while (ancestor && ancestor !== document.body && ancestor !== document.documentElement) {
        if (ancestor.matches(overlaySelector)) overlay = ancestor;
        ancestor = ancestor.parentElement;
      }
    }
    if (!overlay) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    hideOverlay(overlay);
  }, true);
})();
"""


def _samples_dir() -> Path:
    return Path(os.environ.get("PHISHGATE_MANUAL_SAMPLES", DEFAULT_SAMPLES_DIR))


def _data_uri(ctype: str, raw: bytes) -> str:
    return f"data:{ctype};base64,{base64.b64encode(raw).decode()}"


def _inline_css_urls(css: str, base: str, by_loc: dict) -> str:
    # A frozen snapshot must never resolve a stylesheet import at runtime.
    css = re.sub(r"@import\s+(?:url\()?[^;]+;", "", css, flags=re.IGNORECASE)

    def repl(match: re.Match) -> str:
        ref = match.group(1).strip().strip("'\"")
        if ref.startswith("data:"):
            return match.group(0)
        # Empty CSS URLs resolve to the stylesheet itself. Inlining that match
        # embeds the complete stylesheet once per empty url() and can turn a
        # small snapshot into a response hundreds of MiB large. Fragment-only
        # references are already local to the frozen document and need no
        # resource lookup either.
        if not ref:
            return 'url("")'
        if ref.startswith("#"):
            return match.group(0)
        part = by_loc.get(urljoin(base or "", ref))
        return f"url({_data_uri(part['ctype'], part['data'])})" if part else 'url("")'

    return re.sub(r"url\(([^)]*)\)", repl, css)


def _inject_safe_overlay_dismissal(soup: BeautifulSoup) -> None:
    """Add the trusted offline runtime after all original scripts are removed."""
    runtime = soup.new_tag("script")
    runtime["data-phishgate-runtime"] = "safe-overlay-dismissal-v1"
    runtime.string = _SAFE_OVERLAY_RUNTIME
    (soup.body or soup).append(runtime)


def _mhtml_to_html(data: bytes) -> str:
    msg = message_from_bytes(data, policy=default)
    parts: list[dict] = []
    for part in (msg.iter_parts() if msg.is_multipart() else [msg]):
        if part.is_multipart():
            continue
        parts.append(
            {
                "loc": part.get("Content-Location"),
                "ctype": part.get_content_type(),
                "data": part.get_payload(decode=True) or b"",
                "cs": part.get_content_charset(),
            }
        )

    main_loc = msg.get("Snapshot-Content-Location")
    by_loc = {part["loc"]: part for part in parts if part["loc"]}
    main = next((part for part in parts if part["loc"] == main_loc), None) or next(
        (part for part in parts if part["ctype"] == "text/html"), None
    )
    if main is None:
        return "<p>could not find an HTML part in this mhtml</p>"

    css_data_uris = {
        part["loc"]: _data_uri(
            "text/css",
            _inline_css_urls(part["data"].decode("utf-8", "replace"), part["loc"], by_loc).encode("utf-8"),
        )
        for part in parts
        if part["ctype"] == "text/css"
    }

    base = main["loc"] or main_loc or ""
    soup = BeautifulSoup(main["data"].decode(main["cs"] or "utf-8", "replace"), "html.parser")

    # Drop executable / navigational elements.
    for tag in soup.find_all(["script", "base"]):
        tag.decompose()
    for tag in soup.find_all("meta"):
        http_equiv = (tag.get("http-equiv") or "").lower()
        if http_equiv in ("refresh", "content-security-policy"):
            tag.decompose()

    # Inline resources; strip inline event handlers.
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith("on"):
                del tag[attr]
        # The browser may prefer an unresolved srcset candidate over the
        # inlined src. Removing it prevents a frozen sample from reaching the
        # original host while preserving the captured src resource below.
        tag.attrs.pop("srcset", None)
        if tag.has_attr("style"):
            tag["style"] = _inline_css_urls(tag["style"], base, by_loc)
        for attr in ("src", "href", "poster"):
            if not tag.has_attr(attr):
                continue
            ref = tag[attr]
            if ref.startswith(("data:", "#")):
                continue
            if ref.startswith("javascript:"):
                tag[attr] = "#"
                continue
            absolute = urljoin(base, ref)
            if absolute in css_data_uris:
                tag[attr] = css_data_uris[absolute]
            elif absolute in by_loc:
                part = by_loc[absolute]
                tag[attr] = css_data_uris.get(absolute) or _data_uri(part["ctype"], part["data"])
            elif tag.name != "a":
                # Anchors are neutralized separately while retaining their
                # original destination as inert feature data. Every other
                # unresolved resource reference must be removed.
                del tag[attr]

        if tag.name == "object":
            tag.attrs.pop("data", None)

    for style_tag in soup.find_all("style"):
        style_tag.string = _inline_css_urls(style_tag.get_text(), base, by_loc)

    # Make it inert: no submission or navigation can reach the original site.
    for form in soup.find_all("form"):
        form["data-orig-action"] = form.get("action", "")
        form["action"] = "#"
        form["onsubmit"] = "return false"
    for tag in soup.find_all(attrs={"formaction": True}):
        tag["formaction"] = "#"
    for anchor in soup.find_all("a"):
        href = anchor.get("href", "")
        if href and not href.startswith(("#", "javascript:")):
            anchor["data-original-href"] = urljoin(base, href)
        # Preserve the real target for feature analysis, but never let a
        # click actually leave this frozen sample -- a detector's click
        # tendency would otherwise decide which live external site (or
        # dead link, or same-origin routing error on a kit) it ends up
        # looking at, which is neither a fair nor a safe control condition.
        anchor["href"] = "#"
        for attr in ("target", "ping", "download"):
            anchor.attrs.pop(attr, None)

    _inject_safe_overlay_dismissal(soup)

    return str(soup)


# Tiny mtime-keyed cache so a sample is not re-parsed on every request.
_render_cache: dict[str, tuple[float, str]] = {}


def render_sample(sample_id: str, label: str) -> str | None:
    """Return the inert, self-contained HTML for one manual sample, or ``None``.

    ``label`` ("phishing" or "benign") selects which subfolder the sample
    lives under.
    """
    path = _samples_dir() / label / sample_id / "raw" / "page.mhtml"
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None

    key = str(path)
    cached = _render_cache.get(key)
    if cached and cached[0] == mtime:
        return cached[1]

    html = _mhtml_to_html(path.read_bytes())
    _render_cache[key] = (mtime, html)
    return html
