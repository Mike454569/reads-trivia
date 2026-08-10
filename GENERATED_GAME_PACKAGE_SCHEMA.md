# GeneratedGamePackage -- Schema (v0.1)

Documentation only -- this describes the JSON shape produced by `tools/game_director_v01.py`.
Deliberately scoped to what Director v0.1 can actually produce today: a single, `guess`-mechanic,
four-option Quiz-style game from one supported natural-language request. Fields for mechanics
Reads cannot yet render (`connections`, `elimination`, `matching`, `ordering`, `path`) are **not**
included here -- adding them before there's a UI to render them would be exactly the kind of
overengineering this milestone is explicitly avoiding. See
`GAME_DIRECTOR_PRODUCTION_INTEGRATION_PLAN.md` for why those mechanics have no Reads adapter yet.

## Top-level package

| Field | Type | Notes |
|---|---|---|
| `package_id` | string | Deterministic -- `sha256(request_text + seed + predicate)[:24]`, prefixed `GGP:`. **Not** timestamp-based, so it matches across two runs of the same request+seed (see determinism note below). |
| `package_version` | string | Schema version, `"0.1"` for this milestone. |
| `requested_description` | string | The raw natural-language request text, verbatim. |
| `director_request_id` | string | The id `game_director.interpret()` assigned when logging this request to `game_director_requests` -- traceable back to the (unmodified, reused) existing Director prototype. |
| `parsed_spec` | object | The **actual** Game Factory spec `game_director.interpret()` produced from the request text (not a hand-written stand-in) -- `competition_id`, `mechanic`, `entity_type`, `relationship_predicate`, `object_type`, `answer_type`, `group_size`, `filters`, etc. |
| `mechanic` | string | Copied from `parsed_spec.mechanic` for convenience. Director v0.1 only ever produces a package when this is `"guess"` -- anything else is rejected before generation starts (see Gating below). |
| `game_title` | string | Short, templated (not football-fact-bearing) display title, e.g. `"NFL Draft History: Guess the Team"`. |
| `game_instructions` | string | Short, templated player-facing instructions, e.g. `"You'll see an NFL player. Pick which team drafted them."` |
| `generated_at` | string (ISO 8601, UTC) | Real wall-clock generation time. **Excluded** from the byte-identical determinism comparison (see Step 9 in the report) -- everything else in the package must match across two runs of the same request+seed; this field will legitimately differ by design. |
| `engine_version` | object | `{db_path, database_version, draft_facts_row_count, team_aliases_row_count}` -- identifies which Engine data this package was generated against. **Not** a raw file hash: an earlier version hashed the whole `.sqlite` file and that was empirically non-deterministic across two identical runs, because `game_director.interpret()` itself writes a logging row to `game_director_requests` as a normal side effect, which shifts the file's on-disk bytes without changing any football data. Fingerprinting the specific stable facts that actually describe the data (Engine's own semantic version + row counts of the tables this request's adapter reads) fixed the nondeterminism -- see Step 9 in `GAME_DIRECTOR_V01_REPORT.md`. |
| `source_domains` | array of string | e.g. `["NFL_DRAFT"]` -- the Engine `data_coverage`/table domain(s) the questions came from. |
| `production_safety` | object | The adapter's own `safety_check()` result -- e.g. `{domain_id, production_safe, source_id, approved_for_import, ...}`. Package generation aborts before any candidate is produced if this fails. |
| `qa_status` | string | `"PASSED"` or `"FAILED"` -- whether every exported question cleared every check listed in `qa_checks_performed`. |
| `qa_checks_performed` | array of string | Explicit, human-readable list of exactly which checks ran (see the report for the full list this milestone actually runs) -- so nobody has to guess what "QA'd" means for this package. |
| `difficulty_distribution` | object | Counts by `Easy`/`Medium`/`Hard`, mapped from Engine's own difficulty score the same way as every prior pilot (`EASY/MEDIUM/HARD` -> `Easy/Medium/Hard`, `EXPERT` -> `Hard`). |
| `question_count` | integer | `len(questions)`. |
| `questions` | array of `Question` (below) | |
| `funnel` | object | `{considered, rejected_counts, accepted_total, exported_count, target_count, shortfall_reason}` -- full accounting of what was generated vs. what was rejected and why. |
| `review_status` | string | `"UNREVIEWED"` for every package this milestone produces -- there is no auto-approval path. A human must change this manually; nothing in this pipeline sets it to `"APPROVED"`. |

## `Question` (per-item)

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Stable, namespaced -- Director v0.1 uses the `600000-600099` block (a new, previously-unused range; see the ID-namespace policy already established across the three approved pilots: 100000s/200000s/300000s/400000s/500000s are taken). |
| `question` | string | The actual question text shown to a player. |
| `options` | array of exactly 4 strings | Real, context-valid alternatives (season-matched franchise names for this milestone's domain) -- never arbitrary/invented names. |
| `correctIndex` | integer 0-3 | Index into `options` of the correct answer. |
| `answer` | string | `options[correctIndex]`, duplicated as a plain field for convenience/readability outside the array-index indirection. |
| `category` | string | Must be one of Reads' **existing** Quiz categories -- generation is rejected if it isn't (see `contract.py`'s check, reused unchanged from `tools/quiz_export`). |
| `difficulty` | string | `Easy`/`Medium`/`Hard` -- Engine-sourced, never invented (see `qa_checks_performed`). |
| `notes` | string | Empty string unless a concise, source-backed factual restatement is constructible entirely from structured Engine fields -- never invented flavor text (same rule as every prior pilot). |
| `source_ids` | object | The raw Engine identifiers this question was built from (e.g. `player_key`, `draft_team_code`, `draft_season`, `franchise_id`) -- enough to trace the question back to its exact source rows. |
| `provenance` | object | `{verification_status, source_id, difficulty_score, difficulty_band, engine_qa_issues}` -- what Engine itself says about this specific fact's verification state. |

## Gating (what has to be true before any package is generated)

In order, all enforced by `tools/game_director_v01.py`, using the **existing, unmodified**
`game_director.interpret()` for the parse step:

1. `game_director.interpret(request_text)` must return `feasibility.status == "SUPPORTED"`. Anything
   else (`NEEDS_RULE`, `NEEDS_DATA`, `NEEDS_DENSITY`, `NEEDS_IDENTITY`) aborts with that exact
   reason surfaced, not a generic failure.
2. `parsed_spec.mechanic` must be `"guess"`. Any other mechanic aborts with
   `BLOCKED_MECHANIC_NOT_SUPPORTED` -- Reads has no UI to render the other five mechanics yet (see
   the integration plan), so producing a package for them would just be an unplayable artifact.
3. `parsed_spec.relationship_predicate` must be registered in `ADAPTER_REGISTRY` (today: just
   `DRAFTED_BY`, reusing the exact adapter already proven in `tools/quiz_export/adapters/draft.py`
   across three approved pilots). Anything else aborts with `BLOCKED_NO_ADAPTER` -- a real,
   Engine-supported relationship that simply doesn't have Reads-facing option/distractor-
   construction logic written for it yet. Extending this registry (not rewriting a generic query
   engine) is exactly how a second, third, etc. domain should be added later.

## Explicitly out of scope for v0.1 (not modeled in this schema)

- Any mechanic other than `guess`.
- Multi-round/composite games.
- Anything involving CFB<->NFL identity-bridge cross-domain content (a materially higher-risk
  domain, out of scope for a "smallest possible milestone").
- Auto-publication or auto-approval fields -- `review_status` only ever starts at `"UNREVIEWED"`.

