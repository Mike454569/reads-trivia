# Team Alias Gap Analysis -- TEAM_UNRESOLVED Investigation

**Analysis only.** No changes made to `team_aliases`, `tools/export_quiz_engine_pilot.py`, the live app, or any generated Quiz data.

Reproduced the exact pipeline from `tools/export_quiz_engine_pilot.py` (seed `reads-quiz-engine-pilot-v1`, limit 500): considered 500, rejected 262, of which **251 TEAM_UNRESOLVED** -- matches the original pilot run exactly.

## Method

For every code behind a TEAM_UNRESOLVED rejection, three Engine-internal questions were checked directly against the database (not assumed):

1. What is `draft_facts`' own observed `(min season, max season, row count)` for this exact code, and does it show any season where the SAME code has two independent, non-overlapping draft classes (a same-season collision -- direct evidence of two different real teams sharing one code)?
2. Does `team_aliases` already have a row for this code? If so, resolving it is just widening that row's `season_start` to match `draft_facts`' own observed minimum for the identical code -- no new information required.
3. Does any OTHER Engine table (`franchises`, `team_seasons`, `entity_aliases`, `coach_team_seasons`, `qb_team_seasons`, `team_stadium_seasons`, the `stg_c_*` staging tables) supply a code->franchise link with broader historical coverage than `team_aliases`? **Checked and ruled out** -- see Finding below.

## Finding: the gap is a source-data boundary, not a missed import

`team_aliases`, `franchises`, and `team_seasons` (and their staging-table originals `stg_c_02_franchises` / `stg_c_03_team_aliases` / `stg_c_04_team_seasons`) all bottom out at **season 2002** -- and the staging tables' `source_url` is `https://github.com/nflverse/nfldata`, confirming this is the coverage limit of the upstream nflverse team-ID crosswalk itself, not a filtering step Engine v4 added. `entity_aliases` (a generic alias table) contains only `entity_type='coach'` rows (177), nothing for teams. `coach_team_seasons`, `qb_team_seasons`, and `team_stadium_seasons` do reach back to 1999, but none of them carry a `franchise_id` column -- they record raw `team_code` only, so they don't add any resolving power. **No table anywhere in Engine v4 links a pre-2002 team code to a franchise_id.**

## Recoverability if the alias/history layer were improved

| Classification | Codes | Rejected candidates recoverable |
|---|---|---|
| SAFE_FIX_AVAILABLE | ARI, ATL, BUF, CAR, CHI, CIN, CLE, DAL, DEN, DET, GB, IND, JAX, KC, MIA, MIN, NE, NO, NYG, NYJ, OAK, PHI, PIT, SD, SEA, SF, STL, TB, TEN, WAS | 197 |
| NEEDS_SOURCE_RESEARCH | BAL1, LARD, LARM, PHO | 46 |
| GENUINELY_AMBIGUOUS | BAL, HOU | 8 |
| UNKNOWN | (none) | 0 |
| **Total** | 36 codes | **251** |

**197 of 251 TEAM_UNRESOLVED rejections (78%) could be recovered with a purely mechanical fix**: widening an *already-existing* `team_aliases` row's `season_start` to match `draft_facts`' own observed range for that identical, non-colliding code. This requires no new mapping and no external research -- it only asks the alias table to agree with data Engine v4 already has.

## Per-code detail

| Code | Rejected (n) | Classification | draft_facts range | draft_facts rows | Existing team_aliases row(s) |
|---|---|---|---|---|---|
| `LARD` | 14 | NEEDS_SOURCE_RESEARCH | 1980-1994 | 144 | (none) |
| `BAL1` | 13 | NEEDS_SOURCE_RESEARCH | 1980-1983 | 43 | (none) |
| `LARM` | 13 | NEEDS_SOURCE_RESEARCH | 1980-1994 | 285 | (none) |
| `MIA` | 12 | SAFE_FIX_AVAILABLE | 1980-2024 | 410 | FR_MIA "Miami Dolphins" 2002-2026 |
| `NO` | 12 | SAFE_FIX_AVAILABLE | 1980-2024 | 353 | FR_NO "New Orleans Saints" 2002-2026 |
| `SEA` | 11 | SAFE_FIX_AVAILABLE | 1980-2024 | 404 | FR_SEA "Seattle Seahawks" 2002-2026 |
| `BUF` | 10 | SAFE_FIX_AVAILABLE | 1980-2024 | 420 | FR_BUF "Buffalo Bills" 2002-2026 |
| `NE` | 10 | SAFE_FIX_AVAILABLE | 1980-2024 | 456 | FR_NE "New England Patriots" 2002-2026 |
| `PIT` | 9 | SAFE_FIX_AVAILABLE | 1980-2024 | 432 | FR_PIT "Pittsburgh Steelers" 2002-2026 |
| `WAS` | 9 | SAFE_FIX_AVAILABLE | 1980-2024 | 379 | FR_WAS "Washington Commanders" 2022-2026; FR_WAS "Washington Football Team" 2020-2021; FR_WAS "Washington Redskins" 2002-2019 |
| `CLE` | 8 | SAFE_FIX_AVAILABLE | 1984-2024 | 319 | FR_CLE "Cleveland Browns" 2002-2026 |
| `OAK` | 8 | SAFE_FIX_AVAILABLE | 1995-2019 | 198 | FR_LV "Oakland Raiders" 2002-2019 |
| `PHI` | 8 | SAFE_FIX_AVAILABLE | 1980-2024 | 405 | FR_PHI "Philadelphia Eagles" 2002-2026 |
| `KC` | 7 | SAFE_FIX_AVAILABLE | 1980-2024 | 388 | FR_KC "Kansas City Chiefs" 2002-2026 |
| `MIN` | 7 | SAFE_FIX_AVAILABLE | 1980-2024 | 413 | FR_MIN "Minnesota Vikings" 2002-2026 |
| `SD` | 7 | SAFE_FIX_AVAILABLE | 1980-2016 | 340 | FR_LAC "San Diego Chargers" 2002-2016 |
| `DAL` | 6 | SAFE_FIX_AVAILABLE | 1980-2024 | 433 | FR_DAL "Dallas Cowboys" 2002-2026 |
| `DET` | 6 | SAFE_FIX_AVAILABLE | 1980-2024 | 393 | FR_DET "Detroit Lions" 2002-2026 |
| `GB` | 6 | SAFE_FIX_AVAILABLE | 1980-2024 | 445 | FR_GB "Green Bay Packers" 2002-2026 |
| `IND` | 6 | SAFE_FIX_AVAILABLE | 1984-2024 | 354 | FR_IND "Indianapolis Colts" 2002-2026 |
| `NYJ` | 6 | SAFE_FIX_AVAILABLE | 1980-2024 | 398 | FR_NYJ "New York Jets" 2002-2026 |
| `PHO` | 6 | NEEDS_SOURCE_RESEARCH | 1988-1993 | 72 | (none) |
| `SF` | 6 | SAFE_FIX_AVAILABLE | 1980-2024 | 391 | FR_SF "San Francisco 49ers" 2002-2026 |
| `ATL` | 5 | SAFE_FIX_AVAILABLE | 1980-2024 | 385 | FR_ATL "Atlanta Falcons" 2002-2026 |
| `CHI` | 5 | SAFE_FIX_AVAILABLE | 1980-2024 | 406 | FR_CHI "Chicago Bears" 2002-2026 |
| `CIN` | 5 | SAFE_FIX_AVAILABLE | 1980-2024 | 446 | FR_CIN "Cincinnati Bengals" 2002-2026 |
| `DEN` | 5 | SAFE_FIX_AVAILABLE | 1980-2024 | 395 | FR_DEN "Denver Broncos" 2002-2026 |
| `HOU` | 5 | GENUINELY_AMBIGUOUS | 1980-2024 | 372 | FR_HOU "Houston Texans" 2002-2026 |
| `JAX` | 5 | SAFE_FIX_AVAILABLE | 1995-2024 | 243 | FR_JAX "Jacksonville Jaguars" 2002-2026 |
| `CAR` | 4 | SAFE_FIX_AVAILABLE | 1995-2024 | 222 | FR_CAR "Carolina Panthers" 2002-2026 |
| `TB` | 4 | SAFE_FIX_AVAILABLE | 1980-2024 | 401 | FR_TB "Tampa Bay Buccaneers" 2002-2026 |
| `BAL` | 3 | GENUINELY_AMBIGUOUS | 1980-2024 | 292 | FR_BAL "Baltimore Ravens" 2002-2026 |
| `NYG` | 3 | SAFE_FIX_AVAILABLE | 1980-2024 | 399 | FR_NYG "New York Giants" 2002-2026 |
| `STL` | 3 | SAFE_FIX_AVAILABLE | 1995-2015 | 183 | FR_LAR "St Louis Rams" 2002-2015 |
| `TEN` | 3 | SAFE_FIX_AVAILABLE | 1997-2024 | 231 | FR_TEN "Tennessee Titans" 2002-2026 |
| `ARI` | 1 | SAFE_FIX_AVAILABLE | 1994-2024 | 243 | FR_ARI "Arizona Cardinals" 2002-2026 |

## Evidence detail by classification

### SAFE_FIX_AVAILABLE

Every code below has **exactly one** `team_aliases` row (one franchise_id, no other code ever maps to that same franchise_id in `team_aliases`), and `draft_facts` never shows a second, independent draft class filed under the same code in the same season -- i.e. no internal collision signal anywhere in Engine v4. The fix is mechanical: widen that single existing row's `season_start` down to `draft_facts`' own observed minimum for that code.

- **`ARI`** (1 rejected): `draft_facts` shows 243 rows, seasons 1994-2024, uninterrupted. Existing row: `team_aliases` maps `ARI` -> `FR_ARI` ("Arizona Cardinals") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `ARI`, and `FR_ARI` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1994 introduces no ambiguity.
- **`ATL`** (5 rejected): `draft_facts` shows 385 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `ATL` -> `FR_ATL` ("Atlanta Falcons") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `ATL`, and `FR_ATL` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`BUF`** (10 rejected): `draft_facts` shows 420 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `BUF` -> `FR_BUF` ("Buffalo Bills") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `BUF`, and `FR_BUF` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`CAR`** (4 rejected): `draft_facts` shows 222 rows, seasons 1995-2024, uninterrupted. Existing row: `team_aliases` maps `CAR` -> `FR_CAR` ("Carolina Panthers") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `CAR`, and `FR_CAR` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1995 introduces no ambiguity.
- **`CHI`** (5 rejected): `draft_facts` shows 406 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `CHI` -> `FR_CHI` ("Chicago Bears") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `CHI`, and `FR_CHI` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`CIN`** (5 rejected): `draft_facts` shows 446 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `CIN` -> `FR_CIN` ("Cincinnati Bengals") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `CIN`, and `FR_CIN` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`CLE`** (8 rejected): `draft_facts` shows 319 rows, seasons 1984-2024, uninterrupted except a gap at [(1995, 1999)]. Existing row: `team_aliases` maps `CLE` -> `FR_CLE` ("Cleveland Browns") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `CLE`, and `FR_CLE` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1984 introduces no ambiguity.
- **`DAL`** (6 rejected): `draft_facts` shows 433 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `DAL` -> `FR_DAL` ("Dallas Cowboys") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `DAL`, and `FR_DAL` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`DEN`** (5 rejected): `draft_facts` shows 395 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `DEN` -> `FR_DEN` ("Denver Broncos") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `DEN`, and `FR_DEN` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`DET`** (6 rejected): `draft_facts` shows 393 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `DET` -> `FR_DET` ("Detroit Lions") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `DET`, and `FR_DET` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`GB`** (6 rejected): `draft_facts` shows 445 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `GB` -> `FR_GB` ("Green Bay Packers") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `GB`, and `FR_GB` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`IND`** (6 rejected): `draft_facts` shows 354 rows, seasons 1984-2024, uninterrupted. Existing row: `team_aliases` maps `IND` -> `FR_IND` ("Indianapolis Colts") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `IND`, and `FR_IND` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1984 introduces no ambiguity.
- **`JAX`** (5 rejected): `draft_facts` shows 243 rows, seasons 1995-2024, uninterrupted. Existing row: `team_aliases` maps `JAX` -> `FR_JAX` ("Jacksonville Jaguars") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `JAX`, and `FR_JAX` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1995 introduces no ambiguity.
- **`KC`** (7 rejected): `draft_facts` shows 388 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `KC` -> `FR_KC` ("Kansas City Chiefs") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `KC`, and `FR_KC` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`MIA`** (12 rejected): `draft_facts` shows 410 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `MIA` -> `FR_MIA` ("Miami Dolphins") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `MIA`, and `FR_MIA` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`MIN`** (7 rejected): `draft_facts` shows 413 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `MIN` -> `FR_MIN` ("Minnesota Vikings") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `MIN`, and `FR_MIN` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`NE`** (10 rejected): `draft_facts` shows 456 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `NE` -> `FR_NE` ("New England Patriots") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `NE`, and `FR_NE` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`NO`** (12 rejected): `draft_facts` shows 353 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `NO` -> `FR_NO` ("New Orleans Saints") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `NO`, and `FR_NO` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`NYG`** (3 rejected): `draft_facts` shows 399 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `NYG` -> `FR_NYG` ("New York Giants") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `NYG`, and `FR_NYG` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`NYJ`** (6 rejected): `draft_facts` shows 398 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `NYJ` -> `FR_NYJ` ("New York Jets") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `NYJ`, and `FR_NYJ` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`OAK`** (8 rejected): `draft_facts` shows 198 rows, seasons 1995-2019, uninterrupted. Existing row: `team_aliases` maps `OAK` -> `FR_LV` ("Oakland Raiders") for 2002-2019 only. Evidence: this is the *only* `team_aliases` row for `OAK`, and `FR_LV` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1995 introduces no ambiguity.
- **`PHI`** (8 rejected): `draft_facts` shows 405 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `PHI` -> `FR_PHI` ("Philadelphia Eagles") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `PHI`, and `FR_PHI` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`PIT`** (9 rejected): `draft_facts` shows 432 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `PIT` -> `FR_PIT` ("Pittsburgh Steelers") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `PIT`, and `FR_PIT` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`SD`** (7 rejected): `draft_facts` shows 340 rows, seasons 1980-2016, uninterrupted. Existing row: `team_aliases` maps `SD` -> `FR_LAC` ("San Diego Chargers") for 2002-2016 only. Evidence: this is the *only* `team_aliases` row for `SD`, and `FR_LAC` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`SEA`** (11 rejected): `draft_facts` shows 404 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `SEA` -> `FR_SEA` ("Seattle Seahawks") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `SEA`, and `FR_SEA` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`SF`** (6 rejected): `draft_facts` shows 391 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `SF` -> `FR_SF` ("San Francisco 49ers") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `SF`, and `FR_SF` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`STL`** (3 rejected): `draft_facts` shows 183 rows, seasons 1995-2015, uninterrupted. Existing row: `team_aliases` maps `STL` -> `FR_LAR` ("St Louis Rams") for 2002-2015 only. Evidence: this is the *only* `team_aliases` row for `STL`, and `FR_LAR` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1995 introduces no ambiguity.
- **`TB`** (4 rejected): `draft_facts` shows 401 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `TB` -> `FR_TB` ("Tampa Bay Buccaneers") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `TB`, and `FR_TB` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1980 introduces no ambiguity.
- **`TEN`** (3 rejected): `draft_facts` shows 231 rows, seasons 1997-2024, uninterrupted. Existing row: `team_aliases` maps `TEN` -> `FR_TEN` ("Tennessee Titans") for 2002-2026 only. Evidence: this is the *only* `team_aliases` row for `TEN`, and `FR_TEN` is not reachable via any other code in `team_aliases`, so widening `season_start` to 1997 introduces no ambiguity.
- **`WAS`** (9 rejected): `draft_facts` shows 379 rows, seasons 1980-2024, uninterrupted. Existing row: `team_aliases` maps `WAS` -> `FR_WAS` ("Washington Redskins") for 2002-2019 (earliest of its rows). Evidence: `team_aliases` has 3 rows for `WAS` (renames over time: "Washington Redskins" 2002-2019; "Washington Football Team" 2020-2021; "Washington Commanders" 2022-2026), but all resolve to the SAME `franchise_id` (`FR_WAS`), which is not reachable via any other code in `team_aliases` -- so franchise-level resolution is still unambiguous. The mechanical fix widens only the earliest row ("Washington Redskins", currently 2002-2019) back to 1980; the display name for the widened span is a secondary question this fix does not need to answer to resolve the franchise_id itself.

### NEEDS_SOURCE_RESEARCH

No `team_aliases` row exists for these codes at all, and no other Engine table links them to a franchise_id (see Finding above). Each has a *lead* -- a draft_facts season range that sits adjacent to, and does not overlap, an already-resolved code -- but Engine never states the connection anywhere, so treating the lead as confirmed would be guessing, not reading Engine data. External, authoritative NFL franchise-history research is needed to confirm (or rule out) each lead before any mapping is added.

- **`BAL1`** (13 rejected): draft_facts BAL1 spans exactly 1980-1983 (43 rows) -- the SAME four seasons as plain `BAL` (52 rows in that window), but with entirely different, non-overlapping draft classes in every one of those seasons (verified: e.g. 1980 BAL's top picks differ completely from 1980 BAL1's top picks). This confirms two distinct entities coexisted under Baltimore-flavored codes in 1980-1983, but BAL1 has zero rows in team_aliases or anywhere else, so Engine gives no way to identify which franchise BAL1 refers to.
- **`LARD`** (14 rejected): draft_facts LARD spans 1980-1994 (144 rows) with zero overlap with OAK, whose draft_facts range starts exactly at 1995. OAK already resolves to FR_LV, but no table anywhere links LARD to FR_LV or to any franchise_id.
- **`LARM`** (13 rejected): draft_facts LARM spans 1980-1994 (285 rows) with zero overlap with STL, whose draft_facts range starts exactly at 1995. STL already resolves to FR_LAR (see SAFE_FIX_AVAILABLE), but no table anywhere links LARM to FR_LAR or to any franchise_id.
- **`PHO`** (6 rejected): draft_facts PHO spans 1988-1993 (72 rows) with zero overlap with ARI, whose draft_facts range starts exactly at 1994 (the season immediately after). No team_aliases row exists for PHO, and no table states PHO and FR_ARI are the same franchise -- this adjacency is circumstantial only.

### GENUINELY_AMBIGUOUS

These codes are demonstrably reused by two different, unrelated franchises across non-overlapping eras -- provable directly from Engine v4's own tables, not external knowledge:

- **`HOU`** (5 rejected): `draft_facts` shows HOU rows in two disjoint blocks -- 1980-1996 (195 rows) and 2002-2024 (177 rows) -- separated by a clean 1997-2001 gap. `team_aliases` resolves HOU -> `FR_HOU` ("Houston Texans") for 2002+ only. Critically, `team_aliases`' entry for `FR_TEN` ("Tennessee Titans") uses code `TEN`, never `HOU` -- so Engine's own franchise records treat whatever team used `HOU` before 1997 as a *different* code-space than the Titans' own lineage, while `TEN` itself picks up cleanly in 1997 (matching the relocation year) and resolves without ambiguity from then on (see `TEN` in the SAFE_FIX_AVAILABLE list). This means the pre-1997 `HOU` rows are neither safely mappable to `FR_HOU` (a different, unrelated expansion franchise) nor directly restatable as `TEN` (the code itself is `HOU`, not `TEN`, in draft_facts) without an external crosswalk.
- **`BAL`** (3 rejected): `draft_facts` shows BAL rows in two disjoint blocks -- 1980-1983 (52 rows) and 1996-2024 (240 rows) -- with a clean 1984-1995 gap. `team_aliases` resolves BAL -> `FR_BAL` ("Baltimore Ravens") for 2002+ only, and that resolution is almost certainly correct for the whole 1996+ block (the Ravens' first season was 1996). The 1980-1983 block, however, sits in the same window as the still-unresolved `BAL1` code above and represents a franchise that predates the Ravens by over a decade -- mapping it to `FR_BAL` would be wrong regardless of what BAL1 turns out to mean, since Engine gives no indication the 1980-1983 BAL team and the 1996+ BAL team are the same organization.

### UNKNOWN

No codes fell into this bucket -- every code encountered had enough Engine-internal structure (even if the answer was "Engine has no data at all") to classify confidently into one of the other three categories.

