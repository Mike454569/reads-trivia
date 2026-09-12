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
    "WEEKLY_PICKEM", "LIVE_WEEKLY_FANTASY_DRAFT", "COMPARISON_BRACKET",
    # 40-Format Expansion pass: 6 new taxonomies, one per genuinely new
    # shared primitive the format expansion needed (see each one's own
    # generator module docstring under tools/director_v04/).
    "GRID_CONSTRAINT_BOARD", "RELATIONSHIP_CHAIN", "ROSTER_BUILD",
    "DRIVE_PROGRESSION", "KNOCKOUT_BRACKET", "BRANCH_STATE",
})

# 40-Format Expansion pass: real, disclosed yardage-by-difficulty scale for
# DRIVE_PROGRESSION's YARDAGE mode -- keyed to each question's OWN
# already-computed real difficulty_band (never a fabricated per-question
# value). Real, confirmed-live casing: generated questions carry
# Title-Case difficulty values ("Easy"/"Medium"/"Hard"), not lowercase --
# verified directly against a real generated package during this pass.
# Mirrors tools/director_v04/drive_progression.py's own constant.
_DRIVE_YARDS_BY_DIFFICULTY = {"Easy": 10, "Medium": 20, "Hard": 30, "Any": 15}
_DRIVE_FIELD_LENGTH_YARDS = 100

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
    # Reusable Game Format System pass: the new head-to-head mechanic
    # backing BRACKET_TREE (tools/director_v02/visual_templates.py) --
    # see tools/director_v04/comparison.py's own module docstring for why
    # this reuses higher_lower.py's exact real win-total data instead of a
    # new dataset.
    "COMPARISON_BRACKET": {
        "NFL_TEAM_SEASON_WINS_BRACKET": {"competition": "NFL"},
        "CFB_TEAM_SEASON_WINS_BRACKET": {"competition": "CFB"},
    },
    # 40-Format Expansion pass -- see tools/director_v04/grid_constraint.py's
    # own module docstring for why this is a NEW, server-authoritative
    # taxonomy, deliberately distinct from the existing client-side
    # GRID_BOARD/Immaculate Grid architecture.
    "GRID_CONSTRAINT_BOARD": {
        "NFL_TEAM_DRAFT_ROUND_GRID": {"competition": "NFL"},
    },
    # 40-Format Expansion pass -- see tools/director_v04/drive_progression.py's
    # own module docstring for why this reuses an EXISTING real "guess"
    # capability's question pool rather than a new adapter/data source.
    "DRIVE_PROGRESSION": {
        "NFL_DRAFT_PERFECT_DRIVE": {"competition": "NFL", "mode": "YARDAGE",
            "domain": "NFL_DRAFT", "relationship_predicate": "DRAFTED_BY"},
        "CFB_HEISMAN_PERFECT_DRIVE": {"competition": "CFB", "mode": "YARDAGE",
            "domain": "CFB_HEISMAN", "relationship_predicate": "WON_HEISMAN"},
        "NFL_DRAFT_GOAL_LINE_STAND": {"competition": "NFL", "mode": "DOWNS",
            "domain": "NFL_DRAFT", "relationship_predicate": "DRAFTED_BY"},
        "CFB_HEISMAN_GOAL_LINE_STAND": {"competition": "CFB", "mode": "DOWNS",
            "domain": "CFB_HEISMAN", "relationship_predicate": "WON_HEISMAN"},
    },
    # 40-Format Expansion pass -- see tools/director_v04/roster_build.py's
    # own module docstring for why this generalizes LIVE_WEEKLY_FANTASY_
    # DRAFT's real sequential-slot-filling shape with a swappable pool
    # query instead of a new mechanic convention.
    "ROSTER_BUILD": {
        "NFL_2010S_OFFENSE_BUILDER": {"competition": "NFL", "flow": "SEQUENTIAL"},
        "CFB_SKILL_POSITION_BUILDER": {"competition": "CFB", "flow": "SEQUENTIAL"},
        "NFL_AUCTION_DRAFT": {"competition": "NFL", "flow": "SEQUENTIAL"},
        "NFL_AUCTION_DRAFT_REAL_CONTRACT": {"competition": "NFL", "flow": "SEQUENTIAL"},
        "CFB_AUCTION_DRAFT": {"competition": "CFB", "flow": "SEQUENTIAL"},
        # Finish-10-Formats pass: CAP_CHALLENGE reuses the identical real
        # pool/cost data as its AUCTION_DRAFT sibling, generated with
        # flow="FREE_SELECT" instead of "SEQUENTIAL" -- never a second
        # pool/cost implementation (see roster_build.py's own docstring).
        "NFL_CAP_CHALLENGE": {"competition": "NFL", "flow": "FREE_SELECT", "base_variant": "NFL_AUCTION_DRAFT"},
        "CFB_CAP_CHALLENGE": {"competition": "CFB", "flow": "FREE_SELECT", "base_variant": "CFB_AUCTION_DRAFT"},
    },
    # 40-Format Expansion pass -- see tools/director_v04/knockout_bracket.py's
    # own module docstring for why this generalizes COMPARISON_BRACKET's
    # fixed-8 real bracket to a variable real field size instead of a new
    # answer-checking convention (client_view/evaluate below are byte-for-byte
    # the same shape as _comparison_client_view/_comparison_evaluate).
    "KNOCKOUT_BRACKET": {
        "NFL_TEAM_SEASON_WINS_KNOCKOUT_4": {"competition": "NFL"},
        "NFL_TEAM_SEASON_WINS_KNOCKOUT_16": {"competition": "NFL"},
        "CFB_TEAM_SEASON_WINS_KNOCKOUT_4": {"competition": "CFB"},
        "CFB_TEAM_SEASON_WINS_KNOCKOUT_16": {"competition": "CFB"},
    },
    # 40-Format Expansion pass -- BETA/SUPPORTED_WITH_LIMITATIONS this pass
    # (see tools/director_v04/relationship_chain.py's own module docstring
    # for the real, disclosed bounded-2-hop scope).
    "RELATIONSHIP_CHAIN": {
        "CFB_SCHOOL_TO_NFL_TEAM_CHAIN": {"competition": "CFB"},
    },
    # 40-Format Expansion pass -- BETA this pass (see tools/director_v04/
    # branch_state.py's own module docstring for the real, disclosed
    # small-fixed-tree scope).
    "BRANCH_STATE": {
        "NFL_TOPIC_PATH": {"competition": "NFL"},
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
            if live_g["status"] == "CANCELED":
                # Dynamic Weekly Pick'em pass: a canceled game never counts
                # against a player -- VOID is deliberately excluded from
                # both graded_count/correct_count below and from the
                # "every game must be picked" completion requirement.
                entry["outcome"] = "VOID"
            elif live_g["status"] == "FINAL":
                entry["outcome"] = ("TIE" if live_g["winner_code"] == "TIE"
                                     else ("CORRECT" if pick["predicted_winner"] == live_g["winner_code"] else "INCORRECT"))
            else:
                entry["outcome"] = "PENDING"  # includes POSTPONED -- the pick is preserved, not voided, until a real outcome exists
        out_games.append(entry)

    # Dynamic Weekly Pick'em pass: a canceled game is excluded from grading
    # AND from the "every game must be picked" completion requirement --
    # never counted against a player, regardless of whether they'd already
    # picked it before it was marked canceled.
    decidable_games = [e for e in out_games if e["status"] != "CANCELED"]
    graded = [e for e in decidable_games if e.get("outcome") in ("CORRECT", "INCORRECT", "TIE")]
    correct_count = sum(1 for e in graded if e["outcome"] == "CORRECT")
    voided_count = sum(1 for e in out_games if e["status"] == "CANCELED")
    # A stray pick made on a game BEFORE it was later marked canceled must
    # never block completion -- checking "every decidable game has a pick"
    # (not a strict count match against len(picks)) tolerates that leftover
    # pick instead of demanding it disappear.
    decidable_ids = {e["game_id"] for e in decidable_games}
    return {
        "season": package["season"], "week": package["week"], "variant": variant,
        "games": out_games, "game_count": len(out_games),
        "picks_made": len(picks), "graded_count": len(graded), "correct_count": correct_count,
        "voided_count": voided_count,
        "completed": len(graded) == len(decidable_games) and decidable_ids.issubset(picks.keys()),
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
        game_id, {"status": "UNKNOWN", "winner_code": None, "kickoff_utc": None})

    # Dynamic Weekly Pick'em pass: a canceled game never accepts a pick --
    # it will never be played, regardless of what its (now-meaningless)
    # kickoff time says.
    if live["status"] == "CANCELED":
        raise MechanicError(f"game {game_id!r} is canceled -- picks are closed")

    # Real, per-game kickoff lock -- replaces the old FINAL-only check
    # (mechanics-round Phase 7A original), which left a real, live loophole:
    # a pick was still accepted for a game that had already kicked off but
    # had no final score yet (in progress, or a real data-ingestion lag).
    # Comparing against the game's own real, current kickoff (which already
    # reflects any real reschedule -- see _pickem_status.py's never-clobber
    # rule) closes that loophole and satisfies "lock at kickoff, not at
    # final" for every status, including a rescheduled POSTPONED game
    # (its pick stays open until whatever its CURRENT real kickoff is).
    kickoff_raw = live.get("kickoff_utc")
    if kickoff_raw is not None:
        kickoff_dt = datetime.fromisoformat(kickoff_raw)
        if datetime.now(timezone.utc) >= kickoff_dt:
            raise MechanicError(f"game {game_id!r} has already kicked off -- picks are closed")

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


# --- COMPARISON_BRACKET (real, fully-determined single-elimination bracket) ---
#
# Reusable Game Format System pass -- backs the new BRACKET_TREE format
# (tools/director_v02/visual_templates.py). See tools/director_v04/
# comparison.py's own module docstring for why every real matchup's
# winner is fully determined at generation time (no player-choice
# branching) and why picks are graded per-matchup, exactly like
# WEEKLY_PICKEM's own real per-game picks -- reused pattern, not a new one.

def generate_comparison_round(*, variant: str, seed: str) -> dict:
    from tools.director_v04 import comparison
    return comparison.build_package(seed, variant)


def _comparison_client_view(package: dict, progress: dict) -> dict:
    picks = progress.get("picks", {})
    rounds_out = []
    for r in package["rounds"]:
        matchups_out = []
        for m in r["matchups"]:
            entry = {"match_id": m["match_id"], "entrant_a": m["entrant_a"], "entrant_b": m["entrant_b"]}
            pick = picks.get(m["match_id"])
            if pick:
                entry["your_pick"] = pick["predicted_winner"]
                entry["real_winner"] = pick["real_winner"]
                entry["correct"] = pick["predicted_winner"] == pick["real_winner"]
            matchups_out.append(entry)
        rounds_out.append({"round_index": r["round_index"], "round_label": r["round_label"], "matchups": matchups_out})
    total_matchups = sum(len(r["matchups"]) for r in package["rounds"])
    correct_count = sum(1 for p in picks.values() if p["predicted_winner"] == p["real_winner"])
    return {
        "rounds": rounds_out, "picks_made": len(picks), "total_matchups": total_matchups,
        "correct_count": correct_count, "completed": len(picks) >= total_matchups,
    }


def _comparison_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    match_id = submission.get("match_id")
    predicted_winner = submission.get("predicted_winner")
    match = None
    for r in package["_private_rounds"]:
        for m in r:
            if m["match_id"] == match_id:
                match = m
                break
        if match is not None:
            break
    if match is None:
        raise MechanicError(f"match_id {match_id!r} is not part of this bracket")
    if predicted_winner not in (match["entrant_a"], match["entrant_b"]):
        raise MechanicError(f"predicted_winner must be one of {[match['entrant_a'], match['entrant_b']]!r}")
    real_winner = match["real_winner"]
    return {
        "match_id": match_id, "predicted_winner": predicted_winner, "real_winner": real_winner,
        "correct": predicted_winner == real_winner,
        "value_a": match["value_a"], "value_b": match["value_b"],
    }


# --- KNOCKOUT_BRACKET (40-Format Expansion pass -- reuses
# _comparison_client_view()/_comparison_evaluate() UNCHANGED below: the
# package shape (rounds/picks/_private_rounds) is byte-for-byte identical
# to COMPARISON_BRACKET's, so no new client_view/evaluate pair is needed,
# only a new generator -- see tools/director_v04/knockout_bracket.py) ---

def generate_knockout_bracket_round(*, variant: str, seed: str) -> dict:
    from tools.director_v04 import knockout_bracket
    return knockout_bracket.build_package(seed, variant)


# --- RELATIONSHIP_CHAIN (40-Format Expansion pass -- bounded 2-hop chain,
# see tools/director_v04/relationship_chain.py's own module docstring for
# the real, disclosed scope limit vs. coach_connections_graph.py's harder,
# unbounded pathfinding engine) ---

def generate_relationship_chain_round(*, variant: str, chain_count: int, seed: str) -> dict:
    from tools.director_v04 import relationship_chain
    return relationship_chain.build_package(seed, variant, chain_count=chain_count)


def _relationship_chain_client_view(package: dict, progress: dict) -> dict:
    total = len(package["chains"])
    index = progress.get("current_index", 0)
    if index >= total:
        return {"round_index": index, "round_count": total, "completed": True}
    chain = package["chains"][index]
    return {
        "round_index": index, "round_count": total, "completed": False,
        "prompt": chain["prompt"], "start_node": chain["nodes"][0],
    }


def _relationship_chain_evaluate(package: dict, index: int, submission: dict) -> dict:
    chain = package["chains"][index]
    guess = str(submission.get("guess", "")).strip().lower()
    end_node = chain["nodes"][-1]
    correct = bool(guess) and guess == end_node["label"].strip().lower()
    return {"correct": correct, "canonical_answer": end_node["label"], "full_chain": [n["label"] for n in chain["nodes"]]}


# --- BRANCH_STATE (40-Format Expansion pass -- see tools/director_v04/
# branch_state.py's own module docstring for the real, disclosed
# small-fixed-tree scope) ---

def generate_branch_state_round(*, variant: str, seed: str) -> dict:
    from tools.director_v04 import branch_state
    return branch_state.build_package(seed, variant)


def _branch_state_client_view(package: dict, progress: dict) -> dict:
    node_id = progress.get("current_node", "root")
    tree = package["_private_tree"]
    node = tree[node_id]
    # Real bug found and fixed while wiring the frontend (Finish-10-Formats
    # pass): the leaf's own node type never changes after its question is
    # answered (node_id still points at the same leaf), so without this
    # explicit check this function would keep re-showing the same leaf
    # question with completed=False forever -- the player would never see
    # a real "you're done" state after answering. progress["completed"] is
    # the one authoritative signal (set by _branch_state_evaluate's caller
    # below once the leaf question itself has been answered).
    if progress.get("completed"):
        return {"node_id": node_id, "completed": True}
    if "choices" in node:
        return {"node_id": node_id, "completed": False, "prompt": node["prompt"], "choices": node["choices"]}
    # A leaf node -- generate (or reuse) the real question for this path.
    question = progress.get("leaf_question")
    if question is None:
        raise MechanicError("leaf question was not generated -- call evaluate_submission first")
    return {
        "node_id": node_id, "completed": False, "prompt": question["question"],
        "options": list(question["options"]),
    }


def _branch_state_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    from tools.director_v04 import branch_state

    node_id = progress.get("current_node", "root")
    tree = package["_private_tree"]
    node = tree[node_id]
    if "choices" in node:
        choice_id = submission.get("choice_id")
        valid_ids = {c["choice_id"] for c in node["choices"]}
        if choice_id not in valid_ids:
            raise MechanicError(f"choice_id must be one of {sorted(valid_ids)}")
        next_node_id = next(c["next"] for c in node["choices"] if c["choice_id"] == choice_id)
        leaf = tree[next_node_id]
        question = branch_state._generate_leaf_question(
            domain=leaf["domain"], relationship_predicate=leaf["relationship_predicate"],
            seed=f"{package['package_id']}:{next_node_id}",
        )
        if question is None:
            raise MechanicError(f"no real question could be generated for path {next_node_id!r}")
        return {"advanced_to": next_node_id, "leaf_question": question}
    # Answering the leaf's real question.
    question = progress.get("leaf_question")
    if question is None:
        raise MechanicError("no active question for this path")
    answer = str(submission.get("answer", "")).strip().lower()
    correct_label = question["options"][question["correctIndex"]]
    correct = answer == correct_label.strip().lower()
    return {"correct": correct, "canonical_answer": correct_label}


# --- GRID_CONSTRAINT_BOARD (40-Format Expansion pass -- real,
# server-authoritative connection grid; see tools/director_v04/
# grid_constraint.py's own module docstring for why this is a distinct,
# new architecture from the existing client-side GRID_BOARD) ---

def generate_grid_constraint_round(*, variant: str, seed: str) -> dict:
    from tools.director_v04 import grid_constraint
    return grid_constraint.build_package(seed, variant)


def _grid_constraint_client_view(package: dict, progress: dict) -> dict:
    answers: dict = progress.get("answers", {})
    cells_out = []
    for cell in package["cells"]:
        key = f"{cell['row_index']}:{cell['col_index']}"
        entry = {"row_index": cell["row_index"], "col_index": cell["col_index"]}
        answered = answers.get(key)
        if answered:
            entry["your_guess"] = answered["guess"]
            entry["correct"] = answered["correct"]
        cells_out.append(entry)
    total_cells = len(package["cells"])
    correct_count = sum(1 for a in answers.values() if a["correct"])
    return {
        "row_labels": package["row_labels"], "col_labels": package["col_labels"],
        "cells": cells_out, "cells_answered": len(answers), "total_cells": total_cells,
        "correct_count": correct_count, "completed": len(answers) >= total_cells,
    }


def _grid_constraint_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    from tools.director_v04 import grid_constraint
    from tools.quiz_export import engine as engine_bootstrap

    row_index, col_index = submission.get("row_index"), submission.get("col_index")
    guess_name = submission.get("guess")
    total_rows, total_cols = len(package["row_labels"]), len(package["col_labels"])
    if not isinstance(row_index, int) or not (0 <= row_index < total_rows):
        raise MechanicError(f"row_index must be an int in [0, {total_rows})")
    if not isinstance(col_index, int) or not (0 <= col_index < total_cols):
        raise MechanicError(f"col_index must be an int in [0, {total_cols})")
    answers: dict = progress.get("answers", {})
    if f"{row_index}:{col_index}" in answers:
        raise MechanicError(f"cell ({row_index}, {col_index}) has already been answered")

    c = engine_bootstrap.connect()
    try:
        correct = grid_constraint.check_cell_answer(
            c, package["domain_variant"], package["_private_row_criteria"], package["_private_col_criteria"],
            row_index, col_index, guess_name,
        )
    finally:
        c.close()
    return {
        "row_index": row_index, "col_index": col_index, "guess": guess_name, "correct": correct,
        "row_label": package["row_labels"][row_index], "col_label": package["col_labels"][col_index],
    }


# --- DRIVE_PROGRESSION (40-Format Expansion pass -- backs PERFECT_DRIVE
# (YARDAGE mode) and GOAL_LINE_STAND (DOWNS mode); see tools/director_v04/
# drive_progression.py's own module docstring for why this reuses an
# EXISTING real "guess" capability's question pool rather than new data) ---

def generate_drive_progression_round(*, variant: str, question_count: int, seed: str) -> dict:
    from tools.director_v04 import drive_progression
    cfg = VARIANTS["DRIVE_PROGRESSION"][variant]
    return drive_progression.build_package(
        seed, variant, mode=cfg["mode"], domain=cfg["domain"],
        relationship_predicate=cfg["relationship_predicate"], question_count=question_count,
    )


def _drive_progression_client_view(package: dict, progress: dict) -> dict:
    total = len(package["questions"])
    current_index = progress.get("current_index", 0)
    ended = progress.get("ended", False)
    base = {
        "mode": package["mode"], "round_index": current_index, "round_count": total, "ended": ended,
        "scored": progress.get("scored", False),
    }
    if package["mode"] == "YARDAGE":
        base["field_position_yards"] = progress.get("field_position_yards", 0)
        base["field_length_yards"] = package["field_length_yards"]
    else:
        base["downs_remaining"] = progress.get("downs_remaining", package["downs_total"])
        base["downs_total"] = package["downs_total"]
    if ended or current_index >= total:
        base["completed"] = True
        return base
    q = package["questions"][current_index]
    base.update({
        "completed": False, "prompt": q["question"], "options": list(q["options"]),
        "difficulty": q.get("difficulty"),
        "visual_template": q.get("visual_template", "DEFAULT_MULTIPLE_CHOICE"),
        "visual_payload": q.get("visual_payload"),
    })
    return base


def _drive_progression_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    current_index = progress.get("current_index", 0)
    if current_index >= len(package["questions"]):
        raise MechanicError("no more real questions in this drive")
    q = package["questions"][current_index]
    answer = str(submission.get("answer", "")).strip().lower()
    correct_label = q["options"][q["correctIndex"]]
    correct = answer == correct_label.strip().lower() or answer == str(q.get("answer", "")).strip().lower()
    result = {"correct": correct, "canonical_answer": correct_label, "mode": package["mode"]}
    if package["mode"] == "YARDAGE":
        yards_gained = _DRIVE_YARDS_BY_DIFFICULTY.get(q.get("difficulty"), 15) if correct else 0
        result["yards_gained"] = yards_gained
    return result


# --- ROSTER_BUILD (40-Format Expansion pass -- backs LINEUP_BUILDER and
# AUCTION_DRAFT/CAP_CHALLENGE; see tools/director_v04/roster_build.py's own
# module docstring) ---

def generate_roster_build_round(*, variant: str, seed: str) -> dict:
    from tools.director_v04 import roster_build

    cfg = VARIANTS["ROSTER_BUILD"][variant]
    real_variant = cfg.get("base_variant", variant)
    return roster_build.build_package(seed, real_variant, flow=cfg["flow"])


def _roster_build_client_view(package: dict, progress: dict) -> dict:
    if package.get("flow") == "FREE_SELECT":
        return _roster_build_free_select_client_view(package, progress)
    slots = package["roster_slots"]
    drafted = progress.get("drafted", [])
    drafted_ids = set(progress.get("drafted_player_ids", []))
    current_index = progress.get("current_slot_index", 0)
    completed = current_index >= len(slots)
    budgeted = package["budgeted"]
    remaining_budget = package["budget_total"] - sum(p["cost"] for p in drafted) if budgeted else None

    current_slot = None if completed else slots[current_index]
    remaining_pool = []
    if not completed:
        for p in package["players"]:
            if p["position"] != current_slot or p["player_id"] in drafted_ids:
                continue
            if budgeted and p["cost"] > remaining_budget:
                continue  # real, live affordability filter -- never offer an unaffordable real player
            remaining_pool.append({
                "player_id": p["player_id"], "display_name": p["display_name"],
                "position": p["position"], "cost": p["cost"],
            })
    return {
        "domain_variant": package["domain_variant"], "flow": "SEQUENTIAL", "roster_slots": slots,
        "current_slot_index": current_index, "current_slot": current_slot,
        "roster": drafted, "picks_made": len(drafted), "slots_total": len(slots),
        "remaining_pool_size": len(remaining_pool), "remaining_pool": remaining_pool,
        "budgeted": budgeted, "budget_total": package["budget_total"], "remaining_budget": remaining_budget,
        "completed": completed,
    }


def _roster_build_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    if package.get("flow") == "FREE_SELECT":
        return _roster_build_free_select_evaluate(package, progress, submission)
    slots = package["roster_slots"]
    current_index = progress.get("current_slot_index", 0)
    if current_index >= len(slots):
        raise MechanicError("this roster is already complete")

    player_id = submission.get("player_id")
    players_by_id = {p["player_id"]: p for p in package["players"]}
    player = players_by_id.get(player_id)
    if player is None:
        raise MechanicError(f"player_id {player_id!r} is not in this roster's real eligible pool")

    drafted_ids = set(progress.get("drafted_player_ids", []))
    if player_id in drafted_ids:
        raise MechanicError(f"player {player_id!r} has already been drafted -- no player can be drafted twice")

    current_slot = slots[current_index]
    if player["position"] != current_slot:
        raise MechanicError(f"player {player_id!r} plays {player['position']!r}, not eligible for slot {current_slot!r}")

    if package["budgeted"]:
        drafted = progress.get("drafted", [])
        spent = sum(p["cost"] for p in drafted)
        remaining_budget = package["budget_total"] - spent
        if player["cost"] > remaining_budget:
            raise MechanicError(
                f"player {player_id!r} costs {player['cost']}, exceeding the remaining real budget {remaining_budget}"
            )

    return {"slot": current_slot, "player_id": player_id, "display_name": player["display_name"],
            "position": player["position"], "cost": player["cost"]}


# --- ROSTER_BUILD, FREE_SELECT flow (Finish-10-Formats pass -- backs
# CAP_CHALLENGE's real, distinct mechanic: select/swap/remove any open slot
# freely; nothing is locked in until a final `submit_lineup` action, which
# is the one authoritative point a real over-cap or incomplete roster is
# rejected. Shares the identical real pool/cost data as the SEQUENTIAL
# (AUCTION_DRAFT) flow above -- never a second data source.) ---

def _roster_build_free_select_client_view(package: dict, progress: dict) -> dict:
    slots = package["roster_slots"]
    roster = progress.get("roster") or [None] * len(slots)
    filled_ids = {r["player_id"] for r in roster if r}
    spent = sum(r["cost"] for r in roster if r) if package["budgeted"] else 0
    remaining_budget = package["budget_total"] - spent if package["budgeted"] else None
    submitted = progress.get("submitted", False)

    pool_by_slot = {}
    if not submitted:
        for i, slot in enumerate(slots):
            candidates = []
            for p in package["players"]:
                if p["position"] != slot or p["player_id"] in filled_ids:
                    continue
                if package["budgeted"] and p["cost"] > (remaining_budget or 0):
                    continue
                candidates.append({"player_id": p["player_id"], "display_name": p["display_name"],
                                    "position": p["position"], "cost": p["cost"]})
            pool_by_slot[str(i)] = candidates

    return {
        "domain_variant": package["domain_variant"], "flow": "FREE_SELECT", "roster_slots": slots,
        "roster": roster, "slots_filled": sum(1 for r in roster if r), "slots_total": len(slots),
        "budgeted": package["budgeted"], "budget_total": package["budget_total"], "remaining_budget": remaining_budget,
        "pool_by_slot": pool_by_slot, "submitted": submitted,
        "completed": submitted,
    }


def _roster_build_free_select_evaluate(package: dict, progress: dict, submission: dict) -> dict:
    if progress.get("submitted"):
        raise MechanicError("this lineup has already been submitted")
    slots = package["roster_slots"]
    roster = list(progress.get("roster") or [None] * len(slots))
    action = submission.get("action")

    if action == "select":
        slot_index = submission.get("slot_index")
        player_id = submission.get("player_id")
        if not isinstance(slot_index, int) or not (0 <= slot_index < len(slots)):
            raise MechanicError(f"slot_index must be an int in [0, {len(slots)})")
        players_by_id = {p["player_id"]: p for p in package["players"]}
        player = players_by_id.get(player_id)
        if player is None:
            raise MechanicError(f"player_id {player_id!r} is not in this roster's real eligible pool")
        if player["position"] != slots[slot_index]:
            raise MechanicError(f"player {player_id!r} plays {player['position']!r}, not eligible for slot {slots[slot_index]!r}")
        filled_ids = {r["player_id"] for i, r in enumerate(roster) if r and i != slot_index}
        if player_id in filled_ids:
            raise MechanicError(f"player {player_id!r} is already used in another slot -- no player can fill two slots")
        if package["budgeted"]:
            spent = sum(r["cost"] for i, r in enumerate(roster) if r and i != slot_index)
            if spent + player["cost"] > package["budget_total"]:
                raise MechanicError(
                    f"selecting {player_id!r} (cost {player['cost']}) would exceed the fictional budget "
                    f"(spent {spent} + cost {player['cost']} > {package['budget_total']})"
                )
        return {"action": "select", "slot_index": slot_index, "player_id": player_id,
                "display_name": player["display_name"], "position": player["position"], "cost": player["cost"]}

    if action == "deselect":
        slot_index = submission.get("slot_index")
        if not isinstance(slot_index, int) or not (0 <= slot_index < len(slots)):
            raise MechanicError(f"slot_index must be an int in [0, {len(slots)})")
        return {"action": "deselect", "slot_index": slot_index}

    if action == "submit_lineup":
        if any(r is None for r in roster):
            missing = [slots[i] for i, r in enumerate(roster) if r is None]
            raise MechanicError(f"lineup is incomplete -- missing real picks for slot(s) {missing}")
        if package["budgeted"]:
            total_spent = sum(r["cost"] for r in roster)
            if total_spent > package["budget_total"]:
                raise MechanicError(f"final lineup costs {total_spent}, exceeding the fictional cap {package['budget_total']}")
            return {"action": "submit_lineup", "roster": roster, "total_spent": total_spent}
        return {"action": "submit_lineup", "roster": roster, "total_spent": None}

    raise MechanicError(f"action must be one of 'select', 'deselect', 'submit_lineup', got {action!r}")


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
    if taxonomy_id == "COMPARISON_BRACKET":
        return _comparison_client_view(package, progress)
    if taxonomy_id == "KNOCKOUT_BRACKET":
        return _comparison_client_view(package, progress)
    if taxonomy_id == "RELATIONSHIP_CHAIN":
        return _relationship_chain_client_view(package, progress)
    if taxonomy_id == "BRANCH_STATE":
        return _branch_state_client_view(package, progress)
    if taxonomy_id == "GRID_CONSTRAINT_BOARD":
        return _grid_constraint_client_view(package, progress)
    if taxonomy_id == "DRIVE_PROGRESSION":
        return _drive_progression_client_view(package, progress)
    if taxonomy_id == "ROSTER_BUILD":
        return _roster_build_client_view(package, progress)
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
    if taxonomy_id == "COMPARISON_BRACKET":
        result = _comparison_evaluate(package, progress, submission)
        picks = dict(progress.get("picks", {}))
        picks[result["match_id"]] = {"predicted_winner": result["predicted_winner"], "real_winner": result["real_winner"]}
        progress["picks"] = picks
        total_matchups = sum(len(r["matchups"]) for r in package["rounds"])
        progress["completed"] = len(picks) >= total_matchups
        return result, progress
    if taxonomy_id == "KNOCKOUT_BRACKET":
        result = _comparison_evaluate(package, progress, submission)
        picks = dict(progress.get("picks", {}))
        picks[result["match_id"]] = {"predicted_winner": result["predicted_winner"], "real_winner": result["real_winner"]}
        progress["picks"] = picks
        total_matchups = sum(len(r["matchups"]) for r in package["rounds"])
        progress["completed"] = len(picks) >= total_matchups
        return result, progress
    if taxonomy_id == "RELATIONSHIP_CHAIN":
        result = _relationship_chain_evaluate(package, progress.get("current_index", 0), submission)
        progress["current_index"] = progress.get("current_index", 0) + 1
        progress["completed"] = progress["current_index"] >= len(package["chains"])
        return result, progress
    if taxonomy_id == "BRANCH_STATE":
        result = _branch_state_evaluate(package, progress, submission)
        if "advanced_to" in result:
            progress["current_node"] = result["advanced_to"]
            progress["leaf_question"] = result["leaf_question"]
        else:
            progress["completed"] = True
        return result, progress
    if taxonomy_id == "GRID_CONSTRAINT_BOARD":
        result = _grid_constraint_evaluate(package, progress, submission)
        answers = dict(progress.get("answers", {}))
        answers[f"{result['row_index']}:{result['col_index']}"] = {
            "guess": result["guess"], "correct": result["correct"],
        }
        progress["answers"] = answers
        progress["completed"] = len(answers) >= len(package["cells"])
        return result, progress
    if taxonomy_id == "DRIVE_PROGRESSION":
        if progress.get("ended"):
            raise MechanicError("this drive has already ended")
        result = _drive_progression_evaluate(package, progress, submission)
        progress["current_index"] = progress.get("current_index", 0) + 1
        total = len(package["questions"])
        if package["mode"] == "YARDAGE":
            if result["correct"]:
                new_position = min(
                    package["field_length_yards"],
                    progress.get("field_position_yards", 0) + result["yards_gained"],
                )
                progress["field_position_yards"] = new_position
                if new_position >= package["field_length_yards"]:
                    progress["scored"] = True
                    progress["ended"] = True
                elif progress["current_index"] >= total:
                    progress["ended"] = True
            else:
                progress["ended"] = True
        else:  # DOWNS
            if result["correct"]:
                progress["scored"] = True
                progress["ended"] = True
            else:
                progress["downs_remaining"] = progress.get("downs_remaining", package["downs_total"]) - 1
                if progress["downs_remaining"] <= 0 or progress["current_index"] >= total:
                    progress["ended"] = True
        return result, progress
    if taxonomy_id == "ROSTER_BUILD" and package.get("flow") == "FREE_SELECT":
        result = _roster_build_free_select_evaluate(package, progress, submission)
        roster = list(progress.get("roster") or [None] * len(package["roster_slots"]))
        if result["action"] == "select":
            roster[result["slot_index"]] = {
                "player_id": result["player_id"], "display_name": result["display_name"],
                "position": result["position"], "cost": result["cost"],
            }
        elif result["action"] == "deselect":
            roster[result["slot_index"]] = None
        else:  # submit_lineup
            progress["submitted"] = True
        progress["roster"] = roster
        progress["completed"] = progress.get("submitted", False)
        return result, progress
    if taxonomy_id == "ROSTER_BUILD":
        result = _roster_build_evaluate(package, progress, submission)
        drafted = list(progress.get("drafted", []))
        drafted.append({
            "slot": result["slot"], "player_id": result["player_id"], "display_name": result["display_name"],
            "position": result["position"], "cost": result["cost"],
        })
        progress["drafted"] = drafted
        progress["drafted_player_ids"] = list(progress.get("drafted_player_ids", [])) + [result["player_id"]]
        progress["current_slot_index"] = progress.get("current_slot_index", 0) + 1
        progress["completed"] = progress["current_slot_index"] >= len(package["roster_slots"])
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
    if taxonomy_id == "COMPARISON_BRACKET":
        return {"picks": {}}
    if taxonomy_id == "KNOCKOUT_BRACKET":
        return {"picks": {}}
    if taxonomy_id == "GRID_CONSTRAINT_BOARD":
        return {"answers": {}, "completed": False}
    if taxonomy_id == "DRIVE_PROGRESSION":
        # field_position_yards/downs_remaining are deliberately absent here --
        # both are lazily defaulted from the real package's own
        # field_length_yards/downs_total (never hardcoded here, where the
        # package isn't available) the first time client_view/evaluate reads them.
        return {"current_index": 0, "ended": False, "scored": False, "completed": False}
    if taxonomy_id == "ROSTER_BUILD":
        return {"drafted": [], "drafted_player_ids": [], "current_slot_index": 0, "completed": False}
    if taxonomy_id == "BRANCH_STATE":
        return {"current_node": "root", "completed": False}
    return {"current_index": 0, "completed": False}
