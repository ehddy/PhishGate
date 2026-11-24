"""Explicit research-group catalog used for stratified template assignment."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path

from app.annotations import list_kit_ids
from app.dynapd_annotations import list_dynapd_ids
from app.manual_annotations import list_sample_ids, lookup_sample_metadata


G1_SYNTHETIC = "G1"
G2_WILD_PHISHING = "G2"
G3_BENIGN = "G3"


@dataclass(frozen=True, order=True)
class TargetKey:
    dataset: str
    canonical_id: str


def group_for_target(dataset: str, canonical_id: str) -> str:
    """Return the explicit experiment group for one registered target.

    Future DynaPD support should register its dataset as ``dynapd`` below and
    add its target keys to ``group_catalog()[G1_SYNTHETIC]``. The assignment
    code itself does not need to change.
    """
    if dataset in {"phishdecloaker", "dynapd"}:
        return G1_SYNTHETIC
    if dataset == "manual":
        return G3_BENIGN if lookup_sample_metadata(canonical_id).label == "benign" else G2_WILD_PHISHING
    raise ValueError(f"Unknown research dataset: {dataset}")


def experiment_manifest_path() -> Path | None:
    configured = os.environ.get("PHISHGATE_EXPERIMENT_MANIFEST", "").strip()
    return Path(configured) if configured else None


def _manifest_catalog(path: Path) -> dict[str, tuple[TargetKey, ...]]:
    groups: dict[str, list[TargetKey]] = {
        G1_SYNTHETIC: [],
        G2_WILD_PHISHING: [],
        G3_BENIGN: [],
    }
    try:
        with path.open(encoding="utf-8", newline="") as manifest_file:
            rows = list(csv.DictReader(manifest_file))
    except OSError as error:
        raise RuntimeError(f"Unable to read experiment manifest: {path}") from error

    seen: set[TargetKey] = set()
    for row_number, row in enumerate(rows, start=2):
        group_id = (row.get("group_id") or "").strip()
        target = TargetKey(
            (row.get("dataset") or "").strip(),
            (row.get("canonical_id") or "").strip(),
        )
        if group_id not in groups or not target.dataset or not target.canonical_id:
            raise RuntimeError(f"Invalid experiment-manifest row {row_number}.")
        if group_for_target(target.dataset, target.canonical_id) != group_id:
            raise RuntimeError(f"Experiment-manifest row {row_number} has a mismatched group.")
        if target in seen:
            raise RuntimeError(f"Experiment-manifest row {row_number} duplicates a target.")
        seen.add(target)
        groups[group_id].append(target)
    return {group_id: tuple(targets) for group_id, targets in groups.items()}


def group_catalog() -> dict[str, tuple[TargetKey, ...]]:
    """Return all currently registered targets, explicitly separated by group."""
    manifest_path = experiment_manifest_path()
    if manifest_path is not None:
        return _manifest_catalog(manifest_path)
    return {
        G1_SYNTHETIC: (
            tuple(TargetKey("phishdecloaker", kit_id) for kit_id in list_kit_ids())
            + tuple(TargetKey("dynapd", canonical_id) for canonical_id in list_dynapd_ids())
        ),
        G2_WILD_PHISHING: tuple(TargetKey("manual", sample_id) for sample_id in list_sample_ids("phishing")),
        G3_BENIGN: tuple(TargetKey("manual", sample_id) for sample_id in list_sample_ids("benign")),
    }
