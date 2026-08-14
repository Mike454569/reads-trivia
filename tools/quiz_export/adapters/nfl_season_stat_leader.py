"""NFL Season Stat Leader domain adapter (Creator-gap-audit operation).

Built on `player_season_stats` (43,819 rows, real per-player season totals),
which had zero Creator capabilities built on it despite being fully
populated. "Which player led the NFL in [stat] in [season]" -- entity is a
(season, stat_category) pair, answer is the real player who had the highest
real total in that category that season.

Real, disclosed limits found by auditing before building:
  - `interceptions` in this table is DEFENSIVE interceptions (confirmed
    directly: the top values every season belong to real cornerbacks/
    safeties with pass_yards=0, e.g. 2019's leaders were Stephon Gilmore/
    Anthony Harris/Tre'Davious White at 6 each) -- not interceptions thrown.
  - TIES are real and common, especially for small-integer categories like
    sacks/interceptions (that exact 2019 example is a real 3-way tie at 6).
    Every (season, category) pair where the top value is shared by 2+ real
    players is excluded outright -- never guessed at, same "never pick an
    arbitrary co-leader" discipline cfb_championship.py uses for the same
    real problem in a different table.
  - Distractors are drawn from the REAL next-highest finishers in that same
    season+category (not random players) -- a genuinely plausible pool,
    since every option is a player who ALSO had a real, strong season in
    that exact category.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "NFL Season Stat Leaders"
REQUIRED_SOURCE_ID = "NFLVERSE_DATA"
TRACK_ENTITY = True  # one question per real (season, category) leaderboard

MIN_SEASON = 1999
MAX_SEASON = 2025

STAT_CATEGORIES = {
    "pass_yards": "passing yards",
    "rush_yards": "rushing yards",
    "rec_yards": "receiving yards",
    "sacks": "sacks",
    "interceptions": "interceptions",
}


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(c, "player_season_stats", REQUIRED_SOURCE_ID)


def _fetch_column_rows(c, column: str):
    return c.execute(
        f"""
        SELECT ps.season AS season, ps.player_key AS player_key, cp.display_name AS display_name,
               ps.{column} AS stat_value
        FROM player_season_stats ps
        JOIN canonical_players cp ON cp.player_id = ps.player_key
        WHERE ps.{column} IS NOT NULL AND ps.{column} > 0
          AND ps.source_id = ? AND ps.verification_status = 'SOURCE_BACKED'
          AND ps.season BETWEEN ? AND ?
        """,
        (REQUIRED_SOURCE_ID, MIN_SEASON, MAX_SEASON),
    ).fetchall()


def fetch_ordered_candidates(c, seed: str):
    """Builds one candidate dict per (season, category) with a real, non-
    tied leader -- computed once per category via a single query, grouped
    in Python (kept simple/explicit rather than a SQLite window-function
    query, matching this codebase's existing style elsewhere)."""
    candidates = []
    for column, label in STAT_CATEGORIES.items():
        rows = _fetch_column_rows(c, column)
        by_season: dict = defaultdict(list)
        for r in rows:
            by_season[r["season"]].append((r["stat_value"], r["player_key"], r["display_name"]))
        for season, entries in by_season.items():
            entries.sort(key=lambda e: e[0], reverse=True)
            top_value = entries[0][0]
            leaders = [e for e in entries if e[0] == top_value]
            if len(leaders) != 1:
                continue  # real tie -- excluded, never guessed at (see module docstring)
            runner_ups = [e for e in entries[1:] if e[0] != top_value]
            # De-dup runner-up names (a player can't be their own distractor).
            seen_names = {leaders[0][2]}
            distractor_pool = []
            for _v, _k, name in runner_ups:
                if name not in seen_names:
                    distractor_pool.append(name)
                    seen_names.add(name)
                if len(distractor_pool) >= 8:
                    break
            candidates.append({
                "season": season, "column": column, "label": label,
                "leader_key": leaders[0][1], "leader_name": leaders[0][2], "leader_value": top_value,
                "distractor_pool": distractor_pool,
            })
    rng_order = engine.seeded(seed)
    rng_order.shuffle(candidates)
    return candidates


def evaluate(c, row, rng, guard):
    if len(row["distractor_pool"]) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(row["distractor_pool"], 3)

    options = [row["leader_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    season = row["season"]
    question = f"Which player led the NFL in {row['label']} in the {season} season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"nfl_stat_leader:{season}:{row['column']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_LEADERBOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, row["leader_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != row["leader_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    value_text = f"{row['leader_value']:,.0f}" if row["leader_value"] == int(row["leader_value"]) else f"{row['leader_value']:,.1f}"
    notes = f"{row['leader_name']} led the NFL with {value_text} {row['label']} in {season}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "column": row["column"], "leader_key": row["leader_key"],
            "correct_answer_text": row["leader_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real (season, category) leaderboards on record ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}. "
        f"Seasons with a real tie for the league lead in that category are excluded, never guessed at."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    by_category = Counter(q["_audit"]["column"] for q in exported)
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "category_distribution": dict(by_category),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_season_stat_leader.py -- NFL Season Stat Leaders.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Season/category:** {a['season']}, {a['column']}",
        f"- **Leader:** `{a['leader_key']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `player_season_stats`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
