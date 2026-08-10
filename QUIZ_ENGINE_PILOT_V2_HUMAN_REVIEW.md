# Quiz Engine Pilot v2 -- Human Review Package

Regenerated from the same deterministic pipeline as `tools/export_quiz_engine_pilot_v2.py` (seed `reads-quiz-engine-pilot-v1`) and verified byte-identical, field-by-field, against the already-written `data/quiz-engine-pilot-v2.js` before this document was produced -- this is the real output with its audit trail re-attached, not a separate approximation of the pipeline. No question text, option, or answer was altered to produce this report.

## Summary

- Total questions: **100**
- Difficulty split: Hard 69, Medium 31
- Unique players: **100**
- Unique franchises represented: **31** / 32
- Draft-year range: **1980-2024**
- Category: NFL Draft History (all 100)
- Underlying Engine source/domain: `draft_facts` table, domain `NFL_DRAFT`, source `NFLVERSE_DATA`
- Team-code resolution: `team_aliases`, including the 30 SAFE_FIX_AVAILABLE corrections applied per `TEAM_ALIAS_SAFE_FIX_CHANGELOG.md`

---

## #200000 -- Which NFL team drafted Isaiah Ford?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Los Angeles Rams
  1. New Orleans Saints
  2. Miami Dolphins **<- CORRECT**
  3. Cleveland Browns
- **Draft year:** 2017
- **Raw historical team code:** `MIA`
- **Resolved franchise:** `FR_MIA` ("Miami Dolphins"), resolved via Engine's `team_aliases` table, season-matched to 2017
- **Source/domain:** `draft_facts` row, player_key `PFR:FordIs00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200001 -- Which NFL team drafted Jaylen Twyman?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Minnesota Vikings **<- CORRECT**
  1. Detroit Lions
  2. Miami Dolphins
  3. Tampa Bay Buccaneers
- **Draft year:** 2021
- **Raw historical team code:** `MIN`
- **Resolved franchise:** `FR_MIN` ("Minnesota Vikings"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:TwymJa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200002 -- Which NFL team drafted Andrew Melontree?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Buffalo Bills
  1. Cincinnati Bengals **<- CORRECT**
  2. Dallas Cowboys
  3. Kansas City Chiefs
- **Draft year:** 1980
- **Raw historical team code:** `CIN`
- **Resolved franchise:** `FR_CIN` ("Cincinnati Bengals"), resolved via Engine's `team_aliases` table, season-matched to 1980
- **Source/domain:** `draft_facts` row, player_key `PFR:MeloAn20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200003 -- Which NFL team drafted Hayden Epstein?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6567)
- **Options:**
  0. New England Patriots
  1. Jacksonville Jaguars **<- CORRECT**
  2. St Louis Rams
  3. Arizona Cardinals
- **Draft year:** 2002
- **Raw historical team code:** `JAX`
- **Resolved franchise:** `FR_JAX` ("Jacksonville Jaguars"), resolved via Engine's `team_aliases` table, season-matched to 2002
- **Source/domain:** `draft_facts` row, player_key `PFR:epstehay01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200004 -- Which NFL team drafted James Lee?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6427)
- **Options:**
  0. Arizona Cardinals
  1. Detroit Lions
  2. Green Bay Packers **<- CORRECT**
  3. Seattle Seahawks
- **Draft year:** 2003
- **Raw historical team code:** `GB`
- **Resolved franchise:** `FR_GB` ("Green Bay Packers"), resolved via Engine's `team_aliases` table, season-matched to 2003
- **Source/domain:** `draft_facts` row, player_key `PFR:LeexJa21`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200005 -- Which NFL team drafted Dan Fike?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. Tampa Bay Buccaneers
  1. Miami Dolphins
  2. New York Jets **<- CORRECT**
  3. Seattle Seahawks
- **Draft year:** 1983
- **Raw historical team code:** `NYJ`
- **Resolved franchise:** `FR_NYJ` ("New York Jets"), resolved via Engine's `team_aliases` table, season-matched to 1983
- **Source/domain:** `draft_facts` row, player_key `PFR:FikeDa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200006 -- Which NFL team drafted Hudhaifa Ismaeli?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6147)
- **Options:**
  0. Detroit Lions
  1. Arizona Cardinals
  2. Jacksonville Jaguars
  3. Miami Dolphins **<- CORRECT**
- **Draft year:** 1997
- **Raw historical team code:** `MIA`
- **Resolved franchise:** `FR_MIA` ("Miami Dolphins"), resolved via Engine's `team_aliases` table, season-matched to 1997
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1997:203:HUDHAIFA_ISMAELI`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200007 -- Which NFL team drafted George Crump?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5867)
- **Options:**
  0. New England Patriots **<- CORRECT**
  1. Pittsburgh Steelers
  2. San Diego Chargers
  3. Chicago Bears
- **Draft year:** 1982
- **Raw historical team code:** `NE`
- **Resolved franchise:** `FR_NE` ("New England Patriots"), resolved via Engine's `team_aliases` table, season-matched to 1982
- **Source/domain:** `draft_facts` row, player_key `PFR:CrumGe20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200008 -- Which NFL team drafted Larry Jones?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. New England Patriots
  1. Pittsburgh Steelers
  2. Tampa Bay Buccaneers
  3. Washington Redskins **<- CORRECT**
- **Draft year:** 1995
- **Raw historical team code:** `WAS`
- **Resolved franchise:** `FR_WAS` ("Washington Redskins"), resolved via Engine's `team_aliases` table, season-matched to 1995
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1995:103:LARRY_JONES`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200009 -- Which NFL team drafted Darius Slayton?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Houston Texans
  1. New York Giants **<- CORRECT**
  2. Philadelphia Eagles
  3. Pittsburgh Steelers
- **Draft year:** 2019
- **Raw historical team code:** `NYG`
- **Resolved franchise:** `FR_NYG` ("New York Giants"), resolved via Engine's `team_aliases` table, season-matched to 2019
- **Source/domain:** `draft_facts` row, player_key `PFR:SlayDa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200010 -- Which NFL team drafted Johnnie Lee Higgins?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6147)
- **Options:**
  0. Carolina Panthers
  1. New York Giants
  2. Oakland Raiders **<- CORRECT**
  3. Washington Redskins
- **Draft year:** 2007
- **Raw historical team code:** `OAK`
- **Resolved franchise:** `FR_LV` ("Oakland Raiders"), resolved via Engine's `team_aliases` table, season-matched to 2007
- **Source/domain:** `draft_facts` row, player_key `PFR:HiggJo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200011 -- Which NFL team drafted Antico Dalton?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. Detroit Lions
  1. New Orleans Saints
  2. Minnesota Vikings **<- CORRECT**
  3. Kansas City Chiefs
- **Draft year:** 1999
- **Raw historical team code:** `MIN`
- **Resolved franchise:** `FR_MIN` ("Minnesota Vikings"), resolved via Engine's `team_aliases` table, season-matched to 1999
- **Source/domain:** `draft_facts` row, player_key `PFR:DaltAn20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200012 -- Which NFL team drafted Ron Lewis?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. San Diego Chargers
  1. New York Giants
  2. San Francisco 49ers **<- CORRECT**
  3. Washington Redskins
- **Draft year:** 1990
- **Raw historical team code:** `SF`
- **Resolved franchise:** `FR_SF` ("San Francisco 49ers"), resolved via Engine's `team_aliases` table, season-matched to 1990
- **Source/domain:** `draft_facts` row, player_key `PFR:LewiRo01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200013 -- Which NFL team drafted Bobby Joe Edmonds?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. New England Patriots
  1. Buffalo Bills
  2. Tampa Bay Buccaneers
  3. Seattle Seahawks **<- CORRECT**
- **Draft year:** 1986
- **Raw historical team code:** `SEA`
- **Resolved franchise:** `FR_SEA` ("Seattle Seahawks"), resolved via Engine's `team_aliases` table, season-matched to 1986
- **Source/domain:** `draft_facts` row, player_key `PFR:EdmoBo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200014 -- Which NFL team drafted John Greco?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5867)
- **Options:**
  0. Tennessee Titans
  1. St Louis Rams **<- CORRECT**
  2. Cleveland Browns
  3. Buffalo Bills
- **Draft year:** 2008
- **Raw historical team code:** `STL`
- **Resolved franchise:** `FR_LAR` ("St Louis Rams"), resolved via Engine's `team_aliases` table, season-matched to 2008
- **Source/domain:** `draft_facts` row, player_key `PFR:GrecJo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200015 -- Which NFL team drafted Maurice Rodriguez?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. Kansas City Chiefs **<- CORRECT**
  1. Detroit Lions
  2. San Diego Chargers
  3. New England Patriots
- **Draft year:** 2002
- **Raw historical team code:** `KC`
- **Resolved franchise:** `FR_KC` ("Kansas City Chiefs"), resolved via Engine's `team_aliases` table, season-matched to 2002
- **Source/domain:** `draft_facts` row, player_key `DRAFT:2002:221:MAURICE_RODRIGUEZ`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200016 -- Which NFL team drafted Lance Sellers?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Cincinnati Bengals
  1. Miami Dolphins **<- CORRECT**
  2. Seattle Seahawks
  3. Kansas City Chiefs
- **Draft year:** 1987
- **Raw historical team code:** `MIA`
- **Resolved franchise:** `FR_MIA` ("Miami Dolphins"), resolved via Engine's `team_aliases` table, season-matched to 1987
- **Source/domain:** `draft_facts` row, player_key `PFR:SellLa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200017 -- Which NFL team drafted Tyree Gillespie?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Pittsburgh Steelers
  1. Miami Dolphins
  2. New York Giants
  3. Las Vegas Raiders **<- CORRECT**
- **Draft year:** 2021
- **Raw historical team code:** `LV`
- **Resolved franchise:** `FR_LV` ("Las Vegas Raiders"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:GillTy00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200018 -- Which NFL team drafted Alvin Harper?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6287)
- **Options:**
  0. Green Bay Packers
  1. Dallas Cowboys **<- CORRECT**
  2. San Diego Chargers
  3. Minnesota Vikings
- **Draft year:** 1991
- **Raw historical team code:** `DAL`
- **Resolved franchise:** `FR_DAL` ("Dallas Cowboys"), resolved via Engine's `team_aliases` table, season-matched to 1991
- **Source/domain:** `draft_facts` row, player_key `PFR:HarpAl00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200019 -- Which NFL team drafted Patrick Chukwurah?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6287)
- **Options:**
  0. Green Bay Packers
  1. Minnesota Vikings **<- CORRECT**
  2. Pittsburgh Steelers
  3. Chicago Bears
- **Draft year:** 2001
- **Raw historical team code:** `MIN`
- **Resolved franchise:** `FR_MIN` ("Minnesota Vikings"), resolved via Engine's `team_aliases` table, season-matched to 2001
- **Source/domain:** `draft_facts` row, player_key `PFR:ChukPa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200020 -- Which NFL team drafted Tavon Young?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5447)
- **Options:**
  0. Cincinnati Bengals
  1. New York Jets
  2. Baltimore Ravens **<- CORRECT**
  3. San Francisco 49ers
- **Draft year:** 2016
- **Raw historical team code:** `BAL`
- **Resolved franchise:** `FR_BAL` ("Baltimore Ravens"), resolved via Engine's `team_aliases` table, season-matched to 2016
- **Source/domain:** `draft_facts` row, player_key `PFR:YounTa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200021 -- Which NFL team drafted A.J. McCarron?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5727)
- **Options:**
  0. Cincinnati Bengals **<- CORRECT**
  1. Baltimore Ravens
  2. San Francisco 49ers
  3. Tennessee Titans
- **Draft year:** 2014
- **Raw historical team code:** `CIN`
- **Resolved franchise:** `FR_CIN` ("Cincinnati Bengals"), resolved via Engine's `team_aliases` table, season-matched to 2014
- **Source/domain:** `draft_facts` row, player_key `PFR:McCaA.00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200022 -- Which NFL team drafted Joe Germaine?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6427)
- **Options:**
  0. St Louis Rams **<- CORRECT**
  1. Dallas Cowboys
  2. Miami Dolphins
  3. Seattle Seahawks
- **Draft year:** 1999
- **Raw historical team code:** `STL`
- **Resolved franchise:** `FR_LAR` ("St Louis Rams"), resolved via Engine's `team_aliases` table, season-matched to 1999
- **Source/domain:** `draft_facts` row, player_key `PFR:GermJo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200023 -- Which NFL team drafted Samuel Cosmi?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Washington Football Team **<- CORRECT**
  1. Minnesota Vikings
  2. Philadelphia Eagles
  3. Cleveland Browns
- **Draft year:** 2021
- **Raw historical team code:** `WAS`
- **Resolved franchise:** `FR_WAS` ("Washington Football Team"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:CosmSa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200024 -- Which NFL team drafted Chris Davis?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Seattle Seahawks **<- CORRECT**
  1. Washington Redskins
  2. Arizona Cardinals
  3. Atlanta Falcons
- **Draft year:** 2003
- **Raw historical team code:** `SEA`
- **Resolved franchise:** `FR_SEA` ("Seattle Seahawks"), resolved via Engine's `team_aliases` table, season-matched to 2003
- **Source/domain:** `draft_facts` row, player_key `PFR:DaviCh24`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200025 -- Which NFL team drafted Justin Fargas?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Cleveland Browns
  1. Kansas City Chiefs
  2. Minnesota Vikings
  3. Oakland Raiders **<- CORRECT**
- **Draft year:** 2003
- **Raw historical team code:** `OAK`
- **Resolved franchise:** `FR_LV` ("Oakland Raiders"), resolved via Engine's `team_aliases` table, season-matched to 2003
- **Source/domain:** `draft_facts` row, player_key `PFR:FargJu00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200026 -- Which NFL team drafted Ian Silberman?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Houston Texans
  1. Dallas Cowboys
  2. San Francisco 49ers **<- CORRECT**
  3. Chicago Bears
- **Draft year:** 2015
- **Raw historical team code:** `SF`
- **Resolved franchise:** `FR_SF` ("San Francisco 49ers"), resolved via Engine's `team_aliases` table, season-matched to 2015
- **Source/domain:** `draft_facts` row, player_key `PFR:SilbIa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200027 -- Which NFL team drafted Marvin Mitchell?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. New Orleans Saints **<- CORRECT**
  1. Minnesota Vikings
  2. Cincinnati Bengals
  3. New York Giants
- **Draft year:** 2007
- **Raw historical team code:** `NO`
- **Resolved franchise:** `FR_NO` ("New Orleans Saints"), resolved via Engine's `team_aliases` table, season-matched to 2007
- **Source/domain:** `draft_facts` row, player_key `PFR:MitcMa99`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200028 -- Which NFL team drafted Chase Pittman?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5447)
- **Options:**
  0. Cleveland Browns **<- CORRECT**
  1. Carolina Panthers
  2. Washington Redskins
  3. Atlanta Falcons
- **Draft year:** 2007
- **Raw historical team code:** `CLE`
- **Resolved franchise:** `FR_CLE` ("Cleveland Browns"), resolved via Engine's `team_aliases` table, season-matched to 2007
- **Source/domain:** `draft_facts` row, player_key `DRAFT:2007:213:CHASE_PITTMAN`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200029 -- Which NFL team drafted Rocky Klever?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Washington Redskins
  1. Denver Broncos
  2. New York Jets **<- CORRECT**
  3. Detroit Lions
- **Draft year:** 1982
- **Raw historical team code:** `NYJ`
- **Resolved franchise:** `FR_NYJ` ("New York Jets"), resolved via Engine's `team_aliases` table, season-matched to 1982
- **Source/domain:** `draft_facts` row, player_key `PFR:KlevRo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200030 -- Which NFL team drafted Jonathan Stewart?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6427)
- **Options:**
  0. Carolina Panthers **<- CORRECT**
  1. Chicago Bears
  2. Minnesota Vikings
  3. Washington Redskins
- **Draft year:** 2008
- **Raw historical team code:** `CAR`
- **Resolved franchise:** `FR_CAR` ("Carolina Panthers"), resolved via Engine's `team_aliases` table, season-matched to 2008
- **Source/domain:** `draft_facts` row, player_key `PFR:StewJo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200031 -- Which NFL team drafted Eddie Miller?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Dallas Cowboys
  1. Indianapolis Colts **<- CORRECT**
  2. San Francisco 49ers
  3. Kansas City Chiefs
- **Draft year:** 1992
- **Raw historical team code:** `IND`
- **Resolved franchise:** `FR_IND` ("Indianapolis Colts"), resolved via Engine's `team_aliases` table, season-matched to 1992
- **Source/domain:** `draft_facts` row, player_key `PFR:MillEd21`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200032 -- Which NFL team drafted Kenny King?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Dallas Cowboys
  1. Green Bay Packers
  2. Tennessee Titans
  3. Arizona Cardinals **<- CORRECT**
- **Draft year:** 2003
- **Raw historical team code:** `ARI`
- **Resolved franchise:** `FR_ARI` ("Arizona Cardinals"), resolved via Engine's `team_aliases` table, season-matched to 2003
- **Source/domain:** `draft_facts` row, player_key `PFR:KingKe20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200033 -- Which NFL team drafted Deebo Samuel?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Indianapolis Colts
  1. Tampa Bay Buccaneers
  2. Philadelphia Eagles
  3. San Francisco 49ers **<- CORRECT**
- **Draft year:** 2019
- **Raw historical team code:** `SF`
- **Resolved franchise:** `FR_SF` ("San Francisco 49ers"), resolved via Engine's `team_aliases` table, season-matched to 2019
- **Source/domain:** `draft_facts` row, player_key `PFR:SamuDe00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200034 -- Which NFL team drafted Ricky Wagner?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. Baltimore Ravens **<- CORRECT**
  1. Buffalo Bills
  2. Atlanta Falcons
  3. Miami Dolphins
- **Draft year:** 2013
- **Raw historical team code:** `BAL`
- **Resolved franchise:** `FR_BAL` ("Baltimore Ravens"), resolved via Engine's `team_aliases` table, season-matched to 2013
- **Source/domain:** `draft_facts` row, player_key `PFR:WagnRi00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200035 -- Which NFL team drafted Paul Lankford?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Miami Dolphins **<- CORRECT**
  1. Pittsburgh Steelers
  2. New England Patriots
  3. Denver Broncos
- **Draft year:** 1982
- **Raw historical team code:** `MIA`
- **Resolved franchise:** `FR_MIA` ("Miami Dolphins"), resolved via Engine's `team_aliases` table, season-matched to 1982
- **Source/domain:** `draft_facts` row, player_key `PFR:LankPa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200036 -- Which NFL team drafted Kinnon Tatum?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Carolina Panthers **<- CORRECT**
  1. Seattle Seahawks
  2. Chicago Bears
  3. Pittsburgh Steelers
- **Draft year:** 1997
- **Raw historical team code:** `CAR`
- **Resolved franchise:** `FR_CAR` ("Carolina Panthers"), resolved via Engine's `team_aliases` table, season-matched to 1997
- **Source/domain:** `draft_facts` row, player_key `PFR:TatuKi20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200037 -- Which NFL team drafted Onterrio Smith?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Cincinnati Bengals
  1. Oakland Raiders
  2. Indianapolis Colts
  3. Minnesota Vikings **<- CORRECT**
- **Draft year:** 2003
- **Raw historical team code:** `MIN`
- **Resolved franchise:** `FR_MIN` ("Minnesota Vikings"), resolved via Engine's `team_aliases` table, season-matched to 2003
- **Source/domain:** `draft_facts` row, player_key `PFR:SmitOn00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200038 -- Which NFL team drafted Kris Mangum?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5867)
- **Options:**
  0. Jacksonville Jaguars
  1. Arizona Cardinals
  2. Carolina Panthers **<- CORRECT**
  3. New York Jets
- **Draft year:** 1997
- **Raw historical team code:** `CAR`
- **Resolved franchise:** `FR_CAR` ("Carolina Panthers"), resolved via Engine's `team_aliases` table, season-matched to 1997
- **Source/domain:** `draft_facts` row, player_key `PFR:MangKr00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200039 -- Which NFL team drafted Aaron Brant?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6707)
- **Options:**
  0. Chicago Bears **<- CORRECT**
  1. Miami Dolphins
  2. Minnesota Vikings
  3. New York Jets
- **Draft year:** 2007
- **Raw historical team code:** `CHI`
- **Resolved franchise:** `FR_CHI` ("Chicago Bears"), resolved via Engine's `team_aliases` table, season-matched to 2007
- **Source/domain:** `draft_facts` row, player_key `DRAFT:2007:241:AARON_BRANT`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200040 -- Which NFL team drafted Armonty Bryant?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Cleveland Browns **<- CORRECT**
  1. Carolina Panthers
  2. Indianapolis Colts
  3. Chicago Bears
- **Draft year:** 2013
- **Raw historical team code:** `CLE`
- **Resolved franchise:** `FR_CLE` ("Cleveland Browns"), resolved via Engine's `team_aliases` table, season-matched to 2013
- **Source/domain:** `draft_facts` row, player_key `PFR:BryaAr00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200041 -- Which NFL team drafted Frank Walker?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6847)
- **Options:**
  0. Carolina Panthers
  1. Houston Texans
  2. New York Giants **<- CORRECT**
  3. Detroit Lions
- **Draft year:** 2003
- **Raw historical team code:** `NYG`
- **Resolved franchise:** `FR_NYG` ("New York Giants"), resolved via Engine's `team_aliases` table, season-matched to 2003
- **Source/domain:** `draft_facts` row, player_key `PFR:WalkFr20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200042 -- Which NFL team drafted Saquan Hampton?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. New Orleans Saints **<- CORRECT**
  1. Washington Redskins
  2. Seattle Seahawks
  3. New England Patriots
- **Draft year:** 2019
- **Raw historical team code:** `NO`
- **Resolved franchise:** `FR_NO` ("New Orleans Saints"), resolved via Engine's `team_aliases` table, season-matched to 2019
- **Source/domain:** `draft_facts` row, player_key `PFR:HampSa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200043 -- Which NFL team drafted Godfrey Myles?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6427)
- **Options:**
  0. Dallas Cowboys **<- CORRECT**
  1. New York Jets
  2. Detroit Lions
  3. Buffalo Bills
- **Draft year:** 1991
- **Raw historical team code:** `DAL`
- **Resolved franchise:** `FR_DAL` ("Dallas Cowboys"), resolved via Engine's `team_aliases` table, season-matched to 1991
- **Source/domain:** `draft_facts` row, player_key `PFR:MyleGo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200044 -- Which NFL team drafted Daniel Sepulveda?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. New York Jets
  1. Jacksonville Jaguars
  2. San Diego Chargers
  3. Pittsburgh Steelers **<- CORRECT**
- **Draft year:** 2007
- **Raw historical team code:** `PIT`
- **Resolved franchise:** `FR_PIT` ("Pittsburgh Steelers"), resolved via Engine's `team_aliases` table, season-matched to 2007
- **Source/domain:** `draft_facts` row, player_key `PFR:SepuDa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200045 -- Which NFL team drafted Dave Stachelski?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5867)
- **Options:**
  0. Carolina Panthers
  1. Atlanta Falcons
  2. New England Patriots **<- CORRECT**
  3. Denver Broncos
- **Draft year:** 2000
- **Raw historical team code:** `NE`
- **Resolved franchise:** `FR_NE` ("New England Patriots"), resolved via Engine's `team_aliases` table, season-matched to 2000
- **Source/domain:** `draft_facts` row, player_key `PFR:StacDa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200046 -- Which NFL team drafted Keith Williams?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Cleveland Browns
  1. New England Patriots
  2. Pittsburgh Steelers
  3. Atlanta Falcons **<- CORRECT**
- **Draft year:** 1986
- **Raw historical team code:** `ATL`
- **Resolved franchise:** `FR_ATL` ("Atlanta Falcons"), resolved via Engine's `team_aliases` table, season-matched to 1986
- **Source/domain:** `draft_facts` row, player_key `PFR:WillKe01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200047 -- Which NFL team drafted Bob Holly?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Washington Redskins **<- CORRECT**
  1. New Orleans Saints
  2. New England Patriots
  3. Miami Dolphins
- **Draft year:** 1982
- **Raw historical team code:** `WAS`
- **Resolved franchise:** `FR_WAS` ("Washington Redskins"), resolved via Engine's `team_aliases` table, season-matched to 1982
- **Source/domain:** `draft_facts` row, player_key `PFR:HollBo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200048 -- Which NFL team drafted Jamaal Anderson?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Denver Broncos
  1. Philadelphia Eagles
  2. Miami Dolphins
  3. Atlanta Falcons **<- CORRECT**
- **Draft year:** 2007
- **Raw historical team code:** `ATL`
- **Resolved franchise:** `FR_ATL` ("Atlanta Falcons"), resolved via Engine's `team_aliases` table, season-matched to 2007
- **Source/domain:** `draft_facts` row, player_key `PFR:AndeJa98`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200049 -- Which NFL team drafted Quinton Reese?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5727)
- **Options:**
  0. Cleveland Browns
  1. Detroit Lions **<- CORRECT**
  2. New England Patriots
  3. Minnesota Vikings
- **Draft year:** 2000
- **Raw historical team code:** `DET`
- **Resolved franchise:** `FR_DET` ("Detroit Lions"), resolved via Engine's `team_aliases` table, season-matched to 2000
- **Source/domain:** `draft_facts` row, player_key `DRAFT:2000:181:QUINTON_REESE`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200050 -- Which NFL team drafted Gerome Sapp?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Baltimore Ravens **<- CORRECT**
  1. Tampa Bay Buccaneers
  2. Minnesota Vikings
  3. New England Patriots
- **Draft year:** 2003
- **Raw historical team code:** `BAL`
- **Resolved franchise:** `FR_BAL` ("Baltimore Ravens"), resolved via Engine's `team_aliases` table, season-matched to 2003
- **Source/domain:** `draft_facts` row, player_key `PFR:SappGe20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200051 -- Which NFL team drafted John Parrella?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `EXPERT`, score 0.8247)
- **Options:**
  0. San Francisco 49ers
  1. New York Jets
  2. Miami Dolphins
  3. Buffalo Bills **<- CORRECT**
- **Draft year:** 1993
- **Raw historical team code:** `BUF`
- **Resolved franchise:** `FR_BUF` ("Buffalo Bills"), resolved via Engine's `team_aliases` table, season-matched to 1993
- **Source/domain:** `draft_facts` row, player_key `PFR:ParrJo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200052 -- Which NFL team drafted Cody Mauch?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4467)
- **Options:**
  0. New Orleans Saints
  1. Tampa Bay Buccaneers **<- CORRECT**
  2. New England Patriots
  3. Green Bay Packers
- **Draft year:** 2023
- **Raw historical team code:** `TB`
- **Resolved franchise:** `FR_TB` ("Tampa Bay Buccaneers"), resolved via Engine's `team_aliases` table, season-matched to 2023
- **Source/domain:** `draft_facts` row, player_key `PFR:MaucCo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200053 -- Which NFL team drafted Ron Pitts?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6007)
- **Options:**
  0. New Orleans Saints
  1. Buffalo Bills **<- CORRECT**
  2. San Francisco 49ers
  3. Cincinnati Bengals
- **Draft year:** 1985
- **Raw historical team code:** `BUF`
- **Resolved franchise:** `FR_BUF` ("Buffalo Bills"), resolved via Engine's `team_aliases` table, season-matched to 1985
- **Source/domain:** `draft_facts` row, player_key `PFR:PittRo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200054 -- Which NFL team drafted Brandon Carr?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5727)
- **Options:**
  0. Buffalo Bills
  1. San Diego Chargers
  2. Kansas City Chiefs **<- CORRECT**
  3. Cleveland Browns
- **Draft year:** 2008
- **Raw historical team code:** `KC`
- **Resolved franchise:** `FR_KC` ("Kansas City Chiefs"), resolved via Engine's `team_aliases` table, season-matched to 2008
- **Source/domain:** `draft_facts` row, player_key `PFR:CarrBr99`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200055 -- Which NFL team drafted Andre Maddox?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Arizona Cardinals
  1. Washington Redskins
  2. New York Jets **<- CORRECT**
  3. Houston Texans
- **Draft year:** 2005
- **Raw historical team code:** `NYJ`
- **Resolved franchise:** `FR_NYJ` ("New York Jets"), resolved via Engine's `team_aliases` table, season-matched to 2005
- **Source/domain:** `draft_facts` row, player_key `DRAFT:2005:161:ANDRE_MADDOX`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200056 -- Which NFL team drafted Dez White?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6567)
- **Options:**
  0. Miami Dolphins
  1. Chicago Bears **<- CORRECT**
  2. Cleveland Browns
  3. Indianapolis Colts
- **Draft year:** 2000
- **Raw historical team code:** `CHI`
- **Resolved franchise:** `FR_CHI` ("Chicago Bears"), resolved via Engine's `team_aliases` table, season-matched to 2000
- **Source/domain:** `draft_facts` row, player_key `PFR:WhitDe00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200057 -- Which NFL team drafted Trayvon Mullen?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Oakland Raiders **<- CORRECT**
  1. Pittsburgh Steelers
  2. Seattle Seahawks
  3. Tennessee Titans
- **Draft year:** 2019
- **Raw historical team code:** `OAK`
- **Resolved franchise:** `FR_LV` ("Oakland Raiders"), resolved via Engine's `team_aliases` table, season-matched to 2019
- **Source/domain:** `draft_facts` row, player_key `PFR:MullTr00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200058 -- Which NFL team drafted Ralph Giacomarro?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `EXPERT`, score 0.7127)
- **Options:**
  0. Green Bay Packers
  1. Atlanta Falcons **<- CORRECT**
  2. New York Jets
  3. New Orleans Saints
- **Draft year:** 1983
- **Raw historical team code:** `ATL`
- **Resolved franchise:** `FR_ATL` ("Atlanta Falcons"), resolved via Engine's `team_aliases` table, season-matched to 1983
- **Source/domain:** `draft_facts` row, player_key `PFR:GiacRa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200059 -- Which NFL team drafted Ronnie Burgess?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Atlanta Falcons
  1. Green Bay Packers **<- CORRECT**
  2. Seattle Seahawks
  3. New York Jets
- **Draft year:** 1985
- **Raw historical team code:** `GB`
- **Resolved franchise:** `FR_GB` ("Green Bay Packers"), resolved via Engine's `team_aliases` table, season-matched to 1985
- **Source/domain:** `draft_facts` row, player_key `PFR:BurgRo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200060 -- Which NFL team drafted Deon Figures?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4467)
- **Options:**
  0. Pittsburgh Steelers **<- CORRECT**
  1. Seattle Seahawks
  2. Miami Dolphins
  3. Washington Redskins
- **Draft year:** 1993
- **Raw historical team code:** `PIT`
- **Resolved franchise:** `FR_PIT` ("Pittsburgh Steelers"), resolved via Engine's `team_aliases` table, season-matched to 1993
- **Source/domain:** `draft_facts` row, player_key `PFR:FiguDe20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200061 -- Which NFL team drafted Thomas Wilcher?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5447)
- **Options:**
  0. San Diego Chargers **<- CORRECT**
  1. Washington Redskins
  2. New York Giants
  3. Tampa Bay Buccaneers
- **Draft year:** 1987
- **Raw historical team code:** `SD`
- **Resolved franchise:** `FR_LAC` ("San Diego Chargers"), resolved via Engine's `team_aliases` table, season-matched to 1987
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1987:226:THOMAS_WILCHER`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200062 -- Which NFL team drafted Jason Pinkston?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6147)
- **Options:**
  0. Philadelphia Eagles
  1. Kansas City Chiefs
  2. New Orleans Saints
  3. Cleveland Browns **<- CORRECT**
- **Draft year:** 2011
- **Raw historical team code:** `CLE`
- **Resolved franchise:** `FR_CLE` ("Cleveland Browns"), resolved via Engine's `team_aliases` table, season-matched to 2011
- **Source/domain:** `draft_facts` row, player_key `PFR:PinkJa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200063 -- Which NFL team drafted Derrick Gibson?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6287)
- **Options:**
  0. Miami Dolphins
  1. Denver Broncos
  2. Oakland Raiders **<- CORRECT**
  3. San Diego Chargers
- **Draft year:** 2001
- **Raw historical team code:** `OAK`
- **Resolved franchise:** `FR_LV` ("Oakland Raiders"), resolved via Engine's `team_aliases` table, season-matched to 2001
- **Source/domain:** `draft_facts` row, player_key `PFR:GibsDe21`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200064 -- Which NFL team drafted Jeremiah Pharms?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Arizona Cardinals
  1. Denver Broncos
  2. Miami Dolphins
  3. Cleveland Browns **<- CORRECT**
- **Draft year:** 2001
- **Raw historical team code:** `CLE`
- **Resolved franchise:** `FR_CLE` ("Cleveland Browns"), resolved via Engine's `team_aliases` table, season-matched to 2001
- **Source/domain:** `draft_facts` row, player_key `DRAFT:2001:134:JEREMIAH_PHARMS`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200065 -- Which NFL team drafted Carlos Rogers?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6987)
- **Options:**
  0. Buffalo Bills
  1. Indianapolis Colts
  2. Chicago Bears
  3. Washington Redskins **<- CORRECT**
- **Draft year:** 2005
- **Raw historical team code:** `WAS`
- **Resolved franchise:** `FR_WAS` ("Washington Redskins"), resolved via Engine's `team_aliases` table, season-matched to 2005
- **Source/domain:** `draft_facts` row, player_key `PFR:RogeCa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200066 -- Which NFL team drafted Jordan Kent?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Seattle Seahawks **<- CORRECT**
  1. St Louis Rams
  2. New Orleans Saints
  3. Kansas City Chiefs
- **Draft year:** 2007
- **Raw historical team code:** `SEA`
- **Resolved franchise:** `FR_SEA` ("Seattle Seahawks"), resolved via Engine's `team_aliases` table, season-matched to 2007
- **Source/domain:** `draft_facts` row, player_key `PFR:KentJo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200067 -- Which NFL team drafted Bruce McGonnigal?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6287)
- **Options:**
  0. Cleveland Browns
  1. Pittsburgh Steelers **<- CORRECT**
  2. Detroit Lions
  3. New England Patriots
- **Draft year:** 1991
- **Raw historical team code:** `PIT`
- **Resolved franchise:** `FR_PIT` ("Pittsburgh Steelers"), resolved via Engine's `team_aliases` table, season-matched to 1991
- **Source/domain:** `draft_facts` row, player_key `PFR:McGoBr20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200068 -- Which NFL team drafted Kevin Carter?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6987)
- **Options:**
  0. Seattle Seahawks
  1. Tampa Bay Buccaneers
  2. St Louis Rams **<- CORRECT**
  3. Buffalo Bills
- **Draft year:** 1995
- **Raw historical team code:** `STL`
- **Resolved franchise:** `FR_LAR` ("St Louis Rams"), resolved via Engine's `team_aliases` table, season-matched to 1995
- **Source/domain:** `draft_facts` row, player_key `PFR:CartKe00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200069 -- Which NFL team drafted Shawn Wilbourn?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `EXPERT`, score 0.8247)
- **Options:**
  0. Miami Dolphins
  1. Washington Redskins
  2. Detroit Lions
  3. Buffalo Bills **<- CORRECT**
- **Draft year:** 1991
- **Raw historical team code:** `BUF`
- **Resolved franchise:** `FR_BUF` ("Buffalo Bills"), resolved via Engine's `team_aliases` table, season-matched to 1991
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1991:138:SHAWN_WILBOURN`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200070 -- Which NFL team drafted Brandon Keith?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Arizona Cardinals **<- CORRECT**
  1. Denver Broncos
  2. Houston Texans
  3. Buffalo Bills
- **Draft year:** 2008
- **Raw historical team code:** `ARI`
- **Resolved franchise:** `FR_ARI` ("Arizona Cardinals"), resolved via Engine's `team_aliases` table, season-matched to 2008
- **Source/domain:** `draft_facts` row, player_key `PFR:KeitBr20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200071 -- Which NFL team drafted Kade Weston?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6287)
- **Options:**
  0. Baltimore Ravens
  1. Arizona Cardinals
  2. New England Patriots **<- CORRECT**
  3. Green Bay Packers
- **Draft year:** 2010
- **Raw historical team code:** `NE`
- **Resolved franchise:** `FR_NE` ("New England Patriots"), resolved via Engine's `team_aliases` table, season-matched to 2010
- **Source/domain:** `draft_facts` row, player_key `DRAFT:2010:248:KADE_WESTON`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200072 -- Which NFL team drafted John Ford?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `EXPERT`, score 0.7967)
- **Options:**
  0. Indianapolis Colts
  1. Miami Dolphins
  2. Chicago Bears
  3. Detroit Lions **<- CORRECT**
- **Draft year:** 1989
- **Raw historical team code:** `DET`
- **Resolved franchise:** `FR_DET` ("Detroit Lions"), resolved via Engine's `team_aliases` table, season-matched to 1989
- **Source/domain:** `draft_facts` row, player_key `PFR:FordJo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200073 -- Which NFL team drafted Tom Daniel?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. New Orleans Saints
  1. Minnesota Vikings
  2. Tampa Bay Buccaneers
  3. New England Patriots **<- CORRECT**
- **Draft year:** 1980
- **Raw historical team code:** `NE`
- **Resolved franchise:** `FR_NE` ("New England Patriots"), resolved via Engine's `team_aliases` table, season-matched to 1980
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1980:266:TOM_DANIEL`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200074 -- Which NFL team drafted Jermaine Gresham?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Oakland Raiders
  1. Miami Dolphins
  2. Chicago Bears
  3. Cincinnati Bengals **<- CORRECT**
- **Draft year:** 2010
- **Raw historical team code:** `CIN`
- **Resolved franchise:** `FR_CIN` ("Cincinnati Bengals"), resolved via Engine's `team_aliases` table, season-matched to 2010
- **Source/domain:** `draft_facts` row, player_key `PFR:GresJe00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200075 -- Which NFL team drafted Mark Berry?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6427)
- **Options:**
  0. Chicago Bears **<- CORRECT**
  1. Dallas Cowboys
  2. Pittsburgh Steelers
  3. Minnesota Vikings
- **Draft year:** 1992
- **Raw historical team code:** `CHI`
- **Resolved franchise:** `FR_CHI` ("Chicago Bears"), resolved via Engine's `team_aliases` table, season-matched to 1992
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1992:161:MARK_BERRY`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200076 -- Which NFL team drafted Jalston Fowler?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. St Louis Rams
  1. Denver Broncos
  2. Tennessee Titans **<- CORRECT**
  3. Dallas Cowboys
- **Draft year:** 2015
- **Raw historical team code:** `TEN`
- **Resolved franchise:** `FR_TEN` ("Tennessee Titans"), resolved via Engine's `team_aliases` table, season-matched to 2015
- **Source/domain:** `draft_facts` row, player_key `PFR:FowlJa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200077 -- Which NFL team drafted Brandon Tolbert?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Kansas City Chiefs
  1. Philadelphia Eagles
  2. Tennessee Titans
  3. Jacksonville Jaguars **<- CORRECT**
- **Draft year:** 1998
- **Raw historical team code:** `JAX`
- **Resolved franchise:** `FR_JAX` ("Jacksonville Jaguars"), resolved via Engine's `team_aliases` table, season-matched to 1998
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1998:214:BRANDON_TOLBERT`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200078 -- Which NFL team drafted Ben Jones?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Atlanta Falcons
  1. Houston Texans **<- CORRECT**
  2. Washington Redskins
  3. Arizona Cardinals
- **Draft year:** 2012
- **Raw historical team code:** `HOU`
- **Resolved franchise:** `FR_HOU` ("Houston Texans"), resolved via Engine's `team_aliases` table, season-matched to 2012
- **Source/domain:** `draft_facts` row, player_key `PFR:JoneBe01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200079 -- Which NFL team drafted Victor Dimukeje?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Carolina Panthers
  1. Arizona Cardinals **<- CORRECT**
  2. Atlanta Falcons
  3. Philadelphia Eagles
- **Draft year:** 2021
- **Raw historical team code:** `ARI`
- **Resolved franchise:** `FR_ARI` ("Arizona Cardinals"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:DimuVi00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200080 -- Which NFL team drafted Dave Piepkorn?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Green Bay Packers
  1. San Diego Chargers
  2. New York Jets
  3. Cleveland Browns **<- CORRECT**
- **Draft year:** 1984
- **Raw historical team code:** `CLE`
- **Resolved franchise:** `FR_CLE` ("Cleveland Browns"), resolved via Engine's `team_aliases` table, season-matched to 1984
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1984:131:DAVE_PIEPKORN`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200081 -- Which NFL team drafted Justin Jackson?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Los Angeles Chargers **<- CORRECT**
  1. Miami Dolphins
  2. Pittsburgh Steelers
  3. Oakland Raiders
- **Draft year:** 2018
- **Raw historical team code:** `LAC`
- **Resolved franchise:** `FR_LAC` ("Los Angeles Chargers"), resolved via Engine's `team_aliases` table, season-matched to 2018
- **Source/domain:** `draft_facts` row, player_key `PFR:JackJu01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200082 -- Which NFL team drafted Aaron Jones?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `EXPERT`, score 0.8247)
- **Options:**
  0. Seattle Seahawks
  1. Philadelphia Eagles
  2. Pittsburgh Steelers **<- CORRECT**
  3. Detroit Lions
- **Draft year:** 1988
- **Raw historical team code:** `PIT`
- **Resolved franchise:** `FR_PIT` ("Pittsburgh Steelers"), resolved via Engine's `team_aliases` table, season-matched to 1988
- **Source/domain:** `draft_facts` row, player_key `PFR:JoneAa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200083 -- Which NFL team drafted Kevin Harris?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Seattle Seahawks
  1. Detroit Lions **<- CORRECT**
  2. Miami Dolphins
  3. New York Giants
- **Draft year:** 1985
- **Raw historical team code:** `DET`
- **Resolved franchise:** `FR_DET` ("Detroit Lions"), resolved via Engine's `team_aliases` table, season-matched to 1985
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1985:286:KEVIN_HARRIS`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200084 -- Which NFL team drafted Isaiah Buggs?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. New York Jets
  1. Baltimore Ravens
  2. Pittsburgh Steelers **<- CORRECT**
  3. Oakland Raiders
- **Draft year:** 2019
- **Raw historical team code:** `PIT`
- **Resolved franchise:** `FR_PIT` ("Pittsburgh Steelers"), resolved via Engine's `team_aliases` table, season-matched to 2019
- **Source/domain:** `draft_facts` row, player_key `PFR:BuggIs00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200085 -- Which NFL team drafted Mike Gesicki?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Los Angeles Chargers
  1. New Orleans Saints
  2. Denver Broncos
  3. Miami Dolphins **<- CORRECT**
- **Draft year:** 2018
- **Raw historical team code:** `MIA`
- **Resolved franchise:** `FR_MIA` ("Miami Dolphins"), resolved via Engine's `team_aliases` table, season-matched to 2018
- **Source/domain:** `draft_facts` row, player_key `PFR:GesiMi00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200086 -- Which NFL team drafted Brad White?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5727)
- **Options:**
  0. Seattle Seahawks
  1. Denver Broncos
  2. Tampa Bay Buccaneers **<- CORRECT**
  3. Kansas City Chiefs
- **Draft year:** 1981
- **Raw historical team code:** `TB`
- **Resolved franchise:** `FR_TB` ("Tampa Bay Buccaneers"), resolved via Engine's `team_aliases` table, season-matched to 1981
- **Source/domain:** `draft_facts` row, player_key `PFR:WhitBr20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200087 -- Which NFL team drafted Baron Browning?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Denver Broncos **<- CORRECT**
  1. Green Bay Packers
  2. Pittsburgh Steelers
  3. New Orleans Saints
- **Draft year:** 2021
- **Raw historical team code:** `DEN`
- **Resolved franchise:** `FR_DEN` ("Denver Broncos"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:BrowBa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200088 -- Which NFL team drafted Jerraud Powers?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6147)
- **Options:**
  0. Pittsburgh Steelers
  1. New York Jets
  2. New Orleans Saints
  3. Indianapolis Colts **<- CORRECT**
- **Draft year:** 2009
- **Raw historical team code:** `IND`
- **Resolved franchise:** `FR_IND` ("Indianapolis Colts"), resolved via Engine's `team_aliases` table, season-matched to 2009
- **Source/domain:** `draft_facts` row, player_key `PFR:PoweJe99`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200089 -- Which NFL team drafted Keith Chappelle?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6567)
- **Options:**
  0. Atlanta Falcons **<- CORRECT**
  1. Kansas City Chiefs
  2. Tampa Bay Buccaneers
  3. Minnesota Vikings
- **Draft year:** 1981
- **Raw historical team code:** `ATL`
- **Resolved franchise:** `FR_ATL` ("Atlanta Falcons"), resolved via Engine's `team_aliases` table, season-matched to 1981
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1981:301:KEITH_CHAPPELLE`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200090 -- Which NFL team drafted Ifeatu Melifonwu?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Carolina Panthers
  1. Chicago Bears
  2. Baltimore Ravens
  3. Detroit Lions **<- CORRECT**
- **Draft year:** 2021
- **Raw historical team code:** `DET`
- **Resolved franchise:** `FR_DET` ("Detroit Lions"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:MeliIf00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200091 -- Which NFL team drafted Brian Hill?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Chicago Bears
  1. Buffalo Bills
  2. Green Bay Packers
  3. Atlanta Falcons **<- CORRECT**
- **Draft year:** 2017
- **Raw historical team code:** `ATL`
- **Resolved franchise:** `FR_ATL` ("Atlanta Falcons"), resolved via Engine's `team_aliases` table, season-matched to 2017
- **Source/domain:** `draft_facts` row, player_key `PFR:HillBr02`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200092 -- Which NFL team drafted Trey Taylor?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Las Vegas Raiders **<- CORRECT**
  1. Los Angeles Rams
  2. Carolina Panthers
  3. Green Bay Packers
- **Draft year:** 2024
- **Raw historical team code:** `LV`
- **Resolved franchise:** `FR_LV` ("Las Vegas Raiders"), resolved via Engine's `team_aliases` table, season-matched to 2024
- **Source/domain:** `draft_facts` row, player_key `PFR:TaylTr03`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200093 -- Which NFL team drafted Don Gibson?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Denver Broncos **<- CORRECT**
  1. Green Bay Packers
  2. San Diego Chargers
  3. Tampa Bay Buccaneers
- **Draft year:** 1991
- **Raw historical team code:** `DEN`
- **Resolved franchise:** `FR_DEN` ("Denver Broncos"), resolved via Engine's `team_aliases` table, season-matched to 1991
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1991:227:DON_GIBSON`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200094 -- Which NFL team drafted John Ionata?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4467)
- **Options:**
  0. New York Giants
  1. Indianapolis Colts
  2. Dallas Cowboys **<- CORRECT**
  3. Kansas City Chiefs
- **Draft year:** 1986
- **Raw historical team code:** `DAL`
- **Resolved franchise:** `FR_DAL` ("Dallas Cowboys"), resolved via Engine's `team_aliases` table, season-matched to 1986
- **Source/domain:** `draft_facts` row, player_key `DRAFT:1986:242:JOHN_IONATA`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200095 -- Which NFL team drafted Lorenzo Bromell?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Tennessee Titans
  1. Denver Broncos
  2. Miami Dolphins **<- CORRECT**
  3. Kansas City Chiefs
- **Draft year:** 1998
- **Raw historical team code:** `MIA`
- **Resolved franchise:** `FR_MIA` ("Miami Dolphins"), resolved via Engine's `team_aliases` table, season-matched to 1998
- **Source/domain:** `draft_facts` row, player_key `PFR:BromLo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200096 -- Which NFL team drafted Brenden Jaimes?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Washington Football Team
  1. Detroit Lions
  2. Carolina Panthers
  3. Los Angeles Chargers **<- CORRECT**
- **Draft year:** 2021
- **Raw historical team code:** `LAC`
- **Resolved franchise:** `FR_LAC` ("Los Angeles Chargers"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:JaimBr00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200097 -- Which NFL team drafted Ernest Spears?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5727)
- **Options:**
  0. Miami Dolphins
  1. Kansas City Chiefs
  2. Buffalo Bills
  3. New Orleans Saints **<- CORRECT**
- **Draft year:** 1990
- **Raw historical team code:** `NO`
- **Resolved franchise:** `FR_NO` ("New Orleans Saints"), resolved via Engine's `team_aliases` table, season-matched to 1990
- **Source/domain:** `draft_facts` row, player_key `PFR:SpeaEr20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200098 -- Which NFL team drafted Anthony Malbrough?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Cleveland Browns **<- CORRECT**
  1. Washington Redskins
  2. Green Bay Packers
  3. Seattle Seahawks
- **Draft year:** 2000
- **Raw historical team code:** `CLE`
- **Resolved franchise:** `FR_CLE` ("Cleveland Browns"), resolved via Engine's `team_aliases` table, season-matched to 2000
- **Source/domain:** `draft_facts` row, player_key `PFR:MalbAn20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #200099 -- Which NFL team drafted Patrick Surtain II?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Seattle Seahawks
  1. Denver Broncos **<- CORRECT**
  2. Baltimore Ravens
  3. Detroit Lions
- **Draft year:** 2021
- **Raw historical team code:** `DEN`
- **Resolved franchise:** `FR_DEN` ("Denver Broncos"), resolved via Engine's `team_aliases` table, season-matched to 2021
- **Source/domain:** `draft_facts` row, player_key `PFR:SurtPa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

