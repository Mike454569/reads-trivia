# Player From Clues -- Feasibility Report (Director v0.4, Part A)

Analysis only. Every number below was produced by direct SQL queries against
`reads_football_v4.0.sqlite` in this session -- nothing here is inferred
from table/column names alone. See `DIRECTOR_V04_IDENTITY_POLICY.md` for how
the "safe universe" referenced throughout was derived.

## Method

Explored all 225 tables in the Engine database; inspected schema, row
counts, `verification_status`/`source_id` distributions, and
`data_coverage.production_safe` flags for every table that could plausibly
hold player-level facts. Cross-checked the `relationships` graph table
(1,412,611 rows) for predicates not otherwise exposed through a dedicated
table. Where a table existed but its `data_coverage` domain was
`production_safe = 0` or the table itself had 0 rows despite a populated
schema, that was treated as **UNAVAILABLE**, not merely low-confidence --
several tables in this database exist as schema scaffolding for data that
was never actually imported (e.g. `player_season_stats`: 0 rows;
`NFL_ROSTERS_CURRENT` domain: `ADAPTER_READY_NOT_IMPORTED`).

## Base candidate universe

Established first, before any clue-family analysis (see identity policy for
the full justification): **4,506 players** -- every `draft_facts` row whose
`player_key` (a) is `SOURCE_BACKED`/`NFLVERSE_DATA`, the same proven source
as three approved pilots, and (b) uses the `PFR:...` key format and has a
matching row in `canonical_players.player_id`. All narrowing/candidate-count
math in this milestone is computed against this fixed 4,506-player universe.

## Clue family classification

| Clue family | Classification | Coverage in universe | Source | Notes |
|---|---|---|---|---|
| Draft year | **SAFE** | 4,506 / 4,506 (100%) | `draft_facts.draft_season` | Same field already proven across 3 approved pilots + Director v0.1. |
| Draft round | **SAFE** | 4,506 / 4,506 (100%) | `draft_facts.draft_round` | 0 nulls. |
| Draft pick (overall) | **SAFE** | 4,506 / 4,506 (100%) | `draft_facts.draft_pick_overall` | 0 nulls. Confirmed `(draft_season, draft_pick_overall)` is unique across all 12,253 `draft_facts` rows -- this pair alone is a natural key, so it is deliberately used as a late/narrow clue, never a first clue (see mechanic spec, clue ordering). |
| Drafting franchise | **SAFE** | ~87% resolve (same rate as the approved Draft capability) | `draft_facts.draft_team` -> `resolve_franchise()` | Reuses the exact, already-proven `tools/quiz_export/adapters/draft.py` franchise-resolution logic and `team_aliases` table, including the Pilot #1 safe-fix corrections. Unresolvable team codes (historical ambiguity, same ~13% as Draft) are skipped for that player, not guessed. |
| Position (at draft) | **SAFE** | 4,495 / 4,506 (99.8%) | `draft_facts.position` | Deliberately scoped as "position at the time of the draft," not "career position" -- see identity policy for why a second position source (`canonical_players.primary_position`) was investigated and rejected for clue use (44% disagreement rate with `draft_facts.position`, mostly granularity differences like DT vs. NT, not usable as a second independent clue without risking an apparent contradiction). |
| College | **SAFE_WITH_LIMITATIONS** | 2,124 / 4,506 (47%) | `relationships` (`ATTENDED_BEFORE_DRAFT`, `source_id=READS_IDENTITY_BRIDGE`, `verification_status=PRODUCTION_SAFE_DERIVED`) -> `schools.school_name` | Cross-domain derived relationship (CFB<->NFL identity bridge), backed by `data_coverage.NFL_CFB_IDENTITY_BRIDGE` (`production_safe=1`). 104 of the 2,228 players who have any `ATTENDED_BEFORE_DRAFT` row have **more than one** distinct school on record (transfers or a bridge inconsistency) -- those 104 are excluded from this clue family entirely rather than guessing which school is correct. All 204 referenced schools resolve cleanly to a `schools` row. |
| NFL teams played for / team-season history | **SAFE** | 4,506 / 4,506 (100%) | `canonical_roster_seasons` (`SOURCE_BACKED`/`NFLVERSE_DATA`), filtered to `games > 0` | Every universe player has at least one such row. |
| Career span (first/last season) | **SAFE** | 4,506 / 4,506 (100%) | `MIN(season)`/`MAX(season)` over the same `canonical_roster_seasons` rows | Purely derived from an already-verified source, no new dependency. |
| Postseason participation | **SAFE_WITH_LIMITATIONS** | 2,851 / 4,506 (63%) | Derived join: `canonical_roster_seasons` (`games > 0`) x `season_standings` (`playoff_result IS NOT NULL`) on `(team_code, season)` | Both source tables are independently 100% `SOURCE_BACKED`/`NFLVERSE_DATA` (the same tables the Championship capability already uses). Roster presence with `games > 0` is a reasonable but imperfect proxy for actually appearing in the playoff game itself -- disclosed as a limitation, not treated as certain. |
| Won a Super Bowl | **SAFE_WITH_LIMITATIONS** | 492 / 4,506 (11%) | Same derived join, filtered to `playoff_result = 'WonSB'` | Subset of the above; same limitation applies. |
| QB season information | **IDENTITY_RISK** (excluded) | N/A | `qb_team_seasons` | `qb_team_seasons.qb_source_id` uses GSIS-style IDs (`"00-0001907"`); the safe universe is keyed by PFR-style IDs (`"PFR:..."`). `canonical_players.gsis_id` is **NULL for all 7,277 rows** -- there is no populated bridge column anywhere in the schema connecting these two ID spaces. Bridging would require name-based matching, which is explicitly forbidden by this milestone's non-negotiable principle. This is exactly the reverse-identity issue the QB pilot already exposed (7 excluded QB IDs, including a confirmed two-different-people merge) -- treated here as a hard exclusion, not a risk to route around. |
| Statistical milestones | **UNAVAILABLE** | 0 / 4,506 | `player_season_stats` | Table schema exists (pass/rush/rec/sack/int/tackle columns) but contains **0 rows** -- never imported. Confirmed by direct row count, not assumed from the schema's existence. |
| Awards / accomplishments (NFL) | **UNAVAILABLE** | 0 / 4,506 | -- | No NFL-level awards table or relationship exists anywhere in the 225-table schema. The only award-related data (`cfb_awards`, `cfb_award_facts`, the `WON_AWARD` relationship) is 100% college-side (`subject_type = 'cfb_player'` in every one of 91 `WON_AWARD` rows) -- not usable for an NFL player identity puzzle. |
| Championships beyond "won the Super Bowl" (e.g. conference titles as a distinct fact) | **INSUFFICIENT_DATA** | -- | -- | `season_standings.playoff_result` already captures this as one of 5 values (`WonSB`/`LostSB`/`LostCC`/`LostDV`/`LostWC`) -- there is no additional distinct "championship" fact beyond what "postseason participation" already covers. Not a separate clue family; folded into postseason participation above. |

## Identity-collision finding (relevant to Part B and adversarial testing)

Within the 4,506-player safe universe, **44 distinct `display_name` values are
shared by more than one real, different player** -- e.g. "Mike Williams"
resolves to 4 different `player_id`s, "Adrian Peterson" to 2. This is
expected (common names recur across NFL history) and is **not** a data
defect. It is flagged here because it directly motivates the identity
policy's core rule: nothing in this mechanic may ever join, deduplicate, or
prove uniqueness using `display_name` -- only `player_id`. See
`DIRECTOR_V04_IDENTITY_POLICY.md`.

## What this rules in for v0.4

Six clue families are always available for every one of the 4,506 universe
players (draft year, draft round, draft pick, position-at-draft, team
history, career span), plus three that are conditionally available per
player (drafting franchise ~87%, college ~47%, postseason ~63%/11%). This
is enough to build the 3-5 clue progressive-narrowing puzzles this milestone
targets using only `SAFE` and `SAFE_WITH_LIMITATIONS` clue families -- see
`PLAYER_FROM_CLUES_MECHANIC_SPEC.md` for exactly how clues are selected and
ordered per puzzle.
