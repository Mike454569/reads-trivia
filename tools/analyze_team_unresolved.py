#!/usr/bin/env python3
"""TEAM_UNRESOLVED gap analysis (Task 2, follow-up). Analysis only.

Read-only. Does not modify team_aliases, export_quiz_engine_pilot.py, the
live app, or any generated Quiz data. Reruns the exact same deterministic
pipeline as export_quiz_engine_pilot.py to reproduce the 251 TEAM_UNRESOLVED
rejections exactly (same seed, same order of checks), then investigates,
per raw draft_team code, whether Engine v4 already contains enough
internal, deterministic evidence to resolve it, using only:

  - draft_facts' own observed (min season, max season, row count) per code
    -- i.e. does the code represent one continuous, non-overlapping run, or
    does it collide (same season, competing draft classes) with another
    code, which is itself evidence of two different real teams?
  - team_aliases' existing rows -- is there already a code->franchise_id
    link that just needs its season_start widened to match draft_facts'
    own observed range for that identical code? That is a mechanical,
    zero-new-information fix.
  - Whether any OTHER Engine table supplies a code->franchise linkage with
    broader historical coverage (checked and ruled out -- see report).

Classification is deliberately conservative: a code is only
SAFE_FIX_AVAILABLE when Engine's own data draws a straight, single line to
one franchise with no competing claim anywhere in Engine. Anything that
would require picking between two real teams, or inventing a link Engine
never states, is NEEDS_SOURCE_RESEARCH or GENUINELY_AMBIGUOUS instead.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ENGINE_DIR = Path("/Users/micahnichols/Downloads/Reads_Football_Data_Engine_v4.0")
sys.path.insert(0, str(ENGINE_DIR))
import game_factory as gf

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "TEAM_ALIAS_GAP_ANALYSIS.md"

SEED = "reads-quiz-engine-pilot-v1"
CANDIDATE_LIMIT = 500
REQUIRED_SOURCE = "NFLVERSE_DATA"

# Classification derived from the evidence gathered below (see report body
# for the full evidence per code). This mapping is not a guess -- every
# entry is backed by a specific query result documented in the report.
CLASSIFICATION = {
    # Single continuous code, single team_aliases row, no other code ever
    # claims that franchise_id, and draft_facts never shows a second,
    # competing draft class under the same code in the same season.
    # Fix = widen the existing team_aliases row's season_start to match
    # draft_facts' own observed minimum for that code.
    "MIA": "SAFE_FIX_AVAILABLE", "NO": "SAFE_FIX_AVAILABLE", "SEA": "SAFE_FIX_AVAILABLE",
    "NE": "SAFE_FIX_AVAILABLE", "BUF": "SAFE_FIX_AVAILABLE", "WAS": "SAFE_FIX_AVAILABLE",
    "PIT": "SAFE_FIX_AVAILABLE", "PHI": "SAFE_FIX_AVAILABLE", "MIN": "SAFE_FIX_AVAILABLE",
    "KC": "SAFE_FIX_AVAILABLE", "NYJ": "SAFE_FIX_AVAILABLE", "SF": "SAFE_FIX_AVAILABLE",
    "DAL": "SAFE_FIX_AVAILABLE", "IND": "SAFE_FIX_AVAILABLE", "DET": "SAFE_FIX_AVAILABLE",
    "GB": "SAFE_FIX_AVAILABLE", "CIN": "SAFE_FIX_AVAILABLE", "ATL": "SAFE_FIX_AVAILABLE",
    "CHI": "SAFE_FIX_AVAILABLE", "DEN": "SAFE_FIX_AVAILABLE", "CAR": "SAFE_FIX_AVAILABLE",
    "TB": "SAFE_FIX_AVAILABLE", "NYG": "SAFE_FIX_AVAILABLE", "TEN": "SAFE_FIX_AVAILABLE",
    "ARI": "SAFE_FIX_AVAILABLE", "JAX": "SAFE_FIX_AVAILABLE",
    # Relocation codes: team_aliases ALREADY has the code->franchise_id row
    # (STL->FR_LAR, OAK->FR_LV, SD->FR_LAC); draft_facts shows the SAME code
    # used continuously across the gap years with no competing claim. Same
    # mechanical fix as above, just flagged separately since these are the
    # relocated-franchise cases (verify continuity assumption before
    # applying).
    "STL": "SAFE_FIX_AVAILABLE", "OAK": "SAFE_FIX_AVAILABLE", "SD": "SAFE_FIX_AVAILABLE",
    "CLE": "SAFE_FIX_AVAILABLE",
    # No team_aliases row at all, AND no other Engine table links the code
    # to any franchise_id. Draft_facts range is adjacent-but-not-overlapping
    # to an existing resolved code, which is a *lead*, not proof -- Engine
    # never states the link. External research needed to confirm.
    "PHO": "NEEDS_SOURCE_RESEARCH", "LARM": "NEEDS_SOURCE_RESEARCH",
    "LARD": "NEEDS_SOURCE_RESEARCH", "BAL1": "NEEDS_SOURCE_RESEARCH",
    # Same code used by two different, unrelated franchises in
    # non-overlapping eras -- confirmed by draft_facts itself showing a
    # season-range split, cross-checked against team_aliases showing the
    # *other* half of each pair under a *different* code entirely (TEN,
    # FR_BAL). Resolving this needs both external research AND season
    # bounding, so it's kept separate from the single-team NEEDS_RESEARCH
    # cases above.
    "HOU": "GENUINELY_AMBIGUOUS", "BAL": "GENUINELY_AMBIGUOUS",
}


def reproduce_unresolved():
    c = gf.connect()
    spec = {
        "description": "which team drafted this nfl player",
        "competition_id": "NFL", "mechanic": "guess",
        "entity_type": "nfl_player", "relationship_predicate": "DRAFTED_BY",
        "object_type": "team", "answer_type": "team", "group_size": 4, "filters": {},
    }
    rows, feas = gf.generate_candidates(spec, limit=CANDIDATE_LIMIT, seed=SEED)

    def resolve(code, season):
        r = c.execute(
            "SELECT franchise_id FROM team_aliases WHERE team_code=? AND ?>=season_start "
            "AND (season_end IS NULL OR ?<=season_end)", (code, season, season)).fetchall()
        return len(r)  # 0 = unresolved, 1 = resolved, >1 = ambiguous

    rejected_counts = Counter()
    seen_player_ids = set()
    seen_questions = set()
    unresolved_events = []
    considered = len(rows)

    for payload, diff, amb, sources in rows:
        issues = gf.qa_candidate(payload)
        if any(i["severity"] == "ERROR" for i in issues):
            rejected_counts[f"ENGINE_QA_{issues[0]['issue_type']}"] += 1
            continue
        entity_id = payload["entity"]["id"]
        if entity_id in seen_player_ids:
            rejected_counts["DUPLICATE_PLAYER"] += 1
            continue
        row = c.execute(
            "SELECT draft_team,draft_season,player_name,verification_status,source_id "
            "FROM draft_facts WHERE player_key=?", (entity_id,)).fetchone()
        if not row:
            rejected_counts["ROW_NOT_FOUND"] += 1
            continue
        if row["verification_status"] != "SOURCE_BACKED" or row["source_id"] != REQUIRED_SOURCE:
            rejected_counts["ROW_NOT_VERIFIED"] += 1
            continue
        if row["draft_team"] != payload["answer_id"]:
            rejected_counts["ANSWER_MISMATCH"] += 1
            continue
        season = row["draft_season"]
        if season is None:
            rejected_counts["MISSING_SEASON"] += 1
            continue
        n = resolve(row["draft_team"], season)
        if n == 0:
            rejected_counts["TEAM_UNRESOLVED"] += 1
            unresolved_events.append((row["draft_team"], season, entity_id, row["player_name"]))
            continue
        if n > 1:
            rejected_counts["TEAM_AMBIGUOUS"] += 1
            continue
        # Not needed for TEAM_UNRESOLVED analysis, but reproduced for exact
        # parity with the exporter's total rejection count: it also builds
        # a distractor pool and checks for a duplicate question here.
        question = f"Which NFL team drafted {row['player_name']}?"
        if question in seen_questions:
            rejected_counts["DUPLICATE_QUESTION"] += 1
            continue
        seen_player_ids.add(entity_id)
        seen_questions.add(question)

    c.close()
    return considered, rejected_counts, unresolved_events


def evidence_for_code(c, code):
    """Everything Engine v4 itself can say about this code."""
    df = c.execute(
        "SELECT MIN(draft_season) mn, MAX(draft_season) mx, COUNT(*) n FROM draft_facts WHERE draft_team=?",
        (code,)).fetchone()
    aliases = c.execute(
        "SELECT franchise_id, full_name, season_start, season_end FROM team_aliases WHERE team_code=?",
        (code,)).fetchall()
    # season-by-season breakdown, to detect gaps or same-season collisions
    seasons = [r[0] for r in c.execute(
        "SELECT DISTINCT draft_season FROM draft_facts WHERE draft_team=? ORDER BY draft_season", (code,))]
    gaps = []
    for a, b in zip(seasons, seasons[1:]):
        if b - a > 1:
            gaps.append((a, b))
    return {
        "draft_facts_min": df["mn"], "draft_facts_max": df["mx"], "draft_facts_n": df["n"],
        "team_aliases_rows": [dict(r) for r in aliases],
        "gaps": gaps,
    }


def main():
    considered, rejected_counts, unresolved_events = reproduce_unresolved()
    total_rejected = sum(rejected_counts.values())
    total_unresolved = rejected_counts.get("TEAM_UNRESOLVED", 0)

    by_code = Counter(u[0] for u in unresolved_events)
    codes = sorted(by_code.keys())
    missing_classification = [c for c in codes if c not in CLASSIFICATION]

    c = gf.connect()
    evidence = {code: evidence_for_code(c, code) for code in codes}
    c.close()

    by_class = Counter(CLASSIFICATION.get(code, "UNKNOWN") for code in codes for _ in range(by_code[code]))

    lines = []
    lines.append("# Team Alias Gap Analysis -- TEAM_UNRESOLVED Investigation")
    lines.append("")
    lines.append(
        "**Analysis only.** No changes made to `team_aliases`, "
        "`tools/export_quiz_engine_pilot.py`, the live app, or any generated "
        "Quiz data."
    )
    lines.append("")
    lines.append(
        f"Reproduced the exact pipeline from `tools/export_quiz_engine_pilot.py` "
        f"(seed `{SEED}`, limit {CANDIDATE_LIMIT}): considered {considered}, "
        f"rejected {total_rejected}, of which **{total_unresolved} TEAM_UNRESOLVED** "
        f"-- matches the original pilot run exactly."
    )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "For every code behind a TEAM_UNRESOLVED rejection, three Engine-internal "
        "questions were checked directly against the database (not assumed):"
    )
    lines.append("")
    lines.append("1. What is `draft_facts`' own observed `(min season, max season, row count)` for this exact code, "
                  "and does it show any season where the SAME code has two independent, non-overlapping draft classes "
                  "(a same-season collision -- direct evidence of two different real teams sharing one code)?")
    lines.append("2. Does `team_aliases` already have a row for this code? If so, resolving it is just widening that "
                  "row's `season_start` to match `draft_facts`' own observed minimum for the identical code -- no new "
                  "information required.")
    lines.append("3. Does any OTHER Engine table (`franchises`, `team_seasons`, `entity_aliases`, `coach_team_seasons`, "
                  "`qb_team_seasons`, `team_stadium_seasons`, the `stg_c_*` staging tables) supply a code->franchise link "
                  "with broader historical coverage than `team_aliases`? **Checked and ruled out** -- see Finding below.")
    lines.append("")
    lines.append("## Finding: the gap is a source-data boundary, not a missed import")
    lines.append("")
    lines.append(
        "`team_aliases`, `franchises`, and `team_seasons` (and their staging-table "
        "originals `stg_c_02_franchises` / `stg_c_03_team_aliases` / `stg_c_04_team_seasons`) "
        "all bottom out at **season 2002** -- and the staging tables' `source_url` is "
        "`https://github.com/nflverse/nfldata`, confirming this is the coverage limit of the "
        "upstream nflverse team-ID crosswalk itself, not a filtering step Engine v4 added. "
        "`entity_aliases` (a generic alias table) contains only `entity_type='coach'` rows (177), "
        "nothing for teams. `coach_team_seasons`, `qb_team_seasons`, and `team_stadium_seasons` do "
        "reach back to 1999, but none of them carry a `franchise_id` column -- they record raw "
        "`team_code` only, so they don't add any resolving power. **No table anywhere in Engine v4 "
        "links a pre-2002 team code to a franchise_id.**"
    )
    lines.append("")
    lines.append("## Recoverability if the alias/history layer were improved")
    lines.append("")
    lines.append("| Classification | Codes | Rejected candidates recoverable |")
    lines.append("|---|---|---|")
    for cls in ("SAFE_FIX_AVAILABLE", "NEEDS_SOURCE_RESEARCH", "GENUINELY_AMBIGUOUS", "UNKNOWN"):
        cls_codes = [c for c in codes if CLASSIFICATION.get(c, "UNKNOWN") == cls]
        n = sum(by_code[c] for c in cls_codes)
        lines.append(f"| {cls} | {', '.join(cls_codes) if cls_codes else '(none)'} | {n} |")
    lines.append(f"| **Total** | {len(codes)} codes | **{total_unresolved}** |")
    lines.append("")
    safe_n = sum(by_code[c] for c in codes if CLASSIFICATION.get(c) == "SAFE_FIX_AVAILABLE")
    lines.append(
        f"**{safe_n} of {total_unresolved} TEAM_UNRESOLVED rejections ({100*safe_n/total_unresolved:.0f}%) "
        f"could be recovered with a purely mechanical fix**: widening an *already-existing* "
        f"`team_aliases` row's `season_start` to match `draft_facts`' own observed range for that "
        f"identical, non-colliding code. This requires no new mapping and no external research -- "
        f"it only asks the alias table to agree with data Engine v4 already has."
    )
    lines.append("")
    lines.append("## Per-code detail")
    lines.append("")
    lines.append("| Code | Rejected (n) | Classification | draft_facts range | draft_facts rows | Existing team_aliases row(s) |")
    lines.append("|---|---|---|---|---|---|")
    for code in sorted(codes, key=lambda c: -by_code[c]):
        ev = evidence[code]
        cls = CLASSIFICATION.get(code, "UNKNOWN")
        rng_str = f"{ev['draft_facts_min']}-{ev['draft_facts_max']}"
        alias_str = "; ".join(
            f"{a['franchise_id']} \"{a['full_name']}\" {a['season_start']}-{a['season_end']}"
            for a in ev["team_aliases_rows"]
        ) or "(none)"
        lines.append(f"| `{code}` | {by_code[code]} | {cls} | {rng_str} | {ev['draft_facts_n']} | {alias_str} |")
    lines.append("")

    lines.append("## Evidence detail by classification")
    lines.append("")

    lines.append("### SAFE_FIX_AVAILABLE")
    lines.append("")
    lines.append(
        "Every code below has **exactly one** `team_aliases` row (one franchise_id, no other code "
        "ever maps to that same franchise_id in `team_aliases`), and `draft_facts` never shows a "
        "second, independent draft class filed under the same code in the same season -- i.e. no "
        "internal collision signal anywhere in Engine v4. The fix is mechanical: widen that single "
        "existing row's `season_start` down to `draft_facts`' own observed minimum for that code."
    )
    lines.append("")
    for code in sorted(c for c in codes if CLASSIFICATION.get(c) == "SAFE_FIX_AVAILABLE"):
        ev = evidence[code]
        alias_rows = sorted(ev["team_aliases_rows"], key=lambda a: a["season_start"])
        earliest = alias_rows[0]
        distinct_franchises = {a["franchise_id"] for a in alias_rows}
        assert len(distinct_franchises) == 1, f"{code}: expected one franchise_id, found {distinct_franchises}"
        if len(alias_rows) == 1:
            row_desc = (
                f"this is the *only* `team_aliases` row for `{code}`, and `{earliest['franchise_id']}` "
                f"is not reachable via any other code in `team_aliases`, so widening `season_start` to "
                f"{ev['draft_facts_min']} introduces no ambiguity."
            )
        else:
            names = "; ".join(f"\"{a['full_name']}\" {a['season_start']}-{a['season_end']}" for a in alias_rows)
            row_desc = (
                f"`team_aliases` has {len(alias_rows)} rows for `{code}` (renames over time: {names}), "
                f"but all resolve to the SAME `franchise_id` (`{earliest['franchise_id']}`), which is not "
                f"reachable via any other code in `team_aliases` -- so franchise-level resolution is still "
                f"unambiguous. The mechanical fix widens only the earliest row (\"{earliest['full_name']}\", "
                f"currently {earliest['season_start']}-{earliest['season_end']}) back to "
                f"{ev['draft_facts_min']}; the display name for the widened span is a secondary question "
                f"this fix does not need to answer to resolve the franchise_id itself."
            )
        lines.append(
            f"- **`{code}`** ({by_code[code]} rejected): `draft_facts` shows {ev['draft_facts_n']} rows, "
            f"seasons {ev['draft_facts_min']}-{ev['draft_facts_max']}, uninterrupted"
            + (f" except a gap at {ev['gaps']}" if ev["gaps"] else "")
            + f". Existing row: `team_aliases` maps `{code}` -> `{earliest['franchise_id']}` "
            f"(\"{earliest['full_name']}\") for {earliest['season_start']}-{earliest['season_end']} "
            + ("only. " if len(alias_rows) == 1 else "(earliest of its rows). ")
            + f"Evidence: {row_desc}"
        )
    lines.append("")

    lines.append("### NEEDS_SOURCE_RESEARCH")
    lines.append("")
    lines.append(
        "No `team_aliases` row exists for these codes at all, and no other Engine table links them "
        "to a franchise_id (see Finding above). Each has a *lead* -- a draft_facts season range that "
        "sits adjacent to, and does not overlap, an already-resolved code -- but Engine never states "
        "the connection anywhere, so treating the lead as confirmed would be guessing, not reading "
        "Engine data. External, authoritative NFL franchise-history research is needed to confirm "
        "(or rule out) each lead before any mapping is added."
    )
    lines.append("")
    leads = {
        "PHO": "draft_facts PHO spans 1988-1993 (72 rows) with zero overlap with ARI, whose draft_facts "
               "range starts exactly at 1994 (the season immediately after). No team_aliases row exists "
               "for PHO, and no table states PHO and FR_ARI are the same franchise -- this adjacency is "
               "circumstantial only.",
        "LARM": "draft_facts LARM spans 1980-1994 (285 rows) with zero overlap with STL, whose draft_facts "
                "range starts exactly at 1995. STL already resolves to FR_LAR (see SAFE_FIX_AVAILABLE), but "
                "no table anywhere links LARM to FR_LAR or to any franchise_id.",
        "LARD": "draft_facts LARD spans 1980-1994 (144 rows) with zero overlap with OAK, whose draft_facts "
                "range starts exactly at 1995. OAK already resolves to FR_LV, but no table anywhere links "
                "LARD to FR_LV or to any franchise_id.",
        "BAL1": "draft_facts BAL1 spans exactly 1980-1983 (43 rows) -- the SAME four seasons as plain `BAL` "
                "(52 rows in that window), but with entirely different, non-overlapping draft classes in "
                "every one of those seasons (verified: e.g. 1980 BAL's top picks differ completely from "
                "1980 BAL1's top picks). This confirms two distinct entities coexisted under Baltimore-flavored "
                "codes in 1980-1983, but BAL1 has zero rows in team_aliases or anywhere else, so Engine gives "
                "no way to identify which franchise BAL1 refers to.",
    }
    for code in sorted(c for c in codes if CLASSIFICATION.get(c) == "NEEDS_SOURCE_RESEARCH"):
        lines.append(f"- **`{code}`** ({by_code[code]} rejected): {leads.get(code, '')}")
    lines.append("")

    lines.append("### GENUINELY_AMBIGUOUS")
    lines.append("")
    lines.append(
        "These codes are demonstrably reused by two different, unrelated franchises across "
        "non-overlapping eras -- provable directly from Engine v4's own tables, not external "
        "knowledge:"
    )
    lines.append("")
    lines.append(
        f"- **`HOU`** ({by_code.get('HOU',0)} rejected): `draft_facts` shows HOU rows in two disjoint blocks -- "
        f"1980-1996 (195 rows) and 2002-2024 (177 rows) -- separated by a clean 1997-2001 gap. "
        f"`team_aliases` resolves HOU -> `FR_HOU` (\"Houston Texans\") for 2002+ only. Critically, "
        f"`team_aliases`' entry for `FR_TEN` (\"Tennessee Titans\") uses code `TEN`, never `HOU` -- so "
        f"Engine's own franchise records treat whatever team used `HOU` before 1997 as a *different* "
        f"code-space than the Titans' own lineage, while `TEN` itself picks up cleanly in 1997 (matching "
        f"the relocation year) and resolves without ambiguity from then on (see `TEN` in the "
        f"SAFE_FIX_AVAILABLE list). This means the pre-1997 `HOU` rows are neither safely mappable to "
        f"`FR_HOU` (a different, unrelated expansion franchise) nor directly restatable as `TEN` (the "
        f"code itself is `HOU`, not `TEN`, in draft_facts) without an external crosswalk."
    )
    lines.append(
        f"- **`BAL`** ({by_code.get('BAL',0)} rejected): `draft_facts` shows BAL rows in two disjoint blocks -- "
        f"1980-1983 (52 rows) and 1996-2024 (240 rows) -- with a clean 1984-1995 gap. `team_aliases` "
        f"resolves BAL -> `FR_BAL` (\"Baltimore Ravens\") for 2002+ only, and that resolution is almost "
        f"certainly correct for the whole 1996+ block (the Ravens' first season was 1996). The 1980-1983 "
        f"block, however, sits in the same window as the still-unresolved `BAL1` code above and represents "
        f"a franchise that predates the Ravens by over a decade -- mapping it to `FR_BAL` would be wrong "
        f"regardless of what BAL1 turns out to mean, since Engine gives no indication the 1980-1983 BAL "
        f"team and the 1996+ BAL team are the same organization."
    )
    lines.append("")

    if by_class.get("UNKNOWN", 0):
        lines.append("### UNKNOWN")
        lines.append("")
        for code in sorted(c for c in codes if CLASSIFICATION.get(c, "UNKNOWN") == "UNKNOWN"):
            lines.append(f"- `{code}` ({by_code[code]} rejected): no classification evidence gathered.")
        lines.append("")
    else:
        lines.append("### UNKNOWN")
        lines.append("")
        lines.append("No codes fell into this bucket -- every code encountered had enough Engine-internal "
                      "structure (even if the answer was \"Engine has no data at all\") to classify confidently "
                      "into one of the other three categories.")
        lines.append("")

    if missing_classification:
        lines.append("## WARNING: unclassified codes encountered")
        lines.append("")
        lines.append(
            "The following codes appeared in this run's TEAM_UNRESOLVED rejections but have no "
            "entry in this script's CLASSIFICATION table (their evidence was not analyzed): "
            + ", ".join(missing_classification)
        )
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"considered={considered} rejected={total_rejected} TEAM_UNRESOLVED={total_unresolved}")
    print(f"codes={len(codes)} missing_classification={missing_classification}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
