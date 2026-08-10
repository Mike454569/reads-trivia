# Quiz Engine Pilot v2 -- Audit Report (v1 vs v2 Comparison)

Pilot v2 reruns the exact same deterministic exporter pipeline as Pilot v1 (`tools/export_quiz_engine_pilot_v2.py`, same seed `reads-quiz-engine-pilot-v1`, same `DRAFTED_BY`/`guess` spec, same production-safety gate, same per-candidate QA rules, same category/difficulty mappings), run once against the database *before* the 30 SAFE_FIX_AVAILABLE `team_aliases` corrections, and once *after*. No validation rule was loosened between runs -- the corrections are the only thing that changed. Output: `data/quiz-engine-pilot-v2.js` (100 questions). `data/quiz-engine-pilot.js` (Pilot v1, 50 questions) is untouched.

## Headline comparison

| Metric | Pilot v1 (pre-fix) | Pilot v2 (post-fix) |
|---|---|---|
| Candidates considered | 500 | 500 |
| TEAM_UNRESOLVED rejections | 251 | 54 |
| DUPLICATE_PLAYER rejections | 10 | 14 |
| DUPLICATE_QUESTION rejections | 1 | 1 |
| Total rejected | 262 | 69 |
| Total QA-passing candidates (accepted) | 238 | 431 |
| Total unique exportable candidates | 238 | 431 |
| Total exported | 50 | 100 |
| Category distribution | {'NFL Draft History': 50} | {'NFL Draft History': 100} |
| Difficulty distribution | {'Hard': 33, 'Medium': 17} | {'Hard': 69, 'Medium': 31} |
| Franchise coverage | 29/32 | 31/32 |
| Draft-year range | 2002-2024 | 1980-2024 |
| Unique players (exported) | 50 | 100 |
| Duplicate questions (exported) | 0 | 0 |
| Duplicate players (exported) | 0 | 0 |
| Duplicate IDs (exported) | 0 | 0 |
| Data-contract failures | 0 | 0 |

## Full v2 rejection breakdown

| Reason | Count |
|---|---|
| TEAM_UNRESOLVED | 54 |
| DUPLICATE_PLAYER | 14 |
| DUPLICATE_QUESTION | 1 |

All 54 remaining `TEAM_UNRESOLVED` rejections in v2 were verified to fall exclusively under the 6 still-blocked codes (`LARD`, `LARM`, `BAL1`, `PHO`, `HOU`, `BAL` -- NEEDS_SOURCE_RESEARCH or GENUINELY_AMBIGUOUS) with per-code counts identical to the pre-fix run (LARD 14, LARM 13, BAL1 13, PHO 6, HOU 5, BAL 3 = 54). No code outside the approved 30-code patch plan changed behavior.

## Database validation results (applied once, before this rerun)

- SQLite integrity check: **PASSED** (`PRAGMA integrity_check` = [['ok']])
- Foreign-key check: **PASSED** (0 violations)
- Alias collision check: **PASSED** (0 collisions)
- Duplicate alias-range check: **PASSED** (0 duplicates)
- `team_aliases` row count unchanged: 37 (widened existing rows only, no inserts/deletes)

## Recovery of the 197 previously-blocked SAFE_FIX_AVAILABLE candidates

`197` in `TEAM_ALIAS_GAP_ANALYSIS.md` counts *rejection events* within the 500-candidate v1 sample (the same accounting the exporter itself uses, which can count one player more than once if they were drawn into more than one generated candidate group before ever being accepted). Cross-checking v1's event-level number: TEAM_UNRESOLVED dropped from 251 to 54 -- a drop of 197, matching the patch plan's 197 exactly.

At the *distinct-player* level (deduplicating repeat draws), 193 unique players were blocked by a safe-fix code pre-fix. Re-running the identical pipeline post-fix:

- **193 / 193 (100%)** now pass every downstream QA and uniqueness rule (distractor pool, duplicate-options, duplicate-question) -- **zero** were recovered by the alias fix only to be lost to a different rule.
- **0** were recovered by the alias fix but rejected for a different reason.
- **48** of the recovered players landed in the exported 100-question set; the remaining 145 are present in the full 431-candidate accepted pool (available for a future, larger export) but fell after position 100 in generation order.

## Patch plan summary

- Codes proposed: 30
- Codes applied: 30 (all passed collision validation, 0 held)
- Codes blocked (untouched, per instruction): 6 -- LARD, LARM, BAL1, PHO, HOU, BAL

