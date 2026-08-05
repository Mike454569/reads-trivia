// 17-0 mode data: a curated pool of notable team-seasons (1999-2025), each with
// that team's real skill-position roster depth (~8 players) and approximate
// PPR fantasy points-per-game (FPPG). This is NOT scraped from Pro-Football-
// Reference — the user's source file (NFL_Roster_Links_1999_to_2026.xlsx) is
// 893 links to PFR pages, which isn't something that can be fetched at that
// scale here. Instead this is authored from known real stat lines/season
// narratives and should be read as "approximate but in the right
// neighborhood," not exact box-score accurate. ~160 team-seasons, roughly 5
// per franchise, spread across the era.
//
// Shape: { team, year, players: [{ name, position, fppg }] }
// position is one of QB/RB/WR/TE. fppg is an approximate standard-PPR fantasy
// points-per-game for that player's season (season total / ~16 games), per
// the 17-0 template's "Base score = Real PPR FPPG" rule.

window.LEGENDS_TEAMS = [
  // ---- AFC EAST ----
  { team: "Buffalo Bills", year: 2020, players: [
    { name: "Josh Allen", position: "QB", fppg: 24.8 },
    { name: "Stefon Diggs", position: "WR", fppg: 20.6 },
    { name: "Devin Singletary", position: "RB", fppg: 10.9 },
    { name: "Zack Moss", position: "RB", fppg: 7.5 },
    { name: "Cole Beasley", position: "WR", fppg: 13.1 },
    { name: "John Brown", position: "WR", fppg: 9.5 },
    { name: "Dawson Knox", position: "TE", fppg: 5.8 },
    { name: "Gabriel Davis", position: "WR", fppg: 6.0 }
  ]},
  { team: "Buffalo Bills", year: 2021, players: [
    { name: "Josh Allen", position: "QB", fppg: 23.3 },
    { name: "Stefon Diggs", position: "WR", fppg: 19.7 },
    { name: "Devin Singletary", position: "RB", fppg: 10.3 },
    { name: "Zack Moss", position: "RB", fppg: 8.0 },
    { name: "Emmanuel Sanders", position: "WR", fppg: 11.3 },
    { name: "Gabriel Davis", position: "WR", fppg: 9.4 },
    { name: "Cole Beasley", position: "WR", fppg: 8.6 },
    { name: "Dawson Knox", position: "TE", fppg: 7.9 }
  ]},
  { team: "Buffalo Bills", year: 2022, players: [
    { name: "Josh Allen", position: "QB", fppg: 24.3 },
    { name: "Stefon Diggs", position: "WR", fppg: 21.3 },
    { name: "James Cook", position: "RB", fppg: 10.6 },
    { name: "Devin Singletary", position: "RB", fppg: 8.7 },
    { name: "Gabriel Davis", position: "WR", fppg: 10.9 },
    { name: "Isaiah McKenzie", position: "WR", fppg: 8.0 },
    { name: "Dawson Knox", position: "TE", fppg: 7.2 },
    { name: "Nyheim Hines", position: "RB", fppg: 5.0 }
  ]},
  { team: "Buffalo Bills", year: 1999, players: [
    { name: "Doug Flutie", position: "QB", fppg: 15.0 },
    { name: "Antowain Smith", position: "RB", fppg: 13.1 },
    { name: "Eric Moulds", position: "WR", fppg: 14.4 },
    { name: "Andre Reed", position: "WR", fppg: 9.5 },
    { name: "Peerless Price", position: "WR", fppg: 7.8 },
    { name: "Jay Riemersma", position: "TE", fppg: 5.5 },
    { name: "Sam Gash", position: "RB", fppg: 3.1 },
    { name: "Rob Johnson", position: "QB", fppg: 6.9 }
  ]},
  { team: "Buffalo Bills", year: 2004, players: [
    { name: "Drew Bledsoe", position: "QB", fppg: 15.3 },
    { name: "Willis McGahee", position: "RB", fppg: 14.4 },
    { name: "Eric Moulds", position: "WR", fppg: 14.1 },
    { name: "Lee Evans", position: "WR", fppg: 10.6 },
    { name: "Travis Henry", position: "RB", fppg: 6.5 },
    { name: "Mark Campbell", position: "TE", fppg: 4.5 },
    { name: "Josh Reed", position: "WR", fppg: 5.6 },
    { name: "Bobby Shaw", position: "WR", fppg: 3.8 }
  ]},

  { team: "Miami Dolphins", year: 2023, players: [
    { name: "Tua Tagovailoa", position: "QB", fppg: 20.6 },
    { name: "Tyreek Hill", position: "WR", fppg: 23.4 },
    { name: "Jaylen Waddle", position: "WR", fppg: 17.5 },
    { name: "Raheem Mostert", position: "RB", fppg: 13.8 },
    { name: "De'Von Achane", position: "RB", fppg: 15.2 },
    { name: "Braxton Berrios", position: "WR", fppg: 6.9 },
    { name: "Durham Smythe", position: "TE", fppg: 4.6 },
    { name: "Salvon Ahmed", position: "RB", fppg: 3.4 }
  ]},
  { team: "Miami Dolphins", year: 2020, players: [
    { name: "Ryan Fitzpatrick", position: "QB", fppg: 14.4 },
    { name: "DeVante Parker", position: "WR", fppg: 13.8 },
    { name: "Myles Gaskin", position: "RB", fppg: 12.2 },
    { name: "Mike Gesicki", position: "TE", fppg: 9.4 },
    { name: "Jakeem Grant", position: "WR", fppg: 6.5 },
    { name: "Preston Williams", position: "WR", fppg: 6.1 },
    { name: "Matt Breida", position: "RB", fppg: 4.4 },
    { name: "Tua Tagovailoa", position: "QB", fppg: 12.1 }
  ]},
  { team: "Miami Dolphins", year: 2001, players: [
    { name: "Jay Fiedler", position: "QB", fppg: 13.1 },
    { name: "Lamar Smith", position: "RB", fppg: 14.7 },
    { name: "Chris Chambers", position: "WR", fppg: 12.5 },
    { name: "Oronde Gadsden", position: "WR", fppg: 10.6 },
    { name: "Rob Konrad", position: "RB", fppg: 5.9 },
    { name: "James McKnight", position: "WR", fppg: 5.6 },
    { name: "Dedric Ward", position: "WR", fppg: 4.4 }
  ]},
  { team: "Miami Dolphins", year: 2016, players: [
    { name: "Ryan Tannehill", position: "QB", fppg: 15.9 },
    { name: "Jay Ajayi", position: "RB", fppg: 16.6 },
    { name: "Jarvis Landry", position: "WR", fppg: 16.9 },
    { name: "DeVante Parker", position: "WR", fppg: 9.4 },
    { name: "Kenny Stills", position: "WR", fppg: 9.5 },
    { name: "Damien Williams", position: "RB", fppg: 6.0 },
    { name: "Dion Sims", position: "TE", fppg: 3.8 },
    { name: "Matt Moore", position: "QB", fppg: 6.3 }
  ]},
  { team: "Miami Dolphins", year: 1999, players: [
    { name: "Dan Marino", position: "QB", fppg: 15.6 },
    { name: "Lamar Smith", position: "RB", fppg: 11.9 },
    { name: "O.J. McDuffie", position: "WR", fppg: 13.4 },
    { name: "Oronde Gadsden", position: "WR", fppg: 9.0 },
    { name: "Tony Martin", position: "WR", fppg: 8.1 },
    { name: "J.J. Johnson", position: "RB", fppg: 5.0 },
    { name: "Troy Drayton", position: "TE", fppg: 3.8 }
  ]},

  { team: "New England Patriots", year: 2007, players: [
    { name: "Tom Brady", position: "QB", fppg: 25.0 },
    { name: "Randy Moss", position: "WR", fppg: 21.0 },
    { name: "Wes Welker", position: "WR", fppg: 19.1 },
    { name: "Laurence Maroney", position: "RB", fppg: 9.7 },
    { name: "Donte' Stallworth", position: "WR", fppg: 8.9 },
    { name: "Kevin Faulk", position: "RB", fppg: 8.0 },
    { name: "Ben Watson", position: "TE", fppg: 6.8 },
    { name: "Jabar Gaffney", position: "WR", fppg: 6.4 }
  ]},
  { team: "New England Patriots", year: 2011, players: [
    { name: "Tom Brady", position: "QB", fppg: 23.4 },
    { name: "Rob Gronkowski", position: "TE", fppg: 17.5 },
    { name: "Wes Welker", position: "WR", fppg: 18.8 },
    { name: "BenJarvus Green-Ellis", position: "RB", fppg: 10.6 },
    { name: "Aaron Hernandez", position: "TE", fppg: 12.4 },
    { name: "Deion Branch", position: "WR", fppg: 7.5 },
    { name: "Danny Woodhead", position: "RB", fppg: 7.9 },
    { name: "Chad Ochocinco", position: "WR", fppg: 3.8 }
  ]},
  { team: "New England Patriots", year: 2010, players: [
    { name: "Tom Brady", position: "QB", fppg: 22.5 },
    { name: "Wes Welker", position: "WR", fppg: 16.3 },
    { name: "Rob Gronkowski", position: "TE", fppg: 11.3 },
    { name: "BenJarvus Green-Ellis", position: "RB", fppg: 10.9 },
    { name: "Danny Woodhead", position: "RB", fppg: 7.5 },
    { name: "Deion Branch", position: "WR", fppg: 8.9 },
    { name: "Aaron Hernandez", position: "TE", fppg: 8.1 },
    { name: "Brandon Tate", position: "WR", fppg: 3.8 }
  ]},
  { team: "New England Patriots", year: 2004, players: [
    { name: "Tom Brady", position: "QB", fppg: 18.1 },
    { name: "Corey Dillon", position: "RB", fppg: 17.5 },
    { name: "David Givens", position: "WR", fppg: 10.6 },
    { name: "Deion Branch", position: "WR", fppg: 9.4 },
    { name: "Daniel Graham", position: "TE", fppg: 6.4 },
    { name: "Kevin Faulk", position: "RB", fppg: 6.9 },
    { name: "David Patten", position: "WR", fppg: 5.6 },
    { name: "Troy Brown", position: "WR", fppg: 6.9 }
  ]},
  { team: "New England Patriots", year: 2016, players: [
    { name: "Tom Brady", position: "QB", fppg: 22.9 },
    { name: "Julian Edelman", position: "WR", fppg: 14.7 },
    { name: "LeGarrette Blount", position: "RB", fppg: 13.1 },
    { name: "James White", position: "RB", fppg: 9.7 },
    { name: "Chris Hogan", position: "WR", fppg: 9.4 },
    { name: "Martellus Bennett", position: "TE", fppg: 8.7 },
    { name: "Malcolm Mitchell", position: "WR", fppg: 6.3 },
    { name: "Dion Lewis", position: "RB", fppg: 5.6 }
  ]},

  { team: "New York Jets", year: 2015, players: [
    { name: "Ryan Fitzpatrick", position: "QB", fppg: 18.1 },
    { name: "Brandon Marshall", position: "WR", fppg: 18.8 },
    { name: "Eric Decker", position: "WR", fppg: 14.4 },
    { name: "Chris Ivory", position: "RB", fppg: 13.4 },
    { name: "Bilal Powell", position: "RB", fppg: 7.5 },
    { name: "Jace Amaro", position: "TE", fppg: 4.5 },
    { name: "Quincy Enunwa", position: "WR", fppg: 4.4 }
  ]},
  { team: "New York Jets", year: 2002, players: [
    { name: "Chad Pennington", position: "QB", fppg: 16.3 },
    { name: "Curtis Martin", position: "RB", fppg: 16.3 },
    { name: "Santana Moss", position: "WR", fppg: 12.2 },
    { name: "Wayne Chrebet", position: "WR", fppg: 9.4 },
    { name: "Curtis Conway", position: "WR", fppg: 7.5 },
    { name: "Richie Anderson", position: "RB", fppg: 6.3 },
    { name: "Anthony Becht", position: "TE", fppg: 4.4 }
  ]},
  { team: "New York Jets", year: 2010, players: [
    { name: "Mark Sanchez", position: "QB", fppg: 13.1 },
    { name: "LaDainian Tomlinson", position: "RB", fppg: 13.8 },
    { name: "Santonio Holmes", position: "WR", fppg: 10.9 },
    { name: "Shonn Greene", position: "RB", fppg: 9.4 },
    { name: "Braylon Edwards", position: "WR", fppg: 8.7 },
    { name: "Dustin Keller", position: "TE", fppg: 8.0 },
    { name: "Jerricho Cotchery", position: "WR", fppg: 5.0 }
  ]},
  { team: "New York Jets", year: 2009, players: [
    { name: "Mark Sanchez", position: "QB", fppg: 10.9 },
    { name: "Thomas Jones", position: "RB", fppg: 15.3 },
    { name: "Jerricho Cotchery", position: "WR", fppg: 10.0 },
    { name: "Dustin Keller", position: "TE", fppg: 8.4 },
    { name: "Leon Washington", position: "RB", fppg: 6.9 },
    { name: "Braylon Edwards", position: "WR", fppg: 7.5 },
    { name: "David Clowney", position: "WR", fppg: 3.8 }
  ]},
  { team: "New York Jets", year: 1999, players: [
    { name: "Vinny Testaverde", position: "QB", fppg: 3.8 },
    { name: "Curtis Martin", position: "RB", fppg: 15.6 },
    { name: "Keyshawn Johnson", position: "WR", fppg: 13.8 },
    { name: "Wayne Chrebet", position: "WR", fppg: 10.9 },
    { name: "Rick Mirer", position: "QB", fppg: 8.0 },
    { name: "Dedric Ward", position: "WR", fppg: 6.3 },
    { name: "Kyle Brady", position: "TE", fppg: 4.4 }
  ]},

  // ---- AFC NORTH ----
  { team: "Baltimore Ravens", year: 2019, players: [
    { name: "Lamar Jackson", position: "QB", fppg: 25.9 },
    { name: "Mark Andrews", position: "TE", fppg: 13.8 },
    { name: "Marquise Brown", position: "WR", fppg: 10.9 },
    { name: "Mark Ingram II", position: "RB", fppg: 14.4 },
    { name: "Gus Edwards", position: "RB", fppg: 8.1 },
    { name: "Willie Snead IV", position: "WR", fppg: 7.5 },
    { name: "Nick Boyle", position: "TE", fppg: 4.4 }
  ]},
  { team: "Baltimore Ravens", year: 2023, players: [
    { name: "Lamar Jackson", position: "QB", fppg: 24.4 },
    { name: "Mark Andrews", position: "TE", fppg: 10.6 },
    { name: "Zay Flowers", position: "WR", fppg: 12.5 },
    { name: "Gus Edwards", position: "RB", fppg: 10.9 },
    { name: "Odell Beckham Jr.", position: "WR", fppg: 9.4 },
    { name: "Justice Hill", position: "RB", fppg: 6.9 },
    { name: "Nelson Agholor", position: "WR", fppg: 4.4 }
  ]},
  { team: "Baltimore Ravens", year: 2020, players: [
    { name: "Lamar Jackson", position: "QB", fppg: 21.6 },
    { name: "Mark Andrews", position: "TE", fppg: 13.1 },
    { name: "J.K. Dobbins", position: "RB", fppg: 11.9 },
    { name: "Gus Edwards", position: "RB", fppg: 8.1 },
    { name: "Marquise Brown", position: "WR", fppg: 9.4 },
    { name: "Willie Snead IV", position: "WR", fppg: 6.3 },
    { name: "Mark Ingram II", position: "RB", fppg: 8.7 }
  ]},
  { team: "Baltimore Ravens", year: 2014, players: [
    { name: "Joe Flacco", position: "QB", fppg: 16.3 },
    { name: "Steve Smith Sr.", position: "WR", fppg: 13.8 },
    { name: "Justin Forsett", position: "RB", fppg: 14.1 },
    { name: "Torrey Smith", position: "WR", fppg: 9.4 },
    { name: "Owen Daniels", position: "TE", fppg: 6.9 },
    { name: "Marlon Brown", position: "WR", fppg: 5.0 },
    { name: "Bernard Pierce", position: "RB", fppg: 4.4 }
  ]},
  { team: "Baltimore Ravens", year: 2003, players: [
    { name: "Jamal Lewis", position: "RB", fppg: 21.3 },
    { name: "Kyle Boller", position: "QB", fppg: 8.1 },
    { name: "Todd Heap", position: "TE", fppg: 10.9 },
    { name: "Marcus Robinson", position: "WR", fppg: 8.7 },
    { name: "Chester Taylor", position: "RB", fppg: 4.5 },
    { name: "Travis Taylor", position: "WR", fppg: 6.3 }
  ]},

  { team: "Cincinnati Bengals", year: 2021, players: [
    { name: "Joe Burrow", position: "QB", fppg: 20.0 },
    { name: "Ja'Marr Chase", position: "WR", fppg: 20.9 },
    { name: "Tee Higgins", position: "WR", fppg: 14.7 },
    { name: "Joe Mixon", position: "RB", fppg: 16.3 },
    { name: "C.J. Uzomah", position: "TE", fppg: 6.9 },
    { name: "Tyler Boyd", position: "WR", fppg: 10.6 },
    { name: "Samaje Perine", position: "RB", fppg: 4.4 }
  ]},
  { team: "Cincinnati Bengals", year: 2022, players: [
    { name: "Joe Burrow", position: "QB", fppg: 22.2 },
    { name: "Ja'Marr Chase", position: "WR", fppg: 18.1 },
    { name: "Tee Higgins", position: "WR", fppg: 15.6 },
    { name: "Joe Mixon", position: "RB", fppg: 15.3 },
    { name: "Tyler Boyd", position: "WR", fppg: 8.7 },
    { name: "Hayden Hurst", position: "TE", fppg: 6.9 },
    { name: "Samaje Perine", position: "RB", fppg: 5.6 }
  ]},
  { team: "Cincinnati Bengals", year: 2005, players: [
    { name: "Carson Palmer", position: "QB", fppg: 18.8 },
    { name: "Chad Johnson", position: "WR", fppg: 18.8 },
    { name: "Rudi Johnson", position: "RB", fppg: 15.3 },
    { name: "T.J. Houshmandzadeh", position: "WR", fppg: 11.9 },
    { name: "Kelley Washington", position: "WR", fppg: 5.0 },
    { name: "Chris Perry", position: "RB", fppg: 4.4 },
    { name: "Tony Stewart", position: "TE", fppg: 3.1 }
  ]},
  { team: "Cincinnati Bengals", year: 2013, players: [
    { name: "Andy Dalton", position: "QB", fppg: 16.9 },
    { name: "A.J. Green", position: "WR", fppg: 17.8 },
    { name: "Giovani Bernard", position: "RB", fppg: 13.1 },
    { name: "BenJarvus Green-Ellis", position: "RB", fppg: 8.7 },
    { name: "Marvin Jones Jr.", position: "WR", fppg: 8.1 },
    { name: "Tyler Eifert", position: "TE", fppg: 7.5 },
    { name: "Mohamed Sanu", position: "WR", fppg: 5.0 }
  ]},
  { team: "Cincinnati Bengals", year: 2015, players: [
    { name: "Andy Dalton", position: "QB", fppg: 16.3 },
    { name: "A.J. Green", position: "WR", fppg: 16.3 },
    { name: "Jeremy Hill", position: "RB", fppg: 11.9 },
    { name: "Giovani Bernard", position: "RB", fppg: 9.4 },
    { name: "Tyler Eifert", position: "TE", fppg: 11.3 },
    { name: "Marvin Jones Jr.", position: "WR", fppg: 8.7 },
    { name: "Mohamed Sanu", position: "WR", fppg: 6.3 }
  ]},

  { team: "Cleveland Browns", year: 2007, players: [
    { name: "Derek Anderson", position: "QB", fppg: 17.2 },
    { name: "Braylon Edwards", position: "WR", fppg: 16.3 },
    { name: "Kellen Winslow II", position: "TE", fppg: 15.0 },
    { name: "Jamal Lewis", position: "RB", fppg: 13.8 },
    { name: "Joe Jurevicius", position: "WR", fppg: 6.9 },
    { name: "Jason Wright", position: "RB", fppg: 3.8 }
  ]},
  { team: "Cleveland Browns", year: 2020, players: [
    { name: "Baker Mayfield", position: "QB", fppg: 16.3 },
    { name: "Nick Chubb", position: "RB", fppg: 15.3 },
    { name: "Jarvis Landry", position: "WR", fppg: 12.8 },
    { name: "Odell Beckham Jr.", position: "WR", fppg: 13.0 },
    { name: "Kareem Hunt", position: "RB", fppg: 12.5 },
    { name: "Austin Hooper", position: "TE", fppg: 6.9 },
    { name: "Rashard Higgins", position: "WR", fppg: 5.6 }
  ]},
  { team: "Cleveland Browns", year: 2002, players: [
    { name: "Tim Couch", position: "QB", fppg: 14.7 },
    { name: "William Green", position: "RB", fppg: 10.9 },
    { name: "Kevin Johnson", position: "WR", fppg: 10.9 },
    { name: "Quincy Morgan", position: "WR", fppg: 8.7 },
    { name: "James Jackson", position: "RB", fppg: 5.0 },
    { name: "Andre King", position: "WR", fppg: 3.1 }
  ]},
  { team: "Cleveland Browns", year: 2019, players: [
    { name: "Baker Mayfield", position: "QB", fppg: 15.6 },
    { name: "Odell Beckham Jr.", position: "WR", fppg: 13.8 },
    { name: "Nick Chubb", position: "RB", fppg: 16.6 },
    { name: "Jarvis Landry", position: "WR", fppg: 14.4 },
    { name: "David Njoku", position: "TE", fppg: 5.6 },
    { name: "Kareem Hunt", position: "RB", fppg: 8.1 },
    { name: "Rashard Higgins", position: "WR", fppg: 4.4 }
  ]},
  { team: "Cleveland Browns", year: 1999, players: [
    { name: "Tim Couch", position: "QB", fppg: 11.9 },
    { name: "Kevin Johnson", position: "WR", fppg: 12.2 },
    { name: "Terry Kirby", position: "RB", fppg: 9.4 },
    { name: "Leslie Shepherd", position: "WR", fppg: 6.3 },
    { name: "Marc Edwards", position: "RB", fppg: 4.4 },
    { name: "Darrin Chiaverini", position: "WR", fppg: 4.4 }
  ]},

  { team: "Pittsburgh Steelers", year: 2014, players: [
    { name: "Ben Roethlisberger", position: "QB", fppg: 21.3 },
    { name: "Antonio Brown", position: "WR", fppg: 24.1 },
    { name: "Le'Veon Bell", position: "RB", fppg: 20.9 },
    { name: "Markus Wheaton", position: "WR", fppg: 8.1 },
    { name: "Heath Miller", position: "TE", fppg: 7.5 },
    { name: "LeGarrette Blount", position: "RB", fppg: 4.4 },
    { name: "Lance Moore", position: "WR", fppg: 3.8 }
  ]},
  { team: "Pittsburgh Steelers", year: 2016, players: [
    { name: "Ben Roethlisberger", position: "QB", fppg: 17.8 },
    { name: "Antonio Brown", position: "WR", fppg: 22.5 },
    { name: "Le'Veon Bell", position: "RB", fppg: 17.5 },
    { name: "Eli Rogers", position: "WR", fppg: 6.9 },
    { name: "Jesse James", position: "TE", fppg: 5.0 },
    { name: "DeAngelo Williams", position: "RB", fppg: 6.9 },
    { name: "Sammie Coates", position: "WR", fppg: 3.8 }
  ]},
  { team: "Pittsburgh Steelers", year: 2018, players: [
    { name: "Ben Roethlisberger", position: "QB", fppg: 21.6 },
    { name: "Antonio Brown", position: "WR", fppg: 18.8 },
    { name: "JuJu Smith-Schuster", position: "WR", fppg: 17.8 },
    { name: "James Conner", position: "RB", fppg: 17.2 },
    { name: "Vance McDonald", position: "TE", fppg: 8.1 },
    { name: "Jaylen Samuels", position: "RB", fppg: 6.9 },
    { name: "Ryan Switzer", position: "WR", fppg: 3.8 }
  ]},
  { team: "Pittsburgh Steelers", year: 2005, players: [
    { name: "Ben Roethlisberger", position: "QB", fppg: 13.1 },
    { name: "Jerome Bettis", position: "RB", fppg: 10.0 },
    { name: "Hines Ward", position: "WR", fppg: 14.7 },
    { name: "Willie Parker", position: "RB", fppg: 11.3 },
    { name: "Heath Miller", position: "TE", fppg: 7.5 },
    { name: "Antwaan Randle El", position: "WR", fppg: 7.5 },
    { name: "Cedrick Wilson", position: "WR", fppg: 4.4 }
  ]},
  { team: "Pittsburgh Steelers", year: 2001, players: [
    { name: "Kordell Stewart", position: "QB", fppg: 13.1 },
    { name: "Jerome Bettis", position: "RB", fppg: 13.1 },
    { name: "Hines Ward", position: "WR", fppg: 13.8 },
    { name: "Plaxico Burress", position: "WR", fppg: 9.4 },
    { name: "Amos Zereoue", position: "RB", fppg: 5.6 },
    { name: "Bobby Shaw", position: "WR", fppg: 4.4 }
  ]},

  // ---- AFC SOUTH ----
  { team: "Houston Texans", year: 2012, players: [
    { name: "Matt Schaub", position: "QB", fppg: 15.6 },
    { name: "Arian Foster", position: "RB", fppg: 20.0 },
    { name: "Andre Johnson", position: "WR", fppg: 16.6 },
    { name: "Owen Daniels", position: "TE", fppg: 8.7 },
    { name: "Ben Tate", position: "RB", fppg: 6.9 },
    { name: "Kevin Walter", position: "WR", fppg: 5.6 },
    { name: "DeVier Posey", position: "WR", fppg: 2.5 }
  ]},
  { team: "Houston Texans", year: 2015, players: [
    { name: "Brian Hoyer", position: "QB", fppg: 11.9 },
    { name: "DeAndre Hopkins", position: "WR", fppg: 20.6 },
    { name: "Arian Foster", position: "RB", fppg: 7.5 },
    { name: "Alfred Blue", position: "RB", fppg: 7.5 },
    { name: "Cecil Shorts III", position: "WR", fppg: 5.0 },
    { name: "Nate Washington", position: "WR", fppg: 5.6 },
    { name: "Ryan Griffin", position: "TE", fppg: 3.1 }
  ]},
  { team: "Houston Texans", year: 2018, players: [
    { name: "Deshaun Watson", position: "QB", fppg: 20.0 },
    { name: "DeAndre Hopkins", position: "WR", fppg: 20.0 },
    { name: "Lamar Miller", position: "RB", fppg: 11.3 },
    { name: "Will Fuller V", position: "WR", fppg: 10.6 },
    { name: "Ryan Griffin", position: "TE", fppg: 4.4 },
    { name: "Alfred Blue", position: "RB", fppg: 4.4 },
    { name: "Bruce Ellington", position: "WR", fppg: 3.8 }
  ]},
  { team: "Houston Texans", year: 2019, players: [
    { name: "Deshaun Watson", position: "QB", fppg: 20.9 },
    { name: "DeAndre Hopkins", position: "WR", fppg: 18.8 },
    { name: "Carlos Hyde", position: "RB", fppg: 11.9 },
    { name: "Will Fuller V", position: "WR", fppg: 12.5 },
    { name: "Duke Johnson", position: "RB", fppg: 8.1 },
    { name: "Darren Fells", position: "TE", fppg: 6.3 },
    { name: "Kenny Stills", position: "WR", fppg: 5.0 }
  ]},
  { team: "Houston Texans", year: 2023, players: [
    { name: "C.J. Stroud", position: "QB", fppg: 21.0 },
    { name: "Nico Collins", position: "WR", fppg: 16.6 },
    { name: "Devin Singletary", position: "RB", fppg: 11.3 },
    { name: "Tank Dell", position: "WR", fppg: 11.9 },
    { name: "Dalton Schultz", position: "TE", fppg: 9.4 },
    { name: "Robert Woods", position: "WR", fppg: 7.5 },
    { name: "Dameon Pierce", position: "RB", fppg: 5.6 }
  ]},

  { team: "Indianapolis Colts", year: 2004, players: [
    { name: "Peyton Manning", position: "QB", fppg: 26.0 },
    { name: "Marvin Harrison", position: "WR", fppg: 18.8 },
    { name: "Reggie Wayne", position: "WR", fppg: 15.6 },
    { name: "Edgerrin James", position: "RB", fppg: 16.3 },
    { name: "Dallas Clark", position: "TE", fppg: 6.9 },
    { name: "Brandon Stokley", position: "WR", fppg: 9.4 },
    { name: "James Mungro", position: "RB", fppg: 3.1 }
  ]},
  { team: "Indianapolis Colts", year: 1999, players: [
    { name: "Peyton Manning", position: "QB", fppg: 20.0 },
    { name: "Edgerrin James", position: "RB", fppg: 22.2 },
    { name: "Marvin Harrison", position: "WR", fppg: 19.4 },
    { name: "Marcus Pollard", position: "TE", fppg: 8.1 },
    { name: "Terrence Wilkins", position: "WR", fppg: 4.4 },
    { name: "E.G. Green", position: "WR", fppg: 3.8 }
  ]},
  { team: "Indianapolis Colts", year: 2006, players: [
    { name: "Peyton Manning", position: "QB", fppg: 21.3 },
    { name: "Marvin Harrison", position: "WR", fppg: 15.3 },
    { name: "Reggie Wayne", position: "WR", fppg: 16.3 },
    { name: "Joseph Addai", position: "RB", fppg: 13.8 },
    { name: "Dallas Clark", position: "TE", fppg: 8.7 },
    { name: "Dominic Rhodes", position: "RB", fppg: 5.6 },
    { name: "Aaron Moorehead", position: "WR", fppg: 2.5 }
  ]},
  { team: "Indianapolis Colts", year: 2014, players: [
    { name: "Andrew Luck", position: "QB", fppg: 23.4 },
    { name: "T.Y. Hilton", position: "WR", fppg: 16.3 },
    { name: "Reggie Wayne", position: "WR", fppg: 9.4 },
    { name: "Dwayne Allen", position: "TE", fppg: 6.3 },
    { name: "Ahmad Bradshaw", position: "RB", fppg: 8.7 },
    { name: "Coby Fleener", position: "TE", fppg: 7.5 },
    { name: "Hakeem Nicks", position: "WR", fppg: 4.4 }
  ]},
  { team: "Indianapolis Colts", year: 2012, players: [
    { name: "Andrew Luck", position: "QB", fppg: 20.6 },
    { name: "Reggie Wayne", position: "WR", fppg: 15.6 },
    { name: "Donald Brown", position: "RB", fppg: 8.7 },
    { name: "T.Y. Hilton", position: "WR", fppg: 9.4 },
    { name: "Vick Ballard", position: "RB", fppg: 6.9 },
    { name: "Coby Fleener", position: "TE", fppg: 6.3 },
    { name: "LaVon Brazill", position: "WR", fppg: 2.5 }
  ]},

  { team: "Jacksonville Jaguars", year: 1999, players: [
    { name: "Mark Brunell", position: "QB", fppg: 18.1 },
    { name: "Fred Taylor", position: "RB", fppg: 16.3 },
    { name: "Jimmy Smith", position: "WR", fppg: 17.5 },
    { name: "Keenan McCardell", position: "WR", fppg: 11.3 },
    { name: "Kyle Brady", position: "TE", fppg: 5.0 },
    { name: "James Stewart", position: "RB", fppg: 6.3 },
    { name: "Reggie Barlow", position: "WR", fppg: 3.1 }
  ]},
  { team: "Jacksonville Jaguars", year: 2017, players: [
    { name: "Blake Bortles", position: "QB", fppg: 13.8 },
    { name: "Leonard Fournette", position: "RB", fppg: 14.7 },
    { name: "Marqise Lee", position: "WR", fppg: 10.9 },
    { name: "Allen Robinson", position: "WR", fppg: 3.0 },
    { name: "Allen Hurns", position: "WR", fppg: 8.1 },
    { name: "Keelan Cole", position: "WR", fppg: 7.5 },
    { name: "Corey Grant", position: "RB", fppg: 3.1 }
  ]},
  { team: "Jacksonville Jaguars", year: 2022, players: [
    { name: "Trevor Lawrence", position: "QB", fppg: 19.1 },
    { name: "Christian Kirk", position: "WR", fppg: 15.0 },
    { name: "Travis Etienne Jr.", position: "RB", fppg: 14.7 },
    { name: "Evan Engram", position: "TE", fppg: 12.5 },
    { name: "Zay Jones", position: "WR", fppg: 9.4 },
    { name: "Marvin Jones Jr.", position: "WR", fppg: 8.1 },
    { name: "James Robinson", position: "RB", fppg: 4.4 }
  ]},
  { team: "Jacksonville Jaguars", year: 2015, players: [
    { name: "Blake Bortles", position: "QB", fppg: 18.8 },
    { name: "Allen Robinson", position: "WR", fppg: 17.5 },
    { name: "T.J. Yeldon", position: "RB", fppg: 11.9 },
    { name: "Allen Hurns", position: "WR", fppg: 12.5 },
    { name: "Julius Thomas", position: "TE", fppg: 6.9 },
    { name: "Denard Robinson", position: "RB", fppg: 5.0 },
    { name: "Marqise Lee", position: "WR", fppg: 4.4 }
  ]},
  { team: "Jacksonville Jaguars", year: 2020, players: [
    { name: "Gardner Minshew", position: "QB", fppg: 13.1 },
    { name: "D.J. Chark Jr.", position: "WR", fppg: 10.9 },
    { name: "James Robinson", position: "RB", fppg: 15.0 },
    { name: "Chris Conley", position: "WR", fppg: 7.5 },
    { name: "Tyler Eifert", position: "TE", fppg: 5.6 },
    { name: "Keelan Cole", position: "WR", fppg: 5.0 },
    { name: "Laviska Shenault Jr.", position: "WR", fppg: 6.9 }
  ]},

  { team: "Tennessee Titans", year: 1999, players: [
    { name: "Steve McNair", position: "QB", fppg: 14.4 },
    { name: "Eddie George", position: "RB", fppg: 17.5 },
    { name: "Frank Wycheck", position: "TE", fppg: 9.4 },
    { name: "Yancey Thigpen", position: "WR", fppg: 10.6 },
    { name: "Chris Sanders", position: "WR", fppg: 7.5 },
    { name: "Kevin Dyson", position: "WR", fppg: 5.6 }
  ]},
  { team: "Tennessee Titans", year: 2009, players: [
    { name: "Chris Johnson", position: "RB", fppg: 25.0 },
    { name: "Kerry Collins", position: "QB", fppg: 13.8 },
    { name: "Kenny Britt", position: "WR", fppg: 8.1 },
    { name: "Nate Washington", position: "WR", fppg: 7.5 },
    { name: "Bo Scaife", position: "TE", fppg: 6.3 },
    { name: "Justin Gage", position: "WR", fppg: 5.0 },
    { name: "LenDale White", position: "RB", fppg: 4.4 }
  ]},
  { team: "Tennessee Titans", year: 2020, players: [
    { name: "Derrick Henry", position: "RB", fppg: 20.6 },
    { name: "Ryan Tannehill", position: "QB", fppg: 18.1 },
    { name: "A.J. Brown", position: "WR", fppg: 16.3 },
    { name: "Corey Davis", position: "WR", fppg: 9.4 },
    { name: "Jonnu Smith", position: "TE", fppg: 6.9 },
    { name: "Adam Humphries", position: "WR", fppg: 5.0 }
  ]},
  { team: "Tennessee Titans", year: 2003, players: [
    { name: "Steve McNair", position: "QB", fppg: 17.5 },
    { name: "Eddie George", position: "RB", fppg: 13.1 },
    { name: "Derrick Mason", position: "WR", fppg: 14.7 },
    { name: "Frank Wycheck", position: "TE", fppg: 6.9 },
    { name: "Justin McCareins", position: "WR", fppg: 7.5 },
    { name: "Chris Brown", position: "RB", fppg: 4.4 }
  ]},
  { team: "Tennessee Titans", year: 2008, players: [
    { name: "Chris Johnson", position: "RB", fppg: 17.5 },
    { name: "Kerry Collins", position: "QB", fppg: 13.1 },
    { name: "Justin Gage", position: "WR", fppg: 9.1 },
    { name: "LenDale White", position: "RB", fppg: 8.7 },
    { name: "Bo Scaife", position: "TE", fppg: 7.5 },
    { name: "Brandon Jones", position: "WR", fppg: 4.4 }
  ]},

  // ---- AFC WEST ----
  { team: "Denver Broncos", year: 2013, players: [
    { name: "Peyton Manning", position: "QB", fppg: 27.8 },
    { name: "Demaryius Thomas", position: "WR", fppg: 19.1 },
    { name: "Julius Thomas", position: "TE", fppg: 13.8 },
    { name: "Eric Decker", position: "WR", fppg: 16.3 },
    { name: "Wes Welker", position: "WR", fppg: 13.1 },
    { name: "Knowshon Moreno", position: "RB", fppg: 13.1 },
    { name: "Montee Ball", position: "RB", fppg: 5.6 }
  ]},
  { team: "Denver Broncos", year: 2012, players: [
    { name: "Peyton Manning", position: "QB", fppg: 23.1 },
    { name: "Demaryius Thomas", position: "WR", fppg: 16.6 },
    { name: "Eric Decker", position: "WR", fppg: 13.8 },
    { name: "Knowshon Moreno", position: "RB", fppg: 9.4 },
    { name: "Jacob Tamme", position: "TE", fppg: 5.6 },
    { name: "Lance Ball", position: "RB", fppg: 3.8 },
    { name: "Brandon Stokley", position: "WR", fppg: 5.6 }
  ]},
  { team: "Denver Broncos", year: 2014, players: [
    { name: "Peyton Manning", position: "QB", fppg: 24.4 },
    { name: "Demaryius Thomas", position: "WR", fppg: 18.1 },
    { name: "Emmanuel Sanders", position: "WR", fppg: 16.3 },
    { name: "Julius Thomas", position: "TE", fppg: 12.5 },
    { name: "Ronnie Hillman", position: "RB", fppg: 6.9 },
    { name: "C.J. Anderson", position: "RB", fppg: 8.1 },
    { name: "Wes Welker", position: "WR", fppg: 6.9 }
  ]},
  { team: "Denver Broncos", year: 2003, players: [
    { name: "Jake Plummer", position: "QB", fppg: 13.8 },
    { name: "Clinton Portis", position: "RB", fppg: 16.9 },
    { name: "Rod Smith", position: "WR", fppg: 13.8 },
    { name: "Ashley Lelie", position: "WR", fppg: 7.5 },
    { name: "Shannon Sharpe", position: "TE", fppg: 6.9 },
    { name: "Rod Smith", position: "RB", fppg: 3.8 }
  ]},
  { team: "Denver Broncos", year: 2000, players: [
    { name: "Brian Griese", position: "QB", fppg: 15.0 },
    { name: "Mike Anderson", position: "RB", fppg: 16.3 },
    { name: "Rod Smith", position: "WR", fppg: 15.3 },
    { name: "Ed McCaffrey", position: "WR", fppg: 11.3 },
    { name: "Shannon Sharpe", position: "TE", fppg: 6.9 },
    { name: "Olandis Gary", position: "RB", fppg: 3.8 }
  ]},

  { team: "Kansas City Chiefs", year: 2018, players: [
    { name: "Patrick Mahomes", position: "QB", fppg: 26.1 },
    { name: "Tyreek Hill", position: "WR", fppg: 19.7 },
    { name: "Travis Kelce", position: "TE", fppg: 16.3 },
    { name: "Kareem Hunt", position: "RB", fppg: 17.2 },
    { name: "Sammy Watkins", position: "WR", fppg: 8.7 },
    { name: "Damien Williams", position: "RB", fppg: 6.9 },
    { name: "Chris Conley", position: "WR", fppg: 4.4 }
  ]},
  { team: "Kansas City Chiefs", year: 2020, players: [
    { name: "Patrick Mahomes", position: "QB", fppg: 23.4 },
    { name: "Travis Kelce", position: "TE", fppg: 18.1 },
    { name: "Tyreek Hill", position: "WR", fppg: 17.2 },
    { name: "Clyde Edwards-Helaire", position: "RB", fppg: 11.3 },
    { name: "Mecole Hardman", position: "WR", fppg: 6.9 },
    { name: "Sammy Watkins", position: "WR", fppg: 6.3 },
    { name: "Le'Veon Bell", position: "RB", fppg: 3.8 }
  ]},
  { team: "Kansas City Chiefs", year: 2022, players: [
    { name: "Patrick Mahomes", position: "QB", fppg: 26.3 },
    { name: "Travis Kelce", position: "TE", fppg: 18.4 },
    { name: "JuJu Smith-Schuster", position: "WR", fppg: 12.2 },
    { name: "Isiah Pacheco", position: "RB", fppg: 8.7 },
    { name: "Marquez Valdes-Scantling", position: "WR", fppg: 6.9 },
    { name: "Mecole Hardman", position: "WR", fppg: 5.6 },
    { name: "Jerick McKinnon", position: "RB", fppg: 5.0 }
  ]},
  { team: "Kansas City Chiefs", year: 2003, players: [
    { name: "Priest Holmes", position: "RB", fppg: 24.1 },
    { name: "Trent Green", position: "QB", fppg: 17.5 },
    { name: "Tony Gonzalez", position: "TE", fppg: 13.8 },
    { name: "Eddie Kennison", position: "WR", fppg: 9.4 },
    { name: "Derrick Blaylock", position: "RB", fppg: 5.0 },
    { name: "Johnnie Morton", position: "WR", fppg: 6.3 }
  ]},
  { team: "Kansas City Chiefs", year: 2019, players: [
    { name: "Patrick Mahomes", position: "QB", fppg: 20.0 },
    { name: "Travis Kelce", position: "TE", fppg: 15.6 },
    { name: "Tyreek Hill", position: "WR", fppg: 14.7 },
    { name: "Damien Williams", position: "RB", fppg: 10.6 },
    { name: "Sammy Watkins", position: "WR", fppg: 8.1 },
    { name: "LeSean McCoy", position: "RB", fppg: 4.4 }
  ]},

  { team: "Las Vegas Raiders", year: 2002, players: [
    { name: "Rich Gannon", position: "QB", fppg: 21.3 },
    { name: "Jerry Rice", position: "WR", fppg: 13.8 },
    { name: "Tim Brown", position: "WR", fppg: 13.1 },
    { name: "Charlie Garner", position: "RB", fppg: 15.0 },
    { name: "Doug Jolley", position: "TE", fppg: 5.6 },
    { name: "Jerry Porter", position: "WR", fppg: 6.9 },
    { name: "Zack Crockett", position: "RB", fppg: 4.4 }
  ]},
  { team: "Las Vegas Raiders", year: 2000, players: [
    { name: "Rich Gannon", position: "QB", fppg: 18.8 },
    { name: "Tim Brown", position: "WR", fppg: 15.6 },
    { name: "Charlie Garner", position: "RB", fppg: 16.3 },
    { name: "Jerry Rice", position: "WR", fppg: 12.5 },
    { name: "Rickey Dudley", position: "TE", fppg: 5.6 },
    { name: "Napoleon Kaufman", position: "RB", fppg: 5.0 }
  ]},
  { team: "Las Vegas Raiders", year: 2016, players: [
    { name: "Derek Carr", position: "QB", fppg: 18.1 },
    { name: "Amari Cooper", position: "WR", fppg: 15.0 },
    { name: "Michael Crabtree", position: "WR", fppg: 14.4 },
    { name: "Latavius Murray", position: "RB", fppg: 11.9 },
    { name: "Clive Walford", position: "TE", fppg: 5.0 },
    { name: "Jalen Richard", position: "RB", fppg: 5.6 },
    { name: "Seth Roberts", position: "WR", fppg: 5.6 }
  ]},
  { team: "Las Vegas Raiders", year: 2021, players: [
    { name: "Derek Carr", position: "QB", fppg: 18.8 },
    { name: "Darren Waller", position: "TE", fppg: 14.7 },
    { name: "Hunter Renfrow", position: "WR", fppg: 13.8 },
    { name: "Josh Jacobs", position: "RB", fppg: 13.1 },
    { name: "Bryan Edwards", position: "WR", fppg: 6.3 },
    { name: "Kenyan Drake", position: "RB", fppg: 5.6 }
  ]},
  { team: "Las Vegas Raiders", year: 2010, players: [
    { name: "Jason Campbell", position: "QB", fppg: 13.1 },
    { name: "Darren McFadden", position: "RB", fppg: 16.3 },
    { name: "Louis Murphy", position: "WR", fppg: 8.7 },
    { name: "Zach Miller", position: "TE", fppg: 8.1 },
    { name: "Michael Bush", position: "RB", fppg: 6.3 },
    { name: "Jacoby Ford", position: "WR", fppg: 5.6 }
  ]},

  { team: "Los Angeles Chargers", year: 2006, players: [
    { name: "LaDainian Tomlinson", position: "RB", fppg: 28.5 },
    { name: "Philip Rivers", position: "QB", fppg: 17.5 },
    { name: "Antonio Gates", position: "TE", fppg: 13.8 },
    { name: "Keenan McCardell", position: "WR", fppg: 7.5 },
    { name: "Eric Parker", position: "WR", fppg: 7.5 },
    { name: "Michael Turner", position: "RB", fppg: 6.9 },
    { name: "Vincent Jackson", position: "WR", fppg: 5.6 }
  ]},
  { team: "Los Angeles Chargers", year: 2009, players: [
    { name: "Philip Rivers", position: "QB", fppg: 21.3 },
    { name: "Vincent Jackson", position: "WR", fppg: 15.6 },
    { name: "Antonio Gates", position: "TE", fppg: 13.8 },
    { name: "LaDainian Tomlinson", position: "RB", fppg: 10.6 },
    { name: "Malcom Floyd", position: "WR", fppg: 8.7 },
    { name: "Darren Sproles", position: "RB", fppg: 8.1 }
  ]},
  { team: "Los Angeles Chargers", year: 2018, players: [
    { name: "Philip Rivers", position: "QB", fppg: 19.4 },
    { name: "Keenan Allen", position: "WR", fppg: 18.1 },
    { name: "Melvin Gordon", position: "RB", fppg: 16.3 },
    { name: "Mike Williams", position: "WR", fppg: 9.4 },
    { name: "Austin Ekeler", position: "RB", fppg: 9.4 },
    { name: "Hunter Henry", position: "TE", fppg: 8.1 },
    { name: "Tyrell Williams", position: "WR", fppg: 6.3 }
  ]},
  { team: "Los Angeles Chargers", year: 2021, players: [
    { name: "Justin Herbert", position: "QB", fppg: 23.4 },
    { name: "Austin Ekeler", position: "RB", fppg: 23.8 },
    { name: "Keenan Allen", position: "WR", fppg: 16.3 },
    { name: "Mike Williams", position: "WR", fppg: 14.4 },
    { name: "Jared Cook", position: "TE", fppg: 6.3 },
    { name: "Josh Palmer", position: "WR", fppg: 4.4 }
  ]},
  { team: "Los Angeles Chargers", year: 2004, players: [
    { name: "Drew Brees", position: "QB", fppg: 16.9 },
    { name: "LaDainian Tomlinson", position: "RB", fppg: 21.3 },
    { name: "Antonio Gates", position: "TE", fppg: 11.9 },
    { name: "Eric Parker", position: "WR", fppg: 8.1 },
    { name: "Keenan McCardell", position: "WR", fppg: 8.7 },
    { name: "Reche Caldwell", position: "WR", fppg: 4.4 }
  ]},

  // ---- NFC EAST ----
  { team: "Dallas Cowboys", year: 2007, players: [
    { name: "Tony Romo", position: "QB", fppg: 20.0 },
    { name: "Terrell Owens", position: "WR", fppg: 18.8 },
    { name: "Jason Witten", position: "TE", fppg: 13.8 },
    { name: "Marion Barber III", position: "RB", fppg: 13.8 },
    { name: "Patrick Crayton", position: "WR", fppg: 7.5 },
    { name: "Julius Jones", position: "RB", fppg: 6.3 },
    { name: "Terry Glenn", position: "WR", fppg: 4.4 }
  ]},
  { team: "Dallas Cowboys", year: 2014, players: [
    { name: "Tony Romo", position: "QB", fppg: 18.8 },
    { name: "DeMarco Murray", position: "RB", fppg: 22.2 },
    { name: "Dez Bryant", position: "WR", fppg: 16.3 },
    { name: "Jason Witten", position: "TE", fppg: 10.6 },
    { name: "Terrance Williams", position: "WR", fppg: 8.1 },
    { name: "Cole Beasley", position: "WR", fppg: 5.6 }
  ]},
  { team: "Dallas Cowboys", year: 2016, players: [
    { name: "Dak Prescott", position: "QB", fppg: 19.4 },
    { name: "Ezekiel Elliott", position: "RB", fppg: 20.0 },
    { name: "Dez Bryant", position: "WR", fppg: 11.3 },
    { name: "Jason Witten", position: "TE", fppg: 9.4 },
    { name: "Cole Beasley", position: "WR", fppg: 9.4 },
    { name: "Terrance Williams", position: "WR", fppg: 8.7 },
    { name: "Alfred Morris", position: "RB", fppg: 3.8 }
  ]},
  { team: "Dallas Cowboys", year: 2021, players: [
    { name: "Dak Prescott", position: "QB", fppg: 20.6 },
    { name: "CeeDee Lamb", position: "WR", fppg: 16.3 },
    { name: "Ezekiel Elliott", position: "RB", fppg: 14.7 },
    { name: "Amari Cooper", position: "WR", fppg: 13.8 },
    { name: "Tony Pollard", position: "RB", fppg: 8.7 },
    { name: "Dalton Schultz", position: "TE", fppg: 10.9 },
    { name: "Michael Gallup", position: "WR", fppg: 6.9 }
  ]},
  { team: "Dallas Cowboys", year: 2018, players: [
    { name: "Dak Prescott", position: "QB", fppg: 16.9 },
    { name: "Ezekiel Elliott", position: "RB", fppg: 20.0 },
    { name: "Amari Cooper", position: "WR", fppg: 13.8 },
    { name: "Cole Beasley", position: "WR", fppg: 9.4 },
    { name: "Blake Jarwin", position: "TE", fppg: 4.4 },
    { name: "Michael Gallup", position: "WR", fppg: 6.3 }
  ]},

  { team: "New York Giants", year: 2011, players: [
    { name: "Eli Manning", position: "QB", fppg: 20.9 },
    { name: "Victor Cruz", position: "WR", fppg: 16.3 },
    { name: "Hakeem Nicks", position: "WR", fppg: 14.4 },
    { name: "Ahmad Bradshaw", position: "RB", fppg: 12.5 },
    { name: "Jake Ballard", position: "TE", fppg: 6.3 },
    { name: "Mario Manningham", position: "WR", fppg: 6.9 }
  ]},
  { team: "New York Giants", year: 2016, players: [
    { name: "Eli Manning", position: "QB", fppg: 18.1 },
    { name: "Odell Beckham Jr.", position: "WR", fppg: 19.7 },
    { name: "Rashad Jennings", position: "RB", fppg: 10.6 },
    { name: "Sterling Shepard", position: "WR", fppg: 9.4 },
    { name: "Will Tye", position: "TE", fppg: 5.0 },
    { name: "Bobby Rainey", position: "RB", fppg: 3.1 }
  ]},
  { team: "New York Giants", year: 2002, players: [
    { name: "Kerry Collins", position: "QB", fppg: 16.3 },
    { name: "Tiki Barber", position: "RB", fppg: 18.8 },
    { name: "Amani Toomer", position: "WR", fppg: 12.5 },
    { name: "Jeremy Shockey", position: "TE", fppg: 8.7 },
    { name: "Ike Hilliard", position: "WR", fppg: 7.5 },
    { name: "Tim Carter", position: "WR", fppg: 3.8 }
  ]},
  { team: "New York Giants", year: 2022, players: [
    { name: "Daniel Jones", position: "QB", fppg: 17.2 },
    { name: "Saquon Barkley", position: "RB", fppg: 18.8 },
    { name: "Darius Slayton", position: "WR", fppg: 8.1 },
    { name: "Richie James", position: "WR", fppg: 7.5 },
    { name: "Daniel Bellinger", position: "TE", fppg: 5.0 },
    { name: "Isaiah Hodgins", position: "WR", fppg: 5.6 }
  ]},
  { team: "New York Giants", year: 2000, players: [
    { name: "Kerry Collins", position: "QB", fppg: 16.3 },
    { name: "Tiki Barber", position: "RB", fppg: 13.8 },
    { name: "Ike Hilliard", position: "WR", fppg: 10.6 },
    { name: "Amani Toomer", position: "WR", fppg: 9.4 },
    { name: "Greg Comella", position: "RB", fppg: 4.4 },
    { name: "Joe Jurevicius", position: "WR", fppg: 4.4 }
  ]},

  { team: "Philadelphia Eagles", year: 2022, players: [
    { name: "Jalen Hurts", position: "QB", fppg: 25.0 },
    { name: "A.J. Brown", position: "WR", fppg: 19.4 },
    { name: "DeVonta Smith", position: "WR", fppg: 14.4 },
    { name: "Miles Sanders", position: "RB", fppg: 13.8 },
    { name: "Dallas Goedert", position: "TE", fppg: 10.6 },
    { name: "Kenneth Gainwell", position: "RB", fppg: 6.3 },
    { name: "Quez Watkins", position: "WR", fppg: 5.6 }
  ]},
  { team: "Philadelphia Eagles", year: 2013, players: [
    { name: "Nick Foles", position: "QB", fppg: 20.0 },
    { name: "LeSean McCoy", position: "RB", fppg: 21.9 },
    { name: "DeSean Jackson", position: "WR", fppg: 15.0 },
    { name: "Riley Cooper", position: "WR", fppg: 9.4 },
    { name: "Zach Ertz", position: "TE", fppg: 6.9 },
    { name: "Bryce Brown", position: "RB", fppg: 4.4 }
  ]},
  { team: "Philadelphia Eagles", year: 2017, players: [
    { name: "Carson Wentz", position: "QB", fppg: 18.8 },
    { name: "Alshon Jeffery", position: "WR", fppg: 12.5 },
    { name: "LeGarrette Blount", position: "RB", fppg: 11.9 },
    { name: "Zach Ertz", position: "TE", fppg: 12.5 },
    { name: "Nelson Agholor", position: "WR", fppg: 8.7 },
    { name: "Jay Ajayi", position: "RB", fppg: 5.6 }
  ]},
  { team: "Philadelphia Eagles", year: 2004, players: [
    { name: "Donovan McNabb", position: "QB", fppg: 20.0 },
    { name: "Terrell Owens", position: "WR", fppg: 18.1 },
    { name: "Brian Westbrook", position: "RB", fppg: 15.6 },
    { name: "Todd Pinkston", position: "WR", fppg: 6.9 },
    { name: "L.J. Smith", position: "TE", fppg: 5.6 },
    { name: "Dorsey Levens", position: "RB", fppg: 4.4 }
  ]},
  { team: "Philadelphia Eagles", year: 2010, players: [
    { name: "Michael Vick", position: "QB", fppg: 21.3 },
    { name: "DeSean Jackson", position: "WR", fppg: 13.8 },
    { name: "LeSean McCoy", position: "RB", fppg: 17.2 },
    { name: "Jeremy Maclin", position: "WR", fppg: 11.3 },
    { name: "Brent Celek", position: "TE", fppg: 8.1 },
    { name: "Jason Avant", position: "WR", fppg: 4.4 }
  ]},

  { team: "Washington Commanders", year: 1999, players: [
    { name: "Brad Johnson", position: "QB", fppg: 16.3 },
    { name: "Stephen Davis", position: "RB", fppg: 16.3 },
    { name: "Michael Westbrook", position: "WR", fppg: 13.1 },
    { name: "Albert Connell", position: "WR", fppg: 9.4 },
    { name: "Skip Hicks", position: "RB", fppg: 5.0 },
    { name: "James Thrash", position: "WR", fppg: 6.3 }
  ]},
  { team: "Washington Commanders", year: 2012, players: [
    { name: "Robert Griffin III", position: "QB", fppg: 20.6 },
    { name: "Alfred Morris", position: "RB", fppg: 16.3 },
    { name: "Pierre Garcon", position: "WR", fppg: 9.4 },
    { name: "Santana Moss", position: "WR", fppg: 8.1 },
    { name: "Fred Davis", position: "TE", fppg: 5.6 },
    { name: "Josh Morgan", position: "WR", fppg: 5.0 }
  ]},
  { team: "Washington Commanders", year: 2005, players: [
    { name: "Mark Brunell", position: "QB", fppg: 13.8 },
    { name: "Clinton Portis", position: "RB", fppg: 15.6 },
    { name: "Santana Moss", position: "WR", fppg: 16.3 },
    { name: "Chris Cooley", position: "TE", fppg: 9.4 },
    { name: "David Patten", position: "WR", fppg: 6.3 },
    { name: "Ladell Betts", position: "RB", fppg: 4.4 }
  ]},
  { team: "Washington Commanders", year: 2024, players: [
    { name: "Jayden Daniels", position: "QB", fppg: 23.8 },
    { name: "Terry McLaurin", position: "WR", fppg: 15.6 },
    { name: "Brian Robinson Jr.", position: "RB", fppg: 12.5 },
    { name: "Zach Ertz", position: "TE", fppg: 8.7 },
    { name: "Austin Ekeler", position: "RB", fppg: 8.1 },
    { name: "Noah Brown", position: "WR", fppg: 7.5 },
    { name: "Dyami Brown", position: "WR", fppg: 4.4 }
  ]},
  { team: "Washington Commanders", year: 2016, players: [
    { name: "Kirk Cousins", position: "QB", fppg: 21.3 },
    { name: "DeSean Jackson", position: "WR", fppg: 12.2 },
    { name: "Jordan Reed", position: "TE", fppg: 12.5 },
    { name: "Pierre Garcon", position: "WR", fppg: 12.5 },
    { name: "Chris Thompson", position: "RB", fppg: 7.5 },
    { name: "Jamison Crowder", position: "WR", fppg: 8.7 }
  ]},

  // ---- NFC NORTH ----
  { team: "Chicago Bears", year: 2012, players: [
    { name: "Jay Cutler", position: "QB", fppg: 15.0 },
    { name: "Brandon Marshall", position: "WR", fppg: 20.0 },
    { name: "Matt Forte", position: "RB", fppg: 15.6 },
    { name: "Alshon Jeffery", position: "WR", fppg: 8.1 },
    { name: "Kellen Davis", position: "TE", fppg: 3.8 },
    { name: "Michael Bush", position: "RB", fppg: 6.3 }
  ]},
  { team: "Chicago Bears", year: 2013, players: [
    { name: "Jay Cutler", position: "QB", fppg: 13.8 },
    { name: "Brandon Marshall", position: "WR", fppg: 17.8 },
    { name: "Alshon Jeffery", position: "WR", fppg: 14.1 },
    { name: "Matt Forte", position: "RB", fppg: 17.5 },
    { name: "Martellus Bennett", position: "TE", fppg: 8.7 },
    { name: "Earl Bennett", position: "WR", fppg: 4.4 }
  ]},
  { team: "Chicago Bears", year: 2006, players: [
    { name: "Rex Grossman", position: "QB", fppg: 11.9 },
    { name: "Thomas Jones", position: "RB", fppg: 14.7 },
    { name: "Muhsin Muhammad", position: "WR", fppg: 10.9 },
    { name: "Bernard Berrian", position: "WR", fppg: 8.1 },
    { name: "Desmond Clark", position: "TE", fppg: 5.6 },
    { name: "Cedric Benson", position: "RB", fppg: 4.4 }
  ]},
  { team: "Chicago Bears", year: 2020, players: [
    { name: "David Montgomery", position: "RB", fppg: 15.3 },
    { name: "Allen Robinson II", position: "WR", fppg: 14.7 },
    { name: "Mitchell Trubisky", position: "QB", fppg: 12.2 },
    { name: "Anthony Miller", position: "WR", fppg: 8.1 },
    { name: "Jimmy Graham", position: "TE", fppg: 5.6 },
    { name: "Cordarrelle Patterson", position: "RB", fppg: 5.0 }
  ]},
  { team: "Chicago Bears", year: 2018, players: [
    { name: "Mitchell Trubisky", position: "QB", fppg: 16.3 },
    { name: "Allen Robinson II", position: "WR", fppg: 10.9 },
    { name: "Tarik Cohen", position: "RB", fppg: 13.1 },
    { name: "Jordan Howard", position: "RB", fppg: 8.7 },
    { name: "Trey Burton", position: "TE", fppg: 6.9 },
    { name: "Taylor Gabriel", position: "WR", fppg: 6.3 }
  ]},

  { team: "Detroit Lions", year: 2011, players: [
    { name: "Matthew Stafford", position: "QB", fppg: 22.5 },
    { name: "Calvin Johnson", position: "WR", fppg: 18.8 },
    { name: "Jahvid Best", position: "RB", fppg: 8.7 },
    { name: "Nate Burleson", position: "WR", fppg: 8.1 },
    { name: "Brandon Pettigrew", position: "TE", fppg: 7.5 },
    { name: "Kevin Smith", position: "RB", fppg: 4.4 }
  ]},
  { team: "Detroit Lions", year: 2012, players: [
    { name: "Matthew Stafford", position: "QB", fppg: 21.6 },
    { name: "Calvin Johnson", position: "WR", fppg: 21.3 },
    { name: "Reggie Bush", position: "RB", fppg: 13.1 },
    { name: "Brandon Pettigrew", position: "TE", fppg: 7.5 },
    { name: "Titus Young", position: "WR", fppg: 5.6 },
    { name: "Kevin Smith", position: "RB", fppg: 3.8 }
  ]},
  { team: "Detroit Lions", year: 2022, players: [
    { name: "Jared Goff", position: "QB", fppg: 18.1 },
    { name: "Amon-Ra St. Brown", position: "WR", fppg: 17.5 },
    { name: "Jamaal Williams", position: "RB", fppg: 14.4 },
    { name: "D.J. Chark Jr.", position: "WR", fppg: 6.9 },
    { name: "T.J. Hockenson", position: "TE", fppg: 9.4 },
    { name: "D'Andre Swift", position: "RB", fppg: 8.7 }
  ]},
  { team: "Detroit Lions", year: 2023, players: [
    { name: "Jared Goff", position: "QB", fppg: 20.0 },
    { name: "Amon-Ra St. Brown", position: "WR", fppg: 18.8 },
    { name: "Jahmyr Gibbs", position: "RB", fppg: 16.3 },
    { name: "David Montgomery", position: "RB", fppg: 14.4 },
    { name: "Sam LaPorta", position: "TE", fppg: 12.5 },
    { name: "Josh Reynolds", position: "WR", fppg: 6.3 }
  ]},
  { team: "Detroit Lions", year: 1999, players: [
    { name: "Charlie Batch", position: "QB", fppg: 12.5 },
    { name: "Herman Moore", position: "WR", fppg: 13.8 },
    { name: "Greg Hill", position: "RB", fppg: 10.6 },
    { name: "Johnnie Morton", position: "WR", fppg: 9.4 },
    { name: "David Sloan", position: "TE", fppg: 4.4 },
    { name: "Sedrick Irvin", position: "RB", fppg: 3.1 }
  ]},

  { team: "Green Bay Packers", year: 2011, players: [
    { name: "Aaron Rodgers", position: "QB", fppg: 25.0 },
    { name: "Jordy Nelson", position: "WR", fppg: 16.3 },
    { name: "Greg Jennings", position: "WR", fppg: 15.3 },
    { name: "Jermichael Finley", position: "TE", fppg: 8.7 },
    { name: "James Starks", position: "RB", fppg: 6.9 },
    { name: "Ryan Grant", position: "RB", fppg: 5.6 }
  ]},
  { team: "Green Bay Packers", year: 2014, players: [
    { name: "Aaron Rodgers", position: "QB", fppg: 23.4 },
    { name: "Jordy Nelson", position: "WR", fppg: 18.8 },
    { name: "Eddie Lacy", position: "RB", fppg: 15.6 },
    { name: "Randall Cobb", position: "WR", fppg: 14.7 },
    { name: "Jermichael Finley", position: "TE", fppg: 4.4 },
    { name: "James Starks", position: "RB", fppg: 5.0 }
  ]},
  { team: "Green Bay Packers", year: 2020, players: [
    { name: "Aaron Rodgers", position: "QB", fppg: 23.8 },
    { name: "Davante Adams", position: "WR", fppg: 21.3 },
    { name: "Aaron Jones", position: "RB", fppg: 16.3 },
    { name: "Allen Lazard", position: "WR", fppg: 8.7 },
    { name: "Robert Tonyan", position: "TE", fppg: 8.1 },
    { name: "Jamaal Williams", position: "RB", fppg: 6.9 }
  ]},
  { team: "Green Bay Packers", year: 2003, players: [
    { name: "Brett Favre", position: "QB", fppg: 18.1 },
    { name: "Ahman Green", position: "RB", fppg: 21.9 },
    { name: "Donald Driver", position: "WR", fppg: 12.5 },
    { name: "Robert Ferguson", position: "WR", fppg: 6.9 },
    { name: "Bubba Franks", position: "TE", fppg: 6.3 },
    { name: "Najeh Davenport", position: "RB", fppg: 3.1 }
  ]},
  { team: "Green Bay Packers", year: 2016, players: [
    { name: "Aaron Rodgers", position: "QB", fppg: 22.5 },
    { name: "Jordy Nelson", position: "WR", fppg: 17.5 },
    { name: "Ty Montgomery", position: "RB", fppg: 11.9 },
    { name: "Davante Adams", position: "WR", fppg: 13.1 },
    { name: "Jared Cook", position: "TE", fppg: 7.5 },
    { name: "James Starks", position: "RB", fppg: 3.8 }
  ]},

  { team: "Minnesota Vikings", year: 2000, players: [
    { name: "Daunte Culpepper", position: "QB", fppg: 20.6 },
    { name: "Randy Moss", position: "WR", fppg: 18.8 },
    { name: "Cris Carter", position: "WR", fppg: 13.8 },
    { name: "Robert Smith", position: "RB", fppg: 12.5 },
    { name: "Jake Reed", position: "WR", fppg: 6.3 },
    { name: "Byron Chamberlain", position: "TE", fppg: 4.4 }
  ]},
  { team: "Minnesota Vikings", year: 2009, players: [
    { name: "Brett Favre", position: "QB", fppg: 20.0 },
    { name: "Adrian Peterson", position: "RB", fppg: 20.0 },
    { name: "Sidney Rice", position: "WR", fppg: 15.6 },
    { name: "Visanthe Shiancoe", position: "TE", fppg: 7.5 },
    { name: "Percy Harvin", position: "WR", fppg: 10.6 },
    { name: "Chester Taylor", position: "RB", fppg: 5.6 }
  ]},
  { team: "Minnesota Vikings", year: 2012, players: [
    { name: "Adrian Peterson", position: "RB", fppg: 25.0 },
    { name: "Christian Ponder", position: "QB", fppg: 11.9 },
    { name: "Percy Harvin", position: "WR", fppg: 14.4 },
    { name: "Kyle Rudolph", position: "TE", fppg: 8.1 },
    { name: "Jerome Simpson", position: "WR", fppg: 6.3 },
    { name: "Toby Gerhart", position: "RB", fppg: 4.4 }
  ]},
  { team: "Minnesota Vikings", year: 2015, players: [
    { name: "Adrian Peterson", position: "RB", fppg: 18.8 },
    { name: "Teddy Bridgewater", position: "QB", fppg: 12.5 },
    { name: "Stefon Diggs", position: "WR", fppg: 9.4 },
    { name: "Mike Wallace", position: "WR", fppg: 7.5 },
    { name: "Kyle Rudolph", position: "TE", fppg: 8.7 },
    { name: "Charles Johnson", position: "WR", fppg: 4.4 }
  ]},
  { team: "Minnesota Vikings", year: 2020, players: [
    { name: "Justin Jefferson", position: "WR", fppg: 18.8 },
    { name: "Dalvin Cook", position: "RB", fppg: 21.3 },
    { name: "Kirk Cousins", position: "QB", fppg: 18.8 },
    { name: "Adam Thielen", position: "WR", fppg: 11.9 },
    { name: "Irv Smith Jr.", position: "TE", fppg: 6.3 },
    { name: "Alexander Mattison", position: "RB", fppg: 5.0 }
  ]},

  // ---- NFC SOUTH ----
  { team: "Atlanta Falcons", year: 1999, players: [
    { name: "Chris Chandler", position: "QB", fppg: 13.8 },
    { name: "Jamal Anderson", position: "RB", fppg: 12.5 },
    { name: "Tony Martin", position: "WR", fppg: 11.9 },
    { name: "Terance Mathis", position: "WR", fppg: 10.6 },
    { name: "O.J. Santiago", position: "TE", fppg: 4.4 },
    { name: "Bob Christian", position: "RB", fppg: 3.1 }
  ]},
  { team: "Atlanta Falcons", year: 2004, players: [
    { name: "Michael Vick", position: "QB", fppg: 17.5 },
    { name: "Warrick Dunn", position: "RB", fppg: 13.8 },
    { name: "Alge Crumpler", position: "TE", fppg: 10.9 },
    { name: "T.J. Duckett", position: "RB", fppg: 6.9 },
    { name: "Peerless Price", position: "WR", fppg: 7.5 },
    { name: "Dez White", position: "WR", fppg: 4.4 }
  ]},
  { team: "Atlanta Falcons", year: 2012, players: [
    { name: "Matt Ryan", position: "QB", fppg: 21.3 },
    { name: "Julio Jones", position: "WR", fppg: 18.8 },
    { name: "Roddy White", position: "WR", fppg: 16.3 },
    { name: "Michael Turner", position: "RB", fppg: 12.5 },
    { name: "Tony Gonzalez", position: "TE", fppg: 12.5 },
    { name: "Jacquizz Rodgers", position: "RB", fppg: 5.0 }
  ]},
  { team: "Atlanta Falcons", year: 2016, players: [
    { name: "Matt Ryan", position: "QB", fppg: 25.0 },
    { name: "Julio Jones", position: "WR", fppg: 18.8 },
    { name: "Devonta Freeman", position: "RB", fppg: 16.3 },
    { name: "Tevin Coleman", position: "RB", fppg: 9.4 },
    { name: "Mohamed Sanu", position: "WR", fppg: 8.7 },
    { name: "Austin Hooper", position: "TE", fppg: 4.4 }
  ]},
  { team: "Atlanta Falcons", year: 2021, players: [
    { name: "Matt Ryan", position: "QB", fppg: 16.3 },
    { name: "Kyle Pitts", position: "TE", fppg: 11.9 },
    { name: "Cordarrelle Patterson", position: "RB", fppg: 14.4 },
    { name: "Russell Gage", position: "WR", fppg: 8.7 },
    { name: "Calvin Ridley", position: "WR", fppg: 12.5 },
    { name: "Mike Davis", position: "RB", fppg: 5.6 }
  ]},

  { team: "Carolina Panthers", year: 2015, players: [
    { name: "Cam Newton", position: "QB", fppg: 24.4 },
    { name: "Greg Olsen", position: "TE", fppg: 14.4 },
    { name: "Jonathan Stewart", position: "RB", fppg: 12.5 },
    { name: "Ted Ginn Jr.", position: "WR", fppg: 8.7 },
    { name: "Devin Funchess", position: "WR", fppg: 6.3 },
    { name: "Mike Tolbert", position: "RB", fppg: 5.6 }
  ]},
  { team: "Carolina Panthers", year: 2003, players: [
    { name: "Jake Delhomme", position: "QB", fppg: 14.4 },
    { name: "Stephen Davis", position: "RB", fppg: 15.6 },
    { name: "Steve Smith Sr.", position: "WR", fppg: 12.5 },
    { name: "Muhsin Muhammad", position: "WR", fppg: 10.9 },
    { name: "DeShaun Foster", position: "RB", fppg: 5.6 },
    { name: "Ricky Proehl", position: "WR", fppg: 5.0 }
  ]},
  { team: "Carolina Panthers", year: 1999, players: [
    { name: "Steve Beuerlein", position: "QB", fppg: 20.0 },
    { name: "Tim Biakabutuka", position: "RB", fppg: 11.3 },
    { name: "Muhsin Muhammad", position: "WR", fppg: 14.4 },
    { name: "Wesley Walls", position: "TE", fppg: 9.4 },
    { name: "Patrick Jeffers", position: "WR", fppg: 8.7 },
    { name: "Fred Lane", position: "RB", fppg: 4.4 }
  ]},
  { team: "Carolina Panthers", year: 2017, players: [
    { name: "Cam Newton", position: "QB", fppg: 18.8 },
    { name: "Christian McCaffrey", position: "RB", fppg: 16.3 },
    { name: "Devin Funchess", position: "WR", fppg: 10.9 },
    { name: "Greg Olsen", position: "TE", fppg: 6.9 },
    { name: "Kelvin Benjamin", position: "WR", fppg: 7.5 },
    { name: "Jonathan Stewart", position: "RB", fppg: 6.3 }
  ]},
  { team: "Carolina Panthers", year: 2020, players: [
    { name: "Christian McCaffrey", position: "RB", fppg: 21.6 },
    { name: "Teddy Bridgewater", position: "QB", fppg: 13.8 },
    { name: "D.J. Moore", position: "WR", fppg: 13.8 },
    { name: "Robby Anderson", position: "WR", fppg: 11.9 },
    { name: "Mike Davis", position: "RB", fppg: 12.5 },
    { name: "Curtis Samuel", position: "WR", fppg: 8.1 }
  ]},

  { team: "New Orleans Saints", year: 2009, players: [
    { name: "Drew Brees", position: "QB", fppg: 23.1 },
    { name: "Marques Colston", position: "WR", fppg: 15.6 },
    { name: "Pierre Thomas", position: "RB", fppg: 13.8 },
    { name: "Robert Meachem", position: "WR", fppg: 7.5 },
    { name: "Jeremy Shockey", position: "TE", fppg: 6.9 },
    { name: "Mike Bell", position: "RB", fppg: 5.6 }
  ]},
  { team: "New Orleans Saints", year: 2011, players: [
    { name: "Drew Brees", position: "QB", fppg: 25.0 },
    { name: "Darren Sproles", position: "RB", fppg: 17.5 },
    { name: "Marques Colston", position: "WR", fppg: 15.0 },
    { name: "Jimmy Graham", position: "TE", fppg: 14.4 },
    { name: "Pierre Thomas", position: "RB", fppg: 8.7 },
    { name: "Lance Moore", position: "WR", fppg: 7.5 }
  ]},
  { team: "New Orleans Saints", year: 2013, players: [
    { name: "Drew Brees", position: "QB", fppg: 23.8 },
    { name: "Jimmy Graham", position: "TE", fppg: 17.5 },
    { name: "Mark Ingram II", position: "RB", fppg: 11.3 },
    { name: "Marques Colston", position: "WR", fppg: 11.3 },
    { name: "Kenny Stills", position: "WR", fppg: 7.5 },
    { name: "Darren Sproles", position: "RB", fppg: 9.4 }
  ]},
  { team: "New Orleans Saints", year: 2019, players: [
    { name: "Drew Brees", position: "QB", fppg: 17.5 },
    { name: "Michael Thomas", position: "WR", fppg: 21.3 },
    { name: "Alvin Kamara", position: "RB", fppg: 18.8 },
    { name: "Latavius Murray", position: "RB", fppg: 8.7 },
    { name: "Jared Cook", position: "TE", fppg: 7.5 },
    { name: "Ted Ginn Jr.", position: "WR", fppg: 5.0 }
  ]},
  { team: "New Orleans Saints", year: 2000, players: [
    { name: "Jeff Blake", position: "QB", fppg: 13.1 },
    { name: "Ricky Williams", position: "RB", fppg: 17.5 },
    { name: "Joe Horn", position: "WR", fppg: 14.4 },
    { name: "Willie Jackson", position: "WR", fppg: 6.9 },
    { name: "Cam Cleeland", position: "TE", fppg: 5.0 },
    { name: "Aaron Craver", position: "RB", fppg: 3.1 }
  ]},

  { team: "Tampa Bay Buccaneers", year: 2021, players: [
    { name: "Tom Brady", position: "QB", fppg: 23.8 },
    { name: "Mike Evans", position: "WR", fppg: 16.3 },
    { name: "Leonard Fournette", position: "RB", fppg: 13.8 },
    { name: "Chris Godwin", position: "WR", fppg: 15.6 },
    { name: "Rob Gronkowski", position: "TE", fppg: 11.3 },
    { name: "Antonio Brown", position: "WR", fppg: 10.6 }
  ]},
  { team: "Tampa Bay Buccaneers", year: 2020, players: [
    { name: "Tom Brady", position: "QB", fppg: 21.3 },
    { name: "Mike Evans", position: "WR", fppg: 15.0 },
    { name: "Rob Gronkowski", position: "TE", fppg: 11.3 },
    { name: "Chris Godwin", position: "WR", fppg: 13.8 },
    { name: "Leonard Fournette", position: "RB", fppg: 6.3 },
    { name: "Ronald Jones II", position: "RB", fppg: 8.7 }
  ]},
  { team: "Tampa Bay Buccaneers", year: 2015, players: [
    { name: "Jameis Winston", position: "QB", fppg: 17.2 },
    { name: "Mike Evans", position: "WR", fppg: 16.3 },
    { name: "Doug Martin", position: "RB", fppg: 16.9 },
    { name: "Vincent Jackson", position: "WR", fppg: 11.3 },
    { name: "Austin Seferian-Jenkins", position: "TE", fppg: 5.6 },
    { name: "Charles Sims", position: "RB", fppg: 6.9 }
  ]},
  { team: "Tampa Bay Buccaneers", year: 2018, players: [
    { name: "Jameis Winston", position: "QB", fppg: 15.6 },
    { name: "Mike Evans", position: "WR", fppg: 16.3 },
    { name: "Chris Godwin", position: "WR", fppg: 14.4 },
    { name: "Peyton Barber", position: "RB", fppg: 9.4 },
    { name: "O.J. Howard", position: "TE", fppg: 8.1 },
    { name: "DeSean Jackson", position: "WR", fppg: 8.7 }
  ]},
  { team: "Tampa Bay Buccaneers", year: 1999, players: [
    { name: "Shaun King", position: "QB", fppg: 9.4 },
    { name: "Mike Alstott", position: "RB", fppg: 13.8 },
    { name: "Keyshawn Johnson", position: "WR", fppg: 11.9 },
    { name: "Warrick Dunn", position: "RB", fppg: 10.6 },
    { name: "Reidel Anthony", position: "WR", fppg: 5.6 },
    { name: "Dave Moore", position: "TE", fppg: 3.1 }
  ]},

  // ---- NFC WEST ----
  { team: "Arizona Cardinals", year: 2008, players: [
    { name: "Kurt Warner", position: "QB", fppg: 20.6 },
    { name: "Larry Fitzgerald", position: "WR", fppg: 18.8 },
    { name: "Anquan Boldin", position: "WR", fppg: 16.3 },
    { name: "Edgerrin James", position: "RB", fppg: 9.4 },
    { name: "Steve Breaston", position: "WR", fppg: 8.1 },
    { name: "Tim Hightower", position: "RB", fppg: 5.6 }
  ]},
  { team: "Arizona Cardinals", year: 2015, players: [
    { name: "Carson Palmer", position: "QB", fppg: 21.3 },
    { name: "Larry Fitzgerald", position: "WR", fppg: 15.0 },
    { name: "David Johnson", position: "RB", fppg: 12.5 },
    { name: "John Brown", position: "WR", fppg: 10.6 },
    { name: "Michael Floyd", position: "WR", fppg: 9.4 },
    { name: "Chris Johnson", position: "RB", fppg: 5.0 }
  ]},
  { team: "Arizona Cardinals", year: 2016, players: [
    { name: "David Johnson", position: "RB", fppg: 25.0 },
    { name: "Carson Palmer", position: "QB", fppg: 17.5 },
    { name: "Larry Fitzgerald", position: "WR", fppg: 14.4 },
    { name: "John Brown", position: "WR", fppg: 7.5 },
    { name: "Jermaine Gresham", position: "TE", fppg: 5.6 },
    { name: "J.J. Nelson", position: "WR", fppg: 5.0 }
  ]},
  { team: "Arizona Cardinals", year: 2021, players: [
    { name: "Kyler Murray", position: "QB", fppg: 20.6 },
    { name: "DeAndre Hopkins", position: "WR", fppg: 15.6 },
    { name: "James Conner", position: "RB", fppg: 14.4 },
    { name: "A.J. Green", position: "WR", fppg: 7.5 },
    { name: "Zach Ertz", position: "TE", fppg: 9.4 },
    { name: "Chase Edmonds", position: "RB", fppg: 8.7 }
  ]},
  { team: "Arizona Cardinals", year: 2005, players: [
    { name: "Kurt Warner", position: "QB", fppg: 15.6 },
    { name: "Larry Fitzgerald", position: "WR", fppg: 15.6 },
    { name: "Marcel Shipp", position: "RB", fppg: 9.4 },
    { name: "Anquan Boldin", position: "WR", fppg: 11.9 },
    { name: "Freddie Jones", position: "TE", fppg: 5.6 },
    { name: "Troy Hambrick", position: "RB", fppg: 3.8 }
  ]},

  { team: "Los Angeles Rams", year: 1999, players: [
    { name: "Kurt Warner", position: "QB", fppg: 26.3 },
    { name: "Marshall Faulk", position: "RB", fppg: 27.5 },
    { name: "Isaac Bruce", position: "WR", fppg: 17.5 },
    { name: "Torry Holt", position: "WR", fppg: 14.4 },
    { name: "Az-Zahir Hakim", position: "WR", fppg: 8.7 },
    { name: "Ricky Proehl", position: "WR", fppg: 6.3 },
    { name: "Roland Williams", position: "TE", fppg: 3.1 }
  ]},
  { team: "Los Angeles Rams", year: 2000, players: [
    { name: "Kurt Warner", position: "QB", fppg: 23.8 },
    { name: "Marshall Faulk", position: "RB", fppg: 28.8 },
    { name: "Torry Holt", position: "WR", fppg: 17.5 },
    { name: "Isaac Bruce", position: "WR", fppg: 13.1 },
    { name: "Az-Zahir Hakim", position: "WR", fppg: 8.7 },
    { name: "Ernie Conwell", position: "TE", fppg: 3.8 }
  ]},
  { team: "Los Angeles Rams", year: 2001, players: [
    { name: "Kurt Warner", position: "QB", fppg: 25.0 },
    { name: "Marshall Faulk", position: "RB", fppg: 25.0 },
    { name: "Torry Holt", position: "WR", fppg: 18.8 },
    { name: "Isaac Bruce", position: "WR", fppg: 13.8 },
    { name: "Ricky Proehl", position: "WR", fppg: 6.9 },
    { name: "Az-Zahir Hakim", position: "WR", fppg: 6.3 }
  ]},
  { team: "Los Angeles Rams", year: 2017, players: [
    { name: "Jared Goff", position: "QB", fppg: 17.5 },
    { name: "Todd Gurley II", position: "RB", fppg: 25.0 },
    { name: "Robert Woods", position: "WR", fppg: 13.8 },
    { name: "Sammy Watkins", position: "WR", fppg: 9.4 },
    { name: "Cooper Kupp", position: "WR", fppg: 10.6 },
    { name: "Gerald Everett", position: "TE", fppg: 5.0 }
  ]},
  { team: "Los Angeles Rams", year: 2021, players: [
    { name: "Matthew Stafford", position: "QB", fppg: 21.3 },
    { name: "Cooper Kupp", position: "WR", fppg: 27.5 },
    { name: "Sony Michel", position: "RB", fppg: 10.6 },
    { name: "Robert Woods", position: "WR", fppg: 9.4 },
    { name: "Tyler Higbee", position: "TE", fppg: 8.1 },
    { name: "Darrell Henderson Jr.", position: "RB", fppg: 6.9 }
  ]},

  { team: "San Francisco 49ers", year: 2012, players: [
    { name: "Colin Kaepernick", position: "QB", fppg: 13.8 },
    { name: "Frank Gore", position: "RB", fppg: 14.4 },
    { name: "Vernon Davis", position: "TE", fppg: 12.5 },
    { name: "Michael Crabtree", position: "WR", fppg: 10.6 },
    { name: "Randy Moss", position: "WR", fppg: 6.3 },
    { name: "LaMichael James", position: "RB", fppg: 3.1 }
  ]},
  { team: "San Francisco 49ers", year: 2019, players: [
    { name: "Jimmy Garoppolo", position: "QB", fppg: 16.3 },
    { name: "George Kittle", position: "TE", fppg: 16.3 },
    { name: "Deebo Samuel", position: "WR", fppg: 10.6 },
    { name: "Raheem Mostert", position: "RB", fppg: 9.4 },
    { name: "Tevin Coleman", position: "RB", fppg: 8.1 },
    { name: "Emmanuel Sanders", position: "WR", fppg: 10.6 },
    { name: "Matt Breida", position: "RB", fppg: 6.9 }
  ]},
  { team: "San Francisco 49ers", year: 2022, players: [
    { name: "Christian McCaffrey", position: "RB", fppg: 16.9 },
    { name: "Deebo Samuel", position: "WR", fppg: 15.6 },
    { name: "George Kittle", position: "TE", fppg: 12.5 },
    { name: "Brandon Aiyuk", position: "WR", fppg: 12.5 },
    { name: "Jimmy Garoppolo", position: "QB", fppg: 15.6 },
    { name: "Elijah Mitchell", position: "RB", fppg: 6.3 }
  ]},
  { team: "San Francisco 49ers", year: 2023, players: [
    { name: "Brock Purdy", position: "QB", fppg: 20.6 },
    { name: "Christian McCaffrey", position: "RB", fppg: 25.0 },
    { name: "Deebo Samuel", position: "WR", fppg: 14.7 },
    { name: "George Kittle", position: "TE", fppg: 14.4 },
    { name: "Brandon Aiyuk", position: "WR", fppg: 13.8 },
    { name: "Jauan Jennings", position: "WR", fppg: 5.6 }
  ]},
  { team: "San Francisco 49ers", year: 2002, players: [
    { name: "Jeff Garcia", position: "QB", fppg: 18.1 },
    { name: "Terrell Owens", position: "WR", fppg: 18.8 },
    { name: "Garrison Hearst", position: "RB", fppg: 13.8 },
    { name: "Tai Streets", position: "WR", fppg: 8.1 },
    { name: "Cedrick Wilson", position: "WR", fppg: 6.3 },
    { name: "Kevan Barlow", position: "RB", fppg: 4.4 }
  ]},

  { team: "Seattle Seahawks", year: 2005, players: [
    { name: "Shaun Alexander", position: "RB", fppg: 21.9 },
    { name: "Matt Hasselbeck", position: "QB", fppg: 16.3 },
    { name: "Darrell Jackson", position: "WR", fppg: 12.5 },
    { name: "Bobby Engram", position: "WR", fppg: 7.5 },
    { name: "Jerramy Stevens", position: "TE", fppg: 6.3 },
    { name: "Joe Jurevicius", position: "WR", fppg: 5.0 }
  ]},
  { team: "Seattle Seahawks", year: 2013, players: [
    { name: "Russell Wilson", position: "QB", fppg: 18.8 },
    { name: "Marshawn Lynch", position: "RB", fppg: 17.5 },
    { name: "Doug Baldwin", position: "WR", fppg: 11.9 },
    { name: "Golden Tate", position: "WR", fppg: 10.6 },
    { name: "Zach Miller", position: "TE", fppg: 5.6 },
    { name: "Sidney Rice", position: "WR", fppg: 5.0 }
  ]},
  { team: "Seattle Seahawks", year: 2014, players: [
    { name: "Russell Wilson", position: "QB", fppg: 20.6 },
    { name: "Marshawn Lynch", position: "RB", fppg: 18.1 },
    { name: "Doug Baldwin", position: "WR", fppg: 12.5 },
    { name: "Jermaine Kearse", position: "WR", fppg: 8.1 },
    { name: "Luke Willson", position: "TE", fppg: 5.0 },
    { name: "Robert Turbin", position: "RB", fppg: 4.4 }
  ]},
  { team: "Seattle Seahawks", year: 2020, players: [
    { name: "Russell Wilson", position: "QB", fppg: 23.8 },
    { name: "DK Metcalf", position: "WR", fppg: 16.3 },
    { name: "Chris Carson", position: "RB", fppg: 12.5 },
    { name: "Tyler Lockett", position: "WR", fppg: 17.5 },
    { name: "Greg Olsen", position: "TE", fppg: 5.6 },
    { name: "Carlos Hyde", position: "RB", fppg: 6.3 }
  ]},
  { team: "Seattle Seahawks", year: 2018, players: [
    { name: "Russell Wilson", position: "QB", fppg: 20.0 },
    { name: "Chris Carson", position: "RB", fppg: 14.4 },
    { name: "Tyler Lockett", position: "WR", fppg: 13.8 },
    { name: "Doug Baldwin", position: "WR", fppg: 11.3 },
    { name: "Ed Dickson", position: "TE", fppg: 5.0 },
    { name: "Mike Davis", position: "RB", fppg: 5.6 }
  ]}
];
