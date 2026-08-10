# Identity Bridge v1.7

v1.7 expands the production-safe NFL↔CFB bridge from 107 to **3,534 players** without using fuzzy name matching or GPL data in production.

## Evidence rule
A player is promoted only when:
1. SportsDataverse supplies a stable CFB ESPN athlete identity and roster history.
2. The normalized CFB player name maps to exactly one NFL draft identity in the approved NFL draft source.
3. The NFL draft occurs no earlier than the final CFB roster season and no more than three years later.
4. When both sides have position data, broad position groups must be compatible.
5. Same-name ambiguities, chronology failures, and position conflicts are quarantined.

## Historical CFB roster expansion
The packaged roster table now spans **2004–2025** with **282,124 roster rows** and **109,221 canonical CFB players**.

## Game unlocks
- school → NFL draft team
- CFB identity → NFL identity
- award → draft team
- award-before-draft ordering
- school pipeline Connections
- draft-class college matching
- deeper cross-league graph traversal

## Source policy
A current DynastyProcess ID file was used only as a development audit to measure possible future stable-ID coverage. It is **not shipped and is not used to mark production-safe links**. Production v1.7 links come from the approved SportsDataverse CFB roster source plus the approved NFL draft source already in Reads.
