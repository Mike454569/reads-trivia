"""SORTING_TIMELINE -- Reliability Design Phase 6, real mechanic template #4.

A real ordering game: N items sharing one real, verified, tie-free
orderable attribute. Built from scratch (no prior adapter existed) on
already-certified real tables.

Five real, disclosed variants:
  - NFL_DRAFT_PICK_ORDER: N real players from the SAME real NFL draft class
    (draft_facts, NFLVERSE_DATA, SOURCE_BACKED), ordered by their real
    `draft_pick_overall`. Tie-free by construction -- overall picks are
    unique within a draft class, so no tie-handling logic is needed or
    invented.
  - CFB_HEISMAN_YEAR_ORDER: N real Heisman Trophy winners (cfb_award_facts,
    SOURCE_BACKED_FROM_CFB_MASTER), ordered by real `award_year`. Tie-free
    by construction -- exactly one winner per year.
  - NFL_SEASON_RUSHING_YARDS_LADDER / NFL_CAREER_PASSING_TD_LADDER /
    CFB_CAREER_RUSHING_YARDS_LADDER (STAT_LADDER format, 40-Format
    Expansion Part 2): N real players sharing one real orderable
    statistical total (player_season_stats/cfb_player_season_stats_real,
    both SOURCE_BACKED*), ordered ascending or descending by that real
    value. "The Engine must resolve ties deterministically" (the format
    spec's own words) -- rather than invent a tiebreak rule, every round is
    resampled until all sampled totals are genuinely, exactly distinct
    (same real discipline the two pre-existing variants above already use
    for their own tie-free guarantee).

A 7th and 8th variant, NFL_PLAYER_CAREER_TEAM_ORDER / CFB_PLAYER_CAREER_SCHOOL_ORDER
(MAP_THE_CAREER format, 15-Format Expansion Part 2, format #9): N real
teams/schools ONE real player's own career genuinely touched
(canonical_roster_seasons / cfb_player_season_stats_real -- the same real
tables BEFORE_AFTER already uses for a 2-item version of this same real
idea), ordered by each real team/school's real earliest season for that
player. Same tie-avoidance discipline: a round is resampled until all N
sampled real debut seasons are genuinely distinct.
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
MECHANIC = "SORTING_TIMELINE"
MIN_ITEMS = 4
MAX_ITEMS = 6

VARIANTS = frozenset({
    "NFL_DRAFT_PICK_ORDER", "CFB_HEISMAN_YEAR_ORDER",
    "NFL_SEASON_RUSHING_YARDS_LADDER", "NFL_CAREER_PASSING_TD_LADDER", "CFB_CAREER_RUSHING_YARDS_LADDER",
    "NFL_PLAYER_CAREER_TEAM_ORDER", "CFB_PLAYER_CAREER_SCHOOL_ORDER",
})
_STAT_LADDER_VARIANTS = frozenset(
    {"NFL_SEASON_RUSHING_YARDS_LADDER", "NFL_CAREER_PASSING_TD_LADDER", "CFB_CAREER_RUSHING_YARDS_LADDER"}
)
_MAP_THE_CAREER_VARIANTS = frozenset({"NFL_PLAYER_CAREER_TEAM_ORDER", "CFB_PLAYER_CAREER_SCHOOL_ORDER"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        "cfb_award_facts": safety.check_verification_status_safety(
            c, "cfb_award_facts", "READS_CFB_MASTER", "SOURCE_BACKED_FROM_CFB_MASTER",
            where_extra="award_name = 'Heisman Trophy'",
        ),
        "player_season_stats": safety.check_table_wide_safety(c, "player_season_stats", "NFLVERSE_DATA"),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED",
        ),
        # canonical_roster_seasons carries more than one real source/
        # provenance (confirmed live, same real fix pick_the_impostor.py's
        # own safety_check already established) -- scoped to the exact
        # source_id='NFLVERSE_DATA' subset the real query below uses.
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'",
        ),
    }


def _nfl_draft_pick_order_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_pick_overall FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' "
        "AND draft_season IS NOT NULL AND draft_pick_overall IS NOT NULL "
        "ORDER BY draft_season, draft_pick_overall"
    ).fetchall()
    by_season: dict[int, list] = {}
    for r in rows:
        by_season.setdefault(r["draft_season"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    seasons = sorted(by_season.keys())
    rng.shuffle(seasons)

    rounds = []
    for season in seasons:
        if len(rounds) >= round_count:
            break
        players = by_season[season]
        if len(players) < item_count:
            continue
        picks = sorted(rng.sample(players, item_count), key=lambda p: p["draft_pick_overall"])
        if len({p["draft_pick_overall"] for p in picks}) != len(picks):
            continue  # unreachable given real draft data, but never trust silently
        rounds.append({
            "variant": "NFL_DRAFT_PICK_ORDER", "season": season,
            "prompt": f"Put these {season} NFL Draft picks in order, earliest overall selection first.",
            "items_in_order": [{"label": p["player_name"], "_audit": {"player_key": p["player_key"],
                                "draft_pick_overall": p["draft_pick_overall"]}} for p in picks],
            "notes": f"Real {season} NFL Draft order by overall pick number, NFLVERSE_DATA, SOURCE_BACKED.",
        })
    return rounds


def _cfb_heisman_year_order_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT award_year, player_name, school_name FROM cfb_award_facts "
        "WHERE verification_status='SOURCE_BACKED_FROM_CFB_MASTER' AND award_name='Heisman Trophy' "
        "AND player_name IS NOT NULL ORDER BY award_year"
    ).fetchall()
    if len(rows) < item_count:
        return []
    rng = engine_bootstrap.seeded(seed)
    rounds = []
    attempts = 0
    while len(rounds) < round_count and attempts < round_count * 5:
        attempts += 1
        sample = sorted(rng.sample(rows, item_count), key=lambda r: r["award_year"])
        if len({r["award_year"] for r in sample}) != len(sample):
            continue  # unreachable (one winner per year), defensive only
        rounds.append({
            "variant": "CFB_HEISMAN_YEAR_ORDER", "season": None,
            "prompt": "Put these Heisman Trophy winners in order, earliest year first.",
            "items_in_order": [{"label": f"{r['player_name']} ({r['school_name']})",
                                "_audit": {"award_year": r["award_year"]}} for r in sample],
            "notes": "Real Heisman Trophy winners ordered by real award year, cfb_award_facts, SOURCE_BACKED_FROM_CFB_MASTER.",
        })
    return rounds


def _nfl_season_rushing_yards_ladder_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.season, s.player_key, p.display_name, s.rush_yards AS val FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' "
        "AND s.rush_yards IS NOT NULL AND s.rush_yards > 0"
    ).fetchall()
    by_season: dict[int, list] = {}
    for r in rows:
        by_season.setdefault(r["season"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    seasons = sorted(by_season.keys())
    rng.shuffle(seasons)

    rounds = []
    for season in seasons:
        if len(rounds) >= round_count:
            break
        players = by_season[season]
        if len(players) < item_count:
            continue
        sample = None
        for _ in range(8):
            candidate = rng.sample(players, item_count)
            if len({p["val"] for p in candidate}) == item_count:
                sample = candidate
                break
        if sample is None:
            continue  # this season's real values weren't all distinct for this draw -- skip, never fake a tiebreak
        ordered = sorted(sample, key=lambda p: -p["val"])
        rounds.append({
            "variant": "NFL_SEASON_RUSHING_YARDS_LADDER", "season": season,
            "prompt": f"Put these real {season} NFL rushers in order, most rushing yards first.",
            "items_in_order": [{"label": p["display_name"], "value": p["val"],
                                 "_audit": {"player_key": p["player_key"], "rush_yards": p["val"]}} for p in ordered],
            "notes": f"Real {season} NFL rushing yards, NFLVERSE_DATA, SOURCE_BACKED.",
        })
    return rounds


def _nfl_career_passing_td_ladder_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    # Restricted to players with a real QB-position roster season -- without
    # this, a non-QB's incidental trick-play passing stat (e.g. a WR with
    # 1-2 career pass_td) would surface under a prompt that names them
    # "quarterbacks", a real mislabeling risk this join closes.
    rows = c.execute(
        "SELECT s.player_key, p.display_name, SUM(s.pass_td) AS val FROM player_season_stats s "
        "JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' AND s.pass_td IS NOT NULL "
        "AND EXISTS (SELECT 1 FROM canonical_roster_seasons rs WHERE rs.player_id = s.player_key AND rs.position = 'QB') "
        "GROUP BY s.player_key HAVING val > 0"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    pool = list(rows)
    rng.shuffle(pool)

    rounds = []
    attempts = 0
    while len(rounds) < round_count and attempts < round_count * 10 and len(pool) >= item_count:
        attempts += 1
        sample = rng.sample(pool, item_count)
        if len({r["val"] for r in sample}) != item_count:
            continue  # real players who happen to share the exact same career total -- resample, never invent a tiebreak
        ordered = sorted(sample, key=lambda r: -r["val"])
        rounds.append({
            "variant": "NFL_CAREER_PASSING_TD_LADDER", "season": None,
            "prompt": "Put these real NFL quarterbacks in order, most career passing touchdowns first.",
            "items_in_order": [{"label": r["display_name"], "value": r["val"],
                                 "_audit": {"player_key": r["player_key"], "career_pass_td": r["val"]}} for r in ordered],
            "notes": "Real career passing touchdown totals, summed from player_season_stats, NFLVERSE_DATA, SOURCE_BACKED.",
        })
    return rounds


def _cfb_career_rushing_yards_ladder_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.cfb_player_id, p.display_name, SUM(s.rushing_yards) AS val FROM cfb_player_season_stats_real s "
        "JOIN canonical_cfb_players p ON p.cfb_player_id = s.cfb_player_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED' AND s.rushing_yards IS NOT NULL "
        "GROUP BY s.cfb_player_id HAVING val > 0"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    pool = list(rows)
    rng.shuffle(pool)

    rounds = []
    attempts = 0
    while len(rounds) < round_count and attempts < round_count * 10 and len(pool) >= item_count:
        attempts += 1
        sample = rng.sample(pool, item_count)
        if len({r["val"] for r in sample}) != item_count:
            continue
        ordered = sorted(sample, key=lambda r: -r["val"])
        rounds.append({
            "variant": "CFB_CAREER_RUSHING_YARDS_LADDER", "season": None,
            "prompt": "Put these real CFB players in order, most career rushing yards first.",
            "items_in_order": [{"label": r["display_name"], "value": r["val"],
                                 "_audit": {"cfb_player_id": r["cfb_player_id"], "career_rushing_yards": r["val"]}}
                                for r in ordered],
            "notes": "Real career rushing yard totals, summed from cfb_player_season_stats_real, "
                     "SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED.",
        })
    return rounds


def _nfl_player_career_team_order_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT rs.player_id, p.display_name, rs.season, rs.team_code FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA'"
    ).fetchall()
    by_player: dict[str, list] = {}
    for r in rows:
        by_player.setdefault(r["player_id"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    player_ids = [pid for pid, hist in by_player.items() if len({h["team_code"] for h in hist}) >= item_count]
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
        if len(earliest_by_team) < item_count:
            continue
        team_codes = list(earliest_by_team.keys())
        sample = None
        for _ in range(8):
            candidate = rng.sample(team_codes, item_count)
            if len({earliest_by_team[t] for t in candidate}) == item_count:
                sample = candidate
                break
        if sample is None:
            continue  # this real player's sampled real teams tied on debut season -- resample, never invent a tiebreak
        ordered = sorted(sample, key=lambda t: earliest_by_team[t])
        display_name = history[0]["display_name"]
        rounds.append({
            "variant": "NFL_PLAYER_CAREER_TEAM_ORDER", "season": None,
            "prompt": f"Put these real teams {display_name} played for in order, earliest first.",
            "items_in_order": [{"label": t, "value": earliest_by_team[t],
                                 "_audit": {"team_code": t, "debut_season": earliest_by_team[t]}} for t in ordered],
            "notes": f"Real career team history for {display_name} (NFLVERSE_DATA, SOURCE_BACKED).",
        })
    return rounds


def _cfb_player_career_school_order_rounds(c, seed: str, round_count: int, item_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.cfb_player_id, s.player_name, s.season, s.school_id, sc.school_name "
        "FROM cfb_player_season_stats_real s JOIN schools sc ON sc.school_id = s.school_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED'"
    ).fetchall()
    by_player: dict[str, list] = {}
    for r in rows:
        by_player.setdefault(r["cfb_player_id"], []).append(r)

    rng = engine_bootstrap.seeded(seed)
    player_ids = [pid for pid, hist in by_player.items() if len({h["school_id"] for h in hist}) >= item_count]
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
        if len(earliest_by_school) < item_count:
            continue
        school_ids = list(earliest_by_school.keys())
        sample = None
        for _ in range(8):
            candidate = rng.sample(school_ids, item_count)
            if len({earliest_by_school[s][0] for s in candidate}) == item_count:
                sample = candidate
                break
        if sample is None:
            continue
        ordered = sorted(sample, key=lambda s: earliest_by_school[s][0])
        player_name = history[0]["player_name"]
        rounds.append({
            "variant": "CFB_PLAYER_CAREER_SCHOOL_ORDER", "season": None,
            "prompt": f"Put these real schools {player_name} played for in order, earliest first.",
            "items_in_order": [{"label": earliest_by_school[s][1], "value": earliest_by_school[s][0],
                                 "_audit": {"school_id": s, "debut_season": earliest_by_school[s][0]}}
                                for s in ordered],
            "notes": f"Real career school history for {player_name} (SPORTSDATAVERSE_CFB, "
                     f"SOURCE_BACKED_DERIVED).",
        })
    return rounds


def _finalize_round(round_index: int, raw: dict) -> dict:
    ordered = raw["items_in_order"]
    item_ids_in_order = [f"I{i}" for i in range(len(ordered))]
    shuffled_indices = list(range(len(ordered)))
    engine_bootstrap.seeded(f"shuffle-{round_index}-{raw.get('season')}").shuffle(shuffled_indices)
    items_shuffled = [{"item_id": item_ids_in_order[i], "label": ordered[i]["label"]} for i in shuffled_indices]
    result = {
        "round_index": round_index, "variant": raw["variant"], "prompt": raw["prompt"],
        "items_shuffled": items_shuffled,
        "_private_correct_order": item_ids_in_order,
        "notes": raw["notes"],
        "_audit": {"season": raw.get("season"), "items": [it["_audit"] for it in ordered]},
    }
    # STAT_LADDER rounds carry a real numeric value per item (rushing
    # yards, career passing TDs, ...) -- exposed keyed by item_id so the
    # client can reveal real evidence after answering. TIMELINE_RIBBON's
    # pre-existing rounds have no "value" key, so this stays absent for
    # them exactly as before (backward compatible, never a regression).
    if all("value" in it for it in ordered):
        result["values_by_item_id"] = {item_ids_in_order[i]: ordered[i]["value"] for i in range(len(ordered))}
    return result


def generate_rounds(seed: str, variant: str, round_count: int = 5, item_count: int = 4) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    if not (MIN_ITEMS <= item_count <= MAX_ITEMS):
        raise ValueError(f"item_count must be in [{MIN_ITEMS}, {MAX_ITEMS}]")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_DRAFT_PICK_ORDER":
            raw_rounds = _nfl_draft_pick_order_rounds(c, seed, round_count, item_count)
        elif variant == "CFB_HEISMAN_YEAR_ORDER":
            raw_rounds = _cfb_heisman_year_order_rounds(c, seed, round_count, item_count)
        elif variant == "NFL_SEASON_RUSHING_YARDS_LADDER":
            raw_rounds = _nfl_season_rushing_yards_ladder_rounds(c, seed, round_count, item_count)
        elif variant == "NFL_CAREER_PASSING_TD_LADDER":
            raw_rounds = _nfl_career_passing_td_ladder_rounds(c, seed, round_count, item_count)
        elif variant == "CFB_CAREER_RUSHING_YARDS_LADDER":
            raw_rounds = _cfb_career_rushing_yards_ladder_rounds(c, seed, round_count, item_count)
        elif variant == "NFL_PLAYER_CAREER_TEAM_ORDER":
            raw_rounds = _nfl_player_career_team_order_rounds(c, seed, round_count, item_count)
        else:  # CFB_PLAYER_CAREER_SCHOOL_ORDER
            raw_rounds = _cfb_player_career_school_order_rounds(c, seed, round_count, item_count)
    finally:
        c.close()

    rounds = [_finalize_round(i, r) for i, r in enumerate(raw_rounds)]
    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real SORTING_TIMELINE rounds could be built "
            f"for variant={variant!r} with {item_count} items each, all genuinely tie-free; exported the "
            f"maximum available rather than include a tied or fabricated ordering."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {
    "NFL_DRAFT_PICK_ORDER": "NFL Draft Order", "CFB_HEISMAN_YEAR_ORDER": "Heisman Timeline",
    "NFL_SEASON_RUSHING_YARDS_LADDER": "NFL Rushing Ladder", "NFL_CAREER_PASSING_TD_LADDER": "NFL Passing TD Ladder",
    "CFB_CAREER_RUSHING_YARDS_LADDER": "CFB Rushing Ladder",
    "NFL_PLAYER_CAREER_TEAM_ORDER": "Map the Career", "CFB_PLAYER_CAREER_SCHOOL_ORDER": "Map the Career",
}


def build_package(seed: str, variant: str, round_count: int = 5, item_count: int = 4) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count, item_count=item_count)
    package_id = "GGP6:" + hashlib.sha256(
        f"SORTING|{variant}|{seed}|{round_count}|{item_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    is_stat_ladder = variant in _STAT_LADDER_VARIANTS
    is_map_the_career = variant in _MAP_THE_CAREER_VARIANTS
    if is_stat_ladder:
        instructions = "Rank these real players from highest to lowest -- your real evidence is revealed once you submit."
    elif is_map_the_career:
        instructions = "Put these real teams/schools in the order this real player actually played for them."
    else:
        instructions = "Put these real items in the correct order."
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": _GAME_TITLES[variant],
        "game_instructions": instructions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if result["rounds"] else "FAILED",
        "rounds": result["rounds"], "round_count": len(result["rounds"]),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
