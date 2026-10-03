"""Resolve graph entity IDs to safe human-readable labels without guessing."""
from __future__ import annotations


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _cols(conn, table):
    return {r[1] for r in conn.execute("PRAGMA table_info(" + table + ")")}


def _first(conn, table, where_col, where_val, label_cols):
    cols = _cols(conn, table)
    if where_col not in cols:
        return None
    usable = [c for c in label_cols if c in cols]
    if not usable:
        return None
    row = conn.execute(
        "SELECT " + ",".join(usable) + " FROM " + table + " WHERE " + where_col + "=? LIMIT 1",
        (where_val,),
    ).fetchone()
    if not row:
        return None
    for i, col in enumerate(usable):
        value = row[i]
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def resolve_label(conn, entity_type, entity_id):
    """Return a stored label for an entity, never an invented one."""
    entity_type = str(entity_type)
    entity_id = str(entity_id)
    tables = _tables(conn)

    candidates = {
        "NFL_PLAYER": [
            ("canonical_players", "player_id", ("display_name", "player_name", "name")),
            ("draft_facts", "player_key", ("player_name",)),
        ],
        "CFB_PLAYER": [
            ("canonical_cfb_players", "cfb_player_id", ("display_name", "player_name", "name")),
            ("cfb_players_canonical", "cfb_player_id", ("display_name", "player_name", "name")),
            ("cfb_transfer_summary", "cfb_player_id", ("display_name",)),
            ("cfb_player_game_stats_real", "cfb_player_id", ("player_name",)),
        ],
        "COACH": [
            ("canonical_coaches", "coach_id", ("display_name", "coach_name", "name")),
            ("coach_team_seasons", "coach_id", ("coach_name",)),
        ],
        "SCHOOL": [
            ("schools", "school_id", ("school_name", "display_name", "name")),
            ("school_aliases", "school_id", ("alias_name", "school_name", "display_name", "name")),
            ("cfb_schools", "school_id", ("school_name", "display_name", "name")),
            ("cfb_rankings", "school_id", ("school_name_raw",)),
        ],
        "NFL_TEAM": [
            ("team_aliases", "team_code", ("full_name", "team_name", "display_name", "name")),
            ("nfl_teams", "team_code", ("team_name", "display_name", "name", "full_name")),
            ("teams", "team_code", ("team_name", "display_name", "name", "full_name")),
        ],
    }

    for table, where_col, label_cols in candidates.get(entity_type, []):
        if table not in tables:
            continue
        value = _first(conn, table, where_col, entity_id, label_cols)
        if value:
            return value

    # Stable codes/IDs remain preferable to guessed names.
    return entity_id



def resolve_required_label(conn, entity_type, entity_id):
    """Return a real user-facing label or fail closed on an unresolved ID/code."""
    value = resolve_label(conn, entity_type, entity_id)
    raw = str(entity_id)
    if not value or str(value).strip() == raw.strip():
        raise ValueError("UNRESOLVED_ENTITY_LABEL:" + str(entity_type) + ":" + raw)
    return str(value).strip()
