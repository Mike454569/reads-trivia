"""Dynamic Weekly Pick'em pass -- real, persistent, per-user picks storage.

Replaces game_state.py's round-scoped JSON blob for Pick'em specifically
(that model has no user dimension at all -- every caller requesting the
same (variant, season, week) with the default seed shared the exact same
picks, confirmed a real defect this pass fixes). `pickem_picks` lives in
the SAME production Engine database every other real table already lives
in (per explicit project direction: no separate SQLite file for Pick'em),
via `pickem_schema_migration.py`'s additive migration.

This is a deliberate, disclosed exception to this Gateway's own standing
read-only discipline (see tools/quiz_export/engine.py's connect()
docstring -- "the entire Gateway generation path performs ZERO writes to
the Engine database... every real call site is already read-only in
practice"). Writes here are small, single-row upserts on a
`busy_timeout`-protected connection (engine.connect() already sets
PRAGMA busy_timeout=5000 on every connection) -- safe at this app's real
traffic scale, and never touching the bulk schedule tables those refresh
jobs own.

`client_id`: the lightweight, unauthenticated identifier this project
already uses on the frontend for its Firestore leaderboard (app.js's
getClientId()) -- trusted by possession, same trust model this Gateway
already uses for round_ids/public game_ids elsewhere. Real, structural
"no duplicate picks" guarantee comes from pickem_picks's own composite
PRIMARY KEY (client_id, league, season, week, game_id) -- a second pick
for the same game is a real UPSERT target, never a second row.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.data_refresh.pickem_schema_migration import ensure_pickem_schema  # noqa: E402

CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,64}$")


class InvalidClientId(ValueError):
    pass


def _validate_client_id(client_id: str) -> None:
    if not isinstance(client_id, str) or not CLIENT_ID_RE.match(client_id):
        raise InvalidClientId(f"invalid client_id format: {client_id!r}")


def upsert_pick(*, client_id: str, league: str, season: int, week, game_id: str, predicted_winner: str) -> dict:
    """Real UPSERT, not insert-only -- a pick may be changed until kickoff
    (the lock itself is enforced one layer up, in
    tools/director_v02/mechanic_engine.py's _weekly_pickem_evaluate(),
    against the SAME live schedule data every other grading check already
    uses -- never re-implemented here)."""
    _validate_client_id(client_id)
    now = datetime.now(timezone.utc).isoformat()
    c = engine_bootstrap.connect()
    try:
        ensure_pickem_schema(c)
        c.execute(
            "INSERT INTO pickem_picks(client_id,league,season,week,game_id,predicted_winner,picked_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(client_id,league,season,week,game_id) DO UPDATE SET "
            "predicted_winner=excluded.predicted_winner, updated_at=excluded.updated_at",
            (client_id, league, season, str(week), game_id, predicted_winner, now, now),
        )
        c.commit()
    finally:
        c.close()
    return {"game_id": game_id, "predicted_winner": predicted_winner, "updated_at": now}


def picks_for(*, client_id: str, league: str, season: int, week) -> dict:
    """Returns {game_id: {"predicted_winner":..., "picked_at":...}} -- the
    IDENTICAL shape mechanic_engine.py's own progress["picks"] already
    uses, so _weekly_pickem_client_view()/_weekly_pickem_evaluate() are
    reused completely unchanged, just fed from this store instead of a
    game_state.py JSON blob."""
    _validate_client_id(client_id)
    c = engine_bootstrap.connect()
    try:
        ensure_pickem_schema(c)
        rows = c.execute(
            "SELECT game_id, predicted_winner, picked_at FROM pickem_picks "
            "WHERE client_id=? AND league=? AND season=? AND week=?",
            (client_id, league, season, str(week)),
        ).fetchall()
    finally:
        c.close()
    return {r["game_id"]: {"predicted_winner": r["predicted_winner"], "picked_at": r["picked_at"]} for r in rows}
