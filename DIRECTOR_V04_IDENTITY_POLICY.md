# Player From Clues -- Identity Policy (Director v0.4, Part B)

Identity must be solved before multi-source clues are allowed. This
document is the hard gate: no clue-construction code may combine facts
from two different tables about "the same player" except by the rule
defined here.

## The core rule

**A player's identity, for this mechanic, is their `player_id` in
`canonical_players` (`"PFR:..."` format). Every clue-source table used by
this mechanic must be joined to that ID directly and exactly -- never by
name, never fuzzily, never by inference.**

No code in `tools/director_v04/` may compare `display_name`,
`player_name`, or any other free-text name field between two tables to
decide they refer to the same person. Name fields are used only for
*display* (constructing clue text, showing the answer to a human
reviewer) -- never for *matching*.

## What was investigated

### 1. Is `player_identity_links` a real cross-source bridge?

No -- empirically, it is not. Every one of its 4,506 rows has
`canonical_player_id == nfl_player_key` (checked directly: 0 rows differ).
It provides zero additional identity resolution beyond a plain string-equality
join between `draft_facts.player_key` and `canonical_players.player_id`.
Its actual value is narrower than its name suggests: it identifies *which
subset* of `draft_facts` rows have a matching `canonical_players` row, not a
mechanism for resolving conflicting IDs. This is disclosed rather than
taken at face value, per this project's standing rule to verify rather than
assume.

### 2. Are there one-ID-to-many-name or many-ID-to-one-name conflicts?

- **One-ID-to-many-name**: not found. Every `player_id` in
  `canonical_players` has exactly one `display_name` (by construction --
  `player_id` is the table's primary identity column).
- **Many-ID-to-one-name (same-name, different-player)**: found and
  confirmed real. 44 distinct names are shared across 2+ different
  `player_id`s within the safe universe (see feasibility report). This is
  handled correctly by construction, not by special-casing: because every
  join and every uniqueness check in this mechanic operates on
  `player_id`, a name collision has zero effect on correctness. It is
  listed here, and used as a real adversarial test fixture in Part P,
  specifically to prove that claim empirically rather than assert it.

### 3. Can NFL-side player facts be safely bridged to CFB-side (college) facts?

Yes, narrowly, through `relationships.SAME_PERSON_AS` /
`relationships.ATTENDED_BEFORE_DRAFT`, both tagged
`source_id = READS_IDENTITY_BRIDGE`, `verification_status =
PRODUCTION_SAFE_DERIVED`, and backed by `data_coverage.NFL_CFB_IDENTITY_BRIDGE`
(`production_safe = 1`). This is Engine's own explicit certification of this
bridge, not an assumption made here. Two additional safety rules were added
on top of that certification because a *domain-level* safety flag doesn't
guarantee every individual row is unambiguous:

- A player is only eligible for a college clue if `ATTENDED_BEFORE_DRAFT`
  names **exactly one** distinct school for them. 104 of 2,228 candidate
  players have 2+ distinct schools on record (transfers, or a genuine bridge
  inconsistency) -- **excluded from this clue family entirely**, not
  resolved by guessing which school is "primary."
- The bridge's `nfl_player` side is checked to land inside the same
  4,506-player safe universe (i.e. resolves through `draft_facts.player_key`
  -> `canonical_players.player_id` the same way every other clue source
  does) before it's used -- some `SAME_PERSON_AS`/`ATTENDED_BEFORE_DRAFT`
  rows point at `DRAFT:...`-prefixed synthetic keys (players with no PFR
  match) that fall outside the safe universe entirely and are simply never
  reached by this mechanic's queries.

### 4. Can QB-specific data (`qb_team_seasons`) be safely bridged in?

**No.** Investigated and rejected. `qb_team_seasons.qb_source_id` uses
GSIS-format IDs (`"00-0001907"`); the safe universe is keyed by PFR-format
IDs (`"PFR:..."`). `canonical_players.gsis_id` -- the column that would be
the obvious bridge -- is `NULL` for all 7,277 rows. No other table in the
225-table schema maps GSIS IDs to PFR IDs. The only way to connect these
two ID spaces would be matching on `qb_name` against `player_name`/
`display_name` -- exactly the fuzzy name-matching this policy forbids, and
exactly the failure mode the QB pilot already documented (7 QB IDs excluded
for identity inconsistency, including one confirmed two-different-people
merge). **QB season data is excluded from Player From Clues entirely** --
not routed around, not approximated.

### 5. Birth information, height/weight

`canonical_players.birth_date`, `height_in`, `weight_lb` exist as columns
but were not investigated further for clue use in this milestone --
population rate wasn't checked. Not used in v0.4. Flagged as a possible
future clue family, not a rejected one; "not evaluated" is a distinct,
honest status from "rejected."

## Resulting policy for `tools/director_v04/player_from_clues.py`

1. The target-player universe is fixed and computed once: `draft_facts`
   rows with `verification_status='SOURCE_BACKED'`, `source_id='NFLVERSE_DATA'`,
   `player_key LIKE 'PFR:%'`, joined by exact string equality to
   `canonical_players.player_id`.
2. Every clue-source query joins to this same `player_key`/`player_id`
   value directly -- no intermediate table is trusted to perform identity
   resolution on the adapter's behalf.
3. Candidate-set counts (Part E/F narrowing math) are always computed
   against this same fixed universe, so a clue's "how many players could
   this describe" number means the same thing across every clue type in
   the same puzzle.
4. If a player has a conflicting or missing fact for a given clue family
   (e.g. 2+ distinct colleges, no roster-season data), that clue family is
   simply not offered for that player -- never approximated, never
   resolved by picking the "most likely" value.
5. `display_name` (and any other free-text name field) is used only inside
   already-finalized clue `display_text` and the human-review/answer
   fields -- never as a join key, never as an equality check for
   determining whether two rows describe the same player.
