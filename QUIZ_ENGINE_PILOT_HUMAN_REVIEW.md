# Quiz Engine Pilot -- Human Review Package

Regenerated from the same deterministic pipeline as `tools/export_quiz_engine_pilot.py` (seed `reads-quiz-engine-pilot-v1`) and verified byte-identical, field-by-field, against the already-written `data/quiz-engine-pilot.js` before this document was produced. No question text, option, or answer was altered to produce this report.

## Summary

- Total questions: **50**
- Difficulty split: Hard 33, Medium 17
- Unique players: **50**
- Unique franchises represented: **29** / 32
- Draft-year range: **2002-2024**
- Category: NFL Draft History (all 50)
- Underlying Engine source/domain: `draft_facts` table, domain `NFL_DRAFT`, source `NFLVERSE_DATA`

---

## #100000 -- Which NFL team drafted Isaiah Ford?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Los Angeles Rams
  1. New Orleans Saints
  2. Miami Dolphins **<- CORRECT**
  3. Cleveland Browns
- **Draft year / source context:** Isaiah Ford was drafted in the **2017** NFL Draft by team code `MIA`, resolved to franchise `FR_MIA` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:FordIs00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100001 -- Which NFL team drafted Jaylen Twyman?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Minnesota Vikings **<- CORRECT**
  1. Detroit Lions
  2. Miami Dolphins
  3. Tampa Bay Buccaneers
- **Draft year / source context:** Jaylen Twyman was drafted in the **2021** NFL Draft by team code `MIN`, resolved to franchise `FR_MIN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:TwymJa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100002 -- Which NFL team drafted Hayden Epstein?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6567)
- **Options:**
  0. Atlanta Falcons
  1. Jacksonville Jaguars **<- CORRECT**
  2. Buffalo Bills
  3. Cleveland Browns
- **Draft year / source context:** Hayden Epstein was drafted in the **2002** NFL Draft by team code `JAX`, resolved to franchise `FR_JAX` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:epstehay01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100003 -- Which NFL team drafted James Lee?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6427)
- **Options:**
  0. New England Patriots
  1. Green Bay Packers **<- CORRECT**
  2. St Louis Rams
  3. Arizona Cardinals
- **Draft year / source context:** James Lee was drafted in the **2003** NFL Draft by team code `GB`, resolved to franchise `FR_GB` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:LeexJa21`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100004 -- Which NFL team drafted Darius Slayton?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Arizona Cardinals
  1. Detroit Lions
  2. New York Giants **<- CORRECT**
  3. Seattle Seahawks
- **Draft year / source context:** Darius Slayton was drafted in the **2019** NFL Draft by team code `NYG`, resolved to franchise `FR_NYG` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:SlayDa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100005 -- Which NFL team drafted Johnnie Lee Higgins?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6147)
- **Options:**
  0. Minnesota Vikings
  1. Detroit Lions
  2. Oakland Raiders **<- CORRECT**
  3. St Louis Rams
- **Draft year / source context:** Johnnie Lee Higgins was drafted in the **2007** NFL Draft by team code `OAK`, resolved to franchise `FR_LV` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:HiggJo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100006 -- Which NFL team drafted John Greco?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5867)
- **Options:**
  0. Denver Broncos
  1. Arizona Cardinals
  2. Houston Texans
  3. St Louis Rams **<- CORRECT**
- **Draft year / source context:** John Greco was drafted in the **2008** NFL Draft by team code `STL`, resolved to franchise `FR_LAR` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:GrecJo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100007 -- Which NFL team drafted Maurice Rodriguez?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. Minnesota Vikings
  1. St Louis Rams
  2. Denver Broncos
  3. Kansas City Chiefs **<- CORRECT**
- **Draft year / source context:** Maurice Rodriguez was drafted in the **2002** NFL Draft by team code `KC`, resolved to franchise `FR_KC` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `DRAFT:2002:221:MAURICE_RODRIGUEZ`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100008 -- Which NFL team drafted Tyree Gillespie?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Kansas City Chiefs
  1. Pittsburgh Steelers
  2. New England Patriots
  3. Las Vegas Raiders **<- CORRECT**
- **Draft year / source context:** Tyree Gillespie was drafted in the **2021** NFL Draft by team code `LV`, resolved to franchise `FR_LV` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:GillTy00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100009 -- Which NFL team drafted Tavon Young?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5447)
- **Options:**
  0. Indianapolis Colts
  1. Baltimore Ravens **<- CORRECT**
  2. Philadelphia Eagles
  3. Pittsburgh Steelers
- **Draft year / source context:** Tavon Young was drafted in the **2016** NFL Draft by team code `BAL`, resolved to franchise `FR_BAL` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:YounTa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100010 -- Which NFL team drafted A.J. McCarron?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5727)
- **Options:**
  0. Carolina Panthers
  1. New York Giants
  2. Cincinnati Bengals **<- CORRECT**
  3. Washington Redskins
- **Draft year / source context:** A.J. McCarron was drafted in the **2014** NFL Draft by team code `CIN`, resolved to franchise `FR_CIN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:McCaA.00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100011 -- Which NFL team drafted Samuel Cosmi?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Denver Broncos
  1. Miami Dolphins
  2. Washington Football Team **<- CORRECT**
  3. Indianapolis Colts
- **Draft year / source context:** Samuel Cosmi was drafted in the **2021** NFL Draft by team code `WAS`, resolved to franchise `FR_WAS` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:CosmSa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100012 -- Which NFL team drafted Chris Davis?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Green Bay Packers
  1. San Diego Chargers
  2. Seattle Seahawks **<- CORRECT**
  3. New Orleans Saints
- **Draft year / source context:** Chris Davis was drafted in the **2003** NFL Draft by team code `SEA`, resolved to franchise `FR_SEA` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:DaviCh24`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100013 -- Which NFL team drafted Justin Fargas?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Jacksonville Jaguars
  1. Atlanta Falcons
  2. New Orleans Saints
  3. Oakland Raiders **<- CORRECT**
- **Draft year / source context:** Justin Fargas was drafted in the **2003** NFL Draft by team code `OAK`, resolved to franchise `FR_LV` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:FargJu00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100014 -- Which NFL team drafted Ian Silberman?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Tennessee Titans
  1. San Francisco 49ers **<- CORRECT**
  2. Cleveland Browns
  3. Buffalo Bills
- **Draft year / source context:** Ian Silberman was drafted in the **2015** NFL Draft by team code `SF`, resolved to franchise `FR_SF` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:SilbIa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100015 -- Which NFL team drafted Marvin Mitchell?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. New Orleans Saints **<- CORRECT**
  1. Detroit Lions
  2. Kansas City Chiefs
  3. Minnesota Vikings
- **Draft year / source context:** Marvin Mitchell was drafted in the **2007** NFL Draft by team code `NO`, resolved to franchise `FR_NO` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:MitcMa99`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100016 -- Which NFL team drafted Chase Pittman?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5447)
- **Options:**
  0. Buffalo Bills
  1. Cleveland Browns **<- CORRECT**
  2. Minnesota Vikings
  3. Green Bay Packers
- **Draft year / source context:** Chase Pittman was drafted in the **2007** NFL Draft by team code `CLE`, resolved to franchise `FR_CLE` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `DRAFT:2007:213:CHASE_PITTMAN`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100017 -- Which NFL team drafted Jonathan Stewart?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6427)
- **Options:**
  0. Pittsburgh Steelers
  1. Miami Dolphins
  2. New York Giants
  3. Carolina Panthers **<- CORRECT**
- **Draft year / source context:** Jonathan Stewart was drafted in the **2008** NFL Draft by team code `CAR`, resolved to franchise `FR_CAR` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:StewJo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100018 -- Which NFL team drafted Kenny King?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Dallas Cowboys
  1. Arizona Cardinals **<- CORRECT**
  2. Green Bay Packers
  3. Indianapolis Colts
- **Draft year / source context:** Kenny King was drafted in the **2003** NFL Draft by team code `ARI`, resolved to franchise `FR_ARI` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:KingKe20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100019 -- Which NFL team drafted Deebo Samuel?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Detroit Lions
  1. San Francisco 49ers **<- CORRECT**
  2. New York Giants
  3. Carolina Panthers
- **Draft year / source context:** Deebo Samuel was drafted in the **2019** NFL Draft by team code `SF`, resolved to franchise `FR_SF` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:SamuDe00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100020 -- Which NFL team drafted Ricky Wagner?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. Cincinnati Bengals
  1. New York Jets
  2. Baltimore Ravens **<- CORRECT**
  3. San Francisco 49ers
- **Draft year / source context:** Ricky Wagner was drafted in the **2013** NFL Draft by team code `BAL`, resolved to franchise `FR_BAL` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:WagnRi00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100021 -- Which NFL team drafted Onterrio Smith?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Minnesota Vikings **<- CORRECT**
  1. Baltimore Ravens
  2. San Francisco 49ers
  3. Tennessee Titans
- **Draft year / source context:** Onterrio Smith was drafted in the **2003** NFL Draft by team code `MIN`, resolved to franchise `FR_MIN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:SmitOn00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100022 -- Which NFL team drafted Aaron Brant?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6707)
- **Options:**
  0. Chicago Bears **<- CORRECT**
  1. Dallas Cowboys
  2. St Louis Rams
  3. Philadelphia Eagles
- **Draft year / source context:** Aaron Brant was drafted in the **2007** NFL Draft by team code `CHI`, resolved to franchise `FR_CHI` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `DRAFT:2007:241:AARON_BRANT`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100023 -- Which NFL team drafted Armonty Bryant?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Cleveland Browns **<- CORRECT**
  1. New England Patriots
  2. Pittsburgh Steelers
  3. Dallas Cowboys
- **Draft year / source context:** Armonty Bryant was drafted in the **2013** NFL Draft by team code `CLE`, resolved to franchise `FR_CLE` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:BryaAr00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100024 -- Which NFL team drafted Frank Walker?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6847)
- **Options:**
  0. New York Giants **<- CORRECT**
  1. Washington Redskins
  2. Arizona Cardinals
  3. Atlanta Falcons
- **Draft year / source context:** Frank Walker was drafted in the **2003** NFL Draft by team code `NYG`, resolved to franchise `FR_NYG` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:WalkFr20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100025 -- Which NFL team drafted Saquan Hampton?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Cleveland Browns
  1. Kansas City Chiefs
  2. Miami Dolphins
  3. New Orleans Saints **<- CORRECT**
- **Draft year / source context:** Saquan Hampton was drafted in the **2019** NFL Draft by team code `NO`, resolved to franchise `FR_NO` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:HampSa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100026 -- Which NFL team drafted Daniel Sepulveda?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4607)
- **Options:**
  0. Houston Texans
  1. Dallas Cowboys
  2. Pittsburgh Steelers **<- CORRECT**
  3. Chicago Bears
- **Draft year / source context:** Daniel Sepulveda was drafted in the **2007** NFL Draft by team code `PIT`, resolved to franchise `FR_PIT` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:SepuDa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100027 -- Which NFL team drafted Jamaal Anderson?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Atlanta Falcons **<- CORRECT**
  1. New England Patriots
  2. Cleveland Browns
  3. New York Giants
- **Draft year / source context:** Jamaal Anderson was drafted in the **2007** NFL Draft by team code `ATL`, resolved to franchise `FR_ATL` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:AndeJa98`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100028 -- Which NFL team drafted Gerome Sapp?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5587)
- **Options:**
  0. Baltimore Ravens **<- CORRECT**
  1. Chicago Bears
  2. Washington Redskins
  3. Atlanta Falcons
- **Draft year / source context:** Gerome Sapp was drafted in the **2003** NFL Draft by team code `BAL`, resolved to franchise `FR_BAL` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:SappGe20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100029 -- Which NFL team drafted Cody Mauch?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4467)
- **Options:**
  0. Seattle Seahawks
  1. Chicago Bears
  2. Tampa Bay Buccaneers **<- CORRECT**
  3. Cincinnati Bengals
- **Draft year / source context:** Cody Mauch was drafted in the **2023** NFL Draft by team code `TB`, resolved to franchise `FR_TB` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:MaucCo00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100030 -- Which NFL team drafted Brandon Carr?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5727)
- **Options:**
  0. Kansas City Chiefs **<- CORRECT**
  1. Carolina Panthers
  2. Minnesota Vikings
  3. Washington Redskins
- **Draft year / source context:** Brandon Carr was drafted in the **2008** NFL Draft by team code `KC`, resolved to franchise `FR_KC` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:CarrBr99`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100031 -- Which NFL team drafted Andre Maddox?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Chicago Bears
  1. New York Jets **<- CORRECT**
  2. Philadelphia Eagles
  3. Denver Broncos
- **Draft year / source context:** Andre Maddox was drafted in the **2005** NFL Draft by team code `NYJ`, resolved to franchise `FR_NYJ` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `DRAFT:2005:161:ANDRE_MADDOX`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100032 -- Which NFL team drafted Trayvon Mullen?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Cleveland Browns
  1. Detroit Lions
  2. Tennessee Titans
  3. Oakland Raiders **<- CORRECT**
- **Draft year / source context:** Trayvon Mullen was drafted in the **2019** NFL Draft by team code `OAK`, resolved to franchise `FR_LV` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:MullTr00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100033 -- Which NFL team drafted Jason Pinkston?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6147)
- **Options:**
  0. Jacksonville Jaguars
  1. Tampa Bay Buccaneers
  2. Pittsburgh Steelers
  3. Cleveland Browns **<- CORRECT**
- **Draft year / source context:** Jason Pinkston was drafted in the **2011** NFL Draft by team code `CLE`, resolved to franchise `FR_CLE` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:PinkJa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100034 -- Which NFL team drafted Carlos Rogers?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6987)
- **Options:**
  0. Washington Redskins **<- CORRECT**
  1. Baltimore Ravens
  2. Atlanta Falcons
  3. Oakland Raiders
- **Draft year / source context:** Carlos Rogers was drafted in the **2005** NFL Draft by team code `WAS`, resolved to franchise `FR_WAS` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:RogeCa20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100035 -- Which NFL team drafted Jordan Kent?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4887)
- **Options:**
  0. Seattle Seahawks **<- CORRECT**
  1. Chicago Bears
  2. New York Jets
  3. Green Bay Packers
- **Draft year / source context:** Jordan Kent was drafted in the **2007** NFL Draft by team code `SEA`, resolved to franchise `FR_SEA` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:KentJo20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100036 -- Which NFL team drafted Brandon Keith?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Tennessee Titans
  1. Philadelphia Eagles
  2. New York Jets
  3. Arizona Cardinals **<- CORRECT**
- **Draft year / source context:** Brandon Keith was drafted in the **2008** NFL Draft by team code `ARI`, resolved to franchise `FR_ARI` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:KeitBr20`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100037 -- Which NFL team drafted Kade Weston?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6287)
- **Options:**
  0. Tennessee Titans
  1. Denver Broncos
  2. New England Patriots **<- CORRECT**
  3. Pittsburgh Steelers
- **Draft year / source context:** Kade Weston was drafted in the **2010** NFL Draft by team code `NE`, resolved to franchise `FR_NE` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `DRAFT:2010:248:KADE_WESTON`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100038 -- Which NFL team drafted Jermaine Gresham?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Minnesota Vikings
  1. Arizona Cardinals
  2. Miami Dolphins
  3. Cincinnati Bengals **<- CORRECT**
- **Draft year / source context:** Jermaine Gresham was drafted in the **2010** NFL Draft by team code `CIN`, resolved to franchise `FR_CIN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:GresJe00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100039 -- Which NFL team drafted Jalston Fowler?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. Minnesota Vikings
  1. Dallas Cowboys
  2. Arizona Cardinals
  3. Tennessee Titans **<- CORRECT**
- **Draft year / source context:** Jalston Fowler was drafted in the **2015** NFL Draft by team code `TEN`, resolved to franchise `FR_TEN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:FowlJa00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100040 -- Which NFL team drafted Ben Jones?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. San Diego Chargers
  1. Indianapolis Colts
  2. Houston Texans **<- CORRECT**
  3. Kansas City Chiefs
- **Draft year / source context:** Ben Jones was drafted in the **2012** NFL Draft by team code `HOU`, resolved to franchise `FR_HOU` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:JoneBe01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100041 -- Which NFL team drafted Victor Dimukeje?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Chicago Bears
  1. Green Bay Packers
  2. Arizona Cardinals **<- CORRECT**
  3. Indianapolis Colts
- **Draft year / source context:** Victor Dimukeje was drafted in the **2021** NFL Draft by team code `ARI`, resolved to franchise `FR_ARI` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:DimuVi00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100042 -- Which NFL team drafted Justin Jackson?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Los Angeles Chargers **<- CORRECT**
  1. Washington Redskins
  2. Seattle Seahawks
  3. New Orleans Saints
- **Draft year / source context:** Justin Jackson was drafted in the **2018** NFL Draft by team code `LAC`, resolved to franchise `FR_LAC` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:JackJu01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100043 -- Which NFL team drafted Isaiah Buggs?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5027)
- **Options:**
  0. Tennessee Titans
  1. Philadelphia Eagles
  2. Pittsburgh Steelers **<- CORRECT**
  3. New York Giants
- **Draft year / source context:** Isaiah Buggs was drafted in the **2019** NFL Draft by team code `PIT`, resolved to franchise `FR_PIT` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:BuggIs00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100044 -- Which NFL team drafted Mike Gesicki?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5167)
- **Options:**
  0. Oakland Raiders
  1. Los Angeles Rams
  2. Miami Dolphins **<- CORRECT**
  3. Detroit Lions
- **Draft year / source context:** Mike Gesicki was drafted in the **2018** NFL Draft by team code `MIA`, resolved to franchise `FR_MIA` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:GesiMi00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100045 -- Which NFL team drafted Baron Browning?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. New Orleans Saints
  1. Cincinnati Bengals
  2. Denver Broncos **<- CORRECT**
  3. Philadelphia Eagles
- **Draft year / source context:** Baron Browning was drafted in the **2021** NFL Draft by team code `DEN`, resolved to franchise `FR_DEN` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:BrowBa01`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100046 -- Which NFL team drafted Jerraud Powers?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.6147)
- **Options:**
  0. Baltimore Ravens
  1. Green Bay Packers
  2. Chicago Bears
  3. Indianapolis Colts **<- CORRECT**
- **Draft year / source context:** Jerraud Powers was drafted in the **2009** NFL Draft by team code `IND`, resolved to franchise `FR_IND` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:PoweJe99`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100047 -- Which NFL team drafted Ifeatu Melifonwu?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4747)
- **Options:**
  0. Chicago Bears
  1. Detroit Lions **<- CORRECT**
  2. Kansas City Chiefs
  3. Green Bay Packers
- **Draft year / source context:** Ifeatu Melifonwu was drafted in the **2021** NFL Draft by team code `DET`, resolved to franchise `FR_DET` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:MeliIf00`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100048 -- Which NFL team drafted Brian Hill?

- **Category:** NFL Draft History
- **Difficulty:** Hard (Engine band `HARD`, score 0.5307)
- **Options:**
  0. New England Patriots
  1. Atlanta Falcons **<- CORRECT**
  2. Houston Texans
  3. New York Giants
- **Draft year / source context:** Brian Hill was drafted in the **2017** NFL Draft by team code `ATL`, resolved to franchise `FR_ATL` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:HillBr02`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

## #100049 -- Which NFL team drafted Trey Taylor?

- **Category:** NFL Draft History
- **Difficulty:** Medium (Engine band `MEDIUM`, score 0.4327)
- **Options:**
  0. Atlanta Falcons
  1. Las Vegas Raiders **<- CORRECT**
  2. Cincinnati Bengals
  3. Los Angeles Rams
- **Draft year / source context:** Trey Taylor was drafted in the **2024** NFL Draft by team code `LV`, resolved to franchise `FR_LV` via Engine's `team_aliases` table (season-matched).
- **Underlying Engine source:** `draft_facts` row, player_key `PFR:TaylTr03`, verification_status `SOURCE_BACKED`, source_id `NFLVERSE_DATA` (domain `NFL_DRAFT`); relationship generated via Game Factory predicate `DRAFTED_BY` (source table reported by Engine: `relationships`).

