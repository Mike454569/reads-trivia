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

That leaves four modes genuinely blocked, each for a stated, real reason
(no Director v0.2 capability covers their content type, and inventing one
would mean the disallowed "add a new data source" / "rebuild the engine"):
**Grid** (multi-criteria player-accolade intersection puzzles — HOF/
Pro-Bowl/All-America flags, not a registered relationship predicate),
**Blitz** (free-response answer-set lists, a different output shape than
every registered capability's single-MC-with-distractors format),
**Silhouette** (image-based player identification), and **17-0/12-0**
(deliberately deferred — see below).

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
| Grid / CFB Grid | Hand-authored (`GRID_PLAYERS`/`CFB_GRID_PLAYERS`, accolade-flag criteria) | **Blocked, real reason**: no registered Director v0.2 capability models multi-criteria accolade intersection (HOF/Pro-Bowl/All-America) — would require a new capability, out of scope | — | No | N/A |
| Blitz / CFB Blitz | Hand-authored answer-set lists | **Blocked for migration** (free-response list format, no matching capability) — but audited for factual freshness against Engine tables this pass: fixed 2 real gaps in "Super Bowl-Winning Starting QBs" (Sam Darnold/SB LX, Joe Flacco/SB XLVII, both verified against `games`); confirmed CFB's Heisman-since-2010 list already exactly matches `cfb_award_facts` through 2025; left "#1 Overall Draft Picks" untouched since Engine's own `draft_facts` table (max season 2024) is actually behind the existing hand-curated list | — | Partial (SB list now current) | N/A |
| Silhouette | Hand-authored (`SILHOUETTE_PLAYERS`, image-based) | **Blocked, real reason**: mechanic requires a player photo/silhouette asset per question — no Engine capability produces or references visual assets | — | No | N/A |
| 17-0 (Legends) | Hand-curated, disclosed non-box-score-exact | Deliberately deferred — see below | N/A | No | N/A |
| 12-0 (CFB Legends) | Hand-curated, disclosed non-box-score-exact | Deliberately deferred — same reason | N/A | No | N/A |

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
incidents. Goal 2 is substantially achieved: 12 of ~19 modes are now
Engine-powered or Engine-blended (5 native from prior work, 7 blended —
2 directly this phase, 4 that inherited the blend automatically by sharing
the same pool, 1 fixed this phase to join them). The remaining 4 modes
(Grid, Blitz, Silhouette, 17-0/12-0) are each explicitly blocked with a
real, stated reason — not silently left behind — and Blitz additionally
received a real factual-freshness fix against Engine's own tables even
though its mechanic can't be migrated.
