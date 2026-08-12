// Blitz mode data: Sporcle-style "name as many as you can before time runs
// out" list challenges. Each entry has canonical answers plus accepted
// aliases (nicknames, abbreviations, common misspellings-that-are-fine).
// Matching in app.js is case/punctuation-insensitive and checks the typed
// text against `answer` and every string in `aliases`.

window.BLITZ_LISTS = [
  {
    id: "all_32_teams",
    title: "Name All 32 NFL Teams",
    prompt: "Type any team by city or nickname.",
    answers: [
      { answer: "Arizona Cardinals", aliases: ["Cardinals", "Cards"] },
      { answer: "Atlanta Falcons", aliases: ["Falcons"] },
      { answer: "Baltimore Ravens", aliases: ["Ravens"] },
      { answer: "Buffalo Bills", aliases: ["Bills"] },
      { answer: "Carolina Panthers", aliases: ["Panthers"] },
      { answer: "Chicago Bears", aliases: ["Bears"] },
      { answer: "Cincinnati Bengals", aliases: ["Bengals"] },
      { answer: "Cleveland Browns", aliases: ["Browns"] },
      { answer: "Dallas Cowboys", aliases: ["Cowboys"] },
      { answer: "Denver Broncos", aliases: ["Broncos"] },
      { answer: "Detroit Lions", aliases: ["Lions"] },
      { answer: "Green Bay Packers", aliases: ["Packers", "Pack"] },
      { answer: "Houston Texans", aliases: ["Texans"] },
      { answer: "Indianapolis Colts", aliases: ["Colts"] },
      { answer: "Jacksonville Jaguars", aliases: ["Jaguars", "Jags"] },
      { answer: "Kansas City Chiefs", aliases: ["Chiefs"] },
      { answer: "Las Vegas Raiders", aliases: ["Raiders"] },
      { answer: "Los Angeles Chargers", aliases: ["Chargers"] },
      { answer: "Los Angeles Rams", aliases: ["Rams"] },
      { answer: "Miami Dolphins", aliases: ["Dolphins", "Fins"] },
      { answer: "Minnesota Vikings", aliases: ["Vikings", "Vikes"] },
      { answer: "New England Patriots", aliases: ["Patriots", "Pats"] },
      { answer: "New Orleans Saints", aliases: ["Saints"] },
      { answer: "New York Giants", aliases: ["Giants"] },
      { answer: "New York Jets", aliases: ["Jets"] },
      { answer: "Philadelphia Eagles", aliases: ["Eagles"] },
      { answer: "Pittsburgh Steelers", aliases: ["Steelers"] },
      { answer: "San Francisco 49ers", aliases: ["49ers", "Niners"] },
      { answer: "Seattle Seahawks", aliases: ["Seahawks", "Hawks"] },
      { answer: "Tampa Bay Buccaneers", aliases: ["Buccaneers", "Bucs"] },
      { answer: "Tennessee Titans", aliases: ["Titans"] },
      { answer: "Washington Commanders", aliases: ["Commanders"] }
    ]
  },
  {
    id: "sb_winning_qbs",
    title: "Super Bowl-Winning Starting QBs",
    prompt: "Name a quarterback who started and won a Super Bowl.",
    answers: [
      { answer: "Tom Brady" }, { answer: "Peyton Manning" }, { answer: "Eli Manning" },
      { answer: "Aaron Rodgers" }, { answer: "Drew Brees" }, { answer: "Russell Wilson" },
      { answer: "Patrick Mahomes" }, { answer: "Matthew Stafford" }, { answer: "Joe Montana" },
      { answer: "Terry Bradshaw" }, { answer: "John Elway" }, { answer: "Troy Aikman" },
      { answer: "Ben Roethlisberger" }, { answer: "Kurt Warner" }, { answer: "Steve Young" },
      { answer: "Brett Favre" }, { answer: "Bart Starr" }, { answer: "Jim Plunkett" },
      { answer: "Joe Namath" }, { answer: "Roger Staubach" }, { answer: "Phil Simms" },
      { answer: "Jeff Hostetler" }, { answer: "Mark Rypien" }, { answer: "Doug Williams" },
      { answer: "Brad Johnson" }, { answer: "Trent Dilfer" }, { answer: "Nick Foles" },
      { answer: "Jalen Hurts" }, { answer: "Joe Flacco" }, { answer: "Sam Darnold" }
    ]
  },
  {
    id: "no1_picks_2000s",
    title: "#1 Overall Draft Picks Since 2000",
    prompt: "Name a player taken #1 overall in the NFL Draft, 2000-present.",
    answers: [
      { answer: "Courtney Brown" }, { answer: "Michael Vick" }, { answer: "David Carr" },
      { answer: "Carson Palmer" }, { answer: "Eli Manning" }, { answer: "Alex Smith" },
      { answer: "Mario Williams" }, { answer: "JaMarcus Russell" }, { answer: "Matthew Stafford" },
      { answer: "Sam Bradford" }, { answer: "Cam Newton" }, { answer: "Andrew Luck" },
      { answer: "Eric Fisher" }, { answer: "Jadeveon Clowney" }, { answer: "Jameis Winston" },
      { answer: "Jared Goff" }, { answer: "Myles Garrett" }, { answer: "Baker Mayfield" },
      { answer: "Kyler Murray" }, { answer: "Joe Burrow" }, { answer: "Trevor Lawrence" },
      { answer: "Travon Walker" }, { answer: "Bryce Young" }, { answer: "Caleb Williams" },
      { answer: "Jake Long" }, { answer: "Cam Ward" }
    ]
  },
  {
    id: "mvps_2000s",
    title: "NFL MVPs Since 2000",
    prompt: "Name a player who won NFL Most Valuable Player, 2000-present.",
    answers: [
      { answer: "Marshall Faulk" }, { answer: "Kurt Warner" }, { answer: "Rich Gannon" },
      { answer: "Peyton Manning" }, { answer: "Shaun Alexander" }, { answer: "LaDainian Tomlinson" },
      { answer: "Tom Brady" }, { answer: "Adrian Peterson" }, { answer: "Aaron Rodgers" },
      { answer: "Cam Newton" }, { answer: "Matt Ryan" }, { answer: "Patrick Mahomes" },
      { answer: "Lamar Jackson" }, { answer: "Josh Allen" }, { answer: "Steve McNair" }
    ]
  },
  {
    id: "hof_qbs",
    title: "Pro Football Hall of Fame Quarterbacks",
    prompt: "Name a quarterback enshrined in the Pro Football Hall of Fame.",
    answers: [
      { answer: "Joe Montana" }, { answer: "John Elway" }, { answer: "Dan Marino" },
      { answer: "Troy Aikman" }, { answer: "Brett Favre" }, { answer: "Steve Young" },
      { answer: "Warren Moon" }, { answer: "Fran Tarkenton" }, { answer: "Terry Bradshaw" },
      { answer: "Bart Starr" }, { answer: "Johnny Unitas" }, { answer: "Otto Graham" },
      { answer: "Sammy Baugh" }, { answer: "Bob Griese" }, { answer: "Roger Staubach" },
      { answer: "Len Dawson" }, { answer: "Dan Fouts" }, { answer: "Jim Kelly" },
      { answer: "Kurt Warner" }, { answer: "Peyton Manning" }, { answer: "Drew Brees" },
      { answer: "Y.A. Tittle" }, { answer: "Norm Van Brocklin" }, { answer: "George Blanda" }
    ]
  },
  {
    id: "teams_never_won_sb",
    title: "Teams That Have Never Won a Super Bowl",
    prompt: "Name a current NFL franchise with zero Super Bowl titles.",
    answers: [
      { answer: "Arizona Cardinals", aliases: ["Cardinals"] },
      { answer: "Atlanta Falcons", aliases: ["Falcons"] },
      { answer: "Buffalo Bills", aliases: ["Bills"] },
      { answer: "Carolina Panthers", aliases: ["Panthers"] },
      { answer: "Cincinnati Bengals", aliases: ["Bengals"] },
      { answer: "Cleveland Browns", aliases: ["Browns"] },
      { answer: "Detroit Lions", aliases: ["Lions"] },
      { answer: "Houston Texans", aliases: ["Texans"] },
      { answer: "Jacksonville Jaguars", aliases: ["Jaguars", "Jags"] },
      { answer: "Los Angeles Chargers", aliases: ["Chargers"] },
      { answer: "Minnesota Vikings", aliases: ["Vikings"] },
      { answer: "Tennessee Titans", aliases: ["Titans"] }
    ]
  },
  {
    id: "hof_rbs",
    title: "Pro Football Hall of Fame Running Backs",
    prompt: "Name a running back enshrined in the Pro Football Hall of Fame.",
    answers: [
      { answer: "Jim Brown" }, { answer: "Walter Payton" }, { answer: "Barry Sanders" },
      { answer: "Emmitt Smith" }, { answer: "Eric Dickerson" }, { answer: "Tony Dorsett" },
      { answer: "Marshall Faulk" }, { answer: "Curtis Martin" }, { answer: "LaDainian Tomlinson" },
      { answer: "Marcus Allen" }, { answer: "Franco Harris" }, { answer: "O.J. Simpson" },
      { answer: "Earl Campbell" }, { answer: "Gale Sayers" }, { answer: "John Riggins" },
      { answer: "Thurman Thomas" }, { answer: "Jerome Bettis" }, { answer: "Terrell Davis" },
      { answer: "Floyd Little" }, { answer: "Leroy Kelly" }, { answer: "Bobby Mitchell" },
      { answer: "Edgerrin James" }, { answer: "Roger Craig" }
    ]
  },
  {
    id: "sb_5plus_titles",
    title: "Franchises With 5+ Super Bowl Titles",
    prompt: "This one's short — name a team with 5 or more Super Bowl championships.",
    answers: [
      { answer: "Pittsburgh Steelers", aliases: ["Steelers"] },
      { answer: "New England Patriots", aliases: ["Patriots"] },
      { answer: "San Francisco 49ers", aliases: ["49ers", "Niners"] },
      { answer: "Dallas Cowboys", aliases: ["Cowboys"] }
    ]
  },
  {
    id: "roty_offense",
    title: "Offensive Rookie of the Year Winners",
    prompt: "Name a player who won NFL Offensive Rookie of the Year.",
    answers: [
      { answer: "Barry Sanders" }, { answer: "Eric Dickerson" }, { answer: "Curtis Martin" },
      { answer: "Randy Moss" }, { answer: "Tony Dorsett" },
      { answer: "Vince Young" }, { answer: "Cam Newton" }, { answer: "Robert Griffin III", aliases: ["RG3"] },
      { answer: "Odell Beckham Jr.", aliases: ["OBJ"] },
      { answer: "Saquon Barkley" }, { answer: "Justin Jefferson" }, { answer: "Ja'Marr Chase" },
      { answer: "C.J. Stroud" }, { answer: "Jayden Daniels" },
      { answer: "Todd Gurley" }, { answer: "Dak Prescott" }, { answer: "Kyler Murray" }
    ]
  },
  {
    id: "colleges_top_qbs",
    title: "Colleges of Recent Franchise QBs",
    prompt: "Name the college of any current or recent star NFL quarterback.",
    answers: [
      { answer: "Alabama", aliases: [] }, { answer: "Ohio State" }, { answer: "Oklahoma" },
      { answer: "Texas Tech" }, { answer: "Wyoming" }, { answer: "Louisville" },
      { answer: "LSU" }, { answer: "Wisconsin" }, { answer: "Oregon" },
      { answer: "Iowa State" }, { answer: "North Dakota State" }, { answer: "Michigan" },
      { answer: "Purdue" }, { answer: "California" }, { answer: "Stanford" },
      { answer: "Georgia" }, { answer: "Clemson" }, { answer: "Notre Dame" }
    ]
  },
  {
    id: "retired_numbers_generic",
    title: "Franchises With a Retired #12",
    prompt: "Name a team that has retired jersey #12 for a legendary player.",
    answers: [
      { answer: "Pittsburgh Steelers", aliases: ["Steelers"] },
      { answer: "Miami Dolphins", aliases: ["Dolphins"] },
      { answer: "New York Jets", aliases: ["Jets"] },
      { answer: "Buffalo Bills", aliases: ["Bills"] }
    ]
  },
  {
    id: "coaches_multiple_sb",
    title: "Head Coaches Who've Won Multiple Super Bowls",
    prompt: "Name a head coach who has won 2 or more Super Bowls.",
    answers: [
      { answer: "Bill Belichick" }, { answer: "Chuck Noll" }, { answer: "Bill Walsh" },
      { answer: "Joe Gibbs" }, { answer: "Jimmy Johnson" }, { answer: "Tom Landry" },
      { answer: "Don Shula" }, { answer: "Vince Lombardi" }, { answer: "Andy Reid" },
      { answer: "Mike Shanahan" }, { answer: "Bill Parcells" }
    ]
  },
  {
    id: "3000yd_rushers_single_season",
    title: "Players With a 2,000+ Yard Rushing Season",
    prompt: "Name a running back who rushed for 2,000+ yards in a single season.",
    answers: [
      { answer: "Eric Dickerson" }, { answer: "Barry Sanders" }, { answer: "Terrell Davis" },
      { answer: "Jamal Lewis" }, { answer: "Adrian Peterson" }, { answer: "Chris Johnson" },
      { answer: "O.J. Simpson" }, { answer: "Derrick Henry" }
    ]
  },
  {
    id: "400td_passers",
    title: "Quarterbacks With 400+ Career Passing TDs",
    prompt: "Name a QB who threw 400 or more career passing touchdowns.",
    answers: [
      { answer: "Tom Brady" }, { answer: "Drew Brees" }, { answer: "Peyton Manning" },
      { answer: "Brett Favre" }, { answer: "Aaron Rodgers" }, { answer: "Philip Rivers" },
      { answer: "Dan Marino" }, { answer: "Ben Roethlisberger" }
    ]
  },
  {
    id: "franchises_multiple_cities",
    title: "Franchises That Have Played in More Than One City",
    prompt: "Name an NFL team that has relocated to a different city at some point in its history.",
    answers: [
      { answer: "Las Vegas Raiders", aliases: ["Raiders"] },
      { answer: "Los Angeles Rams", aliases: ["Rams"] },
      { answer: "Los Angeles Chargers", aliases: ["Chargers"] },
      { answer: "Tennessee Titans", aliases: ["Titans", "Oilers"] },
      { answer: "Indianapolis Colts", aliases: ["Colts"] },
      { answer: "Arizona Cardinals", aliases: ["Cardinals"] },
      { answer: "Washington Commanders", aliases: ["Commanders", "Redskins"] },
      { answer: "Baltimore Ravens", aliases: ["Ravens"] }
    ]
  }
];
