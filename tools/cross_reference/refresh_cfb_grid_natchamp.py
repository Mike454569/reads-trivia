"""Cross-reference CFB_GRID_PLAYERS (data/cfb-grid.js) `natChamp` flags
against the Engine's real, SOURCE_BACKED `cfb_champion_school_links` table
-- App-Wide Engine Migration operation, Part I.

Scope, deliberately narrow: only ADDS `natChamp: true` where a player's own
curated (school, year) overlaps a real championship season for that school
-- never removes/flips an existing `natChamp: true` (no case where the
Engine data proves one wrong was found; see the module's own audit run).
`heisman` was audited too (cross-referenced against cfb_award_facts) and
found already 100% accurate for all 940 players -- the 3 candidates an
initial name-only pass flagged were resolved as nickname-normalization
false positives (Johnny/John Lattner, Clint/Clinton Frank) or a
same-named-different-person mixup already correctly split into two
separate curated entries (two real "Bruce Smith"s: Minnesota 1941 Heisman
winner, and an unrelated 1984 Virginia Tech player) -- so `heisman` is left
untouched entirely, not because it can't be checked but because checking
it found nothing to fix.

`hof` (Pro Football Hall of Fame, i.e. these CFB players' later NFL
careers) is deliberately NOT cross-referenced this pass -- doing so
correctly would require the CFB<->NFL identity bridge
(cfb_nfl_identity_bridge_certified), previously measured elsewhere in this
project to have low real coverage for exactly this kind of lookup; a
low-confidence bridge join is a worse foundation for a boolean truth flag
than leaving the existing curated value alone.

School-name vocabulary note: `cfb_champion_school_links.school_name` uses
"USC" and "Miami" where CFB_GRID_PLAYERS' own `schools` field (matching
this file's own header-documented aliasing convention) uses "Southern
California" and "Miami (FL)" -- a real vocabulary mismatch that silently
produced 9 false "can't verify" results before the alias map below was
added; confirmed by checking cfb_champion_school_links's actual distinct
school_name values directly rather than assuming a match.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402
from tools.cross_reference.refresh_grid_accolades import dump_raw_array_json, extract_array_literal  # noqa: E402

SCHOOL_ALIAS = {"Southern California": "USC", "Miami (FL)": "Miami"}


def refresh(js_path: Path, global_name: str, scratch_dir: Path) -> dict:
    c = engine.connect()
    champ_by_school: dict[str, set[int]] = {}
    for r in c.execute("SELECT season, school_name FROM cfb_champion_school_links").fetchall():
        champ_by_school.setdefault(r["school_name"], set()).add(r["season"])

    file_text = js_path.read_text()
    literal_text, start, end = extract_array_literal(file_text, global_name)

    scratch_dir.mkdir(parents=True, exist_ok=True)
    snippet_path = scratch_dir / f"{global_name}_snippet.js"
    snippet_path.write_text(literal_text)
    dump_path = scratch_dir / f"{global_name}_dump.json"
    players = dump_raw_array_json(snippet_path, global_name, dump_path)

    additions = []
    for p in players:
        if p.get("natChamp"):
            continue  # never touch an existing True
        real_champ = False
        for sc in p.get("schools") or []:
            key = SCHOOL_ALIAS.get(sc, sc)
            champ_years = champ_by_school.get(key, set())
            if champ_years and any(y in champ_years for y in (p.get("years") or [])):
                real_champ = True
                break
        if real_champ:
            additions.append(p["name"])

    applied = 0
    new_literal = literal_text
    for name in additions:
        name_escaped = re.escape(name)
        line_pat = re.compile(r'(\{ "name": "' + name_escaped + r'",.*?\},?\n)')
        m = line_pat.search(new_literal)
        if not m:
            print(f"  WARNING: could not locate line for {name!r} — skipped.")
            continue
        line = m.group(1)
        fixed = re.sub(r'"natChamp": false', '"natChamp": true', line)
        if fixed != line:
            new_literal = new_literal[: m.start(1)] + fixed + new_literal[m.end(1):]
            applied += 1

    if applied:
        js_path.write_text(file_text[:start] + new_literal + file_text[end:])

    return {
        "file": str(js_path),
        "total_players": len(players),
        "natchamp_additions_found": len(additions),
        "natchamp_additions_applied": applied,
        "additions": additions,
    }


if __name__ == "__main__":
    scratch = Path("/tmp/cfb_grid_xref_scratch")
    result = refresh(REPO_ROOT / "data" / "cfb-grid.js", "CFB_GRID_PLAYERS", scratch)
    print(json.dumps({k: v for k, v in result.items() if k != "additions"}, indent=2))
    for n in result["additions"]:
        print(" ", n)
