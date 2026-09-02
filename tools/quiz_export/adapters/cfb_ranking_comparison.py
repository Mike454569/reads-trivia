"""CFB Ranking Comparison domain adapter (Creator/Game Quality Correction
pass) -- answers the real request directly: "Give me two ranked teams and
make me choose which one was ranked higher." A true 2-option head-to-head,
NOT "which team was ranked No. X" (that's cfb_ranking.py/RANKED_IN_POLL, a
different, single-entity question).

Built on the same `cfb_rankings` table as cfb_ranking.py (AP Top 25 only,
same real-data discipline: season_type='regular' only, so the question's
"that week" framing is always honest). Two real schools are drawn from the
SAME real (season, week) snapshot with two different real ranks -- "ranked
higher" means the smaller rank number (No. 3 is ranked higher than No. 12),
which is unambiguous and needs no tie handling (AP Top 25 has no duplicate
ranks within one real snapshot).
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
MAX_FETCHED_CANDIDATES = 5000

# Same real N+1-avoidance discipline as cfb_ranking.py's own _pool_cache --
# partner rows for a given (season, week) are fetched once, reused across
# every candidate row from that same snapshot.
_snapshot_cache: dict[tuple, list] = {}


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_rankings", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra=f"poll = '{POLL}' AND season_type = 'regular'",
    )


def fetch_ordered_candidates(c, seed: str):
    _snapshot_cache.clear()
    rows = c.execute(
        "SELECT record_id, season, week, rank, school_id, school_name_raw, source_id, verification_status "
        "FROM cfb_rankings WHERE poll = ? AND season_type = 'regular' AND rank BETWEEN 1 AND 25 "
        "ORDER BY season, week, rank",
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

    season, week = row["season"], row["week"]
    cache_key = (season, week)
    snapshot = _snapshot_cache.get(cache_key)
    if snapshot is None:
        snapshot = c.execute(
            "SELECT record_id, rank, school_name_raw FROM cfb_rankings "
            "WHERE poll = ? AND season_type = 'regular' AND season = ? AND week = ? AND rank BETWEEN 1 AND 25",
            (POLL, season, week),
        ).fetchall()
        _snapshot_cache[cache_key] = snapshot

    partners = [r for r in snapshot if r["record_id"] != row["record_id"] and r["rank"] != row["rank"]]
    if not partners:
        return "NO_SAME_WEEK_PARTNER"
    partner = partners[rng.randrange(len(partners))]

    team_a_name, team_a_rank = row["school_name_raw"], row["rank"]
    team_b_name, team_b_rank = partner["school_name_raw"], partner["rank"]
    if team_a_name == team_b_name:
        return "SAME_DISPLAY_NAME_AMBIGUOUS"

    higher_name = team_a_name if team_a_rank < team_b_rank else team_b_name  # lower number = ranked higher

    question = (
        f"In the AP Top 25 entering Week {week} of the {season} college football season, "
        f"{team_a_name} and {team_b_name} were both ranked. Which team was ranked higher?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_ranking_cmp:{season}:{week}:{'|'.join(sorted([str(row['record_id']), str(partner['record_id'])]))}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_PAIR"

    shuffled_options, correct_index = serializer.finalize_binary_options(rng, team_a_name, team_b_name, higher_name)
    if not (0 <= correct_index <= 1) or shuffled_options[correct_index] != higher_name:
        return "INVALID_CORRECT_INDEX"

    # Harder when both ranks are close together (No. 4 vs No. 5 is a real
    # recall test; No. 1 vs No. 25 barely requires knowing either ranking).
    rank_gap = abs(team_a_rank - team_b_rank)
    diff_score = 1 - min(rank_gap, 24) / 24
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    hi_rank, lo_rank = min(team_a_rank, team_b_rank), max(team_a_rank, team_b_rank)
    notes = f"{higher_name} was ranked No. {hi_rank}, compared to No. {lo_rank}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "week": week, "correct_answer_text": higher_name,
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
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_ranking_comparison.py -- CFB Ranking Comparison (AP Top 25).",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Snapshot:** {a['season']} Week {a['week']} (AP Top 25)",
        f"- **Ranked higher:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_rankings`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
