"""CFB All-America identity resolution (Knowledge Expansion Batch 1).

`cfb_all_america` (5,002 rows) already carries a real, resolved `school_id`
per row, but only a raw `player_name` string for the player -- no
`cfb_player_id`. This module resolves that name (+ the row's own
school_id) against the real roster record (`cfb_roster_seasons_real` joined
to `canonical_players_cfb` for a display_name) and writes only the
UNAMBIGUOUS matches into a new certified table, `cfb_all_america_certified`
-- never a blind name join. A row with zero or multiple distinct
`cfb_player_id` candidates at that school is left OUT of the certified
table and tracked as unresolved with a real reason (see
resolve_all_america_identities()'s own return shape) -- exactly the
"track ambiguous/unresolved rows rather than forcing matches" requirement.

Same real, disclosed normalization rule `tools/data_refresh/
nfl_college_identity_bridge.py` already established (lowercase, strip
punctuation/suffixes) -- reused verbatim, not reinvented.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

CERTIFIED_TABLE = "cfb_all_america_certified"

# Same real rule as nfl_college_identity_bridge.py's own _norm() -- reused,
# not reinvented, so "identity resolution" means the same thing everywhere
# in this project.
_SUFFIX_RE = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _norm(s: str | None) -> str:
    s = (s or "").lower().replace("’", "'").replace(".", "").replace("'", "")
    s = _SUFFIX_RE.sub("", s)
    return _NON_ALNUM_RE.sub("", s)


MATCH_SEASON_EXACT = "UNIQUE_NAME_SCHOOL_SEASON_ROSTER_MATCH"
MATCH_CAREER_APPROX = "UNIQUE_NAME_SCHOOL_ROSTER_MATCH_SEASON_APPROX"
CONFIDENCE_BY_METHOD = {MATCH_SEASON_EXACT: 0.98, MATCH_CAREER_APPROX: 0.85}


def ensure_schema(c) -> None:
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {CERTIFIED_TABLE} (
            certified_id       TEXT PRIMARY KEY,
            record_id          INTEGER NOT NULL UNIQUE,
            cfb_player_id       TEXT NOT NULL,
            season              INTEGER NOT NULL,
            school_id           TEXT NOT NULL,
            position            TEXT,
            is_consensus        INTEGER NOT NULL DEFAULT 0,
            selectors_raw       TEXT,
            resolution_method   TEXT NOT NULL,
            confidence          REAL NOT NULL,
            created_at          TEXT NOT NULL
        )
    """)
    c.commit()


def _build_roster_index(c) -> dict[tuple[str, str], list[tuple[str, int]]]:
    """(school_id, normalized_display_name) -> [(cfb_player_id, season), ...]
    -- built once from the real roster + identity tables, never a per-row
    query (5,002 All-America rows would otherwise mean 5,002 separate
    lookups against a 282K-row roster table)."""
    index: dict[tuple[str, str], list[tuple[str, int]]] = {}
    rows = c.execute(
        "SELECT crs.school_id, crs.season, crs.cfb_player_id, cp.display_name "
        "FROM cfb_roster_seasons_real crs "
        "JOIN canonical_cfb_players cp ON cp.cfb_player_id = crs.cfb_player_id "
        "WHERE crs.verification_status='SOURCE_BACKED'"
    ).fetchall()
    for r in rows:
        key = (r["school_id"], _norm(r["display_name"]))
        index.setdefault(key, []).append((r["cfb_player_id"], r["season"]))
    return index


def resolve_all_america_identities(c) -> dict:
    """Real, idempotent resolution pass. Never raises for ordinary
    data-shape issues (an enrichment step, not critical path) -- every row
    either resolves with a real, disclosed method, or is tracked as
    unresolved with a real reason, never silently dropped or guessed."""
    ensure_schema(c)
    index = _build_roster_index(c)

    aa_rows = c.execute(
        "SELECT record_id, season, player_name, school_id, position, is_consensus, selectors_raw "
        "FROM cfb_all_america WHERE verification_status IS NOT NULL"
    ).fetchall()

    already_certified = {r[0] for r in c.execute(f"SELECT record_id FROM {CERTIFIED_TABLE}")}
    resolved_count, newly_inserted = 0, 0
    unresolved: list[dict] = []
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()

    for row in aa_rows:
        key = (row["school_id"], _norm(row["player_name"]))
        candidates = index.get(key, [])
        distinct_players = sorted({pid for pid, _season in candidates})

        if not distinct_players:
            unresolved.append({"record_id": row["record_id"], "player_name": row["player_name"],
                                "school_id": row["school_id"], "season": row["season"],
                                "reason": "NO_ROSTER_MATCH"})
            continue
        if len(distinct_players) > 1:
            unresolved.append({"record_id": row["record_id"], "player_name": row["player_name"],
                                "school_id": row["school_id"], "season": row["season"],
                                "reason": "AMBIGUOUS_MULTIPLE_PLAYERS", "candidates": distinct_players})
            continue

        cfb_player_id = distinct_players[0]
        seasons_for_player = {s for pid, s in candidates if pid == cfb_player_id}
        if row["season"] in seasons_for_player:
            method = MATCH_SEASON_EXACT
        else:
            method = MATCH_CAREER_APPROX
        resolved_count += 1

        if row["record_id"] in already_certified:
            continue
        certified_id = "AACERT:" + hashlib.sha256(f"{row['record_id']}|{cfb_player_id}".encode()).hexdigest()[:20]
        c.execute(
            f"INSERT OR IGNORE INTO {CERTIFIED_TABLE} "
            f"(certified_id, record_id, cfb_player_id, season, school_id, position, is_consensus, "
            f"selectors_raw, resolution_method, confidence, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (certified_id, row["record_id"], cfb_player_id, row["season"], row["school_id"],
             row["position"], row["is_consensus"], row["selectors_raw"], method,
             CONFIDENCE_BY_METHOD[method], now),
        )
        newly_inserted += 1

    c.commit()
    total = len(aa_rows)
    return {
        "total_rows": total,
        "resolved_rows": resolved_count,
        "unresolved_rows": len(unresolved),
        "newly_inserted_this_run": newly_inserted,
        "usable_percentage": round(100.0 * resolved_count / total, 1) if total else 0.0,
        "unresolved_reason_counts": {
            reason: sum(1 for u in unresolved if u["reason"] == reason)
            for reason in {u["reason"] for u in unresolved}
        },
        "unresolved_sample": unresolved[:10],
    }


def run() -> dict:
    from tools.data_refresh import safety
    backup = safety.create_verified_backup()
    c = engine_bootstrap.connect()
    try:
        c.execute("BEGIN")
        try:
            result = resolve_all_america_identities(c)
            c.commit()
        except Exception:
            c.rollback()
            raise
        integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"PRAGMA integrity_check failed: {integrity}")
        result["backup_id"] = backup["backup_id"]
        return result
    finally:
        c.close()
