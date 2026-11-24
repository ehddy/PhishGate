"""Load and validate the selected ordered Gate profile from YAML."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.presentation import (
    CONTEXT_MODES,
    COPY_VARIANTS,
    LAYOUT_VARIANTS,
    THEME_VARIANTS,
)


ALLOWED_GATE_TYPES = {"challenge", "click", "interaction"}
DEFAULT_CONFIG_PATH = "/app/config/profiles.yaml"
DEFAULT_PROFILE_ID = "click"


class ProfileConfigError(ValueError):
    """Raised when the selected Gate profile is missing or malformed."""


@dataclass(frozen=True)
class GateTemplate:
    template_id: str
    parameters: dict[str, object]


@dataclass(frozen=True)
class GateStage:
    gate_type: str
    templates: tuple[GateTemplate, ...]


@dataclass(frozen=True)
class GateProfile:
    profile_id: str
    gates: tuple[GateStage, ...]


def _validate_presentation_parameters(
    parameters: dict[str, object],
    *,
    stage_index: int,
    template_id: str,
) -> None:
    context_mode = parameters.get("context_mode")
    if context_mode is not None and (
        not isinstance(context_mode, str) or context_mode not in CONTEXT_MODES
    ):
        raise ProfileConfigError(
            f"Gate stage {stage_index} template {template_id} has an invalid "
            "context_mode."
        )

    option_domains = {
        "layout_variants": frozenset(LAYOUT_VARIANTS),
        "copy_variants": frozenset(COPY_VARIANTS),
        "theme_variants": frozenset(THEME_VARIANTS),
    }
    for name, allowed in option_domains.items():
        configured = parameters.get(name)
        if configured is None:
            continue
        if (
            not isinstance(configured, list)
            or not configured
            or any(
                not isinstance(value, str) or value not in allowed
                for value in configured
            )
        ):
            raise ProfileConfigError(
                f"Gate stage {stage_index} template {template_id} has invalid {name}."
            )


def _template_option(
    raw: object,
    *,
    stage_index: int,
    common_parameters: dict[str, object],
) -> GateTemplate:
    if isinstance(raw, str):
        template_id = raw
        own_parameters: dict[str, object] = {}
    elif isinstance(raw, dict):
        template_id = raw.get("id")
        own_parameters = raw.get("parameters", {})
        if not isinstance(own_parameters, dict):
            raise ProfileConfigError(
                f"Gate stage {stage_index} template parameters must be a mapping."
            )
    else:
        raise ProfileConfigError(f"Gate stage {stage_index} has an invalid template entry.")

    if not isinstance(template_id, str) or not template_id:
        raise ProfileConfigError(f"Gate stage {stage_index} requires a template id.")
    parameters = {**common_parameters, **own_parameters}
    _validate_presentation_parameters(
        parameters,
        stage_index=stage_index,
        template_id=template_id,
    )
    return GateTemplate(template_id=template_id, parameters=parameters)


def load_active_profile() -> GateProfile:
    """Return the profile selected by environment variables after validation."""
    config_path = Path(os.environ.get("PHISHGATE_CONFIG", DEFAULT_CONFIG_PATH))
    profile_id = os.environ.get("PHISHGATE_PROFILE", DEFAULT_PROFILE_ID)

    try:
        with config_path.open(encoding="utf-8") as config_file:
            document = yaml.safe_load(config_file)
    except (OSError, yaml.YAMLError) as error:
        raise ProfileConfigError(f"Unable to read Gate config: {config_path}") from error

    if not isinstance(document, dict) or not isinstance(document.get("profiles"), dict):
        raise ProfileConfigError("Gate config must contain a profiles mapping.")

    profile = document["profiles"].get(profile_id)
    if not isinstance(profile, dict):
        raise ProfileConfigError(f"Unknown Gate profile: {profile_id}")

    raw_gates = profile.get("gates")
    if not isinstance(raw_gates, list):
        raise ProfileConfigError(f"Profile {profile_id} must contain a gates list.")

    gates: list[GateStage] = []
    for stage_index, raw_gate in enumerate(raw_gates):
        if not isinstance(raw_gate, dict):
            raise ProfileConfigError(f"Gate stage {stage_index} must be a mapping.")

        gate_type = raw_gate.get("type")
        common_parameters = raw_gate.get("parameters", {})
        if gate_type not in ALLOWED_GATE_TYPES:
            raise ProfileConfigError(f"Gate stage {stage_index} has an unsupported type.")
        if not isinstance(common_parameters, dict):
            raise ProfileConfigError(f"Gate stage {stage_index} parameters must be a mapping.")

        has_template = "template" in raw_gate
        has_templates = "templates" in raw_gate
        if has_template == has_templates:
            raise ProfileConfigError(
                f"Gate stage {stage_index} must define exactly one of template or templates."
            )

        raw_templates = raw_gate.get("templates") if has_templates else [raw_gate.get("template")]
        if not isinstance(raw_templates, list) or not raw_templates:
            raise ProfileConfigError(f"Gate stage {stage_index} templates must be a non-empty list.")
        templates = tuple(
            _template_option(
                raw_template,
                stage_index=stage_index,
                common_parameters=common_parameters,
            )
            for raw_template in raw_templates
        )
        template_ids = [template.template_id for template in templates]
        if len(template_ids) != len(set(template_ids)):
            raise ProfileConfigError(f"Gate stage {stage_index} contains duplicate template ids.")

        gates.append(GateStage(gate_type=gate_type, templates=templates))

    return GateProfile(profile_id=profile_id, gates=tuple(gates))
