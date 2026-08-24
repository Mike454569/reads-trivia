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
        "playerId": "PFR:BrowJa23",
        "displayName": "Jason Brown"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 292,
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
          "text": "This player was drafted in 2005.",
          "candidatesBefore": 292,
          "candidatesAfter": 18,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2005 to 2011.",
          "candidatesBefore": 18,
          "candidatesAfter": 3,
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
          "text": "This player attended Air Force before entering the NFL draft.",
          "candidatesBefore": 3,
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
      "id": 620001,
      "answer": {
        "playerId": "PFR:JenkJo00",
        "displayName": "John Jenkins"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 334,
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
          "candidatesBefore": 334,
          "candidatesAfter": 27,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2013 to 2018.",
          "candidatesBefore": 27,
          "candidatesAfter": 3,
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
          "text": "This player was selected with the #82 overall pick.",
          "candidatesBefore": 3,
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
        "playerId": "PFR:MannPa20",
        "displayName": "Patrick Mannelly"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 193,
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
          "candidatesBefore": 193,
          "candidatesAfter": 12,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 1999 to 2013.",
          "candidatesBefore": 12,
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
        "playerId": "PFR:BrowJo02",
        "displayName": "John Brown"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 334,
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
          "text": "This player's position at the time of the draft was WR.",
          "candidatesBefore": 334,
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
          "type": "drafting_franchise",
          "text": "This player was drafted by the Arizona Cardinals.",
          "candidatesBefore": 43,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2014 to 2018.",
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
      "id": 620004,
      "answer": {
        "playerId": "PFR:FreeDe00",
        "displayName": "Devonta Freeman"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 292,
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
          "candidatesBefore": 292,
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
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2014 to 2018.",
          "candidatesBefore": 30,
          "candidatesAfter": 3,
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
          "text": "This player attended Florida State before entering the NFL draft.",
          "candidatesBefore": 3,
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
      "id": 620005,
      "answer": {
        "playerId": "PFR:BernMa20",
        "displayName": "Mackenzy Bernadeau"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 178,
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
          "candidatesBefore": 178,
          "candidatesAfter": 12,
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
          "text": "This player was drafted by the Carolina Panthers.",
          "candidatesBefore": 12,
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
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2009 to 2015.",
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
      "id": 620006,
      "answer": {
        "playerId": "PFR:LehaMi20",
        "displayName": "Michael Lehan"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 2136,
          "candidatesAfter": 418,
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
          "candidatesBefore": 418,
          "candidatesAfter": 52,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #152 overall pick.",
          "candidatesBefore": 52,
          "candidatesAfter": 3,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2003 to 2008.",
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
      "id": 620007,
      "answer": {
        "playerId": "PFR:ZastDa20",
        "displayName": "Dave Zastudil"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 292,
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
          "text": "This player was drafted in 2002.",
          "candidatesBefore": 292,
          "candidatesAfter": 15,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2002 to 2014.",
          "candidatesBefore": 15,
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
          "text": "This player was selected with the #112 overall pick.",
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
      "id": 620008,
      "answer": {
        "playerId": "PFR:CoopMa00",
        "displayName": "Marcus Cooper"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 2136,
          "candidatesAfter": 418,
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
          "text": "This player was drafted in round 7.",
          "candidatesBefore": 418,
          "candidatesAfter": 27,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2013 to 2018.",
          "candidatesBefore": 27,
          "candidatesAfter": 3,
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
          "text": "This player attended Rutgers before entering the NFL draft.",
          "candidatesBefore": 3,
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
      "id": 620009,
      "answer": {
        "playerId": "PFR:SidnDa20",
        "displayName": "Dainon Sidney"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 2136,
          "candidatesAfter": 418,
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
          "text": "This player was drafted in round 3.",
          "candidatesBefore": 418,
          "candidatesAfter": 59,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #77 overall pick.",
          "candidatesBefore": 59,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 1999 to 2003.",
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
      "id": 620010,
      "answer": {
        "playerId": "PFR:SimpJe00",
        "displayName": "Jerome Simpson"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 405,
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
          "text": "This player's position at the time of the draft was WR.",
          "candidatesBefore": 405,
          "candidatesAfter": 50,
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
          "text": "This player was drafted in 2008.",
          "candidatesBefore": 50,
          "candidatesAfter": 5,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2008 to 2015.",
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
      "id": 620011,
      "answer": {
        "playerId": "PFR:DoucEa00",
        "displayName": "Early Doucet"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 334,
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
          "text": "This player's position at the time of the draft was WR.",
          "candidatesBefore": 334,
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
          "text": "This player was drafted in 2008.",
          "candidatesBefore": 43,
          "candidatesAfter": 5,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2008 to 2012.",
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
      "id": 620012,
      "answer": {
        "playerId": "PFR:WashLe00",
        "displayName": "Leon Washington"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 292,
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
          "candidatesBefore": 292,
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
          "type": "college",
          "text": "This player attended Florida State before entering the NFL draft.",
          "candidatesBefore": 30,
          "candidatesAfter": 2,
          "provenance": {
            "table": "relationships(ATTENDED_BEFORE_DRAFT)+schools",
            "field": "school_name",
            "sourceId": "READS_IDENTITY_BRIDGE",
            "verificationStatus": "PRODUCTION_SAFE_DERIVED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2014.",
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
      "id": 620013,
      "answer": {
        "playerId": "PFR:PaceCa20",
        "displayName": "Calvin Pace"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 487,
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
          "candidatesBefore": 487,
          "candidatesAfter": 63,
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
          "candidatesBefore": 63,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2003 to 2015.",
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
      "id": 620014,
      "answer": {
        "playerId": "PFR:WileMa00",
        "displayName": "Marcellus Wiley"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 405,
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
          "candidatesBefore": 405,
          "candidatesAfter": 33,
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
          "text": "This player was selected with the #52 overall pick.",
          "candidatesBefore": 33,
          "candidatesAfter": 3,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 1999 to 2006.",
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
      "id": 620015,
      "answer": {
        "playerId": "PFR:TappDa20",
        "displayName": "Darryl Tapp"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 405,
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
          "candidatesBefore": 405,
          "candidatesAfter": 33,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "team_history",
          "text": "At another point in his career, this player played for the Tampa Bay Buccaneers.",
          "candidatesBefore": 33,
          "candidatesAfter": 2,
          "provenance": {
            "table": "canonical_roster_seasons+team_aliases",
            "field": "team_code (season-resolved)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2006 to 2017.",
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
      "id": 620016,
      "answer": {
        "playerId": "PFR:SullJo24",
        "displayName": "John Sullivan"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 193,
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
          "candidatesBefore": 193,
          "candidatesAfter": 16,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2008 to 2018.",
          "candidatesBefore": 16,
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
          "text": "This player attended New Mexico before entering the NFL draft.",
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
      "id": 620017,
      "answer": {
        "playerId": "PFR:VilmJo99",
        "displayName": "Jonathan Vilma"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 487,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "won_super_bowl",
          "text": "This player was on the active roster of a team that won the Super Bowl at some point in his career.",
          "candidatesBefore": 487,
          "candidatesAfter": 111,
          "provenance": {
            "table": "canonical_roster_seasons+season_standings",
            "field": "playoff_result='WonSB' (derived join on team_code+season, games>0)",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "position",
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 111,
          "candidatesAfter": 15,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2004 to 2013.",
          "candidatesBefore": 15,
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
        "playerId": "PFR:ClarDe00",
        "displayName": "Desmond Clark"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 193,
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
          "text": "This player's position at the time of the draft was TE.",
          "candidatesBefore": 193,
          "candidatesAfter": 16,
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
          "text": "This player was selected with the #179 overall pick.",
          "candidatesBefore": 16,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 1999 to 2010.",
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
      "id": 620019,
      "answer": {
        "playerId": "PFR:CollTo00",
        "displayName": "Todd Collins"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 405,
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
          "text": "This player's position at the time of the draft was QB.",
          "candidatesBefore": 405,
          "candidatesAfter": 18,
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
          "text": "This player was drafted in 1995.",
          "candidatesBefore": 18,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 2001 to 2010.",
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
      "id": 620020,
      "answer": {
        "playerId": "PFR:SchwGe20",
        "displayName": "Geoff Schwartz"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "text": "This player's position at the time of the draft was T.",
          "candidatesBefore": 2136,
          "candidatesAfter": 183,
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
          "text": "This player was drafted in 2008.",
          "candidatesBefore": 183,
          "candidatesAfter": 17,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_season",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "draft_round",
          "text": "This player was drafted in round 7.",
          "candidatesBefore": 17,
          "candidatesAfter": 2,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2009 to 2015.",
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
      "id": 620021,
      "answer": {
        "playerId": "PFR:SimmJa20",
        "displayName": "Jason Simmons"
      },
      "clues": [
        {
          "index": 0,
          "type": "position",
          "text": "This player's position at the time of the draft was DB.",
          "candidatesBefore": 2489,
          "candidatesAfter": 486,
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
          "text": "This player was drafted in round 5.",
          "candidatesBefore": 486,
          "candidatesAfter": 58,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 2,
          "type": "draft_pick_overall",
          "text": "This player was selected with the #137 overall pick.",
          "candidatesBefore": 58,
          "candidatesAfter": 4,
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
          "text": "This player's NFL career (by recorded roster seasons) spanned 1999 to 2007.",
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
      "id": 620022,
      "answer": {
        "playerId": "PFR:DaviDe00",
        "displayName": "Demario Davis"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 334,
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
          "candidatesBefore": 334,
          "candidatesAfter": 46,
          "provenance": {
            "table": "draft_facts",
            "field": "position",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2012 to 2018.",
          "candidatesBefore": 46,
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
          "text": "This player attended Arkansas State before entering the NFL draft.",
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
      "id": 620023,
      "answer": {
        "playerId": "PFR:HaggCl20",
        "displayName": "Clark Haggans"
      },
      "clues": [
        {
          "index": 0,
          "type": "postseason_participation",
          "text": "This player was on an NFL team's active roster during a playoff run at some point in his career.",
          "candidatesBefore": 2489,
          "candidatesAfter": 2136,
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
          "candidatesBefore": 2136,
          "candidatesAfter": 473,
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
          "text": "This player's position at the time of the draft was LB.",
          "candidatesBefore": 473,
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
          "type": "draft_round",
          "text": "This player was drafted in round 5.",
          "candidatesBefore": 61,
          "candidatesAfter": 6,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_round",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 4,
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2001 to 2012.",
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
      "id": 620024,
      "answer": {
        "playerId": "PFR:QuicBr00",
        "displayName": "Brian Quick"
      },
      "clues": [
        {
          "index": 0,
          "type": "draft_round",
          "text": "This player was drafted in round 2.",
          "candidatesBefore": 2489,
          "candidatesAfter": 477,
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
          "text": "This player's position at the time of the draft was WR.",
          "candidatesBefore": 477,
          "candidatesAfter": 59,
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
          "text": "This player was selected with the #33 overall pick.",
          "candidatesBefore": 59,
          "candidatesAfter": 5,
          "provenance": {
            "table": "draft_facts",
            "field": "draft_pick_overall",
            "sourceId": "NFLVERSE_DATA",
            "verificationStatus": "SOURCE_BACKED"
          }
        },
        {
          "index": 3,
          "type": "drafting_franchise",
          "text": "This player was drafted by the St Louis Rams.",
          "candidatesBefore": 5,
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
          "type": "career_span",
          "text": "This player's NFL career (by recorded roster seasons) spanned 2012 to 2018.",
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
    }
  ]
};
