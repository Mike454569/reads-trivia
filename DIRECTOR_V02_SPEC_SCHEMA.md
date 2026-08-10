# Director v0.2 -- Structured Spec Schema

Documentation only -- describes the JSON shape a translator (LLM or the
deterministic mock) must produce, defined in `tools/director_v02/schema.py`.
This is the **only** interface between natural language and the Engine.
Nothing outside this shape is ever accepted; nothing inside it is ever
trusted without re-validation (see `validator.py`).

## Design rule

The spec below is deliberately **smaller** than v0.1's Game Factory spec. It
expresses only what a user's request actually varies:
`mechanic + domain + relationship_predicate + question_count + difficulty +
filters + exclusions`. Fields v0.1 needed for execution --
`entity_type`, `object_type`, `answer_type`, `group_size`, `competition_id`
-- are **not** translator-facing. They are derived, Engine-side, from the
registered capability triple `(mechanic, domain, relationship_predicate)` via
`registry.py`. A translator (including a real LLM) is never even offered the
option to name those fields, which shrinks the attack surface by construction
rather than by hoping the model behaves.

No field in this schema is free-form. Every field is either a literal from a
hardcoded allowlist, a bounded integer, or a structurally-typed but
currently-empty extension point (`filters`, `exclusions`).

## DirectorSpec (v0.2)

| Field | Type | Allowlist / bounds | Notes |
|---|---|---|---|
| `mechanic` | string | `{"guess"}` | Only mechanic with a Reads-renderable adapter today. |
| `domain` | string | `{"NFL_DRAFT"}` | Engine data domain. |
| `relationship_predicate` | string | `{"DRAFTED_BY"}` | The football relationship being asked about. |
| `question_count` | integer | `1`-`100` (schema-level); a registered capability may declare a tighter range | Directly becomes `target_count`. |
| `difficulty` | string | `{"any", "easy", "medium", "hard"}` | `"any"` = no filtering (v0.1's original behavior). Any other value filters already-computed, already-QA'd candidates by their natural difficulty band -- never invents or reclassifies a difficulty. |
| `filters` | object | keys must be a subset of `ALLOWED_FILTER_KEYS` (currently **empty** -- no capability supports any filter key yet) | Structural extension point, not a free-form dict. Any key present today is rejected as unsupported, never silently dropped or executed. |
| `exclusions` | array of string | must be `[]` (currently **no** capability supports exclusions) | Same extension-point pattern as `filters`. |

A valid spec dict has **exactly** the keys `{mechanic, domain,
relationship_predicate, question_count, difficulty}` required, plus the two
optional `{filters, exclusions}` -- no more, no fewer. `validator.py` checks
this exact key set before checking anything else: an extra field (e.g. an
injected `sql`, `table`, `path`, `eval`) is a hard schema failure, not an
ignored field.

## Why the allowlists are split into two layers

There are two distinct "is this real" questions, and this schema keeps them
separate on purpose:

1. **Is this a value the schema can express at all?** -- `schema.py`'s
   `ALLOWED_*` sets. These represent real football/game concepts the spec
   format knows how to name.
2. **Is this specific combination something the Engine can actually
   execute today?** -- `registry.py`'s `CAPABILITY_REGISTRY`. Only
   combinations that have already run successfully in a prior approved
   pilot or Director v0.1 are registered.

Today `ALLOWED_PREDICATES` and `CAPABILITY_REGISTRY` happen to describe the
same single value (`DRAFTED_BY`), but the split exists so a spec can be
**schema-valid and still correctly rejected** as
`UNDERSTOOD_BUT_UNSUPPORTED` once a second predicate is added to the schema
before an adapter for it exists -- exactly how v0.1's `NFL_ATTENDED_SCHOOL`
case worked. See `GAME_DIRECTOR_V02_REPORT.md`, Step 6, for a live example.

## TranslationResult (what a translator returns, before validation)

```json
{
  "raw_request_text": "...",
  "translator_id": "mock-deterministic-v1",
  "translation_status": "TRANSLATED",
  "spec": { "...DirectorSpec above, or null..." },
  "translator_notes": "short, human-readable, informational only -- never executed"
}
```

`translation_status` is one of:

- **`TRANSLATED`** -- `spec` is populated and, in the translator's own
  judgment, matches the schema. Still independently re-validated by
  `validator.py` -- this status is never trusted at face value.
- **`UNDERSTOOD_UNSUPPORTED_MECHANIC`** -- the translator recognized a
  specific, real game concept that has no expressible/registered mapping
  (e.g. "identify a player from five clues"). `spec` is `null`.
- **`NO_MATCH`** -- the translator could not confidently map the request to
  anything, including hostile/off-topic/injection-style input. `spec` is
  `null`.

## GateResult (what `validator.py` returns)

```json
{
  "gate_status": "READY",
  "gate_reason": "...",
  "validated_spec": { "...DirectorSpec, only when READY..." },
  "capability": { "...registry entry, only when READY..." },
  "missing_capability": null,
  "closest_supported_capability": null
}
```

`gate_status` values: `READY`, `BLOCKED_NO_TRANSLATION`,
`BLOCKED_INVALID_SPEC`, `BLOCKED_OUT_OF_BOUNDS`,
`BLOCKED_UNSUPPORTED_FILTER`, `UNDERSTOOD_BUT_UNSUPPORTED`. See
`validator.py`'s module docstring for exactly which check produces which
status.

## Explicitly out of scope for v0.2

- Any `mechanic`, `domain`, or `relationship_predicate` value beyond the one
  registered capability -- adding a second is a registry change plus a proven
  adapter, not a schema change.
- Any non-empty `filters` or `exclusions` value -- no adapter implements
  either yet.
- Free-text fields that flow into execution. `translator_notes` exists for
  human/audit readability only and is never read by any code path that
  touches the database, a file path, or a shell command.
