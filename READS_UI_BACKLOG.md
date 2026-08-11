# Reads UI Backlog

Started in v1.5 (UI/product-foundation phase), updated in v1.6 (P0 hardening +
homepage/FYP/game discovery) and v1.7 (Six Degrees + product audit). This is a
prioritized list of known work — not a commitment, not a schedule.

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

v1.7 re-confirmed both statuses unchanged: concurrency remains **CANARY READY,
NOT BROAD-TRAFFIC READY** (re-tested with mixed Draft+Six Degrees traffic — Six
Degrees does not share or affect the generation pool, see below); mobile stays
**CLOSED** (no CSS touched in v1.7 either).

---

## P1 — High impact, reasonable effort

### CFB has no engine-backed public mode (data is real and rich; architecture isn't built)
**Category**: Engine/CFB. **Effort**: L (comparable to the original Draft/Championship build).
v1.7 audited the real CFB tables, not planning docs: `canonical_cfb_players`
(109,221 rows), `cfb_roster_seasons_real` (282,124 rows, 401 schools, seasons
2004-2025), `cfb_award_facts`/`cfb_champions` (91 each), `cfb_coaches` (188),
`cfb_rivalries` (48) — genuinely substantial, comparable in richness to the NFL
side. The actual gap is architectural, not data: `tools/director_v02/registry.py`
has exactly 3 registered capabilities (`guess`/NFL_DRAFT, `guess`/NFL_CHAMPIONSHIP,
`identify_player_from_clues`) — zero CFB entries. A CFB-equivalent of Draft/
Championship (a `cfb_draft_guess` or similar capability, its own adapter under
`tools/quiz_export/adapters/`, registry entry, public certification in
`gateway/config.py`'s `PUBLIC_MODE_ALLOWLIST`) is real, buildable, and the data
supports it — just a full mode build, not a cheap addition. Not attempted in
v1.7 to avoid rushing a second full engine-mode integration in the same phase
Six Degrees was built and verified. **Classification: BLOCKED_BY_ARCHITECTURE,
not BLOCKED_BY_DATA** — an important distinction for scoping future work.

### Player Explorer (data audited, real and rich; no endpoint or UI built)
**Category**: New surface. **Effort**: M.
v1.7 audited `canonical_players` (17,113 rows: display_name, birth_date, height,
weight, primary_position, primary_school_id, verification_status) and CFB's
equivalent (109,221 rows) plus `draft_facts` (12,253) and `canonical_roster_seasons`
(60,246) as real join targets for a player's draft info and team/season history.
This is genuinely enough for an honest "Player" card (identity, position, draft,
teams/seasons — never fabricated stats the schema doesn't have). Not built in
v1.7: doing it safely needs its own public search endpoint (the graph search this
phase already proved safe internally, in `public_six_degrees.py`'s distractor
queries, was never exposed as its own standalone public route) plus a dedicated
player-detail endpoint with its own safe-field allowlist and duplicate-name
handling (Part D2's own explicit concern — this database has real name collisions,
not checked in detail this phase). Deferred to keep this phase's actual shipped
feature (Six Degrees) fully real and fully tested rather than splitting effort
across two half-finished ones. **Classification: READY_WITH_ARCHITECTURE_NEEDED**
— the data audit found no blocker, only unbuilt scope.

### Six Degrees: NFL-only, and a narrow 23-puzzle pool (real, honest limitation)
**Category**: Content/Engine. **Effort**: depends entirely on the Engine's own
`graph_path_cache`, not this Gateway.
Shipped in v1.7 (flag OFF by default) — see the v1.7 report for full detail. The
real, checked content today is exactly 23 distinct puzzles, every one a two-NFL-
team connection through a shared coach (`graph_path_cache` has only 500 total
pre-computed paths; only 23 are entirely NFL-player/team/coach-typed, and every
one of those 23 happens to be length-2 specifically — confirmed by direct query,
not assumed). The public mode is honestly titled "Coach Connections," not "Six
Degrees," specifically because of this. Growing the puzzle variety (more paths,
more hop-lengths, eventually CFB or cross-league content) is entirely the
Engine's `graph_path_cache` pre-computation job, outside this Gateway project's
scope — flagged here so it isn't mistaken for a Gateway-side limitation.

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
— but engine modes set `state.screen = 'enginePilot'` (and, as of v1.7, Six
Degrees sets `state.screen = 'sixDegrees'`), not their own `draft_guess`/
`championship_guess`/`six_degrees_guess` id, so neither lookup matches while
actually playing one. Cosmetic only (nav just doesn't highlight "NFL" specially;
"?" falls through to generic behavior instead of a mode-specific tip) — not
attempted in v1.6 or v1.7 to avoid touching the shared nav/help code paths (Part
C18: no navigation rewrite without a demonstrated need). Small, contained fix:
special-case `state.enginePilot`'s `modeKey` and `state.sixDegrees`'s presence in
both lookups the same way `goToMode()` special-cases `ENGINE_DISCOVERY_ENTRIES`.

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

### Profiles/achievements UI polish
**Category**: Future surfaces. **Effort**: S — this one is smaller than it
looks, since the underlying system is already real and complete.
v1.7 audited this specifically (Part B) and found `BADGES` (17 real, live-computed
achievements in `app.js`, ~line 7574), a Football Rating with a real sparkline
history, and Daily streak display already built to a high standard on the Profile
page. Nothing here needs building from scratch — only cosmetic polish, if any, is
left. Downgraded from "not started" (its v1.5/v1.6 status) now that it's been
actually read, not assumed missing.

### NFL/CFB discovery toggle
**Category**: Homepage. **Effort**: S, once CFB has an engine-backed mode to
justify it.
Not built — and per Part F5's own instruction, correctly not built: CFB already
has 6 real, working local modes with their own homepage section
(`modeSectionHtml('cfb')`), so a toggle isn't filling an empty gap, and until CFB
has at least one engine-backed public mode (see the CFB item above), a dedicated
NFL/CFB *engine content* toggle would have nothing new to filter.

### Results / social sharing for engine modes
**Category**: Sharing. **Effort**: S–M.
Unchanged from v1.5/v1.6 — Quiz/Legends have `data-share`, Draft/Championship/Six
Degrees don't.

---

## P3 — Low urgency / speculative

### Game creation / Director-facing UI
No player-facing need currently.

### Daily mode integration with engine-backed modes
**Category**: Daily. **Effort**: M, and genuinely risky if rushed.
v1.7 specifically considered adding Draft/Championship/Six Degrees to
`DAILY_CHALLENGE_TYPES`' deterministic daily rotation (Part A4 asked this be
audited) and deliberately did NOT do it this phase: the rotation must be
guaranteed playable for every visitor on a given day, but engine modes are
flag-gated and, per the P0 concurrency item above, only canary-safe at low
volume — a real production day where the deterministic hash happened to roll an
engine-backed type could either show a dead/flag-off card to everyone, or expose
Daily's guaranteed-playable promise to the same concurrency ceiling Draft/
Championship already have. Fixing this properly needs either a flag-aware
rotation (skip engine types when their flag is off, without breaking the "same
for everyone" determinism) or confidence the concurrency ceiling is resolved
first — real design work, not a one-line addition, and not worth risking Daily's
already-excellent reliability for in this phase.

### Play-count tracking for engine modes (including Six Degrees)
**Category**: FYP data quality. **Effort**: S, but touches stats/leaderboard territory.
`recommendedModeHtml()`'s real "unplayed → new, least-played → fresh" logic now
naturally includes Draft/Championship/Six Degrees (each joins `LEAGUE_MODES.nfl`
when its flag is on) — but none of them write to `state.stats`, so
`modeTimesPlayed()` always returns 0, meaning they'll show as "New to you"
indefinitely even after a player has played many rounds. Deliberately NOT fixed:
wiring engine-mode results into `state.stats`/the leaderboard/Football Rating
touches scoring economics and Firestore writes, explicitly out of scope for a
UI-foundation phase (Part C27/C28 in v1.6; same reasoning applies in v1.7). Not a
fabrication — the signal genuinely doesn't exist yet, which is why the
recommendation algorithm reads it that way.

---

## Audit reference

Original Part 1 audit (v1.5), what v1.6 re-verified, and what v1.7 newly audited
(Daily/streak/progression/achievements, Six Degrees backend, CFB data, player
data).

| Surface | Strength | Weakness | Status |
|---|---|---|---|
| Quiz | Clean, established `.panel`/`.quiz-*` component set; already accessible | None found relevant to this phase | Re-verified working during v1.6 regression, unmodified |
| Engine shell (`engine-game-ui.js`) | Reusable state model, clean copy (v1.5) | Concurrency ceiling under real load (see P0 above) | Mobile-certified (v1.6, 48/48 checks clean), reachable from the homepage |
| Homepage / FYP (`renderHome`, `recommendedModeHtml`, `continuePlayingCardHtml`) | Genuinely real recommendation logic: deterministic per-day/per-user, prioritizes unplayed then least-played, real "Continue where you left off" via localStorage | Engine modes were invisible to this system pre-v1.6 | **Fixed in v1.6**, extended in v1.7 (Six Degrees joins the same registry) |
| Daily Challenge + streak (`app.js` ~line 652-882) | v1.7 found this MUCH more complete than assumed: 8 deterministic rotating challenge types (Quiz/Silhouette/both Grids/both Blitzes/both Legends drafts), a real streak system with a documented 7-day grace-day mechanic, full completion/leaderboard tracking | Engine modes (Draft/Championship/Six Degrees) aren't in the rotation (see P3 above — deliberately not added, real risk if rushed) | **READY** — audited in v1.7, found essentially complete, no changes made |
| Progression / achievements (`BADGES`, Football Rating, rating sparkline, Profile page) | v1.7 found this also far more complete than assumed: 17 real, live-computed badges, a real rating-history sparkline, streak display | None found | **READY** — audited in v1.7, found essentially complete, no changes made |
| Six Degrees / graph backend (`gateway/services/graph.py`, `Reads_Football_Data_Engine_v4.0/graph_explorer.py`) | Real, already-tested (19 tests), read-only, deterministic | Admin-only; `random_six()` returns the solution in the same dict as everything else — unsafe to expose as-is | **Shipped in v1.7** as a new safe public adapter (`public_six_degrees.py`) — see the P1 item above for the real 23-puzzle content limitation |
| Onboarding modal | — | v1.5 flagged possible 375px text cropping (unconfirmed) | **Resolved in v1.6** — did not reproduce under real device-metric emulation |
| CFB data (canonical_cfb_players, cfb_roster_seasons_real, cfb_award_facts, etc.) | v1.7 found this genuinely rich: 109,221 players, 282,124 roster-season rows, 401 schools, 2004-2025 coverage | Zero engine-backed public capability registered for it (architecture gap, not data gap) | **LIMITED** — real local modes already work; engine-backed CFB modes are real future scope, see P1 above |
| Player data (canonical_players, draft_facts, canonical_roster_seasons) | v1.7 found 17,113 NFL + 109,221 CFB players with real identity/position/draft/team fields | No public search or player-detail endpoint built yet | **READY_WITH_ARCHITECTURE_NEEDED** — see the Player Explorer P1 item above |
| Grid / Speed / Blitz / Silhouette / Legends / IQ / Study | Each has its own established, working render/state pattern | Not shell candidates yet | Spot-verified (Grid launch) during v1.6 regression, unmodified |
