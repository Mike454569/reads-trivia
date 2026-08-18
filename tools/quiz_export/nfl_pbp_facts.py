"""NFL play-by-play -- reusable knowledge relationships (Knowledge
Expansion Batch 3).

Built entirely on the EXISTING `nfl_plays` table (1,279,628 real rows,
1999-2025, NFLVERSE_DATA-sourced) -- no new table, no duplicated rows.
Most core fields (`down`, `ydstogo`, `yardline_100`, `qtr`,
`game_seconds_remaining`, `posteam`/`defteam`, `play_type`,
`yards_gained`, `posteam_score`/`defteam_score`, and the real
`passer_player_key`/`receiver_player_key`/`rusher_player_key` player-
identity columns) are already structured and are exposed here directly,
never re-derived.

--- SCORING-PLAY CLASSIFICATION: REAL, STANDARDIZED TEXT, NOT A GUESS ---
`play_type`/`touchdown`/`pass_touchdown`/`rush_touchdown`/`interception`/
`fumble_lost` cover most cases directly. The remaining subtypes (punt/
kickoff/blocked-FG return touchdowns, made vs. missed field goals/extra
points, two-point conversion result, safety) are NOT separately flagged
by any column -- they are derived from `play_desc`, which is nflverse's
own highly standardized boilerplate ("... is GOOD", "... is No Good",
"TWO-POINT CONVERSION ATTEMPT. ... ATTEMPT SUCCEEDS/FAILS", "SAFETY"),
confirmed by direct inspection of real sample rows for every subtype
below -- substring matching on fixed, repeated boilerplate is a reliable
classification here, not the "vague text parsing" the task explicitly
warns against. Any row that doesn't match a known pattern is classified
`UNCLASSIFIED_TOUCHDOWN`/`None`, never forced into a category.

--- PLAYER IDENTITY: REAL, BUT ONE-SIDED (disclosed, not silent) ---
`passer_player_key`/`receiver_player_key`/`rusher_player_key` are real,
already-resolved `canonical_players.player_id` values (offense side only).
There is NO column anywhere in `nfl_plays` identifying which defender
recorded a sack, interception, forced fumble, or fumble recovery, and no
reliable jersey-number-to-player mapping is attempted here to invent one
-- `defensive_player_identity_available = False` is reported explicitly
by `identity_coverage()`, not silently omitted.
"""
from __future__ import annotations

_FG_GOOD = "is GOOD"
_FG_NO_GOOD = "No Good"
_XP_GOOD = "is GOOD"


def game_plays(c, *, game_id: str) -> list[dict]:
    """PLAY -> GAME (+ QUARTER/CLOCK/DOWN/DISTANCE/YARD_LINE/OFFENSE/
    DEFENSE/PLAY_TYPE/YARDS_GAINED/SCORE_STATE/RESULT), raw play text and
    IDs preserved. PK-indexed lookup (SEARCH via the existing composite
    primary key), not a scan."""
    rows = c.execute(
        "SELECT game_id, play_id, season, week, qtr, down, ydstogo, yardline_100, "
        "game_seconds_remaining, posteam, defteam, play_type, play_desc, yards_gained, "
        "posteam_score, defteam_score, touchdown, pass_touchdown, rush_touchdown, "
        "interception, fumble_lost, sack, "
        "passer_player_key, receiver_player_key, rusher_player_key "
        "FROM nfl_plays WHERE game_id=? ORDER BY CAST(play_id AS INTEGER)", (game_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def classify_scoring_play(row: dict) -> str | None:
    """PLAY -> scoring type, or None if the play is not a scoring play.
    Method precedence: real boolean columns first, standardized raw-text
    boilerplate only where no column exists."""
    desc = row.get("play_desc") or ""
    if row.get("pass_touchdown") == 1:
        return "PASSING_TOUCHDOWN"
    if row.get("rush_touchdown") == 1:
        return "RUSHING_TOUCHDOWN"
    if row.get("touchdown") == 1:
        if row.get("interception") == 1:
            return "INTERCEPTION_RETURN_TOUCHDOWN"
        if row.get("play_type") == "punt":
            return "PUNT_RETURN_TOUCHDOWN"
        if row.get("play_type") == "kickoff":
            return "KICKOFF_RETURN_TOUCHDOWN"
        if row.get("play_type") == "field_goal" and "BLOCKED" in desc.upper():
            return "BLOCKED_FIELD_GOAL_RETURN_TOUCHDOWN"
        if row.get("fumble_lost") == 1:
            return "FUMBLE_RETURN_TOUCHDOWN"
        return "UNCLASSIFIED_TOUCHDOWN"  # real, disclosed miss -- never forced into a category
    if row.get("play_type") == "field_goal" and _FG_GOOD in desc:
        return "FIELD_GOAL"
    if row.get("play_type") == "extra_point" and _XP_GOOD in desc:
        return "EXTRA_POINT"
    upper = desc.upper()
    if "TWO-POINT CONVERSION" in upper and "ATTEMPT SUCCEEDS" in upper:
        return "TWO_POINT_CONVERSION"
    if "SAFETY" in upper:
        return "SAFETY"
    return None


def classify_turnover(row: dict) -> str | None:
    """PLAY -> TURNOVER_TYPE. A fumble is only ever counted as a turnover
    when the source's own `fumble_lost` flag says so -- an own-recovered
    fumble is never treated as a turnover."""
    if row.get("interception") == 1:
        return "INTERCEPTION"
    if row.get("fumble_lost") == 1:
        return "FUMBLE_LOST"
    return None


def game_scoring_plays(c, *, game_id: str) -> list[dict]:
    """GAME -> SCORING_PLAYS (+ QUARTER, YARDS, SCORE_AFTER_PLAY)."""
    out = []
    for row in game_plays(c, game_id=game_id):
        scoring_type = classify_scoring_play(row)
        if scoring_type is None:
            continue
        out.append({
            "play_id": row["play_id"], "scoring_type": scoring_type, "qtr": row["qtr"],
            "yards": row["yards_gained"], "posteam": row["posteam"], "defteam": row["defteam"],
            "score_after_posteam": row["posteam_score"], "score_after_defteam": row["defteam_score"],
            "passer_player_key": row["passer_player_key"], "receiver_player_key": row["receiver_player_key"],
            "rusher_player_key": row["rusher_player_key"], "play_desc": row["play_desc"],
        })
    return out


def game_turnovers(c, *, game_id: str) -> list[dict]:
    """GAME -> TURNOVERS (+ TURNOVER_TYPE)."""
    out = []
    for row in game_plays(c, game_id=game_id):
        t = classify_turnover(row)
        if t is None:
            continue
        out.append({"play_id": row["play_id"], "turnover_type": t, "qtr": row["qtr"],
                     "posteam": row["posteam"], "defteam": row["defteam"],
                     "passer_player_key": row["passer_player_key"], "rusher_player_key": row["rusher_player_key"],
                     "play_desc": row["play_desc"]})
    return out


def player_scoring_plays(c, *, player_key: str) -> list[dict]:
    """PLAYER -> SCORING_PLAY -- only ever the offense-side identity
    columns (passer/receiver/rusher); real, one-sided, disclosed."""
    rows = c.execute(
        "SELECT game_id, play_id, season, week, qtr, play_type, play_desc, yards_gained, touchdown, "
        "pass_touchdown, rush_touchdown, interception, fumble_lost, posteam "
        "FROM nfl_plays WHERE passer_player_key=? OR receiver_player_key=? OR rusher_player_key=?",
        (player_key, player_key, player_key),
    ).fetchall()
    out = []
    for row in rows:
        d = dict(row)
        scoring_type = classify_scoring_play(d)
        if scoring_type:
            d["scoring_type"] = scoring_type
            out.append(d)
    return out


def explosive_plays(c, *, game_id: str | None = None, season: int | None = None,
                     rush_threshold: int = 10, pass_threshold: int = 20, any_play_threshold: int = 40) -> list[dict]:
    """TEAM/GAME -> EXPLOSIVE_PLAYS -- a reusable, CALLER-CHOSEN threshold
    layer (never one hard-coded number). Exposes exact `yards_gained` so a
    caller can re-filter to any other threshold without re-querying."""
    where = []
    params: list = []
    if game_id:
        where.append("game_id=?")
        params.append(game_id)
    if season:
        where.append("season=?")
        params.append(season)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rows = c.execute(
        f"SELECT game_id, play_id, play_type, yards_gained, touchdown, posteam, defteam, play_desc "
        f"FROM nfl_plays {where_sql}{' AND' if where_sql else 'WHERE'} play_type IN ('run','pass')",
        params,
    ).fetchall()
    out = []
    for row in rows:
        yards = row["yards_gained"] or 0
        threshold = rush_threshold if row["play_type"] == "run" else pass_threshold
        is_explosive = yards >= threshold or yards >= any_play_threshold
        if is_explosive:
            d = dict(row)
            d["is_touchdown_explosive"] = bool(row["touchdown"]) and yards >= 20
            out.append(d)
    return out


def game_derived_facts(c, *, game_id: str) -> dict:
    """GAME -> derived PBP facts: longest play, longest TD, first/final
    TD, first turnover, total turnovers/sacks, scoring-play count, scoring
    by quarter. Conservative: no lead-change/comeback/game-winning-score
    claims here -- see module docstring; those require broader score-state
    reconstruction and are intentionally NOT exposed as a generic fact
    until validated per-mechanic."""
    plays = game_plays(c, game_id=game_id)
    if not plays:
        return {"game_id": game_id, "found": False}

    scoring = [(p, classify_scoring_play(p)) for p in plays]
    scoring = [(p, t) for p, t in scoring if t]
    turnovers = [(p, classify_turnover(p)) for p in plays]
    turnovers = [(p, t) for p, t in turnovers if t]
    real_plays = [p for p in plays if p["play_type"] in ("run", "pass") and p["yards_gained"] is not None]

    longest_play = max(real_plays, key=lambda p: p["yards_gained"], default=None)
    tds = [p for p, t in scoring if "TOUCHDOWN" in t]
    longest_td = max(tds, key=lambda p: p["yards_gained"] or 0, default=None)

    by_quarter: dict[int, int] = {}
    for p, _t in scoring:
        by_quarter[p["qtr"]] = by_quarter.get(p["qtr"], 0) + 1

    sacks = [p for p in plays if p.get("sack") == 1]

    return {
        "game_id": game_id, "found": True,
        "longest_play": {"play_id": longest_play["play_id"], "yards": longest_play["yards_gained"],
                          "play_desc": longest_play["play_desc"]} if longest_play else None,
        "longest_touchdown": {"play_id": longest_td["play_id"], "yards": longest_td["yards_gained"],
                               "play_desc": longest_td["play_desc"]} if longest_td else None,
        "first_touchdown": {"play_id": tds[0]["play_id"], "qtr": tds[0]["qtr"], "play_desc": tds[0]["play_desc"]} if tds else None,
        "final_scoring_play": {"play_id": scoring[-1][0]["play_id"], "type": scoring[-1][1],
                                "play_desc": scoring[-1][0]["play_desc"]} if scoring else None,
        "first_turnover": {"play_id": turnovers[0][0]["play_id"], "type": turnovers[0][1]} if turnovers else None,
        "total_turnovers": len(turnovers),
        "total_sacks": len(sacks),
        "scoring_play_count": len(scoring),
        "scoring_by_quarter": by_quarter,
    }


def identity_coverage(c, *, season: int | None = None) -> dict:
    """Measured, honest player-identity coverage for `nfl_plays` -- offense
    side only (see module docstring)."""
    where = "WHERE season=?" if season else ""
    params = [season] if season else []
    total = c.execute(f"SELECT COUNT(*) FROM nfl_plays {where}", params).fetchone()[0]
    pass_rows = c.execute(f"SELECT COUNT(*) FROM nfl_plays {where}{' AND' if where else 'WHERE'} play_type='pass'", params).fetchone()[0]
    pass_resolved = c.execute(
        f"SELECT COUNT(*) FROM nfl_plays {where}{' AND' if where else 'WHERE'} play_type='pass' AND passer_player_key IS NOT NULL", params
    ).fetchone()[0]
    rush_rows = c.execute(f"SELECT COUNT(*) FROM nfl_plays {where}{' AND' if where else 'WHERE'} play_type='run'", params).fetchone()[0]
    rush_resolved = c.execute(
        f"SELECT COUNT(*) FROM nfl_plays {where}{' AND' if where else 'WHERE'} play_type='run' AND rusher_player_key IS NOT NULL", params
    ).fetchone()[0]
    return {
        "total_plays": total,
        "pass_plays": pass_rows, "passer_identity_resolved": pass_resolved,
        "passer_resolution_pct": round(100.0 * pass_resolved / pass_rows, 1) if pass_rows else 0.0,
        "rush_plays": rush_rows, "rusher_identity_resolved": rush_resolved,
        "rusher_resolution_pct": round(100.0 * rush_resolved / rush_rows, 1) if rush_rows else 0.0,
        "defensive_player_identity_available": False,
        "defensive_identity_note": "nfl_plays has no sacking/intercepting/recovering-defender player column; not derivable from structured fields this batch.",
    }


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM nfl_plays").fetchone()[0]
    seasons = c.execute("SELECT MIN(season), MAX(season) FROM nfl_plays").fetchone()
    games = c.execute("SELECT COUNT(DISTINCT game_id) FROM nfl_plays").fetchone()[0]
    return {"total_rows": total, "season_range": [seasons[0], seasons[1]], "distinct_games": games}
