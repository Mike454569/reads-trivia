# Reads — Unified Engine v4.0 + Live NFL/CFB Data: Real Status Report

This reports the real, evidence-based current state against the Unified
Engine v4.0 mission's own explicit standard: *"Success requires AUTOMATIC
NFL DATA + AUTOMATIC CFB DATA + EVERY GAME TRACKED + POSTGAME STATS +
CANONICAL IDENTITIES + ENGINE v4.0 + DERIVED RELATIONSHIPS + APP-WIDE
ENGINE INTEGRATION + LEGACY MODE MIGRATION + 17-0/12-0 REGRESSION
PROTECTION AND EXPANSION + GAME-WIDE QUALITY GATES + REAL PRODUCTION
AUTOMATION + REAL PRODUCTION GAMEPLAY VERIFICATION."* That is a genuine,
multi-week platform-engineering scope. This report says plainly which
pieces are real and proven, which are real but partial, and which have
not been started — not a premature "done."

## 1. What's real and proven (Sections 3-5, 10-14, 18-19, 52-55)

A real, already-substantial NFL/CFB roster + games ingestion pipeline
existed in the working tree at the start of this session (built across
several prior commits: `22726a4`, `b3b4d54`, `ad6ce5f`, `bf5ca97`,
`93bd050`, `df66bce`, `535eb62`, `20bb411`) plus in-progress, uncommitted
work extending it to game-level data. This session's job was auditing,
finishing, deploying, and proving that work against real production —
not building it from scratch.

**Audited first (Section 2), not duplicated**: confirmed no prior
importer wrote to the `games` table at all (grepped the whole tree for
`INTO games`); confirmed `identity_bridge_v16.py` writes to a different,
disconnected table than the one Lineup/Coach Connections actually query
and crashes on real data (a prior commit had already found and disclosed
this, not re-discovered blind); confirmed `cfb_games_canonical`'s
existing importer hardcodes a source_id that would misattribute
provenance for live automated data.

**Committed, deployed, and proven end-to-end against real production**:
- `tools/data_refresh/nfl_games_refresh.py` — real source (nflverse-data's
  GitHub Release), verified live: **7,548 games downloaded, imported,
  0 rejected**, real 11m24s run against the actual Fly deployment.
- `tools/data_refresh/cfb_games_refresh.py` — real source (cfbfastR-data),
  a real column-drift bug found and fixed before ever running. Verified
  live: correctly reported `SOURCE_NOT_YET_PUBLISHED` for the 2026 season
  (which genuinely hasn't been published upstream yet) — the fail-closed
  path worked correctly on real data, not just in a unit test.
- Both reuse the same backup/verify/sanity-check/restore-on-failure safety
  layer (`tools/data_refresh/safety.py`) as the already-deployed roster
  refreshes (`nfl_refresh.py`, `cfb_refresh.py`).
- Real production scheduler: four Netlify Scheduled Functions, one per
  dataset, calling the admin-gated `/v1/admin/refresh/{dataset_key}`
  Gateway route.
- Admin-safe status surface: `GET /v1/admin/refresh/status` (Section 50).

**A real, live production incident was found and fixed during this
verification** — not hidden: running the NFL games refresh immediately
followed by a CFB games refresh filled the entire 5GB Fly volume solid
(`backup_manager.create()`, vendored Engine code, has no retention policy
— every refresh left its ~1.6GB backup behind forever). The Gateway then
failed on every request, including `/v1/health`, for roughly 19 minutes
real downtime, diagnosed live via direct SSH/log inspection while it was
happening. Fixed: `safety.py` now prunes all old backups before creating
a new one; the Fly volume was extended 5GB→10GB for real headroom; the
Netlify scheduler gap widened from 10 to 30 minutes based on the real
measured 11m24s run time (the original "130-200s" estimate was almost 4x
too low against the real production volume). Re-verified live: a second
real CFB games refresh completed cleanly, health stayed 200 throughout.

**A second real, unrelated bug also found and fixed**: the Netlify
environment variable holding the Gateway URL was configured as
`Reads_Engine_Gateway_Base_URL` (mixed case) while the code reads
`process.env.READS_ENGINE_GATEWAY_BASE_URL` (all caps) — different names
in a case-sensitive environment. Every scheduled trigger had been
silently no-op-ing since it was first deployed. Fixed and redeployed.

## 2. What's real but not yet exercised

- `nfl_refresh.py`/`cfb_refresh.py` (rosters): deployed, wired, but no
  real end-to-end production run was triggered this session (only the
  new *games* refreshes were). The identical dependency-file gap that
  blocked games refresh (missing `import_data.py`, `backup_manager.py`,
  `fetch_nflverse_current.py` from the production volume) was found and
  fixed as part of this session's work, so rosters should now work too —
  but "should" is not "proven." Recommend a real triggered run before
  fully trusting the daily schedule.
- CFB games refresh has not yet returned a real `SUCCESS` (only the
  correct, safe `SOURCE_NOT_YET_PUBLISHED` for the not-yet-live 2026
  season) — worth a real re-check once cfbfastR-data actually publishes
  this season's schedule, or a manual run with an explicit prior season.

## 3. What has NOT been done (the honest, larger gap)

- **Nothing yet consumes the `games`/`cfb_games_canonical` tables for
  gameplay.** Grepped the whole `gateway/services/` and `tools/
  quiz_export/` tree: zero references to `FROM games`. Sections 9, 37,
  41-46 (derived postgame facts, immediate postgame content, mechanic-
  specific quality gates for game-level content) are **not built**. The
  ingestion half of the mission is real; the "new data becomes generatable
  content" half has not been started.
- **App-wide Engine migration (Sections 22-36) has not happened.** Of the
  ~19 total modes on the live site, only five are Engine-native (Draft,
  Championship, Lineup, CFB Heisman, Coach Connections). Quiz, Speed,
  Grid, NFL IQ Test, Study/Learn, Daily, X's & O's, Legends (17-0), CFB
  Legends (12-0), Blitz, Silhouette, and the rest remain on static local
  JS data files, unconnected to Engine v4.0 or the new games data.
- **17-0/12-0 (Sections 33-35) were not touched.** No regression (nothing
  changed), but also no migration, no measurement, no expansion — the
  explicit before/after candidate-count comparison Section 59 asks for
  was not performed because no migration was attempted.
- **Play-by-play (Section 8) was not attempted** — no source was audited
  or integrated this round.
- **Weekly content pools (Section 40), relative-time semantics (Section
  39), and Creator understanding of recent games (Section 38) were not
  built** — all depend on the postgame-facts layer above existing first.

## 4. Honest answers to Section 63's explicit questions

1. Are all applicable modes Engine-powered? **No** — 5 of ~19.
2. Which still depend on legacy data, and why? Quiz/Speed/Grid/IQ/Study/
   Daily/17-0/12-0/X's&O's/Blitz/Silhouette and others — no migration
   work has reached them yet; this was always a large, separate
   follow-on effort.
3. Can new NFL game data automatically reach Engine v4.0? **Yes, proven
   live** (7,548 real games).
4. Can new CFB game data automatically reach Engine v4.0? **Yes at the
   pipeline level, proven safe-and-correct live**; a real full `SUCCESS`
   with actual new rows is still pending a season that's actually
   published.
5. Can that new data automatically become generated-game content? **No**
   — the consuming layer doesn't exist yet.
6. Can existing modes benefit from the same new data? **No**, same gap.
7-9. Did 17-0/12-0 lose or gain anything? **Neither** — untouched.
10. Will future roster/game updates automatically expand applicable
    modes? **Yes, for the 5 Engine-native modes** (their candidate pools
    already query live Engine tables); **no** for anything depending on
    the not-yet-built postgame-facts layer.
11-12. Are the NFL/CFB updaters actually scheduled and running in
    production? **Yes** — real Netlify Scheduled Functions, real
    admin-gated Gateway routes, real proven runs, a real incident found
    and fixed along the way, not a diagram.
13. Does failure preserve last-known-good data? **Yes, proven for real**
    — the interrupted run (from the disk-space incident) never touched
    the live database; it died during its own pre-write backup step.
14. Is Engine v4.0 genuinely the shared football brain of Reads? **Only
    partially.** It is the real, live, canary-verified brain for five
    modes. For the other ~14, it is not yet connected at all.

## 5. Recommendation

This mission's full scope (63 sections) is a genuine multi-week platform
initiative, not a single-session task, and the mission's own "Hard
Completion Standard" explicitly warns against declaring success because
"scripts exist... one question loads." In that spirit: this session's
real, verified contribution is a working, production-proven, incident-
hardened NFL/CFB games ingestion pipeline added to an already-real
roster pipeline — genuinely new capability, not a report. The next
honest increment (not started this round, and substantial enough to
deserve its own dedicated pass) is the postgame-facts + Game Factory
adapter layer that would let any of this new data actually become a
playable question — everything in Sections 9/37/41-46 depends on it.

## 6. Final state

- Production: `https://reads.football` live, `https://reads-football-
  gateway.fly.dev` healthy, disk at 35% (was 100%, incident resolved).
- 287/287 tests passing.
- Git: pushed through `ffe69e2`.
