"""Cross-reference LEGENDS_TEAMS (data/legends.js) `fppg` values against
the Engine's real, now-populated `player_season_stats` (nflverse-data,
SOURCE_BACKED, includes nflverse's own standard-PPR `fantasy_points_ppr`)
-- Historical Engine Enrichment operation, continuation.

Real finding that justifies this: legends.js's own header already
discloses its fppg values are "approximate... not exact box-score
accurate," hand-authored without a real source. Comparing the full
curated pool against real per-game stats (real fppg = fantasy_points_ppr
/ games) confirmed this -- some curated values were wildly off (Arian
Foster's real 2015 fppg is 19.2, curated said 7.5; Christian McCaffrey's
real 2020 fppg is 30.1, curated said 21.6). This corrects fppg ONLY,
matched via (team, year, player name), never touching which players/
teams are curated (the mission's own explicit "preserve the existing
editorial character" instruction) -- no roster ever gains or loses a
player here, no team-season is added or removed. `position` is trusted
as-is from the curated data (used only to select the matching stat
column in the DEF-less version of the roster; DEF entries are skipped
entirely, since there is no real per-player DEF fppg to compute).

Block-scoped, not global-regex: multiple team-seasons legitimately share
player names (a star having his LEGENDS_TEAMS entry from two different
years, e.g. Josh Allen in both the 2020 and 2021 Bills blocks) -- editing
by a bare `name: "X"` match risks touching the wrong occurrence. Each
`{ team, year, players: [...] }` block is isolated by regex first, then
each player line inside that specific block is matched and corrected
independently, so a same-named player in a different block is never
touched by mistake.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402
from tools.cross_reference.refresh_grid_accolades import dump_raw_array_json  # noqa: E402

def norm_name(s: str | None) -> str:
    s = (s or "").lower()
    s = re.sub(r"[.']", "", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def refresh(js_path: Path, global_name: str, scratch_dir: Path) -> dict:
    c = engine.connect()
    canon_by_name: dict[str, list[str]] = {}
    for r in c.execute("SELECT player_id, display_name FROM canonical_players").fetchall():
        canon_by_name.setdefault(norm_name(r["display_name"]), []).append(r["player_id"])

    stats_by_key_season: dict[tuple[str, int], tuple[int | None, float | None]] = {}
    for r in c.execute("SELECT season, player_key, games, fantasy_points_ppr FROM player_season_stats").fetchall():
        stats_by_key_season[(r["player_key"], r["season"])] = (r["games"], r["fantasy_points_ppr"])

    file_text = js_path.read_text()

    scratch_dir.mkdir(parents=True, exist_ok=True)
    snippet_path = scratch_dir / f"{global_name}_snippet.js"
    array_start = file_text.index(f"window.{global_name} = [")
    array_end = file_text.index("\n];\n", array_start) + 4
    literal_text = file_text[array_start:array_end]
    snippet_path.write_text(literal_text)
    dump_path = scratch_dir / f"{global_name}_dump.json"
    teams = dump_raw_array_json(snippet_path, global_name, dump_path)

    corrections = []
    ambiguous_name_skips = 0
    for t in teams:
        for p in t["players"]:
            if p.get("position") == "DEF":
                continue
            n = norm_name(p["name"])
            cands = canon_by_name.get(n, [])
            if len(cands) != 1:
                if len(cands) > 1:
                    ambiguous_name_skips += 1
                continue
            key = cands[0]
            games, pts = stats_by_key_season.get((key, t["year"]), (None, None))
            if not games or pts is None:
                continue
            real_fppg = round(pts / games, 1)
            if abs(real_fppg - p["fppg"]) >= 0.1:
                corrections.append({"team": t["team"], "year": t["year"], "name": p["name"],
                                     "old_fppg": p["fppg"], "new_fppg": real_fppg})

    applied = 0
    new_text = file_text
    for corr in corrections:
        block_pat = re.compile(
            r'\{ team: "' + re.escape(corr["team"]) + r'", year: ' + str(corr["year"]) + r', players: \[.*?\n  \]\},?\n',
            re.DOTALL,
        )
        bm = block_pat.search(new_text)
        if not bm:
            print(f"  WARNING: block not found for {corr['team']} {corr['year']} — skipped.")
            continue
        block_text = bm.group(0)
        line_pat = re.compile(r'(\{ name: "' + re.escape(corr["name"]) + r'", position: "\w+", fppg: [\d.]+ \},?\n)')
        lm = line_pat.search(block_text)
        if not lm:
            print(f"  WARNING: line not found for {corr['name']} in {corr['team']} {corr['year']} — skipped.")
            continue
        old_line = lm.group(1)
        new_line = re.sub(r"fppg: [\d.]+", f"fppg: {corr['new_fppg']}", old_line)
        new_block = block_text[: lm.start(1)] + new_line + block_text[lm.end(1):]
        new_text = new_text[: bm.start()] + new_block + new_text[bm.end():]
        applied += 1

    if applied:
        js_path.write_text(new_text)

    return {
        "file": str(js_path),
        "total_team_seasons": len(teams),
        "corrections_found": len(corrections),
        "corrections_applied": applied,
        "ambiguous_name_skips": ambiguous_name_skips,
        "corrections": corrections,
    }


if __name__ == "__main__":
    scratch = Path("/tmp/legends_xref_scratch")
    result = refresh(REPO_ROOT / "data" / "legends.js", "LEGENDS_TEAMS", scratch)
    print(json.dumps({k: v for k, v in result.items() if k != "corrections"}, indent=2))
    for c in result["corrections"][:30]:
        print(" ", c)
    if len(result["corrections"]) > 30:
        print(f"  ... and {len(result['corrections']) - 30} more")
