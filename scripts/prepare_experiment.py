#!/usr/bin/env python3
"""Prepare every seed-derived experiment artifact through one command."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
KIT_ANNOTATION = ROOT / "data" / "kit_brand_annotation.csv"
DYNAPD_SELECTION = ROOT / "data" / "private" / "dynapd" / "selection.csv"
MANUAL_PHISHING = ROOT / "data" / "manual_annotation.csv"
MANUAL_BENIGN = ROOT / "data" / "manual_benign_annotation.csv"
TARGET_ROOT = ROOT / "targets"
PRELIMINARY_ROOT = TARGET_ROOT / "PRELIM"
EVALUATION_ROOT = TARGET_ROOT / "EVAL"
BENCHMARK_ROOT = TARGET_ROOT / "BENCH"
SUBSET_ROOT = TARGET_ROOT / "SUBSETS"
STANDALONE_CONTEXT_ROOT = TARGET_ROOT / "CONTEXT"
CONFIG_ROOT = ROOT / "config"
PRELIMINARY_GROUP_QUOTAS = {"G1": 50}
EVALUATION_GROUP_COUNTS = {"G1": 150, "G2": 100, "G3": 200}
EVALUATION_G1_DATASETS = {"phishdecloaker": 75, "dynapd": 75}
AUXILIARY_GROUP_QUOTAS = {"G1": 50}
AUXILIARY_G1_DATASETS = {"phishdecloaker": 25, "dynapd": 25}
# Comparative = Original + Click (external and controlled detectors);
# Controlled gate-family analysis = Interaction + Challenge (controlled
# detectors). Each gated family maps directly to one pooled backend profile
# and gate type.
GATED_FAMILIES = ("click", "interaction", "challenge")
COMPARATIVE_FAMILIES = ("original", "click")
CONTROLLED_GATE_FAMILIES = ("interaction", "challenge")
PRELIMINARY_FAMILIES = ("click", "interaction", "challenge")
MAIN_PROFILES = ("baseline", "click")
EXTERNAL_DETECTORS = ("memophishagent", "phishllm")
CONTROLLED_ANALYSIS_DETECTORS = ("one_shot", "generic", "phishwalk")
MAIN_DETECTORS = EXTERNAL_DETECTORS + CONTROLLED_ANALYSIS_DETECTORS
EVALUATION_RUNTIME_MANIFEST = "/app/targets/EVAL/manifest.csv"
PRELIMINARY_RUNTIME_MANIFEST = "/app/targets/PRELIM/manifest.csv"
AUXILIARY_RUNTIME_MANIFEST = "/app/targets/SUBSETS/AUX_G1/manifest.csv"
STANDALONE_CONTEXT_RUNTIME_MANIFEST = "/app/targets/CONTEXT/manifest.csv"
# PRELIM sweeps two model pools: "selection" (commercial, for model selection)
# and "oss" (open-source, to confirm PhishWalk also runs on OSS models). The oss
# ids are placeholders to be replaced with real model names.
PRELIMINARY_MODELS = (
    ("selection", "gpt-5.6-luna"),
    ("selection", "claude-haiku-4-5"),
    ("selection", "gemini-3.5-flash-lite"),
    ("oss", "oss1"),
    ("oss", "oss2"),
    ("oss", "oss3"),
)
CONTEXT_MODES = ("neutral", "brand-label")
MAIN_DOMAIN_STYLE = "pronounceable"
DOMAIN_STYLE_ABLATION_PROFILE = "click"
DOMAIN_STYLE_ABLATION_STYLES = ("hash",)
EXPECTED_GROUP_COUNTS = {"G1": 200, "G2": 100, "G3": 200}
EXPECTED_G1_DATASETS = {"phishdecloaker": 100, "dynapd": 100}
EXPECTED_G3_STRATA = {
    ("form", "popular"): 50,
    ("form", "long_tail"): 50,
    ("general", "popular"): 50,
    ("general", "long_tail"): 50,
}
COHORT_COLUMNS = ("group_id", "dataset", "canonical_id")
SEED_PLACEHOLDER = "change-me-per-experiment"
sys.path.insert(0, str(ROOT / "backend"))

from app.runtime_config import DOMAIN_STYLES, derive_local_domain, derive_route_prefix
from app.seeding import derive_seed


def derive_kit_slug(seed: str, directory: str) -> str:
    return hashlib.sha256(f"{seed}:{directory}".encode()).hexdigest()[:12]


def derive_dynapd_slug(seed: str, canonical_id: str) -> str:
    return hashlib.sha256(f"dynapd:{seed}:{canonical_id}".encode()).hexdigest()[:12]


def derive_manual_slug(seed: str, sample_id: str) -> str:
    return hashlib.sha256(f"manual:{seed}:{sample_id}".encode()).hexdigest()[:12]


def read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        raise SystemExit(f"{ENV_PATH} not found. Copy .env.example to .env first.")
    values: dict[str, str] = {}
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def require_seed(env: dict[str, str]) -> str:
    seed = env.get("PHISHGATE_SEED", "").strip()
    if not seed:
        raise SystemExit(
            "PHISHGATE_SEED is empty in .env -- set it before preparing the experiment."
        )
    if seed == SEED_PLACEHOLDER:
        raise SystemExit(
            "PHISHGATE_SEED still uses the example placeholder. "
            "Set a private value (a numeric random_state-style value is fine) and run again."
        )
    return seed


def generate_route_values() -> None:
    env = read_env()
    master_seed = require_seed(env)
    prefix = derive_route_prefix(master_seed)
    style = env.get("PHISHGATE_DOMAIN_STYLE", "off").strip() or "off"
    try:
        local_domain = derive_local_domain(master_seed, style)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    print(f"Derived route prefix: /{prefix}/")
    if local_domain is None:
        print("PHISHGATE_DOMAIN_STYLE=off -- no local domain generated.")
        return
    port = env.get("PHISHGATE_PORT", "80").strip() or "80"
    print(f"Derived local domain: {local_domain}")
    print(f"Hosts mapping: 127.0.0.1 {local_domain}")
    print(f"Public URL: http://{local_domain}:{port}/")


def public_url(host: str, port: str, slug: str | None = None) -> str:
    suffix = f"{slug}/" if slug else ""
    port_suffix = "" if port in ("", "80", "443") else f":{port}"
    return f"http://{host}{port_suffix}/{suffix}"


def csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as annotation_file:
            return list(csv.DictReader(annotation_file))
    except OSError as error:
        raise SystemExit(f"Unable to read {path}.") from error


def _registered_cohort_rows() -> list[dict[str, str]]:
    """Return the current registrations in the runtime manifest schema."""
    rows: list[dict[str, str]] = []
    for row in csv_rows(KIT_ANNOTATION):
        canonical_id = (row.get("directory") or "").strip()
        if canonical_id:
            rows.append(
                {
                    "group_id": "G1",
                    "dataset": "phishdecloaker",
                    "canonical_id": canonical_id,
                }
            )
    if DYNAPD_SELECTION.is_file():
        for row in csv_rows(DYNAPD_SELECTION):
            canonical_id = (row.get("canonical_id") or "").strip()
            if canonical_id:
                rows.append(
                    {
                        "group_id": "G1",
                        "dataset": "dynapd",
                        "canonical_id": canonical_id,
                    }
                )
    for group_id, annotation in (("G2", MANUAL_PHISHING), ("G3", MANUAL_BENIGN)):
        for row in csv_rows(annotation):
            canonical_id = (row.get("directory") or "").strip()
            if canonical_id:
                rows.append(
                    {
                        "group_id": group_id,
                        "dataset": "manual",
                        "canonical_id": canonical_id,
                    }
                )

    rows.sort(key=lambda row: (row["group_id"], row["dataset"], row["canonical_id"]))
    keys = [(row["dataset"], row["canonical_id"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise SystemExit("Registered datasets contain a duplicate cohort target.")
    return rows


def _cohort_csv_bytes(rows: list[dict[str, str]]) -> bytes:
    from io import StringIO

    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COHORT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _cohort_output_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    try:
        resolved.relative_to(CONFIG_ROOT.resolve())
    except ValueError as error:
        raise SystemExit("Frozen cohort must be written under config/ for Docker and Conda.") from error
    if resolved.suffix.lower() != ".csv":
        raise SystemExit("Frozen cohort filename must end in .csv.")
    return resolved


def freeze_cohort(output: str) -> None:
    """Write a deterministic snapshot of every currently registered target."""
    path = _cohort_output_path(output)
    rows = _registered_cohort_rows()
    content = _cohort_csv_bytes(rows)
    if path.exists():
        if path.read_bytes() == content:
            print(f"Frozen cohort already matches current registrations: {path}")
        else:
            raise SystemExit(
                f"Refusing to replace a different frozen cohort: {path}. "
                "Choose a new filename so the earlier experiment remains reproducible."
            )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        print(f"Wrote frozen cohort: {path}")

    counts = Counter(row["group_id"] for row in rows)
    digest = hashlib.sha256(content).hexdigest()
    print(" ".join(f"{group_id}={counts[group_id]}" for group_id in ("G1", "G2", "G3")))
    print(f"SHA256={digest}")
    print(f"Set PHISHGATE_COHORT_MANIFEST=/app/config/{path.name} in .env")


@dataclass(frozen=True)
class TargetRecord:
    group_id: str
    dataset: str
    canonical_id: str
    brand: str
    target_url: str
    slug_url: str
    page_type: str = ""
    popularity: str = ""
    tranco_rank: str = ""
    tranco_list_id: str = ""


def _record_rank(seed: str, purpose: str, record: TargetRecord) -> bytes:
    material = (
        f"{seed}:{purpose}:{record.group_id}:"
        f"{record.dataset}:{record.canonical_id}"
    )
    return hashlib.sha256(material.encode("utf-8")).digest()


def _record_stratum(record: TargetRecord) -> str:
    if record.group_id == "G1":
        return record.dataset
    if record.group_id == "G3":
        return f"{record.page_type}:{record.popularity}"
    return "all"


def select_experiment_subset(
    by_group: dict[str, list[TargetRecord]],
    master_seed: str,
    *,
    purpose: str,
    group_quotas: dict[str, int],
    stratum_quotas: dict[tuple[str, str], int] | None = None,
) -> tuple[dict[str, list[TargetRecord]], list[TargetRecord]]:
    """Select and order one reproducible, optionally stratified experiment subset."""
    selection_seed = derive_seed(master_seed, f"{purpose}-selection")
    stratum_quotas = stratum_quotas or {}
    selected: dict[str, list[TargetRecord]] = {}

    for group_id, quota in group_quotas.items():
        candidates = by_group.get(group_id, [])
        if len(candidates) < quota:
            raise SystemExit(
                f"{purpose} requires {quota} {group_id} targets, "
                f"but only {len(candidates)} are available."
            )

        chosen: list[TargetRecord] = []
        for (quota_group, stratum), stratum_quota in sorted(stratum_quotas.items()):
            if quota_group != group_id:
                continue
            stratum_candidates = [
                record for record in candidates if _record_stratum(record) == stratum
            ]
            if len(stratum_candidates) < stratum_quota:
                raise SystemExit(
                    f"{purpose} requires {stratum_quota} {group_id}/{stratum} targets, "
                    f"but only {len(stratum_candidates)} are available."
                )
            chosen.extend(
                sorted(
                    stratum_candidates,
                    key=lambda record: (
                        _record_rank(selection_seed, f"stratum:{stratum}", record),
                        record.dataset,
                        record.canonical_id,
                    ),
                )[:stratum_quota]
            )

        if len(chosen) > quota:
            raise ValueError(f"{purpose} stratum quotas exceed the {group_id} quota.")
        chosen_keys = {(record.dataset, record.canonical_id) for record in chosen}
        remaining = [
            record
            for record in candidates
            if (record.dataset, record.canonical_id) not in chosen_keys
        ]
        chosen.extend(
            sorted(
                remaining,
                key=lambda record: (
                    _record_rank(selection_seed, "fill", record),
                    record.dataset,
                    record.canonical_id,
                ),
            )[: quota - len(chosen)]
        )
        selected[group_id] = chosen

    order_seed = derive_seed(master_seed, f"{purpose}-order")
    combined = sorted(
        (record for records in selected.values() for record in records),
        key=lambda record: (
            _record_rank(order_seed, "order", record),
            record.group_id,
            record.dataset,
            record.canonical_id,
        ),
    )
    return selected, combined


def select_preliminary_records(
    by_group: dict[str, list[TargetRecord]],
    master_seed: str,
) -> tuple[dict[str, list[TargetRecord]], list[TargetRecord]]:
    """Select 50 development-only G1 targets, balanced across both sources."""
    return select_experiment_subset(
        by_group,
        master_seed,
        purpose="preliminary",
        group_quotas=PRELIMINARY_GROUP_QUOTAS,
        stratum_quotas={
            ("G1", "phishdecloaker"): 25,
            ("G1", "dynapd"): 25,
        },
    )


def select_main_g1_subset(
    evaluation_by_group: dict[str, list[TargetRecord]],
    master_seed: str,
) -> tuple[dict[str, list[TargetRecord]], list[TargetRecord]]:
    """Select the shared balanced 50-sample G1 auxiliary cohort."""
    return select_experiment_subset(
        evaluation_by_group,
        master_seed,
        purpose="auxiliary-g1-subset",
        group_quotas=AUXILIARY_GROUP_QUOTAS,
        stratum_quotas={
            ("G1", dataset): quota
            for dataset, quota in AUXILIARY_G1_DATASETS.items()
        },
    )


def build_evaluation_split(
    by_group: dict[str, list[TargetRecord]],
    development_records: list[TargetRecord],
    master_seed: str,
) -> tuple[dict[str, list[TargetRecord]], list[TargetRecord]]:
    """Return the full cohort minus the development-only records."""
    development_keys = {
        (record.dataset, record.canonical_id) for record in development_records
    }
    evaluation_by_group = {
        group_id: [
            record
            for record in records
            if (record.dataset, record.canonical_id) not in development_keys
        ]
        for group_id, records in by_group.items()
    }
    evaluation_seed = derive_seed(master_seed, "main-evaluation-order")
    evaluation_records = sorted(
        (
            record
            for records in evaluation_by_group.values()
            for record in records
        ),
        key=lambda record: (
            _record_rank(evaluation_seed, "order", record),
            record.group_id,
            record.dataset,
            record.canonical_id,
        ),
    )
    return evaluation_by_group, evaluation_records


def _validate_development_evaluation_split(
    by_group: dict[str, list[TargetRecord]],
    development_records: list[TargetRecord],
    evaluation_by_group: dict[str, list[TargetRecord]],
    evaluation_records: list[TargetRecord],
) -> None:
    development_keys = {
        (record.dataset, record.canonical_id) for record in development_records
    }
    evaluation_keys = {
        (record.dataset, record.canonical_id) for record in evaluation_records
    }
    full_keys = {
        (record.dataset, record.canonical_id)
        for records in by_group.values()
        for record in records
    }
    if development_keys & evaluation_keys:
        raise SystemExit("Development and evaluation cohorts overlap.")
    if development_keys | evaluation_keys != full_keys:
        raise SystemExit("Development and evaluation cohorts do not cover the full cohort.")

    counts = {
        group_id: len(evaluation_by_group.get(group_id, []))
        for group_id in EVALUATION_GROUP_COUNTS
    }
    if counts != EVALUATION_GROUP_COUNTS:
        raise SystemExit(
            f"Main evaluation requires group counts {EVALUATION_GROUP_COUNTS}, "
            f"found {counts}."
        )
    g1_counts = Counter(record.dataset for record in evaluation_by_group["G1"])
    if dict(g1_counts) != EVALUATION_G1_DATASETS:
        raise SystemExit(
            f"Main G1 requires source counts {EVALUATION_G1_DATASETS}, "
            f"found {dict(g1_counts)}."
        )


def _remove_obsolete_experiment_outputs() -> None:
    """Remove generated artifacts from retired experiment designs."""
    for legacy_subset in ("BASELINE", "MAX_STEPS", "CONTEXT_MODE"):
        path = SUBSET_ROOT / legacy_subset
        if path.is_dir():
            shutil.rmtree(path)
    for legacy_interaction_lists in (
        PRELIMINARY_ROOT / "interaction",
        EVALUATION_ROOT / "interaction",
    ):
        if legacy_interaction_lists.is_dir():
            shutil.rmtree(legacy_interaction_lists)
    for legacy_plan in (
        TARGET_ROOT / "PLANS" / "main-phishwalk-order.csv",
        TARGET_ROOT / "PLANS" / "baseline-subset-order.csv",
        TARGET_ROOT / "PLANS" / "challenge.csv",
        TARGET_ROOT / "PLANS" / "max-steps.csv",
        TARGET_ROOT / "PLANS" / "context-mode.csv",
    ):
        if legacy_plan.is_file():
            legacy_plan.unlink()


def _write_urls(path: Path, urls: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")


def _write_record_set(
    root: Path,
    selected: dict[str, list[TargetRecord]],
    combined: list[TargetRecord],
    *,
    dataset_splits: tuple[str, ...] = (),
) -> None:
    """Write one subset as runtime manifest, detailed records, and target URLs."""
    root.mkdir(parents=True, exist_ok=True)
    for stale_path in root.glob("*.txt"):
        stale_path.unlink()
    _write_urls(root / "target.txt", [record.target_url for record in combined])
    for group_id, records in selected.items():
        _write_urls(root / f"{group_id}.txt", [record.target_url for record in records])
    for dataset in dataset_splits:
        _write_urls(
            root / f"{dataset}.txt",
            [record.target_url for record in combined if record.dataset == dataset],
        )
    with (root / "records.csv").open("w", encoding="utf-8", newline="") as output:
        columns = tuple(TargetRecord.__dataclass_fields__)
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(record.__dict__ for record in combined)
    with (root / "manifest.csv").open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=COHORT_COLUMNS)
        writer.writeheader()
        writer.writerows(
            {
                "group_id": record.group_id,
                "dataset": (
                    "manual" if record.dataset.startswith("manual_") else record.dataset
                ),
                "canonical_id": record.canonical_id,
            }
            for record in sorted(
                combined,
                key=lambda item: (item.group_id, item.dataset, item.canonical_id),
            )
        )


def _validate_benchmark_cohort(by_group: dict[str, list[TargetRecord]]) -> None:
    counts = {group_id: len(by_group.get(group_id, [])) for group_id in EXPECTED_GROUP_COUNTS}
    if counts != EXPECTED_GROUP_COUNTS:
        raise SystemExit(
            f"PhishGate-Bench requires group counts {EXPECTED_GROUP_COUNTS}, found {counts}."
        )

    g1_counts = Counter(record.dataset for record in by_group["G1"])
    if dict(g1_counts) != EXPECTED_G1_DATASETS:
        raise SystemExit(
            f"G1 requires source counts {EXPECTED_G1_DATASETS}, found {dict(g1_counts)}."
        )

    g3_counts = Counter(
        (record.page_type, record.popularity) for record in by_group["G3"]
    )
    if dict(g3_counts) != EXPECTED_G3_STRATA:
        raise SystemExit(
            f"G3 requires 2x2 counts {EXPECTED_G3_STRATA}, found {dict(g3_counts)}."
        )
    tranco_lists = {record.tranco_list_id for record in by_group["G3"] if record.tranco_list_id}
    if len(tranco_lists) != 1:
        raise SystemExit(f"G3 must use one frozen Tranco list, found {sorted(tranco_lists)}.")
    for record in by_group["G3"]:
        try:
            rank = int(record.tranco_rank)
        except ValueError as error:
            raise SystemExit(
                f"G3 target {record.canonical_id} has no valid Tranco rank."
            ) from error
        valid = (
            record.popularity == "popular" and 1 <= rank <= 5_000
        ) or (
            record.popularity == "long_tail" and 5_001 <= rank <= 1_000_000
        )
        if not valid:
            raise SystemExit(
                f"G3 target {record.canonical_id} has inconsistent popularity/rank metadata."
            )


def _profile(profile_id: str):
    from app.profiles import load_active_profile

    previous_profile = os.environ.get("PHISHGATE_PROFILE")
    previous_config = os.environ.get("PHISHGATE_CONFIG")
    os.environ["PHISHGATE_PROFILE"] = profile_id
    os.environ["PHISHGATE_CONFIG"] = str(ROOT / "config" / "profiles.yaml")
    try:
        return load_active_profile()
    finally:
        if previous_profile is None:
            os.environ.pop("PHISHGATE_PROFILE", None)
        else:
            os.environ["PHISHGATE_PROFILE"] = previous_profile
        if previous_config is None:
            os.environ.pop("PHISHGATE_CONFIG", None)
        else:
            os.environ["PHISHGATE_CONFIG"] = previous_config


def build_benchmark_variants(
    by_group: dict[str, list[TargetRecord]],
    master_seed: str,
) -> list[dict[str, str]]:
    """Return Original plus one gated variant per evaluation family for each sample.

    Click, Interaction, and Challenge each use one pooled profile whose templates
    are balanced independently within every research group.
    """
    from app.research_groups import TargetKey
    from app.template_assignment import build_balanced_assignment

    variants: list[dict[str, str]] = []
    for group_id in ("G1", "G2", "G3"):
        for record in by_group[group_id]:
            variants.append(
                {
                    "variant_id": f"{record.dataset}:{record.canonical_id}:original",
                    "group_id": group_id,
                    "dataset": record.dataset,
                    "canonical_id": record.canonical_id,
                    "condition": "original",
                    "evaluation_family": "original",
                    "profile_id": "baseline",
                    "gate_type": "",
                    "template_id": "",
                    "target_url": record.target_url,
                }
            )

    assignment_seed = derive_seed(master_seed, "assignment")

    def _targets(records: list[TargetRecord]) -> tuple:
        return tuple(
            TargetKey(
                "manual" if record.dataset.startswith("manual_") else record.dataset,
                record.canonical_id,
            )
            for record in records
        )

    for family in GATED_FAMILIES:
        profile = _profile(family)
        if len(profile.gates) != 1:
            raise SystemExit(
                f"Benchmark family {family} must map to a one-gate profile."
            )
        stage = profile.gates[0]
        for group_id in ("G1", "G2", "G3"):
            records = by_group[group_id]
            targets = _targets(records)
            assignments = build_balanced_assignment(
                seed=assignment_seed,
                gate_type=stage.gate_type,
                group_id=group_id,
                targets=targets,
                templates=stage.templates,
            )
            for record, target in zip(records, targets, strict=True):
                template_id = assignments[target].template_id
                variants.append(
                    {
                        "variant_id": f"{record.dataset}:{record.canonical_id}:{family}",
                        "group_id": group_id,
                        "dataset": record.dataset,
                        "canonical_id": record.canonical_id,
                        "condition": "gated",
                        "evaluation_family": family,
                        "profile_id": family,
                        "gate_type": stage.gate_type,
                        "template_id": template_id,
                        "target_url": record.target_url,
                    }
                )
    return variants


def _write_benchmark_manifest(
    by_group: dict[str, list[TargetRecord]],
    master_seed: str,
) -> list[dict[str, str]]:
    variants = build_benchmark_variants(by_group, master_seed)
    BENCHMARK_ROOT.mkdir(parents=True, exist_ok=True)
    columns = (
        "variant_id", "group_id", "dataset", "canonical_id", "condition",
        "evaluation_family", "profile_id", "gate_type", "template_id", "target_url",
    )
    with (BENCHMARK_ROOT / "manifest.csv").open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(variants)
    for family in ("original", *GATED_FAMILIES):
        _write_urls(
            BENCHMARK_ROOT / f"{family}.txt",
            [row["target_url"] for row in variants if row["evaluation_family"] == family],
        )
    return variants


def _write_condition_order(
    path: Path,
    records_by_group: dict[str, list[TargetRecord]],
    master_seed: str,
    *,
    purpose: str,
    conditions: tuple[str, ...] = MAIN_PROFILES,
) -> None:
    """Write a balanced crossover order for Original and gated conditions."""
    seed = derive_seed(master_seed, f"{purpose}-condition-order")
    rows: list[dict[str, str | int]] = []
    for group_id, records in records_by_group.items():
        ordered = sorted(
            records,
            key=lambda record: (
                _record_rank(seed, "sample", record),
                record.dataset,
                record.canonical_id,
            ),
        )
        base = sorted(
            conditions,
            key=lambda condition: hashlib.sha256(
                f"{seed}:{group_id}:{condition}".encode()
            ).digest(),
        )
        for index, record in enumerate(ordered):
            rotation = index % len(base)
            sequence = base[rotation:] + base[:rotation]
            rows.append(
                {
                    "group_id": group_id,
                    "dataset": record.dataset,
                    "canonical_id": record.canonical_id,
                    "condition_order": ">".join(sequence),
                }
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=("group_id", "dataset", "canonical_id", "condition_order"),
        )
        writer.writeheader()
        writer.writerows(rows)


def build_domain_style_plan(
    records: list[TargetRecord],
    variants: list[dict[str, str]],
    master_seed: str,
    port: str,
) -> list[dict[str, str | int]]:
    """Build the additional hash-style Original/Click runs.

    The pronounceable rows are reused from the main experiment.
    """
    if any(record.group_id != "G1" for record in records):
        raise ValueError("Domain-style ablation accepts G1 records only.")

    profile = _profile(DOMAIN_STYLE_ABLATION_PROFILE)
    if len(profile.gates) != 1 or profile.gates[0].gate_type != "click":
        raise SystemExit("Domain-style ablation profile must contain one Click gate.")
    stage = profile.gates[0]
    variant_index = _variant_index(variants)
    route_seed = derive_seed(master_seed, "route")
    rows: list[dict[str, str | int]] = []
    for style in DOMAIN_STYLE_ABLATION_STYLES:
        host = derive_local_domain(master_seed, style)
        if host is None:
            raise SystemExit(f"Domain style {style} did not produce a local hostname.")
        for record in records:
            if record.dataset == "phishdecloaker":
                slug = derive_kit_slug(route_seed, record.canonical_id)
            elif record.dataset == "dynapd":
                slug = derive_dynapd_slug(route_seed, record.canonical_id)
            else:
                raise ValueError(
                    f"Unsupported G1 dataset for domain-style ablation: {record.dataset}"
                )
            target_url = public_url(host, port, slug)
            for condition, family, profile_id, gate_type, template_id in (
                ("original", "original", "baseline", "", ""),
                (
                    "gated",
                    "click",
                    DOMAIN_STYLE_ABLATION_PROFILE,
                    stage.gate_type,
                    variant_index[
                        (record.dataset, record.canonical_id, "click")
                    ]["template_id"],
                ),
            ):
                rows.append(
                    {
                        "run_id": (
                            f"{record.dataset}:{record.canonical_id}:"
                            f"{style}:{profile_id}"
                        ),
                        "detector": "phishwalk",
                        "PHISHGATE_EXPERIMENT_MANIFEST": AUXILIARY_RUNTIME_MANIFEST,
                        "group_id": record.group_id,
                        "dataset": record.dataset,
                        "canonical_id": record.canonical_id,
                        "domain_style": style,
                        "condition": condition,
                        "evaluation_family": family,
                        "profile_id": profile_id,
                        "gate_type": gate_type,
                        "template_id": template_id,
                        "target_url": target_url,
                    }
                )

    order_seed = derive_seed(master_seed, "domain-style-run-order")
    rows.sort(
        key=lambda row: hashlib.sha256(
            f"{order_seed}:{row['run_id']}".encode("utf-8")
        ).digest()
    )
    for run_order, row in enumerate(rows, start=1):
        row["run_order"] = run_order
    return rows


def _write_domain_style_plan(
    path: Path,
    records: list[TargetRecord],
    variants: list[dict[str, str]],
    master_seed: str,
    port: str,
) -> list[dict[str, str | int]]:
    rows = build_domain_style_plan(records, variants, master_seed, port)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = (
        "run_order",
        "run_id",
        "detector",
        "PHISHGATE_EXPERIMENT_MANIFEST",
        "group_id",
        "dataset",
        "canonical_id",
        "domain_style",
        "condition",
        "evaluation_family",
        "profile_id",
        "gate_type",
        "template_id",
        "target_url",
    )
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def _ordered_runs(
    rows: list[dict[str, str | int]],
    master_seed: str,
    purpose: str,
) -> list[dict[str, str | int]]:
    """Apply one reproducible execution order to complete run rows."""
    order_seed = derive_seed(master_seed, f"{purpose}-run-order")
    rows.sort(
        key=lambda row: hashlib.sha256(
            f"{order_seed}:{row['run_id']}".encode("utf-8")
        ).digest()
    )
    for run_order, row in enumerate(rows, start=1):
        row["run_order"] = run_order
    return rows


def _variant_index(
    variants: list[dict[str, str]],
) -> dict[tuple[str, str, str], dict[str, str]]:
    # Keyed by evaluation_family (original/click/interaction/challenge); there is
    # exactly one variant per sample per family.
    return {
        (row["dataset"], row["canonical_id"], row["evaluation_family"]): row
        for row in variants
    }


_VARIANT_COPY_KEYS = (
    "group_id",
    "dataset",
    "canonical_id",
    "evaluation_family",
    "profile_id",
    "gate_type",
    "template_id",
    "target_url",
)


def build_preliminary_plan(
    preliminary_by_group: dict[str, list[TargetRecord]],
    master_seed: str,
) -> list[dict[str, str | int]]:
    """Build 50 samples x 3 gated families x 6 models = 900 runs."""
    variants = build_benchmark_variants(
        {"G1": preliminary_by_group["G1"], "G2": [], "G3": []},
        master_seed,
    )
    rows: list[dict[str, str | int]] = []
    for variant in variants:
        if variant["evaluation_family"] not in PRELIMINARY_FAMILIES:
            continue
        for model_pool, model_id in PRELIMINARY_MODELS:
            rows.append(
                {
                    "run_id": f"preliminary:{variant['variant_id']}:{model_id}",
                    "detector": "phishwalk",
                    "PHISHGATE_EXPERIMENT_MANIFEST": PRELIMINARY_RUNTIME_MANIFEST,
                    "model_pool": model_pool,
                    "model_id": model_id,
                    **{key: variant[key] for key in _VARIANT_COPY_KEYS},
                }
            )
    return _ordered_runs(rows, master_seed, "preliminary")


def build_main_plan(
    variants: list[dict[str, str]],
    master_seed: str,
) -> list[dict[str, str | int]]:
    """Build MAIN: 10 comparative + 6 controlled gate-family runs/sample."""
    rows: list[dict[str, str | int]] = []
    for variant in variants:
        family = variant["evaluation_family"]
        if family in COMPARATIVE_FAMILIES:
            detectors = MAIN_DETECTORS
        elif family in CONTROLLED_GATE_FAMILIES:
            detectors = CONTROLLED_ANALYSIS_DETECTORS
        else:
            continue
        for detector in detectors:
            rows.append(
                {
                    "run_id": f"main:{variant['variant_id']}:{detector}",
                    "detector": detector,
                    "PHISHGATE_EXPERIMENT_MANIFEST": EVALUATION_RUNTIME_MANIFEST,
                    **{key: variant[key] for key in _VARIANT_COPY_KEYS},
                }
            )
    return _ordered_runs(rows, master_seed, "main")


def build_aux_reference_plan(
    records: list[TargetRecord],
    variants: list[dict[str, str]],
    master_seed: str,
) -> list[dict[str, str | int]]:
    """Build 50 PhishWalk Original + 50 Click x controlled trio = 200."""
    index = _variant_index(variants)
    rows: list[dict[str, str | int]] = []
    for record in records:
        for family, detectors in (
            ("original", ("phishwalk",)),
            ("click", CONTROLLED_ANALYSIS_DETECTORS),
        ):
            variant = index[(record.dataset, record.canonical_id, family)]
            for detector in detectors:
                rows.append(
                    {
                        "run_id": (
                            f"aux-reference:{record.dataset}:{record.canonical_id}:"
                            f"{family}:{detector}"
                        ),
                        "detector": detector,
                        "PHISHGATE_EXPERIMENT_MANIFEST": AUXILIARY_RUNTIME_MANIFEST,
                        "context_mode": "neutral",
                        "domain_style": MAIN_DOMAIN_STYLE,
                        **{key: variant[key] for key in _VARIANT_COPY_KEYS},
                    }
                )
    return _ordered_runs(rows, master_seed, "aux-reference")


def build_context_mode_plan(
    records: list[TargetRecord],
    variants: list[dict[str, str]],
    master_seed: str,
    runtime_manifest: str = AUXILIARY_RUNTIME_MANIFEST,
) -> list[dict[str, str | int]]:
    """Build paired Click context runs for the supplied records."""
    index = _variant_index(variants)
    rows: list[dict[str, str | int]] = []
    for record in records:
        variant = index[(record.dataset, record.canonical_id, "click")]
        for context_mode in CONTEXT_MODES:
            for detector in CONTROLLED_ANALYSIS_DETECTORS:
                rows.append(
                    {
                        "run_id": (
                            f"context-mode:{record.dataset}:{record.canonical_id}:"
                            f"{context_mode}:{detector}"
                        ),
                        "detector": detector,
                        "PHISHGATE_EXPERIMENT_MANIFEST": runtime_manifest,
                        "context_mode": context_mode,
                        **{key: variant[key] for key in _VARIANT_COPY_KEYS},
                    }
                )
    return _ordered_runs(rows, master_seed, "context-mode")


def _write_run_plan(path: Path, rows: list[dict[str, str | int]]) -> None:
    if not rows:
        raise ValueError(f"Run plan is empty: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ("run_order",) + tuple(key for key in rows[0] if key != "run_order")
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _manifest_path(
    env: dict[str, str],
    variable: str = "PHISHGATE_EXPERIMENT_MANIFEST",
) -> Path | None:
    configured = env.get(variable, "").strip()
    if not configured:
        return None
    if configured.startswith("/app/config/"):
        return ROOT / "config" / Path(configured).name
    if configured.startswith("/app/targets/"):
        relative = Path(configured).relative_to("/app/targets")
        return TARGET_ROOT / relative
    path = Path(configured).expanduser()
    return path if path.is_absolute() else ROOT / path


def _cohort_manifest_path(env: dict[str, str]) -> Path | None:
    """Return the frozen preparation pool, with legacy fallback."""
    if env.get("PHISHGATE_COHORT_MANIFEST", "").strip():
        return _manifest_path(env, "PHISHGATE_COHORT_MANIFEST")
    return _manifest_path(env)


def _selected_keys(
    env: dict[str, str],
    available: dict[tuple[str, str], str],
) -> dict[str, list[tuple[str, str]]]:
    groups = {"G1": [], "G2": [], "G3": []}
    manifest = _cohort_manifest_path(env)
    if manifest is None:
        for key in available:
            dataset, _ = key
            group_id = "G1" if dataset in {"phishdecloaker", "dynapd"} else (
                "G2" if dataset == "manual_phishing" else "G3"
            )
            groups[group_id].append(key)
        return groups

    seen: set[tuple[str, str]] = set()
    for row_number, row in enumerate(csv_rows(manifest), start=2):
        group_id = (row.get("group_id") or "").strip()
        dataset = (row.get("dataset") or "").strip()
        canonical_id = (row.get("canonical_id") or "").strip()
        if dataset == "manual":
            matching = [
                key for key in available if key[1] == canonical_id and key[0].startswith("manual_")
            ]
            if len(matching) != 1:
                raise SystemExit(f"Unknown manual target on manifest row {row_number}: {canonical_id}")
            key = matching[0]
        else:
            key = (dataset, canonical_id)
        if group_id not in groups or key not in available:
            raise SystemExit(f"Invalid experiment target on manifest row {row_number}: {row}")
        expected_group = "G1" if key[0] in {"phishdecloaker", "dynapd"} else (
            "G2" if key[0] == "manual_phishing" else "G3"
        )
        if group_id != expected_group:
            raise SystemExit(f"Mismatched group on manifest row {row_number}: {row}")
        if key in seen:
            raise SystemExit(f"Duplicate experiment target on manifest row {row_number}: {row}")
        seen.add(key)
        groups[group_id].append(key)
    return groups


def generate_group_targets() -> None:
    env = read_env()
    master_seed = require_seed(env)
    route_seed = derive_seed(master_seed, "route")
    style = env.get("PHISHGATE_DOMAIN_STYLE", "off").strip() or "off"
    if style != MAIN_DOMAIN_STYLE:
        raise SystemExit(
            "PhishGate-Bench main preparation requires "
            f"PHISHGATE_DOMAIN_STYLE={MAIN_DOMAIN_STYLE}; found {style!r}. "
            "The hash style is generated separately by the domain-style ablation plan."
        )
    try:
        local_domain = derive_local_domain(master_seed, style)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    local_host = (
        local_domain
        or env.get("PHISHGATE_HOST", "127.0.0.1").strip()
        or "127.0.0.1"
    )
    slug_smoke_host = env.get("PHISHGATE_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = env.get("PHISHGATE_PORT", "80").strip() or "80"
    available: dict[tuple[str, str], str] = {}
    manual_hosts: dict[tuple[str, str], str] = {}
    manual_metadata: dict[tuple[str, str], dict[str, str]] = {}

    for row in csv_rows(KIT_ANNOTATION):
        canonical_id = (row.get("directory") or "").strip()
        if canonical_id:
            available[("phishdecloaker", canonical_id)] = (row.get("brand") or "").strip()
    if DYNAPD_SELECTION.is_file():
        for row in csv_rows(DYNAPD_SELECTION):
            canonical_id = (row.get("canonical_id") or "").strip()
            if canonical_id:
                available[("dynapd", canonical_id)] = (row.get("brand") or "").strip()
    else:
        print("DynaPD selection is not ready; generating G1 from PhishDecloaker only.")
    for dataset, annotation in (
        ("manual_phishing", MANUAL_PHISHING),
        ("manual_benign", MANUAL_BENIGN),
    ):
        for row in csv_rows(annotation):
            canonical_id = (row.get("directory") or "").strip()
            hostname = urlparse((row.get("source_url") or "").strip()).hostname
            if canonical_id and hostname:
                key = (dataset, canonical_id)
                available[key] = (row.get("brand") or "").strip()
                manual_hosts[key] = hostname.lower()
                manual_metadata[key] = row

    groups = _selected_keys(env, available)
    records: list[TargetRecord] = []
    for group_id, keys in groups.items():
        for dataset, canonical_id in keys:
            if dataset == "phishdecloaker":
                slug = derive_kit_slug(route_seed, canonical_id)
                target_url = public_url(local_host, port, slug)
                slug_url = target_url
            elif dataset == "dynapd":
                slug = derive_dynapd_slug(route_seed, canonical_id)
                target_url = public_url(local_host, port, slug)
                slug_url = target_url
            else:
                slug = derive_manual_slug(route_seed, canonical_id)
                target_url = public_url(manual_hosts[(dataset, canonical_id)], port)
                slug_url = public_url(slug_smoke_host, port, slug)
            metadata = manual_metadata.get((dataset, canonical_id), {})
            records.append(
                TargetRecord(
                    group_id=group_id,
                    dataset=dataset,
                    canonical_id=canonical_id,
                    brand=available[(dataset, canonical_id)],
                    target_url=target_url,
                    slug_url=slug_url,
                    page_type=(metadata.get("page_type") or "").strip(),
                    popularity=(metadata.get("popularity") or "").strip(),
                    tranco_rank=(metadata.get("tranco_rank") or "").strip(),
                    tranco_list_id=(metadata.get("tranco_list_id") or "").strip(),
                )
            )

    records.sort(key=lambda record: (record.group_id, record.dataset, record.canonical_id))
    by_group = {group_id: [r for r in records if r.group_id == group_id] for group_id in groups}
    _validate_benchmark_cohort(by_group)
    g1 = by_group["G1"]
    _write_urls(TARGET_ROOT / "G1" / "target.txt", [r.target_url for r in g1])
    for dataset in ("phishdecloaker", "dynapd"):
        _write_urls(
            TARGET_ROOT / "G1" / f"{dataset}.txt",
            [r.target_url for r in g1 if r.dataset == dataset],
        )
    for group_id in ("G2", "G3"):
        _write_urls(
            TARGET_ROOT / group_id / "target.txt",
            [r.target_url for r in by_group[group_id]],
        )
        _write_urls(
            TARGET_ROOT / group_id / "slug.txt",
            [r.slug_url for r in by_group[group_id]],
        )

    manifest_path = TARGET_ROOT / "manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as manifest_file:
        columns = tuple(TargetRecord.__dataclass_fields__)
        writer = csv.DictWriter(manifest_file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(record.__dict__ for record in records)

    configured_manifest = _cohort_manifest_path(env)
    cohort_receipt: dict[str, object] = {
        "schema_version": 1,
        "frozen": configured_manifest is not None,
        "group_counts": {
            group_id: len(by_group[group_id]) for group_id in ("G1", "G2", "G3")
        },
    }
    if configured_manifest is not None:
        try:
            manifest_bytes = configured_manifest.read_bytes()
        except OSError as error:
            raise SystemExit(f"Unable to read {configured_manifest}.") from error
        cohort_receipt.update(
            {
                "manifest": configured_manifest.name,
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            }
        )
    else:
        print(
            "WARNING: PHISHGATE_COHORT_MANIFEST is unset; generated plans are "
            "a reproducible preview, not a frozen experiment cohort."
        )
    (TARGET_ROOT / "cohort.json").write_text(
        json.dumps(cohort_receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    _remove_obsolete_experiment_outputs()

    preliminary_by_group, preliminary_records = select_preliminary_records(by_group, master_seed)
    _write_record_set(
        PRELIMINARY_ROOT,
        preliminary_by_group,
        preliminary_records,
        dataset_splits=("phishdecloaker", "dynapd"),
    )

    evaluation_by_group, evaluation_records = build_evaluation_split(
        by_group,
        preliminary_records,
        master_seed,
    )
    _validate_development_evaluation_split(
        by_group,
        preliminary_records,
        evaluation_by_group,
        evaluation_records,
    )
    _write_record_set(
        EVALUATION_ROOT,
        evaluation_by_group,
        evaluation_records,
        dataset_splits=("phishdecloaker", "dynapd"),
    )

    auxiliary_by_group, auxiliary_records = select_main_g1_subset(
        evaluation_by_group,
        master_seed,
    )
    for subset_name in ("AUX_G1", "DOMAIN_STYLE"):
        _write_record_set(
            SUBSET_ROOT / subset_name,
            auxiliary_by_group,
            auxiliary_records,
            dataset_splits=("phishdecloaker", "dynapd"),
        )

    variants = _write_benchmark_manifest(evaluation_by_group, master_seed)
    auxiliary_variants = build_benchmark_variants(
        {"G1": auxiliary_by_group["G1"], "G2": [], "G3": []},
        master_seed,
    )
    _write_condition_order(
        TARGET_ROOT / "PLANS" / "main-eval-order.csv",
        evaluation_by_group,
        master_seed,
        purpose="main-evaluation",
    )
    domain_style_plan_path = TARGET_ROOT / "PLANS" / "domain-style-click.csv"
    domain_style_runs = _write_domain_style_plan(
        domain_style_plan_path,
        auxiliary_records,
        auxiliary_variants,
        master_seed,
        port,
    )

    plan_root = TARGET_ROOT / "PLANS"
    run_plans = {
        "main": build_main_plan(variants, master_seed),
        "preliminary": build_preliminary_plan(preliminary_by_group, master_seed),
        "aux_reference": build_aux_reference_plan(
            auxiliary_records, auxiliary_variants, master_seed
        ),
    }
    expected_run_counts = {
        "main": 7_200,
        "preliminary": 900,
        "aux_reference": 200,
    }
    actual_run_counts = {name: len(rows) for name, rows in run_plans.items()}
    if actual_run_counts != expected_run_counts:
        raise SystemExit(
            f"Experiment run budgets do not match the design: {actual_run_counts}"
        )
    run_plan_paths = {
        name: plan_root / f"{name.replace('_', '-')}.csv"
        for name in run_plans
    }
    for name, rows in run_plans.items():
        _write_run_plan(run_plan_paths[name], rows)

    receipt_artifacts = (
        BENCHMARK_ROOT / "manifest.csv",
        PRELIMINARY_ROOT / "manifest.csv",
        EVALUATION_ROOT / "manifest.csv",
        SUBSET_ROOT / "AUX_G1" / "manifest.csv",
        SUBSET_ROOT / "DOMAIN_STYLE" / "manifest.csv",
        TARGET_ROOT / "PLANS" / "main-eval-order.csv",
        domain_style_plan_path,
        *run_plan_paths.values(),
    )

    template_counts = Counter(
        (row["group_id"], row["evaluation_family"], row["template_id"])
        for row in variants
        if row["condition"] == "gated"
    )
    family_counts = Counter(
        row["evaluation_family"] for row in variants if row["condition"] == "gated"
    )
    plan_receipt = {
        "schema_version": 8,
        "cohort": cohort_receipt,
        "full_cohort_samples": len(records),
        "development_samples": len(preliminary_records),
        "source_samples": len(evaluation_records),
        "original_variants": sum(row["condition"] == "original" for row in variants),
        "gated_variants": sum(row["condition"] == "gated" for row in variants),
        "subsets": {
            "preliminary": {
                "total": len(preliminary_records),
                "groups": PRELIMINARY_GROUP_QUOTAS,
            },
            "evaluation": {
                "total": len(evaluation_records),
                "groups": EVALUATION_GROUP_COUNTS,
            },
            "domain_style": {"total": len(auxiliary_records), "groups": {"G1": 50}},
        },
        "run_budget": {
            "main": len(run_plans["main"]),
            "preliminary": len(run_plans["preliminary"]),
            "aux_reference": len(run_plans["aux_reference"]),
            "domain_style": len(domain_style_runs),
            "total": sum(len(rows) for rows in run_plans.values()) + len(domain_style_runs),
        },
        "evaluation_families": {
            "comparative": list(COMPARATIVE_FAMILIES),
            "controlled_gate_family": list(CONTROLLED_GATE_FAMILIES),
        },
        "gated_family_variants": dict(sorted(family_counts.items())),
        "preliminary_model_pools": {
            pool: [
                model_id
                for candidate_pool, model_id in PRELIMINARY_MODELS
                if candidate_pool == pool
            ]
            for pool in sorted({pool for pool, _ in PRELIMINARY_MODELS})
        },
        "main_detectors": list(MAIN_DETECTORS),
        "detector_roles": {
            "external_baselines": list(EXTERNAL_DETECTORS),
            "controlled_baselines": ["one_shot", "generic"],
            "proposed": ["phishwalk"],
        },
        "analysis_sets": {
            "controlled_gate_family": list(CONTROLLED_ANALYSIS_DETECTORS),
        },
        "main_domain_style": MAIN_DOMAIN_STYLE,
        "recommended_runtime_manifest": "/app/targets/EVAL/manifest.csv",
        "domain_style_gate_profile": DOMAIN_STYLE_ABLATION_PROFILE,
        "artifact_sha256": {
            str(path.relative_to(TARGET_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in receipt_artifacts
        },
        "notes": [
            "G1 subsets are balanced across PhishDecloaker and DynaPD where the quota is even.",
            "PRELIM contains only development G1 targets, split 25/25 by source dataset.",
            "EVAL excludes every PRELIM target; Comparative (Original+Click) runs all five detectors.",
            "Controlled gate-family analysis runs One-shot, Generic, and PhishWalk on Interaction+Challenge.",
            "Interaction uses one pooled profile with five evenly assigned templates.",
            "AUX_REFERENCE and Domain-style share one main-EVAL G1 subset split 25/25 by source.",
            "Domain-style ablation adds hash Original/Click; pronounceable rows reuse AUX_REFERENCE.",
        ],
        "template_counts": {
            f"{group_id}/{family}/{template_id}": count
            for (group_id, family, template_id), count in sorted(template_counts.items())
        },
    }
    (TARGET_ROOT / "experiment.json").write_text(
        json.dumps(plan_receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    for group_id in ("G1", "G2", "G3"):
        counts = Counter(record.dataset for record in by_group[group_id])
        detail = " ".join(f"{dataset}={count}" for dataset, count in sorted(counts.items()))
        print(f"{group_id} total={len(by_group[group_id])} {detail}".rstrip())
    preliminary_sources = Counter(record.dataset for record in preliminary_records)
    preliminary_detail = " ".join(
        f"{dataset}={preliminary_sources[dataset]}"
        for dataset in ("phishdecloaker", "dynapd")
    )
    print(f"PRELIM total={len(preliminary_records)} {preliminary_detail}")
    evaluation_sources = Counter(record.dataset for record in evaluation_by_group["G1"])
    print(
        f"EVAL total={len(evaluation_records)} "
        f"G1={len(evaluation_by_group['G1'])} "
        f"G2={len(evaluation_by_group['G2'])} "
        f"G3={len(evaluation_by_group['G3'])} "
        f"phishdecloaker={evaluation_sources['phishdecloaker']} "
        f"dynapd={evaluation_sources['dynapd']}"
    )
    print(
        f"BENCH originals={plan_receipt['original_variants']} "
        f"gated={plan_receipt['gated_variants']}"
    )
    print("SUBSETS AUX_G1=50 shared by aux_reference and domain_style")
    print(
        f"DOMAIN_STYLE runs={len(domain_style_runs)} "
        f"gate={DOMAIN_STYLE_ABLATION_PROFILE}"
    )
    print(
        "RUN_PLANS "
        + " ".join(f"{name}={count}" for name, count in actual_run_counts.items())
    )
    print(f"wrote group targets under {TARGET_ROOT}")


def verify_completed_experiment_artifacts(*, required: bool = True) -> None:
    """Fail if any artifact recorded by the completed experiment has drifted."""
    receipt_path = TARGET_ROOT / "experiment.json"
    if not receipt_path.is_file() and not required:
        return
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Unable to verify completed experiment receipt: {receipt_path}") from error
    mismatches = []
    for relative_path, expected in receipt.get("artifact_sha256", {}).items():
        path = TARGET_ROOT / relative_path
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
        if actual != expected:
            mismatches.append(f"{relative_path}: expected {expected}, found {actual}")
    if mismatches:
        raise SystemExit("Completed experiment artifacts have drifted:\n" + "\n".join(mismatches))


def load_frozen_evaluation_records() -> dict[str, list[TargetRecord]]:
    """Load EVAL records only when they exactly match its frozen runtime manifest."""
    manifest_path = EVALUATION_ROOT / "manifest.csv"
    records_path = EVALUATION_ROOT / "records.csv"
    manifest_rows = csv_rows(manifest_path)
    manifest_keys = {
        (row["group_id"], row["dataset"], row["canonical_id"])
        for row in manifest_rows
    }
    groups = {"G1": [], "G2": [], "G3": []}
    for row in csv_rows(records_path):
        record = TargetRecord(
            **{name: row.get(name, "") for name in TargetRecord.__dataclass_fields__}
        )
        runtime_dataset = "manual" if record.dataset.startswith("manual_") else record.dataset
        key = (record.group_id, runtime_dataset, record.canonical_id)
        if key not in manifest_keys:
            raise SystemExit(f"EVAL record is absent from its frozen manifest: {key}")
        if not record.brand.strip():
            raise SystemExit(
                f"Context experiment requires a brand: {record.dataset}/{record.canonical_id}"
            )
        groups[record.group_id].append(record)
    if sum(map(len, groups.values())) != len(manifest_keys):
        raise SystemExit("EVAL records and manifest do not contain the same cohort.")
    return groups


def select_standalone_context_records(
    evaluation_by_group: dict[str, list[TargetRecord]],
    master_seed: str,
) -> tuple[dict[str, list[TargetRecord]], list[TargetRecord]]:
    """Select G1/G2/G3 50 each, with balanced G1 sources and G3 margins."""
    diagonal_seed = derive_seed(master_seed, "standalone-context-g3-diagonal")
    diagonal = hashlib.sha256(diagonal_seed.encode("utf-8")).digest()[0] % 2
    g3_quotas = {
        "form:popular": 13 if diagonal == 0 else 12,
        "form:long_tail": 12 if diagonal == 0 else 13,
        "general:popular": 12 if diagonal == 0 else 13,
        "general:long_tail": 13 if diagonal == 0 else 12,
    }
    return select_experiment_subset(
        evaluation_by_group,
        master_seed,
        purpose="standalone-context",
        group_quotas={"G1": 50, "G2": 50, "G3": 50},
        stratum_quotas={
            ("G1", "phishdecloaker"): 25,
            ("G1", "dynapd"): 25,
            **{("G3", stratum): quota for stratum, quota in g3_quotas.items()},
        },
    )


def prepare_standalone_context_experiment() -> None:
    """Write only targets/CONTEXT while preserving every completed artifact."""
    env = read_env()
    master_seed = require_seed(env)
    verify_completed_experiment_artifacts()
    evaluation_by_group = load_frozen_evaluation_records()
    selected, records = select_standalone_context_records(
        evaluation_by_group, master_seed
    )
    _write_record_set(
        STANDALONE_CONTEXT_ROOT,
        selected,
        records,
        dataset_splits=("phishdecloaker", "dynapd"),
    )
    variants = build_benchmark_variants(selected, master_seed)
    runs = build_context_mode_plan(
        records,
        variants,
        master_seed,
        runtime_manifest=STANDALONE_CONTEXT_RUNTIME_MANIFEST,
    )
    if len(runs) != 900:
        raise SystemExit(f"Standalone Context run budget must be 900, found {len(runs)}.")
    run_plan_path = STANDALONE_CONTEXT_ROOT / "run-plan.csv"
    _write_run_plan(run_plan_path, runs)

    template_counts = Counter(
        (row["group_id"], row["template_id"])
        for row in variants
        if row["evaluation_family"] == "click"
    )
    g1_sources = Counter(record.dataset for record in selected["G1"])
    g3_strata = Counter(_record_stratum(record) for record in selected["G3"])
    artifacts = (
        STANDALONE_CONTEXT_ROOT / "manifest.csv",
        STANDALONE_CONTEXT_ROOT / "records.csv",
        run_plan_path,
    )
    receipt = {
        "schema_version": 1,
        "source": {
            "eval_manifest": "targets/EVAL/manifest.csv",
            "eval_manifest_sha256": hashlib.sha256(
                (EVALUATION_ROOT / "manifest.csv").read_bytes()
            ).hexdigest(),
        },
        "seed_sha256": hashlib.sha256(master_seed.encode("utf-8")).hexdigest(),
        "samples": {
            "total": len(records),
            "groups": {group_id: len(items) for group_id, items in selected.items()},
        },
        "g1_sources": dict(sorted(g1_sources.items())),
        "g3_strata": dict(sorted(g3_strata.items())),
        "template_counts": {
            f"{group_id}/{template_id}": count
            for (group_id, template_id), count in sorted(template_counts.items())
        },
        "run_budget": {
            "total": len(runs),
            "detectors": dict(sorted(Counter(row["detector"] for row in runs).items())),
            "contexts": dict(sorted(Counter(row["context_mode"] for row in runs).items())),
        },
        "artifact_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in artifacts
        },
    }
    (STANDALONE_CONTEXT_ROOT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    verify_completed_experiment_artifacts()
    print("CONTEXT samples=150 G1=50 G2=50 G3=50 runs=900")
    print(f"wrote standalone artifacts under {STANDALONE_CONTEXT_ROOT}")


def assignment_environment(env: dict[str, str], master_seed: str) -> None:
    os.environ["PHISHGATE_SEED"] = master_seed
    os.environ["PHISHGATE_PROFILE"] = env.get("PHISHGATE_PROFILE", "click").strip() or "click"
    os.environ["PHISHGATE_CONFIG"] = str(ROOT / "config" / "profiles.yaml")
    os.environ["PHISHGATE_BRAND_ANNOTATION"] = str(KIT_ANNOTATION)
    if DYNAPD_SELECTION.is_file():
        os.environ["PHISHGATE_DYNAPD_SELECTION"] = str(DYNAPD_SELECTION)
    else:
        os.environ.pop("PHISHGATE_DYNAPD_SELECTION", None)
    os.environ["PHISHGATE_MANUAL_ANNOTATION"] = str(ROOT / "data" / "manual_annotation.csv")
    os.environ["PHISHGATE_MANUAL_BENIGN_ANNOTATION"] = str(
        ROOT / "data" / "manual_benign_annotation.csv"
    )
    manifest = env.get("PHISHGATE_EXPERIMENT_MANIFEST", "").strip()
    if manifest.startswith("/app/config/"):
        manifest = str(ROOT / "config" / Path(manifest).name)
    elif manifest.startswith("/app/targets/"):
        relative = Path(manifest).relative_to("/app/targets")
        manifest = str(TARGET_ROOT / relative)
    if manifest:
        os.environ["PHISHGATE_EXPERIMENT_MANIFEST"] = manifest
    else:
        os.environ.pop("PHISHGATE_EXPERIMENT_MANIFEST", None)


def show_assignments_local() -> None:
    env = read_env()
    master_seed = require_seed(env)
    assignment_environment(env, master_seed)

    from app.profiles import load_active_profile
    from app.research_groups import group_catalog
    from app.template_assignment import build_balanced_assignment

    profile = load_active_profile()
    if not profile.gates:
        print(f"{profile.profile_id}: baseline profile has no template assignment")
        return
    if len(profile.gates) != 1:
        raise SystemExit("Assignment audit supports single-stage experiment profiles only.")

    stage = profile.gates[0]
    assignment_seed = derive_seed(master_seed, "assignment")
    print(f"profile={profile.profile_id} gate_type={stage.gate_type}")
    for group_id, targets in group_catalog().items():
        assignment = build_balanced_assignment(
            seed=assignment_seed,
            gate_type=stage.gate_type,
            group_id=group_id,
            targets=targets,
            templates=stage.templates,
        )
        counts = Counter(template.template_id for template in assignment.values())
        summary = " ".join(
            f"{template.template_id}={counts[template.template_id]}" for template in stage.templates
        )
        print(f"{group_id} total={len(targets)} {summary}")


def show_assignments() -> None:
    if sys.version_info < (3, 10):
        show_assignments_container()
        return
    try:
        show_assignments_local()
    except ModuleNotFoundError as error:
        if error.name != "yaml":
            raise
        show_assignments_container()


def show_assignments_container() -> None:
    print("Using the backend container for the assignment audit.")
    subprocess.run(
        (
            "docker", "compose", "run", "--build", "--rm", "--no-deps",
            "--volume", f"{ROOT}:/workspace:ro", "--workdir", "/workspace",
            "backend-local", "python", "scripts/prepare_experiment.py",
            "--assignments-only",
        ),
        cwd=ROOT,
        check=True,
    )


def run_step(number: int, total: int, title: str, action: Callable[[], None]) -> None:
    print(f"\n[{number}/{total}] {title}", flush=True)
    action()


def main() -> None:
    require_seed(read_env())
    verify_completed_experiment_artifacts(required=False)
    steps: tuple[tuple[str, Callable[[], None]], ...] = (
        ("Show seed-derived route prefix and local domain", generate_route_values),
        ("Generate G1/G2/G3 target files", generate_group_targets),
        ("Show the active profile's balanced template allocation", show_assignments),
        ("Prepare standalone Context experiment", prepare_standalone_context_experiment),
    )
    for number, (title, action) in enumerate(steps, start=1):
        run_step(number, len(steps), title, action)
    verify_completed_experiment_artifacts()
    print("\nAll experiment preparation completed. Restart the active runtime if it is already running.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--assignments-only"]:
        show_assignments_local()
    elif sys.argv[1:] == ["--context-only"]:
        prepare_standalone_context_experiment()
    elif len(sys.argv) == 3 and sys.argv[1] == "--freeze-cohort":
        freeze_cohort(sys.argv[2])
    elif sys.argv[1:]:
        raise SystemExit(
            "Usage: python3 scripts/prepare_experiment.py "
            "[--context-only | --freeze-cohort config/<name>.csv]"
        )
    else:
        main()
