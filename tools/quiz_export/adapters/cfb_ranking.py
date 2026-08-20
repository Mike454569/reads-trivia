"""CFB Rankings/Polls domain adapter (Creator Capability Completion pass).

Built on `cfb_rankings` (31,801 rows, SOURCE_BACKED/CFBD_API_LIVE, seasons
2002-2026, real AP/Coaches/CFP/FCS/D2/D3/BCS poll snapshots).  Scoped to
`poll='AP Top 25'` (9,680 rows) -- the one real, single, unambiguous "the
rankings" concept most requests mean (matching NFL_ALL_PRO's own
is_ap=1-scoping precedent: this table also carries several other real,
distinct polls, never silently combined into one implied ranking).

"Which team was ranked No. [rank] in the AP Top 25 entering Week [week] of
the [season] season" -- entity is one real ranking row, answer is the real
school name as recorded by the source. `school_id` matches
`cfb_games_canonical.home_school_id`/`away_school_id`'s own format
(`CFB_SCHOOL_X`), confirmed directly, though this capability does not need
that join -- see `cfb_upset_ranking.py` for the one that does.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Rankings"
REQUIRED_SOURCE_ID = "CFBD_API_LIVE"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
TRACK_ENTITY = True
POLL = "AP Top 25"
MIN_SEASON = 2002
MAX_SEASON = 2026

# Real, measured N+1 fix (Creator Capability Completion pass): evaluate()'s
# distractor pool query re-scanned cfb_rankings (31,801 rows, no index on
# poll/season/week at all -- confirmed via EXPLAIN QUERY PLAN) once per
# candidate. Measured directly: 5 rounds took ~50s before this fix, well
# past the real 45s admin generation timeout. Cached per (season, week) for
# the duration of one generation call only -- reset at the top of
# fetch_ordered_candidates(). Also caps total candidates considered, the
# same real safeguard compiler.py's own RelationshipSpec.max_fetched_candidates
# uses, since this table's AP-Top-25 subset alone is 9,680 rows.
_pool_cache: dict[tuple, list[str]] = {}
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_rankings", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra=f"poll = '{POLL}'",
    )


def fetch_ordered_candidates(c, seed: str):
    _pool_cache.clear()
    rows = c.execute(
        "SELECT record_id, season, week, rank, school_id, school_name_raw, source_id, verification_status "
        "FROM cfb_rankings WHERE poll = ? AND rank BETWEEN 1 AND 25 ORDER BY season, week, rank",
        (POLL,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if not row["school_name_raw"]:
        return "MISSING_FIELD"

    season, week, rank = row["season"], row["week"], row["rank"]
    correct_school = row["school_name_raw"]

    cache_key = (season, week)
    cached_pool = _pool_cache.get(cache_key)
    if cached_pool is None:
        pool_rows = c.execute(
            "SELECT DISTINCT school_name_raw FROM cfb_rankings "
            "WHERE poll = ? AND season = ? AND week = ? AND rank BETWEEN 1 AND 25",
            (POLL, season, week),
        ).fetchall()
        cached_pool = [r["school_name_raw"] for r in pool_rows]
        _pool_cache[cache_key] = cached_pool
    pool = [n for n in cached_pool if n != correct_school]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [correct_school] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which team was ranked No. {rank} in the AP Top 25 entering Week {week} of the {season} college football season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_ranking:{row['record_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_RANKING_ROW"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_school, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_school:
        return "INVALID_CORRECT_INDEX"

    # Recency + rank both drive difficulty: an older season OR a lower-
    # profile (higher-numbered) ranking is harder to know off the top of
    # your head than a recent #1-5 team.
    recency_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    rank_score = (rank - 1) / 24
    diff_score = (recency_score + rank_score) / 2
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{correct_school} was ranked No. {rank} in the AP Top 25 entering Week {week} of the {season} season."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "week": week, "rank": rank, "record_id": row["record_id"],
            "school_id": row["school_id"], "correct_answer_text": correct_school,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real AP Top 25 ranking records on file ({MIN_SEASON}-{MAX_SEASON}); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_ranking.py -- CFB Rankings (AP Top 25).",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Ranking:** `{a['record_id']}`, {a['season']} Week {a['week']}, rank {a['rank']}",
        f"- **School:** `{a['school_id']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `cfb_rankings`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
