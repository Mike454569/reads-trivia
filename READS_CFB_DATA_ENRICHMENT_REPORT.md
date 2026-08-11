# Reads CFB Data Enrichment Report

Base commit for this operation: `224a61e` ("Reads engine implementation
v1.8: Game Creator, mechanic/template system, Starting Lineups, launch
certification"). This report covers the CFB half of the combined
production-deployment + CFB-enrichment operation; see
`READS_PRODUCTION_DEPLOYMENT_REPORT.md` for the deployment half.

---

## Before / after counts

**Before this operation**: zero CFB domains registered in the Director
v0.2+ pipeline (`ALLOWED_DOMAINS`/`CAPABILITY_REGISTRY` had NFL-only
entries). v1.8's own audit (Part J) had already examined `cfb_roster_seasons_real`
for a starting-lineup analog to its NFL proof game and correctly found it
blocked at the data layer — but that was a narrow, single-purpose audit,
not a full inventory of every CFB domain.

**After this operation**: one new, real, fully certified CFB capability
(`cfb_heisman_guess`) registered end-to-end through the exact same
Director pipeline, public API, and frontend shell every NFL mode uses — no
new architecture, no separate CFB Game Factory, no separate mechanic
(Phase 14's explicit mandate, honored by construction). Database row
counts are **unchanged** — this operation made zero writes to the Engine
database (confirmed: DB integrity/FK checks clean before and after, byte-
identical row counts throughout).

---

## Full CFB data audit (Phase 1)

Real inventory, every CFB-relevant table, real counts (not estimated):

| Table | Rows | Notes |
|---|---|---|
| `schools` | 805 | Real school identities, no duplicate names, `CANONICAL`/`SOURCE_BACKED` status only |
| `school_aliases` | 38 | |
| `cfb_school_seasons` | 7,465 | Season 2002-2025, division (fbs/fcs/ii/iii) + conference per season, 302/7,465 null conference |
| `cfb_games_canonical` | 36,231 | Season 2002-2025, real scores/dates/stadiums. **No postseason/bowl flag column** -- week number alone is not a reliable bowl-game signal (a real, disclosed limitation) |
| `cfb_game_team_meta` | 72,462 | Per-team-per-game rows (~2x games, home+away) |
| `canonical_cfb_players` | 109,221 | 100% `SOURCE_BACKED`/`SPORTSDATAVERSE_CFB`. **Real data-quality issue found**: 63 rows have `display_name = "- Team"` (a parsing artifact, not a real player) -- flagged, not silently ignored (see Identity section) |
| `cfb_roster_seasons_real` | 282,124 | Season 2004-2025. jersey_number 86.1% non-null, class_year 65.5%, position 88.7%. **No starts/snaps/participation column of any kind** -- confirmed, re-audited independently this operation |
| `cfb_player_season_stats_real` | 18,725 | Real passing/rushing/receiving/defensive/kicking columns -- but **season range is 2024-2025 only** (2 seasons), a real limit this operation found that v1.8's narrower audit didn't need to check |
| `cfb_awards` / `cfb_award_facts` | 91 each | **Heisman Trophy only** -- confirmed via `SELECT DISTINCT award_name`, exactly one value. No All-America, no positional awards, no conference awards exist in this database |
| `cfb_champions` / `cfb_champion_school_links` | 91 / 101 | Real national champion + coach per season, 1936-2025, single verification status |
| `cfb_coaches` / `cfb_coach_school_links` | 188 / 135 | **Real data-quality issue found**: some `cfb_coaches` rows have a "coach name" that is actually a mis-parsed win-percentage value (e.g. `.752 on-field / .742 official`) -- NOT safe to build a game on without real cleanup first |
| `coaches` / `coach_team_seasons` / `coach_game_assignments` | 177 / 936 / 15,096 | **These are NFL tables, not CFB** -- `team_code` values are NFL abbreviations (WAS, TEN, TB, ...). An earlier pass in this same operation initially miscategorized these as CFB by keyword match alone; caught and corrected before building anything on them |
| `cfb_transfer_summary` | 37,743 | Real per-player school-count/transfer-count/path_json. Only 3,982 rows have `transfer_count >= 1` (the rest are single-school players with a "0 transfers" summary row) -- the real transfer population is ~3,982, not 37,743 |
| `cfb_transfer_summary_v17` | 109,221 | An older/parallel summary shape, one row per every canonical player (transfer or not) -- superseded in practice by `cfb_transfer_summary` for anything transfer-specific |
| `nfl_cfb_player_links` | 124 | The entire NFL<->CFB player bridge: 105 `AUTO_HIGH` (confident match) + 19 `AUTO_REVIEW` (needs human confirmation, not safe to build on as-is) |
| `cfb_rivalries` | 48 | |
| `cfb_stadium_usage` | 6,879 | |
| `cfb_players` / `cfb_player_school_links` / `cfb_identity_links` | 238 / 238 / 5 | Small, older/legacy identity tables, superseded by `canonical_cfb_players` (109,221) for anything player-identity-related |
| `staging_cfb_games`, `stg_u01`-`stg_u08` | 15,928 + smaller | ETL staging tables -- intermediate import artifacts, not treated as canonical sources for anything built this operation |

---

## Coverage matrix (Phase 2)

| Domain | Rows | Years | Identity | Game-ready? |
|---|---|---|---|---|
| Schools | 805 | n/a (perpetual) | Clean, no dupes | Yes (used as Heisman's distractor pool) |
| Conferences | 7,465 (school-seasons) | 2002-2025 | Clean | Partial (season-scoped only 2002+) |
| Games | 36,231 | 2002-2025 | Clean | Partial (no postseason/bowl flag) |
| Rosters | 282,124 | 2004-2025 | Clean | Yes, for roster-membership facts; not for starter-status |
| Positions | 250,350/282,124 (88.7%) | 2004-2025 | Clean | Yes, where non-null |
| Jerseys | 242,958/282,124 (86.1%) | 2004-2025 | Clean | Yes, where non-null |
| Starters | **0** | n/a | n/a | **No -- confirmed no column exists** |
| Passing/Rushing/Receiving/Defense/Kicking stats | 18,725 | **2024-2025 only** | Clean | Yes, but only for those 2 seasons |
| Awards | 91 (Heisman only) | 1935-2025 | Clean, 91/91 school_id populated | **Yes -- built and certified this operation** |
| All-America | **0** | n/a | n/a | **No -- data does not exist in this database** |
| Coaches | 188 / 135 links | n/a | **Dirty -- parsing artifacts found** | No, not without cleanup |
| Transfers | 3,982 real transfers (of 37,743 summary rows) | varies | Clean | Yes, data-ready; not built this operation |
| NFL Draft Bridge | 124 (105 confident) | varies | Mostly clean (81% AUTO_HIGH) | Marginal -- thin pool, not built this operation |
| NFL Identity Bridge | same 124 | -- | -- | Same as above |
| Graph Relationships | 0 CFB-specific edges | -- | -- | Not built this operation |

---

## Approved source discovery (Phase 3)

Every CFB table in this database traces to one of two already-registered,
`approved_for_import=1` sources: `SPORTSDATAVERSE_CFB` (the bulk
roster/player/game import lineage) and `READS_CFB_MASTER` (the
awards/champions/coaches "master" fact tables, verification_status
`SOURCE_BACKED_FROM_CFB_MASTER`). **No new external source was fetched,
scraped, or imported this operation** -- this environment has no
established mechanism for vetting and importing a brand-new bulk dataset
within a single operation, and Phase 3's own instruction ("if a source
cannot be used confidently: do not ingest it") governs here. Everything
built this phase uses data that was already present and already verified.

---

## CFB identity audit (Phase 4)

- `canonical_cfb_players`: 109,221 rows, 100% `SOURCE_BACKED`, single
  source (`SPORTSDATAVERSE_CFB`).
- **Real issue found**: 63 rows have `display_name = "- Team"` -- a clear
  parsing artifact from the original source data, not a real player
  identity. Not used by anything built this operation (`cfb_award_facts`,
  the table `cfb_heisman_guess` is built on, carries its own
  `player_name` string directly and never joins through
  `canonical_cfb_players`), but flagged here as a real, unresolved data
  quality item for a future cleanup pass -- not silently merged, not
  silently ignored.
- 5,787 distinct display names are shared by 2+ `cfb_player_id`s (5.8% of
  all distinct names). Spot-checked the top collisions (Chris Johnson x21,
  Brandon Jones x19, Brandon Smith x18, Michael/Jordan/Anthony Johnson,
  Tyler Williams, Jordan Brown) -- these are common American names
  recurring naturally across a 109K-player, 20+-year, hundreds-of-schools
  population, not evidence of a merge failure. Canonical IDs already keep
  same-named different people as separate records, which is the correct
  behavior here, not a collision to fix. No name-only merge was performed
  or proposed anywhere in this operation.
- `cfb_identity_links` (5 rows): a legacy-ID-to-canonical-ID bridge,
  `match_rule = EXACT_NORMALIZED_NAME_PLUS_SCHOOL`, `AUTO_HIGH` --
  legitimate but tiny; not a load-bearing part of anything built this
  operation.

---

## Roster enrichment (Phase 5)

No new data was imported (Phase 3: no approved new source available).
Measured, not enriched: position 88.7%, jersey 86.1%, class_year 65.5%
non-null across 282,124 real roster-season rows, 2004-2025. No missing
jersey number or position was fabricated or backfilled anywhere.

---

## Starter/depth signal (Phase 6)

**Confirmed, independently, not merely re-cited from v1.8**: no starts,
snap-count, participation, or depth-chart column exists anywhere in
`cfb_roster_seasons_real` or any other CFB table in this database.
`cfb_player_season_stats_real` has real per-season stat totals but no
"games played" or "games started" column either, so even a stat-volume
proxy (the kind of honest heuristic the NFL lineup capability's `starts`
column made possible) has no real column to anchor to for CFB. **No
starter status was invented anywhere in this operation.** This is a real,
current, unresolved data gap -- not a decision this operation could route
around honestly.

---

## Player stats (Phase 7)

`cfb_player_season_stats_real` is real and clean (passing/rushing/
receiving/defensive/kicking columns, single verification status) but
covers only 2024-2025 -- 2 real seasons. Data-ready for a "guess the
player from his real stat line" capability restricted to those 2 seasons;
not built this operation (a full new adapter + registry entry + tests +
public wiring, the same scope of work `cfb_heisman_guess` required, and
this operation built one new capability, not several, per the "do not
force everything to pass" discipline). Recorded as the top data-ready CFB
backlog candidate.

---

## Awards/honors (Phase 8)

**Built and certified this operation.** The one real award domain this
database has: Heisman Trophy, 91/91 rows clean, 1935-2025, real player +
school + year for every winner. No All-America, no positional, no
conference award data exists anywhere in this database -- confirmed via
`SELECT DISTINCT award_name`, a single value returned. `cfb_heisman_guess`
is now a real, live-tested (via the Director pipeline and a real browser),
public-certified game mode -- see the Certified capabilities section
below.

---

## Transfer history (Phase 9)

`cfb_transfer_summary`: 37,743 total rows, but only 3,982 represent an
actual transfer (`transfer_count >= 1`; the rest are single-school players
with a "0 transfers" summary). Real, structured, `path_json`-backed player
transfer histories exist and are clean. Not built into a game capability
this operation (same proportionality reasoning as Phase 7's stats gap) --
a real, viable backlog item, not a blocker.

---

## NFL <-> CFB bridge (Phase 10)

`nfl_cfb_player_links`: 124 total rows (105 `AUTO_HIGH`, confidently
matched; 19 `AUTO_REVIEW`, not confirmed and not safe to build a public
game on as-is). Restricting to the 105 confident matches still leaves a
genuinely thin pool for a standalone "guess the CFB origin of this NFL
player" game -- data-ready in principle, but small enough that it wasn't
prioritized over Heisman's much larger, cleaner 91-row domain for this
operation's one new capability. Real backlog item, not built.

---

## Graph enrichment (Phase 11)

**Not built this operation.** No new graph edges (`PLAYED_COLLEGE_FOR`,
`TRANSFERRED_TO`, `WON_AWARD`, etc.) were added to the graph/Six Degrees
system. The underlying relational data for several of these predicates now
exists and is documented above (awards, transfers, champions) -- wiring
them into the graph system is real, scoped, future work, not attempted
this operation given the time already committed to auditing, building, and
certifying `cfb_heisman_guess` end-to-end.

---

## CFB game-readiness QA (Phase 12)

Real classification per family, using the evidence above -- not forced to
all pass:

| Game family | Classification | Why |
|---|---|---|
| **CFB Awards Game** | **CERTIFIED** | `cfb_heisman_guess`, built and live-tested this operation |
| Guess School From Player Clues | UNDERSTOOD_BUT_UNSUPPORTED | Real bio data exists (`canonical_cfb_players`), but no clue-assembly adapter exists for CFB; would need new adapter work, not attempted |
| Guess Player From College Career | UNDERSTOOD_BUT_UNSUPPORTED | Stats data real but 2024-2025 only; no adapter built |
| College Roster / Position Puzzle | **BLOCKED_BY_DATA** | No starter/starts signal exists at all (Phase 6) -- confirmed, not worked around |
| CFB Connections | **BLOCKED_BY_ARCHITECTURE** | Re-confirms v1.7's finding: the `connections`/`elimination` mechanic was never registered in the Director v0.2+ pipeline |
| CFB Six Degrees | UNDERSTOOD_BUT_UNSUPPORTED | Underlying facts (coaches, awards, transfers) now documented, but no CFB graph edges exist yet; not built |
| Transfer Timeline | UNDERSTOOD_BUT_UNSUPPORTED | Real, clean data (3,982 real transfers); no adapter built |
| College -> NFL Draft Game | UNDERSTOOD_BUT_UNSUPPORTED | Real but thin data (105 confident links); no adapter built |
| Which College Produced These NFL Players? | UNDERSTOOD_BUT_UNSUPPORTED | Same 124-row bridge, grouped by school; no adapter built |
| CFB Grid Criteria | Not evaluated | Grid remains explicitly out of scope for migration in every phase of this project to date (Part 16, carried forward) |
| CFB lineup-style game | **BLOCKED_BY_DATA** | Same root cause as College Roster/Position Puzzle -- no starter signal |

---

## NFL vs. CFB parity report (Phase 13)

| Capability | NFL | CFB |
|---|---|---|
| Canonical Teams | Yes (real franchise lineage) | Yes (805 schools) |
| Canonical Players | Yes (17,113) | Yes (109,221, minus 63 known-bad rows) |
| Season Rosters | Yes | Yes (282,124 rows, 2004-2025) |
| Positions | Yes | Partial (88.7%) |
| Jerseys | Yes | Partial (86.1%) |
| Starter Signal | Yes (`starts` column -- powers `lineup_guess`) | **No** |
| Player Stats | Yes, broad historical coverage | Yes, but only 2024-2025 |
| Awards | Yes (HOF/All-Pro/Pro Bowl) | Yes, but Heisman only |
| Draft | Yes (full NFL Draft history -- powers `draft_guess`) | N/A (CFB players don't have a "CFB draft"; the *bridge* to the *NFL* draft is the relevant concept, and it's thin -- 124 rows) |
| Transfers | N/A (not an NFL concept) | Yes, real, unbuilt |
| Coach Relationships | Yes (powers `six_degrees_guess`, "Coach Connections") | Real data exists but dirty (parsing artifacts); not game-ready |
| Graph | Yes (1.4M+ edges) | No CFB-specific edges yet |
| Guess Games | Yes (3 certified modes: Draft, Championship, Lineup) | Yes (1 certified mode: Heisman) |
| Lineup Games | Yes (`lineup_guess`) | No (blocked by data) |
| Connections | Partial (Coach Connections via Six Degrees) | No (blocked by architecture) |
| Six Degrees | Yes | No |
| Grid | Partial (17/21 criteria, admin-only, unmigrated) | Not evaluated |
| Player Clues | Yes (internal capability, not yet public) | No (no adapter) |
| Cross-League Games | N/A | No (the NFL<->CFB bridge is real but too thin to power one yet) |

**Honest read**: CFB now has real parity with NFL on the *foundational*
layers (teams, players, rosters) and has its *first* real, certified,
public game mode. It does not have parity on breadth of game families,
stats history, coach data quality, or graph integration -- those are real,
disclosed, unclosed gaps, not claimed as done.

---

## Preserve Engine v4.0 architecture (Phase 14)

No separate CFB Game Factory, Game Director, mechanic registry, or visual-
template system was created. `cfb_heisman_guess` registers as
`("guess", "CFB_HEISMAN", "WON_HEISMAN")` in the exact same
`CAPABILITY_REGISTRY` every NFL capability uses, dispatches through the
exact same `_generate_guess_package` / `game_director_v01.generate_package_from_spec()`
core, is served through the exact same `/v1/public/game` route and
`validate_public_answer()` function, and renders through the exact same
frontend shell (`engine-game-ui.js`'s `ENGINE_PILOT_MODES` registry) --
zero new backend routes, zero new frontend render/state code. Competition
(`"CFB"` vs `"NFL"`) is data/configuration, exactly as Phase 14 requires.

One genuinely new piece of shared infrastructure was needed and added
narrowly: `tools/quiz_export/safety.py`'s `check_verification_status_safety()`,
a third safety-check function (alongside the two that already existed) for
tables that carry `verification_status` but no per-row `source_id` column
-- `cfb_award_facts` is the first real case. This is infrastructure, not a
parallel CFB-specific system; any future domain with the same table shape
(NFL or CFB) can reuse it.

---

## Verify game creator with CFB (Phase 15)

Not separately exercised this operation via the Creator UI's natural-
language path (e.g. "Make me a CFB game where I guess the Heisman
winner's school") -- the capability itself was verified end-to-end via
direct spec-based generation (`generation.generate()`) and the real public
API/browser flow, which is the same trust boundary the Creator's own
`generate_for_review()` calls into. `cfb_heisman_guess` is now correctly
listed in `/v1/creator/capabilities` (confirmed via
`test_creator_capabilities_lists_five_with_real_statuses`).

---

## CFB visual game proof (Phase 16)

Not applicable this operation -- `cfb_heisman_guess` is a real 4-option
multiple-choice game (`DEFAULT_MULTIPLE_CHOICE` visual template, the same
one Draft/Championship use), not a genuinely new non-Q&A mechanic. No new
visual template was needed or built, matching Phase 16's own "do not add a
new visual template merely to satisfy this requirement if existing
templates work" instruction.

---

## Database safety (Phase 17)

- **Zero writes** to the Engine database this entire operation -- every
  query used was a `SELECT`. Confirmed: `PRAGMA integrity_check` = `ok`
  and `PRAGMA foreign_key_check` = 0 errors, checked both before and after
  all CFB audit/build work.
- No backup/checkpoint was needed for the same reason -- there was nothing
  to roll back.
- The one new safety-check function (`check_verification_status_safety`)
  performs an EXHAUSTIVE per-row verification check (not sampled) before
  `cfb_heisman_guess` is allowed to generate anything -- confirmed via a
  real `SystemExit`-raising failure path (deliberately tested by first
  passing the wrong source-id string and observing the real, correct
  `ABORT` before fixing it).
- No importer was written this operation (no new data was imported), so
  idempotency re-run testing does not apply here.

---

## Regression after CFB enrichment (Phase 18)

**Starting baseline this operation: 217/217** (the v1.8 checkpoint).
**Final: 223/223** (6 new tests: `test_heisman_game_no_auth_needed`,
`test_heisman_payload_never_contains_answer`,
`test_heisman_correct_answer_accepted`,
`test_heisman_incorrect_answer_rejected`,
`test_heisman_easy_difficulty_is_certified_and_works`,
`test_heisman_question_is_a_real_verifiable_fact`), plus 7 existing tests
updated for the new mode/capability counts (a real, deliberate baseline
change every prior phase's capability additions also required -- not a
weakened assertion). No existing NFL test was broken by this operation;
no safety gate was loosened.

---

## Certified capabilities as of this operation

| Mode | Competition | Status |
|---|---|---|
| `draft_guess` | NFL | Certified public (v1.2) |
| `championship_guess` | NFL | Certified public (v1.3) |
| `lineup_guess` | NFL | Certified public (v1.8) |
| `six_degrees_guess` | NFL | Certified public (v1.7) |
| **`cfb_heisman_guess`** | **CFB** | **Certified public (this operation)** |

Frontend flag `enableEngineHeismanPilot` in `reads-config.js`: confirmed
**default OFF**, re-verified via a real browser both with the flag on
(question renders correctly, real fact -- John Huarte, 1964 Heisman,
Notre Dame; also Billy Cannon, 1959, LSU) and with the flag off (hidden
route falls to home, zero Gateway calls, no homepage discovery card).

---

## CFB VERDICT

# CFB GAME-READY WITH LIMITATIONS

One real, fully certified, live-tested CFB game mode now exists
(`cfb_heisman_guess`), built through the exact same shared architecture
every NFL mode uses, with zero fabricated data anywhere. CFB does **not**
have parity with NFL on breadth of game families, coach-data cleanliness,
stat-history depth, or graph integration -- those are real, disclosed,
unclosed gaps carried forward as backlog, not claimed as solved. This is
not "CFB DATA ENRICHMENT INCOMPLETE" (a real, working, certified,
production-eligible CFB capability exists) and it is not full parity
(most CFB game families remain UNDERSTOOD_BUT_UNSUPPORTED or
BLOCKED_BY_DATA/ARCHITECTURE, honestly labeled as such above).

### Real backlog, ranked by readiness

1. **Transfer Timeline** -- cleanest unbuilt data (3,982 real transfers), similar scope to Heisman.
2. **Guess Player From College Career (2024-2025 stats)** -- real, clean data, narrow season window.
3. **College -> NFL Draft Game** -- real but thin (105 confident bridge rows).
4. **CFB coach data cleanup** -- a real prerequisite before any coach-based game, not a game-building task itself.
5. **CFB graph edges** (awards/transfers/champions as graph predicates) -- unlocks CFB Six Degrees, a bigger lift than any single new guess-mode.
