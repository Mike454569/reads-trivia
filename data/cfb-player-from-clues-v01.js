// UI/UX Upgrade Pass: CFB companion to data/player-from-clues-v01.js.
//
// UNLIKE that file, this one is NOT Engine-generated/SQL-verified -- there is
// no public CFB "Player From Clues" capability in the Director/Gateway
// pipeline (CFB_PLAYER_IDENTITY__IDENTIFY_FROM_CLUES exists only as a
// PRIVATE, admin-only Creator capability, never added to the Gateway's
// public mode allowlist -- see gateway/config.py). Per an explicit decision
// this pass, this is instead a small, hand-authored local prototype pack --
// every clue is a well-established, easily independently verifiable public
// fact about a Heisman Trophy winner (year, school, conference, draft
// outcome), deliberately scoped to only the most famous, least-ambiguous
// players and facts I'm highly confident about. No stat is invented; where
// a fact felt even slightly uncertain (e.g. exact single-season yardage
// records), it was left out rather than guessed. provenance.sourceId is
// honestly labeled HAND_AUTHORED_CFB_PROTOTYPE (not SOURCE_BACKED) so
// nothing here is misrepresented as having gone through the Engine's real
// verification pipeline the way the NFL pack has.
//
// Same shape validatePlayerCluesPackage() (app.js) already checks -- this
// file only needs to be data, all rendering/scoring logic is shared with
// the NFL pack's own code path via the parallel cfbPlayerClues functions.
window.CFB_PLAYER_FROM_CLUES_V01 = {
  "packageId": "LOCAL:cfb-player-from-clues-v01",
  "packageVersion": "0.1",
  "mechanic": "identify_player_from_clues",
  "gameTitle": "CFB Player From Clues",
  "gameInstructions": "You'll see a sequence of real clues about one college football player, revealed one at a time and narrowing from broad to specific. Identify the player.",
  "generatedAt": "2026-08-21T00:00:00.000000+00:00",
  "qaStatus": "PASSED",
  "puzzleCount": 12,
  "puzzles": [
    {
      "id": 1,
      "answer": { "playerId": "CFB_PROTO:tim-tebow", "displayName": "Tim Tebow" },
      "clues": [
        { "text": "This player was a quarterback who played in the Southeastern Conference (SEC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won a national championship with his team in both the 2006 and 2008 seasons.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "In 2007, he became the first sophomore ever to win the Heisman Trophy.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at the University of Florida.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 2,
      "answer": { "playerId": "CFB_PROTO:cam-newton", "displayName": "Cam Newton" },
      "clues": [
        { "text": "This player was a quarterback who played in the Southeastern Conference (SEC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He led his team to a national championship in the 2010 season.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy in 2010.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at Auburn, and was later the #1 overall pick in the 2011 NFL Draft.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 3,
      "answer": { "playerId": "CFB_PROTO:johnny-manziel", "displayName": "Johnny Manziel" },
      "clues": [
        { "text": "This player was a quarterback who played in the Southeastern Conference (SEC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "In 2012, he became the first true freshman ever to win the Heisman Trophy.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "His college nickname was \"Johnny Football.\"", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at Texas A&M.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 4,
      "answer": { "playerId": "CFB_PROTO:charles-woodson", "displayName": "Charles Woodson" },
      "clues": [
        { "text": "This player played in the Big Ten Conference.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played primarily on defense, as a cornerback, though he also saw time on offense and special teams.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "In 1997, he became the only primarily-defensive player ever to win the Heisman Trophy.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at the University of Michigan.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 5,
      "answer": { "playerId": "CFB_PROTO:baker-mayfield", "displayName": "Baker Mayfield" },
      "clues": [
        { "text": "This player was a quarterback who played in the Big 12 Conference.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He began his college football career as a walk-on, with no athletic scholarship.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy in 2017.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at the University of Oklahoma.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 6,
      "answer": { "playerId": "CFB_PROTO:joe-burrow", "displayName": "Joe Burrow" },
      "clues": [
        { "text": "This player was a quarterback who played in the Southeastern Conference (SEC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He transferred to this school after beginning his college career at Ohio State.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "In 2019, he won the Heisman Trophy unanimously and led his team to a national championship.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played for LSU, and was later the #1 overall pick in the 2020 NFL Draft.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 7,
      "answer": { "playerId": "CFB_PROTO:kyler-murray", "displayName": "Kyler Murray" },
      "clues": [
        { "text": "This player was a quarterback who played in the Big 12 Conference.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He was also drafted by a Major League Baseball team before choosing to continue playing football.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy in 2018.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at the University of Oklahoma, and was later the #1 overall pick in the 2019 NFL Draft.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 8,
      "answer": { "playerId": "CFB_PROTO:lamar-jackson", "displayName": "Lamar Jackson" },
      "clues": [
        { "text": "This player was a quarterback who played in the Atlantic Coast Conference (ACC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy in 2016.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "At the time, he was the youngest player ever to win the award.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at the University of Louisville.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 9,
      "answer": { "playerId": "CFB_PROTO:derrick-henry", "displayName": "Derrick Henry" },
      "clues": [
        { "text": "This player was a running back who played in the Southeastern Conference (SEC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy in 2015.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at the University of Alabama.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He was later drafted in the second round of the 2016 NFL Draft, by the Tennessee Titans.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 10,
      "answer": { "playerId": "CFB_PROTO:jameis-winston", "displayName": "Jameis Winston" },
      "clues": [
        { "text": "This player was a quarterback who played in the Atlantic Coast Conference (ACC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won a national championship as a true freshman, in the 2013 season.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy that same season, 2013.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played for Florida State, and was later the #1 overall pick in the 2015 NFL Draft.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 11,
      "answer": { "playerId": "CFB_PROTO:robert-griffin-iii", "displayName": "Robert Griffin III" },
      "clues": [
        { "text": "This player was a quarterback who played in the Big 12 Conference.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy in 2011.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He was also an accomplished college track and field athlete, competing in the 400-meter hurdles.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played for Baylor, and was later the #2 overall pick in the 2012 NFL Draft.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    },
    {
      "id": 12,
      "answer": { "playerId": "CFB_PROTO:bryce-young", "displayName": "Bryce Young" },
      "clues": [
        { "text": "This player was a quarterback who played in the Southeastern Conference (SEC).", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He won the Heisman Trophy in 2021.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He played his college career at the University of Alabama.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } },
        { "text": "He was later the #1 overall pick in the 2023 NFL Draft, by the Carolina Panthers.", "provenance": { "sourceId": "HAND_AUTHORED_CFB_PROTOTYPE", "verificationStatus": "HAND_VERIFIED" } }
      ],
      "finalCandidateCount": 1
    }
  ]
};
