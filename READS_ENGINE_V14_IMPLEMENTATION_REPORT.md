# Reads Engine — Claude Code Implementation v1.4

## Production Deployment + Controlled Rollout

Reads Football Engine: v4.0. Claude Code implementation phase: v1.4.

This phase's mission was not to build new engine capability — it was to make the
already-certified v1.3 multi-mode architecture **safe to operate** in front of real
traffic: production configuration, startup/readiness validation, kill switches,
CORS/rate-limit intent, telemetry, and a reproducible deploy/rollback procedure.

**Note on how this report came to exist**: the v1.4 implementation itself (Parts
1–33, 51 below) was already present, complete, and uncommitted in the working tree
at the start of this session — startup validation, the public kill switch,
mode-level rollout controls, safe health/ready responses, structured telemetry,
frontend runtime config, timeouts, and 10 new tests were all already written, with
extensive inline reasoning comments throughout. This session's job was to verify
that work end-to-end against a real running Gateway, find what it missed, and
produce this report. Everything under **"Verification performed this session"** is
this session's own work; everything else is attributed to that prior state.

---

## Git

- **v1.3 checkpoint (HEAD)**: `3e998c6555385dff8798927de80bf97852a61f64` — "Reads engine
  implementation v1.3: certify multi-mode frontend integration"
- **Working tree**: NOT clean — 13 modified files + 2 untracked files (`reads-config.js`,
  a new git-tracked runtime config file that belongs with this checkpoint, and
  `2026 NFL Draft Guide.code-workspace`, an unrelated local IDE artifact, left untouched).
  None of this is committed. Per the completion rule, it stays uncommitted until you
  approve it.

## Baseline

- **151/151 tests passing** (up from the 141 cited in the v1.3 checkpoint — v1.4 added
  10 new tests: master-switch defaults, master-switch-off blocking fetch/answer/mode-list,
  `READS_PUBLIC_MODES` narrowing and single-mode disabling, `/v1/ready` and `/v1/health`
  path-leak checks, and telemetry-event correctness for both served-game and
  answer-submitted events).
- DB FK check: clean. DB integrity check (`PRAGMA integrity_check`): `ok`.
- `draft_facts` row count: 12,253. `database_version`: `4.0.0`.
- No test-run noise in tracked files after the full suite ran (`git status` identical
  before/after) — confirms the `tools/director_v02/audit_log.py` redirect fix (Part 19)
  actually works, not just reads correctly.
- Draft pilot and Championship pilot both verified live against a real running Gateway
  (see below), not just via test doubles.
- Both frontend flags default OFF in the committed `reads-config.js`.
- Admin routes: verified rejecting both a missing token and a wrong token (401/401).
- No answer leakage, no admin-token leakage: verified directly (see Security below).

Architecture status carried from v1.3: **READY**.

---

## Verification performed this session

Everything below was executed directly against this repo, not inferred from reading code:

1. **Full pytest run** with `READS_ENGINE_DIR` pointed at the in-repo
   `Reads_Football_Data_Engine_v4.0/` (a symlink to the real 1.6GB
   `Reads_v4_Database.sqlite`) — 151 passed in ~88s.
2. **DB integrity**: `PRAGMA foreign_key_check` (empty/clean) and `PRAGMA
   integrity_check` (`ok`) run directly against the real database file.
3. **Live Gateway smoke test** (`uvicorn gateway.app:app`, real process, real DB):
   - `GET /v1/health` → `{"status":"ok","service":"reads-engine-gateway","api_version":"v1"}` —
     no path, no DB detail.
   - `GET /v1/ready` → `{"status":"ready","engine_database":{"ready":true,"database_version":"4.0.0"},"package_storage":{"writable":true},"mode_registry":{"loaded":true}}` —
     no filesystem path anywhere in the body (this is the exact gap the prior
     session's Part 6 fix closed — confirmed closed, not just claimed).
   - `GET /v1/public/modes` → both modes listed, `available: true`, no internal ids.
   - `GET /v1/public/game?mode=draft_guess` and `...mode=championship_guess` → both
     returned real, engine-generated questions with no `correctIndex`, no `answer`
     field, no QA metadata anywhere in the response body.
   - `POST /v1/public/game/answer` with a wrong answer → `{"correct":false,"canonical_answer":"...","notes":null}`
     (the canonical answer is *supposed* to appear here — that's the reveal after a
     submission, not a leak).
   - `GET /v1/public/game?mode=not_a_real_mode` → clean `INVALID_MODE` error, no stack trace.
   - `POST /v1/games/generate` with no `Authorization` header → `401`. With a wrong
     bearer token → `401`. Admin routes unaffected by any of the public-side work.
   - `POST /v1/public/game/answer` with a path-traversal-shaped `game_id`
     (`../../etc/passwd`) → clean `INVALID_GAME_ID`, no filesystem interaction, no leak.
   - CORS: `Origin: https://reads.football` → response echoes
     `access-control-allow-origin: https://reads.football`. `Origin:
     https://evil-attacker.example` → no `Access-Control-Allow-Origin` header at all
     (browser-enforced rejection confirmed at the header level, not just "the code
     looks right").
4. **Master kill switch**, tested on a second instance with
   `READS_PUBLIC_GAME_ENABLED=false`:
   - `/v1/public/modes` → both modes now report `"available": false`.
   - `/v1/public/game?mode=draft_guess` → `503 SERVICE_UNAVAILABLE`, clean body, no leak.
5. **Concurrency smoke test** — 15 concurrent `GET /v1/public/game?mode=draft_guess`
   requests against one instance: 1 succeeded (`200`), 14 got `429`. See **Real
   finding** below — this is not the public rate limiter; it's a pre-existing,
   admin-side single-slot generation lock (`gateway/services/generation.py`'s
   `_generation_lock`, "Director v0.6, Part H") that public gameplay inherited by
   reusing the same generation pipeline. It degrades safely (clean `GENERATION_BUSY`
   error, frontend shows "Try Again" + fallback, no crash, no corruption) but it is a
   real concurrency ceiling worth knowing about before real traffic arrives.
6. **Frontend fallback code path** (`app.js`) read directly: confirmed error screen
   offers an explicit "Try Again" button and a "Play the existing quiz instead"
   fallback button — no automatic retry loop, matching Part 16's requirement.
7. **CSP**: `index.html` has no `Content-Security-Policy` meta tag or header
   anywhere. Documenting this per Part 28's explicit instruction ("if no CSP exists,
   document that rather than inventing a huge security project") rather than adding one.
8. **Fly CLI**: neither `fly` nor `flyctl` is installed or authenticated in this
   environment. Confirms the deployment blocker the prior session's `fly.toml`
   comments already stated.

### Real finding: concurrent public generation contends on one global lock

`gateway/services/generation.py` enforces a single in-process generation slot
(`_generation_lock`, non-blocking `acquire`) — a v0.6-era admin-tooling safeguard
("only one generation job at a time"). `/v1/public/game` calls this same pipeline for
every fresh-game request (there's no pre-generated pool), so **any two real players
requesting a new Draft or Championship question within the same ~1 second will have
one of them get `GENERATION_BUSY` (429)**. In the 15-concurrent-request test, that
was 14 of 15. The failure mode is safe (clean error, working fallback UI, no
corruption, no leaked internals) but it is a real per-instance concurrency ceiling
that a canary rollout should watch for in telemetry (`public_game_no_eligible` /
`GENERATION_BUSY` rates), not assume away. It does not block a small controlled
canary (Stage 2 in the rollout plan below is explicitly "controlled testing", not
open traffic) but it should be resolved — most simply with a small request queue or
a short bounded wait-and-retry server-side — before Stage 6 (broader rollout).

---

## Production environment contract

| Variable | Class | Purpose | Missing behavior |
|---|---|---|---|
| `READS_ENGINE_DIR` | REQUIRED CONFIG | Path to the Engine's `.py` modules + `reads_football_v4.0.sqlite`, colocated (the Engine resolves its own DB path relative to itself). | `check_engine_readiness()` reports `ready: false`, `reason_code: DIR_MISSING`; `/v1/ready` returns 503. No fallback default (Part 2 fix — the old default was a specific developer's `/Users/.../Downloads/...` path; now unset resolves to an obviously-fake sentinel that fails closed instead of silently pointing at a stranger's folder). |
| `READS_ENGINE_ADMIN_TOKEN` | REQUIRED SECRET | Bearer token gating every `/v1/games/*`, `/v1/grid/*` (write), `/v1/graph/*` (admin surface) route. | All admin routes reject with 401. Startup also validates minimum strength (32+ chars, not a known placeholder) and logs (not raises) a warning if weak. |
| `READS_ENGINE_ALLOWED_ORIGINS` | OPTIONAL CONFIG | Comma-separated exact origins for CORS. | Falls back to `DEFAULT_CORS_ORIGINS` = local dev origins + `https://reads.football`. Never a wildcard. |
| `READS_PUBLIC_GAME_ENABLED` | OPTIONAL CONFIG (operator switch) | Master kill switch for all `/v1/public/game*` routes. | Unset = `true` (matches every tested environment). `false` → clean `503 SERVICE_UNAVAILABLE` on every public route, admin routes unaffected. |
| `READS_PUBLIC_MODES` | OPTIONAL CONFIG | Comma-separated subset of code-certified modes (`draft_guess`, `championship_guess`) currently allowed. | Unset = every code-certified mode. Can only narrow, never expand, `PUBLIC_MODE_ALLOWLIST`. |
| `READS_ENGINE_PACKAGES_DIR` | OPTIONAL CONFIG | Where generated public/admin game packages persist. | Falls back to `gateway/storage/packages/` (repo-relative — fine locally, needs a mounted volume in production, see Database deployment). |
| `READS_ENGINE_LOG_DIR` | OPTIONAL CONFIG | Where operational/audit JSONL logs write. | Falls back to `gateway/storage/`. |
| `READS_ENGINE_PUBLIC_GAME_RATE_LIMIT` / `READS_ENGINE_PUBLIC_ANSWER_RATE_LIMIT` | OPTIONAL CONFIG | Per-minute caps for public fetch/answer routes. | Defaults 20/min fetch, 60/min answer. |
| `READS_ENGINE_PREVIEW_RATE_LIMIT`, `READS_ENGINE_GENERATE_RATE_LIMIT`, `READS_ENGINE_GRAPH*`, `READS_ENGINE_GRID*` | OPTIONAL CONFIG | Admin-surface rate limits. | Sensible defaults (30/10/30/10/30/15 per minute respectively). |
| `READS_ENGINE_DIR` (local override example) | LOCAL-ONLY | Developer's own machine path during local development. | N/A — never committed, never required to have a specific value in production beyond "point at a real Engine directory". |

No secret is committed anywhere in this diff — verified by reading every changed
file's actual content, not just `.gitignore`. `.gitignore` already excludes `.env`,
`.env.*` (except `.env.example`), and `*.sqlite*`.

## Database deployment

The 1.6GB `reads_football_v4.0.sqlite` (via the `Reads_v4_Database.sqlite` symlink
target) is **not** baked into the Docker image (`gateway/Dockerfile`'s own docstring
is explicit about this) — it ships on a Fly persistent volume mounted at `/data`,
populated once via `READS_ENGINE_BACKUP_AND_RESTORE.md`'s restore procedure, then
read by every Gateway instance through `READS_ENGINE_DIR=/data/engine`. Gameplay
itself is read-only against that database (`generation.generate()` only reads;
package storage and JSONL telemetry are the only writes, and both live in a
separate path from the canonical database file). SQLite concurrency: read-heavy
single-writer access is the right fit for this access pattern; the real observed
concurrency ceiling this session (see **Real finding** above) is the generation
lock, not SQLite itself — `PRAGMA integrity_check`/`foreign_key_check` both ran
clean against the live file under concurrent read load with no lock contention
observed.

## Gateway

- **Startup**: `check_engine_readiness()` runs at process start and logs a clear
  `[gateway] startup OK` / failure line to stderr (operator-visible, never the
  public response body).
- **Liveness** (`/v1/health`): process-alive only, minimal body, matches
  `Dockerfile`'s own `HEALTHCHECK`.
- **Readiness** (`/v1/ready`): checks DB presence/readability/integrity via a cheap
  indexed lookup (not a full scan), package-storage writability, and that the mode +
  capability registries loaded — verified this session to return only
  `reason_code` (fixed vocabulary), never a raw path or exception string, on failure.
- **Public kill switch / mode narrowing**: verified live (503 with switch off; modes
  correctly hidden/narrowed).
- **CORS**: verified live — production origin allowed, untrusted origin rejected at
  the header level.
- **Rate limits**: public fetch 20/min, public answer 60/min — generous enough for a
  real multi-tab/shared-NAT household session without being unlimited. The real
  near-term ceiling under concurrent load is the generation lock (see finding above),
  not these limits.

## Frontend configuration

- `reads-config.js` (new, untracked, meant to be committed): the one runtime
  surface for `engineGatewayBaseUrl`, `enableEngineDraftPilot`,
  `enableEngineChampionshipPilot`. Loaded before `app.js` in `index.html`. Contains
  no secret by construction (it's served as a public static asset).
- `app.js` reads it via `window.READS_CONFIG`, with strict `=== true` checks so a
  missing/malformed config fails every pilot closed, never open (Part 13, verified
  by reading the actual boolean comparison, not just the comment claiming it).
- Bounded 10s fetch timeout via `AbortController`, no automatic retry — explicit
  "Try Again" button only. Verified in the actual `renderEnginePilotScreen` error
  branch.
- Both pilot flags are `false` in the committed `reads-config.js` as shipped.

## Telemetry

`gateway/services/oplog.py`'s new `record_event()` writes structured JSONL lines
(`public_game_served`, `public_game_no_eligible`, `public_answer_submitted`,
`public_game_mode_disabled`) with `mode`, `difficulty`, `latency_ms`,
`generation_attempts`, and `correct: bool` for answers — never a raw free-text
answer, never a token. Verified by reading the call sites directly: the answer
event only ever passes `correct`, never the submitted string.

## Security

- **Admin**: no-token and wrong-token both rejected (401), verified live.
- **Answer truth**: verified live — no game-fetch response contains
  `correctIndex`/`answer`/QA metadata; `canonical_answer` only appears in the
  post-submission response, which is correct gameplay behavior, not a leak.
- **Errors**: `INVALID_MODE`, `INVALID_GAME_ID`, `SERVICE_UNAVAILABLE`,
  `GENERATION_BUSY` all verified to return clean, fixed-vocabulary JSON with a
  `request_id` — no traceback, no path, no SQL, in any response body observed this
  session.
- **CORS**: verified at the header level for both allowed and untrusted origins.
- **Secrets**: none committed; `.gitignore` coverage confirmed.
- **CSP**: does not exist in this project (`index.html` has no CSP meta tag).
  Documented per Part 28's explicit instruction rather than added as new scope.

## Performance (measured locally, real DB, real process — not a hosted environment)

| Route | Observed |
|---|---|
| `/v1/health` | sub-10ms |
| `/v1/ready` | sub-20ms (cheap indexed lookup, not a scan) |
| `/v1/public/modes` | sub-10ms |
| Draft fetch (`/v1/public/game?mode=draft_guess`) | ~0.03–0.64s single-request; degrades to `GENERATION_BUSY` under concurrency (see finding) |
| Championship fetch | comparable to Draft — same generation pipeline |
| Answer validation | low-single-digit ms (package lookup + string compare, no generation) |

These are local-machine numbers, not a hosted Fly measurement — no SLA is being
claimed from them, per Part 44's instruction not to invent numbers.

## Load smoke test

15 concurrent public-game-fetch requests against one local instance: 1 succeeded, 14
returned a clean `GENERATION_BUSY` (429), 0 crashed, 0 corrupted data, DB integrity
re-checked clean immediately after. See **Real finding** above — this is the one
concrete production-readiness gap this session surfaced that the prior
implementation hadn't (it isn't mentioned anywhere in the pre-existing code
comments). Recommend addressing before Stage 6 of the rollout below; does not block
Stages 0–5.

## Deployment

**NOT DEPLOYED.**

Blocker: neither the `fly` nor `flyctl` CLI is installed or authenticated in this
environment — verified directly (`fly auth whoami` / `flyctl auth whoami` both
"command not found"). No Fly account, app, or volume exists for this project yet.
`gateway/fly.toml` is configuration-only, exactly as its own header states, and is
otherwise ready to be used as the starting point for a real `fly launch` +
`fly deploy` once you have Fly access available. The exact manual steps required are
already itemized at the bottom of `gateway/fly.toml` (app creation, volume creation,
data restore, secrets, canary env values).

**DEPLOYMENT READY = YES** (pending the concurrency finding above, which is a
recommended fix before broad rollout, not a blocker to a controlled canary).
**ACTUALLY DEPLOYED = NO.**

## Canary rollout plan

Values below are literal `fly.toml [env]` / `fly secrets set` edits, not code changes:

- **Stage 0** — Deploy with `READS_PUBLIC_GAME_ENABLED=false` (already the checked-in
  default in `gateway/fly.toml`). Frontend flags OFF (already the shipped
  `reads-config.js` default). Verify `/v1/health` and `/v1/ready` only.
- **Stage 1** — Flip `READS_PUBLIC_GAME_ENABLED=true`. Frontend flags still OFF. Run
  the smoke test in this report directly against the production hostname (no real
  user reaches these routes yet — nothing links to them without a frontend flag).
- **Stage 2** — Enable Draft only: `READS_PUBLIC_MODES=draft_guess`, ship a
  `reads-config.js` with `enableEngineDraftPilot: true` to a small controlled
  audience (or just yourself, via the hidden `#draftpilot` route).
- **Stage 3** — Watch `public_game_served` / `public_game_no_eligible` /
  `GENERATION_BUSY` rates in the operational JSONL log for at least one real session
  under mild concurrency before going further.
- **Stage 4** — Add Championship: unset `READS_PUBLIC_MODES` (or set it to both),
  flip `enableEngineChampionshipPilot: true`.
- **Stage 5** — Observe both under the same telemetry watch as Stage 3.
- **Stage 6** — Broader rollout. Recommend resolving the generation-lock concurrency
  ceiling (see finding) before this stage specifically, since it's the stage where
  concurrent requests actually become likely.

## Rollback

- **Mode rollback**: set `READS_PUBLIC_MODES` to exclude the affected mode, or flip
  the corresponding `reads-config.js` flag to `false` and redeploy the static
  frontend (Netlify) — no Gateway change required either way.
- **Public gameplay rollback**: `READS_PUBLIC_GAME_ENABLED=false`, no redeploy of
  Gateway code, no frontend change (existing Reads is unaffected either way, verified
  in the fallback code path).
- **Gateway rollback**: redeploy the previous known-good Fly release (`fly releases`
  / `fly deploy --image <previous>`), no database change involved (gameplay is
  read-only against canonical data).
- **Frontend rollback**: restore the previous Netlify deployment; `reads-config.js`
  is a static asset like any other, so an old deploy simply serves its old flags.
- None of the above requires database surgery.

## Production readiness matrix

| CATEGORY | STATUS |
|---|---|
| Gateway build | READY |
| Engine data availability | READY (local); volume population is a documented manual step for actual Fly deploy |
| Database deployment | READY (strategy documented, read-only gameplay confirmed) |
| Secrets | READY (contract documented; none committed) |
| CORS | READY (verified live) |
| Rate limiting | READY (values documented; concurrency ceiling documented separately) |
| Health | READY (verified live, no leak) |
| Readiness | READY (verified live, no leak) |
| Telemetry | READY (structured events verified via code path) |
| Feature controls | READY (kill switch + mode narrowing verified live) |
| Fallback | READY (verified via code path + local error-state test) |
| Rollback | READY (documented, no DB surgery needed) |
| Draft | READY (verified live end-to-end) |
| Championship | READY (verified live end-to-end) |
| Frontend production config | READY (`reads-config.js` verified, fails closed) |
| Concurrent generation throughput | **NOT READY for broad rollout** — single global generation lock (pre-existing, not new this phase); safe degradation confirmed, but recommend a fix before Stage 6 |
| Actual production deployment | NO |
| Actual real-user enablement | NO |

## UI PHASE VERDICT

# UI PHASE GO

The engine integration architecture is proven end-to-end against a real running
Gateway with a real 1.6GB production database: startup validation, safe
health/readiness, the master kill switch, per-mode rollout narrowing, CORS,
telemetry, and frontend fail-closed configuration all behave exactly as designed
when actually exercised, not just as written. Security posture (admin auth, answer
truth, error responses, CORS) holds under direct testing. Fallback works — existing
Reads stays playable regardless of Gateway state. Rollback requires no database
surgery at any layer. Future mode migration is a code-certification + allow-list
change, not an architectural one.

The one real gap found this session — concurrent public generation requests
contending on a single admin-era lock — is a genuine production concern, but it is
scoped, understood, safely-failing, and does not block a controlled canary (Stages
0–5 above involve at most a handful of simultaneous testers). It should be fixed
before Stage 6's broader rollout, but does not require redesigning anything already
built.

## Next recommendation

Begin the Reads UI/Product Upgrade phase. In parallel, before Stage 6 of the canary
plan specifically: resolve the generation-lock concurrency ceiling (a request queue
or short bounded wait-and-retry is the smallest fix that doesn't touch the
architecture), and actually run `fly launch`/`fly deploy` once Fly credentials are
available, following the exact manual steps already itemized in `gateway/fly.toml`.

---

## Final status

- Test count: **151/151 passing**
- Deployment readiness: **YES** (with the one documented concurrency caveat)
- Actual deployment status: **NOT DEPLOYED** — no Fly CLI/auth in this environment
- Health/readiness: verified live, no leaks
- Security: verified live — admin auth, answer truth, error bodies, CORS all clean
- Performance: measured locally (see table above); no SLA invented
- Fallback: verified via code path — existing Reads unaffected by Gateway state
- Feature flag defaults: Draft OFF, Championship OFF, master public-gameplay switch
  ON by default (operator emergency switch, not the primary gate — the frontend
  flags are)
- Remaining blockers to a full production rollout: Fly authentication/credentials
  (external to this environment), volume population, and the generation-lock
  concurrency fix before Stage 6
- **UI PHASE GO**

This report is the only new artifact this session created. All implementation
changes described above (Parts 1–33, 51) were already present in the working tree
before this session began; this session's contribution was live verification, the
one concurrency finding, and this report. Nothing has been committed.
