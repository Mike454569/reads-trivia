"""Reads Engine Gateway -- admin-only POSTPONED/CANCELED game-status
override (Dynamic Weekly Pick'em pass).

Confirmed directly against both real upstream schedule sources
(nflverse's games.csv, cfbfastR's schedules CSV) that neither ever
carries a postponed/canceled signal -- a canceled game is simply absent
as a row, never flagged. So this is the ONLY way a game's `status` column
ever becomes POSTPONED/CANCELED -- a real, disclosed manual override, not
automated detection. Every call is audit-logged (oplog.record_event) with
the human-supplied `reason`, so an override is always traceable to a real
decision, never a silent mutation.

Small, single-row UPDATE on an already-existing game_id -- no backup step
(unlike tools/data_refresh/*.py's bulk refreshes, this never risks more
than one row, and the row's prior value is always recoverable by another
admin call)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

from ..errors import GatewayError
from . import oplog

_TABLE_FOR_LEAGUE = {"NFL": "games", "CFB": "cfb_games_canonical"}


def set_game_status(*, league: str, game_id: str, status: str, reason: str) -> dict:
    table = _TABLE_FOR_LEAGUE.get(league)
    if table is None:
        raise GatewayError("INVALID_MODE", f"league must be one of {sorted(_TABLE_FOR_LEAGUE)}.")

    c = engine_bootstrap.connect()
    try:
        row = c.execute(f"SELECT game_id, status FROM {table} WHERE game_id=?", (game_id,)).fetchone()
        if row is None:
            raise GatewayError("NOT_FOUND", f"No such {league} game_id: {game_id!r}.")
        previous_status = row["status"]
        now = datetime.now(timezone.utc).isoformat()
        c.execute(f"UPDATE {table} SET status=?, updated_at=? WHERE game_id=?", (status, now, game_id))
        c.commit()
    finally:
        c.close()

    oplog.record_event(
        "admin_pickem_status_override", league=league, game_id=game_id,
        previous_status=previous_status, new_status=status, reason=reason,
    )
    return {"league": league, "game_id": game_id, "previous_status": previous_status, "status": status}
