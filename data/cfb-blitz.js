// College Football Blitz mode data: Sporcle-style "name as many as you can
// before time runs out" list challenges, college edition. Same shape/matching
// rules as data/blitz.js (case/punctuation-insensitive, checks `answer` and
// every string in `aliases`). Built from the user's CFB_Trivia_Cheat_Code-11.xlsx
// reference tables (Heisman winners, national champions, coaching records,
// career/season FBS stat leaders, All-America selections by era, major awards,
// winningest/championship-winning coaches by school). All-America lists are
// split into eras (1889-1949, 1950-1979, 1980-1999, 2000-2025) since the
// underlying dataset now covers every year of college football, 1889-2025 —
// a single un-split list per position would otherwise span 137 years.
window.CFB_BLITZ_LISTS = [
  {
    "id": "cfb_heisman_since_2010",
    "title": "Heisman Trophy Winners Since 2010",
    "prompt": "Name a Heisman Trophy winner from 2010 to today.",
    "answers": [
      {
        "answer": "Cam Newton",
        "aliases": [
          "Newton"
        ]
      },
      {
        "answer": "Robert Griffin III",
        "aliases": [
          "III"
        ]
      },
      {
        "answer": "Johnny Manziel",
        "aliases": [
          "Manziel"
        ]
      },
      {
        "answer": "Jameis Winston",
        "aliases": [
          "Winston"
        ]
      },
      {
        "answer": "Marcus Mariota",
        "aliases": [
          "Mariota"
        ]
      },
      {
        "answer": "Derrick Henry",
        "aliases": [
          "Henry"
        ]
      },
      {
        "answer": "Lamar Jackson",
        "aliases": [
          "Jackson"
        ]
      },
      {
        "answer": "Baker Mayfield",
        "aliases": [
          "Mayfield"
        ]
      },
      {
        "answer": "Kyler Murray",
        "aliases": [
          "Murray"
        ]
      },
      {
        "answer": "Joe Burrow",
        "aliases": [
          "Burrow"
        ]
      },
      {
        "answer": "DeVonta Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Bryce Young",
        "aliases": [
          "Young"
        ]
      },
      {
        "answer": "Caleb Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Jayden Daniels",
        "aliases": [
          "Daniels"
        ]
      },
      {
        "answer": "Travis Hunter",
        "aliases": [
          "Hunter"
        ]
      },
      {
        "answer": "Fernando Mendoza",
        "aliases": [
          "Mendoza"
        ]
      }
    ]
  },
  {
    "id": "cfb_champs_since_2010",
    "title": "National Champions Since 2010",
    "prompt": "Name a team that won the college football national championship since 2010.",
    "answers": [
      {
        "answer": "Indiana",
        "aliases": []
      },
      {
        "answer": "Ohio State",
        "aliases": [
          "State"
        ]
      },
      {
        "answer": "Michigan",
        "aliases": []
      },
      {
        "answer": "Georgia",
        "aliases": []
      },
      {
        "answer": "Alabama",
        "aliases": []
      },
      {
        "answer": "LSU",
        "aliases": []
      },
      {
        "answer": "Clemson",
        "aliases": []
      },
      {
        "answer": "Florida State",
        "aliases": [
          "State"
        ]
      },
      {
        "answer": "Auburn",
        "aliases": []
      }
    ]
  },
  {
    "id": "cfb_coaches_3plus_titles",
    "title": "Coaches With 3+ National Championships",
    "prompt": "Name a head coach who won 3 or more college football national championships (career total, any schools).",
    "answers": [
      {
        "answer": "Barry Switzer",
        "aliases": [
          "Switzer"
        ]
      },
      {
        "answer": "Bear Bryant",
        "aliases": [
          "Bryant"
        ]
      },
      {
        "answer": "Bernie Bierman",
        "aliases": [
          "Bierman"
        ]
      },
      {
        "answer": "Bud Wilkinson",
        "aliases": [
          "Wilkinson"
        ]
      },
      {
        "answer": "Darrell Royal",
        "aliases": [
          "Royal"
        ]
      },
      {
        "answer": "Frank Leahy",
        "aliases": [
          "Leahy"
        ]
      },
      {
        "answer": "John McKay",
        "aliases": [
          "McKay"
        ]
      },
      {
        "answer": "Nick Saban",
        "aliases": [
          "Saban"
        ]
      },
      {
        "answer": "Tom Osborne",
        "aliases": [
          "Osborne"
        ]
      },
      {
        "answer": "Urban Meyer",
        "aliases": [
          "Meyer"
        ]
      },
      {
        "answer": "Woody Hayes",
        "aliases": [
          "Hayes"
        ]
      }
    ]
  },
  {
    "id": "cfb_champ_coaches_any",
    "title": "National-Championship-Winning Coaches",
    "prompt": "Name any head coach who has won a college football national championship (1936-2025 poll/BCS/Playoff era).",
    "answers": [
      {
        "answer": "Ara Parseghian",
        "aliases": [
          "Parseghian"
        ]
      },
      {
        "answer": "Barry Switzer",
        "aliases": [
          "Switzer"
        ]
      },
      {
        "answer": "Bear Bryant",
        "aliases": [
          "Bryant"
        ]
      },
      {
        "answer": "Ben Schwartzwalder",
        "aliases": [
          "Schwartzwalder"
        ]
      },
      {
        "answer": "Bennie Oosterbaan",
        "aliases": [
          "Oosterbaan"
        ]
      },
      {
        "answer": "Bernie Bierman",
        "aliases": [
          "Bierman"
        ]
      },
      {
        "answer": "Biggie Munn",
        "aliases": [
          "Munn"
        ]
      },
      {
        "answer": "Bill McCartney",
        "aliases": [
          "McCartney"
        ]
      },
      {
        "answer": "Bob Devaney",
        "aliases": [
          "Devaney"
        ]
      },
      {
        "answer": "Bob Stoops",
        "aliases": [
          "Stoops"
        ]
      },
      {
        "answer": "Bobby Bowden",
        "aliases": [
          "Bowden"
        ]
      },
      {
        "answer": "Bobby Ross",
        "aliases": [
          "Ross"
        ]
      },
      {
        "answer": "Bud Wilkinson",
        "aliases": [
          "Wilkinson"
        ]
      },
      {
        "answer": "Curt Cignetti",
        "aliases": [
          "Cignetti"
        ]
      },
      {
        "answer": "Dabo Swinney",
        "aliases": [
          "Swinney"
        ]
      },
      {
        "answer": "Dan Devine",
        "aliases": [
          "Devine"
        ]
      },
      {
        "answer": "Danny Ford",
        "aliases": [
          "Ford"
        ]
      },
      {
        "answer": "Darrell Royal",
        "aliases": [
          "Royal"
        ]
      },
      {
        "answer": "Dennis Erickson",
        "aliases": [
          "Erickson"
        ]
      },
      {
        "answer": "Don James",
        "aliases": [
          "James"
        ]
      },
      {
        "answer": "Duffy Daugherty",
        "aliases": [
          "Daugherty"
        ]
      },
      {
        "answer": "Dutch Meyer",
        "aliases": [
          "Meyer"
        ]
      },
      {
        "answer": "Ed Orgeron",
        "aliases": [
          "Orgeron"
        ]
      },
      {
        "answer": "Frank Leahy",
        "aliases": [
          "Leahy"
        ]
      },
      {
        "answer": "Gene Chizik",
        "aliases": [
          "Chizik"
        ]
      },
      {
        "answer": "Gene Stallings",
        "aliases": [
          "Stallings"
        ]
      },
      {
        "answer": "Homer Norton",
        "aliases": [
          "Norton"
        ]
      },
      {
        "answer": "Howard Schnellenberger",
        "aliases": [
          "Schnellenberger"
        ]
      },
      {
        "answer": "Jim Harbaugh",
        "aliases": [
          "Harbaugh"
        ]
      },
      {
        "answer": "Jim Tatum",
        "aliases": [
          "Tatum"
        ]
      },
      {
        "answer": "Jim Tressel",
        "aliases": [
          "Tressel"
        ]
      },
      {
        "answer": "Jimbo Fisher",
        "aliases": [
          "Fisher"
        ]
      },
      {
        "answer": "Jimmy Johnson",
        "aliases": [
          "Johnson"
        ]
      },
      {
        "answer": "Jock Sutherland",
        "aliases": [
          "Sutherland"
        ]
      },
      {
        "answer": "Joe Paterno",
        "aliases": [
          "Paterno"
        ]
      },
      {
        "answer": "John McKay",
        "aliases": [
          "McKay"
        ]
      },
      {
        "answer": "John Robinson",
        "aliases": [
          "Robinson"
        ]
      },
      {
        "answer": "Johnny Majors",
        "aliases": [
          "Majors"
        ]
      },
      {
        "answer": "Kirby Smart",
        "aliases": [
          "Smart"
        ]
      },
      {
        "answer": "LaVell Edwards",
        "aliases": [
          "Edwards"
        ]
      },
      {
        "answer": "Larry Coker",
        "aliases": [
          "Coker"
        ]
      },
      {
        "answer": "Les Miles",
        "aliases": [
          "Miles"
        ]
      },
      {
        "answer": "Lloyd Carr",
        "aliases": [
          "Carr"
        ]
      },
      {
        "answer": "Lou Holtz",
        "aliases": [
          "Holtz"
        ]
      },
      {
        "answer": "Mack Brown",
        "aliases": [
          "Brown"
        ]
      },
      {
        "answer": "Murray Warmath",
        "aliases": [
          "Warmath"
        ]
      },
      {
        "answer": "Nick Saban",
        "aliases": [
          "Saban"
        ]
      },
      {
        "answer": "Paul Brown",
        "aliases": [
          "Brown"
        ]
      },
      {
        "answer": "Paul Dietzel",
        "aliases": [
          "Dietzel"
        ]
      },
      {
        "answer": "Pete Carroll",
        "aliases": [
          "Carroll"
        ]
      },
      {
        "answer": "Phillip Fulmer",
        "aliases": [
          "Fulmer"
        ]
      },
      {
        "answer": "Red Blaik",
        "aliases": [
          "Blaik"
        ]
      },
      {
        "answer": "Red Sanders",
        "aliases": [
          "Sanders"
        ]
      },
      {
        "answer": "Robert Neyland",
        "aliases": [
          "Neyland"
        ]
      },
      {
        "answer": "Ryan Day",
        "aliases": [
          "Day"
        ]
      },
      {
        "answer": "Shug Jordan",
        "aliases": [
          "Jordan"
        ]
      },
      {
        "answer": "Steve Spurrier",
        "aliases": [
          "Spurrier"
        ]
      },
      {
        "answer": "Tom Osborne",
        "aliases": [
          "Osborne"
        ]
      },
      {
        "answer": "Urban Meyer",
        "aliases": [
          "Meyer"
        ]
      },
      {
        "answer": "Vince Dooley",
        "aliases": [
          "Dooley"
        ]
      },
      {
        "answer": "Woody Hayes",
        "aliases": [
          "Hayes"
        ]
      }
    ]
  },
  {
    "id": "cfb_winningest_by_school",
    "title": "Winningest Coach in Program History (Major Programs)",
    "prompt": "Name a coach who is the winningest (most total wins) coach in a major program's history.",
    "answers": [
      {
        "answer": "Bear Bryant",
        "aliases": [
          "Bryant"
        ]
      },
      {
        "answer": "Vince Dooley",
        "aliases": [
          "Dooley"
        ]
      },
      {
        "answer": "Charles McClendon",
        "aliases": [
          "McClendon"
        ]
      },
      {
        "answer": "Shug Jordan",
        "aliases": [
          "Jordan"
        ]
      },
      {
        "answer": "Steve Spurrier",
        "aliases": [
          "Spurrier"
        ]
      },
      {
        "answer": "Robert Neyland",
        "aliases": [
          "Neyland"
        ]
      },
      {
        "answer": "R.C. Slocum",
        "aliases": [
          "Slocum"
        ]
      },
      {
        "answer": "Johnny Vaught",
        "aliases": [
          "Vaught"
        ]
      },
      {
        "answer": "Mark Stoops",
        "aliases": [
          "Stoops"
        ]
      },
      {
        "answer": "Gary Pinkel",
        "aliases": [
          "Pinkel"
        ]
      },
      {
        "answer": "Frank Broyles",
        "aliases": [
          "Broyles"
        ]
      },
      {
        "answer": "Dan McGugin",
        "aliases": [
          "McGugin"
        ]
      },
      {
        "answer": "Allyn McKeen",
        "aliases": [
          "McKeen"
        ]
      },
      {
        "answer": "Bob Stoops",
        "aliases": [
          "Stoops"
        ]
      },
      {
        "answer": "Darrell Royal",
        "aliases": [
          "Royal"
        ]
      },
      {
        "answer": "Bo Schembechler",
        "aliases": [
          "Schembechler"
        ]
      },
      {
        "answer": "Woody Hayes",
        "aliases": [
          "Hayes"
        ]
      },
      {
        "answer": "Joe Paterno",
        "aliases": [
          "Paterno"
        ]
      },
      {
        "answer": "Tom Osborne",
        "aliases": [
          "Osborne"
        ]
      },
      {
        "answer": "Barry Alvarez",
        "aliases": [
          "Alvarez"
        ]
      },
      {
        "answer": "Kirk Ferentz",
        "aliases": [
          "Ferentz"
        ]
      },
      {
        "answer": "Duffy Daugherty",
        "aliases": [
          "Daugherty"
        ]
      },
      {
        "answer": "Bernie Bierman",
        "aliases": [
          "Bierman"
        ]
      },
      {
        "answer": "Bob Zuppke",
        "aliases": [
          "Zuppke"
        ]
      },
      {
        "answer": "Bill Mallory",
        "aliases": [
          "Mallory"
        ]
      },
      {
        "answer": "Jack Mollenkopf",
        "aliases": [
          "Mollenkopf"
        ]
      },
      {
        "answer": "Pat Fitzgerald",
        "aliases": [
          "Fitzgerald"
        ]
      },
      {
        "answer": "Greg Schiano",
        "aliases": [
          "Schiano"
        ]
      },
      {
        "answer": "John McKay",
        "aliases": [
          "McKay"
        ]
      },
      {
        "answer": "Terry Donahue",
        "aliases": [
          "Donahue"
        ]
      },
      {
        "answer": "Don James",
        "aliases": [
          "James"
        ]
      },
      {
        "answer": "Mike Bellotti",
        "aliases": [
          "Bellotti"
        ]
      },
      {
        "answer": "Mike Gundy",
        "aliases": [
          "Gundy"
        ]
      },
      {
        "answer": "Bill Snyder",
        "aliases": [
          "Snyder"
        ]
      },
      {
        "answer": "Gary Patterson",
        "aliases": [
          "Patterson"
        ]
      },
      {
        "answer": "Grant Teaff",
        "aliases": [
          "Teaff"
        ]
      },
      {
        "answer": "Don Nehlen",
        "aliases": [
          "Nehlen"
        ]
      },
      {
        "answer": "Dan McCarney",
        "aliases": [
          "McCarney"
        ]
      },
      {
        "answer": "Bill Yeoman",
        "aliases": [
          "Yeoman"
        ]
      },
      {
        "answer": "Dabo Swinney",
        "aliases": [
          "Swinney"
        ]
      },
      {
        "answer": "Bobby Bowden",
        "aliases": [
          "Bowden"
        ]
      },
      {
        "answer": "Andy Gustafson",
        "aliases": [
          "Gustafson"
        ]
      },
      {
        "answer": "Mack Brown",
        "aliases": [
          "Brown"
        ]
      },
      {
        "answer": "Dave Doeren",
        "aliases": [
          "Doeren"
        ]
      },
      {
        "answer": "Frank Beamer",
        "aliases": [
          "Beamer"
        ]
      },
      {
        "answer": "Bobby Dodd",
        "aliases": [
          "Dodd"
        ]
      },
      {
        "answer": "Jock Sutherland",
        "aliases": [
          "Sutherland"
        ]
      },
      {
        "answer": "Wallace Wade",
        "aliases": [
          "Wade"
        ]
      },
      {
        "answer": "Peahead Walker",
        "aliases": [
          "Walker"
        ]
      },
      {
        "answer": "Ben Schwartzwalder",
        "aliases": [
          "Schwartzwalder"
        ]
      },
      {
        "answer": "Bobby Petrino",
        "aliases": [
          "Petrino"
        ]
      },
      {
        "answer": "Andy Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Pop Warner",
        "aliases": [
          "Warner"
        ]
      },
      {
        "answer": "Knute Rockne",
        "aliases": [
          "Rockne"
        ]
      },
      {
        "answer": "Earl Blaik",
        "aliases": [
          "Blaik"
        ]
      },
      {
        "answer": "George Welsh",
        "aliases": [
          "Welsh"
        ]
      },
      {
        "answer": "LaVell Edwards",
        "aliases": [
          "Edwards"
        ]
      },
      {
        "answer": "Chris Petersen",
        "aliases": [
          "Petersen"
        ]
      },
      {
        "answer": "Bobby Pruett",
        "aliases": [
          "Pruett"
        ]
      },
      {
        "answer": "George O'Leary",
        "aliases": [
          "O'Leary"
        ]
      },
      {
        "answer": "Bill McCartney",
        "aliases": [
          "McCartney"
        ]
      },
      {
        "answer": "Kyle Whittingham",
        "aliases": [
          "Whittingham"
        ]
      },
      {
        "answer": "Dick Tomey",
        "aliases": [
          "Tomey"
        ]
      },
      {
        "answer": "Frank Kush",
        "aliases": [
          "Kush"
        ]
      },
      {
        "answer": "Mike Price",
        "aliases": [
          "Price"
        ]
      },
      {
        "answer": "Randy Edsall",
        "aliases": [
          "Edsall"
        ]
      },
      {
        "answer": "Mike Norvell",
        "aliases": [
          "Norvell"
        ]
      },
      {
        "answer": "Matty Bell",
        "aliases": [
          "Bell"
        ]
      },
      {
        "answer": "Fisher DeBerry",
        "aliases": [
          "DeBerry"
        ]
      },
      {
        "answer": "Frank Solich",
        "aliases": [
          "Solich"
        ]
      },
      {
        "answer": "Joe Novak",
        "aliases": [
          "Novak"
        ]
      },
      {
        "answer": "Rocky Long",
        "aliases": [
          "Long"
        ]
      },
      {
        "answer": "Pat Hill",
        "aliases": [
          "Hill"
        ]
      },
      {
        "answer": "Craig Bohl",
        "aliases": [
          "Bohl"
        ]
      },
      {
        "answer": "Sonny Lubick",
        "aliases": [
          "Lubick"
        ]
      },
      {
        "answer": "June Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Jerry Moore",
        "aliases": [
          "Moore"
        ]
      },
      {
        "answer": "Joe Moglia",
        "aliases": [
          "Moglia"
        ]
      },
      {
        "answer": "Jeff Bower",
        "aliases": [
          "Bower"
        ]
      },
      {
        "answer": "Jack Harbaugh",
        "aliases": [
          "Harbaugh"
        ]
      },
      {
        "answer": "-",
        "aliases": []
      }
    ]
  },
  {
    "id": "cfb_heisman_qbs",
    "title": "Heisman-Winning Quarterbacks",
    "prompt": "Name a Heisman Trophy winner who played quarterback.",
    "answers": [
      {
        "answer": "Davey O'Brien",
        "aliases": [
          "O'Brien"
        ]
      },
      {
        "answer": "Angelo Bertelli",
        "aliases": [
          "Bertelli"
        ]
      },
      {
        "answer": "John Lujack",
        "aliases": [
          "Lujack"
        ]
      },
      {
        "answer": "Paul Hornung",
        "aliases": [
          "Hornung"
        ]
      },
      {
        "answer": "Terry Baker",
        "aliases": [
          "Baker"
        ]
      },
      {
        "answer": "Roger Staubach",
        "aliases": [
          "Staubach"
        ]
      },
      {
        "answer": "John Huarte",
        "aliases": [
          "Huarte"
        ]
      },
      {
        "answer": "Steve Spurrier",
        "aliases": [
          "Spurrier"
        ]
      },
      {
        "answer": "Gary Beban",
        "aliases": [
          "Beban"
        ]
      },
      {
        "answer": "Jim Plunkett",
        "aliases": [
          "Plunkett"
        ]
      },
      {
        "answer": "Pat Sullivan",
        "aliases": [
          "Sullivan"
        ]
      },
      {
        "answer": "Doug Flutie",
        "aliases": [
          "Flutie"
        ]
      },
      {
        "answer": "Vinny Testaverde",
        "aliases": [
          "Testaverde"
        ]
      },
      {
        "answer": "Andre Ware",
        "aliases": [
          "Ware"
        ]
      },
      {
        "answer": "Ty Detmer",
        "aliases": [
          "Detmer"
        ]
      },
      {
        "answer": "Gino Torretta",
        "aliases": [
          "Torretta"
        ]
      },
      {
        "answer": "Charlie Ward",
        "aliases": [
          "Ward"
        ]
      },
      {
        "answer": "Danny Wuerffel",
        "aliases": [
          "Wuerffel"
        ]
      },
      {
        "answer": "Chris Weinke",
        "aliases": [
          "Weinke"
        ]
      },
      {
        "answer": "Eric Crouch",
        "aliases": [
          "Crouch"
        ]
      },
      {
        "answer": "Carson Palmer",
        "aliases": [
          "Palmer"
        ]
      },
      {
        "answer": "Jason White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "Matt Leinart",
        "aliases": [
          "Leinart"
        ]
      },
      {
        "answer": "Troy Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Tim Tebow",
        "aliases": [
          "Tebow"
        ]
      },
      {
        "answer": "Sam Bradford",
        "aliases": [
          "Bradford"
        ]
      },
      {
        "answer": "Cam Newton",
        "aliases": [
          "Newton"
        ]
      },
      {
        "answer": "Robert Griffin III",
        "aliases": [
          "III"
        ]
      },
      {
        "answer": "Johnny Manziel",
        "aliases": [
          "Manziel"
        ]
      },
      {
        "answer": "Jameis Winston",
        "aliases": [
          "Winston"
        ]
      },
      {
        "answer": "Marcus Mariota",
        "aliases": [
          "Mariota"
        ]
      },
      {
        "answer": "Lamar Jackson",
        "aliases": [
          "Jackson"
        ]
      },
      {
        "answer": "Baker Mayfield",
        "aliases": [
          "Mayfield"
        ]
      },
      {
        "answer": "Kyler Murray",
        "aliases": [
          "Murray"
        ]
      },
      {
        "answer": "Joe Burrow",
        "aliases": [
          "Burrow"
        ]
      },
      {
        "answer": "Bryce Young",
        "aliases": [
          "Young"
        ]
      },
      {
        "answer": "Caleb Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Jayden Daniels",
        "aliases": [
          "Daniels"
        ]
      },
      {
        "answer": "Fernando Mendoza",
        "aliases": [
          "Mendoza"
        ]
      }
    ]
  },
  {
    "id": "cfb_heisman_rbs",
    "title": "Heisman-Winning Running Backs",
    "prompt": "Name a Heisman Trophy winner who played running back (or halfback).",
    "answers": [
      {
        "answer": "Jay Berwanger",
        "aliases": [
          "Berwanger"
        ]
      },
      {
        "answer": "Clinton Frank",
        "aliases": [
          "Frank"
        ]
      },
      {
        "answer": "Nile Kinnick",
        "aliases": [
          "Kinnick"
        ]
      },
      {
        "answer": "Tom Harmon",
        "aliases": [
          "Harmon"
        ]
      },
      {
        "answer": "Bruce Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Frank Sinkwich",
        "aliases": [
          "Sinkwich"
        ]
      },
      {
        "answer": "Les Horvath",
        "aliases": [
          "Horvath"
        ]
      },
      {
        "answer": "Glenn Davis",
        "aliases": [
          "Davis"
        ]
      },
      {
        "answer": "Doak Walker",
        "aliases": [
          "Walker"
        ]
      },
      {
        "answer": "Vic Janowicz",
        "aliases": [
          "Janowicz"
        ]
      },
      {
        "answer": "Dick Kazmaier",
        "aliases": [
          "Kazmaier"
        ]
      },
      {
        "answer": "Billy Vessels",
        "aliases": [
          "Vessels"
        ]
      },
      {
        "answer": "John Lattner",
        "aliases": [
          "Lattner"
        ]
      },
      {
        "answer": "Howard Cassady",
        "aliases": [
          "Cassady"
        ]
      },
      {
        "answer": "John David Crow",
        "aliases": [
          "Crow"
        ]
      },
      {
        "answer": "Pete Dawkins",
        "aliases": [
          "Dawkins"
        ]
      },
      {
        "answer": "Billy Cannon",
        "aliases": [
          "Cannon"
        ]
      },
      {
        "answer": "Joe Bellino",
        "aliases": [
          "Bellino"
        ]
      },
      {
        "answer": "Ernie Davis",
        "aliases": [
          "Davis"
        ]
      },
      {
        "answer": "Mike Garrett",
        "aliases": [
          "Garrett"
        ]
      },
      {
        "answer": "O.J. Simpson",
        "aliases": [
          "Simpson"
        ]
      },
      {
        "answer": "Steve Owens",
        "aliases": [
          "Owens"
        ]
      },
      {
        "answer": "John Cappelletti",
        "aliases": [
          "Cappelletti"
        ]
      },
      {
        "answer": "Archie Griffin",
        "aliases": [
          "Griffin"
        ]
      },
      {
        "answer": "Tony Dorsett",
        "aliases": [
          "Dorsett"
        ]
      },
      {
        "answer": "Earl Campbell",
        "aliases": [
          "Campbell"
        ]
      },
      {
        "answer": "Billy Sims",
        "aliases": [
          "Sims"
        ]
      },
      {
        "answer": "Charles White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "George Rogers",
        "aliases": [
          "Rogers"
        ]
      },
      {
        "answer": "Marcus Allen",
        "aliases": [
          "Allen"
        ]
      },
      {
        "answer": "Herschel Walker",
        "aliases": [
          "Walker"
        ]
      },
      {
        "answer": "Mike Rozier",
        "aliases": [
          "Rozier"
        ]
      },
      {
        "answer": "Bo Jackson",
        "aliases": [
          "Jackson"
        ]
      },
      {
        "answer": "Barry Sanders",
        "aliases": [
          "Sanders"
        ]
      },
      {
        "answer": "Rashaan Salaam",
        "aliases": [
          "Salaam"
        ]
      },
      {
        "answer": "Eddie George",
        "aliases": [
          "George"
        ]
      },
      {
        "answer": "Ricky Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Ron Dayne",
        "aliases": [
          "Dayne"
        ]
      },
      {
        "answer": "Reggie Bush",
        "aliases": [
          "Bush"
        ]
      },
      {
        "answer": "Mark Ingram",
        "aliases": [
          "Ingram"
        ]
      },
      {
        "answer": "Derrick Henry",
        "aliases": [
          "Henry"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_qb_1889_1949",
    "title": "Consensus All-America Quarterbacks (1889-1949)",
    "prompt": "Name a consensus All-America quarterback selected between 1889 and 1949.",
    "answers": [
      {
        "answer": "Harry Stuhldreher",
        "aliases": [
          "Stuhldreher"
        ]
      },
      {
        "answer": "Davey O'Brien",
        "aliases": [
          "O'Brien"
        ]
      },
      {
        "answer": "Johnny Lujack",
        "aliases": [
          "Lujack"
        ]
      },
      {
        "answer": "Walter Eckersall",
        "aliases": [
          "Eckersall"
        ]
      },
      {
        "answer": "Angelo Bertelli",
        "aliases": [
          "Bertelli"
        ]
      },
      {
        "answer": "James Johnson",
        "aliases": [
          "Johnson"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_qb_1950_1979",
    "title": "Consensus All-America Quarterbacks (1950-1979)",
    "prompt": "Name a consensus All-America quarterback selected between 1950 and 1979.",
    "answers": [
      {
        "answer": "Bob Griese",
        "aliases": [
          "Griese"
        ]
      },
      {
        "answer": "Paul Hornung",
        "aliases": [
          "Hornung"
        ]
      },
      {
        "answer": "Roger Staubach",
        "aliases": [
          "Staubach"
        ]
      },
      {
        "answer": "Chuck Fusina",
        "aliases": [
          "Fusina"
        ]
      },
      {
        "answer": "Jack Scarbath",
        "aliases": [
          "Scarbath"
        ]
      },
      {
        "answer": "Richie Lucas",
        "aliases": [
          "Lucas"
        ]
      },
      {
        "answer": "Gary Beban",
        "aliases": [
          "Beban"
        ]
      },
      {
        "answer": "Terry Hanratty",
        "aliases": [
          "Hanratty"
        ]
      },
      {
        "answer": "Mike Phipps",
        "aliases": [
          "Phipps"
        ]
      },
      {
        "answer": "Jim Plunkett",
        "aliases": [
          "Plunkett"
        ]
      },
      {
        "answer": "Pat Sullivan",
        "aliases": [
          "Sullivan"
        ]
      },
      {
        "answer": "Dave Jaynes",
        "aliases": [
          "Jaynes"
        ]
      },
      {
        "answer": "Steve Bartkowski",
        "aliases": [
          "Bartkowski"
        ]
      },
      {
        "answer": "Marc Wilson",
        "aliases": [
          "Wilson"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_qb_1980_1999",
    "title": "Consensus All-America Quarterbacks (1980-1999)",
    "prompt": "Name a consensus All-America quarterback selected between 1980 and 1999.",
    "answers": [
      {
        "answer": "Danny Wuerffel",
        "aliases": [
          "Wuerffel"
        ]
      },
      {
        "answer": "Chuck Long",
        "aliases": [
          "Long"
        ]
      },
      {
        "answer": "Joe Hamilton",
        "aliases": [
          "Hamilton"
        ]
      },
      {
        "answer": "John Elway",
        "aliases": [
          "Elway"
        ]
      },
      {
        "answer": "Charlie Ward",
        "aliases": [
          "Ward"
        ]
      },
      {
        "answer": "Mark Herrmann",
        "aliases": [
          "Herrmann"
        ]
      },
      {
        "answer": "Steve Young",
        "aliases": [
          "Young"
        ]
      },
      {
        "answer": "Doug Flutie",
        "aliases": [
          "Flutie"
        ]
      },
      {
        "answer": "Vinny Testaverde",
        "aliases": [
          "Testaverde"
        ]
      },
      {
        "answer": "Don McPherson",
        "aliases": [
          "McPherson"
        ]
      },
      {
        "answer": "Andre Ware",
        "aliases": [
          "Ware"
        ]
      },
      {
        "answer": "Ty Detmer",
        "aliases": [
          "Detmer"
        ]
      },
      {
        "answer": "Gino Torretta",
        "aliases": [
          "Torretta"
        ]
      },
      {
        "answer": "Jim McMahon",
        "aliases": [
          "McMahon"
        ]
      },
      {
        "answer": "Kerry Collins",
        "aliases": [
          "Collins"
        ]
      },
      {
        "answer": "Tommie Frazier",
        "aliases": [
          "Frazier"
        ]
      },
      {
        "answer": "Peyton Manning",
        "aliases": [
          "Manning"
        ]
      },
      {
        "answer": "Michael Bishop",
        "aliases": [
          "Bishop"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_qb_2000_2025",
    "title": "Consensus All-America Quarterbacks (2000-2025)",
    "prompt": "Name a consensus All-America quarterback selected between 2000 and 2025.",
    "answers": [
      {
        "answer": "Vince Young",
        "aliases": [
          "Young"
        ]
      },
      {
        "answer": "Joe Burrow",
        "aliases": [
          "Burrow"
        ]
      },
      {
        "answer": "Jayden Daniels",
        "aliases": [
          "Daniels"
        ]
      },
      {
        "answer": "Johnny Manziel",
        "aliases": [
          "Manziel"
        ]
      },
      {
        "answer": "Lamar Jackson",
        "aliases": [
          "Jackson"
        ]
      },
      {
        "answer": "Bryce Young",
        "aliases": [
          "Young"
        ]
      },
      {
        "answer": "Carson Palmer",
        "aliases": [
          "Palmer"
        ]
      },
      {
        "answer": "Colt McCoy",
        "aliases": [
          "McCoy"
        ]
      },
      {
        "answer": "Cam Ward",
        "aliases": [
          "Ward"
        ]
      },
      {
        "answer": "Josh Heupel",
        "aliases": [
          "Heupel"
        ]
      },
      {
        "answer": "Rex Grossman",
        "aliases": [
          "Grossman"
        ]
      },
      {
        "answer": "Jason White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "Matt Leinart",
        "aliases": [
          "Leinart"
        ]
      },
      {
        "answer": "Troy Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Tim Tebow",
        "aliases": [
          "Tebow"
        ]
      },
      {
        "answer": "Cam Newton",
        "aliases": [
          "Newton"
        ]
      },
      {
        "answer": "Robert Griffin III",
        "aliases": [
          "III"
        ]
      },
      {
        "answer": "Marcus Mariota",
        "aliases": [
          "Mariota"
        ]
      },
      {
        "answer": "Deshaun Watson",
        "aliases": [
          "Watson"
        ]
      },
      {
        "answer": "Baker Mayfield",
        "aliases": [
          "Mayfield"
        ]
      },
      {
        "answer": "Kyler Murray",
        "aliases": [
          "Murray"
        ]
      },
      {
        "answer": "Trevor Lawrence",
        "aliases": [
          "Lawrence"
        ]
      },
      {
        "answer": "Fernando Mendoza",
        "aliases": [
          "Mendoza"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_rb_1889_1949",
    "title": "Consensus All-America Running Backs (1889-1949)",
    "prompt": "Name a consensus All-America running back selected between 1889 and 1949.",
    "answers": [
      {
        "answer": "Red Grange",
        "aliases": [
          "Grange"
        ]
      },
      {
        "answer": "Jim Crowley",
        "aliases": [
          "Crowley"
        ]
      },
      {
        "answer": "Bob Chappuis",
        "aliases": [
          "Chappuis"
        ]
      },
      {
        "answer": "Jim Thorpe",
        "aliases": [
          "Thorpe"
        ]
      },
      {
        "answer": "Charles Brickley",
        "aliases": [
          "Brickley"
        ]
      },
      {
        "answer": "Tony Butkovich",
        "aliases": [
          "Butkovich"
        ]
      },
      {
        "answer": "Chic Harley",
        "aliases": [
          "Harley"
        ]
      },
      {
        "answer": "Eddie Casey",
        "aliases": [
          "Casey"
        ]
      },
      {
        "answer": "Jay Berwanger",
        "aliases": [
          "Berwanger"
        ]
      },
      {
        "answer": "Ozzie Simmons",
        "aliases": [
          "Simmons"
        ]
      },
      {
        "answer": "Thomas 'Bum' McClung",
        "aliases": [
          "McClung"
        ]
      },
      {
        "answer": "Harold Weekes",
        "aliases": [
          "Weekes"
        ]
      },
      {
        "answer": "Paul Bunker",
        "aliases": [
          "Bunker"
        ]
      },
      {
        "answer": "Willie Heston",
        "aliases": [
          "Heston"
        ]
      },
      {
        "answer": "Andy Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Eddie Mahan",
        "aliases": [
          "Mahan"
        ]
      },
      {
        "answer": "James Craig",
        "aliases": [
          "Craig"
        ]
      },
      {
        "answer": "George McLaren",
        "aliases": [
          "McLaren"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_rb_1950_1979",
    "title": "Consensus All-America Running Backs (1950-1979)",
    "prompt": "Name a consensus All-America running back selected between 1950 and 1979.",
    "answers": [
      {
        "answer": "Mike Garrett",
        "aliases": [
          "Garrett"
        ]
      },
      {
        "answer": "Jim Grabowski",
        "aliases": [
          "Grabowski"
        ]
      },
      {
        "answer": "Nick Eddy",
        "aliases": [
          "Eddy"
        ]
      },
      {
        "answer": "Floyd Little",
        "aliases": [
          "Little"
        ]
      },
      {
        "answer": "Jim Brown",
        "aliases": [
          "Brown"
        ]
      },
      {
        "answer": "Johnny Majors",
        "aliases": [
          "Majors"
        ]
      },
      {
        "answer": "Tommy McDonald",
        "aliases": [
          "McDonald"
        ]
      },
      {
        "answer": "Ricky Bell",
        "aliases": [
          "Bell"
        ]
      },
      {
        "answer": "Chuck Muncie",
        "aliases": [
          "Muncie"
        ]
      },
      {
        "answer": "Tony Dorsett",
        "aliases": [
          "Dorsett"
        ]
      },
      {
        "answer": "Greg Pruitt",
        "aliases": [
          "Pruitt"
        ]
      },
      {
        "answer": "Gale Sayers",
        "aliases": [
          "Sayers"
        ]
      },
      {
        "answer": "Johnny Lattner",
        "aliases": [
          "Lattner"
        ]
      },
      {
        "answer": "Billy Vessels",
        "aliases": [
          "Vessels"
        ]
      },
      {
        "answer": "Billy Cannon",
        "aliases": [
          "Cannon"
        ]
      },
      {
        "answer": "O.J. Simpson",
        "aliases": [
          "Simpson"
        ]
      },
      {
        "answer": "Leroy Keyes",
        "aliases": [
          "Keyes"
        ]
      },
      {
        "answer": "Larry Csonka",
        "aliases": [
          "Csonka"
        ]
      },
      {
        "answer": "Steve Owens",
        "aliases": [
          "Owens"
        ]
      },
      {
        "answer": "Steve Worster",
        "aliases": [
          "Worster"
        ]
      },
      {
        "answer": "Don McCauley",
        "aliases": [
          "McCauley"
        ]
      },
      {
        "answer": "Ed Marinaro",
        "aliases": [
          "Marinaro"
        ]
      },
      {
        "answer": "John Cappelletti",
        "aliases": [
          "Cappelletti"
        ]
      },
      {
        "answer": "Roosevelt Leaks",
        "aliases": [
          "Leaks"
        ]
      },
      {
        "answer": "Archie Griffin",
        "aliases": [
          "Griffin"
        ]
      },
      {
        "answer": "Joe Washington",
        "aliases": [
          "Washington"
        ]
      },
      {
        "answer": "Anthony Davis",
        "aliases": [
          "Davis"
        ]
      },
      {
        "answer": "Earl Campbell",
        "aliases": [
          "Campbell"
        ]
      },
      {
        "answer": "Terry Miller",
        "aliases": [
          "Miller"
        ]
      },
      {
        "answer": "Charles White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "Billy Sims",
        "aliases": [
          "Sims"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_rb_1980_1999",
    "title": "Consensus All-America Running Backs (1980-1999)",
    "prompt": "Name a consensus All-America running back selected between 1980 and 1999.",
    "answers": [
      {
        "answer": "Barry Sanders",
        "aliases": [
          "Sanders"
        ]
      },
      {
        "answer": "Bo Jackson",
        "aliases": [
          "Jackson"
        ]
      },
      {
        "answer": "Lorenzo White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "Ron Dayne",
        "aliases": [
          "Dayne"
        ]
      },
      {
        "answer": "Thomas Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Herschel Walker",
        "aliases": [
          "Walker"
        ]
      },
      {
        "answer": "Eric Dickerson",
        "aliases": [
          "Dickerson"
        ]
      },
      {
        "answer": "Marshall Faulk",
        "aliases": [
          "Faulk"
        ]
      },
      {
        "answer": "LeShon Johnson",
        "aliases": [
          "Johnson"
        ]
      },
      {
        "answer": "George Rogers",
        "aliases": [
          "Rogers"
        ]
      },
      {
        "answer": "Mike Rozier",
        "aliases": [
          "Rozier"
        ]
      },
      {
        "answer": "Keith Byars",
        "aliases": [
          "Byars"
        ]
      },
      {
        "answer": "Kenneth Davis",
        "aliases": [
          "Davis"
        ]
      },
      {
        "answer": "Brent Fullwood",
        "aliases": [
          "Fullwood"
        ]
      },
      {
        "answer": "Paul Palmer",
        "aliases": [
          "Palmer"
        ]
      },
      {
        "answer": "Anthony Thompson",
        "aliases": [
          "Thompson"
        ]
      },
      {
        "answer": "Emmitt Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Eric Bieniemy",
        "aliases": [
          "Bieniemy"
        ]
      },
      {
        "answer": "Vaughn Dunbar",
        "aliases": [
          "Dunbar"
        ]
      },
      {
        "answer": "Garrison Hearst",
        "aliases": [
          "Hearst"
        ]
      },
      {
        "answer": "Marcus Allen",
        "aliases": [
          "Allen"
        ]
      },
      {
        "answer": "Rashaan Salaam",
        "aliases": [
          "Salaam"
        ]
      },
      {
        "answer": "Ki-Jana Carter",
        "aliases": [
          "Carter"
        ]
      },
      {
        "answer": "Eddie George",
        "aliases": [
          "George"
        ]
      },
      {
        "answer": "Ricky Williams",
        "aliases": [
          "Williams"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_rb_2000_2025",
    "title": "Consensus All-America Running Backs (2000-2025)",
    "prompt": "Name a consensus All-America running back selected between 2000 and 2025.",
    "answers": [
      {
        "answer": "Reggie Bush",
        "aliases": [
          "Bush"
        ]
      },
      {
        "answer": "Jerome Harrison",
        "aliases": [
          "Harrison"
        ]
      },
      {
        "answer": "Jonathan Taylor",
        "aliases": [
          "Taylor"
        ]
      },
      {
        "answer": "Chuba Hubbard",
        "aliases": [
          "Hubbard"
        ]
      },
      {
        "answer": "Ollie Gordon II",
        "aliases": [
          "II"
        ]
      },
      {
        "answer": "Andre Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Dalvin Cook",
        "aliases": [
          "Cook"
        ]
      },
      {
        "answer": "Kenneth Walker III",
        "aliases": [
          "III"
        ]
      },
      {
        "answer": "Larry Johnson",
        "aliases": [
          "Johnson"
        ]
      },
      {
        "answer": "Willis McGahee",
        "aliases": [
          "McGahee"
        ]
      },
      {
        "answer": "Ashton Jeanty",
        "aliases": [
          "Jeanty"
        ]
      },
      {
        "answer": "LaDainian Tomlinson",
        "aliases": [
          "Tomlinson"
        ]
      },
      {
        "answer": "Adrian Peterson",
        "aliases": [
          "Peterson"
        ]
      },
      {
        "answer": "Steve Slaton",
        "aliases": [
          "Slaton"
        ]
      },
      {
        "answer": "Darren McFadden",
        "aliases": [
          "McFadden"
        ]
      },
      {
        "answer": "Toby Gerhart",
        "aliases": [
          "Gerhart"
        ]
      },
      {
        "answer": "Mark Ingram",
        "aliases": [
          "Ingram"
        ]
      },
      {
        "answer": "LaMichael James",
        "aliases": [
          "James"
        ]
      },
      {
        "answer": "Trent Richardson",
        "aliases": [
          "Richardson"
        ]
      },
      {
        "answer": "Melvin Gordon",
        "aliases": [
          "Gordon"
        ]
      },
      {
        "answer": "Tevin Coleman",
        "aliases": [
          "Coleman"
        ]
      },
      {
        "answer": "Derrick Henry",
        "aliases": [
          "Henry"
        ]
      },
      {
        "answer": "Bryce Love",
        "aliases": [
          "Love"
        ]
      },
      {
        "answer": "Najee Harris",
        "aliases": [
          "Harris"
        ]
      },
      {
        "answer": "Bijan Robinson",
        "aliases": [
          "Robinson"
        ]
      },
      {
        "answer": "Jeremiyah Love",
        "aliases": [
          "Love"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_wr_1889_1949",
    "title": "Consensus All-America Receivers (1889-1949)",
    "prompt": "Name a consensus All-America receiver selected between 1889 and 1949.",
    "answers": [
      {
        "answer": "Richard Luman",
        "aliases": [
          "Luman"
        ]
      },
      {
        "answer": "Henry 'Hek' Wakefield",
        "aliases": [
          "Wakefield"
        ]
      },
      {
        "answer": "Waddy Young",
        "aliases": [
          "Young"
        ]
      },
      {
        "answer": "Jerome H. Holland",
        "aliases": [
          "Holland"
        ]
      },
      {
        "answer": "Paul Cleary",
        "aliases": [
          "Cleary"
        ]
      },
      {
        "answer": "Bill Swiacki",
        "aliases": [
          "Swiacki"
        ]
      },
      {
        "answer": "Guy Hutchinson",
        "aliases": [
          "Hutchinson"
        ]
      },
      {
        "answer": "Dave Campbell",
        "aliases": [
          "Campbell"
        ]
      },
      {
        "answer": "Ralph Heywood",
        "aliases": [
          "Heywood"
        ]
      },
      {
        "answer": "John Yonakor",
        "aliases": [
          "Yonakor"
        ]
      },
      {
        "answer": "Pete Pihos",
        "aliases": [
          "Pihos"
        ]
      },
      {
        "answer": "Bob Higgins",
        "aliases": [
          "Higgins"
        ]
      },
      {
        "answer": "Bob Wilson",
        "aliases": [
          "Wilson"
        ]
      },
      {
        "answer": "Frank Hinkey",
        "aliases": [
          "Hinkey"
        ]
      },
      {
        "answer": "Charles Gelbert",
        "aliases": [
          "Gelbert"
        ]
      },
      {
        "answer": "Norman Cabot",
        "aliases": [
          "Cabot"
        ]
      },
      {
        "answer": "Garrett Cochran",
        "aliases": [
          "Cochran"
        ]
      },
      {
        "answer": "John A. Hall",
        "aliases": [
          "Hall"
        ]
      },
      {
        "answer": "Lew Palmer",
        "aliases": [
          "Palmer"
        ]
      },
      {
        "answer": "John Hallowell",
        "aliases": [
          "Hallowell"
        ]
      },
      {
        "answer": "Neil Snow",
        "aliases": [
          "Snow"
        ]
      },
      {
        "answer": "David Campbell",
        "aliases": [
          "Campbell"
        ]
      },
      {
        "answer": "Ralph Davis",
        "aliases": [
          "Davis"
        ]
      },
      {
        "answer": "Charles D. Rafferty",
        "aliases": [
          "Rafferty"
        ]
      },
      {
        "answer": "Tom Shevlin",
        "aliases": [
          "Shevlin"
        ]
      },
      {
        "answer": "Bill Dague",
        "aliases": [
          "Dague"
        ]
      },
      {
        "answer": "Clarence Alcott",
        "aliases": [
          "Alcott"
        ]
      },
      {
        "answer": "Albert Exendine",
        "aliases": [
          "Exendine"
        ]
      },
      {
        "answer": "Caspar Wister",
        "aliases": [
          "Wister"
        ]
      },
      {
        "answer": "John Kilpatrick",
        "aliases": [
          "Kilpatrick"
        ]
      },
      {
        "answer": "Stanfield Wells",
        "aliases": [
          "Wells"
        ]
      },
      {
        "answer": "Bob Forbes",
        "aliases": [
          "Forbes"
        ]
      },
      {
        "answer": "Louis Merrilat",
        "aliases": [
          "Merrilat"
        ]
      },
      {
        "answer": "Huntington Hardwick",
        "aliases": [
          "Hardwick"
        ]
      },
      {
        "answer": "Bert Baston",
        "aliases": [
          "Baston"
        ]
      },
      {
        "answer": "John Beckett",
        "aliases": [
          "Beckett"
        ]
      },
      {
        "answer": "Everett Strupper",
        "aliases": [
          "Strupper"
        ]
      },
      {
        "answer": "Paul Robeson",
        "aliases": [
          "Robeson"
        ]
      },
      {
        "answer": "Amos Alonzo Stagg",
        "aliases": [
          "Stagg"
        ]
      },
      {
        "answer": "Arthur Cumnock",
        "aliases": [
          "Cumnock"
        ]
      },
      {
        "answer": "John Hartwell",
        "aliases": [
          "Hartwell"
        ]
      },
      {
        "answer": "William Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Douglass Bomeisler",
        "aliases": [
          "Bomeisler"
        ]
      },
      {
        "answer": "Sanford White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "Murray Shelton",
        "aliases": [
          "Shelton"
        ]
      },
      {
        "answer": "Guy Chamberlin",
        "aliases": [
          "Chamberlin"
        ]
      },
      {
        "answer": "Luke Urban",
        "aliases": [
          "Urban"
        ]
      },
      {
        "answer": "Charles Carney",
        "aliases": [
          "Carney"
        ]
      },
      {
        "answer": "Bill Fincher",
        "aliases": [
          "Fincher"
        ]
      },
      {
        "answer": "Brick Muller",
        "aliases": [
          "Muller"
        ]
      },
      {
        "answer": "Eddie Anderson",
        "aliases": [
          "Anderson"
        ]
      },
      {
        "answer": "Wendell Taylor",
        "aliases": [
          "Taylor"
        ]
      },
      {
        "answer": "Pete McRae",
        "aliases": [
          "McRae"
        ]
      },
      {
        "answer": "Ray Ecklund",
        "aliases": [
          "Ecklund"
        ]
      },
      {
        "answer": "Lynn Bomar",
        "aliases": [
          "Bomar"
        ]
      },
      {
        "answer": "Bennie Oosterbaan",
        "aliases": [
          "Oosterbaan"
        ]
      },
      {
        "answer": "George Tully",
        "aliases": [
          "Tully"
        ]
      },
      {
        "answer": "Vic Hanson",
        "aliases": [
          "Hanson"
        ]
      },
      {
        "answer": "Tom Nash",
        "aliases": [
          "Nash"
        ]
      },
      {
        "answer": "Irv Phillips",
        "aliases": [
          "Phillips"
        ]
      },
      {
        "answer": "Wes Fesler",
        "aliases": [
          "Fesler"
        ]
      },
      {
        "answer": "Frank Baker",
        "aliases": [
          "Baker"
        ]
      },
      {
        "answer": "Jerry Dalrymple",
        "aliases": [
          "Dalrymple"
        ]
      },
      {
        "answer": "Vernon Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Paul Moss",
        "aliases": [
          "Moss"
        ]
      },
      {
        "answer": "Joe Skladany",
        "aliases": [
          "Skladany"
        ]
      },
      {
        "answer": "Don Hutson",
        "aliases": [
          "Hutson"
        ]
      },
      {
        "answer": "Frank Larson",
        "aliases": [
          "Larson"
        ]
      },
      {
        "answer": "Larry Kelley",
        "aliases": [
          "Kelley"
        ]
      },
      {
        "answer": "Gaynell Tinsley",
        "aliases": [
          "Tinsley"
        ]
      },
      {
        "answer": "Chuck Sweeney",
        "aliases": [
          "Sweeney"
        ]
      },
      {
        "answer": "Andy Bershak",
        "aliases": [
          "Bershak"
        ]
      },
      {
        "answer": "Esco Sarkkinen",
        "aliases": [
          "Sarkkinen"
        ]
      },
      {
        "answer": "Ken Kavanaugh",
        "aliases": [
          "Kavanaugh"
        ]
      },
      {
        "answer": "Gene Goodreault",
        "aliases": [
          "Goodreault"
        ]
      },
      {
        "answer": "Holt Rast",
        "aliases": [
          "Rast"
        ]
      },
      {
        "answer": "Bob Dove",
        "aliases": [
          "Dove"
        ]
      },
      {
        "answer": "Dave Schreiner",
        "aliases": [
          "Schreiner"
        ]
      },
      {
        "answer": "Phil Tinsley",
        "aliases": [
          "Tinsley"
        ]
      },
      {
        "answer": "Dick Duden",
        "aliases": [
          "Duden"
        ]
      },
      {
        "answer": "Burr Baldwin",
        "aliases": [
          "Baldwin"
        ]
      },
      {
        "answer": "Dick Rifenburg",
        "aliases": [
          "Rifenburg"
        ]
      },
      {
        "answer": "Leon Hart",
        "aliases": [
          "Hart"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_wr_1950_1979",
    "title": "Consensus All-America Receivers (1950-1979)",
    "prompt": "Name a consensus All-America receiver selected between 1950 and 1979.",
    "answers": [
      {
        "answer": "Howard Twilley",
        "aliases": [
          "Twilley"
        ]
      },
      {
        "answer": "Freeman White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "Frank McPhee",
        "aliases": [
          "McPhee"
        ]
      },
      {
        "answer": "Bill Carpenter",
        "aliases": [
          "Carpenter"
        ]
      },
      {
        "answer": "Dan Foldberg",
        "aliases": [
          "Foldberg"
        ]
      },
      {
        "answer": "Bill McColl",
        "aliases": [
          "McColl"
        ]
      },
      {
        "answer": "Don Dohoney",
        "aliases": [
          "Dohoney"
        ]
      },
      {
        "answer": "Max Boydston",
        "aliases": [
          "Boydston"
        ]
      },
      {
        "answer": "Ron Beagle",
        "aliases": [
          "Beagle"
        ]
      },
      {
        "answer": "Ron Kramer",
        "aliases": [
          "Kramer"
        ]
      },
      {
        "answer": "Jimmy Phillips",
        "aliases": [
          "Phillips"
        ]
      },
      {
        "answer": "Buddy Dial",
        "aliases": [
          "Dial"
        ]
      },
      {
        "answer": "Mike Ditka",
        "aliases": [
          "Ditka"
        ]
      },
      {
        "answer": "Gary Collins",
        "aliases": [
          "Collins"
        ]
      },
      {
        "answer": "Hal Bedsole",
        "aliases": [
          "Bedsole"
        ]
      },
      {
        "answer": "Jack Snow",
        "aliases": [
          "Snow"
        ]
      },
      {
        "answer": "Fred Biletnikoff",
        "aliases": [
          "Biletnikoff"
        ]
      },
      {
        "answer": "Carlos Alvarez",
        "aliases": [
          "Alvarez"
        ]
      },
      {
        "answer": "Lynn Swann",
        "aliases": [
          "Swann"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_wr_1980_1999",
    "title": "Consensus All-America Receivers (1980-1999)",
    "prompt": "Name a consensus All-America receiver selected between 1980 and 1999.",
    "answers": [
      {
        "answer": "Hart Lee Dykes",
        "aliases": [
          "Dykes"
        ]
      },
      {
        "answer": "David Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Peter Warrick",
        "aliases": [
          "Warrick"
        ]
      },
      {
        "answer": "Troy Walters",
        "aliases": [
          "Walters"
        ]
      },
      {
        "answer": "Anthony Carter",
        "aliases": [
          "Carter"
        ]
      },
      {
        "answer": "J.J. Stokes",
        "aliases": [
          "Stokes"
        ]
      },
      {
        "answer": "Irving Fryar",
        "aliases": [
          "Fryar"
        ]
      },
      {
        "answer": "Cris Carter",
        "aliases": [
          "Carter"
        ]
      },
      {
        "answer": "Tim Brown",
        "aliases": [
          "Brown"
        ]
      },
      {
        "answer": "Clarkston Hines",
        "aliases": [
          "Hines"
        ]
      },
      {
        "answer": "Raghib 'Rocket' Ismail",
        "aliases": [
          "Ismail"
        ]
      },
      {
        "answer": "Desmond Howard",
        "aliases": [
          "Howard"
        ]
      },
      {
        "answer": "Michael Westbrook",
        "aliases": [
          "Westbrook"
        ]
      },
      {
        "answer": "Keyshawn Johnson",
        "aliases": [
          "Johnson"
        ]
      },
      {
        "answer": "Randy Moss",
        "aliases": [
          "Moss"
        ]
      },
      {
        "answer": "Troy Edwards",
        "aliases": [
          "Edwards"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_wr_2000_2025",
    "title": "Consensus All-America Receivers (2000-2025)",
    "prompt": "Name a consensus All-America receiver selected between 2000 and 2025.",
    "answers": [
      {
        "answer": "Dwayne Jarrett",
        "aliases": [
          "Jarrett"
        ]
      },
      {
        "answer": "Ja'Marr Chase",
        "aliases": [
          "Chase"
        ]
      },
      {
        "answer": "CeeDee Lamb",
        "aliases": [
          "Lamb"
        ]
      },
      {
        "answer": "Marvin Harrison Jr.",
        "aliases": [
          "Jr."
        ]
      },
      {
        "answer": "Malik Nabers",
        "aliases": [
          "Nabers"
        ]
      },
      {
        "answer": "Rome Odunze",
        "aliases": [
          "Odunze"
        ]
      },
      {
        "answer": "Dede Westbrook",
        "aliases": [
          "Westbrook"
        ]
      },
      {
        "answer": "Jameson Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Charles Rogers",
        "aliases": [
          "Rogers"
        ]
      },
      {
        "answer": "Michael Crabtree",
        "aliases": [
          "Crabtree"
        ]
      },
      {
        "answer": "Nick Nash",
        "aliases": [
          "Nash"
        ]
      },
      {
        "answer": "Jabar Gaffney",
        "aliases": [
          "Gaffney"
        ]
      },
      {
        "answer": "Larry Fitzgerald",
        "aliases": [
          "Fitzgerald"
        ]
      },
      {
        "answer": "Braylon Edwards",
        "aliases": [
          "Edwards"
        ]
      },
      {
        "answer": "Calvin Johnson",
        "aliases": [
          "Johnson"
        ]
      },
      {
        "answer": "Golden Tate",
        "aliases": [
          "Tate"
        ]
      },
      {
        "answer": "Justin Blackmon",
        "aliases": [
          "Blackmon"
        ]
      },
      {
        "answer": "Marqise Lee",
        "aliases": [
          "Lee"
        ]
      },
      {
        "answer": "Terrance Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Amari Cooper",
        "aliases": [
          "Cooper"
        ]
      },
      {
        "answer": "Corey Coleman",
        "aliases": [
          "Coleman"
        ]
      },
      {
        "answer": "James Washington",
        "aliases": [
          "Washington"
        ]
      },
      {
        "answer": "DeVonta Smith",
        "aliases": [
          "Smith"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_lb_1950_1979",
    "title": "Consensus All-America Linebackers (1950-1979)",
    "prompt": "Name a consensus All-America linebacker selected between 1950 and 1979.",
    "answers": [
      {
        "answer": "Jim Lynch",
        "aliases": [
          "Lynch"
        ]
      },
      {
        "answer": "Greg Buttle",
        "aliases": [
          "Buttle"
        ]
      },
      {
        "answer": "Steve Kiner",
        "aliases": [
          "Kiner"
        ]
      },
      {
        "answer": "Jack Ham",
        "aliases": [
          "Ham"
        ]
      },
      {
        "answer": "Mike Taylor",
        "aliases": [
          "Taylor"
        ]
      },
      {
        "answer": "Randy Gradishar",
        "aliases": [
          "Gradishar"
        ]
      },
      {
        "answer": "Rod Shoate",
        "aliases": [
          "Shoate"
        ]
      },
      {
        "answer": "Robert Jackson",
        "aliases": [
          "Jackson"
        ]
      },
      {
        "answer": "Jerry Robinson",
        "aliases": [
          "Robinson"
        ]
      },
      {
        "answer": "Mike Singletary",
        "aliases": [
          "Singletary"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_lb_1980_1999",
    "title": "Consensus All-America Linebackers (1980-1999)",
    "prompt": "Name a consensus All-America linebacker selected between 1980 and 1999.",
    "answers": [
      {
        "answer": "Derrick Thomas",
        "aliases": [
          "Thomas"
        ]
      },
      {
        "answer": "Brian Bosworth",
        "aliases": [
          "Bosworth"
        ]
      },
      {
        "answer": "Larry Station",
        "aliases": [
          "Station"
        ]
      },
      {
        "answer": "Darryl Talley",
        "aliases": [
          "Talley"
        ]
      },
      {
        "answer": "Trev Alberts",
        "aliases": [
          "Alberts"
        ]
      },
      {
        "answer": "Derrick Brooks",
        "aliases": [
          "Brooks"
        ]
      },
      {
        "answer": "Lawrence Taylor",
        "aliases": [
          "Taylor"
        ]
      },
      {
        "answer": "Ricky Hunley",
        "aliases": [
          "Hunley"
        ]
      },
      {
        "answer": "Cornelius Bennett",
        "aliases": [
          "Bennett"
        ]
      },
      {
        "answer": "Chris Spielman",
        "aliases": [
          "Spielman"
        ]
      },
      {
        "answer": "Percy Snow",
        "aliases": [
          "Snow"
        ]
      },
      {
        "answer": "Keith McCants",
        "aliases": [
          "McCants"
        ]
      },
      {
        "answer": "Alfred Williams",
        "aliases": [
          "Williams"
        ]
      },
      {
        "answer": "Robert Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Marcus Buckley",
        "aliases": [
          "Buckley"
        ]
      },
      {
        "answer": "Marvin Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Dana Howard",
        "aliases": [
          "Howard"
        ]
      },
      {
        "answer": "Zach Thomas",
        "aliases": [
          "Thomas"
        ]
      },
      {
        "answer": "Andy Katzenmoyer",
        "aliases": [
          "Katzenmoyer"
        ]
      },
      {
        "answer": "Dat Nguyen",
        "aliases": [
          "Nguyen"
        ]
      }
    ]
  },
  {
    "id": "cfb_aa_lb_2000_2025",
    "title": "Consensus All-America Linebackers (2000-2025)",
    "prompt": "Name a consensus All-America linebacker selected between 2000 and 2025.",
    "answers": [
      {
        "answer": "Patrick Willis",
        "aliases": [
          "Willis"
        ]
      },
      {
        "answer": "Isaiah Simmons",
        "aliases": [
          "Simmons"
        ]
      },
      {
        "answer": "Dallas Turner",
        "aliases": [
          "Turner"
        ]
      },
      {
        "answer": "Anthony Barr",
        "aliases": [
          "Barr"
        ]
      },
      {
        "answer": "Reuben Foster",
        "aliases": [
          "Foster"
        ]
      },
      {
        "answer": "Jabrill Peppers",
        "aliases": [
          "Peppers"
        ]
      },
      {
        "answer": "Will Anderson Jr.",
        "aliases": [
          "Jr."
        ]
      },
      {
        "answer": "Jay Higgins",
        "aliases": [
          "Higgins"
        ]
      },
      {
        "answer": "Dan Morgan",
        "aliases": [
          "Morgan"
        ]
      },
      {
        "answer": "Teddy Lehman",
        "aliases": [
          "Lehman"
        ]
      },
      {
        "answer": "Derrick Johnson",
        "aliases": [
          "Johnson"
        ]
      },
      {
        "answer": "James Laurinaitis",
        "aliases": [
          "Laurinaitis"
        ]
      },
      {
        "answer": "Rolando McClain",
        "aliases": [
          "McClain"
        ]
      },
      {
        "answer": "Greg Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Luke Kuechly",
        "aliases": [
          "Kuechly"
        ]
      },
      {
        "answer": "Jarvis Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Manti Te'o",
        "aliases": [
          "Te'o"
        ]
      },
      {
        "answer": "Scooby Wright III",
        "aliases": [
          "III"
        ]
      },
      {
        "answer": "Hau'oli Kikaha",
        "aliases": [
          "Kikaha"
        ]
      },
      {
        "answer": "Reggie Ragland",
        "aliases": [
          "Ragland"
        ]
      },
      {
        "answer": "Jaylon Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Josey Jewell",
        "aliases": [
          "Jewell"
        ]
      },
      {
        "answer": "Roquan Smith",
        "aliases": [
          "Smith"
        ]
      },
      {
        "answer": "Devin White",
        "aliases": [
          "White"
        ]
      },
      {
        "answer": "Micah Parsons",
        "aliases": [
          "Parsons"
        ]
      }
    ]
  },
  {
    "id": "cfb_career_record_holders",
    "title": "All-Time FBS Career Statistical Record Holders",
    "prompt": "Name a player who holds an all-time FBS career statistical record.",
    "answers": [
      {
        "answer": "Case Keenum",
        "aliases": [
          "Keenum"
        ]
      },
      {
        "answer": "Case Keenum",
        "aliases": [
          "Keenum"
        ]
      },
      {
        "answer": "Dillon Gabriel",
        "aliases": [
          "Gabriel"
        ]
      },
      {
        "answer": "Case Keenum",
        "aliases": [
          "Keenum"
        ]
      },
      {
        "answer": "Donnel Pumphrey",
        "aliases": [
          "Pumphrey"
        ]
      },
      {
        "answer": "Keenan Reynolds",
        "aliases": [
          "Reynolds"
        ]
      },
      {
        "answer": "Corey Davis",
        "aliases": [
          "Davis"
        ]
      },
      {
        "answer": "Zay Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Jarett Dillard",
        "aliases": [
          "Dillard"
        ]
      },
      {
        "answer": "Al Brosky",
        "aliases": [
          "Brosky"
        ]
      },
      {
        "answer": "Terrell Suggs",
        "aliases": [
          "Suggs"
        ]
      },
      {
        "answer": "Al Brosky",
        "aliases": [
          "Brosky"
        ]
      }
    ]
  },
  {
    "id": "cfb_season_record_holders",
    "title": "Single-Season FBS Statistical Record Holders",
    "prompt": "Name a player who holds a single-season FBS statistical record.",
    "answers": [
      {
        "answer": "Barry Sanders",
        "aliases": [
          "Sanders"
        ]
      },
      {
        "answer": "Barry Sanders",
        "aliases": [
          "Sanders"
        ]
      },
      {
        "answer": "Bailey Zappe",
        "aliases": [
          "Zappe"
        ]
      },
      {
        "answer": "Bailey Zappe",
        "aliases": [
          "Zappe"
        ]
      },
      {
        "answer": "Trevor Insley",
        "aliases": [
          "Insley"
        ]
      },
      {
        "answer": "Zay Jones",
        "aliases": [
          "Jones"
        ]
      },
      {
        "answer": "Troy Edwards",
        "aliases": [
          "Edwards"
        ]
      },
      {
        "answer": "Terrell Suggs",
        "aliases": [
          "Suggs"
        ]
      },
      {
        "answer": "Al Brosky",
        "aliases": [
          "Brosky"
        ]
      },
      {
        "answer": "Roberto Aguayo",
        "aliases": [
          "Aguayo"
        ]
      },
      {
        "answer": "John Lee",
        "aliases": [
          "Lee"
        ]
      }
    ]
  },
  {
    "id": "cfb_2025_award_winners",
    "title": "2025 Major College Football Award Winners",
    "prompt": "Name a winner of a major 2025 college football award.",
    "answers": [
      {
        "answer": "Fernando Mendoza, Indiana",
        "aliases": [
          "Indiana"
        ]
      },
      {
        "answer": "Diego Pavia, Vanderbilt",
        "aliases": [
          "Vanderbilt"
        ]
      },
      {
        "answer": "Jeremiyah Love, Notre Dame",
        "aliases": [
          "Dame"
        ]
      },
      {
        "answer": "Makai Lemon, USC",
        "aliases": [
          "USC"
        ]
      },
      {
        "answer": "Eli Stowers, Vanderbilt",
        "aliases": [
          "Vanderbilt"
        ]
      },
      {
        "answer": "Spencer Fano, Utah",
        "aliases": [
          "Utah"
        ]
      },
      {
        "answer": "Logan Jones, Iowa",
        "aliases": [
          "Iowa"
        ]
      },
      {
        "answer": "Tate Sandell, Oklahoma",
        "aliases": [
          "Oklahoma"
        ]
      },
      {
        "answer": "Brett Thorson, Georgia",
        "aliases": [
          "Georgia"
        ]
      },
      {
        "answer": "Jacob Rodriguez, Texas Tech",
        "aliases": [
          "Tech"
        ]
      },
      {
        "answer": "Caleb Downs, Ohio State",
        "aliases": [
          "State"
        ]
      },
      {
        "answer": "Curt Cignetti, Indiana",
        "aliases": [
          "Indiana"
        ]
      }
    ]
  }
];
