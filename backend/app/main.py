import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.annotations import has_slug_mappings, lookup_kit_by_slug, lookup_kit_metadata
from app.challenges import (
    AreaSelectChallenge,
    DigitChallenge,
    ImageGridChallenge,
    MathChallenge,
    RotationChallenge,
    TextChallenge,
    challenge_rng,
    create_area_select_challenge,
    create_digit_challenge,
    create_image_grid_challenge,
    create_math_challenge,
    create_rotation_challenge,
    create_text_challenge,
)
from app.dynapd_annotations import (
    has_slug_mappings as has_dynapd_slug_mappings,
    lookup_dynapd_by_slug,
    lookup_dynapd_metadata,
    rewrite_public_redirect_root as rewrite_dynapd_public_redirect_root,
    upstream_location as dynapd_upstream_location,
)
from app.gate_state import PendingGate, profile_config_hash, resolve_pending_gate
from app.manual_annotations import lookup_sample_by_host, lookup_sample_by_slug, lookup_sample_metadata
from app.manual_render import render_sample as render_manual_sample
from app.profiles import ProfileConfigError, load_active_profile
from app.research_groups import TargetKey, experiment_manifest_path, group_catalog, group_for_target
from app.research_log import DEFAULT_LOG_DIR, ResearchLogger
from app.runtime_config import derive_local_domain, derive_route_prefix
from app.seeding import master_seed, purpose_seed
from app.template_assignment import select_template
from app.presentation import build_display_context, public_interaction_parameters
from app.upstream_policy import (
    KIT_CONTENT_SECURITY_POLICY,
    LocalUpstreamClient,
    preserved_content_type,
    rewrite_public_redirect_root,
)


app = FastAPI(title="PhishGate")
SESSION_COOKIE = "phishgate_session"
ROUTE_PREFIX = "/" + derive_route_prefix(master_seed())

# Docker's Nginx (prod) and Vite (dev/local) both serve the built SPA
# themselves and never forward those requests to FastAPI -- see
# nginx/templates/default.conf.template and frontend/vite.config.ts. The
# The production Conda runtime has no Node process because nodejs=22 and
# php=7.4 require incompatible OpenSSL ranges. It uses a pre-built
# frontend/dist/ and FastAPI serves that build directly.
# Both mounts below are no-ops -- and Docker/dev's own serving is untouched
# -- whenever frontend/dist/ does not exist, which is the normal state for
# every runtime except a Conda deployment that received a built dist/.
_FRONTEND_DIST = Path(
    os.environ.get("PHISHGATE_FRONTEND_DIST")
    or Path(__file__).resolve().parents[2] / "frontend" / "dist"
)
FRONTEND_INDEX = _FRONTEND_DIST / "index.html"
_FRONTEND_ASSETS = _FRONTEND_DIST / "assets"
FRONTEND_BUILD_READY = (
    FRONTEND_INDEX.is_file()
    and _FRONTEND_ASSETS.is_dir()
    and any(path.is_file() for path in _FRONTEND_ASSETS.rglob("*"))
)
if _FRONTEND_DIST.exists() and not FRONTEND_BUILD_READY:
    raise RuntimeError(
        f"Incomplete frontend build at {_FRONTEND_DIST}; expected index.html and built assets."
    )
# Mirrors nginx/templates/00-map.conf.template's $phishgate_is_own_host map:
# these are the only Host values where bare "/" is PhishGate's own SPA
# placeholder rather than a Host-routed manual/benign sample's real domain.
try:
    _OWN_HOST_DOMAIN = derive_local_domain(
        master_seed(), (os.environ.get("PHISHGATE_DOMAIN_STYLE", "off").strip() or "off")
    )
except ValueError:
    _OWN_HOST_DOMAIN = None
OWN_HOST_NAMES = {"localhost", "127.0.0.1"} | ({_OWN_HOST_DOMAIN} if _OWN_HOST_DOMAIN else set())
PRESENTATION_SEED = purpose_seed("presentation")
CHALLENGE_SEED = purpose_seed("challenge")
ASSIGNMENT_SEED = purpose_seed("assignment")
RESEARCH_LOGGER = ResearchLogger(
    os.environ.get("PHISHGATE_LOG_DIR", DEFAULT_LOG_DIR),
    os.environ.get("PHISHGATE_RUN_LABEL", ""),
)
unlocked_targets: dict[str, set[tuple[str, str, str]]] = {}
pending_targets: dict[str, PendingGate] = {}
pending_challenges: dict[
    str,
    DigitChallenge
    | MathChallenge
    | ImageGridChallenge
    | TextChallenge
    | AreaSelectChallenge
    | RotationChallenge,
] = {}

# Generic mode injects the gate in front of a single operator-configured
# upstream (see PHISHGATE_UPSTREAM) with no bundled dataset. When it is on, the
# PhishDecloaker access-slug index may legitimately be empty, so the dataset
# fail-fast below is skipped. Research mode (flag off) keeps the strict check.
GENERIC_UPSTREAM_ENABLED = bool(os.environ.get("PHISHGATE_GENERIC_UPSTREAM", "").strip())

if not GENERIC_UPSTREAM_ENABLED and not has_slug_mappings():
    raise RuntimeError(
        "Unable to build kit access-slug mappings. Set PHISHGATE_SEED "
        "and provide a readable annotation CSV containing kit directories."
    )

DYNAPD_ENABLED = bool(os.environ.get("PHISHGATE_DYNAPD_SELECTION", "").strip())
if DYNAPD_ENABLED and not has_dynapd_slug_mappings():
    raise RuntimeError(
        "PHISHGATE_DYNAPD_SELECTION is configured but no DynaPD access-slug "
        "mappings could be built."
    )

UPSTREAM_CLIENT = LocalUpstreamClient(os.environ["PHISHGATE_UPSTREAM"])
DYNAPD_UPSTREAM_CLIENT = (
    LocalUpstreamClient(os.environ["PHISHGATE_DYNAPD_UPSTREAM"])
    if DYNAPD_ENABLED
    else None
)

ACTIVE_PROFILE = load_active_profile()
ACTIVE_CONFIG_HASH = profile_config_hash(ACTIVE_PROFILE)
if len(ACTIVE_PROFILE.gates) > 1:
    raise ProfileConfigError("Runtime execution does not support multi-stage profiles yet.")

ACTIVE_STAGE = ACTIVE_PROFILE.gates[0] if ACTIVE_PROFILE.gates else None
GROUP_CATALOG = group_catalog()
SUPPORTED_TEMPLATES: dict[str, set[str]] = {
    "challenge": {
        "custom-digit",
        "math-challenge",
        "image-grid",
        "text-captcha",
        "area-select",
        "rotate-upright",
    },
    "click": {
        "alert",
        "blurred-preview",
        "cloudflare-checkbox",
        "cookie-consent",
        "document-ready",
        "notification-confirm",
        "security-check",
    },
    "interaction": {
        "movement-verify",
        "press-and-hold",
        "slide-to-verify",
        "below-fold-reveal",
        "terms-scroll",
    },
}
if ACTIVE_STAGE:
    supported = SUPPORTED_TEMPLATES.get(ACTIVE_STAGE.gate_type, set())
    if not supported or any(template.template_id not in supported for template in ACTIVE_STAGE.templates):
        raise ProfileConfigError(
            "The active profile contains an unsupported gate type or template."
        )


@app.get(f"{ROUTE_PREFIX}/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@dataclass(frozen=True)
class ResolvedTarget:
    """One path segment resolved to its dataset and canonical id, if any."""

    dataset: str  # "phishdecloaker" | "dynapd" | "manual"
    canonical_id: str  # kit_root (e.g. "kit8") or manual sample id


@dataclass(frozen=True)
class UpstreamPayload:
    content: bytes
    status_code: int
    content_type: str
    location: str | None


def _fetch_upstream(
    upstream_client: LocalUpstreamClient,
    target_url: str,
    method: str,
    body: bytes | None,
    headers: dict[str, str],
) -> UpstreamPayload:
    """Perform blocking local-kit I/O outside FastAPI's event loop."""
    try:
        with upstream_client.open(
            target_url,
            method=method,
            body=body,
            headers=headers,
        ) as upstream_response:
            location = upstream_response.headers.get("Location")
            return UpstreamPayload(
                content=upstream_response.read(),
                status_code=upstream_response.status,
                content_type=preserved_content_type(upstream_response.headers),
                location=(
                    upstream_client.browser_redirect_location(target_url, location)
                    if location is not None
                    else None
                ),
            )
    except HTTPError as error:
        return UpstreamPayload(
            content=error.read(),
            status_code=error.code,
            content_type=preserved_content_type(error.headers),
            location=None,
        )


def _resolve_target(public_root: str) -> ResolvedTarget | None:
    """Resolve a direct kit path or an opaque access slug to its dataset.

    Checks the phishdecloaker kit100 dataset first (its direct ``/kitN/``
    paths and its own access slugs, via ``app.annotations``), then the
    private DynaPD selection and separately maintained manual dataset by their
    own access slugs. The three datasets never share a lookup table.
    """
    if public_root.startswith("kit") and public_root[3:].isdigit():
        return ResolvedTarget("phishdecloaker", public_root)

    kit_root = lookup_kit_by_slug(public_root)
    if kit_root is not None:
        return ResolvedTarget("phishdecloaker", kit_root)

    dynapd_id = lookup_dynapd_by_slug(public_root) if DYNAPD_ENABLED else None
    if dynapd_id is not None:
        return ResolvedTarget("dynapd", dynapd_id)

    sample_id = lookup_sample_by_slug(public_root)
    if sample_id is not None:
        return ResolvedTarget("manual", sample_id)

    return None


def _resolve_pending_gate(token: str, session_id: str | None) -> PendingGate | None:
    """Resolve a token only for its browser session and active configuration."""
    return resolve_pending_gate(
        pending_targets,
        token,
        session_id,
        active_profile_id=ACTIVE_PROFILE.profile_id,
        active_config_hash=ACTIVE_CONFIG_HASH,
    )


def _integer_parameter(
    parameters: dict[str, object], name: str, default: int, minimum: int, maximum: int
) -> int:
    """Return one bounded integer parameter from the trusted startup profile."""
    value = parameters.get(name)
    return value if isinstance(value, int) and minimum <= value <= maximum else default


def _boolean_parameter(parameters: dict[str, object], name: str, default: bool) -> bool:
    """Return one boolean parameter from the trusted startup profile."""
    value = parameters.get(name)
    return value if isinstance(value, bool) else default


@app.get(f"{ROUTE_PREFIX}/api/gates/config")
def gate_config(request: Request, t: str) -> Response:
    pending = _resolve_pending_gate(t, request.cookies.get(SESSION_COOKIE))
    if pending is None:
        return JSONResponse({"detail": "The gate token is invalid or has expired."}, status_code=400)

    if ACTIVE_STAGE is None:
        return JSONResponse(
            {
                "profile_id": ACTIVE_PROFILE.profile_id,
                "stage_count": 0,
                "current_stage": None,
                "display_context": dict(pending.display_context),
            }
        )

    payload: dict[str, object] = {
        "profile_id": ACTIVE_PROFILE.profile_id,
        "stage_index": pending.stage_index,
        "stage_count": 1,
        "gate_type": pending.gate_type,
        "template_id": pending.template_id,
        "parameters": public_interaction_parameters(pending.parameters),
        "display_context": dict(pending.display_context),
    }
    if pending.gate_type == "challenge":
        challenge = pending_challenges.get(t)
        if challenge is None:
            rng = challenge_rng(CHALLENGE_SEED, pending.kit_root, pending.config_hash, pending.stage_index)
            if pending.template_id == "custom-digit":
                digit_count = _integer_parameter(pending.parameters, "digit_count", 5, 4, 8)
                challenge = create_digit_challenge(
                    digit_count=digit_count,
                    cell_width_px=_integer_parameter(pending.parameters, "digit_cell_width_px", 52, 24, 64),
                    max_rotation_degrees=_integer_parameter(pending.parameters, "max_rotation_degrees", 8, 0, 30),
                    noise_dot_count=_integer_parameter(pending.parameters, "noise_dot_count", 140, 0, 1000),
                    noise_line_count=_integer_parameter(pending.parameters, "noise_line_count", 11, 0, 100),
                    watermark_enabled=_boolean_parameter(pending.parameters, "watermark_enabled", False),
                    rng=rng,
                )
            elif pending.template_id == "image-grid":
                grid_size = _integer_parameter(pending.parameters, "grid_size", 3, 2, 4)
                min_matches = _integer_parameter(pending.parameters, "min_matches", 2, 1, 8)
                max_matches = _integer_parameter(pending.parameters, "max_matches", 4, min_matches, 8)
                challenge = create_image_grid_challenge(
                    grid_size=grid_size, min_matches=min_matches, max_matches=max_matches, rng=rng
                )
            elif pending.template_id == "text-captcha":
                challenge = create_text_challenge(
                    length=_integer_parameter(pending.parameters, "text_length", 6, 4, 8),
                    cell_width_px=_integer_parameter(pending.parameters, "text_cell_width_px", 54, 24, 64),
                    max_rotation_degrees=_integer_parameter(pending.parameters, "max_rotation_degrees", 10, 0, 30),
                    noise_dot_count=_integer_parameter(pending.parameters, "noise_dot_count", 150, 0, 1000),
                    noise_line_count=_integer_parameter(pending.parameters, "noise_line_count", 12, 0, 100),
                    watermark_enabled=_boolean_parameter(pending.parameters, "watermark_enabled", False),
                    rng=rng,
                )
            elif pending.template_id == "area-select":
                challenge = create_area_select_challenge(
                    columns=_integer_parameter(pending.parameters, "columns", 3, 2, 4),
                    rows=_integer_parameter(pending.parameters, "rows", 2, 1, 4),
                    rng=rng,
                )
            elif pending.template_id == "rotate-upright":
                challenge = create_rotation_challenge(
                    step_count=_integer_parameter(pending.parameters, "step_count", 8, 4, 24),
                    rng=rng,
                )
            else:
                allowed_operators = {"addition", "subtraction", "multiplication"}
                configured_operators = pending.parameters.get("operators")
                operators = tuple(
                    operator
                    for operator in configured_operators
                    if isinstance(operator, str) and operator in allowed_operators
                ) if isinstance(configured_operators, list) else ()
                min_operand = _integer_parameter(pending.parameters, "min_operand", 1, 0, 20)
                max_operand = _integer_parameter(pending.parameters, "max_operand", 12, min_operand, 20)
                challenge = create_math_challenge(
                    min_operand=min_operand,
                    max_operand=max_operand,
                    operators=operators or ("addition", "subtraction", "multiplication"),
                    rng=rng,
                )
            pending_challenges[t] = challenge
        if isinstance(challenge, DigitChallenge):
            payload["challenge"] = {
                "kind": "digit-image",
                "image_data_url": challenge.image_data_url,
                "variant": challenge.variant,
            }
        elif isinstance(challenge, TextChallenge):
            payload["challenge"] = {
                "kind": "text-image",
                "image_data_url": challenge.image_data_url,
                "variant": challenge.variant,
            }
        elif isinstance(challenge, ImageGridChallenge):
            payload["challenge"] = {
                "kind": "image-grid",
                "category_label": challenge.category_label,
                "cells": list(challenge.cell_image_data_urls),
                "variant": challenge.variant,
            }
        elif isinstance(challenge, AreaSelectChallenge):
            payload["challenge"] = {
                "kind": "area-select",
                "category_label": challenge.category_label,
                "image_data_url": challenge.image_data_url,
                "columns": challenge.columns,
                "rows": challenge.rows,
                "variant": challenge.variant,
            }
        elif isinstance(challenge, RotationChallenge):
            payload["challenge"] = {
                "kind": "rotation",
                "image_data_url": challenge.image_data_url,
                "step_count": challenge.step_count,
                "variant": challenge.variant,
            }
        else:
            payload["challenge"] = {
                "kind": "math-problem",
                "prompt": challenge.prompt,
                "operator": challenge.operator,
                "variant": challenge.variant,
            }

    return JSONResponse(payload)


async def _complete_gate(request: Request, expected_gate_type: str, gate_label: str) -> Response:
    if ACTIVE_STAGE is None or ACTIVE_STAGE.gate_type != expected_gate_type:
        return JSONResponse({"detail": f"The active profile has no {gate_label} gate."}, status_code=409)

    payload = await request.json()
    token = payload.get("t")
    if not isinstance(token, str):
        return JSONResponse({"detail": "A gate token is required."}, status_code=400)

    session_id = request.cookies.get(SESSION_COOKIE)
    pending = _resolve_pending_gate(token, session_id)
    if pending is None:
        return JSONResponse({"detail": "The gate token is invalid or has expired."}, status_code=400)

    if session_id not in unlocked_targets:
        return JSONResponse({"detail": "The gate session has expired."}, status_code=409)

    if pending.gate_type != expected_gate_type:
        return JSONResponse({"detail": "The gate token does not match this completion endpoint."}, status_code=409)

    unlocked_targets[session_id].add((pending.dataset, pending.kit_root, pending.config_hash))
    RESEARCH_LOGGER.gate_completed(
        session_id=pending.research_session_id,
        target_path=pending.log_target_path,
        profile_id=pending.profile_id,
        stage_index=pending.stage_index,
        stage_count=1,
        gate_type=pending.gate_type,
        template_id=pending.template_id,
        context_mode=str(pending.display_context["context_mode"]),
        elapsed_ms=round((time.monotonic() - pending.issued_monotonic) * 1000),
    )
    pending_targets.pop(token, None)
    return JSONResponse({"next_url": pending.target_path})


@app.post(f"{ROUTE_PREFIX}/api/gates/click/complete")
async def complete_click_gate(request: Request) -> Response:
    return await _complete_gate(request, "click", "Click")


@app.post(f"{ROUTE_PREFIX}/api/gates/interaction/complete")
async def complete_interaction_gate(request: Request) -> Response:
    return await _complete_gate(request, "interaction", "Interaction")


@app.post(f"{ROUTE_PREFIX}/api/gates/challenge/complete")
async def complete_challenge_gate(request: Request) -> Response:
    if ACTIVE_STAGE is None or ACTIVE_STAGE.gate_type != "challenge":
        return JSONResponse({"detail": "The active profile has no Challenge gate."}, status_code=409)

    payload = await request.json()
    token = payload.get("t")
    answer = payload.get("answer")
    if not isinstance(token, str) or not isinstance(answer, str):
        return JSONResponse({"detail": "A gate token and answer are required."}, status_code=400)

    session_id = request.cookies.get(SESSION_COOKIE)
    pending = _resolve_pending_gate(token, session_id)
    challenge = pending_challenges.get(token)
    if pending is None or challenge is None:
        return JSONResponse({"detail": "The gate challenge is invalid or has expired."}, status_code=400)
    normalized_answer = answer.strip() if isinstance(challenge, MathChallenge) else answer
    if isinstance(challenge, DigitChallenge):
        digit_count = len(challenge.answer)
        if len(normalized_answer) != digit_count or not normalized_answer.isascii() or not normalized_answer.isdigit():
            return JSONResponse(
                {"detail": f"Enter the {digit_count} digits shown in the image."},
                status_code=422,
            )
        mismatch_detail = "The code did not match. Please try again."
    elif isinstance(challenge, ImageGridChallenge):
        try:
            selected = sorted({int(piece) for piece in normalized_answer.split(",") if piece.strip() != ""})
        except ValueError:
            return JSONResponse({"detail": "Select the matching squares and try again."}, status_code=422)
        normalized_answer = ",".join(str(index) for index in selected)
        mismatch_detail = "The selection did not match. Please try again."
    elif isinstance(challenge, TextChallenge):
        # Text CAPTCHAs are matched case-insensitively (the answer alphabet is
        # upper-case), so an all-caps vs lower-case read is not a failure.
        character_count = len(challenge.answer)
        normalized_answer = answer.strip().upper()
        if len(normalized_answer) != character_count or not normalized_answer.isascii() or not normalized_answer.isalnum():
            return JSONResponse(
                {"detail": f"Enter the {character_count} characters shown in the image."},
                status_code=422,
            )
        mismatch_detail = "The code did not match. Please try again."
    elif isinstance(challenge, AreaSelectChallenge):
        # The client resolves the clicked point to a region index; the answer is
        # that single whole-number index.
        normalized_answer = answer.strip()
        if not normalized_answer.isascii() or not normalized_answer.isdigit():
            return JSONResponse({"detail": "Click the requested item and try again."}, status_code=422)
        mismatch_detail = "That was not the requested item. Please try again."
    elif isinstance(challenge, RotationChallenge):
        # The client submits the number of forward rotation steps it applied; the
        # correct step count is held server-side.
        normalized_answer = answer.strip()
        if not normalized_answer.isascii() or not normalized_answer.isdigit():
            return JSONResponse({"detail": "Rotate the image upright and try again."}, status_code=422)
        mismatch_detail = "The image was not upright. Please try again."
    else:
        if not normalized_answer.isascii() or not normalized_answer.isdigit():
            return JSONResponse({"detail": "Enter a whole-number answer."}, status_code=422)
        mismatch_detail = "The answer was not correct. Please try again."
    if not secrets.compare_digest(normalized_answer, challenge.answer):
        return JSONResponse({"detail": mismatch_detail}, status_code=422)

    if session_id not in unlocked_targets:
        return JSONResponse({"detail": "The gate session has expired."}, status_code=409)

    unlocked_targets[session_id].add((pending.dataset, pending.kit_root, pending.config_hash))
    RESEARCH_LOGGER.gate_completed(
        session_id=pending.research_session_id,
        target_path=pending.log_target_path,
        profile_id=pending.profile_id,
        stage_index=pending.stage_index,
        stage_count=1,
        gate_type=pending.gate_type,
        template_id=pending.template_id,
        context_mode=str(pending.display_context["context_mode"]),
        elapsed_ms=round((time.monotonic() - pending.issued_monotonic) * 1000),
    )
    pending_challenges.pop(token, None)
    pending_targets.pop(token, None)
    return JSONResponse({"next_url": pending.target_path})


def _gate_or_serve(
    resolved: ResolvedTarget,
    request: Request,
    redirect_target: str,
    log_target_path: str,
) -> Response | None:
    """Return a Gate redirect Response if `resolved` isn't unlocked yet, else None.

    Shared by every resolution path (phishdecloaker slug/kitN, manual/phishing
    slug, manual/benign Host) so the unlock-check / PendingGate construction
    logic lives in exactly one place. `redirect_target` becomes
    `PendingGate.target_path` -- the URL the browser is sent back to once the
    Gate is passed, which differs per caller (the original slug path for
    slug-resolved targets, a bare "/" for Host-resolved ones).
    """
    if not ACTIVE_STAGE:
        return None

    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id not in unlocked_targets:
        session_id = secrets.token_urlsafe(24)
        unlocked_targets[session_id] = set()

    unlock_key = (resolved.dataset, resolved.canonical_id, ACTIVE_CONFIG_HASH)
    if unlock_key in unlocked_targets[session_id]:
        return None

    token = secrets.token_urlsafe(9)
    target_key = TargetKey(resolved.dataset, resolved.canonical_id)
    # Generic mode gates one operator-configured upstream and is not part of a
    # stratified experiment, so it skips group/manifest membership and uses a
    # neutral (generic/en-US) presentation.
    if resolved.dataset == "generic":
        group_id = "generic"
        group_targets: tuple[TargetKey, ...] = (target_key,)
        brand = None
    else:
        group_id = group_for_target(resolved.dataset, resolved.canonical_id)
        if experiment_manifest_path() is not None and target_key not in GROUP_CATALOG[group_id]:
            return JSONResponse({"detail": "The target is not part of the active experiment manifest."}, status_code=404)
        group_targets = GROUP_CATALOG[group_id]
        if resolved.dataset == "phishdecloaker":
            metadata = lookup_kit_metadata(resolved.canonical_id)
            brand = metadata.brand
        elif resolved.dataset == "dynapd":
            metadata = lookup_dynapd_metadata(resolved.canonical_id)
            brand = metadata.brand if metadata is not None else None
        else:
            metadata = lookup_sample_metadata(resolved.canonical_id)
            brand = metadata.brand
    selected_template = select_template(
        seed=ASSIGNMENT_SEED,
        gate_type=ACTIVE_STAGE.gate_type,
        group_id=group_id,
        target=target_key,
        group_targets=group_targets,
        templates=ACTIVE_STAGE.templates,
    )
    pending_targets[token] = PendingGate(
        session_id=session_id,
        target_path=redirect_target,
        kit_root=resolved.canonical_id,
        dataset=resolved.dataset,
        profile_id=ACTIVE_PROFILE.profile_id,
        config_hash=ACTIVE_CONFIG_HASH,
        stage_index=0,
        gate_type=ACTIVE_STAGE.gate_type,
        template_id=selected_template.template_id,
        parameters=dict(selected_template.parameters),
        display_context=build_display_context(
            brand=brand,
            kit_root=resolved.canonical_id,
            profile_id=ACTIVE_PROFILE.profile_id,
            template_id=selected_template.template_id,
            presentation_seed=PRESENTATION_SEED,
            parameters=selected_template.parameters,
        ),
        research_session_id=secrets.token_urlsafe(12),
        log_target_path=log_target_path,
        issued_monotonic=time.monotonic(),
    )
    gate_url = f"{ROUTE_PREFIX}/?t={quote(token, safe='')}"
    # A locked POST must not replay its submitted body against the Gate Host.
    # Normal in-page form submissions happen after this session is unlocked.
    response = RedirectResponse(url=gate_url, status_code=303 if request.method == "POST" else 307)
    response.set_cookie(SESSION_COOKIE, session_id, httponly=True, samesite="lax")
    return response


# Registered after every literal {ROUTE_PREFIX}/... route above (health,
# api/gates/*) and before the catch-all below, so Starlette's
# registration-order route matching tries those exact routes first and only
# falls through to serving a static file when none of them match. A no-op
# when frontend/dist/ does not exist (see FRONTEND_INDEX above).
if FRONTEND_BUILD_READY:
    app.mount(ROUTE_PREFIX, StaticFiles(directory=_FRONTEND_DIST, html=True), name="spa")


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy_request(path: str, request: Request) -> Response:
    # A manual sample (either label) can also be resolved by its real Host
    # header instead of a slug -- see data/manual/README.md. This is on top
    # of, not instead of, the existing dummy-domain + slug routing below,
    # which every manual sample keeps regardless of label.
    host_header = (request.headers.get("host") or "").split(":", 1)[0].lower()
    host_sample_id = lookup_sample_by_host(host_header) if host_header else None
    if host_sample_id is not None:
        if path not in ("", "/"):
            return JSONResponse({"detail": "Not found."}, status_code=404)

        resolved = ResolvedTarget("manual", host_sample_id)
        gate_response = _gate_or_serve(
            resolved,
            request,
            redirect_target="/",
            log_target_path=f"//{host_header}/",
        )
        if gate_response is not None:
            return gate_response

        label = lookup_sample_metadata(resolved.canonical_id).label or "phishing"
        rendered = render_manual_sample(resolved.canonical_id, label)
        if rendered is None:
            return JSONResponse({"detail": "The manual sample could not be found."}, status_code=404)
        return HTMLResponse(rendered)

    # No Host-routed sample claimed this request. On PhishGate's own address,
    # bare "/" is the SPA's placeholder page -- Docker's Nginx/Vite already
    # serve it themselves and never reach this function; only a Conda
    # deployment with no Node process (see FRONTEND_INDEX above) depends on
    # this branch, and only when a built frontend/dist/ is actually present.
    # In generic mode the whole operator upstream is gated at "/", so the bare
    # root must reach the gate rather than the SPA placeholder (the gate SPA is
    # still served at ROUTE_PREFIX).
    if (
        not GENERIC_UPSTREAM_ENABLED
        and path in ("", "/")
        and host_header in OWN_HOST_NAMES
        and FRONTEND_INDEX.is_file()
    ):
        return FileResponse(FRONTEND_INDEX)

    # Direct /kitN/ paths remain the canonical phishdecloaker entry points.
    # Opaque access slugs are accepted for phishdecloaker, DynaPD, and as a
    # second entry point for manual samples (either label).
    public_root = path.split("/", 1)[0]
    resolved = _resolve_target(public_root)

    if resolved is not None:
        if path == public_root:
            query = f"?{request.url.query}" if request.url.query else ""
            return RedirectResponse(url=f"/{path}/{query}", status_code=307)

        query = f"?{request.url.query}" if request.url.query else ""
        gate_response = _gate_or_serve(
            resolved,
            request,
            redirect_target=f"/{path}{query}",
            log_target_path=f"/{path}",
        )
        if gate_response is not None:
            return gate_response

        # Gate passed (or gate-free baseline).
        if resolved.dataset == "manual":
            if path != f"{public_root}/":
                return JSONResponse({"detail": "Not found."}, status_code=404)
            label = lookup_sample_metadata(resolved.canonical_id).label or "phishing"
            rendered = render_manual_sample(resolved.canonical_id, label)
            if rendered is None:
                return JSONResponse({"detail": "The manual sample could not be found."}, status_code=404)
            return HTMLResponse(rendered)

        if resolved.dataset == "dynapd":
            try:
                path, entrypoint_query = dynapd_upstream_location(
                    resolved.canonical_id,
                    path[len(public_root):],
                )
            except (KeyError, ValueError):
                return JSONResponse({"detail": "Not found."}, status_code=404)
        # phishdecloaker: translate only a compatible access-slug alias.
        # Canonical /kitN/ paths are forwarded unchanged.
        elif public_root != resolved.canonical_id:
            path = f"{resolved.canonical_id}{path[len(public_root):]}"

    # Generic mode: nothing in the bundled datasets claimed this request, so
    # gate the whole operator-configured upstream behind one gate (unlock once
    # -> browse freely). `resolved` stays None so the raw path is proxied
    # verbatim to UPSTREAM_CLIENT below, exactly like the ungated fall-through.
    elif GENERIC_UPSTREAM_ENABLED:
        query = f"?{request.url.query}" if request.url.query else ""
        gate_response = _gate_or_serve(
            ResolvedTarget("generic", "generic"),
            request,
            redirect_target=f"/{path}{query}",
            log_target_path=f"/{path}",
        )
        if gate_response is not None:
            return gate_response

    if resolved is not None and resolved.dataset == "dynapd":
        if DYNAPD_UPSTREAM_CLIENT is None:
            return JSONResponse({"detail": "The DynaPD upstream is unavailable."}, status_code=503)
        upstream_client = DYNAPD_UPSTREAM_CLIENT
    else:
        upstream_client = UPSTREAM_CLIENT

    # `path` holds real (decoded) filesystem-derived segments here -- a DynaPD
    # kit's own saved-webpage folder names routinely contain spaces (e.g.
    # "Login - Anmelden bei eBay Kleinanzeigen_files"), which urlopen() rejects
    # outright as a control character in an unencoded request line.
    target_url = f"{upstream_client.base_url}/{quote(path, safe='/')}"
    target_query = request.url.query
    if resolved is not None and resolved.dataset == "dynapd" and not target_query:
        target_query = entrypoint_query
    if target_query:
        target_url = f"{target_url}?{target_query}"

    upstream_headers: dict[str, str] = {}
    content_type = request.headers.get("content-type")
    if content_type is not None:
        upstream_headers["Content-Type"] = content_type
    request_body = await request.body() if request.method == "POST" else None

    upstream_payload = await run_in_threadpool(
        _fetch_upstream,
        upstream_client,
        target_url,
        request.method,
        request_body,
        upstream_headers,
    )
    response_headers = {
        "content-type": upstream_payload.content_type,
        "content-security-policy": KIT_CONTENT_SECURITY_POLICY,
        "referrer-policy": "no-referrer",
    }
    if upstream_payload.location is not None:
        response_headers["location"] = upstream_payload.location
        if resolved is not None and resolved.dataset == "phishdecloaker":
            response_headers["location"] = rewrite_public_redirect_root(
                upstream_payload.location,
                resolved.canonical_id,
                public_root,
            )
        elif resolved is not None and resolved.dataset == "dynapd":
            response_headers["location"] = rewrite_dynapd_public_redirect_root(
                upstream_payload.location,
                resolved.canonical_id,
                public_root,
                path,
            )
    return Response(
        content=upstream_payload.content,
        status_code=upstream_payload.status_code,
        headers=response_headers,
    )
