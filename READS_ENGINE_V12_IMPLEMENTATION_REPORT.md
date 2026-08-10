# Reads Engine implementation v1.2 — Connect the Engine to the App, Safely

**Status: implementation complete, tested, NOT yet committed.** Per the v1.2
completion rule, this report is presented for review before any commit is
made.

---

## Git baseline

Verified starting point: commit `6c02671` ("Reads engine implementation
v1.1: extend historical PLAYED_FOR coverage"), HEAD of `main`, working tree
clean before this phase began. `git log --oneline -5` immediately before
starting:

```
6c02671 Reads engine implementation v1.1: extend historical PLAYED_FOR coverage
0bc1a88 Reads engine implementation v1.0: expand historical canonical player identity
382eedd Reads engine implementation v0.9: add HOF All-Pro Pro Bowl Grid coverage
2c72401 Reads engine implementation v0.8: extend NFL roster coverage and Grid draft support
505e667 Checkpoint before v0.8: v0.7 Gateway graph + Grid roster verification port
```

v1.1 baseline re-verified before touching anything: 100/100 backend tests
passing, DB integrity clean, `PLAYED_FOR` covering 1999-2026, Grid honestly
at 17/21 criteria, frontend completely untouched by any prior phase.

As v1.1's own report framed it: *"the primary blocker is no longer football
truth… it is application delivery architecture."* v1.2 exists to resolve
exactly that — connect the real Reads frontend to the Gateway without ever
trusting the browser with truth it shouldn't have.

---

## What v1.2 actually is

A new, separate, **public** route family (`/v1/public/*`) sitting alongside
the existing admin-only Gateway, plus a single new frontend mode
(hidden route `#draftpilot`, feature-flagged, default OFF) that consumes it.
**Scope: NFL draft-guessing only.** Grid and Six Degrees are explicitly
untouched (Parts 34/35) — see "What was deliberately NOT done" below.

Nothing about question generation was reinvented: `/v1/public/game` calls
the exact same `generation.generate()` → `tools.director_v02.pipeline.run()`
path `/v1/games/generate` already uses, with a pre-resolved spec dict
instead of natural-language translation. One generator, two doors.

---

## Public API architecture

Three new unauthenticated routes in `gateway/app.py`:

| Route | Purpose | Auth |
|---|---|---|
| `GET /v1/public/modes` | Lists public-safe modes (currently: `draft_guess`) | None |
| `GET /v1/public/game?mode=&difficulty=&seed=&exclude=` | Fetches a real, QA-passed game | None |
| `POST /v1/public/game/answer {game_id, answer}` | Validates a guess server-side | None |

None of the three have `Depends(require_admin)` — deliberately. Safety
instead comes from a combination of:

1. **A hard mode allow-list** — `config.PUBLIC_MODE_ALLOWLIST = frozenset({"draft_guess"})`,
   cross-checked at import time against `public_game.py`'s own
   `PUBLIC_MODES` dict via an `assert` (drift guard: the two can never
   silently diverge). Requesting anything else returns one of two distinct,
   honest codes: `INVALID_MODE` (400, not a real capability) or
   `MODE_UNAVAILABLE` (404, a real internal Director capability —
   `championship_guess`/`player_from_clues` — just not yet public).
2. **Dedicated rate limiters**, separate from every admin limiter:
   `PUBLIC_GAME_RATE_LIMIT_MAX=20/min` (generation-backed, tighter),
   `PUBLIC_ANSWER_RATE_LIMIT_MAX=60/min` (cheap lookup, looser). Both
   env-overridable, both real `SlidingWindowRateLimiter` instances wired
   through `Depends(...)`, same mechanism every existing limiter uses.
3. **Strict request validation** — `PublicAnswerRequest` uses
   `model_config = ConfigDict(extra="forbid")`; an unexpected field (e.g.
   a client trying to send its own `score`) is rejected with 400, not
   silently ignored.
4. **An allow-list response shaper**, not a deny-list — see Security below.

### Reusing `package_id` as the game identifier

Rather than invent a new session/token system, `/v1/public/game` reuses
`gateway/services/packages.py`'s existing `package_id` (`GGP:<24-hex-sha256>`)
directly as the public `game_id`. It's already a content hash, already
strictly regex-validated before any filesystem path use
(`_safe_filename_for_id()`), already has atomic storage — reusing it
satisfies "prevent obvious tampering without unnecessary cryptographic
complexity" (Part 7) for free: forging a valid-but-unissued `game_id` would
require finding a real sha256 preimage.

---

## Security — explicit confirmation

Each of these was **verified by direct testing this phase**, not inferred
from reading the code:

- **No admin token ever reaches the browser.** Confirmed two ways: (1)
  `grep`'d `app.js`, `sw.js`, `index.html` for the token, `Bearer`, and
  related strings — zero matches; (2) real Playwright network capture of
  every request the browser made during a full pilot round (fetch, answer,
  next-question, retry-after-failure) — the admin token string never
  appeared in any request header or body.
- **No direct SQLite/DB access from the browser.** The browser only ever
  calls `/v1/public/*`; all Engine DB access stays server-side inside
  `generation.generate()`, unchanged from every prior phase.
- **No answer leakage.** `_public_view()` in `public_game.py` is the *only*
  function allowed to shape a fresh-game response, built as an **allow-list**
  (`game_id, mode, competition, difficulty, title, instructions,
  payload:{prompt,options}, metadata:{seed,version}`) — not a deny-list.
  `correctIndex`, `answer`, `source_ids`, `provenance`, `funnel`,
  `qa_checks_performed`, `notes` are structurally excluded, so a future
  field added to the internal package shape can't leak by accident.
  Verified by: a dedicated unit test (`test_game_payload_never_contains_answer`)
  that checks both raw-text substring absence *and* exact key-set equality,
  plus real Playwright inspection of actual response bodies during E2E
  runs — zero forbidden substrings found in any captured response.
- **`notes` (which can contain identifying detail) is only ever returned
  after a real guess**, from `validate_public_answer()` — never from
  `get_public_game()`. Matches the one existing convention this pilot
  borrows: Quiz's `q.notes` is likewise only shown post-answer.
- **CORS is env-configurable, not a wildcard.** `DEFAULT_CORS_ORIGINS` now
  includes `https://reads.football` by default (a deliberate policy change
  this phase explicitly authorizes — see `config.py`'s rewritten comment),
  plus the existing local dev origins. An untrusted origin (tested:
  `https://evil-scraper.example.com`) is never reflected back in
  `Access-Control-Allow-Origin`. Admin routes are unaffected regardless —
  CORS controls which origins can *read* a response, not who can guess the
  bearer token, so loosening CORS for the new public routes changes nothing
  about admin-route security.
- **Errors never leak internals.** `test_public_errors_never_contain_admin_secret`
  confirms an error response contains no token, no `sqlite`, no `/Users/`
  path — same contract every existing route already honors.

### Orphaned documentation found (noted honestly, not silently fixed or blindly trusted)

`gateway/fly.toml` cites a `READS_ENGINE_PUBLIC_EXPOSURE_GATE.md` file for
"don't expose the Gateway publicly" reasoning — confirmed via `find`/`grep`
that this file does not exist anywhere in the repo. `config.py`'s old CORS
comment cited `READS_ENGINE_HOSTING_READINESS.md` for CORS reasoning that
file doesn't actually contain (it only has disk/memory sizing). Both are
now noted honestly in the rewritten `config.py` comment rather than either
blindly trusted or silently dropped. Neither is a security problem by
itself — just a docs/reality gap worth someone's attention eventually.

---

## Real bugs found and fixed (via actually running the integration, not code review)

Four real, non-trivial bugs surfaced only by executing the real system —
exactly the class of bug unit tests alone would not have caught:

1. **Director validator requires `difficulty` inside the spec dict itself**,
   not just as `generate()`'s separate kwarg — omitting it produced
   `BLOCKED_INVALID_SPEC`. Fixed in `public_game.py` by setting
   `call_spec["difficulty"] = difficulty or "any"` before every generate call.
2. **Fallback screen-state bug**: `enginePilotFallbackToQuiz()` correctly
   populated `state.quiz`, but never set `state.screen = 'quiz'` (every
   other caller reaches `startQuizRound()` via `goToMode('quiz')`, which
   does that separately) — so `renderAll()` kept rendering the dead pilot
   screen. Caught by actually clicking the fallback button in a browser;
   fixed by adding the explicit assignment.
3. **Service worker HTML-masking bug**: with the Gateway down, `sw.js`'s
   fetch handler intercepted the failed `GET /v1/public/game` request and
   silently resolved with the cached `index.html` instead of a real network
   error — turning a clean "Gateway unreachable" into a confusing
   `"Unexpected token '<'"` JSON-parse error. Caught by actually killing the
   Gateway process and testing in a browser. Fixed with a narrow,
   path-based exclusion (`/v1/public/` in the URL) alongside the existing
   Firebase exclusion, plus a `CACHE_VERSION` bump (`v18`→`v19`).
4. **Two bugs found this session, during Part 25/38 re-verification, after
   the above three were already fixed:**
   - **`IndexError` in `_public_view()`** — `game_director_v01.py` sets
     `qa_status: "PASSED"` whenever `contract_failures` is empty, which is
     also true when zero questions were exported at all (e.g. a narrow
     `difficulty` filter matching no candidate for a given seed's sample —
     validating an empty list has nothing to fail). The fetch loop treated
     that as eligible and indexed into an empty `questions` list. Confirmed
     this same "PASSED with 0 questions" behavior already exists in the
     pre-existing admin `/v1/games/generate` route too — **not a v1.2
     regression**, a pre-existing engine characteristic v1.2's stricter
     public boundary was the first thing to actually notice. Fixed by
     making `get_public_game()`'s retry loop treat empty-questions results
     as ineligible and retry with a new seed (up to `MAX_GAME_FETCH_ATTEMPTS`),
     same as any other ineligible attempt, only raising `NO_ELIGIBLE_GAME`
     once every attempt is exhausted. Re-verified: 127/127 tests still
     green, and repeated real calls now return a clean 503 instead of a 500.
   - **Broken "Try Again" button**: `renderEnginePilotScreen()`'s error
     state rendered `data-pilot-retry">Try Again</button>` — a stray `"`
     immediately after the attribute name with no matching opening quote,
     making the actual DOM attribute name `data-pilot-retry"` (with the
     quote literally part of the name), so `[data-pilot-retry]` and
     `dataset.pilotRetry` never matched. This button was never clicked in
     the prior session's E2E tests (only `data-pilot-fallback` was
     exercised on the error screen), so it shipped broken. Found this
     session by re-reading the real diff before writing this report, then
     confirmed with a real click test: before the fix, `[data-pilot-retry]`
     still matched 1 element via Playwright's lenient selector engine, but
     no visual/functional difference could be confirmed without a targeted
     network-request-count check. Fixed the stray quote; re-verified with
     the Gateway killed that clicking "Try Again" fires a real second
     `GET /v1/public/game` request (request count 1→2), confirming the
     click handler now genuinely fires.

---

## Known engine limitation (not a v1.2 bug — documented honestly)

`difficulty=easy` for `draft_guess` currently returns `NO_ELIGIBLE_GAME`
essentially always — direct survey of a 500-row deterministic candidate
sample found **zero** candidates ever graded `"Easy"` by the draft
adapter's difficulty scorer (131 Hard, 101 Medium, 0 Easy). This is a
pre-existing characteristic of the difficulty-scoring model from earlier
Director phases, reproduced identically through the unmodified admin
`/v1/games/generate` route — not something v1.2 introduced or should fix
in scope. Recommendation for whoever eventually works on Director's
difficulty scoring: either recalibrate the "Easy" threshold for this
predicate, or have the public mode listing/UI omit "Easy" as a selectable
difficulty for `draft_guess` until it does. `medium`/`hard`/`any` all work
correctly and were verified with real generated questions.

---

## Frontend — exact files touched and why

- **`app.js`** (+187 lines): the only frontend file with real logic changes.
  - `ENABLE_ENGINE_DRAFT_PILOT_V01` (default `false`) + `ENGINE_GATEWAY_BASE_URL`
    — the feature flag and the (local-dev-only, per-environment) Gateway
    origin. Necessary: this is the only mode in the app that talks to a
    network service instead of a local `data/*.js` file, so it needs an
    explicit off-switch and a configurable target.
  - `state.enginePilot` + `resetModeState()` entry — follows the exact
    existing pattern every other mode's state slot uses.
  - New ~140-line section (`enginePilotFetchJson`, `startEnginePilotRound`,
    `loadNextEnginePilotQuestion`, `pickEnginePilotAnswer`,
    `advanceEnginePilot`, `enginePilotFallbackToQuiz`, `renderEnginePilotScreen`)
    — the adapter itself. Necessary: this is the actual pilot mode.
    Deliberately reuses the existing `.quiz-question`/`.quiz-options`/
    `.quiz-option`/`.quiz-feedback` CSS classes verbatim — **zero new CSS**,
    per Part 12's "do not redesign" constraint.
  - `renderAll()` dispatch entry, `HIDDEN_ROUTES['#draftpilot']`, and 5 new
    `data-pilot-*` click-dispatcher lines — necessary wiring, follows the
    exact pattern `#clues`/`playerClues` already established.
- **`sw.js`** (+15/-1 lines): `CACHE_VERSION` bump + the `/v1/public/`
  fetch-exclusion described above. Necessary: without it, a real Gateway
  outage is silently masked as a confusing HTML-parse error instead of a
  clean, honest network failure.

Nothing else in the frontend was touched. No colors, typography,
navigation, personalization, scoring architecture, or existing mode was
modified, per Part 12/29's explicit constraints — confirmed by `git diff`
showing exactly these two files changed on the frontend side.

---

## Feature flag

`ENABLE_ENGINE_DRAFT_PILOT_V01`, default **`false`**, confirmed both by
reading the shipped source (`app.js:40`) and by direct browser testing:
navigating to `#draftpilot` with the flag off renders the home screen and
issues **zero** requests to the Gateway (`gw_calls: []`, confirmed via
Playwright network capture). Flipping it to `true` (local testing only —
never committed as `true`) enables the hidden route. Verified working
*after* the final revert-to-`false` cycle (Part 38's explicit requirement):
flipped back to `true` one more time, ran the full happy path again
(question → answer → next, zero leaks), then reverted to `false` for the
final, shipped state — confirmed via `grep` immediately before writing this
report.

Failure behavior (Part 20): flag ON + Gateway reachable → live pilot
question. Flag ON + Gateway unreachable → clean error screen with two
real options, "Try Again" (now genuinely functional — see bug #4 above)
and "Play NFL Draft History (Quiz) Instead" (a real, already-working,
engine-exported Quiz category — `data/quiz-engine-draft-production.js`,
zero network dependency). No infinite retry loop; every fetch either
resolves or lands on the error screen.

---

## Testing

**Backend: 127/127 passing** (`READS_ENGINE_DIR=... pytest gateway/tests/ -q`
→ `127 passed`). 100 pre-existing (untouched, unmodified) + 27 new in
`gateway/tests/test_public_game.py`, covering: no-auth-needed on all three
public routes, admin routes still 401 without a token (regression), answer
non-leakage (raw-text + key-set checks), correct/incorrect/case-insensitive
answer validation, unknown/malformed `game_id` → `INVALID_GAME_ID`,
extra-field rejection, `INVALID_MODE` vs `MODE_UNAVAILABLE` vs confirming
Grid/Six Degrees are absent from the allow-list, determinism (same seed →
same `game_id`+prompt; different seeds → different), invalid-difficulty
rejection, rate limiting on both limiters, CORS (production origin allowed,
untrusted origin not reflected), error-contract-never-leaks-secrets,
new-error-codes-registered, `/v1/capabilities` unaffected, and a
performance sanity check (answer validation `<1.0s`).

**Real local E2E (Playwright + Chromium, actual browser, actual network
capture)** — not unit tests, not code inference:

- Happy path: `#draftpilot` → Start → real question renders → click an
  option → real feedback renders → Next → real, *different* question
  renders (duplicate-exclusion via the `exclude` param genuinely worked).
  Screenshots taken and visually reviewed at each step.
- Gateway-down fallback: killed the Gateway process (`lsof -i :8850`
  confirmed nothing listening) → Start → clean error UI (not the
  `sw.js`-masked HTML-parse error) → "Try Again" fires a real second
  request (confirmed via request-count assertion, 1→2) → "Play NFL Draft
  History (Quiz) Instead" → real quiz question renders
  (`state.screen === 'quiz'`, `state.quiz.queue.length === 10`).
- Network/security inspection: every request/response during every run
  above captured and scanned for the admin-token string and forbidden
  answer-revealing fields — zero matches in every run.
- Flag-OFF / flag-ON / flag-OFF-again cycle: verified independently at
  each stage (see Feature flag section).
- Pilot data variety (Part 25): difficulty bands `easy` (correctly returns
  `NO_ELIGIBLE_GAME`, see Known limitation above), `medium`, `hard`, `any`
  all producing real questions; 12 additional real games sampled by
  distinct random seed showing genuine player-name variety (Jason Smith,
  Anthony Averett, M.J. Devonshire, James Casey, Kenny Moore, etc.) rather
  than a narrow happy-path set.
- Cross-mode regression (Part 30): Quiz, Speed, Grid, IQ Test each launched
  via a real nav-button click (not a direct hash — confirmed those modes
  aren't hash-routable, so the earlier draft of this test using direct
  hashes was itself corrected) — all four reach their correct screen with
  zero new console errors. The one console message observed identically
  across all four (`click.mp3` 404) was traced to a pre-existing missing
  sound-effect asset, unrelated to this phase's changes, reproduced even
  on a plain Quiz-mode click with the pilot flag off entirely.
- Source-level check: `grep`'d `app.js`/`sw.js`/`index.html` for the admin
  token / `Bearer` / related strings — zero matches, confirming the
  network-level finding at the source level too.

---

## Performance

Real measured latency against the local Gateway (6 real generation calls,
distinct seeds): `GET /v1/public/game` — **avg 0.274s, max 0.511s** (first
call includes Engine DB connection warmup; steady-state ~0.2s). `POST
/v1/public/game/answer` — **~0.002s** (confirmed cheap package lookup +
string comparison, no generation, consistent with the unit test's `<1.0s`
assertion). Across all testing this session: 8/8 consecutive `easy`
requests hit the fallback-worthy `NO_ELIGIBLE_GAME` path (a real, expected
count given the difficulty-scoring finding above — not a flake); the
fallback UI itself was exercised and confirmed working during the
Gateway-down test.

---

## Deployment readiness

- `READS_ENGINE_DIR` remains fully env-driven, no hardcoded machine paths
  (unchanged from every prior phase's pattern) — example local invocation:
  `export READS_ENGINE_DIR=/path/to/Reads_Football_Data_Engine_v4.0`.
- Admin token remains server-side only — confirmed by both source grep and
  live network capture (see Security).
- CORS: `READS_ENGINE_ALLOWED_ORIGINS` env var still overrides the default
  list; default now includes the real production Reads origin (deliberate
  v1.2 policy change, documented above).
- Public rate limits: `READS_ENGINE_PUBLIC_GAME_RATE_LIMIT` (default 20/min),
  `READS_ENGINE_PUBLIC_ANSWER_RATE_LIMIT` (default 60/min), both
  env-overridable.
- `ENGINE_GATEWAY_BASE_URL` in `app.js` is a local-dev value
  (`http://localhost:8850`) — a real deployment needs this edited to a
  real reachable Gateway URL, same as `SITE_URL` already requires per
  environment. Not automated in this phase (no build step exists in this
  app to inject it).
- Health checks (`/v1/health`, `/v1/ready`) unaffected, unchanged.
- Port/hosting config (`gateway/fly.toml`, `Dockerfile`) unchanged this
  phase.

---

## Engine readiness matrix (updated, Part 36)

| Mode | Engine data ready? | Generator ready? | QA ready? | Public API ready? | Frontend adapter ready? | **Live pilot?** | Fallback? | Safe next migration? |
|---|---|---|---|---|---|---|---|---|
| **Draft-guessing (NFL_DRAFT)** | Yes | Yes | Yes | **Yes (v1.2, new)** | **Yes (v1.2, new)** | **YES — first live pilot** | Yes (existing "NFL Draft History" Quiz category, zero network dependency) | Already migrated |
| Championship-guessing (NFL_CHAMPIONSHIP) | Yes | Yes | Yes | No (`MODE_UNAVAILABLE` by design) | No | No | N/A | **Best v1.3 candidate** — same tier as draft-guessing was pre-v1.2, no new architecture needed |
| Player-From-Clues | Yes | Yes | Yes | No | Partial (dev-only static-file swap exists, not a live fetch) | No | Existing static hand-authored version | Second-best v1.3 candidate, slightly higher QA cost (real-time uniqueness) |
| Six Degrees | Yes (1.5M edges) | Yes | Partial | No | No (no matching frontend mode exists) | No | N/A | New mode to build, not a migration — larger product scope than v1.3 should take on alone |
| NFL Grid | Partial (17/21) | No (admin QA only) | Yes | No (Part 34: explicitly not migrated) | No | No | Existing static Grid | Not yet — architecture question (content-pipeline vs. live API) still unresolved from v0.7 |
| CFB Grid | No | No | No | No | No | No | Existing static CFB Grid | No |
| Quiz / CFB Quiz (general) | No (only draft-guessing partially overlaps) | No | No | No | No | No | N/A | No |
| Blitz/Speed/Silhouette/IQ/Legends/Higher-Lower/X's&Os (NFL+CFB) | No | No | No | No | No | No | N/A | No |

---

## What was deliberately NOT done

- **Grid was not migrated to the public API.** Still admin-only, still
  17/21 criteria, completely untouched this phase (Part 34).
- **Six Degrees UI was not built.** The `/v1/six-degrees` route is
  unaffected and remains admin-only; no public route or frontend mode was
  added (Part 35).
- **Every other existing mode's static-file architecture is untouched.**
- **No v1.3 work was started.**

---

## Recommendation for Claude Code implementation v1.3 — Production Mode Migration + Certification

1. **Championship-guessing (NFL_CHAMPIONSHIP) is the safest next migration.**
   It sits at exactly the tier draft-guessing occupied before v1.2: real
   data, real tested generator, real QA, already reachable through the
   existing admin `/v1/games/generate` path. Migrating it means extending
   `PUBLIC_MODES`/`PUBLIC_MODE_ALLOWLIST` with a second entry and adding a
   second frontend adapter mode — the trust boundary, rate limiting, CORS,
   and error-contract work from v1.2 is fully reusable as-is, zero new
   architecture required.
2. **Player-From-Clues is the second candidate**, one tier down only
   because its real-time uniqueness QA is more expensive per-request than
   a simple guess-mechanic lookup — worth a dedicated look at whether that
   cost is acceptable under the same rate-limit model before committing to
   it in the same phase as Championship-guessing, or as its own follow-up.
3. **Do not attempt Grid or Six Degrees in v1.3.** Both have real,
   unresolved product/architecture questions (Grid's content-pipeline-vs-
   live-API fork from v0.7; Six Degrees having no frontend concept at all)
   that are bigger than an incremental migration — each deserves its own
   scoped phase.
4. **Recalibrate (or explicitly document) the "Easy" difficulty gap** found
   this phase for `draft_guess` before exposing a difficulty selector to
   real users — either fix the scorer's threshold or have the UI simply
   not offer "Easy" for this mode yet.
5. **Consider a lightweight telemetry pass** (game served / answer
   submitted / correct-incorrect / latency / fallback-used) before scaling
   pilot traffic — v1.2 has the hooks (`game_id`, `mode`, `difficulty` all
   present in every response) but no telemetry emission was added this
   phase (out of scope, not requested).
6. **Carry forward v1.1's still-open items** (`PFR:JohnTy00` unresolved,
   1999-2005 stat-row identity gaps, 1980-1998 `PLAYED_FOR` coverage,
   MVP/SB MVP/ROTY governance, CFB Grid zero engine work) as background,
   not blocking v1.3.

---

## Full regression checklist (Part 38)

| Check | Result |
|---|---|
| Backend test suite | 127/127 passing |
| DB integrity | Unchanged from v1.1 baseline (no DB writes this phase) |
| Admin routes still require auth | Confirmed (regression test + manual check) |
| Public routes require no auth | Confirmed |
| No admin token in browser (network) | Confirmed (real Playwright capture) |
| No admin token in browser (source) | Confirmed (`grep`, zero matches) |
| No answer leakage in fresh-game payload | Confirmed (unit test + real response inspection) |
| Answer validation is server-authoritative | Confirmed (`validate_public_answer` is the only place `correctIndex` is read) |
| Feature flag defaults OFF | Confirmed (source + live browser test) |
| Feature flag ON works after revert-and-recheck cycle | Confirmed |
| Gateway-down fallback works | Confirmed (real process kill + browser test) |
| Retry button works | Confirmed after fix (real request-count check) |
| Service worker doesn't mask Gateway errors | Confirmed after fix |
| Service worker doesn't cache dynamic pilot responses | Confirmed (`/v1/public/` excluded from cache-put path too) |
| CORS: production origin allowed | Confirmed |
| CORS: untrusted origin rejected | Confirmed |
| Rate limiting: game fetch | Confirmed (test forces limit to 3, sees 429s) |
| Rate limiting: answer validation | Confirmed |
| Determinism: same seed → same game | Confirmed |
| Duplicate-exclusion: `exclude` param works | Confirmed (real different question on Next) |
| Quiz mode unaffected | Confirmed (real click-through, correct screen, no new errors) |
| Speed mode unaffected | Confirmed |
| Grid mode unaffected | Confirmed |
| IQ Test mode unaffected | Confirmed |
| Home page / onboarding unaffected | Confirmed |

---

## Completion

Per the v1.2 completion rule: **implementation, testing, and this report
are complete. No commit has been made.** Working tree currently has these
real changes, not yet staged:

```
 M app.js
 M gateway/app.py
 M gateway/config.py
 M gateway/errors.py
 M gateway/models.py
 M gateway/services/grid.py
 M gateway/tests/conftest.py
 M sw.js
 M tools/director_v02/logs/audit_log.jsonl   (test-run noise — accumulated
                                               audit entries from every
                                               generate() call made while
                                               testing this phase; harmless,
                                               real telemetry, but flagging
                                               it explicitly since it's not
                                               a deliberate code change)
?? gateway/services/public_game.py
?? gateway/tests/test_public_game.py
```

Two local test servers were left running during this phase (Gateway on
`:8850`, static file server on `:8000`) — both will be stopped once this
report is reviewed, or sooner on request.

**Awaiting your review and explicit go-ahead before creating the v1.2
checkpoint commit. Do not begin v1.3 without your approval.**
