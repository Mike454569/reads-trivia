"""Reliability Design Phase 6 -- the common mechanic execution contract.

One place that knows, for every real mechanic template, how to: generate a
real private round (server-private state), build the client-safe payload
(allow-list, never a deny-list -- the same discipline gateway/services/
public_game.py's `_public_view()` already established), accept a
submission, and evaluate it server-authoritatively. Reuses, never
redesigns: `gateway.services.generation.generate()` + `packages.py` for
MULTIPLE_CHOICE_SINGLE_FACT/POSITION_LINEUP_GRID (both share the exact same
"guess" mechanic contract -- only the visual_template differs),
`tools.director_v04.player_from_clues` for PROGRESSIVE_CLUE_IDENTIFY, and
the four new `tools.director_v04.{matching,sorting,elimination,
higher_lower}` generators for the mechanics Phase 6 builds from scratch.
Round PROGRESS (current index, streak, clues revealed) is real, mutable,
server-side state -- reuses `gateway.services.game_state` (the same
content-addressed-id + atomic-write mutable-state store Coach Connections
v2 already established), keyed by the round's own package_id, never
trusted from the client (same reasoning as game_state.py's own docstring).

Every `client_safe_view()` below is an explicit allow-list of fields for
that specific mechanic -- a field not named is never included, so a future
field added to a generator's private package shape is excluded by default.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

TAXONOMY_IDS = frozenset({
    "MULTIPLE_CHOICE_SINGLE_FACT", "PROGRESSIVE_CLUE_IDENTIFY", "MATCHING",
    "SORTING_TIMELINE", "HIGHER_LOWER_STREAK", "ELIMINATION_SURVIVAL", "POSITION_LINEUP_GRID",
    "WEEKLY_PICKEM", "LIVE_WEEKLY_FANTASY_DRAFT",
})

# Real, disclosed variant catalog -- the "Required relationship shape" per
# mechanic (Phase 6's common execution contract). Each variant names the
# real capability/table it is built on; nothing here is invented at
# request time.
VARIANTS: dict[str, dict[str, dict]] = {
    "MATCHING": {
        "NFL_DRAFT_CLASS_MATCH": {"competition": "NFL"},
        "CFB_HEISMAN_SCHOOL_MATCH": {"competition": "CFB"},
    },
    "SORTING_TIMELINE": {
        "NFL_DRAFT_PICK_ORDER": {"competition": "NFL"},
        "CFB_HEISMAN_YEAR_ORDER": {"competition": "CFB"},
    },
    "HIGHER_LOWER_STREAK": {
        "NFL_TEAM_SEASON_WINS": {"competition": "NFL"},
        "CFB_TEAM_SEASON_WINS": {"competition": "CFB"},
    },
    "ELIMINATION_SURVIVAL": {
        "NFL_SUPER_BOWL_CHAMPION_SURVIVAL": {"competition": "NFL"},
        "CFB_NATIONAL_CHAMPION_SURVIVAL": {"competition": "CFB"},
    },
    "PROGRESSIVE_CLUE_IDENTIFY": {
        "NFL_PLAYER_FROM_CLUES": {"competition": "NFL"},
    },
    "MULTIPLE_CHOICE_SINGLE_FACT": {},  # driven by (domain, relationship_predicate), see generate_guess_round()
    "POSITION_LINEUP_GRID": {
        "NFL_OFFENSE_LINEUP_COLLEGE_TEAM_ONLY": {"competition": "NFL",
            "domain": "NFL_OFFENSE_LINEUP_COLLEGE", "relationship_predicate": "TEAM_OF_STARTING_LINEUP_BY_COLLEGE"},
        "NFL_OFFENSE_LINEUP_NAMES_TEAM_ONLY": {"competition": "NFL",
            "domain": "NFL_OFFENSE_LINEUP", "relationship_predicate": "TEAM_OF_STARTING_LINEUP"},
    },
    # Phase 7A: schedule-driven, not relationship-driven -- WEEKLY_PICKEM has
    # no (mechanic, domain, relationship_predicate) triple in the capability
    # registry at all (see tools/director_v04/weekly_pickem.py's own module
    # docstring), so its "Required relationship shape" is a real (league,
    # season, week) slate query instead of a table/predicate pair.
    "WEEKLY_PICKEM": {
        "NFL_WEEKLY_PICKEM": {"competition": "NFL"},
        "CFB_WEEKLY_PICKEM": {"competition": "CFB"},
    },
    # Phase 7B: same schedule-driven shape as WEEKLY_PICKEM above -- see
    # tools/director_v04/live_weekly_fantasy_draft.py's own module docstring.
    "LIVE_WEEKLY_FANTASY_DRAFT": {
        "NFL_WEEKLY_FANTASY_DRAFT": {"competition": "NFL"},
        "CFB_WEEKLY_FANTASY_DRAFT": {"competition": "CFB"},
    },
}


class MechanicError(ValueError):
    pass


# --- MULTIPLE_CHOICE_SINGLE_FACT / POSITION_LINEUP_GRID (shared "guess" contract) ---

def generate_guess_round(*, domain: str, relationship_predicate: str, question_count: int, seed: Optional[str]) -> dict:
    from gateway.services import generation as generation_service
    spec = {"mechanic": "guess", "domain": domain, "relationship_predicate": relationship_predicate,
            "question_count": question_count, "difficulty": "any", "filters": {}, "exclusions": []}
    return generation_service.generate(request_text=None, spec=spec, provider="mock",
                                        puzzle_count=None, difficulty=None, seed=seed)


def _guess_client_view(package: dict, index: int) -> dict:
    total = len(package["questions"])
    # Real bug found and fixed during Phase 6 testing: after the LAST round
    # in a contest is submitted, evaluate_submission() advances
    # current_index past the final valid index and sets completed=True --
    # but the route still called client_safe_view() for the (now
    # nonexistent) next round, causing a real IndexError/500 on a player's
    # exact final question. Every mechanic's client view must handle "no
    # more rounds" as a real, clean state, never an unhandled crash --
    # exactly the "Load failed" class of bug the phase's own acceptance
    # criteria call out.
    if index >= total:
        return {"round_index": index, "round_count": total, "completed": True}
    q = package["questions"][index]
    return {
        "round_index": index, "round_count": total, "completed": False,
        "prompt": q["question"], "options": list(q["options"]),
        "visual_template": q.get("visual_template", "DEFAULT_MULTIPLE_CHOICE"),
        "visual_payload": q.get("visual_payload"), "difficulty": q.get("difficulty"),
    }


def _guess_evaluate(package: dict, index: int, submission: dict) -> dict:
    q = package["questions"][index]
    answer = str(submission.get("answer", "")).strip().lower()
    correct_label = q["options"][q["correctIndex"]]
    correct = answer == correct_label.strip().lower() or answer == str(q.get("answer", "")).strip().lower()
    return {"correct": correct, "canonical_answer": correct_label, "notes": q.get("notes")}


# --- PROGRESSIVE_CLUE_IDENTIFY ---

def generate_clue_round(*, target_count: int, seed: str) -> dict:
    from tools.director_v04 import player_from_clues
    return player_from_clues.build_package(seed, target_count=target_count)


def _clue_client_view(package: dict, index: int, clues_revealed: int) -> dict:
    total = len(package["puzzles"])
    if index >= total:
        return {"round_index": index, "round_count": total, "completed": True}
    puzzle = package["puzzles"][index]
    revealed = puzzle["clues"][:max(1, clues_revealed)]
    return {
        "round_index": index, "round_count": total, "completed": False,
        "clues_revealed_count": len(revealed), "total_clues": len(puzzle["clues"]),
        "clues": [{"clue_index": cl["clue_index"], "display_text": cl["display_text"]} for cl in revealed],
        "can_reveal_more": len(revealed) < len(puzzle["clues"]),
    }


def _clue_evaluate(package: dict, index: int, clues_revealed: int, submission: dict) -> dict:
    puzzle = package["puzzles"][index]
    guess = str(submission.get("guess_name", "")).strip().lower()
    canonical = puzzle["answer"]["display_name"]
    correct = bool(guess) and guess == canonical.strip().lower()
    # Fewer clues used = more points (the spec's own scoring rule) -- max
    # score at MIN_CLUES used, tapering to 1 point at full reveal.
    max_clues = len(puzzle["clues"])
    score = max(1, max_clues - clues_revealed + 1) if correct else 0
    return {"correct": correct, "canonical_answer": canonical, "clues_used": clues_revealed, "score": score}


# --- MATCHING ---

def generate_matching_round(*, variant: str, round_count: int, pair_count: int, seed: str) -> dict:
    from tools.director_v04 import matching
    return matching.build_package(seed, variant, round_count=round_count, pair_count=pair_count)


def _matching_client_view(package: dict, index: int) -> dict:
    total = len(package["rounds"])
    if index >= total:
        return {"round_index": index, "round_count": total, "completed": True}
    r = package["rounds"][index]
    return {"round_index": index, "round_count": total, "completed": False, "prompt": r["prompt"],
            "left_items": r["left_items"], "right_items": r["right_items"]}


def _matching_evaluate(package: dict, index: int, submission: dict) -> dict:
    r = package["rounds"][index]
    key = r["_private_answer_key"]
    mapping = submission.get("mapping") or {}
    correct_count = sum(1 for left_id, right_id in mapping.items() if key.get(left_id) == right_id)
    total = len(key)
    return {"correct_count": correct_count, "total_pairs": total, "all_correct": correct_count == total,
            "canonical_mapping": key, "notes": r.get("notes")}


# --- SORTING_TIMELINE ---

def generate_sorting_round(*, variant: str, round_count: int, item_count: int, seed: str) -> dict:
    from tools.director_v04 import sorting
    return sorting.build_package(seed, variant, round_count=round_count, item_count=item_count)


def _sorting_client_view(package: dict, index: int) -> dict:
    total = len(package["rounds"])
    if index >= total:
        return {"round_index": index, "round_count": total, "completed": True}
    r = package["rounds"][index]
    return {"round_index": index, "round_count": total, "completed": False, "prompt": r["prompt"],
            "items_shuffled": r["items_shuffled"]}


def _sorting_evaluate(package: dict, index: int, submission: dict) -> dict:
    r = package["rounds"][index]
    correct_order = r["_private_correct_order"]
    submitted_order = list(submission.get("order") or [])
    correct_positions = sum(1 for i, item_id in enumerate(submitted_order)
                             if i < len(correct_order) and item_id == correct_order[i])
    return {"correct_positions": correct_positions, "total_items": len(correct_order),
            "exact_match": submitted_order == correct_order, "canonical_order": correct_order,
            "notes": r.get("notes")}


# --- HIGHER_LOWER_STREAK (sequence-based streak, server-tracked position) ---

def generate_higher_lower_round(*, variant: str, sequence_length: int, seed: str) -> dict:
    from tools.director_v04 import higher_lower
    return higher_lower.build_package(seed, variant, sequence_length=sequence_length)


def _higher_lower_client_view(package: dict, current_index: int, streak: int, ended: bool) -> dict:
    seq = package["sequence"]
    current = seq[current_index]
    nxt = seq[current_index + 1] if current_index + 1 < len(seq) else None
    # Once the streak has ended, the comparison at `current_index` was
    # already server-authoritatively revealed via the submit result that
    # ended it (evaluate_submission always returns revealed_next_value/
    # revealed_next_label before setting ended=True) -- a resumed/refreshed
    # view after that point shows the SAME already-disclosed value again,
    # never a new one, so it is not a new leak, just not re-hiding
    # information the player already legitimately saw.
    next_item = ({"label": nxt["label"], "value": nxt["_private_value"]} if (nxt and ended) else
                 ({"label": nxt["label"]} if nxt else None))
    return {
        "current_index": current_index, "sequence_length": len(seq), "streak": streak, "ended": ended,
        "comparison_attribute": package.get("comparison_attribute"),
        "current_item": {"label": current["label"], "value": current["_private_value"]},
        "next_item": next_item,
        "sequence_complete": nxt is None,
    }


def _higher_lower_evaluate(package: dict, current_index: int, submission: dict) -> dict:
    seq = package["sequence"]
    current, nxt = seq[current_index], seq[current_index + 1]
    cur_v, next_v = current["_private_value"], nxt["_private_value"]
    guess = submission.get("guess")
    actual = "higher" if next_v > cur_v else "lower"  # tie-free by construction (higher_lower.py)
    correct = guess == actual
    return {"correct": correct, "actual_direction": actual, "revealed_next_value": next_v,
            "revealed_next_label": nxt["label"]}


# --- ELIMINATION_SURVIVAL (sequence-based survival, server-tracked position) ---

def generate_elimination_round(*, variant: str, sequence_length: int, seed: str) -> dict:
    from tools.director_v04 import elimination
    return elimination.build_package(seed, variant, sequence_length=sequence_length)


def _elimination_client_view(package: dict, current_index: int, survived: int, ended: bool) -> dict:
    seq = package["sequence"]
    current = seq[current_index] if current_index < len(seq) else None
    # Same already-disclosed-once reasoning as _higher_lower_client_view above:
    # once ended, the item at current_index was already revealed via the
    # submit result that ended the run.
    result = {
        "current_index": current_index, "sequence_length": len(seq), "survived_count": survived, "ended": ended,
        "current_prompt": (current["prompt"] if current else None),
        "sequence_complete": current is None,
    }
    if ended and current is not None:
        result["revealed_membership"] = bool(current["_private_membership"])
    return result


def _elimination_evaluate(package: dict, current_index: int, submission: dict) -> dict:
    item = package["sequence"][current_index]
    guess = bool(submission.get("guess"))
    actual = bool(item["_private_membership"])
    return {"correct": guess == actual, "actual_membership": actual, "prompt": item["prompt"]}


# --- WEEKLY_PICKEM (schedule-driven slate, real-world-async grading) ---
#
# Genuinely different shape from every mechanic above, and deliberately so
# -- see tools/director_v04/weekly_pickem.py's own module docstring for the
# full reasoning. Every other mechanic's "truth" is fully known at
# generation time and baked once into the immutable package. WEEKLY_PICKEM's
# truth (each game's real winner) is usually NOT known yet at generation
# time -- it only becomes knowable later, as real scores are ingested by
# the ordinary games/cfb_games_canonical refresh schedule. So:
#   - the package stores only the STATIC slate (game_id, real team codes,
#     kickoff date) -- never a result.
#   - progress stores only the RAW pick per game_id (predicted_winner,
#     picked_at) -- never a cached "graded"/"correct" flag.
#   - correctness is recomputed FRESH from the live tables on every single
#     view/evaluate call (weekly_pickem.live_game_statuses()) -- this is
#     what makes "grading happens automatically once a game goes final"
#     literally true, with no scheduled sweep/job to build or forget to run.

def generate_weekly_pickem_round(*, variant: str, season: int, week, seed: str) -> dict:
    from tools.director_v04 import weekly_pickem
    return weekly_pickem.build_package(seed, variant, season, week)


def _weekly_pickem_client_view(package: dict, progress: dict) -> dict:
    from tools.director_v04 import weekly_pickem

    variant = package["domain_variant"]
    games = package["games"]
    picks: dict = progress.get("picks", {})
    live = weekly_pickem.live_game_statuses(variant, [g["game_id"] for g in games])

    out_games = []
    for g in games:
        live_g = live.get(g["game_id"], {"status": "UNKNOWN", "winner_code": None, "home_score": None, "away_score": None})
        entry = {
            "game_id": g["game_id"],
            # Real, genuine defect caught by Phase 7B's own playthrough QA,
            # fixed here: the display names alone gave a real caller no
            # value it could actually submit as `predicted_winner` (which
            # is checked against the raw team/school code, never the
            # display name -- see _weekly_pickem_evaluate). Both are now
            # exposed, explicitly paired, so "which value do I submit" is
            # never a guess.
            "home_team": g["home_display"], "home_team_code": g["home_team"],
            "away_team": g["away_display"], "away_team_code": g["away_team"],
            "kickoff": g["kickoff"], "status": live_g["status"],
        }
        # Never leak a score/winner before the game is genuinely FINAL --
        # the one hard rule this whole mechanic exists to satisfy.
        if live_g["status"] == "FINAL":
            entry["home_score"] = live_g["home_score"]
            entry["away_score"] = live_g["away_score"]
            entry["winner"] = live_g["winner_code"]
            if live_g["winner_code"] == g["home_team"]:
                entry["winner_display"] = g["home_display"]
            elif live_g["winner_code"] == g["away_team"]:
                entry["winner_display"] = g["away_display"]
            else:
                entry["winner_display"] = "TIE"
        pick = picks.get(g["game_id"])
        if pick:
            entry["your_pick"] = pick["predicted_winner"]
            if live_g["status"] == "FINAL":
                entry["outcome"] = ("TIE" if live_g["winner_code"] == "TIE"
                                     else ("CORRECT" if pick["predicted_winner"] == live_g["winner_code"] else "INCORRECT"))
            else:
                entry["outcome"] = "PENDING"
        out_games.append(entry)

    graded = [e for e in out_games if e.get("outcome") in ("CORRECT", "INCORRECT", "TIE")]
    correct_count = sum(1 for e in graded if e["outcome"] == "CORRECT")
    return {
        "season": package["season"], "week": package["week"], "variant": variant,
        "games": out_games, "game_count": len(out_games),
        "picks_made": len(picks), "graded_count": len(graded), "correct_count": correct_count,
        "completed": len(graded) == len(out_games) and len(picks) == len(out_games),
    }


def _weekly_pickem_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    from tools.director_v04 import weekly_pickem

    variant = package["domain_variant"]
    games_by_id = {g["game_id"]: g for g in package["games"]}
    game_id = submission.get("game_id")
    game = games_by_id.get(game_id)
    if game is None:
        raise MechanicError(f"game_id {game_id!r} is not part of this slate")

    valid_sides = {game["home_team"], game["away_team"]}
    predicted_winner = submission.get("predicted_winner")
    if predicted_winner not in valid_sides:
        raise MechanicError(f"predicted_winner must be one of {sorted(valid_sides)} for game {game_id!r}")

    live = weekly_pickem.live_game_statuses(variant, [game_id]).get(
        game_id, {"status": "UNKNOWN", "winner_code": None})
    if live["status"] == "FINAL":
        raise MechanicError(f"game {game_id!r} is already final -- picks are closed")

    return {"game_id": game_id, "predicted_winner": predicted_winner, "status": "PENDING",
            "message": "Pick recorded -- will grade automatically once this game is final."}


# --- LIVE_WEEKLY_FANTASY_DRAFT (sequential slot-filling, real player pool,
# no hidden solution -- every eligible player is real, visible data, never
# a secret to reveal) ---
#
# The one thing this mechanic needs that no other one does: real protection
# against a stale write silently clobbering a newer one (a duplicate/rapid
# double-submit on the SAME round_id -- the one realistic race in this
# still-single-session, poll-based architecture; see
# live_weekly_fantasy_draft.py's own module docstring for why no new
# realtime backend was built). progress carries a `state_version` counter;
# evaluate re-reads the REAL current on-disk state immediately before
# accepting a pick and rejects if it has moved since the caller's own
# load_state() call -- contained entirely in this function, so the shared
# Gateway route/other mechanics are untouched.

def generate_fantasy_draft_round(*, variant: str, season: int, week, seed: str) -> dict:
    from tools.director_v04 import live_weekly_fantasy_draft
    return live_weekly_fantasy_draft.build_package(seed, variant, season, week)


def _fantasy_draft_client_view(package: dict, progress: dict) -> dict:
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd

    slots = package["draft_slots"]
    drafted = progress.get("drafted", [])
    drafted_ids = set(progress.get("drafted_player_ids", []))
    current_index = progress.get("current_slot_index", 0)
    completed = current_index >= len(slots)

    current_slot = None if completed else slots[current_index]
    remaining_pool = []
    if not completed:
        eligible_positions = lwfd.FLEX_ELIGIBLE_POSITIONS if current_slot == "FLEX" else {current_slot}
        remaining_pool = [
            {"player_id": p["player_id"], "display_name": p["display_name"],
             "position": p["position"], "team_display": p["team_display"]}
            for p in package["players"]
            if p["position"] in eligible_positions and p["player_id"] not in drafted_ids
        ]
    return {
        "season": package["season"], "week": package["week"], "variant": package["domain_variant"],
        "pool_source": package["pool_source"], "draft_slots": slots,
        "current_slot_index": current_index, "current_slot": current_slot,
        "roster": drafted, "picks_made": len(drafted), "slots_total": len(slots),
        "remaining_pool_size": len(remaining_pool), "remaining_pool": remaining_pool,
        "completed": completed, "state_version": progress.get("state_version", 0),
    }


def _fantasy_draft_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    from gateway.services import game_state

    slots = package["draft_slots"]
    current_index = progress.get("current_slot_index", 0)
    if current_index >= len(slots):
        raise MechanicError("this draft is already complete")

    fresh = game_state.load_state(package["package_id"])
    if fresh is not None and fresh.get("state_version", 0) != progress.get("state_version", 0):
        raise MechanicError("stale draft state -- another pick was already recorded, reload and retry")

    player_id = submission.get("player_id")
    players_by_id = {p["player_id"]: p for p in package["players"]}
    player = players_by_id.get(player_id)
    if player is None:
        raise MechanicError(f"player_id {player_id!r} is not in this draft's real eligible pool")

    drafted_ids = set(progress.get("drafted_player_ids", []))
    if player_id in drafted_ids:
        raise MechanicError(f"player {player_id!r} has already been drafted -- no player can be drafted twice")

    current_slot = slots[current_index]
    eligible_positions = lwfd.FLEX_ELIGIBLE_POSITIONS if current_slot == "FLEX" else {current_slot}
    if player["position"] not in eligible_positions:
        raise MechanicError(f"player {player_id!r} plays {player['position']!r}, not eligible for slot {current_slot!r}")

    return {"slot": current_slot, "player_id": player_id, "display_name": player["display_name"],
            "position": player["position"], "team_display": player["team_display"]}


# --- Generic dispatch used by the Gateway routes ---

def client_safe_view(taxonomy_id: str, package: dict, progress: dict) -> dict:
    if taxonomy_id in ("MULTIPLE_CHOICE_SINGLE_FACT", "POSITION_LINEUP_GRID"):
        return _guess_client_view(package, progress["current_index"])
    if taxonomy_id == "PROGRESSIVE_CLUE_IDENTIFY":
        return _clue_client_view(package, progress["current_index"], progress.get("clues_revealed", 1))
    if taxonomy_id == "MATCHING":
        return _matching_client_view(package, progress["current_index"])
    if taxonomy_id == "SORTING_TIMELINE":
        return _sorting_client_view(package, progress["current_index"])
    if taxonomy_id == "HIGHER_LOWER_STREAK":
        return _higher_lower_client_view(package, progress["current_index"], progress.get("streak", 0), progress.get("ended", False))
    if taxonomy_id == "ELIMINATION_SURVIVAL":
        return _elimination_client_view(package, progress["current_index"], progress.get("survived", 0), progress.get("ended", False))
    if taxonomy_id == "WEEKLY_PICKEM":
        return _weekly_pickem_client_view(package, progress)
    if taxonomy_id == "LIVE_WEEKLY_FANTASY_DRAFT":
        return _fantasy_draft_client_view(package, progress)
    raise MechanicError(f"unknown taxonomy_id {taxonomy_id!r}")


def evaluate_submission(taxonomy_id: str, package: dict, progress: dict, submission: dict) -> tuple[dict, dict]:
    """Returns (result, new_progress). Never mutates `progress` in place --
    callers persist the returned new_progress via game_state.save_state()."""
    progress = dict(progress)
    if taxonomy_id in ("MULTIPLE_CHOICE_SINGLE_FACT", "POSITION_LINEUP_GRID"):
        result = _guess_evaluate(package, progress["current_index"], submission)
        progress["current_index"] += 1
        progress["completed"] = progress["current_index"] >= len(package["questions"])
        return result, progress
    if taxonomy_id == "PROGRESSIVE_CLUE_IDENTIFY":
        if submission.get("action") == "reveal_next_clue":
            puzzle = package["puzzles"][progress["current_index"]]
            progress["clues_revealed"] = min(len(puzzle["clues"]), progress.get("clues_revealed", 1) + 1)
            return {"revealed": True}, progress
        result = _clue_evaluate(package, progress["current_index"], progress.get("clues_revealed", 1), submission)
        progress["current_index"] += 1
        progress["clues_revealed"] = 1
        progress["completed"] = progress["current_index"] >= len(package["puzzles"])
        return result, progress
    if taxonomy_id == "MATCHING":
        result = _matching_evaluate(package, progress["current_index"], submission)
        progress["current_index"] += 1
        progress["completed"] = progress["current_index"] >= len(package["rounds"])
        return result, progress
    if taxonomy_id == "SORTING_TIMELINE":
        result = _sorting_evaluate(package, progress["current_index"], submission)
        progress["current_index"] += 1
        progress["completed"] = progress["current_index"] >= len(package["rounds"])
        return result, progress
    if taxonomy_id == "HIGHER_LOWER_STREAK":
        if progress.get("ended"):
            raise MechanicError("this streak has already ended")
        result = _higher_lower_evaluate(package, progress["current_index"], submission)
        if result["correct"]:
            progress["streak"] = progress.get("streak", 0) + 1
            progress["current_index"] += 1
            progress["ended"] = progress["current_index"] + 1 >= len(package["sequence"])
        else:
            progress["ended"] = True
        return result, progress
    if taxonomy_id == "ELIMINATION_SURVIVAL":
        if progress.get("ended"):
            raise MechanicError("this run has already ended")
        result = _elimination_evaluate(package, progress["current_index"], submission)
        if result["correct"]:
            progress["survived"] = progress.get("survived", 0) + 1
            progress["current_index"] += 1
            progress["ended"] = progress["current_index"] >= len(package["sequence"])
        else:
            progress["ended"] = True
        return result, progress
    if taxonomy_id == "WEEKLY_PICKEM":
        result = _weekly_pickem_evaluate(package, progress, submission)
        picks = dict(progress.get("picks", {}))
        picks[result["game_id"]] = {
            "predicted_winner": result["predicted_winner"],
            "picked_at": datetime.now(timezone.utc).isoformat(),
        }
        progress["picks"] = picks
        return result, progress
    if taxonomy_id == "LIVE_WEEKLY_FANTASY_DRAFT":
        result = _fantasy_draft_evaluate(package, progress, submission)
        drafted = list(progress.get("drafted", []))
        drafted.append({
            "slot": result["slot"], "player_id": result["player_id"], "display_name": result["display_name"],
            "position": result["position"], "team_display": result["team_display"],
            "picked_at": datetime.now(timezone.utc).isoformat(),
        })
        progress["drafted"] = drafted
        progress["drafted_player_ids"] = list(progress.get("drafted_player_ids", [])) + [result["player_id"]]
        progress["current_slot_index"] = progress.get("current_slot_index", 0) + 1
        progress["completed"] = progress["current_slot_index"] >= len(package["draft_slots"])
        progress["state_version"] = progress.get("state_version", 0) + 1
        return result, progress
    raise MechanicError(f"unknown taxonomy_id {taxonomy_id!r}")


def initial_progress(taxonomy_id: str) -> dict:
    if taxonomy_id == "PROGRESSIVE_CLUE_IDENTIFY":
        return {"current_index": 0, "clues_revealed": 1, "completed": False}
    if taxonomy_id == "HIGHER_LOWER_STREAK":
        return {"current_index": 0, "streak": 0, "ended": False}
    if taxonomy_id == "ELIMINATION_SURVIVAL":
        return {"current_index": 0, "survived": 0, "ended": False}
    if taxonomy_id == "WEEKLY_PICKEM":
        return {"picks": {}}
    if taxonomy_id == "LIVE_WEEKLY_FANTASY_DRAFT":
        return {"drafted": [], "drafted_player_ids": [], "current_slot_index": 0, "completed": False, "state_version": 0}
    return {"current_index": 0, "completed": False}
