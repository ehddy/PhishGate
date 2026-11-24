"""Build safe and reproducible presentation metadata for one Gate stage."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping


CONTEXT_MODES = frozenset({"neutral", "brand-label"})
LAYOUT_VARIANTS = ("centered", "compact")
COPY_VARIANTS = ("concise", "standard", "detailed")
THEME_VARIANTS = ("blue", "mint", "slate", "violet")
PRESENTATION_PARAMETER_NAMES = frozenset(
    {"context_mode", "layout_variants", "copy_variants", "theme_variants"}
)


def _safe_options(
    parameters: Mapping[str, object],
    name: str,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    configured = parameters.get(name)
    if configured is None:
        return allowed
    if not isinstance(configured, list) or not configured:
        raise ValueError(f"{name} must be a non-empty list of allowed values.")

    allowed_values = frozenset(allowed)
    if any(
        not isinstance(value, str) or value not in allowed_values
        for value in configured
    ):
        raise ValueError(f"{name} contains an unsupported value.")
    return tuple(dict.fromkeys(configured))


def _deterministic_choice(material: str, dimension: str, options: tuple[str, ...]) -> str:
    digest = hashlib.sha256(f"{material}:{dimension}".encode("utf-8")).digest()
    return options[int.from_bytes(digest[:4], "big") % len(options)]


def public_interaction_parameters(parameters: Mapping[str, object]) -> dict[str, object]:
    """Remove presentation inputs after they have been reduced to safe context fields."""
    return {
        name: value
        for name, value in parameters.items()
        if name not in PRESENTATION_PARAMETER_NAMES
    }


def build_display_context(
    *,
    brand: str | None,
    kit_root: str,
    profile_id: str,
    template_id: str,
    presentation_seed: str,
    parameters: Mapping[str, object],
) -> dict[str, str | None]:
    """Return whitelisted display metadata stable for one experiment condition."""
    if not presentation_seed:
        raise ValueError("A presentation seed is required to derive presentation variants.")

    configured_mode = parameters.get("context_mode", "brand-label")
    if not isinstance(configured_mode, str) or configured_mode not in CONTEXT_MODES:
        raise ValueError("context_mode contains an unsupported value.")
    context_mode = configured_mode
    safe_brand = brand.strip() if isinstance(brand, str) and brand.strip() else None
    if context_mode == "neutral":
        safe_brand = None

    material = f"{presentation_seed}:{kit_root}:{profile_id}:{template_id}"
    layout_variant = _deterministic_choice(
        material,
        "layout",
        _safe_options(parameters, "layout_variants", LAYOUT_VARIANTS),
    )
    copy_variant = _deterministic_choice(
        material,
        "copy",
        _safe_options(parameters, "copy_variants", COPY_VARIANTS),
    )
    theme_variant = _deterministic_choice(
        material,
        "theme",
        _safe_options(parameters, "theme_variants", THEME_VARIANTS),
    )

    return {
        "brand": safe_brand,
        "context_mode": context_mode,
        "layout_variant": layout_variant,
        "copy_variant": copy_variant,
        "theme_variant": theme_variant,
        "variant_id": f"{layout_variant}.{copy_variant}.{theme_variant}",
    }
