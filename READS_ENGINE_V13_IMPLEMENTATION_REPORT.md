# Reads Engine implementation v1.3 — Production Mode Migration + Shared Pipeline Certification

**Status: implementation complete, tested, NOT yet committed.** Per the
completion rule, this report is presented for review before any commit.

---

## Git

- v1.2 checkpoint hash: `26defc0` ("Reads engine implementation v1.2: add
  public game API and draft pilot"), confirmed via `git log` and `git show
  --stat HEAD` at the start of this phase.
- Working tree at that point: clean (`git status` → "nothing to commit,
  working tree clean").
- Working tree now (before this phase's commit): `app.js`,
  `gateway/config.py`, `gateway/services/public_game.py`,
  `gateway/tests/test_public_game.py` modified;
  `tools/director_v02/logs/audit_log.jsonl` modified with pure test-run
  telemetry (238 purely-additive lines, 0 deletions — confirmed via `git
  diff --stat` and grepping for removed lines) that will be `git restore`d
  before any commit, same as v1.2.

---

## Baseline

- Starting tests: **127/127** (re-run fresh at the start of this phase,
  matching the v1.2 report's own final count).
- Existing public API state: `/v1/public/modes`, `/v1/public/game`,
  `/v1/public/game/answer` — all real, all no-auth, `draft_guess` the only
  certified mode.
- Draft pilot state: `#draftpilot` hidden route, `ENABLE_ENGINE_DRAFT_PILOT_V01`
  default OFF, real engine-backed questions, server-side answer validation,
  mode-aware fallback to the "NFL Draft History" Quiz category.

---

## Championship capability audit (Part 1-3)

Real audit, not assumed from prior reports:

- **Underlying source**: `season_standings` table, `playoff_result` column
  (direct query — no Game Factory predicate exists for this domain, same
  as documented in `tools/quiz_export/adapters/championship.py`'s module
  docstring).
- **Adapter**: `tools/quiz_export/adapters/championship.py`, registered in
  `tools/director_v02/registry.py` as `("guess", "NFL_CHAMPIONSHIP",
  "TEAM_POSTSEASON_RESULT")` — the same `guess` mechanic and
  `_generate_guess_package` generate_fn as Draft, so it flows through the
  identical `game_director_v01.generate_package_from_spec()` core.
- **Mechanic**: 4-option multiple choice. Outcome vocabulary is a closed,
  5-value set: `WonSB`, `LostSB`, `LostCC`, `LostDV`, `LostWC` (mapped to
  human-readable labels e.g. "Won the Super Bowl"). Distractors sampled
  from the other 4 outcomes — never invented, always a real canonical
  label.
- **Real candidate survey** (direct call to `fetch_ordered_candidates` +
  `evaluate`, not inferred): **296 raw candidates considered, 296
  accepted, 0 rejected** — "the domain is a primary key by construction"
  (each team-season pair is already unique). Season range: **2002-2025**.
  Unique franchises: **32** (full NFL coverage). Outcome distribution:
  `LostWC` 108, `LostDV` 96, `LostCC` 48, `LostSB` 22, `WonSB` 22 — a
  distribution that matches the real shape of an elimination bracket
  (many first-round exits, few champions).
- **Difficulty distribution among accepted**: `Hard` 216, `Medium` 80,
  **`Easy` 0** — the same "zero Easy candidates" pattern v1.2 found for
  Draft, confirmed independently here for Championship. Not a bug; a real
  property of this difficulty scorer, reproduced through the unmodified
  admin path too (`generation.generate(..., difficulty="easy")` returns
  `qa_status: PASSED, question_count: 0` with an honest `shortfall_reason`).
- **Spot-checked 5 real outcomes against the raw table directly**: 2017
  Patriots (13-3, `LostSB` — Super Bowl LII loss to Philadelphia), 2015
  Broncos (12-4, `WonSB` — Super Bowl 50), 2007 Patriots (16-0, `LostSB` —
  Super Bowl XLII), 2019 Chiefs (12-4, `WonSB` — Super Bowl LIV), 2021
  Bengals (10-7, `LostSB` — Super Bowl LVI). All five are real,
  independently verifiable facts.
- **Ran the actual generation pipeline** (`generation.generate()`, the
  real Director path, not a stub): 3 real QA-passed questions produced,
  e.g. *"How did the Carolina Panthers finish the 2003 NFL season?" → "Lost
  the Super Bowl"* (real: 2003 Panthers lost Super Bowl XXXVIII to New
  England).
- **Known limitation, documented honestly**: `difficulty="easy"` has zero
  real candidates for this mode, same as Draft. Not weakened or
  manufactured — see "Certified difficulty enforcement" below for how the
  public API now handles this cleanly instead of wastefully.

**Conclusion: Championship guessing is at least as mature as Draft was
before v1.2** (zero rejections vs. Draft's real `TEAM_UNRESOLVED`/
`DUPLICATE_PLAYER` rejection categories) — confirming v1.1/v1.2's
recommendation was correct, re-proven with real evidence rather than
re-trusted from memory (Part 3's explicit instruction).

---

## Public architecture — what was actually generalized

### Mode registry (Part 4/30/34)

`gateway/services/public_game.py`'s `PUBLIC_MODES` dict now has two
entries (`draft_guess`, `championship_guess`), each carrying:
`competition`, `title`, `instructions`, `kind` (`"multiple_choice"` for
both), `certified_difficulties` (hand-verified, empirical — see below),
and the internal `spec` dict. `config.PUBLIC_MODE_ALLOWLIST` and
`KNOWN_NOT_YET_PUBLIC_MODES` were updated to match (`championship_guess`
moved from the latter to the former; `player_from_clues` remains the one
real, registered-but-not-yet-public capability).

**Why this isn't a `DraftGuessHandler`/`ChampionshipGuessHandler` class
hierarchy**, as Part 30's diagram sketches: both certified modes share the
*exact same* internal shape (`guess` mechanic → Game Factory/adapter → 4
options → `correctIndex`). Building separate handler classes for two modes
with byte-identical fetch/validate logic would be pure ceremony with zero
behavioral difference — directly against Part 30's own "do not
overengineer... for hypothetical future modes" caveat. What actually *was*
Draft-specific coupling in v1.2, and is what got fixed:
1. Only one registry entry existed at all.
2. There was no per-mode certified-difficulty check (a mode's metadata
   could silently claim a difficulty band with zero real candidates).
3. `/v1/public/modes` returned only `{mode, competition, title}` — too
   thin for a client to make a real choice between modes.

The `kind` field exists specifically so a future mode with a genuinely
different mechanic (e.g. real free-text) has a place to branch from,
without speculative branching code with no mode to exercise it yet.

### Shared game contract (Part 5)

Reviewed the v1.2 response shape for Draft-specific assumptions. Found
none in the shape itself — `payload.prompt`/`payload.options` and
`options[correctIndex]` are already generic across both mechanics (a
"guess the drafting team" and "guess the postseason outcome" are both
naturally 4-option multiple choice). The one real gap was metadata
richness (see mode registry above), not contract shape.

### Shared answer validation (Part 6/32)

`validate_public_answer()` required **zero mode-specific changes** — it
already took no `mode` parameter, loading whatever package `game_id`
resolves to and comparing against that package's own `options[correctIndex]`
label. Confirmed this now serves both modes correctly with real Championship
answers (team names vs. postseason-outcome labels — genuinely different
value spaces, same comparison logic: `strip().lower()` exact match).
`POST /v1/public/game/answer` remains the single route for both modes, per
Part 6's explicit preference over per-mode answer routes.

### Game ID / cross-mode tamper resistance (Part 7)

Re-audited with two real modes live. Because `validate_public_answer`
never accepts a client-declared `mode` at all, there is no "declared mode"
field for a client to lie about — the mode is implied entirely by which
package the `game_id` resolves to. Verified with a real test
(`test_cross_mode_game_id_stays_scoped_to_its_own_mode`): fetched one real
Draft game and one real Championship game, confirmed their real answers
differ (a team name vs. an outcome label), then submitted the
*Championship* answer against the *Draft* `game_id` — correctly judged
`False` against the Draft game's own real answer, never cross-contaminated.

### Contract versioning (Part 31)

Added `metadata.contract_version = 1` (a `CONTRACT_VERSION` module
constant), distinct from `metadata.version` (the internal Director
*package schema* version — a different, pre-existing concept). No
version-negotiation framework — just a stable integer a future client can
branch on if this response shape ever changes in a breaking way.

### Certified-difficulty enforcement (Part 20/21) — a real efficiency + honesty fix

New `_ensure_difficulty_certified()` check, run *before* any generation
attempt. Real problem this fixes: in v1.2, requesting `difficulty=easy`
for Draft silently burned all 5 retry attempts (each a real Engine DB
round-trip, ~0.2-0.5s) only to land on `NO_ELIGIBLE_GAME` every time — a
fact that was already known (0 real Easy candidates), not something that
needed re-discovering per request. Now: `easy` is rejected immediately with
`INVALID_REQUEST` and an honest message naming the real certified
difficulties. `"any"` always passes (it means "no filter", not a
difficulty-band claim). Verified for both modes directly:
`test_draft_uncertified_easy_difficulty_rejected_immediately`,
`test_championship_uncertified_easy_difficulty_rejected_immediately`
(both 400/`INVALID_REQUEST`, not a 503 after wasted retries), plus
`test_draft_certified_difficulties_actually_work` /
`test_championship_certified_difficulties_actually_work` confirming
`medium`/`hard`/`any` all genuinely return real games for both modes.

`/v1/public/modes` now reports real, certified difficulties per mode
(`["medium", "hard", "any"]` for both today) — never the internal
capability registry's `supported_difficulties` (which is
technically-supported-by-the-code, not empirically-has-real-candidates —
a different, more optimistic claim that would have been dishonest to
expose directly).

---

## Championship migration — actual results

- `championship_guess` fully live behind its own independent flag,
  end-to-end tested via real HTTP calls and real browser automation (see
  Browser certification below).
- Real question example: *"How did the San Francisco 49ers finish the
  2011 NFL season?"* (real 49ers 2011: 13-3, lost NFC Championship to the
  Giants).
- Real question example: *"How did the Tennessee Titans finish the 2017
  NFL season?"* (real Titans 2017: 9-7, lost Wild Card round to Chiefs).
- Fallback correctly routes to **"Super Bowl History"** (a real,
  already-loaded, hand-authored Quiz category — `data/quiz.js`, 60
  questions) — deliberately *not* `data/quiz-engine-championship-award-pilot.js`
  (a real engine-exported file that exists on disk but, like the equivalent
  Draft pilot file before `ENABLE_ENGINE_QUIZ_DRAFT`, was never wired into
  `QUIZ` — wiring it in would be a separate, unrequested content change
  outside this phase's scope).

---

## Optional third mode (Part 15) — stopped at two, with reasoning

Re-examined the v1.1/v1.2 readiness matrix's remaining candidates:

- **Player-From-Clues**: data/generator/QA all real and tested — but its
  mechanic is fundamentally *not* 4-option multiple choice (progressive
  clue reveal + free-text/search-based guessing). Migrating it would not
  reuse the shared adapter built this phase at all; it would require a
  genuinely new frontend build, failing Part 15's own "mechanically
  compatible... low frontend complexity" bar for an *optional* third mode
  in this phase.
- **Six Degrees**: real data (1.5M edges) and generator, but Part 17
  explicitly forbids building its UI in v1.3, and it has no existing
  frontend mode concept to adapt at all — a new-mode product decision, not
  an incremental migration.
- **Grid**: explicitly out of scope (Part 16).

**Decision: stop at two.** Draft and Championship already prove the
architectural question v1.3 exists to answer — two mechanically-identical-
shaped but *conceptually and data-wise completely different* engine
capabilities (NFL Draft picks vs. NFL playoff outcomes) both running
through one shared public API, one shared answer validator, and one shared
frontend adapter. A third mode that doesn't fit the same mechanic shape
would prove a different, narrower thing (whether the architecture can grow
a second *mechanic*, not whether it can grow a second *mode*) — legitimate
future work, not required to answer this phase's actual question.

---

## Security

Re-verified with two real modes live, largely via direct browser execution
(not just unit tests):

- **No admin-token leakage**: `grep`'d `app.js`/`sw.js`/`index.html` for
  the token/`Bearer`/related strings — zero matches. Real Playwright
  network capture across every scenario tested this phase (both pilots,
  both fallback paths, both retry paths) — zero occurrences in any request
  header or response body.
- **No answer leakage**: `test_championship_payload_never_contains_answer`
  (raw-text substring check + exact key-set equality, mirroring the v1.2
  Draft test) — passes for Championship too. Real response bodies
  inspected directly during browser testing — clean in every case.
- **CORS rejects untrusted origins — confirmed via a REAL browser, not
  just a unit test this time**: served the app from a second static server
  on `127.0.0.1:8001` (deliberately *not* in the Gateway's CORS allow-list)
  and attempted a real `fetch()` from that page. Result: `TypeError: Failed
  to fetch`, with the browser's own console logging the real CORS
  rejection: *"Access to fetch at
  'http://127.0.0.1:8850/v1/public/game?mode=draft_guess' from origin
  'http://127.0.0.1:8001' has been blocked by CORS policy: No
  'Access-Control-Allow-Origin' header is present..."* — genuine browser
  enforcement, not an assumption from reading `config.py`.
- **Rate limits**: confirmed the two public limiters are genuinely
  *shared* across modes (one bucket per client per route, not per
  mode) — a deliberate design decision (see Part 22 below), verified with
  a real test alternating `draft_guess`/`championship_guess` requests
  against the same limiter and observing 429s regardless of which mode was
  requested.
- **Abuse/enumeration (Part 23)**: submitted a path-traversal-shaped
  `game_id` (`../../etc/passwd`) from a real browser — safely rejected as
  a clean `404 INVALID_GAME_ID`, no crash, no path traversal (confirms
  `packages._safe_filename_for_id()`'s regex validation holds against a
  real malicious-looking input, not just a well-formed-but-unknown one).
  `/v1/public/modes` exposes only mode id/title/competition/kind/
  difficulties/availability — no puzzle inventory, no source tables, no
  QA/admin detail.
- **Tamper resistance**: see "Game ID / cross-mode tamper resistance"
  above.

---

## Frontend — exact files touched and why

- **`app.js`** (+120/-63 net across the touched region): the pilot section
  was generalized from a single Draft-hardcoded implementation into one
  shared adapter (`enginePilotFetchJson`, `startEnginePilotRound`,
  `loadNextEnginePilotQuestion`, `pickEnginePilotAnswer`,
  `advanceEnginePilot`, `renderEnginePilotScreen`, all unchanged in
  *behavior*) plus a new `ENGINE_PILOT_MODES` config table
  (`{draft: {...}, championship: {...}}`) that each function now reads
  from instead of hardcoding Draft's title/API-mode-id/fallback. New
  independent flag `ENABLE_ENGINE_CHAMPIONSHIP_PILOT_V01` (default OFF),
  new hidden route `#championshippilot`, and `enginePilotCurrentModeKey` (a
  small module-level variable tracking which pilot a not-yet-started
  screen refers to, resolved once at hidden-route entry). The rename
  `enginePilotFallbackToQuiz` → `enginePilotFallback` (now mode-aware,
  dispatching to whichever mode's own `fallback` function) was the one
  actual behavior-affecting change to existing Draft code — necessary
  because a single hardcoded "go to NFL Draft History" fallback can no
  longer be correct once Championship exists too (Part 12: never
  accidentally serve a Draft question under Championship UI). **No other
  frontend file was touched.** No new CSS, no colors, no typography, no
  navigation, no card redesign — the Championship pilot reuses the exact
  same `.quiz-question`/`.quiz-options`/`.quiz-option`/`.quiz-feedback`
  classes Draft already used, confirmed visually via real screenshots.
- **`sw.js`**: **zero changes this phase** — its `/v1/public/` fetch
  exclusion (added in v1.2) is path-based, not mode-based, so it already
  covered `/v1/public/game?mode=championship_guess` by construction.
  Confirmed via `git diff sw.js` (empty) and by directly re-running the
  Gateway-down fallback test against the Championship pilot: clean
  `"Failed to fetch"`, not the HTML-parse-error bug v1.2 fixed.

---

## Browser certification — actual scenarios tested (Part 25/39)

All via real Playwright + Chromium against a real locally-running Gateway
and static file server, not code inference:

1. **Both flags OFF**: `#draftpilot` and `#championshippilot` both fall to
   the home screen, zero Gateway calls from either. Existing Quiz mode
   loads its real setup screen unaffected.
2. **Draft ON / Championship OFF**: Draft pilot fully works (question →
   answer → feedback, `mode=draft_guess` confirmed in the real request
   URL); Championship route still falls to home with zero Gateway calls.
3. **Draft OFF / Championship ON**: Championship pilot fully works
   independently (`mode=championship_guess` confirmed in the real request
   URL, real question/answer/next-question cycle); Draft route still falls
   to home with zero Gateway calls.
4. **Both ON**: both pilots verified working within one shared browser
   session (same `BrowserContext`, same `localStorage`, confirmed via a
   direct equality check) — Draft played to a correct answer, then
   Championship played to a correct answer, real requests for both modes
   captured in the same session's network log.
5. **Correct answer / incorrect answer**: both real, both modes (unit
   tests + live browser).
6. **Retry**: verified for Championship specifically (not just relying on
   shared code) — killed the Gateway, clicked "Try Again", confirmed a
   real second `GET /v1/public/game?mode=championship_guess` request
   fired.
7. **Next game**: verified for both modes; Championship's duplicate-
   exclusion (`exclude` param) produces a genuinely different next
   question.
8. **Gateway unavailable**: both modes show the clean, mode-correct error
   screen (`"Failed to fetch"`, correct mode-specific fallback button
   label: *"Play NFL Draft History (Quiz) Instead"* vs. *"Play Super Bowl
   History (Quiz) Instead"*).
9. **Malformed game ID**: real browser-originated request with a
   path-traversal-shaped id → clean `404 INVALID_GAME_ID`.
10. **Untrusted CORS origin**: real browser-originated `fetch()` from a
    genuinely different origin, genuinely blocked by the browser (see
    Security above).
11. **Rate-limit response**: confirmed at the API level (real 429s
    observed); not separately re-verified from a browser UI perspective
    this phase (would require firing >20 real generation requests inside
    a live page in rapid succession — the backend behavior is what
    actually matters here and is directly tested).

One real methodology finding worth recording honestly: navigating the
*same* Playwright `Page` object from `#draftpilot` directly to
`#championshippilot` via `page.goto()` does **not** force a full page
reload, because the two URLs differ only by fragment — this is standard
same-document-navigation browser behavior, not an app bug, and it applies
to *every* hidden route in this app (`#stats`, `#clues`, etc.), not
something v1.3 introduced. Real cross-pilot verification used two tabs in
one shared browser context instead, which is also the more realistic
scenario since nothing in this app currently links between hidden routes
in-page.

---

## Mobile smoke test (Part 26)

Both pilots rendered at a 375×667 viewport (iPhone SE-class width). No
horizontal overflow (`document.documentElement.scrollWidth >
clientWidth` → `false` for both). Screenshots visually confirmed clean
layout, matching existing Quiz styling exactly — no redesign, no new CSS.

---

## Existing Reads regression (Part 27)

Re-verified via real browser clicks, both flags OFF: Quiz (setup screen
renders correctly), Speed, Grid, IQ Test, Study/Learn (via direct
`goToMode('study')`, since it's a conditionally-shown continue-card, not a
home-grid button) — all reach their correct screen with no new console
errors. Homepage/onboarding: fresh-visit onboarding modal still shows
correctly. Draft pilot itself (Part 14): re-verified fully working after
every generalization change described above — happy path, fallback, and
retry all still pass with the shared-adapter refactor in place.

---

## Performance (Part 29)

Real measured latency against the local Gateway:

| Call | Avg | Notes |
|---|---|---|
| `GET /v1/public/game?mode=draft_guess` | 0.264s | 5 real calls, distinct seeds |
| `POST /v1/public/game/answer` (draft) | 0.0018s | cheap package lookup, no generation |
| `GET /v1/public/game?mode=championship_guess` | **0.034s** | 5 real calls, distinct seeds |
| `POST /v1/public/game/answer` (championship) | 0.0017s | cheap package lookup, no generation |

Championship's fetch is noticeably faster than Draft's (~8x) — plausibly
because Draft's candidate evaluation (franchise/team-alias resolution per
row) is more expensive per-candidate than Championship's (each
`season_standings` row is already a resolved primary key with zero
rejections). Not investigated further — a real, honest observation, not a
problem to fix in this phase. No generation-retry pathology observed for
either mode at certified difficulties.

---

## Testing

- **Baseline**: 127/127 (start of phase).
- **New this phase**: 14 tests (5 real Championship fetch/answer/leakage/
  real-fact tests, 2 registry tests, 4 certified-difficulty tests, 1
  cross-mode tamper test, 1 contract-version test, 1 shared-rate-limit
  test).
- **Total**: **141/141 passing**.
- **Failures discovered and fixed during this phase**: none in the sense
  of bugs — 3 *pre-existing v1.2 test assertions* needed updating because
  they encoded "draft_guess is the only public mode" as a literal
  assertion, which stopped being true the moment Championship was
  certified (expected, not a regression): `test_public_modes_no_auth_needed`,
  `test_known_internal_but_not_public_mode_is_mode_unavailable`,
  `test_grid_and_six_degrees_are_not_public_modes`. All three updated to
  reflect the new two-mode reality and re-verified passing.
- **Final result**: `141 passed` (confirmed via a full, fresh
  `pytest gateway/tests/ -q` run at the end of this phase).

---

## Certification manifest (Part 33/34)

Three genuinely distinct states, kept from blurring together per Part 34's
explicit instruction. Source of truth for each: the real code, not a
separate hand-maintained file (avoids a second place these can drift out
of sync) — summarized here for review:

| Capability | Internal (registered)? | Public-certified? | Frontend-enabled (default)? | Source of truth |
|---|---|---|---|---|
| `draft_guess` (NFL_DRAFT/DRAFTED_BY) | Yes | Yes (v1.2) | Yes, flag default **OFF** | `director_v02/registry.py`, `public_game.py:PUBLIC_MODES`, `app.js:ENGINE_PILOT_MODES.draft` |
| `championship_guess` (NFL_CHAMPIONSHIP/TEAM_POSTSEASON_RESULT) | Yes | **Yes (v1.3, new)** | **Yes, flag default OFF (new)** | same three files, `.championship` entries |
| `player_from_clues` (IDENTIFY_FROM_CLUES) | Yes | No (`MODE_UNAVAILABLE`) | No (dev-only static-file swap flag exists, not a live fetch) | `director_v02/registry.py`; deliberately absent from `PUBLIC_MODES` |
| Grid QA (`/v1/grid/*`) | Yes (admin-only Gateway routes) | No (Part 16: out of scope) | No (existing static Grid, unchanged) | `gateway/services/grid.py` |
| Six Degrees (`/v1/six-degrees`) | Yes (admin-only) | No (Part 17: out of scope) | No (no frontend concept exists) | `gateway/services/graph.py` |

**Certification gate actually satisfied for both live modes** (Part 33's
checklist, verified per-mode this phase):

```
DATA_READY                 draft: yes   championship: yes (296/296, 0 rejections)
GENERATOR_READY             draft: yes   championship: yes (shared game_director_v01 core)
QA_READY                    draft: yes   championship: yes (qa_status PASSED, real spot-checks)
ANSWER_VALIDATION_READY     draft: yes   championship: yes (shared validate_public_answer)
PUBLIC_RESPONSE_SAFE        draft: yes   championship: yes (allow-list _public_view, leak tests)
RATE_LIMITED                draft: yes   championship: yes (shared bucket, tested)
CORS_SAFE                   draft: yes   championship: yes (real browser block confirmed)
FEATURE_FLAGGED             draft: yes   championship: yes (independent flags, both default OFF)
FALLBACK_READY              draft: yes   championship: yes (mode-aware, real Quiz category)
FRONTEND_ADAPTER_READY      draft: yes   championship: yes (shared adapter, zero new CSS)
REAL_BROWSER_TESTED         draft: yes   championship: yes (full matrix, this phase)
REGRESSION_GREEN            draft: yes   championship: yes (141/141, existing Reads unaffected)
```

---

## UI UPGRADE READINESS

| Area | Status | Notes |
|---|---|---|
| Engine truth | READY | Two mechanically-shared, data-wise independent modes both certified with real evidence. |
| Public API | READY | Generalized mode registry proven to extend cleanly to a second mode with no route/contract rework. |
| Answer validation | READY | Single shared validator handled both modes with zero mode-specific code. |
| Frontend adapter | READY | One shared adapter (fetch/render/state-machine) now powers two conceptually different games via config, not duplication. |
| Feature flags | READY | Independent per-mode flags verified across all 4 on/off combinations, both default OFF. |
| Fallback | READY | Mode-aware, real hand-authored equivalents for both modes, verified via real Gateway-down tests. |
| Security | READY | No token/answer leakage, real browser-confirmed CORS rejection, tamper resistance re-verified with two modes live. |
| Multi-mode support | READY | This is what v1.3 set out to prove, and did — real evidence above, not inferred. |
| Regression safety | READY | 141/141, existing Reads modes (Quiz/Speed/Grid/IQ/Study/onboarding) unaffected. |
| Production deployment | **NOT READY** | Unchanged blockers from v1.2: `ENGINE_GATEWAY_BASE_URL` is still a local-dev value requiring manual per-environment editing (no build step exists to inject it); no telemetry emission has been added yet (v1.2's Part 28 hooks exist in the response shape but nothing emits events); Gateway hosting/scaling for real public traffic has not been addressed in any phase. These are real, separate blockers from the integration-architecture question v1.3 answers — not reasons to call the architecture itself unready. |

**Overall: the integration architecture is certified. Production
deployment readiness (hosting, telemetry, environment config) is a
separate, smaller, well-scoped remaining gap — not an architecture
question anymore.**

---

## Next mode roadmap (Part 37)

| Mode | Data | Generator | QA | Public API complexity | Frontend complexity | Recommended? |
|---|---|---|---|---|---|---|
| Player-From-Clues | Ready (tested) | Ready (tested) | Ready | Low (same registry pattern) | **High** (new mechanic: progressive clues, free-text/search guess, not 4-option choice) | Yes, but as its own phase — first real test of the architecture's SECOND mechanic shape, not a quick add. |
| Six Degrees | Ready (1.5M edges) | Ready (`graph_explorer.random_six`) | Partial | Low-Medium | **High** (no existing frontend concept at all — new product surface, not a migration) | Yes, but as a product decision + build, not an incremental certification step. |
| NFL Grid | Partial (17/21 criteria) | No (admin QA only, not a live generator) | Yes | Unknown (content-pipeline-vs-live-API fork unresolved since v0.7) | Medium-High (richer intersection semantics per Part 16) | Not yet — architecture question predates v1.3 and is unrelated to the mode-registry work done here. |
| CFB Grid | Not ready (zero engine work) | No | No | N/A | N/A | No. |
| Quiz-domain modes generally (Blitz/Speed/Silhouette/Legends/etc.) | Not ready (no engine backing) | No | No | N/A | N/A | No — these are a different category of work (new domains), not migrations of existing capabilities. |

---

## Recommendation

Two fundamentally different engine-backed modes (draft picks vs. playoff
outcomes — different tables, different vocabularies, different real-world
facts) now run through one public API, one mode registry, one answer
validator, and one frontend adapter, each independently flagged and each
falling back safely. That is exactly what v1.3 set out to prove, and the
evidence above — not assumption — supports it.

# PRODUCTION CERTIFICATION + UI UPGRADE PHASE

is the right next step, not another backend/data migration project. The
remaining blockers (`ENGINE_GATEWAY_BASE_URL` environment wiring,
telemetry emission, Gateway hosting for real public traffic) are
deployment/ops work, not integration-architecture work — they should be
resolved as part of standing the product up for real users, likely
alongside or just before the UI phase, not as a v1.4 repeat of this
phase's certification work.

---

## Completion

Per the completion rule: **implementation, testing, and this report are
complete. No commit has been made.** Both feature flags confirmed default
OFF in the current source (`grep` re-run immediately before writing this
report). Working tree has these real changes, not yet staged:

```
 M app.js
 M gateway/config.py
 M gateway/services/public_game.py
 M gateway/tests/test_public_game.py
 M tools/director_v02/logs/audit_log.jsonl   (test-run telemetry noise --
                                               will be `git restore`d before
                                               any commit, same as v1.2)
```
Plus this report file, new/untracked.

Both local test servers (Gateway `:8850`, static file server `:8000`, and
the temporary untrusted-origin server `:8001`) have been stopped.

**Awaiting your review and explicit go-ahead before creating the v1.3
checkpoint commit. Do not begin the UI redesign without your approval.**
