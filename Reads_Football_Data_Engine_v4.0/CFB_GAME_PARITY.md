# College Football parity plan

The game engine is now league-symmetric: mechanics are templates, and NFL/CFB bind their own data views underneath them.

## Working for both NFL and CFB now
- Connections
- Matching
- Ordering
- Odd One Out
- Six Degrees / graph traversal
- Guess the Coach (CFB is school-context currently)
- Generic graph search

## Working CFB-specific content now
- Player → school
- Award winner
- Award winner → school
- National champion by year
- Rivalry trophy / series
- Coach → school
- Connections using shared school relationships
- Chronological ordering using awards/championships

## CFB feeds needed for full NFL-style parity
Populate the tables in `CFB_PARITY_SCHEMA.sql`:
1. team-season standings/records
2. every game + score/opponent
3. season rosters, jersey numbers and positions
4. player-season stats
5. stadium/venue history
6. conference membership by season

Once those tables are populated, existing generic templates immediately unlock:
- season record
- game winner / score
- stadium
- conference/division
- starting QB / position starter
- jersey number
- teammate
- played-for / roster history
- player stats / higher-lower
- weekly/daily CFB game generation

The important rule: do not fork the product into a separate CFB codebase. Add CFB source adapters and bind them to the same mechanic templates.
