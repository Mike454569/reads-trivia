# Player From Clues -- Frontend Integration Plan (Director v0.5, Step 1)

Analysis and plan only, written before any implementation, per Step 1's
explicit instruction.

## Existing UI patterns identified for reuse

**NFL Silhouette mode (`app.js`, search `/* ============================== silhouette`)
is the closest existing analog and is reused almost directly.** It already
implements: progressive clue reveal (`revealSilhouetteClue`,
`s.revealedCount`), a typeahead/autocomplete name-guess input
(`TYPEAHEAD_CONFIGS['silhouette-input']`), correct/wrong feedback, a
give-up/reveal-answer flow, round progression through a queue, and a
completion/summary screen. Player From Clues reuses this exact shape:
clue-array + reveal-count + guess input + reveal state + queue index +
summary screen.

**CSS -- zero new classes needed.** Every visual element needed already
exists and is generic enough to reuse verbatim:

| Element | Existing class(es) |
|---|---|
| Card container | `.panel`, `.panel-title` |
| Clue list/individual clue | `.silhouette-clues`, `.silhouette-clue` |
| Answer reveal | `.silhouette-reveal` |
| Answer input + autocomplete | `.grid-answer-box`, `.typeahead-wrap`, `.typeahead-list`, `.typeahead-row` |
| Buttons | `.btn-primary`, `.btn-secondary`, `.btn-row`, `.btn-tiny` |
| Wrong-guess feedback | `.blitz-feedback.wrong` |
| Round-size / setup chips | `.chip-row`, `.chip-toggle` |
| Completion screen | `.summary-score`, `.summary-note` |
| Loading state | `.loading-panel`, `.loading-spinner` |

**Shared JS infrastructure reused, not reimplemented:** `esc()`, `icon()`,
`normName()`, the generic `TYPEAHEAD_CONFIGS`/`renderTypeahead`/
`typeaheadMatches`/`typeaheadPickActive` system (already powers Grid, CFB
Grid, and Silhouette's own name search), the central `renderAll()` screen
dispatcher, and the single delegated `click`/`input`/`keydown` event
listeners at the bottom of `app.js` (extended additively with new
`data-clues-*` attributes, following the exact pattern already used for
every other mode's `data-silhouette-*`, `data-grid-*`, etc.).

**Entry point -- `HIDDEN_ROUTES`, not the home screen.** `app.js` already
has exactly the mechanism Step 8 asks for: a `HIDDEN_ROUTES` map
(`{'#stats': 'stats', '#reports': 'reports'}`) checked once at boot,
completely separate from the nav bar / home mode grid / `LEAGUE_MODES`.
Adding `'#clues': 'playerClues'` to it (conditionally, only when the
feature flag is on) is the smallest possible entry point: it touches zero
existing UI, adds zero visible elements when not navigated to directly, and
matches an idiom the codebase already established for exactly this purpose
(local/hidden dev routes).

## Exact files to create

- `tools/export_player_from_clues_frontend.py` -- deterministic conversion
  script, `generated_games/director-v04-player-from-clues.json` ->
  `data/player-from-clues-v01.js` (Step 3).
- `data/player-from-clues-v01.js` -- the generated output of the script
  above (`window.PLAYER_FROM_CLUES_V01 = {...}`). Generated, not hand-written.
- `playtest-player-from-clues.js` -- local-only playtest logger (Step 12),
  modeled directly on the existing `playtest-engine-draft.js`.

## Exact files to modify

- `index.html` -- add two `<script>` tags (`data/player-from-clues-v01.js`,
  `playtest-player-from-clues.js`), same eager-load pattern already used for
  `data/quiz-engine-draft-production.js` and `playtest-engine-draft.js`.
  No other change to `index.html` -- the home screen's static pre-render
  markup, nav bar, and mode grid are untouched.
- `app.js` -- additive only:
  1. One feature-flag constant, `ENABLE_PLAYER_FROM_CLUES_V01`.
  2. Package-integrity validation function (Step 11), run once at load.
  3. New render functions (`renderPlayerCluesSetup/Round/Summary/Screen`),
     modeled on the Silhouette equivalents, consuming
     `window.PLAYER_FROM_CLUES_V01` only -- no new football-fact logic.
  4. New state-mutation functions (`startPlayerCluesRound`,
     `revealPlayerCluesClue`, `submitPlayerCluesGuess`,
     `advancePlayerClues`, etc.), modeled on the Silhouette equivalents.
  5. One new key in `TYPEAHEAD_CONFIGS` (`'clues-input'`), pool = the
     distinct answer names already present in the loaded package (Step 5,
     option 1 -- no separate name list, no invented distractors).
  6. One new branch in `renderAll()`'s screen dispatcher
     (`else if (state.screen === 'playerClues') ...`).
  7. New `data-clues-*` attributes added to the existing giant delegated
     event-listener selector strings (click/input/keydown), plus their
     handler branches -- the same additive pattern every existing mode
     already uses.
  8. `'#clues': 'playerClues'` added to `HIDDEN_ROUTES`, guarded by the
     feature flag.
  9. `EXTRA_MODE_LABELS.playerClues` (or equivalent) so any shared helper
     that labels a mode (e.g. a restart-toolbar) has a real string, matching
     how `study`/`xso` (also outside `LEAGUE_MODES`) already do this.

**Not modified:** `styles.css` (zero new rules needed -- see CSS table
above), `firebase-sync.js`, `sw.js` (see caching note below), `data/quiz.js`,
any existing mode's render/state functions, `LEAGUE_MODES`, the home screen
markup, the nav bar, `netlify.toml`, any Engine `.py` file, any already-
generated package file.

`sw.js`'s `CORE_ASSETS` precache list is a borderline case: the two new
static files (`data/player-from-clues-v01.js`,
`playtest-player-from-clues.js`) would 404-safe-fail (fetch-and-cache-on-use,
same as any uncached asset) without a `sw.js` change, since this app's
service worker does not precache-or-fail -- confirmed by reading `sw.js`
before deciding. Left out of `CORE_ASSETS` deliberately for this milestone:
adding entries there is a real (if small) production-facing change to a
file explicitly called out as off-limits in the CRITICAL RESTRICTIONS list,
and offline availability of a local-dev-only hidden route is not a
requirement of this milestone.

## Visual consistency

No new visual language. Every element reuses an existing Reads component
verbatim (see CSS table). The screen is entered only via a hidden route
behind a feature flag, is built from `.panel`/`.btn-primary`/`.chip-row`/
etc. exactly like every other mode, and uses the same `icon()`/`esc()`
helpers -- it will read as "a Reads game," not an embedded widget.

## Feature flag

`ENABLE_PLAYER_FROM_CLUES_V01 = true` (top of `app.js`, next to other
top-level constants). Gates three things: whether `HIDDEN_ROUTES['#clues']`
exists at all, whether `renderAll()`'s `playerClues` branch renders the
real game vs. falls back silently to Home, and whether the package
integrity check even runs. Setting it to `false` makes the entry point,
the route, and the render branch all simultaneously inert -- confirmed by
construction (every one of the three checks it, not just one gate that the
others assume held).

## Rollback

One-line: `ENABLE_PLAYER_FROM_CLUES_V01 = false`. No file deletion required
(Step 14). With the flag false: `#clues` resolves to nothing (falls out of
`HIDDEN_ROUTES`, default boot behavior applies exactly as it did before this
milestone), the `playerClues` screen branch never renders real content, and
the two new `<script>` tags still load (inert data/logger, no DOM/state
effect) -- harmless dead weight, removable later but not required to be
removed for rollback to be complete.

## Answer UX decision (Step 5)

**Option 1 (autocomplete/search from names already in the approved
package)**, per the milestone's stated preference order. The pool is the 25
distinct `display_name` values already present in the loaded
`PLAYER_FROM_CLUES_V01` puzzles -- nothing external, nothing invented,
reusing the exact same `TYPEAHEAD_CONFIGS`/`normName()` matching machinery
Grid and Silhouette already use. No fuzzy matching beyond `normName()`'s
existing case/punctuation/whitespace normalization (already proven safe
across two existing modes); an incorrect name never matches a different
correct `player_id`, since matching is always against the single target
`display_name` string for that specific puzzle, not a fuzzy identity
resolution.
