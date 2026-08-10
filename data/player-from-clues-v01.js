// AUTO-GENERATED -- do not hand-edit.
// Produced by tools/export_player_from_clues_frontend.py from
// generated_games/director-v04-player-from-clues.json (package_id GGP4:7b4a6260b92fc2a0d6902e56).
// Pure reshaping of the already-QA'd Engine package -- no facts added, removed, or
// reordered. Re-run the script after regenerating the source package to refresh this file.
//
// NOT WIRED INTO PRODUCTION NAVIGATION: only reachable via the local hidden route
// (#clues) behind the ENABLE_PLAYER_FROM_CLUES_V01 flag in app.js. See
// PLAYER_FROM_CLUES_FRONTEND_INTEGRATION_PLAN.md.
window.PLAYER_FROM_CLUES_V01 = {
  "packageId": "GGP4:7b4a6260b92fc2a0d6902e56",
  "packageVersion": "0.4",
  "mechanic": "identify_player_from_clues",
  "gameTitle": "Player From Clues",
  "gameInstructions": "You'll see a sequence of verified clues about one NFL player, revealed one at a time and narrowing from broad to specific. Identify the player.",
  "generatedAt": "2026-08-09T22:30:32.930547+00:00",
  "qaStatus": "PASSED",
  "puzzleCount": 25,
  "puzzles": [
    {
      "id": 620000,
      "answer": {
        "playerId": "PFR:FryxDu20",
        "displayName": "Dustin Fry"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 5.",
          "candidatesBefore": 4506,
          "candidatesAfter": 600,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_year",
          "text": "This player was drafted in 2007.",
          "candidatesBefore": 600,
          "candidatesAfter": 34,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2007 to 2007.",
          "candidatesBefore": 34,
          "candidatesAfter": 5,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #139 overall pick.",
          "candidatesBefore": 5,
          "candidatesAfter": 1,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 620001,
      "answer": {
        "playerId": "PFR:JameTo99",
        "displayName": "Tory James"
      },
      "clues": [
        {
          "index": 0,
          "type": "position",
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 4506,
          "candidatesAfter": 666,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_round",
          "text": "This player was drafted in round 2.",
          "candidatesBefore": 666,
          "candidatesAfter": 112,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2006.",
          "candidatesBefore": 112,
          "candidatesAfter": 10,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "drafting_franchise",
          "text": "This player was drafted by the Denver Broncos.",
          "candidatesBefore": 10,
          "candidatesAfter": 2,
          "provenance": {
            "table": "draft_facts+team_aliases",
            "field": "draft_team (season-resolved)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #44 overall pick.",
          "candidatesBefore": 2,
          "candidatesAfter": 1,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 620002,
      "answer": {
        "playerId": "PFR:CampCa00",
        "displayName": "Caleb Campbell"
      },
      "clues": [
        {
          "index": 0,
          "type": "position",
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 4506,
          "candidatesAfter": 666,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_round",
          "text": "This player was drafted in round 7.",
          "candidatesBefore": 666,
          "candidatesAfter": 89,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "draft_year",
          "text": "This player was drafted in 2008.",
          "candidatesBefore": 89,
          "candidatesAfter": 6,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2010 to 2010.",
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
      "id": 620003,
      "answer": {
        "playerId": "PFR:TaylHe21",
        "displayName": "Herbert Taylor"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 6.",
          "candidatesBefore": 4506,
          "candidatesAfter": 591,
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
          "text": "This player's position at the time of the draft was T.",
          "candidatesBefore": 591,
          "candidatesAfter": 37,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "draft_year",
          "text": "This player was drafted in 2007.",
          "candidatesBefore": 37,
          "candidatesAfter": 4,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2007 to 2012.",
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
      "id": 620004,
      "answer": {
        "playerId": "PFR:JohnBr00",
        "displayName": "Brad Johnson"
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
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2008.",
          "candidatesBefore": 2851,
          "candidatesAfter": 119,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "position",
          "text": "This player's position at the time of the draft was QB.",
          "candidatesBefore": 119,
          "candidatesAfter": 5,
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
          "text": "This player was selected with the #227 overall pick.",
          "candidatesBefore": 5,
          "candidatesAfter": 1,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 620005,
      "answer": {
        "playerId": "PFR:CarlCo20",
        "displayName": "Cooper Carlisle"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 4.",
          "candidatesBefore": 4506,
          "candidatesAfter": 666,
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
          "text": "This player's position at the time of the draft was G.",
          "candidatesBefore": 666,
          "candidatesAfter": 39,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "drafting_franchise",
          "text": "This player was drafted by the Denver Broncos.",
          "candidatesBefore": 39,
          "candidatesAfter": 3,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2012.",
          "candidatesBefore": 3,
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
      "id": 620006,
      "answer": {
        "playerId": "PFR:ThomDo21",
        "displayName": "Dontarrious Thomas"
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
          "text": "This player was drafted in round 2.",
          "candidatesBefore": 2851,
          "candidatesAfter": 447,
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
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 447,
          "candidatesAfter": 61,
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
          "text": "This player was selected with the #48 overall pick.",
          "candidatesBefore": 61,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2008.",
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
      "id": 620007,
      "answer": {
        "playerId": "PFR:CoheLa99",
        "displayName": "Landon Cohen"
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
          "text": "This player was drafted in round 7.",
          "candidatesBefore": 2851,
          "candidatesAfter": 308,
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
          "text": "This player's position at the time of the draft was DT.",
          "candidatesBefore": 308,
          "candidatesAfter": 30,
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
          "text": "This player was selected with the #216 overall pick.",
          "candidatesBefore": 30,
          "candidatesAfter": 2,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2008 to 2013.",
          "candidatesBefore": 2,
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
      "id": 620008,
      "answer": {
        "playerId": "PFR:JohnCh26",
        "displayName": "Chris Johnson"
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
          "type": "won_super_bowl",
          "text": "This player was on the active roster of a team that won the Super Bowl at some point in his career.",
          "candidatesBefore": 2851,
          "candidatesAfter": 492,
          "provenance": {
            "table": "canonical_roster_seasons+season_standings",
            "field": "playoff_result='WonSB' (derived join on team_code+season, games>0)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "position",
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 492,
          "candidatesAfter": 88,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "drafting_franchise",
          "text": "This player was drafted by the Green Bay Packers.",
          "candidatesBefore": 88,
          "candidatesAfter": 8,
          "provenance": {
            "table": "draft_facts+team_aliases",
            "field": "draft_team (season-resolved)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2007 to 2012.",
          "candidatesBefore": 8,
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
      "id": 620009,
      "answer": {
        "playerId": "PFR:ShorBr20",
        "displayName": "Brandon Short"
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
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 418,
          "candidatesAfter": 61,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "drafting_franchise",
          "text": "This player was drafted by the New York Giants.",
          "candidatesBefore": 61,
          "candidatesAfter": 5,
          "provenance": {
            "table": "draft_facts+team_aliases",
            "field": "draft_team (season-resolved)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2006.",
          "candidatesBefore": 5,
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
      "id": 620010,
      "answer": {
        "playerId": "PFR:HerrDa00",
        "displayName": "Dan Herron"
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
          "text": "This player was drafted in round 6.",
          "candidatesBefore": 2851,
          "candidatesAfter": 332,
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
          "text": "This player's position at the time of the draft was RB.",
          "candidatesBefore": 332,
          "candidatesAfter": 42,
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
          "text": "This player was drafted in 2012.",
          "candidatesBefore": 42,
          "candidatesAfter": 3,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2012 to 2015.",
          "candidatesBefore": 3,
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
      "id": 620011,
      "answer": {
        "playerId": "PFR:GainCh00",
        "displayName": "Charles Gaines"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 6.",
          "candidatesBefore": 4506,
          "candidatesAfter": 591,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_year",
          "text": "This player was drafted in 2015.",
          "candidatesBefore": 591,
          "candidatesAfter": 35,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2015 to 2015.",
          "candidatesBefore": 35,
          "candidatesAfter": 11,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "position",
          "text": "This player's position at the time of the draft was CB.",
          "candidatesBefore": 11,
          "candidatesAfter": 2,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "college",
          "text": "This player attended Louisville before entering the NFL draft.",
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
      "id": 620012,
      "answer": {
        "playerId": "PFR:BailBo20",
        "displayName": "Boss Bailey"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 2.",
          "candidatesBefore": 4506,
          "candidatesAfter": 657,
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
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 657,
          "candidatesAfter": 84,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "draft_year",
          "text": "This player was drafted in 2003.",
          "candidatesBefore": 84,
          "candidatesAfter": 6,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2008.",
          "candidatesBefore": 6,
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
          "type": "draft_pick_overall",
          "text": "This player was selected with the #34 overall pick.",
          "candidatesBefore": 2,
          "candidatesAfter": 1,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 620013,
      "answer": {
        "playerId": "PFR:ApkeTr00",
        "displayName": "Troy Apke"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 4.",
          "candidatesBefore": 4506,
          "candidatesAfter": 666,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_year",
          "text": "This player was drafted in 2018.",
          "candidatesBefore": 666,
          "candidatesAfter": 37,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2018 to 2018.",
          "candidatesBefore": 37,
          "candidatesAfter": 33,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "position",
          "text": "This player's position at the time of the draft was S.",
          "candidatesBefore": 33,
          "candidatesAfter": 4,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "college",
          "text": "This player attended Penn State before entering the NFL draft.",
          "candidatesBefore": 4,
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
      "id": 620014,
      "answer": {
        "playerId": "PFR:HumpD.00",
        "displayName": "D.J. Humphries"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 1.",
          "candidatesBefore": 4506,
          "candidatesAfter": 704,
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
          "text": "This player's position at the time of the draft was T.",
          "candidatesBefore": 704,
          "candidatesAfter": 83,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2016 to 2018.",
          "candidatesBefore": 83,
          "candidatesAfter": 5,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #24 overall pick.",
          "candidatesBefore": 5,
          "candidatesAfter": 1,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 620015,
      "answer": {
        "playerId": "PFR:WillDa99",
        "displayName": "Dan Williams"
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
          "text": "This player's position at the time of the draft was DT.",
          "candidatesBefore": 522,
          "candidatesAfter": 43,
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
          "candidatesBefore": 43,
          "candidatesAfter": 3,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2010 to 2016.",
          "candidatesBefore": 3,
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
      "id": 620016,
      "answer": {
        "playerId": "PFR:BrowAr00",
        "displayName": "Arthur Brown"
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
          "text": "This player was drafted in round 2.",
          "candidatesBefore": 2851,
          "candidatesAfter": 447,
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
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 447,
          "candidatesAfter": 61,
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
          "text": "This player was drafted in 2013.",
          "candidatesBefore": 61,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2013 to 2016.",
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
      "id": 620017,
      "answer": {
        "playerId": "PFR:HawkJe00",
        "displayName": "Jerald Hawkins"
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
          "text": "This player's position at the time of the draft was T.",
          "candidatesBefore": 418,
          "candidatesAfter": 28,
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
          "text": "This player was selected with the #123 overall pick.",
          "candidatesBefore": 28,
          "candidatesAfter": 2,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2017 to 2017.",
          "candidatesBefore": 2,
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
      "id": 620018,
      "answer": {
        "playerId": "PFR:TillTr20",
        "displayName": "Travares Tillman"
      },
      "clues": [
        {
          "index": 0,
          "type": "position",
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 4506,
          "candidatesAfter": 666,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 1,
          "type": "draft_round",
          "text": "This player was drafted in round 2.",
          "candidatesBefore": 666,
          "candidatesAfter": 112,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2007.",
          "candidatesBefore": 112,
          "candidatesAfter": 7,
          "provenance": {
            "table": "canonical_roster_seasons",
            "field": "MIN/MAX(season) WHERE games>0",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_year",
          "text": "This player was drafted in 2000.",
          "candidatesBefore": 7,
          "candidatesAfter": 2,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #58 overall pick.",
          "candidatesBefore": 2,
          "candidatesAfter": 1,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        }
      ],
      "finalCandidateCount": 1,
      "qaStatus": "PASSED"
    },
    {
      "id": 620019,
      "answer": {
        "playerId": "PFR:BrotKe00",
        "displayName": "Kentrell Brothers"
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
          "text": "This player was drafted in round 5.",
          "candidatesBefore": 372,
          "candidatesAfter": 53,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "drafting_franchise",
          "text": "This player was drafted by the Minnesota Vikings.",
          "candidatesBefore": 53,
          "candidatesAfter": 4,
          "provenance": {
            "table": "draft_facts+team_aliases",
            "field": "draft_team (season-resolved)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2016 to 2018.",
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
      "id": 620020,
      "answer": {
        "playerId": "PFR:VandLe00",
        "displayName": "Leighton Vander Esch"
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
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 522,
          "candidatesAfter": 55,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "drafting_franchise",
          "text": "This player was drafted by the Dallas Cowboys.",
          "candidatesBefore": 55,
          "candidatesAfter": 3,
          "provenance": {
            "table": "draft_facts+team_aliases",
            "field": "draft_team (season-resolved)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2018 to 2018.",
          "candidatesBefore": 3,
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
      "id": 620021,
      "answer": {
        "playerId": "PFR:WarfLa00",
        "displayName": "Larry Warford"
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
          "text": "This player was drafted in round 3.",
          "candidatesBefore": 2851,
          "candidatesAfter": 450,
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
          "text": "This player's position at the time of the draft was G.",
          "candidatesBefore": 450,
          "candidatesAfter": 29,
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
          "text": "This player was drafted in 2013.",
          "candidatesBefore": 29,
          "candidatesAfter": 2,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2013 to 2018.",
          "candidatesBefore": 2,
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
      "id": 620022,
      "answer": {
        "playerId": "PFR:BryaAu00",
        "displayName": "Austin Bryant"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 4.",
          "candidatesBefore": 4506,
          "candidatesAfter": 666,
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
          "text": "This player's position at the time of the draft was DE.",
          "candidatesBefore": 666,
          "candidatesAfter": 57,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "draft_year",
          "text": "This player was drafted in 2019.",
          "candidatesBefore": 57,
          "candidatesAfter": 5,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "college",
          "text": "This player attended Clemson before entering the NFL draft.",
          "candidatesBefore": 5,
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
      "id": 620023,
      "answer": {
        "playerId": "PFR:KropTr20",
        "displayName": "Troy Kropog"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 4.",
          "candidatesBefore": 4506,
          "candidatesAfter": 666,
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
          "text": "This player's position at the time of the draft was T.",
          "candidatesBefore": 666,
          "candidatesAfter": 43,
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
          "text": "This player was selected with the #135 overall pick.",
          "candidatesBefore": 43,
          "candidatesAfter": 2,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2009 to 2012.",
          "candidatesBefore": 2,
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
      "id": 620024,
      "answer": {
        "playerId": "PFR:MoreVe00",
        "displayName": "Vernand Morency"
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
          "text": "This player was drafted in round 3.",
          "candidatesBefore": 2851,
          "candidatesAfter": 450,
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
          "text": "This player's position at the time of the draft was RB.",
          "candidatesBefore": 450,
          "candidatesAfter": 37,
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
          "text": "This player was selected with the #73 overall pick.",
          "candidatesBefore": 37,
          "candidatesAfter": 5,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2007.",
          "candidatesBefore": 5,
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
