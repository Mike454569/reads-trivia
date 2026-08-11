# Reads Engine — Claude Code Implementation v1.6

## P0 Hardening + Homepage / FYP / Game Discovery

Reads Football Engine: v4.0. Claude Code implementation phase: v1.6.

Three sequential objectives, in order: (A) fix or materially improve public
generation concurrency, (B) get conclusive mobile evidence for the engine shell,
(C) build the first real product upgrade — unified game discovery — on top of both.
Neither P0 exposed an architectural blocker, so all three phases ran.

---

## Git

- **v1.5 checkpoint**: `5791d8c18e9186003561636899fa641e3e2c9b22` — "Reads UI
  implementation v1.5: add reusable engine game shell"
- **Starting working tree**: clean except the pre-existing, unrelated untracked
  `2026 NFL Draft Guide.code-workspace`.
- **Working tree now**: `app.js`, `gateway/config.py`, `gateway/services/generation.py`,
  `gateway/services/public_game.py`, `gateway/tests/test_public_game.py`,
  `READS_UI_BACKLOG.md` modified; this report new. All uncommitted per the
  completion rule.

## Baseline

- **151/151 → 155/155**: backend suite re-confirmed green at each checkpoint (151
  entering v1.6, unchanged from the v1.5 checkpoint since v1.5 touched no backend
  files; 155 after this phase's 4 new concurrency tests — re-verified passing
  multiple times throughout this phase, most recently right before writing this
  report).
- Draft/Championship flags: confirmed OFF in the committed `reads-config.js`
  throughout (flipped on three separate times this phase for live testing —
  concurrency load tests, mobile matrix, discovery click-through — reverted every
  time, confirmed via `git diff` showing no change against the committed file).
- `engine-game-ui.js` confirmed loading and working via the real running app
  (extensively, see Phases A/B/C below).
- No answer leakage, no admin-token leakage: reconfirmed live (see Security below).
- Existing homepage/FYP/major game modes: read in full for the Part C1 audit, then
  spot-verified via real browser regression after the discovery integration (Quiz
  full round-trip, Grid launch, both unmodified and unaffected).

---

## Phase A — Public Generation Concurrency

### A1-A4: root cause, traced fresh and cross-checked against an existing proof

Traced the entire public generation path line by line:
`gateway/services/public_game.py` → `gateway/services/generation.py`'s
`generate()` (previously: single `_generation_lock` + `ThreadPoolExecutor(max_workers=1)`)
→ `tools/director_v02/pipeline.py`'s `run()` (its own docstring: "This module
never touches the Engine database directly") → for both certified public modes
(`draft_guess`, `championship_guess`), `registry.py` dispatches to
`_generate_guess_package` → `tools/game_director_v01.py`'s
`generate_package_from_spec()` — **the one function that touches the Engine
database for candidate generation** (its own docstring says so explicitly).

Read every line of that function: it opens exactly one connection
(`engine.connect()`), calls `adapter.safety_check(c)` and
`_engine_version_fingerprint(c)` (both confirmed pure `SELECT`), delegates
candidate sourcing to `adapter.fetch_ordered_candidates(c, seed)` (grepped
`tools/quiz_export/adapters/draft.py` and `championship.py` for
`.commit()`/`INSERT`/`UPDATE`/`DELETE` — zero matches in either), closes the
connection, then does everything else (QA, contract validation, package
construction) as pure in-memory Python. **Zero writes, confirmed by direct code
reading, not assumption.**

While tracing this, found that this exact conclusion was **already independently
proven and documented** in `tools/quiz_export/engine.py`'s `connect()` docstring
(Director v0.7, Part E): *"empirically verified this milestone that the ENTIRE
Gateway generation path... performs ZERO writes to the Engine database."* This
phase's fresh trace and that prior proof agree.

**What the old lock actually protected**: `game_factory.py` (the Engine's own
NL-description-driven Game Factory CLI, a *separate* code path with real
`.commit()` writes to `game_factory_specs`/`game_factory_candidates`/
`game_factory_qa`/`puzzle_catalog`/`game_factory_publications`) — but neither
public mode's `generate_fn` ever calls into it. The single-slot lock was a
blanket, maximally-conservative policy applied uniformly to ALL generation
(admin and public alike), calibrated for the admin surface's broader risk
surface, never specifically re-examined for the public path's much narrower,
already-read-only-in-practice one.

### A2/A4: public vs. admin, SQLite safety

Public generation is fully read-only against canonical truth — confirmed above.
Concurrent reads against one SQLite file (via independently-opened,
independently-closed connections, each already carrying the existing
`busy_timeout` PRAGMA) is exactly the access pattern SQLite is built to support.
No shared mutable Python state either: `duplicates.DuplicateGuard` and the
distractor RNG (`engine.seeded(...)`) are both fresh, function-local instances
per call, never module-level globals.

### A5/A6: the fix

Added `generate_public()` alongside the unchanged `generate()` in
`gateway/services/generation.py`, both now sharing a `_run_pipeline_bounded()`
helper (a `threading.Lock` and a `threading.Semaphore` share the same
`acquire(blocking=False)`/`release()` shape, so one function serves both call
sites without duplicating the submit/timeout logic). `generate_public()` uses a
**separate, bounded, non-blocking** `threading.Semaphore` + its own
`ThreadPoolExecutor`, sized via `config.PUBLIC_GENERATION_MAX_CONCURRENCY`
(new config, default 4). The admin path (`generate()`, `_generation_lock`,
`_executor`) is **completely untouched** — same object, same single-slot
behavior, verified with a dedicated regression test
(`test_admin_generation_still_single_slot_after_public_change`). `gateway/services/public_game.py`
now calls `generation.generate_public()` instead of `generation.generate()` —
a two-line change, `call_spec` always built from this module's own certified
templates, never arbitrary caller input.

Backpressure (Part A6): non-blocking acquire, so a caller at capacity gets an
immediate, clean `GENERATION_BUSY` — never an unbounded queue, never unbounded
threads (both `_executor` and `_public_executor` cap their own `max_workers`).

### A7-A9: real concurrency test results (real Gateway, real 1.6GB DB)

| Concurrent requests | SUCCESS | GENERATION_BUSY | Other errors | P50 latency | P95 latency | Max latency |
|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 785ms | 785ms | 785ms |
| 5 | 4 | 1 | 0 | 3,896ms | 3,915ms | 3,915ms |
| 15 | 4 | 11 | 0 | 31ms* | 4,567ms | 4,567ms |
| 25 | 4 | 21 | 0 | 59ms* | 4,238ms | 4,248ms |
| 50 | 4 | 46 | 0 | 129ms* | 3,930ms | 3,963ms |

\* P50 lands among the fast-rejected `GENERATION_BUSY` responses when busy
requests dominate the batch; the 4 successful requests in every row above
completed in ~4s regardless of batch size — the pool ceiling is exactly 4,
deterministically, at every concurrency level tested.

**Before (v1.4/v1.5, same style of test)**: 15 concurrent → 1 success, 14
`GENERATION_BUSY` (93% failure). **After**: 15/25/50 concurrent → 4 successes
every time (a hard, predictable, configured ceiling — not degrading further
under heavier load), rest fail cleanly and fast.

**Mixed-mode (A8)**: 10 Draft + 10 Championship concurrent → 4 successes total
(shared pool, not 4+4 separate). This is deliberate, not a gap: the real
constraint is process-wide CPU/GIL capacity, not a per-mode resource, so a
shared pool is the honest design — separate per-mode pools would double the
worst-case concurrent CPU contention for zero real throughput gain. Neither
mode is artificially blocked *because of* the other; both compete fairly for
the same real resource.

**Answer validation under concurrency (A9)**: 8 concurrent answer submissions
across 8 distinct real games (mixed Draft/Championship) — all 8 resolved
correctly, each `canonical_answer` verified to belong to its own game's own
option set (zero cross-game contamination). Verified at both the pytest level
(`test_concurrent_answer_validation_no_cross_contamination`) and a separate
live HTTP-level load test.

**A real, honest finding this phase surfaced**: concurrent execution of the SAME
8 requests took *longer* in total wall time (9.2s) than running them
sequentially (6.06s) — CPython's GIL serializes the CPU-bound candidate-scanning
work inside `generate_package_from_spec()`, so more threads doesn't mean more
real parallelism for this specific workload. This directly informed the pool
size: `PUBLIC_GENERATION_MAX_CONCURRENCY` was set to **4, not a larger number**,
specifically because the frontend's own `ENGINE_PILOT_FETCH_TIMEOUT_MS` (v1.4,
10000ms) means a pool sized for maximum throughput (e.g. 8, worst-case ~9.2s)
would leave under 1 second of margin before a real player's browser gives up —
4's worst-case ~4.0s leaves a comfortable ~6s margin. This reasoning is
documented directly in `gateway/config.py`'s comment for future re-tuning.

### A10: failure testing

Forced: invalid game ID under load (clean `INVALID_GAME_ID`, no crash), disabled
mode (clean `INVALID_MODE`), capacity exhaustion at 50 concurrent (clean,
deterministic `GENERATION_BUSY` for 46/50, zero crashes, zero hangs). DB
integrity (`PRAGMA foreign_key_check` + `PRAGMA integrity_check`) confirmed clean
immediately after the heaviest load test.

### A11: exit verdict

# P0-A: CANARY READY. NOT BROAD-TRAFFIC READY.

Public generation concurrency went from "near-total failure under any real
simultaneous traffic" (1 success out of 15) to "a hard, predictable,
configuration-visible ceiling of 4 concurrent successes, failing cleanly and
immediately beyond that, with zero corruption and zero cross-contamination at
any tested load up to 50 concurrent requests." This is safe for an initial
canary (a handful of real simultaneous testers, which is what Stages 2-5 of the
v1.4 rollout plan actually describe). It is explicitly **not** validated for
open/heavy production traffic — the GIL-bound throughput ceiling is real and
would need a deeper architecture change (multiprocessing or a pre-generated
candidate pool) to raise meaningfully. Logged as a P1 backlog item, downgraded
from P0 given the real, verified improvement — not silently closed.

---

## Phase B — Authoritative Mobile Certification

### B1: tooling

Attempted `pip install playwright` (succeeded) + `playwright install chromium`
(**failed**: `OSError: [Errno 86] Bad CPU type in executable` — the bundled
Node driver is arm64-only, and this sandbox cannot execute arm64 binaries at all,
confirmed directly: `arch -arm64`/`arch -arm64e` both report "Unknown
architecture"). Rather than stop there, installed `websocket-client` (pure
Python, no native/arch dependency) and wrote a ~100-line Chrome DevTools
Protocol client (`cdp.py`) to drive the real, already-working headless Chrome
directly via its own remote-debugging port — real
`Emulation.setDeviceMetricsOverride` (genuine mobile/touch emulation, not just a
narrow window), real navigation, real DOM queries, real clicks via
`element.click()`, real screenshots.

### B2-B9: methodology and results

Tested the **real, unmodified** `index.html`/`app.js`/`engine-game-ui.js` (not a
harness) — Draft and Championship pilots temporarily flag-enabled, real Gateway
running, real 1.6GB database. Full required viewport matrix: 320, 360, 375, 390,
430, 768, 1024, 1440px. At each width: Start screen, real fetched Question
screen, real Answered screen (after a real click on a real answer option) — 3
checks × 8 widths × 2 modes = **48 total overflow checks**.

**Result: 0 of 48 showed horizontal overflow** (`document.documentElement.scrollWidth
> clientWidth`, checked programmatically, not by eye). Real production
question/option text captured during the run (not fixture data): questions up to
60 characters ("How did the Pittsburgh Steelers finish the 2025 NFL season?"),
options up to 38 characters ("D. Lost in the Conference Championship") — all
rendered cleanly with no truncation at every width down to 320px, satisfying the
text-stress-test requirement (B6) with real data rather than synthetic fixtures.
Touch targets measured 36-42px tall depending on breakpoint (logged as a P2
backlog polish item — below the 44px Apple HIG guideline, above WCAG's 24px
minimum, not a blocker).

A real methodological mistake happened mid-phase and is disclosed rather than
hidden: an early full run of the matrix, using a Chrome profile reused from
earlier in this session, silently rendered the plain homepage instead of the
Draft/Championship screens for all 48 checks (root cause never fully isolated —
most likely leftover profile/service-worker state from many prior test sessions
sharing that same profile directory). This was caught by manually inspecting
screenshots rather than trusting the "0 overflow" summary at face value, and
resolved by re-running the full matrix with a completely fresh Chrome profile —
the run whose results are reported above were independently re-verified via
direct screenshot inspection (not just the automated overflow-report summary)
before being trusted.

### B10: CSS changes made

**None.** The v1.5 "possible cropping" concern did not reproduce under real
device-metric emulation — closed with evidence, no speculative CSS touched, per
the explicit instruction.

### B11: exit verdict

# P0-B: CLOSED.

The real page has been tested across the full required viewport matrix with real
device-metric emulation, zero critical clipping/overflow found, real production
long-text content confirmed rendering cleanly at every width. The v1.5 "possible
cropping" finding (both for the engine shell and, newly checked this phase, the
onboarding modal) did not reproduce and is attributed to that prior test's
harness/methodology, not the shared CSS.

---

## Phase C — Homepage + FYP + Game Discovery

### C1: audit (before changing anything)

Read `renderHome()` and its constituent pieces in full. Finding, contrary to the
v1.5 audit's more cautious framing: **the existing homepage/FYP system is
already genuinely strong**, not just "has an identity worth preserving":

- `LEAGUE_MODES` (nfl/cfb) is already a real, if implicit, game-metadata
  registry: `id`/`icon`/`title`/`desc`/`featured`/`difficulty` per mode, one
  unified list every card grid, the mode-picker sheet, "Continue Playing," and
  the recommendation engine all already read from.
- `recommendedModeHtml()` ("For You") is a real recommendation engine, not a
  placeholder: deterministic per day+username (seeded PRNG, not `Math.random()`,
  so it doesn't change on every re-render), prioritizes never-played modes
  ("New to you"), falls back to least-played once everything's been tried
  ("Keep it fresh") — using real play-count signals from `state.stats`.
- `continuePlayingCardHtml()` reads real `localStorage` session history, not
  fabricated data.
- Team personalization (`favoriteTeamGreeting`, 32 real NFL teams + 70+ real CFB
  programs with real colors/chants) is a genuinely well-built existing system.

Given this, the right scope was **not** a homepage rebuild — Part C1's own
instruction ("do not redesign strong areas just to make the diff bigger")
applied directly. The real, demonstrated weakness was narrow and specific:
engine-backed modes were completely invisible to this entire system, reachable
only via a hidden hash route while their own flags happened to be on.

### C5-C6: game discovery model

Extended the existing `LEAGUE_MODES.nfl` registry — did not build a parallel
one. Added `ENGINE_DISCOVERY_ENTRIES`, built conditionally on each pilot's
existing `ENGINE_PILOT_MODES[x].flagOn()` check (from `engine-game-ui.js`,
unchanged), so the two new entries are **entirely absent** from the registry —
not shown-disabled — when a flag is off. `id` matches the Gateway's own public
API mode ids (`draft_guess`/`championship_guess`) for one consistent vocabulary
client- and server-side. `title`/`desc` are read directly from
`ENGINE_PILOT_MODES` (one source of truth, no copy duplicated). An internal-only
`engineMode` field (never read by `modeCardHtml()`, only by `goToMode()`'s new
routing branch) is the one thing that distinguishes an engine-backed entry
internally — nothing in the rendered card, the mode-picker sheet, or the
recommendation/continue-playing logic treats it differently from any other mode.
This is Part C6's own framing achieved literally: a player sees **GAME**, never
"old game vs. engine game."

### C7/C12/C13: cards, availability, gating

No new card component was built — `modeCardHtml()` (unchanged) already produces
a visually consistent card from `icon`/`title`/`desc`/`difficulty`, so engine
modes render pixel-identical in style to every hand-authored mode (verified live,
see screenshots). Icons reused from the existing set (no new SVG assets):
`flag` for Draft, `lombardiTrophy` for Championship — both already existed for
other purposes. Availability gating is binary and structural, not a rendered
"coming soon" state (Part C13): a flag being off means the entry doesn't exist in
the array at all, so there is no dead card, no click-to-nowhere, ever.

### C9/C17: FYP

No new recommendation code was written — extending `LEAGUE_MODES.nfl` was
sufficient for `recommendedModeHtml()` to include engine modes in its existing
real "unplayed → new, least-played → fresh" logic automatically, verified live.
Empty-FYP behavior (Part C17) is unchanged and was already correct: the
existing `if (!state.name) return ''` guard means the card simply doesn't render
for a player without personalization set up — not broken, not fabricated data.

### C14: continue playing

`goToMode()`'s new engine-mode branch calls the exact same
`lsSet('nflTriviaLastMode', mode)` / `window.__fbSync.logPlay(mode)` bookkeeping
`enterMode()` already does for every other mode — verified live: playing Draft
via the new discovery card, then returning home, correctly showed "Continue
where you left off → NFL Draft History: Guess the Team."

### C20/C31: Gateway-independence

Confirmed live with the Gateway process killed entirely: the homepage (including
both discovery cards) rendered with zero errors and zero missing content —
building the registry is a pure local boolean check
(`ENGINE_PILOT_MODES[x].flagOn()`), no network call. Clicking into Draft with no
Gateway running correctly reached the existing (v1.5) polished error state
("Couldn't load that — please try again.") with working Try Again/fallback
buttons — no crash, no dead end.

### What was deliberately NOT built this phase

Per Part C32/C34's explicit scope limits and this phase's own C1 finding (the
homepage was already strong): no featured-game hero treatment, no new browse
categories ("Quick Games"/"Challenge Games"), no profile/achievements changes,
no Firestore schema changes, no new writes beyond the same `localStorage`
key every other mode already uses. All logged as backlog items with honest
reasoning, not silently dropped — see `READS_UI_BACKLOG.md`.

---

## Visual changes

Two new cards in the existing NFL Modes grid (visible only when their flags are
on) — otherwise **zero** visual change to the homepage. Confirmed via direct
comparison: with both flags off (the shipped default), the NFL mode grid's card
list is exactly the same 14 titles as before this phase, in the same order.

## Responsive

Desktop and mobile both verified via the Phase B viewport matrix (discovery
cards use the exact same `.mode-card` component already proven clean at every
width) plus a dedicated discovery-flow screenshot at 390px showing the new cards
rendering identically to existing ones.

## Accessibility

No new accessibility surface introduced — `modeCardHtml()` is unchanged, so
every existing property (real `<button>`, keyboard-reachable, consistent focus
styling) applies to the new cards automatically. Not independently re-audited
beyond that inheritance.

## Performance

No new network calls added to homepage render (the registry check is a boolean
read, not a fetch). No additional DOM nodes rendered when flags are off (array
`.concat()` of an empty list). Clicking a discovery card reuses the exact
already-measured Draft/Championship fetch latency from Phase A (no new code path
in the fetch itself).

## Regression

- Backend: 155/155 (151 + 4 new concurrency tests), unchanged files outside
  `gateway/config.py`, `gateway/services/generation.py`,
  `gateway/services/public_game.py`, `gateway/tests/test_public_game.py`.
- Frontend: Quiz (real full round-trip: start → real question rendered → answer
  clicked → feedback shown → zero overflow), Grid (launch verified), both
  unmodified by this phase and confirmed still working live. `app.js`'s diff is
  additive-only (one new registry block, one new early-return branch in
  `goToMode()`) — no existing function bodies were altered.
- Flags-off homepage: byte-for-byte identical mode-grid contents to pre-v1.6,
  confirmed via live DOM query.

## Security

- No admin token anywhere in frontend source (unchanged, re-grepped).
- No answer leakage: verified live through the new discovery-card path
  specifically (not just the pre-existing hash-route path) — fetched a real
  question via the homepage card, confirmed no `correctIndex`/`answer` in the
  response.
- Server-side validation remains authoritative — the discovery integration adds
  zero new client-side logic that touches correctness; it only decides which
  screen to route to.
- CORS/rate-limiting/mode-allowlist: untouched by this phase except the new,
  narrowly-scoped `PUBLIC_GENERATION_MAX_CONCURRENCY` config (documented above),
  which affects only how many concurrent generation jobs run, not who can reach
  them.

---

## UI Backlog

See `READS_UI_BACKLOG.md` (updated this phase) for the full prioritized list.
Headline changes: both P0s resolved (one closed, one downgraded to P1 with a
clear "canary vs. broad-traffic" distinction); "Homepage/FYP + game discovery"
removed as a P1 (done); new P1s added for the deeper concurrency architecture,
touch-target sizing, and a small nav/contextual-help gap for engine modes found
while wiring in the discovery cards.

## Recommended v1.7

# v1.7 — Deeper Public Generation Concurrency (multiprocessing or pre-generated pool)

Not another UI phase. The homepage/discovery work this phase did is real and
complete for its stated scope, and the existing FYP system turned out to already
be strong enough that no further homepage UI work is urgently justified. The
actual highest-leverage next step, directly gating whether Draft/Championship can
ever move from "canary" to real broad rollout, is resolving the GIL-bound
throughput ceiling identified in Phase A — either a multiprocessing-based worker
pool or a pre-generated/cached candidate pool, both already scoped as concrete
options in this report and the backlog. Once that's closed, a genuine v1.8
product phase (featured-game treatment, browse categories, Six Degrees UI, or
whichever candidate the next audit finds strongest) has a production-ready engine
underneath it instead of a canary-only one.

---

## Final status

- Backend test count: **155/155 passing**
- Browser test count: no Playwright (confirmed unavailable — arm64-only driver,
  sandbox cannot run arm64 binaries); real coverage instead via a hand-built pure-Python
  CDP client driving real headless Chrome against the real, unmodified app: 48
  mobile-viewport overflow checks (0 failures), 1 full discovery-to-play
  click-through, 1 Gateway-down resilience check, 1 Quiz full-round-trip
  regression check, 1 Grid-launch regression check, plus the Phase A HTTP-level
  concurrency/answer-validation load tests
- Concurrency before/after: 15 concurrent public fetches, 1 success → 4 successes
  (deterministic ceiling, verified up to 50 concurrent)
- Concurrency P0 status: **CANARY READY, NOT BROAD-TRAFFIC READY** (downgraded
  from P0 to P1, real verified improvement, real remaining ceiling documented)
- Mobile P0 status: **CLOSED** (authoritative real-device-emulation evidence, 0/48
  overflow)
- Homepage improvements: engine-backed modes now discoverable through the
  existing, already-strong FYP/recommendation/continue-playing system; zero
  visible change when both flags are off
- FYP improvements: none needed beyond registry extension — the existing
  recommendation engine was already real and already correctly picked up the new
  entries
- Discovery improvements: one unified game registry, no "engine mode" concept
  exposed to players
- Frontend files touched: `app.js` (additive only)
- Backend files touched: `gateway/config.py`, `gateway/services/generation.py`,
  `gateway/services/public_game.py`, `gateway/tests/test_public_game.py`
- Bugs found/fixed: the GIL-bound concurrency/latency interaction (found,
  informed the pool-size choice); a nav/contextual-help gap for engine modes
  (found, documented, not fixed — P1 backlog); a test-methodology mistake in an
  early mobile-matrix run (found via manual verification, corrected before
  trusting results)
- Security result: no answer/admin-token leakage, verified live through the new
  code path
- Feature-flag defaults: Draft OFF, Championship OFF — unchanged, verified via
  `git diff` after every temporary flip during testing
- Remaining P0/P1 issues: deeper concurrency architecture (P1, was P0-A), touch
  target sizing (P1), nav/contextual-help gap (P1), clean routing (P1, carried
  from v1.5), Championship Quiz-content wiring (P1, carried from v1.5)
- Recommended v1.7 scope: deeper public-generation concurrency architecture, not
  another UI phase

Nothing has been committed.
