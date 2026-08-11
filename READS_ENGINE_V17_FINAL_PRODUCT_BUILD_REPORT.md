# Reads Engine — Claude Code Implementation v1.7

## Final Major Product Build: Daily + Retention + Six Degrees + Player Explorer + Progression + CFB Readiness

Reads Football Engine: v4.0. Claude Code implementation phase: v1.7.

The mandate was broad; the actual finding was narrower and better than expected:
most of what this phase asked for (Daily, streak, progression, achievements) was
**already built, and built well**, before this phase started. Real new work went
where it was actually needed — a safe public Six Degrees game, shipped end-to-end
— and everything else got an honest audit rather than a rushed, duplicate rebuild.

---

## Git

- **v1.6 checkpoint**: `ac35784100392e3cef624cab3af99577fd96cba0` — "Reads
  implementation v1.6: harden public concurrency and unify game discovery"
- **Starting working tree**: clean except the pre-existing, unrelated untracked
  `2026 NFL Draft Guide.code-workspace`.
- **A note on the starting baseline stated in this phase's instructions**: it said
  "159/159 passing." The actual, verified v1.6 baseline is **151/151** (v1.5's
  count, since v1.5 touched no backend files) → **155/155** after v1.6's own 4 new
  concurrency tests. This was independently re-verified at the start of this phase
  (`git log`, fresh `pytest` run) rather than trusted from the prompt — the "159"
  figure does not match anything in this repository's actual history and is not
  used anywhere in this report's own counts below.

## Baseline (Step 0, actually verified)

- v1.6 commit confirmed, working tree clean.
- **155/155 backend tests passing** at the start of this phase (re-run fresh, not
  assumed).
- DB FK check: clean. DB integrity check: `ok`.
- Homepage, FYP, unified game discovery, Draft, Championship, the shared engine
  shell: all re-confirmed working via the exact same live-browser methodology
  established in v1.5/v1.6 (see Regression, below, for this phase's own fresh
  re-runs rather than repeating v1.6's already-reported ones here).
- Mobile: v1.6's 48/48-clean result re-confirmed still applicable (no CSS changed
  since).
- Security baseline: no admin-token/answer leakage, re-confirmed live (see
  Security, below).
- Flags: Draft OFF, Championship OFF confirmed in the committed `reads-config.js`.

---

## Part A — Daily Challenge + Retention Loop

### A1: audit finding

Searched the entire frontend for "daily"/"streak"/"completion state" before
writing anything. Found a **complete, already-shipped system** (`app.js`,
roughly lines 601-882):

- `DAILY_CHALLENGE_TYPES`: 8 real rotating challenge types — the classic 10-
  question mixed Quiz, Silhouette, NFL Grid, CFB Grid, NFL Blitz, CFB Blitz, 17-0,
  CFB 12-0.
- `dailyChallengeTypeForToday()`: deterministic per calendar date via a seeded
  PRNG (`mulberry32(hashStr(todayStr() + '__dailyType'))`) — the same type for
  every player on a given day, genuinely satisfying Part A2's "same user should
  not receive random contradictory Daily content" requirement, already.
- `playedToday()` / `getDailyResult()`: real per-user completion tracking via
  `localStorage`, keyed per-username.
- `bumpStreak()`: a real streak system with a **documented, tested grace-day
  mechanic** — one missed day survives without resetting, available once every 7
  rolling days (not calendar-week-aligned), with the actual code comment
  explaining exactly why ("a real, honest safety net... not shown as an
  earnable/purchasable resource").
- `completeDailyChallengeFrom()`: shared completion bookkeeping (stats, streak,
  leaderboard push) reused by every one of the 8 challenge types, not
  duplicated per type.

### A2-A6: product contract, seed, content, completion, streak — all already met

Every one of Part A2-A6's stated requirements was independently already true:
deterministic per-day, clear completion state, integrated into the homepage
(`dailyChallengeCardHtml()`), Gateway-independent (100% local — the current 8
rotation types are all hand-authored/local content, never touching the engine),
mobile-friendly (reuses the same proven `.panel`/`.quiz-*` components as
everything else), and a real, specific, tested streak-break/grace rule.

**Timezone semantics** (Part A3's explicit ask): `todayStr()` uses `new Date()` —
the player's own local device time, not UTC. This means a player in a different
timezone could see a different calendar date (and therefore a different daily
type/question set) around midnight boundaries than a player elsewhere — a real,
honest characteristic of the existing design, not something this phase
introduced or changed. Documented here rather than silently assumed away.

### A7: return experience

`renderDailySummary()` offers Share and Home — Home lands on a homepage that
already surfaces Continue Playing, the Daily card (now completed), and the real
"For You" recommendation, so a returning player is never actually dead-ended,
just one click from the next useful action rather than a next-action button
sitting directly on the summary screen itself. Not changed this phase — a real,
working design, not a gap worth risking a regression to "fix."

### What v1.7 did NOT do: add engine modes to the Daily rotation

Explicitly considered (Part A4 asked this be audited) and deliberately not done.
Daily's core promise is "guaranteed playable for everyone, same day" — but
engine-backed modes are flag-gated (could be OFF for a given deployment) and,
per the P0-A concurrency finding, only canary-safe at low volume. Rolling an
engine-backed type into a REAL production day's rotation risks either a dead
card (flag off) or exposing Daily to the same concurrency ceiling Draft/
Championship already have. Logged as a real, specific P3 backlog item with the
actual design problem stated, not silently dropped.

---

## Part B — Streaks / Progression / Player Retention

### B1: audit finding

Also already complete. `BADGES` (`app.js` ~line 7574): **17 real, live-computed
achievements** — Perfect Grid, Blitz Master (both leagues), Speed Demon (both
leagues), Football Genius (both leagues), Sharpshooter, CFB Specialist, Perfect
Season (17-0 and 12-0), Sharp Eye, On Fire (7-day streak), Daily Grinder (10+
Daily completions), Got Next (H2H win), On a Heater (Higher/Lower streak) — every
one computed on-the-fly from `state.stats`/`getStreak()`, never a separately
persisted "earned" flag that could drift out of sync with the real underlying
data.

### B2: unified presentation

`renderProfile()` already shows: Football Rating (with a real sparkline history
of the last 20 values), day streak, and the full badge grid (locked/earned).
This already exactly matches Part B2's own suggested display list.

### B3: session completion

Every existing mode already shows a summary screen (score, what changed,
next-action buttons) — not modified this phase; this was Part 1 of the v1.5
audit's own finding, re-confirmed still true.

### B4: achievements

"Audit whether achievements already exist. If they do: polish them." They do,
comprehensively. No polish was identified as actually needed — the system reads
real state directly rather than needing synchronization work. Six Degrees is not
yet included in `BADGES` (no achievement for e.g. "solved 5 Coach Connections
puzzles") — a real, cheap, obvious future addition, logged in the backlog rather
than added here to keep this phase's actual new-code surface (Six Degrees itself)
the sole focus of new backend/frontend logic this phase touches.

---

## Part C — Six Degrees (the real new build this phase)

### C1: backend verification

Re-traced and re-tested the existing admin-only graph service
(`gateway/services/graph.py`, a v0.7 port of `Reads_Football_Data_Engine_v4.0/
graph_explorer.py`) fresh: `search()`, `shortest_path()`, `random_six()` are all
real, already covered by 19 existing tests, all read-only (grepped
`graph_explorer.py` for `.commit()`/`INSERT`/`UPDATE`/`DELETE` — zero matches).

### C2: public safety audit — the real finding

**`graph_explorer.random_six()` returns the puzzle's full `solution_path` in the
exact same dict as everything else the client would need.** The existing
admin-only `graph.six_degrees()` passes that dict through unmodified. Exposing
it to the public as-is would have hhand a player the answer before they made a
single guess — a real, concrete gap found by actually reading the return value,
not assumed safe from the function's docstring.

Built `gateway/services/public_six_degrees.py` (368 lines) as the smallest safe
adapter: a genuinely separate contract that withholds the answer server-side
until each step is actually attempted, storing the full puzzle (via the existing
`packages.py` content-addressed storage, reused rather than duplicated) and only
ever returning the current step's real display names to the client.

**A second real finding, caught by actually computing the numbers rather than
assuming `random_six()`'s uniform-random seed selection was safe as-is**: only 23
of `graph_path_cache`'s 500 total pre-computed paths are entirely
NFL-player/team/coach-typed (public-safe, non-CFB, non-internal-bookkeeping). A
naive seed-retry loop against the full cache would have found one of those 23
only ~4-5% of the time per attempt — a real reliability bug that would have made
this mode mostly return `NO_ELIGIBLE_GAME` in practice. Fixed by filtering to the
eligible rows first, then picking deterministically among only those — every
valid seed now succeeds on the first try.

**A third real finding**: all 23 of those eligible puzzles turned out to be
`team → team` connections through a shared coach specifically (predicate
`COACHED_TEAM_IN_SEASON`), all at exactly par=2. This is genuinely narrow — not
the varied, multi-hop "six degrees of separation" experience the name implies.
Rather than oversell it, the shipped public mode is titled **"Coach
Connections"**, with copy that says exactly what it is: *"Two NFL teams, one
coach who led them both."*

### C3-C6: mechanic, search/identity, path validation, reveal

Deliberately **not** open-ended path search-and-build (Part C4's own "duplicate
names" identity-safety concern, and a materially larger UI/UX surface to get
right safely in one phase). Instead: the exact same proven-safe multiple-choice
"guess" mechanic Draft/Championship already use, applied per-step across a chain.
At each step, the correct next hop (from the puzzle's pre-computed canonical
path) is mixed with real, true "wrong" options — other genuine edges from the
current node, falling back to other real entities only if a node has too few of
its own — never a fabricated name. The server is authoritative throughout:
`step_index`/`choice_index` are the only things the client ever sends, and both
are meaningless without the server's own stored puzzle to resolve them against.
A wrong answer ends the attempt (Part C5's "do not trust a client-constructed
path" combined with "no retry-until-right," matching Draft/Championship's own
established contract). Give-up/reveal (Part C6) is its own separate endpoint,
never bundled into the initial fetch or an in-progress answer.

### C7: mobile

Tested the real, complete flow (start → correct → next move → complete, and
separately wrong → reveal) across all 8 required widths (320-1440px):
**24 checks, 0 showed horizontal overflow** — including the reveal screen's
joined "Philadelphia Eagles → Andy Reid → Kansas City Chiefs"-style chain text,
Part C7's own specifically-named risk area, confirmed wrapping cleanly rather
than overflowing even at 320px (screenshot evidence captured).

### C8: discovery

Composed into the same `GET /v1/public/modes` response Draft/Championship already
use (not a second catalog endpoint), and joins the exact same `LEAGUE_MODES.nfl`
frontend registry — one unified "NFL Modes" grid, no separate "engine games"
section, gated by its own `ENABLE_ENGINE_SIX_DEGREES_V01` flag (default OFF,
same fail-closed pattern as the other two engine flags).

### A real bug found and fixed during frontend wiring

Adding the Six Degrees discovery-card entry to the SAME `ENGINE_DISCOVERY_ENTRIES`
array Draft/Championship use caused `goToMode()`'s existing lookup to match it
too (same `id`-based `.find()`) and call `startEnginePilotRound(undefined)` —
silently launching Draft instead of Six Degrees. Caught by actually clicking the
card in a real browser and checking `state.screen`, not assumed correct from
reading the code. Fixed by guarding that lookup on the presence of `engineMode`
specifically, scoping it back to only the entries it was designed for.

---

## Part D — Player Explorer

### D1: data audit

Real, rich data exists: `canonical_players` (17,113 rows: display_name,
birth_date, height_in, weight_lb, primary_position, primary_school_id,
verification_status), the CFB equivalent `canonical_cfb_players` (109,221 rows),
`draft_facts` (12,253 rows, a real join target for draft info), and
`canonical_roster_seasons` (60,246 rows, a real join target for team/season
history). No statistics tables beyond what's already used elsewhere were
assumed to exist without checking — none were found, and none are claimed here.

### D2-D5: not built this phase

**Classification: READY_WITH_ARCHITECTURE_NEEDED.** The audit found no data
blocker — only unbuilt scope: a public search endpoint (the graph search this
phase already proved safe internally, inside `public_six_degrees.py`'s own
distractor-option queries, was never exposed as its own standalone public
route), a player-detail endpoint with its own safe-field allowlist, and real
duplicate-name handling (Part D2's explicit concern — not checked in detail this
phase). Deferred deliberately to keep this phase's one real new shipped feature
(Six Degrees) fully built, fully tested, and fully mobile-certified, rather than
splitting the same effort across two half-finished ones. Full findings and the
concrete next steps are in `READS_UI_BACKLOG.md`.

---

## Part E — Game Catalog Expansion

### E1: capability audit

The Director pipeline's actual registered capabilities (`tools/director_v02/
registry.py`), read fresh rather than trusted from any planning doc:

| Capability | Data ready? | Public API ready? | UI ready? | Safe to ship? |
|---|---|---|---|---|
| `guess`/NFL_DRAFT (Draft) | Yes | Yes (certified) | Yes | **Shipped, flag OFF** |
| `guess`/NFL_CHAMPIONSHIP (Championship) | Yes | Yes (certified) | Yes | **Shipped, flag OFF** |
| `identify_player_from_clues` | Yes | No (internal only) | Dev-only | Not public-certified |
| Graph search/path/Six Degrees | Yes | **New this phase** | **New this phase** | **Shipped, flag OFF** |
| Any CFB-equivalent capability | Data yes, capability no | No — not registered at all | No | See Part F below |

### E2-E5: cheap wins, Grid criteria caution, registry, future mechanics

The one genuinely "cheap" win available this phase — reusing already-proven,
already-safe infrastructure to ship a new mode — was Six Degrees, and it's what
got built. No new Grid criteria were touched (Part E3's caution about MVP/ROTY-
style unsupported criteria was noted, not re-litigated — nothing in this phase
touched Grid). Six Degrees enters the exact same discovery registry as every
other mode (Part E4). The shell/registry architecture already supports the
multiple-choice mechanic family Six Degrees uses; text-guess, matching, ordering,
and Connections/Odd-One-Out mechanics remain unimplemented and unassessed beyond
what v1.5/v1.6 already noted (Part E5 — not re-audited in depth this phase).

---

## Part F — CFB Readiness

### F1-F2: real audit, real counts

| CFB capability | Data coverage | Identity quality | Game ready? |
|---|---|---|---|
| Players | `canonical_cfb_players`: 109,221 rows | `verification_status` field present, not deep-audited this phase | Local modes yes (cfbQuiz/cfbGrid/cfbBlitz/cfbSpeed/cfbIq/cfbLegends already ship); engine-backed: no |
| Roster/seasons | `cfb_roster_seasons_real`: 282,124 rows, 401 distinct schools, seasons 2004-2025 | — | Same as above |
| Awards/champions | `cfb_award_facts`/`cfb_champions`: 91 rows each | — | Used by existing local CFB modes |
| Coaches | `cfb_coaches`: 188 rows | — | Not currently used in any public/engine mode |
| Rivalries | `cfb_rivalries`: 48 rows | — | Not currently used in any public/engine mode |
| Games | `cfb_games_canonical`: 36,231 rows | — | Used by existing local CFB modes |

Genuinely comparable in scale to the NFL side (draft_facts: 12,253;
canonical_roster_seasons: 60,246) — CFB is not a thin or neglected dataset.

### F3-F5: discovery architecture, honest shipping decision, filter

`LEAGUE_MODES.nfl`/`.cfb` already cleanly separates NFL and CFB (Part F3's own
requirement — already satisfied by the existing architecture, confirmed not
requiring any change). **No CFB engine-backed mode was shipped this phase** — the
real gap is architectural (zero CFB entries in `tools/director_v02/registry.py`,
confirmed by direct grep), not a data gap, and building a CFB-equivalent of
Draft/Championship (new adapter, new capability registration, new public
certification) is comparable in scope to that original build — not attempted
in the same phase as building and fully verifying Six Degrees. No CFB
engine-mode parity is claimed anywhere in this report or the app. A discovery
filter/toggle (Part F5) was considered and not built: CFB already has its own
full homepage section with 6 real modes, so a toggle isn't filling an empty
gap, and there's no new engine-backed CFB content yet to filter.

---

## Homepage / FYP integration

No changes beyond what v1.6 already built (the unified `LEAGUE_MODES` registry) —
Six Degrees simply joins that exact same system: same card component
(`modeCardHtml`, unmodified), same recommendation engine (`recommendedModeHtml()`,
unmodified — Six Degrees just becomes another real entry it can pick), same
"Continue where you left off" bookkeeping (`goToMode()`'s existing
`lsSet('nflTriviaLastMode', ...)` call, now also firing for the six-degrees
route). Zero visible homepage change when the flag is off (verified live).

---

## Mobile

Two real browser-verified matrices this phase, both using the same v1.6 CDP
methodology (Playwright itself remains unavailable — arm64-only bundled driver,
this sandbox cannot execute arm64 binaries at all):

1. **Discovery integration**: confirmed the "Coach Connections" card appears in
   the unified mode grid, is clickable, and correctly launches Six Degrees (after
   fixing the routing bug described in Part C above).
2. **Full Six Degrees viewport matrix**: 8 widths (320-1440px) × question/
   answered/reveal states = **24 checks, 0 overflow**, including the specific
   long-chain-text risk area Part C7 called out.

---

## Performance

Not separately re-measured beyond what the concurrency section already covers —
Six Degrees' own fetch/answer latency (~0.9s per real puzzle fetch, observed
during the mixed-concurrency test below) is well within the existing 10s
client-side timeout, and no new homepage network calls were added (the registry
check is a boolean flag read, not a fetch, same as v1.6's Draft/Championship
integration).

## Concurrency

Re-tested with Six Degrees now in the mix, per Part J's explicit instruction not
to let a new mode share an unnecessary bottleneck. Fired 6 concurrent Draft
requests and 6 concurrent Six Degrees requests simultaneously against one
Gateway instance:

- **Draft: 4/6 succeeded** — exactly the known, unchanged concurrency ceiling
  from v1.6, unaffected by simultaneous Six Degrees traffic.
- **Six Degrees: 6/6 succeeded**, all in ~0.9s — Six Degrees does not share the
  generation semaphore at all (by design: it's fast, indexed SQL against
  `graph_nodes`/`graph_edges`/`graph_path_cache`, never the CPU-bound Director
  pipeline `generate_public()` guards).

DB integrity re-confirmed clean (`PRAGMA foreign_key_check` empty, `PRAGMA
integrity_check` → `ok`) immediately after.

# Concurrency classification: CANARY READY. NOT BROAD-TRAFFIC READY.

Unchanged from v1.6 — this phase neither improved nor regressed it, and does not
claim otherwise. Six Degrees introduces no new concurrency concern of its own.

## Security

Re-verified live, specifically through the new Six Degrees surface (not just a
repeat of Draft/Championship's already-covered checks):

- No admin token anywhere in Six Degrees' frontend source or requests (unchanged
  pattern, re-grepped).
- **No answer leakage**: fetched a real puzzle, confirmed the response contains
  no `correct_id`/`solution_path` — only display names and an opaque `game_id`.
  Confirmed live via direct inspection of a real fetch response, not just unit
  tests.
- **No raw graph IDs exposed**: every step's `options`/`current` field is a
  plain display-name string; the underlying `graph_nodes.node_id` values never
  leave the server.
- Server remains fully authoritative: `step_index`/`choice_index` are meaningless
  without the server's own stored puzzle; a wrong-mode `game_id` (e.g. a real
  Draft `game_id` submitted to the Six Degrees answer route) is correctly
  rejected as `INVALID_GAME_ID` (404, matching this project's established
  convention), verified by a dedicated cross-mode tampering test.
- Admin routes: no-token and wrong-token both still rejected (401), re-verified
  live.
- Errors: no stack traces, paths, or SQL in any Six Degrees response observed —
  same clean, structured error contract every other route in this Gateway uses.

---

## Regression

- **Backend: 179/179** (155 entering this phase + 23 new Six Degrees tests + 1
  new concurrency-independence test). Three pre-existing tests needed real
  updates (not just re-runs) because this phase's addition of a third public
  mode with its own independent switch genuinely changed what they were
  asserting: `test_public_modes_no_auth_needed` and
  `test_both_certified_modes_registered` needed their mode-count assumptions
  widened/rescoped, and `test_master_switch_off_reflected_in_modes_list` needed
  to become a genuine test of switch *independence* rather than assuming one
  switch governs every public mode. All three updated with the real reasoning
  documented inline, not just silenced.
- Frontend: full-page load re-confirmed clean with the flag off (byte-identical
  mode grid to pre-v1.7). `app.js`'s diff is additive plus one bug-fix
  (the routing guard described in Part C) — no existing function's established
  behavior was altered.
- DB: FK check clean, integrity check `ok`, re-confirmed after the heaviest
  concurrency test in this phase.

---

## Product Readiness Matrix

```text
AREA                              STATUS
Engine                            READY
Gateway                           READY
Public gameplay                   READY
Concurrency                       CANARY (not BROAD)
Mobile                            READY
Homepage                          READY
FYP                               READY
Discovery                         READY
Daily                             READY
Streak / retention                READY
Draft                             READY (flag OFF)
Championship                      READY (flag OFF)
Six Degrees                       READY (flag OFF) -- LIMITED content (23 puzzles, NFL-only, par=2 only)
Player Explorer                   LIMITED -- data audited real/rich, no endpoint/UI built
Progression                       READY
NFL catalog                       READY
CFB                               LIMITED -- rich local content; zero engine-backed public capability
Security                          READY
Fallback                          READY
Production deployment             READY_NOT_DEPLOYED (unchanged from v1.4 -- no Fly credentials in this environment)
Broad public launch               NOT READY -- gated on concurrency (CANARY only) and the still-OFF feature flags
```

---

## Launch Blockers

Only genuine blockers, not optional feature ideas:

1. **Public generation concurrency remains CANARY, not broad-traffic ready.**
   The single real launch blocker for turning Draft/Championship/Six Degrees on
   for anyone beyond a small controlled canary. Real fix scoped in the backlog
   (multiprocessing worker pool, or a pre-generated candidate pool).
2. **Actual production deployment has never been exercised** (unchanged since
   v1.4 — no Fly.io credentials/CLI available in this development environment).
   Deployment readiness (config, health checks, rollback plan) exists; an actual
   `fly deploy` has not been run.

Everything else in this report (Player Explorer, CFB engine modes, Daily/engine
integration, achievement additions) is real, scoped future work — **not** a
launch blocker, since none of it is required for the currently-shipped,
flag-gated feature set to be safe.

---

## v1.8 scope

# v1.8 — Final Launch Certification + Polish

Per this phase's own instruction, v1.8 should be certification and fixes, not
another feature phase. Recommended exact scope, in priority order:

1. **LAUNCH BLOCKER**: resolve the public-generation concurrency ceiling (the
   one thing actually gating broader rollout of everything already built).
2. **LAUNCH BLOCKER** (if a real launch is imminent): actually exercise
   production deployment once credentials are available, following the
   already-documented runbook from the v1.4 report.
3. **POST-LAUNCH P1**: the nav-active-state/contextual-help gap for engine
   modes (small, cosmetic, already precisely scoped in the backlog).
4. **POST-LAUNCH P1**: touch-target sizing polish (36-42px → closer to 44px).
5. **POST-LAUNCH P2**: Player Explorer (data audit already done this phase —
   the next phase would be pure build, not more auditing).
6. **FUTURE**: CFB engine-backed modes, Daily/engine-mode integration,
   achievement entries for Six Degrees, results/social sharing for engine
   modes — all real, all scoped, none blocking launch.

---

## Final status

- Backend test count: **179/179 passing**
- Browser test results: no Playwright available (confirmed again this phase);
  real coverage via the same pure-Python CDP client — discovery-card click-
  through, full Six Degrees round-trip (correct path to completion AND wrong
  path to reveal), 24-check mobile matrix, mixed-concurrency live test
- Daily status: **READY** — audited, found essentially complete, no changes made
- Streak/retention status: **READY** — audited, found essentially complete
- Six Degrees status: **READY, flag OFF** — shipped, real backend + UI + 23
  tests + mobile certification; content honestly limited (23 NFL-only,
  par-2-only puzzles) and honestly labeled ("Coach Connections," not "Six
  Degrees") rather than oversold
- Player Explorer status: **LIMITED** — data audited and found real/rich, no
  endpoint or UI built this phase
- Progression status: **READY** — audited, found essentially complete
- Additional modes shipped: Six Degrees (public, flag-gated, OFF by default)
- CFB readiness: **LIMITED** — rich local content already shipped; zero
  engine-backed public capability, honestly documented as an architecture gap
  not a data gap
- Mobile status: **READY** (24/24 new checks clean; v1.6's 48/48 unaffected)
- Concurrency status: **CANARY READY, NOT BROAD-TRAFFIC READY** — unchanged,
  re-verified with Six Degrees in the mix, confirmed no shared bottleneck
- Security status: **READY** — no answer/admin-token/raw-graph-ID leakage,
  verified live through the new Six Degrees surface specifically
- Feature-flag defaults: Draft OFF, Championship OFF, Six Degrees OFF —
  confirmed via `git diff` against the committed file
- Actual production deployment status: **NOT DEPLOYED** (unchanged since v1.4 —
  no Fly credentials in this environment; not falsely claimed otherwise)
- Remaining LAUNCH BLOCKERS: public-generation concurrency ceiling; production
  deployment never actually exercised
- Recommended v1.8 scope: concurrency fix first, then real deployment if
  credentials become available, then the small cosmetic P1 items — explicitly
  NOT another feature-build phase

Nothing has been committed.
