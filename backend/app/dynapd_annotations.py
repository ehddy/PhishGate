"""Private DynaPD selection lookup and opaque access-slug derivation."""

from __future__ import annotations

import csv
import hashlib
import os
import posixpath
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlsplit, urlunsplit

from app.seeding import purpose_seed


DEFAULT_SELECTION_PATH = "/app/data/dynapd/selection.csv"
CANONICAL_ID_PATTERN = re.compile(r"^dynapd-[0-9a-f]{12}$")


@dataclass(frozen=True)
class DynaPDMetadata:
    brand: str
    entrypoint: str
    copied_directory: str


def _selection_path() -> str:
    return os.environ.get("PHISHGATE_DYNAPD_SELECTION", DEFAULT_SELECTION_PATH)


def _routing_seed() -> str:
    try:
        return purpose_seed("route")
    except RuntimeError:
        return ""


def _safe_relative_entrypoint(value: str) -> str:
    path_text = value.split("?", 1)[0]
    path = PurePosixPath(path_text)
    if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        raise RuntimeError(f"Unsafe DynaPD entrypoint: {value!r}")
    return value


@lru_cache(maxsize=2)
def _metadata_index(path: str) -> dict[str, DynaPDMetadata]:
    index: dict[str, DynaPDMetadata] = {}
    try:
        with open(path, encoding="utf-8", newline="") as selection_file:
            rows = list(csv.DictReader(selection_file))
    except FileNotFoundError:
        return {}
    except OSError:
        return {}

    for row_number, row in enumerate(rows, start=2):
        canonical_id = (row.get("canonical_id") or "").strip()
        brand = (row.get("brand") or "").strip()
        entrypoint = (row.get("entrypoint") or "").strip()
        copied_directory = (row.get("copied_directory") or "").strip()
        if not CANONICAL_ID_PATTERN.fullmatch(canonical_id):
            raise RuntimeError(f"Invalid DynaPD canonical id on row {row_number}.")
        if not brand or copied_directory != canonical_id:
            raise RuntimeError(f"Invalid DynaPD selection row {row_number}.")
        if canonical_id in index:
            raise RuntimeError(f"Duplicate DynaPD canonical id on row {row_number}.")
        index[canonical_id] = DynaPDMetadata(
            brand=brand,
            entrypoint=_safe_relative_entrypoint(entrypoint),
            copied_directory=copied_directory,
        )
    return index


def list_dynapd_ids() -> tuple[str, ...]:
    """Return every selected DynaPD canonical id in CSV order."""
    return tuple(_metadata_index(_selection_path()))


def lookup_dynapd_metadata(canonical_id: str) -> DynaPDMetadata | None:
    """Return one selected DynaPD record, or ``None`` when it is unknown."""
    return _metadata_index(_selection_path()).get(canonical_id)


def upstream_location(canonical_id: str, public_suffix: str) -> tuple[str, str]:
    """Map a public slug suffix to the selected kit's private copied path.

    The bare slug resolves to the recorded entrypoint. Relative browser asset
    requests resolve beside that entrypoint so the private source hash and
    nested source path never need to appear in the public URL.
    """
    metadata = lookup_dynapd_metadata(canonical_id)
    if metadata is None:
        raise KeyError(canonical_id)

    entrypoint_path, _, entrypoint_query = metadata.entrypoint.partition("?")
    suffix = public_suffix.lstrip("/")
    suffix_path = PurePosixPath(suffix)
    if suffix_path.is_absolute() or any(part in {".", ".."} for part in suffix_path.parts):
        raise ValueError(f"Unsafe DynaPD public path suffix: {public_suffix!r}")

    root_alias = derive_redirect_root_alias(canonical_id)
    if suffix == root_alias or suffix.startswith(f"{root_alias}/"):
        relative_path = suffix[len(root_alias):].lstrip("/")
        query = ""
    elif suffix:
        entrypoint_directory = (
            entrypoint_path
            if entrypoint_path.endswith("/")
            else posixpath.dirname(entrypoint_path)
        )
        relative_path = posixpath.join(entrypoint_directory, suffix)
        query = ""
    else:
        relative_path = entrypoint_path
        query = entrypoint_query

    upstream_path = posixpath.join(metadata.copied_directory, relative_path)
    if entrypoint_path.endswith("/") and not suffix and not upstream_path.endswith("/"):
        upstream_path += "/"
    return upstream_path, query


def rewrite_public_redirect_root(
    location: str,
    canonical_id: str,
    public_root: str,
    upstream_request_path: str,
) -> str:
    """Keep a DynaPD redirect inside its detector-facing slug namespace.

    Resolve relative redirects against the real upstream request, then replace
    the private copied-directory root with an opaque public root alias. The
    alias distinguishes root-relative paths from the normal public namespace,
    whose suffixes resolve beside the selected entrypoint.
    """
    metadata = lookup_dynapd_metadata(canonical_id)
    if metadata is None:
        raise KeyError(canonical_id)

    resolved = urlsplit(urljoin(f"/{upstream_request_path}", location))
    internal_prefix = f"/{metadata.copied_directory}"
    if resolved.path != internal_prefix and not resolved.path.startswith(f"{internal_prefix}/"):
        return location

    suffix = resolved.path[len(internal_prefix):].lstrip("/")
    root_alias = derive_redirect_root_alias(canonical_id)
    public_path = f"/{public_root}/{root_alias}"
    if suffix:
        public_path = f"{public_path}/{suffix}"
    elif resolved.path.endswith("/"):
        public_path += "/"
    return urlunsplit(("", "", public_path, resolved.query, resolved.fragment))


def derive_redirect_root_alias(canonical_id: str) -> str:
    """Return an opaque segment for DynaPD root-relative redirect paths."""
    return hashlib.sha256(
        f"dynapd-redirect-root:{_routing_seed()}:{canonical_id}".encode("utf-8")
    ).hexdigest()[:12]


def derive_access_slug(seed: str, canonical_id: str) -> str:
    """Return a DynaPD-specific opaque 12-character access slug."""
    return hashlib.sha256(
        f"dynapd:{seed}:{canonical_id}".encode("utf-8")
    ).hexdigest()[:12]


@lru_cache(maxsize=4)
def _slug_index(path: str, seed: str) -> dict[str, str]:
    if not seed:
        return {}
    index: dict[str, str] = {}
    for canonical_id in _metadata_index(path):
        slug = derive_access_slug(seed, canonical_id)
        existing = index.get(slug)
        if existing is not None and existing != canonical_id:
            raise RuntimeError(
                "Generated DynaPD access slugs collided; use a different seed."
            )
        index[slug] = canonical_id
    return index


def lookup_dynapd_by_slug(slug: str) -> str | None:
    """Return the selected DynaPD id for an opaque access slug."""
    return _slug_index(_selection_path(), _routing_seed()).get(slug)


def has_slug_mappings() -> bool:
    """Return whether selected DynaPD slug mappings are loaded."""
    return bool(_slug_index(_selection_path(), _routing_seed()))
