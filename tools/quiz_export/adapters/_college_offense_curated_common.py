"""Shared helper for every adapter built on `curated_nfl_offense_college_board`
/ `curated_nfl_offense_college_position` (Rivalry Data + Gold Standard
Content Integration operation) -- the normalized import of the Gold
Standard Game Mode Blueprint workbook's "3. Pre-Made Puzzles" (32 real 2026
projected NFL team offenses) and "7/8. SB Modern/Historic" (60 real Super
Bowl champion offenses, 1967-2026) sheets. Both sheets share the exact same
11-position shape (LT, LG, C, RG, RT, WR1, QB, WR2, WR3, RB, TE), all real
colleges, zero player names by construction (player names live only in the
separate, deliberately-unimported "4. Answer Key" sheet -- see the import
script's own module docstring).

Factored out because two sibling adapters
(`nfl_offense_college_curated.py` for CURRENT_TEAM_2026,
`sb_champion_offense_college.py` for SB_CHAMPION) need the identical
"load one board's full position->college map" query -- not because the two
capabilities are the same domain (they have different answer contracts:
guess-the-team vs guess-the-team-and-season -- kept as separate registered
capabilities, same discipline `lineup_college.py`'s own docstring documents
for its sibling relationship to `lineup.py`)."""
from __future__ import annotations

POSITIONS = ("LT", "LG", "C", "RG", "RT", "WR1", "QB", "WR2", "WR3", "RB", "TE")


def possessive(name: str) -> str:
    """Grammatically correct possessive for a team display name -- real
    polish fix: every one of these curated adapters previously wrote
    f"{team}'s", which reads as "49ers's"/"Steelers's" for the (very
    common, real NFL franchise names) that already end in 's'. Standard
    English style adds only an apostrophe for a plural noun already ending
    in 's' ("49ers'", "Steelers'"), and "'s" otherwise ("Colts's" would be
    wrong too -- "Colts'" for the same reason)."""
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def all_colleges(c) -> list[str]:
    """Every distinct real college appearing anywhere in the curated
    dataset (both board types combined) -- the plausible-distractor pool for
    every "which college is NOT really part of this lineup" style capability
    below. Real, not fabricated: every value here is a college that really
    appears on some real curated board."""
    rows = c.execute("SELECT DISTINCT college FROM curated_nfl_offense_college_position ORDER BY college").fetchall()
    return [r["college"] for r in rows]


def fetch_boards(c, board_type: str) -> list[dict]:
    """Every real board of the given type, each with its full ordered
    position->college map attached. Raises if any board is missing a
    position row -- this table is import-time validated to have exactly
    11 positions per board (see the import script), so a gap here would
    mean real data corruption, not a normal, expected gap to route around."""
    boards = c.execute(
        "SELECT board_id, team_code, franchise_id, team_display_name, season, difficulty, notes "
        "FROM curated_nfl_offense_college_board WHERE board_type = ? ORDER BY board_id",
        (board_type,),
    ).fetchall()
    out = []
    for b in boards:
        pos_rows = c.execute(
            "SELECT position, college FROM curated_nfl_offense_college_position WHERE board_id = ?",
            (b["board_id"],),
        ).fetchall()
        positions = {r["position"]: r["college"] for r in pos_rows}
        missing = [p for p in POSITIONS if p not in positions]
        if missing:
            raise ValueError(f"board {b['board_id']} is missing position(s) {missing} -- real data corruption.")
        out.append({
            "board_id": b["board_id"], "team_code": b["team_code"], "franchise_id": b["franchise_id"],
            "team_display_name": b["team_display_name"], "season": b["season"], "difficulty": b["difficulty"],
            "notes": b["notes"], "positions": positions,
        })
    return out
