// AUTO-GENERATED -- do not hand-edit.
// Produced by tools/gateway_dev_client.py via a LIVE call to the local Reads Engine
// Gateway (package_id GGP4:3729ee0bb1de9d131e12ebfb) -- NOT the static baseline
// (data/player-from-clues-v01.js). Only loaded by the Reads frontend when
// ENABLE_PLAYER_FROM_CLUES_GATEWAY_DEV_V01 is explicitly turned on in app.js --
// see READS_ENGINE_GATEWAY_V01_REPORT.md, Part O.
window.PLAYER_FROM_CLUES_GATEWAY_DEV = {
  "packageId": "GGP4:3729ee0bb1de9d131e12ebfb",
  "packageVersion": "0.4",
  "mechanic": "identify_player_from_clues",
  "gameTitle": "Player From Clues",
  "gameInstructions": "You'll see a sequence of verified clues about one NFL player, revealed one at a time and narrowing from broad to specific. Identify the player.",
  "generatedAt": "2026-08-10T00:59:27.973775+00:00",
  "qaStatus": "PASSED",
  "puzzleCount": 5,
  "puzzles": [
    {
      "id": 630000,
      "answer": {
        "playerId": "PFR:AverAn00",
        "displayName": "Anthony Averett"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 4506,
          "candidatesAfter": 2851,
          "provenance": {
            "table": "canonical_roster_seasons+season_standings",
            "field": "playoff_result IS NOT NULL (derived join on team_code+season, games>0)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_round",
          "text": "This player was drafted in round 4.",
          "candidatesBefore": 2851,
          "candidatesAfter": 418,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "drafting_franchise",
          "text": "This player was drafted by the Baltimore Ravens.",
          "candidatesBefore": 418,
          "candidatesAfter": 26,
          "provenance": {
            "table": "draft_facts+team_aliases",
            "field": "draft_team (season-resolved)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2018 to 2018.",
          "candidatesBefore": 26,
          "candidatesAfter": 2,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "college",
          "text": "This player attended Alabama before entering the NFL draft.",
          "candidatesBefore": 2,
          "candidatesAfter": 1,
          "provenance": {
            "table": "relationships(ATTENDED_BEFORE_DRAFT)+schools",
            "field": "school_name",
            "sourceId": "READS_IDENTITY_BRIDGE",
            "verificationStatus": "PRODUCTION_SAFE_DERIVED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 630001,
      "answer": {
        "playerId": "PFR:MontDa01",
        "displayName": "David Montgomery"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 3.",
          "candidatesBefore": 4506,
          "candidatesAfter": 669,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "position",
          "text": "This player's position at the time of the draft was RB.",
          "candidatesBefore": 669,
          "candidatesAfter": 55,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #73 overall pick.",
          "candidatesBefore": 55,
          "candidatesAfter": 6,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "college",
          "text": "This player attended Iowa State before entering the NFL draft.",
          "candidatesBefore": 6,
          "candidatesAfter": 1,
          "provenance": {
            "table": "relationships(ATTENDED_BEFORE_DRAFT)+schools",
            "field": "school_name",
            "sourceId": "READS_IDENTITY_BRIDGE",
            "verificationStatus": "PRODUCTION_SAFE_DERIVED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 630002,
      "answer": {
        "playerId": "PFR:ThomJ.02",
        "displayName": "J.T. Thomas"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 4506,
          "candidatesAfter": 2851,
          "provenance": {
            "table": "canonical_roster_seasons+season_standings",
            "field": "playoff_result IS NOT NULL (derived join on team_code+season, games>0)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "position",
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 2851,
          "candidatesAfter": 372,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "draft_round",
          "text": "This player was drafted in round 6.",
          "candidatesBefore": 372,
          "candidatesAfter": 40,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_year",
          "text": "This player was drafted in 2011.",
          "candidatesBefore": 40,
          "candidatesAfter": 6,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2012 to 2017.",
          "candidatesBefore": 6,
          "candidatesAfter": 1,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 630003,
      "answer": {
        "playerId": "PFR:PaceCa20",
        "displayName": "Calvin Pace"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 4506,
          "candidatesAfter": 2851,
          "provenance": {
            "table": "canonical_roster_seasons+season_standings",
            "field": "playoff_result IS NOT NULL (derived join on team_code+season, games>0)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_round",
          "text": "This player was drafted in round 1.",
          "candidatesBefore": 2851,
          "candidatesAfter": 522,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "position",
          "text": "This player's position at the time of the draft was DE.",
          "candidatesBefore": 522,
          "candidatesAfter": 67,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #18 overall pick.",
          "candidatesBefore": 67,
          "candidatesAfter": 4,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2015.",
          "candidatesBefore": 4,
          "candidatesAfter": 1,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 630004,
      "answer": {
        "playerId": "PFR:WilsE.99",
        "displayName": "E.J. Wilson"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 4506,
          "candidatesAfter": 2851,
          "provenance": {
            "table": "canonical_roster_seasons+season_standings",
            "field": "playoff_result IS NOT NULL (derived join on team_code+season, games>0)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_round",
          "text": "This player was drafted in round 4.",
          "candidatesBefore": 2851,
          "candidatesAfter": 418,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "position",
          "text": "This player's position at the time of the draft was DE.",
          "candidatesBefore": 418,
          "candidatesAfter": 39,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_year",
          "text": "This player was drafted in 2010.",
          "candidatesBefore": 39,
          "candidatesAfter": 4,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2010 to 2010.",
          "candidatesBefore": 4,
          "candidatesAfter": 1,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    }
  ]
};
