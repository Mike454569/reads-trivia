"""CFB Game Box Score -- Sacks (Existing-Data Wiring pass, Phase 3: CFB
play-by-play). "Which team's defense recorded more sacks in this real CFB
game" -- the CFB mirror of nfl_game_boxscore_sacks.py, sharing its real
question shape but NOT its data source: there is no CFB team_game_stats-
style pre-aggregated box-score table in this Engine (confirmed directly),
so this aggregates real sack counts live from cfb_plays (play_type='Sack',
grouped by (game_id, defense_school_id)) rather than reading a precomputed
column. This is a genuinely new, real use of the 3.72M-row cfb_plays
table -- team-level only, deliberately: cfb_plays has no player-identity
columns at all (confirmed directly against its schema), so a player-level
"who recorded the sack" CFB capability is NOT buildable here and is not
attempted.

Games where both teams recorded the same real sack count (including
0-0) are excluded outright -- no fair winner to ask about. Real measured
pool: 14,921 of 19,937 real CFB games with any play-by-play on file have a
decisive (non-tied) sack comparison.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Game Box Scores -- Sacks"
REQUIRED_SOURCE_ID = "CFBD_API_LIVE"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
TRACK_ENTITY = True
MIN_SEASON = 2002
MAX_SEASON = 2025
MAX_FETCHED_CANDIDATES = 5000


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_plays", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
        where_extra="play_type = 'Sack'",
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        """
        WITH sacks AS (
            SELECT game_id, defense_school_id, COUNT(*) AS n
            FROM cfb_plays WHERE play_type = 'Sack' AND defense_school_id IS NOT NULL
            GROUP BY game_id, defense_school_id
        ),
        pbp_games AS (SELECT DISTINCT game_id FROM cfb_plays)
        SELECT g.game_id, g.season, g.week, g.home_school_id, g.away_school_id,
               hs.school_name AS home_name, aws.school_name AS away_name,
               COALESCE(hsk.n, 0) AS home_sacks, COALESCE(ask.n, 0) AS away_sacks
        FROM cfb_games_canonical g
        JOIN pbp_games pg ON pg.game_id = g.game_id
        JOIN schools hs ON hs.school_id = g.home_school_id
        JOIN schools aws ON aws.school_id = g.away_school_id
        LEFT JOIN sacks hsk ON hsk.game_id = g.game_id AND hsk.defense_school_id = g.home_school_id
        LEFT JOIN sacks ask ON ask.game_id = g.game_id AND ask.defense_school_id = g.away_school_id
        WHERE COALESCE(hsk.n, 0) != COALESCE(ask.n, 0)
        """
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard):
    if not row["home_name"] or not row["away_name"]:
        return "MISSING_FIELD"
    if row["home_name"] == row["away_name"]:
        return "SAME_DISPLAY_NAME_AMBIGUOUS"

    winner_name = row["home_name"] if row["home_sacks"] > row["away_sacks"] else row["away_name"]
    loser_name = row["away_name"] if winner_name == row["home_name"] else row["home_name"]
    winner_sacks = max(row["home_sacks"], row["away_sacks"])
    loser_sacks = min(row["home_sacks"], row["away_sacks"])

    question = (
        f"In the {row['season']} college football game between {row['home_name']} and {row['away_name']}, "
        f"which team's defense recorded more sacks?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_boxscore_sacks:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_binary_options(rng, row["home_name"], row["away_name"], winner_name)
    if not (0 <= correct_index <= 1) or shuffled_options[correct_index] != winner_name:
        return "INVALID_CORRECT_INDEX"

    # A bigger sack-count gap is easier to have plausibly known/guessed;
    # a 1-0 game is a real recall test.
    gap = winner_sacks - loser_sacks
    diff_score = 1 - min(gap, 8) / 8
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    loser_possessive = loser_name + ("'" if loser_name.endswith("s") else "'s")
    winner_word = "sack" if winner_sacks == 1 else "sacks"
    loser_word = "sack" if loser_sacks == 1 else "sacks"
    notes = f"{winner_name} recorded {winner_sacks} {winner_word} to {loser_possessive} {loser_sacks} {loser_word}."

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": row["season"], "week": row["week"], "game_id": row["game_id"],
            "correct_answer_text": winner_name,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real CFB games with a decisive (non-tied) sack comparison on file "
        f"({MIN_SEASON}-{MAX_SEASON}); exported the maximum available ({accepted_count}) rather than "
        f"loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_game_boxscore_sacks.py -- CFB Game Box Scores (sacks, live PBP aggregation).",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}`, {a['season']} Week {a['week']}",
        f"- **More sacks:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_plays` (live aggregation) + `cfb_games_canonical`, "
        f"verification_status `{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
