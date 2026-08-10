# Reads Football Engine v4.0 -- Claude Code Implementation v0.7 Report

Scope actually delivered in this phase, in the order it was built:
1. Rebuild and verify the Engine database (`Reads_v4_Database.sqlite`).
2. Port Graph Explorer / Six Degrees into the Gateway.
3. Port Grid roster/eligibility into the Gateway (content-pipeline model).

Everything below is either a command that was actually run with its actual
output, or a fact read directly from source files/the live database. Nothing
in this report is estimated. Where something was not done, it says so.

---

## 1. Database rebuild

- Source: `Reads_v4_Database.sqlite.gz.part00` (user-provided this phase) +
  `part01`/`part02`/`part03` (pre-existing), reassembled via `cat ... | gzip -d`.
- Result: `Reads_Football_Data_Engine_v4.0/Reads_v4_Database.sqlite`,
  1,650,307,072 bytes, sha256
  `39ed5fe996e6b240642bde46daabb2eec1dc310f46e8cdc7e3ea3365070a549d` --
  verified byte-for-byte against `Reads_v4_Rebuild_Instructions/MANIFEST.json`.
- `reads_football_v4.0.sqlite` is a symlink to the above (the hardcoded path
  `graph_explorer.py`/`api_server.py`/`tools/quiz_export/engine.py` all
  resolve to).
- Integrity, re-checked in this phase:
  ```
  PRAGMA foreign_key_check   -> 0 errors
  PRAGMA quick_check         -> ok
  PRAGMA integrity_check(5)  -> ok
  ```

---

## 2. Gateway Graph / Six Degrees port

### Files created
- `gateway/services/graph.py` -- thin wrapper around
  `graph_explorer.search/shortest_path/random_six`, translated into this
  Gateway's request/response and `GatewayError` conventions. Deliberately
  has no hardcoded `node_type` whitelist (an earlier draft guessed one;
  removed once I realized it was never checked against real data).
- `gateway/tests/test_graph.py` -- 19 tests.

### Files modified
- `gateway/app.py` -- added `graph_limiter`/`graph_path_limiter`, three
  routes, extended `/v1/capabilities`.
- `gateway/config.py` -- `GRAPH_SEARCH_LIMIT_MAX`, `GRAPH_PATH_DEFAULT_MAX_DEPTH`,
  `GRAPH_PATH_MAX_DEPTH_LIMIT`, `SIX_DEGREES_*`, `GRAPH_RATE_LIMIT_MAX`,
  `GRAPH_PATH_RATE_LIMIT_MAX`.
- `gateway/tests/conftest.py` -- reset the two new limiters per test.

### Routes added
| Route | Auth | Rate limit |
|---|---|---|
| `GET /v1/graph/search` | admin | 30/60s |
| `GET /v1/graph/path` | admin | 10/60s |
| `GET /v1/six-degrees` | admin | 30/60s |

### Real database used
`Reads_Football_Data_Engine_v4.0/reads_football_v4.0.sqlite` --
**91,466 graph_nodes**, **1,412,831 graph_edges**, 500 `graph_path_cache`
rows, 415,973 `puzzle_catalog` rows.

### Real verification examples (this phase, live HTTP via TestClient)
```
GET /v1/graph/search?query=Mahomes&limit=3
-> {"count": 1, "results": [{"node_type": "nfl_player", "node_id": "PFR:MahoPa00",
    "display_name": "Patrick Mahomes", "popularity_score": 0.6465...}]}

GET /v1/graph/path?start_type=nfl_player&start_id=PFR:MahoPa00&end_type=team&end_id=KC
-> {"found": true, "degrees": 1,
    "path": [{"from_id": "PFR:MahoPa00", "predicate": "DRAFTED_BY", "to_id": "KC", ...}]}

GET /v1/six-degrees?seed=daily
-> "Connect Seattle Seahawks to Mike McCarthy in 2 moves or fewer."
```

---

## 3. Gateway Grid roster/eligibility port

### Architecture decision (confirmed with the user before building)
The Gateway is admin-only and private (bearer token on every route, CORS
restricted to localhost, `https://reads.football` explicitly "documented,
not enabled"). Two integration models were presented; **content-pipeline
integration** was chosen: the Gateway gains an admin-only Grid capability
for content ops to verify/QA `data/grid.js` entries against the real graph.
**The live frontend is unchanged** -- `app.js`'s Grid game and `data/grid.js`
still work exactly as before: 100% client-side, offline (`file://`)-capable,
instant validation. Confirmed via file mtimes at the end of this phase that
neither file was touched:
```
app.js        last modified 2026-08-09 (before this phase started)
data/grid.js  last modified 2026-08-07 (before this phase started)
```

### Files created
- `gateway/services/grid.py` -- the adapter (293 lines). Public functions:
  `list_supported_criteria()`, `build_board()`, `resolve_intersection()`,
  `player_metadata()`, `validate_answer()`.
- `gateway/tests/test_grid.py` -- 28 tests.

### Files modified
- `gateway/app.py` -- added `grid_lookup_limiter`/`grid_board_limiter`,
  five routes, extended `/v1/capabilities`.
- `gateway/config.py` -- `GRID_LOOKUP_RATE_LIMIT_MAX`, `GRID_BOARD_RATE_LIMIT_MAX`.
- `gateway/models.py` -- `GridBoardRequest`, `GridValidateRequest`
  (`extra="forbid"`, same convention as every existing request model).
- `gateway/errors.py` -- added a generic `NOT_FOUND` code (404) for
  well-formed-but-nonexistent resource lookups (`/v1/grid/player/{id}`);
  `PACKAGE_NOT_FOUND` stays package-specific.
- `gateway/tests/conftest.py` -- reset the two new limiters per test.

### Routes added
| Route | Auth | Rate limit |
|---|---|---|
| `GET /v1/grid/criteria` | admin | 30/60s |
| `POST /v1/grid/board` | admin | 15/60s |
| `GET /v1/grid/intersection` | admin | 30/60s |
| `POST /v1/grid/validate` | admin | 15/60s |
| `GET /v1/grid/player/{node_id}` | admin | 30/60s |

### Grid eligibility rules -- copied 1:1 from `data/grid.js`, not invented
Read `data/grid.js`'s real `GRID_CRITERIA` and `app.js`'s real
`buildGridAttempt`/`submitGridGuess` (lines 2527-2624) before writing any
adapter code. Current Grid has 32 team criteria (`teams.indexOf(code)`,
career-long, any-season) + 21 stat criteria (position groups, draft round,
7 accolade flags, team-count).

### Real graph schema coverage (checked against the live database, not assumed)
| Predicate/data | Rows | Season range | Used for |
|---|---|---|---|
| `PLAYED_FOR` | 28,617 | **2006-2019 only** | team_* roster membership |
| `PLAYED_POSITION` | 19,726 | 2006-2019 | the 8 position-group criteria |
| `PLAYOFF_RESULT` (object='WonSB') | subset of 296 | back to 2002 | `sb_champ` (derived) |
| `DRAFTED_BY`/`DRAFTED_IN` | 12,253 each | 1980-2024, team+year only, **no round column** | -- |
| `ATTENDED_BEFORE_DRAFT` | 3,751 (204 distinct players) | -- | -- |
| award_fact/`WON_AWARD` | 91 | 1935-1944-ish | -- (pre-1950s CFB Heisman-era awards only, `subject_type='cfb_player'`) |

### Criterion support matrix (real, not guessed)
**Supported (graph-backed):**
- 32 `team_<CODE>` (after a verified 3-entry franchise-relocation alias:
  `OAK->LV`, `SD->LAC`, `STL->LAR` -- each confirmed via real season-range
  queries before being added to the map)
- 8 position-group criteria (`pos_qb` ... `pos_ol`, with side-specific graph
  codes like `RCB`/`LDT`/`RG` folded into the same equivalence groups
  `data/grid.js` already uses for DE/DT/EDGE -> `pos_dl` etc.)
- `multi_team`, `one_team`
- `sb_champ` (**derived**: `PLAYED_FOR(player,team,season)` joined to
  `PLAYOFF_RESULT(team,season)='WonSB'` -- a real, source-backed team-season
  fact, same derivation pattern the DB's own `PRODUCTION_SAFE_DERIVED`
  status already uses elsewhere)

**Unsupported -- confirmed absent from the schema, not attempted:**
`draft_r1`, `draft_undrafted`, `draft_day2plus` (no round data anywhere),
`hof`, `mvp`, `sb_mvp`, `roty`, `probowl_5plus`, `probowl_10plus`,
`allpro_3plus` (no NFL-level award/honor data in the graph at all).
College/school was never a `data/grid.js` criterion type to begin with, and
`ATTENDED_BEFORE_DRAFT`'s 1.7% coverage (204/12,253) would be too sparse to
add safely even if it were.

Requesting an unsupported criterion, or a `season` outside the real
2006-2019 coverage window, returns `UNDERSTOOD_BUT_UNSUPPORTED` (a
structured 200, not a silent empty result and not a guess) -- this was a
real bug I found and fixed during this phase: my first version let an
out-of-window season query fall through to a real SQL query that correctly
returned zero rows, which would have looked identical to "checked, found
nobody" instead of "no data exists to check." Fixed before writing tests.

### Real verification examples (this phase, live HTTP via TestClient)

**Valid team x position intersection:**
```
GET /v1/grid/intersection?row_id=team_KC&col_id=pos_qb
-> count includes PFR:MahoPa00 "Patrick Mahomes"
```

**Valid team x sb_champ (derived) intersection:**
```
GET /v1/grid/intersection?row_id=team_GB&col_id=sb_champ
-> count: 78, sample: A.J. Hawk, Aaron Rodgers, Andrew Quarless
```

**Rejected invalid answer (satisfies one side only):**
```
POST /v1/grid/validate {"row_id":"team_NE","col_id":"pos_qb","player_name":"Aaron Rodgers"}
-> {"valid": false, "satisfies_row": false, "satisfies_col": true,
    "reason": "DOES_NOT_SATISFY_BOTH_CONDITIONS"}
```

**Season-bound example:**
```
POST /v1/grid/validate {..., "player_name":"Patrick Mahomes", "season":2018} -> valid: true
POST /v1/grid/validate {..., "player_name":"Patrick Mahomes", "season":2010} -> valid: false
(Mahomes' real first KC season is 2017 -- confirmed via DRAFTED_BY/PLAYED_FOR season_start.)
```

**Identity safety -- real name collision, not fabricated:**
`graph_nodes` has exactly 399 duplicate `nfl_player` display names. Tested
directly against one:
```
POST /v1/grid/validate {"row_id":"team_MIN","col_id":"pos_rb","player_name":"Adrian Peterson"}
-> {"valid": false, "reason": "AMBIGUOUS",
    "candidates": [{"node_id":"PFR:PeteAd00", ...}, {"node_id":"PFR:PeteAd01", ...}]}
```
Never silently resolved to "first match."

### Performance
All lookups filter on `(subject_type, subject_id)` or `(object_type,
object_id)` plus `predicate`, which SQLite resolves via the existing
`sqlite_autoindex_graph_edges_1` / `idx_graph_edges_object` indexes (checked
with `EXPLAIN QUERY PLAN` -- both `SEARCH ... USING INDEX`, not `SCAN`).
Measured: 50 team-roster lookups in 84ms (~1.7ms each); 50 single-player
lookups in <1ms each. `multi_team`/`one_team` is the one query that pulls
all 28,617 `PLAYED_FOR` rows in one shot (unavoidable -- it's a per-player
distinct-team count) -- a full board including it still completes in well
under a second in the test suite's own timing assertions.

---

## 4. Full regression (this phase, actually executed)

```
$ READS_ENGINE_DIR=.../Reads_Football_Data_Engine_v4.0 gateway/.venv/bin/python -m pytest gateway/tests/ -v
...
79 passed in 19.09s
```
Breakdown: 25 pre-existing (`test_gateway.py`) + 19 graph (`test_graph.py`)
+ 28 grid (`test_grid.py`) + 7 staging-hardening (`test_staging_hardening.py`) = 79.

Also re-ran in this phase, independently of pytest:
- `PRAGMA foreign_key_check` / `quick_check` / `integrity_check(5)` on the
  live database -- all clean (section 1 above).
- Live `/v1/graph/search`, `/v1/graph/path`, `/v1/six-degrees` via
  `TestClient` -- all three still return real, correct results (section 2).
- `app.js`/`data/grid.js` mtimes confirm zero frontend changes this phase.

No failures were hidden or worked around silently. The one real bug found
during this phase (out-of-coverage season silently returning empty instead
of `UNDERSTOOD_BUT_UNSUPPORTED`) is documented above, not omitted.

---

## 5. Environment / config requirements

`tools/quiz_export/engine.py` hardcodes a fallback `READS_ENGINE_DIR`
pointing at a different machine's path
(`/Users/micahnichols/Downloads/Reads_Football_Data_Engine_v4.0`) --
**pre-existing, not introduced this phase**. It is already correctly
overridden for deployment in `gateway/fly.toml`
(`READS_ENGINE_DIR = "/data/engine"`) and documented in `.env.example`. For
any local run on this machine, export it first:
```bash
export READS_ENGINE_DIR="/Users/enterprise2/Desktop/2026 NFL Draft Guide/nfl-trivia/Reads_Football_Data_Engine_v4.0"
```
Not hardcoded into any application source file.

Test dependencies: `gateway/.venv` (created this phase),
`gateway/requirements-dev.txt` (fastapi, uvicorn, pydantic, httpx, pytest --
unchanged, no new dependencies added for either the graph or Grid port).

---

## 6. Coverage restrictions (do not build on these without re-reading this section)

1. **Grid roster data is a 2006-2019 window, not "current" and not
   "all-time."** This is narrower than `data/grid.js`'s existing hand/ESPN-
   curated scope in both directions. This module is a QA/verification tool
   for that window, not a replacement data source.
2. **No draft round, no NFL-level awards (HOF/MVP/SB MVP/ROTY/Pro
   Bowl/All-Pro) anywhere in the graph.** 10 of `data/grid.js`'s 21 stat
   criteria cannot be backed by this Engine as it's currently populated.
3. **College/school coverage is 1.7%** (204/12,253 drafted players) -- not
   usable as a Grid criterion at any real scale.
4. Graph-wide: `graph_nodes`/`graph_edges` verification_status values
   `AUTO_REVIEW`/`CONFLICT` are excluded from every Grid query (same
   convention `graph_explorer.shortest_path` already uses).

## 7. Intentionally disabled / not attempted

- No `data/grid.js` regeneration or refresh script was written. Given
  restriction #1 above, an automatic refresh today would *narrow* the
  live file's real coverage, which would be a regression, not an
  improvement -- flagged as a v0.8 question, not silently built anyway.
- No live/public Grid API. The admin-gated, content-pipeline-only routes
  above are all that exists; nothing here is reachable by the deployed
  static site.
- College/school criterion type was not added to `CRITERIA_REGISTRY`'s
  supported set, even though `ATTENDED_BEFORE_DRAFT` technically exists as a
  predicate -- 1.7% coverage isn't production-safe, and it was never a
  `data/grid.js` criterion type to begin with (adding it would be new
  gameplay, which was out of scope).

## 8. Deployment implications

No new runtime dependencies. `gateway/fly.toml` already sets
`READS_ENGINE_DIR` correctly for the deployed environment. The five new
Grid routes are admin-gated exactly like every existing route, so no CORS
or auth posture change is needed for deployment. `gateway/errors.py`'s new
`NOT_FOUND` code is additive (existing clients that only check for known
codes are unaffected).

## 9. Rollback

Every change in this phase is additive (new files, new routes, new
config/model fields, one new error code). To roll back:
- Remove `gateway/services/grid.py`, `gateway/tests/test_grid.py`.
- Revert the Grid-related additions in `gateway/app.py`, `gateway/config.py`,
  `gateway/models.py`, `gateway/errors.py`, `gateway/tests/conftest.py`
  (each addition is a clearly delimited block/import, not an edit to
  existing logic).
- The graph/Six Degrees port (section 2) and database rebuild (section 1)
  are unaffected by rolling back Grid alone, and vice versa.
- No data migration occurred -- the database itself was only read, never
  written, by anything in this phase.

## 10. Recommendation for v0.8

1. Decide, with real content-ops input, whether a **manual QA workflow**
   (content ops calls `/v1/grid/intersection` to spot-check specific
   `data/grid.js` entries against the 2006-2019 window, by hand) is valuable
   enough on its own, given the coverage gap -- or whether it's not worth
   using until the Engine's data covers current seasons and accolades.
2. If NFL-level award/HOF/Pro-Bowl data is ever ingested into the graph,
   `UNSUPPORTED_CRITERIA_REASONS` in `gateway/services/grid.py` names
   exactly which criteria to re-enable and how (the code structure already
   anticipates this -- no redesign needed, just populate the data and move
   the ids from `unsupported` to `POSITION_GROUPS`-style registries).
3. Do not build a `data/grid.js` auto-refresh pipeline until the roster
   coverage window extends past 2019 -- doing so earlier would regress the
   live game's real player pool.
4. The broader "unified `getGame()` boundary across all existing
   generators" work from the original v0.7 prompt (Connections/Matching/
   Ordering/Odd One Out, etc.) has still not been started -- it was
   explicitly descoped to graph/Six Degrees + Grid for this phase and
   should be its own scoping conversation before any code is written.
