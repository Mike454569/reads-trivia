# Game Director v0.1 -- Report

Milestone: the smallest genuinely-working pipeline from a natural-language game
request to a verified, structured, playable `GeneratedGamePackage`:

    natural language -> Director parse -> feasibility -> Game Factory -> strong QA
    -> GeneratedGamePackage -> human review

Nothing in this milestone touches the live Reads app, publishes anything, starts
a server, or calls an LLM. See "Do-not-touch-production check" at the bottom.

## 1. Natural-language request used

> "Make a guessing game where I see an NFL player and have to guess which NFL
> team drafted him."

Chosen because it was the one candidate request, of three tested, that the
existing (unmodified) `game_director.interpret()` parser maps to a `guess`-
mechanic spec backed by an already-proven, already-approved Reads adapter
(`tools/quiz_export/adapters/draft.py`, used in three prior approved pilots).
See section 6 for the other two requests and why they were rejected instead.

## 2. Did Director parse it?

Yes. `game_director.interpret()` (unmodified, reused as-is) returned:

```json
{
  "competition_id": "NFL",
  "mechanic": "guess",
  "entity_type": "nfl_player",
  "relationship_predicate": "DRAFTED_BY",
  "object_type": "team",
  "answer_type": "team",
  "group_size": 4,
  "filters": {},
  "intent_status": "PARSED",
  "rule_version": "1.4"
}
```

`director_request_id: GDR:e04e88d72ce68f327b76de93` (Director's own request log,
written to `game_director_requests` as its normal, unmodified behavior).

## 3. Did feasibility pass?

Yes.

```json
{
  "status": "SUPPORTED",
  "estimated_candidates": 12253,
  "reason": "Backed by NFL draft data.",
  "missing": [],
  "source_table": "relationships"
}
```

This is `game_factory`'s own feasibility check, called via
`game_director.interpret()` -- not re-implemented.

## 4. Which Game Factory mechanic/domain ran

- **Mechanic:** `guess` -- the only mechanic with a Reads-renderable UI adapter
  today (see `GAME_DIRECTOR_PRODUCTION_INTEGRATION_PLAN.md`).
- **Domain/adapter:** `NFL_DRAFT` via `tools/quiz_export/adapters/draft.py`,
  the exact adapter already proven across the Draft pilot (v1), Draft pilot v2
  (production), and the 300-question mixed pack. Not a new adapter.
- **Candidate sourcing:** `game_factory.generate_candidates(spec, ...)`, called
  directly with the **actual Director-parsed spec** (not the adapter's own
  hardcoded stand-in spec). Confirmed the two specs are field-for-field
  identical for this request, so using the real parsed spec doesn't change
  the result -- but it does mean request-specific filters would be genuinely
  honored for a future request that included any, rather than silently
  dropped.
- **Per-candidate evaluation:** `adapter.evaluate()` and `adapter.safety_check()`
  reused verbatim -- the exact functions already proven in three approved
  pilots, not copies.
- **`game_director.publish()` was never called** (confirmed broken --
  calls a nonexistent `game_factory.build_mode()`). This pipeline only ever
  calls `interpret()` for the parse/feasibility step.

## 5. Candidate funnel and QA results

| Stage | Count |
|---|---|
| Candidates considered | 500 (deterministic sample, seeded) |
| Rejected -- TEAM_UNRESOLVED | 66 |
| Rejected -- DUPLICATE_PLAYER | 15 |
| Rejected -- DUPLICATE_QUESTION | 1 |
| **Accepted (passed every check)** | **418** |
| Exported into the package | 25 (target met, no shortfall) |

**QA status: PASSED.** 16 checks ran (full list embedded in the package's
`qa_checks_performed` field and in `DIRECTOR_V01_FIRST_GAME_HUMAN_REVIEW.md`),
spanning: Director/feasibility gating, mechanic/adapter registry gating,
production-safety check, Engine's own `qa_candidate` logic, row-level identity
and provenance checks, season-aware team/franchise resolution (including the
Pilot #1 safe-fix corrections), distractor-construction restricted to real
season-matched data, duplicate-entity/question/ID guards, and full contract
validation (4 unique options, correctIndex validity, category match,
difficulty enum, notes-is-string).

`quality_intelligence.py` was **not** used and is **not** claimed as having
certified this package -- its output tables are empty in this database (see
the prior architecture-assessment turn), so claiming its certification would
be false. This is stated explicitly inside the package's own
`qa_checks_performed` comment in `tools/game_director_v01.py`.

Zero `contract_failures`, zero `dup_questions`, zero `dup_ids` in the final
export (see the package's `_diagnostics` field).

## 6. Questions in the final package

**25 of 25 requested.** IDs `600000`-`600024` (a new, previously-unused ID
block -- 100000s/200000s/300000s/400000s/500000s are already taken by prior
pilots). Full per-question detail, including all 4 options, the marked
correct answer, difficulty, category, source IDs, and provenance, is in
`DIRECTOR_V01_FIRST_GAME_HUMAN_REVIEW.md`.

Difficulty distribution: `{"Medium": 7, "Hard": 18}` (no Easy questions
happened to survive the top-500 deterministic sample for this seed --
disclosed, not smoothed over).

## 7. Determinism test

Ran the identical request with the identical seed
(`director-v01-drafted-by-guess`) twice.

- **Run 1 whole-file SHA-256:** `678dae918925634780cc789ede868f7ffbad5fa8555a8de57ab4957fc6c75c13`
- **Run 2 whole-file SHA-256:** `d94765a211b8e7c383858af80b260fb7527d63938c1980109660f28888c85b22`
- These differ **only** because of `generated_at` (a real wall-clock
  timestamp, explicitly excluded from the determinism claim by design -- see
  the schema doc).
- **Content-normalized (generated_at excluded) SHA-256, both runs:**
  `f376adbc0d92404b20eae7197388f9da70f6e5aea8cc9d573ba699022c02d653` -- **identical.**
- `package_id` matched exactly across both runs: `GGP:7eac206fa520f0996d7e0cda`.

### Bug found and fixed during this test

The first implementation computed `engine_version.db_sha256` by hashing the
raw 1.65GB `.sqlite` file. That field differed between the two runs even
though every other field (including the full `questions` array) matched.
Root cause: `game_director.interpret()` writes a logging row to
`game_director_requests` as part of its own normal, unmodified behavior --
this is a real write to the database file, which shifts its on-disk bytes
between runs even though no football data changed. A whole-file hash can't
tell "the draft data changed" apart from "an unrelated table got a new log
row," so it was the wrong tool for this field.

**Fix:** replaced the raw file hash with `_engine_version_fingerprint()`,
which reads only the specific, stable facts that actually describe the data
a request's adapter reads: Engine's own `meta.database_version` (`"4.0.0"`)
plus row counts for `draft_facts` (12,253) and `team_aliases` (37). These
don't change from a read-only `interpret()` call, so the fingerprint is now
identical across runs (verified above) -- and it's arguably more meaningful
than a file hash, since it says exactly which data mattered rather than
"the whole file, including unrelated tables."

## 8. Did unsupported requests fail safely?

Yes, on both tested cases, run through the real `generate_package()` function
(not just raw `interpret()`):

**Request B** -- "Make a game about which college an NFL player attended."
Parsed successfully (`relationship_predicate: NFL_ATTENDED_SCHOOL`,
`entity_type: nfl_player`, `object_type: school`) but feasibility returned
`NEEDS_DATA` ("NFL player→college edges are not populated in the current
production-safe database.", `estimated_candidates: 0`). `generate_package()`
returned a structured `BLOCKED_INFEASIBLE` result with `package_id: null` --
no candidates were generated, no partial package was produced.

**Request C** -- "Make me a game where you get clues about an NFL player and
have to identify him." (the user's own example of a "completely novel"
request). Parser returned `intent_status: NEEDS_RULE`,
`relationship_predicate: null`; feasibility returned `NEEDS_RULE` ("The
description does not map to a supported relationship yet.").
`generate_package()` returned the same structured `BLOCKED_INFEASIBLE` shape,
`package_id: null`.

**No hard-coded support was added for Request C merely to make it pass.**
It fails exactly as predicted in the architecture-assessment turn, and that
failure is graceful and structured, not a crash or a silently-wrong package --
which was the actual point of testing it.

## 9. Can we now honestly say: "Reads can take a supported natural-language
   game request and produce a verified structured playable game package"?

**Yes, for the narrow case this milestone targeted:** a `guess`-mechanic
request whose predicate is already registered in `ADAPTER_REGISTRY` (today:
just `DRAFTED_BY`). For that case, the full path -- NL text in,
Director-parsed spec, Game Factory feasibility and candidate generation,
16-check QA, a schema-documented `GeneratedGamePackage` out -- is real,
runs end-to-end, is deterministic, and was verified against the live 1.65GB
Engine database, not mocked data.

**What remains missing / still prototype-only**, so this claim isn't
overstated:

- `ADAPTER_REGISTRY` has exactly one entry. Any request whose predicate isn't
  `DRAFTED_BY` is correctly and safely rejected, but that's a narrow slice of
  what the Engine's `relationships` table could in principle support --
  extending coverage means adding proven adapters one at a time (as sections
  6-8 of this project already did for QB/Championship), not a claim that
  "any football question" works now.
- Only the `guess` mechanic is covered. The other five Game Factory mechanics
  (`connections`, `elimination`, `matching`, `ordering`, `path`) have no
  Reads-renderable UI adapter at all -- a request that parses to one of those
  correctly gets `BLOCKED_MECHANIC_NOT_SUPPORTED`, not a package.
  `game_director.publish()` and the underlying `game_factory.build_mode()`
  remain broken/nonexistent, unmodified and untouched by this milestone, per
  the explicit instruction to leave the broken prototype alone.
  `game_director_api.py` was not touched or exercised.
- `quality_intelligence.py` remains unused -- its tables are empty in this
  database, so nothing here relies on it, and nothing claims it ran.
- This package was never rendered in the actual Reads Quiz UI. It is pure
  data, sitting in `generated_games/`, outside `data/`, never referenced by
  `index.html`, `app.js`, or the service worker. "Playable" here means
  "schema-valid and structurally ready for the same Quiz renderer the three
  approved pilots already use," not "was actually clicked through in a
  browser this session."
- No LLM is involved anywhere in this pipeline. `game_director.interpret()`'s
  parser is deterministic regex/keyword matching against ~10-15 hardcoded
  predicates, not general NLU -- confirmed again by Request C failing to
  parse. Where a future LLM belongs: translating open-ended natural language
  into a *safe, structured intent* (entity_type / relationship_predicate /
  object_type -- the same shape `interpret()` already produces) for a human
  or this same gating pipeline to then validate against real data -- not
  generating answers or owning football facts. It would sit strictly upstream
  of `interpret_and_gate()`, replacing or supplementing the regex parser only,
  with every downstream gate (feasibility, adapter registry, QA) unchanged.

## 10. Exact files created or modified

**Created:**
- `GENERATED_GAME_PACKAGE_SCHEMA.md`
- `tools/game_director_v01.py`
- `generated_games/director-v01-first-game.json`
- `DIRECTOR_V01_FIRST_GAME_HUMAN_REVIEW.md`
- `GAME_DIRECTOR_V01_REPORT.md` (this file)

**Modified:**
- `tools/quiz_export/core.py` -- added an opt-in `raw_rows_override` parameter
  to `run_export()`, default `None`, preserving byte-identical behavior for
  every existing caller (re-verified via SHA-256 against all three prior
  pilots' output after the change). Note: the final `game_director_v01.py`
  ended up **not** calling `core.run_export()` -- it needed output in
  `GeneratedGamePackage` JSON shape rather than the Reads `.js` quiz-array
  shape that `run_export()` unconditionally writes via
  `serializer.write_quiz_js()`, and didn't want that file written as a side
  effect. So `game_director_v01.py` has its own orchestration loop that
  mirrors `run_export()`'s structure (same rejected-counts/accepted/guard
  pattern) but calls `adapter.evaluate()` and `adapter.safety_check()`
  directly -- the actual domain-specific, previously-proven logic -- rather
  than copying their internals. The `raw_rows_override` change to `core.py`
  is therefore currently unused infrastructure; disclosed here rather than
  silently left in.

**Not modified (verified untouched):** `game_director.py`,
`game_director_api.py`, `game_factory.py`, and every other pre-existing
Engine `.py` file; no football facts or `team_aliases` rows were changed.

## Do-not-touch-production check

- `app.js`, `index.html`, `sw.js` -- untouched (not read or written this
  milestone).
- Firebase config/logic -- untouched.
- `data/quiz.js` and every existing `data/quiz-engine-*.js` production/pilot
  file -- untouched.
- The Engine Draft production rollout (`ENABLE_ENGINE_QUIZ_DRAFT` kill switch,
  `quiz-engine-draft-production.js`) -- untouched.
- Existing pilot outputs (v1/v2 Draft, QB, Championship, mixed pack) --
  untouched.
- UI, CSS, routes, Netlify config, hosting -- untouched.
- No server was started or exposed. No deployment occurred. No `git push`.
- No LLM/API integration was added.
- `generated_games/director-v01-first-game.json` is not referenced by any
  script tag, service-worker cache list, or runtime code -- it is inert data
  on disk.

---

**Summary answer to the milestone's core question:** yes, for the one
registered domain/mechanic combination (`DRAFTED_BY` + `guess`), Reads' Engine
backend can now take a supported natural-language request and produce a real,
QA-verified, deterministic, schema-documented playable game package -- proven
against live data, not mocked. Extending this beyond that one combination is
adapter-registry growth and mechanic-adapter work, not a re-architecture.
