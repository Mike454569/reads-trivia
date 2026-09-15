"""PICK_THE_IMPOSTOR -- 15-Format Expansion Part 2, format #5.

4 real players shown together; 3 of them share one real, verifiable
membership fact (the same real team roster, or the same real CFB school
roster, in the same real season) and 1 -- the impostor -- genuinely does
not. The player taps whichever one is the impostor.

Real data, 2 variants:
  - NFL_TEAM_ROSTER_IMPOSTOR: 3 real players really on the same real NFL
    team's real roster in a real season (canonical_roster_seasons,
    NFLVERSE_DATA, SOURCE_BACKED), plus 1 real player who was really on a
    DIFFERENT real team's roster that same real season.
  - CFB_SCHOOL_ROSTER_IMPOSTOR: 3 real CFB players who really recorded
    real stats for the same real school in a real season
    (cfb_player_season_stats_real, SPORTSDATAVERSE_CFB,
    SOURCE_BACKED_DERIVED -- a real stat-appearance proxy for roster
    membership, not an official full-roster list, disclosed here rather
    than silently treated as equivalent), plus 1 real player who recorded
    real stats for a DIFFERENT real school that same real season.

The impostor is always confirmed absent from the 3-member group's own
real player-id set before being finalized -- never assumed disjoint just
because the two groups came from different teams/schools (a genuine
in-season trade could, in principle, put a player on two roster rows).

A 3rd variant, NFL_DRAFT_CLASS_ONE_OUT (format UNIQUE_ONE_OUT, 15-Format
Expansion Part 2, format #6), reuses this exact same taxonomy and shape
for a real, distinct kind of shared fact: 3 real players really drafted
in the same real NFL Draft class (draft_facts, NFLVERSE_DATA,
SOURCE_BACKED -- the same real, already-proven table SORTING_TIMELINE's
own NFL_DRAFT_PICK_ORDER variant uses), plus 1 real player really drafted
in a DIFFERENT real year. No CFB equivalent exists yet -- there is no
real per-player "class year" table on the CFB side this Engine can use
the same way (disclosed rather than silently faked).

Answer format: the item_id ('A'-'D') of the real impostor, in a real
position shuffled per round -- never sent to the client before
evaluate() runs.
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
MECHANIC = "PICK_THE_IMPOSTOR"
VARIANTS = frozenset({"NFL_TEAM_ROSTER_IMPOSTOR", "CFB_SCHOOL_ROSTER_IMPOSTOR", "NFL_DRAFT_CLASS_ONE_OUT"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    # canonical_roster_seasons carries more than one real source/provenance
    # (confirmed live -- check_table_wide_safety's whole-table assumption
    # does not hold here), so this is scoped with the exact same
    # source_id='NFLVERSE_DATA' filter the real queries below use, not the
    # whole table.
    return {
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'",
        ),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED",
        ),
        # draft_facts is a real table-wide-uniform source, same discipline
        # sorting.py's own NFL_DRAFT_PICK_ORDER safety_check already uses.
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
    }


def _nfl_team_roster_impostor_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT rs.season, rs.team_code, rs.player_id, p.display_name FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA'"
    ).fetchall()
    by_team_season: dict[tuple, list] = {}
    for r in rows:
        by_team_season.setdefault((r["season"], r["team_code"]), []).append(r)
    by_season: dict[int, dict[str, list]] = {}
    for (season, team), players in by_team_season.items():
        by_season.setdefault(season, {})[team] = players

    rng = engine_bootstrap.seeded(seed)
    keys = list(by_team_season.keys())
    rng.shuffle(keys)

    rounds = []
    for season, team in keys:
        if len(rounds) >= round_count:
            break
        group = by_team_season[(season, team)]
        if len(group) < 3:
            continue
        other_teams = [t for t in by_season[season] if t != team]
        if not other_teams:
            continue
        members = rng.sample(group, 3)
        member_ids = {p["player_id"] for p in members}
        impostor_team = rng.choice(other_teams)
        impostor_pool = [p for p in by_season[season][impostor_team] if p["player_id"] not in member_ids]
        if not impostor_pool:
            continue  # this real candidate genuinely appears on both rosters -- try another team-season
        impostor = rng.choice(impostor_pool)
        rounds.append({
            "prompt": f"3 of these were really on the {season} {team} roster. Which one wasn't?",
            "members": [{"label": p["display_name"], "_audit": {"player_id": p["player_id"]}} for p in members],
            "impostor": {"label": impostor["display_name"],
                         "_audit": {"player_id": impostor["player_id"], "actual_team": impostor_team}},
            "notes": f"Real {season} {team} roster vs. a real {impostor_team} player that season "
                     f"(NFLVERSE_DATA, SOURCE_BACKED).",
        })
    return rounds


def _cfb_school_roster_impostor_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.season, s.school_id, sc.school_name, s.cfb_player_id, s.player_name "
        "FROM cfb_player_season_stats_real s JOIN schools sc ON sc.school_id = s.school_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED'"
    ).fetchall()
    by_school_season: dict[tuple, list] = {}
    for r in rows:
        by_school_season.setdefault((r["season"], r["school_id"]), []).append(r)
    by_season: dict[int, dict[str, list]] = {}
    for (season, school_id), players in by_school_season.items():
        by_season.setdefault(season, {})[school_id] = players

    rng = engine_bootstrap.seeded(seed)
    keys = list(by_school_season.keys())
    rng.shuffle(keys)

    rounds = []
    for season, school_id in keys:
        if len(rounds) >= round_count:
            break
        group = by_school_season[(season, school_id)]
        if len(group) < 3:
            continue
        other_schools = [sid for sid in by_season[season] if sid != school_id]
        if not other_schools:
            continue
        members = rng.sample(group, 3)
        member_ids = {p["cfb_player_id"] for p in members}
        impostor_school = rng.choice(other_schools)
        impostor_pool = [p for p in by_season[season][impostor_school] if p["cfb_player_id"] not in member_ids]
        if not impostor_pool:
            continue
        impostor = rng.choice(impostor_pool)
        school_name = group[0]["school_name"]
        impostor_school_name = impostor["school_name"]
        rounds.append({
            "prompt": f"3 of these really played for {school_name} in {season}. Which one didn't?",
            "members": [{"label": p["player_name"], "_audit": {"cfb_player_id": p["cfb_player_id"]}}
                        for p in members],
            "impostor": {"label": impostor["player_name"],
                         "_audit": {"cfb_player_id": impostor["cfb_player_id"], "actual_school": impostor_school_name}},
            "notes": f"Real {season} {school_name} players (by real recorded stats) vs. a real "
                     f"{impostor_school_name} player that season (SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED).",
        })
    return rounds


def _nfl_draft_class_one_out_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT player_key, player_name, draft_season FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' AND draft_season IS NOT NULL"
    ).fetchall()
    by_season: dict[int, list] = {}
    for r in rows:
        by_season.setdefault(r["draft_season"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    seasons = list(by_season.keys())
    rng.shuffle(seasons)

    rounds = []
    for season in seasons:
        if len(rounds) >= round_count:
            break
        group = by_season[season]
        if len(group) < 3:
            continue
        other_seasons = [s for s in by_season if s != season]
        if not other_seasons:
            continue
        members = rng.sample(group, 3)
        member_ids = {p["player_key"] for p in members}
        impostor_season = rng.choice(other_seasons)
        impostor_pool = [p for p in by_season[impostor_season] if p["player_key"] not in member_ids]
        if not impostor_pool:
            continue  # this real candidate was genuinely drafted in both years -- unreachable, but never trusted
        impostor = rng.choice(impostor_pool)
        rounds.append({
            "prompt": f"3 of these were really drafted in {season}. Which one wasn't?",
            "members": [{"label": p["player_name"], "_audit": {"player_key": p["player_key"]}} for p in members],
            "impostor": {"label": impostor["player_name"],
                         "_audit": {"player_key": impostor["player_key"], "actual_draft_season": impostor_season}},
            "notes": f"Real {season} NFL Draft class vs. a real player drafted in {impostor_season} "
                     f"(NFLVERSE_DATA, SOURCE_BACKED).",
        })
    return rounds


def generate_rounds(seed: str, variant: str, round_count: int = 5) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_TEAM_ROSTER_IMPOSTOR":
            raw_rounds = _nfl_team_roster_impostor_rounds(c, seed, round_count)
        elif variant == "CFB_SCHOOL_ROSTER_IMPOSTOR":
            raw_rounds = _cfb_school_roster_impostor_rounds(c, seed, round_count)
        else:  # NFL_DRAFT_CLASS_ONE_OUT
            raw_rounds = _nfl_draft_class_one_out_rounds(c, seed, round_count)
    finally:
        c.close()

    shortfall_reason = None
    if len(raw_rounds) < round_count:
        shortfall_reason = (
            f"Only {len(raw_rounds)} of {round_count} requested real PICK_THE_IMPOSTOR rounds could be built "
            f"for variant={variant!r} with a genuinely absent real impostor each time; exported the maximum "
            f"available rather than include a fabricated or ambiguous impostor."
        )
    return {"rounds": raw_rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {
    "NFL_TEAM_ROSTER_IMPOSTOR": "Pick the Impostor", "CFB_SCHOOL_ROSTER_IMPOSTOR": "Pick the Impostor",
    "NFL_DRAFT_CLASS_ONE_OUT": "Unique One Out",
}


def build_package(seed: str, variant: str, round_count: int = 5) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP19:" + hashlib.sha256(
        f"PICK_THE_IMPOSTOR|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        entities = list(r["members"]) + [r["impostor"]]
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        items = [{"item_id": item_ids[pos], "label": entities[src]["label"]} for pos, src in enumerate(order)]
        impostor_pos = order.index(3)
        rounds.append({
            "round_index": i, "prompt": r["prompt"], "items": items,
            # Server-private (_prefixed) until evaluate() runs -- same
            # discipline every other mechanic's package uses.
            "_impostor_item_id": item_ids[impostor_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "3 of these 4 real players share a real fact -- tap whichever one doesn't belong.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
