"""Annotation lookup for the separately maintained ``manual`` dataset.

Kept fully independent from ``backend/app/annotations.py`` (the phishdecloaker
kit100 lookup): its own CSVs (``data/manual_annotation.csv`` for phishing
samples and ``data/manual_benign_annotation.csv`` for benign ones, both
generated from each sample's source.yaml), its own access-slug derivation (salted separately so a kit100
directory name and a manual sample id can never collide), and its own
metadata type. ``backend/app/main.py`` combines this with the phishdecloaker
lookup only at the single point where it decides which dataset a request's
access slug belongs to.

Both labels are served through the identical gate-then-reveal path -- a
benign sample gets the same access slug / gate / reveal mechanism as a
phishing one, since the point of collecting benign samples is to give a
detection agent the same interaction hurdle in front of pages that should
*not* be classified as phishing, not to special-case them at serving time.
``label`` here exists purely so a display/consuming caller can tell which
bucket a given sample_id came from.
"""

import csv
import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse

from app.seeding import purpose_seed


DEFAULT_ANNOTATION_PATH = "/app/data/manual/manual_annotation.csv"
DEFAULT_BENIGN_ANNOTATION_PATH = "/app/data/manual/manual_benign_annotation.csv"


@dataclass(frozen=True)
class ManualSampleMetadata:
    brand: str | None
    label: str | None = None


def _annotation_paths() -> tuple[str, str]:
    return (
        os.environ.get("PHISHGATE_MANUAL_ANNOTATION", DEFAULT_ANNOTATION_PATH),
        os.environ.get("PHISHGATE_MANUAL_BENIGN_ANNOTATION", DEFAULT_BENIGN_ANNOTATION_PATH),
    )


def _routing_seed() -> str:
    try:
        return purpose_seed("route")
    except RuntimeError:
        return ""


def _read_rows(path: str) -> list[dict[str, str]]:
    try:
        with open(path, encoding="utf-8", newline="") as csv_file:
            return list(csv.DictReader(csv_file))
    except (FileNotFoundError, OSError):
        return []


@lru_cache(maxsize=1)
def _metadata_index(phishing_path: str, benign_path: str) -> dict[str, ManualSampleMetadata]:
    """Return stable display metadata keyed by manual sample id, both labels merged."""
    index: dict[str, ManualSampleMetadata] = {}
    for label, path in (("phishing", phishing_path), ("benign", benign_path)):
        for row in _read_rows(path):
            sample_id = (row.get("directory") or "").strip()
            if not sample_id:
                continue
            index[sample_id] = ManualSampleMetadata(
                brand=(row.get("brand") or "").strip() or None,
                label=(row.get("label") or "").strip() or label,
            )
    return index


def lookup_sample_metadata(sample_id: str) -> ManualSampleMetadata:
    """Return annotation metadata with empty fields when a sample is unknown."""
    return _metadata_index(*_annotation_paths()).get(sample_id, ManualSampleMetadata(None, None))


def list_sample_ids(label: str) -> tuple[str, ...]:
    """Return registered manual sample ids for one explicit research label."""
    if label not in {"phishing", "benign"}:
        return ()
    return tuple(
        sample_id
        for sample_id, metadata in _metadata_index(*_annotation_paths()).items()
        if metadata.label == label
    )


def derive_access_slug(seed: str, sample_id: str) -> str:
    """Return the 12-character access slug for one manual sample id.

    Salted with a ``manual:`` prefix distinct from
    ``annotations.derive_access_slug``'s kit100 salt, so a kit directory name
    and a manual sample id can never collide even if they happened to match.
    The same derivation is used for both phishing and benign samples -- they
    share one slug keyspace, since sample_id is already guaranteed unique
    across both labels.
    """
    return hashlib.sha256(f"manual:{seed}:{sample_id}".encode("utf-8")).hexdigest()[:12]


@lru_cache(maxsize=4)
def _slug_index(phishing_path: str, benign_path: str, seed: str) -> dict[str, str]:
    """Build an in-memory ``{access_slug: sample_id}`` map from stable rows."""
    index: dict[str, str] = {}
    if not seed:
        return index

    for path in (phishing_path, benign_path):
        for row in _read_rows(path):
            sample_id = (row.get("directory") or "").strip()
            if not sample_id:
                continue
            slug = derive_access_slug(seed, sample_id)
            existing = index.get(slug)
            if existing is not None and existing != sample_id:
                raise RuntimeError("Generated manual-sample access slugs collided; use a different seed.")
            index[slug] = sample_id
    return index


def lookup_sample_by_slug(slug: str) -> str | None:
    """Return the real manual sample id for an opaque, seed-derived access slug."""
    phishing_path, benign_path = _annotation_paths()
    return _slug_index(phishing_path, benign_path, _routing_seed()).get(slug)


def has_slug_mappings() -> bool:
    """Return whether any manual-sample access-slug mappings are currently loaded."""
    phishing_path, benign_path = _annotation_paths()
    return bool(_slug_index(phishing_path, benign_path, _routing_seed()))


def _hostname_from_url(url: str) -> str | None:
    """Return the lower-cased hostname from a source URL, or ``None``."""
    hostname = urlparse(url).hostname
    return hostname.lower() if hostname else None


@lru_cache(maxsize=1)
def _host_index(phishing_path: str, benign_path: str) -> dict[str, str]:
    """Build an in-memory ``{hostname: sample_id}`` map, both labels merged.

    Both phishing and benign samples are reachable at their own real source
    domain (e.g. ``amazon.com``, or the domain a phishing kit impersonated),
    on top of the existing dummy-domain + slug routing every manual sample
    already has (kept as a second, independent access path -- this never
    removes a mapping from ``_slug_index``). See data/manual/README.md.
    """
    index: dict[str, str] = {}
    for path in (phishing_path, benign_path):
        for row in _read_rows(path):
            sample_id = (row.get("directory") or "").strip()
            source_url = (row.get("source_url") or "").strip()
            if not sample_id or not source_url:
                continue
            hostname = _hostname_from_url(source_url)
            if hostname is None:
                continue
            existing = index.get(hostname)
            if existing is not None and existing != sample_id:
                raise RuntimeError(
                    f"Two manual samples ({existing!r}, {sample_id!r}) share the host {hostname!r}; "
                    "a hostname can only route to one page. Remove/re-collect one of them."
                )
            index[hostname] = sample_id
    return index


def lookup_sample_by_host(host: str) -> str | None:
    """Return the manual sample id whose real domain matches ``host``, if any."""
    phishing_path, benign_path = _annotation_paths()
    return _host_index(phishing_path, benign_path).get(host.lower())
