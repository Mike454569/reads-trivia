// NFL trivia bank, 482 multiple-choice questions across 16 categories. Started
// from the draft app's 300-question Trivia tab, plus 233 more hard questions
// added later. A later audit (duplicates / answer-context mismatches /
// answer-leaking questions) removed 47 duplicates, 2 questions with no
// defensible single correct answer (real historical ties), and 1 question
// whose claim was contradicted elsewhere in this same file; rewrote 6
// questions that gave away their own answer and 2 with a vague "Both"/"All
// contributed" non-answer marked correct. See README.md's "A note on the
// trivia content" for details.
window.QUIZ_DATA = [
  {
    "id": 1,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team was the first to win back-to-back Super Bowls?",
    "options": [
      "Dallas Cowboys",
      "Pittsburgh Steelers",
      "Green Bay Packers",
      "Miami Dolphins"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 2,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Joe Namath guaranteed a win and was named MVP of which Super Bowl?",
    "options": [
      "Super Bowl III",
      "Super Bowl VI",
      "Super Bowl IV",
      "Super Bowl V"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 3,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team holds the record for most consecutive Super Bowl losses, dropping four straight from 1991-1994?",
    "options": [
      "Denver Broncos",
      "Buffalo Bills",
      "Atlanta Falcons",
      "Minnesota Vikings"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 4,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Scott Norwood's missed field goal in Super Bowl XXV gave the win to which team?",
    "options": [
      "San Francisco 49ers",
      "Dallas Cowboys",
      "Washington Redskins",
      "New York Giants"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 5,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which quarterback holds the record for most Super Bowl MVP awards, with five?",
    "options": [
      "Peyton Manning",
      "Terry Bradshaw",
      "Tom Brady",
      "Joe Montana"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 6,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Super Bowl XXIV set the record for largest margin of victory (45 points) when the 49ers routed which team?",
    "options": [
      "Buffalo Bills",
      "Denver Broncos",
      "Miami Dolphins",
      "San Diego Chargers"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 7,
    "category": "Super Bowl History",
    "difficulty": "Very Hard",
    "question": "Chuck Howley remains the only player named Super Bowl MVP while on the losing team. Which Super Bowl?",
    "options": [
      "Super Bowl XVI",
      "Super Bowl XIII",
      "Super Bowl X",
      "Super Bowl V"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 9,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Whose pass did Malcolm Butler intercept at the goal line to seal Super Bowl XLIX for the Patriots?",
    "options": [
      "Tom Brady",
      "Andrew Luck",
      "Cam Newton",
      "Russell Wilson"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 11,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which quarterback led the Kansas City Chiefs in their loss to Green Bay in Super Bowl I?",
    "options": [
      "Curtis McClinton",
      "Otis Taylor",
      "Len Dawson",
      "Bobby Bell"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 12,
    "category": "Super Bowl History",
    "difficulty": "Very Hard",
    "question": "Which team became the first wild-card entrant to win a Super Bowl, doing so after the 1980 season?",
    "options": [
      "Oakland Raiders",
      "Baltimore Ravens",
      "Pittsburgh Steelers",
      "Denver Broncos"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 13,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Doug Williams became the first Black starting quarterback to win a Super Bowl with which team, in Super Bowl XXII?",
    "options": [
      "Washington Redskins",
      "Los Angeles Raiders",
      "Denver Broncos",
      "Chicago Bears"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 14,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team defeated the Miami Dolphins in Super Bowl VI, the year before Miami's perfect season?",
    "options": [
      "Washington Redskins",
      "Dallas Cowboys",
      "Minnesota Vikings",
      "Baltimore Colts"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 15,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The 1972 Miami Dolphins capped their perfect season by winning which Super Bowl?",
    "options": [
      "Super Bowl VI",
      "Super Bowl VIII",
      "Super Bowl VII",
      "Super Bowl IX"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 16,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The Tennessee Titans' 'Music City Miracle' lateral play sent them to a Super Bowl loss against which team?",
    "options": [
      "St. Louis Rams",
      "Buffalo Bills",
      "Baltimore Ravens",
      "Jacksonville Jaguars"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 17,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The controversial 'Tuck Rule Game' helped propel which team toward its first Super Bowl title after the 2001 season?",
    "options": [
      "Pittsburgh Steelers",
      "New England Patriots",
      "St. Louis Rams",
      "Oakland Raiders"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 18,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which kicker's 48-yard field goal as time expired won Super Bowl XXXVI for the Patriots?",
    "options": [
      "Jason Elam",
      "Adam Vinatieri",
      "Sebastian Janikowski",
      "John Carney"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 19,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Kurt Warner led the 'Greatest Show on Turf' Rams to victory in which Super Bowl?",
    "options": [
      "Super Bowl XXXIV",
      "Super Bowl XXXIII",
      "Super Bowl XXXV",
      "Super Bowl XXXVI"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 20,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team beat the Patriots to end their bid for a perfect 19-0 season in Super Bowl XLII?",
    "options": [
      "Philadelphia Eagles",
      "New York Jets",
      "Washington Redskins",
      "New York Giants"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 21,
    "category": "Super Bowl History",
    "difficulty": "Very Hard",
    "question": "Von Miller's dominant pass rush earned him MVP honors in Super Bowl 50, played in the final game of which quarterback's career?",
    "options": [
      "Cam Newton",
      "Aaron Rodgers",
      "Peyton Manning",
      "Tom Brady"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 22,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl XIII in a rematch of Super Bowl X, both against the Dallas Cowboys?",
    "options": [
      "Denver Broncos",
      "Pittsburgh Steelers",
      "Miami Dolphins",
      "Oakland Raiders"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 23,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The Pittsburgh Steelers won four Super Bowls in six seasons during which decade?",
    "options": [
      "1960s",
      "1970s",
      "1990s",
      "1980s"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 24,
    "category": "Super Bowl History",
    "difficulty": "Very Hard",
    "question": "Super Bowl XXV was played just ten days after the start of which conflict, prompting heightened security?",
    "options": [
      "The Kosovo War",
      "The Gulf War",
      "The Falklands War",
      "Operation Just Cause"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 25,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Super Bowl XLVII, the 'Harbaugh Bowl,' pitted brothers against each other. Who coached the winning Baltimore Ravens?",
    "options": [
      "Sean Payton",
      "Jim Harbaugh",
      "Mike Tomlin",
      "John Harbaugh"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 26,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl LVIII in overtime, the first Super Bowl decided under the newer playoff overtime rules?",
    "options": [
      "Philadelphia Eagles",
      "Kansas City Chiefs",
      "San Francisco 49ers",
      "Baltimore Ravens"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 27,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Backup-turned-starter Nick Foles won Super Bowl MVP leading which team to its first title, upsetting the Patriots?",
    "options": [
      "Philadelphia Eagles",
      "New Orleans Saints",
      "Chicago Bears",
      "Minnesota Vikings"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 28,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Tom Brady won his seventh Super Bowl title, his first away from New England, in Super Bowl LV with which team?",
    "options": [
      "Los Angeles Rams",
      "Tampa Bay Buccaneers",
      "Kansas City Chiefs",
      "Arizona Cardinals"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 29,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl LVI, becoming the first to play a Super Bowl in its own home stadium?",
    "options": [
      "Los Angeles Rams",
      "Tampa Bay Buccaneers",
      "Cincinnati Bengals",
      "Kansas City Chiefs"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 30,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl LVII, defeating the Philadelphia Eagles despite Patrick Mahomes playing on a high-ankle sprain?",
    "options": [
      "Cincinnati Bengals",
      "Buffalo Bills",
      "San Francisco 49ers",
      "Kansas City Chiefs"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 31,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The Kansas City Chiefs' bid for a Super Bowl three-peat ended in Super Bowl LIX against which team?",
    "options": [
      "Detroit Lions",
      "San Francisco 49ers",
      "Philadelphia Eagles",
      "Buffalo Bills"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 32,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team's Super Bowl III win is considered one of the greatest upsets in sports history, over the heavily favored Colts?",
    "options": [
      "Kansas City Chiefs",
      "New York Jets",
      "Houston Oilers",
      "Oakland Raiders"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 33,
    "category": "Super Bowl History",
    "difficulty": "Very Hard",
    "question": "Timmy Smith's Super Bowl-record 204 rushing yards came in the game where Doug Williams was named MVP. Which Super Bowl?",
    "options": [
      "Super Bowl XXI",
      "Super Bowl XXIII",
      "Super Bowl XXIV",
      "Super Bowl XXII"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 34,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which two franchises have met in the Super Bowl three times, more than any other pairing?",
    "options": [
      "San Francisco 49ers and Cincinnati Bengals",
      "Pittsburgh Steelers and Dallas Cowboys",
      "New England Patriots and New York Giants",
      "Denver Broncos and Green Bay Packers"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 36,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which franchise has won the most NFL championships overall, including the pre-Super Bowl era, with 13 titles?",
    "options": [
      "Pittsburgh Steelers",
      "New England Patriots",
      "Green Bay Packers",
      "Chicago Bears"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 39,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The 1972 Miami Dolphins remain the only team to complete a perfect season including playoffs. What was their final record?",
    "options": [
      "14-0",
      "16-0",
      "17-0",
      "15-0"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 40,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which expansion team joined the NFL in 1976 alongside the Seattle Seahawks?",
    "options": [
      "Tampa Bay Buccaneers",
      "Jacksonville Jaguars",
      "Houston Texans",
      "Carolina Panthers"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 41,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which two teams joined the NFL as expansion franchises in 1995?",
    "options": [
      "Carolina Panthers and Jacksonville Jaguars",
      "Houston Texans and Cleveland Browns",
      "Baltimore Ravens and Tennessee Titans",
      "Seattle Seahawks and Tampa Bay Buccaneers"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 42,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The original Cleveland Browns franchise 'moved' in 1996 to become which team, while Cleveland retained its name and history?",
    "options": [
      "Los Angeles Rams",
      "Tennessee Titans",
      "Indianapolis Colts",
      "Baltimore Ravens"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 43,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team relocated from Houston to Tennessee, eventually becoming the Titans?",
    "options": [
      "Houston Oilers",
      "Dallas Texans",
      "Houston Gamblers",
      "Houston Texans"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 44,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Los Angeles Rams franchise originally began in which city before later relocating to Los Angeles?",
    "options": [
      "Cleveland",
      "St. Louis",
      "San Diego",
      "Anaheim"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 45,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which NFL stadium is famously nicknamed 'The Frozen Tundra'?",
    "options": [
      "Highmark Stadium",
      "Soldier Field",
      "Lambeau Field",
      "Arrowhead Stadium"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 46,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "As of the mid-2020s, which longtime NFL franchises have never appeared in a Super Bowl?",
    "options": [
      "Minnesota Vikings and Houston Texans",
      "Detroit Lions and Houston Texans",
      "Detroit Lions and Cleveland Browns",
      "Cleveland Browns and Buffalo Bills"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 47,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team set the NFL record for most points scored in a season (606) in 2013, led by Peyton Manning?",
    "options": [
      "Denver Broncos",
      "Green Bay Packers",
      "New Orleans Saints",
      "New England Patriots"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 48,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Chicago Bears and Green Bay Packers share the NFL's oldest rivalry, first playing in which decade?",
    "options": [
      "1910s",
      "1940s",
      "1930s",
      "1920s"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 49,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team's identity traces back to being originally called the 'Decatur Staleys' before relocating to Chicago?",
    "options": [
      "Chicago Bears",
      "Chicago Cardinals",
      "Green Bay Packers",
      "Detroit Lions"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 50,
    "category": "Franchise & Team Records",
    "difficulty": "Very Hard",
    "question": "The Dallas Cowboys earned the nickname 'America's Team' largely due to what in the 1970s?",
    "options": [
      "Being the league's first expansion team",
      "Coach Tom Landry's fame alone",
      "Their outsized national TV popularity and highlight-reel exposure",
      "Winning five straight Super Bowls"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 51,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team won a Super Bowl-era record 17 consecutive regular-season games spanning the 2003-04 seasons?",
    "options": [
      "New England Patriots",
      "Pittsburgh Steelers",
      "San Diego Chargers",
      "Indianapolis Colts"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 52,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which franchise holds the record for the most all-time regular-season wins in NFL history?",
    "options": [
      "Dallas Cowboys",
      "Green Bay Packers",
      "Pittsburgh Steelers",
      "Chicago Bears"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 55,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The 'Purple People Eaters' defensive line terrorized the NFL in the late 1960s and 1970s for which team?",
    "options": [
      "Minnesota Vikings",
      "Baltimore Ravens",
      "Pittsburgh Steelers",
      "Los Angeles Rams"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 57,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The 'Doomsday Defense' nickname belonged to which team's dominant units in the 1960s and 1970s?",
    "options": [
      "Washington Redskins",
      "Chicago Bears",
      "Miami Dolphins",
      "Dallas Cowboys"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 58,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team's high-powered offense of the late 1990s and early 2000s was nicknamed 'The Greatest Show on Turf'?",
    "options": [
      "Kansas City Chiefs",
      "Indianapolis Colts",
      "St. Louis Rams",
      "Denver Broncos"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 59,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team's early-era dominant defenses earned the nickname 'Monsters of the Midway'?",
    "options": [
      "Cleveland Browns",
      "Chicago Bears",
      "Detroit Lions",
      "Green Bay Packers"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 60,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team's 1985 squad, famous for the 'Super Bowl Shuffle,' won Super Bowl XX?",
    "options": [
      "Chicago Bears",
      "Miami Dolphins",
      "San Francisco 49ers",
      "New York Giants"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 61,
    "category": "Franchise & Team Records",
    "difficulty": "Very Hard",
    "question": "Which team completed the largest regular-season comeback in NFL history, erasing a 33-point deficit against the Colts in 2022?",
    "options": [
      "Green Bay Packers",
      "Chicago Bears",
      "Minnesota Vikings",
      "Detroit Lions"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 62,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Buffalo Bills' famous 32-point playoff comeback in January 1993 came against which team?",
    "options": [
      "Houston Oilers",
      "Cleveland Browns",
      "Miami Dolphins",
      "Pittsburgh Steelers"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 63,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Arizona Cardinals, one of the NFL's oldest franchises, played in which cities before settling in Arizona?",
    "options": [
      "St. Louis and Cleveland",
      "Chicago and St. Louis",
      "Chicago and Baltimore",
      "Boston and St. Louis"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 64,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team plays its home games at Lincoln Financial Field, nicknamed 'The Linc'?",
    "options": [
      "New York Giants",
      "Baltimore Ravens",
      "Philadelphia Eagles",
      "Washington Commanders"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 65,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which two NFL teams share SoFi Stadium in Inglewood, California?",
    "options": [
      "Los Angeles Rams and Los Angeles Chargers",
      "Los Angeles Rams and Oakland Raiders",
      "Los Angeles Chargers and San Francisco 49ers",
      "San Diego Chargers and Los Angeles Rams"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 66,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Who holds the NFL record for most career passing yards?",
    "options": [
      "Brett Favre",
      "Peyton Manning",
      "Drew Brees",
      "Tom Brady"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 67,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Who holds the NFL record for most career passing touchdowns?",
    "options": [
      "Peyton Manning",
      "Aaron Rodgers",
      "Drew Brees",
      "Tom Brady"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 68,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Which quarterback set the single-season passing yards record (5,477) in 2011?",
    "options": [
      "Drew Brees",
      "Peyton Manning",
      "Dan Marino",
      "Tom Brady"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 69,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Dan Marino's 20-year-old single-season touchdown pass record (48) was finally broken in 2004 by whom?",
    "options": [
      "Tom Brady",
      "Peyton Manning",
      "Drew Brees",
      "Kurt Warner"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 70,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Who set the current NFL single-season passing touchdown record with 55 touchdowns in 2013?",
    "options": [
      "Patrick Mahomes",
      "Tom Brady",
      "Aaron Rodgers",
      "Peyton Manning"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 72,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Very Hard",
    "question": "Which quarterback is NOT part of the group who has thrown seven touchdown passes in a single game?",
    "options": [
      "Nick Foles",
      "Dan Marino",
      "Peyton Manning",
      "Drew Brees"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 73,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Peyton Manning holds the record for most NFL MVP awards won by a single player. How many did he win?",
    "options": [
      "6",
      "5",
      "4",
      "3"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 74,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Michael Vick set the single-season rushing yards record for a quarterback (1,039 yards) in which season?",
    "options": [
      "2002",
      "2004",
      "2006",
      "2010"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 75,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Who was the first quarterback to throw for over 5,000 yards in a single season, doing so in 1984?",
    "options": [
      "Dan Marino",
      "Warren Moon",
      "Dan Fouts",
      "Y.A. Tittle"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 77,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Brett Favre holds the record for most consecutive starts by a quarterback, at 297 regular-season games. Roughly what is that total?",
    "options": [
      "320",
      "297",
      "275",
      "250"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 79,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Tom Brady was famously drafted in which round of the 2000 NFL Draft?",
    "options": [
      "3rd round",
      "7th round",
      "1st round",
      "6th round"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 80,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Steve Young set the Super Bowl record for touchdown passes in a game with six. In which Super Bowl?",
    "options": [
      "Super Bowl XXX",
      "Super Bowl XXIV",
      "Super Bowl XXIX",
      "Super Bowl XXIII"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 81,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Which quarterback had his jersey number retired by both the Colts and the Broncos?",
    "options": [
      "Eli Manning",
      "John Elway",
      "Peyton Manning",
      "Johnny Unitas"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 82,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Which quarterback won NFL MVP in just his second professional season, in 2019?",
    "options": [
      "Patrick Mahomes",
      "Dak Prescott",
      "Josh Allen",
      "Lamar Jackson"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 83,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Which quarterback holds the NFL record for most career playoff wins as a starter?",
    "options": [
      "Joe Montana",
      "Tom Brady",
      "Peyton Manning",
      "Ben Roethlisberger"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 84,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Peyton and Eli Manning are the only siblings to each have won a Super Bowl MVP award. Which pair of coaching brothers has also faced off in a Super Bowl?",
    "options": [
      "Sean and Mike McDermott",
      "Jim and John Harbaugh",
      "Kurt and Jon Gruden",
      "JJ and TJ Watt"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 85,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Warren Moon, a Pro Football Hall of Famer known for his years in the CFL, had his best NFL seasons with which team?",
    "options": [
      "Houston Oilers",
      "Kansas City Chiefs",
      "Minnesota Vikings",
      "Seattle Seahawks"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 86,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Which quarterback threw the most career touchdown passes without ever winning a Super Bowl?",
    "options": [
      "Dan Fouts",
      "Dan Marino",
      "Warren Moon",
      "Philip Rivers"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 87,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Dan Marino appeared in exactly one Super Bowl in his Hall of Fame career. Which one?",
    "options": [
      "Super Bowl XXI",
      "Super Bowl XVII",
      "Super Bowl XXIII",
      "Super Bowl XIX"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 88,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Very Hard",
    "question": "Cam Newton is the only player in NFL history to accomplish which unique combination?",
    "options": [
      "Win Super Bowl MVP as a rookie",
      "Win the Heisman Trophy, be picked #1 overall, and win NFL MVP",
      "Lead the league in rushing as a QB three times",
      "Throw five touchdowns in his NFL debut"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 89,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Whose number 12 jersey is retired by the New England Patriots?",
    "options": [
      "Tom Brady",
      "Matt Cassel",
      "Drew Bledsoe",
      "Steve Grogan"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 90,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Otto Graham led which franchise to a championship game in all ten years of his AAFC and NFL career?",
    "options": [
      "New York Giants",
      "Detroit Lions",
      "Cleveland Browns",
      "San Francisco 49ers"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 91,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Known as 'The Comeback Kid' for his fourth-quarter heroics, which quarterback starred for the Denver Broncos?",
    "options": [
      "John Elway",
      "Jake Plummer",
      "Frank Tripucka",
      "Craig Morton"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 92,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "John Elway won back-to-back Super Bowl titles with the Broncos before retiring. Which two seasons?",
    "options": [
      "1997 and 1998",
      "1999 and 2000",
      "1996 and 1997",
      "1998 and 1999"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 93,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Which quarterback famously wore number 4 and played 20 NFL seasons, mostly with Green Bay?",
    "options": [
      "Brett Favre",
      "Bart Starr",
      "Aaron Rodgers",
      "Lynn Dickey"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 94,
    "category": "Passing Records & QB Trivia",
    "difficulty": "Hard",
    "question": "Bart Starr won MVP honors in the first two Super Bowls ever played while quarterbacking which team?",
    "options": [
      "Kansas City Chiefs",
      "Dallas Cowboys",
      "Green Bay Packers",
      "Baltimore Colts"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 96,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Who holds the NFL record for most career rushing yards?",
    "options": [
      "Adrian Peterson",
      "Walter Payton",
      "Barry Sanders",
      "Emmitt Smith"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 97,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Emmitt Smith broke Walter Payton's career rushing record while playing for which team?",
    "options": [
      "Philadelphia Eagles",
      "Dallas Cowboys",
      "Washington Redskins",
      "Arizona Cardinals"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 98,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Who holds the single-season rushing yards record (2,105 yards), set in 1984?",
    "options": [
      "Adrian Peterson",
      "Eric Dickerson",
      "Jim Brown",
      "O.J. Simpson"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 99,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Eric Dickerson set his single-season rushing record while playing for which team?",
    "options": [
      "Los Angeles Rams",
      "Houston Oilers",
      "Indianapolis Colts",
      "Atlanta Falcons"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 100,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Who holds the NFL single-game rushing record with 296 yards, set in 2007?",
    "options": [
      "O.J. Simpson",
      "Corey Dillon",
      "Adrian Peterson",
      "Jamal Lewis"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 101,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which running back holds the NFL record for most career rushing touchdowns?",
    "options": [
      "Emmitt Smith",
      "Walter Payton",
      "LaDainian Tomlinson",
      "Marcus Allen"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 102,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Barry Sanders retired abruptly in 1999, just short of breaking whose career rushing record at the time?",
    "options": [
      "Eric Dickerson",
      "Jim Brown",
      "Walter Payton",
      "O.J. Simpson"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 103,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which running back rushed for over 2,000 yards in a season at age 28 or older, in 2012, with the Vikings?",
    "options": [
      "LaDainian Tomlinson",
      "Frank Gore",
      "Adrian Peterson",
      "Marshawn Lynch"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 104,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Jim Brown retired at the peak of his career while holding the all-time rushing record. Which team did he play for?",
    "options": [
      "New York Giants",
      "Baltimore Colts",
      "Cleveland Browns",
      "Chicago Bears"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 105,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Who holds the NFL record for most career receiving yards?",
    "options": [
      "Terrell Owens",
      "Jerry Rice",
      "Larry Fitzgerald",
      "Randy Moss"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 106,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Jerry Rice's career record for receiving touchdowns stands at how many?",
    "options": [
      "197",
      "208",
      "180",
      "190"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 109,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Randy Moss set his single-season receiving touchdown record while playing for which team?",
    "options": [
      "New England Patriots",
      "Oakland Raiders",
      "San Francisco 49ers",
      "Minnesota Vikings"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 110,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which running back holds the NFL record for most career rushing attempts?",
    "options": [
      "Walter Payton",
      "Emmitt Smith",
      "Curtis Martin",
      "Frank Gore"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 111,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which player holds the NFL record for most career all-purpose yards?",
    "options": [
      "Jerry Rice",
      "Walter Payton",
      "Emmitt Smith",
      "Marshall Faulk"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 112,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Derrick Henry became the eighth player in NFL history to rush for 2,000-plus yards in a season, doing so with which team?",
    "options": [
      "Baltimore Ravens",
      "Tennessee Titans",
      "Indianapolis Colts",
      "Kansas City Chiefs"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 113,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Walter Payton's nickname, reflecting his relentless running style, was:",
    "options": [
      "Prime Time",
      "The Juice",
      "The Bus",
      "Sweetness"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 114,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "O.J. Simpson was the first to rush for over 2,000 yards in a season, in 1973's 14-game schedule. What was his exact total?",
    "options": [
      "1,999 yards",
      "2,058 yards",
      "2,003 yards",
      "2,105 yards"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 115,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which running back's nickname is 'The Bus,' known for his power running with the Steelers?",
    "options": [
      "Curtis Martin",
      "Jerome Bettis",
      "Eddie George",
      "William Perry"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 116,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which wide receiver's nickname is 'Megatron'?",
    "options": [
      "Terrell Owens",
      "A.J. Green",
      "Randy Moss",
      "Calvin Johnson"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 117,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Marshall Faulk is best remembered for his versatility as a dual-threat back on which 'Greatest Show on Turf' team?",
    "options": [
      "St. Louis Rams",
      "Indianapolis Colts",
      "San Diego Chargers",
      "Kansas City Chiefs"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 118,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "LaDainian Tomlinson set the single-season touchdown record with 31, a mark that stood for years. In which year?",
    "options": [
      "2009",
      "2006",
      "2003",
      "2000"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 119,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "LaDainian Tomlinson's 31-touchdown record season came while playing for which team?",
    "options": [
      "San Diego Chargers",
      "Dallas Cowboys",
      "Kansas City Chiefs",
      "New York Jets"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 120,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which tight end is the NFL's all-time leader in career receptions among tight ends, having starred for the Chiefs and Falcons?",
    "options": [
      "Tony Gonzalez",
      "Jason Witten",
      "Rob Gronkowski",
      "Antonio Gates"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 121,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Curtis Martin, a Hall of Fame running back, spent his best seasons with which team after starting his career with the Patriots?",
    "options": [
      "Indianapolis Colts",
      "Miami Dolphins",
      "New York Jets",
      "Buffalo Bills"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 123,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which team featured the running back duo of Priest Holmes and later Larry Johnson, both posting monster rushing seasons in the mid-2000s?",
    "options": [
      "Seattle Seahawks",
      "Denver Broncos",
      "Indianapolis Colts",
      "Kansas City Chiefs"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 124,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Which wide receiver holds the NFL record for most receptions in a single season, with 149, set in 2019?",
    "options": [
      "Julio Jones",
      "Michael Thomas",
      "DeAndre Hopkins",
      "Antonio Brown"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 125,
    "category": "Rushing & Receiving Records",
    "difficulty": "Hard",
    "question": "Michael Thomas set his single-season reception record while playing for which team?",
    "options": [
      "Atlanta Falcons",
      "Tampa Bay Buccaneers",
      "Carolina Panthers",
      "New Orleans Saints"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 126,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Who was the first pick of the 2004 NFL Draft, later involved in a famous draft-day trade?",
    "options": [
      "J.P. Losman",
      "Eli Manning",
      "Philip Rivers",
      "Ben Roethlisberger"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 127,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "The famous 2004 draft-day trade sent Eli Manning to the Giants and sent which quarterback to San Diego?",
    "options": [
      "Philip Rivers",
      "Ben Roethlisberger",
      "Byron Leftwich",
      "Kellen Winslow II"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 128,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Tom Brady was the 199th overall pick in the 2000 NFL Draft. Which team selected him?",
    "options": [
      "New England Patriots",
      "Miami Dolphins",
      "San Francisco 49ers",
      "New York Jets"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 130,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Robert Griffin III (RG3) was selected #2 overall in 2012 by which team?",
    "options": [
      "Washington Redskins",
      "St. Louis Rams",
      "Miami Dolphins",
      "Cleveland Browns"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 132,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Ryan Leaf, taken #2 overall in 1998, is often cited as one of the biggest draft busts. Which team drafted him?",
    "options": [
      "Indianapolis Colts",
      "Cincinnati Bengals",
      "San Diego Chargers",
      "Arizona Cardinals"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 133,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "JaMarcus Russell, a notorious draft bust quarterback, was the #1 pick in 2007 by which team?",
    "options": [
      "Detroit Lions",
      "Oakland Raiders",
      "Tampa Bay Buccaneers",
      "Cleveland Browns"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 134,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which quarterback was the #1 overall pick of the 2015 draft, going to Tampa Bay?",
    "options": [
      "Teddy Bridgewater",
      "Blake Bortles",
      "Jameis Winston",
      "Marcus Mariota"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 135,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Marcus Mariota was picked #2 overall in the 2015 draft by which team?",
    "options": [
      "New York Jets",
      "Chicago Bears",
      "Tennessee Titans",
      "Philadelphia Eagles"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 136,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which quarterback became the #1 overall pick in 2018, joining the Cleveland Browns?",
    "options": [
      "Josh Allen",
      "Sam Darnold",
      "Josh Rosen",
      "Baker Mayfield"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 137,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which team traded up to select Patrick Mahomes with the 10th overall pick in the 2017 draft?",
    "options": [
      "Houston Texans",
      "Buffalo Bills",
      "Chicago Bears",
      "Kansas City Chiefs"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 138,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which team drafted Tom Brady's eventual successor, Mac Jones, in the first round of 2021?",
    "options": [
      "New England Patriots",
      "Chicago Bears",
      "New York Jets",
      "San Francisco 49ers"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 139,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Trevor Lawrence was the #1 overall pick of the 2021 draft, selected by which team?",
    "options": [
      "Miami Dolphins",
      "Jacksonville Jaguars",
      "Detroit Lions",
      "New York Jets"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 140,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which quarterback, the #1 pick in the 2023 draft, joined the Carolina Panthers via a blockbuster trade?",
    "options": [
      "Bryce Young",
      "C.J. Stroud",
      "Anthony Richardson",
      "Will Levis"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 141,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which team held the #1 overall pick in the 2024 draft and selected quarterback Caleb Williams?",
    "options": [
      "Washington Commanders",
      "New England Patriots",
      "Chicago Bears",
      "Arizona Cardinals"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 142,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Aaron Rodgers infamously slid to the 24th overall pick in the 2005 draft before being selected by which team?",
    "options": [
      "Green Bay Packers",
      "Cleveland Browns",
      "Baltimore Ravens",
      "San Francisco 49ers"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 143,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which quarterback was taken #1 overall in the 2001 draft by the Atlanta Falcons?",
    "options": [
      "Drew Brees",
      "Chris Weinke",
      "Michael Vick",
      "Ken Dorsey"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 144,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "John Elway was drafted #1 overall in 1983 by the Baltimore Colts but was traded before ever playing for them. Which team acquired him?",
    "options": [
      "Los Angeles Raiders",
      "Denver Broncos",
      "San Diego Chargers",
      "Seattle Seahawks"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 145,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which Hall of Fame quarterback was part of the legendary 1983 draft class, going to the Dolphins?",
    "options": [
      "Ken O'Brien",
      "Dan Marino",
      "Jim Kelly",
      "Tony Eason"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 146,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Dan Marino's slide to the 27th overall pick in the 1983 draft is remembered as one of the draft's biggest what?",
    "options": [
      "Busts",
      "Trades",
      "Controversies",
      "Steals"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 147,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which team held the #1 overall pick and selected Bo Jackson in the 1986 draft, though he chose baseball instead?",
    "options": [
      "Tampa Bay Buccaneers",
      "Atlanta Falcons",
      "Indianapolis Colts",
      "Detroit Lions"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 148,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Ki-Jana Carter, the #1 overall pick of the 1995 draft, is often cited as a draft bust after being taken by which team?",
    "options": [
      "Cincinnati Bengals",
      "St. Louis Rams",
      "Carolina Panthers",
      "Jacksonville Jaguars"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 149,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Sam Bradford was the #1 overall pick of the 2010 NFL Draft, selected by which team?",
    "options": [
      "Detroit Lions",
      "Buffalo Bills",
      "Carolina Panthers",
      "St. Louis Rams"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 150,
    "category": "NFL Draft History",
    "difficulty": "Hard",
    "question": "Which Heisman-winning quarterback was the #1 overall pick of the 2019 draft, taken by the Arizona Cardinals?",
    "options": [
      "Dwayne Haskins",
      "Drew Lock",
      "Daniel Jones",
      "Kyler Murray"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 152,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Don Shula's regular-season win total record stands at how many wins?",
    "options": [
      "328",
      "300",
      "292",
      "347"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 153,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach led the Green Bay Packers to victory in the first two Super Bowls ever played?",
    "options": [
      "Bart Starr",
      "Curly Lambeau",
      "Vince Lombardi",
      "Mike Holmgren"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 154,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "The Super Bowl trophy is named after which legendary Packers coach?",
    "options": [
      "Curly Lambeau",
      "Paul Brown",
      "Vince Lombardi",
      "George Halas"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 155,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach won a record six Super Bowls as head coach of the New England Patriots?",
    "options": [
      "Bill Belichick",
      "Nick Saban",
      "Bill Parcells",
      "Josh McDaniels"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 156,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Bill Belichick left the Patriots in 2024 and later became head coach at which college program?",
    "options": [
      "Ohio State University",
      "University of Michigan",
      "University of North Carolina",
      "University of Alabama"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 157,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach led the Pittsburgh Steelers to four Super Bowl titles in the 1970s?",
    "options": [
      "Mike Tomlin",
      "Bill Cowher",
      "Bud Grant",
      "Chuck Noll"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 158,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach led the Dallas Cowboys to back-to-back Super Bowl titles in the early 1990s before a falling out with owner Jerry Jones?",
    "options": [
      "Chan Gailey",
      "Barry Switzer",
      "Tom Landry",
      "Jimmy Johnson"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 159,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach guided the Denver Broncos to consecutive Super Bowl titles (XXXII and XXXIII) before retiring?",
    "options": [
      "Dan Reeves",
      "Josh McDaniels",
      "Wade Phillips",
      "Mike Shanahan"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 160,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which head coach led the Chicago Bears to victory in Super Bowl XX?",
    "options": [
      "Mike Ditka",
      "Dave Wannstedt",
      "George Halas",
      "Lovie Smith"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 161,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach won a Super Bowl as both a player (1971 Cowboys) and later as a head coach (1985 Bears)?",
    "options": [
      "Chuck Knox",
      "Mike Ditka",
      "Dan Reeves",
      "Tom Flores"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 162,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach led the Baltimore Ravens to victory in Super Bowl XLVII over his brother's team?",
    "options": [
      "Jim Harbaugh",
      "John Harbaugh",
      "Marvin Lewis",
      "Brian Billick"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 163,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Jon Gruden won Super Bowl XXXVII coaching Tampa Bay against his former team. Which team had he coached the previous season?",
    "options": [
      "San Diego Chargers",
      "Oakland Raiders",
      "Kansas City Chiefs",
      "Philadelphia Eagles"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 164,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach led the Kansas City Chiefs to multiple Super Bowl titles during the Patrick Mahomes era?",
    "options": [
      "Herm Edwards",
      "Andy Reid",
      "Dick Vermeil",
      "Marty Schottenheimer"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 165,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Andy Reid served as head coach of which team before joining the Chiefs?",
    "options": [
      "Green Bay Packers",
      "Minnesota Vikings",
      "St. Louis Rams",
      "Philadelphia Eagles"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 166,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach, known for the 'Legion of Boom' defensive scheme, led the Seahawks to a Super Bowl XLVIII title?",
    "options": [
      "Mike Holmgren",
      "Jim Mora",
      "Dan Quinn",
      "Pete Carroll"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 168,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Bill Parcells is the only coach to lead four different franchises to the playoffs. Which team did he NOT coach?",
    "options": [
      "Dallas Cowboys",
      "New York Giants",
      "New England Patriots",
      "Green Bay Packers"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 169,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach's Miami Dolphins remain the only team to complete a perfect, undefeated season including playoffs, in 1972?",
    "options": [
      "George Wilson",
      "Bill Arnsparger",
      "Don Shula",
      "Howard Schnellenberger"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 170,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach led the Tampa Bay Buccaneers to a Super Bowl LV title in Tom Brady's first season with the team?",
    "options": [
      "Dirk Koetter",
      "Todd Bowles",
      "Bruce Arians",
      "Lovie Smith"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 171,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which quarterback was the first-ever unanimous NFL MVP selection, winning the award in 2010?",
    "options": [
      "Tom Brady",
      "Aaron Rodgers",
      "Drew Brees",
      "Peyton Manning"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 172,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which running back won NFL MVP unanimously in 2012 after his historic 2,097-yard rushing season?",
    "options": [
      "Marshawn Lynch",
      "Doug Martin",
      "Adrian Peterson",
      "Arian Foster"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 173,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which quarterback won back-to-back NFL MVP awards in 2020 and 2021?",
    "options": [
      "Tom Brady",
      "Patrick Mahomes",
      "Aaron Rodgers",
      "Josh Allen"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 174,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which quarterback won NFL MVP in both 2019 and 2023?",
    "options": [
      "Lamar Jackson",
      "Justin Herbert",
      "Patrick Mahomes",
      "Josh Allen"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 175,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Very Hard",
    "question": "Who is the most recent defensive player to win NFL MVP, doing so in 1986?",
    "options": [
      "Mike Singletary",
      "Reggie White",
      "Bruce Smith",
      "Lawrence Taylor"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 176,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Lawrence Taylor, the last defensive player to win NFL MVP, played his entire career for which team?",
    "options": [
      "Dallas Cowboys",
      "New York Giants",
      "Philadelphia Eagles",
      "Washington Redskins"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 177,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which running back won NFL Offensive Rookie of the Year and later an NFL MVP award, having starred for the Vikings?",
    "options": [
      "Marshawn Lynch",
      "Chris Johnson",
      "Eddie George",
      "Adrian Peterson"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 178,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which quarterback won NFL Offensive Rookie of the Year in 2012 after a stellar debut season with the Colts?",
    "options": [
      "Russell Wilson",
      "Ryan Tannehill",
      "Robert Griffin III",
      "Andrew Luck"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 179,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which longtime Titans/Oilers offensive lineman was selected to a record-tying 14 Pro Bowls?",
    "options": [
      "Willie Roaf",
      "Anthony Munoz",
      "Jonathan Ogden",
      "Bruce Matthews"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 180,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which wide receiver is widely considered the greatest of all time and holds nearly every major career receiving record?",
    "options": [
      "Larry Fitzgerald",
      "Randy Moss",
      "Terrell Owens",
      "Jerry Rice"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 181,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "J.J. Watt won NFL Defensive Player of the Year three times while playing for which team?",
    "options": [
      "Arizona Cardinals",
      "Houston Texans",
      "Pittsburgh Steelers",
      "Denver Broncos"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 182,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which cornerback, nicknamed 'Prime Time,' was a two-sport star and Pro Football Hall of Fame inductee?",
    "options": [
      "Rod Woodson",
      "Bo Jackson",
      "Charles Woodson",
      "Deion Sanders"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 183,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Deion Sanders is the only athlete to have played in both a Super Bowl and which other major sporting event?",
    "options": [
      "The Masters",
      "A Stanley Cup Final",
      "An NBA Finals game",
      "A World Series game"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 184,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which player won both the Heisman Trophy and, years later, an NFL MVP award?",
    "options": [
      "Johnny Manziel",
      "Marcus Mariota",
      "Robert Griffin III",
      "Cam Newton"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 185,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which quarterback won the Heisman Trophy at Oklahoma and later an NFL MVP award with the Cardinals?",
    "options": [
      "Baker Mayfield",
      "Jason White",
      "Sam Bradford",
      "Kyler Murray"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 186,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "O.J. Simpson won the Heisman at USC and later set the single-season rushing record with which NFL team?",
    "options": [
      "Kansas City Chiefs",
      "San Francisco 49ers",
      "Buffalo Bills",
      "Los Angeles Rams"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 187,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which player won Super Bowl MVP for his defensive dominance in Super Bowl 50?",
    "options": [
      "T.J. Ward",
      "Von Miller",
      "Aqib Talib",
      "DeMarcus Ware"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 188,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Santonio Holmes won Super Bowl XLIII MVP for a game-winning touchdown catch against which team?",
    "options": [
      "Arizona Cardinals",
      "Green Bay Packers",
      "Carolina Panthers",
      "Seattle Seahawks"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 189,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Hines Ward won Super Bowl XL MVP playing which position for the Steelers?",
    "options": [
      "Quarterback",
      "Running Back",
      "Wide Receiver",
      "Tight End"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 190,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which linebacker won Super Bowl XXXV MVP anchoring the Baltimore Ravens' historic defense?",
    "options": [
      "Ray Lewis",
      "Peter Boulware",
      "Terrell Suggs",
      "Ed Reed"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 191,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which player won Super Bowl XLVIII MVP with a pick-six interception return for the Seahawks?",
    "options": [
      "Malcolm Smith",
      "Kam Chancellor",
      "Richard Sherman",
      "Earl Thomas"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 192,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Julian Edelman won Super Bowl LIII MVP despite the Patriots' offense managing very few points, against which opponent?",
    "options": [
      "Philadelphia Eagles",
      "Los Angeles Rams",
      "Atlanta Falcons",
      "Seattle Seahawks"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 193,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Cooper Kupp won Super Bowl LVI MVP catching the game-winning touchdown for which team?",
    "options": [
      "Cincinnati Bengals",
      "Los Angeles Rams",
      "San Francisco 49ers",
      "Tampa Bay Buccaneers"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 194,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Tom Brady won Super Bowl MVP honors with two different franchises. Which was the second team?",
    "options": [
      "Miami Dolphins",
      "Tampa Bay Buccaneers",
      "San Francisco 49ers",
      "Kansas City Chiefs"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 195,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Terrell Davis won Super Bowl XXXII MVP rushing for the Broncos against which heavily favored opponent?",
    "options": [
      "Pittsburgh Steelers",
      "Green Bay Packers",
      "New England Patriots",
      "San Francisco 49ers"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 196,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Desmond Howard won Super Bowl XXXI MVP as a return specialist for which team?",
    "options": [
      "Dallas Cowboys",
      "Green Bay Packers",
      "Denver Broncos",
      "New England Patriots"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 197,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Marcus Allen's dazzling touchdown run in Super Bowl XVIII earned him MVP honors for which team?",
    "options": [
      "Miami Dolphins",
      "San Diego Chargers",
      "Los Angeles Raiders",
      "Washington Redskins"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 198,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which quarterback won Super Bowl MVP honors in Super Bowl XV while leading the wild-card Oakland Raiders?",
    "options": [
      "Marc Wilson",
      "Jim Plunkett",
      "Dan Pastorini",
      "Ken Stabler"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 199,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Franco Harris, famous for the 'Immaculate Reception,' won Super Bowl MVP honors in which Super Bowl?",
    "options": [
      "Super Bowl XIV",
      "Super Bowl IX",
      "Super Bowl X",
      "Super Bowl XIII"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 200,
    "category": "Awards, MVPs & Hall of Fame",
    "difficulty": "Hard",
    "question": "Which safety, playing for Tampa Bay, won Super Bowl XXXVII MVP with two interceptions, including a pick-six?",
    "options": [
      "Ronde Barber",
      "Dexter Jackson",
      "Simeon Rice",
      "John Lynch"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 202,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "'The Catch,' Dwight Clark's famous touchdown grab, sent which team to Super Bowl XVI?",
    "options": [
      "Los Angeles Rams",
      "San Francisco 49ers",
      "Dallas Cowboys",
      "Washington Redskins"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 203,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "'The Catch' came in the 1981 NFC Championship Game, defeating which team?",
    "options": [
      "Atlanta Falcons",
      "Green Bay Packers",
      "Dallas Cowboys",
      "Minnesota Vikings"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 204,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Music City Miracle' lateral play propelled the Titans past which team in the 1999 playoffs?",
    "options": [
      "Buffalo Bills",
      "Miami Dolphins",
      "Jacksonville Jaguars",
      "Indianapolis Colts"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 205,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Ice Bowl,' the brutally cold 1967 NFL Championship Game, featured the Packers against which team?",
    "options": [
      "Baltimore Colts",
      "Cleveland Browns",
      "Los Angeles Rams",
      "Dallas Cowboys"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 206,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The controversial 'Fail Mary' replacement-referee call happened in a 2012 game involving which two teams?",
    "options": [
      "San Francisco 49ers and Arizona Cardinals",
      "Seattle Seahawks and Green Bay Packers",
      "Denver Broncos and Baltimore Ravens",
      "Detroit Lions and Chicago Bears"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 207,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Minneapolis Miracle,' a walk-off touchdown from Case Keenum to Stefon Diggs, beat which team in the 2017 playoffs?",
    "options": [
      "New Orleans Saints",
      "Carolina Panthers",
      "Atlanta Falcons",
      "Philadelphia Eagles"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 208,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 1958 NFL Championship Game, often called 'The Greatest Game Ever Played,' was won in sudden-death overtime by which team?",
    "options": [
      "Cleveland Browns",
      "Baltimore Colts",
      "Detroit Lions",
      "New York Giants"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 209,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 1958 Championship Game overtime win helped cement the legend of which quarterback?",
    "options": [
      "Y.A. Tittle",
      "Bobby Layne",
      "Johnny Unitas",
      "Norm Van Brocklin"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 210,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Tuck Rule Game' snowstorm thriller between the Raiders and Patriots occurred following which NFL season?",
    "options": [
      "2001 season",
      "2002 season",
      "2000 season",
      "1999 season"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 211,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Which team completed the largest comeback in NFL playoff history at the time (32 points) against the Houston Oilers in January 1993?",
    "options": [
      "Buffalo Bills",
      "Kansas City Chiefs",
      "San Diego Chargers",
      "Pittsburgh Steelers"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 212,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Epic in Miami,' a 1981 playoff overtime thriller, was won by which team over the Dolphins?",
    "options": [
      "San Diego Chargers",
      "Pittsburgh Steelers",
      "New York Jets",
      "Buffalo Bills"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 213,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The controversial 'Holy Roller' forward-fumble play helped which team beat the Chargers in 1978?",
    "options": [
      "Kansas City Chiefs",
      "Denver Broncos",
      "Seattle Seahawks",
      "Oakland Raiders"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 214,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Which team's 2007 run as a wild-card entrant culminated in a Super Bowl XLII upset of the previously undefeated Patriots?",
    "options": [
      "Washington Redskins",
      "Green Bay Packers",
      "Philadelphia Eagles",
      "New York Giants"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 215,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Fog Bowl,' a 1988 playoff game played in near-zero visibility, featured the Bears against which team?",
    "options": [
      "Minnesota Vikings",
      "Los Angeles Rams",
      "San Francisco 49ers",
      "Philadelphia Eagles"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 216,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Dez Bryant's controversial overturned catch happened in a 2014 playoff loss to which team?",
    "options": [
      "Green Bay Packers",
      "Detroit Lions",
      "Carolina Panthers",
      "Seattle Seahawks"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 217,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'River City Relay,' a miraculous multi-lateral play, fell just short for the Saints against which team in 2003?",
    "options": [
      "Jacksonville Jaguars",
      "Carolina Panthers",
      "Atlanta Falcons",
      "Tennessee Titans"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 218,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Which team's 1990s dynasty included three Super Bowl titles in four seasons, led by Troy Aikman?",
    "options": [
      "San Francisco 49ers",
      "Green Bay Packers",
      "Dallas Cowboys",
      "Buffalo Bills"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 219,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Beast Quake' touchdown run by Marshawn Lynch happened in a 2010 playoff win for the Seahawks over which team?",
    "options": [
      "New Orleans Saints",
      "Atlanta Falcons",
      "Chicago Bears",
      "St. Louis Rams"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 220,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Adam Vinatieri's clutch kicks in the snowy 'Tuck Rule Game' helped the Patriots beat which team?",
    "options": [
      "Oakland Raiders",
      "Tennessee Titans",
      "Pittsburgh Steelers",
      "Indianapolis Colts"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 221,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Which team won the 2018 AFC Championship Game in overtime against the Chiefs, advancing to Super Bowl LIII?",
    "options": [
      "Pittsburgh Steelers",
      "Baltimore Ravens",
      "New England Patriots",
      "Jacksonville Jaguars"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 222,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Patrick Mahomes' legendary comeback in a shootout with the 49ers came in which Super Bowl?",
    "options": [
      "Super Bowl LVII",
      "Super Bowl LIV",
      "Super Bowl LVIII",
      "Super Bowl LV"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 223,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Which team blew a 19-point lead in the 2016 playoffs, one of the biggest collapses in postseason history, losing to the Falcons?",
    "options": [
      "Detroit Lions",
      "Seattle Seahawks",
      "Dallas Cowboys",
      "Green Bay Packers"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 224,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The Atlanta Falcons suffered the biggest collapse in Super Bowl history, blowing a 28-3 lead to which team in Super Bowl LI?",
    "options": [
      "Green Bay Packers",
      "Denver Broncos",
      "New England Patriots",
      "Pittsburgh Steelers"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 225,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'NOLA No-Call,' a controversial missed pass interference penalty, occurred in the 2019 NFC Championship between the Saints and which team?",
    "options": [
      "San Francisco 49ers",
      "Green Bay Packers",
      "Minnesota Vikings",
      "Los Angeles Rams"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 226,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Very Hard",
    "question": "The Jacksonville Jaguars overcame a 27-point deficit in the 2022 playoffs against which team, the largest comeback in NFL playoff history?",
    "options": [
      "Buffalo Bills",
      "Kansas City Chiefs",
      "Cincinnati Bengals",
      "Los Angeles Chargers"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 227,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Which quarterback led the Eagles to a Super Bowl LIX blowout win over the Chiefs, denying them a three-peat?",
    "options": [
      "Nick Foles",
      "Marcus Mariota",
      "Carson Wentz",
      "Jalen Hurts"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 229,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "Kevin Dyson scored the game-winning touchdown on the 'Music City Miracle' lateral, playing for which team?",
    "options": [
      "Buffalo Bills",
      "Baltimore Ravens",
      "Tennessee Titans",
      "Jacksonville Jaguars"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 230,
    "category": "Playoffs & Postseason Moments",
    "difficulty": "Hard",
    "question": "The 'Sea of Hands' playoff thriller in 1974 was a classic between the Dolphins and which team?",
    "options": [
      "Pittsburgh Steelers",
      "Cincinnati Bengals",
      "Denver Broncos",
      "Oakland Raiders"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 231,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Under current NFL playoff overtime rules (since 2022), what happens if the team that receives the ball first scores a touchdown?",
    "options": [
      "The game ends immediately",
      "Another coin toss occurs",
      "The game goes to a second overtime automatically",
      "The opposing team still gets a possession"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 232,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The 'tuck rule,' controversial and later repealed, once defined what action as an incomplete pass rather than a fumble?",
    "options": [
      "Any pass thrown from inside the pocket",
      "A lateral pass behind the line of scrimmage",
      "A quarterback pulling the ball back toward his body after cocking to throw",
      "A pass batted down at the line of scrimmage"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 233,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "In 1974, the NFL moved the goalposts from the goal line to where, changing kicking strategy?",
    "options": [
      "Ten yards behind the end zone",
      "The back of the end zone",
      "The 5-yard line",
      "Midfield for practice kicks only"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 234,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The two-point conversion was adopted by the NFL in which decade, long after it was used in college and the AFL?",
    "options": [
      "1990s",
      "1980s",
      "1970s",
      "1960s"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 235,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Instant replay review was permanently reinstated by NFL owners in what year, after an earlier trial run was dropped?",
    "options": [
      "2001",
      "1999",
      "1995",
      "1992"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 236,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The regular-season overtime period was shortened from 15 minutes to how many minutes starting in 2017?",
    "options": [
      "5 minutes",
      "10 minutes",
      "12 minutes",
      "8 minutes"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 237,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "AT&T Stadium, home of the Dallas Cowboys, is famous for its enormous what feature suspended above the field?",
    "options": [
      "A retractable roof only, with no scoreboard",
      "An indoor waterfall",
      "A massive video scoreboard",
      "A hanging garden display"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 238,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Which NFL stadium sits at the highest elevation in the league, giving home teams a 'thin air' advantage?",
    "options": [
      "Highmark Stadium",
      "Lambeau Field",
      "Empower Field at Mile High",
      "Arrowhead Stadium"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 239,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Which team's home stadium, Highmark Stadium, is notorious for brutal lake-effect snow games?",
    "options": [
      "New England Patriots",
      "Cleveland Browns",
      "Buffalo Bills",
      "Pittsburgh Steelers"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 240,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Which NFL franchise is unique in being a publicly owned, non-profit corporation rather than privately owned?",
    "options": [
      "Kansas City Chiefs",
      "Green Bay Packers",
      "Pittsburgh Steelers",
      "Buffalo Bills"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 241,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The 'Hail Mary' pass got its name from a famous 1975 playoff touchdown thrown by Roger Staubach to which receiver?",
    "options": [
      "Bob Hayes",
      "Drew Pearson",
      "Tony Hill",
      "Golden Richards"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 242,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The NFL football's nickname, 'The Duke,' honors which historical figure connected to the New York Giants?",
    "options": [
      "Pete Rozelle",
      "Tim Mara",
      "Wellington Mara",
      "Bert Bell"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 243,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The 'Immaculate Reception' controversy centers on whether the ball first touched which player before Franco Harris caught it?",
    "options": [
      "Terry Bradshaw",
      "John Fuqua's teammate",
      "Jack Tatum",
      "Frenchy Fuqua"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 244,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Roughing the passer and horse-collar tackle are examples of what type of penalty, carrying an automatic first down?",
    "options": [
      "Illegal formation",
      "Personal foul",
      "Delay of game",
      "Illegal contact"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 245,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "A 'Hail Mary' pass at the end of a half is typically thrown from around which area of the field?",
    "options": [
      "The 40-yard line of one's own territory",
      "The opponent's 5-yard line",
      "Deep in one's own end zone",
      "Near midfield"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 246,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The NFL's 'Rooney Rule,' requiring teams to interview minority candidates for head coaching jobs, was named after which longtime owner?",
    "options": [
      "Dan Rooney",
      "Lamar Hunt",
      "Wellington Mara",
      "Art Rooney"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 247,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Which stadium hosted the first-ever Super Bowl in 1967?",
    "options": [
      "Rice Stadium",
      "Tulane Stadium",
      "Los Angeles Memorial Coliseum",
      "Miami Orange Bowl"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 249,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "Before the 17-game season, the NFL had played a 16-game regular season schedule since which year?",
    "options": [
      "1990",
      "1978",
      "1985",
      "1970"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 250,
    "category": "Rules, Officiating & Stadiums",
    "difficulty": "Hard",
    "question": "The NFL-AFL merger, creating the modern AFC and NFC conference structure, was fully completed in which year?",
    "options": [
      "1968",
      "1975",
      "1970",
      "1966"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 251,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which team's mascot is a bucking bronco named 'Miles'?",
    "options": [
      "Kansas City Chiefs",
      "Dallas Cowboys",
      "Houston Texans",
      "Denver Broncos"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 252,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "The Baltimore Ravens are named after a famous poem by which author, a former Baltimore resident?",
    "options": [
      "Walt Whitman",
      "Herman Melville",
      "Nathaniel Hawthorne",
      "Edgar Allan Poe"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 253,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which team's name pays homage to steel production in its home city?",
    "options": [
      "Cleveland Browns",
      "Detroit Lions",
      "Pittsburgh Steelers",
      "Buffalo Bills"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 254,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "The Tennessee Titans' name replaced which original moniker after the franchise relocated from Houston?",
    "options": [
      "Nashville Sounds",
      "Houston Texans",
      "Tennessee Oilers",
      "Tennessee Football Club"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 260,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "The Dallas Cowboys Cheerleaders became a nationwide pop-culture phenomenon starting in which decade?",
    "options": [
      "1980s",
      "1970s",
      "1960s",
      "1990s"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 261,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which team's owner, Jerry Jones, famously fired Jimmy Johnson and hired Barry Switzer in the 1990s?",
    "options": [
      "Washington Redskins",
      "San Francisco 49ers",
      "Dallas Cowboys",
      "New York Giants"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 263,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which team's owner, Robert Kraft, purchased the franchise in 1994, transforming it into a modern dynasty?",
    "options": [
      "New York Jets",
      "Buffalo Bills",
      "New England Patriots",
      "Miami Dolphins"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 264,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which team is nicknamed 'America's Team,' a moniker earned largely in the 1970s?",
    "options": [
      "Green Bay Packers",
      "San Francisco 49ers",
      "New York Giants",
      "Dallas Cowboys"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 266,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which former NFL quarterback, a longtime broadcaster, won a Super Bowl with the Cowboys as a player?",
    "options": [
      "Danny White",
      "Roger Staubach",
      "Troy Aikman",
      "Tony Romo"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 268,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "The best-selling annual NFL video game franchise is named after which Hall of Fame coach turned broadcaster?",
    "options": [
      "Al Michaels",
      "Pat Summerall",
      "Bill Walsh",
      "John Madden"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 269,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "The 'Madden Curse' is a superstition claiming what effect on players who appear on the game's cover?",
    "options": [
      "They win the Super Bowl that season",
      "They are traded within a year",
      "They suffer notable injuries or a decline in performance the following season",
      "They retire early"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 270,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which team's 1970s 'No-Name Defense' helped anchor its perfect, undefeated season?",
    "options": [
      "Minnesota Vikings",
      "Los Angeles Rams",
      "Miami Dolphins",
      "Pittsburgh Steelers"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 271,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which quarterback's flashy persona and autobiography earned him the nickname 'Broadway Joe'?",
    "options": [
      "Terry Bradshaw",
      "Fran Tarkenton",
      "Kenny Stabler",
      "Joe Namath"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 272,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which rivalry, dating to 1921, is often called the oldest in NFL history?",
    "options": [
      "New York Giants vs. Washington Redskins",
      "Detroit Lions vs. Chicago Bears",
      "Pittsburgh Steelers vs. Cleveland Browns",
      "Chicago Bears vs. Green Bay Packers"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 274,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which team's blank, colored helmet has remained unchanged since the franchise's founding, a rare case in the NFL?",
    "options": [
      "Cleveland Browns",
      "Pittsburgh Steelers",
      "Cincinnati Bengals",
      "Baltimore Ravens"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 275,
    "category": "Miscellaneous & Team Culture",
    "difficulty": "Hard",
    "question": "Which franchise's original name honored owner Bud Adams's roots in the Texas oil industry, before the team eventually became the Titans?",
    "options": [
      "Detroit Lions",
      "Cleveland Browns",
      "Houston/Tennessee Oilers",
      "Buffalo Bills"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 277,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Bruce Smith recorded the bulk of his career-record sacks with which team?",
    "options": [
      "Buffalo Bills",
      "Miami Dolphins",
      "Washington Redskins",
      "New York Jets"
    ],
    "correctIndex": 0,
    "notes": ""
  },
  {
    "id": 281,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Paul Krause set his career interception record largely as a safety for which team?",
    "options": [
      "Washington Redskins",
      "Chicago Bears",
      "Minnesota Vikings",
      "Green Bay Packers"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 282,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Dick 'Night Train' Lane set the single-season interception record (14) during his rookie season. In what year?",
    "options": [
      "1948",
      "1960",
      "1956",
      "1952"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 283,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Which cornerback is nicknamed 'Night Train' and holds the NFL rookie interception record?",
    "options": [
      "Herb Adderley",
      "Dick Lane",
      "Willie Brown",
      "Mel Blount"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 285,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Deacon Jones played the majority of his dominant career for which team's 'Fearsome Foursome' defensive line?",
    "options": [
      "Pittsburgh Steelers",
      "Los Angeles Rams",
      "Dallas Cowboys",
      "Minnesota Vikings"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 287,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Reggie White, nicknamed the 'Minister of Defense,' is second all-time in career sacks. He starred for which two teams?",
    "options": [
      "Philadelphia Eagles and Dallas Cowboys",
      "Philadelphia Eagles and Green Bay Packers",
      "Carolina Panthers and Philadelphia Eagles",
      "Green Bay Packers and Minnesota Vikings"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 290,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Justin Tucker's record-breaking 66-yard field goal as time expired came against which team?",
    "options": [
      "Cleveland Browns",
      "Green Bay Packers",
      "Detroit Lions",
      "Chicago Bears"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 293,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "The record-setting 2000 Baltimore Ravens defense won the Super Bowl behind which Defensive Player of the Year?",
    "options": [
      "Peter Boulware",
      "Rod Woodson",
      "Ray Lewis",
      "Sam Adams"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 294,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Which team's 1985 defense, coordinated by Buddy Ryan, is considered among the greatest ever, powering a Super Bowl XX win?",
    "options": [
      "Minnesota Vikings",
      "New York Giants",
      "Philadelphia Eagles",
      "Chicago Bears"
    ],
    "correctIndex": 3,
    "notes": ""
  },
  {
    "id": 297,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Devin Hester also holds the combined punt-and-kick return touchdown record, playing most of his career for which team?",
    "options": [
      "Atlanta Falcons",
      "Chicago Bears",
      "Baltimore Ravens",
      "Seattle Seahawks"
    ],
    "correctIndex": 1,
    "notes": ""
  },
  {
    "id": 299,
    "category": "Defense & Special Teams Records",
    "difficulty": "Hard",
    "question": "Tom Dempsey's historic 63-yard field goal was remarkable because he kicked with what unique physical trait?",
    "options": [
      "Complete blindness in one eye",
      "No use of his non-kicking arm",
      "A partially amputated kicking foot, using a specially designed shoe",
      "A prosthetic leg"
    ],
    "correctIndex": 2,
    "notes": ""
  },
  {
    "id": 301,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which Super Bowl was the first played in a domed stadium?",
    "options": [
      "Super Bowl X",
      "Super Bowl XII",
      "Super Bowl VIII",
      "Super Bowl XIV"
    ],
    "correctIndex": 1,
    "notes": "Louisiana Superdome"
  },
  {
    "id": 303,
    "category": "Super Bowl History",
    "difficulty": "Very Hard",
    "question": "In Super Bowl III the Jets stopped which Colts fullback on a key 4th-and-1?",
    "options": [
      "Tom Matte",
      "Norm Bulaich",
      "Don Shinnick",
      "Jerry Hill"
    ],
    "correctIndex": 0,
    "notes": "Tom Matte"
  },
  {
    "id": 304,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which Super Bowl MVP never played a down on offense that game?",
    "options": [
      "Chuck Howley",
      "Randy White",
      "Harvey Martin",
      "Jake Scott"
    ],
    "correctIndex": 0,
    "notes": "Super Bowl V"
  },
  {
    "id": 305,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The first overtime Super Bowl was which game?",
    "options": [
      "Super Bowl XLIII",
      "Super Bowl XXXVIII",
      "Super Bowl LI",
      "Super Bowl XXV"
    ],
    "correctIndex": 2,
    "notes": "Patriots vs Falcons"
  },
  {
    "id": 306,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who threw the first touchdown pass in Super Bowl history?",
    "options": [
      "Len Dawson",
      "Bart Starr",
      "Johnny Unitas",
      "Max McGee"
    ],
    "correctIndex": 1,
    "notes": "Starr to Max McGee"
  },
  {
    "id": 307,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which Super Bowl was delayed more than 30 minutes by a power outage?",
    "options": [
      "Super Bowl XLVIII",
      "Super Bowl XLVII",
      "Super Bowl XLVI",
      "Super Bowl XLV"
    ],
    "correctIndex": 1,
    "notes": "Harbaugh Bowl"
  },
  {
    "id": 308,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who holds the record for most Super Bowl appearances by a non-quarterback?",
    "options": [
      "Marv Fleming",
      "Jerry Rice",
      "Mike Webster",
      "Charlie Waters"
    ],
    "correctIndex": 1,
    "notes": "Four appearances"
  },
  {
    "id": 309,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which defensive player returned an INT for a TD in a Super Bowl and later became a head coach?",
    "options": [
      "Mike Ditka",
      "Tony Dungy",
      "Mike Singletary",
      "Herm Edwards"
    ],
    "correctIndex": 1,
    "notes": "Tony Dungy with Steelers"
  },
  {
    "id": 310,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who caught the game-winning TD from Joe Montana in Super Bowl XXIII?",
    "options": [
      "Brent Jones",
      "Roger Craig",
      "John Taylor",
      "Jerry Rice"
    ],
    "correctIndex": 2,
    "notes": "John Taylor"
  },
  {
    "id": 311,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The Immaculate Reception happened in a playoff game against which team?",
    "options": [
      "Denver Broncos",
      "Oakland Raiders",
      "Houston Oilers",
      "Dallas Cowboys"
    ],
    "correctIndex": 1,
    "notes": "Raiders"
  },
  {
    "id": 312,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which Super Bowl is remembered for David Tyree's Helmet Catch?",
    "options": [
      "Super Bowl XLIII",
      "Super Bowl XLI",
      "Super Bowl XLII",
      "Super Bowl XLVI"
    ],
    "correctIndex": 2,
    "notes": "Giants vs Patriots"
  },
  {
    "id": 313,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who returned a kickoff 108 yards for a TD in Super Bowl XLVII?",
    "options": [
      "Randall Cobb",
      "Devin Hester",
      "Jacoby Jones",
      "Ted Ginn Jr."
    ],
    "correctIndex": 2,
    "notes": "Jacoby Jones"
  },
  {
    "id": 314,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which QB was named Super Bowl MVP despite throwing zero TD passes?",
    "options": [
      "Len Dawson",
      "Bart Starr",
      "Joe Namath",
      "Roger Staubach"
    ],
    "correctIndex": 2,
    "notes": "Super Bowl III"
  },
  {
    "id": 315,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "The Philly Special trick play occurred in which Super Bowl?",
    "options": [
      "Super Bowl LII",
      "Super Bowl LIV",
      "Super Bowl LI",
      "Super Bowl LIII"
    ],
    "correctIndex": 0,
    "notes": "Eagles vs Patriots"
  },
  {
    "id": 316,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which Super Bowl had the highest combined point total?",
    "options": [
      "Super Bowl XIII",
      "Super Bowl LII",
      "Super Bowl XXIX",
      "Super Bowl XI"
    ],
    "correctIndex": 2,
    "notes": "75 points"
  },
  {
    "id": 317,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl IV, the last pre-merger AFL-NFL title game?",
    "options": [
      "Minnesota Vikings",
      "New York Jets",
      "Kansas City Chiefs",
      "Baltimore Colts"
    ],
    "correctIndex": 2,
    "notes": "Chiefs over Vikings"
  },
  {
    "id": 318,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who was MVP of Super Bowl XXXIV (Greatest Show on Turf)?",
    "options": [
      "London Fletcher",
      "Isaac Bruce",
      "Kurt Warner",
      "Marshall Faulk"
    ],
    "correctIndex": 2,
    "notes": "Kurt Warner"
  },
  {
    "id": 319,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who caught the winning TD in Super Bowl XLII for the Giants?",
    "options": [
      "Amani Toomer",
      "Plaxico Burress",
      "Steve Smith",
      "David Tyree"
    ],
    "correctIndex": 1,
    "notes": "Plaxico Burress"
  },
  {
    "id": 320,
    "category": "Super Bowl History",
    "difficulty": "Very Hard",
    "question": "Which Super Bowl was the first decided by a last-second field goal?",
    "options": [
      "Super Bowl V",
      "Super Bowl XXV",
      "Super Bowl XXXVIII",
      "Super Bowl XXXVI"
    ],
    "correctIndex": 3,
    "notes": "Vinatieri in XXXVI"
  },
  {
    "id": 321,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which franchise has the most losses in NFL history?",
    "options": [
      "Tampa Bay Buccaneers",
      "Cleveland Browns",
      "Arizona Cardinals",
      "Detroit Lions"
    ],
    "correctIndex": 2,
    "notes": "Including Chicago/St. Louis eras"
  },
  {
    "id": 322,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which expansion team made the playoffs in its second season?",
    "options": [
      "Houston Texans",
      "Tampa Bay Buccaneers",
      "Carolina Panthers",
      "Jacksonville Jaguars"
    ],
    "correctIndex": 2,
    "notes": "1996 Panthers"
  },
  {
    "id": 323,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Cleveland Browns' last pre-Super Bowl NFL championship came in which year?",
    "options": [
      "1955",
      "1964",
      "1965",
      "1957"
    ],
    "correctIndex": 1,
    "notes": "1964 vs Colts"
  },
  {
    "id": 324,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the most consecutive Super Bowl appearances?",
    "options": [
      "Buffalo Bills",
      "Dallas Cowboys",
      "New England Patriots",
      "Miami Dolphins"
    ],
    "correctIndex": 0,
    "notes": "Four straight 1991-94"
  },
  {
    "id": 325,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which franchise began as the Portsmouth Spartans?",
    "options": [
      "Chicago Bears",
      "Cleveland Browns",
      "Green Bay Packers",
      "Detroit Lions"
    ],
    "correctIndex": 3,
    "notes": "Moved to Detroit"
  },
  {
    "id": 326,
    "category": "Franchise & Team Records",
    "difficulty": "Very Hard",
    "question": "The NFL's first sudden-death overtime game occurred in which year?",
    "options": [
      "1962",
      "1943",
      "1974",
      "1958"
    ],
    "correctIndex": 3,
    "notes": "1958 NFL Championship"
  },
  {
    "id": 327,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the most playoff wins without a Super Bowl title?",
    "options": [
      "Minnesota Vikings",
      "Buffalo Bills",
      "Cincinnati Bengals",
      "Tennessee Titans"
    ],
    "correctIndex": 0,
    "notes": "Vikings"
  },
  {
    "id": 328,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which current NFL stadium has the highest seating capacity?",
    "options": [
      "Lambeau Field",
      "MetLife Stadium",
      "AT&T Stadium",
      "Arrowhead Stadium"
    ],
    "correctIndex": 2,
    "notes": "Cowboys stadium"
  },
  {
    "id": 329,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team holds the record for most points scored in a single regular-season game?",
    "options": [
      "Chicago Bears",
      "New England Patriots",
      "Washington",
      "Los Angeles Rams"
    ],
    "correctIndex": 2,
    "notes": "72 vs Giants 1966"
  },
  {
    "id": 330,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which franchise was originally the AFL Dallas Texans?",
    "options": [
      "Denver Broncos",
      "Houston Oilers",
      "Dallas Cowboys",
      "Kansas City Chiefs"
    ],
    "correctIndex": 3,
    "notes": "Moved to KC"
  },
  {
    "id": 331,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Ice Bowl was played in which year?",
    "options": [
      "1968",
      "1966",
      "1967",
      "1972"
    ],
    "correctIndex": 2,
    "notes": "1967 NFL Championship"
  },
  {
    "id": 332,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team was first to win three Super Bowls in four years?",
    "options": [
      "New England Patriots",
      "Pittsburgh Steelers",
      "Dallas Cowboys",
      "San Francisco 49ers"
    ],
    "correctIndex": 1,
    "notes": "Steelers 1974-79"
  },
  {
    "id": 333,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Greatest Show on Turf played in which city?",
    "options": [
      "Los Angeles",
      "San Diego",
      "St. Louis",
      "Indianapolis"
    ],
    "correctIndex": 2,
    "notes": "St. Louis Rams"
  },
  {
    "id": 334,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the most Super Bowl losses?",
    "options": [
      "Denver Broncos",
      "Buffalo Bills",
      "New England Patriots",
      "Minnesota Vikings"
    ],
    "correctIndex": 0,
    "notes": "Five losses"
  },
  {
    "id": 335,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the most Super Bowl appearances without a win?",
    "options": [
      "Cincinnati Bengals",
      "Buffalo Bills",
      "Minnesota Vikings",
      "Atlanta Falcons"
    ],
    "correctIndex": 2,
    "notes": "0-4"
  },
  {
    "id": 336,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "The Perfect Season Dolphins of 1972 were coached by whom?",
    "options": [
      "John Madden",
      "Chuck Noll",
      "Tom Landry",
      "Don Shula"
    ],
    "correctIndex": 3,
    "notes": "Don Shula"
  },
  {
    "id": 337,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team holds the record for most consecutive playoff appearances?",
    "options": [
      "New England Patriots",
      "Dallas Cowboys",
      "San Francisco 49ers",
      "Green Bay Packers"
    ],
    "correctIndex": 0,
    "notes": "11 under Belichick"
  },
  {
    "id": 339,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team went 0-16 in 2008, first to lose all 16 games?",
    "options": [
      "Cleveland Browns",
      "Oakland Raiders",
      "Detroit Lions",
      "St. Louis Rams"
    ],
    "correctIndex": 2,
    "notes": "Lions"
  },
  {
    "id": 340,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team finished 16-0 in the regular season in 2007?",
    "options": [
      "San Francisco 49ers",
      "New England Patriots",
      "Chicago Bears",
      "Miami Dolphins"
    ],
    "correctIndex": 1,
    "notes": "Patriots"
  },
  {
    "id": 341,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the NFL record for most career rushing touchdowns?",
    "options": [
      "Jim Brown",
      "Emmitt Smith",
      "LaDainian Tomlinson",
      "Marcus Allen"
    ],
    "correctIndex": 1,
    "notes": "164"
  },
  {
    "id": 342,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which QB holds the record for most consecutive games with a TD pass?",
    "options": [
      "Peyton Manning",
      "Drew Brees",
      "Johnny Unitas",
      "Tom Brady"
    ],
    "correctIndex": 1,
    "notes": "54 games"
  },
  {
    "id": 343,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who is the only player to lead the NFL in both rushing and receiving yards in the same season?",
    "options": [
      "Christian McCaffrey",
      "Billy Cannon",
      "Marshall Faulk",
      "Roger Craig"
    ],
    "correctIndex": 2,
    "notes": "1999 Faulk"
  },
  {
    "id": 344,
    "category": "Player Records",
    "difficulty": "Very Hard",
    "question": "Which RB holds the record for most consecutive 1,000-yard rushing seasons?",
    "options": [
      "Walter Payton",
      "Emmitt Smith",
      "Barry Sanders",
      "Curtis Martin"
    ],
    "correctIndex": 2,
    "notes": "10 seasons"
  },
  {
    "id": 345,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the single-season receiving yards record?",
    "options": [
      "Cooper Kupp",
      "Julio Jones",
      "Calvin Johnson",
      "Jerry Rice"
    ],
    "correctIndex": 2,
    "notes": "1,964 in 2012"
  },
  {
    "id": 346,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which QB threw for the most yards in a single Super Bowl?",
    "options": [
      "Kurt Warner",
      "Peyton Manning",
      "Joe Montana",
      "Tom Brady"
    ],
    "correctIndex": 0,
    "notes": "414 yards"
  },
  {
    "id": 347,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the record for most career INT return touchdowns?",
    "options": [
      "Deion Sanders",
      "Rod Woodson",
      "Charles Woodson",
      "Aeneas Williams"
    ],
    "correctIndex": 1,
    "notes": "12"
  },
  {
    "id": 348,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which kicker holds the record for most consecutive field goals made?",
    "options": [
      "Adam Vinatieri",
      "Mike Vanderjagt",
      "Matt Stover",
      "Justin Tucker"
    ],
    "correctIndex": 1,
    "notes": "42"
  },
  {
    "id": 349,
    "category": "Player Records",
    "difficulty": "Very Hard",
    "question": "Who is the only undrafted player to win NFL MVP?",
    "options": [
      "Jeff Garcia",
      "Tony Romo",
      "Kurt Warner",
      "Rich Gannon"
    ],
    "correctIndex": 2,
    "notes": "1999"
  },
  {
    "id": 350,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which TE holds the record for most career receiving TDs at the position?",
    "options": [
      "Tony Gonzalez",
      "Antonio Gates",
      "Rob Gronkowski",
      "Shannon Sharpe"
    ],
    "correctIndex": 1,
    "notes": "116"
  },
  {
    "id": 351,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which QB holds the record for most career rushing TDs by a quarterback?",
    "options": [
      "Lamar Jackson",
      "Steve Young",
      "Cam Newton",
      "Randall Cunningham"
    ],
    "correctIndex": 2,
    "notes": "75"
  },
  {
    "id": 352,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the single-game receiving yards record?",
    "options": [
      "Jerry Rice",
      "Julio Jones",
      "Calvin Johnson",
      "Flipper Anderson"
    ],
    "correctIndex": 3,
    "notes": "336 in 1989"
  },
  {
    "id": 353,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the record for most career pass completions?",
    "options": [
      "Tom Brady",
      "Peyton Manning",
      "Drew Brees",
      "Brett Favre"
    ],
    "correctIndex": 0,
    "notes": "Tom Brady"
  },
  {
    "id": 354,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the record for most consecutive starts by a QB?",
    "options": [
      "Philip Rivers",
      "Peyton Manning",
      "Tom Brady",
      "Brett Favre"
    ],
    "correctIndex": 3,
    "notes": "297"
  },
  {
    "id": 355,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which WR has the most career receptions?",
    "options": [
      "Tony Gonzalez",
      "Jason Witten",
      "Jerry Rice",
      "Larry Fitzgerald"
    ],
    "correctIndex": 2,
    "notes": "Jerry Rice"
  },
  {
    "id": 356,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who was the first player to rush for 200 yards in a Super Bowl?",
    "options": [
      "Timmy Smith",
      "Marcus Allen",
      "Terrell Davis",
      "Emmitt Smith"
    ],
    "correctIndex": 0,
    "notes": "Super Bowl XXII"
  },
  {
    "id": 357,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the single-season record for most total touchdowns?",
    "options": [
      "LaDainian Tomlinson",
      "Priest Holmes",
      "Shaun Alexander",
      "Emmitt Smith"
    ],
    "correctIndex": 0,
    "notes": "31 in 2006"
  },
  {
    "id": 358,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which TE has the most career receptions?",
    "options": [
      "Travis Kelce",
      "Tony Gonzalez",
      "Antonio Gates",
      "Jason Witten"
    ],
    "correctIndex": 1,
    "notes": "Tony Gonzalez"
  },
  {
    "id": 359,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the record for most career pass attempts?",
    "options": [
      "Drew Brees",
      "Peyton Manning",
      "Brett Favre",
      "Tom Brady"
    ],
    "correctIndex": 3,
    "notes": "Tom Brady"
  },
  {
    "id": 360,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which RB has the most career 100-yard rushing games?",
    "options": [
      "Barry Sanders",
      "Emmitt Smith",
      "Jim Brown",
      "Walter Payton"
    ],
    "correctIndex": 1,
    "notes": "Emmitt Smith"
  },
  {
    "id": 361,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which WR holds the record for most consecutive games with a reception?",
    "options": [
      "Marvin Harrison",
      "Jerry Rice",
      "Tim Brown",
      "Larry Fitzgerald"
    ],
    "correctIndex": 1,
    "notes": "274"
  },
  {
    "id": 362,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which college has produced the most No. 1 overall NFL Draft picks?",
    "options": [
      "Ohio State",
      "Notre Dame",
      "Alabama",
      "USC"
    ],
    "correctIndex": 1,
    "notes": "Five"
  },
  {
    "id": 363,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "The 1983 Draft produced how many Hall of Fame QBs in the first round?",
    "options": [
      "2",
      "3",
      "4",
      "5"
    ],
    "correctIndex": 1,
    "notes": "Elway, Marino, Kelly"
  },
  {
    "id": 364,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the Texans' inaugural 2002 draft?",
    "options": [
      "Andre Johnson",
      "David Carr",
      "Mario Williams",
      "Domanick Davis"
    ],
    "correctIndex": 1,
    "notes": "David Carr"
  },
  {
    "id": 365,
    "category": "Draft & College",
    "difficulty": "Very Hard",
    "question": "Who was the first overall pick of the 1998 NFL Draft?",
    "options": [
      "Charles Woodson",
      "Peyton Manning",
      "Randy Moss",
      "Ryan Leaf"
    ],
    "correctIndex": 1,
    "notes": "Peyton Manning"
  },
  {
    "id": 366,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "The 2004 QB class included Eli Manning, Philip Rivers and which other first-round QB?",
    "options": [
      "Ben Roethlisberger",
      "Kyle Orton",
      "J.P. Losman",
      "Matt Schaub"
    ],
    "correctIndex": 0,
    "notes": "Ben Roethlisberger"
  },
  {
    "id": 367,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which WR was selected 21st overall by the Vikings in 1998 and became a star?",
    "options": [
      "Plaxico Burress",
      "Randy Moss",
      "Larry Fitzgerald",
      "Torry Holt"
    ],
    "correctIndex": 1,
    "notes": "Randy Moss"
  },
  {
    "id": 368,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 2011 NFL Draft?",
    "options": [
      "Cam Newton",
      "Von Miller",
      "Patrick Peterson",
      "A.J. Green"
    ],
    "correctIndex": 0,
    "notes": "Cam Newton"
  },
  {
    "id": 369,
    "category": "Draft & College",
    "difficulty": "Very Hard",
    "question": "Which DE was taken No. 1 overall by the Browns in 2000?",
    "options": [
      "LaVar Arrington",
      "Julian Peterson",
      "Brian Urlacher",
      "Courtney Brown"
    ],
    "correctIndex": 3,
    "notes": "Courtney Brown"
  },
  {
    "id": 370,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "The 2007 first overall pick was which OT?",
    "options": [
      "Jake Long",
      "Joe Thomas",
      "Duane Brown",
      "Ryan Clady"
    ],
    "correctIndex": 0,
    "notes": "Jake Long (Miami)"
  },
  {
    "id": 371,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which Heisman winner was No. 1 overall to the Buccaneers in 2015?",
    "options": [
      "Amari Cooper",
      "Jameis Winston",
      "Marcus Mariota",
      "Derrick Henry"
    ],
    "correctIndex": 1,
    "notes": "Jameis Winston"
  },
  {
    "id": 372,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was No. 1 overall in the 2012 Draft?",
    "options": [
      "Andrew Luck",
      "Ryan Tannehill",
      "Morris Claiborne",
      "Robert Griffin III"
    ],
    "correctIndex": 0,
    "notes": "Andrew Luck (Colts)"
  },
  {
    "id": 373,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 1990 Draft?",
    "options": [
      "Emmitt Smith",
      "Junior Seau",
      "Jeff George",
      "Cortez Kennedy"
    ],
    "correctIndex": 2,
    "notes": "Jeff George"
  },
  {
    "id": 374,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who did the Browns select No. 1 overall in 2017?",
    "options": [
      "Leonard Fournette",
      "Solomon Thomas",
      "Mitchell Trubisky",
      "Myles Garrett"
    ],
    "correctIndex": 3,
    "notes": "Myles Garrett"
  },
  {
    "id": 375,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was No. 1 overall in the 2020 Draft?",
    "options": [
      "Chase Young",
      "Joe Burrow",
      "Jeff Okudah",
      "Tua Tagovailoa"
    ],
    "correctIndex": 1,
    "notes": "Joe Burrow"
  },
  {
    "id": 376,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was No. 1 overall in the 2021 Draft?",
    "options": [
      "Justin Fields",
      "Zach Wilson",
      "Trey Lance",
      "Trevor Lawrence"
    ],
    "correctIndex": 3,
    "notes": "Trevor Lawrence"
  },
  {
    "id": 377,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which RB was No. 1 overall in 1995?",
    "options": [
      "Rashaan Salaam",
      "Ki-Jana Carter",
      "Tyrone Wheatley",
      "Napoleon Kaufman"
    ],
    "correctIndex": 1,
    "notes": "Ki-Jana Carter"
  },
  {
    "id": 378,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which DE was No. 1 overall by the Texans in 2006?",
    "options": [
      "A.J. Hawk",
      "Mario Williams",
      "Reggie Bush",
      "Vince Young"
    ],
    "correctIndex": 1,
    "notes": "Mario Williams"
  },
  {
    "id": 379,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was No. 1 overall in 1999?",
    "options": [
      "Edgerrin James",
      "Donovan McNabb",
      "Akili Smith",
      "Tim Couch"
    ],
    "correctIndex": 3,
    "notes": "Tim Couch"
  },
  {
    "id": 380,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which OT was No. 1 overall by the Dolphins in 2008?",
    "options": [
      "Jake Long",
      "Duane Brown",
      "Ryan Clady",
      "Joe Thomas"
    ],
    "correctIndex": 0,
    "notes": "Jake Long"
  },
  {
    "id": 381,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "The 2013 No. 1 overall pick was which OT?",
    "options": [
      "Dee Milliner",
      "Luke Joeckel",
      "Eric Fisher",
      "Lane Johnson"
    ],
    "correctIndex": 2,
    "notes": "Eric Fisher"
  },
  {
    "id": 382,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which QB was drafted No. 1 by the Falcons in 1991 and never started for them?",
    "options": [
      "Chris Chandler",
      "Bobby Hebert",
      "Brett Favre",
      "Jeff George"
    ],
    "correctIndex": 2,
    "notes": "Traded to Packers"
  },
  {
    "id": 383,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which player holds the record for most career forced fumbles?",
    "options": [
      "John Abraham",
      "Charles Haley",
      "Julius Peppers",
      "Robert Mathis"
    ],
    "correctIndex": 3,
    "notes": "52"
  },
  {
    "id": 384,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who recorded the most sacks in a single postseason?",
    "options": [
      "Willie McGinest",
      "Bruce Smith",
      "Michael Strahan",
      "Reggie White"
    ],
    "correctIndex": 0,
    "notes": "4.5 in 2001"
  },
  {
    "id": 385,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "The Purple People Eaters played for which franchise?",
    "options": [
      "Baltimore Ravens",
      "Chicago Bears",
      "Pittsburgh Steelers",
      "Minnesota Vikings"
    ],
    "correctIndex": 3,
    "notes": "Vikings"
  },
  {
    "id": 386,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who is the only punter in the Pro Football Hall of Fame?",
    "options": [
      "Jeff Feagles",
      "Sean Landeta",
      "Ray Guy",
      "Shane Lechler"
    ],
    "correctIndex": 2,
    "notes": "Ray Guy"
  },
  {
    "id": 387,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which team's defense was nicknamed the Doomsday Defense?",
    "options": [
      "Pittsburgh Steelers",
      "Dallas Cowboys",
      "Los Angeles Rams",
      "Minnesota Vikings"
    ],
    "correctIndex": 1,
    "notes": "Cowboys"
  },
  {
    "id": 388,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who holds the record for most career interceptions?",
    "options": [
      "Ronde Barber",
      "Dick Lane",
      "Paul Krause",
      "Rod Woodson"
    ],
    "correctIndex": 2,
    "notes": "81"
  },
  {
    "id": 389,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who set the single-season sack record with 22.5 in 1984?",
    "options": [
      "Lawrence Taylor",
      "Mark Gastineau",
      "Reggie White",
      "Deacon Jones"
    ],
    "correctIndex": 1,
    "notes": "Mark Gastineau"
  },
  {
    "id": 390,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Michael Strahan matched the single-season sack record in which year?",
    "options": [
      "2003",
      "2005",
      "2001",
      "1999"
    ],
    "correctIndex": 2,
    "notes": "2001"
  },
  {
    "id": 391,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which Hall of Famer is credited with coining the term sack?",
    "options": [
      "Bruce Smith",
      "Deacon Jones",
      "Carl Eller",
      "Reggie White"
    ],
    "correctIndex": 1,
    "notes": "Deacon Jones"
  },
  {
    "id": 392,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Deacon Jones starred on which team's Fearsome Foursome?",
    "options": [
      "Minnesota Vikings",
      "Pittsburgh Steelers",
      "Dallas Cowboys",
      "Los Angeles Rams"
    ],
    "correctIndex": 3,
    "notes": "Rams"
  },
  {
    "id": 393,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which DT was nicknamed Mean Joe and anchored the Steel Curtain?",
    "options": [
      "Joe Greene",
      "L.C. Greenwood",
      "Jack Lambert",
      "Ernie Holmes"
    ],
    "correctIndex": 0,
    "notes": "Mean Joe Greene"
  },
  {
    "id": 394,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Reggie White starred primarily for which two teams?",
    "options": [
      "Packers and Vikings",
      "Eagles and Packers",
      "Panthers and Eagles",
      "Eagles and Cowboys"
    ],
    "correctIndex": 1,
    "notes": "Philadelphia and Green Bay"
  },
  {
    "id": 395,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who holds the NFL record for most career points scored?",
    "options": [
      "Adam Vinatieri",
      "Morten Andersen",
      "Justin Tucker",
      "Jason Hanson"
    ],
    "correctIndex": 0,
    "notes": "Adam Vinatieri"
  },
  {
    "id": 396,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who holds the record for longest field goal in NFL history (66 yards)?",
    "options": [
      "Brandon McManus",
      "Graham Gano",
      "Justin Tucker",
      "Matt Prater"
    ],
    "correctIndex": 2,
    "notes": "2021 vs Lions"
  },
  {
    "id": 397,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "The Ray Guy Award is named for a Hall of Fame punter who played for which team?",
    "options": [
      "Pittsburgh Steelers",
      "Miami Dolphins",
      "Oakland Raiders",
      "Dallas Cowboys"
    ],
    "correctIndex": 2,
    "notes": "Raiders"
  },
  {
    "id": 398,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which team's 2000 defense set the record for fewest points allowed in a 16-game season?",
    "options": [
      "Pittsburgh Steelers",
      "Chicago Bears",
      "Baltimore Ravens",
      "Tampa Bay Buccaneers"
    ],
    "correctIndex": 2,
    "notes": "Ravens"
  },
  {
    "id": 399,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "The 1985 Bears defense was known as the?",
    "options": [
      "4-3 Under",
      "Cover 3 Blitz",
      "Tampa 2",
      "46 Defense"
    ],
    "correctIndex": 3,
    "notes": "46 Defense"
  },
  {
    "id": 400,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who holds the record for most career punt return TDs?",
    "options": [
      "Josh Cribbs",
      "Dante Hall",
      "Cordarrelle Patterson",
      "Devin Hester"
    ],
    "correctIndex": 3,
    "notes": "14"
  },
  {
    "id": 401,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which kicker made a then-record 63-yard FG in 1970?",
    "options": [
      "Toni Fritsch",
      "Jan Stenerud",
      "Garo Yepremian",
      "Tom Dempsey"
    ],
    "correctIndex": 3,
    "notes": "Tom Dempsey"
  },
  {
    "id": 402,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Tom Dempsey's 63-yard FG was notable because of what physical trait?",
    "options": [
      "No use of non-kicking arm",
      "Partially amputated kicking foot",
      "Blind in one eye",
      "Prosthetic leg"
    ],
    "correctIndex": 1,
    "notes": "Special shoe"
  },
  {
    "id": 403,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which team's pass-rush duo of Gastineau and Klecko was called the Sack Exchange?",
    "options": [
      "New York Jets",
      "New York Giants",
      "Buffalo Bills",
      "Philadelphia Eagles"
    ],
    "correctIndex": 0,
    "notes": "Jets"
  },
  {
    "id": 404,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which CB holds the record for most career interception return yards?",
    "options": [
      "Rod Woodson",
      "Darren Sharper",
      "Deion Sanders",
      "Ed Reed"
    ],
    "correctIndex": 3,
    "notes": "Ed Reed"
  },
  {
    "id": 405,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "The Steel Curtain refers to which team's 1970s defense?",
    "options": [
      "Pittsburgh Steelers",
      "Minnesota Vikings",
      "Chicago Bears",
      "Dallas Cowboys"
    ],
    "correctIndex": 0,
    "notes": "Steelers"
  },
  {
    "id": 406,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which LB was known as Captain Crunch?",
    "options": [
      "Dick Butkus",
      "Ray Nitschke",
      "Jack Lambert",
      "Mike Singletary"
    ],
    "correctIndex": 2,
    "notes": "Jack Lambert"
  },
  {
    "id": 407,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "The Legion of Boom secondary played for which team?",
    "options": [
      "Baltimore Ravens",
      "San Francisco 49ers",
      "Seattle Seahawks",
      "Denver Broncos"
    ],
    "correctIndex": 2,
    "notes": "Seahawks"
  },
  {
    "id": 408,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which CB popularized shutdown coverage and the bail technique in the 2000s?",
    "options": [
      "Darrelle Revis",
      "Champ Bailey",
      "Charles Woodson",
      "Ronde Barber"
    ],
    "correctIndex": 0,
    "notes": "Darrelle Revis"
  },
  {
    "id": 409,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach holds the record for most Super Bowl victories?",
    "options": [
      "Joe Gibbs",
      "Chuck Noll",
      "Bill Walsh",
      "Bill Belichick"
    ],
    "correctIndex": 3,
    "notes": "Six"
  },
  {
    "id": 410,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who was the first African-American head coach to win a Super Bowl?",
    "options": [
      "Tony Dungy",
      "Mike Tomlin",
      "Herm Edwards",
      "Lovie Smith"
    ],
    "correctIndex": 0,
    "notes": "Super Bowl XLI"
  },
  {
    "id": 411,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach developed the West Coast Offense while with the Bengals?",
    "options": [
      "Paul Brown",
      "Bill Walsh",
      "Don Coryell",
      "Sid Gillman"
    ],
    "correctIndex": 1,
    "notes": "Bill Walsh"
  },
  {
    "id": 412,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach originated the vertical, deep-passing offensive system used by the Chargers in the late '70s/early '80s that's still referred to by his surname today?",
    "options": [
      "Don Coryell",
      "Bill Walsh",
      "Joe Gibbs",
      "Norv Turner"
    ],
    "correctIndex": 0,
    "notes": "Don Coryell"
  },
  {
    "id": 413,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who coached the 1985 Bears to a Super Bowl title?",
    "options": [
      "Buddy Ryan",
      "Dave Wannstedt",
      "George Halas",
      "Mike Ditka"
    ],
    "correctIndex": 3,
    "notes": "Mike Ditka"
  },
  {
    "id": 414,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach has the most regular-season wins in NFL history?",
    "options": [
      "Don Shula",
      "Tom Landry",
      "Bill Belichick",
      "George Halas"
    ],
    "correctIndex": 0,
    "notes": "347"
  },
  {
    "id": 415,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach won Super Bowls in consecutive seasons with the Cowboys in the 1990s?",
    "options": [
      "Mike Shanahan",
      "Jimmy Johnson",
      "George Seifert",
      "Joe Gibbs"
    ],
    "correctIndex": 1,
    "notes": "Jimmy Johnson"
  },
  {
    "id": 416,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who coached the Broncos to back-to-back Super Bowl wins in the late 1990s?",
    "options": [
      "John Fox",
      "Mike Shanahan",
      "Dan Reeves",
      "Gary Kubiak"
    ],
    "correctIndex": 1,
    "notes": "Mike Shanahan"
  },
  {
    "id": 417,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach was known as The Big Tuna?",
    "options": [
      "Bill Belichick",
      "Bill Parcells",
      "Jeff Fisher",
      "Tom Coughlin"
    ],
    "correctIndex": 1,
    "notes": "Bill Parcells"
  },
  {
    "id": 418,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who was the head coach of the Greatest Show on Turf Rams?",
    "options": [
      "John Gruden",
      "Dick Vermeil then Mike Martz",
      "Mike Martz only",
      "Dick Vermeil only"
    ],
    "correctIndex": 1,
    "notes": "Both"
  },
  {
    "id": 419,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach has the most playoff wins in NFL history?",
    "options": [
      "Bill Belichick",
      "Don Shula",
      "Chuck Noll",
      "Tom Landry"
    ],
    "correctIndex": 0,
    "notes": "Belichick"
  },
  {
    "id": 420,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who was the first African-American GM in the NFL?",
    "options": [
      "Ron Wolf",
      "Ozzie Newsome",
      "Bobby Beathard",
      "Bill Polian"
    ],
    "correctIndex": 1,
    "notes": "Ravens"
  },
  {
    "id": 421,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach is most associated with the Tampa 2 scheme?",
    "options": [
      "Lovie Smith only",
      "Buddy Ryan",
      "Dick LeBeau",
      "Tony Dungy and Monte Kiffin"
    ],
    "correctIndex": 3,
    "notes": "Dungy/Kiffin"
  },
  {
    "id": 422,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who coached the 49ers after Bill Walsh and won Super Bowls?",
    "options": [
      "Steve Mariucci",
      "George Seifert",
      "Mike Singletary",
      "Jim Harbaugh"
    ],
    "correctIndex": 1,
    "notes": "George Seifert"
  },
  {
    "id": 423,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which GM is most associated with building the 1980s 49ers dynasty?",
    "options": [
      "Eddie DeBartolo",
      "John McVay",
      "Bill Walsh",
      "Carmen Policy"
    ],
    "correctIndex": 2,
    "notes": "Walsh influence"
  },
  {
    "id": 425,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The two-point conversion was adopted by the NFL in which year?",
    "options": [
      "1999",
      "2001",
      "1994",
      "1988"
    ],
    "correctIndex": 2,
    "notes": "1994"
  },
  {
    "id": 426,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "Instant replay was permanently adopted by the NFL in which year?",
    "options": [
      "2004",
      "1986",
      "1978",
      "1999"
    ],
    "correctIndex": 3,
    "notes": "1999"
  },
  {
    "id": 427,
    "category": "NFL History & Rules",
    "difficulty": "Very Hard",
    "question": "The Tuck Rule was eliminated in which year?",
    "options": [
      "2013",
      "2008",
      "2010",
      "2015"
    ],
    "correctIndex": 0,
    "notes": "2013"
  },
  {
    "id": 428,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The salary cap was first introduced in which year?",
    "options": [
      "1994",
      "2001",
      "1989",
      "1993"
    ],
    "correctIndex": 0,
    "notes": "1994"
  },
  {
    "id": 429,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "Overtime was introduced in the regular season in which year?",
    "options": [
      "1958",
      "1974",
      "1960",
      "1980"
    ],
    "correctIndex": 1,
    "notes": "1974"
  },
  {
    "id": 430,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The current 17-game regular season began in which year?",
    "options": [
      "2020",
      "2019",
      "2021",
      "2022"
    ],
    "correctIndex": 2,
    "notes": "2021"
  },
  {
    "id": 431,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The Rooney Rule was implemented in which year?",
    "options": [
      "1999",
      "2003",
      "2007",
      "2011"
    ],
    "correctIndex": 1,
    "notes": "2003"
  },
  {
    "id": 432,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The NFL Draft began in which year?",
    "options": [
      "1925",
      "1936",
      "1950",
      "1940"
    ],
    "correctIndex": 1,
    "notes": "1936"
  },
  {
    "id": 433,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "Which commissioner oversaw the AFL-NFL merger?",
    "options": [
      "Paul Tagliabue",
      "Roger Goodell",
      "Bert Bell",
      "Pete Rozelle"
    ],
    "correctIndex": 3,
    "notes": "Pete Rozelle"
  },
  {
    "id": 434,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The current 7-team-per-conference playoff format began in which year?",
    "options": [
      "2021",
      "2020",
      "2022",
      "2019"
    ],
    "correctIndex": 1,
    "notes": "2020 season"
  },
  {
    "id": 435,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "In what year was the forward pass legalized?",
    "options": [
      "1912",
      "1933",
      "1920",
      "1906"
    ],
    "correctIndex": 3,
    "notes": "1906"
  },
  {
    "id": 436,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The first televised NFL game occurred in which year?",
    "options": [
      "1951",
      "1948",
      "1939",
      "1958"
    ],
    "correctIndex": 2,
    "notes": "1939"
  },
  {
    "id": 437,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "Which year saw major rule changes that opened the passing game (illegal contact, hands by OL)?",
    "options": [
      "1982",
      "1980",
      "1977",
      "1978"
    ],
    "correctIndex": 3,
    "notes": "1978"
  },
  {
    "id": 438,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The first NFL night game was played in which year?",
    "options": [
      "1951",
      "1948",
      "1929",
      "1939"
    ],
    "correctIndex": 2,
    "notes": "1929"
  },
  {
    "id": 439,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which player's autobiography was titled I Am Third?",
    "options": [
      "Mike Ditka",
      "Brian Piccolo",
      "Dick Butkus",
      "Gale Sayers"
    ],
    "correctIndex": 3,
    "notes": "Gale Sayers"
  },
  {
    "id": 440,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Gale Sayers's friendship with which Bears teammate, who died of cancer in 1970, was depicted in an Emmy-winning TV movie?",
    "options": [
      "Johnny Morris",
      "Dick Butkus",
      "Brian Piccolo",
      "Mike Ditka"
    ],
    "correctIndex": 2,
    "notes": "Brian Piccolo"
  },
  {
    "id": 441,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which NFL Films narrator was known as The Voice of God?",
    "options": [
      "John Facenda",
      "Sam Spence",
      "Harry Kalas",
      "Steve Sabol"
    ],
    "correctIndex": 0,
    "notes": "John Facenda"
  },
  {
    "id": 442,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The Immaculate Reception occurred on December 23 of which year?",
    "options": [
      "1972",
      "1973",
      "1971",
      "1974"
    ],
    "correctIndex": 0,
    "notes": "1972"
  },
  {
    "id": 443,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which team's fans wave the Terrible Towel?",
    "options": [
      "Cleveland Browns",
      "Cincinnati Bengals",
      "Pittsburgh Steelers",
      "Baltimore Ravens"
    ],
    "correctIndex": 2,
    "notes": "Steelers"
  },
  {
    "id": 444,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Cheesehead hats are worn by fans of which team?",
    "options": [
      "Green Bay Packers",
      "Detroit Lions",
      "Chicago Bears",
      "Minnesota Vikings"
    ],
    "correctIndex": 0,
    "notes": "Packers"
  },
  {
    "id": 445,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which former coach became famous for his telestrator work on broadcasts?",
    "options": [
      "Howie Long",
      "Troy Aikman",
      "John Madden",
      "Michael Irvin"
    ],
    "correctIndex": 2,
    "notes": "John Madden"
  },
  {
    "id": 446,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The Madden Curse refers to cover athletes suffering what?",
    "options": [
      "Injury or decline",
      "Trade",
      "Retirement",
      "Holdout"
    ],
    "correctIndex": 0,
    "notes": "Injury/decline"
  },
  {
    "id": 447,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which Super Bowl had the famous wardrobe malfunction halftime show?",
    "options": [
      "Super Bowl XXXVII",
      "Super Bowl XL",
      "Super Bowl XXXIX",
      "Super Bowl XXXVIII"
    ],
    "correctIndex": 3,
    "notes": "2004"
  },
  {
    "id": 448,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The 12th Man tradition is most associated with which NFL team?",
    "options": [
      "Green Bay Packers",
      "Seattle Seahawks",
      "Kansas City Chiefs",
      "New Orleans Saints"
    ],
    "correctIndex": 1,
    "notes": "Seahawks"
  },
  {
    "id": 449,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The Super Bowl Shuffle was performed by which Super Bowl team?",
    "options": [
      "1990 Giants",
      "1984 49ers",
      "1985 Chicago Bears",
      "1972 Miami Dolphins"
    ],
    "correctIndex": 2,
    "notes": "Bears"
  },
  {
    "id": 450,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which two-sport star played RB for the Raiders and OF for the Royals?",
    "options": [
      "Deion Sanders",
      "Bo Jackson",
      "Brian Jordan",
      "Chad Hutchinson"
    ],
    "correctIndex": 1,
    "notes": "Bo Jackson"
  },
  {
    "id": 451,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which Hall of Fame coach became a color commentator known for Boom!?",
    "options": [
      "Bill Parcells",
      "Mike Ditka",
      "John Madden",
      "Tom Landry"
    ],
    "correctIndex": 2,
    "notes": "John Madden"
  },
  {
    "id": 452,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The Gatorade shower tradition began with which 1980s team?",
    "options": [
      "Chicago Bears",
      "New York Giants",
      "Washington",
      "San Francisco 49ers"
    ],
    "correctIndex": 1,
    "notes": "Giants"
  },
  {
    "id": 453,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which team's helmet is famously plain with no logo?",
    "options": [
      "Cincinnati Bengals",
      "Cleveland Browns",
      "Pittsburgh Steelers",
      "Baltimore Ravens"
    ],
    "correctIndex": 1,
    "notes": "Browns"
  },
  {
    "id": 454,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The Black Hole fan section is associated with which team?",
    "options": [
      "Buffalo Bills",
      "Las Vegas Raiders",
      "Kansas City Chiefs",
      "Philadelphia Eagles"
    ],
    "correctIndex": 1,
    "notes": "Raiders"
  },
  {
    "id": 455,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which NFL team's official fight song, written in 1941, opens with the line 'Bear down, ___, make every play clear the way to victory'?",
    "options": [
      "Green Bay Packers",
      "Chicago Bears",
      "Minnesota Vikings",
      "Detroit Lions"
    ],
    "correctIndex": 1,
    "notes": "Bears"
  },
  {
    "id": 456,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "America's Team nickname is most associated with which franchise?",
    "options": [
      "New York Giants",
      "San Francisco 49ers",
      "Dallas Cowboys",
      "Green Bay Packers"
    ],
    "correctIndex": 2,
    "notes": "Cowboys"
  },
  {
    "id": 457,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which owner purchased the Patriots in 1994 and built a dynasty?",
    "options": [
      "Paul Allen",
      "Robert Kraft",
      "Jerry Jones",
      "Al Davis"
    ],
    "correctIndex": 1,
    "notes": "Robert Kraft"
  },
  {
    "id": 458,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Al Davis was the longtime owner most associated with which franchise?",
    "options": [
      "Chiefs",
      "Chargers",
      "Broncos",
      "Raiders"
    ],
    "correctIndex": 3,
    "notes": "Raiders"
  },
  {
    "id": 459,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which QB has the most career 300-yard passing games?",
    "options": [
      "Peyton Manning",
      "Aaron Rodgers",
      "Drew Brees",
      "Tom Brady"
    ],
    "correctIndex": 2,
    "notes": "Drew Brees"
  },
  {
    "id": 460,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the record for most career all-purpose yards?",
    "options": [
      "Jerry Rice",
      "Walter Payton",
      "Emmitt Smith",
      "Brian Mitchell"
    ],
    "correctIndex": 3,
    "notes": "Brian Mitchell"
  },
  {
    "id": 461,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which RB rushed for 2,105 yards in 1984?",
    "options": [
      "O.J. Simpson",
      "Walter Payton",
      "Eric Dickerson",
      "Barry Sanders"
    ],
    "correctIndex": 2,
    "notes": "Eric Dickerson"
  },
  {
    "id": 462,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the single-season receiving TD record?",
    "options": [
      "Jerry Rice",
      "Cooper Kupp",
      "Randy Moss",
      "CeeDee Lamb"
    ],
    "correctIndex": 2,
    "notes": "23 in 2007"
  },
  {
    "id": 463,
    "category": "Player Records",
    "difficulty": "Very Hard",
    "question": "Who is the only player to score a TD on offense, defense and special teams in the same game?",
    "options": [
      "Gale Sayers",
      "William Perry",
      "Deion Sanders",
      "Walter Payton"
    ],
    "correctIndex": 2,
    "notes": "Deion Sanders"
  },
  {
    "id": 464,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which QB has the most career interceptions thrown?",
    "options": [
      "George Blanda",
      "Peyton Manning",
      "Vinny Testaverde",
      "Brett Favre"
    ],
    "correctIndex": 3,
    "notes": "Brett Favre"
  },
  {
    "id": 465,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the record for most career sacks since they became official in 1982?",
    "options": [
      "Reggie White",
      "Julius Peppers",
      "Kevin Greene",
      "Bruce Smith"
    ],
    "correctIndex": 3,
    "notes": "Bruce Smith"
  },
  {
    "id": 466,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which player has the most career Pro Bowl selections?",
    "options": [
      "Tony Gonzalez",
      "Jerry Rice",
      "Tom Brady",
      "Peyton Manning"
    ],
    "correctIndex": 2,
    "notes": "Tom Brady (15)"
  },
  {
    "id": 467,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Who holds the record for most career yards from scrimmage?",
    "options": [
      "Emmitt Smith",
      "Walter Payton",
      "Frank Gore",
      "Jerry Rice"
    ],
    "correctIndex": 1,
    "notes": "Walter Payton"
  },
  {
    "id": 468,
    "category": "Player Records",
    "difficulty": "Hard",
    "question": "Which kicker has the most career field goals made?",
    "options": [
      "Morten Andersen",
      "Jason Hanson",
      "Justin Tucker",
      "Adam Vinatieri"
    ],
    "correctIndex": 3,
    "notes": "Adam Vinatieri"
  },
  {
    "id": 469,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which college has produced the most overall NFL Draft picks historically?",
    "options": [
      "Notre Dame",
      "USC",
      "Ohio State",
      "Alabama"
    ],
    "correctIndex": 1,
    "notes": "USC often leads"
  },
  {
    "id": 470,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 2014 NFL Draft?",
    "options": [
      "Khalil Mack",
      "Sammy Watkins",
      "Blake Bortles",
      "Jadeveon Clowney"
    ],
    "correctIndex": 3,
    "notes": "Jadeveon Clowney"
  },
  {
    "id": 471,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 2016 NFL Draft?",
    "options": [
      "Jared Goff",
      "Joey Bosa",
      "Ezekiel Elliott",
      "Carson Wentz"
    ],
    "correctIndex": 0,
    "notes": "Jared Goff"
  },
  {
    "id": 472,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 2019 NFL Draft?",
    "options": [
      "Quinnen Williams",
      "Josh Allen",
      "Nick Bosa",
      "Kyler Murray"
    ],
    "correctIndex": 3,
    "notes": "Kyler Murray"
  },
  {
    "id": 473,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Which QB was taken No. 1 overall by the Panthers in 2011?",
    "options": [
      "Cam Newton",
      "Blaine Gabbert",
      "Christian Ponder",
      "Jake Locker"
    ],
    "correctIndex": 0,
    "notes": "Cam Newton"
  },
  {
    "id": 474,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 2005 NFL Draft?",
    "options": [
      "Cedric Benson",
      "Alex Smith",
      "Braylon Edwards",
      "Ronnie Brown"
    ],
    "correctIndex": 1,
    "notes": "Alex Smith"
  },
  {
    "id": 475,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 2003 NFL Draft?",
    "options": [
      "Carson Palmer",
      "Andre Johnson",
      "Charles Rogers",
      "Byron Leftwich"
    ],
    "correctIndex": 0,
    "notes": "Carson Palmer"
  },
  {
    "id": 476,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 2001 NFL Draft?",
    "options": [
      "Leonard Davis",
      "Michael Vick",
      "Gerard Warren",
      "Justin Smith"
    ],
    "correctIndex": 1,
    "notes": "Michael Vick"
  },
  {
    "id": 477,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 1997 NFL Draft?",
    "options": [
      "Warrick Dunn",
      "Shawn Springs",
      "Orlando Pace",
      "Darrell Russell"
    ],
    "correctIndex": 2,
    "notes": "Orlando Pace"
  },
  {
    "id": 478,
    "category": "Draft & College",
    "difficulty": "Hard",
    "question": "Who was the first overall pick of the 1996 NFL Draft?",
    "options": [
      "Jonathan Ogden",
      "Kevin Hardy",
      "Keyshawn Johnson",
      "Simeon Rice"
    ],
    "correctIndex": 2,
    "notes": "Keyshawn Johnson"
  },
  {
    "id": 479,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl XXX as the underdog over the Steelers?",
    "options": [
      "Dallas Cowboys",
      "Denver Broncos",
      "Green Bay Packers",
      "San Francisco 49ers"
    ],
    "correctIndex": 0,
    "notes": "Cowboys"
  },
  {
    "id": 480,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who was the MVP of Super Bowl XXV?",
    "options": [
      "Lawrence Taylor",
      "Mark Bavaro",
      "Ottis Anderson",
      "Jeff Hostetler"
    ],
    "correctIndex": 2,
    "notes": "Ottis Anderson"
  },
  {
    "id": 482,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who returned an interception for a TD in Super Bowl XLVIII?",
    "options": [
      "Kam Chancellor",
      "Earl Thomas",
      "Richard Sherman",
      "Malcolm Smith"
    ],
    "correctIndex": 3,
    "notes": "Malcolm Smith (MVP)"
  },
  {
    "id": 483,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl XXXIII over the Falcons?",
    "options": [
      "Green Bay Packers",
      "Denver Broncos",
      "Atlanta Falcons",
      "Minnesota Vikings"
    ],
    "correctIndex": 1,
    "notes": "Broncos"
  },
  {
    "id": 484,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who was the MVP of Super Bowl XXXII?",
    "options": [
      "Rod Smith",
      "John Elway",
      "Terrell Davis",
      "Shannon Sharpe"
    ],
    "correctIndex": 2,
    "notes": "Terrell Davis"
  },
  {
    "id": 485,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which Super Bowl featured the first overtime touchdown?",
    "options": [
      "Super Bowl XXV",
      "Super Bowl XLIII",
      "Super Bowl LI",
      "Super Bowl XXXVIII"
    ],
    "correctIndex": 2,
    "notes": "James White TD"
  },
  {
    "id": 486,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who was the starting QB for the Rams in Super Bowl XXXVI?",
    "options": [
      "Jamie Martin",
      "Trent Green",
      "Kurt Warner",
      "Marc Bulger"
    ],
    "correctIndex": 2,
    "notes": "Kurt Warner"
  },
  {
    "id": 487,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Which team won Super Bowl XXVIII over the Bills?",
    "options": [
      "San Francisco 49ers",
      "Green Bay Packers",
      "Dallas Cowboys",
      "Buffalo Bills"
    ],
    "correctIndex": 2,
    "notes": "Cowboys"
  },
  {
    "id": 488,
    "category": "Super Bowl History",
    "difficulty": "Hard",
    "question": "Who was the MVP of Super Bowl XXVII?",
    "options": [
      "Michael Irvin",
      "Troy Aikman",
      "Ken Norton Jr.",
      "Emmitt Smith"
    ],
    "correctIndex": 1,
    "notes": "Troy Aikman"
  },
  {
    "id": 489,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the most Hall of Fame inductees all-time?",
    "options": [
      "New York Giants",
      "Chicago Bears",
      "Pittsburgh Steelers",
      "Green Bay Packers"
    ],
    "correctIndex": 1,
    "notes": "Bears"
  },
  {
    "id": 490,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team was the first to win a Super Bowl after relocating in the modern era?",
    "options": [
      "Los Angeles Rams",
      "Indianapolis Colts",
      "Baltimore Ravens",
      "Tennessee Titans"
    ],
    "correctIndex": 2,
    "notes": "Ravens (from Cleveland)"
  },
  {
    "id": 491,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team holds the record for most consecutive road wins?",
    "options": [
      "Pittsburgh Steelers",
      "Dallas Cowboys",
      "New England Patriots",
      "San Francisco 49ers"
    ],
    "correctIndex": 2,
    "notes": "Various claims; Pats high"
  },
  {
    "id": 493,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team won the most games in the 1990s?",
    "options": [
      "San Francisco 49ers",
      "Buffalo Bills",
      "Green Bay Packers",
      "Dallas Cowboys"
    ],
    "correctIndex": 3,
    "notes": "Cowboys"
  },
  {
    "id": 494,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the longest Super Bowl drought among teams that have won one?",
    "options": [
      "Miami Dolphins",
      "Chicago Bears",
      "Washington",
      "New York Jets"
    ],
    "correctIndex": 3,
    "notes": "Jets (1968)"
  },
  {
    "id": 495,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team was the last to win a championship before the Super Bowl era and still not win a Super Bowl?",
    "options": [
      "Tennessee Titans",
      "Minnesota Vikings",
      "Detroit Lions",
      "Cleveland Browns"
    ],
    "correctIndex": 3,
    "notes": "Browns 1964"
  },
  {
    "id": 496,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the most losses in a single season since the 16-game schedule began?",
    "options": [
      "Cleveland Browns 2017",
      "Tampa Bay early",
      "Multiple 0-16 or 1-15",
      "Detroit Lions 2008"
    ],
    "correctIndex": 3,
    "notes": "Lions 0-16"
  },
  {
    "id": 497,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has appeared in the most NFC Championship Games?",
    "options": [
      "Green Bay Packers",
      "Dallas Cowboys",
      "San Francisco 49ers",
      "Philadelphia Eagles"
    ],
    "correctIndex": 2,
    "notes": "49ers high"
  },
  {
    "id": 498,
    "category": "Franchise & Team Records",
    "difficulty": "Hard",
    "question": "Which team has the most wins in franchise history?",
    "options": [
      "New York Giants",
      "Green Bay Packers",
      "Chicago Bears",
      "Pittsburgh Steelers"
    ],
    "correctIndex": 2,
    "notes": "Bears or Packers close"
  },
  {
    "id": 499,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which LB holds the record for most career tackles (unofficial/official mixed eras)?",
    "options": [
      "Ray Lewis",
      "Junior Seau",
      "Zach Thomas",
      "London Fletcher"
    ],
    "correctIndex": 3,
    "notes": "London Fletcher among leaders"
  },
  {
    "id": 500,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who holds the record for most career safeties?",
    "options": [
      "Doug English",
      "Multiple with 4",
      "Ted Hendricks",
      "Jared Allen"
    ],
    "correctIndex": 2,
    "notes": "Ted Hendricks (4)"
  },
  {
    "id": 501,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which return specialist has the most combined kick/punt return TDs?",
    "options": [
      "Cordarrelle Patterson",
      "Dante Hall",
      "Devin Hester",
      "Josh Cribbs"
    ],
    "correctIndex": 2,
    "notes": "Devin Hester"
  },
  {
    "id": 502,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who blocked the most punts in a single season?",
    "options": [
      "Bill Bates",
      "Special teams records vary",
      "Ted Hendricks",
      "Steve Tasker"
    ],
    "correctIndex": 2,
    "notes": "Historical leaders"
  },
  {
    "id": 503,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which CB has the most career Pro Bowls at the position?",
    "options": [
      "Rod Woodson",
      "Darrelle Revis",
      "Champ Bailey",
      "Charles Woodson"
    ],
    "correctIndex": 2,
    "notes": "Champ Bailey (12)"
  },
  {
    "id": 504,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who holds the record for most consecutive games with a sack?",
    "options": [
      "Bruce Smith",
      "Reggie White",
      "Deacon Jones",
      "Jared Allen"
    ],
    "correctIndex": 3,
    "notes": "Jared Allen (11)"
  },
  {
    "id": 505,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which DT has the most career sacks among pure interior linemen?",
    "options": [
      "Aaron Donald",
      "John Randle",
      "Merlin Olsen",
      "Warren Sapp"
    ],
    "correctIndex": 1,
    "notes": "John Randle high"
  },
  {
    "id": 507,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Which team's defense was called the No-Name Defense?",
    "options": [
      "Miami Dolphins",
      "Chicago Bears",
      "Pittsburgh Steelers",
      "Minnesota Vikings"
    ],
    "correctIndex": 0,
    "notes": "1972 Dolphins"
  },
  {
    "id": 508,
    "category": "Defense & Special Teams",
    "difficulty": "Hard",
    "question": "Who holds the record for most career special-teams tackles?",
    "options": [
      "Larry Izzo",
      "Steve Tasker",
      "Bill Bates",
      "Various"
    ],
    "correctIndex": 2,
    "notes": "Bill Bates early leader"
  },
  {
    "id": 509,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach has the highest winning percentage among those with significant games (modern)?",
    "options": [
      "John Madden",
      "Vince Lombardi",
      "George Allen",
      "Bill Belichick"
    ],
    "correctIndex": 1,
    "notes": "Lombardi high"
  },
  {
    "id": 510,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who was the first coach to win 100 games with two different franchises?",
    "options": [
      "Tom Landry",
      "Don Shula",
      "Bill Parcells",
      "Chuck Noll"
    ],
    "correctIndex": 2,
    "notes": "Parcells"
  },
  {
    "id": 511,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach won Super Bowls with the Redskins in three different decades?",
    "options": [
      "Joe Gibbs",
      "George Allen",
      "Norv Turner",
      "Marty Schottenheimer"
    ],
    "correctIndex": 0,
    "notes": "Joe Gibbs"
  },
  {
    "id": 512,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who coached the Raiders to their first Super Bowl win?",
    "options": [
      "Al Davis",
      "Tom Flores",
      "Art Shell",
      "John Madden"
    ],
    "correctIndex": 3,
    "notes": "John Madden"
  },
  {
    "id": 513,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which offensive line coach is credited as the primary architect of the zone-blocking scheme popularized in Denver?",
    "options": [
      "Mike Shanahan",
      "Rick Dennison",
      "Gary Kubiak",
      "Alex Gibbs"
    ],
    "correctIndex": 3,
    "notes": "Alex Gibbs primary"
  },
  {
    "id": 514,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who was the head coach of the 1986 Giants Super Bowl team?",
    "options": [
      "Ray Handley",
      "Bill Parcells",
      "Tom Coughlin",
      "Bill Belichick"
    ],
    "correctIndex": 1,
    "notes": "Bill Parcells"
  },
  {
    "id": 515,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach won Super Bowl XXXVII with the Buccaneers?",
    "options": [
      "Bruce Arians",
      "Jon Gruden",
      "Monte Kiffin",
      "Tony Dungy"
    ],
    "correctIndex": 1,
    "notes": "Jon Gruden"
  },
  {
    "id": 516,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who coached the Saints to their only Super Bowl title?",
    "options": [
      "Sean Payton",
      "Mike Ditka",
      "Jim Mora",
      "Jim Haslett"
    ],
    "correctIndex": 0,
    "notes": "Sean Payton"
  },
  {
    "id": 517,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Which coach has the most losses in NFL history?",
    "options": [
      "Don Shula",
      "Tom Landry",
      "Jeff Fisher",
      "Dan Reeves"
    ],
    "correctIndex": 2,
    "notes": "Jeff Fisher high"
  },
  {
    "id": 518,
    "category": "Coaches & Front Office",
    "difficulty": "Hard",
    "question": "Who was the first African-American head coach in the modern NFL?",
    "options": [
      "Tony Dungy",
      "Dennis Green",
      "Art Shell",
      "Ray Rhodes"
    ],
    "correctIndex": 2,
    "notes": "Art Shell 1989"
  },
  {
    "id": 519,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "Which year did the NFL introduce the current overtime rules for regular season (both teams possess)?",
    "options": [
      "2012",
      "2022",
      "2017",
      "2010"
    ],
    "correctIndex": 0,
    "notes": "Refined over time"
  },
  {
    "id": 520,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The fair-catch kick has been successful how many times in Super Bowl history?",
    "options": [
      "Three",
      "One",
      "Two",
      "Zero"
    ],
    "correctIndex": 3,
    "notes": "Never"
  },
  {
    "id": 521,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The catch rule was clarified after controversial plays involving which two receivers?",
    "options": [
      "Larry Fitzgerald and Anquan Boldin",
      "Randy Moss and Terrell Owens",
      "Dez Bryant and Calvin Johnson",
      "Odell Beckham and Julio Jones"
    ],
    "correctIndex": 2,
    "notes": "Both"
  },
  {
    "id": 522,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "Which year did the NFL begin using sky judge / additional replay assistance more heavily?",
    "options": [
      "2020s",
      "1990s",
      "2000s",
      "2010s"
    ],
    "correctIndex": 3,
    "notes": "Ongoing evolution"
  },
  {
    "id": 523,
    "category": "NFL History & Rules",
    "difficulty": "Hard",
    "question": "The first use of a coach's challenge system was in which decade?",
    "options": [
      "1980s",
      "2000s",
      "1970s",
      "1990s"
    ],
    "correctIndex": 3,
    "notes": "1990s experimental"
  },
  {
    "id": 524,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which player's career inspired the book and movie The Blind Side?",
    "options": [
      "Lawrence Taylor",
      "Joe Theismann",
      "Bo Jackson",
      "Michael Oher"
    ],
    "correctIndex": 3,
    "notes": "Michael Oher"
  },
  {
    "id": 525,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The term Hail Mary for a desperation pass was popularized by which QB?",
    "options": [
      "Fran Tarkenton",
      "Joe Namath",
      "Johnny Unitas",
      "Roger Staubach"
    ],
    "correctIndex": 3,
    "notes": "Staubach"
  },
  {
    "id": 526,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which team's fans are known as Cheeseheads?",
    "options": [
      "Green Bay Packers",
      "Detroit Lions",
      "Minnesota Vikings",
      "Chicago Bears"
    ],
    "correctIndex": 0,
    "notes": "Packers"
  },
  {
    "id": 527,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which broadcaster is famous for the call Do you believe in miracles (Olympic hockey, not NFL)?",
    "options": [
      "John Madden",
      "Pat Summerall",
      "Al Michaels",
      "Keith Jackson"
    ],
    "correctIndex": 2,
    "notes": "Al Michaels"
  },
  {
    "id": 528,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The Frozen Tundra nickname for Lambeau was popularized by which source?",
    "options": [
      "Pat Summerall",
      "NFL Films / John Facenda",
      "Curt Gowdy",
      "Ray Scott"
    ],
    "correctIndex": 1,
    "notes": "NFL Films"
  },
  {
    "id": 529,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which team's owner is Jerry Jones?",
    "options": [
      "Philadelphia Eagles",
      "New York Giants",
      "Dallas Cowboys",
      "Washington"
    ],
    "correctIndex": 2,
    "notes": "Cowboys"
  },
  {
    "id": 530,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which former Cowboys quarterback became CBS's lead NFL color analyst in 2017, immediately upon retiring with no broadcasting experience?",
    "options": [
      "Troy Aikman",
      "Phil Simms",
      "Tony Romo",
      "Danny White"
    ],
    "correctIndex": 2,
    "notes": "Both prominent"
  },
  {
    "id": 531,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "The No. 12 is retired by the Jets for which player?",
    "options": [
      "Joe Namath",
      "Ken O'Brien",
      "Richard Todd",
      "Vinny Testaverde"
    ],
    "correctIndex": 0,
    "notes": "Joe Namath"
  },
  {
    "id": 532,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which team's mascot is a pirate?",
    "options": [
      "Tampa Bay Buccaneers",
      "None exactly",
      "Las Vegas Raiders",
      "Pittsburgh Steelers"
    ],
    "correctIndex": 0,
    "notes": "Buccaneers"
  },
  {
    "id": 533,
    "category": "Miscellaneous",
    "difficulty": "Hard",
    "question": "Which team's name comes from a poem by Edgar Allan Poe?",
    "options": [
      "Atlanta Falcons",
      "Arizona Cardinals",
      "Philadelphia Eagles",
      "Baltimore Ravens"
    ],
    "correctIndex": 3,
    "notes": "Ravens"
  },
];
