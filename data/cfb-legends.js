// CFB 16-0 mode data: a curated pool of notable college football team-seasons
// (1990-2025), each with a real roster core -- 1 QB, 1 RB, 2 more skill
// weapons (WR or TE, occasionally a 2nd RB), 1 DEF -- sourced directly from
// the user-provided "CFB_16-0_Game_Template-2.xlsx" spreadsheet, sheet 9
// ("Featured Team Rosters"): 207 real team-seasons across 69 FBS programs,
// including every Power 4 team, all 16 SEC teams, plus Notre Dame and Boise
// State. This fully replaces the earlier hand-authored 44-entry/30-program
// pool (see cfbLegendsRollEntry()'s no-repeat deck in app.js for the other
// half of the original "same few teams keep showing up" fix -- a wide, real
// pool alone doesn't help if the roll is still unweighted Math.random()).
//
// DEF is a whole TEAM DEFENSE unit (e.g. "2011 Alabama Defense"), not an
// individual defensive player -- standard fantasy-football convention, and
// what lets a DEF slot be drafted independently of every other slot. DEF
// FPPG is derived from each team's real season points-allowed-per-game
// figure (given in the spreadsheet) run through the standard fantasy
// points-allowed bracket (0 allowed=10, 1-6=7, 7-13=4, 14-20=1, 21-27=0,
// 28-34=-1, 35+=-4) plus a modeled bonus for a defense's likely sacks/
// turnovers/special-teams scoring (better points-allowed -> bigger bonus,
// capped 3-7) -- the spreadsheet itself notes the full sack/INT/TD box
// score isn't available, so this bonus is a reasonable, transparent stand-in
// rather than fabricated exact splash-play counts.
//
// The spreadsheet lists names and season highlights but not individual
// offensive stat lines (its own notes call it "a roster index, not a full
// stats database"), so offensive FPPG here is an honest approximation, not
// box-score-derived: a per-position baseline (QB ~22, RB ~15.5, WR ~11,
// TE ~7) with a SMALL deterministic per-player spread, a +1 bump for
// players on a national-championship-season roster, and a +3 bump
// specifically for the season's actual Heisman WINNER (detected from the
// sheet's own "Heisman (Name)" highlight tag -- runner-ups/finalists don't
// get the bump).
//
// Tuned twice: a first pass tried a wide floor-to-ceiling spread (QB jitter
// as wide as -3..+6, chasing a bigger "perfect team" number for
// excitement), but that meant cfbLegendsPerfectScore() in app.js -- which
// derives its ceiling straight from this pool's own max value per position
// -- was anchored to rare high outliers, so an ordinary draft (whatever
// legal player you actually get offered each round, not the literal single
// best in the whole 207-entry pool) landed far below that ceiling and
// graded harshly (real user feedback: routinely stuck at C+ or below). This
// pass narrows the spread back down (perfect-team ceiling ~140, down from a
// wide-spread ~173) so nearly any legal pick scores close to its position's
// max rather than just the one lucky best-in-pool player -- the ceiling
// stays a real, unreachable-in-practice upper bound (as it must, since nothing
// can score above the pool's own max), but a normal, non-optimized draft now
// lands comfortably higher against it. Same "approximate but in the right
// neighborhood, not exact box-score accurate" standard as this app's NFL
// 17-0 data (data/legends.js).
//
// Positions: the spreadsheet's two "weapon" columns are WR by default,
// upgraded to TE wherever the sheet tags a name "(TE)", plus a short list of
// well-known backs the sheet places in a weapon column without a tag
// (Warrick Dunn, Felix Jones, LenDale White, Ronnie Brown, Foswhitt
// Whittaker, Roddy Jones -- all real RBs, kept as RB here) and Bill Flowers
// (Ole Miss TE, 2003 -- an untagged sheet miss).
//
// Shape: { team, year, players: [{ name, position, fppg }] }
// position is one of QB/RB/WR/TE/DEF. Unlike the old pool, entries here
// have 5 players (not always a full 7-deep depth chart) -- fine for the
// roll mechanic, since only one player is ever picked per roll regardless
// of pool size.

window.CFB_LEGENDS_TEAMS = [
  { team: "Alabama", year: 2020, players: [
    { name: "Mac Jones", position: "QB", fppg: 22.5 },
    { name: "Najee Harris", position: "RB", fppg: 19.5 },
    { name: "DeVonta Smith", position: "WR", fppg: 15.0 },
    { name: "Jaylen Waddle", position: "WR", fppg: 12.5 },
    { name: "2020 Alabama Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Alabama", year: 2009, players: [
    { name: "Greg McElroy", position: "QB", fppg: 21.5 },
    { name: "Mark Ingram II", position: "RB", fppg: 18.0 },
    { name: "Julio Jones", position: "WR", fppg: 11.5 },
    { name: "Colin Peek", position: "TE", fppg: 10.0 },
    { name: "2009 Alabama Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Alabama", year: 2015, players: [
    { name: "Jake Coker", position: "QB", fppg: 21.5 },
    { name: "Derrick Henry", position: "RB", fppg: 18.0 },
    { name: "Calvin Ridley", position: "WR", fppg: 11.5 },
    { name: "O.J. Howard", position: "TE", fppg: 9.5 },
    { name: "2015 Alabama Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Georgia", year: 2022, players: [
    { name: "Stetson Bennett", position: "QB", fppg: 25.0 },
    { name: "Kenny McIntosh", position: "RB", fppg: 18.0 },
    { name: "Ladd McConkey", position: "WR", fppg: 11.0 },
    { name: "Brock Bowers", position: "TE", fppg: 9.0 },
    { name: "2022 Georgia Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Georgia", year: 2021, players: [
    { name: "Stetson Bennett", position: "QB", fppg: 25.0 },
    { name: "Zamir White", position: "RB", fppg: 15.0 },
    { name: "George Pickens", position: "WR", fppg: 13.5 },
    { name: "Brock Bowers", position: "TE", fppg: 10.0 },
    { name: "2021 Georgia Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Georgia", year: 2017, players: [
    { name: "Jake Fromm", position: "QB", fppg: 22.5 },
    { name: "Nick Chubb", position: "RB", fppg: 18.0 },
    { name: "Terry Godwin", position: "WR", fppg: 11.0 },
    { name: "Isaac Nauta", position: "TE", fppg: 9.5 },
    { name: "2017 Georgia Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Ohio State", year: 2024, players: [
    { name: "Will Howard", position: "QB", fppg: 26.0 },
    { name: "TreVeyon Henderson", position: "RB", fppg: 18.0 },
    { name: "Jeremiah Smith", position: "WR", fppg: 14.5 },
    { name: "Emeka Egbuka", position: "WR", fppg: 10.5 },
    { name: "2024 Ohio State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Ohio State", year: 2014, players: [
    { name: "Cardale Jones", position: "QB", fppg: 22.0 },
    { name: "Ezekiel Elliott", position: "RB", fppg: 17.5 },
    { name: "Michael Thomas", position: "WR", fppg: 14.0 },
    { name: "Devin Smith", position: "WR", fppg: 13.0 },
    { name: "2014 Ohio State Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Ohio State", year: 2019, players: [
    { name: "Justin Fields", position: "QB", fppg: 21.5 },
    { name: "J.K. Dobbins", position: "RB", fppg: 17.0 },
    { name: "Chris Olave", position: "WR", fppg: 10.0 },
    { name: "Garrett Wilson", position: "WR", fppg: 14.0 },
    { name: "2019 Ohio State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Clemson", year: 2018, players: [
    { name: "Trevor Lawrence", position: "QB", fppg: 25.5 },
    { name: "Travis Etienne", position: "RB", fppg: 15.0 },
    { name: "Tee Higgins", position: "WR", fppg: 14.5 },
    { name: "Justyn Ross", position: "WR", fppg: 12.5 },
    { name: "2018 Clemson Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Clemson", year: 2016, players: [
    { name: "Deshaun Watson", position: "QB", fppg: 25.0 },
    { name: "Wayne Gallman", position: "RB", fppg: 15.5 },
    { name: "Mike Williams", position: "WR", fppg: 12.0 },
    { name: "Jordan Leggett", position: "TE", fppg: 8.5 },
    { name: "2016 Clemson Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Clemson", year: 2019, players: [
    { name: "Trevor Lawrence", position: "QB", fppg: 21.5 },
    { name: "Travis Etienne", position: "RB", fppg: 14.5 },
    { name: "Tee Higgins", position: "WR", fppg: 10.5 },
    { name: "Justyn Ross", position: "WR", fppg: 14.5 },
    { name: "2019 Clemson Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "LSU", year: 2019, players: [
    { name: "Joe Burrow", position: "QB", fppg: 23.5 },
    { name: "Clyde Edwards-Helaire", position: "RB", fppg: 18.0 },
    { name: "Ja'Marr Chase", position: "WR", fppg: 12.0 },
    { name: "Justin Jefferson", position: "WR", fppg: 12.5 },
    { name: "2019 LSU Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "LSU", year: 2007, players: [
    { name: "Matt Flynn", position: "QB", fppg: 23.5 },
    { name: "Jacob Hester", position: "RB", fppg: 16.0 },
    { name: "Early Doucet", position: "WR", fppg: 11.5 },
    { name: "Richard Dickson", position: "TE", fppg: 7.0 },
    { name: "2007 LSU Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "LSU", year: 2003, players: [
    { name: "Matt Mauck", position: "QB", fppg: 25.5 },
    { name: "Justin Vincent", position: "RB", fppg: 15.5 },
    { name: "Michael Clayton", position: "WR", fppg: 14.5 },
    { name: "Devery Henderson", position: "WR", fppg: 15.0 },
    { name: "2003 LSU Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Florida State", year: 2013, players: [
    { name: "Jameis Winston", position: "QB", fppg: 24.5 },
    { name: "Devonta Freeman", position: "RB", fppg: 15.5 },
    { name: "Kelvin Benjamin", position: "WR", fppg: 13.5 },
    { name: "Rashad Greene", position: "WR", fppg: 11.5 },
    { name: "2013 Florida State Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Florida State", year: 1999, players: [
    { name: "Chris Weinke", position: "QB", fppg: 25.0 },
    { name: "Travis Minor", position: "RB", fppg: 19.0 },
    { name: "Peter Warrick", position: "WR", fppg: 11.0 },
    { name: "Ron Dugans", position: "WR", fppg: 12.5 },
    { name: "1999 Florida State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Florida State", year: 1993, players: [
    { name: "Charlie Ward", position: "QB", fppg: 26.5 },
    { name: "William Floyd", position: "RB", fppg: 19.0 },
    { name: "Kez McCorvey", position: "WR", fppg: 10.5 },
    { name: "Warrick Dunn", position: "RB", fppg: 16.0 },
    { name: "1993 Florida State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Auburn", year: 2010, players: [
    { name: "Cam Newton", position: "QB", fppg: 27.0 },
    { name: "Michael Dyer", position: "RB", fppg: 16.0 },
    { name: "Darvin Adams", position: "WR", fppg: 12.5 },
    { name: "Emory Blake", position: "WR", fppg: 13.0 },
    { name: "2010 Auburn Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Auburn", year: 2013, players: [
    { name: "Nick Marshall", position: "QB", fppg: 25.5 },
    { name: "Tre Mason", position: "RB", fppg: 20.0 },
    { name: "Sammie Coates", position: "WR", fppg: 13.5 },
    { name: "C.J. Uzomah", position: "TE", fppg: 9.0 },
    { name: "2013 Auburn Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Auburn", year: 2004, players: [
    { name: "Jason Campbell", position: "QB", fppg: 23.0 },
    { name: "Carnell Williams", position: "RB", fppg: 14.5 },
    { name: "Courtney Taylor", position: "WR", fppg: 12.0 },
    { name: "Ronnie Brown", position: "RB", fppg: 14.0 },
    { name: "2004 Auburn Defense", position: "DEF", fppg: 9.5 }
  ]},
  { team: "Oregon", year: 2014, players: [
    { name: "Marcus Mariota", position: "QB", fppg: 24.0 },
    { name: "Royce Freeman", position: "RB", fppg: 16.0 },
    { name: "Byron Marshall", position: "WR", fppg: 13.0 },
    { name: "Devon Allen", position: "WR", fppg: 14.5 },
    { name: "2014 Oregon Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Oregon", year: 2010, players: [
    { name: "Darron Thomas", position: "QB", fppg: 22.0 },
    { name: "LaMichael James", position: "RB", fppg: 15.0 },
    { name: "Jeff Maehl", position: "WR", fppg: 14.5 },
    { name: "David Paulson", position: "TE", fppg: 9.5 },
    { name: "2010 Oregon Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Oregon", year: 2001, players: [
    { name: "Joey Harrington", position: "QB", fppg: 23.0 },
    { name: "Maurice Morris", position: "RB", fppg: 16.5 },
    { name: "Keenan Howry", position: "WR", fppg: 11.0 },
    { name: "Justin Peelle", position: "TE", fppg: 6.5 },
    { name: "2001 Oregon Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Michigan", year: 2023, players: [
    { name: "J.J. McCarthy", position: "QB", fppg: 25.0 },
    { name: "Blake Corum", position: "RB", fppg: 16.0 },
    { name: "Roman Wilson", position: "WR", fppg: 12.0 },
    { name: "Cornelius Johnson", position: "WR", fppg: 10.5 },
    { name: "2023 Michigan Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Michigan", year: 1997, players: [
    { name: "Brian Griese", position: "QB", fppg: 22.0 },
    { name: "Chris Howard", position: "RB", fppg: 17.0 },
    { name: "Tai Streets", position: "WR", fppg: 10.5 },
    { name: "Jerame Tuman", position: "TE", fppg: 10.5 },
    { name: "1997 Michigan Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Michigan", year: 2021, players: [
    { name: "Cade McNamara", position: "QB", fppg: 24.5 },
    { name: "Hassan Haskins", position: "RB", fppg: 16.0 },
    { name: "Ronnie Bell", position: "WR", fppg: 13.0 },
    { name: "Erick All", position: "TE", fppg: 8.0 },
    { name: "2021 Michigan Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Texas", year: 2005, players: [
    { name: "Vince Young", position: "QB", fppg: 22.5 },
    { name: "Jamaal Charles", position: "RB", fppg: 15.0 },
    { name: "Limas Sweed", position: "WR", fppg: 12.0 },
    { name: "David Thomas", position: "TE", fppg: 9.0 },
    { name: "2005 Texas Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Texas", year: 2009, players: [
    { name: "Colt McCoy", position: "QB", fppg: 23.5 },
    { name: "Cody Johnson", position: "RB", fppg: 15.0 },
    { name: "Jordan Shipley", position: "WR", fppg: 13.0 },
    { name: "Foswhitt Whittaker", position: "RB", fppg: 19.5 },
    { name: "2009 Texas Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Texas", year: 2008, players: [
    { name: "Colt McCoy", position: "QB", fppg: 22.5 },
    { name: "Chris Ogbonnaya", position: "RB", fppg: 16.5 },
    { name: "Quan Cosby", position: "WR", fppg: 11.5 },
    { name: "Jermichael Finley", position: "TE", fppg: 9.5 },
    { name: "2008 Texas Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "USC", year: 2004, players: [
    { name: "Matt Leinart", position: "QB", fppg: 25.5 },
    { name: "Reggie Bush", position: "RB", fppg: 16.0 },
    { name: "Dwayne Jarrett", position: "WR", fppg: 10.0 },
    { name: "Steve Smith", position: "WR", fppg: 12.0 },
    { name: "2004 USC Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "USC", year: 2003, players: [
    { name: "Matt Leinart", position: "QB", fppg: 23.0 },
    { name: "Justin Fargas", position: "RB", fppg: 17.0 },
    { name: "Mike Williams", position: "WR", fppg: 14.5 },
    { name: "Keary Colbert", position: "WR", fppg: 10.5 },
    { name: "2003 USC Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "USC", year: 2005, players: [
    { name: "Matt Leinart", position: "QB", fppg: 24.0 },
    { name: "Reggie Bush", position: "RB", fppg: 15.0 },
    { name: "Dwayne Jarrett", position: "WR", fppg: 12.5 },
    { name: "LenDale White", position: "RB", fppg: 20.0 },
    { name: "2005 USC Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Oklahoma", year: 2008, players: [
    { name: "Sam Bradford", position: "QB", fppg: 25.0 },
    { name: "DeMarco Murray", position: "RB", fppg: 14.5 },
    { name: "Ryan Broyles", position: "WR", fppg: 12.5 },
    { name: "Jermaine Gresham", position: "TE", fppg: 7.5 },
    { name: "2008 Oklahoma Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Oklahoma", year: 2000, players: [
    { name: "Josh Heupel", position: "QB", fppg: 22.0 },
    { name: "Quentin Griffin", position: "RB", fppg: 15.5 },
    { name: "Curtis Fagan", position: "WR", fppg: 11.0 },
    { name: "Trent Smith", position: "TE", fppg: 8.0 },
    { name: "2000 Oklahoma Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Oklahoma", year: 2003, players: [
    { name: "Jason White", position: "QB", fppg: 29.0 },
    { name: "Kejuan Jones", position: "RB", fppg: 17.5 },
    { name: "Mark Clayton", position: "WR", fppg: 11.5 },
    { name: "Brandon Jones", position: "TE", fppg: 7.0 },
    { name: "2003 Oklahoma Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Miami (FL)", year: 2001, players: [
    { name: "Ken Dorsey", position: "QB", fppg: 26.0 },
    { name: "Clinton Portis", position: "RB", fppg: 14.5 },
    { name: "Andre Johnson", position: "WR", fppg: 13.5 },
    { name: "Jeremy Shockey", position: "TE", fppg: 7.0 },
    { name: "2001 Miami (FL) Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Miami (FL)", year: 2002, players: [
    { name: "Ken Dorsey", position: "QB", fppg: 25.0 },
    { name: "Willis McGahee", position: "RB", fppg: 19.5 },
    { name: "Andre Johnson", position: "WR", fppg: 13.5 },
    { name: "Kellen Winslow II", position: "TE", fppg: 7.0 },
    { name: "2002 Miami (FL) Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Miami (FL)", year: 1991, players: [
    { name: "Gino Torretta", position: "QB", fppg: 25.5 },
    { name: "Stephen McGuire", position: "RB", fppg: 15.0 },
    { name: "Lamar Thomas", position: "WR", fppg: 15.0 },
    { name: "Horace Copeland", position: "WR", fppg: 11.0 },
    { name: "1991 Miami (FL) Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Florida", year: 2008, players: [
    { name: "Tim Tebow", position: "QB", fppg: 25.5 },
    { name: "Percy Harvin", position: "RB", fppg: 18.5 },
    { name: "Louis Murphy", position: "WR", fppg: 11.0 },
    { name: "Aaron Hernandez", position: "TE", fppg: 9.0 },
    { name: "2008 Florida Defense", position: "DEF", fppg: 9.5 }
  ]},
  { team: "Florida", year: 1996, players: [
    { name: "Danny Wuerffel", position: "QB", fppg: 27.0 },
    { name: "Fred Taylor", position: "RB", fppg: 18.5 },
    { name: "Reidel Anthony", position: "WR", fppg: 15.0 },
    { name: "Ike Hilliard", position: "WR", fppg: 10.0 },
    { name: "1996 Florida Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Florida", year: 2006, players: [
    { name: "Chris Leak", position: "QB", fppg: 23.5 },
    { name: "DeShawn Wynn", position: "RB", fppg: 14.5 },
    { name: "Dallas Baker", position: "WR", fppg: 12.5 },
    { name: "Percy Harvin", position: "WR", fppg: 11.5 },
    { name: "2006 Florida Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Notre Dame", year: 2012, players: [
    { name: "Everett Golson", position: "QB", fppg: 22.0 },
    { name: "Theo Riddick", position: "RB", fppg: 15.0 },
    { name: "T.J. Jones", position: "WR", fppg: 13.0 },
    { name: "Tyler Eifert", position: "TE", fppg: 9.5 },
    { name: "2012 Notre Dame Defense", position: "DEF", fppg: 9.5 }
  ]},
  { team: "Notre Dame", year: 2018, players: [
    { name: "Ian Book", position: "QB", fppg: 23.0 },
    { name: "Dexter Williams", position: "RB", fppg: 18.0 },
    { name: "Miles Boykin", position: "WR", fppg: 12.5 },
    { name: "Aliz\u00e9 Mack", position: "TE", fppg: 8.5 },
    { name: "2018 Notre Dame Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Notre Dame", year: 2005, players: [
    { name: "Brady Quinn", position: "QB", fppg: 22.0 },
    { name: "Darius Walker", position: "RB", fppg: 15.5 },
    { name: "Jeff Samardzija", position: "WR", fppg: 11.0 },
    { name: "Maurice Stovall", position: "WR", fppg: 11.0 },
    { name: "2005 Notre Dame Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "TCU", year: 2022, players: [
    { name: "Max Duggan", position: "QB", fppg: 21.5 },
    { name: "Kendre Miller", position: "RB", fppg: 19.0 },
    { name: "Quentin Johnston", position: "WR", fppg: 14.5 },
    { name: "Derius Davis", position: "WR", fppg: 11.0 },
    { name: "2022 TCU Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "TCU", year: 2010, players: [
    { name: "Andy Dalton", position: "QB", fppg: 25.0 },
    { name: "Ed Wesley", position: "RB", fppg: 14.0 },
    { name: "Jeremy Kerley", position: "WR", fppg: 10.0 },
    { name: "Antoine Hicks", position: "TE", fppg: 9.5 },
    { name: "2010 TCU Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "TCU", year: 2014, players: [
    { name: "Trevone Boykin", position: "QB", fppg: 21.5 },
    { name: "Aaron Green", position: "RB", fppg: 16.0 },
    { name: "Josh Doctson", position: "WR", fppg: 11.5 },
    { name: "Kolby Listenbee", position: "WR", fppg: 11.0 },
    { name: "2014 TCU Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Washington", year: 2023, players: [
    { name: "Michael Penix Jr.", position: "QB", fppg: 24.5 },
    { name: "Dillon Johnson", position: "RB", fppg: 16.5 },
    { name: "Rome Odunze", position: "WR", fppg: 13.0 },
    { name: "Ja'Lynn Polk", position: "WR", fppg: 13.5 },
    { name: "2023 Washington Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Washington", year: 1991, players: [
    { name: "Billy Joe Hobert", position: "QB", fppg: 23.0 },
    { name: "Beno Bryant", position: "RB", fppg: 16.5 },
    { name: "Mario Bailey", position: "WR", fppg: 14.0 },
    { name: "Orlando McKay", position: "WR", fppg: 10.5 },
    { name: "1991 Washington Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Washington", year: 2016, players: [
    { name: "Jake Browning", position: "QB", fppg: 21.5 },
    { name: "Myles Gaskin", position: "RB", fppg: 17.0 },
    { name: "John Ross", position: "WR", fppg: 13.5 },
    { name: "Dante Pettis", position: "WR", fppg: 13.5 },
    { name: "2016 Washington Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Tennessee", year: 1998, players: [
    { name: "Tee Martin", position: "QB", fppg: 23.5 },
    { name: "Jamal Lewis", position: "RB", fppg: 18.0 },
    { name: "Peerless Price", position: "WR", fppg: 10.5 },
    { name: "Cedrick Wilson", position: "WR", fppg: 10.0 },
    { name: "1998 Tennessee Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Tennessee", year: 2022, players: [
    { name: "Hendon Hooker", position: "QB", fppg: 23.0 },
    { name: "Jaylen Wright", position: "RB", fppg: 16.0 },
    { name: "Jalin Hyatt", position: "WR", fppg: 14.0 },
    { name: "Bru McCoy", position: "WR", fppg: 12.5 },
    { name: "2022 Tennessee Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Tennessee", year: 1997, players: [
    { name: "Peyton Manning", position: "QB", fppg: 24.0 },
    { name: "Jamal Lewis", position: "RB", fppg: 16.0 },
    { name: "Marcus Nash", position: "WR", fppg: 13.5 },
    { name: "Cedrick Wilson", position: "WR", fppg: 10.0 },
    { name: "1997 Tennessee Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Nebraska", year: 1995, players: [
    { name: "Tommie Frazier", position: "QB", fppg: 22.0 },
    { name: "Ahman Green", position: "RB", fppg: 14.5 },
    { name: "Reggie Baul", position: "WR", fppg: 14.0 },
    { name: "Mark Gilman", position: "TE", fppg: 8.0 },
    { name: "1995 Nebraska Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Nebraska", year: 1994, players: [
    { name: "Tommie Frazier", position: "QB", fppg: 25.5 },
    { name: "Lawrence Phillips", position: "RB", fppg: 15.0 },
    { name: "Brendan Holbein", position: "WR", fppg: 13.0 },
    { name: "Eric Alford", position: "WR", fppg: 13.5 },
    { name: "1994 Nebraska Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Nebraska", year: 1997, players: [
    { name: "Scott Frost", position: "QB", fppg: 25.0 },
    { name: "Ahman Green", position: "RB", fppg: 15.0 },
    { name: "Shevin Wiggins", position: "WR", fppg: 10.0 },
    { name: "Sheldon Jackson", position: "WR", fppg: 14.5 },
    { name: "1997 Nebraska Defense", position: "DEF", fppg: 9.5 }
  ]},
  { team: "Penn State", year: 1994, players: [
    { name: "Kerry Collins", position: "QB", fppg: 23.5 },
    { name: "Ki-Jana Carter", position: "RB", fppg: 14.0 },
    { name: "Bobby Engram", position: "WR", fppg: 9.5 },
    { name: "Kyle Brady", position: "TE", fppg: 7.5 },
    { name: "1994 Penn State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Penn State", year: 2016, players: [
    { name: "Trace McSorley", position: "QB", fppg: 22.0 },
    { name: "Saquon Barkley", position: "RB", fppg: 14.0 },
    { name: "Chris Godwin", position: "WR", fppg: 10.5 },
    { name: "Mike Gesicki", position: "TE", fppg: 6.0 },
    { name: "2016 Penn State Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Penn State", year: 2005, players: [
    { name: "Michael Robinson", position: "QB", fppg: 24.5 },
    { name: "Tony Hunt", position: "RB", fppg: 18.0 },
    { name: "Derrick Williams", position: "WR", fppg: 11.5 },
    { name: "Isaac Smolko", position: "TE", fppg: 6.0 },
    { name: "2005 Penn State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Wisconsin", year: 2011, players: [
    { name: "Russell Wilson", position: "QB", fppg: 23.5 },
    { name: "Montee Ball", position: "RB", fppg: 16.0 },
    { name: "Nick Toon", position: "WR", fppg: 12.5 },
    { name: "Jacob Pedersen", position: "TE", fppg: 7.5 },
    { name: "2011 Wisconsin Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Wisconsin", year: 2012, players: [
    { name: "Joel Stave", position: "QB", fppg: 23.5 },
    { name: "Montee Ball", position: "RB", fppg: 15.5 },
    { name: "Jared Abbrederis", position: "WR", fppg: 11.5 },
    { name: "Jacob Pedersen", position: "TE", fppg: 7.5 },
    { name: "2012 Wisconsin Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Wisconsin", year: 1999, players: [
    { name: "Brooks Bollinger", position: "QB", fppg: 24.5 },
    { name: "Ron Dayne", position: "RB", fppg: 19.0 },
    { name: "Chris Chambers", position: "WR", fppg: 13.5 },
    { name: "Tony Simmons", position: "WR", fppg: 12.0 },
    { name: "1999 Wisconsin Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Boise State", year: 2006, players: [
    { name: "Jared Zabransky", position: "QB", fppg: 24.0 },
    { name: "Ian Johnson", position: "RB", fppg: 18.5 },
    { name: "Legedu Naanee", position: "WR", fppg: 12.5 },
    { name: "Derek Schouman", position: "TE", fppg: 9.0 },
    { name: "2006 Boise State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Boise State", year: 2009, players: [
    { name: "Kellen Moore", position: "QB", fppg: 23.5 },
    { name: "Doug Martin", position: "RB", fppg: 16.0 },
    { name: "Titus Young", position: "WR", fppg: 10.5 },
    { name: "Kyle Efaw", position: "TE", fppg: 6.0 },
    { name: "2009 Boise State Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Boise State", year: 2010, players: [
    { name: "Kellen Moore", position: "QB", fppg: 24.0 },
    { name: "Doug Martin", position: "RB", fppg: 18.5 },
    { name: "Austin Pettis", position: "WR", fppg: 11.0 },
    { name: "Chris Potter", position: "WR", fppg: 12.5 },
    { name: "2010 Boise State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Utah", year: 2008, players: [
    { name: "Brian Johnson", position: "QB", fppg: 21.0 },
    { name: "Matt Asiata", position: "RB", fppg: 17.0 },
    { name: "David Reed", position: "WR", fppg: 11.5 },
    { name: "Freddie Brown", position: "WR", fppg: 12.5 },
    { name: "2008 Utah Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Utah", year: 2004, players: [
    { name: "Alex Smith", position: "QB", fppg: 22.0 },
    { name: "Marty Johnson", position: "RB", fppg: 16.5 },
    { name: "Steve Savoy", position: "WR", fppg: 9.5 },
    { name: "Paris Warren", position: "WR", fppg: 11.5 },
    { name: "2004 Utah Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Utah", year: 2021, players: [
    { name: "Cameron Rising", position: "QB", fppg: 24.5 },
    { name: "Tavion Thomas", position: "RB", fppg: 13.5 },
    { name: "Britain Covey", position: "WR", fppg: 10.0 },
    { name: "Dalton Kincaid", position: "TE", fppg: 6.5 },
    { name: "2021 Utah Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Oklahoma State", year: 2011, players: [
    { name: "Brandon Weeden", position: "QB", fppg: 21.5 },
    { name: "Joseph Randle", position: "RB", fppg: 15.0 },
    { name: "Justin Blackmon", position: "WR", fppg: 12.0 },
    { name: "Josh Cooper", position: "WR", fppg: 13.0 },
    { name: "2011 Oklahoma State Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Oklahoma State", year: 2010, players: [
    { name: "Brandon Weeden", position: "QB", fppg: 22.0 },
    { name: "Kendall Hunter", position: "RB", fppg: 13.5 },
    { name: "Justin Blackmon", position: "WR", fppg: 9.5 },
    { name: "Josh Cooper", position: "WR", fppg: 11.0 },
    { name: "2010 Oklahoma State Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Oklahoma State", year: 2021, players: [
    { name: "Spencer Sanders", position: "QB", fppg: 22.0 },
    { name: "Jaylen Warren", position: "RB", fppg: 17.0 },
    { name: "Tay Martin", position: "WR", fppg: 10.5 },
    { name: "Braydon Johnson", position: "WR", fppg: 10.0 },
    { name: "2021 Oklahoma State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Baylor", year: 2013, players: [
    { name: "Bryce Petty", position: "QB", fppg: 20.5 },
    { name: "Lache Seastrunk", position: "RB", fppg: 13.5 },
    { name: "Antwan Goodley", position: "WR", fppg: 14.0 },
    { name: "Tevin Reese", position: "WR", fppg: 10.0 },
    { name: "2013 Baylor Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Baylor", year: 2014, players: [
    { name: "Bryce Petty", position: "QB", fppg: 21.0 },
    { name: "Shock Linwood", position: "RB", fppg: 14.0 },
    { name: "Corey Coleman", position: "WR", fppg: 9.5 },
    { name: "Antwan Goodley", position: "WR", fppg: 12.0 },
    { name: "2014 Baylor Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Baylor", year: 2011, players: [
    { name: "Robert Griffin III", position: "QB", fppg: 23.5 },
    { name: "Terrance Ganaway", position: "RB", fppg: 15.5 },
    { name: "Kendall Wright", position: "WR", fppg: 12.5 },
    { name: "Tevin Reese", position: "WR", fppg: 10.0 },
    { name: "2011 Baylor Defense", position: "DEF", fppg: -0.5 }
  ]},
  { team: "West Virginia", year: 2007, players: [
    { name: "Pat White", position: "QB", fppg: 24.0 },
    { name: "Steve Slaton", position: "RB", fppg: 17.5 },
    { name: "Noel Devine", position: "WR", fppg: 9.0 },
    { name: "Tito Gonzales", position: "WR", fppg: 13.5 },
    { name: "2007 West Virginia Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "West Virginia", year: 2011, players: [
    { name: "Geno Smith", position: "QB", fppg: 22.0 },
    { name: "Shawne Alston", position: "RB", fppg: 15.5 },
    { name: "Tavon Austin", position: "WR", fppg: 12.0 },
    { name: "Stedman Bailey", position: "WR", fppg: 11.5 },
    { name: "2011 West Virginia Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "West Virginia", year: 1993, players: [
    { name: "Darren Studstill", position: "QB", fppg: 24.0 },
    { name: "Robert Walker", position: "RB", fppg: 15.5 },
    { name: "Tydus Winans", position: "WR", fppg: 13.5 },
    { name: "Mike Collins", position: "WR", fppg: 10.0 },
    { name: "1993 West Virginia Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Louisville", year: 2016, players: [
    { name: "Lamar Jackson", position: "QB", fppg: 26.0 },
    { name: "Brandon Radcliff", position: "RB", fppg: 18.0 },
    { name: "James Quick", position: "WR", fppg: 13.0 },
    { name: "Jamari Staples", position: "WR", fppg: 11.0 },
    { name: "2016 Louisville Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Louisville", year: 2006, players: [
    { name: "Brian Brohm", position: "QB", fppg: 24.0 },
    { name: "Michael Bush", position: "RB", fppg: 14.5 },
    { name: "Mario Urrutia", position: "WR", fppg: 13.5 },
    { name: "Gary Barnidge", position: "TE", fppg: 7.0 },
    { name: "2006 Louisville Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Louisville", year: 2013, players: [
    { name: "Teddy Bridgewater", position: "QB", fppg: 24.0 },
    { name: "Senorise Perry", position: "RB", fppg: 13.5 },
    { name: "DeVante Parker", position: "WR", fppg: 12.0 },
    { name: "Eli Rogers", position: "WR", fppg: 12.5 },
    { name: "2013 Louisville Defense", position: "DEF", fppg: 9.5 }
  ]},
  { team: "Cincinnati", year: 2021, players: [
    { name: "Desmond Ridder", position: "QB", fppg: 22.5 },
    { name: "Jerome Ford", position: "RB", fppg: 15.0 },
    { name: "Alec Pierce", position: "WR", fppg: 9.5 },
    { name: "Michael Young Jr.", position: "WR", fppg: 11.0 },
    { name: "2021 Cincinnati Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Cincinnati", year: 2009, players: [
    { name: "Tony Pike", position: "QB", fppg: 22.0 },
    { name: "Isaiah Pead", position: "RB", fppg: 16.0 },
    { name: "Mardy Gilyard", position: "WR", fppg: 10.5 },
    { name: "Ben Guidugli", position: "TE", fppg: 6.0 },
    { name: "2009 Cincinnati Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Cincinnati", year: 2020, players: [
    { name: "Desmond Ridder", position: "QB", fppg: 23.0 },
    { name: "Gerrid Doaks", position: "RB", fppg: 16.5 },
    { name: "Alec Pierce", position: "WR", fppg: 11.5 },
    { name: "Josh Whyle", position: "TE", fppg: 9.0 },
    { name: "2020 Cincinnati Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "UCF", year: 2017, players: [
    { name: "McKenzie Milton", position: "QB", fppg: 24.5 },
    { name: "Adrian Killins", position: "RB", fppg: 13.5 },
    { name: "Tre'Quan Smith", position: "WR", fppg: 11.5 },
    { name: "Dredrick Snelson", position: "WR", fppg: 13.0 },
    { name: "2017 UCF Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "UCF", year: 2018, players: [
    { name: "McKenzie Milton", position: "QB", fppg: 25.0 },
    { name: "Adrian Killins", position: "RB", fppg: 17.5 },
    { name: "Gabriel Davis", position: "WR", fppg: 12.5 },
    { name: "Dredrick Snelson", position: "WR", fppg: 10.0 },
    { name: "2018 UCF Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "UCF", year: 2013, players: [
    { name: "Blake Bortles", position: "QB", fppg: 21.5 },
    { name: "Storm Johnson", position: "RB", fppg: 17.0 },
    { name: "Breshad Perriman", position: "WR", fppg: 14.0 },
    { name: "Rannell Hall", position: "WR", fppg: 12.0 },
    { name: "2013 UCF Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Kansas State", year: 1998, players: [
    { name: "Michael Bishop", position: "QB", fppg: 21.5 },
    { name: "Eric Hickson", position: "RB", fppg: 16.0 },
    { name: "Darnell McDonald", position: "WR", fppg: 13.5 },
    { name: "Sean Snyder", position: "WR", fppg: 11.5 },
    { name: "1998 Kansas State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Kansas State", year: 2003, players: [
    { name: "Ell Roberson", position: "QB", fppg: 24.0 },
    { name: "Darren Sproles", position: "RB", fppg: 14.0 },
    { name: "Jermaine Griffin", position: "WR", fppg: 11.0 },
    { name: "Craig Chambers", position: "WR", fppg: 11.0 },
    { name: "2003 Kansas State Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Kansas State", year: 2012, players: [
    { name: "Collin Klein", position: "QB", fppg: 22.5 },
    { name: "John Hubert", position: "RB", fppg: 18.5 },
    { name: "Chris Harper", position: "WR", fppg: 13.5 },
    { name: "Travis Tannahill", position: "TE", fppg: 6.5 },
    { name: "2012 Kansas State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Virginia Tech", year: 1999, players: [
    { name: "Michael Vick", position: "QB", fppg: 22.0 },
    { name: "Shyrone Stith", position: "RB", fppg: 16.0 },
    { name: "Andre Davis", position: "WR", fppg: 15.0 },
    { name: "Ricky Hall", position: "WR", fppg: 12.0 },
    { name: "1999 Virginia Tech Defense", position: "DEF", fppg: 10.0 }
  ]},
  { team: "Virginia Tech", year: 2007, players: [
    { name: "Sean Glennon", position: "QB", fppg: 21.0 },
    { name: "Branden Ore", position: "RB", fppg: 16.0 },
    { name: "Eddie Royal", position: "WR", fppg: 12.5 },
    { name: "Josh Morgan", position: "WR", fppg: 9.5 },
    { name: "2007 Virginia Tech Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Virginia Tech", year: 2011, players: [
    { name: "Logan Thomas", position: "QB", fppg: 21.0 },
    { name: "David Wilson", position: "RB", fppg: 16.5 },
    { name: "Danny Coale", position: "WR", fppg: 10.0 },
    { name: "Marcus Davis", position: "WR", fppg: 13.5 },
    { name: "2011 Virginia Tech Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Iowa", year: 2002, players: [
    { name: "Brad Banks", position: "QB", fppg: 24.0 },
    { name: "Fred Russell", position: "RB", fppg: 14.0 },
    { name: "C.J. Jones", position: "WR", fppg: 9.5 },
    { name: "Dallas Clark", position: "TE", fppg: 6.0 },
    { name: "2002 Iowa Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Iowa", year: 2009, players: [
    { name: "Ricky Stanzi", position: "QB", fppg: 22.5 },
    { name: "Shonn Greene", position: "RB", fppg: 18.5 },
    { name: "Marvin McNutt", position: "WR", fppg: 13.0 },
    { name: "Tony Moeaki", position: "TE", fppg: 7.0 },
    { name: "2009 Iowa Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Iowa", year: 2015, players: [
    { name: "C.J. Beathard", position: "QB", fppg: 22.5 },
    { name: "Jordan Canzeri", position: "RB", fppg: 15.5 },
    { name: "Tevaun Smith", position: "WR", fppg: 9.5 },
    { name: "George Kittle", position: "TE", fppg: 7.0 },
    { name: "2015 Iowa Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Stanford", year: 2010, players: [
    { name: "Andrew Luck", position: "QB", fppg: 24.0 },
    { name: "Stepfan Taylor", position: "RB", fppg: 16.5 },
    { name: "Doug Baldwin", position: "WR", fppg: 12.5 },
    { name: "Coby Fleener", position: "TE", fppg: 5.5 },
    { name: "2010 Stanford Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Stanford", year: 2012, players: [
    { name: "Kevin Hogan", position: "QB", fppg: 23.5 },
    { name: "Stepfan Taylor", position: "RB", fppg: 16.0 },
    { name: "Ty Montgomery", position: "WR", fppg: 12.0 },
    { name: "Zach Ertz", position: "TE", fppg: 8.0 },
    { name: "2012 Stanford Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Stanford", year: 2015, players: [
    { name: "Kevin Hogan", position: "QB", fppg: 20.5 },
    { name: "Christian McCaffrey", position: "RB", fppg: 18.0 },
    { name: "Devon Cajuste", position: "WR", fppg: 12.5 },
    { name: "Austin Hooper", position: "TE", fppg: 7.0 },
    { name: "2015 Stanford Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Arkansas", year: 2011, players: [
    { name: "Tyler Wilson", position: "QB", fppg: 23.0 },
    { name: "Knile Davis", position: "RB", fppg: 15.5 },
    { name: "Jarius Wright", position: "WR", fppg: 11.5 },
    { name: "Cobi Hamilton", position: "WR", fppg: 10.0 },
    { name: "2011 Arkansas Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Arkansas", year: 2010, players: [
    { name: "Ryan Mallett", position: "QB", fppg: 25.0 },
    { name: "Knile Davis", position: "RB", fppg: 16.5 },
    { name: "Joe Adams", position: "WR", fppg: 12.5 },
    { name: "Greg Childs", position: "WR", fppg: 9.5 },
    { name: "2010 Arkansas Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Arkansas", year: 2006, players: [
    { name: "Casey Dick", position: "QB", fppg: 24.5 },
    { name: "Darren McFadden", position: "RB", fppg: 13.5 },
    { name: "Marcus Monk", position: "WR", fppg: 14.0 },
    { name: "Felix Jones", position: "RB", fppg: 18.5 },
    { name: "2006 Arkansas Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Ole Miss", year: 2015, players: [
    { name: "Chad Kelly", position: "QB", fppg: 21.0 },
    { name: "Jaylen Walton", position: "RB", fppg: 14.0 },
    { name: "Laquon Treadwell", position: "WR", fppg: 12.5 },
    { name: "Quincy Adeboyejo", position: "WR", fppg: 10.5 },
    { name: "2015 Ole Miss Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Ole Miss", year: 2014, players: [
    { name: "Bo Wallace", position: "QB", fppg: 23.5 },
    { name: "Jaylen Walton", position: "RB", fppg: 14.0 },
    { name: "Laquon Treadwell", position: "WR", fppg: 14.0 },
    { name: "Vince Sanders", position: "WR", fppg: 13.0 },
    { name: "2014 Ole Miss Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Ole Miss", year: 2003, players: [
    { name: "Eli Manning", position: "QB", fppg: 22.5 },
    { name: "BenJarvus Green-Ellis", position: "RB", fppg: 17.5 },
    { name: "Bill Flowers", position: "TE", fppg: 9.0 },
    { name: "Mike Espy", position: "WR", fppg: 12.5 },
    { name: "2003 Ole Miss Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Texas A&M", year: 2012, players: [
    { name: "Johnny Manziel", position: "QB", fppg: 25.5 },
    { name: "Ben Malena", position: "RB", fppg: 18.5 },
    { name: "Mike Evans", position: "WR", fppg: 9.5 },
    { name: "Ryan Swope", position: "WR", fppg: 13.0 },
    { name: "2012 Texas A&M Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Texas A&M", year: 1998, players: [
    { name: "Branndon Stewart", position: "QB", fppg: 22.5 },
    { name: "Sirr Parker", position: "RB", fppg: 17.0 },
    { name: "Chris Cole", position: "WR", fppg: 9.5 },
    { name: "Dan Campbell", position: "TE", fppg: 6.5 },
    { name: "1998 Texas A&M Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Texas A&M", year: 2020, players: [
    { name: "Kellen Mond", position: "QB", fppg: 25.0 },
    { name: "Isaiah Spiller", position: "RB", fppg: 18.5 },
    { name: "Ainias Smith", position: "WR", fppg: 13.0 },
    { name: "Jalen Wydermyer", position: "TE", fppg: 8.5 },
    { name: "2020 Texas A&M Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Kentucky", year: 2021, players: [
    { name: "Will Levis", position: "QB", fppg: 24.5 },
    { name: "Chris Rodriguez Jr.", position: "RB", fppg: 18.0 },
    { name: "Wan'Dale Robinson", position: "WR", fppg: 9.5 },
    { name: "Josh Ali", position: "WR", fppg: 13.0 },
    { name: "2021 Kentucky Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Kentucky", year: 2018, players: [
    { name: "Terry Wilson", position: "QB", fppg: 22.5 },
    { name: "Benny Snell Jr.", position: "RB", fppg: 14.5 },
    { name: "Lynn Bowden Jr.", position: "WR", fppg: 11.0 },
    { name: "C.J. Conrad", position: "TE", fppg: 6.5 },
    { name: "2018 Kentucky Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Kentucky", year: 2006, players: [
    { name: "Andre Woodson", position: "QB", fppg: 20.5 },
    { name: "Rafael Little", position: "RB", fppg: 16.0 },
    { name: "Keenan Burton", position: "WR", fppg: 13.5 },
    { name: "Jacob Tamme", position: "TE", fppg: 9.0 },
    { name: "2006 Kentucky Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Colorado", year: 1994, players: [
    { name: "Kordell Stewart", position: "QB", fppg: 23.5 },
    { name: "Rashaan Salaam", position: "RB", fppg: 15.5 },
    { name: "Michael Westbrook", position: "WR", fppg: 13.5 },
    { name: "Charles E. Johnson", position: "WR", fppg: 10.0 },
    { name: "1994 Colorado Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Colorado", year: 1990, players: [
    { name: "Darian Hagan", position: "QB", fppg: 25.5 },
    { name: "Eric Bieniemy", position: "RB", fppg: 18.0 },
    { name: "Mike Pritchard", position: "WR", fppg: 11.0 },
    { name: "Jeff Campbell", position: "WR", fppg: 10.0 },
    { name: "1990 Colorado Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Colorado", year: 2001, players: [
    { name: "Craig Ochs", position: "QB", fppg: 21.5 },
    { name: "Chris Brown", position: "RB", fppg: 17.5 },
    { name: "Javon Green", position: "WR", fppg: 9.0 },
    { name: "Derek McCoy", position: "WR", fppg: 11.5 },
    { name: "2001 Colorado Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "BYU", year: 1996, players: [
    { name: "Steve Sarkisian", position: "QB", fppg: 20.5 },
    { name: "Ronney Jenkins", position: "RB", fppg: 14.0 },
    { name: "Chad Lewis", position: "TE", fppg: 9.0 },
    { name: "K.O. Kealaluhi", position: "WR", fppg: 12.0 },
    { name: "1996 BYU Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "BYU", year: 2001, players: [
    { name: "Brandon Doman", position: "QB", fppg: 23.0 },
    { name: "Luke Staley", position: "RB", fppg: 18.0 },
    { name: "Reno Mahe", position: "WR", fppg: 11.0 },
    { name: "Doug Jolley", position: "TE", fppg: 8.0 },
    { name: "2001 BYU Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "BYU", year: 2006, players: [
    { name: "John Beck", position: "QB", fppg: 25.0 },
    { name: "Curtis Brown", position: "RB", fppg: 17.5 },
    { name: "Jonny Harline", position: "WR", fppg: 12.0 },
    { name: "Dennis Pitta", position: "TE", fppg: 6.5 },
    { name: "2006 BYU Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Syracuse", year: 1998, players: [
    { name: "Donovan McNabb", position: "QB", fppg: 21.5 },
    { name: "Rob Konrad", position: "RB", fppg: 17.5 },
    { name: "Kevin Johnson", position: "WR", fppg: 9.5 },
    { name: "Quinton Spotwood", position: "WR", fppg: 12.0 },
    { name: "1998 Syracuse Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Syracuse", year: 1996, players: [
    { name: "Donovan McNabb", position: "QB", fppg: 23.5 },
    { name: "Malcolm Thomas", position: "RB", fppg: 14.0 },
    { name: "Marvin Harrison", position: "WR", fppg: 11.0 },
    { name: "Steve Marino", position: "WR", fppg: 10.0 },
    { name: "1996 Syracuse Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Syracuse", year: 2018, players: [
    { name: "Eric Dungey", position: "QB", fppg: 22.5 },
    { name: "Dontae Strickland", position: "RB", fppg: 16.0 },
    { name: "Jamal Custis", position: "WR", fppg: 10.0 },
    { name: "Ravian Pierce", position: "WR", fppg: 13.5 },
    { name: "2018 Syracuse Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Michigan State", year: 2015, players: [
    { name: "Connor Cook", position: "QB", fppg: 23.5 },
    { name: "L.J. Scott", position: "RB", fppg: 18.0 },
    { name: "Aaron Burbridge", position: "WR", fppg: 11.5 },
    { name: "Josiah Price", position: "TE", fppg: 9.5 },
    { name: "2015 Michigan State Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Michigan State", year: 2013, players: [
    { name: "Connor Cook", position: "QB", fppg: 23.0 },
    { name: "Jeremy Langford", position: "RB", fppg: 16.5 },
    { name: "Tony Lippett", position: "WR", fppg: 10.5 },
    { name: "Josiah Price", position: "TE", fppg: 5.5 },
    { name: "2013 Michigan State Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Michigan State", year: 1999, players: [
    { name: "Bill Burke", position: "QB", fppg: 22.5 },
    { name: "Sedrick Irvin", position: "RB", fppg: 15.5 },
    { name: "Plaxico Burress", position: "WR", fppg: 11.0 },
    { name: "Aaron Turner", position: "WR", fppg: 9.5 },
    { name: "1999 Michigan State Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Iowa State", year: 2020, players: [
    { name: "Brock Purdy", position: "QB", fppg: 20.5 },
    { name: "Breece Hall", position: "RB", fppg: 17.0 },
    { name: "Charlie Kolar", position: "TE", fppg: 6.5 },
    { name: "Tarique Milton", position: "WR", fppg: 12.5 },
    { name: "2020 Iowa State Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Iowa State", year: 2021, players: [
    { name: "Brock Purdy", position: "QB", fppg: 21.5 },
    { name: "Breece Hall", position: "RB", fppg: 15.0 },
    { name: "Xavier Hutchinson", position: "WR", fppg: 11.5 },
    { name: "Charlie Kolar", position: "TE", fppg: 9.0 },
    { name: "2021 Iowa State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Iowa State", year: 2000, players: [
    { name: "Sage Rosenfels", position: "QB", fppg: 25.0 },
    { name: "Ennis Haywood", position: "RB", fppg: 14.5 },
    { name: "Lane Danielsen", position: "WR", fppg: 11.0 },
    { name: "Marcus Robinson", position: "WR", fppg: 9.5 },
    { name: "2000 Iowa State Defense", position: "DEF", fppg: 3.5 }
  ]},
  { team: "Wake Forest", year: 2006, players: [
    { name: "Riley Skinner", position: "QB", fppg: 24.0 },
    { name: "Chris Barclay", position: "RB", fppg: 18.5 },
    { name: "Kenneth Moore", position: "WR", fppg: 11.5 },
    { name: "Jason Anderson", position: "TE", fppg: 6.0 },
    { name: "2006 Wake Forest Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Wake Forest", year: 2021, players: [
    { name: "Sam Hartman", position: "QB", fppg: 22.0 },
    { name: "Christian Beal-Smith", position: "RB", fppg: 15.5 },
    { name: "A.T. Perry", position: "WR", fppg: 13.5 },
    { name: "Jahmal Banks", position: "WR", fppg: 11.0 },
    { name: "2021 Wake Forest Defense", position: "DEF", fppg: 3.0 }
  ]},
  { team: "Wake Forest", year: 2008, players: [
    { name: "Riley Skinner", position: "QB", fppg: 23.5 },
    { name: "Josh Adams", position: "RB", fppg: 14.0 },
    { name: "Kenneth Moore", position: "WR", fppg: 10.0 },
    { name: "Chip Vaughn", position: "WR", fppg: 9.5 },
    { name: "2008 Wake Forest Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Duke", year: 2013, players: [
    { name: "Anthony Boone", position: "QB", fppg: 25.0 },
    { name: "Jela Duncan", position: "RB", fppg: 15.5 },
    { name: "Jamison Crowder", position: "WR", fppg: 11.5 },
    { name: "Braxton Deaver", position: "TE", fppg: 8.0 },
    { name: "2013 Duke Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Duke", year: 2014, players: [
    { name: "Anthony Boone", position: "QB", fppg: 24.0 },
    { name: "Shaquille Powell", position: "RB", fppg: 17.0 },
    { name: "Jamison Crowder", position: "WR", fppg: 13.5 },
    { name: "Braxton Deaver", position: "TE", fppg: 5.5 },
    { name: "2014 Duke Defense", position: "DEF", fppg: 3.0 }
  ]},
  { team: "Duke", year: 2018, players: [
    { name: "Daniel Jones", position: "QB", fppg: 21.0 },
    { name: "Brittain Brown", position: "RB", fppg: 18.0 },
    { name: "T.J. Rahming", position: "WR", fppg: 11.0 },
    { name: "Davis Koppenhaver", position: "WR", fppg: 11.0 },
    { name: "2018 Duke Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Northwestern", year: 1995, players: [
    { name: "Steve Schnur", position: "QB", fppg: 23.5 },
    { name: "Darnell Autry", position: "RB", fppg: 16.5 },
    { name: "D'Wayne Bates", position: "WR", fppg: 13.5 },
    { name: "Matt Hartl", position: "TE", fppg: 7.5 },
    { name: "1995 Northwestern Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Northwestern", year: 2000, players: [
    { name: "Zak Kustok", position: "QB", fppg: 25.0 },
    { name: "Damien Anderson", position: "RB", fppg: 17.0 },
    { name: "Sam Simmons", position: "WR", fppg: 13.5 },
    { name: "Kunle Patrick", position: "WR", fppg: 12.0 },
    { name: "2000 Northwestern Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Northwestern", year: 2018, players: [
    { name: "Clayton Thorson", position: "QB", fppg: 21.5 },
    { name: "Jeremy Larkin", position: "RB", fppg: 15.0 },
    { name: "Flynn Nagel", position: "WR", fppg: 12.0 },
    { name: "Bennett Skowronek", position: "WR", fppg: 9.0 },
    { name: "2018 Northwestern Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Purdue", year: 2000, players: [
    { name: "Drew Brees", position: "QB", fppg: 20.5 },
    { name: "Montrell Lowe", position: "RB", fppg: 16.0 },
    { name: "Vinny Sutherland", position: "WR", fppg: 10.0 },
    { name: "Seth Morales", position: "WR", fppg: 12.5 },
    { name: "2000 Purdue Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Purdue", year: 2007, players: [
    { name: "Curtis Painter", position: "QB", fppg: 23.5 },
    { name: "Kory Sheets", position: "RB", fppg: 16.5 },
    { name: "Dorien Bryant", position: "WR", fppg: 9.5 },
    { name: "Greg Orton", position: "WR", fppg: 13.5 },
    { name: "2007 Purdue Defense", position: "DEF", fppg: 3.5 }
  ]},
  { team: "Purdue", year: 2018, players: [
    { name: "David Blough", position: "QB", fppg: 23.0 },
    { name: "D.J. Knox", position: "RB", fppg: 14.5 },
    { name: "Rondale Moore", position: "WR", fppg: 10.0 },
    { name: "Isaac Zico", position: "TE", fppg: 9.5 },
    { name: "2018 Purdue Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Georgia Tech", year: 2009, players: [
    { name: "Josh Nesbitt", position: "QB", fppg: 24.0 },
    { name: "Jonathan Dwyer", position: "RB", fppg: 14.5 },
    { name: "Demaryius Thomas", position: "WR", fppg: 9.5 },
    { name: "Roddy Jones", position: "RB", fppg: 14.0 },
    { name: "2009 Georgia Tech Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Georgia Tech", year: 1998, players: [
    { name: "Joe Hamilton", position: "QB", fppg: 21.0 },
    { name: "Joe Burns", position: "RB", fppg: 17.5 },
    { name: "Dez White", position: "WR", fppg: 11.5 },
    { name: "Kelly Campbell", position: "WR", fppg: 10.0 },
    { name: "1998 Georgia Tech Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Georgia Tech", year: 2014, players: [
    { name: "Justin Thomas", position: "QB", fppg: 25.0 },
    { name: "Synjyn Days", position: "RB", fppg: 14.0 },
    { name: "DeAndre Smelter", position: "WR", fppg: 10.0 },
    { name: "Ryan Chamberlain", position: "WR", fppg: 10.5 },
    { name: "2014 Georgia Tech Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Virginia", year: 2019, players: [
    { name: "Bryce Perkins", position: "QB", fppg: 25.0 },
    { name: "Wayne Taulapapa", position: "RB", fppg: 18.0 },
    { name: "Joe Reed", position: "WR", fppg: 11.5 },
    { name: "Hasise Dubois", position: "WR", fppg: 12.0 },
    { name: "2019 Virginia Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Virginia", year: 1995, players: [
    { name: "Mike Groh", position: "QB", fppg: 21.0 },
    { name: "Tiki Barber", position: "RB", fppg: 16.0 },
    { name: "Symmion Willis", position: "WR", fppg: 10.0 },
    { name: "Patrick Kerney", position: "TE", fppg: 9.0 },
    { name: "1995 Virginia Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Virginia", year: 2004, players: [
    { name: "Marques Hagans", position: "QB", fppg: 25.0 },
    { name: "Wali Lundy", position: "RB", fppg: 16.0 },
    { name: "Michael McGrew", position: "WR", fppg: 9.5 },
    { name: "Heath Miller", position: "TE", fppg: 6.0 },
    { name: "2004 Virginia Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "South Carolina", year: 2012, players: [
    { name: "Connor Shaw", position: "QB", fppg: 23.0 },
    { name: "Marcus Lattimore", position: "RB", fppg: 18.0 },
    { name: "Ace Sanders", position: "WR", fppg: 9.5 },
    { name: "Bruce Ellington", position: "WR", fppg: 11.5 },
    { name: "2012 South Carolina Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "South Carolina", year: 2013, players: [
    { name: "Connor Shaw", position: "QB", fppg: 21.5 },
    { name: "Mike Davis", position: "RB", fppg: 17.0 },
    { name: "Bruce Ellington", position: "WR", fppg: 11.5 },
    { name: "Shaq Roland", position: "WR", fppg: 11.5 },
    { name: "2013 South Carolina Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "South Carolina", year: 2010, players: [
    { name: "Stephen Garcia", position: "QB", fppg: 25.0 },
    { name: "Marcus Lattimore", position: "RB", fppg: 14.0 },
    { name: "Alshon Jeffery", position: "WR", fppg: 10.0 },
    { name: "Ace Sanders", position: "WR", fppg: 13.5 },
    { name: "2010 South Carolina Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Mississippi State", year: 2014, players: [
    { name: "Dak Prescott", position: "QB", fppg: 23.0 },
    { name: "Josh Robinson", position: "RB", fppg: 15.5 },
    { name: "De'Runnya Wilson", position: "WR", fppg: 12.0 },
    { name: "Fred Ross", position: "WR", fppg: 9.5 },
    { name: "2014 Mississippi State Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Mississippi State", year: 2017, players: [
    { name: "Nick Fitzgerald", position: "QB", fppg: 22.5 },
    { name: "Aeris Williams", position: "RB", fppg: 14.0 },
    { name: "Donald Gray", position: "WR", fppg: 12.5 },
    { name: "Jesse Jackson", position: "TE", fppg: 8.0 },
    { name: "2017 Mississippi State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Mississippi State", year: 1999, players: [
    { name: "Wayne Madkin", position: "QB", fppg: 21.0 },
    { name: "Dicenzo Miller", position: "RB", fppg: 14.0 },
    { name: "Kevin Roberson", position: "WR", fppg: 11.0 },
    { name: "Chris Cosh", position: "WR", fppg: 14.0 },
    { name: "1999 Mississippi State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Missouri", year: 2013, players: [
    { name: "James Franklin", position: "QB", fppg: 23.5 },
    { name: "Henry Josey", position: "RB", fppg: 13.5 },
    { name: "L'Damian Washington", position: "WR", fppg: 12.0 },
    { name: "Dorial Green-Beckham", position: "WR", fppg: 12.5 },
    { name: "2013 Missouri Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Missouri", year: 2014, players: [
    { name: "Maty Mauk", position: "QB", fppg: 22.0 },
    { name: "Russell Hansbrough", position: "RB", fppg: 16.0 },
    { name: "Bud Sasser", position: "WR", fppg: 13.0 },
    { name: "Jimmie Hunt", position: "WR", fppg: 9.5 },
    { name: "2014 Missouri Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Missouri", year: 2007, players: [
    { name: "Chase Daniel", position: "QB", fppg: 21.0 },
    { name: "Tony Temple", position: "RB", fppg: 15.5 },
    { name: "Jeremy Maclin", position: "WR", fppg: 10.5 },
    { name: "Martin Rucker", position: "TE", fppg: 6.5 },
    { name: "2007 Missouri Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Vanderbilt", year: 2024, players: [
    { name: "Diego Pavia", position: "QB", fppg: 24.5 },
    { name: "Sedrick Alexander", position: "RB", fppg: 18.5 },
    { name: "Eli Stowers", position: "TE", fppg: 7.0 },
    { name: "London Humphreys", position: "WR", fppg: 11.5 },
    { name: "2024 Vanderbilt Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Vanderbilt", year: 2013, players: [
    { name: "Patton Robinette", position: "QB", fppg: 22.5 },
    { name: "Jerron Seymour", position: "RB", fppg: 15.5 },
    { name: "Jordan Matthews", position: "WR", fppg: 13.5 },
    { name: "Josh Grady", position: "WR", fppg: 10.0 },
    { name: "2013 Vanderbilt Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Vanderbilt", year: 2008, players: [
    { name: "Chris Nickson", position: "QB", fppg: 21.5 },
    { name: "Jeff Jennings", position: "RB", fppg: 14.5 },
    { name: "Earl Bennett", position: "WR", fppg: 13.5 },
    { name: "Sean Walker", position: "WR", fppg: 14.0 },
    { name: "2008 Vanderbilt Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Illinois", year: 1990, players: [
    { name: "Jason Verduzco", position: "QB", fppg: 22.0 },
    { name: "Howard Griffith", position: "RB", fppg: 18.5 },
    { name: "Shawn Wax", position: "WR", fppg: 13.0 },
    { name: "Ryan Wetnight", position: "TE", fppg: 8.5 },
    { name: "1990 Illinois Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Illinois", year: 2001, players: [
    { name: "Kurt Kittner", position: "QB", fppg: 20.5 },
    { name: "Rocky Harvey", position: "RB", fppg: 17.0 },
    { name: "Brandon Lloyd", position: "WR", fppg: 11.0 },
    { name: "Camp Cameron", position: "TE", fppg: 9.0 },
    { name: "2001 Illinois Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Illinois", year: 2007, players: [
    { name: "Juice Williams", position: "QB", fppg: 21.0 },
    { name: "Rashard Mendenhall", position: "RB", fppg: 17.5 },
    { name: "Rejus Benn", position: "WR", fppg: 13.0 },
    { name: "Jacob Willis", position: "TE", fppg: 6.5 },
    { name: "2007 Illinois Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Indiana", year: 1991, players: [
    { name: "Trent Green", position: "QB", fppg: 21.0 },
    { name: "Vaughn Dunbar", position: "RB", fppg: 18.5 },
    { name: "Thomas Lewis", position: "WR", fppg: 13.5 },
    { name: "Blake Faust", position: "WR", fppg: 14.0 },
    { name: "1991 Indiana Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Indiana", year: 2020, players: [
    { name: "Michael Penix Jr.", position: "QB", fppg: 22.0 },
    { name: "Stevie Scott III", position: "RB", fppg: 17.0 },
    { name: "Whop Philyor", position: "WR", fppg: 12.0 },
    { name: "Peyton Hendershot", position: "TE", fppg: 6.0 },
    { name: "2020 Indiana Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Indiana", year: 2024, players: [
    { name: "Kurtis Rourke", position: "QB", fppg: 21.5 },
    { name: "Justice Ellison", position: "RB", fppg: 17.0 },
    { name: "Elijah Sarratt", position: "WR", fppg: 9.5 },
    { name: "Andrew Wilson-Lamp", position: "WR", fppg: 12.5 },
    { name: "2024 Indiana Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Maryland", year: 2001, players: [
    { name: "Shaun Hill", position: "QB", fppg: 22.5 },
    { name: "Bruce Perry", position: "RB", fppg: 18.0 },
    { name: "Guilian Gary", position: "WR", fppg: 10.0 },
    { name: "Latrez Harrison", position: "WR", fppg: 10.5 },
    { name: "2001 Maryland Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Maryland", year: 2010, players: [
    { name: "Danny O'Brien", position: "QB", fppg: 23.5 },
    { name: "Da'Rel Scott", position: "RB", fppg: 18.0 },
    { name: "Torrey Smith", position: "WR", fppg: 9.5 },
    { name: "Quintin McCree", position: "WR", fppg: 11.5 },
    { name: "2010 Maryland Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Maryland", year: 2014, players: [
    { name: "C.J. Brown", position: "QB", fppg: 23.5 },
    { name: "Brandon Ross", position: "RB", fppg: 18.0 },
    { name: "Stefon Diggs", position: "WR", fppg: 12.0 },
    { name: "Deon Long", position: "WR", fppg: 10.0 },
    { name: "2014 Maryland Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Minnesota", year: 2019, players: [
    { name: "Tanner Morgan", position: "QB", fppg: 24.0 },
    { name: "Rodney Smith", position: "RB", fppg: 14.5 },
    { name: "Rashod Bateman", position: "WR", fppg: 10.0 },
    { name: "Tyler Johnson", position: "WR", fppg: 10.0 },
    { name: "2019 Minnesota Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Minnesota", year: 2003, players: [
    { name: "Asad Abdul-Khaliq", position: "QB", fppg: 25.0 },
    { name: "Marion Barber III", position: "RB", fppg: 16.0 },
    { name: "Ron Johnson", position: "WR", fppg: 10.0 },
    { name: "Ben Utecht", position: "TE", fppg: 8.0 },
    { name: "2003 Minnesota Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Minnesota", year: 2016, players: [
    { name: "Mitch Leidner", position: "QB", fppg: 24.5 },
    { name: "Rodney Smith", position: "RB", fppg: 15.5 },
    { name: "Drew Wolitarsky", position: "WR", fppg: 13.5 },
    { name: "Duke Anyanwu", position: "TE", fppg: 8.5 },
    { name: "2016 Minnesota Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Rutgers", year: 2006, players: [
    { name: "Mike Teel", position: "QB", fppg: 24.5 },
    { name: "Ray Rice", position: "RB", fppg: 14.0 },
    { name: "Tiquan Underwood", position: "WR", fppg: 10.0 },
    { name: "Clark Harris", position: "TE", fppg: 9.0 },
    { name: "2006 Rutgers Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Rutgers", year: 2012, players: [
    { name: "Gary Nova", position: "QB", fppg: 23.5 },
    { name: "Jawan Jamison", position: "RB", fppg: 16.5 },
    { name: "Mark Harrison", position: "WR", fppg: 11.5 },
    { name: "D.C. Jefferson", position: "TE", fppg: 8.0 },
    { name: "2012 Rutgers Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Rutgers", year: 2014, players: [
    { name: "Gary Nova", position: "QB", fppg: 23.0 },
    { name: "Paul James", position: "RB", fppg: 15.5 },
    { name: "Leonte Carroo", position: "WR", fppg: 13.5 },
    { name: "Tyler Kroft", position: "TE", fppg: 7.5 },
    { name: "2014 Rutgers Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "UCLA", year: 1998, players: [
    { name: "Cade McNown", position: "QB", fppg: 22.0 },
    { name: "Skip Hicks", position: "RB", fppg: 13.5 },
    { name: "Danny Farmer", position: "WR", fppg: 13.5 },
    { name: "Bob Kratch", position: "WR", fppg: 12.5 },
    { name: "1998 UCLA Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "UCLA", year: 2005, players: [
    { name: "Drew Olson", position: "QB", fppg: 24.0 },
    { name: "Maurice Jones-Drew", position: "RB", fppg: 19.0 },
    { name: "Marcedes Lewis", position: "TE", fppg: 7.5 },
    { name: "Junior Taylor", position: "WR", fppg: 11.5 },
    { name: "2005 UCLA Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "UCLA", year: 2023, players: [
    { name: "Ethan Garbers", position: "QB", fppg: 24.0 },
    { name: "TJ Harden", position: "RB", fppg: 15.0 },
    { name: "J.Michael Sturdivant", position: "WR", fppg: 10.5 },
    { name: "Carsen Ryan", position: "TE", fppg: 9.5 },
    { name: "2023 UCLA Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Arizona", year: 1998, players: [
    { name: "Ortege Jenkins", position: "QB", fppg: 23.5 },
    { name: "Trung Canidate", position: "RB", fppg: 19.0 },
    { name: "Dennis Northcutt", position: "WR", fppg: 11.0 },
    { name: "Brice McCray", position: "WR", fppg: 9.5 },
    { name: "1998 Arizona Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Arizona", year: 2014, players: [
    { name: "Anu Solomon", position: "QB", fppg: 22.0 },
    { name: "Nick Wilson", position: "RB", fppg: 16.0 },
    { name: "Austin Hill", position: "WR", fppg: 10.5 },
    { name: "Trey Griffey", position: "WR", fppg: 12.0 },
    { name: "2014 Arizona Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Arizona", year: 2023, players: [
    { name: "Noah Fifita", position: "QB", fppg: 22.0 },
    { name: "Michael Wiley", position: "RB", fppg: 14.5 },
    { name: "Tetairoa McMillan", position: "WR", fppg: 12.0 },
    { name: "Tanner McLachlan", position: "TE", fppg: 9.0 },
    { name: "2023 Arizona Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Arizona State", year: 1996, players: [
    { name: "Jake Plummer", position: "QB", fppg: 22.5 },
    { name: "Michael Martin", position: "RB", fppg: 15.5 },
    { name: "Keith Poole", position: "WR", fppg: 9.5 },
    { name: "Lorenzo Style", position: "WR", fppg: 12.0 },
    { name: "1996 Arizona State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Arizona State", year: 2007, players: [
    { name: "Rudy Carpenter", position: "QB", fppg: 24.5 },
    { name: "Ryan Torain", position: "RB", fppg: 15.0 },
    { name: "Chris McGaha", position: "WR", fppg: 11.5 },
    { name: "Michael Jones", position: "WR", fppg: 10.5 },
    { name: "2007 Arizona State Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Arizona State", year: 2024, players: [
    { name: "Sam Leavitt", position: "QB", fppg: 20.5 },
    { name: "Cam Skattebo", position: "RB", fppg: 18.0 },
    { name: "Jordyn Tyson", position: "WR", fppg: 13.5 },
    { name: "Kyson Brown", position: "TE", fppg: 8.5 },
    { name: "2024 Arizona State Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Houston", year: 2011, players: [
    { name: "Case Keenum", position: "QB", fppg: 24.5 },
    { name: "Charles Sims", position: "RB", fppg: 18.5 },
    { name: "Patrick Edwards", position: "WR", fppg: 13.0 },
    { name: "Tyron Carrier", position: "WR", fppg: 12.5 },
    { name: "2011 Houston Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Houston", year: 2015, players: [
    { name: "Greg Ward Jr.", position: "QB", fppg: 22.0 },
    { name: "Kenneth Farrow", position: "RB", fppg: 16.0 },
    { name: "Demarcus Ayers", position: "WR", fppg: 11.5 },
    { name: "Tyus Bowser", position: "WR", fppg: 11.0 },
    { name: "2015 Houston Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Houston", year: 2021, players: [
    { name: "Clayton Tune", position: "QB", fppg: 21.5 },
    { name: "Alton McCaskill", position: "RB", fppg: 18.5 },
    { name: "Nathaniel Dell", position: "WR", fppg: 14.0 },
    { name: "Christian Trahan", position: "TE", fppg: 9.5 },
    { name: "2021 Houston Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Kansas", year: 2007, players: [
    { name: "Todd Reesing", position: "QB", fppg: 24.5 },
    { name: "Jake Sharp", position: "RB", fppg: 17.5 },
    { name: "Marcus Henry", position: "WR", fppg: 11.0 },
    { name: "Dezmon Briscoe", position: "WR", fppg: 12.5 },
    { name: "2007 Kansas Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "Kansas", year: 2008, players: [
    { name: "Todd Reesing", position: "QB", fppg: 23.0 },
    { name: "Jake Sharp", position: "RB", fppg: 18.0 },
    { name: "Dezmon Briscoe", position: "WR", fppg: 13.0 },
    { name: "Kerry Meier", position: "WR", fppg: 9.0 },
    { name: "2008 Kansas Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Kansas", year: 2023, players: [
    { name: "Jalon Daniels", position: "QB", fppg: 22.0 },
    { name: "Devin Neal", position: "RB", fppg: 16.5 },
    { name: "Luke Grimm", position: "WR", fppg: 14.0 },
    { name: "Mason Fairchild", position: "TE", fppg: 8.0 },
    { name: "2023 Kansas Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Texas Tech", year: 2008, players: [
    { name: "Graham Harrell", position: "QB", fppg: 22.5 },
    { name: "Baron Batch", position: "RB", fppg: 14.0 },
    { name: "Michael Crabtree", position: "WR", fppg: 13.0 },
    { name: "Edward Britton", position: "WR", fppg: 11.5 },
    { name: "2008 Texas Tech Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Texas Tech", year: 2013, players: [
    { name: "Davis Webb", position: "QB", fppg: 22.0 },
    { name: "Kenny Williams", position: "RB", fppg: 15.5 },
    { name: "Eric Ward", position: "WR", fppg: 9.0 },
    { name: "Jace Amaro", position: "TE", fppg: 6.5 },
    { name: "2013 Texas Tech Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Texas Tech", year: 2024, players: [
    { name: "Behren Morton", position: "QB", fppg: 24.5 },
    { name: "Tahj Brooks", position: "RB", fppg: 18.5 },
    { name: "Josh Kelly", position: "WR", fppg: 10.5 },
    { name: "Baylor Cupp", position: "TE", fppg: 6.0 },
    { name: "2024 Texas Tech Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Boston College", year: 1993, players: [
    { name: "Glenn Foley", position: "QB", fppg: 22.0 },
    { name: "Marc Edwards", position: "RB", fppg: 15.0 },
    { name: "Ivy Joe Hunter", position: "WR", fppg: 11.0 },
    { name: "Pete Mitchell", position: "TE", fppg: 9.0 },
    { name: "1993 Boston College Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Boston College", year: 2007, players: [
    { name: "Matt Ryan", position: "QB", fppg: 23.0 },
    { name: "Andre Callender", position: "RB", fppg: 16.5 },
    { name: "Rich Gunnell", position: "WR", fppg: 10.0 },
    { name: "Ryan Purvis", position: "WR", fppg: 12.5 },
    { name: "2007 Boston College Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "Boston College", year: 2004, players: [
    { name: "Paul Peterson", position: "QB", fppg: 22.5 },
    { name: "Derrick Knight", position: "RB", fppg: 14.5 },
    { name: "Ryan Purvis", position: "WR", fppg: 11.5 },
    { name: "Kevin Challenger", position: "TE", fppg: 6.5 },
    { name: "2004 Boston College Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "California", year: 2004, players: [
    { name: "Aaron Rodgers", position: "QB", fppg: 21.5 },
    { name: "J.J. Arrington", position: "RB", fppg: 15.0 },
    { name: "Geoff McArthur", position: "WR", fppg: 10.0 },
    { name: "Garrett Cross", position: "TE", fppg: 7.0 },
    { name: "2004 California Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "California", year: 2006, players: [
    { name: "Nate Longshore", position: "QB", fppg: 20.5 },
    { name: "Marshawn Lynch", position: "RB", fppg: 15.0 },
    { name: "DeSean Jackson", position: "WR", fppg: 13.0 },
    { name: "Craig Stevens", position: "TE", fppg: 6.5 },
    { name: "2006 California Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "California", year: 2009, players: [
    { name: "Kevin Riley", position: "QB", fppg: 22.0 },
    { name: "Jahvid Best", position: "RB", fppg: 14.0 },
    { name: "Verran Tucker", position: "WR", fppg: 12.5 },
    { name: "Cameron Jordan", position: "WR", fppg: 14.0 },
    { name: "2009 California Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "NC State", year: 2002, players: [
    { name: "Philip Rivers", position: "QB", fppg: 24.0 },
    { name: "T.A. McLendon", position: "RB", fppg: 15.0 },
    { name: "Jerricho Cotchery", position: "WR", fppg: 14.0 },
    { name: "Matt Lougee", position: "TE", fppg: 7.5 },
    { name: "2002 NC State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "NC State", year: 2010, players: [
    { name: "Russell Wilson", position: "QB", fppg: 21.0 },
    { name: "Mustafa Greene", position: "RB", fppg: 18.5 },
    { name: "Owen Spencer", position: "WR", fppg: 14.0 },
    { name: "George Bryan", position: "TE", fppg: 8.0 },
    { name: "2010 NC State Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "NC State", year: 2017, players: [
    { name: "Ryan Finley", position: "QB", fppg: 22.5 },
    { name: "Nyheim Hines", position: "RB", fppg: 17.0 },
    { name: "Jaylen Samuels", position: "WR", fppg: 12.0 },
    { name: "Jaylen Samuels", position: "TE", fppg: 8.0 },
    { name: "2017 NC State Defense", position: "DEF", fppg: 6.0 }
  ]},
  { team: "North Carolina", year: 1997, players: [
    { name: "Chris Keldorf", position: "QB", fppg: 24.5 },
    { name: "Jonathan Linton", position: "RB", fppg: 13.5 },
    { name: "Na Brown", position: "WR", fppg: 10.0 },
    { name: "Alge Crumpler", position: "TE", fppg: 7.5 },
    { name: "1997 North Carolina Defense", position: "DEF", fppg: 6.5 }
  ]},
  { team: "North Carolina", year: 2015, players: [
    { name: "Marquise Williams", position: "QB", fppg: 22.0 },
    { name: "Elijah Hood", position: "RB", fppg: 15.5 },
    { name: "Ryan Switzer", position: "WR", fppg: 12.5 },
    { name: "Bug Howard", position: "WR", fppg: 12.5 },
    { name: "2015 North Carolina Defense", position: "DEF", fppg: 3.0 }
  ]},
  { team: "North Carolina", year: 2022, players: [
    { name: "Drake Maye", position: "QB", fppg: 23.0 },
    { name: "British Brooks", position: "RB", fppg: 18.0 },
    { name: "Josh Downs", position: "WR", fppg: 14.0 },
    { name: "Bryson Nesbit", position: "TE", fppg: 6.0 },
    { name: "2022 North Carolina Defense", position: "DEF", fppg: 3.0 }
  ]},
  { team: "Pitt", year: 2003, players: [
    { name: "Rod Rutherford", position: "QB", fppg: 22.5 },
    { name: "Brandon Miree", position: "RB", fppg: 16.5 },
    { name: "Larry Fitzgerald", position: "WR", fppg: 13.0 },
    { name: "Erik Gill", position: "WR", fppg: 9.0 },
    { name: "2003 Pitt Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "Pitt", year: 2009, players: [
    { name: "Bill Stull", position: "QB", fppg: 24.5 },
    { name: "LeSean McCoy", position: "RB", fppg: 14.5 },
    { name: "Jonathan Baldwin", position: "WR", fppg: 11.0 },
    { name: "Dorin Dickerson", position: "TE", fppg: 5.5 },
    { name: "2009 Pitt Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "Pitt", year: 2021, players: [
    { name: "Kenny Pickett", position: "QB", fppg: 27.5 },
    { name: "Israel Abanikanda", position: "RB", fppg: 17.5 },
    { name: "Jordan Addison", position: "WR", fppg: 10.5 },
    { name: "Lucas Krull", position: "TE", fppg: 8.5 },
    { name: "2021 Pitt Defense", position: "DEF", fppg: 5.0 }
  ]},
  { team: "SMU", year: 2019, players: [
    { name: "Shane Buechele", position: "QB", fppg: 25.0 },
    { name: "Xavier Jones", position: "RB", fppg: 13.5 },
    { name: "James Proche", position: "WR", fppg: 11.0 },
    { name: "Kylen Granson", position: "TE", fppg: 6.0 },
    { name: "2019 SMU Defense", position: "DEF", fppg: 4.5 }
  ]},
  { team: "SMU", year: 2021, players: [
    { name: "Tanner Mordecai", position: "QB", fppg: 21.0 },
    { name: "Ulysses Bentley IV", position: "RB", fppg: 15.5 },
    { name: "Rashee Rice", position: "WR", fppg: 13.0 },
    { name: "Grant Calcaterra", position: "TE", fppg: 7.0 },
    { name: "2021 SMU Defense", position: "DEF", fppg: 3.5 }
  ]},
  { team: "SMU", year: 2024, players: [
    { name: "Kevin Jennings", position: "QB", fppg: 22.0 },
    { name: "Brashard Smith", position: "RB", fppg: 16.0 },
    { name: "Jordan Kerley", position: "WR", fppg: 12.0 },
    { name: "RJ Maryland", position: "TE", fppg: 6.0 },
    { name: "2024 SMU Defense", position: "DEF", fppg: 5.0 }
  ]}
];
