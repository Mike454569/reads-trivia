# Player From Clues -- Mechanic Contract (Director v0.4, Part C)

## Mechanic ID

`identify_player_from_clues`

Deliberately **not** a variant of `guess`. `guess` means "four options, pick
one, single fact." This mechanic means "a sequence of independently
verified facts, progressively narrowing an implicit candidate set to
exactly one person, no options presented." The answer representation,
QA model, and uniqueness requirements are structurally different -- see
Part G below. Overloading `guess` would have made its semantics stop
accurately describing what either mechanic does.

## Target entity type

`nfl_player`, restricted to the fixed 4,506-player safe universe defined in
`DIRECTOR_V04_IDENTITY_POLICY.md`. No player outside that universe can be a
puzzle target, regardless of what data might otherwise exist about them.

## Clue structure

Each clue is a structured object, never arbitrary prose:

```json
{
  "clue_index": 0,
  "clue_type": "draft_year",
  "value": 2017,
  "display_text": "This player was drafted in 2017.",
  "source": {
    "table": "draft_facts",
    "field": "draft_season",
    "source_id": "NFLVERSE_DATA",
    "verification_status": "SOURCE_BACKED"
  },
  "candidates_before": 4506,
  "candidates_after": 312
}
```

`display_text` is produced by a fixed, deterministic template per
`clue_type` (see the adapter's `CLUE_TEMPLATES`) -- never by an LLM. A
template fills in only the already-verified `value`; it cannot introduce a
fact that isn't already present in `value`/`source`.

## Clue type registry (from the feasibility report)

| `clue_type` | Value type | Availability in universe |
|---|---|---|
| `draft_year` | int | 100% |
| `draft_round` | int | 100% |
| `draft_pick_overall` | int | 100% |
| `position` | str (position code at draft) | 99.8% |
| `drafting_franchise` | str (resolved franchise full name) | ~87% |
| `team_history` | list of str (distinct teams played for, `games>0`) | 100% |
| `career_span` | [int, int] (first/last season with `games>0`) | 100% |
| `college` | str (school name) | 47%, only when exactly 1 distinct school on record |
| `postseason_participation` | bool + list of seasons | 63% |
| `won_super_bowl` | bool + list of seasons | 11% |

## Minimum / maximum clue count

**Minimum 3, maximum 5** per puzzle (Part D's "approximately 3-5"). A puzzle
that cannot assemble at least 3 clues that together narrow the safe universe
to exactly 1 candidate is rejected outright -- never padded with a
low-information clue just to hit the minimum.

## Clue ordering

Broad to narrow, enforced structurally, not just by convention: clues are
selected from the player's available clue-type pool and ordered by
descending `candidates_before` (the clue that starts from the largest
remaining candidate pool goes first). The adapter verifies, as part of QA
(Part N), that `candidates_after` is monotonically non-increasing across
the sequence and that each clue's `candidates_before` equals the previous
clue's `candidates_after` (a contiguous, unbroken narrowing chain -- not
independently computed subsets that happen to shrink).

`draft_pick_overall` (which, combined with `draft_year`, is a guaranteed
unique key -- see feasibility report) is deliberately weighted to appear
**last** when used, specifically so it plays the role of the final
uniqueness-resolving clue rather than trivializing the puzzle immediately.

## Answer representation (Part G)

```json
{
  "answer_type": "player",
  "player_id": "PFR:McCoLa02",
  "display_name": "LaDainian Tomlinson"
}
```

No four-option multiple-choice array at the core mechanic level. This
representation is answer-presentation-agnostic by design -- a future
milestone could layer a typed-answer UI, an autocomplete UI, or even a
four-option UI (by sampling 3 plausible-but-wrong names from the same
universe) on top of this same package without changing what the Engine
produces. None of those UIs are built in v0.4.

## Identity requirements

Per `DIRECTOR_V04_IDENTITY_POLICY.md` in full. Summarized: every clue joins
to the target's `player_id` by exact string equality against
`canonical_players.player_id`; no name-based matching anywhere; a player
with a conflicting fact for a given clue type (e.g. 2+ colleges) simply
doesn't get that clue type offered, never resolved by guessing.

## Production-safety requirements

Every clue's `source.source_id`/`verification_status` must reflect a
`SOURCE_BACKED` (or, for the two cross-domain relationships,
`PRODUCTION_SAFE_DERIVED`) row -- reusing the exact same
`tools/quiz_export/safety.py` patterns (`check_table_wide_safety`,
`check_domain_coverage_safety`) already proven across four capabilities.
No new safety-check design is introduced; only the tables/domains checked
differ.

## Ambiguity rules

- **Name-leakage rule**: no clue's `display_text` or `value` may contain
  the target player's `display_name` (or any substring of it) -- checked
  programmatically, not just by construction of the templates.
- **Uniqueness rule** (Part F, non-negotiable): the candidate set after the
  final clue must equal exactly `{target_player_id}` -- both in size (1)
  and in identity (it must actually be the target, not merely "some other
  single player," which would indicate a bug). `candidate_count_after_all_clues
  != 1` rejects the puzzle unconditionally.

## QA rules

See Part N below (full enumerated list) -- summarized here: target identity
resolved, every clue source-backed, every clue verified to belong to the
target player specifically (not just "a player with this value" -- the
actual row is checked against the target's `player_id`), no clue contains
the target's name, no contradictory clues (each clue type's value is read
from exactly one authoritative source per the identity policy, so
cross-source contradiction is structurally prevented rather than merely
checked for), no duplicate clue types within one puzzle, deterministic
ordering, monotonic non-increasing narrowing with a contiguous chain, exactly
one final candidate, no duplicate puzzle targets within one export, no
duplicate clue-type sequences within one export (a weaker check than full
duplicate detection, since exact duplicate clue *values* are already
prevented by "no duplicate puzzle targets"), valid package schema, complete
provenance, production safety passed.

## Difficulty model (Part H)

**`difficulty: null` for every v0.4 puzzle.** Investigated and rejected as
not-yet-defensible:

- **Engine-native difficulty score**: does not exist for this mechanic.
  Draft/QB/Championship all cross-reference an existing `puzzle_catalog`
  mode with its own separately-QA'd difficulty score (see those
  capabilities' adapters). No `puzzle_catalog` mode exists for
  player-identification puzzles -- there is nothing to cross-reference, and
  inventing a numeric score without an Engine-native source would be
  exactly the "fake precision" this milestone is told not to produce.
- **Candidate-narrowing shape as a proxy**: considered. Rejected as the
  primary signal because the total information content of any accepted
  puzzle is mathematically fixed (`log2(4506) ≈ 12.14 bits`, since every
  puzzle starts from the same fixed universe and narrows to exactly 1) --
  what varies is the *shape* of the narrowing curve, and translating curve
  shape into a human-perceived difficulty label would be an invented
  heuristic, not a measurement.
- **Draft position / career longevity as a fame/prominence proxy**:
  considered. Rejected -- both are real fields but are weak, noisy proxies
  for "how likely a person is to recognize this player" (many highly
  drafted players are largely forgotten; some very late picks became
  household names), and this project's standing rule is to not fake
  precision by dressing up a noisy heuristic as a difficulty score.

Candidate-narrowing statistics (`candidates_before`/`candidates_after` per
clue) are still recorded in full on every clue, and reported in aggregate in
`GAME_DIRECTOR_V04_REPORT.md` -- they are genuinely informative and are
reported as exactly what they are (narrowing statistics), not repackaged as
a fabricated Easy/Medium/Hard label.

## Scoring-neutral package representation

The package contains no point values, no time-pressure fields, no
per-clue scoring weights -- purely the puzzle structure (clues, answer,
provenance, QA status). Scoring is a frontend/gameplay-layer concern, not
built in this milestone.

## Failure behavior

For every candidate player considered, the adapter runs the full clue
assembly -> ordering -> uniqueness-verification pipeline. Any failure at
any stage (fewer than 3 safe clue types available, narrowing chain broken,
final candidate count != 1, name-leakage detected) causes that player to be
skipped entirely for this generation run -- never a partially-built or
weakened puzzle. Rejection reasons are counted and reported per-reason (Part
N/R), the same funnel-accounting discipline already used by every prior
capability in this project.
