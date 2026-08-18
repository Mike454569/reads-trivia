"""CFB transfers -- reusable knowledge relationships (Knowledge Expansion
Batch 1).

--- WHICH TABLE IS AUTHORITATIVE (real, verified this batch) ---
Two candidate tables exist. `cfb_transfer_summary` (37,743 rows) is the
real, authoritative transfer source: it is already keyed by a real
`cfb_player_id`, and its own `transfer_count` column shows a genuine
transfer distribution (33,761 players with transfer_count=0 -- i.e. one
school, not a "transfer" at all -- and 3,982 real multi-school transfers,
confirmed via direct query). `cfb_transfer_summary_v17` (109,221 rows,
column-compatible with `canonical_cfb_players`' own row count) has no
`transfer_count`/`path_json` columns and includes every player regardless
of transfer status -- it is a broader school-history summary, NOT a
transfer-specific table, and is NOT used here (no competing version was
created; the existing, more precisely-scoped table was simply identified
and adopted).

`cfb_player_id` in `cfb_transfer_summary` is already a real canonical
identity (not a raw name) -- no separate name-matching identity-resolution
ETL was needed for this domain, unlike All-America. This module's only
"identity" work is a real integrity check (do these IDs actually exist in
canonical_cfb_players?) -- see `integrity_report()`.
"""
from __future__ import annotations

import json

AUTHORITATIVE_TABLE = "cfb_transfer_summary"


def integrity_report(c) -> dict:
    total = c.execute(f"SELECT COUNT(*) FROM {AUTHORITATIVE_TABLE}").fetchone()[0]
    real_transfers = c.execute(f"SELECT COUNT(*) FROM {AUTHORITATIVE_TABLE} WHERE transfer_count > 0").fetchone()[0]
    orphaned = c.execute(
        f"SELECT COUNT(*) FROM {AUTHORITATIVE_TABLE} t "
        f"WHERE NOT EXISTS (SELECT 1 FROM canonical_cfb_players cp WHERE cp.cfb_player_id = t.cfb_player_id)"
    ).fetchone()[0]
    resolved_transfers = c.execute(
        f"SELECT COUNT(*) FROM {AUTHORITATIVE_TABLE} t WHERE t.transfer_count > 0 "
        f"AND EXISTS (SELECT 1 FROM canonical_cfb_players cp WHERE cp.cfb_player_id = t.cfb_player_id)"
    ).fetchone()[0]
    return {
        "authoritative_table": AUTHORITATIVE_TABLE,
        "total_rows": total,
        "real_transfer_rows": real_transfers,
        "single_school_rows_not_transfers": total - real_transfers,
        "orphaned_player_id_rows": orphaned,
        "resolved_transfer_rows": resolved_transfers,
        "usable_transfer_percentage": round(100.0 * resolved_transfers / real_transfers, 1) if real_transfers else 0.0,
    }


def _school_name(c, school_id: str | None) -> str | None:
    if not school_id:
        return None
    row = c.execute("SELECT school_name FROM schools WHERE school_id=?", (school_id,)).fetchone()
    return row["school_name"] if row else school_id


def transfer_path(c, *, cfb_player_id: str) -> dict:
    """PLAYER -> TRANSFER_PATH (+ FROM_SCHOOL / TO_SCHOOL / TRANSFER_SEASON
    implicitly, via the ordered path). Returns real, ordered school history
    parsed from the row's own real path_json -- never inferred."""
    row = c.execute(
        f"SELECT cfb_player_id, display_name, first_school_id, last_school_id, school_count, "
        f"transfer_count, first_season, last_season, path_json FROM {AUTHORITATIVE_TABLE} WHERE cfb_player_id=?",
        (cfb_player_id,),
    ).fetchone()
    if row is None:
        return {"cfb_player_id": cfb_player_id, "found": False}

    try:
        path = json.loads(row["path_json"]) if row["path_json"] else []
    except (TypeError, ValueError):
        path = []

    return {
        "cfb_player_id": cfb_player_id, "found": True, "display_name": row["display_name"],
        "is_transfer": row["transfer_count"] > 0,
        "school_count": row["school_count"], "transfer_count": row["transfer_count"],
        "first_school_id": row["first_school_id"], "first_school_name": _school_name(c, row["first_school_id"]),
        "last_school_id": row["last_school_id"], "last_school_name": _school_name(c, row["last_school_id"]),
        "first_season": row["first_season"], "last_season": row["last_season"],
        "path": path,
    }


def transfers_involving_school(c, *, school_id: str, direction: str) -> list[dict]:
    """SCHOOL -> TRANSFERS_IN / TRANSFERS_OUT. `direction` is 'in' (school
    is the LAST school on a real transfer path) or 'out' (school is the
    FIRST school on a real transfer path) -- both derived from the same
    real, disclosed first/last columns, never a separate guess."""
    if direction not in ("in", "out"):
        raise ValueError("direction must be 'in' or 'out'")
    column = "last_school_id" if direction == "in" else "first_school_id"
    rows = c.execute(
        f"SELECT cfb_player_id, display_name, first_school_id, last_school_id, first_season, last_season "
        f"FROM {AUTHORITATIVE_TABLE} WHERE transfer_count > 0 AND {column} = ?",
        (school_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def transfer_to_nfl_bridge(c) -> dict:
    """TRANSFER_PLAYER -> NFL_IDENTITY, via the certified cross-league
    bridge -- a direct cfb_player_id join, no new matching needed since
    both this table and the bridge already key on the same real ID."""
    total_transfers = c.execute(f"SELECT COUNT(*) FROM {AUTHORITATIVE_TABLE} WHERE transfer_count > 0").fetchone()[0]
    joined = c.execute(
        f"SELECT COUNT(*) FROM {AUTHORITATIVE_TABLE} t "
        f"WHERE t.transfer_count > 0 AND EXISTS "
        f"(SELECT 1 FROM cfb_nfl_identity_bridge_certified b WHERE b.cfb_player_id = t.cfb_player_id)"
    ).fetchone()[0]
    examples = c.execute(
        f"SELECT t.cfb_player_id, t.display_name, t.first_school_id, t.last_school_id, "
        f"b.nfl_player_key, b.nfl_draft_team, b.nfl_draft_year "
        f"FROM {AUTHORITATIVE_TABLE} t JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = t.cfb_player_id "
        f"WHERE t.transfer_count > 0 LIMIT 5"
    ).fetchall()
    return {"total_real_transfers": total_transfers, "joined_to_nfl_identity": joined,
            "join_percentage": round(100.0 * joined / total_transfers, 1) if total_transfers else 0.0,
            "examples": [dict(r) for r in examples]}
