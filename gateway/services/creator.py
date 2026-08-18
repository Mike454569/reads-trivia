"""Reads Engine Gateway -- Game Creator orchestration (v1.8, Part B/C/G/H).

Thin wrapper, same discipline as generation.py's own module docstring
("no Director/Game Factory logic reimplemented here"): every real decision
-- what's feasible, how a package gets generated/QA'd, how it's stored --
already lives in tools/director_v02/feasibility.py, gateway/services/
generation.py, and gateway/services/packages.py. This module only
sequences those calls for the three Creator-specific routes
(gateway/app.py's /v1/creator/*) and shapes their responses.

--- NATURAL-LANGUAGE REACHABILITY FOR SCHEDULE-DRIVEN MECHANICS ------------
WEEKLY_PICKEM and LIVE_WEEKLY_FANTASY_DRAFT (Phase 7A/7B) are fully built
and fully playable through /v1/creator/mechanics/round, but neither has a
(mechanic, domain, relationship_predicate) triple (they're schedule-driven,
not relationship-driven -- see their own module docstrings), so the normal
translator -> registry pipeline below can never route a plain-English
request to either one. `tools.director_v04.nl_schedule_bridge.detect()` is
a small, explicit, standalone check for exactly these two intents, run
BEFORE the normal pipeline in both `assess_feasibility()` and
`generate_for_review()` below -- everything it doesn't recognize (which is
almost everything, including historical game-result and NFL-Draft trivia)
falls straight through to the unchanged existing path.

--- SECURITY (Part L/M) ---
Every function here takes ONLY `request_text` (a plain string, already
length-capped by CreatorFeasibilityRequest/CreatorGenerateRequest at the
Gateway boundary) or an already-validated `package_id` -- never a raw spec,
table name, file path, or code fragment. `request_text` flows through
EXACTLY the same translator -> validator pipeline every other caller
(admin /v1/games/generate, public gameplay) already uses; the Creator gets
no bypass and no elevated trust for its input. See providers/mock.py's own
docstring for why that translator specifically cannot turn attacker text
into an executable value under any input, and providers/anthropic_provider.py's
own docstring for why the real LLM provider is exactly as constrained
(schema-only output, independently re-validated, no tools/DB access).

--- REAL LLM PROVIDER (Production LLM Integration for Game Creator) --------
This is the ONLY place in the Gateway that requests `provider="auto"`
(tools.director_v02.translator's real/mock selection policy -- see that
module's docstring). Deliberately Creator-only: ordinary player gameplay
(public_game.py) always passes `provider="mock"` explicitly and never
reaches this module at all, matching the milestone's explicit instruction
not to invoke a real LLM for gameplay that deterministic Engine generation
already serves. `config.CREATOR_LLM_ENABLED` is a separate operator kill
switch (independent of whether ANTHROPIC_API_KEY is even configured) that
forces every Creator request back to "mock" outright.
"""
from __future__ import annotations

from tools.director_v02 import feasibility as feasibility_mod
from tools.director_v04 import nl_schedule_bridge

from .. import config
from . import generation, packages, game_state
from ..errors import GatewayError


def _creator_provider() -> str:
    return "auto" if config.CREATOR_LLM_ENABLED else "mock"


def _schedule_driven_capability_label(bridged: dict) -> dict:
    game_title = "Weekly Pick'em" if bridged["taxonomy_id"] == "WEEKLY_PICKEM" else "Weekly Fantasy Draft"
    return {"mechanic": bridged["taxonomy_id"], "domain": bridged["league"],
            "relationship_predicate": None, "category": f"{bridged['league']} {game_title}"}


def _schedule_driven_feasibility(bridged: dict) -> dict:
    """Mirrors feasibility.assess()'s response shape (Part B's UI already
    reads `support_status`/`capability` off whatever this function returns)
    -- but the real support check itself is each mechanic's own existing,
    already-tested `check_slate_feasibility()`, never reimplemented here."""
    from tools.director_v04 import live_weekly_fantasy_draft, weekly_pickem

    taxonomy_id, variant, season, week = (
        bridged["taxonomy_id"], bridged["variant"], bridged["season"], bridged["week"])
    if week is None:
        slate = {
            "support_status": "MISSING_DATA", "variant": variant, "season": season, "week": None,
            "reason": f"No real schedule data exists yet for {variant}, season={season} -- "
                      f"cannot resolve a current week to generate from.",
        }
    elif taxonomy_id == "WEEKLY_PICKEM":
        slate = weekly_pickem.check_slate_feasibility(variant, season, week)
    else:
        slate = live_weekly_fantasy_draft.check_slate_feasibility(variant, season, week)

    return {
        "support_status": slate["support_status"],
        "reason": slate.get("reason"),
        "capability": _schedule_driven_capability_label(bridged),
        "known_limitations": [],
        "visual_template": "WEEKLY_PICKEM_SLATE" if taxonomy_id == "WEEKLY_PICKEM" else "FANTASY_DRAFT_BOARD",
        "clarifying_question": None,
        "closest_supported_capability": None,
        "translator_notes": f"Matched schedule-driven mechanic {taxonomy_id} via the natural-language bridge "
                              f"(tools.director_v04.nl_schedule_bridge) -- no (mechanic, domain, predicate) "
                              f"triple involved.",
        "translation_status": "TRANSLATED",
        "catalog_status": None,
        "catalog_vocabulary_status": None,
        "taxonomy_id": taxonomy_id,
        "variant": variant,
        "season": season,
        "week": week,
    }


def assess_feasibility(request_text: str) -> dict:
    bridged = nl_schedule_bridge.detect(request_text)
    if bridged is not None:
        return _schedule_driven_feasibility(bridged)
    return feasibility_mod.assess(request_text, provider=_creator_provider())


def _generate_schedule_driven(bridged: dict, *, seed: str | None) -> dict:
    """Routes straight into mechanic_engine.py's existing generation
    entrypoints -- the SAME functions POST /v1/creator/mechanics/round
    calls (gateway/app.py's mechanics_start_round) -- so a natural-language
    request and an explicit taxonomy_id request produce an identical,
    already-tested, already-playable round through the same
    packages/game_state storage. Never a second package/state system."""
    from tools.director_v02 import mechanic_engine

    taxonomy_id, variant, season, week = (
        bridged["taxonomy_id"], bridged["variant"], bridged["season"], bridged["week"])
    if week is None:
        raise GatewayError(
            "NO_ELIGIBLE_GAME",
            f"No real schedule data exists yet for {variant}, season={season} -- "
            f"cannot resolve a current week to generate from.",
        )

    real_seed = seed or "creator-nl-bridge"
    if taxonomy_id == "WEEKLY_PICKEM":
        package = mechanic_engine.generate_weekly_pickem_round(variant=variant, season=season, week=week, seed=real_seed)
    else:
        package = mechanic_engine.generate_fantasy_draft_round(variant=variant, season=season, week=week, seed=real_seed)

    if package.get("qa_status") != "PASSED":
        raise GatewayError(
            "NO_ELIGIBLE_GAME",
            package.get("shortfall_reason") or f"No qualifying {taxonomy_id} round could be generated right now.",
        )

    stored = packages.save_package(package)
    progress = mechanic_engine.initial_progress(taxonomy_id)
    progress["taxonomy_id"] = taxonomy_id
    game_state.create_state(stored["package_id"], progress)

    view = mechanic_engine.client_safe_view(taxonomy_id, stored, progress)
    return {"round_id": stored["package_id"], "taxonomy_id": taxonomy_id, "view": view}


def generate_for_review(*, request_text: str, puzzle_count, difficulty, seed) -> dict:
    """Reuses generation.generate() -- the SAME admin single-slot pipeline
    /v1/games/generate already uses, not a second generation path (Part B:
    'reuse the real existing Director/Factory architecture'). A
    Creator-generated package is stored exactly like any other admin
    generation (packages.save_package, review_status starts 'GENERATED').

    Checked first, same as assess_feasibility() above: a natural-language
    match for WEEKLY_PICKEM/LIVE_WEEKLY_FANTASY_DRAFT never reaches the
    translator/registry pipeline at all -- see module docstring."""
    bridged = nl_schedule_bridge.detect(request_text)
    if bridged is not None:
        return _generate_schedule_driven(bridged, seed=seed)

    result = generation.generate(
        request_text=request_text, spec=None, provider=_creator_provider(),
        puzzle_count=puzzle_count, difficulty=difficulty, seed=seed,
    )
    if result.get("package_id") and result.get("qa_status") == "PASSED":
        return packages.save_package(result)
    return result


def list_review_queue(review_status: str | None) -> list[dict]:
    return packages.list_packages(review_status=review_status)


def set_review_status(package_id: str, review_status: str) -> dict:
    try:
        return packages.set_review_status(package_id, review_status)
    except FileNotFoundError:
        raise GatewayError("PACKAGE_NOT_FOUND", "No such package.")
    except packages.PackageIdInvalid:
        raise GatewayError("PACKAGE_NOT_FOUND", "No such package.")
