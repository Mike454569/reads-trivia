// College Football Immaculate Grid mode data.
//
// CFB_GRID_PLAYERS: consensus All-America selections (1889-2025) aggregated by
// player, built from the user's CFB_Trivia_Cheat_Code-11.xlsx AllAmerica_Sample_Rosters
// and Heisman_Winners tabs. Pool is filtered to players tied to one of the original 24
// most-decorated programs (by All-America count) plus every Heisman winner, so criteria
// intersections stay dense enough to reliably deal a solvable 3x3 grid. A later pass added
// 9 more schools (Florida, Auburn, Texas A&M, Florida State, Oklahoma State, TCU, Colorado,
// Oregon, Miami (FL)) plus 21 new players — several of these schools already had players in
// the pool via the "every Heisman winner" rule but no school badge/criteria to match them
// against (e.g. Bo Jackson/Auburn, Charlie Ward/Florida State), so this mostly unlocks
// combinations that were already latent in the data. Also fixed two pre-existing bugs where
// Vinny Testaverde and Gino Torretta (both Miami Heisman winners) had empty schools arrays.
//
// No real team logos are used for school badges (same reasoning as the NFL grid's
// colored-badge approach) — each school gets a colored text badge in its real team
// colors instead of a trademarked logo image.
//
// Shape of a player entry:
// { name, schools: [consensus-AA schools], positions: [position groups: QB/RB/WR/TE/OL/DL/LB/DB],
//   years: [selection years], heisman: bool, multiAA: bool (2+ selections), natChamp: bool,
//   hof: bool (Pro Football Hall of Fame), awards: [optional, e.g. "Outland Trophy"],
//   draftRound: optional number (only ever 1 currently — high-confidence subset only) }
//
// CFB_GRID_SCHOOL_CONFERENCE: current (post-2024-realignment) conference per school, drives
// the "conference" criteria. Notre Dame and Army are tagged Independent (football-only).
//
// A second, larger pass (using CFB_Trivia_Cheat_Code-13.xlsx's Major_Awards_By_Year sheet —
// complete year-by-year winner history for 17 major individual awards, back to each award's
// founding year) populated 'awards' comprehensively: 496 distinct award winners found, 187
// already existed in the pool and got enriched in place, 309 were brand-new additions (2 of
// which were mis-parsed co-winner-year rows like "Bennie Blades / Rickey Dixon" that got split
// back into 2 separate entries each). 15 of the new players' schools appeared often enough
// (4+ award winners) to justify adding as real badge schools — UCLA, Arkansas, NC State, Texas
// Tech, Arizona, BYU, Clemson, Boston College, Tennessee, Utah, Kansas State, Maryland, Baylor,
// Georgia Tech, Louisville — bringing the total to 48 schools / 938 players. A few school-name
// aliasing bugs surfaced and got fixed in the process ("USC"/"Southern Cal" → "Southern
// California", bare "Miami" → "Miami (FL)", "Pennsylvania" → "Penn" to match the existing
// badge strings). The remaining ~79 players are tied to schools with only 1-3 award winners —
// not worth a full badge/criteria addition, so they're valid data but currently unreachable
// via team-based row criteria (rows are always a school). Awards actually in use: Maxwell,
// Outland, Lombardi, Walter Camp, Davey O'Brien, Butkus, Jim Thorpe, Johnny Unitas Golden Arm,
// Doak Walker, Lou Groza, Bronko Nagurski, Chuck Bednarik, Fred Biletnikoff, Rimington, Ray
// Guy, John Mackey, and Ted Hendricks.
//
// Grid solvability: every criterion (team AND stat, not just era/awards) is now weighted by
// how many players it actually matches (see cfbGridWeightOf in app.js) rather than a crude
// per-type guess — this was necessary once the pool grew this much, since uniform-random row
// selection was regularly picking newly-added thin schools and tanking the perfect-grid rate
// (measured 65%→30% before this fix, back up to ~77% after, via simulation in this session).

window.CFB_GRID_SCHOOL_COLORS = {
  "Notre Dame": "#0C2340",
  "Yale": "#00356B",
  "Alabama": "#9E1B32",
  "Ohio State": "#BB0000",
  "Michigan": "#00274C",
  "Oklahoma": "#841617",
  "Southern California": "#990000",
  "Princeton": "#E77500",
  "Harvard": "#A51C30",
  "Nebraska": "#E41C38",
  "Pittsburgh": "#003594",
  "Texas": "#BF5700",
  "Minnesota": "#7A0019",
  "Penn State": "#041E42",
  "Army": "#231F20",
  "LSU": "#461D7C",
  "Stanford": "#8C1515",
  "Penn": "#011F5B",
  "Georgia": "#BA0C2F",
  "Illinois": "#13294B",
  "Wisconsin": "#C5050C",
  "Iowa": "#000000",
  "Michigan State": "#18453B",
  "Syracuse": "#D44500",
  "Florida": "#0021A5",
  "Auburn": "#0C2340",
  "Texas A&M": "#500000",
  "Florida State": "#782F40",
  "Oklahoma State": "#FF7300",
  "TCU": "#4D1979",
  "Colorado": "#CFB87C",
  "Oregon": "#154733",
  "Miami (FL)": "#F47321",
  "UCLA": "#2D68C4",
  "Arkansas": "#9D2235",
  "NC State": "#CC0000",
  "Texas Tech": "#CE0E2D",
  "Arizona": "#AB0520",
  "BYU": "#002E5D",
  "Clemson": "#F56600",
  "Boston College": "#98002E",
  "Tennessee": "#FF8200",
  "Utah": "#BE0000",
  "Kansas State": "#512888",
  "Maryland": "#E21833",
  "Baylor": "#154734",
  "Georgia Tech": "#003057",
  "Louisville": "#AD0000"
};

window.CFB_GRID_SCHOOL_CODES = {
  "Notre Dame": "ND",
  "Yale": "YALE",
  "Alabama": "ALA",
  "Ohio State": "OSU",
  "Michigan": "MICH",
  "Oklahoma": "OU",
  "Southern California": "USC",
  "Princeton": "PRIN",
  "Harvard": "HARV",
  "Nebraska": "NEB",
  "Pittsburgh": "PITT",
  "Texas": "TEX",
  "Minnesota": "MINN",
  "Penn State": "PSU",
  "Army": "ARMY",
  "LSU": "LSU",
  "Stanford": "STAN",
  "Penn": "PENN",
  "Georgia": "UGA",
  "Illinois": "ILL",
  "Wisconsin": "WISC",
  "Iowa": "IOWA",
  "Michigan State": "MSU",
  "Syracuse": "SYR",
  "Florida": "UF",
  "Auburn": "AUB",
  "Texas A&M": "TAMU",
  "Florida State": "FSU",
  "Oklahoma State": "OKST",
  "TCU": "TCU",
  "Colorado": "COLO",
  "Oregon": "ORE",
  "Miami (FL)": "MIA",
  "UCLA": "UCLA",
  "Arkansas": "ARK",
  "NC State": "NCST",
  "Texas Tech": "TTU",
  "Arizona": "ARIZ",
  "BYU": "BYU",
  "Clemson": "CLEM",
  "Boston College": "BC",
  "Tennessee": "TENN",
  "Utah": "UTAH",
  "Kansas State": "KST",
  "Maryland": "MD",
  "Baylor": "BAY",
  "Georgia Tech": "GT",
  "Louisville": "LOU"
};

// Conference affiliation per school (CURRENT, i.e. post-2024-realignment) — drives the
// "conference" grid criteria. Notre Dame and Army are historically football independents
// (Notre Dame remains one; Army joined the AAC in 2024 for other sports but still plays
// football as an independent), so they're tagged "Independent" rather than a conference.
window.CFB_GRID_SCHOOL_CONFERENCE = {
  "Notre Dame": "Independent",
  "Yale": "Ivy League",
  "Alabama": "SEC",
  "Ohio State": "Big Ten",
  "Michigan": "Big Ten",
  "Oklahoma": "SEC",
  "Southern California": "Big Ten",
  "Princeton": "Ivy League",
  "Harvard": "Ivy League",
  "Nebraska": "Big Ten",
  "Pittsburgh": "ACC",
  "Texas": "SEC",
  "Minnesota": "Big Ten",
  "Penn State": "Big Ten",
  "Army": "Independent",
  "LSU": "SEC",
  "Stanford": "ACC",
  "Penn": "Ivy League",
  "Georgia": "SEC",
  "Illinois": "Big Ten",
  "Wisconsin": "Big Ten",
  "Iowa": "Big Ten",
  "Michigan State": "Big Ten",
  "Syracuse": "ACC",
  "Florida": "SEC",
  "Auburn": "SEC",
  "Texas A&M": "SEC",
  "Florida State": "ACC",
  "Oklahoma State": "Big 12",
  "TCU": "Big 12",
  "Colorado": "Big 12",
  "Oregon": "Big Ten",
  "Miami (FL)": "ACC",
  "UCLA": "Big Ten",
  "Arkansas": "SEC",
  "NC State": "ACC",
  "Texas Tech": "Big 12",
  "Arizona": "Big 12",
  "BYU": "Big 12",
  "Clemson": "ACC",
  "Boston College": "ACC",
  "Tennessee": "SEC",
  "Utah": "Big 12",
  "Kansas State": "Big 12",
  "Maryland": "Big Ten",
  "Baylor": "Big 12",
  "Georgia Tech": "ACC",
  "Louisville": "ACC"
};

window.CFB_GRID_PLAYERS = [
  { "name": "Aaron Curry", "schools": ["Wake Forest"], "positions": ["LB"], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Aaron Hernandez", "schools": ["Florida"], "positions": ["TE"], "years": [2009], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Aaron Ross", "schools": ["Texas"], "positions": ["DB"], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Adam Korsak", "schools": ["Rutgers"], "positions": [], "years": [2022], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Adoree' Jackson", "schools": ["Southern California"], "positions": ["DB"], "years": [2016], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "A.J. Hawk", "schools": ["Ohio State"], "positions": [], "years": [2005], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "A.J. McCarron", "schools": ["Alabama"], "positions": ["QB"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Alexis Serna", "schools": ["Oregon State"], "positions": [], "years": [2005], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Alex Karras", "schools": ["Iowa"], "positions": ["OL"], "years": [1957], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Alex Leatherwood", "schools": ["Alabama"], "positions": ["OL"], "years": [2020], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Andre Szmyt", "schools": ["Syracuse"], "positions": [], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Andre Williams", "schools": ["Boston College"], "positions": ["RB"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Andrew Luck", "schools": ["Stanford"], "positions": ["QB"], "years": [2011], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Walter Camp Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Anthony Thompson", "schools": ["Indiana"], "positions": [], "years": [1989], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Walter Camp Award"] },
  { "name": "Antoine Cason", "schools": ["Arizona"], "positions": ["DB"], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Antonio Bryant", "schools": ["Pittsburgh"], "positions": ["WR"], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "A.Q. Shipley", "schools": ["Penn State"], "positions": ["OL"], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Art Carmody", "schools": ["Louisville"], "positions": [], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Ashton Jeanty", "schools": ["Boise State"], "positions": ["RB"], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Austin Seferian-Jenkins", "schools": ["Washington"], "positions": ["TE"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Bennie Blades", "schools": ["Miami (FL)"], "positions": ["DB"], "years": [1987], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Rickey Dixon", "schools": ["Oklahoma"], "positions": ["DB"], "years": [1987], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Bill Dudley", "schools": ["Virginia"], "positions": [], "years": [1941], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Bill Fischer", "schools": ["Notre Dame"], "positions": ["OL"], "years": [1948], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Bill Stanfill", "schools": ["Georgia"], "positions": ["OL"], "years": [1968], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "B.J. Sander", "schools": ["Ohio State"], "positions": [], "years": [2003], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Bobby Engram", "schools": ["Penn State"], "positions": ["WR"], "years": [1994], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Bob Gain", "schools": ["Kentucky"], "positions": ["OL"], "years": [1950], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Bob Odell", "schools": ["Penn"], "positions": [], "years": [1943], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Bob Reifsnyder", "schools": ["Navy"], "positions": [], "years": [1957], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Brad Banks", "schools": ["Iowa"], "positions": ["QB"], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Brad Budde", "schools": ["Southern California"], "positions": [], "years": [1979], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Brad Craddock", "schools": ["Maryland"], "positions": [], "years": [2014], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Braden Mann", "schools": ["Texas A&M"], "positions": [], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Bradley Chubb", "schools": ["NC State"], "positions": ["DL"], "years": [2017], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Bronko Nagurski Trophy", "Ted Hendricks Award"] },
  { "name": "Brad Shearer", "schools": ["Texas"], "positions": ["OL"], "years": [1977], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Brady Quinn", "schools": ["Notre Dame"], "positions": ["QB"], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Brandin Cooks", "schools": ["Oregon State"], "positions": ["WR"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Brett Romberg", "schools": ["Miami (FL)"], "positions": ["OL"], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Brett Thorson", "schools": ["Georgia"], "positions": [], "years": [2025], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Bruce Clark", "schools": ["Penn State"], "positions": [], "years": [1978], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Bryant McKinnie", "schools": ["Miami (FL)"], "positions": ["OL"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Bryon Stork", "schools": ["Florida State"], "positions": ["OL"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Bud Brooks", "schools": ["Arkansas"], "positions": ["OL"], "years": [1954], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Byron 'Bam' Morris", "schools": ["Texas Tech"], "positions": ["RB"], "years": [1993], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Byron Hanspard", "schools": ["Texas Tech"], "positions": ["RB"], "years": [1996], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Cade McNown", "schools": ["UCLA"], "positions": ["QB"], "years": [1998], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Cairo Santos", "schools": ["Tulane"], "positions": [], "years": [2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Cal Jones", "schools": ["Iowa"], "positions": ["OL"], "years": [1955], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Calvin Johnson", "schools": ["Georgia Tech"], "positions": ["WR"], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Cameron Ward", "schools": ["Miami (FL)"], "positions": ["QB"], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Carl Nassib", "schools": ["Penn State"], "positions": ["DL"], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award", "Ted Hendricks Award"] },
  { "name": "Carlos Rogers", "schools": ["Auburn"], "positions": ["DB"], "years": [2004], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Casey Weldon", "schools": ["Florida State"], "positions": ["QB"], "years": [1991], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Cedric Benson", "schools": ["Texas"], "positions": ["RB"], "years": [2004], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Chad Hennings", "schools": ["Air Force"], "positions": ["OL"], "years": [1987], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Chase Coffman", "schools": ["Missouri"], "positions": ["TE"], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Chas Henry", "schools": ["Florida"], "positions": [], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Chris Claiborne", "schools": ["Southern California"], "positions": ["LB"], "years": [1998], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Chris Hudson", "schools": ["Colorado"], "positions": ["DB"], "years": [1994], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Chris Long", "schools": ["Virginia"], "positions": ["DL"], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ted Hendricks Award"] },
  { "name": "Chris Perry", "schools": ["Michigan"], "positions": ["RB"], "years": [2003], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Chris Redman", "schools": ["Louisville"], "positions": ["QB"], "years": [1999], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Chris Samuels", "schools": ["Alabama"], "positions": ["OL"], "years": [1999], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Christopher Dunn", "schools": ["NC State"], "positions": [], "years": [2022], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Chris Weinke", "schools": ["Florida State"], "positions": ["QB"], "years": [2000], "heisman": true, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "C.J. Mosley", "schools": ["Alabama"], "positions": ["LB"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Clelin Ferrell", "schools": ["Clemson"], "positions": ["DL"], "years": [2018], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Ted Hendricks Award"] },
  { "name": "Coby Bryant", "schools": ["Cincinnati"], "positions": ["DB"], "years": [2021], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Collin Klein", "schools": ["Kansas State"], "positions": ["QB"], "years": [2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Connor Cook", "schools": ["Michigan State"], "positions": ["QB"], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Corey Coleman", "schools": ["Baylor"], "positions": ["WR"], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Corey Moore", "schools": ["Virginia Tech"], "positions": [], "years": [1999], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Bronko Nagurski Trophy", "Lombardi Award"] },
  { "name": "Craig Erickson", "schools": ["Miami (FL)"], "positions": ["QB"], "years": [1990], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Dan Bailey", "schools": ["Oklahoma State"], "positions": [], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Dan Connor", "schools": ["Penn State"], "positions": [], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award"] },
  { "name": "Daniel Graham", "schools": ["Colorado"], "positions": ["TE"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Daniel Sepulveda", "schools": ["Baylor"], "positions": [], "years": [2004, 2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Dan Morgan", "schools": ["Miami (FL)"], "positions": ["LB"], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Chuck Bednarik Award", "Bronko Nagurski Trophy"] },
  { "name": "Dan Mozes", "schools": ["West Virginia"], "positions": ["OL"], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Da'Quan Bowers", "schools": ["Clemson"], "positions": ["DL"], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Bronko Nagurski Trophy", "Ted Hendricks Award"] },
  { "name": "Darqueze Dennard", "schools": ["Michigan State"], "positions": ["DB"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Darren McFadden", "schools": ["Arkansas"], "positions": ["RB"], "years": [2006, 2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Walter Camp Award", "Doak Walker Award"] },
  { "name": "Darryll Lewis", "schools": ["Arizona"], "positions": ["DB"], "years": [1990], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "David Baas", "schools": ["Michigan"], "positions": ["OL"], "years": [2004], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Ben Wilkerson", "schools": ["LSU"], "positions": ["OL"], "years": [2004], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "David Carr", "schools": ["Fresno State"], "positions": ["QB"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "David Molk", "schools": ["Michigan"], "positions": ["OL"], "years": [2011], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Deandre Baker", "schools": ["Georgia"], "positions": ["DB"], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Dean Steinkuhler", "schools": ["Nebraska"], "positions": ["OL"], "years": [1983], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy", "Lombardi Award"] },
  { "name": "Deon Figures", "schools": ["Colorado"], "positions": ["DB"], "years": [1992], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Deshaun Watson", "schools": ["Clemson"], "positions": ["QB"], "years": [2015, 2016], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Davey O'Brien Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Desmond King", "schools": ["Iowa"], "positions": ["DB"], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Dick Modzelewski", "schools": ["Maryland"], "positions": ["OL"], "years": [1952], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Diego Pavia", "schools": ["Vanderbilt"], "positions": ["QB"], "years": [2025], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "D.J. Williams", "schools": ["Arkansas"], "positions": ["TE"], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Dominic Raiola", "schools": ["Nebraska"], "positions": ["OL"], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "D'Onta Foreman", "schools": ["Texas"], "positions": ["RB"], "years": [2016], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Drew Brees", "schools": ["Purdue"], "positions": [], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Durant Brooks", "schools": ["Georgia Tech"], "positions": [], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Dwayne Allen", "schools": ["Clemson"], "positions": ["TE"], "years": [2011], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Ed Bagdon", "schools": ["Michigan State"], "positions": ["OL"], "years": [1949], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Eddie Czaplicki", "schools": ["Southern California"], "positions": [], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Ed Marinaro", "schools": ["Cornell"], "positions": [], "years": [1971], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Ed Oliver", "schools": ["Houston"], "positions": ["OL"], "years": [2017], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "E.J. Henderson", "schools": ["Maryland"], "positions": ["LB"], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Chuck Bednarik Award"] },
  { "name": "Eli Manning", "schools": ["Ole Miss"], "positions": ["QB"], "years": [2003], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Eli Stowers", "schools": ["Vanderbilt"], "positions": ["TE"], "years": [2025], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Elvis Dumervil", "schools": ["Louisville"], "positions": ["DL"], "years": [2005], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Bronko Nagurski Trophy", "Ted Hendricks Award"] },
  { "name": "Eric Berry", "schools": ["Tennessee"], "positions": ["DB"], "years": [2009], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Eric Crouch", "schools": ["Nebraska"], "positions": ["QB"], "years": [2001], "heisman": true, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Walter Camp Award", "Davey O'Brien Award"] },
  { "name": "Erick Anderson", "schools": ["Michigan"], "positions": ["LB"], "years": [1991], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Eric Kendricks", "schools": ["UCLA"], "positions": ["LB"], "years": [2014], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Felix Blanchard", "schools": ["Army"], "positions": [], "years": [1945], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Fred Davis", "schools": ["Southern California"], "positions": ["TE"], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Gardner Minshew II", "schools": ["Washington State"], "positions": ["QB"], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Garrett Bradbury", "schools": ["NC State"], "positions": ["OL"], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Gerod Holliman", "schools": ["Louisville"], "positions": ["DB"], "years": [2014], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Glenn Ressler", "schools": ["Penn State"], "positions": [], "years": [1964], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Graham Gano", "schools": ["Florida State"], "positions": [], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Graham Harrell", "schools": ["Texas Tech"], "positions": ["QB"], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Graham Nicholson", "schools": ["Miami (OH)"], "positions": [], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Grant Delpit", "schools": ["LSU"], "positions": ["DB"], "years": [2019], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Grant Wistrom", "schools": ["Nebraska"], "positions": [], "years": [1997], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Greg Lewis", "schools": ["Washington"], "positions": ["RB"], "years": [1990], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Greg Myers", "schools": ["Colorado State"], "positions": ["DB"], "years": [1995], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Greg Roberts", "schools": ["Oklahoma"], "positions": ["OL"], "years": [1978], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Harrison Bryant", "schools": ["Florida Atlantic"], "positions": ["TE"], "years": [2019], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Heath Miller", "schools": ["Virginia"], "positions": ["TE"], "years": [2004], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Hunter Henry", "schools": ["Arkansas"], "positions": ["TE"], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Isaiah Simmons", "schools": ["Clemson"], "positions": ["LB"], "years": [2019], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Jack Campbell", "schools": ["Iowa"], "positions": ["LB"], "years": [2022], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Jackson Jeffcoat", "schools": ["Texas"], "positions": ["DL"], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ted Hendricks Award"] },
  { "name": "Jackson Powers-Johnson", "schools": ["Oregon"], "positions": ["OL"], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Jacob Rodriguez", "schools": ["Texas Tech"], "positions": ["LB"], "years": [2025], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award"] },
  { "name": "Jadeveon Clowney", "schools": ["South Carolina"], "positions": ["DL"], "years": [2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ted Hendricks Award"] },
  { "name": "Jahdae Barron", "schools": ["Texas"], "positions": ["DB"], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Jake Butt", "schools": ["Michigan"], "positions": ["TE"], "years": [2016], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Jake Grove", "schools": ["Virginia Tech"], "positions": ["OL"], "years": [2003], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Jake Kirkpatrick", "schools": ["TCU"], "positions": ["OL"], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Jake Moody", "schools": ["Michigan"], "positions": [], "years": [2021], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Jalon Walker", "schools": ["Georgia"], "positions": ["LB"], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Jamal Reynolds", "schools": ["Florida State"], "positions": [], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Jamar Fletcher", "schools": ["Wisconsin"], "positions": ["DB"], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Jameis Winston", "schools": ["Florida State"], "positions": ["QB"], "years": [2013], "heisman": true, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Walter Camp Award", "Davey O'Brien Award"] },
  { "name": "James Washington", "schools": ["Oklahoma State"], "positions": ["WR"], "years": [2017], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Jammal Brown", "schools": ["Oklahoma"], "positions": ["OL"], "years": [2004], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Jason Buck", "schools": ["BYU"], "positions": ["OL"], "years": [1986], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Jay Barker", "schools": ["Alabama"], "positions": ["QB"], "years": [1994], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Jeremiah Owusu-Koramoah", "schools": ["Notre Dame"], "positions": ["LB"], "years": [2020], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Jerry Hughes", "schools": ["TCU"], "positions": ["DL"], "years": [2009], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ted Hendricks Award"] },
  { "name": "Jerry Jeudy", "schools": ["Alabama"], "positions": ["WR"], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Jim McMahon", "schools": ["BYU"], "positions": ["QB"], "years": [1981], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Jim Parker", "schools": ["Ohio State"], "positions": ["OL"], "years": [1956], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Jim Ritcher", "schools": ["NC State"], "positions": ["OL"], "years": [1979], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Jim Weatherall", "schools": ["Oklahoma"], "positions": ["OL"], "years": [1951], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Joe Allison", "schools": ["Memphis"], "positions": [], "years": [1992], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Joe Hamilton", "schools": ["Georgia Tech"], "positions": ["QB"], "years": [1999], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Joe Steffy", "schools": ["Army"], "positions": ["OL"], "years": [1947], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "John Henderson", "schools": ["Tennessee"], "positions": ["OL"], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Johnthan Banks", "schools": ["Mississippi State"], "positions": ["DB"], "years": [2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Jonathan Luigs", "schools": ["Arkansas"], "positions": ["OL"], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Jonathan Nichols", "schools": ["Ole Miss"], "positions": [], "years": [2003], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Jonathan Ogden", "schools": ["UCLA"], "positions": ["OL"], "years": [1995], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Jonathan Ruffin", "schools": ["Cincinnati"], "positions": [], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Jose Borregales", "schools": ["Miami (FL)"], "positions": [], "years": [2020], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Josh Allen", "schools": ["Kentucky"], "positions": [], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy"] },
  { "name": "Josh Reed", "schools": ["LSU"], "positions": ["WR"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Joshua Garnett", "schools": ["Stanford"], "positions": ["OL"], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Judd Davis", "schools": ["Florida"], "positions": [], "years": [1993], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Julius Peppers", "schools": ["North Carolina"], "positions": [], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award", "Lombardi Award"] },
  { "name": "Kai Forbath", "schools": ["UCLA"], "positions": [], "years": [2009], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Ka'imi Fairbairn", "schools": ["UCLA"], "positions": [], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Kellen Winslow II", "schools": ["Miami (FL)"], "positions": ["TE"], "years": [2003], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Ken Dorsey", "schools": ["Miami (FL)"], "positions": [], "years": [2001], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Kenneth Almendares", "schools": ["Louisiana"], "positions": [], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Kenny Pickett", "schools": ["Pittsburgh"], "positions": ["QB"], "years": [2021], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Kevin Hardy", "schools": ["Illinois"], "positions": ["LB"], "years": [1995], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Kevin Stemke", "schools": ["Wisconsin"], "positions": [], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Kris Farris", "schools": ["UCLA"], "positions": ["OL"], "years": [1998], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Kyle Kennard", "schools": ["South Carolina"], "positions": [], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Bronko Nagurski Trophy"] },
  { "name": "Kyle Pitts", "schools": ["Florida"], "positions": ["TE"], "years": [2020], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Laiatu Latu", "schools": ["UCLA"], "positions": [], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "LaMarr Woodley", "schools": ["Michigan"], "positions": ["DL"], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award", "Ted Hendricks Award"] },
  { "name": "LaMichael James", "schools": ["Oregon"], "positions": ["RB"], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Landon Dickerson", "schools": ["Alabama"], "positions": ["OL"], "years": [2020], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Larry Jacobson", "schools": ["Nebraska"], "positions": ["OL"], "years": [1971], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "LaVar Arrington", "schools": ["Penn State"], "positions": ["LB"], "years": [1999], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Chuck Bednarik Award"] },
  { "name": "Lawrence Wright", "schools": ["Florida"], "positions": ["DB"], "years": [1996], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "LeCharles Bentley", "schools": ["Ohio State"], "positions": ["OL"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Lee Roy Selmon", "schools": ["Oklahoma"], "positions": ["OL"], "years": [1975], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Outland Trophy", "Lombardi Award"] },
  { "name": "Logan Jones", "schools": ["Iowa"], "positions": ["OL"], "years": [2025], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Loyd Phillips", "schools": ["Arkansas"], "positions": ["OL"], "years": [1966], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Luke Joeckel", "schools": ["Texas A&M"], "positions": ["OL"], "years": [2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Luke Kuechly", "schools": ["Boston College"], "positions": ["LB"], "years": [2011], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Bronko Nagurski Trophy", "Lombardi Award"] },
  { "name": "Luke Staley", "schools": ["BYU"], "positions": ["RB"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Mac Jones", "schools": ["Alabama"], "positions": ["QB"], "years": [2020], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Davey O'Brien Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Malcolm Jenkins", "schools": ["Ohio State"], "positions": ["DB"], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Marcedes Lewis", "schools": ["UCLA"], "positions": ["TE"], "years": [2005], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Marc Primanti", "schools": ["NC State"], "positions": [], "years": [1996], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Marcus Harris", "schools": ["Wyoming"], "positions": ["WR"], "years": [1996], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Mark Mariscal", "schools": ["Colorado"], "positions": [], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Martin Gramatica", "schools": ["Kansas State"], "positions": [], "years": [1997], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Marvin Jones", "schools": ["Florida State"], "positions": ["LB"], "years": [1992], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Lombardi Award"] },
  { "name": "Mason Rudolph", "schools": ["Oklahoma State"], "positions": ["QB"], "years": [2017], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Matt Araiza", "schools": ["San Diego State"], "positions": [], "years": [2021], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Matt Fodge", "schools": ["Oklahoma State"], "positions": [], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Matt Gay", "schools": ["Utah"], "positions": [], "years": [2017], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Matt Russell", "schools": ["Colorado"], "positions": ["LB"], "years": [1996], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Matt Ryan", "schools": ["Boston College"], "positions": ["QB"], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Matt Spaeth", "schools": ["Minnesota"], "positions": ["TE"], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Maurkice Pouncey", "schools": ["Florida"], "positions": ["OL"], "years": [2009], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Max Duffy", "schools": ["Kentucky"], "positions": [], "years": [2019], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Max Duggan", "schools": ["TCU"], "positions": ["QB"], "years": [2022], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Merlin Olsen", "schools": ["Utah State"], "positions": ["OL"], "years": [1961], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Michael Bishop", "schools": ["Kansas State"], "positions": ["QB"], "years": [1998], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Michael Crabtree", "schools": ["Texas Tech"], "positions": ["WR"], "years": [2007, 2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Michael Huff", "schools": ["Texas"], "positions": ["DB"], "years": [2005], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Michael Reeder", "schools": ["TCU"], "positions": [], "years": [1995], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Mike Hass", "schools": ["Oregon State"], "positions": ["WR"], "years": [2005], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Mike McGee", "schools": ["Duke"], "positions": ["OL"], "years": [1959], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Mike Nugent", "schools": ["Ohio State"], "positions": [], "years": [2004], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Mike Ruth", "schools": ["Boston College"], "positions": ["OL"], "years": [1985], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Mike Singletary", "schools": ["Baylor"], "positions": ["QB"], "years": [1979, 1980], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Mitch Wishnowsky", "schools": ["Utah"], "positions": [], "years": [2016], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Mohammed Elewonibi", "schools": ["BYU"], "positions": ["OL"], "years": [1989], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Montee Ball", "schools": ["Wisconsin"], "positions": ["RB"], "years": [2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Nakobe Dean", "schools": ["Georgia"], "positions": ["LB"], "years": [2021], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Nate Kaeding", "schools": ["Iowa"], "positions": [], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Nate Orchard", "schools": ["Utah"], "positions": ["DL"], "years": [2014], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ted Hendricks Award"] },
  { "name": "Nick Fairley", "schools": ["Auburn"], "positions": [], "years": [2010], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Nick O'Leary", "schools": ["Florida State"], "positions": ["TE"], "years": [2014], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Ollie Gordon II", "schools": ["Oklahoma State"], "positions": ["RB"], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Olusegun Oluwatimi", "schools": ["Michigan"], "positions": ["OL"], "years": [2022], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Pat Fitzgerald", "schools": ["Northwestern"], "positions": [], "years": [1995, 1996], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy"] },
  { "name": "Patrick Willis", "schools": ["Mississippi"], "positions": ["LB"], "years": [2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Paul Governali", "schools": ["Columbia"], "positions": [], "years": [1942], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Paul McGowan", "schools": ["Florida State"], "positions": ["LB"], "years": [1987], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Paul Posluszny", "schools": ["Penn State"], "positions": ["LB"], "years": [2005, 2006], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Chuck Bednarik Award"] },
  { "name": "Payton Wilson", "schools": ["NC State"], "positions": ["LB"], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award", "Chuck Bednarik Award"] },
  { "name": "Penei Sewell", "schools": ["Oregon"], "positions": ["OL"], "years": [2019], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Peyton Manning", "schools": ["Tennessee"], "positions": ["QB"], "years": [1997], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"] },
  { "name": "Pressley Harvin III", "schools": ["Georgia Tech"], "positions": [], "years": [2020], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Quinnen Williams", "schools": ["Alabama"], "positions": ["OL"], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Raghib Ismail", "schools": ["Notre Dame"], "positions": [], "years": [1990], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Walter Camp Award"] },
  { "name": "Randy Bullock", "schools": ["Texas A&M"], "positions": [], "years": [2011], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Randy Moss", "schools": ["Marshall"], "positions": ["WR"], "years": [1997], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Randy White", "schools": ["Maryland"], "positions": ["OL"], "years": [1974], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy", "Lombardi Award"] },
  { "name": "Reds Bagnell", "schools": ["Penn"], "positions": [], "years": [1950], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Reese Dismukes", "schools": ["Auburn"], "positions": ["OL"], "years": [2014], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Rey Maualuga", "schools": ["Southern California"], "positions": [], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award"] },
  { "name": "Rien Long", "schools": ["Washington State"], "positions": ["OL"], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Roberto Aguayo", "schools": ["Florida State"], "positions": [], "years": [2013], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Rob Waldrop", "schools": ["Arizona"], "positions": ["OL"], "years": [1993], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy", "Bronko Nagurski Trophy"] },
  { "name": "Rocky Calmus", "schools": ["Oklahoma"], "positions": ["LB"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Rodney Peete", "schools": ["Southern California"], "positions": ["QB"], "years": [1988], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Rodrigo Blankenship", "schools": ["Georgia"], "positions": [], "years": [2019], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Ron Beagle", "schools": ["Navy"], "positions": [], "years": [1954], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Russell Maryland", "schools": ["Miami (FL)"], "positions": ["OL"], "years": [1990], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Ryan Allen", "schools": ["Louisiana Tech"], "positions": [], "years": [2011, 2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Ryan Kelly", "schools": ["Alabama"], "positions": ["OL"], "years": [2015], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Ryan Plackemeier", "schools": ["Wake Forest"], "positions": [], "years": [2005], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Sam Bradford", "schools": ["Oklahoma"], "positions": ["QB"], "years": [2008], "heisman": true, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Scooby Wright III", "schools": ["Arizona"], "positions": [], "years": [2014], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award"] },
  { "name": "Scott Tolzien", "schools": ["Wisconsin"], "positions": ["QB"], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Sebastian Janikowski", "schools": ["Florida State"], "positions": [], "years": [1998, 1999], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Seth Marler", "schools": ["Tulane"], "positions": [], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Seth McLaughlin", "schools": ["Ohio State"], "positions": ["OL"], "years": [2024], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Rimington Trophy"] },
  { "name": "Shedeur Sanders", "schools": ["Colorado"], "positions": ["QB"], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Shonn Greene", "schools": ["Iowa"], "positions": ["RB"], "years": [2008], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Steve DeLong", "schools": ["Tennessee"], "positions": ["OL"], "years": [1964], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Steve Emtman", "schools": ["Washington"], "positions": ["OL"], "years": [1991], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Outland Trophy", "Lombardi Award"] },
  { "name": "Steve Joachim", "schools": ["Temple"], "positions": [], "years": [1974], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award"] },
  { "name": "Steve McLaughlin", "schools": ["Arizona"], "positions": [], "years": [1994], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Steve Young", "schools": ["BYU"], "positions": ["QB"], "years": [1983], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Tate Sandell", "schools": ["Oklahoma"], "positions": [], "years": [2025], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Terence Newman", "schools": ["Kansas State"], "positions": ["DB"], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Terrell Buckley", "schools": ["Florida State"], "positions": ["DB"], "years": [1991], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Terrell Suggs", "schools": ["Arizona State"], "positions": ["DL"], "years": [2002], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Bronko Nagurski Trophy", "Lombardi Award", "Ted Hendricks Award"] },
  { "name": "Terry Glenn", "schools": ["Ohio State"], "positions": ["WR"], "years": [1995], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Thomas Everett", "schools": ["Baylor"], "positions": ["DB"], "years": [1986], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Thomas Weber", "schools": ["Arizona State"], "positions": [], "years": [2007], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Tim Stratton", "schools": ["Purdue"], "positions": ["TE"], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "T.J. Hockenson", "schools": ["Iowa"], "positions": ["TE"], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Todd Blackledge", "schools": ["Penn State"], "positions": ["QB"], "years": [1982], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Tom Hackett", "schools": ["Utah"], "positions": [], "years": [2014, 2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Tom Hornsey", "schools": ["Memphis"], "positions": [], "years": [2013], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Tommy Nobis", "schools": ["Texas"], "positions": ["OL"], "years": [1965], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Outland Trophy"] },
  { "name": "Tony Casillas", "schools": ["Oklahoma"], "positions": [], "years": [1985], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Tony Degrate", "schools": ["Texas"], "positions": [], "years": [1984], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Tony Rice", "schools": ["Notre Dame"], "positions": ["QB"], "years": [1989], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Johnny Unitas Golden Arm Award"] },
  { "name": "Tory Taylor", "schools": ["Iowa"], "positions": [], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Travis Dorsch", "schools": ["Purdue"], "positions": [], "years": [2001], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Ray Guy Award"] },
  { "name": "Tre'Vius Hodges-Tomlinson", "schools": ["TCU"], "positions": ["DB"], "years": [2022], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Trevon Moehrig", "schools": ["TCU"], "positions": ["DB"], "years": [2020], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Trevor Cobb", "schools": ["Rice"], "positions": ["RB"], "years": [1991], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Doak Walker Award"] },
  { "name": "Trey McBride", "schools": ["Colorado State"], "positions": ["TE"], "years": [2021], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Trey Taylor", "schools": ["Air Force"], "positions": ["DB"], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Troy Aikman", "schools": ["UCLA"], "positions": ["QB"], "years": [1988], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Davey O'Brien Award"] },
  { "name": "Troy Edwards", "schools": ["Louisiana Tech"], "positions": ["WR"], "years": [1998], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Tua Tagovailoa", "schools": ["Alabama"], "positions": [], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Maxwell Award", "Walter Camp Award"] },
  { "name": "Tyler Eifert", "schools": ["Notre Dame"], "positions": ["TE"], "years": [2012], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Tyler Matakevich", "schools": ["Temple"], "positions": [], "years": [2015], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy"] },
  { "name": "Tyler Warren", "schools": ["Penn State"], "positions": ["TE"], "years": [2024], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["John Mackey Award"] },
  { "name": "Tyrann Mathieu", "schools": ["LSU"], "positions": [], "years": [2011], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award"] },
  { "name": "Tyrone Carter", "schools": ["Minnesota"], "positions": ["DB"], "years": [1999], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Jim Thorpe Award"] },
  { "name": "Ugo Amadi", "schools": ["Oregon"], "positions": [], "years": [2018], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Wilson Whitley", "schools": ["Houston"], "positions": [], "years": [1976], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lombardi Award"] },
  { "name": "Xavier Watts", "schools": ["Notre Dame"], "positions": [], "years": [2023], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Bronko Nagurski Trophy"] },
  { "name": "Zane Gonzalez", "schools": ["Arizona State"], "positions": [], "years": [2016], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Lou Groza Award"] },
  { "name": "Zaven Collins", "schools": ["Tulsa"], "positions": [], "years": [2020], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award"] },
  { "name": "Emmitt Smith", "schools": ["Florida"], "positions": ["RB"], "years": [1989], "heisman": false, "multiAA": false, "natChamp": false, "hof": true, "draftRound": 1 },
  { "name": "Jack Youngblood", "schools": ["Florida"], "positions": ["DL"], "years": [1970], "heisman": false, "multiAA": false, "natChamp": false, "hof": true, "draftRound": 1 },
  { "name": "Wilber Marshall", "schools": ["Florida"], "positions": ["LB"], "years": [1982, 1983], "heisman": false, "multiAA": true, "natChamp": false, "hof": false },
  { "name": "Zeke Smith", "schools": ["Auburn"], "positions": ["OL"], "years": [1958], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy"] },
  { "name": "Tracy Rocker", "schools": ["Auburn"], "positions": ["DL"], "years": [1988], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Outland Trophy", "Lombardi Award"] },
  { "name": "Takeo Spikes", "schools": ["Auburn"], "positions": ["LB"], "years": [1997], "heisman": false, "multiAA": false, "natChamp": false, "hof": false },
  { "name": "Dat Nguyen", "schools": ["Texas A&M"], "positions": ["LB"], "years": [1998], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Chuck Bednarik Award", "Lombardi Award"] },
  { "name": "Von Miller", "schools": ["Texas A&M"], "positions": ["LB"], "years": [2010], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "awards": ["Butkus Award"], "draftRound": 1 },
  { "name": "Quentin Coryatt", "schools": ["Texas A&M"], "positions": ["LB"], "years": [1991], "heisman": false, "multiAA": false, "natChamp": false, "hof": false },
  { "name": "Deion Sanders", "schools": ["Florida State"], "positions": ["DB"], "years": [1987, 1988], "heisman": false, "multiAA": true, "natChamp": false, "hof": true, "awards": ["Jim Thorpe Award"], "draftRound": 1 },
  { "name": "Derrick Brooks", "schools": ["Florida State"], "positions": ["LB"], "years": [1993], "heisman": false, "multiAA": false, "natChamp": true, "hof": true, "draftRound": 1 },
  { "name": "Fred Biletnikoff", "schools": ["Florida State"], "positions": ["WR"], "years": [1964], "heisman": false, "multiAA": false, "natChamp": false, "hof": true, "draftRound": 1 },
  { "name": "Peter Warrick", "schools": ["Florida State"], "positions": ["WR"], "years": [1999], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Fred Biletnikoff Award"] },
  { "name": "Justin Blackmon", "schools": ["Oklahoma State"], "positions": ["WR"], "years": [2010, 2011], "heisman": false, "multiAA": true, "natChamp": false, "hof": false, "awards": ["Fred Biletnikoff Award"], "draftRound": 1 },
  { "name": "LaDainian Tomlinson", "schools": ["TCU"], "positions": ["RB"], "years": [2000], "heisman": false, "multiAA": false, "natChamp": false, "hof": true, "draftRound": 1, "awards": ["Doak Walker Award"] },
  { "name": "Alfred Williams", "schools": ["Colorado"], "positions": ["DL"], "years": [1990], "heisman": false, "multiAA": false, "natChamp": true, "hof": false, "awards": ["Butkus Award"] },
  { "name": "Haloti Ngata", "schools": ["Oregon"], "positions": ["DL"], "years": [2005], "heisman": false, "multiAA": false, "natChamp": false, "hof": false, "draftRound": 1 },
  { "name": "Ray Lewis", "schools": ["Miami (FL)"], "positions": ["LB"], "years": [1995], "heisman": false, "multiAA": false, "natChamp": false, "hof": true, "draftRound": 1 },
  { "name": "Michael Irvin", "schools": ["Miami (FL)"], "positions": ["WR"], "years": [1987], "heisman": false, "multiAA": false, "natChamp": true, "hof": true, "draftRound": 1 },
  { "name": "Warren Sapp", "schools": ["Miami (FL)"], "positions": ["DL"], "years": [1994], "heisman": false, "multiAA": false, "natChamp": false, "hof": true, "draftRound": 1, "awards": ["Bronko Nagurski Trophy", "Lombardi Award"] },
  { "name": "Ed Reed", "schools": ["Miami (FL)"], "positions": ["DB"], "years": [2001], "heisman": false, "multiAA": false, "natChamp": true, "hof": true, "draftRound": 1 },
  {
    "name": "Harry Stuhldreher",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1924
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Red Grange",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1923,
      1924,
      1925
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Jim Crowley",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1924
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Elmer Layden",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1924
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Adam Walsh",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1924
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed Weir",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1924,
      1925
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed McGinley",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1924
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Edgar Garbisch",
    "schools": [
      "Army"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1924
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Richard Luman",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1924
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Mike Garrett",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1965
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jim Grabowski",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1965
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Freeman White",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1965
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Nick Eddy",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1966
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Floyd Little",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1966
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Tom Regner",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1966
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Ron Yary",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1966,
      1967
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": true,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Bubba Smith",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1966
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Alan Page",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1966
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": true
  },
  {
    "name": "Jim Lynch",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1966
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Davey O'Brien",
    "schools": [
      "TCU"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1938
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Marshall Goldberg",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1937,
      1938
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Ralph Heikkinen",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1938
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed Beinor",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1938
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Waddy Young",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1938
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Johnny Lujack",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1947
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Bob Chappuis",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1947
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Paul Cleary",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1947
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "George Connor",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1946,
      1947
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "John Ferraro",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1947
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Barry Sanders",
    "schools": [
      "Oklahoma State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1988
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Tony Mandarich",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1988
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Anthony Phillips",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1988
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Derrick Thomas",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1988
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Vince Young",
    "schools": [
      "Texas"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2005
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Davey O'Brien Award"]
  },
  {
    "name": "Reggie Bush",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2004,
      2005
    ],
    "heisman": true,
    "heismanYear": 2005,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Walter Camp Award", "Doak Walker Award"]
  },
  {
    "name": "Dwayne Jarrett",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2005
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jonathan Scott",
    "schools": [
      "Texas"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2005
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Greg Eslinger",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2005
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy", "Rimington Trophy"]
  },
  {
    "name": "Joe Burrow",
    "schools": [
      "LSU"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2019
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award", "Lombardi Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Jonathan Taylor",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2018,
      2019
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Ja'Marr Chase",
    "schools": [
      "LSU"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2019
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "CeeDee Lamb",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2019
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Andrew Thomas",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2019
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tyler Biadasz",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2019
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Rimington Trophy"]
  },
  {
    "name": "Chase Young",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2019
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy", "Ted Hendricks Award"]
  },
  {
    "name": "Jeff Okudah",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2019
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Robert Torrey",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1905
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jim McCormick",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1905
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Guy Hutchinson",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1905
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Brickley",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1912
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Percy Wendell",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1910,
      1911,
      1912
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Stan Pennock",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1912
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bob Butler",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1912
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Paul Hornung",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1955,
      1956
    ],
    "heisman": true,
    "heismanYear": 1956,
    "multiAA": true,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Jim Brown",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1956
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Tommy McDonald",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1956
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Ricky Bell",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1975,
      1976
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tony Dorsett",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1975,
      1976
    ],
    "heisman": true,
    "heismanYear": 1976,
    "multiAA": true,
    "natChamp": true,
    "hof": true,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Leroy Selmon",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1975
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Steve Niehaus",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1975
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Greg Buttle",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1975
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Danny Wuerffel",
    "schools": [
      "Florida"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1996
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Orlando Pace",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1995,
      1996
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": true,
    "awards": ["Outland Trophy", "Lombardi Award"]
  },
  {
    "name": "Kevin Jackson",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1996
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jayden Daniels",
    "schools": [
      "LSU"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2023
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Marvin Harrison Jr.",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2023
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Malik Nabers",
    "schools": [
      "LSU"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2023
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Brock Bowers",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      2023
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["John Mackey Award"]
  },
  {
    "name": "Joe Alt",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2023
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jer'Zhan Newton",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2023
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dallas Turner",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2023
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dave Campbell",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1899
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Art Hillebrand",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1899
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "George S. Stillman",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1899
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bronko Nagurski",
    "schools": [
      "Minnesota"
    ],
    "positions": [],
    "years": [
      1929
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Jack Cannon",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1929
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ben Ticknor",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1929,
      1930
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Joe Donchess",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1929
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Angelo Bertelli",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1943
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Ralph Heywood",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1943
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Yonakor",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1943
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Johnny Rodgers",
    "schools": [
      "Nebraska"
    ],
    "positions": ["WR"],
    "years": [
      1971,
      1972
    ],
    "heisman": true,
    "heismanYear": 1972,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Walter Camp Award"]
  },
  {
    "name": "Charles Young",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      1972
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Jerry Sisemore",
    "schools": [
      "Texas"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1971,
      1972
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Hannah",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1972
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Greg Pruitt",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1971,
      1972
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Greg Marx",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1972
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Rich Glover",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1972
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy", "Lombardi Award"]
  },
  {
    "name": "Brad Van Pelt",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1972
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Bo Jackson",
    "schools": [
      "Auburn"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1983,
      1985
    ],
    "heisman": true,
    "heismanYear": 1985,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Walter Camp Award"]
  },
  {
    "name": "Chuck Long",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1985
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Davey O'Brien Award"]
  },
  {
    "name": "Lorenzo White",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1985,
      1987
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Brian Bosworth",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1985
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "David Williams",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1984,
      1985
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Larry Station",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1985
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Leslie O'Neal",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1985
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Tim Green",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1985
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "David Yankey",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2013
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Aaron Donald",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2013
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy", "Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award"]
  },
  {
    "name": "Johnny Manziel",
    "schools": [
      "Texas A&M"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2012,
      2013
    ],
    "heisman": true,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Davey O'Brien Award"]
  },
  {
    "name": "Bob Higgins",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1919
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chic Harley",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1919
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Eddie Casey",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1919
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jay Berwanger",
    "schools": [
      "Chicago"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1935
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bobby Grayson",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1934,
      1935
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ozzie Simmons",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1935
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gomer Jones",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1935
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Roger Staubach",
    "schools": [
      "Navy"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1963
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Dick Butkus",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1963,
      1964
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Scott Appleton",
    "schools": [
      "Texas"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1963
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Bob Brown",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1963
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Carl Eller",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1963
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Chuck Fusina",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1978
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Keith Dorney",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1978
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Kelvin Clark",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1978
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ron Dayne",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1999
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Doak Walker Award"]
  },
  {
    "name": "Troy Walters",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1999
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "Johnny Lattner",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1952,
      1953
    ],
    "heisman": true,
    "heismanYear": 1953,
    "multiAA": true,
    "natChamp": false,
    "hof": true,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Billy Vessels",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1952
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Frank McPhee",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1952
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Billy Cannon",
    "schools": [
      "LSU"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1958,
      1959
    ],
    "heisman": true,
    "heismanYear": 1959,
    "multiAA": true,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Dan Lanphear",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1959
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Roger Davis",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1959
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Richie Lucas",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1959
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Bill Carpenter",
    "schools": [
      "Army"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1959
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Elway",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1982
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Herschel Walker",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1980,
      1981,
      1982
    ],
    "heisman": true,
    "heismanYear": 1982,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Anthony Carter",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1981,
      1982
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dave Rimington",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1981,
      1982
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy", "Lombardi Award"]
  },
  {
    "name": "Charlie Ward",
    "schools": [
      "Florida State"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1993
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Aaron Taylor",
    "schools": [
      "Nebraska",
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1993,
      1997
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy", "Lombardi Award"]
  },
  {
    "name": "Trev Alberts",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1993
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Antonio Langham",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1993
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Jim Thorpe Award"]
  },
  {
    "name": "Lamar Jackson",
    "schools": [
      "Louisville"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2016
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Dede Westbrook",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "Pat Elflein",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Rimington Trophy"]
  },
  {
    "name": "Cam Robinson",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Jonathan Allen",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award", "Ted Hendricks Award"]
  },
  {
    "name": "Reuben Foster",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Jabrill Peppers",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jourdan Lewis",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jamal Adams",
    "schools": [
      "LSU"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2016
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bryce Young",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2021,
      2022
    ],
    "heisman": true,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Davey O'Brien Award"]
  },
  {
    "name": "Kenneth Walker III",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2021
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Tyler Linderbaum",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2021
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Rimington Trophy"]
  },
  {
    "name": "Jameson Williams",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2021
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Aidan Hutchinson",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2021
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award", "Ted Hendricks Award"]
  },
  {
    "name": "Jordan Davis",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2021
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Chuck Bednarik Award"]
  },
  {
    "name": "Will Anderson Jr.",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2021,
      2022
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award"]
  },
  {
    "name": "Carson Palmer",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2002
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Larry Johnson",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2002
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Doak Walker Award"]
  },
  {
    "name": "Charles Rogers",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2002
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "Dallas Clark",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      2002
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["John Mackey Award"]
  },
  {
    "name": "David Pollack",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2002
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Chuck Bednarik Award", "Lombardi Award", "Ted Hendricks Award"]
  },
  {
    "name": "Mike Doss",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2002
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Shane Walton",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2002
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Colt McCoy",
    "schools": [
      "Texas"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2008,
      2009
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Andre Smith",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2008
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Brian Orakpo",
    "schools": [
      "Texas"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2008
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Bronko Nagurski Trophy", "Lombardi Award", "Ted Hendricks Award"]
  },
  {
    "name": "Travis Hunter",
    "schools": [
      "Colorado"
    ],
    "positions": ["WR", "DB"],
    "years": [
      2024
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Chuck Bednarik Award"]
  },
  {
    "name": "Kelvin Banks Jr.",
    "schools": [
      "Texas"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2024
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award"]
  },
  {
    "name": "Mason Graham",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2024
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Abdul Carter",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2024
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jay Higgins",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2024
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Caleb Downs",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2024,
      2025
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Jim Thorpe Award"]
  },
  {
    "name": "Marshall 'Ma' Newell",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1890
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Pudge Heffelfinger",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1889,
      1890,
      1891
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Thomas 'Bum' McClung",
    "schools": [
      "Yale"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1890
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "William H. Lewis",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1892,
      1893
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Philip King",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1891,
      1892
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Vance McCormick",
    "schools": [
      "Yale"
    ],
    "positions": [],
    "years": [
      1892
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Harry Thayer",
    "schools": [
      "Penn"
    ],
    "positions": [],
    "years": [
      1892
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charley Brewer",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1892
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Frank Hinkey",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1891,
      1894
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Gelbert",
    "schools": [
      "Penn"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1894,
      1895,
      1896
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bert Waters",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1894
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Langdon Lea",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1894,
      1895
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Art Wheeler",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1894
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bill Hickock",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1894
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Norman Cabot",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1895,
      1896
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Fred T. Murphy",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1895
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Wharton",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1895,
      1896
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dudley Riggs",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1895
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Garrett Cochran",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1897
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John A. Hall",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1897
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Outland",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1897
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Lew Palmer",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1898
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Hallowell",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1898,
      1900
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "William Cunningham",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1898
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Neil Snow",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1901
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "David Campbell",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1900,
      1901
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ralph Davis",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1901
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Paul Bunker",
    "schools": [
      "Army"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1902
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John DeWitt",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1903
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles D. Rafferty",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1903
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Willie Heston",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1903
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "James Hogan",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1903
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Fred Schacht",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1903
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tom Shevlin",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1904
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Frank Piekarski",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1904
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Andy Smith",
    "schools": [
      "Penn"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1904
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Clarence Alcott",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1907
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Caspar Wister",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1907
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ted Coy",
    "schools": [
      "Yale"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1907,
      1909
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Hamlin Andrus",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1909
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Carroll Cooney",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1909
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Kilpatrick",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1909
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Albert Benbrook",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1910
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Stanfield Wells",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1910
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "James Walker",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1910
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Robert Fisher",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1910,
      1911
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Paul Veeder",
    "schools": [
      "Yale"
    ],
    "positions": [],
    "years": [
      1906
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Eddie Dillon",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1906
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bob Forbes",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1906
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Germany Schulz",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1908
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Eddie Mahan",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1913,
      1915
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Louis Merrilat",
    "schools": [
      "Army"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1913
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "James Craig",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1913
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Huntington Hardwick",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1914
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bert Baston",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1916
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Harley",
    "schools": [
      "Ohio State"
    ],
    "positions": [],
    "years": [
      1917
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Frank Steketee",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1918
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "George McLaren",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1918
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Amos Alonzo Stagg",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Arthur Cumnock",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Hector Cowan",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Gill",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Cranston",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "William George",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Edgar Allan Poe",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Roscoe Channing",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Knowlton Ames",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "James Lee",
    "schools": [
      "Harvard"
    ],
    "positions": [],
    "years": [
      1889
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Hartwell",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Wallace Winter",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Marshall Newell",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jesse Riggs",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Adams",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Everett Lake",
    "schools": [
      "Harvard"
    ],
    "positions": [],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Thomas McClung",
    "schools": [
      "Yale"
    ],
    "positions": [],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Sheppard Homans",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1891
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "William Church",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Fred Murphy",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Wylie Woodruff",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Robert Gailey",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Clarence Fincke",
    "schools": [
      "Yale"
    ],
    "positions": [],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Edgar Wrightington",
    "schools": [
      "Harvard"
    ],
    "positions": [],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Addison Kelly",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Baird",
    "schools": [
      "Princeton"
    ],
    "positions": [],
    "years": [
      1896
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "William Smith",
    "schools": [
      "Army"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "George Stillman",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "James Bloomer",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gordon Brown",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "T. Truxton Hare",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Herman Olcott",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "George Chadwick",
    "schools": [
      "Yale"
    ],
    "positions": [],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Daly",
    "schools": [
      "Harvard"
    ],
    "positions": [],
    "years": [
      1900
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Douglass Bomeisler",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1911
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Sanford White",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1911
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Edward Hart",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1911
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Leland Devore",
    "schools": [
      "Army"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1911
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Joseph Duff",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1911
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Henry Ketcham",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1911
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Arthur Howe",
    "schools": [
      "Yale"
    ],
    "positions": [],
    "years": [
      1911
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Guy Chamberlin",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1915
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Joseph Gilman",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1915
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Howard Buck",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1915
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Harold White",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1915
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Robert Peck",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1915
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Richard King",
    "schools": [
      "Harvard"
    ],
    "positions": [],
    "years": [
      1915
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bart Macomber",
    "schools": [
      "Illinois"
    ],
    "positions": [],
    "years": [
      1915
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Carney",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1920
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Stan Keck",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1920,
      1921
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ralph Scott",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1920
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tim Callahan",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1920
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Iolas Huffman",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1920,
      1921
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Herb Stein",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1920,
      1921
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "George Gipp",
    "schools": [
      "Notre Dame"
    ],
    "positions": [],
    "years": [
      1920
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gaylord Stinchcomb",
    "schools": [
      "Ohio State"
    ],
    "positions": [],
    "years": [
      1920
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Way",
    "schools": [
      "Penn State"
    ],
    "positions": [],
    "years": [
      1920
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Eddie Anderson",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1921
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Aubrey Devine",
    "schools": [
      "Iowa"
    ],
    "positions": [],
    "years": [
      1921
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Glenn Killinger",
    "schools": [
      "Penn State"
    ],
    "positions": [],
    "years": [
      1921
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Herbert Treat",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1922
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Thurman",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1922
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles Hubbard",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1922,
      1923
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed Garbisch",
    "schools": [
      "Army"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1922
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Harry Kipke",
    "schools": [
      "Michigan"
    ],
    "positions": [],
    "years": [
      1922
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gordon Locke",
    "schools": [
      "Iowa"
    ],
    "positions": [],
    "years": [
      1922
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Pete McRae",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1923
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ray Ecklund",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1923
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Century Milstead",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1923
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Marty Below",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1923
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "James McMillen",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1923
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jack Blott",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1923
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Harry Wilson",
    "schools": [
      "Penn State"
    ],
    "positions": [],
    "years": [
      1923
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bennie Oosterbaan",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1925,
      1926,
      1927
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ralph Chase",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1925
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed Hess",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1925
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed McMillan",
    "schools": [
      "Princeton"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1925
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ernie Nevers",
    "schools": [
      "Stanford"
    ],
    "positions": [],
    "years": [
      1925
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Benny Friedman",
    "schools": [
      "Michigan"
    ],
    "positions": [],
    "years": [
      1925,
      1926
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Vic Hanson",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1926
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bud Sprague",
    "schools": [
      "Army"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1926
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bernie Shively",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1926
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bud Boeringer",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1926
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Mort Kaer",
    "schools": [
      "Southern California"
    ],
    "positions": [],
    "years": [
      1926
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Herb Joesting",
    "schools": [
      "Minnesota"
    ],
    "positions": [],
    "years": [
      1926,
      1927
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tom Nash",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1927
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jesse Hibbs",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1927
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed Hake",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1927
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bill Webster",
    "schools": [
      "Yale"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1927
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Smith",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1927
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gibby Welch",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [],
    "years": [
      1927
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Morley Drury",
    "schools": [
      "Southern California"
    ],
    "positions": [],
    "years": [
      1927
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Red Cagle",
    "schools": [
      "Army"
    ],
    "positions": [],
    "years": [
      1927,
      1928
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Wes Fesler",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1928,
      1930
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Otto Pommerening",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1928
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Mike Getto",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1928
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Seraphim Post",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1928
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Paul Scull",
    "schools": [
      "Penn"
    ],
    "positions": [],
    "years": [
      1928
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Fred Sington",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1930
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Milo Lubratovich",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1930
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Frank Carideo",
    "schools": [
      "Notre Dame"
    ],
    "positions": [],
    "years": [
      1930
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Marchy Schwartz",
    "schools": [
      "Notre Dame"
    ],
    "positions": [],
    "years": [
      1930,
      1931
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Erny Pinckert",
    "schools": [
      "Southern California"
    ],
    "positions": [],
    "years": [
      1930
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Vernon Smith",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1931
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jesse Quatse",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1931
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Biggie Munn",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1931
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tommy Yarr",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1931
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gus Shaver",
    "schools": [
      "Southern California"
    ],
    "positions": [],
    "years": [
      1931
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Barry Wood",
    "schools": [
      "Harvard"
    ],
    "positions": [],
    "years": [
      1931
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Joe Skladany",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1932,
      1933
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Joe Kurth",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1932
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ernie Smith",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1932
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bill Corbus",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1932,
      1933
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Harry Newman",
    "schools": [
      "Michigan"
    ],
    "positions": [],
    "years": [
      1932
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Warren Heller",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [],
    "years": [
      1932
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Francis Wistert",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1933
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Aaron Rosenberg",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1933
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chuck Bernard",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1933
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Cotton Warburton",
    "schools": [
      "Southern California"
    ],
    "positions": [],
    "years": [
      1933
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "George Sauer",
    "schools": [
      "Nebraska"
    ],
    "positions": [],
    "years": [
      1933
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Don Hutson",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Frank Larson",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bill Lee",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bob Reynolds",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chuck Hartwig",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jack Robinson",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Pug Lund",
    "schools": [
      "Minnesota"
    ],
    "positions": [],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dixie Howell",
    "schools": [
      "Alabama"
    ],
    "positions": [],
    "years": [
      1934
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Larry Kelley",
    "schools": [
      "Yale"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1936
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gaynell Tinsley",
    "schools": [
      "LSU"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1936
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ed Widseth",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1936
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Averell Daniell",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1936
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Sam Francis",
    "schools": [
      "Nebraska"
    ],
    "positions": [],
    "years": [
      1936
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chuck Sweeney",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1937
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tony Matisi",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1937
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Clint Frank",
    "schools": [
      "Yale"
    ],
    "positions": ["RB"],
    "years": [
      1937
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Esco Sarkkinen",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1939
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ken Kavanaugh",
    "schools": [
      "LSU"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1939
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Harry Smith",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1939
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Nile Kinnick",
    "schools": [
      "Iowa"
    ],
    "positions": ["RB"],
    "years": [
      1939
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Tom Harmon",
    "schools": [
      "Michigan"
    ],
    "positions": ["RB"],
    "years": [
      1939,
      1940
    ],
    "heisman": true,
    "heismanYear": 1940,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Frank Albert",
    "schools": [
      "Stanford"
    ],
    "positions": [],
    "years": [
      1940
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Holt Rast",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1941
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bob Dove",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1941,
      1942
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dick Wildung",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1941,
      1942
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Endicott Peabody",
    "schools": [
      "Harvard"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1941
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bruce Smith",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1941
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Frank Sinkwich",
    "schools": [
      "Georgia"
    ],
    "positions": ["RB"],
    "years": [
      1941,
      1942
    ],
    "heisman": true,
    "heismanYear": 1942,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dave Schreiner",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1942
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Albert Wistert",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1942
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chuck Taylor",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1942
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Joe Domnanovich",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1942
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bill Hackett",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1944
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Les Horvath",
    "schools": [
      "Ohio State"
    ],
    "positions": ["QB"],
    "years": [
      1944
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Glenn Davis",
    "schools": [
      "Army"
    ],
    "positions": ["RB"],
    "years": [
      1944,
      1945,
      1946
    ],
    "heisman": true,
    "heismanYear": 1946,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Doc Blanchard",
    "schools": [
      "Army"
    ],
    "positions": ["RB"],
    "years": [
      1944,
      1945,
      1946
    ],
    "heisman": true,
    "heismanYear": 1945,
    "multiAA": true,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Tex Coulter",
    "schools": [
      "Army"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1945
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Warren Amling",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1945
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Vaughn Mancha",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1945
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Alex Agase",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1946
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Lujack",
    "schools": [
      "Notre Dame"
    ],
    "positions": ["QB"],
    "years": [
      1946,
      1947
    ],
    "heisman": true,
    "heismanYear": 1947,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Charley Trippi",
    "schools": [
      "Georgia"
    ],
    "positions": [],
    "years": [
      1946
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Dick Rifenburg",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1948
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Leon Hart",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1948,
      1949
    ],
    "heisman": true,
    "heismanYear": 1949,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Leo Nomellini",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1948,
      1949
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Buddy Burris",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1948
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chuck Bednarik",
    "schools": [
      "Penn"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1948
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Doak Walker",
    "schools": [
      "SMU"
    ],
    "positions": ["RB"],
    "years": [
      1948,
      1949
    ],
    "heisman": true,
    "multiAA": true,
    "natChamp": false,
    "hof": true,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Clayton Tonnemaker",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1949
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Emil Sitko",
    "schools": [
      "Notre Dame"
    ],
    "positions": [],
    "years": [
      1949
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Arnold Galiffa",
    "schools": [
      "Army"
    ],
    "positions": [],
    "years": [
      1949
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dan Foldberg",
    "schools": [
      "Army"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1950
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bud McFadin",
    "schools": [
      "Texas"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1950
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jerry Groom",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1950
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Vic Janowicz",
    "schools": [
      "Ohio State"
    ],
    "positions": ["RB"],
    "years": [
      1950
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bill McColl",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1951
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Don Coleman",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1951
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dick Kazmaier",
    "schools": [
      "Princeton"
    ],
    "positions": ["RB"],
    "years": [
      1951
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Don Dohoney",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1953
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "J.D. Roberts",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1953
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Paul Giel",
    "schools": [
      "Minnesota"
    ],
    "positions": [],
    "years": [
      1953
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "J.C. Caroline",
    "schools": [
      "Illinois"
    ],
    "positions": [],
    "years": [
      1953
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Max Boydston",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1954
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Kurt Burris",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1954
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ralph Guglielmi",
    "schools": [
      "Notre Dame"
    ],
    "positions": [],
    "years": [
      1954
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Howard Cassady",
    "schools": [
      "Ohio State"
    ],
    "positions": ["RB"],
    "years": [
      1954,
      1955
    ],
    "heisman": true,
    "heismanYear": 1955,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Alan Ameche",
    "schools": [
      "Wisconsin"
    ],
    "positions": ["RB"],
    "years": [
      1954
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ron Kramer",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1955
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Norman Masters",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1955
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bo Bolinger",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1955
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Bill Krisher",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1957
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dan Currie",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1957
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John David Crow",
    "schools": [
      "Texas A&M"
    ],
    "positions": ["RB"],
    "years": [
      1957
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Walt Kowalczyk",
    "schools": [
      "Michigan State"
    ],
    "positions": [],
    "years": [
      1957
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bob Anderson",
    "schools": [
      "Army"
    ],
    "positions": [],
    "years": [
      1957
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Guzik",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1958
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bob Harrison",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1958
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Randy Duncan",
    "schools": [
      "Iowa"
    ],
    "positions": [],
    "years": [
      1958
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Pete Dawkins",
    "schools": [
      "Army"
    ],
    "positions": ["RB"],
    "years": [
      1958
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Mike Ditka",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1960
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Tom Brown",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1960
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Joe Bellino",
    "schools": [
      "Navy"
    ],
    "positions": ["RB"],
    "years": [
      1960
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Bob Ferguson",
    "schools": [
      "Ohio State"
    ],
    "positions": [],
    "years": [
      1960,
      1961
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Billy Neighbors",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1961
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Roy Winston",
    "schools": [
      "LSU"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1961
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ernie Davis",
    "schools": [
      "Syracuse"
    ],
    "positions": ["RB"],
    "years": [
      1961
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jimmy Saxton",
    "schools": [
      "Texas"
    ],
    "positions": [],
    "years": [
      1961
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Hal Bedsole",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1962
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Bobby Bell",
    "schools": [
      "Minnesota"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1962
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Johnny Treadwell",
    "schools": [
      "Texas"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1962
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Lee Roy Jordan",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1962
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Terry Baker",
    "schools": [
      "Oregon St."
    ],
    "positions": ["QB"],
    "years": [
      1962
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "Jerry Stovall",
    "schools": [
      "LSU"
    ],
    "positions": [],
    "years": [
      1962
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jack Snow",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1964
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Larry Kramer",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1964
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Huarte",
    "schools": [
      "Notre Dame"
    ],
    "positions": ["QB"],
    "years": [
      1964
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Gary Beban",
    "schools": [
      "UCLA"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1967
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award"]
  },
  {
    "name": "O.J. Simpson",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1967,
      1968
    ],
    "heisman": true,
    "heismanYear": 1968,
    "multiAA": true,
    "natChamp": true,
    "hof": true,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Larry Csonka",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1967
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Granville Liggins",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1967
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Terry Hanratty",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1968
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ted Kwalick",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      1968
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dave Foley",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1968
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Steve Owens",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1969
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Walter Camp Award"]
  },
  {
    "name": "Mike Reid",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1969
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Outland Trophy"]
  },
  {
    "name": "Mike McCoy",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1969
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jack Tatum",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1969,
      1970
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jim Plunkett",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1970
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Steve Worster",
    "schools": [
      "Texas"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1970
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Dan Dierdorf",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1970
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Jim Stillwagon",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1970
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy", "Lombardi Award"]
  },
  {
    "name": "Jack Ham",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1970
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Pat Sullivan",
    "schools": [
      "Auburn"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1971
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Walter Camp Award"]
  },
  {
    "name": "Walt Patulski",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1971
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award"]
  },
  {
    "name": "Mike Taylor",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1971
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tommy Casanova",
    "schools": [
      "LSU"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1971
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Lynn Swann",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1973
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Dave Casper",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      1973
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": true
  },
  {
    "name": "John Hicks",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1973
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy", "Lombardi Award"]
  },
  {
    "name": "John Cappelletti",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1973
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Roosevelt Leaks",
    "schools": [
      "Texas"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1973
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "John Dutton",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1973
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Lucious Selmon",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1973
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Randy Gradishar",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1973
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Archie Griffin",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1974,
      1975
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Joe Washington",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1974
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Anthony Davis",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1974
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Rod Shoate",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1974
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Dave Brown",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1974
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ken MacAfee",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      1976,
      1977
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Walter Camp Award"]
  },
  {
    "name": "Ross Browner",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1976,
      1977
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Outland Trophy", "Lombardi Award"]
  },
  {
    "name": "Earl Campbell",
    "schools": [
      "Texas"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1977
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Davey O'Brien Award"]
  },
  {
    "name": "Chris Ward",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1977
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Charles White",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1979
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Billy Sims",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1979,
      1978
    ],
    "heisman": true,
    "heismanYear": 1978,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Walter Camp Award", "Davey O'Brien Award"]
  },
  {
    "name": "Junior Miller",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      1979
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Hugh Green",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1979,
      1980
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Lombardi Award"]
  },
  {
    "name": "George Rogers",
    "schools": [
      "South Carolina"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1980
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Mark May",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1980
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Ronnie Lott",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1980
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Irving Fryar",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1983
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bill Fralic",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1983,
      1984
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Mike Rozier",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1983
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Rick Bryan",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1983
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Doug Flutie",
    "schools": [
      "Boston College"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1984
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award"]
  },
  {
    "name": "Keith Byars",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1984
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Jerry Gray",
    "schools": [
      "Texas"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1984
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Cris Carter",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1986
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Keith Jackson",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      1986,
      1987
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Vinny Testaverde",
    "schools": [
      "Miami (FL)"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1986
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award"]
  },
  {
    "name": "Cornelius Bennett",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1986
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award"]
  },
  {
    "name": "Tim Brown",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1987
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Walter Camp Award"]
  },
  {
    "name": "Don McPherson",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1987
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Chris Spielman",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1987
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award"]
  },
  {
    "name": "Andre Ware",
    "schools": [
      "Houston"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1989
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Davey O'Brien Award"]
  },
  {
    "name": "Chris Zorich",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1989,
      1990
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award"]
  },
  {
    "name": "Percy Snow",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1989
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award", "Lombardi Award"]
  },
  {
    "name": "Keith McCants",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1989
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Todd Lyght",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1989
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Mark Carrier",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1989
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Jim Thorpe Award"]
  },
  {
    "name": "Raghib 'Rocket' Ismail",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1990
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Ty Detmer",
    "schools": [
      "BYU"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1990,
      1991
    ],
    "heisman": true,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Davey O'Brien Award"]
  },
  {
    "name": "Tripp Welborne",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1990
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Desmond Howard",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1991
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Greg Skrepenak",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1991
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chris Gedney",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      1992
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Will Shields",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1992
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Gino Torretta",
    "schools": [
      "Miami (FL)"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1992
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Garrison Hearst",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1992
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Marcus Allen",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1981
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Maxwell Award", "Walter Camp Award"]
  },
  {
    "name": "Kenneth Sims",
    "schools": [
      "Texas"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1981
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award"]
  },
  {
    "name": "Zach Wiegert",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      1994
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Kerry Collins",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1994
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Davey O'Brien Award"]
  },
  {
    "name": "Rashaan Salaam",
    "schools": [
      "Colorado"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1994
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Walter Camp Award", "Doak Walker Award"]
  },
  {
    "name": "Ki-Jana Carter",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1994
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Dana Howard",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1994
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Keyshawn Johnson",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      1995
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Tommie Frazier",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      1995
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Eddie George",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1995
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Doak Walker Award"]
  },
  {
    "name": "Ricky Williams",
    "schools": [
      "Texas"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      1997,
      1998
    ],
    "heisman": true,
    "heismanYear": 1998,
    "multiAA": true,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Doak Walker Award"]
  },
  {
    "name": "Charles Woodson",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1997
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": true,
    "awards": ["Walter Camp Award", "Jim Thorpe Award", "Chuck Bednarik Award", "Bronko Nagurski Trophy"]
  },
  {
    "name": "Andy Katzenmoyer",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      1997
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Champ Bailey",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1998
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Bronko Nagurski Trophy"]
  },
  {
    "name": "Antoine Winfield",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      1998
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Jim Thorpe Award"]
  },
  {
    "name": "Josh Heupel",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2000
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Walter Camp Award"]
  },
  {
    "name": "Dwight Freeney",
    "schools": [
      "Syracuse"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2001
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Quentin Jammer",
    "schools": [
      "Texas"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2001
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Roy Williams",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2001
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Jim Thorpe Award", "Bronko Nagurski Trophy"]
  },
  {
    "name": "Larry Fitzgerald",
    "schools": [
      "Pittsburgh"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2003
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Walter Camp Award", "Fred Biletnikoff Award"]
  },
  {
    "name": "Robert Gallery",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2003
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Jason White",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2003
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Tommie Harris",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2003
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Lombardi Award"]
  },
  {
    "name": "Teddy Lehman",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2003
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award", "Chuck Bednarik Award"]
  },
  {
    "name": "Derrick Strait",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2003
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Jim Thorpe Award", "Bronko Nagurski Trophy"]
  },
  {
    "name": "Braylon Edwards",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2004
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "Matt Leinart",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2004
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Walter Camp Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Adrian Peterson",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2004
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Derrick Johnson",
    "schools": [
      "Texas"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2004
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award", "Bronko Nagurski Trophy"]
  },
  {
    "name": "Joe Thomas",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2006
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Troy Smith",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2006
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Walter Camp Award", "Davey O'Brien Award"]
  },
  {
    "name": "James Laurinaitis",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2006
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award", "Bronko Nagurski Trophy"]
  },
  {
    "name": "Tim Tebow",
    "schools": [
      "Florida"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2007
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Davey O'Brien Award"]
  },
  {
    "name": "Jake Long",
    "schools": [
      "Michigan"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2007
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Glenn Dorsey",
    "schools": [
      "LSU"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2007
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy", "Bronko Nagurski Trophy", "Lombardi Award"]
  },
  {
    "name": "Sedrick Ellis",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2007
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Golden Tate",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2009
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "Toby Gerhart",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2009
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Mark Ingram",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2009
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Ndamukong Suh",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2009
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy", "Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award"]
  },
  {
    "name": "Rolando McClain",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2009
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Drew Butler",
    "schools": [
      "Georgia"
    ],
    "positions": [],
    "years": [
      2009
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Ray Guy Award"]
  },
  {
    "name": "Cam Newton",
    "schools": [
      "Auburn"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2010
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award"]
  },
  {
    "name": "Gabe Carimi",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2010
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Greg Jones",
    "schools": [
      "Michigan State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2010
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Patrick Peterson",
    "schools": [
      "LSU"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2010
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Jim Thorpe Award", "Chuck Bednarik Award"]
  },
  {
    "name": "Prince Amukamara",
    "schools": [
      "Nebraska"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2010
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Robert Griffin III",
    "schools": [
      "Baylor"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2011
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Davey O'Brien Award"]
  },
  {
    "name": "Barrett Jones",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2011
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Outland Trophy", "Rimington Trophy"]
  },
  {
    "name": "David DeCastro",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2011
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Trent Richardson",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2011
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Whitney Mercilus",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2011
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Ted Hendricks Award"]
  },
  {
    "name": "Mark Barron",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2011
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Morris Claiborne",
    "schools": [
      "LSU"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2011
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Jim Thorpe Award"]
  },
  {
    "name": "Marqise Lee",
    "schools": [
      "Southern California"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2012
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "Zach Ertz",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      2012
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Chance Warmack",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2012
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Jarvis Jones",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2012
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Manti Te'o",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2012
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Butkus Award", "Chuck Bednarik Award", "Bronko Nagurski Trophy", "Lombardi Award"]
  },
  {
    "name": "Amari Cooper",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2014
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Fred Biletnikoff Award"]
  },
  {
    "name": "Marcus Mariota",
    "schools": [
      "Oregon"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2014
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award", "Johnny Unitas Golden Arm Award"]
  },
  {
    "name": "Melvin Gordon",
    "schools": [
      "Wisconsin"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2014
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Brandon Scherff",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2014
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Outland Trophy"]
  },
  {
    "name": "Joey Bosa",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2014,
      2015
    ],
    "heisman": false,
    "multiAA": true,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Landon Collins",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2014
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Reggie Ragland",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2015
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Jaylon Smith",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2015
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Derrick Henry",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2015
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Doak Walker Award"]
  },
  {
    "name": "Baker Mayfield",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2017
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Davey O'Brien Award"]
  },
  {
    "name": "Bryce Love",
    "schools": [
      "Stanford"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Doak Walker Award", "Lombardi Award"]
  },
  {
    "name": "Mark Andrews",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "TE"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["John Mackey Award"]
  },
  {
    "name": "Quenton Nelson",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Orlando Brown Jr.",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Billy Price",
    "schools": [
      "Ohio State"
    ],
    "positions": [
      "OL"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Rimington Trophy"]
  },
  {
    "name": "Josey Jewell",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Roquan Smith",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Minkah Fitzpatrick",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Jim Thorpe Award", "Chuck Bednarik Award"]
  },
  {
    "name": "Josh Jackson",
    "schools": [
      "Iowa"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Michael Dickson",
    "schools": [
      "Texas"
    ],
    "positions": [],
    "years": [
      2017
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Ray Guy Award"]
  },
  {
    "name": "Kyler Murray",
    "schools": [
      "Oklahoma"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2018
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Davey O'Brien Award"]
  },
  {
    "name": "Devin White",
    "schools": [
      "LSU"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2018
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Butkus Award"]
  },
  {
    "name": "Deionte Thompson",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2018
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Greedy Williams",
    "schools": [
      "LSU"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2018
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "DeVonta Smith",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "WR"
    ],
    "years": [
      2020
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Maxwell Award", "Walter Camp Award", "Fred Biletnikoff Award"]
  },
  {
    "name": "Najee Harris",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2020
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Micah Parsons",
    "schools": [
      "Penn State"
    ],
    "positions": [
      "LB"
    ],
    "years": [
      2020
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Christian Barmore",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2020
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Patrick Surtain II",
    "schools": [
      "Alabama"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2020
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Bijan Robinson",
    "schools": [
      "Texas"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2022
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false,
    "awards": ["Doak Walker Award"]
  },
  {
    "name": "Jalen Carter",
    "schools": [
      "Georgia"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      2022
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Devon Witherspoon",
    "schools": [
      "Illinois"
    ],
    "positions": [
      "DB"
    ],
    "years": [
      2022
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Fernando Mendoza",
    "schools": [
      "Indiana"
    ],
    "positions": [
      "QB"
    ],
    "years": [
      2025
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": true,
    "hof": false
  },
  {
    "name": "Jeremiyah Love",
    "schools": [
      "Notre Dame"
    ],
    "positions": [
      "RB"
    ],
    "years": [
      2025
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  },
  {
    "name": "Bruce Smith",
    "schools": [
      "Virginia Tech"
    ],
    "positions": [
      "DL"
    ],
    "years": [
      1984
    ],
    "heisman": false,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Steve Spurrier",
    "schools": [
      "Florida"
    ],
    "positions": ["QB"],
    "years": [
      1966
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": true
  },
  {
    "name": "Caleb Williams",
    "schools": [
      "Oklahoma",
      "USC"
    ],
    "positions": ["QB"],
    "years": [
      2022
    ],
    "heisman": true,
    "multiAA": false,
    "natChamp": false,
    "hof": false
  }
];

window.CFB_GRID_CRITERIA = (function () {
  var POSITION_LABELS = { QB: "Quarterback", RB: "Running Back", WR: "Wide Receiver / End", TE: "Tight End", OL: "Offensive Line", DL: "Defensive Line", LB: "Linebacker", DB: "Defensive Back" };
  var ERAS = [
    { id: "era_pre1950", label: "All-American Before 1950", lo: 0, hi: 1949 },
    { id: "era_1950_1979", label: "All-American 1950-1979", lo: 1950, hi: 1979 },
    { id: "era_1980_1999", label: "All-American 1980-1999", lo: 1980, hi: 1999 },
    { id: "era_2000_2025", label: "All-American 2000-2025", lo: 2000, hi: 2025 }
  ];

  var schoolCriteria = Object.keys(window.CFB_GRID_SCHOOL_CODES || {}).map(function (school) {
    return {
      id: "school_" + school.replace(/[^a-z0-9]+/gi, "_"),
      type: "school",
      school: school,
      label: school,
      test: function (p) { return p.schools.indexOf(school) !== -1; }
    };
  });

  var statCriteria = Object.keys(POSITION_LABELS).map(function (pos) {
    return { id: "pos_" + pos, type: "stat", label: "Consensus All-America " + POSITION_LABELS[pos], test: function (p) { return p.positions.indexOf(pos) !== -1; } };
  }).concat([
    { id: "heisman", type: "stat", label: "Heisman Trophy Winner", test: function (p) { return !!p.heisman; } },
    { id: "multi_aa", type: "stat", label: "Multi-Year Consensus All-American", test: function (p) { return !!p.multiAA; } },
    { id: "nat_champ", type: "stat", label: "National Champion", test: function (p) { return !!p.natChamp; } },
    { id: "pro_hof", type: "stat", label: "Pro Football Hall of Famer", test: function (p) { return !!p.hof; } }
  ]).concat(ERAS.map(function (e) {
    return { id: e.id, type: "era", label: e.label, test: function (p) { return p.years.some(function (y) { return y >= e.lo && y <= e.hi; }); } };
  }));

  var conferenceMap = window.CFB_GRID_SCHOOL_CONFERENCE || {};
  var conferences = Array.from(new Set(Object.keys(conferenceMap).map(function (s) { return conferenceMap[s]; })));
  var conferenceCriteria = conferences.map(function (conf) {
    return {
      id: "conf_" + conf.replace(/[^a-z0-9]+/gi, "_"),
      type: "stat",
      label: conf + " School",
      test: function (p) { return p.schools.some(function (s) { return conferenceMap[s] === conf; }); }
    };
  });

  var AWARDS = [
    "Maxwell Award", "Outland Trophy", "Lombardi Award", "Walter Camp Award", "Davey O'Brien Award",
    "Butkus Award", "Jim Thorpe Award", "Johnny Unitas Golden Arm Award", "Doak Walker Award",
    "Lou Groza Award", "Bronko Nagurski Trophy", "Chuck Bednarik Award", "Fred Biletnikoff Award",
    "Rimington Trophy", "Ray Guy Award", "John Mackey Award", "Ted Hendricks Award"
  ];
  var awardCriteria = AWARDS.map(function (award) {
    return {
      id: "award_" + award.replace(/[^a-z0-9]+/gi, "_"),
      type: "stat",
      label: award + " Winner",
      test: function (p) { return !!(p.awards && p.awards.indexOf(award) !== -1); }
    };
  });

  var draftCriteria = [
    { id: "draft_r1", type: "stat", label: "NFL First-Round Draft Pick", test: function (p) { return p.draftRound === 1; } }
  ];

  statCriteria = statCriteria.concat(conferenceCriteria, awardCriteria, draftCriteria);

  return { team: schoolCriteria, stat: statCriteria, all: schoolCriteria.concat(statCriteria) };
})();
