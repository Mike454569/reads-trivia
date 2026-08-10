# Game Director -> Game Factory -> QA -> Reads -- Architecture Assessment

**Analysis only. Nothing implemented, nothing deployed, no Engine code changed, no Reads code
changed.** Every claim below is backed by either (a) direct code reading of the actual files
listed, or (b) empirical, non-destructive test calls made during this assessment (disclosed
below) -- not by trusting file/function/table names or the version-numbered doc files' own
claims. Where I could not verify something without writing to core content tables
(`puzzle_catalog` etc.), I say so explicitly rather than assuming.

## Empirical testing disclosure

I ran `game_director.interpret()` and `game_director.preview()` twice each against the live
database, using requests prefixed `[ARCH_ASSESSMENT_TEST]` for easy identification. These
functions are *designed* to log every call into `game_director_requests` /
`game_director_previews` (that is their entire purpose), so this is expected, minor, easily
identifiable side effect, not a meaningful mutation -- 2 rows and 1 row respectively now exist in
those two logging tables. I also attempted `game_director.publish()` once, which raised an
exception before writing anything (see below) -- confirmed via `PRAGMA` state, no row was written
to `game_director_publications`. **I did not call `game_factory.publish()`** (the function that
*would* write to `puzzle_catalog`), since that writes to core content tables and this is
explicitly an assessment-only turn.

## The headline finding

**There is no LLM, no AI model, and no general natural-language understanding anywhere in this
pipeline.** "AI Game Director" (v3.0) and "Autonomous Expansion" (v3.1) are branding on top of
hand-written regex/keyword pattern matching (`game_factory.compile_description()`) against a
fixed, small vocabulary of ~10 relationship predicates. A request either happens to contain
phrasing the regexes recognize ("drafted by the same team", "transferred exactly once", "same
school", etc.) or it returns `NEEDS_RULE` and produces nothing. This is confirmed, not inferred --
see the exact request trace below.

## What happens today for the user's exact example request

> "Make me a game where you get clues about an NFL player and have to identify him."

I ran this exact sentence through `game_director.interpret()`. Result:

```
status: BLOCKED
spec.intent_status: NEEDS_RULE
feasibility: {"status": "NEEDS_RULE", "estimated_candidates": 0,
              "reason": "The description does not map to a supported relationship yet."}
```

**Nothing is generated. No candidates, no preview, no error message useful to an end user beyond
"not supported yet."** This is a real, representative example of the gap between what a Reads
owner would naturally type and what the parser recognizes -- "guess the player from clues" is a
completely reasonable trivia concept (it's structurally close to the existing Silhouette mode),
but no predicate in `compile_description()`'s hardcoded table matches it. For contrast, I also ran
a request using phrasing the parser *does* recognize ("Make a game about NFL players drafted by
the same team at the same position") and it worked correctly through `interpret()` and
`preview()`, producing 5 real, QA-passing "connections" candidates from verified `draft_facts`
data. The difference between these two outcomes is entirely about whether the input string
happens to contain one of a small number of recognized phrases -- not about whether the
underlying football concept is knowable from the data.

## Component-by-component reality check

### `game_factory.py` (and `game_factory_legacy.py`) -- mostly WORKING, narrow scope

- `compile_description()`: **WORKING**, but as a fixed regex/keyword classifier, not NLU. Only
  recognizes phrasing matching ~10-15 hardcoded predicates across legacy + v1.4 additions
  (`DRAFTED_BY`, `PLAYED_FOR`, `TEAMMATE_OF`, `CFB_ROSTER_SCHOOL`, `DRAFT_PICK_ORDER`,
  `AWARD_DRAFT_SEQUENCE`, `CFB_TRANSFER_COUNT`, `CFB_SAME_SCHOOL_POSITION`,
  `NFL_SAME_DRAFT_TEAM_POSITION`, `NFL_TEAMMATE_TIME`, a handful more). Anything else ->
  `NEEDS_RULE`.
- `feasibility()`: **WORKING**. Correctly checks capability tables and row counts for recognized
  predicates; correctly reports `NEEDS_RULE`/`NEEDS_DATA`/`NEEDS_DENSITY`/`SUPPORTED`. This is the
  same function I relied on for all three of my own approved pilots.
- `generate_candidates()`: **WORKING**. Confirmed by direct use in three shipped pilots and by a
  fresh test call in this assessment (produced a real `connections` payload from `draft_facts`).
- `qa_candidate()`: **WORKING** but narrow -- checks for a missing answer, duplicate visible
  labels, and (for `elimination`) that the answer appears among the displayed items. It does not
  check historical-team-naming correctness, cross-source answer agreement, or anything close to
  the rigor I built into my own three pilot adapters (season-aware team resolution, identity
  consistency, difficulty cross-referencing). Real, but thinner than what shipped to Reads so far.
- `create_spec()` / `preview()` (Factory's own, not Director's): **WORKING** -- writes to
  `game_factory_specs`/`game_factory_candidates`/`game_factory_qa`. 7 real spec rows and 34 real
  candidate rows already exist in the database from some prior exercise of this path (test
  suites, most likely -- `game_factory_tests.py`/`game_factory_v14_tests.py` exist as files).
- `publish(spec_id, mode_id, ...)` (Factory's own): code-reads as **correct and coherent** --
  re-runs feasibility, re-generates, re-QAs, inserts into `puzzle_catalog` with
  `source_id='GAME_FACTORY'`, `verification_status='FACTORY_QA_PASSED'`. **Not executed during
  this assessment** (would write to `puzzle_catalog`), so this specific claim is "reads correct,
  unverified by me" rather than "confirmed working" -- flagged deliberately, per the "be
  skeptical" instruction. What I *can* confirm empirically: **zero rows in the entire 414,165+
  row `puzzle_catalog` have `source_id='GAME_FACTORY'`** (checked directly). Every single existing
  puzzle came from bulk import pipelines (`SPORTSDATAVERSE_CFB`, `NFLVERSE_DATA`,
  `READS_IDENTITY_BRIDGE`, `READS_CFB_MASTER`), not from this publish path. **This exact
  live-database-writing code path has, as best I can tell, never actually run to completion
  against this database.**

### `game_director.py` -- PARTIAL, with one confirmed-broken function

- `interpret()`: **WORKING**. Calls `compile_description()` + a small hardcoded `graph_plan()`
  lookup (8 predicates) + `feasibility()`, logs to `game_director_requests`. Confirmed by direct
  test call.
- `preview()`: **WORKING**, but uses its *own* separate, weaker QA function (`_candidate_qa()` --
  checks payload shape, duplicate labels, `answer_id` membership) instead of
  `game_factory.qa_candidate()`. The module imports `quality_intelligence as Q` but **never calls
  anything from it** -- confirmed by grepping the file for `Q.` (zero matches). The "QA" in
  "Director -> Factory -> QA" is, today, this one small local function, not the substantial
  `quality_intelligence.py` module its own docstring implies.
- `publish()`: **CONFIRMED BROKEN.** Line 80 calls `F.build_mode(text, mode_id=mode_id, ...)`.
  `game_factory` has no `build_mode` function or attribute -- confirmed both by grepping the
  source and by directly calling `game_director.publish()` in this assessment, which raised
  `AttributeError: module 'game_factory' has no attribute 'build_mode'`. **There is currently no
  working code path from a natural-language request to a published game mode.**
  `game_director_publications` has 0 rows in the database, consistent with this having never
  worked.

### `autonomous_expansion.py` -- mostly UNEXERCISED, one dead dependency

- `parse_advanced()`: reads the `director_capabilities` table for extra regex patterns to layer
  onto Director's interpretation. **That table has 0 rows.** This function currently always
  returns an empty `advanced_operators` list, regardless of input -- a fully vestigial feature.
- `remember_template()` / `recall_templates()`: a simple word-overlap-scored template memory (not
  embeddings, not semantic search -- literally counting shared words between the query and stored
  descriptions). Code looks correct, but `director_mode_templates` has 0 rows -- `seed_memory()`
  exists as a function but has apparently never been run against this database.
- `discover()` / `propose_new_games()`: **not** a natural-language generator -- it's a fixed
  5-pattern report that counts existing `puzzle_catalog` rows per hardcoded pattern and assigns a
  volume tier. `autonomous_mode_discoveries` and `director_mode_recommendations` both have 0 rows
  -- never run.

### `quality_intelligence.py` -- real, substantial, almost entirely UNEXERCISED

This is genuinely the most sophisticated file in the set -- a real knowledge-graph builder, truth-
contradiction auditor, puzzle QA auditor, difficulty calibrator, mode-quality scorer, coverage
mapper, and release-certification function (`run_all()` chains all of them). But checking every
table it writes to: `puzzle_quality_audits`, `mode_quality_metrics`, `coverage_dimensions`,
`factory_opportunities`, `reads_health_snapshots`, `release_certifications`, `qa_truth_claims`,
`qa_contradictions` -- **every one of them is empty.** Only `knowledge_nodes` (208,754 rows) and
`knowledge_edges` (496,276 rows) have data, meaning `build_knowledge_graph()` specifically was run
at some point, but none of the other seven functions in this module -- including the actual QA
audit (`audit_puzzles`) and the release gate (`release_certify`) -- have ever been executed
against this database. **The certifications referenced in this Engine's own `V4_0_FINAL_
CERTIFICATION.json` did not come from running this module's release-certification function; that
function's own output table is empty.**

### Existing prototype API servers

`api_server.py` (port 8787) exposes Factory's own working `/factory/analyze|preview|publish|
unpublish` (calling `game_factory.*` directly, spec_id-based -- this is the *correct* pipeline,
separate from and not exposed via Director's broken one) plus read endpoints for the graph and
daily puzzles. `game_director_api.py` (8800) and `autonomous_api.py` (8801) directly expose the
partially-broken Director/Autonomous functions with **zero authentication, zero rate limiting,
zero request timeout beyond SQLite's own lock-wait timeout, loopback-only binding (`127.0.0.1`)**.
`quality_api.py` (8795) exposes the mostly-unexercised quality module the same way. All five are
`http.server.ThreadingHTTPServer` instances -- fine for local development, not close to anything
that should be reachable from the internet.

## Which Game Factory mechanics are genuinely implemented and QA-capable

All six schema-declared mechanics (`guess`, `connections`, `elimination`, `matching`, `ordering`,
`path`) have real code in `generate_candidates()`. `qa_candidate()` applies to all of them but is
thin (see above). In practice, for the predicates that are actually feasibility-`SUPPORTED` today
(the ~10-15 recognized ones), most produce `connections` or `elimination` payloads; only a few
(the plain relationship lookups) produce `guess`; `path` explicitly defers to `graph_explorer` on
demand rather than a static pool; `matching`/`ordering` exist in code but I did not find a
currently-`SUPPORTED` predicate that routes to them in this database's capability table --
present in the schema and the code, unconfirmed as reachable today.

## Which football domains are currently production-safe enough for Director-generated games

Exactly the same domains Game Factory itself gates on -- `NFL_DRAFT` (via `draft_facts`), CFB
roster/school/position data (via `cfb_roster_seasons_real`), CFB transfer counts, the 2006-2019
NFL teammate window, and the conservative CFB<->NFL identity bridge. This is the *same* verified
surface my own three pilots already used, just accessed through Director's thinner QA layer
instead of my adapters' stricter one. No domain is safe *through Director* that isn't already
safe through Factory directly.

## What Game Director currently returns

`interpret()` returns a JSON object: `{request_id, request, spec, graph_plan, feasibility,
status}` -- a parse result, not content. `preview()` returns that plus `{preview_id, candidates:
[{payload, difficulty, ambiguity, sources, qa}], qa: {pass, fail}}` -- a list of raw Game-Factory-
shaped candidate payloads (whichever of the six mechanic shapes applies) with QA pass/fail flags.
**Neither of these is a playable game package** -- they are Engine-internal data shapes
(`items`/`answer` for connections, `entity`/`answer` for guess, etc.), not the flat
`{id, category, difficulty, question, options[4], correctIndex, notes}` contract Reads' static
Quiz UI actually consumes. `publish()` is broken and returns nothing usable.

## What a standardized `GeneratedGamePackage` would need to contain

Based on what Reads' frontend actually needs (per `tools/quiz_export`'s already-proven contract)
and what Engine can actually verify:

```
GeneratedGamePackage {
  package_id: string                     // stable id for this generation run
  source_request: string                 // the original natural-language text
  mechanic: "guess" | "connections" | "elimination" | "matching" | "ordering"  // path excluded --
                                          // no static Reads UI concept fits an on-demand path query
  target_ui: string                      // which existing Reads UI contract this was adapted to,
                                          // e.g. "quiz_data_v1" (the window.QUIZ_DATA shape)
  category: string                       // MUST be an existing Reads category, or generation is rejected
  domain_id / competition_id             // which verified Engine domain this came from
  questions: [ {                         // only populated if target_ui-compatible; see below
      id, category, difficulty, question, options[4], correctIndex, notes
  } ]
  raw_candidates: [ ... ]                 // the native Factory payloads, for domains/mechanics that
                                          // don't yet have a Reads UI -- stored for future use, not rendered
  provenance: { source_tables, source_ids, verification_status, engine_version, seed }
  qa: { engine_qa: {...}, adapter_qa: {...}, contract_validation: {...} }
  status: "DRAFT" | "PENDING_REVIEW" | "APPROVED" | "REJECTED" | "PUBLISHED"
  created_at, reviewed_by, reviewed_at
}
```

The critical design point: **`questions[]` (the Reads-renderable part) can only be populated for
the `guess` mechanic today**, because that's the only mechanic with a working adapter pattern
(proven three times now) that turns an Engine payload into Reads' flat MC contract. Everything
else should be captured as `raw_candidates` and held for a future UI, not forced into a shape it
doesn't fit.

## Can existing Reads game UIs render any of these generated mechanics without visual changes?

**Only indirectly, and only for one mechanic.** Game Factory's native payload shapes do not match
any existing Reads UI directly:

- `guess` payloads (`{prompt, answer, answer_id, entity}`) have **no distractor options at all** --
  every one of my three shipped adapters had to build its own distractor-construction logic
  (`teams_active_in_season()`, the outcome-label vocabulary, etc.) that Game Factory does not
  provide. This is real, necessary adapter work, not a rendering triviality.
- `connections` payloads (`{items[], answer}`, "what connects these players") have **no matching
  Reads UI at all.** Reads' closest mode, NFL Grid, is a different mechanic entirely (a
  procedurally-generated 3x3 intersection board, not a 4-item connections list).
- `elimination` payloads ("odd one out") -- no matching existing Reads UI.
- `matching`/`ordering` payloads -- no matching existing Reads UI.

So: **zero mechanics render without an adapter; one mechanic (`guess`) renders after the same kind
of adapter work already done three times.** This is the single most important reality check for
this whole initiative -- "Director generates a game" cannot mean "Reads instantly displays it" for
five of the six mechanics without new UI being built first.

## Which existing Reads game UI should be the first target for a Director-generated game

**NFL Quiz**, unambiguously -- it's the only Reads UI whose contract a Game-Factory `guess`
payload can be adapted into today, and that adapter pattern (`tools/quiz_export`) is already
built, tested, byte-identical-verified across three domains, and has a locally-approved,
playtested 100-question batch already appended to it. The smallest possible Director milestone is
"make the *predicate selection* dynamic instead of hardcoded per-adapter" -- everything else in
the pipeline (distractor construction, contract validation, serialization) already exists and
works.

## What needs to run on an always-on server vs. what can remain static on Netlify

- **Static on Netlify, unchanged:** everything Reads currently is -- the whole static site, all
  hand-authored and Engine-*exported* JS data files (including any future Director-generated
  batch, once approved and exported the same way the three pilots were).
- **Requires an always-on server, cannot be Netlify Functions:** anything that runs
  `game_director`/`game_factory`/`quality_intelligence` against the 1.65GB SQLite file. This was
  already established in this project's very first architecture pass
  (`PROJECT_TWO_APPS...`/earlier integration-plan work): Netlify Functions are stateless,
  ephemeral, and have no persistent disk for a 1.65GB file. Nothing about Game Director changes
  that conclusion -- if anything it strengthens it, since natural-language requests are
  inherently more expensive (full `compile_description` + `feasibility` + `generate_candidates`
  passes) than serving a pre-built static file.

## What is the minimum production API required

For the smallest useful milestone (below), exactly two endpoints, admin-only, on the always-on
server:

- `POST /gateway/generate-preview` -- body: `{request_text}`. Runs interpret -> feasibility ->
  (if SUPPORTED and mechanic is `guess`) generate_candidates -> Engine QA -> adapter-level
  distractor/contract validation -> returns a `GeneratedGamePackage` in `DRAFT` status. Never
  writes to `puzzle_catalog`.
- `POST /gateway/approve` -- body: `{package_id}`. Admin-only. Triggers the export step (same
  `tools/quiz_export` serialization already proven) to write a new static JS file to disk/S3/
  wherever Reads' build pulls from -- does **not** touch the live site until a human redeploys it,
  matching this project's "append, never auto-publish" pattern so far.

Nothing else is required for the minimum milestone. `/gateway/publish-to-catalog` (writing into
Engine's own `puzzle_catalog` for Engine's *other* consumers) is a materially bigger, riskier
scope-add and should stay out of the first milestone entirely.

## How Director, Factory, and QA should be combined behind one Reads Engine Gateway

A single new process (not yet built) that:
1. Imports `game_factory` and (optionally, later) `quality_intelligence` as Python modules
   directly -- exactly the pattern `tools/quiz_export` already uses, not HTTP calls to the
   existing prototype servers.
2. Does **not** import or call `game_director.py`'s `publish()` (broken) or
   `autonomous_expansion.py` (unexercised, empty support tables) at all for the first milestone.
   `game_director.interpret()`/`preview()` are fine to reuse for the parse+feasibility+raw-
   candidate step -- they work -- but the QA step should use `game_factory.qa_candidate()`
   directly (proven, already relied on) rather than Director's thinner `_candidate_qa()`.
3. Applies a **mechanic gate immediately after feasibility**: if `mechanic != "guess"`, return
   `NOT_YET_RENDERABLE` rather than attempting a preview, since there is nowhere for that content
   to go. This single gate is what keeps the first milestone honest and small.
4. Runs the exact adapter-style verification already proven three times (team/entity identity
   resolution, distractor construction from real Engine data, contract validation) generalized
   just enough to accept a Director-supplied predicate instead of a hardcoded one per domain.
5. Exposes only the two endpoints above, never the raw existing prototype servers (`api_server.py`
   etc. stay as local dev tools, not part of the Gateway's surface).

This retires the "many small stdlib HTTP servers on different ports" pattern for anything
production-facing, consistent with the very first architecture assessment's recommendation, now
made concrete for this specific feature.

## What security controls are required before an admin natural-language generation endpoint can exist

- **Authentication**: the Gateway must sit behind real auth (the existing Firebase Auth the Reads
  app already uses is the natural fit) -- none of the existing prototype servers have any auth at
  all today; that's acceptable for `127.0.0.1`-only local tools, not for anything reachable
  beyond that.
- **Authorization**: admin-role check, not just "logged in" -- this is explicitly an owner/admin
  tool per the request.
- **Input bounds**: request text length cap, `limit`/`seed` parameter validation (the existing
  Director code trusts these values from the caller with no bounds checking).
- **No arbitrary SQL or dynamic query construction reachable from user text** -- confirmed by
  reading `compile_description()`/`generate_candidates()`: the NL text only ever selects among a
  fixed set of hardcoded predicate branches; it never gets interpolated into SQL. This is a real
  and important existing safety property, worth preserving explicitly as a design constraint if
  the parser is ever extended.
- **Output sanitization**: nothing in the existing code HTML-escapes generated question text
  before it would reach a browser -- Reads' own `app.js` handles escaping (`esc()`) at render
  time for hand-authored and Engine-pilot content already; the Gateway's export step must
  preserve that, not assume the Engine payload is pre-sanitized.

## What timeout/resource limits are needed to prevent arbitrary Director requests from hammering the 1.65GB database

- **Per-request wall-clock timeout** (e.g. 10-15s) around the interpret->feasibility->generate
  chain -- none of the existing code has this; a pathological `limit` value or an expensive
  `graph_explorer` path query could otherwise run unbounded.
- **`limit`/`candidate_limit` hard cap** enforced server-side, not just trusted from the request
  body (today `game_factory.publish()`'s `candidate_limit` defaults to 5000 and is fully
  caller-controlled).
- **Concurrency cap** -- `ThreadingHTTPServer` spawns a thread per connection with no pool limit;
  a production Gateway needs a bounded worker pool (or a real WSGI/ASGI server) instead.
- **Rate limiting** per admin session, since even a single admin fat-fingering repeated large
  requests against a 1.65GB SQLite file with `PRAGMA foreign_keys=ON` could cause real lock
  contention.
- **Read-only DB connection mode** for the preview step specifically (SQLite supports opening a
  connection read-only) so a preview request is structurally incapable of writing, independent of
  application-level care.

## What should happen when the requested game cannot be supported by verified Engine data

Exactly what already happens, and it's the one part of this pipeline that's already correct:
`feasibility()` returns `NEEDS_RULE`/`NEEDS_DATA`/`NEEDS_DENSITY`/`NEEDS_IDENTITY` with a specific
`reason` string, and nothing downstream runs. The Gateway's job is to surface that reason clearly
to the admin ("this needs the CFB-to-NFL identity bridge, which isn't dense enough yet" is a real,
already-produced message) rather than a generic failure -- the raw material for a good error
message already exists in Engine's output, it just needs to reach the UI unmodified.

## How generated games should be stored, versioned, reviewed, approved, and eventually published

Mirroring exactly the pattern already used and approved for the three existing pilots:

1. **Generate** -> a `GeneratedGamePackage` in `DRAFT`, stored as a row in a new (not yet built)
   admin-only tracking table or simply a JSON file on disk, same spirit as `tools/backups/*.json`.
2. **Review** -> the same human-review markdown pattern already built three times
   (`QUIZ_ENGINE_*_HUMAN_REVIEW.md`, generated from and verified against the actual package, never
   a separate approximation).
3. **Approve** -> a human (the Reads owner) explicitly marks it `APPROVED` -- no auto-publish path,
   matching this whole project's demonstrated risk posture turn over turn.
4. **Export** -> only on approval, run the same `tools/quiz_export` serializer to produce a new,
   namespaced static JS file (next Engine ID block reserved, e.g. `600000+`).
5. **Integrate** -> append (never replace) into the runtime pool the same way the Draft rollout
   already works -- a kill switch, a runtime merge, zero UI changes.
6. **Publish (deploy)** -> a separate, explicit, human-triggered step, same as every other turn in
   this project.

## Can the first implementation remain admin-only and require manual approval before generated content becomes visible to users?

Yes, and it should -- this requires no new infrastructure beyond what's already proposed above.
"Admin-only" is an authorization check on the Gateway; "manual approval before visible" is just
never wiring the export step to auto-run, and never auto-deploying, exactly like the Draft
rollout's kill switch pattern already does.

## What hosting architecture best fits the current static Netlify + Firebase Reads app while adding the Engine backend with minimal disruption

- Reads stays exactly as-is: static on Netlify, Firebase for user/social state -- zero change.
- The Gateway is a **new, separate, small always-on service** (a single low-cost VM or a
  container platform like Fly.io/Render, as already concluded in this project's original
  integration-architecture assessment), holding the 1.65GB SQLite file locally, reachable **only**
  by the admin (not by the public Reads frontend directly, and not by end users at all).
- The *output* of the Gateway (approved, exported static JS files) is what reaches Netlify -- via
  the same manual "generate file locally, commit, deploy" flow already used for all three
  existing pilots, or later a proper CI step, but not a live runtime dependency from Reads on the
  Gateway.
- This means Reads' uptime/performance is **never** coupled to the Gateway's availability -- if
  the Gateway is down, existing Reads content is completely unaffected, since it only ever
  produces files that get committed, never a live API Reads calls at request time.

## Hypothetical request trace: natural language -> Director parse -> feasibility -> Factory -> QA -> package

Using a request that Director's parser *does* recognize, to trace the best case honestly (the
user's own example, traced separately above, fails at step 2):

| Step | What happens | Status |
|---|---|---|
| 1. Natural language input | Raw text string, e.g. "Make a game about NFL players drafted by the same team at the same position." | n/a (input) |
| 2. Director parse (`compile_description`) | Regex/keyword match against ~10-15 hardcoded predicates. Works *only* if the phrasing happens to match one. | **PARTIAL** -- works for recognized phrasing, silently fails (`NEEDS_RULE`) for anything else, including the user's own example request |
| 3. Feasibility (`feasibility()`) | Checks capability tables + row counts for the matched predicate. Confirmed correct via direct test (574 estimated candidates for the working example). | **WORKING** |
| 4. Factory candidate generation (`generate_candidates()`) | Confirmed working via direct test -- produced a real `connections` payload from `draft_facts`. | **WORKING** |
| 5. QA | Director's `preview()` uses its own thin `_candidate_qa()` (shape/duplicate/answer-membership checks only), *not* `game_factory.qa_candidate()` and *not* `quality_intelligence.py` despite the latter being imported. | **PARTIAL** -- real, but materially thinner than what shipped to Reads in the three approved pilots |
| 6. Package assembly | No `GeneratedGamePackage`-shaped output exists anywhere in the codebase today. `preview()` returns raw Factory payloads (`items`/`answer` for connections), not a Reads-renderable contract. | **MISSING** |
| 7. Publish/persist | `game_director.publish()` calls a nonexistent `game_factory.build_mode()` and crashes -- confirmed by direct execution. `game_factory.publish()` itself (spec_id-based) is separate, code-correct-on-read, but has zero confirmed executions against this database (0 rows with `source_id='GAME_FACTORY'` in 414k+ puzzles) and was not executed during this assessment. | **MISSING** (Director path) / **UNVERIFIED-BUT-PLAUSIBLE** (Factory's own path) |
| 8. Reads-renderable output | No adapter exists today that turns a `connections`-mechanic payload into anything any Reads UI can display. Only `guess`-mechanic content has a proven adapter path (built three times already for Draft/QB/Championship, but as hand-written domain-specific adapters, not yet generalized to accept a Director-supplied predicate). | **MISSING** for 5 of 6 mechanics; **PARTIAL** for `guess` (adapter pattern proven, not yet generalized/automated) |

## Smallest possible implementation milestone

**Goal: type one natural-language request locally, receive one verified, structured, playable
`guess`-mechanic game package -- nothing else.**

1. A single new local script (not a server yet) that: takes a text string on the command line,
   calls `game_director.interpret()` (reuse -- it works), hard-stops with a clear message unless
   `feasibility.status == 'SUPPORTED'` **and** `spec.mechanic == 'guess'` (the mechanic gate is the
   entire trick that keeps this small and honest).
2. Calls `game_factory.generate_candidates()` + `game_factory.qa_candidate()` directly (bypass
   Director's `preview()`/`_candidate_qa()` entirely -- reuse the stronger, already-proven QA).
3. Generalizes exactly one piece of the existing `tools/quiz_export` adapter pattern: distractor
   construction for a `guess`-mechanic `{entity, answer, answer_id}` payload, using the *same*
   `object_type`-driven approach already proven (`team_aliases`/`teams_active_in_season()` for
   team-shaped answers) -- explicitly scoped to object types this already handles, refusing
   (clear error, not a guess) for any object type it doesn't recognize yet.
4. Runs the existing contract validator (`tools/quiz_export/contract.py`) against the result.
5. Writes one `GeneratedGamePackage`-shaped JSON file to disk, plus a human-review markdown (reuse
   `tools/quiz_export/human_review.py`) -- and stops. No server, no auth, no deploy, no
   `puzzle_catalog` write, no auto-export into a live Reads data file.

Everything past step 5 (a real Gateway, auth, storage/versioning workflow, static-file export into
Reads) is the *next* milestone, not this one -- and every piece of infrastructure it would need
(the export serializer, the contract validator, the human-review generator, the byte-identical-
verification discipline) already exists and is already proven, because it's the same
`tools/quiz_export` framework built for the three approved pilots.

