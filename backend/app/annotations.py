"""Kit annotation lookup for gate display context and opaque routing.

The annotation CSV (`data/kit_brand_annotation.csv`) ships with the repo and
is mounted read-only into the backend container. It maps each kit directory
(``kit1`` … ``kit100``) to the published brand label, used only to render a
neutral, brand-aware gate screen; it never exposes upstream kit content.

Access slugs are derived in memory from ``PHISHGATE_SEED`` and the stable
``directory`` column. The seed and its derived slugs therefore never need to be
written into this tracked CSV. Brand lookup stays fail-safe, while startup
validation in ``backend/app/main.py`` rejects missing seed/directory mappings.
"""

import csv
import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache

from app.seeding import purpose_seed


DEFAULT_ANNOTATION_PATH = "/app/data/phishdecloaker/kit_brand_annotation.csv"


@dataclass(frozen=True)
class KitMetadata:
    brand: str | None


def _annotation_path() -> str:
    return os.environ.get("PHISHGATE_BRAND_ANNOTATION", DEFAULT_ANNOTATION_PATH)


def _routing_seed() -> str:
    try:
        return purpose_seed("route")
    except RuntimeError:
        return ""


def list_kit_ids() -> tuple[str, ...]:
    """Return every registered PhishDecloaker kit id in stable order."""
    return tuple(_metadata_index(_annotation_path()))


@lru_cache(maxsize=1)
def _metadata_index(path: str) -> dict[str, KitMetadata]:
    """Return stable display metadata keyed by kit directory."""
    index: dict[str, KitMetadata] = {}
    try:
        with open(path, encoding="utf-8", newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                directory = (row.get("directory") or "").strip()
                if not directory:
                    continue
                index[directory] = KitMetadata(
                    brand=(row.get("brand") or "").strip() or None,
                )
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    return index


def lookup_kit_metadata(kit_root: str) -> KitMetadata:
    """Return annotation metadata with empty fields when a kit is unknown."""
    return _metadata_index(_annotation_path()).get(kit_root, KitMetadata(None))


def lookup_brand(kit_root: str) -> str | None:
    """Return the brand for a kit directory such as ``kit26``, or ``None``."""
    return lookup_kit_metadata(kit_root).brand


def derive_access_slug(seed: str, directory: str) -> str:
    """Return the legacy-compatible 12-character slug for one kit directory."""
    return hashlib.sha256(f"{seed}:{directory}".encode("utf-8")).hexdigest()[:12]


@lru_cache(maxsize=4)
def _slug_index(path: str, seed: str) -> dict[str, str]:
    """Build an in-memory ``{access_slug: directory}`` map from stable rows."""
    index: dict[str, str] = {}
    if not seed:
        return index

    try:
        with open(path, encoding="utf-8", newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                directory = (row.get("directory") or "").strip()
                if not directory:
                    continue
                slug = derive_access_slug(seed, directory)
                existing = index.get(slug)
                if existing is not None and existing != directory:
                    raise RuntimeError("Generated kit access slugs collided; use a different seed.")
                index[slug] = directory
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    return index


def lookup_kit_by_slug(slug: str) -> str | None:
    """Return the real kit directory for an opaque, seed-derived access slug."""
    return _slug_index(_annotation_path(), _routing_seed()).get(slug)


def has_slug_mappings() -> bool:
    """Return whether any access-slug mappings are currently loaded."""
    return bool(_slug_index(_annotation_path(), _routing_seed()))
