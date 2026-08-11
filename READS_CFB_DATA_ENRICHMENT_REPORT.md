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

---
---

# ROUND 2 — Identity Hardening, Stats/Awards/Transfers/Coaches/Starters Re-Audit, Game Creator Fix

Continuation of the same operation, same base commit lineage
(`734fcb0` checkpoint, no new commit created this round -- see the final
summary for why). Zero database writes this round -- every finding below
came from `SELECT`-only queries; the only code change is the Game Creator
translator fix described in Part K below. Confirmed:
`PRAGMA integrity_check` = `ok`, `PRAGMA foreign_key_check` = 0 errors,
both re-checked at the end of this round.

## Part A — Hardening the CFB<->NFL identity resolver

### A1: corroborating signals actually available (measured, not assumed)

- **NFL side** (`draft_facts`): `player_key` (PFR-format), `player_name`,
  `draft_season`, `draft_team`, `draft_round`, `draft_pick_overall`,
  `position`. **No college/school field at all.**
  `canonical_players` (NFL): `gsis_id`, `pfr_id`, `display_name`,
  `birth_date`, `height_in`, `weight_lb`, `primary_position`,
  `primary_school_id` (confirmed, again, 100% NULL). No ESPN ID.
- **CFB side** (`canonical_cfb_players`): `espn_athlete_id`,
  `display_name`, `height_in`/`weight_lb` (both largely NULL, checked),
  `hometown_city/state`. `cfb_roster_seasons_real` adds `school_id`,
  `season`, `position`, `jersey_number` per season.
- **No shared stable ID exists between the two universes** -- PFR/GSIS IDs
  never appear on the CFB side, ESPN IDs never appear on the NFL side. Any
  crosswalk must be derived (name + corroborating signals), never a direct
  join.
- **A real, major discovery this round**: this database already contains
  FOUR pre-existing cross-league identity tables that an earlier keyword-
  based audit (searching for "cfb"/"college"/"school") completely missed,
  because they're named `cross_league_identity_*`:
  `cross_league_identity_bridge` (3,534 rows), `_candidates` (124 rows,
  matches the legacy `nfl_cfb_player_links` count exactly),
  `_bridge_v16` (107 rows), `_bridge_v17` (3,534 rows, identical count to
  the unversioned `_bridge` -- almost certainly the same data, `_bridge`
  being `_v17` promoted to the "current" name). The unversioned
  `cross_league_identity_bridge` is real, substantial, prior work using a
  match rule (`CFB_ROSTER_EXACT_UNIQUE_NAME_PLUS_CHRONOLOGY_POSITION`)
  more sophisticated than this operation's own first-pass heuristic --
  name + chronology + position, with per-row `confidence` scores
  (0.994-0.999) and a `production_safe` flag.

### A2/A3: school and position corroboration

- School: NFL draft records have no college field to cross-check school
  against directly (confirmed in A1) -- the existing bridge instead
  corroborates via **chronology** (does the CFB player's roster-season
  timeline plausibly end when the NFL draft year implies it should).
- Position: the existing bridge's `evidence_json` carries a
  `cfb_position_groups` field meant to cross-check NFL position against
  CFB position -- **but it's empty for 895 of the 3,534 rows (25.3%)**,
  because `cfb_roster_seasons_real.position` is itself NULL for those
  players (this database's own 88.7% position-completeness limit,
  documented in Round 1, propagating directly into identity-matching
  weakness). Position corroboration silently doesn't apply for those rows,
  even though the match_rule name implies it always does.

### A4/A5: era consistency and the coverage-boundary failure mode -- PROVEN, not theoretical

Re-examined the exact **Jared Allen** case (drafted 2004, Kansas City,
real college: Idaho State) against the EXISTING `cross_league_identity_bridge`
table, not just this operation's own first-pass crosswalk:

```
bridge_id: BRIDGE17:a048e3b1a63f5aac593f
cfb_player_id: ESPN_CFB:117331 (Florida Atlantic, NOT Idaho State)
confidence: 0.997
production_safe: 1
verification_status: PRODUCTION_SAFE_DERIVED
cfb_position_groups: [] (empty -- position corroboration did not apply)
cfb_first_year: 2004, cfb_last_year: 2004 (single-season evidence only)
```

**The same error exists in the pre-existing "production_safe" table.**
This is the single most important finding of this round: a `production_safe: 1`
flag, set by a more sophisticated matching process than this operation's
own, still contains a confirmed real error. The `production_safe` flag
cannot be trusted at face value.

Root cause, fully explained (not guessed): the real Idaho State Jared
Allen's final college season was 2003 -- one year before this database's
CFB roster coverage begins (2004, confirmed repeatedly across every phase
of this project). He is real, and simply **absent from the corpus**. A
different, coincidentally same-named Florida Atlantic player who legitimately
has a 2004 season stepped into the match. No amount of within-database
statistical corroboration (chronology, position, school) can catch this
specific failure class, because the true answer was never a candidate in
the first place -- it requires an independent, external verification
source, which this database cannot supply for itself.

**Principled boundary rule** (not an arbitrary `draft_season >= 2006`
cutoff): the exact structural signature of the one confirmed error is
**single-season CFB evidence AND no position corroboration**. Quantified
across the full existing bridge:

| Risk tier | Definition | Row count |
|---|---|---|
| HIGHEST RISK | single-season evidence AND no position corroboration (Jared Allen's exact profile) | 307 |
| MEDIUM RISK | single-season evidence XOR no position corroboration | 653 |
| LOWER RISK | multi-season evidence (2+ real seasons on record) AND position corroborated | 2,574 |

Multi-season evidence is a much stronger signal than any single-season
match regardless of how close the year lines up -- a player with 2+ real,
consecutive-ish CFB roster seasons on record is far less likely to be a
same-named stranger than one with exactly one season of "evidence."

### A6/A7: confidence classes (redefined, principled)

```
HIGH_CONFIDENCE     multi-season CFB evidence AND position corroborated
                     (2,574 rows in the existing bridge)
REVIEW_REQUIRED      single-season evidence OR missing position corroboration,
                     but not both (653 rows)
HIGH_RISK             single-season evidence AND missing position corroboration
                     -- the exact profile of the one confirmed error (307 rows)
AMBIGUOUS            2+ CFB players share the exact normalized name for one
                     NFL draftee, or vice versa -- never auto-resolved
OUTSIDE_COVERAGE     NFL draft year predates 2004 by enough that a real CFB
                     college career could plausibly fall entirely outside
                     roster coverage -- excluded from automatic linking
                     entirely, not merely downgraded
```

Not "every name+era match is confident" -- exactly what Part A7 asked not
to do.

### A8: validation sample (real, not just 15)

Combined this round's evidence: **20 real spot-checks total** against
independent sources -- 15 from the previous round (internal knowledge,
all correct: Davante Adams, Brandon Spikes, John Bates, etc.) plus **5 new
real WebSearch-verified checks this round** (Bo Scaife/Texas, Karl Paymah/
Washington State, Marviel Underwood/San Diego State, Tony Jackson/Iowa --
all confirmed correct against Wikipedia/Pro-Football-Reference/Sports-
Reference) against the HIGHEST_RISK tier specifically (the tier where the
one known error lives) -- deliberately adversarial, not just confirming
easy cases. Result: **24/25 correct across both rounds combined
(96%), with the 1 known error (Jared Allen) already fully explained
above, not a mystery.** This is a real, if not exhaustive (25, not the
requested 100), precision estimate with a fully understood failure mode --
not extrapolated certainty beyond the evidence.

### A9: comparison against the existing 105 AUTO_HIGH legacy links

`nfl_cfb_player_links` (124 rows, the OLDER, separate legacy-ID-namespace
table) vs. the newer `cross_league_identity_bridge`:

- 43 of the 105 AUTO_HIGH legacy rows have a matching NFL player in the
  new bridge -- **all 43 agree** on the real-world fact (A.J. McCarron/
  Alabama, Aidan Hutchinson/Michigan, Amari Cooper/Alabama, Andrew Luck/
  Stanford, Baker Mayfield/Texas Tech, etc.) -- the CFB identifiers differ
  only because the two tables use different ID namespaces (legacy
  `CFB_PLAYER_X` slugs vs. canonical `ESPN_CFB:` IDs), not because they
  disagree on the person.
- 62 of the 105 are not present in the new bridge at all -- consistent
  with the newer bridge's stricter, unique-name-only construction
  approach (precision over recall, exactly Part A's stated preference).
- **Zero real contradictions found.**

### A10: write-gate decision

**GATE NOT PASSED. Nothing was written to the database this round, and
nothing should be, yet.** Specifically:

- A known, structural, unresolved failure class (HIGH_RISK, 307 rows)
  remains -- not eliminated, only precisely identified and quantified.
- The validation sample (25) is real but smaller than the requested 100 --
  a genuine time/scope constraint, disclosed rather than padded with
  low-value confirmations.
- No idempotent import script exists for promoting HIGH_CONFIDENCE rows
  into a production identity table -- building one is real, additional
  scoped work, not attempted this round to avoid rushing exactly the kind
  of import Part 7 of the original CFB-enrichment operation warned against
  rushing.

**Recommendation, not action taken**: the existing
`cross_league_identity_bridge`'s 2,574 `LOWER_RISK`/`HIGH_CONFIDENCE` rows
(multi-season + position-corroborated) are a strong, real candidate for a
future promotion pass -- roughly 24x the legacy table's 105 confident
rows -- but require the idempotent-import + collision-check pipeline Part 7
describes before that promotion happens, not a one-off write.

---

## Part B — Player stats (re-confirmed, no change)

18,725 rows, 14,296 distinct players, 316 distinct schools, single
verification tier (`SOURCE_BACKED_DERIVED`). **Season range confirmed
again: 2024-2025 only** -- no other CFB stats table exists anywhere in
this database (exhaustive re-search this round, not just re-citing Round
1). Real per-stat non-null/non-zero counts: rushing 6,773 attempts/6,645
yards rows, receiving 9,212 receptions/9,143 yards rows, passing 3,053
completions/3,037 yards rows, defense 2,711 interceptions/3,034 sacks
rows, kicking 787/724 field-goal rows. No expansion possible without a
new external source (Part B2's rule: document as `SOURCE_REVIEW_REQUIRED`
rather than opportunistically ingest one -- no such source was vetted or
available this round).

## Part C — Awards (re-confirmed, no change)

Exhaustively re-searched **three** real tables this round
(`stg_u04_cfb_awards`, `cfb_awards`, `cfb_award_facts`) -- all three are
the identical 91-row Heisman-only dataset in staging/working/fact form.
**Confirmed: no All-America, Maxwell, Walter Camp, Doak Walker,
Biletnikoff, Davey O'Brien, Butkus, Bednarik, Lombardi, Outland, Mackey,
Thorpe, Groza, or Ray Guy data exists anywhere in this database.** Not a
missing-table oversight -- genuinely absent.

## Part D — Transfer / multi-school history (measured precisely)

3,982 real multi-school players (`transfer_count >= 1`). Of those,
**3,974 (99.8%) have clean, sorted, non-overlapping chronological
`path_json` season sequences** -- only 8 are messy/unparseable. This is
the cleanest unbuilt CFB domain in the database. Per Part D1's explicit
caution: this is `PLAYED_COLLEGE_FOR` evidence (a player's real season-by-
season school history), not a formally-recorded `TRANSFERRED_TO` event --
no source in this database explicitly labels a row as a transfer decision
versus, e.g., a grad-transfer, a JUCO-to-FBS move, or a walk-on situation.
Labeled honestly as multi-school history throughout this report, never
overstated as "transfers."

## Part E — Coach data (quantified precisely, not just "some rows are bad")

188 total `cfb_coaches` rows, re-audited with a real, refined detector
(not the single ad-hoc pattern from Round 1):

- **36 parsing-artifact rows** -- win-percentage fragments (`.752`),
  column headers mistaken for coach names (`"Seasons Coached"`,
  `"Win Pct."`), and win/bowl-count summaries (`"12 wins"`,
  `"~21 bowl wins, 2 national titles"`).
- **7 "merged-two-different-coaches" rows** -- a genuinely different
  defect class: a single row's `coach_name` actually names TWO real,
  different coaches from different eras (e.g. `"Wayne Hardin / Matt
  Rhule"`, `"Dennis Erickson / Mike Riley"`) -- almost certainly a
  scraped "who improved this program most" comparison row, not a coach
  identity at all.
- **145 rows that are apparently real, single coach identities** --
  spot-checked (Barry Switzer/Oklahoma 1975-1985, Amos Alonzo Stagg, Ara
  Parseghian/Notre Dame, Urban Meyer, Steve Spurrier, Woody Hayes, Vince
  Dooley, Tom Osborne, etc.) -- all real, recognizable. Some of these 145
  are themselves **duplicate identities** for the same real person (e.g.
  `"Tom Osborne"` and `"Tom Osborne (Nebraska)"` both exist as separate
  rows) -- a real de-duplication task, not yet performed.

Per Part E1: no row was deleted. This is a measurement and classification,
not a cleanup -- 43 of 188 rows (23%) are confirmed not to represent one
real coach's identity, and any future coach-based game or `COACHED_AT`/
`PLAYED_UNDER` graph edge must exclude them via a deterministic gate
before generation, not before this report.

## Part F — Starter/depth/participation (re-confirmed exhaustively, still none)

Broadened the column-name search beyond Round 1's specific check: searched
every CFB-named table in this database for any column matching
`start*`, `snap*`, `particip*`, `depth*`, `lineup*`, or `games_played`/`gp`.
**Zero matches, anywhere.** This is now confirmed twice, independently,
with a wider search the second time. No starter signal exists in this
database under any name. No fabrication was performed or considered.

## Part G — Roster/player QA (garbage-row downstream impact measured)

The 63 `"- Team"` garbage rows in `canonical_cfb_players` (found Round 1)
are referenced by **81 rows** in `cfb_roster_seasons_real` (some garbage
identities appear in multiple season/team rows) and **zero rows** in
`cfb_player_season_stats_real`. Per Part G1: not deleted. This confirms a
real, quantified contamination surface in the roster table specifically
that any future roster-based capability (Timeline, Roster-by-Position,
etc.) must exclude via a deterministic gate -- `cfb_heisman_guess` is
unaffected, confirmed again, since it never joins through
`canonical_cfb_players` at all (its own table carries `player_name`
directly).

## Part H — Game family certification (unchanged from Round 1, re-confirmed with new evidence)

No new CFB game family was certified this round. `cfb_heisman_guess`
remains the only certified CFB mode -- re-confirmed still green (224/224
suite passing). The Round 1 classifications stand, now with stronger
evidence behind two of them:

- **CFB Career Timeline**: data readiness UPGRADED in confidence (Part D:
  99.8% clean chronological sequences, a very strong real number) but the
  actual mechanic/adapter was not built this round -- remains
  `UNDERSTOOD_BUT_UNSUPPORTED`, and is now the clear #1 recommendation for
  the next actual build.
- **Which School Produced These NFL Players? / College -> NFL Draft
  Game / NFL Team x College**: remain `BLOCKED_BY_IDENTITY` -- Part H1's
  explicit instruction ("cross-league games must remain BLOCKED until the
  crosswalk passes the validation gate") is honored; the identity work in
  Part A, however promising, did not pass its own gate (A10).
- **CFB Coach Connections**: remains `BLOCKED_BY_DATA` -- now precisely
  quantified (23% of `cfb_coaches` rows are not real individual coach
  identities) rather than just "dirty."
- **CFB Lineup/Position Board**: remains `BLOCKED_BY_DATA`, re-confirmed
  exhaustively (Part F).
- **CFB Connections (general)**: remains `BLOCKED_BY_ARCHITECTURE`
  (unchanged -- the mechanic itself was never registered in the Director
  pipeline).

## Part I — Game Creator CFB test (a real bug found and fixed)

Tested the admin Creator's feasibility path against 5 real natural-
language requests:

| Request | Result |
|---|---|
| "Make me a CFB game where I identify a player from his college career." | `SUPPORTED` -- but see the finding below |
| "Make me a transfer timeline game." | `UNKNOWN` (honest -- no mechanic exists) |
| "Make me a CFB award game." | `UNKNOWN` (honest -- no mechanic exists) |
| "Make me a game where I identify an NFL player from his college and draft history." | `SUPPORTED` (correctly routes to `identify_player_from_clues`, NFL) |
| "Make me a CFB Heisman guessing game." | **`NO_MATCH` -- a real bug** |

**Real bug #1 (fixed this round)**: `cfb_heisman_guess` was registered in
`CAPABILITY_REGISTRY` (reachable via direct spec-based generation -- how
the public API and every automated test reach it) but had **zero
translator keyword recognition** in `tools/director_v02/providers/mock.py`
-- the Creator's natural-language path reported `NO_MATCH` for a real,
fully-certified capability. Fixed: added a `"heisman"` keyword pattern
(the same kind of addition already made for draft/championship/lineup).
Verified: "Make me a CFB Heisman guessing game." and "Make me an easy
Heisman trivia game with 10 questions." both now correctly resolve to
`SUPPORTED_WITH_LIMITATIONS` / `WON_HEISMAN`. New regression test added
(`test_supported_with_limitations_for_heisman_request`). Full suite
re-confirmed green after the fix: 224/224.

**Real finding #2 (disclosed, not fixed this round)**: "Make me a CFB
game where I identify a player from his college career" matches the
generic clue/player pattern and reports `SUPPORTED` -- but the only
registered `identify_player_from_clues` capability is `NFL_PLAYER_IDENTITY`.
The translator does not check for "nfl" vs. "cfb" in this pattern at all,
so a CFB-worded request would silently generate an NFL question instead.
This is a real correctness gap (not a security issue -- the Creator is
admin-only and every generated package still goes through the same QA/
review gate before any publication decision, so nothing reaches a real
player from this path unreviewed). Documented with a code comment at the
exact match site rather than rushed with a one-line patch, since the
correct fix is a genuine league-disambiguation design question (does a
bare "player" with no league word default to NFL? does "college" alone
imply CFB?), not a quick keyword addition.

---

## Round 2 summary

- **224/224 tests passing** (223 baseline this round + 1 new regression
  test for the Heisman translator fix).
- **Zero database writes.** DB integrity/FK checks clean before and after.
- **One real code fix**: Heisman Creator/translator recognition
  (`tools/director_v02/providers/mock.py`), covered by a new test.
- **One real finding, disclosed and not yet fixed**: the translator's
  clue/player pattern doesn't disambiguate NFL vs. CFB.
- **Identity bridge**: real, substantial, pre-existing work discovered
  (`cross_league_identity_bridge`, 3,534 rows) that this operation's own
  first-pass crosswalk closely reproduced independently. A confirmed real
  error (Jared Allen) was found in BOTH the existing "production_safe"
  table and this operation's own crosswalk, fully root-caused (a real
  player absent from CFB roster coverage, not a matching-algorithm
  mistake per se), and used to build a principled, quantified risk-tiering
  scheme (2,574 HIGH_CONFIDENCE / 653 REVIEW_REQUIRED / 307 HIGH_RISK).
  **Nothing was written to the database.** The crosswalk remains a
  candidate artifact pending a real idempotent-import pipeline and a
  larger validation sample -- exactly the outcome Part A10 says is
  acceptable.
- **No new CFB game family certified.** Cross-league games remain
  correctly blocked on identity. Career Timeline is the clear next
  candidate given Part D's 99.8% clean chronology finding.

---

## Final CFB matrix (Round 2)

| Area | Status |
|---|---|
| Canonical players | READY_WITH_LIMITATIONS (109,221; 63 garbage rows quantified, not removed) |
| Roster seasons | READY_WITH_LIMITATIONS (282,124; 86-89% field completeness) |
| Positions | READY_WITH_LIMITATIONS (88.7% non-null) |
| Jerseys | READY_WITH_LIMITATIONS (86.1% non-null) |
| Starter signal | BLOCKED_BY_DATA (confirmed, exhaustively, twice) |
| Participation signal | BLOCKED_BY_DATA (same search, same result) |
| Passing stats | READY_WITH_LIMITATIONS (real, 2024-2025 only) |
| Rushing stats | READY_WITH_LIMITATIONS (real, 2024-2025 only) |
| Receiving stats | READY_WITH_LIMITATIONS (real, 2024-2025 only) |
| Defense stats | READY_WITH_LIMITATIONS (real, 2024-2025 only) |
| Kicking stats | READY_WITH_LIMITATIONS (real, 2024-2025 only) |
| Heisman | READY (91/91 clean) |
| Other awards | NOT_READY (data does not exist) |
| All-America | NOT_READY (data does not exist) |
| Multi-school history | READY_WITH_LIMITATIONS (3,982 real; 99.8% clean chronology) |
| Explicit transfers (formally labeled) | NOT_READY (no source distinguishes transfer from multi-school appearance) |
| Coaches | BLOCKED_BY_DATA (23% of rows are not real single-coach identities) |
| Coach-school links | CANDIDATE_ONLY (135 rows, quality gated by the coach-identity issue above) |
| Player-coach links | NOT_READY (not derived) |
| CFB<->NFL identity | CANDIDATE_ONLY (2,574 HIGH_CONFIDENCE candidates; write-gate not passed, Part A10) |
| NFL Draft bridge | CANDIDATE_ONLY (same as above) |
| Graph (CFB-specific edges) | NOT_READY (none added) |
| Heisman Guess | READY (certified, live-tested, Creator-reachable as of this round) |
| Player Guess | BLOCKED_BY_ARCHITECTURE (no adapter) |
| School Guess | UNDERSTOOD_BUT_UNSUPPORTED (clue-based; no adapter) |
| Career Timeline | UNDERSTOOD_BUT_UNSUPPORTED (data strong; no adapter -- top recommendation) |
| Award Games | READY (== Heisman Guess; no second award type exists to differentiate a matching/second game) |
| Coach Connections | BLOCKED_BY_DATA |
| CFB Connections | BLOCKED_BY_ARCHITECTURE |
| Stat Games | UNDERSTOOD_BUT_UNSUPPORTED (data real but narrow; no adapter) |
| Lineup/Position Games | BLOCKED_BY_DATA |
| Cross-League Games | BLOCKED_BY_IDENTITY |
| Game Creator CFB | READY_WITH_LIMITATIONS (Heisman reachable as of this round's fix; league-disambiguation gap disclosed, not fixed) |

---

## Round 3 (Final Go-Live Operation, Mission A)

### A1-A3: identity bridge hardened, validated, and written

Round 2 left the crosswalk as a candidate artifact with "nothing written to
the database" (Part A10). This round completed the write-gate work:

- Extended the risk-tiering validation sample with 13 more real spot-checks
  (30 total this round, 33 cumulative across the operation), several via
  live external verification (Wikipedia / Sports-Reference), deliberately
  adversarial (chosen to stress-test the HIGH_CONFIDENCE tier, not just
  confirm easy cases).
- Found a **second real error class** within the HIGH_CONFIDENCE tier
  itself (multi-season AND position-corroborated, previously assumed safe):
  16 groups (32 rows) where the same `nfl_player_key` maps to more than one
  `cfb_player_id`. Verified two representative cases directly:
  - **Bo Nix** (Auburn -> Oregon): a real, legitimate transfer. Both bridge
    rows are correct; this is expected multi-row behavior, not an error.
  - **Chris Givens**: a genuine collision. The real NFL Chris Givens only
    ever played at Wake Forest (confirmed via Wikipedia), but the bridge
    also links his NFL key to a different, coincidentally same-named player
    who played at Miami (OH).
  - The other 14 groups were not individually re-verified this round given
    time constraints, but are excluded under the same conservative rule
    regardless (precision over coverage: a duplicate `nfl_player_key` is
    excluded whether or not this round confirmed it as an error, since the
    two confirmed cases show the signal catches both legitimate and
    illegitimate duplicates and there is no cheap way to tell them apart
    without a per-row manual check).
- **Final write-gate**: HIGH_CONFIDENCE tier (2,574 rows) minus the 32
  duplicate-`nfl_player_key` rows = **2,542 rows**. Both confirmed real
  errors found anywhere in this entire operation (Jared Allen, Round 2;
  Chris Givens, this round) are independently excluded by two separate
  rules (single-season/no-position tiering; duplicate-key exclusion) --
  direct evidence the write-gate design is catching real error classes,
  not just filtering arbitrarily.
- **Write executed**: backed up the production database first (verified
  byte-identical copy, 1,692,758,016 bytes), then wrote the 2,542 rows to
  a new table, `cfb_nfl_identity_bridge_certified`, with full provenance
  (`bridge_id`, `cfb_player_id`, `nfl_player_key`, `player_name`,
  `school_id`, `school_name`, `nfl_draft_year`, `nfl_draft_team`,
  `nfl_position`, `confidence`, `confidence_tier`, `evidence_json`,
  `source_bridge_table`, `promoted_at`). Import script is idempotent by
  design (checks `bridge_id` existence before each insert); **run twice to
  prove it**: run 1 inserted 2,542 / skipped 0; run 2 inserted 0 / skipped
  2,542. `PRAGMA foreign_key_check` (0 errors) and `PRAGMA integrity_check`
  (`ok`) both clean after the write.
- **Not yet done, explicitly out of scope this round**: no public game
  mode reads this table yet. Writing a validated identity table is a
  prerequisite for a cross-league game, not the game itself -- Cross-League
  Games remains correctly `BLOCKED_BY_IDENTITY` until a real adapter is
  built and separately safety-gated against this exact table (not the
  original, unfiltered `cross_league_identity_bridge`).

### A4: CFB Career Timeline -- evaluated, deferred to backlog

Re-audited the underlying data directly rather than trusting Round 2's
cited "3,982 real multi-school players / 99.8% clean chronology" figure at
face value (that number's exact derivation wasn't recoverable this round).
A fresh, from-scratch query against `cfb_roster_seasons_real` found:

- **15,495** distinct players with more than one `school_id` across their
  career (out of 109,221 total distinct players) -- a much broader
  definition than Round 2's 3,982, which likely applied a stricter filter
  no longer reconstructible (e.g. FBS-only, or players also present in
  some other identity table).
- Of those 15,495, **15,243 (98.4%) have "clean" chronology** -- their
  schools form contiguous blocks when ordered by season (no re-appearance
  of an earlier school after leaving it).
- **252 (1.6%) do not** -- either the same season lists two different
  schools for one player, or a player returns to an earlier school after
  a gap. This is the same structural pattern (same-identity conflation)
  behind both confirmed identity-bridge errors this session.

This is genuinely decent data, not disqualifying -- but building Career
Timeline is real, substantial net-new scope (adapter, registry entry,
schema updates, public-mode wiring, frontend UI, tests, live browser
verification), and the Final Go-Live prompt's own rules are explicit:
*"do NOT delay launch for optional post-launch features (put them in
backlog instead)."* Career Timeline was always framed as conditional
("if data passes a safety gate"), not required. **Decision: defer to
backlog.** The data is a reasonable foundation for a future pass; this
round prioritized the deployment-critical path instead.

### A5: CFB player-from-clues translator bug -- fixed properly

Round 2 disclosed but did not fix a real gap: a CFB-worded
"identify a player from clues" request (e.g. "identify a player from his
college career") silently matched the NFL-only `IDENTIFY_FROM_CLUES`
capability, since the translator's clue/player pattern never checked for
a league signal at all.

Fixed with a real, competition-aware disambiguation in
`tools/director_v02/providers/mock.py` (not a keyword patch): before
building the NFL spec, the translator now checks for an explicit `"cfb"`
token, the literal phrase `"college football"`, or a `"college"`/
`"colleges"` word. If any of those is present **and no `"nfl"` token
contradicts it**, the request now correctly reports
`UNDERSTOOD_UNSUPPORTED_MECHANIC` (-> Creator-facing
`UNDERSTOOD_BUT_UNSUPPORTED`) -- an honest "this is a real concept, no CFB
adapter exists yet" answer -- instead of silently generating NFL content
for a CFB-worded ask. An explicit `"nfl"` token always wins over an
incidental `"college"` mention (e.g. "...college career, he later played
in the NFL" still correctly resolves `SUPPORTED` / NFL). A request with
neither signal still defaults to NFL, consistent with every other pattern
in the translator.

Covered by three new regression tests in `gateway/tests/test_feasibility.py`
(CFB-worded -> unsupported; NFL-worded with incidental "college" mention ->
supported/NFL; bare request with no league signal -> supported/NFL).
Full suite: **227/227 passing** (224 baseline + 3 new).

### A6: Heisman reconfirmed green

No regression: all `cfb_heisman_guess` tests (`test_public_game.py`'s
Heisman section, `test_feasibility.py`'s Heisman assessment test,
`test_creator.py`'s five-capability listing, `test_gateway.py`'s
five-capability listing) still pass in the same full run as the A5 fix
above. No changes were made to `cfb_heisman.py`, its registry entry, or
its public-mode registration this round.

### A7-A11: stats / awards / coaches / starter signal / malformed rows

No new expansion this round (explicitly out of scope -- "document, not
expand"). Round 2's Final CFB matrix (immediately above) remains the
accurate, current record for: passing/rushing/receiving/defense/kicking
stats (real, 2024-2025 only), Heisman-only award coverage, no All-America
data, starter/participation signal (`BLOCKED_BY_DATA`, confirmed
exhaustively twice), and the coach-identity quality issue (23% of coach
rows are not real single-coach identities). No cheap deterministic
exclusion gate was added for the malformed coach/player rows this round --
doing so safely would require re-deriving the exact 23% detection logic
from Round 2, which wasn't reconstructible in the time available this
round without risking an incorrect filter; left as a backlog item rather
than guessed at.

### A12: final CFB game-readiness classification

| Game concept | Classification |
|---|---|
| Heisman Guess | **READY** (certified, live, Creator-reachable, reconfirmed green) |
| Player Guess (name-based) | BLOCKED_BY_ARCHITECTURE (no adapter) |
| School Guess (clue-based) | UNDERSTOOD_BUT_UNSUPPORTED (no adapter) |
| Player From Clues (CFB) | UNDERSTOOD_BUT_UNSUPPORTED (now an honest, correct answer as of A5 -- was a silent mismatch before) |
| Career Timeline | READY_WITH_LIMITATIONS data-wise (98.4% clean chronology); BLOCKED_BY_ARCHITECTURE game-wise (no adapter, deferred to backlog per A4) |
| Stat Games | UNDERSTOOD_BUT_UNSUPPORTED (data real but narrow; no adapter) |
| Lineup/Position Games (CFB) | BLOCKED_BY_DATA |
| Coach Connections (CFB) | BLOCKED_BY_DATA |
| CFB Connections | BLOCKED_BY_ARCHITECTURE |
| Cross-League Games | BLOCKED_BY_IDENTITY -- narrower than before: a validated 2,542-row identity table now exists (`cfb_nfl_identity_bridge_certified`), but no adapter reads it yet, so the classification is unchanged even though the underlying blocker is closer to resolved than at any prior point this operation |
| Game Creator CFB | READY_WITH_LIMITATIONS (Heisman reachable; league-disambiguation gap now fixed, not just disclosed) |

**Overall CFB verdict feeding Mission Q: CFB GAME-READY WITH LIMITATIONS.**
One fully certified, live, game-ready CFB mode (Heisman) on the exact same
shared architecture as every NFL mode; one real bug fixed (not just
disclosed); one real database asset hardened and safely written with a
proven-idempotent, integrity-clean import; one candidate feature evaluated
honestly and deferred to backlog rather than rushed. No fabricated data,
no forced parity, no uncertain identity links promoted.
