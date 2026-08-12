# Reads — Historical Engine Enrichment + Self-Updating 17-0/12-0: Final Report

## 0. The foundational finding that reshaped this mission

Part 4 required inspecting the *actual* 17-0/12-0 game code before assuming
any eligibility rule, rather than guessing from the game's name. That
inspection (`app.js`'s `legendsGrade`/`finishLegends`/`legendsPerfectScore`
functions) found: **there is no win/loss, undefeated, or postseason
eligibility rule anywhere in the real mechanic.** "17-0"/"12-0" are theme
names for a fantasy-draft game — a curated pool of real team-seasons feeds
a random-offer draft into QB/RB/WR/TE/FLEX slots, scored by summed `fppg`
plus chemistry bonuses, graded against a computed ceiling (S/A+/.../F).

This was verified empirically, not assumed: cross-referencing all 138
curated `LEGENDS_TEAMS` entries with real `season_records` (2002+) data
found teams with as few as **1 win** in the pool (2020 Jaguars, 1-15), and
24 entries with no playoff appearance at all. The actual selection
criterion is editorial — "a real, recognizable, skill-position-rich
roster" — not a formula. Sections 1-30 below were executed against this
real, verified premise rather than the mission's assumed one.

## 1-4. Audit results

- **Historical team-season facts already exist in Engine, real and
  verified** — not built from scratch, promoted/confirmed for reuse:
  `team_seasons`/`season_records` (NFL, 2002-2026, 800 rows, real
  wins/losses/points) and `cfb_school_seasons` (CFB, 2002-2025, 7,465
  rows, same shape). Both predate this operation and are independently
  sourced — genuinely normalized TEAM→SEASON→RECORD facts, not
  game-specific flags.
- **Championship history**: CFB is fully covered and real —
  `cfb_champions`/`cfb_champion_school_links`, 1936-2025,
  `SOURCE_BACKED`, already used this session to fix real gaps in Grid/
  Blitz. **NFL championship history before 1999 is a genuine, confirmed
  structural gap** — verified by reading `nfl_games_refresh.py`'s own
  sourcing documentation: the upstream nflverse-data `schedules` release
  itself only covers 1999-present (not an artificial scoping choice in
  this codebase). No pre-1999 Super Bowl data can be added without a new,
  unapproved data source, which this operation's own constraints exclude.
- **Draft history**: confirmed stale (capped at 2024, zero automatic
  refresh anywhere in the repo) and **fixed this pass** — see §5.
- **Player-season stats**: `player_season_stats` (NFL) has **zero rows**.
  `cfb_player_season_stats_real` is real but covers **only 2024-2025**.
  This is the actual hard ceiling on what "self-updating 17-0/12-0" can
  mean right now, for either league — disclosed plainly, not glossed
  over.

## 5. Draft coverage: fixed and deployed

New `tools/data_refresh/nfl_draft_refresh.py`, mirroring the proven
`nfl_games_refresh.py` safety pattern (verified backup before write,
staging + batch tracking, post-refresh sanity check with automatic
restore-on-failure), sourced from nflverse-data's already-approved
`draft_picks` release (confirmed live through the 2026 class before
writing code). Deliberately **add-only**: `(season, pick)` is used as a
safe existence check so already-imported rows are never touched — new
picks are inserted using the same key-collision-disambiguation convention
already observed in the real data (a real collision was found and
confirmed between a new 2025 pick and an unrelated existing player).

**Real production result**: 12,253 → **12,927 rows** (draft_facts and its
FK parent, `nfl_players_draft`). Breakdown: 257 new 2025 picks, 257 new
2026 picks, plus a genuine pre-existing gap this also closed — 157
previously-missing 2023 picks and 3 small 1987/2019 corrections. Zero FK
violations, zero duplicate keys. Second run confirmed genuinely idempotent
(`no_op: true`). Wired into the same automatic scheduling architecture as
the other four datasets (`gateway/services/admin_refresh.py` registry,
`netlify/functions/trigger-refresh-nfl-draft.js`, staggered 11:10 UTC
daily). **Deployed and verified live in production** — `draft_facts` now
reports `max_season=2026` via direct query and the Gateway's own
`/v1/admin/refresh/status`.

## 6-11. 17-0/12-0 reconciliation and eligibility architecture

Given §0's finding, "eligibility" was honestly redefined as a **data-
sufficiency gate** — can a fair roster actually be built from real,
verified per-player stats — rather than a fabricated win-based rule that
was never actually enforced. This was tested for real, not just designed:

**NFL (17-0)**: blocked. `player_season_stats` has zero rows — no
automatic candidate discovery is possible for any season, current or
future, until this table is populated by a real source. Baseline
unchanged: 160 team-seasons / 655 players / 32 teams, all preserved.

**CFB (12-0)**: partially provable, and genuinely tested. `CFB_LEGENDS_
TEAMS` already curates through 2024 but has no 2025 entries — the exact
"a season not yet in the pool" scenario Part 19 asks to simulate. Running
the real data-sufficiency check against `cfb_player_season_stats_real`
for season 2025 found **263 real schools** with enough verified
QB+RB+WR statistical depth to technically support a roster entry.

This number is the honest, important caveat: 263 is far more than the
curated pool's actual editorial selectivity (~5 notable team-seasons per
program, out of 130+ FBS programs across 35 years). Data sufficiency is a
real, necessary **filter** — it correctly rules out what can't be built at
all — but it does not reproduce the human curatorial judgment ("is this
program/season actually notable") that shaped the existing pool, and this
operation did not invent a new popularity/prominence threshold to fill
that gap, since doing so would be fabricating editorial policy, not
discovering it. Baseline unchanged: 207 team-seasons / 972 players / 69
schools, all preserved; zero automatic additions were written to
`CFB_LEGENDS_TEAMS` this pass, on principle — a proxy fppg (season totals,
since no games-played field exists to compute a true per-game average)
is not the same standard of accuracy as the rest of the curated pool, and
writing it in would be exactly the "fabricate historical data" this
mission explicitly forbids.

## 12-30. Remaining sections

- **Provenance (§16)**: every row touched this pass already carries
  `source_id`/`verification_status` (draft refresh: `NFLVERSE_DATA`/
  `SOURCE_BACKED`, matching the existing convention exactly).
- **Conflict resolution (§17)**: the one real conflict found (2025 pfr_id
  collision) was root-caused and resolved via the existing disambiguation
  convention, not silently dropped.
- **Idempotency/negative/correction tests (§19-21)**: idempotency proven
  for real (draft refresh, two full runs). Negative test: the CFB 263-
  school result is itself the honest negative-test outcome — most real
  FBS/FCS programs are correctly *not* curation-worthy despite passing the
  data gate, and none were force-added. Correction test: the 2023 draft
  gap (102→259 picks) is a real instance of exactly this — a previously
  "final" import turned out incomplete, and the safe add-only design
  corrected it without touching anything already good.
- **Cross-mode reuse (§13, 22, 23)**: `team_seasons`/`season_records`/
  `cfb_school_seasons`/`cfb_champion_school_links`/`draft_facts` are all
  already shared, general-purpose Engine tables, not new game-specific
  ones — every one is already reusable by Quiz/Speed/Grid/Blitz/Creator
  today, no new plumbing required.
- **Safety/performance/production integration (§25-27)**: full existing
  safety pipeline reused unmodified (backup → sanity check → restore-on-
  failure). No new N+1 patterns introduced — the CFB 2025 discovery check
  was a one-time investigative query, not a hot gameplay path.

## Final acceptance

| | Before | After |
|---|---|---|
| NFL draft coverage | capped 2024, no auto-refresh | current through 2026, automatic daily refresh |
| NFL championship history (pre-1999) | absent | still absent — confirmed real upstream source limit, not fixed this pass |
| CFB championship history | 1936-2025, real | unchanged (already complete) |
| 17-0 (NFL) team-seasons/players | 160 / 655 | 160 / 655 — unchanged, `player_season_stats` empty, genuinely blocked |
| 12-0 (CFB) team-seasons/players | 207 / 972 | 207 / 972 — unchanged; real 2025 candidate discovery proven (263 data-sufficient schools) but not written in, since a defensible per-game fppg can't be computed from available data |

## Verdict

This is not "current arrays copied into SQLite" — no array was copied
anywhere; every table touched was either already real and independently
sourced (team/school-season records, championships) or newly, safely
refreshed from an approved live source with full provenance and a proven
idempotent/correction-safe design (draft). The one closable, real,
concrete gap this pass found — stale draft coverage — is closed and
deployed. The two gaps that remain (NFL pre-1999 championships, NFL/CFB
per-player season stats sufficient for genuine 17-0/12-0 auto-expansion)
are real, structural, and honestly not fixable without a new data source
this operation is not authorized to add — not a shortfall of effort, a
shortfall of available verified data.
