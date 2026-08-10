# Game Director v0.3 -- Real LLM Verification + Second Capability -- Report

Milestone goals: (1) verify the real Anthropic provider adapter can safely
translate NL requests into the constrained Director spec; (2) preserve the
deterministic Engine/QA boundary; (3) add exactly one additional genuinely
executable game capability; (4) produce two distinct Director-generated
playable game packages.

## Part A -- Real provider verification

### A1/A2 -- Credential check and hardening

No `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`/`ANTHROPIC_AUTH_TOKEN`) exists in
this local environment -- checked by exact variable name via
`os.environ.get()`, no value ever read, printed, or logged. Running
`tools/director_v02/run_real_provider_verification.py` (created this
milestone) confirms this cleanly:

```json
{
  "status": "REAL_PROVIDER_NOT_CONFIGURED",
  "reason": "ANTHROPIC_API_KEY is not set in this environment."
}
```

No fake result was produced. `generated_games/director-v03-real-provider-draft.json`
was **not** created (confirmed: no file with that name exists in
`generated_games/`).

Before concluding Part A, `providers/anthropic_provider.py` was hardened per
the Step A2 checklist even though it couldn't be live-tested:
- **Strict JSON extraction**: added `_extract_json_text()`, which tolerates
  exactly one common formatting artifact (a single markdown code fence
  wrapping the reply) and nothing else -- it does not scan arbitrary prose
  for an embedded JSON substring, which would risk picking up
  attacker-influenced text. Unit-tested against 4 formatting variants, all
  extracted correctly.
- **`translation_status` allowlist normalization**: the provider now checks
  the model's reported status against `TRANSLATION_STATUSES` (shared with
  the mock translator) and downgrades anything unrecognized to `NO_MATCH`,
  before the shared `validator.py` even sees it (defense-in-depth, not a
  replacement for validation).
- **Spec-type check**: if the model claims `TRANSLATED` but `spec` isn't a
  JSON object, downgraded to `NO_MATCH` rather than passed through.
- Confirmed already true, unchanged: no `tools` key in the API request body
  (no tool access), no database/filesystem/shell/web access from within the
  provider module (verified by import graph -- no `providers/*.py` imports
  `tools.quiz_export`, `game_factory`, or `game_director`), `temperature=0`,
  one call per `translate()` invocation, 15s timeout, 300-token output cap,
  500-char input truncation, no retry loop.

### A3/A4 -- Real-provider test set and Engine generation

**Not run against a live provider** -- no credential exists, per A1. The
5-request test set and the "translate a Draft request through to a real
10-question package" step are both implemented in
`run_real_provider_verification.py` and will execute automatically the
moment `ANTHROPIC_API_KEY` is set; they were not run this milestone. This is
disclosed, not glossed over -- see the "Real provider" summary section below.

## Part B -- Second capability

### B1 -- Capability selection

Compared QB/Season against Championship/Postseason using each domain's
**already-completed, already-approved pilot data** (not new estimates):

| Criterion | QB/Season | Championship/Postseason |
|---|---|---|
| Candidates considered (full table) | 1,587 | 296 |
| Accepted | 246 | **296 (100%)** |
| Rejected | 1,341 | **0** |
| Dominant rejection reason | `DUPLICATE_PLAYER` (1,003), plus 49 identity-inconsistent QB IDs excluded, 20 midseason-trade ambiguity cases | none |
| Identity/ambiguity risk found | QB name inconsistency across seasons (7 IDs excluded, including a confirmed two-different-people merge) | **none -- "domain is a primary key by construction"** (each team-season pair is already unique) |
| Distractor pool | season-dependent `teams_active_in_season()` -- theoretically thin in early seasons | **fixed 5-value outcome vocabulary** -- always exactly 4 remaining after removing the correct answer, never distractor-starved |
| Maps to `guess` mechanic, 4 valid options | yes | yes |

Championship/Postseason was selected. Its prior pilot had **zero
rejections out of 296 candidates** -- the cleanest ambiguity profile of any
domain in this project to date, confirmed again empirically through the new
v0.3 pipeline itself (see Part B4: 296 considered, 296 accepted, 0 rejected,
identical numbers). QB/Season remains unregistered -- not because it's
unsound, but because it's demonstrably higher-risk, and this milestone
explicitly asked for the *safest* second capability, not just *a* second
capability.

### B2 -- Registry entry

```python
("guess", "NFL_CHAMPIONSHIP", "TEAM_POSTSEASON_RESULT"): {
    "adapter": championship_adapter,  # tools/quiz_export/adapters/championship.py, UNMODIFIED
    "competition_id": "NFL", "entity_type": "nfl_team_season",
    "object_type": "outcome", "answer_type": "outcome", "group_size": 4,
    "min_question_count": 1, "max_question_count": 100,
    "supported_difficulties": {"any", "easy", "medium", "hard"},
    "supports_difficulty_filter": True,
    "supported_filter_keys": frozenset(), "supports_exclusions": False,
}
```

`relationship_predicate` is `TEAM_POSTSEASON_RESULT` -- precise (a team, in a
given season, has exactly one postseason outcome from a closed 5-value
vocabulary), not a broad label. Both `NFL_CHAMPIONSHIP` (domain) and
`TEAM_POSTSEASON_RESULT` (predicate) were added to `schema.py`'s allowlists
alongside the existing Draft values -- nothing free-form.

**Architectural fix required first, disclosed here:** `championship.py` (like
`qb_season.py`) has **no Game Factory predicate at all** -- it queries
`season_standings` directly via its own `fetch_ordered_candidates(c, seed)`,
exactly like `tools/quiz_export/core.py`'s `run_export()` already calls it
for every pilot. But `generate_package_from_spec()` (in `game_director_v01.py`)
was hardcoded to call `game_factory.generate_candidates(spec, ...)` --
which only works for Draft. This was fixed by changing
`generate_package_from_spec()` to call `adapter.fetch_ordered_candidates(c,
seed)` uniformly (matching `core.run_export()`'s already-proven interface),
for every adapter. **Verified before applying**: `draft_adapter
.fetch_ordered_candidates(c, seed)` and the old direct `game_factory
.generate_candidates(spec, ...)` call produce byte-identical raw candidate
rows (500/500 identical) -- so this is a correctness fix, not a behavior
change, for Draft. **Verified after applying**: regenerating both
`generated_games/director-v01-first-game.json` and the v0.2 canonical Draft
package with the same seed produced zero field differences besides
`generated_at`.

### B3 -- Translation coverage

`providers/mock.py` extended with a Championship pattern (team + playoff/
postseason/championship/Super Bowl keywords -> `TEAM_POSTSEASON_RESULT`),
alongside the existing Draft pattern -- not hard-coded sentence matches, a
keyword-presence rule like the Draft pattern already was. Three paraphrases
tested through the real `pipeline.run()`:

1. "Make a game where I guess how a team's season ended in the playoffs." -> `TEAM_POSTSEASON_RESULT`, count=25
2. "Give me postseason trivia where I pick whether a team won the Super Bowl or got knocked out earlier." -> matches via the Super Bowl phrase check
3. "Make a hard game about guessing each team's playoff result for a given season." -> `TEAM_POSTSEASON_RESULT`, difficulty=hard

`AnthropicTranslator`'s system prompt was updated to describe both
registered capabilities (see Part A) so it's ready to test the same three
paraphrases the moment a credential exists -- not run live this milestone.

### B4 -- Second package

`generated_games/director-v03-second-capability.json`: **25 questions**,
IDs `610000`-`610024` (same v0.2-reserved sub-block; Championship questions
share the ID range with any other v0.2/v0.3-pipeline-generated package since
they're all namespaced by generation run, not by capability -- no collision
risk since each generation run is a separate file). `package_id:
GGP:7ac75aa52c7227c84af8b0cb`. `qa_status: PASSED`. Funnel: 296 considered,
**0 rejected**, 296 accepted, 25 exported, no shortfall.
Difficulty distribution: `{Hard: 19, Medium: 6}`. Full per-question detail
in `DIRECTOR_V03_SECOND_CAPABILITY_HUMAN_REVIEW.md`.

**Disclosed limitation**: the shared package builder's `source_ids` block
uses Draft-shaped field names (`player_key`, `draft_team_code`,
`draft_season`, `franchise_id`). For Championship, only `franchise_id`
overlaps -- `team_code`, `season`, `record`, and `playoff_result` (which
exist in the adapter's own audit trail) aren't broken out into `source_ids`.
This doesn't affect correctness or QA (every fact remains fully verifiable
from the question text, `notes`, and `provenance`), and was deliberately
**not** fixed this milestone to avoid changing shared, already-approved
package-construction code beyond what was strictly required to make the
second capability executable at all (the `fetch_ordered_candidates` fix was
required; this is a completeness improvement, not a blocker). Flagged as
follow-up work, not silently left unexplained.

## Part C -- Cross-capability Director routing

All five run through the real `pipeline.run()` function:

| Request | Result |
|---|---|
| "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him." | **Routed to Draft adapter** (`NFL_DRAFT`/`DRAFTED_BY`) |
| "Make a game where I guess how a team's season ended in the playoffs." | **Routed to Championship adapter** (`NFL_CHAMPIONSHIP`/`TEAM_POSTSEASON_RESULT`) |
| "Make me some NFL player trivia." | **`NEEDS_CLARIFICATION`** -- `understood: {"competition":"NFL"}`, `missing_fields: ["domain","relationship_predicate"]`, did not guess |
| "Make me an NFL player guessing game from five career clues." | **`UNDERSTOOD_BUT_UNSUPPORTED`** -- `closest_supported_capability: ("guess","NFL_DRAFT","DRAFTED_BY")` -- player-from-clues was deliberately NOT implemented this milestone (explicitly forbidden by the restrictions list) |
| "Give me a game where I guess both a QB's team and his favorite food." | **`UNDERSTOOD_BUT_UNSUPPORTED`** -- blocked as a whole; notes explicitly name BOTH unsupported parts (QB-team-guessing has no registered capability, favorite-food has no data at all) rather than silently generating just the QB half |

A regression bug was caught and fixed during this testing: the
`NEEDS_CLARIFICATION` heuristic initially also fired for "Make a game about
NFL players favorite foods." (mentions "NFL" + "player"), which would have
changed that request's behavior from v0.2's documented `NO_MATCH` to
`NEEDS_CLARIFICATION` -- incorrect, since no clarification question could
ever resolve a request for a data domain that doesn't exist. Fixed by
excluding requests containing an off-topic marker (food/favorite) from the
clarification branch; re-verified the full v0.2 regression set (paraphrases
B/C, unsupported D/E, injection F1/F2) still produces identical outcomes to
what `GAME_DIRECTOR_V02_REPORT.md` documented.

## Part D -- Clarification contract

See `DIRECTOR_V03_CLARIFICATION_CONTRACT.md` for the full spec. Summary:
`{status: "NEEDS_CLARIFICATION", understood, missing_fields, question}`,
returned by `pipeline.run()`, tested via the "ambiguous request" case above.
`understood` and `question` are display text only, never re-parsed as
intent by any code path -- no frontend UI was implemented, per the
milestone's explicit restriction.

## Part E -- Security and audit logging

`tools/director_v02/audit_log.py`, writing to `tools/director_v02/logs/
audit_log.jsonl` (local only -- not referenced by `index.html`, `app.js`, or
the service worker). Every field from the Part E checklist is recorded:
request ID, provider, request-text hash, validated spec, capability
selected, translation status, generation status, package ID, provider
latency, Engine generation latency, rejection reason. **Never logged**: API
keys, authorization headers, secret values -- the logging module never reads
an environment variable or header at all. Raw request text IS logged in
full alongside its hash for this development milestone, explicitly flagged
in the module docstring as a dev-only choice with a documented one-line flip
(`RAW_TEXT_LOGGING = False`) for a production design that should prefer
hash-only. 27 real entries accumulated during this milestone's own testing
(15 `GENERATED`, 12 `NOT_ATTEMPTED`), confirming the logging path executes
correctly under real pipeline runs, not just unit-tested in isolation.

## Security summary

- **Schema validation**: unchanged from v0.2, now covering 2 capabilities
  instead of 1 -- exact key-set check, per-field allowlist checks, bounds
  checks. Re-verified with 4 hand-crafted "compromised translator" cases
  (SQL-as-predicate, injected extra field, path-traversal-as-domain,
  resource-exhaustion question_count) -- all still rejected correctly at the
  validator layer alone.
- **Allowlist enforcement**: `ALLOWED_DOMAINS`/`ALLOWED_PREDICATES` grew from
  1 to 2 entries each, still finite hardcoded Python sets -- no free-form
  domain or predicate value is or has ever been accepted.
- **Execution isolation**: confirmed again this milestone -- no provider
  module has any import path to Engine code or the database; the LLM (real
  or mock) never contributes a football fact, answer, or distractor, only a
  handful of literal enum values, all independently re-checked.
- **Audit logging**: see Part E above.
- **Timeout/token/request limits**: unchanged from v0.2 (15s timeout,
  300-token output cap, 500-char input truncation, one call per request, no
  retry loop) -- still enforced, still never live-tested against a real API
  this milestone.

---

> **Can Reads now use a real LLM, when configured, to translate flexible
> natural language into one of at least two registered deterministic
> football game-generation capabilities without allowing the LLM to control
> football truth or execution?**

**Architecturally, yes -- empirically, not yet verified against a real
provider.** The full pipeline (translator -> strict validator -> capability
registry -> shared, deterministic Engine generation -> QA -> package) now
correctly routes between two real, independently-proven capabilities, fails
closed on ambiguous/unsupported/hostile input without ever letting any
translator (mock or, by construction, a real LLM) contribute football
content, and remains deterministic after translation regardless of which
capability is selected -- all verified empirically against the mock
translator, which exercises the exact same downstream code path a real
provider would. What's **not yet verified**: that `AnthropicTranslator`'s
real HTTP/JSON-parsing/prompt-following behavior actually produces
`TranslationResult`s that clear the same bar, because no credential has ever
been available to test it. The honest answer is: the safety guarantee holds
for *any* translator by construction (validator.py never trusts translator
output), but the *usefulness* claim -- "a real LLM will correctly route
these two capabilities and paraphrases of them" -- remains unverified until
Part A3/A4 actually run.

## Exact files created or modified

**Created:**
- `tools/director_v02/run_real_provider_verification.py`
- `tools/director_v02/audit_log.py`
- `tools/director_v02/logs/audit_log.jsonl` (accumulated data, not a code file)
- `generated_games/director-v03-second-capability.json`
- `DIRECTOR_V03_SECOND_CAPABILITY_HUMAN_REVIEW.md`
- `DIRECTOR_V03_CLARIFICATION_CONTRACT.md`
- `GAME_DIRECTOR_V03_REPORT.md` (this file)

**Modified:**
- `tools/director_v02/providers/anthropic_provider.py` -- hardened per Step
  A2 (fence-tolerant JSON extraction, status/spec-type normalization);
  system prompt extended to describe both registered capabilities and the
  new `NEEDS_CLARIFICATION` status.
- `tools/director_v02/providers/base.py` -- added `NEEDS_CLARIFICATION` to
  `TRANSLATION_STATUSES`; documented its extra `understood`/`missing_fields`/
  `clarifying_question` fields.
- `tools/director_v02/providers/mock.py` -- added the Championship keyword
  pattern, the mixed-unsupported ("both...food") pattern, and the
  `NEEDS_CLARIFICATION` fallback; fixed the tokenizer to handle possessives
  ("team's"); fixed a regression where off-topic requests mentioning "NFL"
  were misclassified as `NEEDS_CLARIFICATION` instead of `NO_MATCH`.
- `tools/director_v02/schema.py` -- added `NFL_CHAMPIONSHIP` to
  `ALLOWED_DOMAINS`, `TEAM_POSTSEASON_RESULT` to `ALLOWED_PREDICATES`.
- `tools/director_v02/registry.py` -- added the Championship capability entry.
- `tools/director_v02/validator.py` -- added `NEEDS_CLARIFICATION` handling.
- `tools/director_v02/pipeline.py` -- surfaces `understood`/`missing_fields`/
  `question` for the clarification case; added audit-logging calls with
  provider/Engine-generation latency instrumentation.
- `tools/game_director_v01.py` -- `generate_package_from_spec()` now calls
  `adapter.fetch_ordered_candidates(c, seed)` uniformly instead of
  hardcoding `game_factory.generate_candidates(spec, ...)` (see Part B2);
  removed the now-unused `import game_factory as GF`. Re-verified
  byte-identical v0.1/v0.2 Draft output after this change.

**Not modified:** `game_director.py`, `game_director_api.py`,
`game_factory.py`, `tools/quiz_export/adapters/draft.py`,
`tools/quiz_export/adapters/championship.py`,
`tools/quiz_export/adapters/qb_season.py` (inspected, not registered, not
touched), every other Engine `.py` file, `data/quiz.js` (the 582-question
pool), and every v0.1/v0.2-created file other than the ones listed above.

## CRITICAL restrictions -- compliance check

- Live Reads app (`app.js`, `index.html`, `sw.js`), Firebase, the 582-question
  pool -- all untouched (confirmed by mtime: all predate this session).
- No deployment, no public endpoint, no hosting migration, no server started.
- LLM given no SQL access, no tools, no ability to name free-form
  tables/predicates, no ability to generate answers or distractors --
  unchanged and re-verified this milestone.
- No auto-publish -- `review_status` starts `"UNREVIEWED"` for both packages.
- Registered exactly one additional capability (Championship), not more.
- Player-from-clues was NOT implemented -- confirmed `UNDERSTOOD_BUT_UNSUPPORTED`
  in Part C, not a working capability.
- No arbitrary new game mechanics added -- still only `guess`.
- Local/admin-only throughout; no key committed (confirmed via grep for
  known API key patterns across all files touched this milestone -- no matches).
