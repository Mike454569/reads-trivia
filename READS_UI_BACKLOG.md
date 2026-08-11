# Reads UI Backlog

Started in v1.5 (UI/product-foundation phase), updated in v1.6 (P0 hardening +
homepage/FYP/game discovery). This is a prioritized list of known work — not a
commitment, not a schedule.

Priority is P0 (do before broader rollout / real risk) → P3 (nice-to-have, low
urgency). Effort is rough T-shirt sizing (S/M/L) for a single-developer-plus-Claude-
Code pace, not a formal estimate.

---

## P0 status as of v1.6

### Public-generation concurrency ceiling — SUBSTANTIALLY IMPROVED, kept open
**Category**: Engine/Gateway. **Effort remaining**: M (architectural, not a quick fix).
v1.6 gave public generation (`generation.generate_public()`, `gateway/services/
generation.py`) its own bounded worker pool (`PUBLIC_GENERATION_MAX_CONCURRENCY`,
default 4), completely independent of the admin path's single-slot lock — backed by
a real, verified proof that the entire public generate_fn path is read-only against
the Engine SQLite file (see the v1.6 report's Phase A section for the full trace).
Verified results: 15 concurrent requests now get 4 clean successes (up from 1
before) with the remaining 11 failing safely and immediately, not queuing or
hanging; concurrent Draft+Championship traffic shares the pool fairly; concurrent
answer validation showed zero cross-game contamination across 8 simultaneous
submissions; DB integrity stayed clean through all of it.

**What's still open**: CPython's GIL means the pool doesn't give true parallel
throughput for the CPU-bound candidate-scanning work inside `generate_package_from_spec()`
— wall-clock latency for N concurrently-served requests scales roughly linearly
with N (measured ~0.8s at N=1, ~4.0s at N=4, ~9.2s at N=8), which is *why* the
pool size was set conservative (4, not higher) rather than tuned for maximum
throughput — a higher number would only mean more requests "succeed" at a latency
closer to the frontend's 10s client-side timeout. Real future fixes: a
multiprocessing-based worker pool (escapes the GIL, meaningfully more complex:
needs its own SQLite-connection-per-process and cross-process semaphore
coordination), or a pre-generated/cached candidate pool (Part A5's own suggested
"short-lived in-memory selection" option, not attempted this phase to keep the fix
minimal and reviewable). **Status: CANARY READY. NOT BROAD-TRAFFIC READY** — safe
for a small number of simultaneous real testers, not yet safe to assume under
open/heavy traffic.

### Mobile rendering verification — CLOSED, with real evidence
**Category**: Tooling/Mobile. ~~Effort~~: done.
v1.6 got real device-metric emulation working via the Chrome DevTools Protocol
directly (Playwright itself could not run in this environment — its bundled Node
driver is arm64-only and this sandbox cannot execute arm64 binaries at all, confirmed
via `arch -arm64`/`arch -arm64e` both failing; `websocket-client`, a pure-Python
package with no native/arch dependency, made a minimal real CDP client possible
instead). Tested the REAL, unmodified `index.html`/`app.js`/`engine-game-ui.js` —
not a hand-built harness — across the full required matrix (320/360/375/390/430/
768/1024/1440px), both Draft and Championship, at start/question/answered states:
**48 checks, 0 showed horizontal overflow.** Real production question/answer text
(up to 60 characters, options up to 38 characters like "Lost in the Conference
Championship") rendered cleanly at every width down to 320px. The v1.5 "possible
cropping" concern did NOT reproduce under real device-metric emulation — confirming
it was a fidelity gap in v1.5's `--window-size`-only test harness, not a genuine CSS
bug, so per the v1.6 instructions no CSS was touched. Touch targets measured 36-42px
tall (see P2 below — below the 44px Apple HIG guideline, though above WCAG 2.1's
24px minimum, not a blocker). **Also newly resolved**: v1.5's onboarding-modal
"cropping" observation *also* did not reproduce under real device-metric emulation
(the `--window-size`-only method used then apparently didn't fully apply mobile
layout rules) — see the updated audit table below.

---

## P1 — High impact, reasonable effort

### Deeper concurrency architecture (multiprocessing or pre-generated pool)
**Category**: Engine/Gateway. **Effort**: M-L.
See the P0 writeup above — this is the actual "broad traffic ready" fix, deliberately
not attempted in v1.6 to keep that phase's change small and reviewable (a bounded
thread pool touching two files vs. a process-pool architecture touching connection
management, IPC, and semaphore coordination). Needed before removing the "canary
only" caveat.

### Touch target sizing polish
**Category**: Mobile/Accessibility. **Effort**: S.
v1.6's real device-emulation testing measured `.quiz-option`/`.btn-*` heights at
36-42px depending on breakpoint — comfortably above WCAG 2.1's 24px AA minimum but
below the 44px Apple HIG / 48px Material guideline some players may be used to.
Not reproduced as a real usability complaint, just measured as a number worth
tracking; a small `min-height` bump on mobile breakpoints would close the gap.

### Clean, non-internal routing for engine-backed modes
**Category**: Routing. **Effort**: S.
`#draftpilot` / `#championshippilot` are still the literal hash routes — still
deliberately untouched (routing overhaul remains out of scope per the original v1.5
instruction, and v1.6's new discovery cards route around this entirely via
`goToMode()` rather than requiring a player to ever see the hash). Once these modes
are fully promoted, they deserve real routes/URLs a player could reasonably see or
share, with the old hashes kept as redirects for anyone with a bookmark.

### Wire Championship's engine-exported Quiz content into Quiz proper
**Category**: Content reuse. **Effort**: S.
Unchanged from v1.5: Draft's fallback plays the real, merged "NFL Draft History"
Quiz category; Championship's fallback plays "Super Bowl History" instead of its own
engine-exported equivalent (`data/quiz-engine-championship-award-pilot.js`), which
exists on disk but was never merged into `QUIZ`. Small, contained, still deferred.

### Nav active-state / contextual help for engine modes
**Category**: Polish. **Effort**: S.
Discovered while wiring the discovery cards in: the top-nav's active-league
highlighting (`app.js`'s `currentLeague`, ~line 7749) and the contextual "?"
help button (~line 7900) both look up `LEAGUE_MODES...find(m => m.id === state.screen)`
— but engine modes set `state.screen = 'enginePilot'`, not their own `draft_guess`/
`championship_guess` id, so neither lookup matches while actually playing one.
Cosmetic only (nav just doesn't highlight "NFL" specially; "?" falls through to
generic behavior instead of a mode-specific tip) — not attempted in v1.6 to avoid
touching the shared nav/help code paths (Part C18: no navigation rewrite without a
demonstrated need). Small, contained fix: special-case `state.enginePilot`'s
`modeKey` in both lookups the same way `goToMode()` now special-cases
`ENGINE_DISCOVERY_ENTRIES`.

---

## P2 — Real, but lower urgency

### Full accessibility pass
**Category**: Accessibility. **Effort**: M.
Still only a basic, scoped pass exists (engine shell's aria-live regions, verified
button semantics; discovery cards inherit `.mode-card`'s existing accessibility
properties by construction since no new markup pattern was introduced). Not a full
WCAG audit of the whole product.

### Featured-game treatment / exploration categories
**Category**: Homepage. **Effort**: M.
v1.6 deliberately did the smallest correct integration (engine modes join the SAME
unified `LEAGUE_MODES`/mode-grid/recommendation system every other mode already
uses) rather than building new homepage sections — the existing homepage/FYP system
was already strong (see the updated audit table below), so a ground-up redesign
wasn't justified. A future phase could still add: a stronger "featured game"
treatment (Part C8 — not hard-coded to any one mode), explicit browse categories
("Quick Games"/"Challenge Games"/"Knowledge Games" per Part C10), and richer
availability messaging ("temporarily unavailable" vs. "coming soon" per Part C13) —
none of which existing signals currently justify building speculatively.

### Six Degrees / Player Explorer / Profiles-achievements / NFL-CFB toggle UI
**Category**: Future surfaces. **Effort**: L each.
Unchanged from v1.5 — not started.

### Results / social sharing for engine modes
**Category**: Sharing. **Effort**: S–M.
Unchanged from v1.5 — Quiz/Legends have `data-share`, Draft/Championship don't.

---

## P3 — Low urgency / speculative

### Game creation / Director-facing UI
No player-facing need currently.

### Daily mode integration with engine-backed modes
v1.4 explicitly deferred Daily migration; nothing since has blocked it, no active
design exists.

### Play-count tracking for engine modes
**Category**: FYP data quality. **Effort**: S, but touches stats/leaderboard territory.
`recommendedModeHtml()`'s real "unplayed → new, least-played → fresh" logic now
naturally includes Draft/Championship (v1.6, they're part of `LEAGUE_MODES.nfl`) —
but engine modes don't write to `state.stats`, so `modeTimesPlayed()` always returns
0 for them, meaning they'll show as "New to you" indefinitely even after a player
has played many rounds. Deliberately NOT fixed in v1.6: wiring engine-mode results
into `state.stats`/the leaderboard/Football Rating touches scoring economics and
Firestore writes, explicitly out of scope for a UI-foundation phase (Part C27/C28).
Not a fabrication — the signal genuinely doesn't exist yet, which is why the
recommendation algorithm reads it that way.

---

## Audit reference

Original Part 1 audit (v1.5) plus what v1.6 re-verified with real tooling.

| Surface | Strength | Weakness | v1.6 status |
|---|---|---|---|
| Quiz | Clean, established `.panel`/`.quiz-*` component set; already accessible | None found relevant to this phase | Re-verified working (full round-trip: start → question → answer → feedback) during v1.6 regression, unmodified |
| Engine shell (`engine-game-ui.js`) | Reusable state model, clean copy (v1.5) | Concurrency ceiling under real load (see P0 above) | Now also mobile-certified with real evidence (48/48 checks clean) and reachable from the homepage, not just a hidden hash route |
| Homepage / FYP (`renderHome`, `recommendedModeHtml`, `continuePlayingCardHtml`) | Genuinely real recommendation logic already: deterministic per-day/per-user, prioritizes unplayed modes then least-played, real "Continue where you left off" via localStorage — stronger than initially assumed in the v1.5 audit | Engine modes were invisible to this whole system (only reachable via hidden hash route) | **Fixed in v1.6** — engine modes now participate in the exact same registry, recommendation, and continue-playing logic as every hand-authored mode, gated by their existing feature flags, zero visible change when both are OFF |
| Onboarding modal | — | v1.5 flagged possible 375px text cropping (unconfirmed) | **Resolved in v1.6** — did not reproduce under real device-metric emulation across the full viewport matrix; was a v1.5 test-harness fidelity gap, not a real bug |
| Grid / Speed / Blitz / Silhouette / Legends / IQ / Study / CFB variants | Each has its own established, working render/state pattern | Not shell candidates yet | Spot-verified (Grid launch) during v1.6 regression, unmodified |
