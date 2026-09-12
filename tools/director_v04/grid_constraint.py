"""GRID_CONSTRAINT_BOARD -- 40-Format Expansion pass, new mechanic template.

Backs the new CONNECTION_GRID format: a 3x3 board where each cell's valid
answer must satisfy BOTH a real row criterion and a real column criterion
(e.g. "drafted in round 1" x "played for the Dallas Cowboys").

Deliberately NOT the same architecture as the existing GRID_BOARD
(Immaculate Grid, app.js) -- that mode is fully client-side (every real
player already sits in a static data file before a single guess is made;
see visual_templates.py's own GRID_BOARD entry for the disclosed
architectural gap this format explicitly does not repeat). This module is
real and server-authoritative: the package publishes only the row/column
CRITERIA LABELS (never a precomputed answer list, which a browser could
inspect); every submitted name is checked live against the real database at
answer time -- the exact same "verify the submission against live truth,
never trust a precomputed key the client could see" discipline
coach_connections_graph.py already established for Six Degrees.

Real, confirmed-live data (40-Format Expansion pass's own data audit):
NFL_TEAM_DRAFT_ROUND_GRID crosses 3 real teams (canonical_roster_seasons.
team_code) against 3 real draft rounds (draft_facts.draft_round -- the
certified, verification_status-bearing sibling of nfl_players_draft, same
real convention draft.py's own DRAFTED_BY capability already uses). One
confirmed real cell (Round 1 x Dallas Cowboys) already has 85 distinct
real players, comfortably clearing the "at least 1 real answer per cell"
bar with room to spare against collisions.

Answer checking is BY NAME, not by a hidden player_key, matching how a
player would naturally guess (they know a name, not an internal id) --
real name collisions exist in the underlying data (multiple distinct
players can share an identical name), so a submitted name is accepted if
ANY real player with that name satisfies both the row and column criteria,
never requiring the player to disambiguate an identity they were never
shown.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "GRID_CONSTRAINT_BOARD"
GRID_SIZE = 3  # 3x3 -- the user's own explicitly requested initial size

VARIANTS = frozenset({"NFL_TEAM_DRAFT_ROUND_GRID"})

_ROSTER_ROW_SQL = (
    "SELECT COUNT(DISTINCT d.player_name) FROM draft_facts d "
    "JOIN canonical_roster_seasons r ON r.player_id = d.player_key "
    "WHERE r.team_code = ? AND r.verification_status = 'SOURCE_BACKED' "
    "AND d.verification_status = 'SOURCE_BACKED' AND d.draft_round = ?"
)
_ROSTER_ROW_CHECK_SQL = (
    "SELECT COUNT(*) FROM draft_facts d "
    "JOIN canonical_roster_seasons r ON r.player_id = d.player_key "
    "WHERE r.team_code = ? AND r.verification_status = 'SOURCE_BACKED' "
    "AND d.verification_status = 'SOURCE_BACKED' AND d.draft_round = ? "
    "AND d.player_name = ? COLLATE NOCASE"
)


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        # Real, confirmed second legitimate source for this table
        # (NFLVERSE_ROSTERS, 21,527 rows) alongside the original NFLVERSE_DATA
        # rows -- check_table_wide_safety's required_source accepts a list
        # for exactly this case (see this session's Engine-schema-drift notes).
        "canonical_roster_seasons": safety.check_table_wide_safety(
            c, "canonical_roster_seasons", ["NFLVERSE_DATA", "NFLVERSE_ROSTERS"]
        ),
    }


def _real_team_pool(c) -> list[str]:
    return [r["team_code"] for r in c.execute(
        "SELECT DISTINCT team_code FROM canonical_roster_seasons WHERE verification_status='SOURCE_BACKED' "
        "ORDER BY team_code"
    ).fetchall()]


def _nfl_team_draft_round_grid(c, seed: str) -> dict:
    rng = engine_bootstrap.seeded(seed)
    teams = _real_team_pool(c)
    rng.shuffle(teams)
    rounds = [1, 2, 3, 4, 5, 6, 7]
    rng.shuffle(rounds)

    chosen_teams: list[str] = []
    chosen_rounds: list[int] = []
    cells: dict[tuple[int, int], int] = {}

    # Real, live per-cell verification -- never assumed from static config.
    # Greedy real search: try team/round combinations until 3 real rows and
    # 3 real columns are found where every one of the resulting 9 cells has
    # >= 1 real distinct answer.
    for team in teams:
        if len(chosen_teams) >= GRID_SIZE:
            break
        candidate_rounds_ok = 0
        trial_cells = {}
        for rnd in (chosen_rounds or rounds):
            n = c.execute(_ROSTER_ROW_SQL, (team, rnd)).fetchone()[0]
            if n >= 1:
                trial_cells[rnd] = n
                candidate_rounds_ok += 1
        if chosen_rounds:
            if all(rnd in trial_cells for rnd in chosen_rounds):
                chosen_teams.append(team)
        else:
            if candidate_rounds_ok >= GRID_SIZE:
                # First team found -- lock in its first GRID_SIZE real rounds as the columns.
                chosen_rounds = [rnd for rnd in rounds if rnd in trial_cells][:GRID_SIZE]
                chosen_teams.append(team)

    for ri, team in enumerate(chosen_teams):
        for ci, rnd in enumerate(chosen_rounds):
            n = c.execute(_ROSTER_ROW_SQL, (team, rnd)).fetchone()[0]
            cells[(ri, ci)] = n

    return {
        "row_labels": [f"Played for the {team}" for team in chosen_teams],
        "col_labels": [f"Drafted in Round {rnd}" for rnd in chosen_rounds],
        "row_criteria": [{"kind": "team_code", "value": team} for team in chosen_teams],
        "col_criteria": [{"kind": "draft_round", "value": rnd} for rnd in chosen_rounds],
        "cell_candidate_counts": cells,
    }


def generate_grid(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        grid = _nfl_team_draft_round_grid(c, seed)
    finally:
        c.close()

    complete = (
        len(grid["row_labels"]) == GRID_SIZE and len(grid["col_labels"]) == GRID_SIZE
        and all(grid["cell_candidate_counts"].get((r, cc), 0) >= 1 for r in range(GRID_SIZE) for cc in range(GRID_SIZE))
    )
    shortfall_reason = None if complete else (
        f"Could not find {GRID_SIZE} real rows x {GRID_SIZE} real columns where every one of the "
        f"{GRID_SIZE * GRID_SIZE} cells has a genuine, real, distinct answer -- no grid was built rather "
        f"than publish a cell with zero real candidates."
    )
    return {"grid": grid, "safety": safety_result, "shortfall_reason": shortfall_reason, "complete": complete}


def check_cell_answer(c, variant: str, row_criteria: list[dict], col_criteria: list[dict],
                       row_index: int, col_index: int, guess_name: str) -> bool:
    """Server-authoritative, live re-verification of a submitted answer --
    never checked against a precomputed key. Real name-collision tolerant:
    accepted if ANY real player with this name satisfies both criteria."""
    if variant != "NFL_TEAM_DRAFT_ROUND_GRID":
        raise ValueError(f"unsupported variant {variant!r}")
    row = row_criteria[row_index]
    col = col_criteria[col_index]
    guess_name = (guess_name or "").strip()
    if not guess_name:
        return False
    n = c.execute(_ROSTER_ROW_CHECK_SQL, (row["value"], col["value"], guess_name)).fetchone()[0]
    return n > 0


def build_package(seed: str, variant: str) -> dict:
    result = generate_grid(seed, variant)
    package_id = "GGP11:" + hashlib.sha256(
        f"GRID_CONSTRAINT|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    grid = result["grid"]
    cells_public = [
        {"row_index": r, "col_index": cc, "guess": None, "correct": None}
        for r in range(len(grid["row_labels"])) for cc in range(len(grid["col_labels"]))
    ]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "NFL Connection Grid",
        "game_instructions": "Each cell needs a real player who satisfies BOTH its row and column criteria. "
                              "Type a real name for each cell.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if result["complete"] else "FAILED",
        "row_labels": grid["row_labels"], "col_labels": grid["col_labels"],
        "cells": cells_public,
        "_private_row_criteria": grid["row_criteria"], "_private_col_criteria": grid["col_criteria"],
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
