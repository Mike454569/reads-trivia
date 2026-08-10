# QB/Season Engine Coverage Report -- Pilot Domain #2

Investigation only, read-only queries against `reads_football_v4.0.sqlite`. No files modified.

## Available production-safe source tables/views

| Object | Type | Rows | Season range | Notes |
|---|---|---|---|---|
| `qb_team_seasons` | table | 1,587 | 1999-2025 | 100% `verification_status='SOURCE_BACKED'`, 100% `source_id='NFLVERSE_DATA'` (uniform, no mixed provenance) |
| `v_qb_season_clues` | view | 1,587 | 1999-2025 | `SELECT season,team_code,qb_source_id,qb_name,starts_observed,first_start_date,last_start_date FROM qb_team_seasons WHERE starts_observed>=1` -- a thin filter over the same table, not an independent source |
| `team_seasons` | table | 800 | 2002-2026 | Has `franchise_id` directly, but doesn't reach back into the 1999-2001 window; `team_aliases` (already fixed for Pilot #1) is season-aware further back and is what this pilot actually uses for resolution |
| `puzzle_catalog` (`mode_id='qb_season'`) | table | 1,131 (1,081 eligible) | 2020-2025 observed in sample | **Pre-existing, already Engine-QA'd puzzle set** -- see finding below |
| `game_factory_capabilities` | table | 0 rows matching `%QB%` | -- | Game Factory has **no built-in QB/season predicate** (confirmed by reading `game_factory.py`/`game_factory_legacy.py` in full and querying the capabilities table) |
| `data_coverage` | table | 0 rows for a QB domain | -- | No domain-level `production_safe` summary row exists specifically for QB starts data. Production-safety is still independently verifiable at the row level (see below), just not via the same single-row shortcut used for `NFL_DRAFT` in Pilot #1. |

### Row-level production-safety (in place of a `data_coverage` domain row)

`qb_team_seasons`: every one of the 1,587 rows has `verification_status='SOURCE_BACKED'` and `source_id='NFLVERSE_DATA'`; `sources.NFLVERSE_DATA.approved_for_import=1` (same approved source already verified for Pilot #1). This row-level check is used as the production-safety gate for this pilot, since no `data_coverage` summary row exists to shortcut it.

### Finding: an existing `qb_season` puzzle mode already exists in `puzzle_catalog`

1,131 rows, 1,081 `eligible=1`, all `verification_status='SOURCE_BACKED'` / `source_id='NFLVERSE_DATA'`. Mechanic: **guess-the-QB** -- e.g. `{"answer": "Dak Prescott", "prompt": "Which QB recorded 8 starts for DAL in 2024?"}`. `difficulty_score`/`difficulty_band` are populated (`mode_health`: 359 easy / 336 medium / 264 hard / 122 expert). `source_entity_id` is the QB's GSIS id (`qb_source_id`) and `season` is populated, so these rows join back to `qb_team_seasons` cleanly (verified: 1,146 of 1,131 rows join, the small excess coming from the mid-season-trade cases described below).

This is strong corroborating evidence the domain is production-ready at Engine's own discretion. It was **not** used as the primary generation path for this pilot (see Step 2 for why), but its `difficulty_score`/`difficulty_band` **is** reused as the Engine-computed difficulty signal for this pilot's own candidates (joined by `qb_source_id` + `season` + `team_code`), rather than inventing a difficulty heuristic -- see Step 2.

## Usable predicates

Evaluated against the user's example list, using only `qb_team_seasons` + `team_aliases` (already fixed in Pilot #1) + `puzzle_catalog`'s existing `qb_season` difficulty scores:

| Predicate | Verdict | Why |
|---|---|---|
| "Which team did this QB play for in a given season?" | **USABLE** | Direct 1:1 analog to Pilot #1's `DRAFTED_BY` mechanic; reuses the exact same, already-audited team-resolution and distractor logic. Chosen for this pilot -- see Step 2. |
| "Which QB led this team in a given season?" | Usable, not chosen | Requires a `MAX(starts_observed)` aggregation per `(season, team_code)` plus explicit tie-rejection. 18 of 861 team-seasons (~2%) have a tie for most starts and would need to be excluded. More new logic than the chosen predicate for no clear safety gain. |
| "Which season belongs to this QB/team pairing?" | Rejected | A QB can start for the same team across many seasons; "the" season is only well-defined for QBs with exactly one season on that team, which shrinks the usable pool and adds another filter layer without adding verification strength. |
| "Which QB/team season achieved a particular verified record/stat?" | Partially usable (via the pre-existing `qb_season` mode) | `starts_observed` is the only stat column in `qb_team_seasons`; Engine's own `qb_season` puzzle mode already implements this shape ("guess the QB from a start count"). Not rebuilt from scratch this round -- see Step 2. |
| Season ordering/comparison questions | Rejected for this pilot | `ordering`/`matching` mechanics don't map cleanly onto the flat 4-option `window.QUIZ_DATA` contract without a lossy transformation; out of scope for a single-mechanic pilot. |

## Identity-resolution issues found

- **7 of 347 distinct `qb_source_id` values have more than one `qb_name` string across their rows.** Two different failure modes were found: (a) genuine typos/format variants (`"Kurt Waner"` vs `"Kurt Warner"`; `"Justin Herbery"` vs `"Justin Herbert"`; `"Mitch Trubisky"` vs `"Mitchell Trubisky"`; `"Gardner Minshew"` vs `"Gardner Minshew II"`; `"Michael Penix"` vs `"Michael Penix Jr."`), and (b) one row-level identity corruption -- `qb_source_id 00-0034577` has rows for both `"Kyle Allen"` and `"Cam Newton"` (two different real people; Carolina's 2019 QB change after Newton's injury), and `qb_source_id 00-0035228` has one row reading `"Taysom Kyler Murray"` (an apparent data-merge artifact). **All 7 IDs are fully excluded from this pilot's candidate pool** -- not one row from any of them is used, since there is no Engine-internal way to determine which name (or which person, in the Kyle Allen/Cam Newton case) is correct without external research. This is a `NEEDS_SOURCE_RESEARCH`-equivalent finding for future work, not something this pilot resolves.
- Checked for cross-QB homonym collisions (two different `qb_source_id`s sharing a name in the same season, which could make a distractor look like the correct answer): **zero found**, both within the same team-season and across different teams in the same season.

## Team-alias issues

- 1,580 of 1,587 `qb_team_seasons` rows resolve to exactly one franchise via the **already-corrected** `team_aliases` table from Pilot #1's safe-fix work.
- The 7 unresolvable rows are **all** `team_code='BAL'`, seasons 1999-2001 -- the same `GENUINELY_AMBIGUOUS` code left deliberately blocked in Pilot #1 (it collides with the pre-1984 Baltimore Colts elsewhere in Engine data). These rows are correctly rejected by the same unmodified resolver; no exception was made for them even though, narrowly, 1999-2001 Baltimore was unambiguously the Ravens -- the blocked classification is inherited as-is, not re-litigated here.
- No other blocked code (`LARD`, `LARM`, `BAL1`, `PHO`, `HOU`) appears in `qb_team_seasons` at all -- its 1999+ coverage window starts after every one of those codes' problematic eras ended.

## Ambiguity risks found and handled

| Risk | Found | Handling |
|---|---|---|
| QB traded mid-season (same `qb_source_id`+season, 2 different `team_code`s) | 10 pairs (20 rows) | Excluded -- "which team" has no single correct answer for these |
| Tie for most starts on a team-season | 18 of 861 (relevant only to the un-chosen "who led this team" predicate) | N/A to the chosen predicate |
| QB identity inconsistency | 7 of 347 QBs | Fully excluded, all rows |
| Same-name different-QB collision | 0 | N/A |

## Estimated unique question capacity per usable predicate

- **"Which team did this QB play for in season Y" (chosen):** 1,035 fully-qualified candidate rows across 246 distinct QBs, after every filter above *and* requiring a matching `eligible=1` row in the pre-existing `qb_season` puzzle mode (for Engine-sourced difficulty -- see Step 2). Comfortably supports a 100-question export with room to spare for a larger future run.
- **"Which QB led this team in season Y" (not chosen):** roughly 843 team-seasons (861 minus 18 ties), before applying the same QB-identity-consistency filter -- lower headroom than the chosen predicate for no safety benefit.
- **"Guess the QB from start count" (Engine's existing `qb_season` mode):** 1,081 eligible rows already published by Engine; not re-derived here.

