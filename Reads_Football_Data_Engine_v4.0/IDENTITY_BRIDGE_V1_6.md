# Cross-League Identity Bridge — v1.6

## What changed
v1.6 turns NFL↔CFB identity resolution into a repeatable pipeline instead of a small hand-seeded bridge.

### Packaged bridge
The shipped database contains 107 production-safe historical links derived from the curated CFB master plus NFL draft history.

Rules:
- exact normalized player name
- exactly one chronologically plausible NFL draft candidate
- CFB evidence must precede draft year
- ambiguous same-name players are quarantined
- no candidate is promoted merely to increase coverage

### Scale-up path: exact ESPN athlete ID
`canonical_cfb_players` already stores ESPN athlete IDs for 37,743 CFB players.

The official nflverse player master contains ESPN IDs in addition to GSIS and PFR IDs. After:

```bash
python fetch_nflverse_current.py --players --rosters 2025 2026
```

v1.6 automatically runs:

```bash
python identity_bridge_v16.py
python rebuild_cross_league.py
```

The preferred production join becomes:

`CFB ESPN athlete ID == nflverse espn_id`

That link is then enriched/corroborated with:
- normalized player name
- GSIS ID
- PFR ID
- NFL position
- college/school
- CFB roster years
- NFL draft year/team
- NFL last season

Impossible chronology is quarantined even when an ID matches, so bad upstream data does not silently become trivia.

## Why this can scale dramatically
The packaged CFB roster contains 37,743 distinct player identities. nflverse documents its players table as a one-row-per-player ID source of truth with GSIS, PFR and ESPN IDs, college, draft data, position, height/weight and other player metadata.

Exact stable-ID matches are not fuzzy-name guesses. As players move from college to the NFL and appear in nflverse, a normal data refresh can promote them automatically.

## Cross-league modes now
- CFB school → NFL draft team
- CFB award → NFL draft team
- award-before-draft ordering
- CFB identity → NFL identity
- school pipeline Connections
- Game Factory cross-domain sequence rules

## Operator rule
Never manually mark a name-only ambiguous match production-safe. Use stable IDs or explicit review evidence.
