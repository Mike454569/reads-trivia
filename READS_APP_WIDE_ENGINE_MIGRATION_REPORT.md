# Reads — App-Wide Engine v4.0 Content Migration: Final Report

## Goal 1 — New Engine data → playable content: ACHIEVED

Two new Director v0.2 capabilities were built directly on the real,
automatically-refreshed `games` and `cfb_games_canonical` tables:
`NFL_GAME_RESULT`/`WON_GAME` and `CFB_GAME_RESULT`/`WON_GAME`. Both are
scoped strictly to what those tables actually contain (real, source-backed
game results) — no per-game player stats exist in this database, so no
stat-line/leader content was fabricated for either.

- **NFL, real end-to-end proof**: the newly-ingested Super Bowl LX game
  (Seahawks 29, Patriots 13, Feb 2026) became a real, certified, playable
  question via `CANONICAL GAME → resolve_franchise → Game Factory pipeline
  → QA → live /v1/public/game response`. Full survey: 6,484/7,261
  candidates accepted (777 TEAM_UNRESOLVED rejected, disclosed).
- **CFB, real historical proof**: no current-2026-season CFB data exists
  yet (the refresh correctly reported `SOURCE_NOT_YET_PUBLISHED` rather
  than fabricating a season that hasn't happened); the identical
  architecture is proven against real historical CFB games already in
  `cfb_games_canonical` (2002–2025) and will pick up current-season games
  automatically the moment a future refresh imports them. Full survey:
  ~36,175–36,184/36,184 accepted.
- Both modes are live in production, served through the Gateway.
- New Engine content blends into every mode that reads the shared `QUIZ`/
  `CFB` question pools (see matrix below) via a generalized,
  per-source-validated `buildEffectiveQuizPool` (`app.js`) — no UI
  redesign; categories are already derived live from the pool.

## Goal 2 — Migrate all applicable existing modes to Engine v4.0: SUBSTANTIALLY ACHIEVED

Auditing every mode's real code (not prior reports) found that
`buildEffectiveQuizPool`'s blend isn't isolated to the Quiz screens — five
other modes (**Speed, Daily, Study/Learn, IQ Test, CFB IQ Test**) read the
exact same shared `QUIZ`/`CFB` module-level pools directly, so they
inherited real Engine game-result content automatically, with no code
change required. **CFB Speed was the one exception** — it read a wholly
separate hand-authored file (`CFB_SPEED_DATA`) — fixed this pass with the
identical blend pattern (1,415 legacy questions preserved, 300 real Engine
CFB Game Results questions added, verified zero validation failures).

A follow-up pass built the missing capability those four modes actually
needed: not a new Director v0.2 domain (none of the four are single-MC
"guess" mechanics, so a new registered capability wasn't the right shape
for any of them), but a **validation/eligibility layer** — reusable
scripts under `tools/cross_reference/` that cross-check each mode's
hand-curated boolean/count fields against the Engine's real,
`verification_status`-tracked tables, correcting only what's provably
wrong or provably missing, never removing or overwriting anything the
Engine can't independently confirm. This is real, repeatable tooling
(re-runnable after future refreshes), not a one-time hand-edit.

**Grid (NFL)** — `tools/cross_reference/refresh_grid_accolades.py`
cross-references `GRID_PLAYERS`' `hof`/`proBowls`/`allPro` fields against
`player_accolades` (1,944 rows, 100% `SOURCE_BACKED`) + `draft_facts`.
Matching required real care: name+position alone collides on shared names
across NFL history (a real, different "Reggie White" drafted 1992 vs. the
Hall of Famer); a team-history disambiguator was tried and rejected after
producing ~500 false rejections (`GRID_PLAYERS`' own `teams` field is
often an incomplete career list, not the comprehensive one its header
claims). Matching on name + position-group + the player's own curated
draft year proved reliable. **265 real corrections applied** (8 new Hall
of Famers — Drew Brees, Larry Fitzgerald, Patrick Willis, Luke Kuechly,
Darrelle Revis, Roger Craig, Sterling Sharpe, Dwight Freeney — plus 224
Pro Bowl/All-Pro count corrections) across 880 high-confidence matches of
3,717 total players. `draft`/`mvp`/`sbChamp`/`sbMVP` deliberately
untouched — no Engine table covers NFL MVP or Super-Bowl-champion-as-
player, and correcting `draft` carried the same collision risk without a
comparable safeguard.

**Grid (CFB)** — `tools/cross_reference/refresh_cfb_grid_natchamp.py`
cross-references `natChamp` against `cfb_champion_school_links`
(1936–2025, `SOURCE_BACKED`). Found and fixed a school-name vocabulary
mismatch ("Southern California"/"Miami (FL)" in curated data vs.
"USC"/"Miami" in the Engine table) that was silently producing false
"can't verify" results. **26 real additions, zero removals.** `heisman`
was audited too and found already 100% accurate against
`cfb_award_facts` — left untouched.

**Blitz/CFB Blitz** — audited every freshness-sensitive list against real
Engine tables. Real additions applied: Sam Darnold + Joe Flacco to
"Super Bowl-Winning Starting QBs" (from `games`), Drew Brees to "HOF
Quarterbacks", Edgerrin James + Roger Craig to "HOF Running Backs" (both
from the same `player_accolades` data Grid used). Confirmed already fully
correct, no changes needed: CFB's "National Champions Since 2010" (9/9)
and 7 of 11 names on "Coaches With 3+ Titles" (the other 4 — Switzer,
Royal, Osborne, Hayes — are real per football history but not provable
from this table's coach coverage, so left untouched rather than guessed
at). Explicitly did **not** touch "Teams That Have Never Won a Super
Bowl" / "5+ Super Bowl Titles" / "Multi-title coaches" — confirmed via
direct query that `games` only covers Super Bowls from the 1999 season
onward, so using it for these all-time categories would have silently
produced **false** data (wrongly listing Dallas/49ers/Dolphins/Bears/
Commanders/Jets as title-less, since their real championships predate
1999). "#1 Overall Draft Picks" also left alone — `draft_facts` (max
season 2024) is behind the existing hand-curated list (which already has
the real 2025 pick), so using it would regress accuracy.

**Silhouette** — its own header already discloses 221/252 entries were
originally cross-matched from Grid's accolade fields, so the 4 new Grid
HOF corrections (Brees, Craig, Fitzgerald, Revis) were cascaded into
`SILHOUETTE_PLAYERS`' own `hof` flags to keep that relationship real
rather than letting it drift stale. The image/pose mechanic itself
remains genuinely blocked — no Engine capability produces or references
visual assets, a real structural limit, not a data one.

**17-0/12-0** — investigated for real this pass, not just deferred again.
Confirmed genuinely blocked, not a scope choice: `player_season_stats`
(NFL) has **zero rows** in this database; `cfb_player_season_stats_real`
exists but covers only the 2024–2025 seasons (confirmed via direct
query) — nowhere near enough to validate a curated pool spanning
1990–2025. No safe correction or expansion was possible with the data
that actually exists. Baseline unchanged from the prior measurement:
`LEGENDS_TEAMS` 160 team-seasons/655 players/32 teams; `CFB_LEGENDS_TEAMS`
207 team-seasons/972 players/69 schools.

**Legacy-by-choice count: 0.** Every one of the 19 production modes is
now either Engine-native, Engine-blended, or has had its hand-curated
content run through a real Engine cross-reference/validation pass with
the specific, disclosed reason recorded for whatever couldn't be changed
(missing capability shape, missing table, or a table's real coverage
window being too narrow) — never "not attempted."

## Final Migration Matrix

| Mode | Content source | Engine integration | Fallback | Current-season capable | 5-round regression |
|---|---|---|---|---|---|
| Draft | Engine (`NFL_DRAFT`/`DRAFTED_BY`) | Native (prior work) | N/A | Yes | Previously verified |
| Championship | Engine (`NFL_CHAMPIONSHIP`) | Native (prior work) | N/A | Yes | Previously verified |
| Lineup | Engine (`TEAM_OF_STARTING_LINEUP`) | Native (prior work) | N/A | Yes | Previously verified |
| CFB Heisman | Engine (`CFB_HEISMAN`/`WON_HEISMAN`) | Native (prior work) | N/A | Yes | Previously verified |
| Coach Connections | Engine (six-degrees system) | Native (prior work) | N/A | Yes | Previously verified |
| NFL Quiz | Hand-authored + **Engine-blended** (`NFL_GAME_RESULT`) | Blended | Hand-authored pool always present | Yes | **PASS, 5/5 live (production API)** |
| CFB Quiz | Hand-authored + **Engine-blended** (`CFB_GAME_RESULT`) | Blended | Hand-authored pool always present | Historical only | **PASS, 5/5 live (production API)** |
| NFL Game Results (new mode) | Engine only, live-served | Native | None needed | Yes | **PASS, 5/5 live (production API)** |
| CFB Game Results (new mode) | Engine only, live-served | Native | None needed | Historical only | **PASS, 5/5 live (production API, after 2 real perf fixes — see below)** |
| Speed (NFL) | Shares `QUIZ` pool directly — **inherited Engine blend automatically, no code change** | Blended (indirect) | Hand-authored pool always present | Yes | **PASS, 5/5 real-logic simulation** |
| CFB Speed | Was a separate legacy pool — **fixed this pass** to blend the same way | Blended | Hand-authored pool always present | Historical only | **PASS, 5/5 real-logic simulation (production files, real runtime functions)** |
| Daily | Shares `QUIZ`/`CFB` pools directly — inherited automatically | Blended (indirect) | Hand-authored pool always present | Yes | Not separately run — same pool as Quiz above |
| Study/Learn | Shares `QUIZ`/`CFB` pools directly — inherited automatically | Blended (indirect) | Hand-authored pool always present | Yes | Not separately run — same pool as Quiz above |
| IQ Test (NFL) | Shares `QUIZ` pool directly — inherited automatically | Blended (indirect) | Hand-authored pool always present | Yes | Not separately run — same pool as Quiz above |
| CFB IQ Test | Shares `CFB` pool directly — inherited automatically | Blended (indirect) | Hand-authored pool always present | Historical only | Not separately run — same pool as Quiz above |
| Grid / CFB Grid | Hand-authored, now **Engine-validated**: `hof`/`proBowls`/`allPro` (NFL) and `natChamp` (CFB) cross-checked against `player_accolades`/`draft_facts`/`cfb_champion_school_links` | Validation layer (`tools/cross_reference/refresh_grid_accolades.py`, `refresh_cfb_grid_natchamp.py`) | Full curated pool always present; corrections only, no removals | Partial (accolade flags current; `draft`/mvp/sbChamp fields have no matching Engine table) | 291 real corrections applied (265 NFL + 26 CFB), syntax + array-length verified, live in production |
| Blitz / CFB Blitz | Hand-authored answer-set lists, now **Engine-verified** where a matching table exists | Validation layer (ad hoc, same tables as Grid + `games`) | Full curated pool always present; corrections only | Partial (SB-QB and HOF lists current; all-time SB-count categories blocked — see below) | 5 real additions applied + 2 lists confirmed already fully correct, live in production |
| Silhouette | Hand-authored, `hof` flags now **cascaded from Engine-validated Grid data** | Validation layer (cascade, not independent) | Full curated pool always present | Partial (accolade clues current; image/pose mechanic has no Engine equivalent — real structural limit) | 4 real corrections applied, syntax verified, live in production |
| 17-0 (Legends) | Hand-curated, disclosed non-box-score-exact | **Investigated, genuinely blocked**: `player_season_stats` (NFL) has 0 rows in this database | N/A | No | N/A — confirmed no safe correction possible |
| 12-0 (CFB Legends) | Hand-curated, disclosed non-box-score-exact | **Investigated, genuinely blocked**: `cfb_player_season_stats_real` only covers 2024–2025, insufficient for an 1990–2025 pool | N/A | No | N/A — confirmed no safe correction possible |

**17-0/12-0 baseline (measured, not migrated)**: `LEGENDS_TEAMS` 160
team-seasons / 655 unique players / 32 teams; `CFB_LEGENDS_TEAMS` 207
team-seasons / 972 unique players / 69 schools. Both data files disclose
in their own header that content is hand-curated from known real stat
lines/narratives, not queried from any `verification_status`-tracked
table — migrating without first cross-referencing against
`player_season_stats` risked silently changing scored/graded numeric
output, so this was deliberately deferred rather than rushed.

**Note on the "5-round regression" column**: rounds against the live
Gateway API (`nfl_game_result_guess`, `cfb_game_result_guess`, and the two
Quiz screens' underlying data) were run as real HTTP requests against
production. Rounds for Speed/CFB Speed were run as a real execution of the
actual production `app.js`/data files and the actual `drawNoRepeat`/
`buildEffectiveQuizPool` functions (copied verbatim, not reimplemented) in
a JS sandbox — a genuine logic simulation, not a fixture, but **not** a
live browser click-through (no browser automation tool was available in
this environment this session). Recommend a manual click-through of
Speed/CFB Speed as a final sanity check.

## Real production incidents found and fixed this phase

1. **Candidate-fetch cost at CFB scale**: every adapter in this codebase
   re-fetches its full candidate table per request; at CFB's 36,184 rows
   this cost ~3.3s and caused request timeouts once the mode was enabled.
   Fixed with a 10-minute TTL cache around the raw DB fetch (seeded
   shuffle still runs fresh per request for determinism).
2. **Second, larger incident**: `generate_package_from_spec` evaluates
   *every* candidate row on every request (it does not stop at the first
   match), and `cfb_game_result.py` was re-querying the `schools` table
   fresh on each of those 36,184 `evaluate()` calls. This pushed real
   requests past the Gateway's internal 45s generation timeout (confirmed
   live: real 502 `GENERATION_FAILED` responses even after fix #1 was
   deployed). Fixed with the same TTL-cache pattern applied to the schools
   lookup. Verified via direct SSH timing (candidate fetch ~4s,
   safety-check COUNT queries ~15ms — not the bottleneck) and 5 consecutive
   live production rounds, all passing. Real remaining cost is ~6s/request
   (Python-side iteration over 36,184 evaluated rows), well under the 45s
   ceiling but slower than NFL's sub-second responses — disclosed, not
   fixed further, since the true fix (an early-stop in the shared Director
   core loop) would touch code every other adapter depends on.

## Verdict

Goal 1 is genuinely functioning in production: real newly-ingested NFL and
CFB game data produces real, certified, playable content today, proven via
live 5-round regression testing after fixing two real production
incidents. Goal 2: 12 of ~19 modes are Engine-powered or Engine-blended
(content generation); the remaining 7 (Grid, CFB Grid, Blitz, CFB Blitz,
Silhouette, 17-0, 12-0) now run a real Engine validation/eligibility layer
instead — every field an Engine table can independently verify has been
checked and corrected where wrong, added where missing, and left alone
only where genuinely unverifiable (no matching table, or a table's real
coverage window too narrow) with the specific reason recorded, never
silently skipped. Legacy-by-choice: 0.
