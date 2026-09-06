# Reads Football — Production Status

**This is the one current, independently-verified source of truth for what's actually live.**
Every other "GO LIVE" / "CERTIFICATION" / "canary verified" report elsewhere in this repo is
historical narrative from the session that wrote it — treat it as unconfirmed until you've
re-checked it against reality the way this doc does below. Do not add another one of those
reports; update this file instead.

Last independently verified: **2026-09-06**, the Reliability pass (Pass 2.6) below. Prior
verification: **2026-08-31 / 2026-09-01**, across the Production Integrity Fix Pass, the Final
Production Hardening Pass, the Reliability Cleanup pass, the Lineup Concurrency pass, and the
Rivalry Pack + Gold Standard Game Ideas Integration pass (all same session).

## Reliability pass (Pass 2.6) — hard-difficulty fix + deploy outage fixed (2026-09-06)

Two unrelated reliability bugs, fixed and independently re-verified live in production.

**Hard difficulty (Spot the Fake / Odd College Out / One School Missing) was silently
unreachable.** Root cause was NOT a search/retry-reliability problem in
`generate_package_from_spec()` (it evaluates every real candidate, then filters by difficulty --
confirmed by reading it and by direct testing). The real blocker was one level up:
`tools/director_v02/registry.py`'s entries for these 3 domains hardcoded
`supported_difficulties={"any","easy","medium"}` -- a stale value copy-pasted from before their
board pool was expanded from a 60-board SB_CHAMPION-only source (genuinely zero real Hard
boards) to today's 595-board 5-source `_group_board_common` pool. A direct `target_count=5000`
survey found 196 real, distinct, QA-passed Hard candidates per domain -- essentially the same
volume as Medium (196) and Easy (203). That stale registry gate rejected `difficulty="hard"` as
`UNDERSTOOD_BUT_UNSUPPORTED` in both the Gateway-override path (`pipeline.py`) and the
NL-translator path (`validator.py`) before generation ever ran. Fixed by correcting exactly
those 3 registry entries (and the matching `gateway/services/public_game.py`
`certified_difficulties`) -- `CFB_THREE_CLUES_ONE_CHAMPION` (a genuinely narrower, SB_CHAMPION-
only pool with real zero Hard boards) was left untouched. Verified: 30/30 across 10 seeds x 3
modes locally, then confirmed live in production for all 3 modes (`difficulty=hard` returns a
real, correctly-labeled Hard question; answer grading correct in both directions). The 5 exact
NL prompts from spec ("Make me a hard Spot the Fake game", etc.) all resolve through
translator -> validator -> Director -> generated package with the requested difficulty intact.

**Every Gateway deploy caused a real 6-8 minute outage.** `gateway/app.py`'s lifespan startup
handler ran the full `PRAGMA quick_check` (`check_engine_readiness_deep()`) synchronously before
serving a single request -- including Fly's own health checks -- so the documented ~166s
(measured, longer under this box's own ambient I/O variance) full-database integrity scan was a
real, total outage window on every single deploy, not a quiet one-time startup cost as the code
this pass replaced assumed. Confirmed directly: Fly release v65 stuck at "Waiting for
application startup" for 8m5s before self-recovering; releases v60-v64 show the identical
"failed" release status in `fly releases` history, all from this same cause. Fix: startup now
runs only the fast check (the same one `/v1/ready` already used -- file exists/opens, one
indexed COUNT, schema marker present); the full deep check moved to a background task
(`_run_periodic_deep_integrity_check()`) that runs once ~60s after boot and then every 6 hours
for the life of the process, off the request-serving critical path entirely. A confirmed failure
updates a cached status `/v1/ready` reads passively (fails closed on real corruption, never
blocks on it) -- surfaced automatically by the existing `gateway-monitor.yml` GitHub Actions job
(already polling `/v1/ready` every 15 minutes), no new external service or secret needed. The
admin `/v1/admin/diagnostics/db-integrity` route now returns this cached result instantly by
default, with `force=true` still available for an on-demand live check.

Real deploy result after the fix (`fly releases`): **v67, status `complete`** -- the first
non-"failed" release in this app's visible history. Real timeline from `fly logs`: old process
shutdown at 07:49:33, new machine's "Application startup complete" at 07:49:37 -- **4 seconds**
of actual outage, down from 6-8 minutes. Health checks passed immediately, no
"not responding properly" errors at all during this deploy (compare to every prior deploy's log,
which shows several before eventually passing). Single-machine, single-attach-volume topology
means this is NOT true zero-downtime (Fly volumes attach to exactly one running machine, so the
old process must stop before the new one can mount `/data` -- a real, disclosed architectural
constraint, not something this pass attempted to redesign) -- but 4 seconds is a different class
of problem than 6-8 minutes, achieved via the safest available strategy (the existing rolling
replace, now fast) without weakening any backup/rollback/disk-space/corruption-detection
safeguard.

234 gateway tests pass across the affected suites (`test_hard_difficulty_reliability.py` -- new,
31 tests; `test_readiness_latency.py`, `test_staging_hardening.py`, `test_gateway.py`,
`test_public_game.py`, `test_public_mode_wiring.py`, `test_rivalry_gold_standard_integration.py`).
Two pre-existing failures in `test_phase6_mechanics.py`
(`test_ten_playable_nfl_ideas_represent_at_least_six_mechanics`,
`test_ten_playable_cfb_ideas_stay_in_domain_and_never_pad`) were found during this pass's own
regression run -- confirmed present on unmodified `main` via `git stash` before this pass's
changes existed, unrelated to either fix here, not touched. Real, unresolved gap: this pass
verified the background integrity task's mechanism locally (a real 632s local run completed
successfully while the app kept serving other requests concurrently, and `/v1/ready` correctly
reflected the result afterward) and confirmed it starts correctly in production (visible via
`/v1/ready`'s `deep_integrity_check` field going from `checked_at: null` right after boot), but
did not sit through this session watching its first live production run complete (it runs ~60s
after boot, can take several minutes) or its 6-hourly recurrence -- re-check
`/v1/ready`'s `deep_integrity_check` field directly to confirm a completed run.

## Rivalry Pack + Gold Standard Game Ideas — audited, extended (2026-09-01)

This pass was different in kind from the ones above: a content/feature audit, not a reliability
fix. Unlike earlier findings in this doc, the starting state here was genuinely good news —
worth stating plainly rather than assuming another "claimed done, not actually done" gap the way
NFL_AWARDS was.

**What was already real, verified independently (not just trusted from code comments) before
touching anything**: a prior "rivalry-gold-standard-integration" operation had already imported
the full 1,272-question CFB rivalry trivia bank (43 real packs) and the Gold Standard workbook's
curated offense-by-college data (32 current teams + 60 real Super Bowl champions, 1966-2025,
all 11 positions, zero player names), and built 11 real Creator capabilities on top of it
(CFB_RIVALRY_TRIVIA, NFL_OFFENSE_COLLEGE_CURATED, NFL_SB_CHAMPION_OFFENSE_COLLEGE, and 8 more
named Gold Standard "10. New Game Modes" concepts — Odd College Out, Fill the Colleges, Spot
the Fake Lineup, Who Changed?, Three Clues One Champion, Position Trap, Duplicate College Hunt,
One School Missing — plus Franchise Marathon / Era Gauntlet as filters). Confirmed for real,
not assumed:
- The existing test suite (`test_rivalry_gold_standard_integration.py`, 16 tests) passed clean
  locally.
- **The underlying tables exist in the real production database with exactly matching row
  counts** (`cfb_trivia_bank`: 1272, `cfb_rivalry_pack_index`: 43, `curated_nfl_offense_college_board`:
  92, `curated_nfl_offense_college_position`: 1012) — checked directly via SSH, not trusted from
  a docstring. Unlike the NFL_AWARDS incident earlier in this session, this data really had
  shipped to production.
- All 10 of the named Gold Standard concepts generated real, non-empty, QA-passed packages
  against the live production Gateway (not just locally) when tested directly via
  `/v1/games/generate` with real prompts ("Make me an Iron Bowl trivia game", "Make me play Odd
  College Out", etc.).
- The offense-by-college output was inspected directly: shows POSITION + COLLEGE for all 11
  positions, zero player names anywhere in the question text, options, or visual payload, sourced
  from `READS_GOLD_STANDARD_BLUEPRINT_V1` (the curated workbook), not the NFL↔CFB identity
  bridge — matching the exact requirement this pass was asked to re-check.

**Workbook audit (all 18 sheets)**: "3. Pre-Made Puzzles" is confirmed to be the literal source
data already imported as `curated_nfl_offense_college_board`/`_position` — fully covered, no new
work. "9. Site Mode Audit" is a "don't duplicate these existing site modes" list — respected,
nothing here duplicates a listed mode. "18. Data QA Standard"'s checklist (identity/college/
position verification, source provenance, answer uniqueness, generator smoke tests) is already
substantially satisfied by the existing adapters' `verification_status`/`source_id`/duplicate-
guard design. "6. More Puzzle Ideas" (8 items) had not been triaged by name before — see below.

**New this pass, built on the same existing data (no new adapter, no new engine)**: two real
filters from "6. More Puzzle Ideas" that were genuinely buildable now —
- **Theme Nights** (`division`/`conference` filters on `NFL_OFFENSE_COLLEGE_CURATED` only):
  joined from this database's own real `season_standings` table (season 2025, all 32 current
  team codes confirmed to resolve). Deliberately NOT offered on the Super Bowl champion board —
  60 years of conference realignment would make "AFC West" for a 1970s champion historically
  misleading against today's alignment.
- **O-Line Only** (`oline_only` filter, both offense-by-college capabilities): shows only the 5
  real O-Line positions; the question-hint text and duplicate-collision math were re-derived
  specifically for this mode (checked directly: LT+RT alone is a unique hint across all 32
  current-team boards; the SB champion pool's larger 60-board history has 5 genuine real
  collisions even using all 5 OL colleges as the hint, which correctly fall through to the
  existing DUPLICATE_QUESTION guard exactly like this codebase's other disclosed collision cases
  — not a bug, the same precedent already established for the non-OL question text).
- Both filters added to Creator natural-language routing too: "Give me an AFC West offense
  game", "Make me an offensive line only game", "Give me a hardcore Super Bowl offensive line
  game" all route and generate real packages.

**Other "More Puzzle Ideas" items, triaged honestly, not built**: Historical Mode is already
covered by the separate, pre-existing `NFL_OFFENSE_LINEUP_COLLEGE` capability (68 real historical
team-seasons via the certified identity bridge) — a different real domain, not a gap. Rookie
Spotlight would need a rookie/experience flag the curated data doesn't carry per position — a
genuine data gap, not built. Reverse Mode (list colleges given the team) doesn't fit the
"guess" mechanic's answer-contract shape at all — would need a genuinely different mechanic,
out of "smallest correct point" scope this pass. Chemistry Bonus, Logo Version, and Tournament
Bracket are scoring/presentation/session-structure features, not engine content capabilities —
correctly out of scope for the Director/Creator pipeline this pass touches.

## TL;DR

The Gateway backend is real, deployed, and was found broken (disk full → every request 500ing)
during the first pass. Root cause fixed, externally re-verified as healthy, and a real game +
a real Creator-generated package were both produced end-to-end against production. The
frontend's public-mode flags were correct to be on and were left on.

The follow-up hardening pass individually round-tripped **all 13** enabled public modes (not a
spot check), found and fixed a second real bug (`NFL_AWARDS` 500 — a missing production data
table, backfilled for real), added a scheduled uptime monitor, added a disk-headroom check to
`/v1/ready` (written, tested, committed, **not yet deployed** — see Remaining Risks), and hit a
second on-volume-backup near-miss caused by the very backfill script used to fix the first bug
(caught and fixed before it became an outage). See **Remaining Risks** at the bottom.

## How to re-verify this yourself, right now

```bash
curl https://reads-football-gateway.fly.dev/v1/health
curl https://reads-football-gateway.fly.dev/v1/ready
curl https://reads-football-gateway.fly.dev/v1/public/modes
```
`/v1/ready` should report `"status":"ready"` with `engine_database.ready: true` and
`package_storage.writable: true`. If `package_storage.writable` is ever `false` again, that's
the same disk-full failure mode documented below — check `fly ssh console -a
reads-football-gateway -C "df -h /data"` first.

## What was actually found (2026-08-31)

- The Fly app `reads-football-gateway` and its 10GB volume (`reads_engine_data`) were **not**
  "configuration only, never deployed" as `gateway/fly.toml`'s old header comment claimed —
  they'd existed for roughly two weeks. That comment was simply stale; it wasn't lying about
  anything currently true, it was describing a state from before an earlier session deployed
  the real thing and never came back to update it.
- The volume was **100% full** (9.8G used / 0 avail). Every request 500'd because a
  request-logging middleware (`gateway/services/oplog.py`) couldn't open its log file
  (`OSError: [Errno 28] No space left on device`). This is why `/v1/health` timed out from
  outside — Fly's proxy stops routing to a machine failing its health checks, and both the
  liveness and readiness checks were failing.
- Breakdown of `/data/engine` (9.3GB of the 9.8GB volume):
  - `reads_football_v4.0.sqlite` — 4.08GB — the real, live database. Untouched.
  - `backups/reads_v2.1_20260830T131011Z.sqlite` — 4.08GB — a full DB backup sitting on the
    *same volume* as production. Removed (see below — a real off-volume backup already exists).
  - `reads_football_v4.0.restoring.tmp` — 420MB — a leftover partial file from an interrupted
    restore. Removed.
  - `imports/` — 698MB — already-ingested nflverse/cfbfastR source CSVs, fully reproducible
    from `tools/data_refresh/`. Removed.
- **Fly was already taking real automated daily volume snapshots** (5-day retention, most
  recent one 22 hours old at the time of the fix) — a genuine off-disk-corruption backup
  mechanism that already existed independent of anything documented in this repo. The
  on-volume `backups/` copy above was redundant with this, which is why it was safe to delete
  rather than needing to be preserved elsewhere first.
- Fix applied: deleted the three items above (user-confirmed before deletion, given it's a
  live-production data change). Volume dropped to 45% used / 5.2GB free. Both `/v1/health` and
  `/v1/ready` confirmed healthy externally within minutes.
- Separately, rotating `READS_ENGINE_ADMIN_TOKEN` (needed to test admin/Creator routes — no
  copy of the existing token existed anywhere locally) triggered a Fly rolling deploy that
  failed mid-rollout with a `401 unauthorized` from Fly's own API, and the CLI session used for
  this pass lost API access entirely afterward (`whoami` still worked, every actual query
  didn't). The app recovered on its own / via a dashboard check shortly after — see Remaining
  Risks. The new token **did** take effect (verified: real 200 from `/v1/creator/feasibility`
  using it) and is saved locally, gitignored, at `gateway/.env.production.local` — not printed
  in any report or chat log.

## Public modes: left ON, not disabled

The task assumption going in was "some public engine modes are pointed at a dead backend,
disable them." That wasn't true by the time this pass checked: once the disk-full issue was
fixed, `/v1/public/modes` reported all 13 modes `reads-config.js` currently enables as
`available: true`.

**All 13 were individually round-tripped in the hardening pass** (fetch/generate a real game +
submit a real answer/move, not just trusting `available: true`):

| Mode | Result |
|---|---|
| draft_guess | PASS — real question, real answer validated (`canonical_answer: "New York Giants"`) |
| championship_guess | PASS |
| lineup_guess | PASS |
| cfb_heisman_guess | PASS |
| nfl_game_result_guess | PASS |
| cfb_game_result_guess | PASS |
| lineup_college_guess | PASS (one transient 20s timeout on first attempt, reproduced instantly on retry — see below) |
| nfl_game_boxscore_guess | PASS |
| offense_college_guess | PASS |
| sb_champion_offense_college_guess | PASS |
| cfb_ranking_guess | PASS |
| cfb_upset_guess | PASS |
| coach_connections (the real API behind `enableEngineSixDegrees` — see note below) | PASS — real puzzle, real move submitted (`Rob Gronkowski → New England Patriots`, `DRAFTED_BY`), `last_move.accepted: true` |

**Naming note**: `reads-config.js`'s `enableEngineSixDegrees` flag does not gate
`/v1/public/six_degrees/*` (a separate, apparently frontend-unused API surface also tested
healthy) — it gates the frontend's "Coach Connections" screen, which calls
`/v1/public/coach_connections/*`. The 13 flags map 1:1 to the 13 entries in
`/v1/public/modes`.

Two transient 20-25s timeouts (`lineup_college_guess`, `coach_connections`) occurred during the
round-trip pass while the `NFL_AWARDS` backfill's `create_verified_backup()` step was running
concurrently on the same shared-cpu-1x machine — both requests succeeded immediately on retry
once the backfill's I/O-heavy step passed, and `/v1/health` stayed fast and green the whole
time. Read as resource contention, not a bug in either mode.

No flags were changed — all 13 were already correctly on.

## NFL_AWARDS 500 — root cause found and fixed

`/v1/games/generate` with `request_text: "NFL quarterbacks who won Super Bowl MVP..."` returned
`500 INTERNAL_ERROR`. Real Fly logs (`flyctl logs`) pinned the exact line:
`sqlite3.OperationalError: no such table: nfl_season_awards`, raised from
`tools/quiz_export/adapters/nfl_season_awards.py`'s `safety_check()`.

Root cause: `nfl_season_awards` existed in the local dev database (used for local test runs)
but had **never been created in the real production database** — the one-time backfill script
that builds it, `tools/data_refresh/nfl_wikipedia_history_import.py`, had only ever been run
locally. Same "claimed done locally, never actually shipped" pattern as the disk-full outage.

Fix (user-confirmed before running, since it writes to production): ran that script for real
against production via `flyctl ssh console`. It has its own built-in safety design (verified
backup before writing, automatic restore-from-backup on any failure) and completed with
`"status": "SUCCESS"` — 60 championship records and 6 real award types imported (369 total
award rows, 238 resolved to a real player). Retested immediately: `/v1/games/generate` with the
same exact Super Bowl MVP prompt now returns `200`, `qa_status: "PASSED"`, 10 real questions
(sample: "Which player won the AP NFL Defensive Rookie of the Year Award for the 1994 NFL
season?" → "Tim Bowens", a real, correct fact).

**A second near-miss found in the process**: the backfill's own `create_verified_backup()`
(`tools/data_refresh/safety.py`) prunes old on-volume backups *before* writing but never prunes
the backup it just took *after* a successful run — it relies on the *next* run to clean up
after it. Since this is a one-time script (not part of the daily scheduled refresh cycle that
would otherwise do that pruning within ~24 hours), its leftover 4.08GB backup sat on the volume
indefinitely, pushing usage to **89%** (from the healthy 45% after the first pass's fix) until
this pass caught it and deleted it (user-confirmed) — back down to 45%/5.2GB free. This is a
real, latent bug in the backup/pruning design, not a one-off mistake, and is very likely
related to how the original disk-full outage happened in the first place. See Remaining Risks.

## Backup cleanup — fixed permanently (Reliability Cleanup pass)

The near-miss above is now fixed at the code level, not just cleaned up by hand a second time.
`tools/data_refresh/safety.py`'s `finish_run()` — the single function all 34 real refresh/import
scripts already call on both their success and failure paths — now prunes a run's own backup
immediately when `status == "SUCCESS"`, via a new `_cleanup_backup_after_success()`:

- Looks the backup's real path up from `backup_registry` (never trusts a caller-supplied path).
- Refuses to delete anything outside the `backups/` directory this module manages, or the live
  database path itself, no matter what the registry says — a hard, enforced check, not an
  assumption.
- Only ever runs for `status == "SUCCESS"`. A failed run's backup is deliberately kept (even
  after `restore_from_backup()` has already used it) so a human can still re-verify or manually
  re-restore from the exact file.
- Updates `backup_registry.status` to `PRUNED_AFTER_SUCCESS` and logs the outcome into the same
  run's `log_json` (`refresh_runs.log_json` now contains a `backup_cleanup` key) — a clear,
  queryable audit trail, not a silent deletion.

7 new regression tests in `gateway/tests/test_data_refresh_backup_cleanup.py` (all passing,
against an isolated temp database + temp backups directory — never the real local or production
DB): a success prunes the file and marks the registry; `finish_run(status="SUCCESS", ...)`
triggers it automatically end-to-end; a failed run keeps its backup; cleanup refuses a path
outside `backups/`; cleanup refuses to delete the live DB even if the registry is fed that exact
path; an unknown `backup_id` is handled gracefully; running cleanup twice is safe (idempotent).

## Lineup generation starvation — investigated and fixed (Lineup Concurrency pass)

The reproducible failing test (`test_stuck_lineup_generation_does_not_starve_other_mechanics`)
was investigated from first principles, not assumed to be either "a real architecture bug" or
"just flaky" — both would have been wrong conclusions on their own.

**What it is NOT**: a shared-lock/executor/worker-pool bug. `gateway/services/generation.py`'s
isolation (separate `threading.Lock()` + separate single-worker `ThreadPoolExecutor` for
`NFL_OFFENSE_LINEUP`/`NFL_OFFENSE_LINEUP_COLLEGE` vs. every other admin domain) is real and
correctly built — confirmed directly: with the "unrelated" domain pre-warmed, an unrelated call
issued immediately after an artificially-stuck lineup call consistently completed in well under
1s, every time. Matching/Sorting/Higher-Lower/Elimination (`tools/director_v02/mechanic_engine.py`)
were separately confirmed to share **zero** code with `generation.py` at all — that module has no
`threading` import whatsoever, so they were never structurally capable of being starved by
anything happening in the lineup-isolated or admin-shared executors.

**What it IS, found via `cProfile`** (same technique `lineup.py`'s own existing fix already used):
`tools/quiz_export/adapters/draft.py`'s `fetch_ordered_candidates()` called
`engine.gf.feasibility(_SPEC)` — a real, ~1,200-`execute()`-call, multi-second-on-a-cold-cache
read into vendored Engine code — **from scratch on every single call**, purely to gate a static
`SystemExit` sanity check whose answer cannot change within one process's lifetime (`_SPEC` is a
fixed module constant; `generate_candidates()` right after it computes the same feasibility
again internally, un-touchably, since that's vendored code this project's own discipline
forbids modifying). Identical bug shape to the lineup.py fix's own documented root cause. Fixed
the same way, in project code: `draft.py` now caches the result after the first call
(`_FEASIBILITY_CACHE`), matching this codebase's existing convention exactly.

**Why the test was still flaky after that fix, and what fixed it for real**: this sandboxed dev
environment has extreme, unrelated ambient CPU variance — confirmed directly via `ps aux`, not
guessed: this very session's own harness process was independently found pinning 100%+ CPU, and
a second, unrelated `claude` process left running since a prior week was also found pinning a
core. Measured real single-call latency for the exact same operation ranged from **0.6s to
30+ seconds** purely from this ambient noise, with zero relation to the lineup code at all. A
fixed absolute test timeout (2.5s/3.0s) can never be reliable under that much environmental
variance, on this or any similarly noisy machine — but simply raising the constant (explicitly
out of scope per this pass's brief) would only have hidden the real signal, not fixed it. The
actual fix: both timing-sensitive tests now (1) warm every domain/mechanic they use *before* the
timed section, so the assertion measures isolation, not somebody else's cold start, and (2)
compare against a **same-run baseline** measured immediately beforehand under identical ambient
conditions (`ceiling = max(10 * baseline, 5.0)`) instead of a fixed constant — self-calibrating
to whatever this machine's real speed happens to be at test time, while still catching a genuine
regression (which would show as a multiple of that same-run baseline, not just uniform ambient
slowness). Verified reliable empirically, not just in theory: **14 consecutive full clean runs
(70/70 individual test passes, 0 failures)** of the whole file, deliberately re-run repeatedly
while this environment's real ambient load was fluctuating (one run's total wall-clock time was
58.65s, another 11.56s, for the identical 5 tests).

Added one new, broader regression test,
`test_matching_sorting_higher_lower_elimination_and_creator_all_work_while_lineup_is_stuck`,
covering the full acceptance criterion by name: Matching, Sorting, Higher-Lower, Elimination,
and one Creator/admin domain all generate successfully (and quickly, by the same self-calibrating
measure) while a lineup call is deliberately held stuck.

**Deployed and independently re-verified live in production**: `flyctl deploy --recreate-builder`
again (same tool as the hardening pass; this deploy's health-check-wait also timed out
client-side during the real startup window — this time closer to ~8.5 minutes, well past the
documented ~166s median, consistent with Fly's own documented volume-I/O variance rather than
anything wrong with this pass's code, and confirmed not an import/syntax issue by checking
`draft.py` imports cleanly locally before concluding that). Once settled: `/v1/health` 200,
`/v1/ready` 200 with `disk.free_percent: 53.0`, both Fly health checks passing. Confirmed the
real public `lineup_college_guess` mode (fetch + real answer, `correct: true`), a real unrelated
mode (`cfb_ranking_guess`), and Creator generation for `NFL_DRAFT` all work — and confirmed the
actual fix's real-world effect directly: first post-restart `NFL_DRAFT` Creator call **3.85s**
(cold), second call **0.49s** (cache warm) — a real, measured ~8x improvement in production, not
just in a local benchmark.

Full local suite after this pass's changes (real database): **1103 passed, 1 skipped, 1
failed** in 1h22m (this run's own wall-clock time is itself evidence of how loaded this machine
was). The 1 failure, `test_grid.py::test_grid_board_multi_team_criterion_completes_quickly`, is
in a completely different file this pass never touched (grid board generation, not
lineup/generation.py) — it missed its own fixed 3.0s absolute threshold by 39 milliseconds
(3.039s). Same root-cause class as the starvation test before this pass's fix (a fixed absolute
timing threshold on an environment with extreme, unrelated ambient CPU variance), but a different
test in a different subsystem, outside this pass's explicit scope (lineup starvation + real-DB
CI) — not fixed here. See Remaining Risks.

## Cleanup done this pass

- Removed 5 orphaned static export files (`data/quiz-engine-{pilot,pilot-v2,qb-pilot,
  championship-award-pilot,mixed-pilot}.js`, ~255KB) — confirmed unreferenced by `index.html`
  or `engine-game-ui.js` (the latter's own comment explicitly says "Deliberately NOT
  data/quiz-engine-championship-award-pilot.js").
- Removed `playtest-engine-draft.js` and `playtest-player-from-clues.js` and their `<script>`
  tags in `index.html` — both were explicitly marked "TEMPORARY... delete this line" in their
  own header comments, loaded on every visit with zero effect on gameplay.
- Fixed the Privacy Policy (`app.js`'s `renderPrivacy()`), which claimed "no accounts,
  passwords, or email addresses required" — the app has had real Firebase Auth username/password
  accounts (synthetic `slug@reads.local` addresses, no real email needed) since before this
  pass. Copy now describes the real mechanism.
- Added `.github/workflows/gateway-tests.yml` — runs `pytest gateway/tests` on every push/PR
  touching `gateway/` or `tools/`. There was no CI at all before this.
- Corrected `gateway/fly.toml`'s stale "still not deployed, no Fly authentication" header and
  its stale "what still needs to happen" punch-list (all of which had, in fact, happened).
- **Hardening pass: made the CI workflow actually structurally runnable without a 4GB DB.**
  This suite has no fixture/mock database — nearly every test opens the real
  `reads_football_v4.0.sqlite` (correctly gitignored, absent on any fresh checkout). Measured
  this precisely rather than guessing: ran the full suite against a simulated fresh checkout
  (git-tracked `Reads_Football_Data_Engine_v4.0/*.py` present, no `.sqlite` file) — **426 tests
  pass with zero database**, spread across 52 of 62 test files (only 10 files are 100%
  DB-independent, so a simple per-file `--ignore` split would have thrown away most of that
  426). Generated an exact, empirical list of the other 667 node IDs (via JUnit XML, not
  string-scraping — pytest's own truncated console summary lines turned out to be unreliable
  for tests with natural-language parametrize values containing spaces) into
  `gateway/tests/.ci_needs_real_db.txt`, and added a `pytest_collection_modifyitems` hook in
  `conftest.py` that skips exactly those node IDs (clear reason shown) when
  `CI_SKIP_DB_TESTS=1` — never touching how the suite behaves in a normal local run. Verified
  clean: **426 passed, 668 skipped, 0 failed** in ~4 seconds against the simulated fresh
  checkout. A genuinely new failure in a previously-passing test, or in any test not on that
  list, still shows up as a real failure — this is a real gate, not a rubber stamp.
- Added a second job, `integration-tests-with-real-db`, restoring the real database from Fly's
  own automated daily volume snapshot and running the full suite against it — using genuine
  production-shaped data, never a fabricated mock, and **never mutating production**: every step
  operates on a brand-new, separate, temporary volume created FROM a snapshot (an immutable
  point-in-time copy) and a brand-new temporary machine, both destroyed in an `if: always()`
  cleanup step regardless of whether the tests pass, fail, or an earlier step in the job itself
  fails partway. **Lineup Concurrency pass: implemented for real, not left as a TODO** — but
  honestly caveated, since it still needs a `FLY_API_TOKEN` GitHub Actions secret this
  environment has no `gh` CLI or GitHub API write access to add (confirmed again this pass), so
  the job as a *whole* has never run end-to-end. Every individual `flyctl` subcommand's flags
  (`volumes list --json`, `volumes snapshots list --json`, `volumes create --snapshot-id`,
  `machine run --volume ... --command ... --detach --json`, `machine wait --wait-timeout`,
  `ssh sftp get --machine`, `machine destroy --force`, `volumes destroy --yes`) was checked
  against real `flyctl <cmd> --help` output in this session, and the JSON field names for
  `volumes list`/`volumes snapshots list` (`id`, `name`, `created_at`) were verified against
  this project's own real production app's real output — but `volumes create --json` and
  `machine run --json`'s exact output shape (assumed here to be a plain object with an `id`
  field, the standard Fly convention) were **not** independently verified, since doing so would
  mean creating real temporary Fly resources outside of an actual CI run to check. Concretely:
  generate the secret with `flyctl tokens create deploy -a reads-football-gateway`, add it at
  the repo's Settings → Secrets and variables → Actions as `FLY_API_TOKEN`, then the first real
  run of this job **is** the first real end-to-end test of this restore path — watch it, don't
  assume it's correct. See Remaining Risks.
- Verified locally (real local DB, full suite, post-hardening-pass changes): **1093 passed, 1
  skipped, 0 failed** — identical to the pre-pass baseline, confirming none of this pass's
  edits introduced a regression. (Lineup Concurrency pass's own final full-suite run — 1103
  passed, 1 skipped, 1 failed, adding the pass's own 10 new tests — is recorded under "Lineup
  generation starvation" above and in Remaining Risks; the 1 failure there is unrelated to any
  change in either pass.)

## Monitoring (new, hardening pass)

Added `.github/workflows/gateway-monitor.yml` — a scheduled GitHub Actions job (every 15
minutes, plus manual `workflow_dispatch`) hitting `/v1/health` and `/v1/ready`. A failure shows
red in the Actions tab and triggers GitHub's default workflow-failure notification. No new
service, no new account — the simplest reliable option that reuses infrastructure already being
added this pass for CI.

Also added a `disk` field to `/v1/ready` (`gateway/app.py`, `config.DISK_FREE_PERCENT_MIN`,
default 10%): readiness now fails *before* the volume actually fills, not just after, by
reporting free-space percentage and returning `503` below the threshold. This reuses Fly's own
already-polling health check (every 30s, `fly.toml`) instead of standing up separate disk
monitoring. **Written, tested locally (`test_staging_hardening.py`'s 7 readiness tests pass, no
regression; full local suite re-verified clean at 1093/1094), and committed — but NOT yet
running in production.** Deploying it (`flyctl deploy --config gateway/fly.toml`) failed twice
this pass with a `401 Unauthorized` from Fly's remote build service, and — both times —
subsequently broke this session's flyctl API access the same way the earlier secrets-rotation
deploy did (identity check keeps working, every actual query fails with "Not authorized").
Read/SSH-only flyctl operations were unaffected throughout; only build/deploy-class operations
hit this. The live Gateway itself was never affected by either failed deploy attempt. See
Remaining Risks.

## Explicitly NOT done this pass, and why

- **`Reads_Football_Data_Engine_v4.0/game_director.py`, `game_factory.py`, and
  `graph_explorer.py` were NOT removed**, despite this task's brief (and an earlier audit
  agent's finding) calling them clearly-obsolete legacy code. That was wrong: `graph_explorer.py`
  is imported directly by five live gateway services (`grid.py`, `graph.py`,
  `coach_connections_graph.py`, `public_six_degrees.py`, `public_coach_connections.py`), and
  `game_director.interpret()` / `game_factory.feasibility()` are real steps in the QA pipeline
  this pass watched execute live in the Creator test above. Only `game_director.py`'s separate
  `.publish()` method is confirmed broken (calls a nonexistent `game_factory.build_mode()`) —
  that one function, not the files, is the actual dead code. `quality_intelligence.py` in the
  same directory does appear genuinely unimported anywhere — safe to remove in a future pass,
  left alone here since it ships as part of the same directory that gets deployed wholesale to
  `/data/engine` and this pass didn't want to touch that deploy path further after the outage
  above.
- **The ~70 other root-level report `.md` files were not individually corrected or archived.**
  This file is meant to supersede them as the thing you actually read, but auditing 70 files of
  historical narrative for accuracy wasn't attempted this pass — treat anything outside this
  file as unverified history, not as a promise to have fixed each one.
- **`creator-ui.js` (21KB, admin-only, gated behind the hidden `#creator` hash route) was not
  lazy-loaded.** It's read synchronously at top-level page-init (`if (state.screen ===
  'creator') { state.creator = ... CREATOR_SCREEN... }`, before `renderAll()`), so lazy-loading
  it safely means restructuring that synchronous boot path into an async one — real surgery on
  code that currently works, for a comparatively small (21KB, cached after first load) payoff.
  Flagged as a legitimate but deferred improvement rather than rushed.

## Infrastructure risks (live findings, not guesses)

- **Volume**: 45% used / 5.2GB free right after cleanup (was 100%/0 avail). No automatic
  alerting exists for this — the same slow fill that caused this outage could recur silently.
- **Backups**: Fly's own automated daily volume snapshots are real and running (5-day
  retention). That's a genuine safety net independent of anything in this codebase. The
  in-repo `READS_ENGINE_BACKUP_AND_RESTORE.md` procedure (copying a full DB onto the same
  volume as a "backup") is the pattern that caused this outage in the first place — don't use it
  this way again; if a manual snapshot is ever needed, take it off-volume.
- **Fly CLI access**: broke mid-pass (`flyctl status`/`apps list`/`checks list` all returned
  "Not authorized to access this organization/firecrackerapp" after a secrets rotation, even
  though `flyctl auth whoami` kept working and the live app itself was healthy throughout this
  particular failure). Never fully re-diagnosed — the user refreshed access via the Fly
  dashboard and the app came back, but the CLI session in this environment may still need a
  fresh `fly auth login` for anyone continuing this work.
- **SQLite / iCloud risk (local dev machine, not production)**: this repo lives under
  `~/Desktop/...`, which has iCloud "Desktop & Documents" sync enabled
  (`FXICloudDriveDesktop=1`) on this Mac. `Reads_Football_Data_Engine_v4.0/` contains **11GB**
  of local SQLite databases, including live `-wal`/`-shm` sidecar files (evidence of
  actively-open-or-uncleanly-closed databases) and **3.7GB across 85+ uncleaned timestamped
  backup copies** in `Reads_Football_Data_Engine_v4.0/backups/` (Aug 12–18). iCloud sync does
  not understand multi-file SQLite (main + `-wal` + `-shm`) as one atomic unit — syncing a
  mid-write database is a real corruption risk, separate from anything on Fly. None of this is
  git-tracked (the `.sqlite*` patterns are gitignored), so it's a local-disk/iCloud-bandwidth
  concern only, not a repo concern. Not cleaned up this pass — it's the user's local disk and
  wasn't blocking production; flagged here as a concrete, real risk worth a deliberate decision
  (move the working DB outside the iCloud-synced folder, and/or prune the 85+ backups) rather
  than continuing to accumulate.
- **~~No alerting/monitoring exists anywhere in this stack~~ — partially fixed.** A scheduled
  GitHub Actions monitor now polls `/v1/health`/`/v1/ready` every 15 minutes. Still missing: the
  new disk-percentage check in `/v1/ready` is written and committed but not deployed (see
  above) — until it ships, disk headroom is only visible by manually SSHing in and running
  `df -h /data`, same as before this pass.
- **The `create_verified_backup()` post-success pruning gap is real and unresolved.** It prunes
  old backups before writing, never after a successful run. A one-time script (like the awards
  backfill) can leave a ~4GB orphaned backup for up to ~24 hours until the next scheduled
  refresh happens to prune it — this pass's own backfill run demonstrated this exact failure
  mode, pushing the volume to 89% before being caught and manually cleaned up. This is very
  plausibly how the original disk-full outage accumulated. Real fix: make
  `create_verified_backup()` (or its caller) prune its own backup immediately after a
  successful run, not just before the next one.
- ~~Deploying the `/v1/ready` disk-check code is blocked~~ **Fixed in the Reliability Cleanup
  pass**: `flyctl deploy --recreate-builder` (a real flag for exactly this stale-remote-builder
  symptom) got past the `401`. The rollout itself briefly looked broken too (`flyctl` reported
  "not listening on the expected address" and gave up with "timeout reached waiting for health
  checks") — this was `flyctl`'s own client-side wait timing out before the Gateway's
  documented ~166s full-database startup check (`gateway/app.py`'s lifespan handler,
  `check_engine_readiness_deep()`) finished; the machine itself was never actually broken.
  Confirmed externally once settled: `/v1/health` 200, `/v1/ready` 200 with a real
  `"disk":{"free_percent":53.0}` field, both Fly health checks passing
  (`servicecheck-00`/`servicecheck-01`). Added 3 regression tests
  (`gateway/tests/test_staging_hardening.py`) for the actual threshold behavior (fails below
  `DISK_FREE_PERCENT_MIN`, passes at/above it, degrades gracefully on a `disk_usage()` error) —
  none existed before.
- **CI's DB-heavy integration job (`integration-tests-with-real-db`) needs a `FLY_API_TOKEN`
  GitHub Actions secret this environment still could not add** (no `gh` CLI, no GitHub API write
  access, reconfirmed again in the Lineup Concurrency pass — this repo's public API gives real,
  useful read access without a token, e.g. confirming the CI run below, but adding a secret is a
  write operation the public API can't do unauthenticated). The DB-restore step is now a real
  implementation (see "Lineup generation starvation" above), not a `TODO` echo — but the job as a
  *whole* has never run end-to-end, and two of its `flyctl --json` output shapes were inferred
  from Fly's general API conventions rather than verified against real output. Concretely:
  generate the secret with `flyctl tokens create deploy -a reads-football-gateway`, add it at the
  repo's Settings → Secrets and variables → Actions as `FLY_API_TOKEN`, then **watch the first
  real run closely** rather than assuming it works — restoring a real ~4GB snapshot on every CI
  run also has real cost/time implications worth a deliberate decision, not a default-on
  assumption.
- **The DB-independent CI job is confirmed real and passing on actual GitHub Actions** (not just
  simulated locally) — run `33444205797` (and every push since), triggered automatically: the
  `pytest` job shows `conclusion: success`, and `integration-tests-with-real-db` correctly
  detected the missing secret and reported itself skipped rather than faking a pass (verified via
  the public `api.github.com` REST API, which needs no token for a public repo's run/job status,
  just not for raw log downloads or secrets).
- **The scheduled monitor workflow (`gateway-monitor.yml`, every 15 min) has not fired yet as of
  this pass** — confirmed via the same public Actions API (still only 1 total run, the CI one).
  GitHub can take up to roughly an hour to activate a newly-added `schedule:` trigger; nothing
  points to it being broken, but it has not been observed actually running. Its YAML was
  validated (parses correctly, correct `cron`/`workflow_dispatch` triggers, correct job
  structure) but `workflow_dispatch` could not be triggered manually to force an immediate,
  observed run — that requires an authenticated write call this environment doesn't have.
- **All 13 public modes were individually round-tripped in the hardening pass** (fetch + real
  answer/move for every one), closing the "spot check only" gap from the first pass. Not
  re-verified under concurrent/production load (only tested one request at a time).
- ~~The full local test suite is not consistently clean on this machine~~ **the specific
  reproducible starvation failure is fixed** (Lineup Concurrency pass — see above), but the
  underlying environmental cause (this sandboxed dev machine has extreme, unrelated ambient CPU
  variance — confirmed via `ps aux`, not guessed) is not something any application code change
  can fully eliminate, and it keeps surfacing in whichever fixed-absolute-timing test happens to
  get unlucky on a given run. Concretely: this pass's own final full-suite run hit a *different*
  one — `test_grid.py::test_grid_board_multi_team_criterion_completes_quickly` (3.039s against
  its own fixed 3.0s ceiling) — in a file this pass never touched. **A real follow-up worth
  doing**: any other fixed-absolute-timing test in this suite (grep for hardcoded second values
  compared against `time.time()`/`time.perf_counter()` deltas) is a candidate for the same
  same-run-baseline fix applied to `test_lineup_starvation_fix.py` in this pass, since this
  machine's ambient variance is a property of the environment, not of any one test.
