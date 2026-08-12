"""Cross-reference GRID_PLAYERS (data/grid.js) against the Engine's real,
SOURCE_BACKED accolade tables (player_accolades, draft_facts) and correct
ONLY the specific hof/proBowls/allPro fields Engine can verify -- App-Wide
Engine Migration operation, Part I ("Make Engine v4.0 the authoritative
validation/eligibility layer wherever coverage supports it").

Why this exists: grid.js's own header discloses its accolade fields are
"hand-authored... not scraped" -- i.e. never verified against a real
source. player_accolades (1,944 rows: 102 HALL_OF_FAME, 1,325
PRO_BOWL_CAREER_COUNT, 517 ALL_PRO_FIRST_TEAM_CAREER_COUNT) is 100%
verification_status='SOURCE_BACKED' from NFLVERSE_DATA/PFR -- a strictly
more authoritative source for exactly these three fields.

What this deliberately does NOT touch: the `draft` field (round/year),
`mvp`/`sbChamp`/`sbMVP`/`roty` (no Engine table covers NFL MVP / Super
Bowl champion-as-player / Super Bowl MVP / Rookie of the Year -- only
CFB has an awards table), `teams`/`position`/`college`/`name`, or any
player Engine can't uniquely identify. Corrections apply ONLY to players
matched via a high-confidence key.

Matching strategy (and why): normalized name + position-group + the
player's own curated draft year. A real risk was found and measured
directly against this database before settling on this key: matching by
name+position alone produces real collisions (e.g. two different real
players both named "Reggie White", DE -- the Hall of Fame legend
[undrafted, 1984] and an unrelated 1992 6th-round pick share the exact
name and position). A team-overlap disambiguator was tried next and
rejected -- it produced ~500 FALSE rejections, because GRID_PLAYERS'
`teams` field is frequently an incomplete career history for
non-superstar players (often just one team), not the comprehensive list
its own header claims. Draft year, by contrast, is a single memorable
fact unlikely to be wrong in a hand-curated set and is highly specific
(few players share name+position+exact draft year) -- confirmed: this
key alone eliminates the Reggie White-style collisions with no
team-history dependency. Players with no curated draft year (undrafted,
~2,574 of 3,717) are excluded from this pass rather than guessed at.

Usage: run after any refresh that updates draft_facts/player_accolades.
Idempotent -- re-running with no real data changes makes no edits.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402

_JXA_DUMP = r"""
ObjC.import("Foundation");
function readFile(path) {
  var str = $.NSString.stringWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null);
  return ObjC.unwrap(str);
}
function writeFile(path, content) {
  var str = $.NSString.alloc.initWithUTF8String(content);
  str.writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, null);
}
var src = readFile(SRC_PATH);
var window = {};
new Function("window", src)(window);
writeFile(OUT_PATH, JSON.stringify(window[GLOBAL_NAME]));
"""


def dump_raw_array_json(js_snippet_path: Path, global_name: str, out_path: Path) -> list[dict]:
    """Evaluate a standalone JS snippet (just the array literal assignment,
    no downstream .map()/normalization) and dump it as JSON. Using a
    snippet -- not the full data file -- specifically avoids picking up
    fields a later `.map()` normalization step adds (e.g. grid.js appends
    a `roty` key downstream; the raw literal never has one)."""
    script = _JXA_DUMP.replace("SRC_PATH", json.dumps(str(js_snippet_path)))
    script = script.replace("OUT_PATH", json.dumps(str(out_path)))
    script = script.replace("GLOBAL_NAME", json.dumps(global_name))
    subprocess.run(["osascript", "-l", "JavaScript", "-e", script], check=True, capture_output=True)
    return json.loads(out_path.read_text())


def extract_array_literal(file_text: str, global_name: str) -> tuple[str, int, int]:
    """Returns (literal_text, start_char_offset, end_char_offset) for
    `window.<global_name> = [ ... ];` -- the FIRST such assignment only
    (grid.js/cfb-grid.js each have exactly one raw literal, followed by a
    separate `.map()` reassignment further down)."""
    pattern = re.compile(r"window\." + re.escape(global_name) + r"\s*=\s*\[.*?\n\];\n", re.DOTALL)
    m = pattern.search(file_text)
    if not m:
        raise SystemExit(f"Could not find `window.{global_name} = [...]` literal.")
    return m.group(0), m.start(), m.end()


def norm_name(s: str | None) -> str:
    s = (s or "").lower()
    s = re.sub(r"[.']", "", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def pos_group(p: str | None) -> str:
    p = (p or "").upper()
    if p in ("OG", "OT", "G", "T", "C", "OL"):
        return "OL"
    if p in ("DE", "DT", "NT", "DL"):
        return "DL"
    if p in ("CB", "S", "DB"):
        return "DB"
    if p == "FB":
        return "RB"
    if p == "EDGE":
        return "EDGE"
    return p


def build_matches(players: list[dict], draft_rows) -> dict[str, str]:
    by_strict: dict[tuple, list] = {}
    for r in draft_rows:
        key = (norm_name(r["player_name"]), pos_group(r["position"]), r["draft_season"])
        by_strict.setdefault(key, []).append(r)

    matched = {}
    for p in players:
        dyear = (p.get("draft") or {}).get("year")
        if not dyear:
            continue
        n, pg = norm_name(p["name"]), pos_group(p.get("position"))
        keys = [(n, "LB", dyear), (n, "DL", dyear)] if pg == "EDGE" else [(n, pg, dyear)]
        cands = [c for k in keys for c in by_strict.get(k, [])]
        if len(cands) == 1:
            matched[p["name"]] = cands[0]["player_key"]
    return matched


def compute_corrections(players: list[dict], matched: dict[str, str], acc_by_pid: dict) -> list[dict]:
    corrections = []
    for p in players:
        key = matched.get(p["name"])
        if not key:
            continue
        acc = acc_by_pid.get(key, {})
        fixes = {}
        real_hof = "HALL_OF_FAME" in acc
        if bool(p.get("hof", False)) != real_hof:
            fixes["hof"] = real_hof
        if "PRO_BOWL_CAREER_COUNT" in acc and acc["PRO_BOWL_CAREER_COUNT"] is not None:
            real_pb = int(acc["PRO_BOWL_CAREER_COUNT"])
            if p.get("proBowls") != real_pb:
                fixes["proBowls"] = real_pb
        if "ALL_PRO_FIRST_TEAM_CAREER_COUNT" in acc and acc["ALL_PRO_FIRST_TEAM_CAREER_COUNT"] is not None:
            real_ap = int(acc["ALL_PRO_FIRST_TEAM_CAREER_COUNT"])
            if p.get("allPro") != real_ap:
                fixes["allPro"] = real_ap
        if fixes:
            corrections.append({"name": p["name"], "player_key": key, "fixes": fixes})
    return corrections


def apply_corrections_to_literal(literal_text: str, corrections: list[dict]) -> tuple[str, int]:
    """Line-level regex substitution -- touches only the specific
    hof:/proBowls:/allPro: tokens on each matched player's own line,
    leaving every other character (formatting, key order, every other
    field, every non-matched player) byte-identical."""
    applied = 0
    for c in corrections:
        name_escaped = re.escape(c["name"])
        line_pat = re.compile(r'(\{ name: "' + name_escaped + r'",.*?\},?\n)')
        m = line_pat.search(literal_text)
        if not m:
            print(f"  WARNING: could not locate line for {c['name']!r} — skipped.")
            continue
        line = m.group(1)
        new_line = line
        if "hof" in c["fixes"]:
            new_line = re.sub(r"hof: (true|false)", f"hof: {str(c['fixes']['hof']).lower()}", new_line)
        if "proBowls" in c["fixes"]:
            new_line = re.sub(r"proBowls: \d+", f"proBowls: {c['fixes']['proBowls']}", new_line)
        if "allPro" in c["fixes"]:
            new_line = re.sub(r"allPro: \d+", f"allPro: {c['fixes']['allPro']}", new_line)
        if new_line != line:
            literal_text = literal_text[: m.start(1)] + new_line + literal_text[m.end(1):]
            applied += 1
    return literal_text, applied


def refresh(js_path: Path, global_name: str, scratch_dir: Path) -> dict:
    c = engine.connect()
    draft_rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_team, draft_round, position FROM draft_facts"
    ).fetchall()
    acc_rows = c.execute("SELECT player_id, accolade_type, count_value FROM player_accolades").fetchall()
    acc_by_pid: dict[str, dict] = {}
    for r in acc_rows:
        acc_by_pid.setdefault(r["player_id"], {})[r["accolade_type"]] = r["count_value"]

    file_text = js_path.read_text()
    literal_text, start, end = extract_array_literal(file_text, global_name)

    scratch_dir.mkdir(parents=True, exist_ok=True)
    snippet_path = scratch_dir / f"{global_name}_snippet.js"
    snippet_path.write_text(literal_text)
    dump_path = scratch_dir / f"{global_name}_dump.json"
    players = dump_raw_array_json(snippet_path, global_name, dump_path)

    matched = build_matches(players, draft_rows)
    corrections = compute_corrections(players, matched, acc_by_pid)

    new_literal, applied = apply_corrections_to_literal(literal_text, corrections)
    if applied:
        new_file_text = file_text[:start] + new_literal + file_text[end:]
        js_path.write_text(new_file_text)

    return {
        "file": str(js_path),
        "total_players": len(players),
        "matched_high_confidence": len(matched),
        "corrections_found": len(corrections),
        "corrections_applied": applied,
        "corrections": corrections,
    }


if __name__ == "__main__":
    scratch = Path("/tmp/grid_xref_scratch")
    result = refresh(REPO_ROOT / "data" / "grid.js", "GRID_PLAYERS", scratch)
    print(json.dumps({k: v for k, v in result.items() if k != "corrections"}, indent=2))
    for c in result["corrections"]:
        print(" ", c["name"], c["fixes"])
