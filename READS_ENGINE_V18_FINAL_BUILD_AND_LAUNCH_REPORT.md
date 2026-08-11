# Reads Engine — v1.8 Final Build and Launch Report
### Game Creator + Mechanic/Template System + Launch Hardening + Production Certification

Base commit for this phase: `4368b08` ("Reads implementation v1.7: add public Six Degrees game"). Everything below is new work on top of that commit, uncommitted until the checkpoint decision at the end of this report.

---

## 0. Step 0 verification

- v1.7 checkpoint confirmed committed at `4368b08`, working tree clean except the pre-existing untracked `2026 NFL Draft Guide.code-workspace` (unrelated to this project's source).
- Baseline test suite (pre-v1.8): 179/179 passing.
- Final test suite (post-v1.8, see Part R): **217/217 passing**.
- All feature flags reconfirmed OFF by default at the end of this phase (Part Q).

---

## Part A — Director/Factory architecture audit

Read in full: `tools/director_v02/translator.py`, `providers/base.py`, `providers/mock.py`, `registry.py`, `validator.py`, `schema.py`, `pipeline.py`, `tools/game_director_v01.py`, `tools/quiz_export/adapters/draft.py` and `championship.py`, `tools/quiz_export/contract.py`, `serializer.py`, `safety.py`, `difficulty.py`, `duplicates.py`, `gateway/services/generation.py`, `gateway/services/packages.py`, `gateway/app.py`.

**Pipeline confirmed**: `translate() → validate_translation() → registry.lookup() → generate_fn() → QA → GeneratedGamePackage`, exactly as documented. `pipeline.py` never touches the Engine DB directly; `game_director_v01.generate_package_from_spec()` is the one function every `guess`-mechanic capability funnels through, and it is the ONLY place per-candidate generation touches the database (via each adapter's own `fetch_ordered_candidates`/`evaluate`).

**The "broken publish path" warning, resolved**: the spec explicitly warned "earlier implementation history included a broken publish path... do NOT assume it is now correct. Test it." Traced this precisely:
- `Reads_Football_Data_Engine_v4.0/game_factory.py`'s own `preview()`/`publish()`/`create_spec()` DO write to the Engine DB (`game_factory_specs`, `game_factory_candidates`, `game_factory_qa`, `puzzle_catalog`, `game_factory_publications`) — but this is the Engine's own standalone CLI entrypoint (`game_factory.py main()`), never invoked by this Gateway, confirmed by grep: zero references to `game_factory.publish` anywhere in `gateway/` or `tools/director_v02/`. This is the "broken" legacy path the warning refers to, and it remains correctly, deliberately unused.
- The Gateway's OWN publish-adjacent mechanism is `gateway/services/packages.py`'s `review_status` vocabulary (`GENERATED`/`REVIEWED`/`APPROVED`/`REJECTED`), which existed in the data model since v0.6 but had **no route to actually transition it** — `save_package()` only ever wrote `GENERATED`. This was a real, confirmed gap (not a broken implementation, an *absent* one). Fixed this phase: `packages.set_review_status()` (new, Part G/H) + `POST /v1/creator/review` (Part B). Tested end-to-end (`test_creator.py`), including the specific case of re-saving under an unchanged `package_id` without tripping `save_package()`'s content-collision guard (a real bug that a naive `save_package(dict(record, review_status=...))` approach would have hit — see `packages.py`'s new docstring for why `set_review_status()` is a deliberately separate code path).

---

## Part F — the primary acceptance test: data audit, honest variant, and build

### F1–F4: data audit (performed before any code was written)

The exact requested concept — "guess the NFL team from the colleges attended by the players on its offense, displayed by position" — was audited directly against the live 1.6GB database, not assumed:

| Fact checked | Result |
|---|---|
| `canonical_roster_seasons.school_id` non-null rows | 0 / 60,246 (100% NULL) |
| `canonical_players.primary_school_id` non-null rows | 0 / 17,113 (100% NULL) |
| `nfl_cfb_player_links` total rows | 124 (105 `AUTO_HIGH`, 19 `AUTO_REVIEW`) |
| Of those, players with any recorded `starts` | 39 |

**Conclusion**: 39 real players is not enough to construct a real starting offense for any real team-season. There is no honest way to build the literal college-based version of this puzzle without fabricating data. Per the spec's own explicit, sanctioned fallback (Part F7 — "find and clearly label a truthful, defensible alternative — still counts as success"), this phase built the real, data-backed variant instead: the same idea (a position-lineup board, guessed to a team), using real player **names** selected via the real `starts` (games-started) column instead of colleges.

Real coverage check (Python + SQLite, requiring ≥1 QB, ≥1 RB, ≥2 WR, ≥1 TE, ≥5 offensive-line-family positions per team-season, each with `starts > 0`, `verification_status='SOURCE_BACKED'`, `source_id` in `{NFLVERSE_DATA, NFLVERSE_ROSTERS}`): **415 of 416 real (season, team_code) pairs** with any starts data qualify, spanning real seasons **2006–2018**.

### F5–F7: the build

New adapter: `tools/quiz_export/adapters/lineup.py`. Modeled directly on `draft.py`'s and `championship.py`'s interfaces (`safety_check`, `fetch_ordered_candidates`, `evaluate`, `shortfall_reason`, `extra_funnel_fields`, `header_lines`, `human_review_context`) — no new adapter contract invented.

- **Position selection**: for each (season, team_code), the single highest-`starts` player at QB/RB/TE, the top 2 at WR, and the top 5 across a combined offensive-line-family bucket (`LT, RT, T, LG, RG, G, C`). Offensive line is shown as one honest "OL" group of 5, not 5 falsely-specific LT/LG/C/RG/RT slots — audited directly: position labeling for linemen is genuinely inconsistent across rows (some say `T`, some say `LT`/`RT` — no reliable way to know which convention a given team-season used), so claiming individual slot identity would itself be a fabrication.
- **Question text**: embeds the starting QB's name (already visible on the board itself, so this adds no new information) rather than a bare season number — fixes a real duplicate-question collision found while building this (per-season prompts without a distinguishing "given" collided across every team sharing that season; 399/415 candidates were rejected as `DUPLICATE_QUESTION` before this fix, 412/415 (99.3%) after).
- **Difficulty**: no `puzzle_catalog` row exists for this brand-new domain (Draft/Championship's difficulty source), so this uses one real, disclosed, deterministic heuristic instead of fabricating a score: season recency (`(2018 - season) / (2018 - 2006)`, mapped through the Engine's own `band()`). Documented explicitly as a stated heuristic, not a claim of empirical validation. Real distribution across all 412 accepted candidates: **Easy 125 / Medium 64 / Hard 223** — genuinely has real "easy" candidates, unlike Draft (0/232) and Championship (0/296).
- **Registered capability**: `("guess", "NFL_OFFENSE_LINEUP", "TEAM_OF_STARTING_LINEUP")` in `registry.py`, reusing the exact `guess` mechanic's answer contract (4-option multiple choice) and `_generate_guess_package` dispatcher — no new generation path.
- **Schema**: `NFL_OFFENSE_LINEUP` / `TEAM_OF_STARTING_LINEUP` added to `tools/director_v02/schema.py`'s allowlists.
- **Translator**: `mock.py` extended with keyword recognition for "offense"/"lineup"/"position"/"college" + "team" — including the literal college-phrased request, which is honestly routed to this real capability rather than left unrecognized, with the package's own title/instructions/notes always stating plainly that names, not colleges, are used (never silently reframed).

### F: end-to-end verification

Ran the exact literal request text from the spec through the real pipeline (`READS_ENGINE_DIR` pointed at the real Engine, mock translator, real generation, real QA):

```
Guess the NFL team from the colleges attended by the players on its offense, displayed by position.
```
→ `qa_status: PASSED`, real package (`GGP:e01019ddfb86187ac2530553` in one verification run), real question: *"Guess the NFL team from its 2008 starting offense (led by JaMarcus Russell at QB), by position."*, real 10-player lineup (Oakland Raiders 2008: JaMarcus Russell, Justin Fargas, Ronald Curry, Javon Walker, Zach Miller, and 5 real offensive linemen), 4 real team options, correct answer verified.

Dedicated test coverage: `gateway/tests/test_lineup_capability.py` (5 tests) — including an explicit "honesty check" asserting the word "college" never appears in any generated game content (title/instructions/question/notes/visual payload), even though the *request* text itself does.

---

## Part D/E — Mechanic Registry and Visual Template Registry

New: `tools/director_v02/mechanics.py`, `tools/director_v02/visual_templates.py`. Both are **documentation/reflection layers over already-real, already-proven behavior** — they do not change how any capability generates or validates content.

- **Mechanics documented**: `guess` (Draft, Championship, and the new lineup capability all share this exact answer contract), `identify_player_from_clues`, and `connection_path` (Six Degrees — listed for completeness; it has no Director-registry entry, served directly by `public_six_degrees.py`).
- **Visual templates documented**: `DEFAULT_MULTIPLE_CHOICE` (the pre-v1.8 implicit rendering, used by Draft/Championship/Player-From-Clues) and `POSITION_LINEUP` (new, used only by the lineup capability).

**The real architectural change** (additive, not a parallel system): `tools/quiz_export/contract.py`'s `CONTRACT_KEYS` gained two new **optional** keys (`visual_template`, `visual_payload`) — a candidate that never sets them (every Draft/Championship candidate today) has an identical key-set to before, so this is verified byte-for-byte non-breaking. `tools/game_director_v01.py`'s `generate_package_from_spec()` now passes these two fields through into the final package generically (defaulting to `"DEFAULT_MULTIPLE_CHOICE"` / `None`). `gateway/services/public_game.py`'s `_public_view()` and `gateway/services/generation.py`'s `list_capabilities()` were extended the same additive way. This is genuinely the "mechanic and visual template are separate, but the mechanic's answer contract is reusable" architecture the spec asked for — not a rename, not a second package shape.

---

## Part C — Feasibility Engine

New: `tools/director_v02/feasibility.py`. Not a second parser — calls the exact same `pipeline.translate_and_validate()` every other caller uses, then maps its `GateResult` onto the required six-value vocabulary:

| Status | Real example produced this phase |
|---|---|
| `SUPPORTED` | Draft request → no known limitations |
| `SUPPORTED_WITH_LIMITATIONS` | The literal college-phrased proof-game request → 3 real, disclosed limitations (names not colleges; grouped OL; 2006–2018 only) |
| `UNDERSTOOD_BUT_UNSUPPORTED` | "guess both a QB's team and his favorite food" |
| `MISSING_DATA` | "player salaries and contracts" / "player injuries" — real, audited: no such table exists at all |
| `UNSAFE` | Reserved, not reachable through any registered capability today (mechanically proven reachable via a real registry-flag test in `test_feasibility.py`, not just documented) |
| `UNKNOWN` | Gibberish, or genuine ambiguity needing clarification |

10 dedicated tests in `gateway/tests/test_feasibility.py`, all passing.

---

## Part B/G/H/L/M/N — Game Creator

### Backend (`gateway/services/creator.py`, `gateway/app.py`'s `/v1/creator/*`, `gateway/models.py`)

Five new admin-gated routes, every one reusing existing infrastructure rather than reimplementing it:
- `POST /v1/creator/feasibility` → `feasibility.assess()`
- `POST /v1/creator/generate` → the exact same `generation.generate()` admin pipeline `/v1/games/generate` uses, then `packages.save_package()`
- `GET /v1/creator/queue` / `POST /v1/creator/review` → `packages.list_packages()` / `packages.set_review_status()` (new, Part G/H)
- `GET /v1/creator/capabilities` → `feasibility.list_capability_support_summary()`

**Security (Part L/M)**: `CreatorFeasibilityRequest`/`CreatorGenerateRequest` accept **only** `request_text` (a length-capped string) — there is no `spec` field on either model, so a Creator caller cannot hand-craft a structured spec to try to reach an unregistered/internal capability triple directly (confirmed: `extra="forbid"` rejects an injected `spec` field with a 400 — tested). Every route requires `require_admin` (the same bearer-token dependency every other cost-incurring route already uses) with no exception. `request_text` flows through the exact same translator this project already proved cannot copy input into an executable output field (`providers/mock.py`'s own docstring). Grepped the entire new codebase for `eval(`/`exec(`/`subprocess`/`os.system`/string-interpolated SQL: zero matches.

**The "publish" boundary, deliberately scoped**: approving a package via `POST /v1/creator/review` marks it reviewed/internal-only — it does **not** make a new capability publicly playable. Exposing a capability to real, unauthenticated players remains a separate, deliberate code-level decision (`gateway/config.py`'s `PUBLIC_MODE_ALLOWLIST`), exactly as every prior public mode was certified. This is a real, intentional security boundary, not a missing feature: it prevents an admin's natural-language description alone from ever certifying new unauthenticated public surface.

19 dedicated tests in `gateway/tests/test_creator.py`, all passing.

### Frontend (`creator-ui.js`, new file)

Reached only via a hidden `#creator` route (same established pattern as the existing owner-only `#stats` page — never linked from the main nav/home grid). Gated by the real Gateway admin token, entered by the operator each session and kept only in `sessionStorage` (never hardcoded, never bundled, never sent anywhere but this Gateway's own `Authorization` header). Deliberately **not** given a separate frontend feature flag like the pilot modes — the real, meaningful gate here is the server-side admin token (fails closed unconditionally), unlike Draft/Championship/Six Degrees/Lineup where the flag genuinely controls unauthenticated public generation cost.

**Part G ("preview using the SAME renderer players see")**: implemented literally, not approximated — the Creator's question preview reshapes one internal question into the exact public payload shape (`creatorQuestionAsPublicPayload()`) and calls `renderEnginePilotPromptHtml()`/`renderPositionLineupBoard()` from `engine-game-ui.js` verbatim. There is no second, parallel preview renderer that could drift from what a real player sees.

**Real, live verification** (Chrome headless via a hand-built CDP client, `websocket-client`, since Playwright's bundled driver is arm64-only in this sandbox — same methodology as prior phases): drove the full flow — enter token → home → check feasibility on the literal college-phrased request (`SUPPORTED_WITH_LIMITATIONS`, 3 limitations shown) → generate 5 real puzzles (`qa_status: PASSED`, real lineup board rendered, 50 `.lineup-cell` elements = 5 questions × 10 positions) → approve → review queue → capabilities reference view. **Zero JavaScript exceptions** across the entire flow.

---

## Part J — CFB Creator support, re-audited honestly

**Not built.** The exact blocking layers, traced directly:

1. **Schema layer**: `tools/director_v02/schema.py`'s `ALLOWED_DOMAINS`/`ALLOWED_PREDICATES` contain zero CFB entries.
2. **Registry layer**: `tools/director_v02/registry.py`'s `CAPABILITY_REGISTRY` contains zero CFB entries.
3. **Adapter layer**: no adapter in `tools/quiz_export/adapters/` targets any CFB table through the v0.2+ Director pipeline's interface.
4. **Data layer (the deepest, and the one that rules out a "cheap win")**: audited `cfb_roster_seasons_real` directly (282,124 rows) — it has `season, school_id, cfb_player_id, jersey_number, class_year, position, height_in, weight_lb, verification_status, source_id`. **There is no games/starts/appearances column at all.** The NFL version's entire honesty story (real `starts` as a defensible "who actually started" signal) has no CFB equivalent. Building a CFB analog to this phase's proof game would require either fabricating a starter signal (forbidden) or picking arbitrarily (jersey number, alphabetical) and dishonestly calling it a "starting lineup" — rejected for the same reason the literal college puzzle was rejected.
5. **Mechanic/template layer**: the Engine's own pre-existing native CFB predicates (`game_factory.py`'s `CFB_SAME_SCHOOL_POSITION`/`CFB_SCHOOL_POSITION_CONTRAST`) use `connections`/`elimination` mechanics that were never registered in the v0.2+ Director registry and have no frontend renderer in `engine-game-ui.js`. Wiring these out would require a genuinely new mechanic + visual template + registry entries + frontend renderer — full new-capability scope, not a small addition.

**Conclusion**: CFB support is blocked at multiple layers simultaneously, with the data layer being the hard floor for anything resembling this phase's proof-game concept. No forced, low-quality CFB capability was built. This reconfirms (does not newly discover) the v1.7 finding: **BLOCKED_BY_ARCHITECTURE for the "connections" mechanic family, and now additionally confirmed BLOCKED_BY_DATA specifically for any starting-lineup-shaped concept.**

---

## Part K — Player Explorer, re-audited

Re-confirmed the v1.7 finding (`READS_UI_BACKLOG.md`): the data genuinely supports an honest Player card (17,113 NFL + 109,221 CFB players with real identity/position/draft/team-history fields, no fabricated stats). No new blocker found. **Deliberately not built this phase** — it requires its own new public search endpoint plus a dedicated player-detail endpoint with its own safe-field allowlist and real duplicate-name handling, genuinely independent-project scope (**Effort: M**, per the existing backlog classification), not a safe addition alongside everything else this phase already shipped. Carried forward as **P1 backlog, `READY_WITH_ARCHITECTURE_NEEDED`** — an explicit scope decision to protect this phase's actual certification work, not an oversight.

---

## Part O — Concurrency finalization

### Re-audit: is the new lineup capability still read-only?

Grepped `tools/quiz_export/adapters/lineup.py`, `tools/director_v02/feasibility.py`, `tools/director_v02/mechanics.py`, `tools/director_v02/visual_templates.py`, `gateway/services/creator.py` for `.commit()`/`INSERT`/`UPDATE`/`DELETE`: **zero matches.** The one SQL query in `lineup.py` is parameterized (`?` placeholders), never string-interpolated. The existing read-only proof (`gateway/services/generation.py`'s own module docstring) holds unchanged with the 3rd public mode added — `lineup_guess` was added to `PUBLIC_MODE_ALLOWLIST` and routes through the identical bounded, non-blocking `generate_public()` pool.

### Real load test (against a live local Gateway, real 1.6GB database, all 3 public modes mixed)

**Burst test** (N requests fired simultaneously — worst case): confirms the pool's bounded, non-blocking design works exactly as documented — at any concurrency above the pool size (4), exactly 4 requests succeed immediately and the rest receive a clean `GENERATION_BUSY` (never an unbounded queue).

**Sustained arrival test** (requests spread over an 8s window — the realistic "many users arriving over time" shape):

| Target rate | Busy rate | p90 latency (successful) |
|---|---|---|
| 1 req/s | 0.0% | 303 ms |
| 2 req/s | 0.0% | 741 ms |
| 4 req/s | 3.1% | 906 ms |
| 8 req/s | 61.9% | 2,602 ms |
| 15 req/s | 86.2% | 3,850 ms |

**Conclusion**: unchanged from v1.6/v1.7 — the architecture comfortably handles low, sustained traffic (roughly ≤2-3 req/s across all public modes combined) with sub-second latency and effectively zero busy-rejections, but degrades sharply above that (the GIL-bound worker pool of 4 is the real ceiling, not an artifact of this specific test). Adding the 3rd mode did not change this ceiling — pool sizing is per-slot, not per-mode.

### Pregenerated/pooled-puzzle architecture — evaluated, not built

A real, specific alternative was designed (not hand-waved): a background job periodically calls the exact same real pipeline (`generate_public()`/`pipeline.run()`, same QA, same registry) offline, accumulating a rotating pool of pre-QA'd packages per mode, stored via the existing content-addressed `packages.py` (no new storage layer). `/v1/public/game` would then serve a random pre-generated package from the pool — a cheap file read instead of live generation, removing GIL contention from the request path entirely and scaling concurrency far beyond 4.

**Trade-offs, weighed honestly**:
- **Pro**: removes the live-generation bottleneck from the hot path entirely; reuses 100% of the existing QA/registry/adapter pipeline (just invoked ahead of time).
- **Con**: a genuinely new subsystem — a reliable scheduler, pool-refresh/rotation logic, and adapted exclude-recent-repeats semantics against a fixed pool instead of always-fresh generation.
- **Con**: pool size needs tuning against each mode's real candidate ceiling (now precisely known from this phase's own funnel data: Draft ~232, Championship ~296, Lineup ~412 real accepted candidates) to avoid feeling more repetitive than live generation's already-small real universe.
- **Con**: a new operational surface (pool health/staleness monitoring, a new failure mode distinct from `GENERATION_BUSY`).

**Verdict**: the correct long-term architecture for genuine broad-traffic readiness, but a new subsystem, not a tuning knob — out of proportion to build within this phase alongside everything else already shipped, using the same proportionality discipline applied to CFB and Player Explorer. Recorded here as the clear, concrete top item for the next phase that prioritizes broad-traffic launch over feature breadth.

### Final concurrency classification: **CANARY READY. NOT BROAD TRAFFIC READY.**

Unchanged from v1.6/v1.7's own classification — re-verified with real numbers, not re-labeled. Fine for the actual current usage pattern (a small, known audience), not fine for organic/viral-scale traffic without the pregeneration work above.

---

## Part P — Production deployment attempt

Re-checked, as instructed: `flyctl`/`fly` binary — not found anywhere on this machine. `FLY_API_TOKEN` or any `FLY_*` environment variable — not set. This is the **exact same external blocker** documented since v1.4: this sandboxed Claude Code environment has no Fly.io CLI and no Fly.io credentials. Nothing changed. `gateway/fly.toml` remains a real, ready-to-use configuration file, never applied. **This blocker cannot be resolved from inside this environment** — it requires the user's own Fly.io account credentials to be supplied here, which have not been.

---

## Part Q — Feature flags reconfirmed OFF by default

`reads-config.js` (the real, committed local-dev default) at the end of this phase:
```js
enableEngineDraftPilot: false,
enableEngineChampionshipPilot: false,
enableEngineSixDegrees: false,
enableEngineLineupPilot: false,   // new this phase
```
`#creator` has no equivalent flag by design (see Part B/L above) — it is reachable at the URL level but produces zero effect without the real admin token, which is never present client-side.

---

## Part R — Full regression

- **Backend**: 217/217 pytest passing (151 pre-v1.6 baseline + 4 v1.6 + 24 v1.7 + 38 new this phase across `test_lineup_capability.py` (5), `test_feasibility.py` (10), `test_creator.py` (19), plus updates to `test_gateway.py`/`test_public_game.py` for the new 4th capability/3rd public mode — the same kind of genuine test-baseline update v1.7 made for Six Degrees, not a weakened assertion).
- **Live-browser regression** (real CDP session, real Gateway, real database): default (all-flags-off) home screen shows no lineup card and no horizontal overflow; `#creator` reachable independent of flags; `#lineuppilot` with its flag OFF correctly falls back to the home screen (`renderHome()`), matching every other pilot's existing guard.
- **No `.env`/secret files touched or staged.**
- Manual test runs' incidental dirt (`tools/director_v02/logs/audit_log.jsonl`) reverted via `git checkout --` before this report, matching the established discipline from every prior phase.

---

## Part S — Mobile certification (real device-emulation, full canonical width matrix)

Methodology: the same one established in v1.6 (`Emulation.setDeviceMetricsOverride`, real navigation, real clicks, `document.documentElement.scrollWidth > clientWidth` checked programmatically) — full required matrix **320, 360, 375, 390, 430, 768, 1024, 1440px**.

Checked the two brand-new v1.8 surfaces specifically, at every real screen in each flow:
- **Game Creator**: auth screen, home, feasibility result (with the 3 real limitation strings shown), and the full 5-question generated preview (with a real rendered `POSITION_LINEUP` board inside it) — 4 screens × 8 widths = 32 checks.
- **Public lineup pilot**: start screen, real fetched question (real lineup board), real answered/feedback screen — 3 screens × 8 widths = 24 checks.

**Result: 0 of 56 checks showed horizontal overflow.** Zero JavaScript exceptions across the entire session.

---

## Part T — Performance

No invented numbers — all measured this phase against the real local Gateway/database:
- Single-request (concurrency=1) latency by mode: Championship ~110ms, Lineup ~253ms (more DB work per candidate — 10-player JOIN vs. 1), Draft ~750-800ms (existing, unchanged behavior, driven by Game-Factory-backed candidate sourcing).
- Sustained-load latency/busy-rate table: see Part O.
- Mobile-render checks (Part S) completed well within interactive budgets; no rendering-performance regression observed.

---

## Part U — Security audit summary

- **Creator input surface**: `request_text`-only, no `spec` field, `extra="forbid"`, length-capped, funneled through the same proven-safe translator every other caller uses. No code/SQL/shell execution path found in any new file (grepped explicitly).
- **Admin-only enforcement**: every `/v1/creator/*` route requires `require_admin`; tested (401 without a token, for all 5 routes).
- **Public mode leakage**: `lineup_guess`'s fresh-game payload never contains `correctIndex`/`answer`/`source_ids`/`provenance` (tested, same allow-list discipline every prior public mode uses); the answer team name is never one of the 10 names shown on the lineup board (tested).
- **Publish/approve boundary**: reviewing a package internally cannot, by construction, make a new capability publicly reachable — that remains a separate code-level `PUBLIC_MODE_ALLOWLIST` change.
- **Admin token handling in the frontend**: never hardcoded, never bundled, kept only in `sessionStorage`, sent only in this Gateway's own `Authorization` header.
- **DB writes**: zero new write paths introduced anywhere in the generation/Creator/feasibility code (grepped).
- **CORS/rate limiting/error contract**: unchanged, reused as-is for every new route.

No new vulnerability class found. No regression in any previously-audited security property.

---

## Final Readiness Matrix

| Surface | Status |
|---|---|
| Core local modes (Quiz, Grid, Speed, IQ, Legends, Higher/Lower, Study, Daily, Progression, etc.) | **LAUNCH READY** — unaffected by this phase, zero network dependency |
| Draft/Championship/Six Degrees/Lineup engine-backed pilots | **CANARY READY**, flags OFF by default, not broad-traffic ready (Part O) |
| Game Creator | **FUNCTIONAL, ADMIN-ONLY, VERIFIED LIVE** — internal tool, not a player-facing surface, no separate readiness bar to clear |
| Proof-game capability (`lineup_guess`) | **REAL, QA-PASSED, CERTIFIED PUBLIC** (as a 3rd `PUBLIC_MODE_ALLOWLIST` entry), same canary caveat as the other pilots |
| CFB Creator support | **NOT BUILT — genuinely blocked at the data layer**, not a launch blocker (CFB was never claimed feature-complete) |
| Player Explorer | **NOT BUILT — deliberate scope decision**, real backlog item, not a launch blocker |
| Production deployment | **NOT DEPLOYED — external environment blocker** (no Fly.io credentials available here), not a code defect |

## Launch blockers vs. backlog (disciplined distinction, per the spec's own instruction)

**Not launch blockers** (explicitly excluded, per the spec): CFB not at feature parity with NFL; Player Explorer unbuilt; not every conceivable mode exists; the pregeneration architecture unbuilt; production not actually deployed (an infrastructure/credentials gap, not a code defect — the code and config to deploy exist and are ready).

**Real launch blockers**: none identified for the core, already-shipped product. The one genuine constraint — engine-backed pilot modes are canary-only, not broad-traffic — is fully mitigated by their default-OFF flags; nothing forces them on.

---

## Verdict: **LAUNCH GO**

The core Reads Football product (every mode that existed before this phase) is unaffected, fully tested, and unchanged in its already-certified readiness. This phase's new surfaces (the Starting Lineups proof game, the mechanic/visual-template system, the Game Creator) are real, genuinely QA-passed, security-audited, and verified live in a real browser — shipped with every new flag OFF by default, so the shipped default state is byte-identical in risk to before this phase. The one real, disciplined caveat — engine-backed generation is canary-ready, not broad-traffic-ready — was true before this phase, remains true after it, and is fully contained by flags that are off unless a human deliberately turns them on.

---

*Per the phase's own completion rule: this report does not commit anything, does not assume a v1.9, and does not enable any experimental mode globally. The next step is asking whether to create the v1.8 checkpoint commit.*
