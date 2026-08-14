"""CFB Season Stat Leader domain adapter (Creator-gap-audit operation).

Built on `cfb_player_season_stats_real` (78,651 rows) -- the CFB mirror of
nfl_season_stat_leader.py, same real-tie-exclusion and real-runner-up-
distractor discipline (see that module's docstring for the full reasoning,
not re-explained here). Notably CLEANER than the NFL table for
interceptions: this table already separates `interceptions_thrown` (a
quarterback stat) from `defensive_interceptions` (a defensive-back stat) as
two distinct real columns, so no column-meaning ambiguity to resolve here
the way nfl_season_stat_leader.py had to confirm by checking real values --
verified directly anyway (2023's real passing_yards leader is Michael
Penix Jr. at 4,881, matching the real historical record).

`player_name` is already a direct column on this table (no join needed --
unlike the NFL table, which only has `player_key` and needs a
canonical_players join for a display name).
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Season Stat Leaders"
REQUIRED_SOURCE_ID = "SPORTSDATAVERSE_CFB"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_DERIVED"
TRACK_ENTITY = True

MIN_SEASON = 2002
MAX_SEASON = 2025

STAT_CATEGORIES = {
    "passing_yards": "passing yards",
    "rushing_yards": "rushing yards",
    "receiving_yards": "receiving yards",
    "sacks": "sacks",
    "defensive_interceptions": "interceptions",
}


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_player_season_stats_real", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
    )


def _fetch_column_rows(c, column: str):
    return c.execute(
        f"""
        SELECT season, player_name, {column} AS stat_value
        FROM cfb_player_season_stats_real
        WHERE {column} IS NOT NULL AND {column} > 0
          AND source_id = ? AND verification_status = ?
          AND season BETWEEN ? AND ?
        """,
        (REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS, MIN_SEASON, MAX_SEASON),
    ).fetchall()


def fetch_ordered_candidates(c, seed: str):
    candidates = []
    for column, label in STAT_CATEGORIES.items():
        rows = _fetch_column_rows(c, column)
        by_season: dict = defaultdict(list)
        for r in rows:
            by_season[r["season"]].append((r["stat_value"], r["player_name"]))
        for season, entries in by_season.items():
            entries.sort(key=lambda e: e[0], reverse=True)
            top_value = entries[0][0]
            leaders = [e for e in entries if e[0] == top_value]
            if len(leaders) != 1:
                continue  # real tie -- excluded, never guessed at
            leader_name = leaders[0][1]
            seen_names = {leader_name}
            distractor_pool = []
            for _v, name in entries[1:]:
                if name not in seen_names:
                    distractor_pool.append(name)
                    seen_names.add(name)
                if len(distractor_pool) >= 8:
                    break
            candidates.append({
                "season": season, "column": column, "label": label,
                "leader_name": leader_name, "leader_value": top_value,
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
    question = f"Which player led college football in {row['label']} in the {season} season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_stat_leader:{season}:{row['column']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_LEADERBOARD"

    shuffled_options, correct_index = serializer.finalize_options(rng, row["leader_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != row["leader_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    value_text = f"{row['leader_value']:,.0f}" if row["leader_value"] == int(row["leader_value"]) else f"{row['leader_value']:,.1f}"
    notes = f"{row['leader_name']} led college football with {value_text} {row['label']} in {season}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "column": row["column"], "correct_answer_text": row["leader_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real (season, category) leaderboards on record ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}. "
        f"Seasons with a real tie for the national lead in that category are excluded, never guessed at."
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
        "// tools/quiz_export/adapters/cfb_season_stat_leader.py -- CFB Season Stat Leaders.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Season/category:** {a['season']}, {a['column']}",
        f"- **Leader:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_player_season_stats_real`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
