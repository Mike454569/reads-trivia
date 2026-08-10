# Quiz Engine -- Live Integration Readiness Analysis

Analysis only. No live-app files touched. This document exists to answer the questions the
framework refactor was explicitly asked to leave open, not to implement any of them.

## Is the shared exporter stable enough to replace manual one-off exporters?

**Yes, for the mechanic family proven so far.** Three independent domains have gone through
`tools/quiz_export` and reproduced their pre-refactor output byte-for-byte (SHA-256-verified),
and a fresh 300-question combined build via the same adapters showed zero drift against the
three standalone pilots. That's real evidence, not just architecture on paper.

What hasn't been tested: a domain needing a materially different candidate shape (e.g. an
`ordering`/`matching` mechanic rather than "guess one of 4 options"), concurrent/parallel
invocation, or recovering mid-run if the Engine database changes underneath a long export. The
adapter interface (`safety_check`, `fetch_ordered_candidates`, `evaluate`, `extra_funnel_fields`,
`header_lines`, `human_review_context`) doesn't assume a team/season axis or a 4-option answer
shape at the *interface* level, but every adapter written against it so far does happen to have
one. Recommend treating "stable for guess-style domains" as proven and "stable for anything" as
not yet claimed.

## Can a deterministic mixed Engine pack now be safely generated on demand?

**Yes, as a manual, explicit action.** `tools/build_mixed_pilot.py` reruns cleanly against an
unchanged database with byte-identical output (verified by rerun). "On demand" today means a
maintainer runs one script and gets a fresh, fully-audited pack plus its funnel stats and
reports. It is **not** wired into any CI/build/deploy pipeline -- nothing regenerates it
automatically on a schedule or on Engine data changes. That's a reasonable Phase 2 item, not a
blocker to a first rollout, since the underlying Engine facts (draft picks, QB starts, playoff
results) don't change retroactively very often.

## What would be required to combine Engine-generated questions with data/quiz.js?

- **Category compatibility: already solved.** All three domains were deliberately restricted to
  *existing* `quiz.js` categories (`NFL Draft History`, `Passing Records & QB Trivia`, `Playoffs &
  Postseason Moments`) -- no new category to introduce, no taxonomy work needed.
- **Difficulty tone mismatch: a real product decision, not a technical blocker.** The hand-authored
  `quiz.js` NFL bank currently uses only `"Hard"` and `"Very Hard"` (confirmed by direct inspection
  of the file) -- it was deliberately curated hard. Engine content spans `Easy`/`Medium`/`Hard`
  (`EXPERT` collapses to `Hard`). Blending Engine's easier questions into the existing pool would
  measurably soften its difficulty distribution. This needs a decision (blend as-is, filter Engine
  output to Hard-only for this app, or keep pools visually/mechanically separate) -- not
  something to decide silently by merging.
- **A merge mechanism.** Two real options:
  - **(A) Build-time merge**: a script concatenates Engine JS array(s) into a new version of
    `quiz.js` (or a new file `app.js` loads alongside it). Rollback = revert to the prior
    `quiz.js`/data file.
  - **(B) Runtime merge**: `app.js`'s data-loading layer (`MODE_DATA_FILES` /
    `refreshDataAliases()`, per the existing README's documented architecture) loads the Engine
    file(s) as additional sources and concatenates them into the in-memory pool alongside
    `QUIZ_DATA`, without ever rewriting `quiz.js` itself.
  
  **(B) is recommended** -- it keeps hand-authored and Engine-sourced content in physically
  separate files, which is also what makes the rollback story clean (see below). This requires an
  `app.js` change, which is out of scope for this refactor and not made here.
- **An editorial pass, even though the automated QA is strict.** `quiz.js`'s own header comment
  documents a past human audit that removed 47 duplicates, 2 no-defensible-answer questions, and
  rewrote 6 that gave away their own answer. Engine content has passed rigorous *automated*
  checks (production-safety, identity resolution, contract validation, determinism) but has not
  had the same kind of human read-through the hand-authored bank got. Recommend at least a spot
  check against the human-review documents already produced (`QUIZ_ENGINE_*_HUMAN_REVIEW.md`)
  before any batch goes live, even though nothing in the pipeline suggests problems -- the QB
  pilot's "Nick Foles has two different Engine identities" finding (see
  `QUIZ_ENGINE_MIXED_PILOT_REPORT.md`) is exactly the kind of thing that's obvious on a quick human
  read and easy to miss in automated stats.

## How should IDs be namespaced to prevent collisions with the existing 482 questions?

`quiz.js` uses ids 1-533 (with gaps from past dedup, 482 actual entries) -- entirely below
100,000. Every Engine pilot already uses a reserved 6-digit-plus range: Draft v1 100000s, Draft v2
200000s, QB 300000s, Championship 400000s, Mixed pack 500000s (subdivided 500000-500099 /
500100-500199 / 500200-500299 by domain). **There is already zero numeric collision risk with the
482 hand-authored questions**, and none between Engine batches, because every range was chosen
before generation, not after. Recommendation: write this convention down as a short, standing
policy (e.g. "hand-authored content stays under 100,000; each Engine domain gets its own reserved
100,000 block, allocated before that domain's first export") so it isn't reinvented ad hoc for a
future 4th domain.

## Should the first production rollout replace questions or append?

**Append. Do not replace.** The hand-authored bank has an editorial history (the dedup/rewrite
pass mentioned above) and an established difficulty identity (consistently hard) that Engine
content doesn't have and shouldn't silently override. Appending is:

- **Lower risk** -- existing questions are untouched; a bad Engine batch can't degrade a question
  that was already live and working.
- **Reversible** -- removing an appended block is a one-line change (stop concatenating the extra
  file); replacing questions in place would require reconstructing exactly what was removed.
- **Measurable** -- the app already has a user-report mechanism (per the existing README); an
  appended batch's questions can be watched for reports distinctly from the legacy bank's, making
  a bad batch obvious without guessing.

Whether Engine questions should eventually be visually/mechanically distinguished from
hand-authored ones (a badge, a separate mode, or fully blended) is a product decision for a later
phase, not resolved here.

## What rollback mechanism should be used?

Because nothing is wired in yet, "rollback" means "how do we cleanly undo a live rollout that
turns out to have a problem":

1. **Keep Engine content in its own file(s)**, never hand-merged into `quiz.js` -- this is already
   true today (`quiz-engine-*.js` are separate files) and should stay true after integration (per
   the runtime-merge recommendation above). Rollback = stop loading/concatenating that file, a
   single small `app.js` change to revert.
2. **Version each batch by filename** (already the convention: `-pilot`, `-pilot-v2`,
   `-qb-pilot`, `-championship-award-pilot`, `-mixed-pilot`) so a bad batch can be swapped for the
   last-known-good one by changing which file `app.js` loads, without needing to hand-edit
   content.
3. **A fast-disable switch** independent of a code deploy -- e.g. a small config flag `app.js`
   checks before concatenating Engine content, toggleable without a full redeploy if the hosting
   setup allows same-day static-file updates (Netlify does, per the existing deployment setup).
4. **Keep the audit trail** -- the funnel-stats JSON, audit report, and human-review doc for
   whichever batch is live should stay retrievable, so "what's live and why" is always answerable
   without re-deriving it.

None of this is implemented in this task -- it's the mechanism to design when integration is
actually approved.

## What caching/service-worker implications exist?

`sw.js` (per prior research) already uses a **network-first** strategy specifically because
`data/*.js` files change often -- this is a deliberate, already-documented design choice, not
something that needs to change in kind for Engine content. What *would* be needed: `sw.js`'s
precached-asset list would need the new Engine data filename(s) added, exactly like every other
`data/*.js` file. That's a `sw.js` change -- explicitly out of scope for this task and not made
here. No new caching *risk* is introduced by adding one more file to a category the service worker
already treats as frequently-changing; the risk would only appear if someone put Engine content on
a *different* caching strategy than the rest of `data/`, which nothing here recommends.

## How can we deploy Engine content without changing current Quiz UI behavior?

This is the one area where the answer is close to "for free." Every exported Engine question
already conforms **exactly** to the object shape `app.js` already knows how to render
(`id, category, difficulty, question, options[4], correctIndex, notes`), using only categories
that already exist in the UI's category list. `app.js`'s *rendering* code needs zero changes to
display an Engine-sourced question correctly -- it cannot tell the difference between a
hand-authored object and an Engine-generated one once both are sitting in the same in-memory
array. The only change needed is at the **data-loading** layer: concatenating the Engine array(s)
into the pool before `quizCategories()`/`quizDifficulties()` and the rest of the quiz engine derive
their lists from it. That's a small, isolated, well-understood change -- but it is still a change
to `app.js`, which this task's scope keeps untouched. Recorded here as the next concrete step, not
taken now.

## Recommended lowest-risk production rollout

**Phase 1 (near-term):**
1. Pick one batch to start with -- recommend the Draft slice alone (100 questions, the
   most-audited domain, three full passes of scrutiny across Pilot #1's original build and its
   post-safe-fix v2) rather than the full 300-question mixed pack, to keep the first live change
   small and easy to attribute if something's wrong.
2. Add a small `app.js` data-loading change that appends this one file's array to `QUIZ_DATA`
   at runtime, behind a simple, instantly-toggleable flag.
3. Do a manual spot check against `QUIZ_ENGINE_PILOT_V2_HUMAN_REVIEW.md` (or the mixed pack's
   Draft slice in `QUIZ_ENGINE_MIXED_PILOT_HUMAN_REVIEW.md`) before flipping the flag on.
4. Add the new filename to `sw.js`'s precache list under the same network-first policy as every
   other `data/*.js` file.
5. Watch the app's existing user-report mechanism for anything flagged from the new ID range
   specifically.

**Phase 2 (once Phase 1 has run cleanly for an observation window):**
6. Add the QB and Championship slices the same way.
7. Consider whether Engine content should be visually distinguished in the UI (a badge, a
   separate mode) -- a product decision, not a technical one.
8. Consider wiring `tools/build_mixed_pilot.py` (or a per-domain adapter run) into a scheduled
   or CI-triggered job so packs refresh automatically as Engine data updates, rather than being a
   manual step.

**Deferred / not recommended yet:** replacing any existing hand-authored question, blending
difficulty tone without a decision, or shipping the full 300-question pack in one step before any
Engine content has been live and observed at smaller scale.

