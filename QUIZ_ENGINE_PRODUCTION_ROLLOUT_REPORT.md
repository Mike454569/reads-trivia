# Quiz Engine -- Production Rollout Report (Draft Only)

Local integration only. Not deployed. Scope: append the 100 approved NFL Draft History Engine
questions to the existing 482-question hand-authored Quiz pool, behind a one-line kill switch.

## Counts

- **Original Quiz count:** 482 (`data/quiz.js`, ids 1-533 with gaps)
- **Engine Draft count:** 100 (`data/quiz-engine-draft-production.js`, ids 500000-500099)
- **Merged count:** 582 (confirmed live in-browser: `QUIZ.length === 582` with the kill switch on)

## Validation results

- **ID collision result:** 0 -- checked both build-time (Python, before wiring anything in) and
  at runtime (the `buildEffectiveQuizPool()` guard in `app.js`). No Engine id (500000-500099)
  overlaps any hand-authored id (1-533).
- **Duplicate-question result:** 0 -- checked both build-time and at runtime. No Engine question
  text exactly matches any hand-authored question text.
- **Category validation:** passed. Every Engine question's category is `"NFL Draft History"`,
  already one of the 16 existing hand-authored categories -- confirmed in-browser: the Category
  dropdown still lists exactly 16 entries after the merge, no new category appeared.
- **Difficulty validation:** passed. Engine questions are `Hard`/`Medium` only (69/31 -- zero
  `Easy`). `Medium` is a **new** value in the NFL Quiz pool (the hand-authored bank uses only
  `Hard`/`Very Hard`) -- confirmed in-browser: the Difficulty dropdown now reads `All
  difficulties, Hard, Medium, Very Hard`. This is a real, intentional consequence of the merge,
  not a defect.
- **Contract failures:** 0 -- validated three times: (1) inside the shared framework's
  `contract.validate_all()` when `data/quiz-engine-draft-production.js` was generated, (2) a
  standalone Python re-check of the persisted file, (3) the runtime `buildEffectiveQuizPool()`
  guard in `app.js`, which re-validates every field, shape, and uniqueness constraint before ever
  merging the array in the live app.

## Game modes tested (in a real headless-Chrome session against a local static server)

| Mode | Result |
|---|---|
| Onboarding | Modal renders, "Skip" dismisses it cleanly |
| NFL Quiz | Category dropdown includes "NFL Draft History"; selecting it and starting a round served a genuine Engine question ("Which NFL team drafted Jamaal Anderson?") with correct category/difficulty labels; answering showed correct red/green highlighting and "Incorrect."/"Next Question" worked; advanced to a new question correctly |
| NFL Speed | Session starts, timer/score/streak UI renders, draws from the merged pool without error |
| NFL IQ Test | Still exactly "Question 1 of 25" -- `IQ_TEST_SIZE` unaffected by the larger pool, as expected |
| Study/Learn mode (NFL Trivia Almanac) | `learnTriviaRows(QUIZ)` returns all 582 rows (482 hand-authored + 100 Engine); description text correctly reads "582 NFL facts..." (dynamically computed, was previously hardcoded "482") |
| Kill switch OFF | Reloaded with `ENABLE_ENGINE_QUIZ_DRAFT = false`: `QUIZ.length === 482`, 0 Engine ids present, `window.QUIZ_DATA.length` still 482 -- **exactly** original behavior |
| Kill switch back ON (restored) | Reloaded: `QUIZ.length === 582` again, confirming the flag is a clean, reversible toggle in both directions |

No console errors were introduced by these changes. Three unrelated 404s (`assets/audio/click.mp3`)
appeared in every run, including before any of this task's edits were considered -- confirmed
the file genuinely doesn't exist in `assets/audio/`; this is a pre-existing, unrelated issue, not
caused by this rollout, and was not touched.

## No-repeat / persistence behavior

Not separately reset -- `drawNoRepeat()`'s per-deck `localStorage` keying (keyed by
category+difficulty) already folds newly-available ids into a user's existing deck on its next
refill without needing a reset, by design (confirmed by reading the function, not just assumed).

## Service-worker / cache changes

- `CACHE_VERSION` bumped `reads-v17` -> `reads-v18`, forcing existing installs to pick up the
  change and clear their old cache on next activate.
- `'./data/quiz-engine-draft-production.js'` added to `CORE_ASSETS`, immediately after
  `'./data/quiz.js'`, matching every other `data/*.js` file's existing precache treatment.
- No other service-worker behavior changed -- still network-first, still opportunistically caches
  any successful fetch regardless of `CORE_ASSETS` membership.

## Rollback instructions

1. **Instant (no rebuild, no file other than one line):** in `app.js`, set
   `var ENABLE_ENGINE_QUIZ_DRAFT = false;` (currently at line 105). Confirmed above to return the
   app to exactly the original 482-question behavior.
2. **Full removal:** revert the `ENABLE_ENGINE_QUIZ_DRAFT`/`buildEffectiveQuizPool` block and the
   two `QUIZ.length` description-string edits in `app.js`; remove the one added `<script>` line in
   `index.html`; revert `sw.js`'s `CACHE_VERSION` bump and the one added `CORE_ASSETS` entry;
   optionally delete `data/quiz-engine-draft-production.js` (harmless if left in place, unreferenced).
   `data/quiz.js` needs no action under any rollback scenario -- it was never touched.

## Kill-switch location

`app.js`, line 105: `var ENABLE_ENGINE_QUIZ_DRAFT = true;` -- immediately above the
`buildEffectiveQuizPool()` function it controls, in the `/* data + state */` section near the top
of the file.

## Exact files modified

| File | Change |
|---|---|
| `app.js` | Added kill-switch constant + `buildEffectiveQuizPool()` validation/merge function + call site (replacing the single-line `var QUIZ = window.QUIZ_DATA \|\| [];`); changed two hardcoded `'482 ...'` description strings to `QUIZ.length + ' ...'` |
| `index.html` | Added one `<script src="data/quiz-engine-draft-production.js"></script>` line after `data/quiz.js`, before `data/cfb.js` |
| `sw.js` | Bumped `CACHE_VERSION` to `reads-v18`; added the new file to `CORE_ASSETS` |

`data/quiz.js` was **not modified** -- confirmed byte-identical before and after this rollout
(SHA-256 `105cc9f9675313d01b03e4730b3aa4864d31dea38a58204acfcfd324d9cd1526`, matches the checksum
recorded in `QUIZ_ENGINE_PRODUCTION_ROLLOUT_PLAN.md` before any change was made).

## Exact files created

- `data/quiz-engine-draft-production.js` (`window.QUIZ_DATA_ENGINE_DRAFT`, 100 questions, ids
  500000-500099 -- content verified identical to the Draft slice of `quiz-engine-mixed-pilot.js`)
- `tools/generate_quiz_engine_draft_production.py` (generator; runs the already-approved Draft
  adapter through the shared framework, no hand-written questions)
- `QUIZ_ENGINE_PRODUCTION_ROLLOUT_PLAN.md`
- `QUIZ_ENGINE_PRODUCTION_ROLLOUT_REPORT.md` (this file)

## Not touched, per explicit scope restriction

QB/Season content, Championship/Postseason content, the full 300-question mixed pack, Firebase
code, profiles, leaderboards, head-to-head, Game Director, any Engine API deployment, hosting,
CSS/UI, routes, SEO, any pilot exporter file, and the Engine database.

## Compatibility issues discovered and resolved

1. Two hardcoded `"482 ..."` description strings (Quiz mode tile, NFL Trivia Almanac entry) would
   have become factually wrong once the pool grew -- fixed by making both read `QUIZ.length`
   live, which is correct under the kill switch in either state.

## Compatibility issues discovered and explicitly not touched (out of scope)

1. `assets/audio/click.mp3` 404s -- pre-existing, unrelated to this rollout, confirmed the file is
   simply absent from `assets/audio/`.

## Not deployed

This integration exists only in the local working tree. No `git push`, no Netlify deploy, no
production traffic was affected.

