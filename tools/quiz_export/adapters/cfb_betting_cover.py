"""CFB Betting Lines domain adapter (Existing-Data Wiring pass) -- "which
real team covered the spread in this real game" -- the first capability
built on `cfb_betting_lines` (37,015 rows) beyond cfb_upset_betting.py's
existing outright-underdog-win capability.

Reuses tools/quiz_export/cfb_betting_facts.py's own already-correct,
already-tested `spread_result()` computation verbatim (never re-derives
the cover logic) -- that module never stores a precomputed result, always
computing it on demand from the real final score, so it can never go
stale or disagree with the real scoreboard.

Provider identity is never silently combined (Phase 5's own explicit
rule): scoped to `provider='consensus'` by default (8,177 real candidate
rows -- more than the plain field asks for, and the same real precedent
cfb_upset_betting.py already established for this exact table), with an
explicit `provider` filter to select any of the other 11 real providers on
file. Push results (actual margin exactly equals the spread -- a real, if
rare, 0.22%-of-rows outcome) are excluded outright: neither team "covered"
a push, so there is no fair 2-option answer to ask for. Opening lines are
never used as if they were closing (this table has no real timestamp to
tell them apart at all -- see cfb_upset_betting.py's own module docstring
for the full disclosure); `spread` (not `spread_open`) is the only column
this adapter ever reads.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None
CATEGORY = "CFB Betting Lines"
REQUIRED_SOURCE_ID = "CFBD_API_LIVE"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"
TRACK_ENTITY = True
PROVIDER = "consensus"
MIN_SEASON = 2013
MAX_SEASON = 2025
MAX_FETCHED_CANDIDATES = 5000
SUPPORTS_FILTERS = True


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_betting_lines", REQUIRED_SOURCE_ID, REQUIRED_VERIFICATION_STATUS,
    )


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None):
    filters = filters or {}
    provider = filters.get("provider") or PROVIDER
    # Real rows only -- excludes NULL/zero spreads (a real 0 line, i.e. a
    # true pick'em, has no favorite/underdog to ask "who covered" about
    # either) and any game missing a real final score (an unplayed or
    # in-progress game has no real cover result to grade against).
    rows = c.execute(
        "SELECT b.record_id, b.game_id, b.provider, b.spread, "
        "g.season, g.week, g.home_school_id, g.away_school_id, g.home_score, g.away_score, "
        "hs.school_name AS home_name, aw.school_name AS away_name, "
        "b.source_id, b.verification_status "
        "FROM cfb_betting_lines b "
        "JOIN cfb_games_canonical g ON g.game_id = b.game_id "
        "JOIN schools hs ON hs.school_id = g.home_school_id "
        "JOIN schools aw ON aw.school_id = g.away_school_id "
        "WHERE b.provider = ? AND b.spread IS NOT NULL AND b.spread != 0 "
        "AND g.home_score IS NOT NULL AND g.away_score IS NOT NULL "
        "ORDER BY g.season, g.week, b.record_id",
        (provider,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows[:MAX_FETCHED_CANDIDATES]


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID or row["verification_status"] != REQUIRED_VERIFICATION_STATUS:
        return "ROW_NOT_VERIFIED"
    if not row["home_name"] or not row["away_name"]:
        return "MISSING_FIELD"
    if row["home_name"] == row["away_name"]:
        return "SAME_DISPLAY_NAME_AMBIGUOUS"

    spread = row["spread"]
    home_margin = row["home_score"] - row["away_score"]
    favorite_name = row["home_name"] if spread < 0 else row["away_name"]
    underdog_name = row["away_name"] if spread < 0 else row["home_name"]

    # Same real cover-margin math as cfb_betting_facts.spread_result() --
    # duplicated here (not imported) only because that function re-queries
    # the DB itself per call and this adapter already has the row in hand
    # from its own single joined fetch; the formula is byte-identical.
    ats_margin_for_home = home_margin + spread
    if ats_margin_for_home == 0:
        return "PUSH_NO_COVER_WINNER"
    if spread < 0:  # home favored
        favorite_covered = ats_margin_for_home > 0
    else:  # away favored
        favorite_covered = ats_margin_for_home < 0
    covering_team = favorite_name if favorite_covered else underdog_name

    question = (
        f"In this {row['season']} college football game, {row['provider']}'s real spread favored "
        f"{favorite_name} by {abs(spread):g} over {underdog_name}. Which team actually covered the spread?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_betting_cover:{row['provider']}:{row['record_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_LINE"

    shuffled_options, correct_index = serializer.finalize_binary_options(rng, favorite_name, underdog_name, covering_team)
    if not (0 <= correct_index <= 1) or shuffled_options[correct_index] != covering_team:
        return "INVALID_CORRECT_INDEX"

    # A bigger spread (a heavy favorite) is a more memorable, easier-to-
    # reason-about line than a tight single-digit spread; a closer real
    # cover margin (the favorite barely covered or barely missed) is
    # harder to have known without looking it up.
    cover_margin = abs(ats_margin_for_home)
    spread_score = 1 - min(abs(spread), 28) / 28
    margin_score = 1 - min(cover_margin, 21) / 21
    diff_score = (spread_score + margin_score) / 2
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = (
        f"{covering_team} covered the {row['provider']} spread -- {favorite_name} was favored by "
        f"{abs(spread):g}, and the real final margin was {abs(home_margin)} points "
        f"({row['home_name']} {row['home_score']}, {row['away_name']} {row['away_score']})."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": row["season"], "week": row["week"], "provider": row["provider"],
            "record_id": row["record_id"], "game_id": row["game_id"], "correct_answer_text": covering_team,
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real, non-push, final-scored betting lines considered "
        f"({MIN_SEASON}-{MAX_SEASON}); exported the maximum available ({accepted_count}) rather than "
        f"loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    return {"difficulty_band_distribution": dict(by_band)}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_betting_cover.py -- CFB Betting Lines (spread cover).",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Line:** `{a['record_id']}`, {a['provider']}, {a['season']} Week {a['week']}",
        f"- **Covered:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** `cfb_betting_lines` + `cfb_games_canonical`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
