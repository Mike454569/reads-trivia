# Reads UI Backlog

Captured during the v1.5 UI/product-foundation phase while auditing the existing
product and building the reusable engine-native game shell. This is a prioritized
list of what v1.5 deliberately did NOT do — not a commitment, not a schedule.

Priority is P0 (do before broader rollout / real risk) → P3 (nice-to-have, low
urgency). Effort is rough T-shirt sizing (S/M/L) for a single-developer-plus-Claude-
Code pace, not a formal estimate.

---

## P0 — Should happen before broader engine rollout

### Fix the shared public-generation concurrency ceiling
**Category**: Engine/Gateway. **Effort**: S–M.
Carried forward from the v1.4 report, still real and still unresolved: `/v1/public/game`
reuses `gateway/services/generation.py`'s single global generation lock (an
admin-tooling-era safeguard), so two players requesting a fresh Draft/Championship
question within about a second of each other will have one land on
`GENERATION_BUSY`. In a 15-concurrent-request test this session, 5 of 6 (and
previously 14 of 15) hit it. v1.5's frontend fix (see the implementation report)
makes this fail *gracefully* — polished copy, explicit retry, working fallback — but
graceful failure under real concurrent traffic is not the same as not failing. Fix:
a small request queue or short bounded wait-and-retry server-side, scoped to public
generation specifically (the admin-tooling lock's own semantics can stay as-is).

### Verify mobile rendering with real device-emulation tooling
**Category**: Tooling/Mobile. **Effort**: S (once tooling exists).
This environment has no Node/npm/Playwright/Selenium — v1.5's mobile verification
used a headless-Chrome screenshot technique with a hand-built two-file test harness,
not the real app.js flow (clicking through screens isn't possible without a real
browser-automation tool here). That harness showed apparent right-edge content
cropping for `.panel`/`.quiz-option` at a 375px viewport that a full, unmodified
real-page screenshot at the same width did *not* show for equivalent components
(buttons, cards, top bar) — most likely a harness-fidelity gap (missing page chrome
the real index.html has), not a genuine shared-CSS bug, but this session could not
fully rule that out. Get Playwright (or even just manual on-device testing) into the
toolchain and give Draft/Championship/Quiz a real mobile pass to close this out with
certainty instead of a hedge.

---

## P1 — High impact, reasonable effort

### Clean, non-internal routing for engine-backed modes
**Category**: Routing. **Effort**: S.
`#draftpilot` / `#championshippilot` are still the literal hash routes (Part 24
explicitly said not to overhaul routing this phase, so they're untouched). Once
these modes leave pilot status, they deserve real routes/URLs a player could
reasonably see or share, with the old hashes kept as redirects for anyone with a
bookmark.

### Wire Championship's engine-exported Quiz content into Quiz proper
**Category**: Content reuse. **Effort**: S.
Draft's fallback plays the real, already-merged "NFL Draft History" Quiz category
(`data/quiz-engine-draft-production.js`, merged when `ENABLE_ENGINE_QUIZ_DRAFT` is
on). Championship's fallback plays "Super Bowl History" instead of its own
engine-exported equivalent (`data/quiz-engine-championship-award-pilot.js`), which
exists on disk but was never merged into `QUIZ` — noted as out-of-scope in both the
v1.3 and this session's code comments. Small, contained, previously-deferred task.

### Homepage / FYP + game discovery
**Category**: Homepage. **Effort**: L.
The user's own likely-next-phase candidate (v1.6). Once a third engine mode or two
exists, players need a real way to discover them — right now Draft/Championship are
literally only reachable via a hidden hash route while their flags are off. This
phase intentionally left the homepage untouched (Part 34) even though `list_public_modes()`
already returns exactly the metadata shape (title, difficulties, availability) a
discovery card would need.

---

## P2 — Real, but lower urgency

### Full accessibility pass
**Category**: Accessibility. **Effort**: M.
v1.5 did a real but *basic* pass on the engine shell specifically (aria-live on
loading/error/submitting states, verified button semantics, relies on the
already-existing `prefers-reduced-motion`/`prefers-contrast` support in
styles.css) — not a full audit of the rest of the product (Quiz, Grid, Speed, Silhouette,
etc. were read for the Part 1 audit but not touched or re-audited for accessibility
specifically this phase).

### Six Degrees / Player Explorer / Profiles-achievements / NFL-CFB switching UI
**Category**: Future surfaces. **Effort**: L each.
Not started. The Gateway's `/v1/graph/*` (Six Degrees) is already ported
server-side (Director v0.7) with no frontend consumer yet. These are real future
engine-mode candidates once the shell pattern this phase built is proven further.

### Results / social sharing for engine modes
**Category**: Sharing. **Effort**: S–M.
Quiz/Legends already have a share flow (`data-share`); Draft/Championship don't.
Small, contained addition once the modes are past pilot status.

---

## P3 — Low urgency / speculative

### Game creation / Director-facing UI
**Category**: Admin tooling. **Effort**: L.
No player-facing need; would only matter for an internal content-authoring UI on
top of the Director pipeline, which doesn't currently exist as a product surface.

### Daily mode integration with engine-backed modes
**Category**: Daily. **Effort**: M.
v1.4 explicitly deferred Daily migration; nothing in v1.5 blocks it (network-first
service-worker caching, confirmed again this phase, doesn't interfere with future
deterministic daily seeds), but no active design exists yet.

---

## Audit reference (Part 1)

Quick summary of the Part 1 UI audit performed before building the shell — full
detail is in `READS_ENGINE_V15_UI_IMPLEMENTATION_REPORT.md`.

| Surface | Strength | Weakness | Reusable? | This phase's action |
|---|---|---|---|---|
| Quiz | Clean, established `.panel`/`.quiz-*` component set; already accessible (aria-live, real buttons) | None found relevant to this phase | Yes — the actual foundation the shell reuses | Read, not modified |
| Engine pilots (pre-v1.5) | Already shared one adapter for both modes (v1.3), already reused Quiz CSS | Copy leaked internal jargon (raw `GENERATION_BUSY` text, "Pilot"/"Engine" wording); no named state model; 226 lines inline in an 8,500-line app.js | Yes | Extracted to `engine-game-ui.js`, state model named, copy fixed |
| Homepage / onboarding / FYP | Strong existing identity/personalization | Onboarding modal showed possible text overflow in a 375px headless capture (pre-existing, unconfirmed, out of scope) | N/A this phase | Read for audit only, not touched (Part 34) |
| Grid / Speed / Blitz / Silhouette / Legends / IQ / Study / CFB variants | Each has its own established, working render/state pattern | Not shell candidates yet — no engine-backed data behind them | N/A this phase | Read for audit only, not touched |
