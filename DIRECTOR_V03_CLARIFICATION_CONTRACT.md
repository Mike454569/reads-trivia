# Director v0.3 -- Clarification Contract (Part D)

Documentation only -- defines the structured result the backend returns when
a request is genuinely underspecified. **No frontend UI is implemented for
this in this milestone.** Only the backend result shape is defined and
tested.

## Why this exists

Before this milestone, an underspecified-but-clearly-NFL-related request
(e.g. "Make me some NFL player trivia") had only two possible outcomes:
`NO_MATCH` (implying nothing was understood at all, which is inaccurate --
"NFL" and "player" WERE understood) or a guess at which capability was
meant (which this project's entire design explicitly refuses to do -- see
every prior milestone's "do not silently change the user's requested game"
rule). `NEEDS_CLARIFICATION` is the honest third option: acknowledge what
was understood, name what's still missing, and surface a question -- without
ever picking an answer on the user's behalf.

## Result shape

Returned by `tools/director_v02/pipeline.py`'s `run()` whenever
`validator.validate_translation()` produces `gate_status ==
"NEEDS_CLARIFICATION"`:

```json
{
  "package_id": null,
  "status": "NEEDS_CLARIFICATION",
  "reason": "Translator recognized partial NFL/trivia intent but not enough to resolve to a specific game: ...",
  "director_request_id": "GDR2:...",
  "translator": { "...full TranslationResult, for audit..." },
  "missing_capability": null,
  "closest_supported_capability": null,
  "understood": { "competition": "NFL" },
  "missing_fields": ["domain", "relationship_predicate"],
  "question": "What kind of NFL trivia game do you want -- for example, guessing which team drafted a player, or guessing how a team's season ended in the playoffs?"
}
```

This matches the shape given in the v0.3 task description exactly
(`status` / `understood` / `missing_fields` / `question`), with the
additional fields every other pipeline result already carries
(`package_id`, `director_request_id`, `translator`, `reason`) so callers can
handle all non-`READY` outcomes uniformly.

## Field-by-field

| Field | Type | Notes |
|---|---|---|
| `status` | string | Always `"NEEDS_CLARIFICATION"` in this branch. |
| `understood` | object | Structured fields the translator IS confident about. Today, in practice, this is only ever `{"competition": "NFL"}` -- the mock and the real-provider system prompt are both scoped to NFL content only, so there is nothing else to be confident about yet. **Display text only** -- never used to construct a spec or select a capability; the Engine does not act on `understood`'s contents. |
| `missing_fields` | array of string | Which `DirectorSpec` fields remain unresolved. In practice today: `["domain", "relationship_predicate"]` -- the translator has enough to know this is an NFL guessing-style request but not enough to know which registered capability. |
| `question` | string | A short, human-readable clarifying question. **Display text only** -- never re-parsed as intent by any code path. A future frontend would show this to the user and collect a follow-up answer, which would then be sent through `pipeline.run()` again as a new, more specific request -- this milestone does not implement that follow-up loop. |

## Who decides what's "missing"

Per the task description: *"The LLM may propose the clarification wording,
but the Engine must determine which required structured fields are
missing."* In the current implementation, `missing_fields` is passed
through from whatever the translator (mock or real LLM) reports, because at
the `NEEDS_CLARIFICATION` stage there is no partial spec object for the
Engine to inspect field-by-field yet -- the translator itself is reporting
"I don't have enough to name a domain/predicate," which is a translation
judgment, not a validation judgment. This is a real limitation, disclosed
here rather than glossed over: `missing_fields`'s trustworthiness depends on
the translator being honest about what it does and doesn't know. It carries
no execution risk either way -- `missing_fields` and `understood` are never
read by `validator.py`, `registry.py`, or `generate_package_from_spec()`;
they are purely informational fields threaded through to the caller. A
future milestone that wants Engine-verified `missing_fields` would need the
translator to emit a *partial* spec (with `null`s for unknown fields) for
the Engine to inspect against `schema.REQUIRED_SPEC_KEYS`, rather than a
free-standing `missing_fields` list.

## How the mock translator decides (for reproducibility)

`providers/mock.py`: fires `NEEDS_CLARIFICATION` when the request contains
the word "nfl" AND ("player" or "team") AND does NOT match the Draft
pattern, the Championship pattern, the clue-based-identification pattern, or
an off-topic marker (e.g. "food"/"favorite" -- a request naming a specific
unsupported subject isn't something clarification would resolve, so that
case falls through to `NO_MATCH` instead, unchanged from v0.2's documented
behavior). This is a narrow, disclosed heuristic -- see `mock.py`'s
docstring -- not a claim of real ambiguity-detection intelligence.

## Tested

See `GAME_DIRECTOR_V03_REPORT.md`, Part C: `"Make me some NFL player
trivia."` produces exactly the shape above, through the real
`pipeline.run()` function (not a hand-simulated shortcut). No package was
generated; `review_status`/`package_id` never came into existence for this
request.
