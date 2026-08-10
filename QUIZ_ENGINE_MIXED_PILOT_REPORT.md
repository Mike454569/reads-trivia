# Quiz Engine Mixed Pilot -- Audit Report

Built by `tools/build_mixed_pilot.py`, running the Draft, QB/Season, and Championship/Postseason domain adapters through the shared `tools/quiz_export` framework and combining their outputs -- **not** a concatenation of the three existing per-domain pilot `.js` files. Output: `data/quiz-engine-mixed-pilot.js` (`window.QUIZ_DATA_ENGINE_MIXED_PILOT`). Not wired into the running app.

## Framework refactor verification (prerequisite for this pack)

Before this mixed pack was built, all three refactored adapters were run through the new shared framework and their output byte-diffed (SHA-256) against the already-existing pilot files:

| Domain | Existing file | SHA-256 match |
|---|---|---|
| draft | `data/quiz-engine-pilot-v2.js` | MATCH (`3dcbe7d3625bcfe6...`) |
| qb_season | `data/quiz-engine-qb-pilot.js` | MATCH (`fbd0541009af62a7...`) |
| championship | `data/quiz-engine-championship-award-pilot.js` | MATCH (`be13f338b50164cf...`) |

**All three: byte-identical.** PASSED -- the shared framework reproduces every existing pilot's output exactly, confirming the refactor changed nothing about existing behavior.

## Target vs exported

- Target: **300** (100 per domain x 3)
- Exported: **300**

## Counts by domain

| Domain | Considered | Rejected | Accepted (QA-passing) | Exported | ID range |
|---|---|---|---|---|---|
| draft | 500 | 69 | 431 | 100 | 500000-500099 |
| qb_season | 1587 | 1341 | 246 | 100 | 500100-500199 |
| championship | 296 | 0 | 296 | 100 | 500200-500299 |

### Rejection reasons by domain

**draft:**

| Reason | Count |
|---|---|
| TEAM_UNRESOLVED | 54 |
| DUPLICATE_PLAYER | 14 |
| DUPLICATE_QUESTION | 1 |

**qb_season:**

| Reason | Count |
|---|---|
| DUPLICATE_PLAYER | 1003 |
| NO_ENGINE_DIFFICULTY_AVAILABLE | 264 |
| UNRESOLVED_QB_IDENTITY | 49 |
| MULTIPLE_PLAUSIBLE_ANSWERS_MIDSEASON_TRADE | 20 |
| TEAM_UNRESOLVED | 5 |

**championship:**
(none -- zero rejections)

## Counts by category

| Category | Count |
|---|---|
| NFL Draft History | 100 |
| Passing Records & QB Trivia | 100 |
| Playoffs & Postseason Moments | 100 |

## Counts by difficulty (combined, all 300)

Hard 187, Medium 87, Easy 26

## Season/year range

- Draft slice: 1980-2024
- QB/Season slice: 1999-2025
- Championship slice: 2002-2025
- Combined: **1980-2025**

## Franchise coverage

- Combined: **32 / 32** franchises appear at least once across the pack
- Draft slice: 31 / 32
- QB/Season slice: 31 / 32
- Championship slice: 29 / 32

## Unique player count

- Draft: **100 / 100** unique players (0 repeats)
- QB/Season: **99 / 100** unique QBs
- Championship: N/A -- this domain has no single-player concept (each question is about a team-season outcome, not a person); see `dup_team_seasons` in the funnel stats for its equivalent entity check (0 found, since (team,season) is a primary key)

## Repeated player/team appearances (reported, not removed)

Per instruction, unique-player enforcement is **not** applied globally across domains (a player being both drafted and later a starting QB, or a franchise reaching multiple postseasons, are legitimate, materially different facts, not duplicates). Reported instead:

- **Draft**: 0 repeated players (unique-player-per-export was already enforced within this domain's own adapter, inherited from the original pilot design)
- **QB/Season**: 1 repeated *name* -- Nick Foles (x2). Checked directly: this is **not** a guard failure -- the two questions use two genuinely different `qb_source_id` values (`00-0029567` and `00-0032792`), both labeled `"Nick Foles"` in `qb_team_seasons`. The adapter's identity-consistency exclusion (`IDENTITY_INCONSISTENT_QB_IDS`, from `QB_SEASON_ENGINE_COVERAGE_REPORT.md`) only catches the reverse pattern -- one ID mapping to multiple names -- not this one, so it wasn't caught before. This is a genuine data-quality finding, newly surfaced by combined-scale analysis, and it already exists in the standalone, previously-approved `quiz-engine-qb-pilot.js` output too (the mixed pack's QB slice is confirmed identical to it). Reporting it here rather than silently fixing it, per the standing "do not guess, do not weaken QA without saying so" instruction -- no change has been made to either QB output as part of this report.
- **Championship**: franchises naturally repeat across different seasons (e.g. a franchise with several playoff runs) -- this is expected and not a defect. Most-repeated franchises in this slice: FR_NE (x8), FR_PIT (x7), FR_SEA (x7), FR_GB (x6), FR_PHI (x5)
- **Cross-domain name overlap (Draft vs QB/Season)**: 0 names appear in both slices -- none, so no risk of a reader confusing a draft-pick question with a QB-starts question about the same person

## Duplicate-question result

**PASSED** -- 0 duplicate question(s) across all 300, checked cross-domain (not just within each 100-question slice).

## Duplicate-ID result

**PASSED** -- 0 duplicate ID(s) across all 300.

## Contract-validation failures

**PASSED** -- 0 failure(s) across all 300 (each domain's questions checked against its own approved category, not one shared constant).

## Production-safety

Every one of the 300 questions passed its own domain's production-safety gate before being considered a candidate at all (Draft: `data_coverage` domain-row check for `NFL_DRAFT`; QB/Championship: exhaustive row-level `SOURCE_BACKED`/`NFLVERSE_DATA` check over the full source table) -- these gates run once per domain, unchanged from each adapter's original pilot, before any candidate is even generated.

## Determinism

**PASSED** -- reran `tools/build_mixed_pilot.py` against the unchanged database; `data/quiz-engine-mixed-pilot.js` was byte-identical on rerun.

## Per-domain slice consistency with the standalone pilots

Each domain's 100-question mixed-pack slice reuses that domain's own original seed. Verified: stripping IDs, the Draft slice's 100 questions are exactly the 100 questions in `quiz-engine-pilot-v2.js`; the QB slice matches `quiz-engine-qb-pilot.js`; the Championship slice matches `quiz-engine-championship-award-pilot.js` -- **identical question sets**, only renumbered into the mixed pack's own ID range. This is expected (same seed, same adapter logic, same target count) and confirms the mixed-pack build didn't introduce any selection drift relative to the already-approved pilots.

