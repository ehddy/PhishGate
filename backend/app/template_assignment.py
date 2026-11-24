"""Seeded, exactly balanced template assignment within research groups."""

from __future__ import annotations

import hashlib

from app.profiles import GateTemplate
from app.research_groups import TargetKey


def build_balanced_assignment(
    *,
    seed: str,
    gate_type: str,
    group_id: str,
    targets: tuple[TargetKey, ...],
    templates: tuple[GateTemplate, ...],
) -> dict[TargetKey, GateTemplate]:
    """Deterministically shuffle targets, then distribute templates round-robin."""
    if not seed:
        raise ValueError("A non-empty assignment seed is required.")
    if not templates:
        raise ValueError("At least one template is required.")

    def rank(target: TargetKey) -> bytes:
        material = f"{seed}:{gate_type}:{group_id}:{target.dataset}:{target.canonical_id}"
        return hashlib.sha256(material.encode("utf-8")).digest()

    ordered_targets = sorted(targets, key=lambda target: (rank(target), target))
    offset_material = f"{seed}:{gate_type}:{group_id}:template-offset"
    offset = int.from_bytes(hashlib.sha256(offset_material.encode("utf-8")).digest()[:4], "big") % len(templates)
    return {
        target: templates[(index + offset) % len(templates)]
        for index, target in enumerate(ordered_targets)
    }


def select_template(
    *,
    seed: str,
    gate_type: str,
    group_id: str,
    target: TargetKey,
    group_targets: tuple[TargetKey, ...],
    templates: tuple[GateTemplate, ...],
) -> GateTemplate:
    """Return the stable balanced choice, with a deterministic fallback for an unregistered target."""
    assignment = build_balanced_assignment(
        seed=seed,
        gate_type=gate_type,
        group_id=group_id,
        targets=group_targets,
        templates=templates,
    )
    selected = assignment.get(target)
    if selected is not None:
        return selected

    material = f"{seed}:{gate_type}:{group_id}:{target.dataset}:{target.canonical_id}:fallback"
    index = int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:4], "big") % len(templates)
    return templates[index]
