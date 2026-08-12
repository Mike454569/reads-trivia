# Reads — App-Wide Engine v4.0 Content Migration: Final Report

## Goal 1 — New Engine data → playable content: ACHIEVED

Two new Director v0.2 capabilities were built directly on the real,
automatically-refreshed `games` and `cfb_games_canonical` tables:
`NFL_GAME_RESULT`/`WON_GAME` and `CFB_GAME_RESULT`/`WON_GAME`. Both are
scoped strictly to what those tables actually contain (real, source-backed
game results) — no per-game player stats exist in this database, so no
stat-line/leader content was fabricated for either.

- **NFL, real end-to-end proof**: the newly-ingested Super Bowl LX game
  became a real, certified, playable question via
  `CANONICAL GAME → resolve_franchise → Game Factory pipeline → QA → live
  /v1/public/game response`. Full survey: 6,484/7,261 candidates accepted
  (777 TEAM_UNRESOLVED rejected, disclosed).
- **CFB, real historical proof**: no current-2026-season CFB data exists
  yet (the refresh correctly reported `SOURCE_NOT_YET_PUBLISHED` rather
  than fabricating a season that hasn't happened); the identical
  architecture is proven against real historical CFB games already in
  `cfb_games_canonical` (2002–2025) and will pick up current-season games
  automatically the moment a future refresh imports them — nothing about
  the adapter is season-specific. Full survey: ~36,175–36,184/36,184
  accepted.
- Both modes are live in production behind `READS_PUBLIC_MODES`, deployed
  as a staged canary matching the existing rollout process.
- New Engine content also blends into two existing modes (Quiz, CFB Quiz)
  via a generalized, per-source-validated `buildEffectiveQuizPool`
  (`app.js`) — no UI redesign; categories are already derived live from
  the pool.

## Goal 2 — Migrate all applicable existing modes to Engine v4.0: PARTIALLY ACHIEVED

**Honest assessment, per the Hard Completion Standard**: this operation did
**not** reach "Engine v4.0 → all applicable modes, legacy as fallback."
Five modes were already Engine-native from prior work; two new Engine
capabilities were added and blended into Quiz/CFB Quiz this phase; the
remaining ~12 modes are unchanged and still run entirely on their existing
legacy/hand-authored content. This was a scope/time choice, not a data
blocker — most of these modes were simply not attempted this pass.

## Final Migration Matrix

| Mode | Content source | Engine integration | Fallback | Current-season capable | 5-round regression |
|---|---|---|---|---|---|
| Draft | Engine (`NFL_DRAFT`/`DRAFTED_BY`) | Native (prior work) | N/A | Yes | Previously verified |
| Championship | Engine (`NFL_CHAMPIONSHIP`) | Native (prior work) | N/A | Yes | Previously verified |
| Lineup | Engine (`TEAM_OF_STARTING_LINEUP`) | Native (prior work) | N/A | Yes | Previously verified |
| CFB Heisman | Engine (`CFB_HEISMAN`/`WON_HEISMAN`) | Native (prior work) | N/A | Yes | Previously verified |
| Coach Connections | Engine (six-degrees system) | Native (prior work) | N/A | Yes | Previously verified |
| NFL Quiz | Hand-authored + **Engine-blended** (`NFL_GAME_RESULT`, new this phase) | Blended, source-independent validation | Hand-authored pool always present | Yes (games table) | **PASS, 5/5 live** |
| CFB Quiz | Hand-authored + **Engine-blended** (`CFB_GAME_RESULT`, new this phase) | Blended, source-independent validation | Hand-authored pool always present | Yes (historical only — no 2026 CFB data published yet) | **PASS, 5/5 live** |
| NFL Game Results (new mode) | Engine only, live-served | Native (new this phase) | None needed (Engine-only) | Yes | **PASS, 5/5 live** |
| CFB Game Results (new mode) | Engine only, live-served | Native (new this phase) | None needed (Engine-only) | Historical only | **PASS, 5/5 live (after 2 real production perf fixes, see below)** |
| Speed / CFB Speed | Hand-authored | Not migrated | — | No | Not run this phase |
| Grid / CFB Grid | Hand-authored | Not migrated | — | No | Not run this phase |
| Blitz / CFB Blitz | Hand-authored | Not migrated | — | No | Not run this phase |
| Silhouette | Hand-authored | Not migrated | — | No | Not run this phase |
| IQ Test / CFB IQ | Hand-authored | Not migrated | — | No | Not run this phase |
| Daily | Hand-authored + CFB/NFL Quiz pool (inherits the blend above) | Indirect (via Quiz pool) | Yes | Partial | Not run this phase |
| 17-0 (Legends) | Hand-curated, disclosed non-box-score-exact | Deliberately deferred (data-integrity risk — see below) | N/A | No | N/A |
| 12-0 (CFB Legends) | Hand-curated, disclosed non-box-score-exact | Deliberately deferred (same reason) | N/A | No | N/A |

**17-0/12-0 baseline (measured, not migrated)**: `LEGENDS_TEAMS` 160
team-seasons / 655 unique players / 32 teams; `CFB_LEGENDS_TEAMS` 207
team-seasons / 972 unique players / 69 schools. Both data files disclose
in their own header that content is hand-curated from known real stat
lines/narratives, not queried from any `verification_status`-tracked
table — migrating without first cross-referencing against
`player_season_stats` risked silently changing scored/graded numeric
output, so this was deliberately deferred rather than rushed.

## Real production incidents found and fixed this phase

1. **Candidate-fetch cost at CFB scale**: every adapter in this codebase
   re-fetches its full candidate table per request; at CFB's 36,184 rows
   this cost ~3.3s and caused request timeouts once the mode was enabled.
   Fixed with a 10-minute TTL cache around the raw DB fetch (seeded
   shuffle still runs fresh per request for determinism).
2. **Second, larger incident (found during this verification pass)**:
   `generate_package_from_spec` evaluates *every* candidate row on every
   request (it does not stop at the first match), and `cfb_game_result.py`
   was re-querying the `schools` table fresh on each of those 36,184
   `evaluate()` calls. This alone pushed real requests past the Gateway's
   internal 45s generation timeout (confirmed live: real 502
   `GENERATION_FAILED` responses). Fixed with the same TTL-cache pattern
   applied to the schools lookup. Verified via direct SSH timing
   (candidate fetch ~4s, safety-check COUNT queries ~15ms — not the
   bottleneck) and via 5 consecutive live production rounds, all passing.
   Real remaining cost is ~6s/request (Python-side iteration over 36,184
   evaluated rows), well under the 45s ceiling but slower than NFL's
   sub-second responses — disclosed, not fixed further this pass, since
   the true fix (an early-stop in the shared Director core loop) would
   touch code every other adapter also depends on, which this operation's
   own scope explicitly excludes ("do not rebuild the engine").

## Verdict

Goal 1 is genuinely functioning in production: real newly-ingested NFL and
CFB game data produces real, certified, playable content today, proven via
live 5-round regression testing after fixing two real production
incidents along the way. Goal 2 remains partial: 7 of ~19 modes are
Engine-integrated or Engine-blended; the rest are unchanged legacy modes,
each left on its existing content by an explicit, time-boxed scope
decision rather than a technical blocker.
