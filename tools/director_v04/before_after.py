"""BEFORE_AFTER -- 15-Format Expansion Part 2, format #8.

One real player who genuinely played for 2 different real teams/schools
across their own real career -- the player guesses which of the two real
teams/schools came FIRST in that real player's own real career.

Unlike PAIRWISE_COMPARE (which compares a real stat BETWEEN 2 different
real entities), this is a real chronological-ordering question about ONE
real person's own career -- there is no numeric "higher wins" comparison
here, so this is its own taxonomy rather than a 5th PAIRWISE_COMPARE
variant, to avoid quietly inverting that taxonomy's own "higher real
value wins" semantics for a fundamentally different kind of question.

Real data, 2 variants:
  - NFL_TEAM_CHANGE_BEFORE_AFTER: a real NFL player's earliest real season
    with each of 2 real NFL teams (canonical_roster_seasons,
    NFLVERSE_DATA, SOURCE_BACKED) -- whichever real team has the earlier
    real debut season is the real "before" answer.
  - CFB_SCHOOL_TRANSFER_BEFORE_AFTER: the same real idea using
    cfb_player_season_stats_real (SPORTSDATAVERSE_CFB,
    SOURCE_BACKED_DERIVED) for a real CFB player who recorded real stats
    for 2 different real schools (a real transfer, by real recorded
    stats -- not necessarily an officially declared transfer).

Every round is resampled until the two real debut seasons are genuinely
distinct -- a real tie (e.g. a genuine same-season team change) is never
silently broken or invented an order for.

Answer format: the entity_id ('A' or 'B') of whichever real team/school
came first, in a real position shuffled per round -- never sent to the
client before evaluate() runs.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "BEFORE_AFTER"
VARIANTS = frozenset({"NFL_TEAM_CHANGE_BEFORE_AFTER", "CFB_SCHOOL_TRANSFER_BEFORE_AFTER"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    # Same real scoping fix pick_the_impostor.py's own safety_check
    # already established for this exact table.
    return {
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'",
        ),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED",
        ),
    }


def _nfl_team_change_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT rs.player_id, p.display_name, rs.season, rs.team_code FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA'"
    ).fetchall()
    by_player: dict[str, list] = {}
    for r in rows:
        by_player.setdefault(r["player_id"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    player_ids = [pid for pid, hist in by_player.items() if len({h["team_code"] for h in hist}) >= 2]
    rng.shuffle(player_ids)

    rounds = []
    for pid in player_ids:
        if len(rounds) >= round_count:
            break
        history = by_player[pid]
        earliest_by_team: dict[str, int] = {}
        for h in history:
            if h["team_code"] not in earliest_by_team or h["season"] < earliest_by_team[h["team_code"]]:
                earliest_by_team[h["team_code"]] = h["season"]
        if len(earliest_by_team) < 2:
            continue
        team_codes = list(earliest_by_team.keys())
        pair = None
        for _ in range(10):
            a, b = rng.sample(team_codes, 2)
            if earliest_by_team[a] != earliest_by_team[b]:
                pair = (a, b) if earliest_by_team[a] < earliest_by_team[b] else (b, a)
                break
        if pair is None:
            continue  # every real team pairing for this player tied on debut season -- skip, never guess
        team_before, team_after = pair
        rounds.append({
            "prompt": f"{history[0]['display_name']} really played for both {team_before} and {team_after}. Which real team did they play for FIRST?",
            "entity_before": {"label": team_before, "season": earliest_by_team[team_before]},
            "entity_after": {"label": team_after, "season": earliest_by_team[team_after]},
            "notes": f"Real {history[0]['display_name']} debuted for {team_before} in "
                     f"{earliest_by_team[team_before]}, then {team_after} in {earliest_by_team[team_after]} "
                     f"(NFLVERSE_DATA, SOURCE_BACKED).",
        })
    return rounds


def _cfb_school_transfer_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.cfb_player_id, s.player_name, s.season, s.school_id, sc.school_name "
        "FROM cfb_player_season_stats_real s JOIN schools sc ON sc.school_id = s.school_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED'"
    ).fetchall()
    by_player: dict[str, list] = {}
    for r in rows:
        by_player.setdefault(r["cfb_player_id"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    player_ids = [pid for pid, hist in by_player.items() if len({h["school_id"] for h in hist}) >= 2]
    rng.shuffle(player_ids)

    rounds = []
    for pid in player_ids:
        if len(rounds) >= round_count:
            break
        history = by_player[pid]
        earliest_by_school: dict[str, tuple] = {}
        for h in history:
            if h["school_id"] not in earliest_by_school or h["season"] < earliest_by_school[h["school_id"]][0]:
                earliest_by_school[h["school_id"]] = (h["season"], h["school_name"])
        if len(earliest_by_school) < 2:
            continue
        school_ids = list(earliest_by_school.keys())
        pair = None
        for _ in range(10):
            a, b = rng.sample(school_ids, 2)
            if earliest_by_school[a][0] != earliest_by_school[b][0]:
                pair = (a, b) if earliest_by_school[a][0] < earliest_by_school[b][0] else (b, a)
                break
        if pair is None:
            continue
        school_before_id, school_after_id = pair
        season_before, name_before = earliest_by_school[school_before_id]
        season_after, name_after = earliest_by_school[school_after_id]
        rounds.append({
            "prompt": f"{history[0]['player_name']} really played for both {name_before} and {name_after}. Which real school did they play for FIRST?",
            "entity_before": {"label": name_before, "season": season_before},
            "entity_after": {"label": name_after, "season": season_after},
            "notes": f"Real {history[0]['player_name']} recorded real stats for {name_before} in "
                     f"{season_before}, then {name_after} in {season_after} (SPORTSDATAVERSE_CFB, "
                     f"SOURCE_BACKED_DERIVED).",
        })
    return rounds


def generate_rounds(seed: str, variant: str, round_count: int = 5) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_TEAM_CHANGE_BEFORE_AFTER":
            raw_rounds = _nfl_team_change_rounds(c, seed, round_count)
        else:  # CFB_SCHOOL_TRANSFER_BEFORE_AFTER
            raw_rounds = _cfb_school_transfer_rounds(c, seed, round_count)
    finally:
        c.close()

    shortfall_reason = None
    if len(raw_rounds) < round_count:
        shortfall_reason = (
            f"Only {len(raw_rounds)} of {round_count} requested real BEFORE_AFTER rounds could be built "
            f"for variant={variant!r} with two genuinely distinct real debut seasons each time; exported "
            f"the maximum available rather than include a tied or fabricated order."
        )
    return {"rounds": raw_rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {
    "NFL_TEAM_CHANGE_BEFORE_AFTER": "Before & After", "CFB_SCHOOL_TRANSFER_BEFORE_AFTER": "Before & After",
}


def build_package(seed: str, variant: str, round_count: int = 5) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP21:" + hashlib.sha256(
        f"BEFORE_AFTER|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        order = [0, 1]  # 0 = entity_before, 1 = entity_after
        engine_bootstrap.seeded(f"{seed}-shuffle-{i}").shuffle(order)
        entities = [r["entity_before"], r["entity_after"]]
        entity_a, entity_b = entities[order[0]], entities[order[1]]
        winner = "A" if order[0] == 0 else "B"
        rounds.append({
            "round_index": i, "prompt": r["prompt"],
            "entity_a": {"entity_id": "A", "label": entity_a["label"]},
            "entity_b": {"entity_id": "B", "label": entity_b["label"]},
            # Real seasons kept server-private (_prefixed) until evaluate()
            # runs -- same discipline every other mechanic's package uses.
            "_answer": winner, "_season_a": entity_a["season"], "_season_b": entity_b["season"],
            "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Tap whichever real team/school you think this real player played for FIRST "
                              "-- the real seasons are revealed once you answer.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
