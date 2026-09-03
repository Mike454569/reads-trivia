"""Dynamic Weekly Pick'em schedule integration -- one-time (but safely
re-runnable) schema migration.

Additive only, same discipline `safety.ensure_refresh_tables()` already
established for `refresh_runs` (see that module's own docstring): every
change here is either `ALTER TABLE ... ADD COLUMN` on an EXISTING table
(`games`, `cfb_games_canonical`) or `CREATE TABLE IF NOT EXISTS` for a
genuinely new one (`pickem_picks`) -- never a competing/duplicate schedule
table. No existing column, row, or constraint is touched or renamed.

--- WHY THESE COLUMNS ---
`status`/`winner`/`updated_at` on both schedule tables: real per-game state
the Weekly Pick'em live-grading path (`tools/director_v04/weekly_pickem.py`)
currently only ever recomputes inline from score/date on every request --
persisting it lets refresh jobs record real signals live derivation alone
can't produce (POSTPONED/CANCELED -- see `status` values below), while
`weekly_pickem.py` keeps recomputing FINAL/SCHEDULED/IN_PROGRESS/UNKNOWN
live from the row's own score/date columns as the primary source of truth
(never trusting a possibly-stale persisted value over what the same row's
score columns say right now).

`status` real, disclosed value set: SCHEDULED, IN_PROGRESS, FINAL,
POSTPONED, CANCELED, UNKNOWN. POSTPONED/CANCELED can NEVER be derived
automatically -- confirmed directly against both real upstream sources
(nflverse's games.csv, cfbfastR's schedules CSV) that neither ever
carries a postponed/canceled signal; a canceled game is simply absent as
a row, never flagged. These two values are therefore only ever set by the
new admin override (`gateway/services/admin_pickem.py`) -- disclosed as a
real data-source limitation, not hidden behind a fake auto-detection.

`neutral_site`/`home_division`/`away_division`: real fields already
present in both live upstream sources (NFL: `games.csv`'s `location`
column, Home/Neutral; CFB: cfbfastR's schedule CSV's own `neutral_site`/
`home_division`/`away_division` columns, confirmed directly against the
live 2026 season file) that neither `nfl_games_refresh.py` nor
`cfb_games_refresh.py` captured before this pass -- real data already
being fetched and silently discarded, not a new source integration.

--- pickem_picks ---
The real, structural "no duplicate picks" guarantee: a composite PRIMARY
KEY on (client_id, league, season, week, game_id) makes a second pick for
the same game by the same client in the same week a real SQLite UPSERT
target, never a second row -- see `tools/director_v04/pickem_store.py`.
`client_id` is the lightweight, unauthenticated identifier this project
already uses on the frontend for its Firestore leaderboard (`getClientId()`
in `app.js`) -- now also accepted by the Gateway, trusted by possession,
same trust model already used for round_ids/public game_ids elsewhere in
this project. No `locked_at` snapshot column: lock status is always
derived live from the game's current kickoff (same "never cache what you
can recompute" discipline `weekly_pickem.py` already lives by) -- a
reschedule changes the value being compared, never the row identity a
pick is keyed on, so "two records after a kickoff-time change" is already
structurally impossible via the game_id-keyed PK.
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import safety

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

_SCHEDULE_COLUMNS = [
    ("status", "TEXT"),
    ("winner", "TEXT"),
    ("neutral_site", "INTEGER"),
    ("home_division", "TEXT"),
    ("away_division", "TEXT"),
    ("updated_at", "TEXT"),
]


def _add_missing_columns(c, table: str) -> list[str]:
    cols = {row[1] for row in c.execute(f"PRAGMA table_info({table})")}
    added = []
    for name, decl in _SCHEDULE_COLUMNS:
        if name not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
            added.append(f"{table}.{name}")
    return added


def ensure_pickem_schema(c) -> list[str]:
    """Idempotent -- safe to call on every process start (mirrors
    `safety.ensure_refresh_tables()`'s own always-safe-to-call contract),
    not just once by a human. Returns the list of columns/tables actually
    added this call (empty on every call after the first)."""
    added = []
    added += _add_missing_columns(c, "games")
    added += _add_missing_columns(c, "cfb_games_canonical")

    existed = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pickem_picks'"
    ).fetchone()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pickem_picks (
            client_id TEXT NOT NULL,
            league TEXT NOT NULL CHECK (league IN ('NFL','CFB')),
            season INTEGER NOT NULL,
            week TEXT NOT NULL,
            game_id TEXT NOT NULL,
            predicted_winner TEXT NOT NULL,
            picked_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (client_id, league, season, week, game_id)
        )
    """)
    if existed is None:
        added.append("pickem_picks (table)")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_pickem_picks_lookup ON pickem_picks(client_id, league, season, week)"
    )
    c.commit()
    return added


def run_migration() -> dict:
    backup = safety.create_verified_backup()
    c = engine_bootstrap.connect()
    try:
        added = ensure_pickem_schema(c)
    finally:
        c.close()
    return {"status": "SUCCESS", "backup_id": backup["backup_id"], "columns_added": added}


if __name__ == "__main__":
    import json
    print(json.dumps(run_migration(), indent=2, default=str))
