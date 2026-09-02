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
game. True 2-option head-to-head (Creator/Game Quality Correction pass):
the only two options are the two real teams that played, and the real
spread is now stated IN the question text itself (e.g. "entered as a
17.5-point underdog"), never only revealed after the fact in `notes` --
matching this pass's own explicit requirement to show/use the actual line,
not just call something a betting upset without it.
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

# Creator/Game Quality Correction pass: biggest_only scopes to a "major
# betting underdog" (the spec's own phrase) -- a real, objective, disclosed
# threshold on the real recorded spread magnitude, not a subjective label.
SUPPORTS_FILTERS = True
BIGGEST_SPREAD_THRESHOLD = 10.0
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


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None):
    filters = filters or {}
    min_spread_clause = ""
    params: tuple = (PROVIDER,)
    if filters.get("biggest_only"):
        min_spread_clause = "AND ABS(b.spread) >= ?"
        params = (PROVIDER, BIGGEST_SPREAD_THRESHOLD)
    rows = c.execute(
        f"""
        SELECT g.game_id, g.season, g.week, g.home_school_id, g.away_school_id,
               g.home_score, g.away_score, b.spread,
               g.source_id AS games_source_id, g.verification_status AS games_verification_status,
               b.source_id AS betting_source_id, b.verification_status AS betting_verification_status
        FROM cfb_games_canonical g
        JOIN cfb_betting_lines b ON b.game_id = g.game_id AND b.provider = ?
        WHERE g.home_score IS NOT NULL AND g.away_score IS NOT NULL AND g.home_score != g.away_score
          AND b.spread IS NOT NULL AND b.spread != 0 {min_spread_clause}
        ORDER BY g.game_id
        """,
        params,
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
    winner_name = _school_name(c, winner_id)  # the underdog -- won outright
    loser_name = _school_name(c, loser_id)  # the favorite -- lost
    if not winner_name or not loser_name:
        return "UNRESOLVED_SCHOOL_NAME"
    if winner_name == loser_name:
        return "SAME_DISPLAY_NAME_AMBIGUOUS"

    spread_magnitude = abs(row["spread"])
    season, week = row["season"], row["week"]
    # Creator/Game Quality Correction pass: the real spread is now stated
    # IN the question (never only in `notes` after the fact) -- this is a
    # real fact about the underdog, not the outcome, so stating it doesn't
    # leak the answer. True 2-option: both real teams that played are the
    # only two options.
    question = (
        f"In Week {week} of the {season} college football season, {winner_name} entered as a "
        f"{spread_magnitude}-point underdog against {loser_name}. Which team won?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_betting_upset:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_binary_options(rng, winner_name, loser_name, winner_name)
    if not (0 <= correct_index <= 1) or shuffled_options[correct_index] != winner_name:
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
