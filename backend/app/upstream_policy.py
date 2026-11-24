"""Constrain reverse-proxy traffic to approved local experiment upstreams."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, OpenerDirector, Request, build_opener


_BUILTIN_UPSTREAM_HOSTS = (
    "127.0.0.1",
    "::1",
    "localhost",
    "host.docker.internal",
    "phishdecloaker-kits",
    "dynapd-kits",
)


def _operator_upstream_hosts() -> tuple[str, ...]:
    """Extra upstream hosts an operator allows via PHISHGATE_UPSTREAM_ALLOWED_HOSTS.

    This only widens which single upstream may be configured at startup; the
    per-request origin pin in ``LocalUpstreamClient.open`` is unchanged, so it
    never enables per-request arbitrary-URL proxying (no open proxy).
    """
    raw = os.environ.get("PHISHGATE_UPSTREAM_ALLOWED_HOSTS", "")
    return tuple(host.strip().lower() for host in raw.split(",") if host.strip())


# Hosts a startup-configured upstream may use. Built-in localhost/kit hosts
# plus any operator-provided hosts for the generic gate mode.
ALLOWED_UPSTREAM_HOSTS = frozenset(_BUILTIN_UPSTREAM_HOSTS + _operator_upstream_hosts())

KIT_CONTENT_SECURITY_POLICY = (
    "default-src 'self' data: blob:; "
    # External scripts from any origin are allowed
    # so author-provided kits keep their original page behavior; fetches,
    # frames, and form submissions below stay same-origin.
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' http: https:; "
    "style-src 'self' 'unsafe-inline' http: https:; "
    "img-src 'self' data: blob: http: https:; "
    "font-src 'self' data: http: https:; "
    "connect-src 'self'; form-action 'self'; "
    "frame-src 'self' data: blob:; object-src 'none'; base-uri 'self'"
)


def preserved_content_type(headers: Mapping[str, str]) -> str:
    """Keep the upstream media type parameters without forwarding unsafe text."""
    content_type = headers.get("Content-Type")
    if content_type is None:
        return "application/octet-stream"
    content_type = content_type.strip()
    if not content_type or "\r" in content_type or "\n" in content_type:
        return "application/octet-stream"
    return content_type


@dataclass(frozen=True)
class UpstreamOrigin:
    scheme: str
    hostname: str
    port: int


def _origin(url: str) -> UpstreamOrigin:
    parsed = urlsplit(url)
    if parsed.scheme != "http":
        raise ValueError("PhishGate upstreams must use local HTTP.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("PhishGate upstream URLs must not contain credentials.")
    hostname = (parsed.hostname or "").lower()
    if hostname not in ALLOWED_UPSTREAM_HOSTS:
        raise ValueError(
            f"PhishGate upstream host {hostname!r} is not an approved local experiment host."
        )
    try:
        port = parsed.port or 80
    except ValueError as error:
        raise ValueError("PhishGate upstream URL has an invalid port.") from error
    return UpstreamOrigin(parsed.scheme, hostname, port)


def validate_upstream_base(url: str) -> str:
    """Return a normalized, origin-only URL for one approved local upstream."""
    parsed = urlsplit(url.strip())
    origin = _origin(url.strip())
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("PhishGate upstream must be an origin without a path, query, or fragment.")
    host = f"[{origin.hostname}]" if ":" in origin.hostname else origin.hostname
    port = "" if origin.port == 80 else f":{origin.port}"
    return f"{origin.scheme}://{host}{port}"


def rewrite_public_redirect_root(location: str, canonical_root: str, public_root: str) -> str:
    """Keep a root-relative kit redirect on its detector-facing alias."""
    parsed = urlsplit(location)
    canonical_prefix = f"/{canonical_root}"
    if parsed.path != canonical_prefix and not parsed.path.startswith(f"{canonical_prefix}/"):
        return location
    public_path = f"/{public_root}{parsed.path[len(canonical_prefix):]}"
    return urlunsplit(("", "", public_path, parsed.query, parsed.fragment))


class SameOriginRedirectHandler(HTTPRedirectHandler):
    """Return local redirects to the caller instead of following them."""

    def __init__(self, allowed_origin: UpstreamOrigin) -> None:
        super().__init__()
        self.allowed_origin = allowed_origin

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        target = urljoin(req.full_url, newurl)
        try:
            target_origin = _origin(target)
        except ValueError as error:
            raise HTTPError(target, code, str(error), headers, fp) from error
        if target_origin != self.allowed_origin:
            raise HTTPError(target, code, "Upstream redirect left its approved local origin.", headers, fp)
        return None

    def http_error_302(self, req, fp, code, msg, headers):  # type: ignore[no-untyped-def]
        location = headers.get("Location")
        if location is None:
            raise HTTPError(req.full_url, code, msg, headers, fp)
        # Validate through redirect_request(), but return the untouched 3xx
        # response so the public browser updates its own URL before resolving
        # relative CSS, JavaScript, and image paths.
        self.redirect_request(req, fp, code, msg, headers, location)
        return fp

    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302
    http_error_308 = http_error_302


class LocalUpstreamClient:
    """Open requests only against one validated local upstream origin."""

    def __init__(self, base_url: str) -> None:
        self.base_url = validate_upstream_base(base_url)
        self.origin = _origin(self.base_url)
        self.opener: OpenerDirector = build_opener(SameOriginRedirectHandler(self.origin))

    def browser_redirect_location(self, request_url: str, location: str) -> str:
        """Return a browser-safe local Location without an internal hostname."""
        target = urljoin(request_url, location)
        if _origin(target) != self.origin:
            raise ValueError("Upstream redirect left its approved local origin.")
        parsed_location = urlsplit(location)
        if not parsed_location.scheme and not parsed_location.netloc:
            return location
        parsed_target = urlsplit(target)
        return urlunsplit(("", "", parsed_target.path or "/", parsed_target.query, parsed_target.fragment))

    def open(
        self,
        target_url: str,
        *,
        method: str = "GET",
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ):  # type: ignore[no-untyped-def]
        if _origin(target_url) != self.origin:
            raise ValueError("The proxy target does not match its configured local upstream.")
        if method not in {"GET", "POST"}:
            raise ValueError(f"Unsupported upstream method: {method}")
        return self.opener.open(
            Request(
                target_url,
                data=body if method == "POST" else None,
                headers=headers or {},
                method=method,
            )
        )
