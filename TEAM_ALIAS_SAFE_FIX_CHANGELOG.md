# Team Alias Safe-Fix Changelog

Applies the SAFE_FIX_AVAILABLE corrections identified in `TEAM_ALIAS_GAP_ANALYSIS.md` to the `team_aliases` table in `reads_football_v4.0.sqlite`. **Scope: 30 team codes only.** The 46 NEEDS_SOURCE_RESEARCH and 8 GENUINELY_AMBIGUOUS candidates (codes `LARD`, `LARM`, `BAL1`, `PHO`, `HOU`, `BAL`) were left untouched, as instructed.

## What changed

For each of the 30 codes, `team_aliases` already had exactly one code->franchise mapping, just scoped to 2002 onward (the coverage limit of the upstream nflverse source file). `draft_facts` shows the identical code used continuously, with no competing franchise claim, back to an earlier season. The fix widens that single existing row's `season_start` down to match `draft_facts`' own observed minimum for that code -- no new rows, no new franchise mappings, no renamed/deleted data.

## Before backing up or changing anything

- Full physical copy of the database taken and checksum-verified before any write: `Reads_Football_Data_Engine_v4.0/pre_safe_fix_backup_20260809/reads_football_v4.0.sqlite.pre_safe_fix_backup`
- Logical (row-level) backup of every affected `team_aliases` row: `tools/backups/team_aliases_backup_pre_safe_fix.json`
- Machine-readable patch plan for all 30 proposed changes: `tools/team_alias_safe_fix_patch_plan.json`

## Collision validation (before applying)

- Proposed: **30**
- Passed validation: **30**
- Held (failed validation, not applied): **0**
  - (none)

Validation checked, for every proposed widened range: (1) no other franchise_id claims the same team_code during an overlapping season, (2) the same franchise_id isn't also reachable via a different code during an overlapping season, (3) whether draft_facts shows any gap inside the widened range (informational, not disqualifying on its own).

## Applied changes

**30 of 30 proposed changes were applied.** All 30 passed validation; none were held.

| Team code | Franchise ID | season_start before | season_start after | season_end (unchanged) |
|---|---|---|---|---|
| `ARI` | `FR_ARI` | 2002 | 1994 | 2026 |
| `ATL` | `FR_ATL` | 2002 | 1980 | 2026 |
| `BUF` | `FR_BUF` | 2002 | 1980 | 2026 |
| `CAR` | `FR_CAR` | 2002 | 1995 | 2026 |
| `CHI` | `FR_CHI` | 2002 | 1980 | 2026 |
| `CIN` | `FR_CIN` | 2002 | 1980 | 2026 |
| `CLE` | `FR_CLE` | 2002 | 1984 | 2026 |
| `DAL` | `FR_DAL` | 2002 | 1980 | 2026 |
| `DEN` | `FR_DEN` | 2002 | 1980 | 2026 |
| `DET` | `FR_DET` | 2002 | 1980 | 2026 |
| `GB` | `FR_GB` | 2002 | 1980 | 2026 |
| `IND` | `FR_IND` | 2002 | 1984 | 2026 |
| `JAX` | `FR_JAX` | 2002 | 1995 | 2026 |
| `KC` | `FR_KC` | 2002 | 1980 | 2026 |
| `MIA` | `FR_MIA` | 2002 | 1980 | 2026 |
| `MIN` | `FR_MIN` | 2002 | 1980 | 2026 |
| `NE` | `FR_NE` | 2002 | 1980 | 2026 |
| `NO` | `FR_NO` | 2002 | 1980 | 2026 |
| `NYG` | `FR_NYG` | 2002 | 1980 | 2026 |
| `NYJ` | `FR_NYJ` | 2002 | 1980 | 2026 |
| `OAK` | `FR_LV` | 2002 | 1995 | 2019 |
| `PHI` | `FR_PHI` | 2002 | 1980 | 2026 |
| `PIT` | `FR_PIT` | 2002 | 1980 | 2026 |
| `SD` | `FR_LAC` | 2002 | 1980 | 2016 |
| `SEA` | `FR_SEA` | 2002 | 1980 | 2026 |
| `SF` | `FR_SF` | 2002 | 1980 | 2026 |
| `STL` | `FR_LAR` | 2002 | 1995 | 2015 |
| `TB` | `FR_TB` | 2002 | 1980 | 2026 |
| `TEN` | `FR_TEN` | 2002 | 1997 | 2026 |
| `WAS` | `FR_WAS` | 2002 | 1980 | 2019 |

## Applied as a single transaction

All 30 UPDATE statements ran inside one transaction, each matched precisely on `(team_code, franchise_id, season_start)` so multi-row codes (`WAS`, which has 3 rows for its three name eras) only had their earliest row touched -- the later rename rows ("Washington Football Team" 2020-2021, "Washington Commanders" 2022-2026) are untouched. Each UPDATE was verified to affect exactly 1 row before commit; the transaction would have rolled back entirely on any mismatch. No rows were inserted or deleted -- `team_aliases` still has 37 rows.

## Post-write database validation

- SQLite integrity check: **PASSED**
- Foreign-key check: **PASSED** (0 violations)
- Alias collision check: **PASSED** (0 collisions)
- Duplicate alias-range check: **PASSED** (0 duplicates)

## Impact

Re-running the NFL Quiz exporter pipeline (same seed, same rules -- see `QUIZ_ENGINE_PILOT_V2_REPORT.md`) against the corrected database dropped `TEAM_UNRESOLVED` rejections from 251 to 54 within the same 500-candidate sample -- a drop of exactly 197, matching the patch plan. All 54 remaining rejections fall under the 6 still-blocked codes, with per-code counts unchanged from before the fix, confirming nothing outside the approved scope was affected.

## Not touched

- `LARD`, `LARM`, `BAL1`, `PHO` (NEEDS_SOURCE_RESEARCH)
- `HOU`, `BAL` (GENUINELY_AMBIGUOUS)
- Every other Engine v4 table
- The live Reads app (`app.js`, `index.html`, `data/quiz.js`, styles, routes, Firebase logic)
- Pilot v1 output (`data/quiz-engine-pilot.js`)

