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
from tools.director_v04 import nl_mechanic_bridge, nl_schedule_bridge

from .. import config
from . import generation, packages, game_state
from ..errors import GatewayError


def _creator_provider() -> str:
    return "auto" if config.CREATOR_LLM_ENABLED else "mock"


# --- Public-readiness punch-list: direct-taxonomy mechanic NL bridge -------
# Same real gap, same fix pattern as the schedule-driven bridge above, for
# the other five real mechanics (MATCHING/SORTING_TIMELINE/HIGHER_LOWER_
# STREAK/ELIMINATION_SURVIVAL/POSITION_LINEUP_GRID) -- see
# tools/director_v04/nl_mechanic_bridge.py's own module docstring.

_DIRECT_MECHANIC_TITLES = {
    "MATCHING": "Matching", "SORTING_TIMELINE": "Sorting / Timeline",
    "HIGHER_LOWER_STREAK": "Higher / Lower Streak", "ELIMINATION_SURVIVAL": "Elimination / Survival",
    "POSITION_LINEUP_GRID": "Position Lineup Grid",
}


def _direct_mechanic_feasibility(bridged: dict) -> dict:
    """Mirrors _schedule_driven_feasibility()'s response shape. Unlike the
    schedule-driven mechanics, these five have no "is there a real slate
    yet" question -- their real variant (tools/director_v02/
    mechanic_engine.py's own VARIANTS registry) is already
    template_status=PRODUCTION_READY with real, already-measured candidate
    data (Phase 6/7), so a recognized request is always SUPPORTED; this
    function never re-derives that from scratch, it reports the same real
    fact concepts.py's own gating already established."""
    taxonomy_id, variant = bridged["taxonomy_id"], bridged["variant"]
    return {
        "support_status": "SUPPORTED",
        "reason": None,
        "capability": {"mechanic": taxonomy_id, "domain": variant, "relationship_predicate": None,
                        "category": _DIRECT_MECHANIC_TITLES[taxonomy_id]},
        "known_limitations": [],
        "visual_template": taxonomy_id,
        "clarifying_question": None,
        "closest_supported_capability": None,
        "translator_notes": f"Matched real mechanic {taxonomy_id} (variant={variant}) via the natural-language "
                              f"bridge (tools.director_v04.nl_mechanic_bridge) -- no (mechanic, domain, predicate) "
                              f"triple involved.",
        "translation_status": "TRANSLATED",
        "catalog_status": None,
        "catalog_vocabulary_status": None,
        "taxonomy_id": taxonomy_id,
        "variant": variant,
    }


def _generate_direct_mechanic(bridged: dict, *, seed: str | None) -> dict:
    """Routes straight into mechanic_engine.py's existing generation
    entrypoints -- the SAME functions POST /v1/creator/mechanics/round
    calls -- so a natural-language request and an explicit taxonomy_id
    request produce an identical, already-tested, already-playable round
    through the same packages/game_state storage."""
    from tools.director_v02 import mechanic_engine

    taxonomy_id, variant = bridged["taxonomy_id"], bridged["variant"]
    real_seed = seed or "creator-nl-mechanic-bridge"

    if taxonomy_id in ("MULTIPLE_CHOICE_SINGLE_FACT", "POSITION_LINEUP_GRID"):
        cfg = mechanic_engine.VARIANTS["POSITION_LINEUP_GRID"][variant]
        package = mechanic_engine.generate_guess_round(
            domain=cfg["domain"], relationship_predicate=cfg["relationship_predicate"],
            question_count=5, seed=real_seed)
    elif taxonomy_id == "MATCHING":
        package = mechanic_engine.generate_matching_round(variant=variant, round_count=3, pair_count=4, seed=real_seed)
    elif taxonomy_id == "SORTING_TIMELINE":
        package = mechanic_engine.generate_sorting_round(variant=variant, round_count=3, item_count=4, seed=real_seed)
    elif taxonomy_id == "HIGHER_LOWER_STREAK":
        package = mechanic_engine.generate_higher_lower_round(variant=variant, sequence_length=12, seed=real_seed)
    else:  # ELIMINATION_SURVIVAL
        package = mechanic_engine.generate_elimination_round(variant=variant, sequence_length=12, seed=real_seed)

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
    direct = nl_mechanic_bridge.detect(request_text)
    if direct is not None:
        return _direct_mechanic_feasibility(direct)
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
    if taxonomy_id == "WEEKLY_PICKEM" and bridged["league"] == "CFB":
        # Player Experience pass: CFB Pick'em is slate-filtered (Featured/
        # Top25/Power4/Conference/Full -- bridged["slate"]/["conference"],
        # set by nl_schedule_bridge.detect()). build_cfb_slate_package()
        # folds slate/conference into its OWN internal seed before ever
        # calling build_package() -- required because packages.py's
        # storage is content-addressed by package_id, a hash of
        # variant|season|week|seed only; two different real slates for the
        # same (season, week) must never collide under the SAME real_seed.
        from tools.director_v04 import weekly_pickem
        try:
            package = weekly_pickem.build_cfb_slate_package(
                real_seed, variant, season, week,
                slate=bridged.get("slate"), conference=bridged.get("conference"))
        except ValueError as e:
            raise GatewayError("INVALID_REQUEST", str(e))
    elif taxonomy_id == "WEEKLY_PICKEM":
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
    direct = nl_mechanic_bridge.detect(request_text)
    if direct is not None:
        return _generate_direct_mechanic(direct, seed=seed)

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
