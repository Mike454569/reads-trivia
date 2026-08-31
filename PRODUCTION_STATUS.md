# Reads Football — Production Status

**This is the one current, independently-verified source of truth for what's actually live.**
Every other "GO LIVE" / "CERTIFICATION" / "canary verified" report elsewhere in this repo is
historical narrative from the session that wrote it — treat it as unconfirmed until you've
re-checked it against reality the way this doc does below. Do not add another one of those
reports; update this file instead.

Last independently verified: **2026-08-31**, during the Production Integrity Fix Pass and the
following Final Production Hardening Pass (same day).

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
- Added a second job, `integration-tests-with-real-db`, structurally scaffolded to restore the
  real database from Fly's own automated daily volume snapshot and run the full suite against
  it — this is the "close the gap for real" path, using genuine production-shaped data rather
  than a fabricated mock. **Not implemented or run**: it needs a `FLY_API_TOKEN` GitHub Actions
  secret, and this environment has no `gh` CLI and no GitHub API write access to add one. The
  job checks for the secret and reports itself skipped (not failing) until it exists — see
  Remaining Risks for the exact next step.
- Verified locally (real local DB, full suite, post-hardening-pass changes): **1093 passed, 1
  skipped, 0 failed** — identical to the pre-pass baseline, confirming none of this pass's
  edits introduced a regression.

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
- **Deploying the `/v1/ready` disk-check code is blocked in this environment**, not diagnosed
  further this pass. `flyctl deploy` failed twice with a `401` from Fly's remote builder, and
  both times left this session's flyctl API access broken afterward (read/SSH operations kept
  working; the same recovery path from the first pass — checking the Fly dashboard directly, or
  a fresh `fly auth login` — likely applies again). The code is committed and ready; someone
  with working deploy access just needs to run
  `flyctl deploy --config gateway/fly.toml -a reads-football-gateway`.
- **CI's DB-heavy integration job (`integration-tests-with-real-db`) needs a `FLY_API_TOKEN`
  GitHub Actions secret this environment could not add** (no `gh` CLI, no GitHub API write
  access here). Concretely: generate one with `flyctl tokens create deploy -a
  reads-football-gateway`, then add it at the repo's Settings → Secrets and variables → Actions
  as `FLY_API_TOKEN`. The job's DB-restore step is scaffolded but intentionally left as a `TODO`
  echo, not implemented — restoring a real ~4GB snapshot on every CI run also has real cost/time
  implications worth a deliberate decision, not a default-on assumption.
- **All 13 public modes were individually round-tripped this pass** (fetch + real answer/move
  for every one), closing the "spot check only" gap from the first pass. Not re-verified: modes
  behave correctly under concurrent/production load (only tested one request at a time), and
  the two transient timeouts during this pass (resource contention with the concurrent backfill
  run) suggest this single shared-cpu-1x/1GB machine may not have much headroom under real
  simultaneous traffic plus a background job — worth watching, not yet a confirmed problem.
