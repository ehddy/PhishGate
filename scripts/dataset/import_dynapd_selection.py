#!/usr/bin/env python3
"""Build and privately stage a reproducible 100-kit DynaPD cohort."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "private" / "dynapd"
DUPLICATE_CONTAINMENT_THRESHOLD = 0.70
XLSX_NAMESPACE = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
}
SELECTION_COLUMNS = (
    "selection_index",
    "selection_source",
    "random_state",
    "canonical_id",
    "source_hash",
    "subfolder",
    "brand",
    "entrypoint",
    "catalog_url",
    "copied_directory",
)
EXCLUSION_COLUMNS = (
    "selection_source",
    "source_hash",
    "subfolder",
    "brand",
    "matched_phishdecloaker_kit",
    "matching_file_count",
    "phishdecloaker_file_count",
    "containment_ratio",
)
NON_BRAND_EXCLUSION_COLUMNS = (
    "selection_source",
    "source_hash",
    "subfolder",
    "brand",
    "reason",
)
INCOMPLETE_EXCLUSION_COLUMNS = (
    "selection_source",
    "source_hash",
    "subfolder",
    "brand",
    "entrypoint",
    "reason",
    "reference",
    "referenced_from",
)
RUNTIME_EXCLUSION_COLUMNS = (
    "selection_source",
    "source_hash",
    "subfolder",
    "brand",
    "entrypoint",
    "reason",
    "http_status",
    "response_bytes",
)

NON_BRAND_EXACT = {
    ".php ext issue",
    "arab website?",
    "audio-login",
    "banking",
    "cloud service",
    "cloaking",
    "email",
    "fierzaxploit",
    "general financial independence",
    "login",
    "kundencenter",
    "multiple brands",
    "not usable",
    "other",
    "php ext issue",
    "postmaster",
    "proximamente",
    "sex scam",
    "start bootstrap",
    "unknown",
    "xleet",
}
BRAND_ALIASES = {
    "aobde,adobe pdf": "Adobe",
    "bet366": "bet365",
    "diepost": "Swiss Post",
    "office 366": "Microsoft",
    "office 367": "Microsoft",
    "royal bank": "Royal Bank of Canada",
    "we": "WeTransfer",
}
BRAND_FAMILY_MARKERS = (
    (("adobe", "aobde"), "Adobe"),
    (("royal bank of canada",), "Royal Bank of Canada"),
    (("caixa bank", "caixabank", "caixa"), "CaixaBank"),
    (("swiss post", "die post", "diepost"), "Swiss Post"),
    (("dpd group", "dpd"), "DPD"),
    (("saudi post", "spl"), "Saudi Post"),
    (("google", "gmail"), "Google"),
    (("microsoft", "windows", "office 365", "onedrive", "sharepoint", "outlook", "excel"), "Microsoft"),
    (("itau", "itaucard"), "Itau"),
    (("ledgersupport",), "Ledger"),
)
NON_BRAND_MARKERS = (
    "cloaking",
    "not usable",
    "php ext problem",
    "php extension problem",
    "syntax error",
    "scam",
    "xploit",
)
INDEX_FILENAMES = ("index.php", "index.html", "index.htm")


@dataclass(frozen=True)
class KitRecord:
    source_hash: str
    subfolder: str
    brand: str
    catalog_url: str
    entrypoint_url: str
    selection_source: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.source_hash, self.subfolder)

    @property
    def canonical_id(self) -> str:
        digest = hashlib.sha256(
            f"{self.source_hash}\0{self.subfolder}".encode("utf-8")
        ).hexdigest()[:12]
        return f"dynapd-{digest}"


@dataclass(frozen=True)
class DuplicateMatch:
    record: KitRecord
    phishdecloaker_kit: str
    matching_file_count: int
    phishdecloaker_file_count: int

    @property
    def containment_ratio(self) -> float:
        return self.matching_file_count / self.phishdecloaker_file_count


@dataclass(frozen=True)
class BrandExclusion:
    record: KitRecord
    reason: str


@dataclass(frozen=True)
class CompletenessIssue:
    reason: str
    reference: str
    referenced_from: str


@dataclass(frozen=True)
class IncompleteExclusion:
    record: KitRecord
    entrypoint: str
    issues: tuple[CompletenessIssue, ...]


@dataclass(frozen=True)
class RuntimeExclusion:
    record: KitRecord
    entrypoint: str
    reason: str
    http_status: int
    response_bytes: int


def non_brand_reason(brand: str) -> str | None:
    normalized = " ".join(brand.casefold().split())
    if normalized in NON_BRAND_EXACT:
        return f"generic or non-brand label: {brand}"
    for marker in NON_BRAND_MARKERS:
        if marker in normalized:
            return f"label marks an unusable/cloaking kit: {marker}"
    return None


def canonical_brand(brand: str) -> str:
    normalized = " ".join(brand.split())
    lowered = normalized.casefold()
    direct = BRAND_ALIASES.get(lowered)
    if direct is not None:
        return direct
    cross_provider_markers = (
        any(marker in lowered for marker in ("google", "gmail")),
        any(marker in lowered for marker in ("microsoft", "office365", "outlook", "onedrive")),
        "aol" in lowered,
        "yahoo" in lowered,
    )
    if sum(cross_provider_markers) > 1:
        return "Multiple brands"
    for markers, canonical in BRAND_FAMILY_MARKERS:
        if any(marker in lowered for marker in markers):
            return canonical
    return normalized


class _RenderReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []
        self.inline_css: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.casefold(): value or "" for name, value in attrs}
        tag = tag.casefold()
        if tag == "img" and values.get("src"):
            self.references.append(("image", values["src"]))
        elif tag == "script" and values.get("src"):
            self.references.append(("script", values["src"]))
        elif tag in {"iframe", "embed"} and values.get("src"):
            self.references.append(("embedded", values["src"]))
        elif tag in {"source", "video", "audio"}:
            if values.get("src"):
                self.references.append(("media", values["src"]))
            if values.get("poster"):
                self.references.append(("image", values["poster"]))
        elif tag == "link":
            rel = {item.casefold() for item in values.get("rel", "").split()}
            if "stylesheet" in rel and values.get("href"):
                self.references.append(("stylesheet", values["href"]))
        if values.get("style"):
            self.inline_css.append(values["style"])
        if tag == "style":
            self._in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.inline_css.append(data)


def _css_references(css: str) -> list[str]:
    return [
        match.group(1).strip(" \t\r\n\"'")
        for match in re.finditer(r"url\(\s*([^)]*?)\s*\)", css, re.IGNORECASE)
    ]


def _resolve_entrypoint(record: KitRecord, raw_root: Path) -> tuple[Path | None, str]:
    entrypoint = safe_entrypoint(record.entrypoint_url, record.source_hash).split("?", 1)[0]
    path = raw_root / record.source_hash / entrypoint
    if path.is_dir():
        for filename in INDEX_FILENAMES:
            candidate = path / filename
            if candidate.is_file():
                return candidate, entrypoint
        return None, entrypoint
    return (path if path.is_file() else None), entrypoint


def _inspect_render_completeness(record: KitRecord, raw_root: Path) -> tuple[CompletenessIssue, ...]:
    source_root = (raw_root / record.source_hash).resolve()
    entry_path, entrypoint = _resolve_entrypoint(record, raw_root)
    if entry_path is None:
        return (CompletenessIssue("missing entrypoint", entrypoint, entrypoint),)

    issues: list[CompletenessIssue] = []
    pending = [entry_path]
    inspected: set[Path] = set()
    while pending:
        document = pending.pop()
        resolved_document = document.resolve()
        if resolved_document in inspected:
            continue
        inspected.add(resolved_document)
        try:
            content = document.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            issues.append(CompletenessIssue("unreadable local asset", str(document), str(document)))
            continue

        if document.suffix.casefold() == ".css":
            references = [("css_asset", value) for value in _css_references(content)]
        else:
            parser = _RenderReferenceParser()
            parser.feed(content)
            references = parser.references
            for css in parser.inline_css:
                references.extend(("css_asset", value) for value in _css_references(css))

        for reference_type, reference in references:
            value = reference.strip()
            if not value or value.startswith(("#", "data:", "blob:", "javascript:")):
                continue
            # Saved CSS bundles commonly retain unused theme/font URLs. Those
            # references do not prove that the entry screen is visibly broken;
            # direct HTML images, media, embeds, and stylesheets remain blocking.
            if reference_type == "css_asset":
                continue
            parsed = urllib.parse.urlsplit(value)
            if parsed.scheme.casefold() in {"http", "https"} or value.startswith("//"):
                if reference_type != "script":
                    issues.append(
                        CompletenessIssue(
                            f"remote {reference_type} dependency",
                            value,
                            str(document.relative_to(source_root)),
                        )
                    )
                continue
            if parsed.scheme or parsed.netloc:
                continue
            decoded_path = urllib.parse.unquote(parsed.path).replace("\\", "/")
            if not decoded_path:
                continue
            asset = (
                source_root / decoded_path.lstrip("/")
                if decoded_path.startswith("/")
                else document.parent / decoded_path
            ).resolve()
            try:
                asset.relative_to(source_root)
            except ValueError:
                issues.append(
                    CompletenessIssue(
                        "render dependency escapes kit root",
                        value,
                        str(document.relative_to(source_root)),
                    )
                )
                continue
            is_font = asset.suffix.casefold() in {".eot", ".otf", ".ttf", ".woff", ".woff2"}
            if not asset.is_file() and reference_type != "script" and not is_font:
                issues.append(
                    CompletenessIssue(
                        f"missing local {reference_type} asset",
                        value,
                        str(document.relative_to(source_root)),
                    )
                )
            elif asset.suffix.casefold() == ".css":
                pending.append(asset)

    return tuple(dict.fromkeys(issues))


class _LocalRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_netloc: str) -> None:
        super().__init__()
        self.allowed_netloc = allowed_netloc

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        target = urllib.parse.urljoin(req.full_url, newurl)
        parsed = urllib.parse.urlsplit(target)
        if parsed.netloc != self.allowed_netloc:
            raise urllib.error.HTTPError(
                target,
                code,
                "external redirect blocked",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, target)


class RuntimeValidator:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        netloc = urllib.parse.urlsplit(self.base_url).netloc
        self.opener = urllib.request.build_opener(_LocalRedirectHandler(netloc))
        self.timeout_seconds = timeout_seconds
        self.cache: dict[tuple[str, str], RuntimeExclusion | None] = {}

    def validate(self, record: KitRecord) -> RuntimeExclusion | None:
        key = (record.source_hash, record.entrypoint_url)
        if key in self.cache:
            cached = self.cache[key]
            return None if cached is None else RuntimeExclusion(
                record,
                cached.entrypoint,
                cached.reason,
                cached.http_status,
                cached.response_bytes,
            )
        entrypoint = safe_entrypoint(record.entrypoint_url, record.source_hash)
        url_path = urllib.parse.quote(
            f"/{record.source_hash}/{entrypoint}",
            safe="/?=&%",
        )
        status = 0
        body = b""
        reason = ""
        try:
            with self.opener.open(
                f"{self.base_url}{url_path}",
                timeout=self.timeout_seconds,
            ) as response:
                status = response.status
                body = response.read(2_000_000)
        except urllib.error.HTTPError as error:
            status = error.code
            reason = str(error.reason)
        except (OSError, TimeoutError) as error:
            reason = f"{type(error).__name__}: {error}"

        body_text = body[:200_000].decode("utf-8", errors="ignore")
        if not reason and status != 200:
            reason = f"HTTP {status}"
        elif not reason and len(body) < 200:
            reason = "response smaller than 200 bytes"
        elif not reason and re.search(
            r"500 Internal Server Error|Fatal error|Parse error|Uncaught Error",
            body_text,
            re.IGNORECASE,
        ):
            reason = "runtime error page/body"

        result = None if not reason else RuntimeExclusion(
            record,
            entrypoint,
            reason,
            status,
            len(body),
        )
        self.cache[key] = result
        return result


def _available_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@contextmanager
def hardened_php_server(raw_root: Path, php_bin: Path):
    port = _available_loopback_port()
    environment = os.environ.copy()
    environment.update(
        {
            "DYNAPD_DOCROOT": str(raw_root),
            "DYNAPD_LISTEN_HOST": "127.0.0.1",
            "DYNAPD_LISTEN_PORT": str(port),
            "DYNAPD_PHP_BIN": str(php_bin),
        }
    )
    process = subprocess.Popen(
        ["sh", str(ROOT / "tools" / "runtime" / "start_dynapd_php.sh")],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("The hardened DynaPD PHP server exited during startup.")
            try:
                with urllib.request.urlopen(base_url, timeout=0.25):
                    break
            except (OSError, urllib.error.URLError):
                time.sleep(0.05)
        else:
            raise RuntimeError("Timed out starting the hardened DynaPD PHP server.")
        yield RuntimeValidator(base_url)
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def _brand_tokens(value: str) -> set[str]:
    ignored = {
        "and",
        "bank",
        "cloud",
        "credit",
        "document",
        "group",
        "limited",
        "of",
        "the",
        "union",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if token not in ignored
    }


def _content_fingerprints(root: Path) -> set[tuple[str, int]]:
    fingerprints: set[tuple[str, int]] = set()
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        size = path.stat().st_size
        if size < 1024:
            continue
        digest = hashlib.sha256()
        with path.open("rb") as input_file:
            for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
                digest.update(chunk)
        fingerprints.add((digest.hexdigest(), size))
    return fingerprints


class PhishDecloakerMatcher:
    """Detect DynaPD source trees substantially reused by PhishDecloaker."""

    def __init__(self, kit_root: Path, annotation_path: Path) -> None:
        with annotation_path.open(encoding="utf-8", newline="") as annotation_file:
            rows = list(csv.DictReader(annotation_file))
        self.kits: list[tuple[str, set[str], set[tuple[str, int]]]] = []
        for row in rows:
            kit_id = (row.get("directory") or "").strip()
            brand = (row.get("brand") or "").strip()
            directory = kit_root / kit_id
            if not kit_id or not brand or not directory.is_dir():
                raise RuntimeError(
                    f"PhishDecloaker comparison input is incomplete: {directory}"
                )
            self.kits.append(
                (kit_id, _brand_tokens(brand), _content_fingerprints(directory))
            )
        self.cache: dict[str, tuple[str, int, int] | None] = {}

    def match(self, record: KitRecord, raw_root: Path) -> DuplicateMatch | None:
        cached = self.cache.get(record.source_hash)
        if record.source_hash in self.cache:
            return (
                None
                if cached is None
                else DuplicateMatch(record, cached[0], cached[1], cached[2])
            )

        candidate = _content_fingerprints(raw_root / record.source_hash)
        record_brand = _brand_tokens(record.brand)
        best: tuple[float, int, str, int] | None = None
        for kit_id, kit_brand, kit_fingerprints in self.kits:
            kit_file_count = len(kit_fingerprints)
            if not kit_file_count:
                continue
            common = len(candidate & kit_fingerprints)
            ratio = common / kit_file_count
            brand_overlap = bool(record_brand & kit_brand)
            is_duplicate = (
                kit_file_count >= 3
                and common >= 3
                and ratio >= DUPLICATE_CONTAINMENT_THRESHOLD
            ) or (
                kit_file_count < 3
                and common == kit_file_count
                and brand_overlap
            )
            if is_duplicate and (
                best is None or (ratio, common, kit_id) > (best[0], best[1], best[2])
            ):
                best = (ratio, common, kit_id, kit_file_count)

        cached = None if best is None else (best[2], best[1], best[3])
        self.cache[record.source_hash] = cached
        return (
            None
            if cached is None
            else DuplicateMatch(record, cached[0], cached[1], cached[2])
        )


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    value = cell.find("m:v", XLSX_NAMESPACE)
    text = "" if value is None else (value.text or "")
    if cell.attrib.get("t") == "s" and text:
        return shared[int(text)]
    return text


def read_selected_xlsx(path: Path) -> list[list[str]]:
    """Read the simple first worksheet without adding an Excel dependency."""
    try:
        with zipfile.ZipFile(path) as archive:
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(
                    node.text or ""
                    for node in item.iter(
                        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                    )
                )
                for item in shared_root.findall("m:si", XLSX_NAMESPACE)
            ]
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        raise RuntimeError(f"Unable to read selected workbook: {path}") from error

    rows: list[list[str]] = []
    for row in sheet.findall(".//m:sheetData/m:row", XLSX_NAMESPACE):
        values = [_cell_text(cell, shared).strip() for cell in row.findall("m:c", XLSX_NAMESPACE)]
        if any(values):
            rows.append(values)
    return rows


def read_catalog(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as catalog_file:
            rows = list(csv.DictReader(catalog_file))
    except OSError as error:
        raise RuntimeError(f"Unable to read DynaPD catalog: {path}") from error
    required = {"HASH", "SUBFOLDER", "BRAND", "URL"}
    if not rows or not required.issubset(rows[0]):
        raise RuntimeError(f"DynaPD catalog is missing required columns: {path}")
    return rows


def safe_entrypoint(url: str, source_hash: str) -> str:
    parsed = urllib.parse.urlparse(url)
    parts = tuple(
        urllib.parse.unquote(part)
        for part in PurePosixPath(parsed.path).parts
        if part not in {"", "/"}
    )
    if not parts or parts[0] != source_hash or any(part in {".", ".."} for part in parts):
        raise RuntimeError(f"URL path does not begin with its source hash: {url}")
    relative_path = "/".join(parts[1:])
    if parsed.path.endswith("/") and relative_path:
        relative_path += "/"
    if parsed.query:
        relative_path += f"?{parsed.query}"
    return relative_path


def selected_records(
    workbook_rows: list[list[str]],
    catalog_rows: list[dict[str, str]],
) -> list[KitRecord]:
    catalog_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in catalog_rows:
        key = (row["HASH"].strip(), row["SUBFOLDER"].strip())
        catalog_by_key.setdefault(key, row)

    records: list[KitRecord] = []
    seen: set[tuple[str, str]] = set()
    for row_number, values in enumerate(workbook_rows, start=1):
        if len(values) < 4:
            raise RuntimeError(f"Selected workbook row {row_number} has fewer than four cells.")
        key = (values[0], values[1])
        catalog = catalog_by_key.get(key)
        if catalog is None:
            raise RuntimeError(f"Selected workbook row {row_number} is absent from the catalog: {key}")
        if key in seen:
            raise RuntimeError(f"Selected workbook contains a duplicate row: {key}")
        seen.add(key)
        final_url = values[5] if len(values) > 5 and values[5] else values[3]
        records.append(
            KitRecord(
                source_hash=key[0],
                subfolder=key[1],
                brand=canonical_brand(values[2] or catalog["BRAND"]),
                catalog_url=catalog["URL"].strip(),
                entrypoint_url=final_url.strip(),
                selection_source="manual_xlsx",
            )
        )
    return records


def _stable_digest(random_state: int, *parts: str) -> str:
    material = ":".join((str(random_state), *parts))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def fill_brand_balanced(
    selected: list[KitRecord],
    catalog_rows: list[dict[str, str]],
    raw_root: Path,
    target_count: int,
    random_state: int,
    duplicate_matcher: PhishDecloakerMatcher,
    runtime_validator: RuntimeValidator,
) -> tuple[
    list[KitRecord],
    list[DuplicateMatch],
    list[BrandExclusion],
    list[IncompleteExclusion],
    list[RuntimeExclusion],
]:
    if len(selected) > target_count:
        raise RuntimeError(
            f"Workbook already contains {len(selected)} rows, above target {target_count}."
        )

    exclusions: list[DuplicateMatch] = []
    brand_exclusions: list[BrandExclusion] = []
    incomplete_exclusions: list[IncompleteExclusion] = []
    runtime_exclusions: list[RuntimeExclusion] = []
    completeness_cache: dict[tuple[str, str], tuple[CompletenessIssue, ...]] = {}

    def completeness_issues(record: KitRecord) -> tuple[CompletenessIssue, ...]:
        cache_key = (record.source_hash, record.entrypoint_url)
        if cache_key not in completeness_cache:
            completeness_cache[cache_key] = _inspect_render_completeness(record, raw_root)
        return completeness_cache[cache_key]

    retained: list[KitRecord] = []
    for record in selected:
        reason = non_brand_reason(record.brand)
        if reason is not None:
            brand_exclusions.append(BrandExclusion(record, reason))
            continue
        issues = completeness_issues(record)
        if issues:
            incomplete_exclusions.append(
                IncompleteExclusion(
                    record,
                    safe_entrypoint(record.entrypoint_url, record.source_hash),
                    issues,
                )
            )
            continue
        runtime_exclusion = runtime_validator.validate(record)
        if runtime_exclusion is not None:
            runtime_exclusions.append(runtime_exclusion)
            continue
        duplicate = duplicate_matcher.match(record, raw_root)
        if duplicate is None:
            retained.append(record)
        else:
            exclusions.append(duplicate)

    blocked_keys = {record.key for record in selected}
    used_keys = {record.key for record in retained}
    used_hashes = {record.source_hash for record in selected}
    brand_exclusion_keys = {
        (exclusion.record.key, exclusion.reason) for exclusion in brand_exclusions
    }
    candidates_by_brand: dict[str, list[KitRecord]] = defaultdict(list)
    for row in catalog_rows:
        source_hash = row["HASH"].strip()
        subfolder = row["SUBFOLDER"].strip()
        brand = canonical_brand(row["BRAND"])
        url = row["URL"].strip()
        key = (source_hash, subfolder)
        brand_reason = non_brand_reason(brand)
        if (
            source_hash
            and subfolder
            and brand
            and brand_reason is not None
            and key not in blocked_keys
            and (raw_root / source_hash).is_dir()
            and (key, brand_reason) not in brand_exclusion_keys
        ):
            brand_exclusions.append(
                BrandExclusion(
                    KitRecord(
                        source_hash=source_hash,
                        subfolder=subfolder,
                        brand=brand,
                        catalog_url=url,
                        entrypoint_url=url,
                        selection_source="catalog_filter",
                    ),
                    brand_reason,
                )
            )
            brand_exclusion_keys.add((key, brand_reason))
        if (
            not source_hash
            or not subfolder
            or not brand
            or brand_reason is not None
            or key in blocked_keys
            or source_hash in used_hashes
            or not (raw_root / source_hash).is_dir()
        ):
            continue
        try:
            entrypoint = safe_entrypoint(url, source_hash)
        except RuntimeError:
            continue
        entry_path = raw_root / source_hash / entrypoint.split("?", 1)[0]
        if not entry_path.exists():
            continue
        candidates_by_brand[brand].append(
            KitRecord(
                source_hash=source_hash,
                subfolder=subfolder,
                brand=brand,
                catalog_url=url,
                entrypoint_url=url,
                selection_source="brand_balanced_fill",
            )
        )

    for brand, records in candidates_by_brand.items():
        records.sort(
            key=lambda record: _stable_digest(
                random_state,
                "candidate",
                brand,
                record.source_hash,
                record.subfolder,
            )
        )

    output = list(retained)
    brand_counts = Counter(record.brand for record in output)
    while len(output) < target_count:
        ordered_brands = sorted(
            candidates_by_brand,
            key=lambda brand: (
                brand_counts[brand],
                _stable_digest(random_state, "brand", str(len(output)), brand),
            ),
        )
        record: KitRecord | None = None
        for brand in ordered_brands:
            for candidate in candidates_by_brand[brand]:
                if candidate.source_hash in used_hashes:
                    continue
                issues = completeness_issues(candidate)
                if issues:
                    incomplete_exclusions.append(
                        IncompleteExclusion(
                            candidate,
                            safe_entrypoint(candidate.entrypoint_url, candidate.source_hash),
                            issues,
                        )
                    )
                    used_hashes.add(candidate.source_hash)
                    continue
                runtime_exclusion = runtime_validator.validate(candidate)
                if runtime_exclusion is not None:
                    runtime_exclusions.append(runtime_exclusion)
                    used_hashes.add(candidate.source_hash)
                    continue
                duplicate = duplicate_matcher.match(candidate, raw_root)
                if duplicate is not None:
                    exclusions.append(duplicate)
                    used_hashes.add(candidate.source_hash)
                    continue
                record = candidate
                break
            if record is not None:
                break
        if record is None:
            raise RuntimeError(f"Only {len(output)} non-overlapping kits were available.")
        output.append(record)
        used_keys.add(record.key)
        used_hashes.add(record.source_hash)
        brand_counts[record.brand] += 1
    return (
        output,
        exclusions,
        brand_exclusions,
        incomplete_exclusions,
        runtime_exclusions,
    )


def validate_source_tree(path: Path) -> None:
    for root, directories, files in os.walk(path):
        root_path = Path(root)
        for name in (*directories, *files):
            child = root_path / name
            if child.is_symlink():
                raise RuntimeError(f"Refusing to copy a source tree containing a symlink: {child}")


def write_selection(path: Path, records: list[KitRecord], random_state: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=SELECTION_COLUMNS)
        writer.writeheader()
        for index, record in enumerate(records, start=1):
            writer.writerow(
                {
                    "selection_index": index,
                    "selection_source": record.selection_source,
                    "random_state": random_state,
                    "canonical_id": record.canonical_id,
                    "source_hash": record.source_hash,
                    "subfolder": record.subfolder,
                    "brand": record.brand,
                    "entrypoint": safe_entrypoint(record.entrypoint_url, record.source_hash),
                    "catalog_url": record.catalog_url,
                    "copied_directory": record.canonical_id,
                }
            )


def write_exclusions(path: Path, exclusions: list[DuplicateMatch]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=EXCLUSION_COLUMNS)
        writer.writeheader()
        for duplicate in exclusions:
            writer.writerow(
                {
                    "selection_source": duplicate.record.selection_source,
                    "source_hash": duplicate.record.source_hash,
                    "subfolder": duplicate.record.subfolder,
                    "brand": duplicate.record.brand,
                    "matched_phishdecloaker_kit": duplicate.phishdecloaker_kit,
                    "matching_file_count": duplicate.matching_file_count,
                    "phishdecloaker_file_count": duplicate.phishdecloaker_file_count,
                    "containment_ratio": f"{duplicate.containment_ratio:.6f}",
                }
            )


def write_brand_exclusions(path: Path, exclusions: list[BrandExclusion]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=NON_BRAND_EXCLUSION_COLUMNS)
        writer.writeheader()
        for exclusion in exclusions:
            writer.writerow(
                {
                    "selection_source": exclusion.record.selection_source,
                    "source_hash": exclusion.record.source_hash,
                    "subfolder": exclusion.record.subfolder,
                    "brand": exclusion.record.brand,
                    "reason": exclusion.reason,
                }
            )


def write_incomplete_exclusions(
    path: Path,
    exclusions: list[IncompleteExclusion],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=INCOMPLETE_EXCLUSION_COLUMNS)
        writer.writeheader()
        for exclusion in exclusions:
            for issue in exclusion.issues:
                writer.writerow(
                    {
                        "selection_source": exclusion.record.selection_source,
                        "source_hash": exclusion.record.source_hash,
                        "subfolder": exclusion.record.subfolder,
                        "brand": exclusion.record.brand,
                        "entrypoint": exclusion.entrypoint,
                        "reason": issue.reason,
                        "reference": issue.reference,
                        "referenced_from": issue.referenced_from,
                    }
                )


def write_runtime_exclusions(path: Path, exclusions: list[RuntimeExclusion]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=RUNTIME_EXCLUSION_COLUMNS)
        writer.writeheader()
        for exclusion in exclusions:
            writer.writerow(
                {
                    "selection_source": exclusion.record.selection_source,
                    "source_hash": exclusion.record.source_hash,
                    "subfolder": exclusion.record.subfolder,
                    "brand": exclusion.record.brand,
                    "entrypoint": exclusion.entrypoint,
                    "reason": exclusion.reason,
                    "http_status": exclusion.http_status,
                    "response_bytes": exclusion.response_bytes,
                }
            )


def stage_private_copy(
    output_root: Path,
    raw_root: Path,
    records: list[KitRecord],
    exclusions: list[DuplicateMatch],
    brand_exclusions: list[BrandExclusion],
    incomplete_exclusions: list[IncompleteExclusion],
    runtime_exclusions: list[RuntimeExclusion],
    random_state: int,
) -> None:
    selection_path = output_root / "selection.csv"
    exclusion_path = output_root / "excluded_phishdecloaker.csv"
    brand_exclusion_path = output_root / "excluded_non_brand.csv"
    incomplete_exclusion_path = output_root / "excluded_incomplete.csv"
    runtime_exclusion_path = output_root / "excluded_runtime.csv"
    destination = output_root / "raw_selected"
    existing = tuple(
        path
        for path in (
            selection_path,
            exclusion_path,
            brand_exclusion_path,
            incomplete_exclusion_path,
            runtime_exclusion_path,
            destination,
        )
        if path.exists()
    )
    if existing:
        raise RuntimeError(
            f"Finalized DynaPD staging already exists under {output_root}; "
            "refusing to replace it."
        )
    output_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="dynapd-import-", dir=output_root))
    try:
        copied_root = staging / "raw_selected"
        copied_root.mkdir()
        for record in records:
            source = raw_root / record.source_hash
            validate_source_tree(source)
            shutil.copytree(source, copied_root / record.canonical_id)
        write_selection(staging / "selection.csv", records, random_state)
        write_exclusions(staging / "excluded_phishdecloaker.csv", exclusions)
        write_brand_exclusions(staging / "excluded_non_brand.csv", brand_exclusions)
        write_incomplete_exclusions(
            staging / "excluded_incomplete.csv",
            incomplete_exclusions,
        )
        write_runtime_exclusions(
            staging / "excluded_runtime.csv",
            runtime_exclusions,
        )
        os.replace(staging / "raw_selected", destination)
        os.replace(staging / "selection.csv", selection_path)
        os.replace(staging / "excluded_phishdecloaker.csv", exclusion_path)
        os.replace(staging / "excluded_non_brand.csv", brand_exclusion_path)
        os.replace(staging / "excluded_incomplete.csv", incomplete_exclusion_path)
        os.replace(staging / "excluded_runtime.csv", runtime_exclusion_path)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-xlsx", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--phishdecloaker-root", type=Path, required=True)
    parser.add_argument(
        "--phishdecloaker-annotation",
        type=Path,
        default=ROOT / "data" / "kit_brand_annotation.csv",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--target-count", type=int, default=100)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument(
        "--php-bin",
        type=Path,
        help="PHP CLI used for the hardened runtime smoke test (auto-detected by default).",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy the selected raw source directories after printing the plan.",
    )
    return parser.parse_args()


def resolve_php_bin(requested: Path | None, raw_root: Path) -> Path:
    candidates: list[Path] = []
    if requested is not None:
        candidates.append(requested.expanduser())
    system_php = shutil.which("php")
    if system_php:
        candidates.append(Path(system_php))
    candidates.append(raw_root.parent.parent / "bin" / "php")
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise RuntimeError("No executable PHP CLI found; pass --php-bin explicitly.")


def main() -> None:
    args = parse_args()
    if args.target_count < 1:
        raise SystemExit("--target-count must be positive.")
    workbook_rows = read_selected_xlsx(args.selected_xlsx)
    catalog_rows = read_catalog(args.catalog)
    manual = selected_records(workbook_rows, catalog_rows)
    duplicate_matcher = PhishDecloakerMatcher(
        args.phishdecloaker_root,
        args.phishdecloaker_annotation,
    )
    php_bin = resolve_php_bin(args.php_bin, args.raw_root)
    with hardened_php_server(args.raw_root, php_bin) as runtime_validator:
        (
            records,
            exclusions,
            brand_exclusions,
            incomplete_exclusions,
            runtime_exclusions,
        ) = fill_brand_balanced(
            manual,
            catalog_rows,
            args.raw_root,
            args.target_count,
            args.random_state,
            duplicate_matcher,
            runtime_validator,
        )
    brand_counts = Counter(record.brand for record in records)
    retained_manual = sum(
        record.selection_source == "manual_xlsx" for record in records
    )
    print(
        f"selected={len(records)} manual_input={len(manual)} "
        f"manual_retained={retained_manual} filled={len(records) - retained_manual} "
        f"non_brand_exclusions={len(brand_exclusions)} "
        f"incomplete_exclusions={len(incomplete_exclusions)} "
        f"runtime_exclusions={len(runtime_exclusions)} "
        f"phishdecloaker_exclusions={len(exclusions)} "
        f"unique_brands={len(brand_counts)} "
        f"max_brand_count={max(brand_counts.values())} random_state={args.random_state}"
    )
    if not args.copy:
        print("Plan only. Re-run with --copy to create selection.csv and raw_selected/.")
        return
    stage_private_copy(
        args.output_root,
        args.raw_root,
        records,
        exclusions,
        brand_exclusions,
        incomplete_exclusions,
        runtime_exclusions,
        args.random_state,
    )
    print(f"wrote {args.output_root / 'selection.csv'}")
    print(f"wrote {args.output_root / 'excluded_phishdecloaker.csv'}")
    print(f"wrote {args.output_root / 'excluded_non_brand.csv'}")
    print(f"wrote {args.output_root / 'excluded_incomplete.csv'}")
    print(f"wrote {args.output_root / 'excluded_runtime.csv'}")
    print(f"copied {len(records)} private raw kit directories to {args.output_root / 'raw_selected'}")


if __name__ == "__main__":
    main()
