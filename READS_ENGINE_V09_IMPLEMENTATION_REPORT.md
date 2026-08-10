# Reads Football Engine v4.0 -- Claude Code Implementation v0.9 Report

Scope: close the next major football-truth gaps (Hall of Fame, All-Pro, Pro
Bowl, and an honest attempt at MVP/SB MVP/ROTY) without breaking the v0.8
baseline, without touching the frontend, and without fabricating anything a
real, checkable source doesn't support.

Everything below is either a command actually run with its actual output,
or a fact read directly from the live database. Nothing is estimated.

---

## Git

- **v0.8 checkpoint commit**: `2c72401` ("Reads engine implementation v0.8:
  extend NFL roster coverage and Grid draft support"), committed at the
  start of this phase after confirming 81/81 green, FK-clean, and the
  changes belonged to the completed v0.8 work (`gateway/services/grid.py`,
  `gateway/tests/test_grid.py`, `tools/quiz_export/safety.py`,
  `tools/director_v04/player_from_clues.py`, `tools/director_v02/logs/audit_log.jsonl`
  [benign, appended by running the test suite], plus the new v0.8 report and
  import script).
- **v0.9 working tree**: uncommitted at the time of this report, per the
  explicit instruction not to auto-commit. See "Files changed" below.

---

## Baseline (start of this phase)

- 81/81 gateway tests passing.
- `Reads_v4_Database.sqlite`: 1,683,808,256 bytes.
- Roster coverage: 2006-2026. Draft coverage: 1980-2024.
- Grid: 13/21 stat criteria engine-backed.

Rule Zero re-verified before any new code: 81/81 green, DB FK check 0
errors, `quick_check` ok, `/v1/graph/search`/`/v1/graph/path`/`/v1/six-degrees`
live-checked via `TestClient`, `roster_coverage`/`draft_coverage` confirmed
unchanged, `app.js`/`data/grid.js`/`index.html`/`sw.js` mtimes confirmed
pre-dating this phase.

---

## Part 1 audit -- existing accolade/award truth (before importing anything)

v0.8 learned not to assume data is missing without checking. This phase's
audit was more thorough than v0.8's: checked **every column name across
all 225 tables** (not just table names) against ~25 keywords (hof, hall,
mvp, probowl, allpro, honor, award, achievement, roty, opoy, dpoy, comeback,
walter_payton, champion, ring, selection, honoree, all_star, ...), and
listed every real **view** in the database.

| Fact family | Exists? | Table/view | Notes |
|---|---|---|---|
| CFB awards (Heisman-era) | Yes | `cfb_awards`/`cfb_award_facts`/`v_award_winner_clues` | 91 rows, 1935+, `subject_type='cfb_player'` -- confirmed NOT NFL-level (view definition read directly: `SELECT ... FROM cfb_award_facts`) |
| CFB national champions | Yes | `cfb_champions`/`v_champion_clues` | College, not Super Bowl -- confirmed via view SQL and real sample rows (2024 Ohio State, 2025 Indiana) |
| NFL playoff seeding | Yes | `season_records`/`v_playoff_seed_clues` | Team-level, not player accolades |
| Gamification achievements | Yes | `achievements`/`user_achievements` | App XP/unlock system, unrelated to football facts |
| **NFL Hall of Fame** | **No table/column** | -- | Confirmed absent from all 225 tables and all real nflverse-data release tags (v0.8) -- **found instead by re-reading an already-approved source file's own columns** (see below) |
| **NFL MVP / Super Bowl MVP / OROY / DROY** | **No** | -- | Confirmed absent from all 225 tables, all views, and every real nflverse-data release tag checked (both v0.8 and this phase, including `draft_picks`' full column list) |

**The real finding**: `draft_picks.csv` -- the same nflverse-data file
`draft_facts`/`nfl_players_draft` were already built from -- has real
`hof`, `allpro`, and `probowls` columns the original import never
extracted. Same lesson as v0.8's `draft_facts` discovery, one file over:
audit before importing, don't assume.

---

## Part 2/3 -- Grid semantics + source discovery

Re-read `data/grid.js`'s exact `GRID_CRITERIA` definitions for the 8
remaining criteria:

| criterion_id | frontend meaning | desired fact |
|---|---|---|
| `hof` | `p.hof` boolean | HOF membership, any time |
| `mvp` | `p.mvp` boolean | ever won NFL MVP |
| `sb_mvp` | `p.sbMVP` boolean | ever won Super Bowl MVP |
| `roty` | `p.roty` boolean | ever won O-ROY or D-ROY |
| `probowl_5plus` / `probowl_10plus` | `p.proBowls >= 5/10` | **career Pro Bowl count** -- Grid's own data model is already a career total, not a season list |
| `allpro_3plus` | `p.allPro >= 3` | **career First-Team All-Pro count** (label explicitly says "First-Team") |

This matters: Grid's own existing criterion for Pro Bowl/All-Pro is
already a career-count threshold, not a season-by-season check -- so a
career-count source (see below) is a **semantic match**, not a downgrade.

**Source discovery**: `nflverse-data`'s `draft_picks` release --
"Draft picks dating back to 1980, courtesy of Pro Football Reference"
(the release's own description). Already `source_id=NFLVERSE_DATA`,
already `approved_for_import=1` -- not a new source, a fuller read of one
already in use.

**Real semantic verification before trusting the columns** (checked
against public record, not assumed):
```
Randy Moss      allpro=4    (real, known First-Team All-Pro count)
J.J. Watt       allpro=5    (real, known First-Team All-Pro count)
Jerry Rice      allpro=10   (real, known First-Team All-Pro count)
Lawrence Taylor allpro=8    (real, known First-Team All-Pro count)
Anthony Munoz   hof=TRUE, allpro=9 (real Hall of Famer, real count)
```
Confirms `allpro` = First-Team specifically (not First+Second combined) --
an exact semantic match to Grid's "3+ First-Team All-Pro" label, not a
coincidence. `probowls` is a plain career selection count. `hof` is a real
boolean (102 TRUE rows in the file).

**MVP / Super Bowl MVP / ROTY**: genuinely not in this file (checked the
real header directly -- no `mvp` column despite the release's own
description text mentioning "MVP", which turned out to be imprecise/stale
wording, not a real column). No other already-approved source has them
either. **Not implemented this phase** -- see Remaining Gaps.

---

## Data imported

Source: `https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv`
sha256 `91f1ead0d531aec7e219e3f19756b3084d8ef6d8dbf37c8b4ec147dd3985c215`,
recorded into `source_releases` as `REL_NFLVERSE_DRAFT_PICKS_ACCOLADES_V09`.

New table: `player_accolades` (`accolade_id, player_id, accolade_type,
season, count_value, induction_year, source_id, verification_status,
notes`). `season`/`induction_year` are `NULL` throughout this import --
the source provides career totals, not per-season/induction-year data,
and neither was fabricated to fill the columns.

**Real identity check caught before writing**: 2 real duplicate
`pfr_player_id`s in the file (`JackBo00` = Bo Jackson, famously drafted
twice -- 1986 Tampa Bay, 1987 Raiders; `EricCr00` = Craig Erickson, also
drafted twice). Both verified to have **identical** hof/allpro/probowls
values across their duplicate rows before being safely aggregated -- the
import script asserts this agreement and would abort loudly on a
disagreement (the same class of check that caught v0.8's real Byron Young
collision).

**Real counts** (`import_accolades_v09.py --commit`):
```
HALL_OF_FAME: 49
ALL_PRO_FIRST_TEAM_CAREER_COUNT (>0): 349
PRO_BOWL_CAREER_COUNT (>0): 893
Total player_accolades rows: 1,291
```

**A real, honest coverage gap found and reported, not hidden**: the source
file has **102** real HOF rows, but only **49** could be linked. The other
53 are real Hall of Famers whose careers ended before 2006 (e.g. Jerry
Rice, retired 2004) -- `canonical_players` itself only has rows for
players with an actual 2006-2026 roster season (that's how it was built in
v0.7/v0.8), so there's no row for them to attach an accolade fact to at
all. Verified directly: `Jerry Rice` (`pfr_id=RiceJe00`) returns no row
from `canonical_players`; `Peyton Manning`/`Calvin Johnson`/`Charles
Woodson` (all active into the 2006+ window) do. This is a structural scope
boundary of `canonical_players`, not a bug in this import -- flagged as
the top v1.0 recommendation.

Additionally: 1,754 rows had no `pfr_player_id` at all (skipped, cannot
safely identify) and 4,866 distinct `pfr_player_id`s had no
`canonical_players` match (same 2006-2026 boundary, or players with a
`GSIS:`-only id from v0.8 who never had a PFR id to begin with).

---

## Grid coverage: 13/21 -> 17/21

`gateway/services/grid.py` now wires `hof`, `allpro_3plus`,
`probowl_5plus`, `probowl_10plus` to real `player_accolades` queries, all
classified `SUPPORTED_WITH_COVERAGE_LIMIT` (not plain `SUPPORTED`) for two
honestly-documented reasons: (1) the source only covers drafted players,
and (2) `canonical_players`' 2006-2026-only universe. `draft_undrafted`,
`mvp`, `sb_mvp`, `roty` remain `UNDERSTOOD_BUT_UNSUPPORTED` -- not forced.

| # | criterion | status |
|---|---|---|
| 1-8 | `pos_qb`...`pos_ol` | SUPPORTED |
| 9 | `multi_team` | SUPPORTED |
| 10 | `one_team` | SUPPORTED |
| 11 | `sb_champ` (derived) | SUPPORTED |
| 12 | `draft_r1` | SUPPORTED_WITH_COVERAGE_LIMIT |
| 13 | `draft_day2plus` | SUPPORTED_WITH_COVERAGE_LIMIT |
| 14 | `hof` | **SUPPORTED_WITH_COVERAGE_LIMIT (new, v0.9)** |
| 15 | `allpro_3plus` | **SUPPORTED_WITH_COVERAGE_LIMIT (new, v0.9)** |
| 16 | `probowl_5plus` | **SUPPORTED_WITH_COVERAGE_LIMIT (new, v0.9)** |
| 17 | `probowl_10plus` | **SUPPORTED_WITH_COVERAGE_LIMIT (new, v0.9)** |
| 18 | `draft_undrafted` | UNDERSTOOD_BUT_UNSUPPORTED |
| 19 | `mvp` | UNDERSTOOD_BUT_UNSUPPORTED |
| 20 | `sb_mvp` | UNDERSTOOD_BUT_UNSUPPORTED |
| 21 | `roty` | UNDERSTOOD_BUT_UNSUPPORTED |

**17/21, not forced to 21/21.** The remaining 4 stay unsupported because no
real, already-approved, safely-verifiable source exists for them --
reported honestly, per the spec's own final rule.

---

## Real-data verification (this phase, live HTTP via TestClient)

```
1. Hall of Famer:
   POST /v1/grid/validate {"row_id":"team_IND","col_id":"hof","player_name":"Peyton Manning"}
   -> {"valid": true, "node_id": "PFR:MannPe00", "points": 25}

2. MVP (unsupported):
   GET /v1/grid/intersection?row_id=team_IND&col_id=mvp
   -> {"error": {"code": "UNDERSTOOD_BUT_UNSUPPORTED", "message": "...no NFL MVP award data exists..."}}

3. Super Bowl MVP (unsupported):
   -> UNDERSTOOD_BUT_UNSUPPORTED, same pattern

4. ROTY (unsupported):
   -> UNDERSTOOD_BUT_UNSUPPORTED, same pattern

5. Pro Bowl 10+:
   POST /v1/grid/validate {"row_id":"team_IND","col_id":"probowl_10plus","player_name":"Peyton Manning"}
   -> {"valid": true, "points": 100}   (real 14 career Pro Bowls)

6. First-Team All-Pro 3+:
   -> {"valid": true, "points": 20}   (real 7 career First-Team All-Pro)

7. Newly supported criterion, full intersection:
   GET /v1/grid/intersection?row_id=team_KC&col_id=hof
   -> count: 5 -- Darrelle Revis, Jared Allen, Tony Gonzalez, Ty Law, Will Shields (all real KC-affiliated HOF)

8. Identity collision protection (regression check):
   POST /v1/grid/validate {"row_id":"team_MIN","col_id":"hof","player_name":"Adrian Peterson"}
   -> {"valid": false, "reason": "AMBIGUOUS", "candidates": [2 real distinct players]}

9. One remaining unsupported criterion:
   GET /v1/grid/intersection?row_id=team_KC&col_id=draft_undrafted
   -> UNDERSTOOD_BUT_UNSUPPORTED, real 54.5%-gap reason (unchanged from v0.8)

10. Full coverage matrix:
    roster_coverage: {"min_season": 2006, "max_season": 2026}
    draft_coverage: {"min_season": 1980, "max_season": 2024}
    accolade_coverage: {"player_count": 909}
    supported stat count: 17, unsupported count: 4
```

---

## Identity

- Automatic exact matches: 11,093 `canonical_players` rows have a real
  `pfr_id` usable as the join key into `draft_picks.csv`.
- Real duplicate-id cases resolved safely: 2 (Bo Jackson, Craig Erickson --
  both verified same-person, agreeing values, aggregated; would have
  aborted the import on disagreement).
- Unresolved (skipped, not guessed): 1,754 source rows with no
  `pfr_player_id`; 4,866 distinct `pfr_player_id`s with no
  `canonical_players` match.
- Existing collision protections re-verified green: Adrian Peterson
  (v0.7) and Byron Young (v0.8) tests both still pass; a new v0.9 test
  (`test_grid_accolade_identity_safety_adrian_peterson_still_blocked`)
  confirms the new accolade criteria don't bypass identity safety.

---

## Database

| | Before (v0.8 end) | After (v0.9) | Delta |
|---|---|---|---|
| File size | 1,683,808,256 bytes | 1,684,180,992 bytes | +372,736 bytes |
| `canonical_players` | 12,245 | 12,245 | 0 (no new players this phase) |
| `player_accolades` | 0 (table didn't exist) | 1,291 | +1,291 |
| `graph_nodes` | 95,464 | 95,464 | 0 |
| `graph_edges` | 1,477,179 | 1,477,179 | 0 |

**No new graph nodes/edges this phase, deliberately.** Accolade facts are
served from the new relational `player_accolades` table with an index on
`(player_id, accolade_type)`, not graph predicates -- matches the spec's
own Part 23 guidance ("SQL is still appropriate for direct fact
retrieval... do not use broad graph scans when an indexed relational
lookup answers the question"). Mirroring these into graph edges (e.g.
`PLAYER -> INDUCTED_INTO -> HOF`) is possible later if Six Degrees puzzle
generation ever wants to traverse through them -- not needed for Grid,
not built this phase.

---

## Testing

```
$ READS_ENGINE_DIR=.../Reads_Football_Data_Engine_v4.0 gateway/.venv/bin/python -m pytest gateway/tests/ -q
89 passed in ~20s
```
81 baseline + 8 new v0.9 tests (`test_grid_hof_real_match`,
`test_grid_hof_known_non_hof_player_fails`,
`test_grid_pro_bowl_10plus_real_match`,
`test_grid_pro_bowl_10plus_known_non_qualifier_fails`,
`test_grid_all_pro_3plus_real_match`,
`test_grid_accolade_criteria_ignore_season_like_draft_round`,
`test_grid_mvp_still_unsupported`,
`test_grid_accolade_identity_safety_adrian_peterson_still_blocked`).

**One real failure found and fixed during this phase**: an existing v0.8
test (`test_grid_unsupported_criterion_is_unavailable_not_guessed`) used
`hof` as its example of an unsupported criterion -- broke the moment `hof`
became genuinely supported. Fixed by switching the example to `mvp`
(still genuinely unsupported), not by weakening the assertion.

FK check: 0 errors. `quick_check`: ok.

---

## Frontend

Confirmed unchanged: `app.js` (2026-08-09), `data/grid.js` (2026-08-07),
`index.html`/`sw.js` (2026-08-09) -- all predate this phase (2026-08-10).
Zero frontend files touched.

---

## Files changed this phase (uncommitted)

- New: `Reads_Football_Data_Engine_v4.0/import_accolades_v09.py`,
  `READS_ENGINE_V09_IMPLEMENTATION_REPORT.md`.
- Modified: `gateway/services/grid.py` (accolade criteria, coverage
  matrix), `gateway/tests/test_grid.py` (8 new tests, 2 updated
  assertions), `tools/director_v02/logs/audit_log.jsonl` (benign, from
  running the test suite).
- Database (not tracked in git, per `.gitignore`):
  `Reads_Football_Data_Engine_v4.0/Reads_v4_Database.sqlite` now has the
  real `player_accolades` table. Backed up before this phase's write to
  `Reads_v4_Database.pre_v09_backup.sqlite` (scratch directory,
  sha256-verified identical to the pre-write live file).

---

## Remaining gaps (not hidden)

1. **`canonical_players`' 2006-2026-only universe is now the single
   biggest limiter on accolade coverage**, not the accolade source
   itself. 53 of 102 real Hall of Famers (52%) were skipped purely
   because their careers ended before 2006. This will keep suppressing
   real, well-known facts (MVP-caliber legends, multi-decade Hall of
   Famers) for as long as `canonical_players` stays roster-scoped.
2. **MVP, Super Bowl MVP, OROY, DROY**: genuinely no safe, already-approved
   source found this phase either. `draft_picks.csv`'s release
   description mentions "MVP" but the real file has no such column --
   checked directly, not assumed. Pro-Football-Reference itself (the
   likely real source) has scraping-restrictive terms of use; using it
   would need an explicit new-source governance decision, not a
   unilateral scrape.
3. **`allpro`/`probowls` are career totals, not season-by-season
   selections** -- Grid doesn't need the finer grain (confirmed via its
   own criterion semantics in Part 2), but any future "which season did
   Player X make the Pro Bowl" style game mode would need a different,
   richer source than this one.
4. **`draft_undrafted`**: unchanged from v0.8, still unsupported for the
   same real, honest reason (54.5% identity-match gap in `draft_facts`).
5. **No graph-edge mirroring** of the new accolade facts (deliberate, see
   Database section) -- Six Degrees can't currently route through HOF/
   All-Pro/Pro-Bowl relationships.

---

## Recommendation for Claude Code implementation v1.0

1. **Decide whether to expand `canonical_players`' universe beyond
   2006-2026.** `draft_picks.csv` itself covers 1980-2026 independent of
   roster-season data -- it could seed `canonical_players` rows for
   pre-2006 draftees directly (with no `canonical_roster_seasons`/team
   data, since `PLAYED_FOR` genuinely doesn't go back that far), which
   would unlock the other 53 real Hall of Famers for HOF-only criteria
   but leave them permanently ineligible for any `team_<CODE>` Grid cell
   (since Grid always requires both a row AND column match). This is a
   real architectural trade-off, not a bug fix -- needs an explicit
   decision before building it, the same way the v0.7 Grid
   content-pipeline-vs-live-API fork did.
2. **MVP/SB MVP/OROY/DROY**: get an explicit decision on an acceptable new
   source before writing any import code -- these are short, extremely
   well-documented lists (roughly one winner per season per award), so
   the risk is entirely in source licensing/governance, not in the data
   itself being hard to verify.
3. Everything else from v0.8's own v0.9 recommendation list (college/
   school crosswalk using the already-fetched `players.csv` data,
   `stats_player` release for `games`/`starts` backfill, one real
   game-mode preview through Game Factory) remains valid and untouched
   this phase -- still real, scoped, available work.

---

## Final note

Per the spec's own final rule: 17/21, not 21/21. `mvp`/`sb_mvp`/`roty`/
`draft_undrafted` are reported as genuinely unsupported, not guessed at or
partially faked. The four newly-supported criteria are marked
`SUPPORTED_WITH_COVERAGE_LIMIT`, not plain `SUPPORTED`, because that's
what's actually true about them. Accuracy first, identity safety second,
coverage third.
