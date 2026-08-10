# Director v0.4 -- Player From Clues -- Report

Milestone: build the first genuinely new Engine-generated game mechanic --
`identify_player_from_clues` -- where a player receives a progressive
sequence of verified clues about one NFL player and must identify them.
Non-negotiable principle honored throughout: the Engine/database is the
source of truth for every clue; the LLM/translator layer is responsible
only for interpreting user intent, never for inventing or selecting facts.

## Feasibility findings (Part A)

Full detail in `PLAYER_FROM_CLUES_FEASIBILITY_REPORT.md`. Audited all 225
tables in the Engine database directly (row counts, `verification_status`,
`data_coverage.production_safe` flags) rather than assuming a table's
existence implied usable data -- this caught real cases where a table
existed with a populated schema but zero imported rows
(`player_season_stats`: 0 rows despite full pass/rush/rec/sack column
definitions).

**Base safe universe: 4,506 players** -- every `draft_facts` row that is
`SOURCE_BACKED`/`NFLVERSE_DATA`, uses a `PFR:...`-format key, and has a
matching row in `canonical_players.player_id`.

## Safe clue families (Part A)

| Clue family | Status | Coverage |
|---|---|---|
| Draft year / round / pick overall | SAFE | 100% |
| Position (at draft) | SAFE | 99.8% |
| Drafting franchise | SAFE | ~87% (same resolution rate as the approved Draft capability) |
| NFL teams played for | SAFE | 100% |
| Career span (first/last season) | SAFE | 100% |
| College | SAFE_WITH_LIMITATIONS | 47% (only players with exactly 1 distinct school on record) |
| Postseason participation | SAFE_WITH_LIMITATIONS | 63% |
| Won a Super Bowl | SAFE_WITH_LIMITATIONS | 11% |

## Rejected clue families and why (Part A)

- **QB season information -- IDENTITY_RISK, excluded entirely.**
  `qb_team_seasons.qb_source_id` uses GSIS-format IDs; the safe universe is
  PFR-keyed. `canonical_players.gsis_id` is `NULL` for all 7,277 rows -- no
  populated bridge exists anywhere in the 225-table schema. Bridging would
  require name-based matching, which the non-negotiable principle forbids.
  This is exactly the reverse-identity issue the QB pilot already exposed.
- **Statistical milestones -- UNAVAILABLE.** `player_season_stats` has 0
  rows (schema exists, never imported).
- **NFL awards/accomplishments -- UNAVAILABLE.** No NFL-level awards table
  or relationship exists; the only award data in the schema is 100%
  college-side (`WON_AWARD`'s subject is always `cfb_player`).

## Identity resolution (Part B)

Full detail in `DIRECTOR_V04_IDENTITY_POLICY.md`. Core rule: identity =
`canonical_players.player_id`; every clue source joins to it by exact
string equality; `display_name` is used only for display text, never as a
join key or equality check. Key finding: `player_identity_links` (the
table that looked like a cross-source identity bridge) turned out to be
entirely trivial on inspection -- every one of its 4,506 rows has
`canonical_player_id == nfl_player_key` (0 rows differ) -- so it provides
no additional resolution beyond a plain string-equality join, which is
exactly what this mechanic uses directly instead. Real identity risk found
and handled: 104 players have 2+ distinct colleges on record (transfers or
a bridge inconsistency) and are excluded from the college clue family
entirely, not resolved by guessing.

## Mechanic definition (Part C)

`identify_player_from_clues` -- deliberately not a `guess` variant (no
options/correctIndex; answer is a resolved entity). Full contract in
`PLAYER_FROM_CLUES_MECHANIC_SPEC.md`: 3-5 structured clues per puzzle,
broad-to-narrow ordering (each clue must strictly narrow the running
candidate set, "true but useless" clues are never selected), final
candidate set must equal exactly `{target_player_id}` or the puzzle is
rejected outright.

## Candidate player universe

**4,506 players.** Every one of them was attempted this run (deterministic
seeded order, not a sample).

## Puzzles attempted / accepted / rejected

| Stage | Count |
|---|---|
| Attempted | 4,506 |
| **Accepted (passed every rule, independently re-verified)** | **3,454 (76.7%)** |
| Exported into the canonical package | 25 |

Rejection reasons (all 1,052 rejections were the same underlying cause --
ambiguity, never a crash or a malformed puzzle):

| Reason | Count |
|---|---|
| AMBIGUOUS_FINAL_SET_SIZE_2 | 752 |
| AMBIGUOUS_FINAL_SET_SIZE_3 | 181 |
| AMBIGUOUS_FINAL_SET_SIZE_4 | 54 |
| AMBIGUOUS_FINAL_SET_SIZE_5 | 38 |
| AMBIGUOUS_FINAL_SET_SIZE_7 | 13 |
| AMBIGUOUS_FINAL_SET_SIZE_6 | 8 |
| AMBIGUOUS_FINAL_SET_SIZE_8 | 6 |
| QA_FAILED | 0 |
| INSUFFICIENT_NARROWING_CLUES | 0 (never occurred in this real run -- every one of the 4,506 players had at least 3 usable clue types; confirmed reachable and correct via a synthetic unit test, see Part P) |

**25 of 25 requested puzzles were exported -- no shortfall.**

## Average clues per puzzle

**4.68** (out of a 3-5 range) across the exported 25.

## Clue-type distribution (exported 25)

`draft_round`: 23, `career_span`: 24, `position`: 24, `postseason_participation`: 13,
`draft_year`: 12, `draft_pick_overall`: 11, `drafting_franchise`: 6, `college`: 3,
`won_super_bowl`: 1. `postseason_participation` and `draft_round` dominate as early
clues because they are the two broadest available splits in the data
(largest single candidate-set fractions) -- an honest reflection of the
real data's information structure, not a design choice to favor them.

## Final uniqueness results

**100% of the 25 exported puzzles (and all 3,454 accepted puzzles) resolve
to exactly 1 eligible player** -- checked twice: once during construction,
and once independently in `validate_puzzle_qa()`, which re-derives every
candidate set from scratch rather than trusting construction's own
bookkeeping. Zero QA failures across all 3,454 accepted puzzles.

## Production-safety results

Five independent checks, all passed: `NFL_DRAFT` domain coverage,
`canonical_players` table-wide, `canonical_roster_seasons` table-wide
(`games > 0`), `season_standings` table-wide (`playoff_result IS NOT NULL`),
`NFL_CFB_IDENTITY_BRIDGE` domain coverage (for the college clue family).

## Determinism results (Part O)

Ran twice, both as a direct adapter call and through the full
translator -> validator -> registry -> pipeline path:

- Direct adapter (`player_from_clues.build_package()`): content-normalized
  SHA-256 identical across 2 runs
  (`6a4aeb690936b6dc84d0ccbf03577333369da208daa4b195397359481f0aeee0`),
  `package_id` identical (`GGP4:7b4a6260b92fc2a0d6902e56`).
- Full pipeline (`director_v02.pipeline.run()`): content-normalized package
  identical across 2 runs, `package_id` identical. Zero fields differed
  besides `generated_at`.

## Adversarial QA results (Part P)

- **Identical/similar names**: "Mike Williams" resolves to 4 different real
  `player_id`s in the safe universe. 3 of 4 produced valid, independently
  QA-passing puzzles that correctly resolved to their own distinct
  `player_id` (verified programmatically, not by inspection); the 4th was
  correctly *rejected* as ambiguous rather than resolved incorrectly.
- **Players outside the safe universe** (`DRAFT:...`-prefixed synthetic
  keys): confirmed 0 such keys ever appear in the adapter's internal
  `facts` dict -- structurally unreachable, not merely untested.
- **Duplicate college/player combinations**: 104 real players with 2+
  distinct recorded schools were checked directly -- 0 of them were ever
  assigned a `college` clue value (confirmed programmatically).
- **Sparse players with too few clues**: no real player in this run
  triggered `INSUFFICIENT_NARROWING_CLUES` (every player had >=3 usable
  clue types), so this code path was exercised with a targeted synthetic
  fixture (a player with only a `draft_year` fact and no other data) --
  correctly rejected with that exact reason.
- **Contradictory cross-source facts**: structurally prevented, not merely
  checked -- each `clue_type` reads from exactly one authoritative source
  per player (a single dict key per type), so two different values for the
  same clue type cannot coexist in the data model at all.
- **Historical franchise aliases / midseason team changes**: handled by
  reusing `resolve_franchise()`, the exact function already proven across
  four prior capabilities -- no new franchise-resolution logic was written
  for this mechanic.
- **No manual whitelisting**: every test above used real data properties
  (actual name collisions, actual multi-school conflicts found by query),
  not hand-picked famous players chosen to guarantee success.

## Translator paraphrase results (Part K)

Mock translator extended with a Player From Clues pattern (clue+player
keywords, or a "who am I" phrase -- not hard-coded sentence matches). All 4
required paraphrases correctly routed to
`(identify_player_from_clues, NFL_PLAYER_IDENTITY, IDENTIFY_FROM_CLUES)`:

1. "Make me a game where you give me clues about an NFL player and I have to identify him." -> TRANSLATED
2. "Give me clues one at a time and make me guess the NFL player." -> TRANSLATED
3. "Make a Who Am I football game using facts about NFL players." -> TRANSLATED
4. "I want to identify players from career clues." -> TRANSLATED

Before this milestone, this exact pattern (clue + player keywords) returned
`UNDERSTOOD_UNSUPPORTED_MECHANIC` (v0.2/v0.3's documented, correct behavior
at the time, since the capability didn't exist yet). It now correctly
routes to a real capability instead -- the translator's job never changed
(mechanic/capability selection only); what changed is that a capability now
exists to select.

**Full regression suite re-run** (all prior v0.2/v0.3 test cases) after
this change: Draft paraphrases, difficulty/count variants, the
"favorite foods" unsupported case, injection cases, the Championship
capability, the ambiguous-request clarification case, and the mixed-
unsupported case all produced **identical outcomes** to what
`GAME_DIRECTOR_V02_REPORT.md`/`GAME_DIRECTOR_V03_REPORT.md` documented.

## Capability registry result (Part J)

Registered **only after** generation was independently proven (3,454/4,506
QA-passing puzzles, deterministic, adversarially tested):

```python
("identify_player_from_clues", "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"): {
    "adapter": player_from_clues,
    "generate_fn": _generate_player_from_clues_package,
    "max_question_count": 25,  # bounded by this milestone's proven run
    "supported_difficulties": frozenset({"any"}),  # no difficulty model -- see Part H
    ...
}
```

The two existing capabilities remain exactly as registered in v0.3:
`(guess, NFL_DRAFT, DRAFTED_BY)` and `(guess, NFL_CHAMPIONSHIP,
TEAM_POSTSEASON_RESULT)` -- unchanged, re-verified byte-identical after the
registry/pipeline refactor this milestone required (see "Architectural
change" below). Exactly one new capability was added, as instructed.

## Difficulty model (Part H)

**`difficulty: null`.** No Engine-native difficulty score exists for this
mechanic (unlike Draft/QB/Championship, which all cross-reference an
existing `puzzle_catalog` mode -- none exists for player-identification
puzzles). Candidate-narrowing-curve-as-proxy and draft-position-as-fame-proxy
were both considered and rejected as not rising to the same evidentiary
standard as the other capabilities' engine-native scores -- see
`PLAYER_FROM_CLUES_MECHANIC_SPEC.md`, Part H, for the full reasoning.
Candidate-narrowing statistics are still recorded on every clue and
reported above, honestly labeled as narrowing statistics, not repackaged as
a fabricated difficulty label.

## Architectural change required (disclosed)

`tools/game_director_v01.py`'s `generate_package_from_spec()` is
`guess`-mechanic-shaped (options/correctIndex) and cannot represent this
mechanic's clue-sequence/entity-answer package. Rather than force-fit it,
`director_v02/pipeline.py` was generalized to dispatch via each registry
entry's own `generate_fn` callable, instead of hardcoding the
Game-Factory-spec-building logic inline. This is a real, disclosed change
to already-approved v0.2/v0.3 code -- re-verified byte-identical output for
both existing capabilities' packages after the change (see Determinism
section of prior reports' logic, re-run this milestone with zero diffs).
`generate_package_from_spec()` itself was not modified; only how
`pipeline.py` calls into generation logic changed.

## Exact files created

- `PLAYER_FROM_CLUES_FEASIBILITY_REPORT.md`
- `DIRECTOR_V04_IDENTITY_POLICY.md`
- `PLAYER_FROM_CLUES_MECHANIC_SPEC.md`
- `tools/director_v04/__init__.py`
- `tools/director_v04/player_from_clues.py`
- `generated_games/director-v04-player-from-clues.json`
- `DIRECTOR_V04_PLAYER_FROM_CLUES_HUMAN_REVIEW.md`
- `GAME_DIRECTOR_V04_REPORT.md` (this file)

## Exact files modified

- `tools/director_v02/registry.py` -- added the third capability entry;
  extracted the `guess`-mechanic generation logic (previously inline in
  `pipeline.py`) into `_generate_guess_package()`; added
  `_generate_player_from_clues_package()`; both wired via each capability's
  `generate_fn`.
- `tools/director_v02/pipeline.py` -- generalized to dispatch via
  `capability["generate_fn"]` instead of hardcoding a Game-Factory-spec
  build; `director_spec`/`translator` now attached generically after
  generation rather than inside one mechanic's generator.
- `tools/director_v02/schema.py` -- added `identify_player_from_clues` to
  `ALLOWED_MECHANICS`, `NFL_PLAYER_IDENTITY` to `ALLOWED_DOMAINS`,
  `IDENTIFY_FROM_CLUES` to `ALLOWED_PREDICATES`.
- `tools/director_v02/providers/mock.py` -- replaced the old
  `UNDERSTOOD_UNSUPPORTED_MECHANIC` clue-pattern branch with a `TRANSLATED`
  branch routing to the new capability; added "who am I" phrase detection.
- `tools/director_v02/providers/anthropic_provider.py` -- system prompt
  updated to describe the third capability (untested live -- no credential
  exists, unchanged from v0.3).

**Not modified:** `game_director.py`, `game_director_api.py`,
`game_factory.py`, every `tools/quiz_export/` file, `draft.py`,
`championship.py`, `qb_season.py` (inspected only), `game_director_v01.py`
itself, and every prior report/package file.

---

> **Can Reads now take a supported request to identify an NFL player from
> progressive clues and generate a deterministic, source-backed, uniquely
> solvable Player From Clues game package without an LLM inventing football
> facts?**

**YES.** Verified end to end this milestone: a natural-language request
("give me clues about an NFL player and I have to identify him") is
recognized by the translator (mechanic/capability selection only), passes
strict schema validation, routes to a registered capability, and generates
a 25-puzzle package where every clue is source-backed (five independent
production-safety checks), every puzzle's final candidate set was
independently re-verified to contain exactly the target player and no one
else, the whole package is byte-identical across repeated runs with the
same seed, and adversarial testing against real identity-collision and
data-conflict cases in the actual database confirmed the mechanic fails
closed (rejects) rather than resolving incorrectly. The translator layer
(mock, standing in for a real LLM per Part Q) never selected, invented, or
influenced a single football fact -- it only chose which registered
capability applies.
