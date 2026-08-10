# Quiz Engine Mixed Pilot -- Human Review Sample

A deterministic sample of the 300-question mixed Engine pack -- the first 15 questions (in each domain's own deterministic export order) from each of the three domains, 45 total. Generated from the same in-memory data used to build `data/quiz-engine-mixed-pilot.js` in this run, verified against the actual persisted file before this document was written.

## Summary

- Total questions shown: **45** (15 Draft + 15 QB/Season + 15 Championship/Postseason)
- Full pack: 300 questions -- see `QUIZ_ENGINE_MIXED_PILOT_REPORT.md` for the complete audit
- Sampling method: first 15 of each domain's 100-question deterministic export order (no additional randomness)

---

# Draft (15 questions)

## #500000 -- Which NFL team drafted Isaiah Ford?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. Los Angeles Rams
  1. New Orleans Saints
  2. Miami Dolphins **<- CORRECT**
  3. Cleveland Browns
- **Draft year / source context:** Isaiah Ford was drafted in the **2017** NFL Draft by team code `MIA`, resolved to franchise `FR_MIA` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:FordIs00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500001 -- Which NFL team drafted Jaylen Twyman?

- **Category:** NFL Draft History
- **Difficulty:** Medium
- **Options:**
  0. Minnesota Vikings **<- CORRECT**
  1. Detroit Lions
  2. Miami Dolphins
  3. Tampa Bay Buccaneers
- **Draft year / source context:** Jaylen Twyman was drafted in the **2021** NFL Draft by team code `MIN`, resolved to franchise `FR_MIN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:TwymJa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500002 -- Which NFL team drafted Andrew Melontree?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. Buffalo Bills
  1. Cincinnati Bengals **<- CORRECT**
  2. Dallas Cowboys
  3. Kansas City Chiefs
- **Draft year / source context:** Andrew Melontree was drafted in the **1980** NFL Draft by team code `CIN`, resolved to franchise `FR_CIN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:MeloAn20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500003 -- Which NFL team drafted Hayden Epstein?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. New England Patriots
  1. Jacksonville Jaguars **<- CORRECT**
  2. St Louis Rams
  3. Arizona Cardinals
- **Draft year / source context:** Hayden Epstein was drafted in the **2002** NFL Draft by team code `JAX`, resolved to franchise `FR_JAX` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:epstehay01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500004 -- Which NFL team drafted James Lee?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. Arizona Cardinals
  1. Detroit Lions
  2. Green Bay Packers **<- CORRECT**
  3. Seattle Seahawks
- **Draft year / source context:** James Lee was drafted in the **2003** NFL Draft by team code `GB`, resolved to franchise `FR_GB` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:LeexJa21`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500005 -- Which NFL team drafted Dan Fike?

- **Category:** NFL Draft History
- **Difficulty:** Medium
- **Options:**
  0. Tampa Bay Buccaneers
  1. Miami Dolphins
  2. New York Jets **<- CORRECT**
  3. Seattle Seahawks
- **Draft year / source context:** Dan Fike was drafted in the **1983** NFL Draft by team code `NYJ`, resolved to franchise `FR_NYJ` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:FikeDa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500006 -- Which NFL team drafted Hudhaifa Ismaeli?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. Detroit Lions
  1. Arizona Cardinals
  2. Jacksonville Jaguars
  3. Miami Dolphins **<- CORRECT**
- **Draft year / source context:** Hudhaifa Ismaeli was drafted in the **1997** NFL Draft by team code `MIA`, resolved to franchise `FR_MIA` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `DRAFT:1997:203:HUDHAIFA_ISMAELI`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500007 -- Which NFL team drafted George Crump?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. New England Patriots **<- CORRECT**
  1. Pittsburgh Steelers
  2. San Diego Chargers
  3. Chicago Bears
- **Draft year / source context:** George Crump was drafted in the **1982** NFL Draft by team code `NE`, resolved to franchise `FR_NE` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:CrumGe20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500008 -- Which NFL team drafted Larry Jones?

- **Category:** NFL Draft History
- **Difficulty:** Medium
- **Options:**
  0. New England Patriots
  1. Pittsburgh Steelers
  2. Tampa Bay Buccaneers
  3. Washington Redskins **<- CORRECT**
- **Draft year / source context:** Larry Jones was drafted in the **1995** NFL Draft by team code `WAS`, resolved to franchise `FR_WAS` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `DRAFT:1995:103:LARRY_JONES`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500009 -- Which NFL team drafted Darius Slayton?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. Houston Texans
  1. New York Giants **<- CORRECT**
  2. Philadelphia Eagles
  3. Pittsburgh Steelers
- **Draft year / source context:** Darius Slayton was drafted in the **2019** NFL Draft by team code `NYG`, resolved to franchise `FR_NYG` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:SlayDa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500010 -- Which NFL team drafted Johnnie Lee Higgins?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. Carolina Panthers
  1. New York Giants
  2. Oakland Raiders **<- CORRECT**
  3. Washington Redskins
- **Draft year / source context:** Johnnie Lee Higgins was drafted in the **2007** NFL Draft by team code `OAK`, resolved to franchise `FR_LV` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:HiggJo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500011 -- Which NFL team drafted Antico Dalton?

- **Category:** NFL Draft History
- **Difficulty:** Medium
- **Options:**
  0. Detroit Lions
  1. New Orleans Saints
  2. Minnesota Vikings **<- CORRECT**
  3. Kansas City Chiefs
- **Draft year / source context:** Antico Dalton was drafted in the **1999** NFL Draft by team code `MIN`, resolved to franchise `FR_MIN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:DaltAn20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500012 -- Which NFL team drafted Ron Lewis?

- **Category:** NFL Draft History
- **Difficulty:** Medium
- **Options:**
  0. San Diego Chargers
  1. New York Giants
  2. San Francisco 49ers **<- CORRECT**
  3. Washington Redskins
- **Draft year / source context:** Ron Lewis was drafted in the **1990** NFL Draft by team code `SF`, resolved to franchise `FR_SF` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:LewiRo01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500013 -- Which NFL team drafted Bobby Joe Edmonds?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. New England Patriots
  1. Buffalo Bills
  2. Tampa Bay Buccaneers
  3. Seattle Seahawks **<- CORRECT**
- **Draft year / source context:** Bobby Joe Edmonds was drafted in the **1986** NFL Draft by team code `SEA`, resolved to franchise `FR_SEA` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:EdmoBo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #500014 -- Which NFL team drafted John Greco?

- **Category:** NFL Draft History
- **Difficulty:** Hard
- **Options:**
  0. Tennessee Titans
  1. St Louis Rams **<- CORRECT**
  2. Cleveland Browns
  3. Buffalo Bills
- **Draft year / source context:** John Greco was drafted in the **2008** NFL Draft by team code `STL`, resolved to franchise `FR_LAR` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:GrecJo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

---

# QB/Season (15 questions)

## #500100 -- Which NFL team did Josh Freeman play for in the 2010 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Medium
- **Options:**
  0. Tampa Bay Buccaneers **<- CORRECT**
  1. Chicago Bears
  2. Carolina Panthers
  3. New York Jets
- **QB:** Josh Freeman (GSIS id `00-0026993`)
- **Season:** 2010
- **Team/context:** raw team code `TB`, resolved franchise `FR_TB` ("Tampa Bay Buccaneers"), 16 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500101 -- Which NFL team did C.J. Beathard play for in the 2018 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Hard
- **Options:**
  0. Los Angeles Rams
  1. Philadelphia Eagles
  2. Cleveland Browns
  3. San Francisco 49ers **<- CORRECT**
- **QB:** C.J. Beathard (GSIS id `00-0033936`)
- **Season:** 2018
- **Team/context:** raw team code `SF`, resolved franchise `FR_SF` ("San Francisco 49ers"), 5 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500102 -- Which NFL team did Blaine Gabbert play for in the 2012 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Medium
- **Options:**
  0. Jacksonville Jaguars **<- CORRECT**
  1. Minnesota Vikings
  2. Tampa Bay Buccaneers
  3. Indianapolis Colts
- **QB:** Blaine Gabbert (GSIS id `00-0027948`)
- **Season:** 2012
- **Team/context:** raw team code `JAX`, resolved franchise `FR_JAX` ("Jacksonville Jaguars"), 10 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500103 -- Which NFL team did Steve Beuerlein play for in the 1999 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Hard
- **Options:**
  0. Atlanta Falcons
  1. Carolina Panthers **<- CORRECT**
  2. Cleveland Browns
  3. Detroit Lions
- **QB:** Steve Beuerlein (GSIS id `00-0001218`)
- **Season:** 1999
- **Team/context:** raw team code `CAR`, resolved franchise `FR_CAR` ("Carolina Panthers"), 16 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500104 -- Which NFL team did Kelly Holcomb play for in the 2002 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Hard
- **Options:**
  0. New York Giants
  1. Philadelphia Eagles
  2. Tampa Bay Buccaneers
  3. Cleveland Browns **<- CORRECT**
- **QB:** Kelly Holcomb (GSIS id `00-0007576`)
- **Season:** 2002
- **Team/context:** raw team code `CLE`, resolved franchise `FR_CLE` ("Cleveland Browns"), 4 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500105 -- Which NFL team did Brock Purdy play for in the 2023 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Easy
- **Options:**
  0. Seattle Seahawks
  1. Dallas Cowboys
  2. New England Patriots
  3. San Francisco 49ers **<- CORRECT**
- **QB:** Brock Purdy (GSIS id `00-0037834`)
- **Season:** 2023
- **Team/context:** raw team code `SF`, resolved franchise `FR_SF` ("San Francisco 49ers"), 19 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500106 -- Which NFL team did Drew Brees play for in the 2018 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Easy
- **Options:**
  0. New England Patriots
  1. Houston Texans
  2. New Orleans Saints **<- CORRECT**
  3. Chicago Bears
- **QB:** Drew Brees (GSIS id `00-0020531`)
- **Season:** 2018
- **Team/context:** raw team code `NO`, resolved franchise `FR_NO` ("New Orleans Saints"), 17 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500107 -- Which NFL team did Matt Ryan play for in the 2011 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Medium
- **Options:**
  0. New York Jets
  1. New York Giants
  2. Houston Texans
  3. Atlanta Falcons **<- CORRECT**
- **QB:** Matt Ryan (GSIS id `00-0026143`)
- **Season:** 2011
- **Team/context:** raw team code `ATL`, resolved franchise `FR_ATL` ("Atlanta Falcons"), 17 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500108 -- Which NFL team did Kerry Collins play for in the 2000 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Hard
- **Options:**
  0. Detroit Lions
  1. Carolina Panthers
  2. Atlanta Falcons
  3. New York Giants **<- CORRECT**
- **QB:** Kerry Collins (GSIS id `00-0003292`)
- **Season:** 2000
- **Team/context:** raw team code `NYG`, resolved franchise `FR_NYG` ("New York Giants"), 19 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500109 -- Which NFL team did Marcus Mariota play for in the 2018 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Easy
- **Options:**
  0. Los Angeles Rams
  1. Cincinnati Bengals
  2. Tennessee Titans **<- CORRECT**
  3. New England Patriots
- **QB:** Marcus Mariota (GSIS id `00-0032268`)
- **Season:** 2018
- **Team/context:** raw team code `TEN`, resolved franchise `FR_TEN` ("Tennessee Titans"), 13 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500110 -- Which NFL team did Andy Dalton play for in the 2020 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Easy
- **Options:**
  0. Buffalo Bills
  1. Dallas Cowboys **<- CORRECT**
  2. Kansas City Chiefs
  3. New York Giants
- **QB:** Andy Dalton (GSIS id `00-0027973`)
- **Season:** 2020
- **Team/context:** raw team code `DAL`, resolved franchise `FR_DAL` ("Dallas Cowboys"), 9 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500111 -- Which NFL team did Jay Cutler play for in the 2006 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Hard
- **Options:**
  0. Denver Broncos **<- CORRECT**
  1. Green Bay Packers
  2. Chicago Bears
  3. Detroit Lions
- **QB:** Jay Cutler (GSIS id `00-0024226`)
- **Season:** 2006
- **Team/context:** raw team code `DEN`, resolved franchise `FR_DEN` ("Denver Broncos"), 5 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500112 -- Which NFL team did Spencer Rattler play for in the 2025 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Medium
- **Options:**
  0. New Orleans Saints **<- CORRECT**
  1. New York Giants
  2. Detroit Lions
  3. Seattle Seahawks
- **QB:** Spencer Rattler (GSIS id `00-0039376`)
- **Season:** 2025
- **Team/context:** raw team code `NO`, resolved franchise `FR_NO` ("New Orleans Saints"), 8 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500113 -- Which NFL team did Peyton Manning play for in the 2006 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Medium
- **Options:**
  0. Jacksonville Jaguars
  1. Indianapolis Colts **<- CORRECT**
  2. Seattle Seahawks
  3. Houston Texans
- **QB:** Peyton Manning (GSIS id `00-0010346`)
- **Season:** 2006
- **Team/context:** raw team code `IND`, resolved franchise `FR_IND` ("Indianapolis Colts"), 20 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

## #500114 -- Which NFL team did Jeff George play for in the 2000 season?

- **Category:** Passing Records & QB Trivia
- **Difficulty:** Hard
- **Options:**
  0. Miami Dolphins
  1. New York Giants
  2. Washington Redskins **<- CORRECT**
  3. San Diego Chargers
- **QB:** Jeff George (GSIS id `00-0005885`)
- **Season:** 2000
- **Team/context:** raw team code `WAS`, resolved franchise `FR_WAS` ("Washington Redskins"), 5 start(s) observed that season
- **Engine source/domain:** `qb_team_seasons` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `qb_season` `puzzle_catalog` mode

---

# Championship/Postseason (15 questions)

## #500200 -- How did the Philadelphia Eagles finish the 2025 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Medium
- **Options:**
  0. Lost in the Divisional Round
  1. Lost in the Conference Championship
  2. Won the Super Bowl
  3. Lost in the Wild Card Round **<- CORRECT**
- **Season/year:** 2025
- **Team/context:** raw team code `PHI`, resolved franchise `FR_PHI` ("Lost in the Wild Card Round" for 2025), regular-season record 11-6, raw outcome code `LostWC`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500201 -- How did the Washington Redskins finish the 2012 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost the Super Bowl
  1. Lost in the Conference Championship
  2. Lost in the Wild Card Round **<- CORRECT**
  3. Lost in the Divisional Round
- **Season/year:** 2012
- **Team/context:** raw team code `WAS`, resolved franchise `FR_WAS` ("Lost in the Wild Card Round" for 2012), regular-season record 10-6, raw outcome code `LostWC`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500202 -- How did the Green Bay Packers finish the 2012 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Won the Super Bowl
  1. Lost in the Wild Card Round
  2. Lost in the Divisional Round **<- CORRECT**
  3. Lost the Super Bowl
- **Season/year:** 2012
- **Team/context:** raw team code `GB`, resolved franchise `FR_GB` ("Lost in the Divisional Round" for 2012), regular-season record 11-5, raw outcome code `LostDV`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500203 -- How did the Pittsburgh Steelers finish the 2008 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost the Super Bowl
  1. Lost in the Wild Card Round
  2. Won the Super Bowl **<- CORRECT**
  3. Lost in the Conference Championship
- **Season/year:** 2008
- **Team/context:** raw team code `PIT`, resolved franchise `FR_PIT` ("Won the Super Bowl" for 2008), regular-season record 12-4, raw outcome code `WonSB`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500204 -- How did the Indianapolis Colts finish the 2009 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Won the Super Bowl
  1. Lost the Super Bowl **<- CORRECT**
  2. Lost in the Conference Championship
  3. Lost in the Wild Card Round
- **Season/year:** 2009
- **Team/context:** raw team code `IND`, resolved franchise `FR_IND` ("Lost the Super Bowl" for 2009), regular-season record 14-2, raw outcome code `LostSB`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500205 -- How did the New England Patriots finish the 2014 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost the Super Bowl
  1. Won the Super Bowl **<- CORRECT**
  2. Lost in the Wild Card Round
  3. Lost in the Divisional Round
- **Season/year:** 2014
- **Team/context:** raw team code `NE`, resolved franchise `FR_NE` ("Won the Super Bowl" for 2014), regular-season record 12-4, raw outcome code `WonSB`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500206 -- How did the Seattle Seahawks finish the 2022 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Medium
- **Options:**
  0. Lost the Super Bowl
  1. Lost in the Wild Card Round **<- CORRECT**
  2. Lost in the Conference Championship
  3. Won the Super Bowl
- **Season/year:** 2022
- **Team/context:** raw team code `SEA`, resolved franchise `FR_SEA` ("Lost in the Wild Card Round" for 2022), regular-season record 9-8, raw outcome code `LostWC`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500207 -- How did the Tennessee Titans finish the 2021 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Medium
- **Options:**
  0. Lost in the Wild Card Round
  1. Lost in the Divisional Round **<- CORRECT**
  2. Lost the Super Bowl
  3. Lost in the Conference Championship
- **Season/year:** 2021
- **Team/context:** raw team code `TEN`, resolved franchise `FR_TEN` ("Lost in the Divisional Round" for 2021), regular-season record 12-5, raw outcome code `LostDV`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500208 -- How did the Kansas City Chiefs finish the 2003 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost in the Conference Championship
  1. Lost in the Wild Card Round
  2. Lost in the Divisional Round **<- CORRECT**
  3. Won the Super Bowl
- **Season/year:** 2003
- **Team/context:** raw team code `KC`, resolved franchise `FR_KC` ("Lost in the Divisional Round" for 2003), regular-season record 13-3, raw outcome code `LostDV`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500209 -- How did the New York Jets finish the 2004 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost the Super Bowl
  1. Lost in the Divisional Round **<- CORRECT**
  2. Won the Super Bowl
  3. Lost in the Conference Championship
- **Season/year:** 2004
- **Team/context:** raw team code `NYJ`, resolved franchise `FR_NYJ` ("Lost in the Divisional Round" for 2004), regular-season record 10-6, raw outcome code `LostDV`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500210 -- How did the Seattle Seahawks finish the 2007 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Won the Super Bowl
  1. Lost in the Divisional Round **<- CORRECT**
  2. Lost in the Conference Championship
  3. Lost in the Wild Card Round
- **Season/year:** 2007
- **Team/context:** raw team code `SEA`, resolved franchise `FR_SEA` ("Lost in the Divisional Round" for 2007), regular-season record 10-6, raw outcome code `LostDV`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500211 -- How did the New England Patriots finish the 2017 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost the Super Bowl **<- CORRECT**
  1. Lost in the Wild Card Round
  2. Lost in the Conference Championship
  3. Lost in the Divisional Round
- **Season/year:** 2017
- **Team/context:** raw team code `NE`, resolved franchise `FR_NE` ("Lost the Super Bowl" for 2017), regular-season record 13-3, raw outcome code `LostSB`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500212 -- How did the Atlanta Falcons finish the 2016 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost in the Conference Championship
  1. Lost in the Divisional Round
  2. Lost in the Wild Card Round
  3. Lost the Super Bowl **<- CORRECT**
- **Season/year:** 2016
- **Team/context:** raw team code `ATL`, resolved franchise `FR_ATL` ("Lost the Super Bowl" for 2016), regular-season record 11-5, raw outcome code `LostSB`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500213 -- How did the Green Bay Packers finish the 2003 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Hard
- **Options:**
  0. Lost in the Conference Championship
  1. Lost in the Divisional Round **<- CORRECT**
  2. Lost in the Wild Card Round
  3. Lost the Super Bowl
- **Season/year:** 2003
- **Team/context:** raw team code `GB`, resolved franchise `FR_GB` ("Lost in the Divisional Round" for 2003), regular-season record 10-6, raw outcome code `LostDV`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

## #500214 -- How did the Tampa Bay Buccaneers finish the 2022 NFL season?

- **Category:** Playoffs & Postseason Moments
- **Difficulty:** Medium
- **Options:**
  0. Lost the Super Bowl
  1. Lost in the Conference Championship
  2. Lost in the Wild Card Round **<- CORRECT**
  3. Won the Super Bowl
- **Season/year:** 2022
- **Team/context:** raw team code `TB`, resolved franchise `FR_TB` ("Lost in the Wild Card Round" for 2022), regular-season record 8-9, raw outcome code `LostWC`
- **Engine source/domain:** `season_standings` row, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA`; difficulty cross-referenced from Engine's pre-existing `playoff_result` `puzzle_catalog` mode

