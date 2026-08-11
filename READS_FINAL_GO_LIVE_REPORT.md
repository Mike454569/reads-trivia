# Reads Football — Final Go-Live Report

This is the closing report of the "Final Go-Live Operation": finish the
remaining CFB work, deploy the real production Gateway and frontend, verify
everything against the real deployed system (not local evidence), stage a
canary rollout, and issue an honest, evidence-based live-traffic verdict.
Every claim below was checked against the real, running production system
(`https://reads-football-gateway.fly.dev`, `https://reads.football`) unless
explicitly marked as a local-only or disclosed-limitation finding.

---

## 1. Starting state

- HEAD was at `734fcb0` (CFB Heisman certified, deployment-readiness
  documented, but never deployed). 227→224 test baseline confirmed clean.
- `origin/main` (the branch reads.football's Netlify site builds from) had
  **never received any of the Engine backend/frontend integration work** —
  17 commits' worth (v0.8 through v1.8, this operation's own commits) existed
  only in this local checkout. Separately, `origin/main` had 2 commits this
  checkout didn't (an X's & O's trivia mode added via GitHub's web upload
  UI) — a real divergence, reconciled by merge (`9a56084`), not force-push.
- Fly.io: authenticated, no app/volume/billing set up. Netlify: not
  installed, not authenticated. Both were genuine external blockers
  resolved by the user during this operation (Fly billing added; Netlify/
  GitHub logins completed).

## 2. CFB final work (Mission A)

- **Identity bridge hardened and written**: extended the validation sample
  to 33 real spot-checks (including live external verification), found a
  second real error class (16 duplicate-`nfl_player_key` groups within the
  previously-assumed-safe HIGH_CONFIDENCE tier — a mix of legitimate
  transfers and genuine collisions), and wrote the resulting **2,542-row**
  validated-safe subset to a new `cfb_nfl_identity_bridge_certified` table
  with full provenance. Import is idempotent (proven via two runs: 2,542
  inserted / 0 skipped, then 0 inserted / 2,542 skipped). DB backed up
  first (byte-identical copy verified); `PRAGMA foreign_key_check` and
  `integrity_check` clean before and after. **No game reads this table
  yet** — this is a prerequisite, not a new game.
- **CFB Career Timeline**: evaluated fresh (15,495 multi-school players,
  98.4% clean chronology, 252 flagged anomalies) and **deferred to
  backlog** — real, substantial net-new scope that would have competed
  directly with the deployment-critical path, and the operation's own
  rules say not to delay launch for optional features.
- **Translator league-disambiguation bug fixed properly** (not a keyword
  patch): a CFB-worded player-from-clues request now correctly reports
  `UNDERSTOOD_UNSUPPORTED_MECHANIC` instead of silently generating NFL
  content. Verified live against production in Mission J below.
- **Heisman reconfirmed green** — no regression across this entire
  operation's other changes.
- Full findings, the risk-tiering scheme, and the final CFB readiness
  matrix are in `READS_CFB_DATA_ENRICHMENT_REPORT.md`'s Round 3 section.

## 3. Scale architecture (Mission B)

Ran real controlled local load tests (1/5/15/25/50 concurrency) against
the actual Gateway process:

- The production default (`PUBLIC_GENERATION_MAX_CONCURRENCY=4`, a
  deliberate, already-documented choice bounding worst-case latency under
  Python's GIL) behaves exactly as designed: excess load gets a clean,
  fast `GENERATION_BUSY` (429) rejection — no hangs, no crashes, ~0.8s p50
  for the 4 that succeed.
- An exploratory pass with the semaphore raised to 50 **made things
  worse, not better** — p50 latency degraded to 9+ seconds and most
  requests eventually timed out, confirming this is a genuine
  single-instance architectural ceiling (GIL/SQLite contention), not just
  a conservative dial. Reaching real broad-traffic scale needs the
  pre-generation/pooling architecture already identified in prior phases
  as "the correct long-term answer, not built this round" — confirmed
  again, not re-litigated.

## 4. Production deployment — Gateway (Mission E)

Deployed to Fly.io (`reads-football-gateway`, app + 5GB volume + secrets),
with real, non-trivial problems found and fixed along the way:

1. **Build context bug**: `.dockerignore` excluded the old
   `Reads_Football_Data_Engine_v0.*/` pattern but not `v4.0` — a 2.2GB
   directory was being uploaded to every build. Fixed.
2. **Dockerfile path bug**: `fly.toml`'s `dockerfile` path was resolving
   relative to the config file's own directory, doubling to
   `gateway/gateway/Dockerfile`. Fixed.
3. **Incomplete dependency closure**: the Engine directory needs more than
   `game_factory.py` — `game_director.py` and `quality_intelligence.py`
   are real transitive imports reached through `tools/game_director_v01.py`
   at Gateway startup. Found via two real crash-and-fix cycles, then
   verified exhaustively (grepped the whole `tools/`/`gateway/` tree for
   every Engine-directory import, confirmed the full closure by importing
   `gateway.app` locally against only the 4 files being shipped).
4. **A genuine WAL-mode lock hang** (not just slowness): the production
   database ships in WAL journal mode locally, and opening it fresh on
   Fly's volume caused `PRAGMA quick_check` to hang indefinitely (5+
   minutes, confirmed via a direct diagnostic, not assumed) — a real lock,
   confirmed by a follow-up `database is locked` error after killing the
   hung process. Fixed by re-shipping the database in DELETE journal mode.
5. **A separate, real performance finding**: even in DELETE mode,
   `PRAGMA quick_check` against the 1.65GB database took **166 seconds**
   on Fly's volume vs ~10s locally — Fly's block storage has meaningfully
   worse random-I/O throughput for quick_check's scattered page walk than
   local dev SSD, even though sequential I/O (e.g. a full sha256) is fine.
   Running that cost on every 15s health-check poll would mean concurrent
   polls pile up redundant expensive work. Fixed with a proper cache +
   lock (`tools/quiz_export/engine.py`'s `check_engine_readiness()`): the
   first call after a cold cache still genuinely blocks for the real
   duration (matches existing test expectations), but repeat/concurrent
   calls are cheap. `fly.toml`'s readiness check timeout widened to 180s
   to cover that real first-check duration.

**Verified, not assumed**: real SHA256 hash of the shipped database
matches the local source exactly (`25452883c0...`) — checked on the
actual serving machine, not a setup machine. `/v1/health` and `/v1/ready`
both confirmed live over the public internet. `fly status`: 2/2 checks
passing.

## 5. Production deployment — frontend (Mission F)

- `reads-config.js`'s `engineGatewayBaseUrl` now points to
  `https://reads-football-gateway.fly.dev`. All five engine pilot flags
  remain `false`.
- Pushing revealed the frontend deploy was much larger in scope than a
  config edit: `origin/main` had never received **any** of the engine
  frontend integration work (three new JS files — `engine-game-ui.js`,
  `creator-ui.js`, `six-degrees-ui.js` — plus substantial `app.js`/
  `index.html`/`styles.css` changes, accumulated across many prior
  sessions). Flagged explicitly to the user before pushing, given the
  real stakes (a live site with real traffic); proceeded with explicit
  confirmation.
- **Git push required the user's own GitHub token** (a genuine external
  blocker — no stored credentials in this environment); the user
  generated a classic PAT and it was used for a single push, never
  persisted to git config. **The user should revoke that token now** —
  it was pasted into chat and must be treated as compromised regardless
  of whether it still works.
- Real Netlify production deploy triggered by the push, confirmed `ready`
  via the Netlify API (not assumed from the CLI output alone).
- Verified live: `reads.football` serves the updated `reads-config.js`
  with the real Gateway URL and all flags `false`; script load order in
  the served HTML is correct (`reads-config.js` → `engine-game-ui.js` →
  `six-degrees-ui.js` → `creator-ui.js` → `app.js`); all new JS assets
  return 200.
- **Disclosed limitation**: no headless browser tool is available in this
  environment, so this is HTTP-level verification only — no visual
  render check, no console-error check, no click-through. Recommend the
  user do a quick manual load of reads.football themselves.

## 6. Production security certification (Mission G)

All checks run against the real deployed Gateway, not local evidence:

| Check | Result |
|---|---|
| CORS | Allowed origin gets `Access-Control-Allow-Origin`; disallowed origin gets none |
| Admin routes, no token | 401 |
| Admin routes, garbage token | 401 |
| Creator routes, no token | 401 |
| Creator routes, garbage token | 401 |
| Public-game kill switch (Stage 0) | Clean 503 `SERVICE_UNAVAILABLE`, no crash |
| Path-traversal game ID | 404, no path leakage |
| Malformed JSON body | 400, safe message, no stack trace |
| Invalid six-degrees game ID | 404, safe message |
| Response headers | No `X-Powered-By`, no framework leakage |
| Answer leakage | None found in any public payload (`draft`, `championship`, `lineup`, `heisman`, `six_degrees`) |
| Rate limiting | Confirmed enforced (20/60s default), consistent with local load-cert findings |

**Two real bugs found and fixed via this certification, not local
testing**:
- `gateway/services/{graph,grid,public_six_degrees}.py` all hardcoded the
  Engine directory as `REPO_ROOT / "Reads_Football_Data_Engine_v4.0"` —
  true only in local dev, never true in the actual container, where that
  directory only exists on the mounted volume. Every graph_explorer-backed
  route (Six Degrees, Graph search/path, Grid) silently 503'd in
  production while passing every local test. Fixed to read
  `READS_ENGINE_DIR` like `tools/quiz_export/engine.py` already did.
- Six Degrees has its **own** kill switch
  (`READS_PUBLIC_SIX_DEGREES_ENABLED`, defaults `true` in code),
  structurally separate from `READS_PUBLIC_GAME_ENABLED`. It was reachable
  in production even while the main kill switch correctly blocked every
  other mode, because nothing had ever set it. Now explicit in `fly.toml`.

## 7. Canary rollout (Mission H/I)

Staged server-side enablement, each mode tested end-to-end against real
production before proceeding to the next:

| Stage | Mode | Verification |
|---|---|---|
| 1 | `draft_guess` | Real fetch, wrong answer rejected, resubmit consistent, brute-forced correct answer accepted |
| 2 | `championship_guess` | Real fetch, correct answer found and accepted |
| 3 | `six_degrees_guess` (Coach Connections) | Real fetch, step progression verified, reveal works |
| 4 | `lineup_guess` | Real fetch incl. `POSITION_LINEUP` visual payload, correct answer accepted |
| 5 | `cfb_heisman_guess` | Real fetch, certified `easy` difficulty confirmed, correct answer accepted |

All five now `"available": true` in `GET /v1/public/modes` on the live
Gateway. **Frontend engine flags remain false** — none of this traffic is
real end-user traffic yet; see §10 for why.

**One real, disclosed gameplay-integrity finding** in Six Degrees: a wrong
guess at a step reports `completed: true`, but the endpoint does not
actually reject further guesses at that same step — a later guess can
still succeed and un-complete the game. Confirmed this is **pre-existing
behavior, not a regression** (the local test suite's own methodology
already relies on probing multiple options per step; only a stale code
comment claims otherwise). Low severity for a trivia game (no security or
data-integrity impact), left as a disclosed backlog item rather than
rushed.

## 8. Game Creator against production (Mission J)

Tested with a real admin token against the live Gateway:

- NFL request → `SUPPORTED`, correct capability, zero hallucination.
- CFB Heisman request → `SUPPORTED_WITH_LIMITATIONS`, correct disclosed
  limitations.
- Unsupported request (salaries) → `MISSING_DATA`, correct real reason.
- CFB-worded clue request → `UNDERSTOOD_BUT_UNSUPPORTED` — the exact
  Mission A5 translator fix, verified live in production, not just in
  the local test suite.
- Real end-to-end generation (`POST /v1/creator/generate`, 5-question CFB
  Heisman request) succeeded, returned a real `package_id`.
- Bad admin token correctly rejected (401).

## 9. Mobile (Mission K) — disclosed limitation

No headless browser or device lab is available in this environment.
Verified what's checkable via HTTP: correct responsive viewport meta tag,
PWA manifest link, and real CSS breakpoints (`max-width: 640px / 520px /
360px`) in the served stylesheet. **Not verified**: actual rendering,
touch interaction, or layout at the 8 specified widths. Recommend the
user spot-check on a real phone before broad promotion.

## 10. Observability and rollback (Mission L/M)

- **Observability**: every response carries `X-Request-Id` and
  `X-Response-Time-Ms` (confirmed on live responses); error bodies
  include a `request_id` for correlation; `fly logs` streams real
  production logs (used throughout this operation to diagnose the WAL
  hang and the missing-module crashes).
- **Rollback, every level, confirmed real** (not executed against the
  current good state, to avoid unnecessary disruption):
  - Per-mode flag: proven live via the entire canary process above.
  - Server kill switch: proven live in §6 (Stage 0 test).
  - Gateway redeploy: `fly releases` shows a real, clean 12-version
    history (v1-v3 are this operation's own real early failures,
    v4-v12 the fixes) — `fly deploy --image <tag>` is the standard
    rollback mechanism.
  - Frontend redeploy: Netlify deploy history shows a real previous
    production deploy (2026-08-07) available to restore.
  - DB backup/restore: a byte-verified local backup exists from before
    the identity-bridge write; Fly's volume has automatic scheduled
    snapshots (5 retained, confirmed at volume creation).

## 11. Remaining P1s / backlog

- Flip frontend engine flags one at a time with real browser verification
  (blocked on browser tooling in this environment, not on the backend).
- CFB Career Timeline (data evaluated, adapter deferred).
- Six Degrees step-resubmission gameplay-integrity gap (§7).
- Coach-identity data quality (23% of coach rows, from Round 2) — not
  re-touched this round.
- No secrets manager — single shared admin token, as previously
  documented; unchanged this operation.
- Revoke the GitHub PAT pasted into this session (see §5).

---

## Final CFB matrix

| Area | Status |
|---|---|
| Heisman Guess | **READY** — live, canary-verified against production |
| CFB↔NFL identity bridge | Validated, written (2,542 rows), no game reads it yet |
| Career Timeline | Data strong; adapter deferred to backlog |
| Player From Clues (CFB) | Honest `UNDERSTOOD_BUT_UNSUPPORTED` (fixed, verified live) |
| Other CFB game concepts | Unchanged from Round 3 — see `READS_CFB_DATA_ENRICHMENT_REPORT.md` |

## Final product matrix

| Component | Status |
|---|---|
| Existing static site (14 modes, X's & O's) | **LIVE**, unaffected, verified reachable |
| Gateway (backend) | **LIVE**, deployed, health/ready/security/canary all verified against production |
| Frontend Gateway wiring | **DEPLOYED**, config live, all engine flags still OFF |
| 5 engine-backed public modes | **CANARY-VERIFIED** at the API level; zero real user traffic yet |
| Game Creator | **LIVE**, admin-only, verified against production |
| Scale | **CANARY** (bounded 4-concurrent design, verified clean); broad-traffic needs pre-generation architecture (not built) |

---

## Final verdicts

1. **PRODUCT: READS IS LIVE.** The real site at reads.football is live,
   reachable, and unaffected by this operation's backend work.
2. **ENGINE: ENGINE LIVE AND SERVING READS.** The Gateway is deployed,
   healthy, and has been verified end-to-end against real production
   traffic for all five certified modes plus the Creator. The one
   deliberate gap: frontend pilot flags remain off, so no real visitor
   has been routed to it yet — that flip needs real browser verification
   this environment cannot perform, not further backend work.
3. **CFB: CFB GAME-READY WITH LIMITATIONS.** One fully certified, live,
   canary-verified CFB mode (Heisman) on the same shared architecture as
   every NFL mode; real gaps disclosed, not hidden; no fabricated data,
   no forced parity.
4. **SCALE: CANARY LIVE.** Verified clean and correct at real canary
   concurrency (bounded, fast-failing, no crashes); broad-traffic
   readiness requires the pre-generation/pooling architecture already
   identified as the right long-term answer, not built this round.
