"""Reads Engine Gateway -- public, unauthenticated access to MATCHING,
SORTING_TIMELINE, HIGHER_LOWER_STREAK, and ELIMINATION_SURVIVAL
(public-readiness punch-list closure pass).

Mirrors gateway/services/public_game.py's own trust-boundary reasoning
exactly: a real anonymous player never receives an admin token, and this
module is the ONLY place allowed to decide what such a caller can trigger
or see.

--- WHY THESE FOUR, AND NOT THE OTHER THREE PHASE 6/7 MECHANICS ---
MULTIPLE_CHOICE_SINGLE_FACT and POSITION_LINEUP_GRID already share the
"guess" mechanic's single-question-per-fetch contract with every existing
PUBLIC_MODES entry (public_game.py) -- POSITION_LINEUP_GRID's college
variant was simply ADDED to that existing, proven allowlist this pass
(gateway/services/public_game.py's `lineup_college_guess` entry), needing
no new route family at all. WEEKLY_PICKEM and LIVE_WEEKLY_FANTASY_DRAFT
are genuinely multi-user/room-shaped (standings, draft rooms, multiple
participants) -- the existing single-player public trust boundary this
module and public_game.py both use doesn't fit them without real new
session/room infrastructure, which is exactly the kind of redesign this
punch-list explicitly excludes. Left admin/Creator-only; reported as a
blocker in the final report, not forced live.

--- WHY THIS IS SAFE (the same read-only, closed-set argument
generate_public() already relies on, re-verified for these four) ---
`tools.director_v04.{matching,sorting,elimination,higher_lower}` (Phase 6)
each open exactly one connection (`engine.connect()`), issue only SELECT
queries, and close it -- confirmed by re-reading every line of all four
this pass. Every parameter these routes let a caller influence is a
`mode` string looked up against `PUBLIC_MECHANIC_MODES` below (a small,
explicit, hand-certified allowlist -- never an arbitrary taxonomy_id or
variant the way the ADMIN `/v1/creator/mechanics/round` route allows);
`round_count`/`pair_count`/`item_count`/`sequence_length` are always
SERVER-chosen constants from that same table, never caller input. A fresh
random seed is generated per request (same `secrets.token_hex` pattern
public_game.py already uses) -- no exclude-list retry loop is needed the
way public_game.py's is: these generators are fast enough (confirmed well
under 1s each in Phase 6 testing) that a fresh random seed is already a
real, different round essentially every time, and MECHANIC_ENGINE's own
`client_safe_view()`/`evaluate_submission()` (Phase 6, unchanged here) are
the SAME functions the admin route already uses -- the identical
allow-list leakage guarantee carries over unchanged, not re-implemented.

--- CONCURRENCY / BACKPRESSURE ---
A bounded, non-blocking semaphore (`config.PUBLIC_MECHANIC_MAX_CONCURRENCY`)
gates round-generation calls -- same "clean GENERATION_BUSY error, never
an unbounded queue" shape every other public/admin generation path in this
project already uses. Round state itself reuses packages.py (content-
addressed, atomic) and game_state.py (mutable progress, atomic) -- the
exact same storage the admin route already writes into; a public round_id
and an admin round_id live in the same id-space by construction, with no
new storage layer.
"""
from __future__ import annotations

import secrets
import threading
from typing import Any, Optional

from .. import config
from ..errors import GatewayError
from . import game_state, oplog, packages

CONTRACT_VERSION = 1

# Public mode id -> (real taxonomy_id + variant + server-chosen generation
# params). Every value here is a real, already-certified-in-Phase-6 variant
# (tools/director_v02/mechanic_engine.py's own VARIANTS registry) -- this
# table only decides which of those are ALSO safe for anonymous traffic,
# never invents a new one.
PUBLIC_MECHANIC_MODES: dict[str, dict[str, Any]] = {
    "matching_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "MATCHING", "variant": "NFL_DRAFT_CLASS_MATCH",
        "title": "NFL Draft Class Matching",
        "instructions": "Match each real NFL Draft pick to the real team that drafted him.",
        "kind": "matching", "gen_kwargs": {"round_count": 1, "pair_count": 4},
    },
    "matching_cfb_heisman": {
        "competition": "CFB", "taxonomy_id": "MATCHING", "variant": "CFB_HEISMAN_SCHOOL_MATCH",
        "title": "CFB Heisman Matching",
        "instructions": "Match each real Heisman Trophy winner to the school he played for.",
        "kind": "matching", "gen_kwargs": {"round_count": 1, "pair_count": 4},
    },
    "sorting_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_DRAFT_PICK_ORDER",
        "title": "NFL Draft Order",
        "instructions": "Put these real NFL Draft picks in order, earliest overall selection first.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    "sorting_cfb_heisman": {
        "competition": "CFB", "taxonomy_id": "SORTING_TIMELINE", "variant": "CFB_HEISMAN_YEAR_ORDER",
        "title": "Heisman Timeline",
        "instructions": "Put these real Heisman Trophy winners in order, earliest year first.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    "higher_lower_nfl_wins": {
        "competition": "NFL", "taxonomy_id": "HIGHER_LOWER_STREAK", "variant": "NFL_TEAM_SEASON_WINS",
        "title": "NFL Wins Streak",
        "instructions": "Guess whether the next real NFL team-season had a higher or lower win total. One miss ends the streak.",
        "kind": "higher_lower", "gen_kwargs": {"sequence_length": 12},
    },
    "higher_lower_cfb_wins": {
        "competition": "CFB", "taxonomy_id": "HIGHER_LOWER_STREAK", "variant": "CFB_TEAM_SEASON_WINS",
        "title": "CFB Wins Streak",
        "instructions": "Guess whether the next real CFB (FBS) team-season had a higher or lower win total. One miss ends the streak.",
        "kind": "higher_lower", "gen_kwargs": {"sequence_length": 12},
    },
    "elimination_nfl_super_bowl": {
        "competition": "NFL", "taxonomy_id": "ELIMINATION_SURVIVAL", "variant": "NFL_SUPER_BOWL_CHAMPION_SURVIVAL",
        "title": "Super Bowl Champion Survival",
        "instructions": "One miss ends the run. Answer True or False for each real NFL team-season.",
        "kind": "elimination", "gen_kwargs": {"sequence_length": 12},
    },
    "elimination_cfb_national_champion": {
        "competition": "CFB", "taxonomy_id": "ELIMINATION_SURVIVAL", "variant": "CFB_NATIONAL_CHAMPION_SURVIVAL",
        "title": "National Champion Survival",
        "instructions": "One miss ends the run. Answer True or False for each real CFB (FBS) team-season.",
        "kind": "elimination", "gen_kwargs": {"sequence_length": 12},
    },
    # Reusable Game Format System pass: the new COMPARISON_BRACKET mechanic
    # (tools/director_v04/comparison.py), backing the new BRACKET_TREE
    # format. gen_kwargs is empty -- comparison.build_package() takes no
    # tunable knobs (a real, fixed 8-entry bracket every time).
    "comparison_nfl_wins": {
        "competition": "NFL", "taxonomy_id": "COMPARISON_BRACKET", "variant": "NFL_TEAM_SEASON_WINS_BRACKET",
        "title": "NFL Wins Bracket",
        "instructions": "Predict the real winner of every matchup in this real 8-team bracket, based on "
                        "regular-season win total.",
        "kind": "comparison", "gen_kwargs": {},
    },
    "comparison_cfb_wins": {
        "competition": "CFB", "taxonomy_id": "COMPARISON_BRACKET", "variant": "CFB_TEAM_SEASON_WINS_BRACKET",
        "title": "CFB Wins Bracket",
        "instructions": "Predict the real winner of every matchup in this real 8-team bracket, based on "
                        "regular-season win total.",
        "kind": "comparison", "gen_kwargs": {},
    },
    # ==========================================================================
    # Finish-10-Formats pass: the 6 new taxonomies from the 40-Format
    # Expansion pass, now real, public, unauthenticated modes -- not
    # admin-preview-only. Same real safety argument as every entry above:
    # each generator opens one connection, issues only SELECT queries
    # (GRID_CONSTRAINT_BOARD's answer-check is the one live re-verification
    # query, also read-only), and every caller-influenced value is looked up
    # against this fixed table, never taken directly from the request.
    "connection_grid_nfl": {
        "competition": "NFL", "taxonomy_id": "GRID_CONSTRAINT_BOARD", "variant": "NFL_TEAM_DRAFT_ROUND_GRID",
        "title": "NFL Connection Grid",
        "instructions": "Each cell needs a real player who satisfies BOTH its row and column criteria.",
        "kind": "grid_constraint", "gen_kwargs": {},
    },
    "perfect_drive_nfl": {
        "competition": "NFL", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "NFL_DRAFT_PERFECT_DRIVE",
        "title": "Perfect Drive (NFL)",
        "instructions": "Answer correctly to gain real yardage toward the end zone. One wrong answer ends the drive.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 15},
    },
    "perfect_drive_cfb": {
        "competition": "CFB", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "CFB_HEISMAN_PERFECT_DRIVE",
        "title": "Perfect Drive (CFB)",
        "instructions": "Answer correctly to gain real yardage toward the end zone. One wrong answer ends the drive.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 15},
    },
    "goal_line_stand_nfl": {
        "competition": "NFL", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "NFL_DRAFT_GOAL_LINE_STAND",
        "title": "Goal Line Stand (NFL)",
        "instructions": "You have 4 downs to score. A wrong answer costs a down.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 10},
    },
    "goal_line_stand_cfb": {
        "competition": "CFB", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "CFB_HEISMAN_GOAL_LINE_STAND",
        "title": "Goal Line Stand (CFB)",
        "instructions": "You have 4 downs to score. A wrong answer costs a down.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 10},
    },
    "lineup_builder_nfl": {
        "competition": "NFL", "taxonomy_id": "ROSTER_BUILD", "variant": "NFL_2010S_OFFENSE_BUILDER",
        "title": "2010s Offense Builder",
        "instructions": "Build a real roster from real 2010s starters -- one real player per slot, no player twice.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "lineup_builder_cfb": {
        "competition": "CFB", "taxonomy_id": "ROSTER_BUILD", "variant": "CFB_SKILL_POSITION_BUILDER",
        "title": "CFB Skill Position Builder",
        "instructions": "Build a real CFB skill-position lineup -- one real player per slot, no player twice.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "auction_draft_nfl": {
        "competition": "NFL", "taxonomy_id": "ROSTER_BUILD", "variant": "NFL_AUCTION_DRAFT",
        "title": "NFL Auction Draft",
        "instructions": "Draft a real roster one slot at a time under a fictional $50,000,000 budget. "
                        "Each player's cost is a fictional value derived from real career production.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "auction_draft_cfb": {
        "competition": "CFB", "taxonomy_id": "ROSTER_BUILD", "variant": "CFB_AUCTION_DRAFT",
        "title": "CFB Auction Draft",
        "instructions": "Draft a real roster one slot at a time under a fictional $50,000,000 budget. "
                        "Each player's cost is a fictional value derived from real career production.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "cap_challenge_nfl": {
        "competition": "NFL", "taxonomy_id": "ROSTER_BUILD", "variant": "NFL_CAP_CHALLENGE",
        "title": "NFL Cap Challenge",
        "instructions": "Freely select, swap, or remove real players per slot under a fictional "
                        "$50,000,000 cap. Nothing locks in until you submit the finished lineup.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "cap_challenge_cfb": {
        "competition": "CFB", "taxonomy_id": "ROSTER_BUILD", "variant": "CFB_CAP_CHALLENGE",
        "title": "CFB Cap Challenge",
        "instructions": "Freely select, swap, or remove real players per slot under a fictional "
                        "$50,000,000 cap. Nothing locks in until you submit the finished lineup.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "knockout_tournament_nfl": {
        "competition": "NFL", "taxonomy_id": "KNOCKOUT_BRACKET", "variant": "NFL_TEAM_SEASON_WINS_KNOCKOUT_16",
        "title": "NFL Knockout Tournament",
        "instructions": "Predict the real winner of every matchup in this real 16-team knockout field, "
                        "based on regular-season win total.",
        "kind": "knockout_bracket", "gen_kwargs": {},
    },
    "knockout_tournament_cfb": {
        "competition": "CFB", "taxonomy_id": "KNOCKOUT_BRACKET", "variant": "CFB_TEAM_SEASON_WINS_KNOCKOUT_16",
        "title": "CFB Knockout Tournament",
        "instructions": "Predict the real winner of every matchup in this real 16-team knockout field, "
                        "based on regular-season win total.",
        "kind": "knockout_bracket", "gen_kwargs": {},
    },
    # SIX_DEGREES and CHAIN_REACTION share the identical real bounded-chain
    # backend/data (tools/director_v04/relationship_chain.py) -- two format
    # framings over one real mechanic, never two implementations.
    "six_degrees_cfb_nfl": {
        "competition": "CFB", "taxonomy_id": "RELATIONSHIP_CHAIN", "variant": "CFB_SCHOOL_TO_NFL_TEAM_CHAIN",
        "title": "Six Degrees: College to NFL",
        "instructions": "See a real player's college. Guess the real NFL team that drafted him.",
        "kind": "relationship_chain", "gen_kwargs": {"chain_count": 8},
    },
    "chain_reaction_cfb_nfl": {
        "competition": "CFB", "taxonomy_id": "RELATIONSHIP_CHAIN", "variant": "CFB_SCHOOL_TO_NFL_TEAM_CHAIN",
        "title": "Chain Reaction: College to NFL",
        "instructions": "Follow the real chain from college to the NFL team that drafted him.",
        "kind": "relationship_chain", "gen_kwargs": {"chain_count": 8},
    },
    "choose_your_path_nfl": {
        "competition": "NFL", "taxonomy_id": "BRANCH_STATE", "variant": "NFL_TOPIC_PATH",
        "title": "Choose Your Path",
        "instructions": "Pick a path at each step -- your choice determines the next real question.",
        "kind": "branch_state", "gen_kwargs": {},
    },
}

_generation_semaphore = threading.Semaphore(config.PUBLIC_MECHANIC_MAX_CONCURRENCY)


def list_public_mechanic_modes() -> list[dict]:
    """Client-safe mode discovery -- same allow-list discipline as
    public_game.py's list_public_modes(): only fields a client needs to
    choose a mode, never internal taxonomy/variant identifiers."""
    return [
        {"mode": mode_id, "competition": entry["competition"], "title": entry["title"],
         "instructions": entry["instructions"], "kind": entry["kind"],
         "available": config.PUBLIC_GAME_ENABLED}
        for mode_id, entry in PUBLIC_MECHANIC_MODES.items()
    ]


def _ensure_mode_public(mode: str) -> dict:
    if not config.PUBLIC_GAME_ENABLED:
        oplog.record_event("public_mechanic_disabled", mode=None, reason="master_switch_off")
        raise GatewayError("SERVICE_UNAVAILABLE", "Public gameplay is currently disabled.")
    entry = PUBLIC_MECHANIC_MODES.get(mode)
    if entry is None:
        raise GatewayError("INVALID_MODE", f"mode={mode!r} is not a recognized mechanic mode.")
    return entry


def start_public_round(*, mode: str) -> dict:
    from tools.director_v02 import mechanic_engine

    entry = _ensure_mode_public(mode)
    taxonomy_id, variant = entry["taxonomy_id"], entry["variant"]
    seed = secrets.token_hex(8)

    acquired = _generation_semaphore.acquire(blocking=False)
    if not acquired:
        raise GatewayError("GENERATION_BUSY", "This game is popular right now -- try again in a moment.")
    try:
        if taxonomy_id == "MATCHING":
            package = mechanic_engine.generate_matching_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "SORTING_TIMELINE":
            package = mechanic_engine.generate_sorting_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "HIGHER_LOWER_STREAK":
            package = mechanic_engine.generate_higher_lower_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "ELIMINATION_SURVIVAL":
            package = mechanic_engine.generate_elimination_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "COMPARISON_BRACKET":
            package = mechanic_engine.generate_comparison_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "GRID_CONSTRAINT_BOARD":
            package = mechanic_engine.generate_grid_constraint_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "DRIVE_PROGRESSION":
            package = mechanic_engine.generate_drive_progression_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "ROSTER_BUILD":
            package = mechanic_engine.generate_roster_build_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "KNOCKOUT_BRACKET":
            package = mechanic_engine.generate_knockout_bracket_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "RELATIONSHIP_CHAIN":
            package = mechanic_engine.generate_relationship_chain_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "BRANCH_STATE":
            package = mechanic_engine.generate_branch_state_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        else:  # unreachable given PUBLIC_MECHANIC_MODES' own real contents, defensive only
            raise GatewayError("INVALID_MODE", f"mode={mode!r} has no public generator wired.")
    finally:
        _generation_semaphore.release()

    if package.get("qa_status") != "PASSED":
        oplog.record_event("public_mechanic_no_eligible", mode=mode)
        raise GatewayError("NO_ELIGIBLE_GAME", package.get("shortfall_reason") or
                            f"No qualifying round could be generated for mode={mode!r} right now.")

    stored = packages.save_package(package)
    progress = mechanic_engine.initial_progress(taxonomy_id)
    progress["taxonomy_id"] = taxonomy_id
    progress["public_mode"] = mode  # so submit-side telemetry can report which public mode this was, never used for trust decisions
    game_state.create_state(stored["package_id"], progress)

    view = mechanic_engine.client_safe_view(taxonomy_id, stored, progress)
    oplog.record_event("public_mechanic_round_started", mode=mode)
    return {
        "round_id": stored["package_id"], "mode": mode, "title": entry["title"], "kind": entry["kind"],
        "instructions": entry["instructions"], "metadata": {"contract_version": CONTRACT_VERSION},
        "view": view,
    }


def get_public_round(*, round_id: str) -> dict:
    from tools.director_v02 import mechanic_engine

    try:
        stored = packages.load_package(round_id)
        progress = game_state.load_state(round_id)
    except (packages.PackageIdInvalid, game_state.StateIdInvalid):
        stored, progress = None, None
    if stored is None or progress is None or "public_mode" not in progress:
        # The "public_mode" check keeps this route scoped to rounds THIS
        # module created -- a real admin-created round_id (no public_mode
        # key) is reported not-found here, never silently served, even
        # though the underlying storage is shared (see module docstring).
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")

    taxonomy_id = progress["taxonomy_id"]
    view = mechanic_engine.client_safe_view(taxonomy_id, stored, progress)
    return {"round_id": round_id, "mode": progress["public_mode"], "view": view}


def submit_public_round(*, round_id: str, submission: dict) -> dict:
    from tools.director_v02 import mechanic_engine

    try:
        stored = packages.load_package(round_id)
        progress = game_state.load_state(round_id)
    except (packages.PackageIdInvalid, game_state.StateIdInvalid):
        stored, progress = None, None
    if stored is None or progress is None or "public_mode" not in progress:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")

    taxonomy_id, mode = progress["taxonomy_id"], progress["public_mode"]
    try:
        result, new_progress = mechanic_engine.evaluate_submission(taxonomy_id, stored, progress, submission)
    except mechanic_engine.MechanicError as e:
        raise GatewayError("INVALID_REQUEST", str(e))
    except (KeyError, IndexError, TypeError, AttributeError, ValueError):
        # Same real, found-and-fixed bug as the admin route's identical
        # guard (gateway/app.py's mechanics_submit_round) -- a malformed
        # submission shape (e.g. a string where a mapping/order was
        # expected) must fail cleanly, never a raw 500.
        raise GatewayError("INVALID_REQUEST", "This round has no more rounds/items to submit against, "
                            "or the submission was not shaped correctly for this mechanic.")

    new_progress["taxonomy_id"] = taxonomy_id
    new_progress["public_mode"] = mode
    game_state.save_state(round_id, new_progress)
    view = mechanic_engine.client_safe_view(taxonomy_id, stored, new_progress)
    oplog.record_event("public_mechanic_submitted", mode=mode,
                        correct=result.get("correct") if isinstance(result.get("correct"), bool) else None)
    return {"round_id": round_id, "mode": mode, "result": result, "view": view}
