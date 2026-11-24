"""Small, framework-independent state helpers for one pending Gate."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass

from app.profiles import GateProfile


DisplayContext = dict[str, str | None]


@dataclass(frozen=True)
class PendingGate:
    """Server-side facts bound to one opaque, single-use Gate token."""

    session_id: str
    target_path: str
    kit_root: str
    dataset: str
    profile_id: str
    config_hash: str
    stage_index: int
    gate_type: str
    template_id: str
    parameters: dict[str, object]
    display_context: DisplayContext
    research_session_id: str
    log_target_path: str
    issued_monotonic: float


def profile_config_hash(profile: GateProfile) -> str:
    """Return a stable hash of the selected profile and its ordered stages."""
    canonical_profile = {
        "profile_id": profile.profile_id,
        "gates": [
            {
                "type": stage.gate_type,
                "templates": [
                    {
                        "id": template.template_id,
                        "parameters": template.parameters,
                    }
                    for template in stage.templates
                ],
            }
            for stage in profile.gates
        ],
    }
    serialized = json.dumps(
        canonical_profile,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def resolve_pending_gate(
    pending_gates: dict[str, PendingGate],
    token: str,
    session_id: str | None,
    *,
    active_profile_id: str,
    active_config_hash: str,
) -> PendingGate | None:
    """Resolve a token only inside its issuing session and experiment config."""
    pending = pending_gates.get(token)
    if pending is None or session_id is None:
        return None
    if not secrets.compare_digest(pending.session_id, session_id):
        return None
    if pending.profile_id != active_profile_id:
        return None
    if pending.config_hash != active_config_hash:
        return None
    if pending.stage_index != 0:
        return None
    return pending
