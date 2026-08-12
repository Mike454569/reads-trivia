"""CFB Game Results domain adapter -- App-Wide Engine Migration operation.

The CFB mirror of nfl_game_result.py, built on `cfb_games_canonical`
(tools/data_refresh/cfb_games_refresh.py's real, automatically-refreshed
table -- 36,231 real CFB games, 36,223 with a final score, verified live
in production). Same architecture as the NFL adapter (Section F of the
mission explicitly requires this, not a separate CFB content engine):
same `guess` mechanic, same safety-then-candidates-then-evaluate shape,
same real disclosed limitation (no per-game player stats exist in this
database, only season-level -- "who won" is what `cfb_games_canonical`
itself actually proves, not a fabricated stat line).

Real, disclosed scope note (App-Wide Engine Migration operation, Section
F): no current-2026-season CFB game data exists yet in this database as
of this writing (the CFB games refresh correctly reported
`SOURCE_NOT_YET_PUBLISHED` when it ran against the real live source,
rather than fabricating a season that hasn't happened). This adapter is
proven here against real HISTORICAL CFB games already in the table --
the same code path will serve current-season games automatically the
moment cfbfastR-data actually publishes them and a refresh run picks
them up; nothing about this adapter is season-specific.
"""
from __future__ import annotations

from .. import engine, safety, difficulty as difficulty_mod, serializer

OUT_PATH = None  # served live via the Gateway AND exportable via
                 # tools/generate_quiz_engine_cfb_game_result_production.py, which passes its
                 # own out_path explicitly -- this default is never actually used
GLOBAL_NAME = "QUIZ_DATA_ENGINE_CFB_GAME_RESULT"
SEED = "reads-quiz-engine-cfb-game-result-production-v1"
ID_START = 670000
TARGET_COUNT = 300
CATEGORY = "CFB Game Results"
REQUIRED_SOURCE_ID = "SPORTSDATAVERSE_CFB"
TRACK_ENTITY = True  # one question per real game_id
MIN_SEASON = 2002  # cfb_games_canonical's real earliest season with source-backed data
MAX_SEASON = 2025  # the most recent season with real completed games as of this operation


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(
        c, "cfb_games_canonical", REQUIRED_SOURCE_ID,
        where_extra="home_score IS NOT NULL AND away_score IS NOT NULL",
    )


def _all_real_schools(c) -> dict:
    rows = c.execute("SELECT school_id, school_name FROM schools").fetchall()
    return {r["school_id"]: r["school_name"] for r in rows}


# Real production performance finding (App-Wide Engine Migration operation):
# every adapter in this codebase re-fetches its FULL candidate table on every
# single request (championship.py/draft.py/cfb_heisman.py all do this too --
# an existing, already-accepted pattern for their much smaller tables, 91-232
# rows). cfb_games_canonical has 36,184 real candidate rows -- measured live
# in production: 1.4s query + 1.4s fetchall + 0.5s shuffle = ~3.3s on EVERY
# single public game request, real enough to cause request timeouts under
# any concurrent load (confirmed: production requests started timing out
# once this mode was enabled). The set of eligible games only actually
# changes once a day (a real cfb_games_refresh.py run) -- caching the raw
# row fetch, the expensive part, for a bounded window is the same real,
# proven fix already used for check_engine_readiness()'s /v1/ready latency
# incident earlier in this same operation. The per-request seeded shuffle
# (the part that must vary per-seed for determinism) still runs fresh every
# call -- only the DB round-trip is cached.
_CANDIDATE_CACHE: dict = {"rows": None, "fetched_at": 0.0}
_CANDIDATE_CACHE_TTL_SECONDS = 600.0  # 10 min -- generous headroom over the ~once-daily real refresh cadence


def _fetch_raw_rows(c):
    import time
    cached = _CANDIDATE_CACHE["rows"]
    if cached is not None and time.monotonic() - _CANDIDATE_CACHE["fetched_at"] < _CANDIDATE_CACHE_TTL_SECONDS:
        return cached
    # Ties are vanishingly rare in modern CFB (overtime rules exist
    # specifically to prevent them) but excluded on the same principle as
    # the NFL adapter: "which team won" has no correct answer for one.
    rows = c.execute(
        "SELECT game_id, season, week, game_date, home_school_id, away_school_id, "
        "home_score, away_score, conference_game, source_id FROM cfb_games_canonical "
        "WHERE home_score IS NOT NULL AND away_score IS NOT NULL AND home_score != away_score "
        "AND season BETWEEN ? AND ? ORDER BY game_id",
        (MIN_SEASON, MAX_SEASON),
    ).fetchall()
    rows = list(rows)
    _CANDIDATE_CACHE["rows"] = rows
    _CANDIDATE_CACHE["fetched_at"] = time.monotonic()
    return rows


def fetch_ordered_candidates(c, seed: str):
    rows = list(_fetch_raw_rows(c))  # copy -- the shuffle below must never mutate the shared cache
    rng_order = engine.seeded(seed)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    if row["source_id"] != REQUIRED_SOURCE_ID:
        return "ROW_NOT_VERIFIED"

    schools = _all_real_schools(c)
    home_name = schools.get(row["home_school_id"])
    away_name = schools.get(row["away_school_id"])
    if not home_name or not away_name:
        return "SCHOOL_UNRESOLVED"

    winner_is_home = row["home_score"] > row["away_score"]
    winner_id = row["home_school_id"] if winner_is_home else row["away_school_id"]
    loser_id = row["away_school_id"] if winner_is_home else row["home_school_id"]
    winner_name = schools[winner_id]
    loser_name = schools[loser_id]

    pool = {sid: name for sid, name in schools.items() if sid not in (winner_id, loser_id)}
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTOR_POOL"
    distractor_names = rng.sample(list(pool.values()), 3)

    options = [winner_name] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    season = row["season"]
    question = f"Which team won when {away_name} played {home_name} in Week {row['week']}, {season}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_game:{row['game_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_GAME"

    shuffled_options, correct_index = serializer.finalize_options(rng, winner_name, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != winner_name:
        return "INVALID_CORRECT_INDEX"

    # Same disclosed recency heuristic as nfl_game_result.py -- no
    # puzzle_catalog row exists for this domain either.
    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    margin = abs(row["home_score"] - row["away_score"])
    conf_note = " (a conference game)" if row["conference_game"] else ""
    notes = (
        f"{winner_name} beat {loser_name} "
        f"{max(row['home_score'], row['away_score'])}-{min(row['home_score'], row['away_score'])}"
        f"{conf_note}."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "game_id": row["game_id"], "season": season, "week": row["week"],
            "home_school_id": row["home_school_id"], "away_school_id": row["away_school_id"],
            "home_score": row["home_score"], "away_score": row["away_score"], "margin": margin,
            "winner_school_id": winner_id, "correct_answer_text": winner_name,
            "difficulty_score": diff_score, "difficulty_band": band, "source_id": row["source_id"],
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count}-game pool ({MIN_SEASON}-{MAX_SEASON}, ties excluded); exported the "
        f"maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    seasons = [q["_audit"]["season"] for q in exported]
    return {
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "conference_game_count": sum(1 for q in exported if "(a conference game)" in q["notes"]),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// CFB Game Results -- served live via the Gateway (tools.data_refresh.cfb_games_refresh's",
        "// real, automatically-refreshed `cfb_games_canonical` table), not a static export.",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Game:** `{a['game_id']}` -- {a['away_school_id']} @ {a['home_school_id']}, {a['season']} "
        f"(week {a['week']}), final {a['away_score']}-{a['home_score']}",
        f"- **Engine source:** `cfb_games_canonical` row, source_id `{a['source_id']}` "
        f"(tools.data_refresh.cfb_games_refresh, real automatic production refresh)",
    ]
