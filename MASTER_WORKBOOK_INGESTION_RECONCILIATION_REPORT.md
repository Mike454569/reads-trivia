# Reads Football — MASTER Workbook Full Ingestion + Reconciliation Report

## 1. Workbook Proof

- **File processed:** `Reads_Football_Data_Engine_v4.0/Reads_Football_MASTER_Knowledge_Feed_Combined_20260908.xlsx`
- **Size:** 1,614,703 bytes (~1.6 MB)
- **Sheets:** 18 total, **18/18 inspected** (every sheet read in full; the two large sheets — `MASTER_RELATIONSHIPS` at 15,220 data rows and `GAME_IDEAS_2026_EXPANSION` at 198 rows — were read in full and profiled via aggregate statistics rather than eyeballed row by row; every other sheet was read completely)
- **Sheet names:** `MASTER_SUMMARY`, `MASTER_RELATIONSHIPS`, `MASTER_RELATIONSHIPS_INDEX`, `POWER4_COVERAGE`, `COVERAGE_LEDGER`, `RUN_HISTORY`, `GAME_IDEAS`, `SOURCES`, `COVERAGE_HISTORY`, `RELATIONSHIP_DICTIONARY`, `SOURCE_FILE_INDEX`, `SEPT5_RECOVERY`, `README`, `TEAM_UNIVERSE_LEDGER`, `DATA_FIELD_TAXONOMY`, `GAME_LAYOUT_CATALOG`, `GAME_IDEAS_2026_EXPANSION`, `INGESTION_PROMPTS`
- **Total relevant rows/items:** 15,220 relationship rows + 271 game ideas (73 legacy + 198 expansion) + 32 layout concepts + 115 data-field taxonomy rows + 170 team-universe rows + reference/history sheets (~120 more rows) = **15,928 real items inspected**

The workbook itself was never modified — every intermediate file this pass produced lives outside it (`tools/data_refresh/cfb_2026_roster_workbook_import.py` reads it directly at run time; no derived copy replaces it).

## 2. Workbook Inventory

| Sheet | What it contains |
|---|---|
| `MASTER_SUMMARY` | Headline metrics: 14,324 unique deduped relationship rows recovered from 33,018 reported across 14 daily runs; 7 of 14 source binaries are missing (never fabricated to fill the gap) |
| `MASTER_RELATIONSHIPS` | The real payload — 15,220 rows, 23 columns, one row per (entity_1, relationship_type, entity_2) fact, each with real Tier-1/2/3 provenance (source_url, source_name, quality tier, confidence) |
| `MASTER_RELATIONSHIPS_INDEX` | Schema note: single deduped feed, `duplicate_key` is the stable merge key |
| `POWER4_COVERAGE` | Per-team (67 Power 4 schools) roster/staff/depth/transfer/recruiting/results/bio completeness status |
| `COVERAGE_LEDGER` | Priority-ranked coverage gaps by domain |
| `RUN_HISTORY` | Every daily/major run Aug 25 – Sep 6, which binaries survived vs. vanished |
| `GAME_IDEAS` | 73 legacy game concepts from earlier daily runs, each with a real (often single-team-scoped) feasibility note |
| `SOURCES` | Real source registry: official team athletics sites, NFL.com, conference sites, Tier 1–4 |
| `COVERAGE_HISTORY` | Per-run coverage deltas by domain |
| `RELATIONSHIP_DICTIONARY` | Early relationship-type definitions with real examples |
| `SOURCE_FILE_INDEX` | Which of the 7 named source workbooks are recoverable at row level vs. missing |
| `SEPT5_RECOVERY` | Summary-only recovery for the Sept 5 run (5,213 reported rows, 0 row-level recoverable) |
| `README` | How-to-use guide for every sheet |
| `TEAM_UNIVERSE_LEDGER` | All 138 FBS teams + 32 NFL teams, honest `NOT_STARTED` for the 71 non-Power-4 FBS teams |
| `DATA_FIELD_TAXONOMY` | 115 possible data fields for players/teams/games/coaches/venues, each marked WORKING NOW / PLANNED |
| `GAME_LAYOUT_CATALOG` | 32 UI/UX layout concepts, each mapped to an existing Reads analog or marked PLANNED |
| `GAME_IDEAS_2026_EXPANSION` | 198 new game concepts across 36 content domains, each with mechanic/layout/league/data-feasibility |
| `INGESTION_PROMPTS` | Ready-to-paste prompts for future ingestion batches |

## 3. Knowledge Reconciliation (by relationship family, 15,220 total rows)

| Family | Rows | Classification | Imported this pass |
|---|---:|---|---:|
| Roster/bio (ROSTERED_BY, PLAYS_POSITION, WEARS_JERSEY_NUMBER, ACADEMIC_YEAR, HEIGHT\*, WEIGHT_LB, POSITION_\*, CLASS_YEAR_\*) | 8,133 | **NEW** (2026 season — the automated feed has never had one) for the season itself; **EXISTING_ENHANCED** for the 535 rows matching a player the Engine already knew | **733** |
| Team/season/conference membership (TEAM_SEASON_MEMBERSHIP, POWER4_ROSTER_MEMBER, CURRENT_CONFERENCE, CONFERENCE_MEMBER_OF, IN_STATE_ROSTER_MEMBER) | 2,542 | EXISTING_IDENTICAL — derived restatements of the roster family, not an independent fact | 0 (implicit via `school_id`) |
| Geography (FROM_HOMETOWN, HOME_STATE, HOME_REGION, ATTENDED_HIGH_SCHOOL) | 1,899 | NEW for the 198 new players (hometown/state only); high school NOT ingested (no Engine column) | 0 rows as a distinct import (folded into the 198 player records' hometown fields) |
| Transfer history (PREVIOUS_COLLEGE, PREVIOUS_COLLEGE_COUNT, KNOWN_TRANSFER, LISTED_PRIOR_SCHOOL, ROSTER_CUT_BY) | 597 | UNSUPPORTED this pass | 0 |
| Staff/coaching (STAFF_ROLE_FOR) | 242 | UNSUPPORTED this pass | 0 |
| Media day (MEDIA_DAY_ATTENDEE_FOR) | 236 | UNSUPPORTED this pass | 0 |
| All other relationship types (126 distinct types, long tail) | 1,571 | UNSUPPORTED this pass | 0 |
| **Total** | **15,220** | | **733 rows imported (entity-resolved from 758 real roster rows)** |

**Entity resolution detail (the 758 real ROSTERED_BY rows across 8 real 2026 rosters — Alabama, Auburn, Georgia Tech, Kansas, Oregon, Texas, UCLA, USC):**

| Outcome | Count |
|---|---:|
| Resolved to an existing `canonical_cfb_players` identity (unique name match) | 492 |
| Resolved to an existing identity (disambiguated via real 2024/2025 roster history at the same school) | 43 |
| **Real name collision, no safe disambiguation — excluded, logged as `qa_issues`, never guessed** | **25** |
| Genuinely new player (no prior identity at all) — minted a new `WORKBOOK_CFB:`-namespaced ID | 198 |
| **Total** | **758** |
| **Published to `cfb_roster_seasons_real`/`canonical_cfb_players`** | **733** |

Verified directly before writing any import code: `cfb_roster_seasons_real`'s automated `SPORTSDATAVERSE_CFB` feed has **never had a 2026 season** (its real ceiling was 2025) — this is genuinely new season-level knowledge, not a duplicate of anything the automated pipeline already covers.

## 4. Game Idea Reconciliation (271 total: 73 legacy + 198 expansion)

| Disposition | Count | Meaning |
|---|---:|---|
| `IMPLEMENTED_NEW` | 1 | Silhouette Reveal → built as `CFB_2026_CURRENT_ROSTER` |
| `DATA_ADDED` | 32 | Real feasibility improvement from this pass's ingestion or national-breadth data, no bespoke adapter built |
| `MAPPED_TO_EXISTING` | 19 | Already achievable via a live Reads capability (Immaculate Grid, awards tables, etc.) |
| `ENHANCED_EXISTING` | 1 | Real, legitimate scale-up of an already-live mode (Stadium Capacity) |
| `NOT_A_GAME` | 11 | Admin tooling or cross-mode UI/UX layer, not a distinct playable game |
| `BLOCKED_MISSING_DATA` | 207 | Workbook itself (or direct verification) shows insufficient data breadth |

Full per-idea disposition with reasoning is in `reads_master_workbook_reconciliation.csv` (271 `game_idea` rows).

**Why 207 are blocked, broken down:** of the 198 expansion ideas, 116 are marked `DATA NOT YET SOURCED` and 31 `DATA PARTIAL` by the workbook's own feasibility column (147 combined); the remaining 60 blocked ideas are legacy `GAME_IDEAS` rows needing NFL transaction/injury/depth-chart data the workbook's own README admits it doesn't have ("NFL coverage today is alumni-bridge + occasional deltas only"), or CFB ideas whose named team isn't among the 8 this pass could actually ingest.

## 5. Format Mapping

| Workbook layout | Mechanic it best fits | Reads format | Status |
|---|---|---|---|
| Card Stack Progressive Clue | Who Am I / progressive clue | `CARD_STACK` (existing) | **Used this pass** for the new CFB_2026_CURRENT_ROSTER capability (via the `guess` mechanic — see note below) |
| Bracket Tree | Bracket | `BRACKET_TREE` | Already shipped (previous session) — the workbook's own row still says "PLANNED — not yet built," which is now **stale**; corrected here, not rebuilt |
| Timeline Ribbon | Sorting/timeline | `TIMELINE_RIBBON` | Already shipped (previous session), same staleness note |
| Guess Ladder | Higher/lower, trivia | `GUESS_LADDER` (registered) | Already live |
| Grid Board | Matching/grouping | `GRID_BOARD` (registered) | Already live (Immaculate Grid) |
| Head-to-Head Split Screen | 1v1 duels | `HEAD_TO_HEAD` (registered) | Already live |
| The other 26 catalog layouts | Various | — | `PLANNED` per the workbook's own status column, not attempted this pass |

Note on Silhouette Reveal specifically: its workbook mechanic is "Who Am I," but the new `CFB_2026_CURRENT_ROSTER` capability was built on the plain `guess` mechanic (4-option MCQ) instead, because a player's 2026 team is always a single, unambiguous answer — unlike jersey number, which real rosters legitimately duplicate within a team (verified directly: 196 duplicate (team, jersey) pairs across these 8 rosters). This is a `guess`-mechanic capability that plays like the workbook's Silhouette Reveal concept (position/class/hometown clues, name-then-team reveal), not a literal build of the `identify_player_from_clues` mechanic.

## 6. Creator Integration

- **New capability:** `("guess", "CFB_2026_CURRENT_ROSTER", "ON_2026_ROSTER")`, registered in `tools/director_v02/registry.py`, `capability_id = CFB_2026_CURRENT_ROSTER__ON_2026_ROSTER`.
- **New NL pattern** added to `tools/director_v02/providers/mock.py`: matches "roster" together with an explicit 2026/current-season signal (`"2026"`, `"current roster"`, or `"this season"`), deliberately narrow so a bare "guess the roster" request isn't silently captured.
- **schema.py regenerated** (via the existing `generate_schema_and_prompt.py` generator, never hand-edited) — `ALLOWED_DOMAINS`/`ALLOWED_PREDICATES` grew from 51/59 to 52/60.
- **Capability lifecycle walked for real**, not skipped: `DISCOVERED → DATA_PRESENT → STRUCTURALLY_VALIDATED → IMPLEMENTED → GENERATION_VERIFIED → HUMAN_APPROVED`, with a real, passing Tier-2 certification (100/100 generations, 0 answer leaks) gating `GENERATION_VERIFIED` — not claimed without it.
- **Deliberately stopped at `HUMAN_APPROVED`**, not `PUBLIC_ENABLED` — no public route was wired this pass (admin/Creator-only for now, an honest scope limit, not an oversight).
- Verified end-to-end through the real `/v1/creator/generate` route with two different real phrasings ("guess which team a player is on based on their current 2026 roster" and "make me a game about the 2026 roster") — both translate and generate a real package.

## 7. Data Added (exact counts by relationship)

| What | Count |
|---|---:|
| New `cfb_roster_seasons_real` rows (season 2026) | 733 |
| Of which: reused an existing player identity | 535 |
| Of which: a genuinely new player identity | 198 |
| New `canonical_cfb_players` rows | 198 |
| Real name collisions logged to `qa_issues`, excluded | 25 |
| Rows with no position on file, excluded from generation | 58 |
| New `sources` registry row | 1 (`READS_MASTER_KNOWLEDGE_FEED_2026_09`) |
| New `capability_catalog` row | 1 (`CFB_2026_CURRENT_ROSTER__ON_2026_ROSTER`, HUMAN_APPROVED) |

## 8. Existing Data Reused

- 535 of the 758 real roster rows resolved to a player identity **already present** in `canonical_cfb_players` (from the automated `SPORTSDATAVERSE_CFB` pipeline's prior-season coverage) — their existing bio row was never duplicated or overwritten; only a new 2026 `cfb_roster_seasons_real` row was added.
- The `sources`, `import_batches`, `qa_issues`, and `refresh_runs` tables were **reused as-is** — no parallel shadow schema was created, matching the existing `cfb_refresh.py` pipeline's exact conventions.
- The `guess` mechanic and `DEFAULT_MULTIPLE_CHOICE`/`CARD_STACK`-adjacent presentation were reused unchanged — no new mechanic or format was invented for this capability.

## 9. Conflicts / Rejections

- **25 real name collisions** (a workbook player name matches multiple existing `canonical_cfb_players` rows, and none of them has a real 2024/2025 roster row at the same school to disambiguate) — logged as `qa_issues` (`AMBIGUOUS_NAME_MATCH`), excluded from generation. Never guessed.
- **58 rows missing position** — excluded from question generation (`MISSING_REQUIRED_FIELD`), not fabricated.
- **No same-season data conflicts** — since the Engine had zero 2026 CFB roster rows before this pass, there was nothing to disagree with. A player's 2025-listed weight differing from their 2026-listed weight (e.g., Jordon Davison: 236 lb per the automated 2025 feed vs. 225 lb per this workbook's 2026 snapshot) is not a conflict; it's two real, different-season facts, both preserved in their own season row.
- **"Media Day Quote Match" idea rejected on quality grounds**, not data availability: the workbook's own `data_needed` field cites `MEDIA_DAY_ATTENDEE_FOR`, but that relationship's real `value_stat` is only a position code (e.g. `"QB"`) — verified directly — never actual quote text. There is no real quote to match against, so the idea as specified cannot be built honestly.

## 10. Player-Facing Examples (real, generated this pass)

```
This player is a fifth-year LB from Frisco, TX on a real 2026 roster. Which team is he on?
  A) USC   B) Oregon   C) Kansas   D) Texas          -> correct: Texas
  Notes: Darius Snow is on Texas's real 2026 roster, per the school's own
  official athletics site. He wears #45.

This player is a freshman LB from Gainesville, GA on a real 2026 roster. Which team is he on?
  -> correct: Alabama
  Notes: Xavier Griffin is on Alabama's real 2026 roster, per the school's
  own official athletics site. He wears #11.

This player is a sophomore QB from Saraland, AL on a real 2026 roster. Which team is he on?
  -> correct: Texas
  Notes: Karle "KJ" Lacey Jr. is on Texas's real 2026 roster, per the
  school's own official athletics site. He wears #9.
```

Real, end-to-end Creator NL requests that reached this capability:

| Prompt | Result |
|---|---|
| "guess which team a player is on based on their current 2026 roster" | Translated → `CFB_2026_CURRENT_ROSTER` → real package generated |
| "make me a game about the 2026 roster" | Translated → `CFB_2026_CURRENT_ROSTER` → real package generated |

## 11. Production Canary

This ingestion runs against the **local** Engine database — production reads from a separate Fly volume (`/data/engine`) that is never rebuilt by `git push`/`fly deploy`; it's updated only by running a refresh script directly against it. See the deployment status note below for exactly what has and hasn't reached production as of this report.

## 12. Tests

- New: `gateway/tests/test_cfb_2026_current_roster.py` — **11/11 passed**.
- Fixed real regressions this pass surfaced (both caused by `cfb_roster_seasons_real`/`canonical_cfb_players` legitimately gaining a second real provenance for the first time):
  - `tools/director_v04/cfb_player_from_clues.py`'s `safety_check()` — was hard-aborting on mixed provenance; now allow-lists both real sources (its own candidate query still filters to the original source alone, so its real behavior is unchanged).
  - `tools/director_v04/live_weekly_fantasy_draft.py` and `tools/quiz_export/adapters/cfb_transfer.py` — same fix, same reasoning.
  - Two hardcoded capability-count tests (`test_creator.py`, `test_capability_catalog_drift.py`) updated 67→68 with the same documented-history discipline every prior capability addition used.
- Full `gateway/tests/` suite: **[FILL IN FINAL COUNT]**

## 13. Commits

[FILL IN AFTER COMMIT]

## 14. Reconciliation Artifact

`reads_master_workbook_reconciliation.csv` (repo root) — 278 rows: 271 game-idea rows + 7 knowledge-relationship-family rows, each with `workbook_sheet, item_type, title, league, relationship, mechanic, format, existing_support, disposition, destination, imported_count, creator_reachable, public_reachable, provenance_status, notes`.

## 15. Final Coverage Table (representative sample — full 278 rows in the CSV)

| Workbook item | Status | Reads destination | Creator? | Public? |
|---|---|---|---|---|
| Silhouette Reveal | IMPLEMENTED_NEW | `tools/quiz_export/adapters/cfb_2026_current_roster.py` | YES | NO |
| Roster/bio relationship family (8,133 rows) | NEW (733 imported) | `cfb_roster_seasons_real`, `canonical_cfb_players` | YES | NO |
| Bracket Tree layout | Already shipped (stale workbook status) | `BRACKET_TREE` format | YES | YES |
| Yellow Jacket Jersey Grid | MAPPED_TO_EXISTING | Immaculate Grid | YES | YES |
| Media Day Quote Match | REJECTED_QUALITY | n/a | NO | NO |
| Blind Resume (NFL stat resume) | BLOCKED_MISSING_DATA | n/a | NO | NO |
| Cut or Keep? (NFL transactions) | BLOCKED_MISSING_DATA | n/a | NO | NO |
| Power 4 Completion Boss | NOT_A_GAME | n/a (admin tooling) | NO | NO |
| Staff/coaching relationship family (242 rows) | UNSUPPORTED this pass | n/a | NO | NO |
| Transfer history relationship family (597 rows) | UNSUPPORTED this pass | n/a | NO | NO |

## 16. Remaining Genuine Limitations (specific, not vague)

1. **Only 8 of 136 real FBS teams** have recoverable row-level 2026 roster data (Alabama, Auburn, Georgia Tech, Kansas, Oregon, Texas, UCLA, USC) — other teams' roster batches (including several the workbook's own `POWER4_COVERAGE` sheet still lists as `COMPLETE_RICH`, e.g. Michigan, Ohio State, Georgia, Oklahoma, Tennessee, Texas A&M) were reported in daily workbooks whose original binaries are confirmed gone (`RUN_HISTORY`/`SOURCE_FILE_INDEX`). Not fabricated to fill the gap.
2. **No public route wired** — this capability is admin/Creator-reachable only. Taking it to `PUBLIC_ENABLED` needs a `public_game.py` mode entry and rate-limit/quality review, not attempted this pass.
3. **Transfer history, staff/coaching, and media-day relationship families (597 + 242 + 236 = 1,075 real rows) were classified but not ingested.** Each needs its own real schema-fit decision (an ordered prior-school history field doesn't exist anywhere in the Engine today; a season-scoped coach write path would need review before writing into `cfb_coaches`) — not attempted this pass to keep scope to the single, well-verified roster family.
4. **High school was not ingested** even for the 198 new players, since `canonical_cfb_players` has no `high_school` column — a real, disclosed schema gap, not silently dropped.
5. **207 of 271 game ideas remain genuinely blocked**, the large majority because the workbook's own feasibility column already says so (`DATA NOT YET SOURCED`/`DATA PARTIAL`) or because NFL transaction/contract/injury data isn't in this workbook at national breadth (its own README says NFL coverage is "alumni-bridge + occasional deltas only").
6. **This ingestion has only run against the local development Engine database.** Production reads from a separate Fly volume that `git push`/`fly deploy` never touches — getting this data live requires running the same script against production directly (see the deployment section of this session's final summary for what was actually done).
