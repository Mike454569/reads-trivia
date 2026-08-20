"""CFB Ranking Upset domain adapter (Creator Capability Completion pass).

Definition (kept distinct from cfb_upset_betting.py's betting-underdog
definition -- see that module's own docstring for why the two are never
merged): a real completed CFB game where the losing team was ranked in the
AP Top 25 that week and the winning team was either unranked or ranked
worse (a higher rank number) -- a real, structurally-computed upset, not a
subjective judgment call.

Built entirely on already-registered-capability tables: `cfb_games_canonical`
(real completed games, the same table CFB_GAME_RESULT/WON_GAME already
uses) LEFT JOINed to `cfb_rankings` (poll='AP Top 25', same real, single-
poll scoping cfb_ranking.py uses) for both the home and away team's real
entering rank that exact (season, week). Real candidate count measured
directly before building: 1,370 real upset games out of 6,889 candidate
games with at least one ranked side.

"Guess the team that pulled the upset" -- entity is one real upset game,
answer is the real winning (upset) team's name, drawn from `schools`
(the same canonical school-name table cfb_player_season_school.py already
uses), never a name join.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Ranking Upsets"
REQUIRED_SOURCE_ID = "SPORTSDATAVERSE_CFB"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
TRACK_ENTITY = True
POLL = "AP Top 25"
MIN_SEASON = 2002
MAX_SEASON = 2026

# Real N+1-avoidance fix, same class of defect measured and fixed in
# cfb_ranking.py this same pass: the distractor pool (schools that have
# ever appeared in a real AP Top 25 snapshot) does not depend on the
# candidate row at all beyond excluding 2 school_ids -- computed once and
# cached for the duration of one generation call, those 2 exclusions
# applied in Python per candidate instead of two full re-queries.
_pool_cache: list[tuple] | None = None
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c) -> dict:
    return {
        "cfb_games_canonical": safety.check_verification_status_safety(
            c, "cfb_games_canonical", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        ),
        "cfb_rankings": safety.check_verification_status_safety(
            c, "cfb_rankings", "CFBD_API_LIVE", "SOURCE_BACKED", where_extra=f"poll = '{POLL}'",
        ),
    }


def fetch_ordered_candidates(c, seed: str):
    global _pool_cache
    _pool_cache = None
    rows = c.execute(
        """
        SELECT g.game_id, g.season, g.week,
               g.home_school_id, g.away_school_id, g.home_score, g.away_score,
               rh.rank AS home_rank, ra.rank AS away_rank,
               g.source_id, g.verification_status
        FROM cfb_games_canonical g
        LEFT JOIN cfb_rankings rh ON rh.school_id=g.home_school_id AND rh.season=g.season
                                  AND rh.week=g.week AND rh.poll=?
        LEFT JOIN cfb_rankings ra ON ra.school_id=g.away_school_id AND ra.season=g.season
                                  AND ra.week=g.week AND ra.poll=?
        WHERE g.home_score IS NOT NULL AND g.away_score IS NOT NULL AND g.home_score != g.away_score
          AND (rh.rank IS NOT NULL OR ra.rank IS NOT NULL)
        ORDER BY g.game_id
        """,
        (POLL, POLL),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def _school_name(c, school_id: str) -> str | None:
    row = c.execute("SELECT school_name FROM schools WHERE school_id=?", (school_id,)).fetchone()
    return row["school_name"] if row else None


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"

    home_won = row["home_score"] > row["away_score"]
    winner_id = row["home_school_id"] if home_won else row["away_school_id"]
    loser_id = row["away_school_id"] if home_won else row["home_school_id"]
    winner_rank = row["home_rank"] if home_won else row["away_rank"]
    loser_rank = row["away_rank"] if home_won else row["home_rank"]

    if loser_rank is None:
        return "LOSER_NOT_RANKED_NOT_AN_UPSET"
    if winner_rank is not None and winner_rank <= loser_rank:
        return "WINNER_RANKED_BETTER_NOT_AN_UPSET"

    winner_name = _school_name(c, winner_id)
    loser_name = _school_name(c, loser_id)
    if not winner_name or not loser_name:
        return "UNRESOLVED_SCHOOL_NAME"

    # Section 19 distractor-quality fix: `schools` (805 rows) spans every
    # real division (FBS/FCS/D2/D3/NAIA) -- drawing from it unscoped
    # produced real but implausible distractors (a D3 school as an option
    # for "who upset a ranked FBS team"). Scoped instead to the 112 real
    # schools that have ever appeared in a real AP Top 25 snapshot -- the
    # same real competitive tier as the correct answer.
    global _pool_cache
    if _pool_cache is None:
        pool_rows = c.execute(
            "SELECT DISTINCT s.school_id, s.school_name FROM schools s "
            "JOIN cfb_rankings r ON r.school_id = s.school_id AND r.poll = ?",
            (POLL,),
        ).fetchall()
        _pool_cache = [(r["school_id"], r["school_name"]) for r in pool_rows if r["school_name"]]
    pool = [name for sid, name in _pool_cache if sid != winner_id and sid != loser_id]
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [winner_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    rank_phrase = f"the AP No. {loser_rank}" if loser_rank else "a ranked"
    season, week = row["season"], row["week"]
    question = (
        f"In a real college football game in Week {week} of the {season} season, an unranked or "
        f"lower-ranked team beat {rank_phrase} team. Which team pulled the upset?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_ranking_upset:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner_name:
        return "INVALID_CORRECT_INDEX"

    rank_gap = loser_rank - (winner_rank or 26)  # unranked winner treated as "worse than #25" for scoring only
    diff_score = 1 - min(abs(rank_gap), 25) / 25  # a bigger gap (winner much worse-ranked) is a MORE famous upset -> easier
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{winner_name} upset {rank_phrase.replace('the ', '')} {loser_name} in Week {week}, {season}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "week": week, "game_id": row["game_id"],
            "winner_school_id": winner_id, "loser_school_id": loser_id,
            "winner_rank": winner_rank, "loser_rank": loser_rank, "correct_answer_text": winner_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real candidate games with at least one AP-ranked side "
        f"({MIN_SEASON}-{MAX_SEASON}); exported the maximum available ({accepted_count}) rather than "
        f"loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_upset_ranking.py -- CFB Ranking Upsets.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}`, {a['season']} Week {a['week']}",
        f"- **Upset:** `{a['winner_school_id']}` (rank {a['winner_rank'] or 'unranked'}) beat "
        f"`{a['loser_school_id']}` (rank {a['loser_rank']})",
        f"- **Underlying Engine source:** `cfb_games_canonical` + `cfb_rankings`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
