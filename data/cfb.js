// College Football trivia bank, 456 multiple-choice questions across 10 categories
// (Heisman Trophy, National Championships, Rivalries, Coaches, Players & Legends,
// Records & Stats, Bowls & Playoff, Traditions & Culture, Conferences & History, Deep
// Cuts). Started from the user's College_Football_Trivia_300_Questions spreadsheet,
// then heavily fact-checked and cleaned: ~24 questions with false premises, vague
// non-answers ('All of the above'/nonsensical answers), or duplicate options were
// removed or corrected, and ~49 near-duplicate questions (same fact asked twice with
// reshuffled options) were deduped. ~156 new questions (Heisman winners/runners-up,
// national champions by year, winningest coaches by school, championship coaches,
// career/season statistical leaders, bowl-win records, vacated/forfeited titles, and
// major position awards) were generated from CFB_Trivia_Cheat_Code-12.xlsx, a
// dedicated reference workbook, with every correct answer AND every wrong-answer
// option pulled from that same verified source table (no fabricated distractors).
// A later audit (duplicates / answer-context mismatches / answer-leaking questions)
// removed 2 exact duplicates, 1 near-duplicate, and 2 self-answering questions
// (e.g. "What is the Army-Navy game officially called?" with "Army-Navy Game" as an
// option), and rewrote 3 questions that gave away their own answer in the question
// text or named a parenthetical team directly (e.g. "...biggest upsets ever (Boise
// State)?"), plus 1 question whose "correct" option wasn't an actual conference name.
window.CFB_DATA = [
  {
    "id": 1,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who was the first player to win the Heisman Trophy twice?",
    "options": [
      "Doak Walker",
      "Johnny Rodgers",
      "Roger Staubach",
      "Archie Griffin"
    ],
    "correctIndex": 3,
    "notes": "Ohio State RB, 1974 & 1975"
  },
  {
    "id": 2,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which school has produced the most Heisman Trophy winners?",
    "options": [
      "USC",
      "Notre Dame",
      "Oklahoma",
      "Ohio State"
    ],
    "correctIndex": 0,
    "notes": "USC has 8 (as of mid-2020s)"
  },
  {
    "id": 3,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the 2023 Heisman Trophy?",
    "options": [
      "Michael Penix Jr.",
      "Bo Nix",
      "Jayden Daniels",
      "Marvin Harrison Jr."
    ],
    "correctIndex": 2,
    "notes": "LSU QB"
  },
  {
    "id": 5,
    "category": "Heisman Trophy",
    "difficulty": "Very Hard",
    "question": "Who is the only defensive player to win the Heisman Trophy?",
    "options": [
      "Lawrence Taylor",
      "Ronnie Lott",
      "Charles Woodson",
      "Dick Butkus"
    ],
    "correctIndex": 2,
    "notes": "1997 Michigan CB"
  },
  {
    "id": 6,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which quarterback won the Heisman in 2016 at Louisville?",
    "options": [
      "Lamar Jackson",
      "Deshaun Watson",
      "Baker Mayfield",
      "Kyler Murray"
    ],
    "correctIndex": 0,
    "notes": "Lamar Jackson"
  },
  {
    "id": 7,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 2019?",
    "options": [
      "Chase Young",
      "Joe Burrow",
      "Jalen Hurts",
      "Justin Fields"
    ],
    "correctIndex": 1,
    "notes": "LSU QB, record-breaking season"
  },
  {
    "id": 8,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which running back won the Heisman in 2015 at Alabama?",
    "options": [
      "Mark Ingram",
      "Trent Richardson",
      "Derrick Henry",
      "Najee Harris"
    ],
    "correctIndex": 2,
    "notes": "Derrick Henry"
  },
  {
    "id": 9,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who was the first freshman to win the Heisman Trophy?",
    "options": [
      "Lamar Jackson",
      "Herschel Walker",
      "Johnny Manziel",
      "Jameis Winston"
    ],
    "correctIndex": 2,
    "notes": "2012 Texas A&M"
  },
  {
    "id": 11,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the 2006 Heisman Trophy while playing for Ohio State?",
    "options": [
      "Braxton Miller",
      "Troy Smith",
      "Justin Fields",
      "Terrelle Pryor"
    ],
    "correctIndex": 1,
    "notes": "Troy Smith"
  },
  {
    "id": 12,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Which Florida QB won the Heisman in 2007?",
    "options": [
      "Rex Grossman",
      "Chris Leak",
      "Danny Wuerffel",
      "Tim Tebow"
    ],
    "correctIndex": 3,
    "notes": "Tim Tebow"
  },
  {
    "id": 13,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who is the only player to win the Heisman, a national title, and the Super Bowl MVP?",
    "options": [
      "Cam Newton",
      "Charles Woodson",
      "None of the above",
      "Marcus Allen"
    ],
    "correctIndex": 3,
    "notes": "Marcus Allen (USC/Raiders)"
  },
  {
    "id": 14,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which Notre Dame player won the Heisman in 1987?",
    "options": [
      "Paul Hornung",
      "Joe Theismann",
      "Raghib Ismail",
      "Tim Brown"
    ],
    "correctIndex": 3,
    "notes": "Tim Brown"
  },
  {
    "id": 15,
    "category": "Heisman Trophy",
    "difficulty": "Very Hard",
    "question": "Who finished second in the 1997 Heisman voting to Charles Woodson?",
    "options": [
      "Peyton Manning",
      "Ricky Williams",
      "Tim Couch",
      "Ryan Leaf"
    ],
    "correctIndex": 0,
    "notes": "Peyton Manning (Tennessee)"
  },
  {
    "id": 16,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which Oklahoma QB won the Heisman in 2018?",
    "options": [
      "Spencer Rattler",
      "Kyler Murray",
      "Baker Mayfield",
      "Jalen Hurts"
    ],
    "correctIndex": 1,
    "notes": "Kyler Murray"
  },
  {
    "id": 17,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the 2021 Heisman Trophy?",
    "options": [
      "C.J. Stroud",
      "Kenny Pickett",
      "Will Rogers",
      "Bryce Young"
    ],
    "correctIndex": 3,
    "notes": "Alabama QB"
  },
  {
    "id": 18,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which Wisconsin running back won the Heisman Trophy in 1999?",
    "options": [
      "Jonathan Taylor",
      "Melvin Gordon",
      "Ron Dayne",
      "Montee Ball"
    ],
    "correctIndex": 2,
    "notes": "Ron Dayne won it"
  },
  {
    "id": 19,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who was the last pure running back to win the Heisman before 2015?",
    "options": [
      "Reggie Bush",
      "Ricky Williams",
      "Mark Ingram",
      "Ron Dayne"
    ],
    "correctIndex": 2,
    "notes": "Mark Ingram 2009 (Bush vacated)"
  },
  {
    "id": 20,
    "category": "Heisman Trophy",
    "difficulty": "Very Hard",
    "question": "Which Heisman winner's trophy was later vacated by the NCAA?",
    "options": [
      "Reggie Bush",
      "Johnny Manziel",
      "Cam Newton",
      "None"
    ],
    "correctIndex": 0,
    "notes": "Reggie Bush (2005)"
  },
  {
    "id": 21,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which school has the most claimed national championships in FBS history?",
    "options": [
      "Oklahoma",
      "Alabama",
      "Michigan",
      "Notre Dame"
    ],
    "correctIndex": 1,
    "notes": "Alabama claims the most"
  },
  {
    "id": 22,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Who coached Alabama to the 2020 national championship?",
    "options": [
      "Jimbo Fisher",
      "Kirby Smart",
      "Dabo Swinney",
      "Nick Saban"
    ],
    "correctIndex": 3,
    "notes": "Nick Saban"
  },
  {
    "id": 23,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the first College Football Playoff national championship (2014 season)?",
    "options": [
      "Oregon",
      "Ohio State",
      "Alabama",
      "Florida State"
    ],
    "correctIndex": 1,
    "notes": "Ohio State over Oregon"
  },
  {
    "id": 24,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which school won consecutive national titles in 1994 and 1995?",
    "options": [
      "Alabama",
      "Miami",
      "Nebraska",
      "Florida"
    ],
    "correctIndex": 2,
    "notes": "Tom Osborne's Nebraska"
  },
  {
    "id": 25,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which team was the last AP Poll national champion before the BCS era began?",
    "options": [
      "Michigan",
      "Nebraska",
      "Florida State",
      "Tennessee"
    ],
    "correctIndex": 0,
    "notes": "1997 Michigan (split with Nebraska)"
  },
  {
    "id": 26,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached Florida to national titles in 2006 and 2008?",
    "options": [
      "Steve Spurrier",
      "Urban Meyer",
      "Jim McElwain",
      "Dan Mullen"
    ],
    "correctIndex": 1,
    "notes": "Urban Meyer"
  },
  {
    "id": 27,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the 2022 national championship?",
    "options": [
      "Ohio State",
      "Michigan",
      "Georgia",
      "TCU"
    ],
    "correctIndex": 2,
    "notes": "Georgia over TCU"
  },
  {
    "id": 29,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which school won the 1984 national championship in a famous Holiday Bowl upset?",
    "options": [
      "BYU",
      "Washington",
      "Nebraska",
      "Oklahoma"
    ],
    "correctIndex": 0,
    "notes": "BYU beat Michigan in the Holiday Bowl (only BYU title)"
  },
  {
    "id": 30,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which two teams shared the 2003 national championship?",
    "options": [
      "LSU and Georgia",
      "USC and Oklahoma",
      "LSU and USC",
      "Oklahoma and LSU"
    ],
    "correctIndex": 2,
    "notes": "LSU (BCS) and USC (AP)"
  },
  {
    "id": 31,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached Clemson to national titles in 2016 and 2018?",
    "options": [
      "Ken Hatfield",
      "Danny Ford",
      "Dabo Swinney",
      "Tommy Bowden"
    ],
    "correctIndex": 2,
    "notes": "Dabo Swinney"
  },
  {
    "id": 32,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the 2019 national championship?",
    "options": [
      "Oklahoma",
      "Ohio State",
      "LSU",
      "Clemson"
    ],
    "correctIndex": 2,
    "notes": "LSU over Clemson"
  },
  {
    "id": 33,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which coach has the most national championships in the modern era (since 1990)?",
    "options": [
      "Dabo Swinney",
      "Bear Bryant",
      "Urban Meyer",
      "Nick Saban"
    ],
    "correctIndex": 3,
    "notes": "Nick Saban (7)"
  },
  {
    "id": 34,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which school won back-to-back titles in 2003-2004 under Pete Carroll?",
    "options": [
      "Texas",
      "Oklahoma",
      "LSU",
      "USC"
    ],
    "correctIndex": 3,
    "notes": "USC (2004 AP, 2003 split)"
  },
  {
    "id": 35,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which team was awarded the 1990 national championship by the AP after Georgia Tech took the Coaches Poll?",
    "options": [
      "Miami",
      "Colorado",
      "Georgia Tech",
      "Notre Dame"
    ],
    "correctIndex": 1,
    "notes": "Colorado (AP) / Georgia Tech (Coaches)"
  },
  {
    "id": 36,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached Tennessee to the 1998 national championship?",
    "options": [
      "Lane Kiffin",
      "Phillip Fulmer",
      "Johnny Majors",
      "Jeremy Pruitt"
    ],
    "correctIndex": 1,
    "notes": "Phillip Fulmer"
  },
  {
    "id": 37,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which Miami team is often called 'The U' and won titles in the 1980s/early 90s?",
    "options": [
      "Florida A&M",
      "Miami Hurricanes",
      "FIU",
      "Miami RedHawks"
    ],
    "correctIndex": 1,
    "notes": "Miami Hurricanes"
  },
  {
    "id": 38,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the 2021 national championship?",
    "options": [
      "Michigan",
      "Alabama",
      "Cincinnati",
      "Georgia"
    ],
    "correctIndex": 3,
    "notes": "Georgia over Alabama"
  },
  {
    "id": 39,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which coach won a national title at Florida State in 1993 and 1999?",
    "options": [
      "Bobby Bowden",
      "Jimbo Fisher",
      "Chuck Amato",
      "Mike Norvell"
    ],
    "correctIndex": 0,
    "notes": "Bobby Bowden"
  },
  {
    "id": 40,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which school won the 1957 national championship under Woody Hayes?",
    "options": [
      "Auburn",
      "Ohio State",
      "Iowa",
      "Michigan State"
    ],
    "correctIndex": 1,
    "notes": "Ohio State"
  },
  {
    "id": 41,
    "category": "Rivalries",
    "difficulty": "Medium",
    "question": "What is the name of the annual Alabama-Auburn game?",
    "options": [
      "Clean, Old-Fashioned Hate",
      "Iron Bowl",
      "Egg Bowl",
      "Red River Rivalry"
    ],
    "correctIndex": 1,
    "notes": "Iron Bowl"
  },
  {
    "id": 42,
    "category": "Rivalries",
    "difficulty": "Medium",
    "question": "What trophy is awarded to the winner of Michigan vs. Minnesota?",
    "options": [
      "Paul Bunyan Trophy",
      "Little Brown Jug",
      "Floyd of Rosedale",
      "Old Oaken Bucket"
    ],
    "correctIndex": 1,
    "notes": "Little Brown Jug"
  },
  {
    "id": 43,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the name of the Texas-Oklahoma rivalry game?",
    "options": [
      "Lone Star Showdown",
      "Border War",
      "Iron Skillet",
      "Red River Rivalry"
    ],
    "correctIndex": 3,
    "notes": "Red River Rivalry / Shootout"
  },
  {
    "id": 44,
    "category": "Rivalries",
    "difficulty": "Medium",
    "question": "Which two teams play for the Paul Bunyan Trophy?",
    "options": [
      "Ohio State and Michigan",
      "Iowa and Minnesota",
      "Minnesota and Wisconsin",
      "Michigan and Michigan State"
    ],
    "correctIndex": 3,
    "notes": "Michigan-Michigan State"
  },
  {
    "id": 45,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the Georgia-Florida rivalry commonly called?",
    "options": [
      "Clean, Old-Fashioned Hate",
      "The World's Largest Outdoor Cocktail Party",
      "Egg Bowl",
      "Deep South's Oldest Rivalry"
    ],
    "correctIndex": 1,
    "notes": "World's Largest Outdoor Cocktail Party"
  },
  {
    "id": 46,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which rivalry is known as 'Clean, Old-Fashioned Hate'?",
    "options": [
      "Clemson vs South Carolina",
      "Florida vs Florida State",
      "Auburn vs Alabama",
      "Georgia vs Georgia Tech"
    ],
    "correctIndex": 3,
    "notes": "Georgia-Georgia Tech"
  },
  {
    "id": 48,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which two teams play for the Old Oaken Bucket?",
    "options": [
      "Iowa and Nebraska",
      "Indiana and Purdue",
      "Ohio State and Penn State",
      "Illinois and Northwestern"
    ],
    "correctIndex": 1,
    "notes": "Indiana-Purdue"
  },
  {
    "id": 49,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What trophy is at stake in Iowa vs. Minnesota?",
    "options": [
      "Heartland Trophy",
      "Cy-Hawk Trophy",
      "Little Brown Jug",
      "Floyd of Rosedale"
    ],
    "correctIndex": 3,
    "notes": "Floyd of Rosedale (bronze pig)"
  },
  {
    "id": 50,
    "category": "Rivalries",
    "difficulty": "Very Hard",
    "question": "Which rivalry is called the 'Deep South's Oldest Rivalry'?",
    "options": [
      "Tennessee vs Vanderbilt",
      "Alabama vs Mississippi State",
      "LSU vs Ole Miss",
      "Auburn vs Georgia"
    ],
    "correctIndex": 3,
    "notes": "Auburn-Georgia"
  },
  {
    "id": 51,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the Oregon-Oregon State rivalry called?",
    "options": [
      "Cascade Clash",
      "Northwest Classic",
      "Civil War",
      "Border War"
    ],
    "correctIndex": 2,
    "notes": "Civil War"
  },
  {
    "id": 52,
    "category": "Rivalries",
    "difficulty": "Medium",
    "question": "Which two teams compete for the Apple Cup?",
    "options": [
      "UCLA and USC",
      "Oregon and Oregon State",
      "Stanford and Cal",
      "Washington and Washington State"
    ],
    "correctIndex": 3,
    "notes": "Washington-Washington State"
  },
  {
    "id": 53,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the USC-UCLA rivalry game trophy?",
    "options": [
      "Victory Bell",
      "Civil War Trophy",
      "Apple Cup",
      "Stanford Axe"
    ],
    "correctIndex": 0,
    "notes": "Victory Bell"
  },
  {
    "id": 54,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which teams play for the Stanford Axe?",
    "options": [
      "Stanford and USC",
      "Cal and UCLA",
      "Stanford and California",
      "Oregon and Stanford"
    ],
    "correctIndex": 2,
    "notes": "Stanford-Cal (Big Game)"
  },
  {
    "id": 55,
    "category": "Rivalries",
    "difficulty": "Very Hard",
    "question": "What is the name of the Missouri-Kansas rivalry?",
    "options": [
      "Midwest Classic",
      "Show-Me Showdown",
      "Tiger-Jayhawk Clash",
      "Border War"
    ],
    "correctIndex": 3,
    "notes": "Border War"
  },
  {
    "id": 56,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which rivalry produces the 'Golden Egg' trophy?",
    "options": [
      "Auburn vs LSU",
      "Ole Miss vs Mississippi State",
      "Tennessee vs Kentucky",
      "LSU vs Alabama"
    ],
    "correctIndex": 1,
    "notes": "Egg Bowl"
  },
  {
    "id": 57,
    "category": "Rivalries",
    "difficulty": "Medium",
    "question": "What is the annual Michigan-Ohio State game often called?",
    "options": [
      "The Big One",
      "Midwest Mayhem",
      "The Game",
      "Ten-Year War"
    ],
    "correctIndex": 2,
    "notes": "The Game"
  },
  {
    "id": 58,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which two teams play for the Governor's Cup (Kentucky)?",
    "options": [
      "Kentucky and Louisville",
      "Kentucky and Tennessee",
      "Louisville and Cincinnati",
      "Kentucky and Vanderbilt"
    ],
    "correctIndex": 0,
    "notes": "Kentucky-Louisville"
  },
  {
    "id": 60,
    "category": "Rivalries",
    "difficulty": "Very Hard",
    "question": "Which trophy is awarded in the Iowa-Wisconsin game?",
    "options": [
      "Old Brass Spittoon",
      "Cy-Hawk Trophy",
      "Floyd of Rosedale",
      "Heartland Trophy"
    ],
    "correctIndex": 3,
    "notes": "Heartland Trophy"
  },
  {
    "id": 61,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who is the winningest coach in FBS history by total wins?",
    "options": [
      "Nick Saban",
      "Bobby Bowden",
      "Joe Paterno",
      "Bear Bryant"
    ],
    "correctIndex": 2,
    "notes": "Joe Paterno (vacated wins still debated)"
  },
  {
    "id": 62,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who coached Alabama from 2007 through 2023?",
    "options": [
      "Gene Stallings",
      "Mike DuBose",
      "Dennis Franchione",
      "Nick Saban"
    ],
    "correctIndex": 3,
    "notes": "Nick Saban"
  },
  {
    "id": 63,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach is known as 'The Bear'?",
    "options": [
      "Tom Osborne",
      "Woody Hayes",
      "Bo Schembechler",
      "Bear Bryant"
    ],
    "correctIndex": 3,
    "notes": "Paul 'Bear' Bryant"
  },
  {
    "id": 64,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached Michigan during the famous 'Ten-Year War' with Ohio State?",
    "options": [
      "Bo Schembechler",
      "Fielding Yost",
      "Jim Harbaugh",
      "Lloyd Carr"
    ],
    "correctIndex": 0,
    "notes": "Bo Schembechler"
  },
  {
    "id": 66,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached Nebraska to three national titles in the 1990s?",
    "options": [
      "Frank Solich",
      "Bob Devaney",
      "Tom Osborne",
      "Bo Pelini"
    ],
    "correctIndex": 2,
    "notes": "Tom Osborne"
  },
  {
    "id": 67,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led Florida State for 34 seasons?",
    "options": [
      "Jimbo Fisher",
      "Bill Peterson",
      "Bobby Bowden",
      "Mike Norvell"
    ],
    "correctIndex": 2,
    "notes": "Bobby Bowden"
  },
  {
    "id": 68,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach led the Miami Dolphins in the NFL before later winning national titles at Alabama?",
    "options": [
      "Nick Saban",
      "Howard Schnellenberger",
      "Don Shula",
      "Jimmy Johnson"
    ],
    "correctIndex": 0,
    "notes": "Nick Saban"
  },
  {
    "id": 70,
    "category": "Coaches",
    "difficulty": "Very Hard",
    "question": "Who coached the 1984 BYU national championship team?",
    "options": [
      "LaVell Edwards",
      "Kalani Sitake",
      "Gary Crowton",
      "Bronco Mendenhall"
    ],
    "correctIndex": 0,
    "notes": "LaVell Edwards"
  },
  {
    "id": 71,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach won a national title at Auburn in 2010?",
    "options": [
      "Gene Chizik",
      "Tommy Tuberville",
      "Terry Bowden",
      "Gus Malzahn"
    ],
    "correctIndex": 0,
    "notes": "Gene Chizik (Cam Newton year)"
  },
  {
    "id": 72,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached Texas to the 2005 national championship?",
    "options": [
      "Mack Brown",
      "Darrell Royal",
      "Charlie Strong",
      "Fred Akers"
    ],
    "correctIndex": 0,
    "notes": "Mack Brown"
  },
  {
    "id": 74,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached Miami during their dominant late 1980s&#8211;early 1990s run?",
    "options": [
      "Jimmy Johnson and Dennis Erickson",
      "Larry Coker",
      "Howard Schnellenberger only",
      "Butch Davis"
    ],
    "correctIndex": 0,
    "notes": "Jimmy Johnson then Dennis Erickson"
  },
  {
    "id": 76,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached Ohio State to the first CFP national title?",
    "options": [
      "Urban Meyer",
      "Ryan Day",
      "Jim Tressel",
      "John Cooper"
    ],
    "correctIndex": 0,
    "notes": "Urban Meyer (2014 season)"
  },
  {
    "id": 77,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach is known for the 'Groundhog Day' speech and intense intensity at Iowa?",
    "options": [
      "Kirk Ferentz",
      "Bret Bielema",
      "Both",
      "Hayden Fry"
    ],
    "correctIndex": 0,
    "notes": "Kirk Ferentz (long tenure)"
  },
  {
    "id": 78,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who coached Georgia to back-to-back national titles in 2021-2022?",
    "options": [
      "Jim Donnan",
      "Kirby Smart",
      "Vince Dooley",
      "Mark Richt"
    ],
    "correctIndex": 1,
    "notes": "Kirby Smart"
  },
  {
    "id": 79,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach won a national title at LSU in 2003 before later coaching Alabama?",
    "options": [
      "Nick Saban",
      "Les Miles",
      "Gerry DiNardo",
      "Ed Orgeron"
    ],
    "correctIndex": 0,
    "notes": "Nick Saban"
  },
  {
    "id": 80,
    "category": "Coaches",
    "difficulty": "Very Hard",
    "question": "Who coached the famous 1971 Nebraska team that beat Oklahoma 35-31 in the 'Game of the Century'?",
    "options": [
      "Warren Powers",
      "Tom Osborne",
      "Frank Solich",
      "Bob Devaney"
    ],
    "correctIndex": 3,
    "notes": "Bob Devaney"
  },
  {
    "id": 81,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which player is known as 'The Galloping Ghost'?",
    "options": [
      "Bronko Nagurski",
      "Tom Harmon",
      "Red Grange",
      "Jim Thorpe"
    ],
    "correctIndex": 2,
    "notes": "Red Grange (Illinois)"
  },
  {
    "id": 82,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who is the all-time leading rusher in FBS history?",
    "options": [
      "Ricky Williams",
      "Donnel Pumphrey",
      "Ron Dayne",
      "Tony Dorsett"
    ],
    "correctIndex": 1,
    "notes": "Donnel Pumphrey (San Diego State)"
  },
  {
    "id": 83,
    "category": "Players & Legends",
    "difficulty": "Medium",
    "question": "Which player scored the most touchdowns for Texas in the 2006 Rose Bowl (BCS title game vs. USC)?",
    "options": [
      "Matt Leinart",
      "LenDale White",
      "Vince Young",
      "Reggie Bush"
    ],
    "correctIndex": 2,
    "notes": "Vince Young (Texas)"
  },
  {
    "id": 85,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Which player returned a kickoff 93 yards for a TD on the opening play of the 2007 BCS National Championship Game and later played in the NFL?",
    "options": [
      "Maurice Clarett",
      "Ted Ginn Jr.",
      "Santonio Holmes",
      "Devin Hester"
    ],
    "correctIndex": 1,
    "notes": "Ted Ginn Jr. (Ohio State)"
  },
  {
    "id": 86,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who holds the FBS record for career passing yards?",
    "options": [
      "Baker Mayfield",
      "Case Keenum",
      "Landry Jones",
      "Timmy Chang"
    ],
    "correctIndex": 1,
    "notes": "Case Keenum (Houston)"
  },
  {
    "id": 87,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which Alabama player was known as 'The Snake'?",
    "options": [
      "Richard Todd",
      "Ken Stabler",
      "Joe Namath",
      "Bart Starr"
    ],
    "correctIndex": 1,
    "notes": "Ken Stabler"
  },
  {
    "id": 91,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which Michigan wide receiver was known for the 'Catch' in the 1981 game against Notre Dame?",
    "options": [
      "Anthony Carter",
      "Mario Manningham",
      "Braylon Edwards",
      "Desmond Howard"
    ],
    "correctIndex": 0,
    "notes": "Anthony Carter"
  },
  {
    "id": 92,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who is the all-time leading scorer in FBS history?",
    "options": [
      "Will Reichard",
      "Keenan Reynolds",
      "Kenneth Dixon",
      "Jonah Dalmas"
    ],
    "correctIndex": 0,
    "notes": "Will Reichard (Alabama K), 547 career points \u2014 all-time FBS scoring record"
  },
  {
    "id": 94,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which running back was known as 'Bo' and won the 1985 Heisman at Auburn?",
    "options": [
      "Bo Jackson",
      "James Brooks",
      "William Andrews",
      "Joe Cribbs"
    ],
    "correctIndex": 0,
    "notes": "Bo Jackson"
  },
  {
    "id": 95,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Who threw the famous 'Hail Mary' pass for Boston College against Miami in 1984?",
    "options": [
      "Doug Flutie",
      "Mark MacDonald",
      "Gerard Phelan",
      "Shawn Halloran"
    ],
    "correctIndex": 0,
    "notes": "Doug Flutie to Gerard Phelan"
  },
  {
    "id": 96,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which player is the all-time leading receiver in Alabama history by yards?",
    "options": [
      "Amari Cooper",
      "DJ Hall",
      "Ozzie Newsome",
      "Julio Jones"
    ],
    "correctIndex": 0,
    "notes": "Amari Cooper"
  },
  {
    "id": 97,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who was the first overall pick in the 2024 NFL Draft from USC?",
    "options": [
      "Drake Maye",
      "Marvin Harrison Jr.",
      "Caleb Williams",
      "Rome Odunze"
    ],
    "correctIndex": 2,
    "notes": "Caleb Williams"
  },
  {
    "id": 98,
    "category": "Players & Legends",
    "difficulty": "Medium",
    "question": "Which LSU quarterback was the first overall pick in the 2020 NFL Draft?",
    "options": [
      "Justin Jefferson",
      "Joe Burrow",
      "Clyde Edwards-Helaire",
      "Ja'Marr Chase"
    ],
    "correctIndex": 1,
    "notes": "Joe Burrow (QB)"
  },
  {
    "id": 99,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which player is known for the 'Superman' dive into the end zone at Florida?",
    "options": [
      "Jeff Demps",
      "Chris Leak",
      "Percy Harvin",
      "Tim Tebow"
    ],
    "correctIndex": 3,
    "notes": "Tim Tebow"
  },
  {
    "id": 100,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Who scored the winning touchdown in the 2005 'Bush Push' game for USC vs Notre Dame?",
    "options": [
      "Matt Leinart",
      "Dwayne Jarrett",
      "LenDale White",
      "Reggie Bush"
    ],
    "correctIndex": 0,
    "notes": "Matt Leinart, pushed into the end zone by Reggie Bush (Nov. 2005)"
  },
  {
    "id": 101,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which team holds the record for the longest winning streak in FBS history?",
    "options": [
      "Notre Dame",
      "USC",
      "Miami",
      "Oklahoma"
    ],
    "correctIndex": 3,
    "notes": "Oklahoma 47 games (1953-57)"
  },
  {
    "id": 102,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which QB holds the FBS record for career touchdown passes?",
    "options": [
      "Baker Mayfield",
      "Case Keenum",
      "Landry Jones",
      "Kellen Moore"
    ],
    "correctIndex": 1,
    "notes": "Case Keenum (Houston), 155 career passing TDs \u2014 NCAA record, tied by Dillon Gabriel in 2024"
  },
  {
    "id": 103,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Which running back holds the single-season rushing record in FBS?",
    "options": [
      "Mike Rozier",
      "Marcus Allen",
      "Barry Sanders",
      "OJ Simpson"
    ],
    "correctIndex": 2,
    "notes": "Barry Sanders (2,628 in 1988)"
  },
  {
    "id": 104,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which team scored the most points in a single FBS game?",
    "options": [
      "Alabama",
      "Oklahoma",
      "Houston",
      "Nebraska"
    ],
    "correctIndex": 2,
    "notes": "Houston 100+ (vs Tulsa, SMU eras)"
  },
  {
    "id": 107,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which school holds the record for most consecutive conference titles?",
    "options": [
      "Alabama",
      "USC",
      "Oklahoma",
      "Nebraska"
    ],
    "correctIndex": 3,
    "notes": "Nebraska (many in Big 8)"
  },
  {
    "id": 108,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Which QB threw for over 5,000 yards in a single season first?",
    "options": [
      "Ty Detmer",
      "Joe Burrow",
      "Baker Mayfield",
      "Case Keenum"
    ],
    "correctIndex": 0,
    "notes": "Ty Detmer (BYU)"
  },
  {
    "id": 109,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which player holds the FBS record for most consecutive games with a reception?",
    "options": [
      "Justin Blackmon",
      "Michael Crabtree",
      "Davante Adams",
      "Ryan Broyles"
    ],
    "correctIndex": 3,
    "notes": "Ryan Broyles (Oklahoma)"
  },
  {
    "id": 110,
    "category": "Records & Stats",
    "difficulty": "Very Hard",
    "question": "Which team holds the record for most points scored in a bowl game?",
    "options": [
      "Houston",
      "West Virginia",
      "Texas Tech",
      "Oklahoma State"
    ],
    "correctIndex": 1,
    "notes": "West Virginia 70 vs Clemson (Orange Bowl)"
  },
  {
    "id": 111,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which kicker holds the record for the longest field goal in college football history (any division)?",
    "options": [
      "Ove Johansson",
      "Tom Whelihan",
      "Russell Erxleben",
      "Justin Tucker (college)"
    ],
    "correctIndex": 0,
    "notes": "Ove Johansson, 69 yards for Abilene Christian (then NAIA) vs East Texas State, 1976 \u2014 longest field goal at any level of college football"
  },
  {
    "id": 112,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which QB has the most career wins as a starter in FBS?",
    "options": [
      "Baker Mayfield",
      "Colt McCoy",
      "Trevor Knight",
      "Kellen Moore"
    ],
    "correctIndex": 3,
    "notes": "Kellen Moore (50)"
  },
  {
    "id": 113,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Which team went 15-0 in the 2018 season?",
    "options": [
      "Notre Dame",
      "Alabama",
      "Clemson",
      "Ohio State"
    ],
    "correctIndex": 2,
    "notes": "Clemson"
  },
  {
    "id": 114,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which player holds the single-game receiving yards record in FBS?",
    "options": [
      "Several have 300+",
      "Jordy Nelson",
      "Troy Walters",
      "Ron Sellers"
    ],
    "correctIndex": 3,
    "notes": "Ron Sellers (Florida State) among early leaders"
  },
  {
    "id": 115,
    "category": "Records & Stats",
    "difficulty": "Very Hard",
    "question": "Which team has the most all-time wins in FBS history?",
    "options": [
      "Ohio State",
      "Michigan",
      "Texas",
      "Alabama"
    ],
    "correctIndex": 1,
    "notes": "Michigan"
  },
  {
    "id": 116,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which defense held opponents to the fewest points per game over a season in modern era?",
    "options": [
      "2009 Alabama",
      "Multiple claims",
      "2000 Oklahoma",
      "2011 Alabama"
    ],
    "correctIndex": 3,
    "notes": "2011 Alabama among the stingiest"
  },
  {
    "id": 118,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Which QB threw 60 touchdown passes in a single season?",
    "options": [
      "Joe Burrow",
      "Baker Mayfield",
      "Colt Brennan",
      "Case Keenum"
    ],
    "correctIndex": 0,
    "notes": "Joe Burrow (2019)"
  },
  {
    "id": 119,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which school has the most appearances in the Rose Bowl?",
    "options": [
      "Stanford",
      "USC",
      "Michigan",
      "Ohio State"
    ],
    "correctIndex": 1,
    "notes": "USC"
  },
  {
    "id": 121,
    "category": "Bowls & Playoff",
    "difficulty": "Medium",
    "question": "What year did the College Football Playoff begin?",
    "options": [
      "2010",
      "2012",
      "2014",
      "2015"
    ],
    "correctIndex": 2,
    "notes": "2014 season"
  },
  {
    "id": 123,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which bowl game is played in the Mercedes-Benz Superdome?",
    "options": [
      "Cotton Bowl",
      "Orange Bowl",
      "Fiesta Bowl",
      "Sugar Bowl"
    ],
    "correctIndex": 3,
    "notes": "Sugar Bowl (New Orleans)"
  },
  {
    "id": 124,
    "category": "Bowls & Playoff",
    "difficulty": "Medium",
    "question": "Which bowl traditionally features the Big Ten vs Pac-12 (historically)?",
    "options": [
      "Cotton Bowl",
      "Orange Bowl",
      "Sugar Bowl",
      "Rose Bowl"
    ],
    "correctIndex": 3,
    "notes": "Rose Bowl"
  },
  {
    "id": 125,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the first-ever CFP National Championship Game?",
    "options": [
      "Oregon",
      "Alabama",
      "Ohio State",
      "Clemson"
    ],
    "correctIndex": 2,
    "notes": "Ohio State (2015)"
  },
  {
    "id": 126,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "What is the nickname of the Cotton Bowl stadium in Dallas?",
    "options": [
      "Big D Dome",
      "The House That Doak Built",
      "Cotton Palace",
      "Jerry World"
    ],
    "correctIndex": 1,
    "notes": "House That Doak Built"
  },
  {
    "id": 128,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which bowl game is associated with the phrase 'Granddaddy of Them All'?",
    "options": [
      "Fiesta Bowl",
      "Rose Bowl",
      "Orange Bowl",
      "Sugar Bowl"
    ],
    "correctIndex": 1,
    "notes": "Rose Bowl"
  },
  {
    "id": 129,
    "category": "Bowls & Playoff",
    "difficulty": "Medium",
    "question": "Which team won the 2023 CFP National Championship?",
    "options": [
      "Alabama",
      "Texas",
      "Washington",
      "Michigan"
    ],
    "correctIndex": 3,
    "notes": "Michigan over Washington"
  },
  {
    "id": 130,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which coach led TCU to the 2022 CFP title game?",
    "options": [
      "Jimbo Fisher",
      "Mike Gundy",
      "Sonny Dykes",
      "Gary Patterson"
    ],
    "correctIndex": 2,
    "notes": "Sonny Dykes"
  },
  {
    "id": 132,
    "category": "Bowls & Playoff",
    "difficulty": "Very Hard",
    "question": "Which team pulled off the Statue of Liberty play to complete one of the biggest upsets ever in the 2007 Fiesta Bowl?",
    "options": [
      "Boise State over Oklahoma",
      "Utah over Alabama",
      "TCU over Wisconsin",
      "Houston over Florida State"
    ],
    "correctIndex": 0,
    "notes": "Boise State Statue of Liberty play"
  },
  {
    "id": 133,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which bowl game is played in Glendale, Arizona?",
    "options": [
      "Rose Bowl",
      "Peach Bowl",
      "Fiesta Bowl",
      "Cotton Bowl"
    ],
    "correctIndex": 2,
    "notes": "Fiesta Bowl"
  },
  {
    "id": 134,
    "category": "Bowls & Playoff",
    "difficulty": "Medium",
    "question": "How many teams make the expanded CFP starting in 2024?",
    "options": [
      "12",
      "4",
      "8",
      "16"
    ],
    "correctIndex": 0,
    "notes": "12-team playoff"
  },
  {
    "id": 135,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team was the first Group of 5 team to reach the CFP Final Four?",
    "options": [
      "Memphis",
      "Cincinnati",
      "Houston",
      "UCF"
    ],
    "correctIndex": 1,
    "notes": "Cincinnati 2021"
  },
  {
    "id": 137,
    "category": "Bowls & Playoff",
    "difficulty": "Very Hard",
    "question": "Which team won the 1998 national title by beating Florida State in the Fiesta Bowl?",
    "options": [
      "Wisconsin",
      "UCLA",
      "Tennessee",
      "Ohio State"
    ],
    "correctIndex": 2,
    "notes": "Tennessee, QB Tee Martin (Peyton Manning had already left for the NFL)"
  },
  {
    "id": 139,
    "category": "Bowls & Playoff",
    "difficulty": "Medium",
    "question": "Which team has the most Cotton Bowl victories historically?",
    "options": [
      "Alabama",
      "Notre Dame",
      "Ohio State",
      "Texas"
    ],
    "correctIndex": 3,
    "notes": "Texas"
  },
  {
    "id": 141,
    "category": "Traditions & Culture",
    "difficulty": "Medium",
    "question": "What is the name of Notre Dame's fighting spirit mascot?",
    "options": [
      "Touchdown Jesus",
      "Leprechaun",
      "Irish Setter",
      "Golden Dome"
    ],
    "correctIndex": 1,
    "notes": "Leprechaun"
  },
  {
    "id": 142,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "What is the famous 'Script Ohio' performed by?",
    "options": [
      "Michigan Marching Band",
      "Penn State Blue Band",
      "Wisconsin Band",
      "Ohio State Marching Band"
    ],
    "correctIndex": 3,
    "notes": "Ohio State"
  },
  {
    "id": 145,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "What is the 'Dotting of the i' in Script Ohio?",
    "options": [
      "A random student",
      "The drum major",
      "A cheerleader",
      "A sousaphone player dots the i"
    ],
    "correctIndex": 3,
    "notes": "Sousaphone player"
  },
  {
    "id": 147,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school has the 'Gator Chomp'?",
    "options": [
      "South Florida",
      "Florida State",
      "Miami",
      "Florida"
    ],
    "correctIndex": 3,
    "notes": "Florida Gators"
  },
  {
    "id": 148,
    "category": "Traditions & Culture",
    "difficulty": "Medium",
    "question": "What is the famous war chant of Florida State?",
    "options": [
      "Seminole Yell",
      "War Chant / Tomahawk Chop",
      "Nole Chant",
      "Uprising"
    ],
    "correctIndex": 1,
    "notes": "War Chant"
  },
  {
    "id": 149,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school is known for the 'Midnight Yell'?",
    "options": [
      "Texas A&M",
      "LSU",
      "Oklahoma",
      "Texas"
    ],
    "correctIndex": 0,
    "notes": "Texas A&M"
  },
  {
    "id": 150,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "What is the name of LSU's famous tiger mascot?",
    "options": [
      "Death Valley Tiger",
      "All used",
      "Mike the Tiger",
      "Bayou Bengal"
    ],
    "correctIndex": 2,
    "notes": "Mike the Tiger (live)"
  },
  {
    "id": 153,
    "category": "Traditions & Culture",
    "difficulty": "Medium",
    "question": "Which school has the 'War Eagle' battle cry?",
    "options": [
      "Georgia",
      "Clemson",
      "Auburn",
      "Alabama"
    ],
    "correctIndex": 2,
    "notes": "Auburn"
  },
  {
    "id": 154,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "What is the name of the Clemson entrance tradition involving a hill?",
    "options": [
      "Running Down the Hill",
      "Tiger Walk",
      "Death Valley March",
      "Both A and C"
    ],
    "correctIndex": 0,
    "notes": "Running Down the Hill into Death Valley"
  },
  {
    "id": 155,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school is known for the 'Howard's Rock'?",
    "options": [
      "Georgia Tech",
      "South Carolina",
      "Clemson",
      "Florida State"
    ],
    "correctIndex": 2,
    "notes": "Clemson (rub the rock)"
  },
  {
    "id": 157,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school has a live bear mascot tradition historically?",
    "options": [
      "California",
      "Baylor",
      "UCLA",
      "Missouri"
    ],
    "correctIndex": 1,
    "notes": "Baylor (though discontinued)"
  },
  {
    "id": 159,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school plays 'Rocky Top' as a fight song / anthem?",
    "options": [
      "Vanderbilt",
      "West Virginia",
      "Kentucky",
      "Tennessee"
    ],
    "correctIndex": 3,
    "notes": "Tennessee"
  },
  {
    "id": 160,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "What is the famous 'Calling the Hogs' associated with?",
    "options": [
      "Arkansas",
      "Missouri",
      "Ole Miss",
      "Texas Tech"
    ],
    "correctIndex": 0,
    "notes": "Arkansas Razorbacks"
  },
  {
    "id": 161,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which conference was formed in 1896 and is the oldest Division I conference?",
    "options": [
      "ACC",
      "SEC",
      "Pac-12",
      "Big Ten"
    ],
    "correctIndex": 3,
    "notes": "Big Ten (Intercollegiate Conference)"
  },
  {
    "id": 162,
    "category": "Conferences & History",
    "difficulty": "Medium",
    "question": "Which conference does Alabama play in?",
    "options": [
      "Big 12",
      "SEC",
      "ACC",
      "Big Ten"
    ],
    "correctIndex": 1,
    "notes": "SEC"
  },
  {
    "id": 164,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "The Big 12 was formed in 1996 when this conference merged with four Southwest Conference schools — what was it called?",
    "options": [
      "Border Conference",
      "SWC",
      "Big 8",
      "WAC"
    ],
    "correctIndex": 2,
    "notes": "Big 8 + 4 SWC teams = Big 12"
  },
  {
    "id": 165,
    "category": "Conferences & History",
    "difficulty": "Very Hard",
    "question": "Which school was the last to join the Big Ten before the 2010s expansion?",
    "options": [
      "Maryland",
      "Nebraska",
      "Rutgers",
      "Penn State"
    ],
    "correctIndex": 3,
    "notes": "Penn State (1990)"
  },
  {
    "id": 166,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which conference did Nebraska leave to join the Big Ten?",
    "options": [
      "Independent",
      "WAC",
      "Big 12",
      "Big 8"
    ],
    "correctIndex": 2,
    "notes": "Big 12"
  },
  {
    "id": 167,
    "category": "Conferences & History",
    "difficulty": "Medium",
    "question": "Which conference is known as 'The Conference of Champions' historically?",
    "options": [
      "SEC",
      "ACC",
      "Big Ten",
      "Pac-12"
    ],
    "correctIndex": 3,
    "notes": "Pac-12 (Olympic sports)"
  },
  {
    "id": 169,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "What does SWC stand for in college football history?",
    "options": [
      "Southern Western Conference",
      "South Western Conference",
      "Southwest Collegiate",
      "Southwest Conference"
    ],
    "correctIndex": 3,
    "notes": "Southwest Conference"
  },
  {
    "id": 170,
    "category": "Conferences & History",
    "difficulty": "Very Hard",
    "question": "Which conference absorbed many of the old SWC teams?",
    "options": [
      "SEC",
      "Big 12",
      "Conference USA",
      "WAC"
    ],
    "correctIndex": 1,
    "notes": "Big 12"
  },
  {
    "id": 171,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which school is the only one to have been a member of the Big Ten, Big 12, and Big 8?",
    "options": [
      "None exactly",
      "Missouri",
      "Nebraska",
      "Iowa"
    ],
    "correctIndex": 2,
    "notes": "Nebraska (Big 8/Big 12 then Big Ten)"
  },
  {
    "id": 172,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which conference created the first conference championship game in FBS?",
    "options": [
      "Pac-12",
      "ACC",
      "Big 12",
      "SEC"
    ],
    "correctIndex": 3,
    "notes": "SEC (1992)"
  },
  {
    "id": 173,
    "category": "Conferences & History",
    "difficulty": "Medium",
    "question": "Which conference holds its championship game at Mercedes-Benz Stadium in Atlanta?",
    "options": [
      "SEC",
      "Big Ten",
      "Big 12",
      "ACC"
    ],
    "correctIndex": 0,
    "notes": "SEC"
  },
  {
    "id": 174,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which school was a founding member of the ACC?",
    "options": [
      "Miami",
      "Clemson",
      "Virginia Tech",
      "Florida State"
    ],
    "correctIndex": 1,
    "notes": "Clemson (among originals)"
  },
  {
    "id": 175,
    "category": "Conferences & History",
    "difficulty": "Very Hard",
    "question": "Which conference did Penn State leave when it joined the Big Ten?",
    "options": [
      "None",
      "Independent",
      "Atlantic 10",
      "Big East"
    ],
    "correctIndex": 1,
    "notes": "Independent"
  },
  {
    "id": 176,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which school joined the Big Ten in 2011?",
    "options": [
      "Rutgers",
      "Maryland",
      "Both B and C later",
      "Nebraska"
    ],
    "correctIndex": 3,
    "notes": "Nebraska 2011"
  },
  {
    "id": 177,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "What year did the Big 12 Championship Game return after a hiatus?",
    "options": [
      "2017",
      "2018",
      "2015",
      "2019"
    ],
    "correctIndex": 0,
    "notes": "2017"
  },
  {
    "id": 178,
    "category": "Conferences & History",
    "difficulty": "Medium",
    "question": "Which conference is home to the 'Iron Bowl'?",
    "options": [
      "Independent",
      "SEC",
      "Big Ten",
      "ACC"
    ],
    "correctIndex": 1,
    "notes": "SEC"
  },
  {
    "id": 180,
    "category": "Conferences & History",
    "difficulty": "Very Hard",
    "question": "The Pacific Coast Conference (1915-1959) was a direct ancestor of which modern conference?",
    "options": [
      "Pac-12",
      "Mountain West",
      "Big Ten",
      "WAC"
    ],
    "correctIndex": 0,
    "notes": "Pac-12 lineage: PCC → AAWU → Pac-8 → Pac-10 → Pac-12"
  },
  {
    "id": 185,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which school has a tradition of the 'Gator Walk'?",
    "options": [
      "Florida State",
      "Georgia",
      "Miami",
      "Florida"
    ],
    "correctIndex": 3,
    "notes": "Florida"
  },
  {
    "id": 186,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the 'Golden Dome' associated with?",
    "options": [
      "Syracuse",
      "Notre Dame",
      "Boston College",
      "Pittsburgh"
    ],
    "correctIndex": 1,
    "notes": "Notre Dame"
  },
  {
    "id": 187,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Which school is known as the 'Fighting Irish'?",
    "options": [
      "Syracuse",
      "Pittsburgh",
      "Notre Dame",
      "Boston College"
    ],
    "correctIndex": 2,
    "notes": "Notre Dame"
  },
  {
    "id": 190,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which school has the longest continuous use of the same helmet design?",
    "options": [
      "Penn State (plain white)",
      "Multiple claims",
      "Alabama",
      "Ohio State"
    ],
    "correctIndex": 0,
    "notes": "Penn State plain helmets famous"
  },
  {
    "id": 192,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Which school has 'Touchdown Jesus' mural overlooking the stadium?",
    "options": [
      "Holy Cross",
      "Boston College",
      "Notre Dame",
      "Georgetown"
    ],
    "correctIndex": 2,
    "notes": "Notre Dame"
  },
  {
    "id": 193,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which player was the first overall pick in the 1998 NFL Draft from Tennessee?",
    "options": [
      "Peyton Manning",
      "Charles Woodson",
      "Ryan Leaf",
      "Takeo Spikes"
    ],
    "correctIndex": 0,
    "notes": "Peyton Manning"
  },
  {
    "id": 194,
    "category": "Deep Cuts",
    "difficulty": "Very Hard",
    "question": "Which school won the first Rose Bowl game in 1902?",
    "options": [
      "California",
      "Stanford",
      "USC",
      "Michigan"
    ],
    "correctIndex": 3,
    "notes": "Michigan 49-0 over Stanford"
  },
  {
    "id": 195,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the name of the trophy given to the best center in college football?",
    "options": [
      "Rimington Trophy",
      "Lombardi Award",
      "Dave Rimington",
      "Outland Trophy"
    ],
    "correctIndex": 0,
    "notes": "Rimington Trophy"
  },
  {
    "id": 196,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which school is associated with the 'Wishbone' offense dominance in the 1970s?",
    "options": [
      "USC",
      "Michigan",
      "Oklahoma / Texas / Alabama",
      "Notre Dame"
    ],
    "correctIndex": 2,
    "notes": "Oklahoma, Texas, Alabama"
  },
  {
    "id": 197,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Which school has the mascot 'Bevo'?",
    "options": [
      "Texas",
      "Baylor",
      "Texas Tech",
      "Texas A&M"
    ],
    "correctIndex": 0,
    "notes": "Texas Longhorns"
  },
  {
    "id": 203,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Which Alabama player won the Heisman in 2009?",
    "options": [
      "AJ McCarron",
      "Mark Ingram",
      "Greg McElroy",
      "Tua Tagovailoa"
    ],
    "correctIndex": 1,
    "notes": "Mark Ingram (RB)"
  },
  {
    "id": 205,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the 1999 national championship?",
    "options": [
      "Alabama",
      "Florida State",
      "Virginia Tech",
      "Nebraska"
    ],
    "correctIndex": 1,
    "notes": "FSU over Virginia Tech"
  },
  {
    "id": 206,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached USC to the 2004 AP national title?",
    "options": [
      "Lane Kiffin",
      "Jeff Tedford",
      "Clay Helton",
      "Pete Carroll"
    ],
    "correctIndex": 3,
    "notes": "Pete Carroll"
  },
  {
    "id": 207,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the 2015 national championship?",
    "options": [
      "Clemson",
      "Michigan State",
      "Ohio State",
      "Alabama"
    ],
    "correctIndex": 3,
    "notes": "Alabama over Clemson"
  },
  {
    "id": 208,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which school won the 1988 national championship undefeated?",
    "options": [
      "Florida State",
      "West Virginia",
      "Notre Dame",
      "Miami"
    ],
    "correctIndex": 2,
    "notes": "Notre Dame 12-0"
  },
  {
    "id": 210,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What trophy is awarded for Purdue vs Indiana?",
    "options": [
      "Old Oaken Bucket",
      "Canal Cup",
      "Iron Skillet",
      "Hoosier Trophy"
    ],
    "correctIndex": 0,
    "notes": "Old Oaken Bucket"
  },
  {
    "id": 211,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which teams play for the Golden Boot?",
    "options": [
      "LSU and Arkansas",
      "Arkansas and Missouri",
      "Ole Miss and Arkansas",
      "LSU and Ole Miss"
    ],
    "correctIndex": 0,
    "notes": "LSU-Arkansas"
  },
  {
    "id": 212,
    "category": "Rivalries",
    "difficulty": "Medium",
    "question": "What is the Michigan-Michigan State trophy?",
    "options": [
      "Paul Bunyan Trophy",
      "Little Brown Jug",
      "Floyd of Rosedale",
      "Old Brass Spittoon"
    ],
    "correctIndex": 0,
    "notes": "Paul Bunyan Trophy"
  },
  {
    "id": 213,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which rivalry is called the Backyard Brawl?",
    "options": [
      "Pittsburgh vs West Virginia",
      "Maryland vs Virginia",
      "Cincinnati vs Louisville",
      "Boston College vs Syracuse"
    ],
    "correctIndex": 0,
    "notes": "Pitt-West Virginia"
  },
  {
    "id": 214,
    "category": "Rivalries",
    "difficulty": "Very Hard",
    "question": "What is the Minnesota-Penn State trophy?",
    "options": [
      "Little Brown Jug",
      "None famous",
      "Governor's Victory Bell",
      "Floyd of Rosedale"
    ],
    "correctIndex": 2,
    "notes": "Governor's Victory Bell"
  },
  {
    "id": 215,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached the Pony Express SMU teams of the early 1980s?",
    "options": [
      "Ron Meyer then Bobby Collins",
      "Only Ron Meyer",
      "Forrest Gregg",
      "Only Bobby Collins"
    ],
    "correctIndex": 0,
    "notes": "Both"
  },
  {
    "id": 216,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach led Virginia Tech to the 1999 title game?",
    "options": [
      "Bud Foster",
      "Justin Fuente",
      "Frank Beamer",
      "Bill Dooley"
    ],
    "correctIndex": 2,
    "notes": "Frank Beamer"
  },
  {
    "id": 217,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who coached Ohio State to the 2002 national championship?",
    "options": [
      "John Cooper",
      "Urban Meyer",
      "Earle Bruce",
      "Jim Tressel"
    ],
    "correctIndex": 3,
    "notes": "Jim Tressel"
  },
  {
    "id": 218,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach is associated with the Swing Your Sword speech?",
    "options": [
      "Mike Leach",
      "Art Briles",
      "Bob Stoops",
      "Gary Patterson"
    ],
    "correctIndex": 0,
    "notes": "Mike Leach \u2014 'Swing Your Sword' is his memoir and coaching philosophy"
  },
  {
    "id": 219,
    "category": "Coaches",
    "difficulty": "Very Hard",
    "question": "Who coached the 1990 Georgia Tech national championship team?",
    "options": [
      "George O'Leary",
      "Chan Gailey",
      "Bobby Ross",
      "Bill Curry"
    ],
    "correctIndex": 2,
    "notes": "Bobby Ross"
  },
  {
    "id": 220,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which player was known as The Refrigerator at Clemson?",
    "options": [
      "William The Refrigerator Perry",
      "William Perry",
      "Michael Dean Perry",
      "Both Perrys"
    ],
    "correctIndex": 1,
    "notes": "William Perry"
  },
  {
    "id": 221,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who is the all-time leading passer in Texas history?",
    "options": [
      "Colt McCoy",
      "Major Applewhite",
      "Vince Young",
      "Sam Ehlinger"
    ],
    "correctIndex": 0,
    "notes": "Colt McCoy"
  },
  {
    "id": 222,
    "category": "Players & Legends",
    "difficulty": "Medium",
    "question": "Which player won the 1997 Heisman at Michigan?",
    "options": [
      "Charles Woodson",
      "Brian Griese",
      "Anthony Thomas",
      "Tom Brady"
    ],
    "correctIndex": 0,
    "notes": "Charles Woodson"
  },
  {
    "id": 223,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which players starred for 1995 Nebraska?",
    "options": [
      "Ahman Green only",
      "Only Frazier",
      "Tommie Frazier and Lawrence Phillips",
      "Only Phillips"
    ],
    "correctIndex": 2,
    "notes": "Both"
  },
  {
    "id": 224,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Who threw the winning pass in the 2002 Ohio State-Miami title game OT?",
    "options": [
      "Maurice Clarett",
      "Craig Krenzel",
      "Chris Perry",
      "Michael Jenkins"
    ],
    "correctIndex": 1,
    "notes": "Craig Krenzel to Michael Jenkins"
  },
  {
    "id": 225,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which team has the most all-time bowl wins?",
    "options": [
      "Alabama",
      "Oklahoma",
      "USC",
      "Georgia"
    ],
    "correctIndex": 0,
    "notes": "Alabama among leaders"
  },
  {
    "id": 227,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Which school has the most Heisman winners?",
    "options": [
      "Notre Dame",
      "USC",
      "Oklahoma",
      "Ohio State"
    ],
    "correctIndex": 1,
    "notes": "USC"
  },
  {
    "id": 230,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2016 national championship?",
    "options": [
      "Washington",
      "Ohio State",
      "Alabama",
      "Clemson"
    ],
    "correctIndex": 3,
    "notes": "Clemson over Alabama"
  },
  {
    "id": 231,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2017 national championship?",
    "options": [
      "Alabama",
      "Georgia",
      "Oklahoma",
      "Clemson"
    ],
    "correctIndex": 0,
    "notes": "Alabama over Georgia"
  },
  {
    "id": 233,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team was the first #4 seed to win the CFP title?",
    "options": [
      "Ohio State",
      "Georgia",
      "Alabama",
      "Clemson"
    ],
    "correctIndex": 0,
    "notes": "Ohio State 2014"
  },
  {
    "id": 234,
    "category": "Bowls & Playoff",
    "difficulty": "Very Hard",
    "question": "Which year featured a Michigan-Nebraska split national title?",
    "options": [
      "1990",
      "1994",
      "1995",
      "1997"
    ],
    "correctIndex": 3,
    "notes": "1997"
  },
  {
    "id": 235,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "What is the Ohio State drum major famous for?",
    "options": [
      "Script Ohio only",
      "The backbend",
      "None",
      "Both"
    ],
    "correctIndex": 1,
    "notes": "Backbend"
  },
  {
    "id": 236,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school has the Tiger Walk tradition?",
    "options": [
      "LSU",
      "Missouri",
      "Clemson",
      "Auburn"
    ],
    "correctIndex": 3,
    "notes": "Auburn"
  },
  {
    "id": 238,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school has a live buffalo mascot?",
    "options": [
      "Kansas State",
      "Nebraska",
      "Colorado",
      "Oklahoma"
    ],
    "correctIndex": 2,
    "notes": "Colorado Ralphie"
  },
  {
    "id": 239,
    "category": "Traditions & Culture",
    "difficulty": "Very Hard",
    "question": "What is the Sagarin system in college football?",
    "options": [
      "None",
      "Both used in BCS",
      "Jeff Sagarin computer rankings",
      "Human poll"
    ],
    "correctIndex": 2,
    "notes": "Computer ranking"
  },
  {
    "id": 241,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which conference did Maryland leave for the Big Ten?",
    "options": [
      "Big East",
      "Independent",
      "ACC",
      "SEC"
    ],
    "correctIndex": 2,
    "notes": "ACC"
  },
  {
    "id": 243,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which schools joined the SEC in 2012?",
    "options": [
      "Texas A&M and Missouri",
      "Only Missouri",
      "Only Texas A&M",
      "South Carolina"
    ],
    "correctIndex": 0,
    "notes": "Both"
  },
  {
    "id": 244,
    "category": "Conferences & History",
    "difficulty": "Very Hard",
    "question": "Which conference split into the SEC and later influenced the ACC?",
    "options": [
      "SWC",
      "WAC",
      "Big 8",
      "Southern Conference"
    ],
    "correctIndex": 3,
    "notes": "Southern Conference"
  },
  {
    "id": 245,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which award is given to the best tight end?",
    "options": [
      "None",
      "Ozzie Newsome Award",
      "Both",
      "John Mackey Award"
    ],
    "correctIndex": 3,
    "notes": "John Mackey Award"
  },
  {
    "id": 246,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What trophy is given to the best running back?",
    "options": [
      "Walter Camp",
      "Maxwell",
      "Doak Walker Award",
      "Both"
    ],
    "correctIndex": 2,
    "notes": "Doak Walker Award"
  },
  {
    "id": 247,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Which school has the mascot The Tree?",
    "options": [
      "Washington",
      "California",
      "Stanford",
      "Oregon"
    ],
    "correctIndex": 2,
    "notes": "Stanford"
  },
  {
    "id": 248,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which player won the 2003 Heisman at Oklahoma?",
    "options": [
      "Jason White",
      "Mark Clayton",
      "Tommie Harris",
      "Bradie James"
    ],
    "correctIndex": 0,
    "notes": "Jason White"
  },
  {
    "id": 249,
    "category": "Deep Cuts",
    "difficulty": "Very Hard",
    "question": "Which schools still use live animal mascots?",
    "options": [
      "LSU and Colorado among others",
      "None",
      "Only LSU",
      "Only Colorado"
    ],
    "correctIndex": 0,
    "notes": "Multiple including Mike and Ralphie"
  },
  {
    "id": 250,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which Oklahoma QB won the 2008 Heisman?",
    "options": [
      "Kyler Murray",
      "Jason White",
      "Sam Bradford",
      "Baker Mayfield"
    ],
    "correctIndex": 2,
    "notes": "Sam Bradford"
  },
  {
    "id": 251,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the 2010 Heisman at Auburn?",
    "options": [
      "Wes Byrum",
      "Darvin Adams",
      "Nick Fairley",
      "Cam Newton"
    ],
    "correctIndex": 3,
    "notes": "Cam Newton"
  },
  {
    "id": 252,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the 2014 Heisman?",
    "options": [
      "Marcus Mariota",
      "Amari Cooper",
      "Todd Gurley",
      "Jameis Winston"
    ],
    "correctIndex": 0,
    "notes": "Marcus Mariota"
  },
  {
    "id": 253,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the 1992 national championship?",
    "options": [
      "Miami",
      "Alabama",
      "Notre Dame",
      "Florida State"
    ],
    "correctIndex": 1,
    "notes": "Alabama over Miami"
  },
  {
    "id": 254,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached the 1996 Florida national championship team?",
    "options": [
      "Urban Meyer",
      "Galen Hall",
      "Steve Spurrier",
      "Ron Zook"
    ],
    "correctIndex": 2,
    "notes": "Steve Spurrier"
  },
  {
    "id": 255,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the 2013 national championship?",
    "options": [
      "Florida State",
      "Michigan State",
      "Alabama",
      "Auburn"
    ],
    "correctIndex": 0,
    "notes": "Florida State over Auburn"
  },
  {
    "id": 256,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which school won the 1985 national championship?",
    "options": [
      "Penn State",
      "Oklahoma",
      "Miami",
      "Michigan"
    ],
    "correctIndex": 1,
    "notes": "Oklahoma"
  },
  {
    "id": 257,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which player was known as The Bus at Notre Dame?",
    "options": [
      "Ricky Watters",
      "Autry Denson",
      "Jerome Bettis",
      "Reggie Brooks"
    ],
    "correctIndex": 2,
    "notes": "Jerome Bettis"
  },
  {
    "id": 259,
    "category": "Players & Legends",
    "difficulty": "Medium",
    "question": "Which player won the 2005 Heisman before it was vacated?",
    "options": [
      "Matt Leinart",
      "Brady Quinn",
      "Reggie Bush",
      "Vince Young"
    ],
    "correctIndex": 2,
    "notes": "Reggie Bush"
  },
  {
    "id": 260,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who scored the winning TD on the Kick Six in the 2013 Iron Bowl?",
    "options": [
      "Chris Davis",
      "Adam Griffith",
      "T.J. Yeldon",
      "Cade Foster"
    ],
    "correctIndex": 0,
    "notes": "Chris Davis return"
  },
  {
    "id": 261,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2009 BCS National Championship?",
    "options": [
      "Florida",
      "Texas",
      "Alabama",
      "Oklahoma"
    ],
    "correctIndex": 2,
    "notes": "Alabama over Texas"
  },
  {
    "id": 265,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which award is given to the best defensive back?",
    "options": [
      "Both",
      "Jack Tatum Trophy",
      "Jim Thorpe Award",
      "Bronko Nagurski"
    ],
    "correctIndex": 2,
    "notes": "Jim Thorpe Award"
  },
  {
    "id": 267,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Which school has Mike the Tiger?",
    "options": [
      "LSU",
      "Missouri",
      "Clemson",
      "Auburn"
    ],
    "correctIndex": 0,
    "notes": "LSU"
  },
  {
    "id": 268,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which player won the 2001 Heisman at Nebraska?",
    "options": [
      "Ahman Green",
      "Mike Rozier",
      "Eric Crouch",
      "Tommie Frazier"
    ],
    "correctIndex": 2,
    "notes": "Eric Crouch"
  },
  {
    "id": 280,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the Apple Cup?",
    "options": [
      "Washington vs Washington State",
      "Stanford vs Cal",
      "UCLA vs USC",
      "Oregon vs Oregon State"
    ],
    "correctIndex": 0,
    "notes": "Washington-Washington State"
  },
  {
    "id": 281,
    "category": "Heisman Trophy",
    "difficulty": "Very Hard",
    "question": "Which Heisman winner was the first from Hawaii?",
    "options": [
      "Timmy Chang",
      "Colt Brennan",
      "Marcus Mariota",
      "None"
    ],
    "correctIndex": 2,
    "notes": "Marcus Mariota born in Hawaii"
  },
  {
    "id": 282,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished second in the 2006 Heisman voting?",
    "options": [
      "Mike Hart",
      "Steve Slaton",
      "Brady Quinn",
      "Darren McFadden"
    ],
    "correctIndex": 3,
    "notes": "Darren McFadden"
  },
  {
    "id": 283,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which player won the 1991 Heisman at Michigan?",
    "options": [
      "Elvis Grbac",
      "Tyrone Wheatley",
      "Desmond Howard",
      "Chris Calloway"
    ],
    "correctIndex": 2,
    "notes": "Desmond Howard"
  },
  {
    "id": 284,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the 1993 Heisman at Florida State?",
    "options": [
      "Warrick Dunn",
      "Charlie Ward",
      "Tamarick Vanover",
      "Casey Weldon"
    ],
    "correctIndex": 1,
    "notes": "Charlie Ward"
  },
  {
    "id": 285,
    "category": "Heisman Trophy",
    "difficulty": "Very Hard",
    "question": "Which Heisman winner threw for 4,000+ and rushed for 1,000+ in one season?",
    "options": [
      "Kyler Murray",
      "Cam Newton",
      "Johnny Manziel",
      "Lamar Jackson"
    ],
    "correctIndex": 3,
    "notes": "Lamar Jackson 2016"
  },
  {
    "id": 286,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished runner-up to Tim Tebow in 2007?",
    "options": [
      "Colt Brennan",
      "Darren McFadden",
      "Graham Harrell",
      "Chase Daniel"
    ],
    "correctIndex": 1,
    "notes": "Darren McFadden"
  },
  {
    "id": 287,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Which Notre Dame player won the Heisman in 1964?",
    "options": [
      "Paul Hornung",
      "Leon Hart",
      "Johnny Lattner",
      "John Huarte"
    ],
    "correctIndex": 3,
    "notes": "John Huarte"
  },
  {
    "id": 288,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the 2011 Heisman at Baylor?",
    "options": [
      "Art Briles",
      "Robert Griffin III",
      "Kendall Wright",
      "Terrance Ganaway"
    ],
    "correctIndex": 1,
    "notes": "RG3"
  },
  {
    "id": 289,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the 2004 Heisman at USC?",
    "options": [
      "Carson Palmer",
      "Reggie Bush",
      "Matt Cassel",
      "Matt Leinart"
    ],
    "correctIndex": 3,
    "notes": "Matt Leinart"
  },
  {
    "id": 290,
    "category": "Heisman Trophy",
    "difficulty": "Very Hard",
    "question": "Which Heisman winner also starred in MLB?",
    "options": [
      "Bo Jackson",
      "Both A and B",
      "Deion Sanders",
      "None"
    ],
    "correctIndex": 0,
    "notes": "Bo Jackson 1985 Heisman"
  },
  {
    "id": 291,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the 2000 Heisman at Florida State?",
    "options": [
      "Peter Warrick",
      "Warrick Dunn",
      "Chris Weinke",
      "Charlie Ward"
    ],
    "correctIndex": 2,
    "notes": "Chris Weinke"
  },
  {
    "id": 292,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the 1999 Heisman at Wisconsin?",
    "options": [
      "Vital y Pisetsky",
      "Mike Samuel",
      "Ron Dayne",
      "Chris Chambers"
    ],
    "correctIndex": 2,
    "notes": "Ron Dayne"
  },
  {
    "id": 296,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which team won the 1978 national title in a split with USC?",
    "options": [
      "Oklahoma",
      "Alabama",
      "Notre Dame",
      "Penn State"
    ],
    "correctIndex": 1,
    "notes": "Alabama AP / USC UPI"
  },
  {
    "id": 297,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached the 1983 Miami national championship team?",
    "options": [
      "Jimmy Johnson",
      "Dennis Erickson",
      "Butch Davis",
      "Howard Schnellenberger"
    ],
    "correctIndex": 3,
    "notes": "Howard Schnellenberger"
  },
  {
    "id": 299,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which school won the 1951 national championship under Bud Wilkinson?",
    "options": [
      "Michigan State",
      "Oklahoma",
      "Tennessee",
      "Maryland"
    ],
    "correctIndex": 1,
    "notes": "Oklahoma"
  },
  {
    "id": 300,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached the 2001 Miami national championship team?",
    "options": [
      "Ed Orgeron",
      "Randy Shannon",
      "Larry Coker",
      "Butch Davis"
    ],
    "correctIndex": 2,
    "notes": "Larry Coker"
  },
  {
    "id": 301,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the 1986 national championship?",
    "options": [
      "Penn State",
      "Alabama",
      "Oklahoma",
      "Miami"
    ],
    "correctIndex": 0,
    "notes": "Penn State over Miami"
  },
  {
    "id": 302,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached the 1994 Nebraska national championship team?",
    "options": [
      "Tom Osborne",
      "Turner Gill",
      "Bob Devaney",
      "Frank Solich"
    ],
    "correctIndex": 0,
    "notes": "Tom Osborne"
  },
  {
    "id": 303,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the 1982 national championship?",
    "options": [
      "Georgia",
      "Nebraska",
      "Penn State",
      "SMU"
    ],
    "correctIndex": 2,
    "notes": "Penn State"
  },
  {
    "id": 304,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached the 1980 Georgia national championship team?",
    "options": [
      "Jim Donnan",
      "Mark Richt",
      "Vince Dooley",
      "Ray Goff"
    ],
    "correctIndex": 2,
    "notes": "Vince Dooley"
  },
  {
    "id": 305,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which team won the 1973 national championship under Ara Parseghian?",
    "options": [
      "Notre Dame",
      "Ohio State",
      "Michigan",
      "Alabama"
    ],
    "correctIndex": 0,
    "notes": "Notre Dame"
  },
  {
    "id": 306,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the 1987 national championship?",
    "options": [
      "Oklahoma",
      "Miami",
      "Syracuse",
      "Florida State"
    ],
    "correctIndex": 1,
    "notes": "Miami"
  },
  {
    "id": 307,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Who coached the 1987 Miami national championship team?",
    "options": [
      "Dennis Erickson",
      "Howard Schnellenberger",
      "Jimmy Johnson",
      "Butch Davis"
    ],
    "correctIndex": 2,
    "notes": "Jimmy Johnson"
  },
  {
    "id": 308,
    "category": "National Championships",
    "difficulty": "Very Hard",
    "question": "Which team won the 1975 national championship under Barry Switzer?",
    "options": [
      "Oklahoma",
      "Michigan",
      "Ohio State",
      "Alabama"
    ],
    "correctIndex": 0,
    "notes": "Oklahoma"
  },
  {
    "id": 309,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the 1995 national championship?",
    "options": [
      "Tennessee",
      "Nebraska",
      "Florida",
      "Ohio State"
    ],
    "correctIndex": 1,
    "notes": "Nebraska"
  },
  {
    "id": 311,
    "category": "Rivalries",
    "difficulty": "Very Hard",
    "question": "What is the trophy for Iowa vs Nebraska?",
    "options": [
      "Cy-Hawk",
      "Heartland Trophy",
      "Heroes Trophy",
      "Floyd of Rosedale"
    ],
    "correctIndex": 2,
    "notes": "Heroes Trophy"
  },
  {
    "id": 312,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which teams play for the Bronze Boot?",
    "options": [
      "Wyoming and Colorado State",
      "Utah State and Wyoming",
      "Colorado and Colorado State",
      "Wyoming and Air Force"
    ],
    "correctIndex": 0,
    "notes": "Wyoming-Colorado State"
  },
  {
    "id": 313,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the Bedlam rivalry?",
    "options": [
      "Kansas vs Kansas State",
      "Oklahoma vs Oklahoma State",
      "Texas vs Oklahoma",
      "Missouri vs Kansas"
    ],
    "correctIndex": 1,
    "notes": "Oklahoma-Oklahoma State"
  },
  {
    "id": 314,
    "category": "Rivalries",
    "difficulty": "Very Hard",
    "question": "What trophy is currently awarded for Illinois-Northwestern?",
    "options": [
      "Land of Lincoln Trophy",
      "None",
      "Both historically",
      "Sweet Sioux Tomahawk"
    ],
    "correctIndex": 0,
    "notes": "Land of Lincoln Trophy"
  },
  {
    "id": 315,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "Which rivalry is known as Farmageddon?",
    "options": [
      "Nebraska vs Iowa",
      "Kansas State vs Iowa State",
      "Kansas vs Iowa State",
      "Missouri vs Kansas State"
    ],
    "correctIndex": 1,
    "notes": "Kansas State-Iowa State"
  },
  {
    "id": 316,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the Territorial Cup?",
    "options": [
      "New Mexico vs New Mexico State",
      "Arizona vs Arizona State",
      "Colorado vs Colorado State",
      "Utah vs Utah State"
    ],
    "correctIndex": 1,
    "notes": "Arizona-Arizona State"
  },
  {
    "id": 317,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the Commonwealth Cup?",
    "options": [
      "Maryland vs Virginia",
      "Penn State vs Pittsburgh",
      "Virginia vs Virginia Tech",
      "Kentucky vs Louisville"
    ],
    "correctIndex": 2,
    "notes": "Virginia-Virginia Tech"
  },
  {
    "id": 318,
    "category": "Rivalries",
    "difficulty": "Hard",
    "question": "What is the Border War historically?",
    "options": [
      "Texas vs Oklahoma",
      "Missouri vs Kansas",
      "All used",
      "Arizona vs Arizona State"
    ],
    "correctIndex": 1,
    "notes": "Missouri-Kansas"
  },
  {
    "id": 320,
    "category": "Rivalries",
    "difficulty": "Very Hard",
    "question": "What was the Textile Bowl?",
    "options": [
      "North Carolina vs NC State",
      "Clemson vs South Carolina historically",
      "Both",
      "None"
    ],
    "correctIndex": 1,
    "notes": "Clemson-South Carolina old name"
  },
  {
    "id": 321,
    "category": "Coaches",
    "difficulty": "Very Hard",
    "question": "Who coached the 1979 Alabama national championship team?",
    "options": [
      "Bear Bryant",
      "Bill Curry",
      "Ray Perkins",
      "Gene Stallings"
    ],
    "correctIndex": 0,
    "notes": "Bear Bryant"
  },
  {
    "id": 322,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach led the 2000 Oklahoma national championship team?",
    "options": [
      "Barry Switzer",
      "Bob Stoops",
      "Gary Gibbs",
      "John Blake"
    ],
    "correctIndex": 1,
    "notes": "Bob Stoops"
  },
  {
    "id": 323,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached Florida State to the 2013 national title?",
    "options": [
      "Odell Haggins",
      "Jimbo Fisher",
      "Mark Richt",
      "Bobby Bowden"
    ],
    "correctIndex": 1,
    "notes": "Jimbo Fisher"
  },
  {
    "id": 324,
    "category": "Coaches",
    "difficulty": "Very Hard",
    "question": "Which coach won a national title at Colorado in 1990?",
    "options": [
      "Bill McCartney",
      "Gary Barnett",
      "Chuck Fairbanks",
      "Rick Neuheisel"
    ],
    "correctIndex": 0,
    "notes": "Bill McCartney"
  },
  {
    "id": 325,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached the 2008 Florida national championship team?",
    "options": [
      "Urban Meyer",
      "Jim McElwain",
      "Will Muschamp",
      "Steve Spurrier"
    ],
    "correctIndex": 0,
    "notes": "Urban Meyer"
  },
  {
    "id": 326,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached the 2006 Florida national championship team?",
    "options": [
      "Urban Meyer",
      "Steve Spurrier",
      "Ron Zook",
      "Will Muschamp"
    ],
    "correctIndex": 0,
    "notes": "Urban Meyer"
  },
  {
    "id": 327,
    "category": "Coaches",
    "difficulty": "Very Hard",
    "question": "Who coached the 1989 Miami national championship team?",
    "options": [
      "Howard Schnellenberger",
      "Dennis Erickson",
      "Jimmy Johnson",
      "Butch Davis"
    ],
    "correctIndex": 1,
    "notes": "Dennis Erickson"
  },
  {
    "id": 328,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Which coach led TCU to multiple major bowls in the 2000s-2010s?",
    "options": [
      "Sonny Dykes",
      "Dennis Franchione",
      "Gary Patterson",
      "Jimbo Fisher"
    ],
    "correctIndex": 2,
    "notes": "Gary Patterson"
  },
  {
    "id": 330,
    "category": "Coaches",
    "difficulty": "Very Hard",
    "question": "Who coached the 1997 Michigan national championship team?",
    "options": [
      "Bo Schembechler",
      "Gary Moeller",
      "Lloyd Carr",
      "Jim Harbaugh"
    ],
    "correctIndex": 2,
    "notes": "Lloyd Carr"
  },
  {
    "id": 331,
    "category": "Coaches",
    "difficulty": "Hard",
    "question": "Who coached Boise State to the 2007 Fiesta Bowl upset?",
    "options": [
      "Houston Nutt",
      "Chris Petersen",
      "Dan Hawkins",
      "Bryan Harsin"
    ],
    "correctIndex": 1,
    "notes": "Chris Petersen"
  },
  {
    "id": 336,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who is the all-time leading rusher at USC among these?",
    "options": [
      "Charles White",
      "O.J. Simpson",
      "Marcus Allen",
      "Ricky Bell"
    ],
    "correctIndex": 0,
    "notes": "Charles White among leaders"
  },
  {
    "id": 337,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which QB holds high career passing yards at Alabama?",
    "options": [
      "Bryce Young",
      "AJ McCarron",
      "Tua Tagovailoa",
      "Jay Barker"
    ],
    "correctIndex": 1,
    "notes": "AJ McCarron"
  },
  {
    "id": 338,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Who scored the first TD in the first CFP National Championship Game?",
    "options": [
      "Ezekiel Elliott",
      "Michael Thomas",
      "Nick Vannett",
      "Cardale Jones"
    ],
    "correctIndex": 0,
    "notes": "Ezekiel Elliott"
  },
  {
    "id": 339,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which player was known as The Great One at Nebraska?",
    "options": [
      "Roger Craig",
      "Mike Rozier",
      "Tommie Frazier",
      "Johnny Rodgers"
    ],
    "correctIndex": 3,
    "notes": "Johnny Rodgers"
  },
  {
    "id": 340,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Who caught the Bluegrass Miracle Hail Mary for LSU?",
    "options": [
      "Skyler Green",
      "Devery Henderson",
      "Dwayne Bowe",
      "Michael Clayton"
    ],
    "correctIndex": 1,
    "notes": "Devery Henderson"
  },
  {
    "id": 341,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Who was the first overall pick in the 2021 NFL Draft from Clemson?",
    "options": [
      "Zach Wilson",
      "Trevor Lawrence",
      "Trey Lance",
      "Justin Fields"
    ],
    "correctIndex": 1,
    "notes": "Trevor Lawrence"
  },
  {
    "id": 342,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which Alabama player won the 2015 Heisman?",
    "options": [
      "Trent Richardson",
      "Derrick Henry",
      "Najee Harris",
      "Mark Ingram"
    ],
    "correctIndex": 1,
    "notes": "Derrick Henry"
  },
  {
    "id": 343,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Who threw the game-winning TD in the 2018 National Championship for Clemson?",
    "options": [
      "Hunter Johnson",
      "Kelly Bryant",
      "Trevor Lawrence",
      "Chase Brice"
    ],
    "correctIndex": 2,
    "notes": "Trevor Lawrence to Hunter Renfrow"
  },
  {
    "id": 346,
    "category": "Players & Legends",
    "difficulty": "Very Hard",
    "question": "Who caught the Hail Mary in the 1984 Boston College-Miami game?",
    "options": [
      "Kelvin Moore",
      "Doug Flutie",
      "Gerard Phelan",
      "Mark MacDonald"
    ],
    "correctIndex": 2,
    "notes": "Gerard Phelan"
  },
  {
    "id": 348,
    "category": "Players & Legends",
    "difficulty": "Hard",
    "question": "Which player was the first freshman to win the Heisman?",
    "options": [
      "Jameis Winston",
      "Lamar Jackson",
      "Herschel Walker",
      "Johnny Manziel"
    ],
    "correctIndex": 3,
    "notes": "Johnny Manziel"
  },
  {
    "id": 352,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which player holds the single-season rushing record?",
    "options": [
      "Marcus Allen",
      "Mike Rozier",
      "OJ Simpson",
      "Barry Sanders"
    ],
    "correctIndex": 3,
    "notes": "Barry Sanders 2628"
  },
  {
    "id": 354,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which team holds the longest winning streak in FBS history?",
    "options": [
      "Oklahoma 47 games",
      "USC",
      "Notre Dame",
      "Miami"
    ],
    "correctIndex": 0,
    "notes": "Oklahoma 1953-57"
  },
  {
    "id": 362,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2003 Fiesta Bowl BCS title?",
    "options": [
      "Ohio State",
      "USC",
      "Oklahoma",
      "Miami"
    ],
    "correctIndex": 0,
    "notes": "Ohio State over Miami in OT"
  },
  {
    "id": 363,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2012 BCS National Championship?",
    "options": [
      "LSU",
      "Oklahoma State",
      "Alabama",
      "Stanford"
    ],
    "correctIndex": 2,
    "notes": "Alabama over LSU"
  },
  {
    "id": 364,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2011 BCS National Championship?",
    "options": [
      "Auburn",
      "TCU",
      "Oregon",
      "Wisconsin"
    ],
    "correctIndex": 0,
    "notes": "Auburn over Oregon"
  },
  {
    "id": 365,
    "category": "Bowls & Playoff",
    "difficulty": "Very Hard",
    "question": "Which team won the 2005 Orange Bowl BCS title?",
    "options": [
      "Auburn",
      "Oklahoma",
      "Texas",
      "USC"
    ],
    "correctIndex": 3,
    "notes": "USC over Oklahoma"
  },
  {
    "id": 366,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2004 Sugar Bowl BCS title?",
    "options": [
      "Georgia",
      "LSU",
      "USC",
      "Oklahoma"
    ],
    "correctIndex": 1,
    "notes": "LSU over Oklahoma"
  },
  {
    "id": 367,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2002 Rose Bowl BCS title?",
    "options": [
      "Colorado",
      "Oregon",
      "Miami",
      "Nebraska"
    ],
    "correctIndex": 2,
    "notes": "Miami over Nebraska"
  },
  {
    "id": 368,
    "category": "Bowls & Playoff",
    "difficulty": "Very Hard",
    "question": "Which team won the 2000 Orange Bowl BCS title?",
    "options": [
      "Wisconsin",
      "Florida State",
      "Tennessee",
      "Virginia Tech"
    ],
    "correctIndex": 1,
    "notes": "Florida State over Virginia Tech"
  },
  {
    "id": 369,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2018 national championship?",
    "options": [
      "Alabama",
      "Clemson",
      "Oklahoma",
      "Notre Dame"
    ],
    "correctIndex": 1,
    "notes": "Clemson over Alabama"
  },
  {
    "id": 370,
    "category": "Bowls & Playoff",
    "difficulty": "Hard",
    "question": "Which team won the 2020 national championship played in 2021?",
    "options": [
      "Notre Dame",
      "Clemson",
      "Alabama",
      "Ohio State"
    ],
    "correctIndex": 2,
    "notes": "Alabama over Ohio State"
  },
  {
    "id": 371,
    "category": "Bowls & Playoff",
    "difficulty": "Very Hard",
    "question": "Which team won the 1991 national championship in a split?",
    "options": [
      "Miami AP / Washington Coaches",
      "Florida State",
      "Washington both",
      "Miami both"
    ],
    "correctIndex": 0,
    "notes": "Split"
  },
  {
    "id": 375,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school has the Script Ohio tradition?",
    "options": [
      "Michigan",
      "Penn State",
      "Ohio State",
      "Wisconsin"
    ],
    "correctIndex": 2,
    "notes": "Ohio State"
  },
  {
    "id": 376,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "What is Jump Around associated with?",
    "options": [
      "Iowa",
      "Nebraska",
      "Minnesota",
      "Wisconsin"
    ],
    "correctIndex": 3,
    "notes": "Wisconsin"
  },
  {
    "id": 382,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school has the 12th Man tradition?",
    "options": [
      "Texas",
      "LSU",
      "Alabama",
      "Texas A&M"
    ],
    "correctIndex": 3,
    "notes": "Texas A&M"
  },
  {
    "id": 383,
    "category": "Traditions & Culture",
    "difficulty": "Hard",
    "question": "Which school has the Dotting of the i?",
    "options": [
      "Penn State",
      "Michigan",
      "Wisconsin",
      "Ohio State"
    ],
    "correctIndex": 3,
    "notes": "Ohio State"
  },
  {
    "id": 384,
    "category": "Traditions & Culture",
    "difficulty": "Very Hard",
    "question": "Which school has the Fifth Quarter band tradition?",
    "options": [
      "Nebraska",
      "Minnesota",
      "Iowa",
      "Wisconsin"
    ],
    "correctIndex": 2,
    "notes": "Iowa \u2014 Hawkeye Marching Band's postgame concert tradition"
  },
  {
    "id": 385,
    "category": "Conferences & History",
    "difficulty": "Very Hard",
    "question": "Which school was the first to leave the Big 12 for the Big Ten?",
    "options": [
      "Texas A&M",
      "Missouri",
      "Nebraska",
      "Colorado"
    ],
    "correctIndex": 2,
    "notes": "Nebraska"
  },
  {
    "id": 386,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which conference did TCU leave to join the Big 12?",
    "options": [
      "Mountain West",
      "Conference USA",
      "WAC",
      "Independent"
    ],
    "correctIndex": 0,
    "notes": "Mountain West"
  },
  {
    "id": 387,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which schools joined the ACC from the Big East in 2014?",
    "options": [
      "Only Syracuse",
      "Louisville Pittsburgh Syracuse",
      "Only Pittsburgh",
      "Only Louisville"
    ],
    "correctIndex": 1,
    "notes": "All three"
  },
  {
    "id": 389,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which schools left the Pac-12 for the Big 12 in recent realignment?",
    "options": [
      "Only Colorado",
      "Only Arizona",
      "Only Utah",
      "Colorado Utah Arizona Arizona State"
    ],
    "correctIndex": 3,
    "notes": "All four"
  },
  {
    "id": 391,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which conference did West Virginia leave to join the Big 12?",
    "options": [
      "C-USA",
      "ACC",
      "Big East",
      "Independent"
    ],
    "correctIndex": 2,
    "notes": "Big East"
  },
  {
    "id": 392,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which schools joined the SEC in 1992?",
    "options": [
      "None",
      "Only South Carolina",
      "South Carolina and Arkansas",
      "Only Arkansas"
    ],
    "correctIndex": 2,
    "notes": "Both"
  },
  {
    "id": 394,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which schools joined the Big Ten in 2014?",
    "options": [
      "Nebraska",
      "Maryland and Rutgers",
      "Only Maryland",
      "Only Rutgers"
    ],
    "correctIndex": 1,
    "notes": "Both"
  },
  {
    "id": 396,
    "category": "Conferences & History",
    "difficulty": "Hard",
    "question": "Which schools left the Pac-12 for the Big Ten in the 2020s?",
    "options": [
      "USC UCLA Oregon Washington",
      "Colorado",
      "Only Oregon Washington",
      "Only USC UCLA"
    ],
    "correctIndex": 0,
    "notes": "All four"
  },
  {
    "id": 398,
    "category": "Deep Cuts",
    "difficulty": "Very Hard",
    "question": "Which awards are given for kickers and punters?",
    "options": [
      "Only Lou Groza",
      "None",
      "Only Ray Guy",
      "Lou Groza and Ray Guy"
    ],
    "correctIndex": 3,
    "notes": "Both exist"
  },
  {
    "id": 399,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Biletnikoff Award given for?",
    "options": [
      "Best tight end",
      "Best RB",
      "Best wide receiver",
      "Best QB"
    ],
    "correctIndex": 2,
    "notes": "Best WR"
  },
  {
    "id": 400,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Butkus Award given for?",
    "options": [
      "Best linebacker",
      "Best coach",
      "Best defensive lineman",
      "Best defensive back"
    ],
    "correctIndex": 0,
    "notes": "Best LB"
  },
  {
    "id": 401,
    "category": "Deep Cuts",
    "difficulty": "Very Hard",
    "question": "Which awards are for interior linemen and centers?",
    "options": [
      "Only Rimington",
      "Lombardi only",
      "Outland and Rimington",
      "Only Outland"
    ],
    "correctIndex": 2,
    "notes": "Both"
  },
  {
    "id": 402,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Maxwell Award given for?",
    "options": [
      "Best all-around player",
      "Best coach",
      "Best QB only",
      "Best freshman"
    ],
    "correctIndex": 0,
    "notes": "Best player"
  },
  {
    "id": 403,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Davey OBrien Award given for?",
    "options": [
      "Best WR",
      "Best coach",
      "Best quarterback",
      "Best RB"
    ],
    "correctIndex": 2,
    "notes": "Best QB"
  },
  {
    "id": 404,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Jim Thorpe Award given for?",
    "options": [
      "Best LB",
      "Best RB",
      "Best defensive back",
      "Best DL"
    ],
    "correctIndex": 2,
    "notes": "Best DB"
  },
  {
    "id": 405,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Rimington Trophy given for?",
    "options": [
      "Best center",
      "Best OT",
      "Best OG",
      "Best DT"
    ],
    "correctIndex": 0,
    "notes": "Best center"
  },
  {
    "id": 406,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Outland Trophy given for?",
    "options": [
      "Best interior lineman",
      "Best coach",
      "Both used",
      "Best overall lineman"
    ],
    "correctIndex": 0,
    "notes": "Best interior lineman"
  },
  {
    "id": 407,
    "category": "Deep Cuts",
    "difficulty": "Very Hard",
    "question": "Which awards are given to coaches?",
    "options": [
      "Bear Bryant and Eddie Robinson",
      "Only Eddie Robinson",
      "Home Depot only",
      "Only Bear Bryant"
    ],
    "correctIndex": 0,
    "notes": "Multiple major awards"
  },
  {
    "id": 408,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Doak Walker Award given for?",
    "options": [
      "Best WR",
      "Best QB",
      "Best running back",
      "Best TE"
    ],
    "correctIndex": 2,
    "notes": "Best RB"
  },
  {
    "id": 409,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the John Mackey Award given for?",
    "options": [
      "Best OT",
      "Best WR",
      "Best tight end",
      "Best LB"
    ],
    "correctIndex": 2,
    "notes": "Best TE"
  },
  {
    "id": 410,
    "category": "Deep Cuts",
    "difficulty": "Very Hard",
    "question": "Which player was the first to rush for 2000 yards in a season in FBS?",
    "options": [
      "Herschel Walker",
      "Marcus Allen",
      "Barry Sanders",
      "Tony Dorsett"
    ],
    "correctIndex": 1,
    "notes": "Marcus Allen 1981"
  },
  {
    "id": 411,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "What is the Wishbone offense associated with?",
    "options": [
      "Oklahoma Texas Alabama 1970s",
      "USC",
      "Notre Dame",
      "Michigan"
    ],
    "correctIndex": 0,
    "notes": "Wishbone teams"
  },
  {
    "id": 500,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Memphis football history?",
    "options": [
      "Kyle Whittingham",
      "Mike Norvell",
      "Gary Pinkel",
      "Chris Petersen"
    ],
    "correctIndex": 1,
    "notes": "Mike Norvell, 38-15 (2016-19)"
  },
  {
    "id": 501,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in UCF football history?",
    "options": [
      "Steve Spurrier",
      "George O'Leary",
      "Charles McClendon",
      "Dan McGugin"
    ],
    "correctIndex": 1,
    "notes": "George O'Leary, 2 stints, most wins in school history"
  },
  {
    "id": 502,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Utah football history?",
    "options": [
      "Frank Solich",
      "George Welsh",
      "Mike Price",
      "Kyle Whittingham"
    ],
    "correctIndex": 3,
    "notes": "Kyle Whittingham, 150+ (2005-present)"
  },
  {
    "id": 503,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in California football history?",
    "options": [
      "Pat Fitzgerald",
      "Don James",
      "Andy Smith",
      "Mike Norvell"
    ],
    "correctIndex": 2,
    "notes": "Andy Smith, 74-16-7 (1916-25)"
  },
  {
    "id": 504,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Clemson football history?",
    "options": [
      "Frank Beamer",
      "Grant Teaff",
      "Bernie Bierman",
      "Dabo Swinney"
    ],
    "correctIndex": 3,
    "notes": "Dabo Swinney, 190+ (2008-present)"
  },
  {
    "id": 505,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Fresno State football history?",
    "options": [
      "Randy Edsall",
      "Pat Fitzgerald",
      "Rocky Long",
      "Pat Hill"
    ],
    "correctIndex": 3,
    "notes": "Pat Hill, 83-72 (1997-2011)"
  },
  {
    "id": 506,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Nebraska football history?",
    "options": [
      "Bo Schembechler",
      "Frank Solich",
      "Bobby Petrino",
      "Tom Osborne"
    ],
    "correctIndex": 3,
    "notes": "Tom Osborne, 255-49-3 (1973-97)"
  },
  {
    "id": 507,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Hawaii football history?",
    "options": [
      "Craig Bohl",
      "Joe Novak",
      "Earl Blaik",
      "June Jones"
    ],
    "correctIndex": 3,
    "notes": "June Jones, 76-41 (1999-2007)"
  },
  {
    "id": 508,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Boise State football history?",
    "options": [
      "Chris Petersen",
      "Johnny Vaught",
      "Wallace Wade",
      "Bob Stoops"
    ],
    "correctIndex": 0,
    "notes": "Chris Petersen, 92-12 (2006-13)"
  },
  {
    "id": 509,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Duke football history?",
    "options": [
      "Frank Solich",
      "Wallace Wade",
      "Andy Gustafson",
      "Gary Pinkel"
    ],
    "correctIndex": 1,
    "notes": "Wallace Wade, 110-36-7 (1931-41, 1946-50)"
  },
  {
    "id": 510,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Louisville football history?",
    "options": [
      "Bob Zuppke",
      "Bobby Petrino",
      "Bill Mallory",
      "Bill Snyder"
    ],
    "correctIndex": 1,
    "notes": "Bobby Petrino, 2 stints, most wins in school history"
  },
  {
    "id": 511,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Iowa State football history?",
    "options": [
      "Dan McCarney",
      "Joe Moglia",
      "Bill McCartney",
      "Duffy Daugherty"
    ],
    "correctIndex": 0,
    "notes": "Dan McCarney, 55-85 (1995-2006)"
  },
  {
    "id": 512,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Marshall football history?",
    "options": [
      "Vince Dooley",
      "Bernie Bierman",
      "Bobby Pruett",
      "Bobby Petrino"
    ],
    "correctIndex": 2,
    "notes": "Bobby Pruett, 94-23 (1996-2004)"
  },
  {
    "id": 513,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Missouri football history?",
    "options": [
      "Robert Neyland",
      "Jack Harbaugh",
      "Gary Pinkel",
      "Dabo Swinney"
    ],
    "correctIndex": 2,
    "notes": "Gary Pinkel, 118-73 (2001-15)"
  },
  {
    "id": 514,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Western Kentucky football history?",
    "options": [
      "Mike Price",
      "Jack Harbaugh",
      "LaVell Edwards",
      "Jerry Moore"
    ],
    "correctIndex": 1,
    "notes": "Jack Harbaugh, -"
  },
  {
    "id": 515,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in NC State football history?",
    "options": [
      "Chris Petersen",
      "Dave Doeren",
      "Bobby Bowden",
      "Bill Mallory"
    ],
    "correctIndex": 1,
    "notes": "Dave Doeren, 90+ (2013-present)"
  },
  {
    "id": 516,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Mississippi State football history?",
    "options": [
      "Pat Fitzgerald",
      "Peahead Walker",
      "Mark Stoops",
      "Allyn McKeen"
    ],
    "correctIndex": 3,
    "notes": "Allyn McKeen, 65-19-3 (1939-48)"
  },
  {
    "id": 517,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Florida State football history?",
    "options": [
      "Bobby Dodd",
      "Steve Spurrier",
      "Craig Bohl",
      "Bobby Bowden"
    ],
    "correctIndex": 3,
    "notes": "Bobby Bowden, 304-97-4 (1976-2009)"
  },
  {
    "id": 518,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Miami (FL) football history?",
    "options": [
      "Bob Stoops",
      "Frank Broyles",
      "Andy Gustafson",
      "Knute Rockne"
    ],
    "correctIndex": 2,
    "notes": "Andy Gustafson, 93-65-3 (1948-63)"
  },
  {
    "id": 519,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Texas football history?",
    "options": [
      "Bill Yeoman",
      "Darrell Royal",
      "Steve Spurrier",
      "Bobby Bowden"
    ],
    "correctIndex": 1,
    "notes": "Darrell Royal, 167-47-5 (1957-76)"
  },
  {
    "id": 520,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Oklahoma State football history?",
    "options": [
      "Kyle Whittingham",
      "Terry Donahue",
      "Mike Gundy",
      "Dick Tomey"
    ],
    "correctIndex": 2,
    "notes": "Mike Gundy, 170+ (2005-present)"
  },
  {
    "id": 521,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Michigan State football history?",
    "options": [
      "Earl Blaik",
      "Jerry Moore",
      "Duffy Daugherty",
      "Wallace Wade"
    ],
    "correctIndex": 2,
    "notes": "Duffy Daugherty, 109-69-5 (1954-72)"
  },
  {
    "id": 522,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in TCU football history?",
    "options": [
      "Wallace Wade",
      "Bobby Bowden",
      "Jack Mollenkopf",
      "Gary Patterson"
    ],
    "correctIndex": 3,
    "notes": "Gary Patterson, 181-79 (2001-21)"
  },
  {
    "id": 523,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Virginia Tech football history?",
    "options": [
      "Jeff Bower",
      "Pat Hill",
      "Frank Beamer",
      "Allyn McKeen"
    ],
    "correctIndex": 2,
    "notes": "Frank Beamer, 238-121-2 (1987-2015)"
  },
  {
    "id": 524,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in LSU football history?",
    "options": [
      "Wallace Wade",
      "Charles McClendon",
      "Mike Price",
      "Andy Smith"
    ],
    "correctIndex": 1,
    "notes": "Charles McClendon, 137-59-7 (1962-79)"
  },
  {
    "id": 525,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Syracuse football history?",
    "options": [
      "Wallace Wade",
      "Joe Novak",
      "Mike Bellotti",
      "Ben Schwartzwalder"
    ],
    "correctIndex": 3,
    "notes": "Ben Schwartzwalder, 153-91-3 (1949-73)"
  },
  {
    "id": 526,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Kentucky football history?",
    "options": [
      "Earl Blaik",
      "Dan McCarney",
      "Bobby Petrino",
      "Mark Stoops"
    ],
    "correctIndex": 3,
    "notes": "Mark Stoops, 95+ (2013-present)"
  },
  {
    "id": 527,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Northwestern football history?",
    "options": [
      "Pat Fitzgerald",
      "Frank Solich",
      "Bill Yeoman",
      "Joe Novak"
    ],
    "correctIndex": 0,
    "notes": "Pat Fitzgerald, 110-101 (2006-22)"
  },
  {
    "id": 528,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Auburn football history?",
    "options": [
      "Bobby Petrino",
      "Frank Kush",
      "Don Nehlen",
      "Shug Jordan"
    ],
    "correctIndex": 3,
    "notes": "Shug Jordan, 176-83-6 (1951-75)"
  },
  {
    "id": 529,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Who is the winningest coach in Indiana football history?",
    "options": [
      "Shug Jordan",
      "Kyle Whittingham",
      "Vince Dooley",
      "Bill Mallory"
    ],
    "correctIndex": 3,
    "notes": "Bill Mallory, 69-77-3 (1984-96)"
  },
  {
    "id": 530,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led Washington to the national championship in 1991?",
    "options": [
      "Jimbo Fisher",
      "Ara Parseghian",
      "Nick Saban",
      "Don James"
    ],
    "correctIndex": 3,
    "notes": "Don James \u2014 Washington titles: 1991"
  },
  {
    "id": 531,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led Oklahoma to the national championship in 1950?",
    "options": [
      "Dutch Meyer",
      "Dabo Swinney",
      "Paul Brown",
      "Bud Wilkinson"
    ],
    "correctIndex": 3,
    "notes": "Bud Wilkinson \u2014 Oklahoma titles: 1950, 1955, 1956"
  },
  {
    "id": 532,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led Pittsburgh to the national championship in 1937?",
    "options": [
      "Paul Dietzel",
      "Joe Paterno",
      "Red Sanders",
      "Jock Sutherland"
    ],
    "correctIndex": 3,
    "notes": "Jock Sutherland \u2014 Pittsburgh titles: 1937"
  },
  {
    "id": 533,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led Michigan to the national championship in 1948?",
    "options": [
      "Larry Coker",
      "Darrell Royal",
      "Bennie Oosterbaan",
      "Pete Carroll"
    ],
    "correctIndex": 2,
    "notes": "Bennie Oosterbaan \u2014 Michigan titles: 1948"
  },
  {
    "id": 534,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led LSU to the national championship in 1958?",
    "options": [
      "Dabo Swinney",
      "Dutch Meyer",
      "Paul Dietzel",
      "Murray Warmath"
    ],
    "correctIndex": 2,
    "notes": "Paul Dietzel \u2014 LSU titles: 1958"
  },
  {
    "id": 535,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led Alabama to the national championship in 1961?",
    "options": [
      "Jim Harbaugh",
      "Dutch Meyer",
      "Bob Stoops",
      "Bear Bryant"
    ],
    "correctIndex": 3,
    "notes": "Bear Bryant \u2014 Alabama titles: 1961, 1964, 1965, 1973, 1978, 1979"
  },
  {
    "id": 536,
    "category": "Coaches",
    "difficulty": "Medium",
    "question": "Which coach led Texas A&M to the national championship in 1939?",
    "options": [
      "Ryan Day",
      "Homer Norton",
      "Shug Jordan",
      "LaVell Edwards"
    ],
    "correctIndex": 1,
    "notes": "Homer Norton \u2014 Texas A&M titles: 1939"
  },
  {
    "id": 537,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which team had wins vacated due to the 'Reggie Bush improper-benefits scandal'?",
    "options": [
      "Penn State",
      "Ohio State",
      "USC",
      "Alabama"
    ],
    "correctIndex": 2,
    "notes": "14 wins vacated (Dec. 2004-2005 season), incl. the Jan. 2005 Orange Bowl BCS title win over Oklahoma. BCS stripped USC's 2004 national title in June 2011 \u2014 the first major-college "
  },
  {
    "id": 538,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which team had wins vacated due to the 'Jim Tressel / Terrelle Pryor 'Tattoo-gate''?",
    "options": [
      "Ohio State",
      "Florida State",
      "Penn State",
      "Alabama"
    ],
    "correctIndex": 0,
    "notes": "Entire 2010 season vacated, incl. the 2011 Sugar Bowl win over Arkansas. Tressel's career record dropped from 241-79-2 to 229-79-2."
  },
  {
    "id": 539,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which team had wins vacated due to the 'Jerry Sandusky scandal'?",
    "options": [
      "Alabama",
      "Penn State",
      "Ohio State",
      "Florida State"
    ],
    "correctIndex": 1,
    "notes": "111 wins (1998-2011) initially vacated in 2012, stripping Joe Paterno of the FBS wins record. Restored in full via a 2015 legal settlement, making Paterno the record holder again."
  },
  {
    "id": 540,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which team had wins vacated due to the 'Nick Saban textbook academic scandal'?",
    "options": [
      "Florida State",
      "USC",
      "Alabama",
      "Ohio State"
    ],
    "correctIndex": 2,
    "notes": "5 wins vacated from the 2007 season after players used scholarships to obtain free textbooks for others."
  },
  {
    "id": 541,
    "category": "Deep Cuts",
    "difficulty": "Hard",
    "question": "Which team had wins vacated due to the 'Academic-fraud case'?",
    "options": [
      "Ohio State",
      "USC",
      "Penn State",
      "Florida State"
    ],
    "correctIndex": 3,
    "notes": "12 wins vacated from the 2006-07 seasons under Bobby Bowden."
  },
  {
    "id": 542,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Maxwell Award in 2023?",
    "options": [
      "Michael Penix Jr.",
      "Ashton Jeanty",
      "Caleb Williams",
      "Bryce Young"
    ],
    "correctIndex": 0,
    "notes": "Maxwell Award (Best All-Around Player)"
  },
  {
    "id": 543,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Maxwell Award in 2021?",
    "options": [
      "Ashton Jeanty",
      "Fernando Mendoza",
      "Caleb Williams",
      "Bryce Young"
    ],
    "correctIndex": 3,
    "notes": "Maxwell Award (Best All-Around Player)"
  },
  {
    "id": 544,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Walter Camp Award in 2021?",
    "options": [
      "Caleb Williams",
      "Kenneth Walker III",
      "Jayden Daniels",
      "Travis Hunter"
    ],
    "correctIndex": 1,
    "notes": "Walter Camp Award (National Player of the Year)"
  },
  {
    "id": 545,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Walter Camp Award in 2024?",
    "options": [
      "Kenneth Walker III",
      "Jayden Daniels",
      "Fernando Mendoza",
      "Travis Hunter"
    ],
    "correctIndex": 3,
    "notes": "Walter Camp Award (National Player of the Year)"
  },
  {
    "id": 546,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Davey O'Brien Award in 2022?",
    "options": [
      "Max Duggan",
      "Cam Ward",
      "Jayden Daniels",
      "Bryce Young"
    ],
    "correctIndex": 0,
    "notes": "Davey O'Brien Award (National Quarterback)"
  },
  {
    "id": 547,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Davey O'Brien Award in 2021?",
    "options": [
      "Max Duggan",
      "Bryce Young",
      "Jayden Daniels",
      "Cam Ward"
    ],
    "correctIndex": 1,
    "notes": "Davey O'Brien Award (National Quarterback)"
  },
  {
    "id": 548,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Johnny Unitas Golden Arm Award in 2022?",
    "options": [
      "Kenny Pickett",
      "Jayden Daniels",
      "Shedeur Sanders",
      "Max Duggan"
    ],
    "correctIndex": 3,
    "notes": "Johnny Unitas Golden Arm Award (Outstanding Senior QB)"
  },
  {
    "id": 549,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Johnny Unitas Golden Arm Award in 2025?",
    "options": [
      "Max Duggan",
      "Diego Pavia",
      "Kenny Pickett",
      "Jayden Daniels"
    ],
    "correctIndex": 1,
    "notes": "Johnny Unitas Golden Arm Award (Outstanding Senior QB)"
  },
  {
    "id": 550,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Doak Walker Award in 2024?",
    "options": [
      "Bijan Robinson",
      "Ashton Jeanty",
      "Jeremiyah Love",
      "Ollie Gordon II"
    ],
    "correctIndex": 1,
    "notes": "Doak Walker Award (National Running Back)"
  },
  {
    "id": 551,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Doak Walker Award in 2023?",
    "options": [
      "Ollie Gordon II",
      "Bijan Robinson",
      "Jeremiyah Love",
      "Ashton Jeanty"
    ],
    "correctIndex": 0,
    "notes": "Doak Walker Award (National Running Back)"
  },
  {
    "id": 552,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Fred Biletnikoff Award in 2025?",
    "options": [
      "Jordan Addison",
      "Marvin Harrison Jr.",
      "Makai Lemon",
      "Jalin Hyatt"
    ],
    "correctIndex": 2,
    "notes": "Fred Biletnikoff Award (Outstanding Receiver)"
  },
  {
    "id": 553,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Fred Biletnikoff Award in 2023?",
    "options": [
      "Makai Lemon",
      "Marvin Harrison Jr.",
      "Jalin Hyatt",
      "Travis Hunter"
    ],
    "correctIndex": 1,
    "notes": "Fred Biletnikoff Award (Outstanding Receiver)"
  },
  {
    "id": 554,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Outland Trophy in 2021?",
    "options": [
      "Spencer Fano",
      "Jordan Davis",
      "Olusegun Oluwatimi",
      "T'Vondre Sweat"
    ],
    "correctIndex": 1,
    "notes": "Outland Trophy (Outstanding Interior Lineman)"
  },
  {
    "id": 555,
    "category": "Deep Cuts",
    "difficulty": "Medium",
    "question": "Who won the Chuck Bednarik Award in 2022?",
    "options": [
      "Jacob Rodriguez",
      "Jordan Davis",
      "Travis Hunter",
      "Will Anderson Jr."
    ],
    "correctIndex": 3,
    "notes": "Chuck Bednarik Award (Defensive Player of the Year)"
  },
  {
    "id": 556,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1945?",
    "options": [
      "Gary Beban",
      "Doc Blanchard",
      "Archie Griffin",
      "Herschel Walker"
    ],
    "correctIndex": 1,
    "notes": "Doc Blanchard, FB, Army"
  },
  {
    "id": 557,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 1998?",
    "options": [
      "Ricky Williams",
      "Mark Ingram",
      "Doc Blanchard",
      "John Cappelletti"
    ],
    "correctIndex": 0,
    "notes": "Ricky Williams, RB, Texas"
  },
  {
    "id": 558,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1947?",
    "options": [
      "Les Horvath",
      "Johnny Rodgers",
      "Jameis Winston",
      "John Lujack"
    ],
    "correctIndex": 3,
    "notes": "John Lujack, QB, Notre Dame"
  },
  {
    "id": 559,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 2003?",
    "options": [
      "Billy Sims",
      "Jason White",
      "Paul Hornung",
      "Alan Ameche"
    ],
    "correctIndex": 1,
    "notes": "Jason White, QB, Oklahoma"
  },
  {
    "id": 560,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1969?",
    "options": [
      "Steve Owens",
      "Tim Tebow",
      "Bryce Young",
      "Les Horvath"
    ],
    "correctIndex": 0,
    "notes": "Steve Owens, RB, Oklahoma"
  },
  {
    "id": 561,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1963?",
    "options": [
      "Johnny Manziel",
      "Ron Dayne",
      "Roger Staubach",
      "Cam Newton"
    ],
    "correctIndex": 2,
    "notes": "Roger Staubach, QB, Navy"
  },
  {
    "id": 562,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1957?",
    "options": [
      "Danny Wuerffel",
      "Jim Plunkett",
      "Fernando Mendoza",
      "John David Crow"
    ],
    "correctIndex": 3,
    "notes": "John David Crow, RB, Texas A&M"
  },
  {
    "id": 563,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1977?",
    "options": [
      "Earl Campbell",
      "Mark Ingram",
      "Kyler Murray",
      "Jayden Daniels"
    ],
    "correctIndex": 0,
    "notes": "Earl Campbell, RB, Texas"
  },
  {
    "id": 564,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1983?",
    "options": [
      "Charles White",
      "Mike Rozier",
      "Bryce Young",
      "Clinton Frank"
    ],
    "correctIndex": 1,
    "notes": "Mike Rozier, RB, Nebraska"
  },
  {
    "id": 565,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1965?",
    "options": [
      "Leon Hart",
      "Marcus Mariota",
      "Ron Dayne",
      "Mike Garrett"
    ],
    "correctIndex": 3,
    "notes": "Mike Garrett, RB, Southern California"
  },
  {
    "id": 566,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1935?",
    "options": [
      "Gary Beban",
      "Jay Berwanger",
      "Billy Vessels",
      "Vinny Testaverde"
    ],
    "correctIndex": 1,
    "notes": "Jay Berwanger, RB, Chicago"
  },
  {
    "id": 567,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1959?",
    "options": [
      "Tim Brown",
      "Paul Hornung",
      "Billy Cannon",
      "Charlie Ward"
    ],
    "correctIndex": 2,
    "notes": "Billy Cannon, RB, LSU"
  },
  {
    "id": 568,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1936?",
    "options": [
      "Larry Kelley",
      "Troy Smith",
      "Andre Ware",
      "Pat Sullivan"
    ],
    "correctIndex": 0,
    "notes": "Larry Kelley, TE, Yale"
  },
  {
    "id": 569,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1951?",
    "options": [
      "Doc Blanchard",
      "Howard Cassady",
      "Dick Kazmaier",
      "Mike Garrett"
    ],
    "correctIndex": 2,
    "notes": "Dick Kazmaier, RB, Princeton"
  },
  {
    "id": 570,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1967?",
    "options": [
      "DeVonta Smith",
      "Gary Beban",
      "John Huarte",
      "Larry Kelley"
    ],
    "correctIndex": 1,
    "notes": "Gary Beban, QB, UCLA"
  },
  {
    "id": 571,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1955?",
    "options": [
      "Howard Cassady",
      "Johnny Rodgers",
      "Jay Berwanger",
      "Steve Owens"
    ],
    "correctIndex": 0,
    "notes": "Howard Cassady, RB, Ohio State"
  },
  {
    "id": 572,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1946?",
    "options": [
      "Tony Dorsett",
      "Glenn Davis",
      "Sam Bradford",
      "Marcus Mariota"
    ],
    "correctIndex": 1,
    "notes": "Glenn Davis, RB, Army"
  },
  {
    "id": 573,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 2001?",
    "options": [
      "Eric Crouch",
      "Jayden Daniels",
      "Charlie Ward",
      "Tim Tebow"
    ],
    "correctIndex": 0,
    "notes": "Eric Crouch, QB, Nebraska"
  },
  {
    "id": 574,
    "category": "Heisman Trophy",
    "difficulty": "Easy",
    "question": "Who won the Heisman Trophy in 2024?",
    "options": [
      "Bo Jackson",
      "Doak Walker",
      "Travis Hunter",
      "Danny Wuerffel"
    ],
    "correctIndex": 2,
    "notes": "Travis Hunter, DB/WR, Colorado"
  },
  {
    "id": 575,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1981?",
    "options": [
      "Ernie Davis",
      "Gino Torretta",
      "Marcus Allen",
      "Angelo Bertelli"
    ],
    "correctIndex": 2,
    "notes": "Marcus Allen, RB, Southern California"
  },
  {
    "id": 576,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1986?",
    "options": [
      "Johnny Manziel",
      "Doak Walker",
      "Bruce Smith",
      "Vinny Testaverde"
    ],
    "correctIndex": 3,
    "notes": "Vinny Testaverde, QB, Miami (FL)"
  },
  {
    "id": 577,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1982?",
    "options": [
      "Matt Leinart",
      "John Lujack",
      "Marcus Allen",
      "Herschel Walker"
    ],
    "correctIndex": 3,
    "notes": "Herschel Walker, RB, Georgia"
  },
  {
    "id": 578,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1956?",
    "options": [
      "Paul Hornung",
      "Alan Ameche",
      "Marcus Mariota",
      "Doug Flutie"
    ],
    "correctIndex": 0,
    "notes": "Paul Hornung, QB, Notre Dame"
  },
  {
    "id": 579,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1980?",
    "options": [
      "George Rogers",
      "Vic Janowicz",
      "Danny Wuerffel",
      "Leon Hart"
    ],
    "correctIndex": 0,
    "notes": "George Rogers, RB, South Carolina"
  },
  {
    "id": 580,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1966?",
    "options": [
      "Archie Griffin",
      "Doc Blanchard",
      "Steve Spurrier",
      "Charles Woodson"
    ],
    "correctIndex": 2,
    "notes": "Steve Spurrier, QB, Florida"
  },
  {
    "id": 581,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1953?",
    "options": [
      "Travis Hunter",
      "John Lattner",
      "Charles Woodson",
      "Steve Owens"
    ],
    "correctIndex": 1,
    "notes": "John Lattner, RB, Notre Dame"
  },
  {
    "id": 582,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 2002?",
    "options": [
      "Marcus Allen",
      "Carson Palmer",
      "Jason White",
      "Ernie Davis"
    ],
    "correctIndex": 1,
    "notes": "Carson Palmer, QB, Southern California"
  },
  {
    "id": 583,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1952?",
    "options": [
      "Kyler Murray",
      "Jason White",
      "Archie Griffin",
      "Billy Vessels"
    ],
    "correctIndex": 3,
    "notes": "Billy Vessels, RB, Oklahoma"
  },
  {
    "id": 584,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1984?",
    "options": [
      "Paul Hornung",
      "Carson Palmer",
      "Doug Flutie",
      "Marcus Allen"
    ],
    "correctIndex": 2,
    "notes": "Doug Flutie, QB, Boston College"
  },
  {
    "id": 585,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 1992?",
    "options": [
      "Roger Staubach",
      "Marcus Mariota",
      "Gino Torretta",
      "Baker Mayfield"
    ],
    "correctIndex": 2,
    "notes": "Gino Torretta, QB, Miami (FL)"
  },
  {
    "id": 586,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1944?",
    "options": [
      "Ernie Davis",
      "Les Horvath",
      "Mike Garrett",
      "Carson Palmer"
    ],
    "correctIndex": 1,
    "notes": "Les Horvath, HB, Ohio State"
  },
  {
    "id": 587,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1943?",
    "options": [
      "Danny Wuerffel",
      "Davey O'Brien",
      "Angelo Bertelli",
      "Pat Sullivan"
    ],
    "correctIndex": 2,
    "notes": "Angelo Bertelli, QB, Notre Dame"
  },
  {
    "id": 588,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 1990?",
    "options": [
      "Charlie Ward",
      "Charles White",
      "Marcus Allen",
      "Ty Detmer"
    ],
    "correctIndex": 3,
    "notes": "Ty Detmer, QB, BYU"
  },
  {
    "id": 589,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1976?",
    "options": [
      "Joe Bellino",
      "John Huarte",
      "Tony Dorsett",
      "Danny Wuerffel"
    ],
    "correctIndex": 2,
    "notes": "Tony Dorsett, RB, Pittsburgh"
  },
  {
    "id": 590,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who won the Heisman Trophy in 1978?",
    "options": [
      "Billy Sims",
      "Derrick Henry",
      "Marcus Mariota",
      "Jay Berwanger"
    ],
    "correctIndex": 0,
    "notes": "Billy Sims, RB, Oklahoma"
  },
  {
    "id": 591,
    "category": "Heisman Trophy",
    "difficulty": "Easy",
    "question": "Who won the Heisman Trophy in 2022?",
    "options": [
      "Doc Blanchard",
      "Joe Burrow",
      "Baker Mayfield",
      "Caleb Williams"
    ],
    "correctIndex": 3,
    "notes": "Caleb Williams, QB, Southern California"
  },
  {
    "id": 592,
    "category": "Heisman Trophy",
    "difficulty": "Easy",
    "question": "Who won the Heisman Trophy in 2020?",
    "options": [
      "Ty Detmer",
      "Danny Wuerffel",
      "DeVonta Smith",
      "John David Crow"
    ],
    "correctIndex": 2,
    "notes": "DeVonta Smith, WR, Alabama"
  },
  {
    "id": 593,
    "category": "Heisman Trophy",
    "difficulty": "Medium",
    "question": "Who won the Heisman Trophy in 1996?",
    "options": [
      "Doc Blanchard",
      "Vinny Testaverde",
      "Danny Wuerffel",
      "Rashaan Salaam"
    ],
    "correctIndex": 2,
    "notes": "Danny Wuerffel, QB, Florida"
  },
  {
    "id": 594,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 1938?",
    "options": [
      "Darren McFadden",
      "Jim Swink",
      "Marshall Goldberg",
      "Hugh Green"
    ],
    "correctIndex": 2,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 595,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 1954?",
    "options": [
      "Charlie Justice",
      "Kurt Burris",
      "Larry Fitzgerald",
      "Jalen Hurts"
    ],
    "correctIndex": 1,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 596,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 2010?",
    "options": [
      "Marshall Goldberg",
      "Andrew Luck",
      "O.J. Simpson",
      "Jerry Stovall"
    ],
    "correctIndex": 1,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 597,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 1994?",
    "options": [
      "Andrew Luck",
      "Ricky Bell",
      "Ki-Jana Carter",
      "Leroy Keyes"
    ],
    "correctIndex": 2,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 598,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 2018?",
    "options": [
      "Hugh Green",
      "Tua Tagovailoa",
      "Heath Shuler",
      "Trevor Lawrence"
    ],
    "correctIndex": 1,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 599,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 1953?",
    "options": [
      "Jim Swink",
      "Larry Fitzgerald",
      "Adrian Peterson",
      "Paul Giel"
    ],
    "correctIndex": 3,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 600,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 2013?",
    "options": [
      "Monk Meyer",
      "Kurt Burris",
      "A.J. McCarron",
      "Manti Te'o"
    ],
    "correctIndex": 2,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 601,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 2011?",
    "options": [
      "Darren McFadden",
      "Kyle Rote",
      "Deshaun Watson",
      "Andrew Luck"
    ],
    "correctIndex": 3,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 602,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 1995?",
    "options": [
      "Darren McFadden",
      "Paul Governali",
      "Tommie Frazier",
      "Charlie Justice"
    ],
    "correctIndex": 2,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 603,
    "category": "Heisman Trophy",
    "difficulty": "Hard",
    "question": "Who finished as Heisman Trophy runner-up in 2019?",
    "options": [
      "John Kimbrough",
      "Jalen Hurts",
      "Bob Chappuis",
      "Joe Hamilton"
    ],
    "correctIndex": 1,
    "notes": "Runner-up to that year's winner"
  },
  {
    "id": 604,
    "category": "National Championships",
    "difficulty": "Easy",
    "question": "Which team won the national championship in 2025?",
    "options": [
      "Michigan State",
      "Indiana",
      "Texas",
      "USC"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Curt Cignetti"
  },
  {
    "id": 605,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1955?",
    "options": [
      "Oklahoma",
      "Minnesota",
      "Notre Dame",
      "Alabama"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Bud Wilkinson"
  },
  {
    "id": 606,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1953?",
    "options": [
      "Maryland",
      "TCU",
      "Colorado",
      "Notre Dame"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Jim Tatum"
  },
  {
    "id": 607,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1946?",
    "options": [
      "LSU",
      "Tennessee",
      "Notre Dame",
      "Florida"
    ],
    "correctIndex": 2,
    "notes": "Head coach: Frank Leahy"
  },
  {
    "id": 608,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1939?",
    "options": [
      "Penn State",
      "Texas A&M",
      "Georgia",
      "Syracuse"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Homer Norton"
  },
  {
    "id": 609,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1964?",
    "options": [
      "Army",
      "Alabama",
      "Florida State",
      "Nebraska"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Bear Bryant"
  },
  {
    "id": 610,
    "category": "National Championships",
    "difficulty": "Easy",
    "question": "Which team won the national championship in 2011?",
    "options": [
      "Alabama",
      "Ohio State",
      "Florida",
      "Auburn"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Nick Saban"
  },
  {
    "id": 611,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1968?",
    "options": [
      "Syracuse",
      "Ohio State",
      "Penn State",
      "Oklahoma"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Woody Hayes"
  },
  {
    "id": 612,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1962?",
    "options": [
      "Notre Dame",
      "Miami",
      "Syracuse",
      "USC"
    ],
    "correctIndex": 3,
    "notes": "Head coach: John McKay"
  },
  {
    "id": 613,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1966?",
    "options": [
      "Tennessee",
      "Clemson",
      "Notre Dame",
      "Syracuse"
    ],
    "correctIndex": 2,
    "notes": "Head coach: Ara Parseghian"
  },
  {
    "id": 614,
    "category": "National Championships",
    "difficulty": "Easy",
    "question": "Which team won the national championship in 2024?",
    "options": [
      "Texas",
      "Ohio State",
      "Notre Dame",
      "Florida"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Ryan Day"
  },
  {
    "id": 615,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1972?",
    "options": [
      "TCU",
      "Florida",
      "USC",
      "Penn State"
    ],
    "correctIndex": 2,
    "notes": "Head coach: John McKay"
  },
  {
    "id": 616,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1967?",
    "options": [
      "USC",
      "Penn State",
      "Michigan",
      "Syracuse"
    ],
    "correctIndex": 0,
    "notes": "Head coach: John McKay"
  },
  {
    "id": 617,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1969?",
    "options": [
      "Michigan State",
      "Texas",
      "Florida",
      "Georgia"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Darrell Royal"
  },
  {
    "id": 618,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1954?",
    "options": [
      "BYU",
      "Pittsburgh",
      "Syracuse",
      "Ohio State"
    ],
    "correctIndex": 3,
    "notes": "Head coach: Woody Hayes (Ohio State)"
  },
  {
    "id": 619,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1942?",
    "options": [
      "Ohio State",
      "Indiana",
      "Minnesota",
      "Notre Dame"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Paul Brown"
  },
  {
    "id": 620,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1974?",
    "options": [
      "Oklahoma",
      "Syracuse",
      "Colorado",
      "LSU"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Barry Switzer (Oklahoma)"
  },
  {
    "id": 621,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the national championship in 2000?",
    "options": [
      "Ohio State",
      "Oklahoma",
      "USC",
      "Florida State"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Bob Stoops"
  },
  {
    "id": 622,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1937?",
    "options": [
      "Pittsburgh",
      "Texas",
      "Michigan State",
      "Maryland"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Jock Sutherland"
  },
  {
    "id": 623,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1940?",
    "options": [
      "Florida State",
      "Penn State",
      "LSU",
      "Minnesota"
    ],
    "correctIndex": 3,
    "notes": "Head coach: Bernie Bierman"
  },
  {
    "id": 624,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the national championship in 2005?",
    "options": [
      "Penn State",
      "Nebraska",
      "Michigan",
      "Texas"
    ],
    "correctIndex": 3,
    "notes": "Head coach: Mack Brown"
  },
  {
    "id": 625,
    "category": "National Championships",
    "difficulty": "Easy",
    "question": "Which team won the national championship in 2010?",
    "options": [
      "Auburn",
      "Texas A&M",
      "Army",
      "Indiana"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Gene Chizik"
  },
  {
    "id": 626,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1960?",
    "options": [
      "Minnesota",
      "Nebraska",
      "Michigan",
      "Penn State"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Murray Warmath"
  },
  {
    "id": 627,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the national championship in 1989?",
    "options": [
      "Miami",
      "Notre Dame",
      "BYU",
      "Syracuse"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Dennis Erickson"
  },
  {
    "id": 628,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the national championship in 2009?",
    "options": [
      "Penn State",
      "Alabama",
      "Texas A&M",
      "Maryland"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Nick Saban"
  },
  {
    "id": 629,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1970?",
    "options": [
      "Alabama",
      "Texas",
      "Notre Dame",
      "Nebraska"
    ],
    "correctIndex": 3,
    "notes": "Head coach: Bob Devaney (Nebraska)"
  },
  {
    "id": 630,
    "category": "National Championships",
    "difficulty": "Easy",
    "question": "Which team won the national championship in 2023?",
    "options": [
      "Maryland",
      "Michigan",
      "Miami",
      "Florida"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Jim Harbaugh"
  },
  {
    "id": 631,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the national championship in 2002?",
    "options": [
      "Syracuse",
      "Oklahoma",
      "Florida State",
      "Ohio State"
    ],
    "correctIndex": 3,
    "notes": "Head coach: Jim Tressel"
  },
  {
    "id": 632,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the national championship in 1981?",
    "options": [
      "Alabama",
      "Penn State",
      "Ohio State",
      "Clemson"
    ],
    "correctIndex": 3,
    "notes": "Head coach: Danny Ford"
  },
  {
    "id": 633,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1949?",
    "options": [
      "Notre Dame",
      "Tennessee",
      "Syracuse",
      "Miami"
    ],
    "correctIndex": 0,
    "notes": "Head coach: Frank Leahy"
  },
  {
    "id": 634,
    "category": "National Championships",
    "difficulty": "Easy",
    "question": "Which team won the national championship in 2017?",
    "options": [
      "Texas",
      "Georgia",
      "Alabama",
      "Minnesota"
    ],
    "correctIndex": 2,
    "notes": "Head coach: Nick Saban"
  },
  {
    "id": 635,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1965?",
    "options": [
      "Clemson",
      "Miami",
      "Alabama",
      "Minnesota"
    ],
    "correctIndex": 2,
    "notes": "Head coach: Bear Bryant (Alabama)"
  },
  {
    "id": 636,
    "category": "National Championships",
    "difficulty": "Medium",
    "question": "Which team won the national championship in 2007?",
    "options": [
      "Pittsburgh",
      "LSU",
      "TCU",
      "Minnesota"
    ],
    "correctIndex": 1,
    "notes": "Head coach: Les Miles"
  },
  {
    "id": 637,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1947?",
    "options": [
      "Auburn",
      "Army",
      "Notre Dame",
      "Florida State"
    ],
    "correctIndex": 2,
    "notes": "Head coach: Frank Leahy"
  },
  {
    "id": 638,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1944?",
    "options": [
      "Clemson",
      "Penn State",
      "Army",
      "LSU"
    ],
    "correctIndex": 2,
    "notes": "Head coach: Red Blaik"
  },
  {
    "id": 639,
    "category": "National Championships",
    "difficulty": "Hard",
    "question": "Which team won the national championship in 1977?",
    "options": [
      "Florida State",
      "Ohio State",
      "Colorado",
      "Notre Dame"
    ],
    "correctIndex": 3,
    "notes": "Head coach: Dan Devine"
  },
  {
    "id": 640,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for passing touchdowns?",
    "options": [
      "Kellen Moore",
      "Colt Brennan",
      "Graham Harrell",
      "Case Keenum"
    ],
    "correctIndex": 3,
    "notes": "Case Keenum (Houston), 155"
  },
  {
    "id": 641,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for total offense?",
    "options": [
      "Case Keenum",
      "Bo Nix",
      "Timmy Chang",
      "Dillon Gabriel"
    ],
    "correctIndex": 0,
    "notes": "Case Keenum (Houston), 20,114"
  },
  {
    "id": 642,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for rushing yards?",
    "options": [
      "Ron Dayne",
      "Donnel Pumphrey",
      "Tony Dorsett",
      "Ricky Williams"
    ],
    "correctIndex": 1,
    "notes": "Donnel Pumphrey (San Diego State), 6,405"
  },
  {
    "id": 643,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for receiving yards?",
    "options": [
      "Justin Hardy",
      "Trevor Insley",
      "Corey Davis",
      "Ryan Broyles"
    ],
    "correctIndex": 2,
    "notes": "Corey Davis (Western Michigan), 5,285"
  },
  {
    "id": 644,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for receptions?",
    "options": [
      "Zay Jones",
      "Taylor Stubblefield",
      "Justin Hardy",
      "Trevor Insley"
    ],
    "correctIndex": 0,
    "notes": "Zay Jones (East Carolina), 399"
  },
  {
    "id": 645,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for total points?",
    "options": [
      "Jonah Dalmas (K)",
      "Kenneth Dixon (RB)",
      "Keenan Reynolds (QB)",
      "Will Reichard (K)"
    ],
    "correctIndex": 3,
    "notes": "Will Reichard (K) (Alabama), 547"
  },
  {
    "id": 646,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for career sacks?",
    "options": [
      "Ja'Von Rolland-Jones",
      "Will Anderson Jr.",
      "Akheem Mesidor",
      "Terrell Suggs"
    ],
    "correctIndex": 3,
    "notes": "Terrell Suggs (Arizona State), 44"
  },
  {
    "id": 647,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS career record for career interceptions (defensive)?",
    "options": [
      "Martin Bayless",
      "Tony Thurman",
      "Tracy Saul",
      "Al Brosky"
    ],
    "correctIndex": 3,
    "notes": "Al Brosky (Illinois), 29"
  },
  {
    "id": 648,
    "category": "Records & Stats",
    "difficulty": "Medium",
    "question": "Who holds the FBS single-season record for sacks?",
    "options": [
      "Hau'oli Kikaha",
      "Terrell Suggs",
      "Elvis Dumervil",
      "Nate Orchard"
    ],
    "correctIndex": 1,
    "notes": "Terrell Suggs (Arizona State), 24 in 2002"
  },
  {
    "id": 649,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which of these teams has the most all-time bowl game wins: Georgia, Tennessee, Iowa, Pittsburgh?",
    "options": [
      "Georgia",
      "Iowa",
      "Tennessee",
      "Pittsburgh"
    ],
    "correctIndex": 0,
    "notes": "Georgia \u2014 38 bowl wins all-time"
  },
  {
    "id": 650,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which of these teams has the most all-time bowl game wins: Texas A&M, NC State, Mississippi State, North Carolina?",
    "options": [
      "Texas A&M",
      "North Carolina",
      "Mississippi State",
      "NC State"
    ],
    "correctIndex": 0,
    "notes": "Texas A&M \u2014 20 bowl wins all-time"
  },
  {
    "id": 651,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which of these teams has the most all-time bowl game wins: Tennessee, Ole Miss, Utah, North Carolina?",
    "options": [
      "Utah",
      "Tennessee",
      "North Carolina",
      "Ole Miss"
    ],
    "correctIndex": 1,
    "notes": "Tennessee \u2014 31 bowl wins all-time"
  },
  {
    "id": 652,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which of these teams has the most all-time bowl game wins: LSU, UCLA, Syracuse, Arizona State?",
    "options": [
      "LSU",
      "UCLA",
      "Syracuse",
      "Arizona State"
    ],
    "correctIndex": 0,
    "notes": "LSU \u2014 31 bowl wins all-time"
  },
  {
    "id": 653,
    "category": "Records & Stats",
    "difficulty": "Hard",
    "question": "Which of these teams has the most all-time bowl game wins: Clemson, Wisconsin, Texas Tech, Utah?",
    "options": [
      "Wisconsin",
      "Texas Tech",
      "Utah",
      "Clemson"
    ],
    "correctIndex": 3,
    "notes": "Clemson \u2014 27 bowl wins all-time"
  }
];
