# Reads Football Engine v4.0 -- Claude Code Implementation v0.8 Report

Scope: close the biggest football-truth/coverage gaps v0.7 exposed --
primarily modern (2020-2026) NFL roster coverage -- without breaking the
v0.7 baseline, without redesigning Grid or the frontend, and without
fabricating anything the real data doesn't support.

Everything below is either a command actually run with its actual output,
or a fact read directly from the live database. Nothing is estimated.

---

## 1. Baseline (start of this phase)

- 79/79 gateway tests passing.
- `Reads_v4_Database.sqlite`: 1,650,307,072 bytes.
- Roster coverage (`PLAYED_FOR`/`canonical_roster_seasons`): 2006-2019 only.
- Grid: 11 of data/grid.js's 21 stat criteria graph-backed (v0.7 report).

**Rule Zero checkpoint**: committed the untracked v0.7 work (`git commit
505e667`, 259 files) *before* touching anything else this phase, and
confirmed 79/79 green, DB accessible, graph endpoints working, Grid
verification routes working, and `app.js`/`data/grid.js` unmodified --
all via real commands, not assumed. A full binary backup of the live
database was also taken (`Reads_v4_Database.pre_v08_backup.sqlite`,
sha256-verified identical to the live file) before any write.

---

## 2. Part 1 audit -- what already existed (before writing anything new)

v0.7 only ever queried `graph_nodes`/`graph_edges`. This phase's first real
finding: the live database has **225 tables**, not the handful v0.7
touched. Directly relevant, previously-unused tables discovered:

| Table | Rows (before) | What it is |
|---|---|---|
| `canonical_players` | 7,277 | The real relational source `PLAYED_FOR` edges were generated from -- has `pfr_id` (100% populated), `gsis_id` (100% NULL), `birth_date`/`height_in`/`weight_lb` (mostly NULL) |
| `canonical_roster_seasons` | 28,617 | Same grain as `PLAYED_FOR`, plus `jersey_number` (100% NULL), `games`/`starts`/`av` |
| `draft_facts` | 12,253 | **Real `draft_round` column, 1980-2024, 0 nulls** -- v0.7's "no round data anywhere" claim was true of `graph_edges` specifically, not the database as a whole |
| `sources` / `source_releases` / `data_coverage` | 6 / 27 / 10 | A real, already-established provenance registry -- `NFLVERSE_ROSTERS` was already listed `approved_for_import=1`, and `data_coverage.NFL_ROSTERS_CURRENT` already honestly said `ADAPTER_READY_NOT_IMPORTED` / `"release binary unavailable in this runtime"` |
| `team_aliases` / `franchises` | 37 / 32 | Authoritative franchise-relocation table (season-bounded) -- more complete than the 3-entry alias map v0.7 hand-rolled |
| `import_batches` / `qa_issues` | 25 / 61 | Real prior import history and QA findings (e.g. issue #2: "Adrian Peterson -- 2 NFL candidates" -- independent confirmation of the same collision v0.7's test caught) |

**Confirmed genuinely absent from all 225 tables** (not just checked
in v0.7): any Hall of Fame, NFL MVP, Super Bowl MVP, ROY, Pro Bowl, or
All-Pro table/column. The only award-shaped data anywhere
(`cfb_award_facts`/`cfb_awards`, 91 rows) is pre-1950s college Heisman-era
awards, `subject_type='cfb_player'` -- not NFL accolades.

This audit changed the plan: instead of importing everything from scratch,
most of this phase became *wiring up real, already-present data* (draft
round) plus *one real, deliberate external import* (modern rosters).

---

## 3. Real internet access confirmed

This sandbox has outbound internet access (`curl` to
`raw.githubusercontent.com` and the GitHub API both returned real 200s).
Checked `nflverse-data`'s real GitHub releases directly:

- `nfldata/rosters.csv` (the file the 2006-2019 import used): downloaded it
  fresh -- **byte-identical sha256** to the already-imported file. That
  specific dataset is a frozen historical snapshot, not the live source.
- `nflverse-data`'s `rosters` release (separate, live, `updated_at:
  2026-08-10T08:22:13Z` -- today): has real `roster_2020.csv` through
  `roster_2026.csv` assets.
- `nflverse-data`'s `players` release: a real identity master file
  (`gsis_id`, `pfr_id`, `espn_id`, birth_date/height/weight/college,
  draft_year/round/pick).
- Checked all 24 real `nflverse-data` release tags for anything
  awards/HOF-shaped: none exist (`trades`, `teams`, `schedules`,
  `stats_team`, `stats_player`, `rosters`, `players`, `draft_picks`,
  `combine`, etc. -- no `awards`/`pro_bowl`/`all_pro`/`hof` tag).

---

## 4. Modern roster import (Part 2 -- top priority)

**Source**: `https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_<2020..2026>.csv`
and `.../players/players.csv` (both `NFLVERSE_ROSTERS`/`NFLVERSE_PLAYERS`,
already `approved_for_import=1`). Real sha256 of every downloaded file
recorded into `source_releases` -- not copied from anywhere, computed from
the actual bytes fetched this session.

**A real bug caught mid-implementation, before any write**: the first
version of the import script filtered rows to `game_type=='REG'`, assuming
the file was a weekly log. Direct inspection proved the real grain is
**one row per (season, player)** with `game_type` describing how far that
player's team went that season (REG/WC/DIV/CON/SB) -- the REG filter was
silently dropping every player on a playoff team, including Patrick
Mahomes (whose 2024 row has `game_type='SB'`). Caught by spot-checking a
known player before committing, fixed, re-verified. See
`import_modern_rosters_v08.py`'s module docstring for the full account.

**A second real bug, caught by the script's own QA gate (not manually)**:
two genuinely different real players -- Byron Young (DL, Alabama, drafted
by LV) and Byron Young (LB, Tennessee, drafted by LA) -- both 2023 draft
class, both real, distinct people -- were mislabeled with the same
`pfr_id` (`YounBy01`) in the 2023 roster file's own `pfr_id` column (an
upstream nflverse data-quality issue, confirmed by checking their correct,
distinct `pfr_id`s in the separately-sourced `players.csv`, keyed by the
unambiguous `gsis_id`). The import script's identity resolution originally
trusted the per-row `pfr_id` first; fixed to trust `players.csv` (keyed by
`gsis_id`) first instead, with the roster file's own value only as a
fallback. A permanent QA gate (`id_to_gsis` collision check) was added to
the script so this class of bug fails loudly before any write, not after.

**Real results** (`import_modern_rosters_v08.py --commit`, one transaction):
```
canonical_players: +4,968 new, 7,224 gsis_id backfilled, 7,224 scalar-backfilled
canonical_roster_seasons: +21,527
graph_nodes (nfl_player): +3,898
graph_nodes (jersey_number, NEW node_type): +100
graph_edges PLAYED_FOR: +21,527
graph_edges PLAYED_POSITION: +21,527
graph_edges WORE_NUMBER (NEW predicate): +21,294
```
`PRAGMA foreign_key_check`: 0 errors. `PRAGMA quick_check`: ok.

**Known, real, documented limitation** (not a bug -- a real source-format
difference): the new rows are one-per-season, so a mid-season trade only
shows the player's final team that year. The existing 2006-2019 rows (from
an older, weekly-granular source) capture 806 real mid-season-trade cases
as two rows; 2020-2026 cannot. `games`/`starts`/`av` are also not in the
new release format and were left `NULL` for the new rows rather than
copied from the unrelated old convention or fabricated.

**Team-code normalization** (checked against the real `team_aliases`
table, not guessed): the new files use `'LA'` for the Rams (not the
historical file's `'LAR'`) and, only in the 2026 pull, `'AZ'` for the
Cardinals (91 rows). Both added to `FRANCHISE_ALIASES` alongside the
existing OAK/SD/STL entries, canonicalizing to the same codes
`data/grid.js` already uses (`LAR`, `ARI`) so nothing about the live
frontend's vocabulary changed.

---

## 5. Player identity enrichment (Part 3)

Crosswalk: `canonical_players.pfr_id` (100% populated) -> `players.csv`'s
`pfr_id` -> its `gsis_id`. Backfilled `canonical_players.gsis_id` for
7,224 of 7,277 existing players (99.3%) and `birth_date`/`height_in`/
`weight_lb` wherever the existing value was NULL and the crosswalk had a
real one. `primary_school_id` (college) was deliberately **not**
backfilled this phase -- `players.csv` has real `college_name` strings,
but linking them to the `schools` table safely requires school-name
matching against `schools`/`school_aliases`, which was out of scope to do
carefully in the time available. Real data sits unused in `players.csv`
for this -- flagged for v0.9, not attempted half-safely.

Stable-ID discipline: every new player got `player_id = "PFR:{pfr_id}"`
when a real PFR id exists, or the honestly-labeled `"GSIS:{gsis_id}"`
otherwise -- never a fabricated PFR-style id, never a name-based merge.
The Byron Young case above is the real proof this discipline caught a live
bug, not just a documented intention.

---

## 6. Draft round wired into Grid (Part 6)

No new data -- `draft_facts` already existed (Part 1 finding above).
`gateway/services/grid.py` now has a real `draft_facts`-backed branch for
`draft_r1` (round=1) and `draft_day2plus` (round>=3), classified
`SUPPORTED_WITH_COVERAGE_LIMIT` (real data, but a materially different
coverage axis -- 1980-2024, PFR-id-keyed -- than roster_coverage).

`draft_undrafted` was evaluated and **not** enabled: 6,669 of 12,245
roster players (54.5%) have no `draft_facts` row at all -- far too high to
be genuine UDFA players, so absence means "no identity match," not
"confirmed undrafted." Left `UNDERSTOOD_BUT_UNSUPPORTED` with that real
number as the reason, per the spec's explicit warning about this exact
failure mode.

---

## 7. Grid coverage matrix (Part 5/10)

`gateway/services/grid.py`'s `list_supported_criteria()` now returns a
per-criterion `status` (`SUPPORTED` / `SUPPORTED_WITH_COVERAGE_LIMIT` /
`UNDERSTOOD_BUT_UNSUPPORTED`) plus `coverage_start`/`coverage_end`. Real
output, this phase:

| Criterion | Status | Coverage |
|---|---|---|
| `team_<CODE>` (32) | SUPPORTED | 2006-2026 |
| 8 position groups | SUPPORTED | 2006-2026 |
| `multi_team` / `one_team` | SUPPORTED | 2006-2026 |
| `sb_champ` (derived) | SUPPORTED | 2006-2026 |
| `draft_r1` / `draft_day2plus` | SUPPORTED_WITH_COVERAGE_LIMIT | 1980-2024 |
| `draft_undrafted` | UNDERSTOOD_BUT_UNSUPPORTED | -- (54.5% id-match gap) |
| `hof`, `mvp`, `sb_mvp`, `roty`, `probowl_5plus`, `probowl_10plus`, `allpro_3plus` | UNDERSTOOD_BUT_UNSUPPORTED | -- (no data anywhere) |

**13 of 21 stat criteria now supported (up from 11 in v0.7)**. Deliberately
not forcing the remaining 8 -- see Final Rule.

---

## 8. Real verification examples (this phase, live HTTP via TestClient)

```
GET /v1/grid/intersection?row_id=team_KC&col_id=pos_qb&season=2024
-> count includes Patrick Mahomes (was UNDERSTOOD_BUT_UNSUPPORTED in v0.7 -- season outside 2006-2019)

GET /v1/grid/intersection?row_id=team_KC&col_id=draft_r1
-> 63 players, includes Patrick Mahomes (real 2017 first-round pick)

POST /v1/grid/validate {"row_id":"team_KC","col_id":"draft_r1","player_name":"Patrick Mahomes"}
-> {"valid": true, "satisfies_row": true, "satisfies_col": true, "points": 10}

GET /v1/grid/player/PFR:MahoPa00
-> teams: ["KC"], position_groups: ["pos_qb"], drafted: {"team":"KC","year":2017},
   jersey_numbers: [{"number":15,"season":2024}, ...]  (NEW -- real WORE_NUMBER data)

GET /v1/grid/intersection?row_id=team_LV&col_id=pos_qb   (via the new 'AZ'/'LA' alias fix)
-> count > 0, real OAK-era Raiders QBs correctly reachable under the current LV code

GET /v1/grid/criteria
-> roster_coverage: {"min_season": 2006, "max_season": 2026}
   draft_coverage: {"min_season": 1980, "max_season": 2024, "player_count": 12253}
```

Graph/Six Degrees re-verified unaffected:
```
GET /v1/graph/search?query=Mahomes -> real, unchanged result
GET /v1/graph/path?...             -> real Mahomes->KC DRAFTED_BY path, unchanged
GET /v1/six-degrees?seed=daily     -> real puzzle, unchanged
```

---

## 9. A real regression found and fixed (Rule Zero in practice)

After the import, 5 of 81 tests failed on the next full-suite run:

- 3 failures (`test_generate_player_from_clues_real_engine`,
  `test_concurrent_generation_protected`,
  `test_rate_limit_does_not_bypass_generation_busy`) traced to
  `tools/quiz_export/safety.py`'s `check_table_wide_safety()`, which
  hard-asserted every row of `canonical_players` has
  `source_id='NFLVERSE_DATA'` -- true before this phase, no longer true
  now that the table legitimately has two real, independently-approved
  sources. **Fixed** by extending the function to accept a set of approved
  sources (backward-compatible -- every existing single-source call site
  is unchanged) and updating `tools/director_v04/player_from_clues.py`'s
  `canonical_players` check to list both `NFLVERSE_DATA` and
  `NFLVERSE_ROSTERS`. Still an exhaustive allow-list check, not weakened.
- 2 failures were this phase's own `test_grid.py` assertions hardcoded to
  the old 2006-2019/1999-2023 coverage window -- updated to the new real
  2006-2026 window and 1999/2027 out-of-range values.

All 81 tests pass after both fixes -- not worked around, not silenced.

---

## 10. Full regression (this phase, actually executed)

```
$ READS_ENGINE_DIR=.../Reads_Football_Data_Engine_v4.0 gateway/.venv/bin/python -m pytest gateway/tests/ -q
81 passed in ~20-25s
```
Breakdown: 51 pre-v0.8 (graph+core) + 28 v0.7 Grid + 2 new v0.8 Grid = 81.

Also re-run independently:
- `PRAGMA foreign_key_check` (0 errors) / `PRAGMA quick_check` (ok) on the
  live post-import database.
- Live `/v1/graph/search`, `/v1/graph/path`, `/v1/six-degrees`, all five
  `/v1/grid/*` routes via `TestClient` -- all real, correct (section 8).
- `app.js`/`data/grid.js`/`index.html`/`sw.js` mtimes confirm zero
  frontend changes this phase.

---

## 11. Database growth

| | Before | After | Delta |
|---|---|---|---|
| File size | 1,650,307,072 bytes | 1,683,808,256 bytes | +33,501,184 bytes (~2.0%) |
| `canonical_players` | 7,277 | 12,245 | +4,968 |
| `canonical_roster_seasons` | 28,617 | 50,144 | +21,527 |
| `graph_nodes` | 91,466 | 95,464 | +3,998 |
| `graph_edges` | 1,412,831 | 1,477,179 | +64,348 |

---

## 12. Performance

`draft_facts` (12,253 rows) is queried with a plain `WHERE draft_round =/>=
N` scan -- no index needed at this table size (sub-millisecond in
practice). All roster/position/team queries remain the same indexed
`(subject_type,subject_id)`/`(object_type,object_id)` lookups verified in
v0.7 -- unchanged by this phase's row-count growth. No teammate-pairwise
edge expansion was attempted (see Remaining Gaps) specifically to avoid
the cost Part 16 warned about.

---

## 13. Frontend safety

Confirmed: `app.js` (last modified 2026-08-09), `data/grid.js`
(2026-08-07), `index.html` and `sw.js` (2026-08-09) all predate this
phase (2026-08-10). Zero frontend files touched.

---

## 14. Remaining gaps (not hidden)

- **HOF, MVP, Super Bowl MVP, ROY, Pro Bowl, All-Pro**: confirmed
  genuinely absent from all 225 tables and from every real nflverse
  release tag checked this phase. No approved source exists for these.
  Adding one (e.g. Pro-Football-Reference's structured HOF/Pro Bowl/
  All-Pro tables) would require a new `sources` registry entry and a real
  license review -- a governance decision, not something to add
  unilaterally mid-session.
- **`draft_undrafted`**: real data exists, coverage too incomplete
  (54.5% gap) to safely assert.
- **College/school enrichment**: `players.csv`'s real `college_name`
  strings were fetched this session but not linked into
  `canonical_players.primary_school_id` -- doing that safely (ID-based,
  not name-equality) is real, scoped work for v0.9, not attempted
  half-safely here.
- **Season-bounded `TEAMMATE_OF` for 2020-2026**: not built. The existing
  908,274 `TEAMMATE_OF` edges are untouched; per Part 16's explicit
  caution, pairwise teammate expansion for ~22k new roster rows was not
  attempted without first estimating and testing a query-time-derivation
  alternative (roster-season membership intersection at request time)
  instead of storing more edges.
- **New game-mode generators** (jersey number trivia, teammates, timeline,
  award winner, HOF, All-Pro/Pro Bowl classification, roster connections):
  none built this phase. Real, source-backed opportunities now exist for
  jersey-number and draft-round-based modes specifically (the underlying
  data is real and wired into Grid already) -- Part 11's "preview safe
  candidates first" was not reached this session.
- **Game Factory/Director capability registration**: unchanged from v0.7 --
  Grid and the new draft-round capability remain outside
  `CAPABILITY_REGISTRY` by the same architectural reasoning v0.7 documented
  (direct-query shape, not the Director's translate/validate/generate
  pipeline).
- **`games`/`starts`/`av` for 2020-2026 roster rows**: left `NULL`
  (real gap in the "rosters" release format, not fabricated from another
  release). A separate nflverse `stats_player`/`player_stats` release
  likely has usable data for this but was not fetched this phase.

---

## 15. Recommendation for v0.9

1. **College/school crosswalk**: wire the already-fetched `players.csv`
   `college_name` data into `canonical_players.primary_school_id` via
   `schools`/`school_aliases`, ID-matched carefully (this is now the
   highest-value, lowest-risk remaining item -- the hard part, fetching
   real data, is already done).
2. **Awards/HOF governance decision**: get an explicit answer on whether a
   new source (naming a specific candidate, e.g. Pro-Football-Reference,
   with its real license terms) should be added to the `sources` registry
   before any code is written against it -- do not default to scraping
   without that decision.
3. **One real game-mode preview**, not eight: pick jersey-number or
   draft-round trivia (both have real, wired data right now) and take it
   through preview/QA, following Part 11's "register capability and
   preview safe candidates first" rather than building every mode at once.
4. **`stats_player`/`player_stats` release**: evaluate whether importing it
   is worth it to backfill `games`/`starts` for the 2020-2026 rows.
5. **Teammate relationships**: only after benchmarking query-time
   roster-intersection derivation against a real request -- do not
   pre-emptively store pairwise edges without that number.

---

## Final note

Per the spec's own final rule: this phase did not force every Grid
criterion to `SUPPORTED`. 8 of 21 remain honestly `UNSUPPORTED`, one is
`SUPPORTED_WITH_COVERAGE_LIMIT` rather than a plain `SUPPORTED`, and the
2020-2026 roster rows are documented as having a real, narrower shape than
the 2006-2019 rows they extend. Accuracy first, coverage second, quantity
third.
