# Reads Football Engine v4.0 -- Claude Code Implementation v1.1 Report

Primary objective: build source-backed historical NFL player-team career
truth (`PLAYED_FOR`), extending backward from the existing 2006-2026
roster window as far as a trustworthy source safely allows -- without
inferring team history from draft data, without merging identities by
name, and without forcing Grid to 21/21. Everything below is either a
command actually run with its actual output, or a fact read directly from
the live database.

---

## Git

- **v1.0 checkpoint**: `0bc1a88` -- confirmed via `git status` (clean) and
  `git log` before any new work began.
- **v1.1 working tree**: uncommitted, per instruction. `git status --short`:
  ```
   M gateway/tests/test_grid.py                              (7 new + 3 fixed tests)
   M tools/director_v02/logs/audit_log.jsonl                  (benign, test-run log)
  ?? Reads_Football_Data_Engine_v4.0/import_historical_played_for_v11.py  (new)
  ```
  (`READS_ENGINE_V11_IMPLEMENTATION_REPORT.md`, this file, also new.)

---

## Baseline (start of this phase)

93/93 tests. DB size 1,686,052,864 bytes. `canonical_players`: 17,113.
`graph_nodes`: 95,467. `graph_edges`: 1,479,122. HOF linked: 102. Grid:
17/21. `PFR:JohnTy00` QA issue: `OPEN` (unchanged, correctly left
quarantined this phase too -- no independent evidence resolved it).

---

## Part 1 audit -- existing historical team-career data

Keyword-swept every table for roster/career/team-season columns. Real
findings:

| Table | Rows | Real? |
|---|---|---|
| `roster_seasons`, `player_season_stats`, `staging_rosters` | 0 each | Empty, schema-ready-not-imported -- not usable |
| `qb_team_seasons` | 1,587 | Real, season-specific, back to **1999** -- but QB-only |
| `coach_team_seasons` | 936 | Real, back to 1999 -- coaches, not players |

None of these were a general (all-position) historical roster source.
Checked nflverse-data's real release catalog directly (not assumed):
`player_stats` (deprecated in favor of `stats_player`, confirmed via its
own release body text) and the current **`stats_player`** release --
real, live (last updated 2026-07-10), regular-season player stats back to
**1999**, keyed by real GSIS `player_id`. Selected this as the source.

---

## Part 2 -- `PLAYED_FOR` semantics, defined explicitly

The existing 2006-2026 rows come from roster **snapshot** files (a player
could appear with zero recorded stats). The new 1999-2005 rows come from
**stats_player**, which requires real recorded game stats to appear at
all -- verified directly: 0 of 11,987 real rows have `games<=0`. This is a
*stricter* participation standard, not a looser one, and matches the
spec's own stated preference ("actual player participation... not loose
association"). **Same `PLAYED_FOR` predicate used for both eras**
(normalized, not forked into a second predicate) so every existing
consumer (Grid, graph traversal, Player-From-Clues) keeps working
unchanged -- the evidentiary distinction is recorded in a dedicated
`source_releases` row and in code comments, not silently absorbed.

---

## Part 3 -- source record

```
Source: nflverse-data "stats_player" release
URL: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_<year>.csv
Files: 1999-2005 (7 files), real sha256 recorded per file in source_releases
Coverage: real regular-season stats, 1999-2005 (this phase's scope)
Identity: real GSIS player_id, crosswalked via players.csv (same file used in v0.8)
License: nflverse-data, code MIT (same family as every other NFLVERSE_DATA source already approved)
```

---

## Parts 4-7 -- import (season-aware, franchise-normalized, identity-safe, no draft inference)

**A real QA bug caught by my own validation gate, not the source**:
`canonical_team()`'s output ("LAR", this codebase's own canonical Rams
code since v0.7/v0.8) was checked against the *raw* `team_aliases` table
directly and failed -- "LAR" legitimately never appears there as a raw
code (only "LA"/"STL" do, both aliasing to it). Fixed by validating
against the *normalized* code set instead. A second real, small
normalization gap found and fixed: `'JAC'` (old Jaguars code) doesn't
appear in `team_aliases` at all (only `'JAX'`, 2002-2026) -- added as a
new alias, verified against the real table before use.

**Scope boundary, deliberate** (Part 29: do not overbuild): this import
does **not** mint new `canonical_players` rows. It only attaches
`PLAYED_FOR` facts to players already canonical from v0.7/v0.8/v1.0.

**Real counts** (`import_historical_played_for_v11.py --commit`):
```
Real rows read (1999-2005): 11,987
Skipped -- blank team (no team to attribute): 1
Skipped -- games<=0: 0
Skipped -- no gsis->pfr crosswalk: 145
Skipped -- pfr not in canonical_players (not minted -- out of v1.1 scope): 1,739
NEW canonical_roster_seasons rows: 10,102 (84.3% of real source rows linked)
NEW graph_edges PLAYED_FOR: 10,102
NEW graph_edges PLAYED_POSITION: 10,102
```
FK check: 0 errors after commit.

---

## Part 8 -- coverage metadata

`data_coverage.NFL_ROSTERS_HIST` updated: `coverage_start` 2006 -> 1999,
`completeness='HISTORICAL_TIERED_1999_2026'`, with an explicit note that
coverage is **not uniform** (1999-2005 only covers already-canonical
players; 2006-2026 is the fuller roster-snapshot window). A new row,
`NFL_PLAYED_FOR_HISTORICAL_1999_2005`, records the 1999-2005 tier
separately with its own real linkage rate (84.3%) rather than blending it
into a single misleading number.

---

## Part 9 -- Jerry Rice acceptance test (generic, no special-case code)

```
GET /v1/grid/player/PFR:RiceJe00
-> teams: ["LV", "SEA", "SF"]   -- his REAL career: SF (1985-2000), traded to
   the Raiders (2001-2003, appearing as both 'OAK' and 'LV' across different
   source files -- an upstream nflverse inconsistency, normalized identically
   by this codebase's existing alias map), Seattle (2004, his real final season)

GET /v1/grid/intersection?row_id=team_SF&col_id=hof
-> count: 8, Jerry Rice present (was 5, absent, before this phase)

POST /v1/grid/validate {"row_id":"team_SF","col_id":"allpro_3plus","player_name":"Jerry Rice"}
-> {"valid": true, "points": 10}
```
No `if player_id == "PFR:RiceJe00"` anywhere in this codebase -- verified
by construction: the import script and `gateway/services/grid.py` contain
no player-specific branches. Rice passes because the generic pipeline
(crosswalk -> canonical match -> franchise normalization -> PLAYED_FOR
insert) works, not because of a hard-coded exception.

---

## Part 10/11 -- Grid: criterion-family coverage vs. answer-universe coverage

**Criterion-family coverage: unchanged, 17/21.** No criterion's `status`
changed -- correct, per instruction ("do not automatically increase this
number merely because historical team coverage improves").

**Answer-universe coverage: real, substantial growth.** Measured directly
against the pre-v1.1 backup vs. the live post-import database (not
estimated):

| Metric | Before | After |
|---|---|---|
| `team_<CODE> x hof` cells with >=1 real answer (of 32 teams) | 28/32 | **32/32** |
| Total real player-team-HOF answers across all 32 cells | 86 | **154** (+79%) |
| `team_SF x hof` | 5 | 8 |
| `team_LV x hof` | 0 | 7 |
| `team_DAL x hof` | 3 | 8 |
| `team_MIN x hof` | 4 | 7 |
| `team_KC x hof` | 5 | 8 |

Every one of the 32 NFL teams now has at least one real, source-backed
Hall-of-Fame intersection -- 4 teams (including the Raiders/LV) had *zero*
valid answers before this phase.

---

## Part 12 -- historical teammates (not built, deliberately)

No pairwise `TEAMMATE_OF` edges were generated for the new 1999-2005 data.
Per the spec's own caution, same-team/same-season teammate relationships
should be derived via indexed relational queries at request time, not
pre-materialized, unless benchmarked and found necessary -- not attempted
this phase, correctly deferred (Part 29: do not overbuild).

---

## Part 15 -- graph / Six Degrees impact

| | Before | After | Delta |
|---|---|---|---|
| `graph_nodes` | 95,467 | 95,467 | **0** (no new nodes needed -- all matched players already had one, from v1.0's expansion or the original imports) |
| `graph_edges` | 1,479,122 | 1,499,326 | +20,204 |
| `PLAYED_FOR` edges | 50,144 | 60,246 | +10,102 |
| `PLAYED_FOR` season range | 2006-2026 | **1999-2026** | |

Real connectivity improvement, verified directly:
```
GET /v1/graph/path?start_type=nfl_player&start_id=PFR:RiceJe00&end_type=team&end_id=SEA
-> found: true, degrees: 1  (a direct edge that did not exist before this phase)
```
No graph explosion: canonical_players grew 40% in v1.0 with +3 nodes; this
phase added 10,102 real facts with **zero** new nodes.

---

## Part 16 -- MVP / Super Bowl MVP / ROTY (secondary, kept secondary)

Re-confirmed briefly, not derailing the primary objective: `stats_player`'s
real, full column list (checked directly, ~140 columns) has no
award/MVP-shaped field. No new source found this phase. Still genuinely
unsupported, unchanged from v0.9/v1.0. Does not block this phase's
completion, per instruction.

---

## Parts 19-21 -- import safety / idempotency (actually executed, not assumed)

Backed up the database before the first write
(`Reads_v4_Database.pre_v11_backup.sqlite`). **A real idempotency bug was
found and fixed**, same class as v1.0's own fix to the v0.9 accolade
script: the first real second-run attempt failed with an actual
`UNIQUE constraint failed: source_releases.release_id` error (not
simulated). Fixed by adding a `DELETE` before the `source_releases`
insert, matching the pattern `import_batches` already had. **Re-ran the
script a second time after the fix** and confirmed a stable, zero-new-rows
result:
```
Already present (idempotent no-op): 10,102
NEW canonical_roster_seasons rows to insert: 0
```
FK check clean after both runs.

---

## Real-data verification (this phase, live HTTP via TestClient)

```
1. Jerry Rice career teams: SF, LV, SEA (real, matches public record)
2. Another pre-2006 retiree: Marshall Faulk -> team LAR present (real Rams career, 1999-2005)
3. Historical multi-team player: Jerry Rice himself (SF -> LV -> SEA)
4. HOF + team: team_SF x hof, count 8, includes Rice
5. All-Pro + team: team_SF x allpro_3plus, Rice valid=true
6. Pro Bowl + team: team_SF x probowl_10plus, count 4
7. Draft-team vs played-for distinction (real, verified example -- not Bo
   Jackson, who turned out to have zero graph presence at all, a real
   pre-existing gap found while building this test): Hamza Abdullah,
   drafted by TB (2005), real roster teams DEN/CLE/ARI -- TB absent.
8. Historical Six Degrees path improvement: Rice->SEA now a real 1-degree path.
9. One unsupported/ambiguous case correctly still blocked: PFR:JohnTy00,
   qa_issues #62, still OPEN, untouched.
10. Season bounds: team_LV x hof x season=1999 correctly excludes Rice
    (his real Raiders stint started 2001); team_SF x hof x season=1999
    correctly includes him.
```

---

## Testing

```
$ READS_ENGINE_DIR=.../Reads_Football_Data_Engine_v4.0 gateway/.venv/bin/python -m pytest gateway/tests/ -q
100 passed in ~31s
```
93 baseline + 7 new v1.1 tests
(`test_grid_jerry_rice_acceptance_real_team_career`,
`test_grid_jerry_rice_now_completes_real_grid_cells`,
`test_grid_multi_team_historical_player_resolves_correctly`,
`test_grid_draft_team_does_not_imply_played_for`,
`test_grid_historical_season_bound_excludes_wrong_season`,
`test_grid_roster_coverage_now_starts_1999`,
`test_grid_modern_2006_2026_coverage_unaffected`).

**3 real failures found and fixed** (same pattern every phase in this
project has hit -- a genuine improvement breaking an old hardcoded
boundary, not a regression):
- `test_grid_criteria_real_coverage_and_split` -- hardcoded
  `min_season: 2006`, now correctly 1999.
- `test_grid_historical_player_has_canonical_identity` (v1.0's own test)
  -- asserted Jerry Rice has `teams: []`; exactly the limitation this
  phase fixed. Updated to assert his real teams instead.
- `test_grid_out_of_coverage_season_is_unsupported_not_a_silent_empty`
  -- used `season=1999` as an "out of range" example; 1999 is now in
  range. Updated to `1998`/`2027`.

Identity regressions all still green: Adrian Peterson (v0.7), Byron Young
(v0.8), `PFR:JohnTy00` still blocked (v1.0, unchanged this phase).

---

## Database

| | Before | After | Delta |
|---|---|---|---|
| File size | 1,686,052,864 bytes | 1,692,758,016 bytes | +6,705,152 bytes (+0.4%) |
| `canonical_roster_seasons` | 50,144 | 60,246 | +10,102 |
| `graph_nodes` | 95,467 | 95,467 | 0 |
| `graph_edges` | 1,479,122 | 1,499,326 | +20,204 |
| `PLAYED_FOR` edges | 50,144 | 60,246 | +10,102 |

FK check: 0 errors. `quick_check`: ok. Idempotency: verified by actually
re-running the importer (see above).

---

## Frontend

Confirmed unchanged: `app.js` (2026-08-09), `data/grid.js` (2026-08-07),
`index.html`/`sw.js` (2026-08-09) -- all predate this phase (2026-08-10).
**Zero frontend files touched.**

---

## v1.2 readiness: what the frontend will need (Part 30)

Real, current frontend mode list (`app.js`'s `LEAGUE_MODES`, read directly
this phase, not from memory): NFL -- Quiz, Grid, Blitz, Speed, Silhouette,
IQ Test, "17-0" (Legends), Higher or Lower; CFB -- Quiz, Grid, Blitz,
Speed, IQ Test, "12-0" (Legends); plus Daily Challenge and X's & Os
(standalone, outside `LEAGUE_MODES`). **All of these currently read only
from static `data/*.js` files -- confirmed zero live Gateway calls from
any frontend mode**, unchanged since the Gateway's content-pipeline model
was established in v0.7.

Existing Gateway surface: `/v1/health`, `/v1/ready`, `/v1/capabilities`,
`/v1/games/preview`, `/v1/games/generate`, `/v1/games/{package_id}`,
`/v1/graph/search`, `/v1/graph/path`, `/v1/six-degrees`, `/v1/grid/*` (5
routes) -- all admin-token-gated, none public-safe as-is.

Missing for any real frontend migration:
- **Public-safe auth model**: every current route requires the admin
  bearer token. A live frontend cannot ship that token client-side.
  Needs either a public read-only endpoint class, a signed/scoped token
  per session, or a build-time export step (content-pipeline, not live
  API) -- this exact fork was flagged and explicitly deferred back in
  v0.7 and is still unresolved.
- **Normalized game payload shape**: `/v1/games/generate`'s Director
  packages, `/v1/grid/*`'s admin QA shapes, and `data/*.js`'s static
  shapes are all different today. No shared "frontend game payload"
  contract exists yet.
- **Answer validation**: currently 100% client-side (`data/*.js` bundled
  locally). Moving any of it server-side is a real product/latency/
  offline-capability decision, not just a technical one (flagged, not
  decided, in v0.7 too).
- **Daily Challenge requirements**: Daily currently layers on top of
  whichever mode's static data is live that day -- no Gateway-side
  "daily selection" concept exists.
- **Personalization hooks**: favorite-team weighting (Grid/CFB Grid),
  streaks, ratings -- all client-local (`localStorage`/Firebase), no
  Gateway equivalent.
- **Fallback behavior**: if a live-integrated mode's Gateway call fails,
  the frontend needs a defined fallback (last-known-good static export?
  cached response? visible error?) -- not designed yet.
- **Feature flags**: no existing mechanism to enable a Gateway-backed mode
  for a subset of users/builds while keeping the static fallback live.

---

## Engine readiness matrix (Part 31)

| Mode | Engine data ready? | Generator ready? | QA ready? | Gateway ready? | Frontend uses engine? | Safe for v1.2 migration? |
|---|---|---|---|---|---|---|
| NFL Grid | Partial (17/21 criteria, real, tested) | No (admin QA only, not a live generator) | Yes (`safety.py`, identity gates) | Partial (`/v1/grid/*`, admin-only) | **No** | Content-pipeline export first, not live API (per v0.7's decision) |
| CFB Grid | **No** (zero v0.7-v1.1 work touched CFB Grid) | No | No | No | No | No |
| Draft-guessing (NFL_DRAFT) | Yes | **Yes** (real, tested: `test_generate_draft_real_engine`) | Yes | Yes (`/v1/games/generate`) | No | Most mechanically ready of anything in this matrix |
| Championship-guessing (NFL_CHAMPIONSHIP) | Yes | **Yes** (tested) | Yes | Yes | No | Same tier as draft-guessing |
| Player-From-Clues | Yes | **Yes** (tested) | Yes | Yes | No | Ready, but real-time uniqueness QA cost is higher (flagged v0.4-era) |
| Six Degrees | Yes (real, 1.5M edges) | Yes (`graph_explorer.random_six`) | Partial | Yes (`/v1/six-degrees`) | No (no matching frontend mode exists at all) | New mode to build, not a migration |
| Quiz / CFB Quiz | No (16/10 categories, only draft-guessing partially overlaps one) | No | No | No | No | No |
| Blitz / CFB Blitz, Speed / CFB Speed, Silhouette, IQ / CFB IQ, Legends / CFB Legends, Higher or Lower, X's & Os | No | No | No | No | No | No |

---

## Remaining gaps (not hidden)

1. **`PFR:JohnTy00`** still unresolved, still `OPEN`. No new evidence this
   phase.
2. **1,739 real 1999-2005 stat-rows** (14.5% of the source) couldn't
   attach -- players with no canonical identity yet. Re-opening identity
   expansion is v1.0's scope, deliberately not repeated here.
3. **1980-1998 remains completely uncovered** by `PLAYED_FOR` -- this
   phase only reached back to 1999 (the real limit of the `stats_player`
   source actually used). A player like John Elway (retired 1998) still
   has zero team data despite being a real, linked HOF fact.
4. **MVP/SB MVP/ROTY**: unchanged, no safe source found.
5. **CFB Grid received zero engine work** across v0.7-v1.1 -- every phase
   so far has been NFL-only.
6. **No historical teammate relationships, no career-timeline capability,
   no historical Player-From-Clues clues** -- all real, valid Part 12-14
   follow-ups, not attempted (Part 29 discipline).

---

## Recommendation for Claude Code implementation v1.2 -- Production Game API / Frontend Adapter

1. **Resolve the public-auth fork before writing any frontend-facing
   route.** This is the single blocking architectural decision, flagged
   in v0.7, still open. Candidates: (a) build-time content-pipeline export
   (matches everything built so far -- Grid QA, Six Degrees, Director
   capabilities all already assume this model), or (b) a genuinely new
   public/scoped API surface (bigger, riskier, unbuilt).
2. **First real migration candidate: draft-guessing (NFL_DRAFT).** It's
   the only capability that's fully real end-to-end today (data,
   generator, QA, Gateway route, tests) -- start there, not with Grid or
   Six Degrees, both of which have real unresolved architecture questions.
3. **Six Degrees as a genuinely new mode**, not a migration -- the data
   and Gateway route are real and ready; it just has no frontend concept
   yet, which is a product decision as much as an engineering one.
4. **Do not touch CFB Grid, Quiz, Blitz, Speed, Silhouette, IQ, Legends,
   or X's & Os in v1.2** -- none have any engine backing yet; migrating
   them is a v1.3+-scale undertaking each, not incremental to v1.2.
5. Carry forward v1.0/v0.9's still-open items (college/school crosswalk,
   `games`/`starts` backfill via `stats_player` for 2020-2026, MVP/SB
   MVP/ROTY governance decision) as background work, not blocking v1.2.
