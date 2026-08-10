"""Reads Engine Gateway -- Grid (Immaculate Grid) roster/eligibility service
(v0.7 content-pipeline port, Grid roster merge phase).

Content-pipeline model (confirmed with the user before building this): the
Gateway is admin-only, private, staging-scoped (see gateway/config.py's
DEV_CORS_ORIGINS / PRODUCTION_ORIGIN_DOCUMENTED_NOT_ENABLED and every route's
require_admin gate). The LIVE frontend's Grid mode is NOT changed by this
module and keeps working exactly as it does today: 100% client-side, offline
(file://)-capable, instant validation, reading data/grid.js. This service is
the admin-only tool content ops uses to VERIFY/QA specific data/grid.js
entries against the Engine's real graph -- it is not called by end users'
browsers, and nothing here changes app.js or data/grid.js.

Same "no game logic duplicated, just called and translated" rule
gateway/services/graph.py already documents. Grid eligibility RULES are
copied 1:1 from data/grid.js's real GRID_CRITERIA (read in full before
writing this file) -- this module does not invent new gameplay.

--- REAL, MEASURED COVERAGE RESTRICTION (read before trusting this module) ---
graph_edges' PLAYED_FOR predicate -- the only roster-membership source this
module has -- covers seasons 2006-2019 ONLY (verified via
`SELECT MIN(season_start), MAX(season_start) ... WHERE predicate='PLAYED_FOR'`
against the real rebuilt database: 7,277 players, 34 raw team codes, zero
seasons before 2006 or after 2019). This is narrower than data/grid.js's
existing "every player, current 2024/2025 rosters" scope in BOTH directions:
nothing before 2006, nothing from 2020 onward. This module is therefore a
QA/verification tool for the 2006-2019 window, not a replacement data source
for data/grid.js -- see the v0.7 report's "coverage restrictions" section.

--- REAL, MEASURED CRITERION-TYPE COVERAGE ---
Of data/grid.js's 32 team + 21 stat GRID_CRITERIA entries, only these are
graph-backed (checked against the real schema, not assumed):
  - team_<CODE> (roster membership via PLAYED_FOR, 2006-2019 window, with a
    3-entry franchise-relocation alias map -- see FRANCHISE_ALIASES)
  - the 8 position-group criteria (via PLAYED_POSITION)
  - multi_team / one_team (distinct-team COUNT via PLAYED_FOR)
  - sb_champ (DERIVED: PLAYED_FOR(player,team,season) join
    PLAYOFF_RESULT(team,season)='WonSB' -- a real, source-backed team-season
    fact, same derivation pattern the DB's own PRODUCTION_SAFE_DERIVED
    verification_status already uses elsewhere)
NOT graph-backed, confirmed absent from the schema (no fabricated whitelist
guessing -- checked graph_nodes.node_type and graph_edges.predicate directly):
  - draft round (draft_r1/draft_undrafted/draft_day2plus) -- graph_edges has
    DRAFTED_BY/DRAFTED_IN with season+team only, no round column anywhere.
  - hof, mvp, sb_mvp, roty, probowl_5plus, probowl_10plus, allpro_3plus --
    no NFL-level award/honor data in the graph at all. The only award-shaped
    data (award_fact/WON_AWARD, 91 rows) is pre-1950s college Heisman-era
    CFB awards (subject_type='cfb_player'), not NFL accolades.
  - college/school (ATTENDED_BEFORE_DRAFT exists but covers only 204 of
    12,253 drafted players -- 1.7% -- too sparse to serve safely; also not
    currently a GRID_CRITERIA type in data/grid.js at all, so it stays out
    of CRITERIA_REGISTRY per "don't add gameplay to make integration
    easier" -- exposed here only as UNSUPPORTED_CRITERIA_REASONS' honest
    documentation, not as a live criterion.
Unsupported criteria are never guessed at -- see resolve_intersection's
UNDERSTOOD_BUT_UNSUPPORTED branch (spec: "if a requested relationship is not
production-safe, the cell should be unavailable rather than guessed").
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_ROOT / "Reads_Football_Data_Engine_v4.0"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from ..errors import GatewayError  # noqa: E402

try:
    import graph_explorer  # noqa: E402
except Exception as e:  # pragma: no cover - exercised only if the engine dir/file is missing
    graph_explorer = None
    _import_error = e
else:
    _import_error = None


def _ensure_engine_importable() -> None:
    if graph_explorer is None:
        raise GatewayError("SERVICE_UNAVAILABLE", f"Graph engine module could not be imported: {_import_error}")


# Exclude the same two statuses graph_explorer.shortest_path already excludes
# from traversal (unreviewed / actively conflicting facts) -- Grid answer
# validation is exactly the kind of place a false positive would be worst.
SAFE_STATUS_SQL = "verification_status NOT IN ('AUTO_REVIEW','CONFLICT')"

# Verified via graph_edges: OAK's PLAYED_FOR rows stop at season_start=2019
# (Raiders' last Oakland season) with zero rows for 'LV'; SD stops at 2016
# with LAC starting 2017; STL stops at 2015 with LAR starting 2017. Three
# real relocations, not a guess -- checked season ranges per code before
# writing this map.
FRANCHISE_ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LAR"}


def canonical_team(raw_code: str) -> str:
    return FRANCHISE_ALIASES.get(raw_code, raw_code)


def _raw_codes_for(canonical_code: str) -> List[str]:
    raws = [canonical_code]
    raws += [raw for raw, canon in FRANCHISE_ALIASES.items() if canon == canonical_code]
    return raws


# Position-group buckets, matching data/grid.js's 8 pos_* GRID_CRITERIA
# exactly (DE/DT/EDGE->pos_dl, CB/S->pos_db, OT/OG/C->pos_ol per its own
# test() functions), extended with the real side/variant codes actually
# observed in PLAYED_POSITION.object_id (e.g. RCB/LCB, RDT/LDT, RG/LG) so a
# player tagged with a side-specific code still matches the same group a
# plain code would -- this mirrors the posGroupOf() equivalence-class fix
# already used for the data/grid.js roster merge, applied to the graph's own
# position vocabulary instead of ESPN's.
POSITION_GROUPS: Dict[str, set] = {
    "pos_qb": {"QB"},
    "pos_rb": {"RB"},
    "pos_wr": {"WR", "SE", "FL"},
    "pos_te": {"TE"},
    "pos_dl": {"DE", "DT", "EDGE", "DL", "NT", "RDT", "LDT"},
    "pos_lb": {"LB", "OLB", "MLB", "ILB", "ROLB", "LOLB", "RILB", "LILB"},
    "pos_db": {"CB", "S", "DB", "SS", "FS", "RCB", "LCB"},
    "pos_ol": {"OT", "OG", "C", "T", "OL", "G", "RT", "LT", "RG", "LG"},
}

POSITION_LABELS = {
    "pos_qb": "Quarterback", "pos_rb": "Running Back", "pos_wr": "Wide Receiver",
    "pos_te": "Tight End", "pos_dl": "Defensive Line (DE/DT/EDGE)", "pos_lb": "Linebacker",
    "pos_db": "Defensive Back (CB/S)", "pos_ol": "Offensive Line (OT/OG/C)",
}

UNSUPPORTED_CRITERIA_REASONS = {
    "draft_r1": "draft round is not tracked anywhere in the graph schema (DRAFTED_BY/DRAFTED_IN store team+year only).",
    "draft_undrafted": "same -- round data absent, and edge-absence alone can't safely distinguish 'confirmed undrafted' from 'no data for this player'.",
    "draft_day2plus": "draft round is not tracked anywhere in the graph schema.",
    "hof": "no Hall of Fame data exists in the graph.",
    "mvp": "no NFL MVP award data exists in the graph.",
    "sb_mvp": "no Super Bowl MVP award data exists in the graph.",
    "roty": "no Rookie of the Year award data exists in the graph.",
    "probowl_5plus": "no Pro Bowl selection data exists in the graph.",
    "probowl_10plus": "no Pro Bowl selection data exists in the graph.",
    "allpro_3plus": "no All-Pro selection data exists in the graph.",
}


def _roster_coverage(conn) -> Dict[str, int]:
    row = conn.execute("SELECT MIN(season_start) lo, MAX(season_start) hi FROM graph_edges WHERE predicate='PLAYED_FOR'").fetchone()
    return {"min_season": row["lo"], "max_season": row["hi"]}


def _require_season_in_coverage(conn, season: Optional[int]) -> None:
    """A season outside the real PLAYED_FOR coverage window (2006-2019, see
    module docstring) must never silently resolve to an empty match set --
    that would look identical to 'checked, found nobody' when the honest
    answer is 'no data to check.' Raises the same UNDERSTOOD_BUT_UNSUPPORTED
    code unsupported criteria use, for the same reason."""
    if season is None:
        return
    coverage = _roster_coverage(conn)
    if not (coverage["min_season"] <= season <= coverage["max_season"]):
        raise GatewayError(
            "UNDERSTOOD_BUT_UNSUPPORTED",
            f"season={season} is outside this Engine's real roster-coverage window "
            f"({coverage['min_season']}-{coverage['max_season']}) -- returning an empty result would "
            f"misrepresent 'no data' as 'checked and found nobody'.",
        )


def _canonical_team_codes(conn) -> List[str]:
    rows = conn.execute("SELECT DISTINCT object_id FROM graph_edges WHERE predicate='PLAYED_FOR'").fetchall()
    raw = {r["object_id"] for r in rows}
    return sorted({canonical_team(code) for code in raw})


def list_supported_criteria() -> Dict[str, Any]:
    """Mirrors data/grid.js's GRID_CRITERIA shape/ids so a client already
    speaking that vocabulary needs no translation layer -- just a
    supported/unsupported split this Gateway can actually back with real
    data. Never called by the live frontend (content-pipeline model); used
    by content ops and by this module's own tests."""
    _ensure_engine_importable()
    conn = graph_explorer.connect()
    try:
        coverage = _roster_coverage(conn)
        team_codes = _canonical_team_codes(conn)
    finally:
        conn.close()

    team_criteria = [{"id": f"team_{code}", "type": "team", "team": code} for code in team_codes]
    stat_criteria = [{"id": pid, "type": "stat", "label": label} for pid, label in POSITION_LABELS.items()]
    stat_criteria += [
        {"id": "multi_team", "type": "stat", "label": "Played for 3+ Teams"},
        {"id": "one_team", "type": "stat", "label": "Played for Only 1 Team"},
        {"id": "sb_champ", "type": "stat", "label": "Super Bowl Champion", "derived": True},
    ]
    return {
        "roster_coverage": coverage,
        "supported": {"team": team_criteria, "stat": stat_criteria},
        "unsupported": [{"id": cid, "reason": reason} for cid, reason in UNSUPPORTED_CRITERIA_REASONS.items()],
    }


def _validate_criterion_id(field_name: str, crit_id: str) -> None:
    if not crit_id or not crit_id.strip():
        raise GatewayError("INVALID_REQUEST", f"{field_name} must not be empty.")
    if crit_id in UNSUPPORTED_CRITERIA_REASONS:
        raise GatewayError(
            "UNDERSTOOD_BUT_UNSUPPORTED",
            f"{field_name}={crit_id!r} is a real Grid criterion but not production-safe from this Engine's graph: "
            f"{UNSUPPORTED_CRITERIA_REASONS[crit_id]}",
        )
    is_team = crit_id.startswith("team_")
    is_stat = crit_id in POSITION_GROUPS or crit_id in ("multi_team", "one_team", "sb_champ")
    if not (is_team or is_stat):
        raise GatewayError("INVALID_REQUEST", f"{field_name}={crit_id!r} is not a recognized Grid criterion id.")


def _season_clause(alias: str, season: Optional[int]) -> tuple:
    if season is None:
        return "", ()
    return f" AND {alias}.season_start <= ? AND {alias}.season_end >= ?", (season, season)


def _players_matching(conn, crit_id: str, season: Optional[int]) -> set:
    """Returns the set of nfl_player node_ids satisfying one criterion,
    restricted to real, safe-status edges. Every branch is an indexed
    lookup (subject_type/object_type + predicate), never an unfiltered scan
    of graph_edges -- see gateway/tests/test_grid.py's performance check."""
    if crit_id.startswith("team_"):
        canonical_code = crit_id[len("team_"):]
        raw_codes = _raw_codes_for(canonical_code)
        placeholders = ",".join("?" for _ in raw_codes)
        clause, params = _season_clause("e", season)
        rows = conn.execute(
            f"""SELECT DISTINCT subject_id FROM graph_edges e
                WHERE predicate='PLAYED_FOR' AND object_type='team' AND object_id IN ({placeholders})
                  AND {SAFE_STATUS_SQL}{clause}""",
            (*raw_codes, *params),
        ).fetchall()
        return {r["subject_id"] for r in rows}

    if crit_id in POSITION_GROUPS:
        codes = POSITION_GROUPS[crit_id]
        placeholders = ",".join("?" for _ in codes)
        clause, params = _season_clause("e", season)
        rows = conn.execute(
            f"""SELECT DISTINCT subject_id FROM graph_edges e
                WHERE predicate='PLAYED_POSITION' AND object_type='position' AND object_id IN ({placeholders})
                  AND {SAFE_STATUS_SQL}{clause}""",
            (*codes, *params),
        ).fetchall()
        return {r["subject_id"] for r in rows}

    if crit_id in ("multi_team", "one_team"):
        clause, params = _season_clause("e", season)
        rows = conn.execute(
            f"""SELECT subject_id, object_id FROM graph_edges e
                WHERE predicate='PLAYED_FOR' AND {SAFE_STATUS_SQL}{clause}""",
            params,
        ).fetchall()
        by_player: Dict[str, set] = {}
        for r in rows:
            by_player.setdefault(r["subject_id"], set()).add(canonical_team(r["object_id"]))
        if crit_id == "multi_team":
            return {p for p, teams in by_player.items() if len(teams) >= 3}
        return {p for p, teams in by_player.items() if len(teams) == 1}

    if crit_id == "sb_champ":
        # DERIVED fact (see module docstring): player's PLAYED_FOR(team,season)
        # must match a team-season where PLAYOFF_RESULT(team,season)='WonSB'.
        clause, params = _season_clause("pf", season)
        pf_status = SAFE_STATUS_SQL.replace("verification_status", "pf.verification_status")
        pr_status = SAFE_STATUS_SQL.replace("verification_status", "pr.verification_status")
        rows = conn.execute(
            f"""SELECT DISTINCT pf.subject_id FROM graph_edges pf
                JOIN graph_edges pr
                  ON pr.predicate='PLAYOFF_RESULT' AND pr.object_type='playoff_result' AND pr.object_id='WonSB'
                 AND pr.subject_type='team' AND pr.subject_id=pf.object_id
                 AND pr.season_start=pf.season_start
                WHERE pf.predicate='PLAYED_FOR' AND {pf_status} AND {pr_status}{clause}""",
            params,
        ).fetchall()
        return {r["subject_id"] for r in rows}

    raise GatewayError("INVALID_REQUEST", f"Unrecognized criterion id {crit_id!r}.")


def _player_label(conn, node_id: str) -> Optional[str]:
    row = conn.execute("SELECT display_name FROM graph_nodes WHERE node_type='nfl_player' AND node_id=?", (node_id,)).fetchone()
    return row["display_name"] if row else None


def build_board(*, row_ids: List[str], col_ids: List[str], season: Optional[int]) -> Dict[str, Any]:
    """Cell validity/counts only -- deliberately does NOT return the
    matching player lists (unlike data/grid.js, which bundles the whole
    pool to the client by necessity of being a static file). Mirrors
    buildGridAttempt()'s re-roll loop contract (app.js:2527) so a caller can
    build a valid 9-cell board the same way, without ever seeing answers
    ahead of a real guess -- see resolve_intersection for the admin/QA path
    that does return full evidence."""
    _ensure_engine_importable()
    if len(row_ids) != 3 or len(col_ids) != 3:
        raise GatewayError("INVALID_REQUEST", "row_ids and col_ids must each have exactly 3 entries.")
    for i, rid in enumerate(row_ids):
        _validate_criterion_id(f"row_ids[{i}]", rid)
    for i, cid in enumerate(col_ids):
        _validate_criterion_id(f"col_ids[{i}]", cid)

    conn = graph_explorer.connect()
    try:
        _require_season_in_coverage(conn, season)
        row_sets = [_players_matching(conn, rid, season) for rid in row_ids]
        col_sets = [_players_matching(conn, cid, season) for cid in col_ids]
        cells = []
        valid_count = 0
        for r in range(3):
            for c in range(3):
                count = len(row_sets[r] & col_sets[c])
                cells.append({"row": row_ids[r], "col": col_ids[c], "valid": count > 0, "count": count})
                if count > 0:
                    valid_count += 1
        return {"row_ids": row_ids, "col_ids": col_ids, "season": season, "valid_count": valid_count, "cells": cells}
    finally:
        conn.close()


def resolve_intersection(*, row_id: str, col_id: str, season: Optional[int]) -> Dict[str, Any]:
    """Admin/QA path: full real matching-player list with evidence, for
    verifying a specific data/grid.js cell against the Engine, not for live
    gameplay (which never sees this -- see module docstring)."""
    _ensure_engine_importable()
    _validate_criterion_id("row_id", row_id)
    _validate_criterion_id("col_id", col_id)
    conn = graph_explorer.connect()
    try:
        _require_season_in_coverage(conn, season)
        matches = _players_matching(conn, row_id, season) & _players_matching(conn, col_id, season)
        players = []
        for node_id in matches:
            name = _player_label(conn, node_id)
            if name:
                players.append({"node_id": node_id, "display_name": name})
        players.sort(key=lambda p: p["display_name"])
        return {
            "row_id": row_id, "col_id": col_id, "season": season,
            "count": len(players), "players": players,
        }
    finally:
        conn.close()


def player_metadata(*, node_id: str) -> Dict[str, Any]:
    _ensure_engine_importable()
    if not node_id or not node_id.strip():
        raise GatewayError("INVALID_REQUEST", "node_id must not be empty.")
    conn = graph_explorer.connect()
    try:
        name = _player_label(conn, node_id)
        if name is None:
            raise GatewayError("NOT_FOUND", f"No nfl_player node with id {node_id!r}.")
        team_rows = conn.execute(
            f"""SELECT DISTINCT object_id FROM graph_edges
                WHERE predicate='PLAYED_FOR' AND subject_type='nfl_player' AND subject_id=? AND {SAFE_STATUS_SQL}""",
            (node_id,),
        ).fetchall()
        teams = sorted({canonical_team(r["object_id"]) for r in team_rows})
        pos_rows = conn.execute(
            f"""SELECT DISTINCT object_id FROM graph_edges
                WHERE predicate='PLAYED_POSITION' AND subject_type='nfl_player' AND subject_id=? AND {SAFE_STATUS_SQL}""",
            (node_id,),
        ).fetchall()
        raw_positions = {r["object_id"] for r in pos_rows}
        position_groups = sorted({g for g, codes in POSITION_GROUPS.items() if raw_positions & codes})
        draft_row = conn.execute(
            f"""SELECT object_id AS team, season_start AS year FROM graph_edges
                WHERE predicate='DRAFTED_BY' AND subject_type='nfl_player' AND subject_id=? AND {SAFE_STATUS_SQL} LIMIT 1""",
            (node_id,),
        ).fetchone()
        drafted = {"team": canonical_team(draft_row["team"]), "year": draft_row["year"]} if draft_row else None
        return {
            "node_id": node_id, "display_name": name, "teams": teams,
            "position_groups": position_groups, "drafted": drafted,
        }
    finally:
        conn.close()


def validate_answer(*, row_id: str, col_id: str, player_name: str, season: Optional[int]) -> Dict[str, Any]:
    """Resolves the frontend's free-text name input (unchanged UX -- see
    module docstring's 'adapter, not a frontend rewrite' framing) to a
    canonical node_id, then checks BOTH conditions against that id, never
    against the typed string. An ambiguous name (matches more than one real
    nfl_player) is reported as ambiguous, not silently resolved to
    whichever row sorts first -- 'never merge players by name alone'."""
    _ensure_engine_importable()
    _validate_criterion_id("row_id", row_id)
    _validate_criterion_id("col_id", col_id)
    norm = (player_name or "").strip()
    if not norm:
        raise GatewayError("INVALID_REQUEST", "player_name must not be empty.")

    conn = graph_explorer.connect()
    try:
        _require_season_in_coverage(conn, season)
        candidates = conn.execute(
            "SELECT node_id, display_name FROM graph_nodes WHERE node_type='nfl_player' AND lower(display_name)=lower(?)",
            (norm,),
        ).fetchall()
        if not candidates:
            return {"valid": False, "reason": "NOT_FOUND", "player_name": player_name}
        if len(candidates) > 1:
            return {
                "valid": False, "reason": "AMBIGUOUS", "player_name": player_name,
                "candidates": [{"node_id": r["node_id"], "display_name": r["display_name"]} for r in candidates],
            }
        node_id = candidates[0]["node_id"]
        display_name = candidates[0]["display_name"]

        row_matches = _players_matching(conn, row_id, season)
        col_matches = _players_matching(conn, col_id, season)
        satisfies_row = node_id in row_matches
        satisfies_col = node_id in col_matches
        is_valid = satisfies_row and satisfies_col
        result = {
            "valid": is_valid, "node_id": node_id, "display_name": display_name,
            "satisfies_row": satisfies_row, "satisfies_col": satisfies_col,
        }
        if is_valid:
            cell_size = len(row_matches & col_matches)
            result["points"] = max(10, round(100 / cell_size)) if cell_size else 0
        else:
            result["reason"] = "DOES_NOT_SATISFY_BOTH_CONDITIONS"
        return result
    finally:
        conn.close()


GRID_CAPABILITIES: List[Dict[str, Any]] = [
    {"id": "grid_criteria", "route": "GET /v1/grid/criteria", "description": "Lists which Grid criteria are graph-backed vs. unsupported, with real coverage metadata.", "requires_admin": True},
    {"id": "grid_board", "route": "POST /v1/grid/board", "description": "Cell validity/counts for a 3x3 criterion pairing (no answers exposed).", "requires_admin": True},
    {"id": "grid_intersection", "route": "GET /v1/grid/intersection", "description": "Full real matching-player list for one row/col criterion pair (admin QA use).", "requires_admin": True},
    {"id": "grid_validate", "route": "POST /v1/grid/validate", "description": "Validates a submitted player name against a Grid cell using canonical graph identity.", "requires_admin": True},
    {"id": "grid_player", "route": "GET /v1/grid/player/{node_id}", "description": "Public display metadata for one canonical player node.", "requires_admin": True},
]


def list_grid_capabilities() -> List[Dict[str, Any]]:
    return list(GRID_CAPABILITIES)
