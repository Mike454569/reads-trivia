# Quiz Engine -- Production Rollout Plan (Draft Only)

Written before any live-app file is modified. Scope: append the 100 approved, already-verified
NFL Draft History Engine questions to the existing 482-question hand-authored Quiz pool, behind a
one-line kill switch. Not deployed as part of this task.

## Step 1 -- Pre-change protection (recorded now)

- **Branch:** `main`
- **Working-tree state:** `git status` shows `app.js`, `index.html`, `sw.js`, `data/grid.js`,
  `.gitignore`, `netlify/README.md` already modified (pre-existing local edits from before this
  session, confirmed by file mtimes predating every prior turn's work), plus a large set of
  untracked files from this session's prior pilot/framework work. `data/quiz.js` is **clean**
  (matches `HEAD`, zero local modifications). Nothing here will be discarded or overwritten --
  all pre-existing local edits are left exactly as found.
- **SHA-256 checksums recorded before any change in this task:**
  - `app.js`: `6f3b787a82f2e8398c671dfbce2712d41b4ee1edb1500fde463b59148045a679`
  - `index.html`: `d77d039ff0e3b536903a28d9daba13aa27396b478182fb845798c856e5a86690`
  - `data/quiz.js`: `105cc9f9675313d01b03e4730b3aa4864d31dea38a58204acfcfd324d9cd1526`
  - `sw.js`: `a3209899049719382fe2d09e3ab18a5f5b236732dddbc343be115f48b6495fb4`

## Rollback note (how to remove this rollout entirely)

Two levels, from instant/no-deploy to full revert:

1. **Instant kill switch (no file changes beyond one line, no rebuild needed):** in `app.js`, set
   `var ENABLE_ENGINE_QUIZ_DRAFT = false;`. The app then behaves exactly as it did before this
   rollout -- `QUIZ` stays the original 482-question hand-authored array, nothing else changes.
2. **Full revert (remove the integration entirely):**
   - `git checkout -- app.js index.html sw.js` restores all three to their state before this
     task's edits (safe only if you want to discard the pre-existing Aug 6-7 local edits too --
     see caveat below), **or**, to keep those pre-existing edits and only undo this task's
     changes: manually remove the `ENABLE_ENGINE_QUIZ_DRAFT` block and merge call from `app.js`,
     remove the one added `<script>` line from `index.html`, and revert `sw.js`'s `CACHE_VERSION`
     bump and the one added `CORE_ASSETS` entry.
   - Delete `data/quiz-engine-draft-production.js` (optional -- an orphaned, unreferenced file is
     harmless, but removing it is cleaner).
   - `data/quiz.js` is never touched by this rollout, so no action is needed there under any
     rollback scenario.
   - **Caveat:** because `app.js`/`index.html`/`sw.js` already had pre-existing local
     modifications before this task started, `git checkout --` would discard *those* too, not
     just this rollout's changes. The surgical (manual-removal) option is the correct rollback if
     those earlier edits should be preserved -- confirm with whoever owns those changes before
     using the blunt `git checkout` option.

## Exact files this rollout will modify

| File | Change |
|---|---|
| `app.js` | Add one kill-switch constant, one small validation+merge function, one call site (near the existing `var QUIZ = window.QUIZ_DATA \|\| [];` line). Replace two hardcoded `'482 ...'` description strings with the live `QUIZ.length` (a factual-accuracy fix made necessary by the pool size changing, not a redesign) -- see Step 6 findings below. |
| `index.html` | Add one `<script src="data/quiz-engine-draft-production.js"></script>` line, positioned after `data/quiz.js` and before `app.js`. No existing tag reordered. |
| `sw.js` | Add `'./data/quiz-engine-draft-production.js'` to `CORE_ASSETS`; bump `CACHE_VERSION` from `reads-v17` to `reads-v18` so existing installs pick up the change. No other behavior changed. |

## Exact files this rollout will create

- `data/quiz-engine-draft-production.js` (`window.QUIZ_DATA_ENGINE_DRAFT`, 100 questions)
- `tools/generate_quiz_engine_draft_production.py` (generator, runs the already-approved Draft
  adapter through the shared framework with the namespaced ID range)
- `QUIZ_ENGINE_PRODUCTION_ROLLOUT_REPORT.md` (after implementation + regression testing)

## Files explicitly NOT touched

`data/quiz.js`, Firebase code, CSS, routes, hosting/deploy config, `data/quiz-engine-pilot.js`,
`quiz-engine-pilot-v2.js`, `quiz-engine-qb-pilot.js`, `quiz-engine-championship-award-pilot.js`,
`quiz-engine-mixed-pilot.js`, the Engine database, and every `tools/quiz_export`/adapter file (the
production generator *calls* the Draft adapter, it does not modify it).

## Findings from inspecting app.js/index.html/sw.js (informs Steps 4-9)

- `var QUIZ = window.QUIZ_DATA || [];` at `app.js:100` is the single point where the hand-authored
  pool enters the app; it is captured once at parse time (unlike lazy-loaded modes' data, which
  gets re-pointed later via `refreshDataAliases()`). This is the correct, minimal injection point.
- `quizCategories()`/`quizDifficulties()`/`quizPool()`/`drawNoRepeat` are already fully dynamic --
  none hardcode a category list, difficulty list, or pool size. `drawNoRepeat`'s per-deck
  localStorage keying already folds newly-available IDs into a user's existing no-repeat deck on
  the next draw without needing a reset.
- Two **user-facing** strings hardcode the count "482" (`LEAGUE_MODES.nfl` quiz tile description,
  and the "NFL Trivia Almanac" `LEARN_SECTIONS` entry) -- both are static text evaluated at
  parse time, after `QUIZ` is already finalized, so both can be changed to reference
  `QUIZ.length` directly and will read correctly whether the kill switch is on or off.
- The approved Draft production content is 69 Hard / 31 Medium (0 Easy) -- appending it introduces
  `"Medium"` as a new difficulty value in the NFL Quiz pool (previously only `Hard`/`Very Hard`
  existed). `quizDifficulties()` will surface it automatically; this is a real, worth-noting UX
  change but not a bug -- flagged here rather than silently absorbed.
- `sw.js` is network-first with opportunistic runtime caching, so a file *not* in `CORE_ASSETS`
  would still get cached after its first fetch -- but adding it to `CORE_ASSETS` (matching every
  other `data/*.js` file already listed there) is needed for correctness on a first-ever offline
  install, and is the one line this rollout adds there.

