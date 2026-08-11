"""Reads Engine Gateway -- Grid (Immaculate Grid) roster/eligibility service
(v0.7 content-pipeline port, Grid roster merge phase).

Content-pipeline model (confirmed with the user before building this): this
module's routes are admin-only (see every route's require_admin gate) --
v1.2 opened a SEPARATE, new public-gameplay route family
(gateway/services/public_game.py, /v1/public/*) for one pilot mode, but
did not touch Grid's admin-only status. The LIVE frontend's Grid mode is NOT changed by this
module and keeps working exactly as it does today: 100% client-side, offline
(file://)-capable, instant validation, reading data/grid.js. This service is
the admin-only tool content ops uses to VERIFY/QA specific data/grid.js
entries against the Engine's real graph -- it is not called by end users'
browsers, and nothing here changes app.js or data/grid.js.

Same "no game logic duplicated, just called and translated" rule
gateway/services/graph.py already documents. Grid eligibility RULES are
copied 1:1 from data/grid.js's real GRID_CRITERIA (read in full before
writing this file) -- this module does not invent new gameplay.

--- v0.9 UPDATE: real HOF/All-Pro/Pro-Bowl facts (hof, allpro_3plus,
probowl_5plus, probowl_10plus now SUPPORTED_WITH_COVERAGE_LIMIT) ---
Source: nflverse-data's `draft_picks` release (courtesy Pro Football
Reference per its own release notes) -- see
import_accolades_v09.py's module docstring for the full real semantic
verification (cross-checked allpro/probowls/hof against Randy Moss, J.J.
Watt, Jerry Rice, Lawrence Taylor, Anthony Munoz). At v0.9, 53 of 102 real
Hall of Famers in the source (anyone whose career ended before 2006)
couldn't link -- canonical_players only had 2006-2026-active players.

--- v1.0 UPDATE: historical identity expansion re-linked ALL 102 real HOF
facts (see import_historical_identity_v10.py) --- canonical_players grew
by 4,868 real, source-backed pre-2006 players (draft-identity only, no
roster/team data -- see data_coverage.NFL_PLAYER_IDENTITY_HISTORICAL).
Re-running import_accolades_v09.py against the larger universe linked
102/102 HOF (up from 49), 517 All-Pro career-count facts (up from 349),
1,325 Pro Bowl career-count facts (up from 893). Grid criterion STATUS is
UNCHANGED by this (still SUPPORTED_WITH_COVERAGE_LIMIT, not upgraded to
SUPPORTED) -- these are still coverage-limited by the drafted-players-only
source, and more importantly: every one of these newly-linked historical
players has ZERO canonical_roster_seasons/PLAYED_FOR data (that source
genuinely doesn't exist before 2006), so they can NEVER satisfy a
team_<CODE> criterion -- and Grid's own board structure requires BOTH a
row (always team-based) AND column match per cell. So while raw HOF/
All-Pro/Pro-Bowl LINKAGE materially improved, Grid CELL-PARTICIPATION for
these criteria is unaffected: only players with both real roster data
*and* real accolade data (i.e. the 2006-2026-era subset) can ever complete
an actual Grid cell. The larger linked universe is real, valuable data
(Player Explorer, Player-From-Clues, general correctness) -- just not a
change to what Grid itself can display. mvp/sb_mvp/roty remain
unsupported: checked all 225 tables (v0.8/v1.0) and every real
nflverse-data release tag (v0.8/v0.9/v1.0) -- genuinely no season-specific
individual award-winner data exists in any already-approved source.

--- v0.8 UPDATE: roster coverage extended 2006-2026 (was 2006-2019 in v0.7) ---
v0.8's import_modern_rosters_v08.py added real nflverse-data "rosters"
release rows for 2020-2026 on top of the v0.7-era 2006-2019 import (both
now live in the same canonical_roster_seasons table / PLAYED_FOR predicate
-- two source_ids, NFLVERSE_DATA and NFLVERSE_ROSTERS, both approved in the
`sources` registry). Verified post-import via the same MIN/MAX query as
before: 2006-2026, 12,245 players, real. Known real limitation carried over
from the source format (not a v0.8 bug): the 2020-2026 rows are one row per
(season, player) as nflverse-data provides them, so a same-season
mid-season trade only shows the player's final team that year -- the
2006-2019 rows (from an older, weekly-granular source) capture 806 such
cases as two rows; 2020-2026 cannot. `games`/`starts`/`av` are also not in
the new release format and are left NULL for 2020-2026 rows rather than
copied from the unrelated 2006-2019 convention or fabricated.

--- v0.8 UPDATE: draft ROUND is real (v0.7 undersold this) ---
v0.7's audit only checked graph_edges/graph_nodes and correctly found no
round column there -- but never checked the database's other 223 tables.
v0.8's Part 1 audit found `draft_facts` (12,253 rows, NFLVERSE_DATA,
1980-2024, draft_round 100% populated, 0 nulls) sitting right there,
unused by this module. draft_r1/draft_day2plus are now real, SQL-backed
criteria (see _players_matching's draft_facts branch) -- no new data
imported, just a real existing table finally wired up. draft_undrafted
stays unsupported: 6,669 of 12,245 roster players (54.5%) have no
draft_facts row at all, which is far too high to be genuine UDFA
players -- absence here means "no identity match found," not "confirmed
undrafted" (exactly the risk Part 6 of the v0.8 spec warned about), so it
is not asserted.

--- REAL, MEASURED CRITERION-TYPE COVERAGE ---
Of data/grid.js's 32 team + 21 stat GRID_CRITERIA entries, these are now
real-data-backed (checked against the live schema, not assumed):
  - team_<CODE> (roster membership via PLAYED_FOR, 2006-2026, with a
    5-entry franchise-code alias map -- see FRANCHISE_ALIASES; LA/AZ added
    in v0.8 after the new nflverse-data rosters release turned out to use
    different raw codes than the historical file for the Rams/Cardinals)
  - the 8 position-group criteria (via PLAYED_POSITION, 2006-2026)
  - multi_team / one_team (distinct-team COUNT via PLAYED_FOR, 2006-2026)
  - sb_champ (DERIVED: PLAYED_FOR(player,team,season) join
    PLAYOFF_RESULT(team,season)='WonSB')
  - draft_r1 / draft_day2plus (v0.8: via draft_facts.draft_round, 1980-2024)
NOT backed, confirmed absent from the ENTIRE database (v0.8 checked all 225
tables, not just graph_*/canonical_*, via
`SELECT m.name,p.name FROM sqlite_master m JOIN pragma_table_info(m.name) p
WHERE p.name LIKE '%hof%' OR ...'%award%' OR ...`  -- only CFB Heisman-era
award tables matched, nothing NFL-level):
  - draft_undrafted (see above -- real data exists, coverage is just too
    incomplete to safely assert absence)
  - hof, mvp, sb_mvp, roty, probowl_5plus, probowl_10plus, allpro_3plus --
    genuinely no NFL-level award/honor table or column anywhere in the
    database, confirmed both in v0.7 (graph only) and v0.8 (whole schema).
  - college/school (ATTENDED_BEFORE_DRAFT covers only 204 of 12,253 drafted
    players -- 1.7% -- too sparse; also never a GRID_CRITERIA type in
    data/grid.js, so stays out of the live registry either way)
Unsupported criteria are never guessed at -- see resolve_intersection's
UNDERSTOOD_BUT_UNSUPPORTED branch (spec: "if a requested relationship is not
production-safe, the cell should be unavailable rather than guessed").
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Real production bug found by testing the deployed Gateway (Final Go-Live
# Operation, Mission G): this used to hardcode ENGINE_DIR as REPO_ROOT /
# "Reads_Football_Data_Engine_v4.0" -- true for local dev, never true in
# the actual Fly.io container, where the Engine directory only exists on
# the mounted volume at READS_ENGINE_DIR. tools/quiz_export/engine.py
# already gets this right; this module (and graph.py/public_six_degrees.py,
# same bug) did not, so every graph_explorer-backed route silently 503'd
# in production while working fine locally.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = Path(os.environ.get("READS_ENGINE_DIR") or str(REPO_ROOT / "Reads_Football_Data_Engine_v4.0"))
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

# Verified via graph_edges/team_aliases: OAK's PLAYED_FOR rows stop at
# season_start=2019 (Raiders' last Oakland season); SD stops at 2016 with
# LAC starting 2017; STL stops at 2015 with LAR starting 2017 -- three real
# relocations, checked season ranges per code (v0.7). v0.8 added two more
# after the new nflverse-data "rosters" release (2020-2026) turned out to
# use different raw codes than the historical file for the same real
# teams: 'LA' for the Rams (the existing team_aliases table already maps
# both 'LA' and 'STL' to franchise_id FR_LAR -- 'LAR' itself, which
# data/grid.js's own GRID_TEAM_NAMES uses, is kept as the canonical target
# so nothing about the live frontend's vocabulary changes) and 'AZ' for the
# Cardinals (91 rows, 2026 data only -- an nflverse labeling quirk, not a
# real relocation, same team as 'ARI').
FRANCHISE_ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LAR", "LA": "LAR", "AZ": "ARI"}


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

DRAFT_ROUND_LABELS = {"draft_r1": "1st Round Pick", "draft_day2plus": "Drafted Round 3 or Later"}

# v0.9: real accolade facts (player_accolades table, imported from nflverse-data's
# draft_picks release -- see import_accolades_v09.py's module docstring for the
# real semantic verification against known players and the two real, honest
# coverage limitations that make these SUPPORTED_WITH_COVERAGE_LIMIT, not
# plain SUPPORTED: (1) drafted-players-only source (a true undrafted HOF/All-Pro/
# Pro-Bowler, rare but real, would be invisible), and (2) canonical_players
# itself only covers players with an actual 2006-2026 roster row, so a real
# Hall of Famer whose career ended before 2006 (e.g. Jerry Rice) has no
# canonical_players row to attach the fact to at all -- 53 of the source
# file's 102 real HOF rows were skipped for exactly this reason, not lost
# data, a structural scope boundary. `hof` is a plain EXISTS check;
# allpro_3plus/probowl_5plus/probowl_10plus are CAREER count thresholds
# (the source has no season-by-season selection list, only a career total).
ACCOLADE_CAREER_THRESHOLDS = {
    "allpro_3plus": ("ALL_PRO_FIRST_TEAM_CAREER_COUNT", 3),
    "probowl_5plus": ("PRO_BOWL_CAREER_COUNT", 5),
    "probowl_10plus": ("PRO_BOWL_CAREER_COUNT", 10),
}
ACCOLADE_LABELS = {
    "hof": "Pro Football Hall of Famer",
    "allpro_3plus": "3+ First-Team All-Pro",
    "probowl_5plus": "5+ Pro Bowls",
    "probowl_10plus": "10+ Pro Bowls",
}

UNSUPPORTED_CRITERIA_REASONS = {
    "draft_undrafted": ("real draft_facts table exists (v0.8), but 6,669 of 12,245 roster players (54.5%) have "
                         "no matching row -- far too high to be genuine UDFA players, so absence here means "
                         "'no identity match found', not 'confirmed undrafted', and is not asserted."),
    "mvp": "no NFL MVP award data exists anywhere in the database or in any real nflverse release checked (v0.8/v0.9 audits).",
    "sb_mvp": "no Super Bowl MVP award data exists anywhere in the database or in any real nflverse release checked.",
    "roty": "no Rookie of the Year (offensive or defensive) award data exists anywhere in the database or in any real nflverse release checked.",
}

# Part 5 (v0.8 spec) coverage-status vocabulary. Only SUPPORTED /
# SUPPORTED_WITH_COVERAGE_LIMIT / UNDERSTOOD_BUT_UNSUPPORTED are actually
# assigned to a real criterion below; BLOCKED_IDENTITY/BLOCKED_SOURCE/
# INVALID_CRITERION are real, valid outcomes this module can return (see
# _validate_criterion_id) but no current criterion sits in those buckets.
GRID_CRITERION_STATUSES = frozenset({
    "SUPPORTED", "SUPPORTED_WITH_COVERAGE_LIMIT", "UNDERSTOOD_BUT_UNSUPPORTED",
    "BLOCKED_IDENTITY", "BLOCKED_SOURCE", "INVALID_CRITERION",
})


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


def _draft_round_coverage(conn) -> Dict[str, Any]:
    row = conn.execute("SELECT MIN(draft_season) lo, MAX(draft_season) hi, COUNT(*) n FROM draft_facts").fetchone()
    return {"min_season": row["lo"], "max_season": row["hi"], "player_count": row["n"]}


def _accolade_coverage(conn) -> Dict[str, Any]:
    row = conn.execute("SELECT COUNT(DISTINCT player_id) n FROM player_accolades").fetchone()
    return {"player_count": row["n"], "universe": "drafted players with a canonical_players row (see notes)"}


def list_supported_criteria() -> Dict[str, Any]:
    """Mirrors data/grid.js's GRID_CRITERIA shape/ids so a client already
    speaking that vocabulary needs no translation layer -- just a
    supported/unsupported split this Gateway can actually back with real
    data. Never called by the live frontend (content-pipeline model); used
    by content ops and by this module's own tests.

    Each entry carries a Part 5 (v0.8 spec) `status` -- SUPPORTED for
    roster/position/derived criteria (bounded by roster_coverage),
    SUPPORTED_WITH_COVERAGE_LIMIT for draft_r1/draft_day2plus (real data,
    but draft_facts' own 1980-2024/PFR-keyed coverage is a materially
    different, narrower axis than roster_coverage -- see draft_coverage)."""
    _ensure_engine_importable()
    conn = graph_explorer.connect()
    try:
        coverage = _roster_coverage(conn)
        team_codes = _canonical_team_codes(conn)
        draft_coverage = _draft_round_coverage(conn)
        accolade_coverage = _accolade_coverage(conn)
    finally:
        conn.close()

    team_criteria = [
        {"id": f"team_{code}", "type": "team", "team": code, "status": "SUPPORTED",
         "coverage_start": coverage["min_season"], "coverage_end": coverage["max_season"]}
        for code in team_codes
    ]
    stat_criteria = [
        {"id": pid, "type": "stat", "label": label, "status": "SUPPORTED",
         "coverage_start": coverage["min_season"], "coverage_end": coverage["max_season"]}
        for pid, label in POSITION_LABELS.items()
    ]
    stat_criteria += [
        {"id": "multi_team", "type": "stat", "label": "Played for 3+ Teams", "status": "SUPPORTED",
         "coverage_start": coverage["min_season"], "coverage_end": coverage["max_season"]},
        {"id": "one_team", "type": "stat", "label": "Played for Only 1 Team", "status": "SUPPORTED",
         "coverage_start": coverage["min_season"], "coverage_end": coverage["max_season"]},
        {"id": "sb_champ", "type": "stat", "label": "Super Bowl Champion", "derived": True, "status": "SUPPORTED",
         "coverage_start": coverage["min_season"], "coverage_end": coverage["max_season"]},
    ]
    stat_criteria += [
        {"id": pid, "type": "stat", "label": label, "status": "SUPPORTED_WITH_COVERAGE_LIMIT",
         "coverage_start": draft_coverage["min_season"], "coverage_end": draft_coverage["max_season"],
         "notes": f"draft_facts covers {draft_coverage['player_count']} players by PFR id; players without a "
                  f"PFR id (v0.8's newly-minted GSIS:-prefixed ids) will never match."}
        for pid, label in DRAFT_ROUND_LABELS.items()
    ]
    stat_criteria += [
        {"id": pid, "type": "stat", "label": label, "status": "SUPPORTED_WITH_COVERAGE_LIMIT",
         "coverage_start": None, "coverage_end": None,
         "notes": (f"v0.9+v1.0: real nflverse-data/PFR-sourced facts ({accolade_coverage['player_count']} players "
                    "total across hof/all-pro/pro-bowl -- 102/102 real HOF now linked after v1.0's historical "
                    "identity expansion, up from 49/102 at v0.9). Still SUPPORTED_WITH_COVERAGE_LIMIT, not "
                    "SUPPORTED: (1) source only covers DRAFTED players -- a true undrafted honoree, rare but "
                    "real, is invisible; (2) v1.0's newly-linked pre-2006 players have NO roster/team data at "
                    "all (PLAYED_FOR doesn't exist before 2006), so they can never satisfy a team_<CODE> "
                    "criterion -- Grid's own board structure needs both a row and column match per cell, so "
                    "this criterion's real-world Grid cell participation is still bounded to the 2006-2026-era "
                    "player pool despite the larger linked universe. All-Pro/Pro-Bowl counts are CAREER "
                    "totals, not season-by-season selections (source limitation, not fabricated data).")}
        for pid, label in ACCOLADE_LABELS.items()
    ]
    return {
        "roster_coverage": coverage,
        "draft_coverage": draft_coverage,
        "accolade_coverage": accolade_coverage,
        "supported": {"team": team_criteria, "stat": stat_criteria},
        "unsupported": [
            {"id": cid, "reason": reason, "status": "UNDERSTOOD_BUT_UNSUPPORTED"}
            for cid, reason in UNSUPPORTED_CRITERIA_REASONS.items()
        ],
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
    is_stat = (crit_id in POSITION_GROUPS or crit_id in ("multi_team", "one_team", "sb_champ")
               or crit_id in DRAFT_ROUND_LABELS or crit_id in ACCOLADE_LABELS)
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

    if crit_id in DRAFT_ROUND_LABELS:
        # v0.8: real draft_facts table, not a graph predicate -- same `conn`
        # (graph_explorer.connect() opens the whole database file, not just
        # the graph_* tables). Draft round is a timeless player attribute
        # (like data/grid.js's own p.draft.round check), not season-bound,
        # so `season` is deliberately not applied here -- matches the
        # current Grid criterion's own semantics, not a bug.
        op = "= 1" if crit_id == "draft_r1" else ">= 3"
        rows = conn.execute(
            f"SELECT DISTINCT player_key FROM draft_facts WHERE draft_round {op} "
            f"AND {SAFE_STATUS_SQL}"
        ).fetchall()
        return {r["player_key"] for r in rows}

    if crit_id == "hof":
        # v0.9: real player_accolades table (import_accolades_v09.py). Season-
        # agnostic, timeless fact like draft round -- `season` not applied.
        rows = conn.execute("SELECT player_id FROM player_accolades WHERE accolade_type='HALL_OF_FAME'").fetchall()
        return {r["player_id"] for r in rows}

    if crit_id in ACCOLADE_CAREER_THRESHOLDS:
        accolade_type, threshold = ACCOLADE_CAREER_THRESHOLDS[crit_id]
        rows = conn.execute(
            "SELECT player_id FROM player_accolades WHERE accolade_type=? AND count_value >= ?",
            (accolade_type, threshold),
        ).fetchall()
        return {r["player_id"] for r in rows}

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
        # v0.8: WORE_NUMBER is new (real jersey_number data only exists for the
        # 2020-2026 import -- the 2006-2019 rows have jersey_number 100% NULL,
        # see import_modern_rosters_v08.py's module docstring), so this can be
        # legitimately empty for players active only in the older window.
        number_rows = conn.execute(
            f"""SELECT DISTINCT object_id, season_start FROM graph_edges
                WHERE predicate='WORE_NUMBER' AND subject_type='nfl_player' AND subject_id=? AND {SAFE_STATUS_SQL}
                ORDER BY season_start DESC""",
            (node_id,),
        ).fetchall()
        jersey_numbers = [{"number": int(r["object_id"]), "season": r["season_start"]} for r in number_rows]
        return {
            "node_id": node_id, "display_name": name, "teams": teams,
            "position_groups": position_groups, "drafted": drafted, "jersey_numbers": jersey_numbers,
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
