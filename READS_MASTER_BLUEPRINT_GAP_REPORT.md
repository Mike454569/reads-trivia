# Reads — Master Knowledge Blueprint: Gap Check + Highest-Value Fixes

Per `14_CLAUDE_EXECUTION`'s step 8 ("concise... no giant essay").

## Compact gap check (High-priority domains, `02_FIELD_MASTER`)

| Domain | Status | Note |
|---|---|---|
| Player-Season Stats (NFL) | **PRESENT** (was EMPTY) | 43,552 rows, 1999-2025, 9,120 unique players, 88.0% identity-resolved |
| Player-Game Stats (NFL) | **PRESENT** (was EMPTY) | 422,316 rows, 1999-2025, 9,132 unique players, 88.8% identity-resolved, real `game_id` FK to `games` (0 soft-misses) |
| Player-Season Stats (CFB) | PARTIAL/STALE | `cfb_player_season_stats_real` real but only 2024-2025 (18,725 rows) — not touched this pass |
| Draft | PRESENT | `draft_facts`/`nfl_players_draft`, 12,927 rows, now current through 2026 |
| NFL-CFB Identity Bridge | PARTIAL | `cfb_nfl_identity_bridge_certified` — known low coverage from prior work, not touched this pass |
| Team & School Season | PARTIAL | `season_records`/`cfb_school_seasons` (2002+) have wins/losses/points; missing conference records, postseason_result, AP/Coaches rank |
| Postseason & Championships | PARTIAL | CFB real 1936-2025; NFL only derivable from `games` (1999+, real upstream limit, confirmed last pass) |
| Awards & Honors | PARTIAL | NFL: HOF/Pro Bowl/All-Pro only (`player_accolades`); no MVP/OPOY/DPOY/ROTY table exists |
| Coaching | PARTIAL | CFB structured (`cfb_coaches`); NFL only has coach names embedded per-game, no tenure table |
| Play-by-Play & Events | EMPTY | Not attempted this pass |
| Contracts/Cap, Injuries | EMPTY | Field Master itself marks these "NEW vetted source required" — no new source was added this session, correctly out of scope |

## What was implemented this pass

Two new automatic refreshes (`tools/data_refresh/nfl_player_stats_refresh.py`,
`nfl_player_game_stats_refresh.py`), same safety pattern as every other
dataset (backup → stage → publish → sanity-check → restore-on-failure),
same already-approved NFLVERSE_DATA source, same canonical identity
(source `player_id` → `canonical_players.gsis_id` → the project-wide
`PFR:xxxYy00` key `draft_facts`/`player_accolades` already use). Both
wired into the same daily scheduled-refresh architecture as every other
dataset (7 total now). Idempotency proven for real on both (second local
run: identical row counts, no growth).

`fantasy_points_ppr` adopted directly from nflverse's own standard-PPR
computation rather than inventing a scoring formula.

## Newly unlocked

- **17-0 candidate generation is now real, not a proxy**: `tools/cross_reference/generate_legends_candidates.py` — a deterministic system built on the real finding (empirically verified against `app.js`'s actual game logic) that 17-0 has no win/loss eligibility rule; a team-season needs a real statistical standout + real rosterable depth, rank-limited to the curated pool's own measured historical density (6.15 teams/season). Validated against an already-curated season (2020) before trusting it on a new one. Applied for real: 6 new 2025 team-seasons added to `LEGENDS_TEAMS` (160→166), using real per-game fppg, not a proxy.
- `tools/cross_reference/refresh_legends_fppg.py` corrected 824 existing curated fppg values against real stats (legends.js's own header already disclosed these were hand-typed approximations; some were off by 2x — e.g. Arian Foster's real 2015 fppg is 19.2, curated said 7.5).
- Player-game data is now available for any future Quiz/Speed/Creator capability needing single-game facts (e.g. "who had the most receiving yards in this specific game"), not just season aggregates.

## Remaining genuine blockers (not this session's scope)

- CFB player-season stats still only cover 2024-2025 — no games-played field either, so CFB's 12-0 candidate generation remains genuinely blocked (unchanged from last pass).
- NFL championship history pre-1999 — confirmed real upstream source limit (nflverse-data's schedules file itself starts at 1999).
- Contracts/cap/injuries — Field Master itself requires a new, not-yet-vetted source; correctly not added.
- Play-by-play/game-event grain, NFL coach tenure, NFL MVP/OPOY/DPOY/ROTY awards — real, identified gaps, not attempted this pass (lower priority than player-game stats per the execution plan's own ordering).

Full test suite: 333/333. Deployed to production and verified via direct query (see commit for exact numbers).
