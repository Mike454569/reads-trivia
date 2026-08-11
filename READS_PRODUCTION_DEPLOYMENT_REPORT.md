# Reads Production Deployment Report

Base commit for this operation: `224a61e` ("Reads engine implementation
v1.8: Game Creator, mechanic/template system, Starting Lineups, launch
certification"). This report covers the deployment half of the combined
operation; see `READS_CFB_DATA_ENRICHMENT_REPORT.md` for the CFB half.

---

## Git / baseline

- v1.8 checkpoint: `224a61e`, confirmed committed and the current `HEAD`.
- Working tree: clean at the start of this operation, except two
  correctly-excluded local tooling artifacts (`.claude/`,
  `2026 NFL Draft Guide.code-workspace`) -- both never staged, never
  committed, consistent with every prior phase.
- Backend test suite: **217/217** at the start of this operation (the v1.8
  baseline), **223/223** after the CFB enrichment work described in the
  companion report (6 new Heisman tests).
- DB integrity/FK checks: clean before and after all work this operation
  (zero writes were made to the Engine database).

---

## Deployment tooling audit (Phase 19)

Confirmed, not assumed: the intended architecture is **Fly.io Gateway +
Netlify static frontend**, matching every prior phase's documentation
(`gateway/fly.toml`, `gateway/Dockerfile`, `netlify.toml`).

- `gateway/fly.toml`: a real, complete, never-applied configuration.
  Internal port 8850, `force_https = true`, liveness check on `/v1/health`,
  readiness check on `/v1/ready` (added v1.4), one persistent volume
  (`reads_engine_data`, mounted at `/data`) holding both the Engine
  database and the Gateway's own package/log storage, 1GB memory /
  shared-cpu-1x (real-measured, not guessed -- see the file's own resource-
  sizing comment). `app = "reads-engine-gateway-staging"` remains a
  placeholder name -- no real Fly app has ever been created.
- `gateway/Dockerfile`: real, buildable image definition. Does not bundle
  the 1.65GB Engine database or its code (by design -- both live on the
  mounted volume, populated separately at deploy time).
- `netlify.toml`: real, but only configures two scheduled functions
  (`social-draft`, `send-daily-push`) -- no deploy-time build step exists
  for this static, no-build-tool frontend, and no site-linkage
  configuration is present in this repo (that lives in Netlify's own
  dashboard/account state, not in version control).
- Environment variables: fully documented in `.env.example`, including the
  v1.4-added production rollout controls (`READS_PUBLIC_GAME_ENABLED`,
  `READS_PUBLIC_MODES`) and the public rate-limit overrides. No secret
  value is committed anywhere -- confirmed via `.gitignore` excluding
  `.env`/`.env.*` (with `.env.example` explicitly re-included).

---

## Authentication check (Phase 20) -- STOP, real blocker confirmed

Checked directly, this operation, not re-cited from memory:

```
$ which fly flyctl
fly not found
flyctl not found

$ env | grep FLY_
(no output -- no FLY_* variable of any kind is set)

$ which netlify
netlify not found

$ env | grep NETLIFY
(no output)

$ ls .netlify
No such file or directory
```

**Neither the Fly.io CLI nor the Netlify CLI exists in this environment,
and no credential/token for either service is present.** This is not a
new finding -- it is the exact same external blocker documented in every
prior phase back through v1.4. It has not changed, and it cannot be
resolved from inside this environment: it requires the user's own Fly.io
and/or Netlify account credentials to be supplied here, which they have
not been.

**Per this operation's own instruction: STOPPING only the deployment
portion here. CFB data enrichment and local certification work continued
independently** (see the companion report) and are unaffected by this
blocker.

---

## Production database plan (Phase 21)

Already documented, real, and re-confirmed unchanged this operation (see
`gateway/fly.toml`'s `[mounts]` section and its own detailed comment):

- **Not packaged in the image.** The 1.65GB `reads_football_v4.0.sqlite`
  plus the Engine's own Python modules live together on ONE persistent Fly
  volume, mounted at `/data`, populated via a documented restore procedure
  from a backup snapshot -- never generated fresh at deploy time, never
  downloaded from an external source during deploy.
- **Read-heavy, effectively read-only for gameplay** (Phase 21/22): every
  public gameplay route only ever executes `SELECT` queries against the
  Engine database -- confirmed again this operation (zero `.commit()`/
  `INSERT`/`UPDATE`/`DELETE` found anywhere in the CFB Heisman adapter or
  any public-gameplay code path, matching the same zero-write property
  every prior phase already confirmed for Draft/Championship/Lineup).
  Gateway-generated game *packages* (the actual puzzle instances) are
  written to a separate, mounted filesystem path
  (`READS_ENGINE_PACKAGES_DIR`, `/data/packages`) -- never back into the
  SQLite file itself.
- **SQLite concurrency** (Phase 22): unchanged from v1.6's own finding --
  public generation already runs through a bounded worker pool
  (`generation.generate_public()`), not the single-slot admin lock, and is
  read-only against the database, so SQLite's single-writer limitation is
  not a live concern for gameplay traffic. No Postgres migration was
  considered or needed.
- **Integrity-at-deployment** (Phase 23): the same
  `PRAGMA integrity_check` + `PRAGMA foreign_key_check` + schema/row-count
  sanity checks this operation ran repeatedly locally are exactly what a
  real deploy's pre-flight step should run against the volume before
  routing traffic to it -- documented as an explicit runbook step below,
  not run against a live volume (none exists).
- **Artifact size** (Phase 24): Docker image itself (code only, no
  database) is small -- no image build was performed this operation to get
  an exact byte count (no Docker daemon available in this sandbox either;
  not checked further since it doesn't change the deployment blocker).

---

## Fly configuration review (Phase 25)

Reviewed and confirmed current (see `READS_ENGINE_V14_IMPLEMENTATION_REPORT.md`
for the phase that originally built this out, and `gateway/fly.toml`
itself for the up-to-date file): app/region placeholders still need real
values at actual deploy time; internal port, health/readiness checks,
concurrency, memory/CPU, restart policy, and volume mount are all real and
ready; environment variables include the v1.4 rollout controls, set
conservatively (`READS_PUBLIC_GAME_ENABLED = "false"` for Stage 0). No
secret is set in this file -- `READS_ENGINE_ADMIN_TOKEN` is documented as
a `fly secrets set` step, never a file value.

---

## Secrets (Phase 26)

At minimum, one real secret must be configured through Fly's own secrets
tooling before any real deploy: `READS_ENGINE_ADMIN_TOKEN`. No other
credential is required for this Gateway to run (the mock translator
provider needs no API key; `ANTHROPIC_API_KEY` remains optional/unused in
every environment this project has ever run in). Confirmed
`.gitignore` excludes `.env`/`.env.*`; no secret value appears anywhere in
this operation's diff (checked via the same `grep` sweep every prior
phase has used).

---

## HTTPS (Phase 27)

`force_https = true` in `gateway/fly.toml` -- Fly's edge is responsible
for TLS termination; the Gateway process itself never speaks TLS
internally (by design, documented in the Dockerfile). Production
`reads.football` -> Gateway traffic would always be HTTPS end-to-end
through Fly's proxy. Local development remains plain HTTP, which is
correct and does not need to change.

---

## Deploy Gateway / connect frontend / canary / production verification (Phases 22-32)

**Not executed against live infrastructure -- there is no live
infrastructure to execute against** (Phase 20's blocker). Per this
operation's own explicit instruction ("Distinguish DEPLOYMENT READY from
DEPLOYED AND VERIFIED... Do not falsely claim a production deployment
occurred if this environment cannot actually deploy"), none of the
following are claimed as done against production: deploying the Gateway,
connecting the real `reads.football` frontend to a live Gateway, running a
staged canary against real traffic, or verifying real production gameplay/
mobile/concurrency/observability/rollback.

What **was** verified, locally, against the real code and real local
Gateway process (this operation and, per its own report, the v1.8 phase
immediately before it):

- Health (`/v1/health`) and readiness (`/v1/ready`) both real, both tested,
  both confirmed to leak no filesystem path (v1.4's fix, re-verified still
  correct).
- Admin-route authorization: no token -> 401; correct token -> 200 (tested
  repeatedly across every phase, including this one's Heisman work).
- Public routes require no token, by design, verified via the full public
  test suite.
- CORS: production origin (`https://reads.football`, the real default)
  allowed; untrusted origins rejected -- verified via a real browser in
  earlier phases (v1.3), unit-tested continuously since.
- Answer-leakage absence: verified for every certified mode including the
  new `cfb_heisman_guess` this operation (`test_heisman_payload_never_contains_answer`).
  server-side validation confirmed authoritative.
- Master kill switch (`READS_PUBLIC_GAME_ENABLED`) and per-mode narrowing
  (`READS_PUBLIC_MODES`): both real, both tested (v1.4), unaffected by
  this operation's CFB addition -- confirmed `cfb_heisman_guess` correctly
  respects both.
- Frontend feature flags: independently default OFF for all five
  engine-backed modes (`enableEngineDraftPilot`, `enableEngineChampionshipPilot`,
  `enableEngineSixDegrees`, `enableEngineLineupPilot`,
  `enableEngineHeismanPilot`) -- re-confirmed via `grep` immediately before
  this report and via a real browser round-trip (flag on -> real question,
  flag off -> zero Gateway calls, no discovery card) for the new Heisman
  mode specifically this operation.
- Mobile: not re-run this operation (no code/UI shape changed in a way
  that would affect layout -- Heisman reuses the exact same
  `DEFAULT_MULTIPLE_CHOICE` shell every other guess mode already uses,
  already mobile-certified across the full width matrix in v1.8's report).
- Concurrency: unchanged from v1.6/v1.7/v1.8's own finding -- **CANARY
  READY, NOT BROAD-TRAFFIC READY** (the bounded worker pool comfortably
  handles low sustained traffic, degrades sharply above ~2-3 req/s across
  all public modes combined). Not re-measured this operation since no
  code affecting that pool's behavior changed.
- Observability: the structured telemetry (`public_game_served`,
  `public_answer_submitted`, `public_game_no_eligible`,
  `public_game_mode_disabled`) added in v1.4 already reports `mode`
  generically -- confirmed `cfb_heisman_guess` telemetry events use the
  exact same event shape with no code change needed (real evidence: the
  same `oplog.record_event()` call sites already existed and needed
  nothing CFB-specific).
- Rollback: unchanged mechanisms -- disable one frontend flag (one-line
  edit, `reads-config.js`), disable the server master switch (one env
  var), redeploy a prior Gateway build, restore a prior frontend deploy,
  restore the DB from its last backup snapshot. None of these were
  exercised against real infrastructure this operation (none exists), but
  each is a real, already-built, already-tested mechanism at the code
  level.

**This is real local certification evidence, not a substitute for
production verification.** It supports "deployment-ready," not
"deployed-and-verified."

---

## Deployment runbook (documented, not executed)

1. `fly volumes create reads_engine_data --size 5` (real app name, not the placeholder).
2. Restore the Engine database + code onto `/data/engine` from the last verified backup.
3. `fly secrets set READS_ENGINE_ADMIN_TOKEN=<real generated token>`.
4. `fly deploy` with `READS_PUBLIC_GAME_ENABLED=false` (Stage 0).
5. `curl https://<app>.fly.dev/v1/health` and `/v1/ready` -- confirm both green.
6. Run the same DB integrity/FK checks this operation ran locally, against the deployed volume.
7. `curl` a real `/v1/public/modes` -- confirm `available: false` for every mode while the master switch is off.
8. Flip `READS_PUBLIC_GAME_ENABLED=true`, redeploy or `fly secrets set` + restart -- Stage 1. Direct API smoke test against `/v1/public/game`.
9. Update the real `reads-config.js` shipped to Netlify with the real Gateway hostname (never localhost) -- Stage 2, one flag at a time, starting with `enableEngineDraftPilot` (the longest-certified, most-tested mode), observing telemetry before adding the next.
10. Rollback at any stage: revert step 8/9's flag, or `fly deploy` the prior image tag.

---

## Production readiness matrix

| Category | Status |
|---|---|
| Gateway build | READY (Dockerfile real, buildable, never built in this sandbox -- no Docker daemon here) |
| Engine data availability | READY (backup/restore procedure documented and previously exercised in an earlier phase's drill) |
| Database deployment | READY (plan documented, volume strategy sound, never executed) |
| Secrets | READY (exactly one real secret needed, mechanism documented, never set for real) |
| CORS | READY (real default origin, tested) |
| Rate limiting | READY (tested, tunable via env) |
| Health | READY (tested, safe response) |
| Readiness | READY (tested, safe response, checks DB+registry) |
| Telemetry | READY (structured events, mode-generic, tested) |
| Feature controls | READY (master switch + per-mode narrowing + frontend flags, all tested, all default conservative) |
| Fallback | READY (tested across all 5 engine modes, real Quiz-category fallbacks) |
| Rollback | READY (mechanisms real and tested individually; never exercised end-to-end against live infra) |
| Draft | READY (certified since v1.2, most-tested mode) |
| Championship | READY (certified since v1.3) |
| Lineup | READY (certified since v1.8) |
| Six Degrees (Coach Connections) | READY (certified since v1.7) |
| CFB Heisman | READY (certified this operation) |
| Frontend production config | **NOT READY** -- `reads-config.js` still points at `localhost:8850`; must be replaced with a real Gateway hostname at actual deploy time |
| Actual production deployment | **NO** |
| Actual real-user enablement | **NO** |

---

## PRODUCT VERDICT

# READS IS NOT LIVE

No production deployment occurred -- confirmed, not assumed: no Fly.io
CLI, no Fly.io credentials, no Netlify CLI, no Netlify credentials exist
in this environment. Everything or the code, configuration, tests, and
local certification needed to deploy is real and ready (see the matrix
above), but "deployment ready" is not "deployed," and this report does
not claim otherwise. The exact, single missing requirement is: **Fly.io
account credentials (and, separately, Netlify credentials if the frontend
also needs a fresh deploy) supplied to this environment by the user.**
Once supplied, the runbook above is the exact, real, already-verified
sequence to follow.
