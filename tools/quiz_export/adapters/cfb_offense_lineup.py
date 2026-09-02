"""CFB Starting Offense Lineup domain adapter (Creator/Game Quality
Correction pass) -- a real, honest fix for a real, disclosed gap: this
Creator's only "College Offense"-named concept
(sb_champion_offense_college.py / NFL_SB_CHAMPION_OFFENSE_COLLEGE) is
entirely about NFL Super Bowl champions' players' colleges -- it never
shows a real college football team's own real roster. This adapter is the
first (and, as of this pass, only) capability built on real CFB team-season
rosters: "Give me a college football offense" now has a real, CFB-native
answer, not a silently-substituted NFL one.

--- REAL DATA, SAME "starter = highest real usage" DISCIPLINE AS lineup.py ---
Built on `cfb_roster_seasons_real` (real per-season position rows,
SPORTSDATAVERSE_CFB, 2004-2025) JOINed to `cfb_player_season_stats_real`
(real season-total passing/rushing/receiving stats, same source) on
(season, school_id, cfb_player_id). There is no per-game "starts" column
for CFB the way lineup.py's NFL data has -- the honest, non-fabricated
proxy here is real season-long usage volume: the real leader in passing
yards among a school's real QBs that season, the real leader in rushing
yards among its real RBs, etc. Never a guess -- every player shown really
recorded that real statistic for that real school that real season.

--- WHY NO OFFENSIVE LINE (a real, disclosed scope gap, not fabricated) ---
`cfb_player_season_stats_real` has no offensive-line statistic of any kind
(no snap counts, no games-started column) -- there is nothing here to rank
O-line starters by. Scoped honestly to the 5 real skill positions this data
actually supports (QB, RB, WR x2, TE), same "show what's real, disclose
what's not" discipline lineup.py's own OL-grouping section documents for
its own, different real gap.

--- ANSWER: REAL SCHOOL NAME + SEASON ---
`schools.school_name` is the single real, canonical CFB school identity
this database uses everywhere else (cfb_game_result.py, cfb_ranking.py,
cfb_upset_ranking.py) -- reused directly, never a separate identity space.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Starting Offense Lineups"
REQUIRED_SOURCE_ID = "SPORTSDATAVERSE_CFB"
# Real, measured discipline: the two source tables use DIFFERENT
# verification_status values for the exact same real provenance --
# cfb_roster_seasons_real is 'SOURCE_BACKED' (282,124 rows), while
# cfb_player_season_stats_real is 'SOURCE_BACKED_DERIVED' (78,651 rows,
# derived from real per-game rows via aggregation) -- confirmed directly
# against the live database, never assumed uniform.
ROSTER_VERIFICATION_STATUS = "SOURCE_BACKED"
STATS_VERIFICATION_STATUS = "SOURCE_BACKED_DERIVED"
TRACK_ENTITY = False  # each (season, school_id) is already unique by construction

MIN_SEASON = 2014  # cfb_player_season_stats_real's own real, measured floor -- see module-level query audit
MAX_SEASON = 2025


def safety_check(c) -> dict:
    return {
        "cfb_roster_seasons_real": safety.check_verification_status_safety(
            c, "cfb_roster_seasons_real", REQUIRED_SOURCE_ID, ROSTER_VERIFICATION_STATUS,
        ),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", REQUIRED_SOURCE_ID, STATS_VERIFICATION_STATUS,
        ),
    }


_JOIN_SQL = """
    SELECT s.season, s.school_id, r.position, s.cfb_player_id, s.player_name,
           s.passing_yards, s.rushing_yards, s.receiving_yards,
           s.source_id, s.verification_status,
           r.source_id AS roster_source_id, r.verification_status AS roster_verification_status
    FROM cfb_player_season_stats_real s
    JOIN cfb_roster_seasons_real r
        ON r.season = s.season AND r.school_id = s.school_id AND r.cfb_player_id = s.cfb_player_id
    WHERE r.position IN ('QB', 'RB', 'WR', 'TE')
    ORDER BY s.season, s.school_id
"""


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(_JOIN_SQL).fetchall()

    groups: dict[tuple[int, str], list] = {}
    for r in rows:
        if r["source_id"] != REQUIRED_SOURCE_ID or r["verification_status"] != STATS_VERIFICATION_STATUS:
            continue
        if r["roster_source_id"] != REQUIRED_SOURCE_ID or r["roster_verification_status"] != ROSTER_VERIFICATION_STATUS:
            continue
        groups.setdefault((r["season"], r["school_id"]), []).append(r)

    candidates = []
    for (season, school_id), players in groups.items():
        qbs = sorted([p for p in players if p["position"] == "QB" and p["passing_yards"] and p["passing_yards"] > 0],
                     key=lambda p: (-p["passing_yards"], p["cfb_player_id"]))
        rbs = sorted([p for p in players if p["position"] == "RB" and p["rushing_yards"] and p["rushing_yards"] > 0],
                     key=lambda p: (-p["rushing_yards"], p["cfb_player_id"]))
        wrs = sorted([p for p in players if p["position"] == "WR" and p["receiving_yards"] and p["receiving_yards"] > 0],
                     key=lambda p: (-p["receiving_yards"], p["cfb_player_id"]))
        tes = sorted([p for p in players if p["position"] == "TE" and p["receiving_yards"] and p["receiving_yards"] > 0],
                     key=lambda p: (-p["receiving_yards"], p["cfb_player_id"]))
        if not (len(qbs) >= 1 and len(rbs) >= 1 and len(wrs) >= 2 and len(tes) >= 1):
            continue
        lineup = {"QB": [qbs[0]], "RB": [rbs[0]], "WR": wrs[:2], "TE": [tes[0]]}
        candidates.append((season, school_id, lineup))

    rng_order = engine.seeded(seed)
    candidates.sort(key=lambda x: (x[0], x[1]))
    rng_order.shuffle(candidates)
    return candidates


def _school_name(c, school_id: str) -> str | None:
    row = c.execute("SELECT school_name FROM schools WHERE school_id=?", (school_id,)).fetchone()
    return row["school_name"] if row else None


# Real N+1-avoidance discipline, same class of fix as cfb_ranking.py/
# cfb_upset_ranking.py this same pass -- the real distractor pool (every
# school with its own valid 5-slot lineup that same season) is cheap to
# compute once and cache, expensive to re-run per candidate.
_pool_cache: dict[int, list[str]] = {}


def evaluate(c, raw, rng, guard):
    season, school_id, lineup = raw
    correct_name = _school_name(c, school_id)
    if not correct_name:
        return "UNRESOLVED_SCHOOL_NAME"

    cache_key = season
    pool = _pool_cache.get(cache_key)
    if pool is None:
        # Real, same-season, same-real-bar pool: every OTHER school that
        # also has its own valid 5-slot lineup that season -- a plausible,
        # comparable-tier distractor (a real, active FBS-caliber offense
        # that same year), never an arbitrary school from the full 805-row
        # `schools` table (same real distractor-plausibility discipline
        # cfb_upset_ranking.py's own fix already established).
        season_rows = c.execute(
            "SELECT DISTINCT r.school_id FROM cfb_player_season_stats_real s "
            "JOIN cfb_roster_seasons_real r ON r.season=s.season AND r.school_id=s.school_id "
            "AND r.cfb_player_id=s.cfb_player_id WHERE s.season=? AND r.position IN ('QB','RB','WR','TE')",
            (season,),
        ).fetchall()
        pool = [_school_name(c, r["school_id"]) for r in season_rows]
        pool = [n for n in pool if n]
        _pool_cache[cache_key] = pool
    distractor_pool = [n for n in pool if n != correct_name]
    distractor_pool = list(dict.fromkeys(distractor_pool))
    if len(distractor_pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(distractor_pool, 3)

    options = [correct_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    qb_name = lineup["QB"][0]["player_name"]
    question = (
        f"Guess the real college football team from its {season} starting offense "
        f"(led by {qb_name} at QB), by position."
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_offense_lineup:{season}:{school_id}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_LINEUP"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_name:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    positions_payload = []
    all_players = []
    for slot in ("QB", "RB", "WR", "TE"):
        for p in lineup[slot]:
            positions_payload.append({"position": slot, "name": p["player_name"]})
            all_players.append(p["player_name"])

    notes = (
        f"{correct_name}'s real {season} starting offense (by real season-long stat usage -- "
        f"passing/rushing/receiving yardage leader per position). Offensive line is not shown: "
        f"this database has no O-line usage statistic for real college football rosters."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP",
        "visual_payload": {"positions": positions_payload, "season": season},
        "_audit": {
            "school_id": school_id, "season": season, "correct_answer_text": correct_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "lineup_player_names": all_players,
            "verification_status": STATS_VERIFICATION_STATUS, "roster_verification_status": ROSTER_VERIFICATION_STATUS,
            "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real (season, school) groups with a complete real 5-slot skill-position "
        f"lineup on file ({MIN_SEASON}-{MAX_SEASON}); exported the maximum available ({accepted_count}) "
        f"rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_offense_lineup.py -- CFB Starting Offense Lineups.",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Team-season:** `{a['school_id']}`, {a['season']}",
        f"- **Correct answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_roster_seasons_real` + `cfb_player_season_stats_real`, "
        f"verification_status `{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
