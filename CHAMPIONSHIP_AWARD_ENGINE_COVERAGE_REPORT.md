# Championship / Award Engine Coverage Report -- Pilot Domain #3

Investigation only, read-only queries against `reads_football_v4.0.sqlite`. No files modified.

## Headline finding: the "objects" named in scope are CFB, not NFL

`v_champion_clues` and `v_award_winner_clues` -- the two views explicitly named in this pilot's
scope -- were inspected directly and are **both CFB-only**:

```sql
CREATE VIEW v_champion_clues AS
SELECT season,school_id,school_name,coach_raw,notes FROM cfb_champion_school_links

CREATE VIEW v_award_winner_clues AS
SELECT award_fact_id,award_id,award_name,award_year,cfb_player_id,player_name,school_id,school_name
FROM cfb_award_facts WHERE player_name IS NOT NULL
```

There is **no NFL award table anywhere in Engine v4** (searched for `%mvp%`, `%poy%`, `%honor%`,
and all `%award%`/`%champ%`/`%super%`/`%bowl%` table names -- every hit is CFB: `cfb_awards`,
`cfb_award_facts`, `cfb_champions`, `cfb_champion_school_links`). This matches the gap already
flagged in Engine's own `PRODUCTION_READINESS.md` ("vetted NFL awards/HOF adapter" listed as
not yet backfilled). **This pilot does not use any CFB award data to answer what is meant to be
NFL trivia** -- that would be a category/domain mismatch, not a safe substitution.

The **championship** half of the domain does have a safe, verified NFL-specific source, described below.

## Production-safe source tables/views

| Object | Type | Rows | Season range | Provenance |
|---|---|---|---|---|
| `season_standings` | table | 800 (296 with non-null `playoff_result`) | 2002-2025 (playoff outcomes present through 2025) | 100% `verification_status='SOURCE_BACKED'`, 100% `source_id='NFLVERSE_DATA'` -- **has row-level provenance columns** |
| `season_records` | table | 800 (same 296 non-null `playoff_result` rows) | 2002-2024 | **No `source_id`/`verification_status` columns at all** -- structurally less verifiable than `season_standings`. Cross-checked: every one of the 22 `WonSB` team/season pairs agrees exactly between the two tables (zero mismatches), so `season_records` is not wrong, just not independently provenance-tagged. `season_standings` is used as the source of record for this pilot because it carries that provenance. |
| `puzzle_catalog` (`mode_id='playoff_result'`) | table | 296 rows, **all 296 eligible=1** | 2002-2025 | Pre-existing Engine-QA'd mode: `{"answer": "LostDV", "prompt": "How did BUF's 2025 postseason end?", "record": "12-5"}`. Joined back to `season_standings` on `(team_code, season)`: **296/296 join, 0 answer mismatches** between the two sources. Used for this pilot's Engine-computed difficulty (same pattern as the QB pilot's use of the pre-existing `qb_season` mode). |
| `puzzle_catalog` (`mode_id='season_record'`) | table | 768 rows | -- | Guess-the-W/L-record mode; not used (a record string like "12-5" isn't itself a championship/award fact) |
| `game_factory_capabilities` | table | 0 rows matching champion/award/super/bowl | -- | Confirmed: no Game Factory predicate exists for championships or awards (full capability list checked: `CFB_ATTENDED`, `CFB_COACHED_AT`, `CFB_CONFERENCE`, `CFB_GAME`, `CFB_RECORD`, `CFB_RIVAL`, `GENERIC_PATH_CFB`, `GENERIC_PATH_NFL`, `NFL_DRAFTED_BY`, `NFL_ORDER_DRAFT`, `NFL_PLAYED_FOR`, `NFL_POSITION`, `NFL_TEAMMATE`) |

### Full `puzzle_catalog` mode inventory relevant to this pilot

Of 43 total `mode_id` values in `puzzle_catalog`, the ones resembling "championship/award" are:
`award_school`, `award_winner`, `cfb_champion_by_year`, `cross_award_before_draft`,
`cross_award_to_draft_team` -- **all confirmed CFB** by sample payload (e.g. `award_winner`:
`{"answer": "Fernando Mendoza", "prompt": "Who won the Heisman Trophy in 2025?"}`). The one
NFL-relevant mode is `playoff_result`, described above.

## Season/year coverage

`season_standings.playoff_result` is populated for seasons **2002-2025**, 296 team-seasons total.
**Season 2023 is missing its Super Bowl outcome specifically**: 2023 has 12 rows with a non-null
`playoff_result` (the full complement of Wild Card/Divisional/Conference-Championship losers), but
zero rows tagged `WonSB` or `LostSB` for that season -- a genuine, confirmed gap in Engine's data,
not a query error (verified by listing every 2023 row directly). Every other season 2002-2022 and
2024-2025 has its outcomes fully populated (2025 has no `WonSB`/`LostSB` yet either, since that
season's playoffs have not concluded as of the data snapshot).

## Verified row counts

- 296 team-season rows with a non-null `playoff_result`, all `SOURCE_BACKED`/`NFLVERSE_DATA`
- Breakdown: `LostWC` 108, `LostDV` 96, `LostCC` 48, `WonSB` 22, `LostSB` 22
- 296/296 resolve to exactly one franchise via `team_aliases` (this domain sits entirely inside
  2002+, which was always covered by `team_aliases` even before Pilot #1's historical extension --
  no code-resolution risk here at all)
- 296/296 join to an `eligible=1` row in the pre-existing `playoff_result` `puzzle_catalog` mode with
  zero answer mismatches

## Available award types

**None usable.** No NFL award/honor table exists in Engine v4. CFB awards (Heisman, etc.) exist but
are out of scope for NFL Quiz content.

## Championship/Super Bowl coverage

22 Super Bowl winners (2002-2022, 2024) and 22 Super Bowl losers/runners-up (same seasons), all
verified, all resolving to the correct season-accurate franchise name. 2023 is the one gap (see above).

## Candidate predicates evaluated

| Predicate | Verdict | Why |
|---|---|---|
| "Which team won the Super Bowl in season Y?" | Usable, but **insufficient volume alone** | Exactly 22 valid rows (one per covered season) -- far short of the 100-question target on its own. |
| "Which team lost the Super Bowl in season Y?" | Usable, same volume ceiling | Also 22 rows; combining both "won" and "lost" framings for the same 22 seasons still only reaches ~44 unique questions. |
| "How did team X finish the season-Y NFL postseason?" (**chosen**) | **USABLE, chosen** | 296 fully-verified rows; each team-season has *exactly one* recorded outcome (no ties/co-winners possible, `season,team_code` is a primary key), and naturally includes the Super Bowl-winner/loser cases as two of its five possible answers. See Step 2. |
| Any NFL MVP/award-winner predicate | **NOT SAFE -- rejected** | No NFL award table exists anywhere in Engine v4. Would require using CFB award data, which is a different sport/domain and would misrepresent itself as NFL trivia. |
| "Which school won the [CFB] national championship in year Y" | **Out of scope** | Real, verified, and already an Engine-published mode (`cfb_champion_by_year`) -- but this is CFB trivia, not NFL, and this pilot (like Pilots #1-2) targets `data/quiz.js`'s NFL-focused contract. Not used. |

## Ambiguity risks

- **None found for the chosen predicate.** `(season, team_code)` is a primary key on `season_standings`, so exactly one `playoff_result` per team-season by construction -- no ties, no co-champions, no disputed outcomes are possible to encounter.
- The *un-chosen* "which team won" direction would have been unambiguous too (exactly one `WonSB` per season), it's simply too low-volume to use alone.
- The genuinely ambiguous direction (which the existing Engine `playoff_result` mode correctly avoids, and which this pilot also avoids) would be "which team lost in the Wild Card round in season Y" as a *reverse* lookup -- up to 6-7 teams share that exact outcome in a single season, so that direction is never used.

## Historical naming/identity issues

None beyond what Pilot #1 already resolved. This domain's full season range (2002-2025) sits
entirely inside `team_aliases`' always-safe window, so no code required extension and no blocked
code (`LARD`/`LARM`/`BAL1`/`PHO`/`HOU`/`BAL`) appears anywhere in this 296-row pool -- confirmed by
a 296/296 resolution rate, not assumed.

## Estimated unique-question capacity by predicate

- **"How did team X finish season Y's postseason?" (chosen):** 296 fully-qualified candidates, comfortably supporting a 100-question export with 196 remaining for a future larger run.
- **"Which team won the Super Bowl in season Y":** 22 max.
- **"Which team lost the Super Bowl in season Y":** 22 max.
- **NFL award-winner (any framing):** 0 -- no source data exists.

## Predicates not safe enough to use, and why

- Any NFL MVP/Offensive-Player-of-the-Year/award framing: **no data exists**, not a safety judgment call -- there is simply nothing to query.
- "Which team reached the Conference Championship in season Y" (or any *reverse* lookup from an outcome shared by multiple teams per season back to "the" team): rejected as inherently ambiguous -- `LostWC`/`LostDV`/`LostCC` are each held by multiple teams in every season.

