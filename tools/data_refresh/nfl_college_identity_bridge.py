"""Real, re-runnable, idempotent NFL<->CFB college identity bridge expansion.

--- WHY THIS EXISTS ---
`cfb_nfl_identity_bridge_certified` (2,542 rows, confidence 0.994-0.999) is
the certified NFL<->CFB college identity bridge every consumer of college
data (tools/quiz_export/adapters/lineup.py's `lineup_college_coverage()`,
Coach Connections) reads from. `nfl_refresh.py`'s own module docstring
already discloses, directly and honestly, that this table is NOT fed by any
re-runnable pipeline in this repo: all 2,542 rows share one identical
`promoted_at` timestamp, meaning they came from a one-time bulk promotion by
a process that no longer exists here (`identity_bridge_v16.py` writes to a
DIFFERENT table -- `cross_league_identity_bridge_v16`, 107 rows -- and
additionally crashes on real data via an uncaught IntegrityError, per that
same docstring). `run_nfl_refresh()` has logged this gap on every run as
`identity_bridge_status = "NOT_ATTEMPTED_NO_REUSABLE_BUILDER"` rather than
silently pretending it was handled.

This module is the real fix for that gap: a genuinely re-runnable,
idempotent expansion that finds NEW high-confidence NFL<->CFB matches on
every call (so a new season's rookies become eligible automatically, no
hand-editing required) and adds them to the SAME certified table every
consumer already trusts, without ever touching or re-deriving the existing
2,542 ESPN-athlete-ID-matched rows.

--- METHODOLOGY (real, disclosed, deliberately conservative) ---
For each NFL player who has actually appeared on a real roster
(`canonical_roster_seasons` -- not the broader `canonical_players` table,
which can include incomplete/placeholder rows) and is NOT already in the
certified bridge:
  1. Normalize their name the same way `identity_bridge_v16.py`'s own
     `norm()` already does (lowercase, strip punctuation/suffixes like
     Jr/Sr/II/III/IV) and look up CFB players in `canonical_cfb_players`
     sharing that normalized name.
  2. If MORE THAN ONE CFB player shares that normalized name, the match is
     genuinely ambiguous -- skipped, never forced (matches the mission's own
     "Ambiguous mappings must remain unresolved" requirement; real, measured
     count reported in the return dict, never silently dropped).
  3. If EXACTLY ONE CFB player shares that name, check chronology: their
     last CFB roster season (`cfb_roster_seasons_real`) must precede the
     NFL player's own first NFL roster season by no more than
     CHRONOLOGY_MAX_GAP_YEARS (the same 0-5-year window
     `identity_bridge_v16.py` already uses for its own chronology check --
     reused, not invented). A player whose real college career predates
     the CFB dataset's own 2004 coverage start will correctly find zero
     candidates here and remain unresolved -- a genuine, disclosed data
     ceiling (see the real coverage audit for this pass's exact numbers),
     not a bug in this matching logic.
  4. Promoted rows get their OWN confidence tier
     (`MODERATE_CONFIDENCE_NAME_CHRONOLOGY_MATCHED`, confidence 0.85) --
     deliberately distinct from and lower than the existing
     HIGH_CONFIDENCE_MULTI_SEASON_POSITION_CORROBORATED tier (which requires
     an exact ESPN athlete ID match, a much stronger signal this pass does
     not have). Any consumer that cares about confidence tier can filter
     accordingly; `lineup_college_coverage()` treats both as certified today
     because unique-name-plus-plausible-chronology is still a real,
     conservative bar -- never a blind name join (ambiguous names are
     explicitly excluded, per point 2).

Idempotent by construction: `bridge_id` is deterministically derived from
(cfb_player_id, nfl_player_key), so re-running this against unchanged
inputs regenerates the identical bridge_id and `INSERT OR IGNORE` makes it
a true no-op. Only genuinely NEW (nfl_player_key not yet certified)
candidates are ever considered -- existing certified rows (from this module
or the original bulk promotion) are never re-evaluated, overwritten, or
removed.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone

MATCH_RULE = "UNIQUE_NORMALIZED_NAME_PLUS_NFL_CHRONOLOGY"
CONFIDENCE_TIER = "MODERATE_CONFIDENCE_NAME_CHRONOLOGY_MATCHED"
CONFIDENCE = 0.85
SOURCE_BRIDGE_TABLE = "reads_college_identity_expansion_v1"
# Same window identity_bridge_v16.py's own chronology_ok check already uses
# (latest CFB season <= draft/first-NFL-season <= latest+5) -- reused, not
# invented.
CHRONOLOGY_MAX_GAP_YEARS = 5


def _norm(s: str | None) -> str:
    s = (s or "").lower().replace("’", "'").replace(".", "").replace("'", "")
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def expand_identity_bridge(c) -> dict:
    """Never raises for ordinary data-shape issues -- this is an enrichment
    step, not a critical-path import; a caller (nfl_refresh.py) wraps this
    in its own try/except regardless so a bug here can never fail or
    restore-from-backup an otherwise-successful roster refresh."""
    already = {
        r["nfl_player_key"] for r in c.execute("SELECT nfl_player_key FROM cfb_nfl_identity_bridge_certified")
    }

    nfl_rows = c.execute(
        "SELECT crs.player_id, cp.display_name, MIN(crs.season) AS first_season, "
        "       (SELECT crs2.position FROM canonical_roster_seasons crs2 "
        "        WHERE crs2.player_id = crs.player_id ORDER BY crs2.season DESC LIMIT 1) AS position "
        "FROM canonical_roster_seasons crs JOIN canonical_players cp ON cp.player_id = crs.player_id "
        "GROUP BY crs.player_id, cp.display_name"
    ).fetchall()

    cfb_by_norm: dict[str, list[str]] = defaultdict(list)
    for r in c.execute("SELECT cfb_player_id, display_name FROM canonical_cfb_players"):
        cfb_by_norm[_norm(r["display_name"])].append(r["cfb_player_id"])

    cfb_last_season = {
        r["cfb_player_id"]: r["last"]
        for r in c.execute("SELECT cfb_player_id, MAX(season) AS last FROM cfb_roster_seasons_real GROUP BY cfb_player_id")
    }

    cfb_schools: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for r in c.execute(
        "SELECT crs.cfb_player_id, crs.school_id, s.school_name, MAX(crs.season) AS last_at_school "
        "FROM cfb_roster_seasons_real crs JOIN schools s ON s.school_id = crs.school_id "
        "GROUP BY crs.cfb_player_id, crs.school_id, s.school_name"
    ):
        cfb_schools[r["cfb_player_id"]].append((r["school_id"], r["school_name"], r["last_at_school"]))

    promoted = []
    skipped_ambiguous_name = 0
    skipped_chronology = 0
    for r in nfl_rows:
        pid = r["player_id"]
        if pid in already:
            continue
        candidates = cfb_by_norm.get(_norm(r["display_name"]), [])
        if len(candidates) != 1:
            if len(candidates) > 1:
                skipped_ambiguous_name += 1
            continue
        cfb_id = candidates[0]
        last = cfb_last_season.get(cfb_id)
        first_season = r["first_season"]
        if last is None or first_season is None:
            continue
        if not (last <= first_season <= last + CHRONOLOGY_MAX_GAP_YEARS):
            skipped_chronology += 1
            continue
        schools = cfb_schools.get(cfb_id)
        if not schools:
            continue
        school_id, school_name, _ = max(schools, key=lambda x: x[2])  # most recent school attended
        promoted.append((pid, r["display_name"], r["position"], cfb_id, school_id, school_name, first_season, last))

    now = datetime.now(timezone.utc).isoformat()
    for pid, name, position, cfb_id, school_id, school_name, first_season, last in promoted:
        bridge_id = "BRIDGE_EXP1:" + hashlib.sha1(f"{cfb_id}|{pid}".encode()).hexdigest()[:20]
        evidence = json.dumps({
            "match_rule": MATCH_RULE, "cfb_last_year": last, "nfl_first_season": first_season,
            "school_id": school_id, "chronology_gap_years": first_season - last,
        }, sort_keys=True)
        c.execute(
            "INSERT OR IGNORE INTO cfb_nfl_identity_bridge_certified "
            "(bridge_id, cfb_player_id, nfl_player_key, player_name, school_id, school_name, "
            "nfl_draft_year, nfl_draft_team, nfl_position, confidence, confidence_tier, evidence_json, "
            "source_bridge_table, promoted_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (bridge_id, cfb_id, pid, name, school_id, school_name, None, None, position,
             CONFIDENCE, CONFIDENCE_TIER, evidence, SOURCE_BRIDGE_TABLE, now),
        )
    c.commit()

    return {
        "status": "OK",
        "nfl_players_considered": len(nfl_rows),
        "already_certified_before": len(already),
        "newly_promoted": len(promoted),
        "skipped_ambiguous_name": skipped_ambiguous_name,
        "skipped_chronology_mismatch": skipped_chronology,
        "total_certified_after": len(already) + len(promoted),
        "match_rule": MATCH_RULE,
        "confidence_tier": CONFIDENCE_TIER,
    }
