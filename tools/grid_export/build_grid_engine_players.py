"""Builds data/grid-engine-players.js -- the auto-generated, Engine-sourced
half of NFL Grid's player universe (Connect Engine v4.0 to NFL Grid task).

--- WHY THIS FILE EXISTS ---
data/grid.js's GRID_PLAYERS array is a hand-curated pool of ~3,700
well-known players -- real, useful, but static: a real player already sitting
in the Engine's graph (graph_nodes/graph_edges, the same live graph
gateway/services/grid.py's own admin QA tool already reads) simply doesn't
appear on any Grid board unless someone manually added a line for them.
Measured directly (Audit, see GRID_ENGINE_CONNECTION_REPORT): 13,665 real
nfl_player nodes have at least one verified PLAYED_FOR edge -- the
prerequisite for EVERY Grid cell, since every board's 3 ROW criteria are
always team_<CODE> (see app.js's buildGridAttempt()) -- and only 3,224 of
data/grid.js's 3,717 hand-curated names match one of them by name.

This script is the fix: it queries the Engine's own graph for every real,
identity-safe, PLAYED_FOR-having player NOT already in data/grid.js by name,
and writes them to a SEPARATE static file (window.GRID_ENGINE_PLAYERS),
concatenated onto window.GRID_PLAYERS at load time (see app.js's
refreshDataAliases()). data/grid.js itself is never rewritten by this
script -- the hand-curated pool's own human-verified facts (some, like
pre-1999 Hall of Famers' MVP/Super Bowl MVP/ROTY awards, aren't derivable
from this Engine at all -- see module docstring further down) stay exactly
as authored, forever authoritative for the names already there.

--- IDENTITY: NO BLIND NAME JOINS THAT CREATE NEW AMBIGUITY ---
NFL Grid's OWN gameplay (app.js's submitGridGuess()) already resolves a
typed answer to a player via `GRID_PLAYERS.find(p => normName(p.name) ===
norm)` -- an existing, shipped, name-string identity model this script does
not redesign (HARD RULE: no Grid UI/gameplay redesign). What this script
DOES do is make sure it never POURS AMBIGUITY into that model: a real,
measured 263 of the Engine's 13,352 distinct PLAYED_FOR display_names are
shared by 2+ distinct canonical player node_ids (576 total player-rows
affected) -- e.g. two different real people both named "Marcus Henry," with
no SAME_PERSON_AS or equivalent fact anywhere in this graph proving they're
the same person. Every one of those 576 rows is EXCLUDED from this export,
full stop -- "ambiguous identities remain excluded until safely resolved,"
never guessed, never merged. Same for any Engine candidate whose name
collides with a name ALREADY in data/grid.js's hand-curated pool (a second,
separate exclusion reason, counted separately) -- app.js's name-keyed lookup
means two same-named entries would make the second permanently unreachable
were it appended, so it's better to have.

--- WHAT DATA THIS PROVIDES, AND WHAT IT HONESTLY DOES NOT ---
Every field below is sourced from a specific Engine table/predicate; see
each block's own comment for the exact provenance. Three of the hand-curated
schema's 12 fields (mvp, sbMVP, roty) have NO Engine data source anywhere
(confirmed: no MVP/Super Bowl MVP/Rookie of the Year table or predicate
exists in this database at all -- gateway/services/grid.py's own module
docstring independently confirms the same absence) -- every auto-generated
entry gets `false` for all three, an honest "no evidence" default, never a
guess. This means these 3 criteria (of Grid's 21 total) stay exactly as
data/grid.js's hand-curated entries alone can supply -- this script adds
players, never new true facts for criteria the Engine cannot back.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402

OUT_PATH = REPO_ROOT / "data" / "grid-engine-players.js"
GRID_JS_PATH = REPO_ROOT / "data" / "grid.js"

# Identical to gateway/services/grid.py's own FRANCHISE_ALIASES -- the same
# real historical-relocation map, reused (not re-derived) so team identity
# is consistent between this export and that module's own live QA queries
# against the same graph.
FRANCHISE_ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LAR", "LA": "LAR", "AZ": "ARI"}

DRAFT_SOURCE = "NFLVERSE_DATA"


def _canonical_team(code: str) -> str:
    return FRANCHISE_ALIASES.get(code, code)


def _existing_grid_js_names() -> set:
    """Real names already in the hand-curated pool -- read directly from the
    source file's own `name: "..."` literals (not re-parsed as JS -- a
    simple, safe regex over a well-known, consistent literal format, the
    same technique this codebase already uses for auditing this exact
    file). Used only to avoid a name collision with app.js's name-keyed
    identity model; never mutates data/grid.js."""
    text = GRID_JS_PATH.read_text()
    return set(re.findall(r'name:\s*"((?:[^"\\]|\\.)*)"', text))


def _safe_played_for_players(c) -> dict:
    """Returns {node_id: display_name} for every real nfl_player node with
    >=1 verified PLAYED_FOR edge, EXCLUDING any display_name shared by 2+
    distinct node_ids (see module docstring's identity-safety section).
    Returns (safe_map, ambiguous_name_count, ambiguous_row_count)."""
    rows = c.execute(
        """SELECT DISTINCT n.node_id, n.display_name FROM graph_nodes n
           JOIN graph_edges e ON e.subject_id = n.node_id AND e.predicate='PLAYED_FOR'
           WHERE n.node_type='nfl_player'"""
    ).fetchall()
    by_name: dict = defaultdict(list)
    for r in rows:
        by_name[r["display_name"]].append(r["node_id"])
    ambiguous_names = {name: ids for name, ids in by_name.items() if len(ids) > 1}
    ambiguous_row_count = sum(len(ids) for ids in ambiguous_names.values())
    safe = {ids[0]: name for name, ids in by_name.items() if len(ids) == 1}
    return safe, len(ambiguous_names), ambiguous_row_count


def _teams_by_player(c, node_ids: list) -> dict:
    """{node_id: [team_code, ...]} ordered by first season played, real
    PLAYED_FOR edges only, canonicalized through FRANCHISE_ALIASES so a
    historical code (OAK/SD/STL) always resolves to its real current
    franchise -- matching data/grid.js's own stated convention exactly
    ("players who were Oakland/LA/Las Vegas are all tagged 'LV'")."""
    placeholders = ",".join("?" for _ in node_ids)
    rows = c.execute(
        f"""SELECT subject_id, object_id, MIN(season_start) first_season FROM graph_edges
            WHERE predicate='PLAYED_FOR' AND subject_id IN ({placeholders})
            GROUP BY subject_id, object_id""",
        node_ids,
    ).fetchall()
    by_player: dict = defaultdict(list)
    for r in rows:
        by_player[r["subject_id"]].append((r["first_season"], _canonical_team(r["object_id"])))
    out = {}
    for pid, entries in by_player.items():
        entries.sort()
        seen = set()
        teams = []
        for _season, team in entries:
            if team not in seen:
                seen.add(team)
                teams.append(team)
        out[pid] = teams
    return out


def _position_by_player(c, node_ids: list) -> dict:
    """{node_id: position_code}, the single most-frequently-recorded raw
    PLAYED_POSITION code per player (tie-break: most recent season, then
    alphabetical, for full determinism). Deliberately NOT translated to a
    "cleaner" specific code when the graph itself only ever recorded a
    generic bucket (e.g. "DB", "OL", "DL") for a player -- guessing CB vs. S
    for a player this data only ever calls "DB" would be exactly the kind of
    fabrication this project doesn't do. Fixed on the OTHER side instead:
    data/grid.js's own pos_db/pos_ol/pos_dl criterion test() functions were
    extended to recognize these same generic codes directly (see that
    file's own comment), mirroring gateway/services/grid.py's already-
    established POSITION_GROUPS equivalence classes -- "DB" already
    unambiguously means "defensive back," which is exactly what pos_db
    tests for; no guess required."""
    placeholders = ",".join("?" for _ in node_ids)
    rows = c.execute(
        f"""SELECT subject_id, object_id, COUNT(*) n, MAX(season_start) last_season
            FROM graph_edges WHERE predicate='PLAYED_POSITION' AND subject_id IN ({placeholders})
            GROUP BY subject_id, object_id""",
        node_ids,
    ).fetchall()
    by_player: dict = defaultdict(list)
    for r in rows:
        by_player[r["subject_id"]].append((-r["n"], -r["last_season"], r["object_id"]))
    out = {}
    for pid, entries in by_player.items():
        entries.sort()
        out[pid] = entries[0][2]
    return out


def _draft_by_player(c, node_ids: list) -> dict:
    """{node_id: (round, year, college)} via draft_facts, joined on
    player_key = node_id directly (draft_facts.player_key already uses the
    same 'PFR:xxx' convention as graph node_ids for matched picks -- see
    tools/quiz_export/adapters/draft_college.py for the same table's
    college-column provenance). round=-1/year=0/college="" (data/grid.js's
    own established "no data" convention -- see 2,573 existing entries using
    it) when no draft_facts row exists, NEVER round=0 (which the game's own
    draft_undrafted criterion reads as a confirmed fact) for an unmatched
    player -- absence of a row means "not found," not "confirmed
    undrafted," the exact distinction gateway/services/grid.py's own
    module docstring already establishes for this same table."""
    placeholders = ",".join("?" for _ in node_ids)
    rows = c.execute(
        f"""SELECT player_key, draft_round, draft_season, college FROM draft_facts
            WHERE player_key IN ({placeholders}) AND verification_status='SOURCE_BACKED' AND source_id=?""",
        (*node_ids, DRAFT_SOURCE),
    ).fetchall()
    return {
        r["player_key"]: (r["draft_round"], r["draft_season"], r["college"] or "")
        for r in rows
    }


def _accolades_by_player(c, node_ids: list) -> dict:
    """{node_id: {"hof": bool, "allPro": int, "proBowls": int}} via
    player_accolades (see tools/quiz_export/adapters -- same table
    gateway/services/grid.py's own hof/allpro_3plus/probowl_5plus/
    probowl_10plus criteria are built on). allPro/proBowls are CAREER
    totals (source limitation, same one grid.py discloses), not
    season-by-season selections."""
    placeholders = ",".join("?" for _ in node_ids)
    rows = c.execute(
        f"""SELECT player_id, accolade_type, count_value FROM player_accolades
            WHERE player_id IN ({placeholders})""",
        node_ids,
    ).fetchall()
    out: dict = defaultdict(lambda: {"hof": False, "allPro": 0, "proBowls": 0})
    for r in rows:
        rec = out[r["player_id"]]
        if r["accolade_type"] == "HALL_OF_FAME":
            rec["hof"] = True
        elif r["accolade_type"] == "ALL_PRO_FIRST_TEAM_CAREER_COUNT":
            rec["allPro"] = r["count_value"] or 0
        elif r["accolade_type"] == "PRO_BOWL_CAREER_COUNT":
            rec["proBowls"] = r["count_value"] or 0
    return out


def _sb_champs(c, node_ids: list) -> set:
    """Set of node_ids with >=1 real season where PLAYED_FOR(player, team,
    season) matches a team-season where PLAYOFF_RESULT(team, season) =
    'WonSB' -- the exact derived-fact join gateway/services/grid.py's own
    sb_champ criterion already uses (reused logic, not reinvented)."""
    placeholders = ",".join("?" for _ in node_ids)
    rows = c.execute(
        f"""SELECT DISTINCT pf.subject_id FROM graph_edges pf
            JOIN graph_edges pr
              ON pr.predicate='PLAYOFF_RESULT' AND pr.object_type='playoff_result' AND pr.object_id='WonSB'
             AND pr.subject_type='team' AND pr.subject_id=pf.object_id
             AND pr.season_start=pf.season_start
            WHERE pf.predicate='PLAYED_FOR' AND pf.subject_id IN ({placeholders})""",
        node_ids,
    ).fetchall()
    return {r["subject_id"] for r in rows}


def build() -> dict:
    c = engine.connect()
    try:
        played_for_universe = c.execute(
            "SELECT COUNT(DISTINCT subject_id) FROM graph_edges WHERE predicate='PLAYED_FOR'"
        ).fetchone()[0]
        safe_players, ambiguous_names, ambiguous_rows = _safe_played_for_players(c)
        existing_names = _existing_grid_js_names()

        # Second exclusion tier: an Engine candidate whose name already
        # exists in the hand-curated pool. Kept separate from the
        # within-Engine ambiguity count above for honest, distinct reporting.
        candidates = {
            nid: name for nid, name in safe_players.items() if name not in existing_names
        }
        name_collision_count = len(safe_players) - len(candidates)

        node_ids = sorted(candidates.keys())
        teams = _teams_by_player(c, node_ids)
        positions = _position_by_player(c, node_ids)
        draft = _draft_by_player(c, node_ids)
        accolades = _accolades_by_player(c, node_ids)
        sb_champs = _sb_champs(c, node_ids)

        players = []
        no_position = 0
        no_draft = 0
        for nid in node_ids:
            player_teams = teams.get(nid, [])
            if not player_teams:
                continue  # structurally impossible (join guarantees >=1), defensive only
            pos = positions.get(nid)
            if pos is None:
                no_position += 1
            d = draft.get(nid)
            if d is None:
                no_draft += 1
                draft_round, draft_year, college = -1, 0, ""
            else:
                draft_round, draft_year, college = d[0], d[1], d[2]
            acc = accolades.get(nid, {"hof": False, "allPro": 0, "proBowls": 0})
            players.append({
                "name": candidates[nid],
                "teams": player_teams,
                "position": pos,
                "draft": {"round": draft_round, "year": draft_year},
                "college": college,
                "hof": acc["hof"],
                "mvp": False,
                "sbChamp": nid in sb_champs,
                "sbMVP": False,
                "proBowls": acc["proBowls"],
                "allPro": acc["allPro"],
                "roty": False,
            })
    finally:
        c.close()

    header = (
        "// Auto-generated NFL Grid player pool -- Engine v4.0-sourced, NOT hand-curated.\n"
        "// Concatenated onto window.GRID_PLAYERS (see app.js's refreshDataAliases()) --\n"
        "// data/grid.js's own hand-curated GRID_PLAYERS array is never modified by this file.\n"
        "// Regenerate: python3 tools/grid_export/build_grid_engine_players.py\n"
        "// See that script's module docstring for full provenance, identity-safety rules,\n"
        "// and exactly which of the 21 real Grid criteria this data can and cannot back.\n"
    )
    js = header + "window.GRID_ENGINE_PLAYERS = " + json.dumps(players, indent=1) + ";\n"
    OUT_PATH.write_text(js)

    return {
        "out_path": str(OUT_PATH),
        "played_for_candidate_universe": played_for_universe,
        "safe_unambiguous_candidates": len(safe_players),
        "excluded_ambiguous_names": ambiguous_names,
        "excluded_ambiguous_rows": ambiguous_rows,
        "excluded_name_collision_with_hand_curated": name_collision_count,
        "exported_players": len(players),
        "exported_missing_position": no_position,
        "exported_missing_draft_data": no_draft,
        "bytes": len(js),
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, default=str))
