# Reads Football — Production Status

**This is the one current, independently-verified source of truth for what's actually live.**
Every other "GO LIVE" / "CERTIFICATION" / "canary verified" report elsewhere in this repo is
historical narrative from the session that wrote it — treat it as unconfirmed until you've
re-checked it against reality the way this doc does below. Do not add another one of those
reports; update this file instead.

Last independently verified: **2026-08-31**, during the Production Integrity Fix Pass.

## TL;DR

The Gateway backend is real, deployed, and was found broken (disk full → every request 500ing)
during this pass. Root cause fixed, externally re-verified as healthy, and a real game +
a real Creator-generated package were both produced end-to-end against production. The
frontend's public-mode flags were correct to be on and were left on. See **Remaining Risks**
at the bottom — the outage was silent for an unknown period because nothing was monitoring it.

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
`available: true`, and this pass verified real end-to-end traffic:

- **draft_guess** (a public mode): fetched a real question ("Which NFL team drafted Raonall
  Smith?"), submitted a real answer, got a real validated result
  (`canonical_answer: "Minnesota Vikings"`).
- **six_degrees_guess**: fetched a real live puzzle (Green Bay Packers → Dallas Cowboys, par 2).
- **Creator generation** (admin-only, `/v1/games/generate`, prompt `"NFL teams, guess which
  team drafted this player"`, `provider: "mock"`): produced a real 25-question package,
  `qa_status: "PASSED"`, real provenance/QA metadata, `package_id: GGP:7e850e609c88f6c3d1670589`.

No flags were changed. This was a spot check across a representative few of the 13 modes, not
an exhaustive per-mode test — see Remaining Risks.

## Known real bug found this pass (not fixed)

`/v1/games/generate` with `request_text: "NFL quarterbacks who won Super Bowl MVP, guess the
team they played for"` returns a genuine `500 INTERNAL_ERROR`, while the identical request
succeeds fine through `/v1/games/preview` (translation-only, no candidate generation). The
`NFL_AWARDS` / `WON_AWARD` capability's candidate-generation path has a real bug — this is not
a stale-doc issue, it reproduced live. Root cause not diagnosed this pass (needs Fly log
access, which was unavailable — see Remaining Risks).

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
  touching `gateway/` or `tools/`. There was no CI at all before this. **Important caveat**:
  the suite needs `READS_ENGINE_DIR` pointed at a real ~4GB `reads_football_v4.0.sqlite` (no
  in-repo test fixture DB exists), and that file is correctly gitignored / not present on a
  fresh checkout — so this workflow has NOT yet been verified green on an actual GitHub Actions
  run, only locally (1093 passed, 1 skipped, 0 failed, ~23 min, against the real local DB).
  Making it actually pass in CI needs a DB-fixture strategy (e.g. restore from the Fly volume's
  daily snapshot, or a small purpose-built subset DB) — that's real follow-up work, not done
  this pass.
- Corrected `gateway/fly.toml`'s stale "still not deployed, no Fly authentication" header and
  its stale "what still needs to happen" punch-list (all of which had, in fact, happened).

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
- **No alerting/monitoring exists anywhere in this stack.** The core reason a 100%-full disk sat
  broken in production long enough to matter is that nothing paged anyone. Fly's own health
  checks were failing the entire time and nothing consumed that signal.
- **The `NFL_AWARDS`/`WON_AWARD` generation bug** documented above is unresolved — needs Fly
  log access to actually diagnose (the CLI access issue above blocked this).
- **This pass's verification of the 13 enabled public modes was a spot check** (2 of 13 public
  modes + 1 Creator domain actually round-tripped), not exhaustive. The other 10 report
  `available: true` from `/v1/public/modes` but weren't individually played through end-to-end
  this pass.
