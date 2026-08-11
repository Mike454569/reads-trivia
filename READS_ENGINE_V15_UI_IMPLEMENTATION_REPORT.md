# Reads Engine — Claude Code Implementation v1.5

## UI/Product Foundation + Engine-Native Game Shell

Reads Football Engine: v4.0. Claude Code implementation phase: v1.5.

v1.4 issued **UI PHASE GO**. This phase's mission was narrow and specific: give
Draft and Championship a real, reusable, polished frontend shell instead of two
copy-pasted-in-spirit render functions, without touching the engine, the API, the
homepage, or anything not already certified. It is explicitly not a product
redesign (Part 34).

---

## Git

- **v1.4 checkpoint**: `a1c70044e5fba4ae252db0ddb56407867187f264` — "Reads engine
  implementation v1.4: production hardening and rollout readiness"
- **Working tree at the start of this phase**: clean except one pre-existing,
  unrelated untracked file (`2026 NFL Draft Guide.code-workspace`, an IDE artifact,
  left untouched throughout).
- **Working tree now**: 3 modified files (`app.js`, `index.html`, `sw.js`) + 1 new
  file (`engine-game-ui.js`), all uncommitted per the completion rule, plus this
  report and `READS_UI_BACKLOG.md`.

## Baseline

- **151/151 backend tests passing**, re-confirmed both before and after this
  phase's frontend-only changes (this phase touched zero files under `gateway/` or
  `tools/`, so backend behavior is unaffected by construction, not just by
  re-running the suite).
- Feature flags: Draft OFF, Championship OFF — unchanged, `reads-config.js` was
  never modified in its committed form (it was flipped to `true`/`true` twice
  during live verification and reverted both times — confirmed via `git status`
  showing no diff against it afterward).
- Existing UI architecture at phase start: a single 8,496-line `app.js` with one
  `render*Screen` function per mode dispatched from a central `state.screen ===`
  chain, and a central delegated click handler keyed on `data-*` attributes. No
  build step, no framework, no Node toolchain in this repo at all (confirmed:
  `package.json` exists only for Netlify Functions' `npm install`, not the static
  site).

---

## Part 1 audit (existing UI)

Read, not modified, before building anything: `renderHome`, `renderQuizScreen`
family, `renderGridScreen`, `renderSpeedScreen`, `renderStudyScreen`, the
CFB-variant screens, and the full pre-v1.5 engine-pilot block (`app.js` lines
4214–4439 at the time). Full findings are in `READS_UI_BACKLOG.md`'s audit table;
the two findings that actually shaped this phase's work:

1. **The engine-pilot code already shared one adapter for both Draft and
   Championship** (v1.3's own work) and **already deliberately reused Quiz's CSS
   classes** (`.panel`, `.quiz-question`, `.quiz-options`, `.quiz-option`,
   `.quiz-feedback`, `.btn-primary`/`.btn-secondary`) rather than inventing new
   styling. This meant Part 30 ("visual consistency between traditional Quiz and
   engine modes") and a meaningful chunk of Part 4 ("one reusable shell") were
   already substantially true going into this phase — the real gap was
   organizational (226 lines of shell logic embedded inside an already-huge
   app.js) and in user-facing copy, not visual design.
2. **Real, concrete copy leaks**: the loading state read "Asking the engine for a
   question…", both mode titles read "(Live Engine Pilot)", and — the most
   significant one — a `GENERATION_BUSY` error rendered its raw server string
   directly to the player: *"Another generation job is already running. This
   Gateway allows only one generation job at a time (Director v0.6, Part H) --
   retry shortly."* A real user hitting the known concurrency ceiling from the
   v1.4 report would have seen an internal architecture citation. This is the
   single most concrete, valuable fix this phase made.

---

## Game shell architecture

### Files created
- **`engine-game-ui.js`** (new, 268 lines) — the entire reusable engine-native
  game shell: mode registry, named state model, fetch adapter with timeout, and
  every state-transition/render function. Loaded in `index.html` before `app.js`
  (same requirement `reads-config.js` already has: app.js's own hash-routing
  bootstrap reads the mode registry at its top level, not deferred in a function).

### Files modified
- **`app.js`** — the entire 226-line engine-pilot block replaced with a 7-line
  pointer comment. Every call site that references shell functions/state
  (`state.enginePilot` init, the render dispatch, the click-delegation table, the
  hash-routing bootstrap) is unchanged — same function names, same signatures, so
  no other part of app.js needed to change.
- **`index.html`** — one new `<script src="engine-game-ui.js">` tag, positioned
  between `reads-config.js` and `app.js`.
- **`sw.js`** — `engine-game-ui.js` added to `CORE_ASSETS`, `CACHE_VERSION` bumped
  `reads-v20` → `reads-v21` (Part 29) so installed PWA users actually pick up the
  new file rather than running a stale cached app.js against a missing dependency.

### State model (Part 5)
Named constants (`ENGINE_GAME_SCREEN.LOADING` / `.QUESTION_READY` / `.SUBMITTING` /
`.ANSWERED` / `.ERROR` / `.COMPLETE`) replace what were previously raw string
literals (`'loading'`, `'question'`, etc.) for `s.screen`. `IDLE` is
`state.enginePilot === null` (the pre-round Start screen) rather than a seventh
named value — there's no meaningful separate state to name. `CORRECT`/`INCORRECT`/
`REVEALED` from the spec's conceptual list collapse into one `ANSWERED` value,
matching how the render branch and the data it needs (`s.answerResult.correct`,
`s.answerResult.canonical_answer`) were already structured — three states for one
render branch would be a distinction without a difference. `FALLBACK` isn't a
screen of this shell at all; it's `cfg.fallback()` escaping entirely to a
different, already-working shell (Quiz), which is the correct semantics.

### Mode registry (Part 7)
`ENGINE_PILOT_MODES` (kept its existing name — internal, not user-facing, renaming
it would have touched two more app.js call sites for zero player-visible benefit)
is the actual `MODE_UI_REGISTRY` the spec asked for: `apiMode`, `hash`, `flagOn`,
`title`, `desc`, `fallbackLabel`, `fallback`. A third certified public mode plugs in
by adding one entry here — every function in `engine-game-ui.js` is already
mode-agnostic.

### Copy fixes (Parts 11, 25, 43, 44)
- `ENGINE_GAME_ERROR_COPY`: a fixed table from safe server error `code` → polished
  player-facing copy (`GENERATION_BUSY` → "This game is popular right now — try
  again in a moment.", `NO_ELIGIBLE_GAME` → "We couldn't find a new question right
  now.", `SERVICE_UNAVAILABLE`/`MODE_UNAVAILABLE` → "This game is temporarily
  unavailable.", `CLIENT_TIMEOUT` → "That took too long to load — check your
  connection and try again.", `INVALID_GAME_ID` → "That question expired — let's
  get you a new one.", unrecognized code → a generic default). The shell **never**
  renders `err.message` (the raw server string) again — verified live (see below).
- Both mode titles changed from "NFL Draft History (Live Engine Pilot)" / "NFL
  Playoffs (Live Engine Pilot)" to "NFL Draft History: Guess the Team" / "NFL
  Playoffs: Guess the Result" — matching the Gateway's own public-facing
  `list_public_modes()` titles exactly, so the copy is consistent whether it comes
  from this file's Start screen or the API's own metadata.
- Loading copy: "Asking the engine for a question…" → "Finding your next
  question…" — no "engine" wording (Part 44: the infrastructure should disappear
  behind the experience).

### Submitting-state feedback (Part 9)
Previously, the in-flight answer-submission state (`SUBMITTING`) disabled the
answer buttons but showed no other feedback. Added a "Checking your answer…" line
(aria-live) and a `.selected` class on the picked option while submitting, so a
slow validation call doesn't look like a dead click.

### Accessibility (Part 17)
Real, targeted additions, not a general audit: `aria-live="polite"` on the loading
and submitting states, `aria-live="assertive"` on the error state (worth
interrupting for). Verified this phase, not assumed: every interactive element was
already a real `<button>` (never a clickable `<div>`), and styles.css already has
`prefers-reduced-motion: reduce` and `prefers-contrast: more` media queries that
apply globally, including to the shell's `.quiz-option.correct`/`.wrong` pop/shake
animations — this phase didn't need to add that support because it already
existed.

---

## Draft — before/after

**Before**: title "NFL Draft History (Live Engine Pilot)", loading said "Asking the
engine for a question…", a `GENERATION_BUSY` error showed the raw internal string
above verbatim, no feedback during answer submission beyond disabled buttons, code
embedded in app.js.

**After**: title "NFL Draft History: Guess the Team", loading says "Finding your
next question…", a `GENERATION_BUSY` error shows "This game is popular right now —
try again in a moment." (verified live, see below), a "Checking your answer…" line
appears during submission, code lives in `engine-game-ui.js`. Server contract,
validation, flags, and fallback are byte-for-byte unchanged.

## Championship — before/after

Identical pattern: title "NFL Playoffs: Guess the Result" (was "(Live Engine
Pilot)"), same shared shell, same copy fixes, same unchanged backend contract.
Verified live end-to-end this phase (see below) — this is the first time this
session actually exercised Championship's fetch→answer round trip against a real
Gateway with the new shell.

## How a third mode plugs in

Add one entry to `ENGINE_PILOT_MODES` in `engine-game-ui.js` (`apiMode`, `hash`,
`flagOn`, `title`, `desc`, `fallbackLabel`, `fallback`), add its hash to
`HIDDEN_ROUTES` in app.js the same way Draft/Championship already are, add its
server-side certification to `gateway/config.py`'s `PUBLIC_MODE_ALLOWLIST` and
`gateway/services/public_game.py`'s `PUBLIC_MODES` (unchanged, out of scope this
phase, but that's the real gate). No new render function, no new state machine, no
new fetch/error-handling code.

---

## Visual design

**What changed**: mode titles, loading copy, error copy, a submitting-state
indicator. That's the entire visible diff a player would notice.

**What deliberately did NOT change**: every CSS class, every color, every
animation, every layout. No new stylesheet was written or needed — the shell
continues to render through Quiz's existing, already-tested component classes.
This was a conscious choice matching Part 2/30: the goal was removing developer-
facing rough edges from an already-good visual foundation, not redesigning it.

---

## Mobile

**Honest result, not a clean pass.** This environment has no Node/npm/Playwright/
Selenium (confirmed: `which node/npm/playwright` all report not found) and no
device-emulation tooling beyond raw headless-Chrome screenshots at a fixed window
size. Two things were actually done:

1. A full, **unmodified** `index.html` was screenshotted at 375×812 (iPhone-width)
   via headless Chrome. The top bar, auth buttons, and home content all rendered
   within bounds with no visible cropping. One pre-existing onboarding modal
   showed text running past the right edge in this capture — unrelated to this
   phase's changes (onboarding was never touched, Part 34), and not confirmed as a
   genuine bug vs. a headless-rendering artifact without real device emulation.
2. A minimal two-file test harness (loading the real, unmodified
   `engine-game-ui.js` and the real `styles.css`, with a `<main id="app">` wrapper
   matching index.html's actual structure) was used to drive a real Draft round
   against a real Gateway and screenshot the result at the same 375×812 size. That
   screenshot showed apparent right-edge cropping on `.panel`/`.quiz-option`
   content that the full real-page screenshot did *not* show for equivalently-
   styled components (buttons, cards). The most likely explanation is that the
   harness still lacks some piece of real page chrome (the top bar, or other
   structural context) rather than a genuine bug in shared CSS this phase reused
   unmodified — but this session could not fully resolve that distinction without
   Playwright-grade tooling.

This is logged as a **P0 backlog item** (`READS_UI_BACKLOG.md`) rather than either
claimed as verified or silently dropped. It should be resolved with real
device-emulation tooling before broader rollout, not guessed at further with
screenshot archaeology.

## Accessibility

Real, scoped verification: confirmed every engine-shell interactive element is a
real `<button>` (grep-verified, none are clickable `<div>`s), confirmed
`aria-live` regions are present and correctly scoped (polite for loading/
submitting/feedback, assertive for errors), confirmed the pre-existing
`prefers-reduced-motion`/`prefers-contrast` media queries in styles.css apply to
the shell's shared classes without any change needed. Not done: a full WCAG audit,
color-contrast measurement, or screen-reader session — out of scope for "basics,"
per Part 17's own instruction not to turn this into "a giant compliance project."

## Security regression

**Confirmed unchanged, by construction and by verification.** This phase touched
zero files under `gateway/` — the public API contract, server-side answer
validation, CORS, rate limits, and the master kill switch are byte-for-byte what
v1.4 committed. Verified live this session:
- No answer leakage: fetched real Draft and Championship questions from the real
  Gateway through the new shell; the rendered DOM contained only `payload.prompt`
  and `payload.options`, never `correctIndex` or `answer`.
- Server-side validation remains authoritative: `pickEnginePilotAnswer()` still
  sends the player's pick to `POST /v1/public/game/answer` and renders whatever the
  server returns — the shell never computes correctness locally, unchanged from
  before this phase.
- Feature flags: confirmed OFF in the committed `reads-config.js` (temporarily
  flipped on twice for live testing, reverted both times, confirmed via `git
  status` showing no diff).

## Browser testing — what was actually run

No Playwright (none is installed in this environment; Part 35's suite could not be
built as literally specified). What was actually done instead, using real headless
Chrome (`Google Chrome.app`'s binary, `--headless=new`) against a real running
Gateway and the real, unmodified project files:

- **Full-page load, no JS errors**: served the real `index.html` locally, loaded
  it headlessly, confirmed via DOM dump that the full home screen rendered
  correctly (title, all `data-go` nav targets present, no stray `undefined`/`NaN`/
  `[object Object]` artifacts) — this is real evidence `engine-game-ui.js` loading
  before `app.js` didn't break anything, since that rendering only happens after
  every script on the page has successfully parsed and executed.
- **Draft start screen, real flag flip**: temporarily set both `reads-config.js`
  flags to `true`, loaded `index.html#draftpilot` headlessly, confirmed the exact
  clean title/description text rendered (no "Pilot"/"Engine" wording). Reverted the
  flag flip immediately after.
- **Full state-machine round trip** (via a minimal test harness loading the real,
  unmodified `engine-game-ui.js` against a real running Gateway):
  `LOADING → QUESTION_READY` for both Draft and Championship — real questions from
  the real 1.6GB database, correct markup, no leakage.
  `QUESTION_READY → SUBMITTING → ANSWERED` — confirmed the submitting state was
  actually reached (`data-ever-saw-submitting="true"`), confirmed correct-answer
  reveal rendering with no leakage.
- **`GENERATION_BUSY` reproduced and the fix confirmed live**: fired 6 concurrent
  Draft fetches against one Gateway instance; 5 hit `GENERATION_BUSY` (consistent
  with the v1.4 report's concurrency finding) and all 5 rendered the polished "This
  game is popular right now — try again in a moment." copy — not the old raw
  server string. This is the single most concrete verification this phase
  produced: it reproduces the known bottleneck *and* confirms the UX fix for it in
  the same test.
- **CORS-blocked fetch → generic error copy**: an early harness run (before CORS
  was configured for its test origin) hit a network failure with no `code`; it
  correctly fell through to the generic default copy ("Couldn't load that — please
  try again.") rather than showing anything raw or broken.

What was **not** run: simulated keyboard-only navigation, a true mobile-device
viewport/touch emulation, or a scripted click through the real app.js UI (only
through the isolated test harness, which calls the same real functions but doesn't
go through app.js's own click-delegation code path — that path was code-reviewed,
not execution-tested, since it's a one-line dispatch to the same functions already
verified working).

## Regression

- Backend: 151/151, unchanged (this phase touched no backend files).
- Frontend: Quiz, Speed, Grid, IQ, Study, and every other existing mode's render
  functions were read for the Part 1 audit but not modified — `git diff --stat`
  confirms only `app.js`, `index.html`, `sw.js` changed, and app.js's diff is
  exactly the 226-line-removed/7-line-added engine-pilot extraction, nothing else.
  Full-page headless load (above) confirms the rest of the app still renders and
  its navigation targets are all present.

## Performance

Not separately measured this phase — the shell's actual network behavior (fetch
timeout, retry semantics, latency) is identical to what v1.4 already measured,
since this phase changed no fetch logic, only relocated it and changed what string
gets displayed on failure.

## Known technical backlog

Full detail in `READS_UI_BACKLOG.md`. The two P0 items:
1. **`GENERATION_BUSY` concurrency ceiling** — reproduced again this phase (5/6
   concurrent requests), still unresolved, still fails safely. Frontend now
   presents it well; the underlying single-generation-slot lock is unchanged.
2. **Mobile verification gap** — this environment's lack of Playwright/device
   emulation means the mobile "pass" for the engine shell specifically is a
   reasoned inference from a harness screenshot, not a confirmed clean result.
   Flagged honestly rather than asserted.

---

## UI backlog

See `READS_UI_BACKLOG.md` for the full prioritized list (P0–P3), including
homepage/discovery, routing cleanup, the Championship Quiz-content wiring gap, and
longer-term surfaces (Six Degrees, Player Explorer, Daily integration).

## Recommendation for v1.6

**v1.6 — Homepage / FYP + Game Discovery Upgrade** is the right next scope, matching
the user's own likely candidate. Rationale: the reusable shell this phase built has
no discovery surface yet — Draft and Championship are only reachable via a hidden
hash route while their flags are off, and `list_public_modes()` already returns
exactly the metadata (title, difficulties, availability) a real discovery card
would consume. Before that phase, though, resolve this phase's two P0 backlog items
(concurrency ceiling, mobile verification) — a homepage that surfaces these modes
more prominently increases the chance real users hit both.

---

## Final status

- Backend test result: **151/151 passing**, unchanged
- Browser test result: no Playwright available in this environment; real
  headless-Chrome verification performed instead (full-page load, live Draft/
  Championship round trips against a real Gateway, `GENERATION_BUSY` reproduction
  and copy-fix confirmation) — see "Browser testing" above for exact scope
- Frontend files changed: `app.js` (-228/+15 net), `index.html` (+5), `sw.js` (+2/-1
  edited lines), `engine-game-ui.js` (new, 268 lines)
- Visual improvements: mode titles, loading copy, error copy, submitting-state
  feedback — deliberately minimal, per Part 2/30's "don't discard the existing
  identity"
- Regressions found: none in existing modes (not modified, verified still
  rendering); no regression introduced in Draft/Championship (before/after behavior
  matches except the intended copy fixes)
- Mobile result: not fully confirmed — flagged as a P0 backlog item rather than
  claimed
- Accessibility result: basic pass done and verified (aria-live, button semantics,
  existing reduced-motion/contrast support confirmed applicable); full audit not
  attempted, per scope
- Security result: unchanged, verified live (no answer/token leakage, server
  validation authoritative, flags default OFF)
- Known blockers: `GENERATION_BUSY` concurrency ceiling (unresolved, documented,
  UX around it improved), mobile verification gap (needs real tooling)

This report and `READS_UI_BACKLOG.md` are the only new files this phase created
beyond `engine-game-ui.js` itself. Nothing has been committed.
