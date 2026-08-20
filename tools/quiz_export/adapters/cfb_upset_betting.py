"""CFB Betting Upset domain adapter (Creator Capability Completion pass).

Definition (kept distinct from cfb_upset_ranking.py's ranking-based
definition): a real completed CFB game where the pregame betting
underdog -- per `cfb_betting_lines`, `provider='consensus'` (the one
real, aggregated-across-books line, not an arbitrary single sportsbook --
8,183 of 37,015 real lines) -- won outright. `spread` is CFBD's real,
home-team-relative spread value (negative = home favored) as recorded at
whatever point the source captured it; this module calls it "the real
betting line" and never claims "closing line" status, since the source
does not itself label `spread` vs `spread_open` as closing vs opening
beyond their column names. Real candidate count measured directly before
building: 1,874 real betting-upset games out of 8,177 candidates with a
real consensus spread.

"Guess the underdog that won outright" -- entity is one real betting-upset
game, answer is the real winning (underdog) team's name, drawn from
`schools`, distractors scoped to real schools that have appeared in a
real CFBD betting line at all (same real, plausible tier as the correct
answer -- see cfb_upset_ranking.py's own distractor-quality fix for the
same real problem with an unscoped `schools` pool).
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Betting Upsets"
REQUIRED_SOURCE_ID = "CFBD_API_LIVE"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
GAMES_SOURCE_ID = "SPORTSDATAVERSE_CFB"
PROVIDER = "consensus"
TRACK_ENTITY = True
MIN_SEASON = 2013
MAX_SEASON = 2025

# Real N+1-avoidance fix, same class of defect measured and fixed in
# cfb_ranking.py this same pass: the "other real betting-upset winners"
# distractor pool is a real, candidate-independent triple-JOIN (aside from
# excluding the current game's 2 school_ids) -- computed once and cached
# for the duration of one generation call, those 2 exclusions applied in
# Python per candidate instead of re-running the full join every time.
_pool_cache: list[tuple] | None = None
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c) -> dict:
    return {
        "cfb_betting_lines": safety.check_verification_status_safety(
            c, "cfb_betting_lines", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
            where_extra=f"provider = '{PROVIDER}'",
        ),
        "cfb_games_canonical": safety.check_verification_status_safety(
            c, "cfb_games_canonical", GAMES_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        ),
    }


def fetch_ordered_candidates(c, seed: str):
    global _pool_cache
    _pool_cache = None
    rows = c.execute(
        """
        SELECT g.game_id, g.season, g.week, g.home_school_id, g.away_school_id,
               g.home_score, g.away_score, b.spread,
               g.source_id AS games_source_id, g.verification_status AS games_verification_status,
               b.source_id AS betting_source_id, b.verification_status AS betting_verification_status
        FROM cfb_games_canonical g
        JOIN cfb_betting_lines b ON b.game_id = g.game_id AND b.provider = ?
        WHERE g.home_score IS NOT NULL AND g.away_score IS NOT NULL AND g.home_score != g.away_score
          AND b.spread IS NOT NULL AND b.spread != 0
        ORDER BY g.game_id
        """,
        (PROVIDER,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def _school_name(c, school_id: str) -> str | None:
    row = c.execute("SELECT school_name FROM schools WHERE school_id=?", (school_id,)).fetchone()
    return row["school_name"] if row else None


def evaluate(c, row, rng, guard):
    if row["games_source_id"] != GAMES_SOURCE_ID or row["games_verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "GAME_ROW_NOT_VERIFIED"
    if row["betting_source_id"] != REQUIRED_SOURCE_ID or row["betting_verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "BETTING_ROW_NOT_VERIFIED"

    home_favored = row["spread"] < 0
    home_won = row["home_score"] > row["away_score"]
    if home_favored == home_won:
        return "FAVORITE_WON_NOT_AN_UPSET"

    winner_id = row["home_school_id"] if home_won else row["away_school_id"]
    loser_id = row["away_school_id"] if home_won else row["home_school_id"]
    winner_name = _school_name(c, winner_id)
    loser_name = _school_name(c, loser_id)
    if not winner_name or not loser_name:
        return "UNRESOLVED_SCHOOL_NAME"

    # Section 19 distractor-quality fix (same real problem
    # cfb_upset_ranking.py's own fix addresses): scoping to "any school
    # that ever appears in a betting line" let real FCS buy-game opponents
    # (Arkansas-Pine Bluff, Lehigh, ...) show up as options next to a real
    # major-conference upset winner -- implausible by comparison. Scoped
    # instead to schools that have themselves won at least one other real
    # betting upset by this exact same definition -- the same real,
    # comparable competitive tier as the correct answer.
    global _pool_cache
    if _pool_cache is None:
        other_upset_winner_rows = c.execute(
            """
            SELECT DISTINCT s.school_name,
                   CASE WHEN g2.home_score > g2.away_score THEN g2.home_school_id ELSE g2.away_school_id END AS wid
            FROM cfb_games_canonical g2
            JOIN cfb_betting_lines b2 ON b2.game_id = g2.game_id AND b2.provider = ?
            JOIN schools s ON s.school_id = (
                CASE WHEN g2.home_score > g2.away_score THEN g2.home_school_id ELSE g2.away_school_id END
            )
            WHERE g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL AND g2.home_score != g2.away_score
              AND b2.spread IS NOT NULL AND b2.spread != 0
              AND ((b2.spread < 0) != (g2.home_score > g2.away_score))
            """,
            (PROVIDER,),
        ).fetchall()
        _pool_cache = [(r["wid"], r["school_name"]) for r in other_upset_winner_rows if r["school_name"]]
    pool = [name for wid, name in _pool_cache if wid not in (winner_id, loser_id)]
    pool = list(dict.fromkeys(pool))  # de-dup while preserving order, no set() nondeterminism before rng.sample
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(pool, 3)

    options = [winner_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    spread_magnitude = abs(row["spread"])
    season, week = row["season"], row["week"]
    question = (
        f"In a real college football game in Week {week} of the {season} season, the real pregame "
        f"betting underdog won outright. Which team was the underdog that won?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_betting_upset:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner_name:
        return "INVALID_CORRECT_INDEX"

    # A bigger spread the underdog overcame is a more famous/memorable
    # upset -> easier; capped at 21 points (a real, generous ceiling for
    # this sport) to keep the score bounded.
    diff_score = 1 - min(spread_magnitude, 21) / 21
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = f"{winner_name} won outright as a {spread_magnitude}-point underdog against {loser_name} in Week {week}, {season}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "week": week, "game_id": row["game_id"],
            "winner_school_id": winner_id, "loser_school_id": loser_id, "spread": row["spread"],
            "correct_answer_text": winner_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real candidate games with a real consensus betting line "
        f"({MIN_SEASON}-{MAX_SEASON}); exported the maximum available ({accepted_count}) rather than "
        f"loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_upset_betting.py -- CFB Betting Upsets.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}`, {a['season']} Week {a['week']}",
        f"- **Upset:** `{a['winner_school_id']}` won outright as an underdog (consensus spread "
        f"{a['spread']}) over `{a['loser_school_id']}`",
        f"- **Underlying Engine source:** `cfb_games_canonical` + `cfb_betting_lines`, "
        f"verification_status `{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
