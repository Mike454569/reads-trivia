# Quiz Export Framework -- Refactor Plan

Planning only. No files created or modified yet beyond this document. Based on a full,
line-by-line read of all three existing exporters:

- `tools/export_quiz_engine_pilot_v2.py` (Draft, 309 lines) -- the version to preserve; v1
  (50-question, pre-safe-fix) is not in this refactor's byte-identical scope
- `tools/export_quiz_engine_qb_pilot.py` (QB/Season, 354 lines)
- `tools/export_quiz_engine_championship_award_pilot.py` (Championship/Postseason, 334 lines)

## Logic duplicated across all three exporters

| Logic | Where it lives today | Notes |
|---|---|---|
| Engine bootstrap (`ENGINE_DIR`, `sys.path.insert`, `import game_factory as gf`) | Top of every file, identical | Trivial but triplicated |
| `resolve_franchise(c, team_code, season)` | Byte-identical function, all three | Queries `team_aliases`, returns `(dict, None)` or `(None, "TEAM_UNRESOLVED"/"TEAM_AMBIGUOUS")` |
| `DIFFICULTY_MAP` constant | Identical dict, all three | `{"EASY":"Easy","MEDIUM":"Medium","HARD":"Hard","EXPERT":"Hard"}` |
| Distractor RNG (`rng = gf.seeded(f"{SEED}:distractors")`) | Identical pattern, all three | One RNG instance, used for both distractor sampling and option shuffling, in that order |
| Option shuffle + correctIndex computation | Identical 4-line block, all three | `order=list(range(4)); rng.shuffle(order); shuffled=[options[i] for i in order]; correct_index=shuffled.index(correct_text)` |
| Contract-validation core checks | Near-identical loop, all three | Key-set check, `id` is int, difficulty enum, non-empty question, exactly-4-unique options, correctIndex range + points at verified answer |
| `dup_questions` / `dup_ids` via `Counter` | Identical, all three | |
| `write_output_js()` shape | Same structure, all three | Build a 7-key clean list (fixed key order), `json.dumps(indent=2, ensure_ascii=False)`, custom header comment block, `window.NAME = ` + body + `;\n`. Header **text** and global **name** differ per domain. |
| Funnel-stats JSON shape | Same base fields, all three | `seed, considered, rejected_counts, total_rejected, accepted_total, exported_count, accepted_but_not_exported, shortfall_reason, category_distribution, difficulty_distribution, min/max_season, dup_questions, dup_ids, contract_failures, contract_passed` -- each domain also adds its own extra fields (see below) |
| End-of-run print summary | Identical text/shape, all three | Considered/Rejected/Accepted/Exported/SHORTFALL?/Contract failures/Wrote X/Wrote Y |
| `shortfall_reason` construction | Same shape, worded slightly differently | Draft-v2 references a candidate-sample `CANDIDATE_LIMIT`; QB/Championship reference "the full N-row table" -- a real conceptual difference (Draft samples via Game Factory up to a limit; QB/Championship process the entire source table), not just wording |

## Logic duplicated across only two exporters

| Logic | Which two | Notes |
|---|---|---|
| `teams_active_in_season(c, season)` | Draft-v2 + QB | Championship doesn't use it -- its distractors come from a closed 5-value outcome vocabulary, not other teams |
| Deterministic candidate-order shuffle (`rng_order = gf.seeded(SEED); rng_order.shuffle(all_rows)`) | QB + Championship | Draft-v2 doesn't need this -- ordering comes for free from `game_factory.generate_candidates(seed=SEED)` itself |
| "No `data_coverage` row exists, so verify `sources.approved_for_import` + exhaustively check every row is `SOURCE_BACKED`/matching `source_id`" production-safety pattern | QB + Championship | Structurally near-identical (only the table name changes); Draft-v2's safety check is genuinely different -- it looks up a `data_coverage` domain row that exists for `NFL_DRAFT` but not for QB starts or postseason results |
| "Cross-reference a pre-existing Engine `puzzle_catalog` mode for difficulty, requiring `eligible=1`" | QB + Championship | Same query shape (`mode_id=?, source_entity_id=?, season=?, eligible=1, verification_status='SOURCE_BACKED', source_id=?`); Championship additionally cross-checks the stored answer against its own source row (a domain-specific strengthening, not shareable as-is) |
| `category != CATEGORY` and `notes not a string` contract sub-checks | QB + Championship | Draft-v2's contract loop lacks both (Draft's `CATEGORY_MAP` only ever produces one value and `notes` is always `""`, so these checks were never added -- they're a strictly *stronger* contract, worth promoting to all three) |
| `dup_players` (entity-duplicate report) | Draft-v2 (`player_key`) + QB (`qb_source_id`) | Championship has no single-entity duplicate concept -- it tracks `dup_team_seasons` instead (a pair, not a single ID), and does not enforce or report player/entity uniqueness the way the other two do |

## Logic that must remain domain-specific

- **Candidate sourcing**: Draft goes through `game_factory.generate_candidates()` + `game_factory.qa_candidate()` (Engine's own payload/QA system); QB and Championship query their source tables directly with hand-written SQL. This is not converging -- it reflects a real fact about the Engine (only Draft has a Game Factory predicate).
- **Identity/ambiguity rules**: Draft has none beyond team resolution; QB has `IDENTITY_INCONSISTENT_QB_IDS` (a hand-curated exclusion set found by data inspection) and `multi_team_pairs` (mid-season trades); Championship has neither, because `(season, team_code)` is a primary key. These are irreducibly different per domain and were each discovered by inspecting that domain's actual data, not derived from a shared rule.
- **Difficulty sourcing mechanics**: Draft reads `gf.band(diff)` off Game Factory's own returned score; QB and Championship join to a different pre-existing `puzzle_catalog` mode each (`qb_season` vs `playoff_result`) using different match keys (`qb_source_id` vs `team_code`).
- **Question phrasing, answer/distractor construction**: "Which team drafted X" vs "Which team did QB X play for" vs "How did team X finish the season" -- and correspondingly, distractors are "other teams active that season" (Draft, QB) vs "the other 4 outcome labels" (Championship, a closed vocabulary rather than a `team_aliases` query).
- **`notes` construction**: `""` always (Draft -- no explanation field exists on the underlying payload) vs a template built from `starts_observed` (QB) vs a template built from `wins/losses/ties` + outcome (Championship). Whether `notes` can be populated at all depends entirely on what the source row carries.
- **Rejection-reason taxonomy**: each domain has rejection reasons the others don't (`ENGINE_QA_*`, `ANSWER_MISMATCH`, `MISSING_SEASON` for Draft; `UNRESOLVED_QB_IDENTITY`, `MULTIPLE_PLAUSIBLE_ANSWERS_MIDSEASON_TRADE` for QB; `UNKNOWN_OUTCOME_LABEL`, `DIFFICULTY_SOURCE_MISMATCH`, `MISSING_RECORD` for Championship).

## Proposed shared module layout

```
tools/quiz_export/
  __init__.py
  engine.py        # ENGINE_DIR bootstrap + sys.path.insert + `gf = game_factory` (once, not x3)
  contract.py       # validate_contract(record, allowed_category) -> list[failure]; the QB/Championship
                     # superset (incl. category + notes-is-string checks) becomes the one shared version
  safety.py         # check_domain_coverage_safety(c, domain_id) [Draft's data_coverage-row pattern]
                     # check_table_wide_safety(c, table, required_source, extra_where="") [QB/Championship's
                     #   exhaustive-row-check pattern]  -- two distinct functions, not one forced generalization,
                     #   because the underlying Engine mechanism genuinely differs
  difficulty.py      # DIFFICULTY_MAP constant; map_band(band) -> Easy/Medium/Hard;
                     # difficulty_from_puzzle_catalog(c, mode_id, entity_id, season, source_id,
                     #   expected_answer=None) -> (score, band) | None -- shared QB/Championship pattern
  duplicates.py      # DuplicateGuard: a small seen-sets helper an adapter can consult mid-loop
                     #   (question text, plus an optional adapter-supplied entity key) --
                     #   NOT a global "unique player" rule; the framework only tracks what an adapter asks it to
  serializer.py      # finalize_options(rng, correct_text, distractor_texts) -> (options, correct_index);
                     # write_quiz_js(path, global_name, header_lines, seed, records) -- fixed 7-key order
  audit.py           # build_funnel_stats(base_fields, extra_fields) -> dict (merges shared + domain-specific);
                     # write_json(path, stats); shared report-section renderers (candidate funnel table,
                     #   rejection-reasons table, contract/determinism/production-safety section text)
  human_review.py    # render_human_review_markdown(records, summary, per_record_context_fn) -- shared
                     #   skeleton (title, summary block, per-question ID/difficulty/category/options/
                     #   correct-marker block); per_record_context_fn is adapter-supplied and renders the
                     #   domain-specific context lines (draft year/team; QB/season/team; season/team/outcome)
  core.py            # run_export(adapter, target_count, seed, id_start) -> (accepted, exported, funnel_stats)
                     #   the orchestrator: safety check -> adapter.fetch_ordered_candidates -> loop calling
                     #   adapter.evaluate() -> contract validation -> serializer -> audit. Returns the full
                     #   in-memory `exported` list so a caller can build the human-review doc from the SAME
                     #   data in the SAME run (eliminating the old "separate script re-derives everything and
                     #   verifies byte-identical against the persisted file" pattern -- with the new
                     #   architecture there is nothing to re-derive, since the export and the review are built
                     #   from one shared in-memory list in one process)
  adapters/
    __init__.py
    draft.py         # DraftAdapter
    qb_season.py      # QBSeasonAdapter
    championship.py   # ChampionshipAdapter
```

### Why two `safety.py` functions instead of one generic one

Draft's production-safety gate is answerable from a `data_coverage` domain row that happens to exist for
`NFL_DRAFT`. QB and Championship have no such row (confirmed and documented in their coverage reports) and
fall back to exhaustively checking every row in the source table. Forcing these into one function would mean
either (a) requiring every future domain to have a `data_coverage` row (not guaranteed, and not true today for
2 of 3 domains), or (b) silently treating "no data_coverage row" as equivalent to "verified," which would be a
real weakening of the safety gate. Two named functions, each doing one real thing, is safer than one function
with a fallback branch that could mask a missing row as acceptable.

## Proposed interface between shared framework and domain adapters

Each adapter is a small class or module exposing:

```python
DOMAIN_ID: str            # "draft" | "qb_season" | "championship"
SEED: str                 # unchanged from each existing script, per Step 4
ID_START: int             # unchanged from each existing script
CATEGORY: str | dict      # existing Reads Quiz category (or the predicate->category map, for Draft)
OUT_PATH: Path             # existing output path, unchanged
GLOBAL_NAME: str           # existing window.* name, unchanged

def safety_check(conn) -> dict:
    """Raise SystemExit on failure. Return a safety-info dict for the funnel stats."""

def fetch_ordered_candidates(conn, seed) -> list:
    """Return the deterministic, already-ordered list of raw domain rows to walk.
    Draft: delegates to game_factory.generate_candidates(spec, limit=CANDIDATE_LIMIT, seed=seed).
    QB/Championship: SQL fetch + gf.seeded(seed).shuffle(rows)."""

def evaluate(conn, raw_row, rng, duplicate_guard) -> Candidate | Rejection:
    """The full per-candidate pipeline: every domain-specific check in its EXACT original order,
    calling shared helpers (resolve_franchise-equivalent, difficulty_from_puzzle_catalog,
    serializer.finalize_options, duplicate_guard.check(...)) at the same points the original
    script did. Returns a normalized Candidate or a (reason: str) rejection."""

def extra_funnel_fields(accepted, exported) -> dict:
    """Domain-specific stats to merge into the shared funnel-stats base (e.g. unique_players,
    identity_inconsistent_qb_ids_excluded, outcome_distribution)."""

def human_review_context(candidate) -> list[str]:
    """Domain-specific markdown lines for the human-review doc (draft year/team; QB/season/team;
    season/team/outcome)."""
```

Normalized candidate shape (per Step 3's suggestion, adopted with minor domain-fit adjustments):

```python
Candidate = {
    "id": int, "category": str, "difficulty": str, "question": str,
    "options": list[str, 4], "correctIndex": int, "notes": str,   # <- exactly the 7 JS-contract fields
    "_audit": {                                                    # <- everything else, domain-specific,
        "entity_key": ...,       # what duplicate_guard dedupes on, if the domain wants that (None for Championship)
        "correct_answer_text": str,
        "difficulty_score": float, "difficulty_band": str,
        "source_fields": {...},  # whatever the domain's report/human-review needs (season, team_code, etc.)
    },
}
```

This is exactly the shape all three scripts already produce today (a 7-key clean record plus a `_audit` side
channel stripped before the JS write) -- Step 3 asked not to force a representation the existing architecture
doesn't already suggest, and this one requires no structural change to any domain's actual data, only moving
where the dict gets built.

### Critical constraint: RNG call order must be preserved exactly

`gf.seeded(seed)` produces a `random.Random` seeded once; every `.sample()`/`.shuffle()`/`.choice()` call
advances its internal state. A rejected candidate never reaches later RNG calls in the original scripts. If the
refactor reorders even logically-equivalent checks (e.g. moving a duplicate check before vs. after a distractor
sample), a different set of candidates will consume RNG draws, cascading into different distractor selections
for every candidate after the first divergence -- silently breaking byte-identical output without any single
check being "wrong." Each adapter's `evaluate()` must replicate its original script's exact sequence of
operations, including exactly where rejects occur relative to `rng.sample()`/`rng.shuffle()` calls. This is
called out explicitly here because it's the single biggest risk in this refactor.

## Exact files that would change

**New files:**
- `tools/quiz_export/__init__.py`, `engine.py`, `contract.py`, `safety.py`, `difficulty.py`, `duplicates.py`, `serializer.py`, `audit.py`, `human_review.py`, `core.py`
- `tools/quiz_export/adapters/__init__.py`, `draft.py`, `qb_season.py`, `championship.py`
- `tools/run_quiz_export.py` (or similar) -- thin CLI driver: `python3 tools/run_quiz_export.py draft|qb|championship|mixed`
- `data/quiz-engine-mixed-pilot.js` (new, Step 5)
- `tools/backups/mixed_pilot_funnel_stats.json` (new)
- `QUIZ_ENGINE_MIXED_PILOT_REPORT.md`, `QUIZ_ENGINE_MIXED_PILOT_HUMAN_REVIEW.md`, `QUIZ_ENGINE_LIVE_INTEGRATION_READINESS.md` (new)

**Unchanged (explicitly, per instructions):**
- `tools/export_quiz_engine_pilot.py`, `export_quiz_engine_pilot_v2.py`, `export_quiz_engine_qb_pilot.py`, `export_quiz_engine_championship_award_pilot.py` -- kept as-is, not deleted, remain the historical/reference implementations
- `tools/generate_human_review*.py` (the three existing ones) -- kept as-is
- `data/quiz-engine-pilot.js`, `quiz-engine-pilot-v2.js`, `quiz-engine-qb-pilot.js`, `quiz-engine-championship-award-pilot.js` -- must remain byte-identical after the new adapters are run against the same database (verified, not assumed -- see below)
- Every live-app file (`app.js`, `index.html`, `sw.js`, `data/quiz.js`, CSS, Firebase, routes)
- The Engine database

## How byte-identical reproduction will be verified

1. Build the framework and all three adapters as described above.
2. Run each new adapter through `core.run_export(...)` writing to a **temporary path**, not the real output
   path, on the first pass.
3. Byte-diff the temporary output against the *existing, already-committed* `data/quiz-engine-pilot-v2.js`,
   `quiz-engine-qb-pilot.js`, and `quiz-engine-championship-award-pilot.js` (`diff -q` or a checksum
   comparison) -- these files are the ground truth, produced by the original scripts against the same
   (unchanged since) database.
4. Only if all three diffs are empty: overwrite the real output paths (which is a no-op content-wise, since
   the bytes already match) and proceed to Step 5.
5. If any diff is non-empty: stop, print the first differing line/field, and diagnose against the "exact RNG
   order" risk above before making any further change -- per instruction, "semantically equivalent" is not
   accepted, only byte-identical.
6. Funnel-stats JSON and report markdown files are explicitly **not** part of this byte-identical requirement
   (only named in Step 4: the three `.js` files) -- the new framework's funnel-stats shape is allowed to differ
   (e.g. by uniformly applying the stronger QB/Championship contract checks to Draft's output), since Step 4
   scopes byte-identical strictly to those three files.

## Mixed-pack ID namespace (Step 5, decided now to avoid an ad-hoc choice later)

Existing ranges in use: Draft v1 100000s, Draft v2 200000s, QB 300000s, Championship 400000s. The mixed pack
gets its own non-overlapping range, subdivided per domain so any single mixed-pack question's origin is
identifiable from its ID alone: **Draft 500000-500099, QB 500100-500199, Championship 500200-500299.** Each
domain's mixed-pack slice reuses that domain's own original seed, so (pending verification once built) the
mixed pack's 100 Draft questions are expected to be the same 100 underlying facts as
`quiz-engine-pilot-v2.js`, just re-numbered into the mixed pack's own ID range -- this will be checked and
reported, not assumed.

