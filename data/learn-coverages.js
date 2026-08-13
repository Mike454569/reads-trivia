// Defensive Coverages Learn module -- structured concepts, relationships, lessons, and
// interactive exercises, exported from the Engine's knowledge graph (knowledge_nodes/
// knowledge_edges) + learn_lessons/learn_exercises tables. Source: the user's Football 101
// Encyclopedia / 700 Question Master workbook (see tools/learn/build_coverage_module.py for
// full provenance and the real workbook row citations for every concept below). Not hand-
// maintained -- re-run tools/learn/export_coverage_module.py to regenerate from the DB.
window.LEARN_COVERAGE_MODULE = {
  "module": "defensive_coverages",
  "concepts": {
    "MAN_COVERAGE": {
      "concept_family": "coverage_principle",
      "difficulty": "beginner",
      "man_or_zone": "man",
      "summary": "Each defender is assigned to follow and cover one specific offensive player, mirroring his movements wherever he goes on the field, rather than covering an area.",
      "source_rows": [
        99
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "MAN_COVERAGE",
      "label": "Man Coverage",
      "verification_status": "SOURCE_BACKED"
    },
    "ZONE_COVERAGE": {
      "concept_family": "coverage_principle",
      "difficulty": "beginner",
      "man_or_zone": "zone",
      "summary": "Each defender is responsible for a specific area of the field and covers whichever receiver enters that area, rather than following one specific player.",
      "source_rows": [
        98
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "ZONE_COVERAGE",
      "label": "Zone Coverage",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_0": {
      "concept_family": "coverage_shell",
      "difficulty": "beginner",
      "man_or_zone": "man",
      "shell": "no_deep_safety",
      "deep_defenders": 0,
      "summary": "Zero deep safeties -- every eligible receiver is covered man-to-man with no safety help over the top.",
      "strengths": [
        "Frees up an extra pass rusher, since no safety is held deep",
        "Tight, disruptive coverage on every receiver at the snap"
      ],
      "weaknesses": [
        "No help over the top -- one blown 1-on-1 matchup can be a touchdown"
      ],
      "pre_snap_indicators": "No safety aligned deep; often paired with a heavy pressure/blitz look.",
      "common_beaters_text": "Any receiver who can win a deep 1-on-1 rep, or a quick-breaking route that gets the ball out before pressure arrives.",
      "source_rows": [
        81
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_0",
      "label": "Cover 0",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_1": {
      "concept_family": "coverage_shell",
      "difficulty": "beginner",
      "man_or_zone": "man",
      "shell": "single_high",
      "deep_defenders": 1,
      "summary": "One deep safety in the middle of the field (single-high) with man coverage everywhere underneath, often with an extra rusher or a spy.",
      "aka": [
        "Man-Free"
      ],
      "pre_snap_indicators": "A single safety aligned deep in the middle of the field.",
      "source_rows": [
        82,
        100
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_1",
      "label": "Cover 1 (Man-Free)",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_2": {
      "concept_family": "coverage_shell",
      "difficulty": "beginner",
      "man_or_zone": "zone",
      "shell": "two_high",
      "deep_defenders": 2,
      "summary": "Two deep safeties split the field evenly, each responsible for a deep half, with zone coverage underneath.",
      "weaknesses": [
        "The deep middle of the field, the seam between the two safeties, is a natural soft spot",
        "Corners playing the flat underneath have no deep help on quick outside-breaking routes"
      ],
      "pre_snap_indicators": "Two safeties aligned deep, split toward each sideline.",
      "source_rows": [
        83,
        102,
        474
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_2",
      "label": "Cover 2",
      "verification_status": "SOURCE_BACKED"
    },
    "TAMPA_2": {
      "concept_family": "coverage_variation",
      "difficulty": "intermediate",
      "man_or_zone": "zone",
      "shell": "two_high",
      "deep_defenders": 2,
      "variation_of": "COVER_2",
      "summary": "A Cover 2 variant, associated with the Tampa Bay Buccaneers under Tony Dungy and Monte Kiffin, where the middle linebacker drops deep down the field into the seam between the two deep safeties -- directly closing Cover 2's biggest weakness.",
      "strengths": [
        "Closes the deep-middle seam that's normally Cover 2's weak point"
      ],
      "coaching_points": [
        "Requires an athletic middle linebacker who can run with vertical seam routes all the way downfield"
      ],
      "source_rows": [
        87
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "TAMPA_2",
      "label": "Tampa 2",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_2_MAN": {
      "concept_family": "coverage_variation",
      "difficulty": "intermediate",
      "man_or_zone": "hybrid",
      "shell": "two_high",
      "deep_defenders": 2,
      "variation_of": "COVER_2",
      "aka": [
        "Man-Under, Two-Deep"
      ],
      "summary": "Man coverage underneath combined with two deep safeties providing help over the top -- also called 'Man-Under, Two-Deep.'",
      "source_rows": [
        88,
        489
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_2_MAN",
      "label": "Cover 2 Man",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_3": {
      "concept_family": "coverage_shell",
      "difficulty": "beginner",
      "man_or_zone": "zone",
      "shell": "single_high",
      "deep_defenders": 3,
      "summary": "Three deep defenders -- typically both cornerbacks and the free safety -- each cover a deep third of the field, with zone coverage underneath.",
      "weaknesses": [
        "The deep out route, into the void between a corner's deep-third zone and the underneath flat defender, is a well-known Cover 3 vulnerability"
      ],
      "pre_snap_indicators": "A single safety aligned deep in the middle of the field (same shell look as Cover 1 -- the difference is confirmed after the snap).",
      "source_rows": [
        84,
        473,
        485
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_3",
      "label": "Cover 3",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_4": {
      "concept_family": "coverage_shell",
      "difficulty": "intermediate",
      "man_or_zone": "zone",
      "shell": "two_high",
      "deep_defenders": 4,
      "aka": [
        "Quarters"
      ],
      "summary": "Four deep defenders -- both cornerbacks and both safeties -- each responsible for a deep quarter of the field. Often called 'quarters' coverage.",
      "pre_snap_indicators": "Two safeties aligned deep, similar to a Cover 2 shell -- confirmed as Cover 4 by the corners' depth and technique after the snap.",
      "source_rows": [
        85,
        475
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_4",
      "label": "Cover 4 (Quarters)",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_6": {
      "concept_family": "coverage_shell",
      "difficulty": "advanced",
      "man_or_zone": "zone",
      "shell": "two_high",
      "deep_defenders": "4 (split 2-and-2)",
      "aka": [
        "Quarter-Quarter-Half"
      ],
      "relies_on": [
        "COVER_4",
        "COVER_2"
      ],
      "summary": "A hybrid coverage that plays Cover 4 (quarters) principles on one side of the field and Cover 2 (half) principles on the other -- often called 'quarter-quarter-half.'",
      "coaching_points": [
        "Commonly used to match a formation's strength -- quarters to the side with more receivers, a half-field zone to the boundary side"
      ],
      "source_rows": [
        86
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_6",
      "label": "Cover 6 (Quarter-Quarter-Half)",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_1_ROBBER": {
      "concept_family": "coverage_rotation",
      "difficulty": "advanced",
      "variation_of": "COVER_1",
      "summary": "A Cover 1 variant where the deep safety, instead of staying deep, drops down to 'rob' or jump underneath routes in the middle of the field.",
      "source_rows": [
        462,
        89
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_1_ROBBER",
      "label": "Cover 1 Robber",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_2_INVERT": {
      "concept_family": "coverage_rotation",
      "difficulty": "advanced",
      "variation_of": "COVER_2",
      "summary": "A Cover 2 rotation where the corner and safety swap their traditional roles -- the corner rotates to a deep half while the safety rolls down underneath.",
      "source_rows": [
        120,
        461
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_2_INVERT",
      "label": "Cover 2 Invert",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_3_CLOUD": {
      "concept_family": "coverage_rotation",
      "difficulty": "advanced",
      "variation_of": "COVER_3",
      "summary": "A Cover 3 rotation where the safety rotates down to help the corner from outside leverage (the 'Cloud' call).",
      "source_rows": [
        112,
        463
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_3_CLOUD",
      "label": "Cover 3 Cloud",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_3_SKY": {
      "concept_family": "coverage_rotation",
      "difficulty": "advanced",
      "variation_of": "COVER_3",
      "summary": "A Cover 3 rotation where the safety rotates down to help the corner from inside leverage (the 'Sky' call) -- the complementary rotation to Cloud.",
      "source_rows": [
        113,
        464
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_3_SKY",
      "label": "Cover 3 Sky",
      "verification_status": "SOURCE_BACKED"
    },
    "COVER_3_BUZZ": {
      "concept_family": "coverage_rotation",
      "difficulty": "advanced",
      "variation_of": "COVER_3",
      "summary": "A Cover 3 rotation where the safety 'buzzes' down into a shallow underneath zone instead of staying deep.",
      "source_rows": [
        465
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVER_3_BUZZ",
      "label": "Cover 3 Buzz",
      "verification_status": "SOURCE_BACKED"
    },
    "SINGLE_HIGH_SHELL": {
      "concept_family": "coverage_shell_read",
      "difficulty": "beginner",
      "summary": "A single safety aligned deep in the middle of the field before the snap -- a pre-snap indicator shared by Cover 1 and Cover 3 (the defense confirms which after the snap).",
      "source_rows": [
        101
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "SINGLE_HIGH_SHELL",
      "label": "Single-High Shell",
      "verification_status": "SOURCE_BACKED"
    },
    "TWO_HIGH_SHELL": {
      "concept_family": "coverage_shell_read",
      "difficulty": "beginner",
      "summary": "Two safeties aligned deep, split toward each sideline, before the snap -- a pre-snap indicator shared by Cover 2, Cover 4, and Cover 6.",
      "source_rows": [
        102
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "TWO_HIGH_SHELL",
      "label": "Two-High Shell",
      "verification_status": "SOURCE_BACKED"
    },
    "PRESS_TECHNIQUE": {
      "concept_family": "coverage_technique",
      "difficulty": "beginner",
      "summary": "A cornerback lines up tight to the line of scrimmage and directly challenges the receiver at the snap.",
      "source_rows": [
        94
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "PRESS_TECHNIQUE",
      "label": "Press Technique",
      "verification_status": "SOURCE_BACKED"
    },
    "OFF_TECHNIQUE": {
      "concept_family": "coverage_technique",
      "difficulty": "beginner",
      "summary": "A cornerback lines up several yards off the receiver, reading the play develop before reacting.",
      "source_rows": [
        95
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "OFF_TECHNIQUE",
      "label": "Off Technique",
      "verification_status": "SOURCE_BACKED"
    },
    "TRAIL_TECHNIQUE": {
      "concept_family": "coverage_technique",
      "difficulty": "intermediate",
      "summary": "A defender covers a receiver from behind, trailing the route, rather than facing him.",
      "source_rows": [
        96
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "TRAIL_TECHNIQUE",
      "label": "Trail Technique",
      "verification_status": "SOURCE_BACKED"
    },
    "BAIL_TECHNIQUE": {
      "concept_family": "coverage_technique",
      "difficulty": "intermediate",
      "summary": "A cornerback shows press coverage before the snap, then backpedals into a deep zone -- a coverage disguise.",
      "source_rows": [
        97
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "BAIL_TECHNIQUE",
      "label": "Bail Technique",
      "verification_status": "SOURCE_BACKED"
    },
    "CATCH_TECHNIQUE": {
      "concept_family": "coverage_technique",
      "difficulty": "intermediate",
      "summary": "A cornerback stays square to mirror the receiver rather than turning to run with him.",
      "source_rows": [
        481
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "CATCH_TECHNIQUE",
      "label": "Catch Technique",
      "verification_status": "SOURCE_BACKED"
    },
    "LEVERAGE": {
      "concept_family": "coverage_fundamental",
      "difficulty": "beginner",
      "summary": "A defender's positioning relative to a receiver -- playing to take away either the inside or outside release.",
      "source_rows": [
        469
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "LEVERAGE",
      "label": "Leverage",
      "verification_status": "SOURCE_BACKED"
    },
    "CUSHION": {
      "concept_family": "coverage_fundamental",
      "difficulty": "beginner",
      "summary": "The distance a defensive back gives a receiver before the snap in off coverage.",
      "source_rows": [
        470
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "CUSHION",
      "label": "Cushion",
      "verification_status": "SOURCE_BACKED"
    },
    "MEG_TECHNIQUE": {
      "concept_family": "coverage_technique",
      "difficulty": "advanced",
      "summary": "'Man Everywhere he Goes' -- a defender plays true man coverage on a receiver regardless of his route, common inside quarters (Cover 4) schemes.",
      "source_rows": [
        466
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "MEG_TECHNIQUE",
      "label": "MEG (Man Everywhere he Goes)",
      "verification_status": "SOURCE_BACKED"
    },
    "MATCH_COVERAGE": {
      "concept_family": "coverage_principle",
      "difficulty": "advanced",
      "summary": "A modern hybrid concept: defenders start in zone drops but convert to man coverage based on the routes receivers actually run -- pattern-matching zone into man.",
      "source_rows": [
        93,
        108
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "MATCH_COVERAGE",
      "label": "Match Coverage",
      "verification_status": "SOURCE_BACKED"
    },
    "ROBBER_COVERAGE": {
      "concept_family": "coverage_technique",
      "difficulty": "advanced",
      "summary": "A defender reads the quarterback's eyes and 'robs' or jumps a route in the middle of the field, often a safety crashing down from depth.",
      "source_rows": [
        89
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "ROBBER_COVERAGE",
      "label": "Robber Coverage",
      "verification_status": "SOURCE_BACKED"
    },
    "BRACKET_COVERAGE": {
      "concept_family": "coverage_technique",
      "difficulty": "advanced",
      "summary": "Two defenders are assigned to a single dangerous receiver, one underneath and one over the top.",
      "source_rows": [
        91
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "BRACKET_COVERAGE",
      "label": "Bracket Coverage",
      "verification_status": "SOURCE_BACKED"
    },
    "PALMS_COVERAGE": {
      "concept_family": "coverage_technique",
      "difficulty": "advanced",
      "aka": [
        "Read coverage",
        "Smoke coverage"
      ],
      "summary": "Common versus stacked or bunch receiver sets -- two defenders are assigned to take away both a flat route and a vertical route from a single receiver combination.",
      "source_rows": [
        90
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "PALMS_COVERAGE",
      "label": "Palms Coverage",
      "verification_status": "SOURCE_BACKED"
    },
    "BANJO_COVERAGE": {
      "concept_family": "coverage_technique",
      "difficulty": "advanced",
      "summary": "A coverage call where two defenders switch assignments mid-play based on receiver release, common versus stacked receivers.",
      "source_rows": [
        92,
        479
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "BANJO_COVERAGE",
      "label": "Banjo Coverage",
      "verification_status": "SOURCE_BACKED"
    },
    "PREVENT_DEFENSE": {
      "concept_family": "coverage_situational",
      "difficulty": "beginner",
      "summary": "A deep, conservative defensive strategy used to protect a lead late in a game -- prioritizing not giving up a big play over stopping short completions.",
      "source_rows": [
        115,
        114
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "PREVENT_DEFENSE",
      "label": "Prevent Defense",
      "verification_status": "SOURCE_BACKED"
    },
    "COVERAGE_DISGUISE": {
      "concept_family": "coverage_principle",
      "difficulty": "advanced",
      "summary": "A defense shows one coverage shell before the snap, then rotates to a different look after the ball is snapped, to confuse the quarterback's pre-snap read.",
      "source_rows": [
        103,
        118,
        483
      ],
      "source_sheet": "Football 101 Trivia (category: Pass Coverages)",
      "canonical_id": "COVERAGE_DISGUISE",
      "label": "Coverage Disguise / Rotation",
      "verification_status": "SOURCE_BACKED"
    }
  },
  "relationships": [
    {
      "source": "BAIL_TECHNIQUE",
      "predicate": "IS_A",
      "target": "COVERAGE_DISGUISE"
    },
    {
      "source": "COVER_0",
      "predicate": "IS_A",
      "target": "MAN_COVERAGE"
    },
    {
      "source": "COVER_0",
      "predicate": "USES_SHELL",
      "target": "SINGLE_HIGH_SHELL"
    },
    {
      "source": "COVER_1",
      "predicate": "IS_A",
      "target": "MAN_COVERAGE"
    },
    {
      "source": "COVER_1",
      "predicate": "SHARES_PRESNAP_SHELL_WITH",
      "target": "COVER_3"
    },
    {
      "source": "COVER_1",
      "predicate": "USES_SHELL",
      "target": "SINGLE_HIGH_SHELL"
    },
    {
      "source": "COVER_1_ROBBER",
      "predicate": "USES_TECHNIQUE",
      "target": "ROBBER_COVERAGE"
    },
    {
      "source": "COVER_1_ROBBER",
      "predicate": "VARIATION_OF",
      "target": "COVER_1"
    },
    {
      "source": "COVER_2",
      "predicate": "IS_A",
      "target": "ZONE_COVERAGE"
    },
    {
      "source": "COVER_2",
      "predicate": "SHARES_PRESNAP_SHELL_WITH",
      "target": "COVER_4"
    },
    {
      "source": "COVER_2",
      "predicate": "USES_SHELL",
      "target": "TWO_HIGH_SHELL"
    },
    {
      "source": "COVER_2_INVERT",
      "predicate": "VARIATION_OF",
      "target": "COVER_2"
    },
    {
      "source": "COVER_2_MAN",
      "predicate": "USES_SHELL",
      "target": "TWO_HIGH_SHELL"
    },
    {
      "source": "COVER_2_MAN",
      "predicate": "VARIATION_OF",
      "target": "COVER_2"
    },
    {
      "source": "COVER_3",
      "predicate": "IS_A",
      "target": "ZONE_COVERAGE"
    },
    {
      "source": "COVER_3",
      "predicate": "USES_SHELL",
      "target": "SINGLE_HIGH_SHELL"
    },
    {
      "source": "COVER_3_BUZZ",
      "predicate": "VARIATION_OF",
      "target": "COVER_3"
    },
    {
      "source": "COVER_3_CLOUD",
      "predicate": "VARIATION_OF",
      "target": "COVER_3"
    },
    {
      "source": "COVER_3_SKY",
      "predicate": "VARIATION_OF",
      "target": "COVER_3"
    },
    {
      "source": "COVER_4",
      "predicate": "IS_A",
      "target": "ZONE_COVERAGE"
    },
    {
      "source": "COVER_4",
      "predicate": "USES_SHELL",
      "target": "TWO_HIGH_SHELL"
    },
    {
      "source": "COVER_6",
      "predicate": "IS_A",
      "target": "ZONE_COVERAGE"
    },
    {
      "source": "COVER_6",
      "predicate": "RELIES_ON",
      "target": "COVER_2"
    },
    {
      "source": "COVER_6",
      "predicate": "RELIES_ON",
      "target": "COVER_4"
    },
    {
      "source": "COVER_6",
      "predicate": "USES_SHELL",
      "target": "TWO_HIGH_SHELL"
    },
    {
      "source": "MATCH_COVERAGE",
      "predicate": "RELATED_TO",
      "target": "MEG_TECHNIQUE"
    },
    {
      "source": "PRESS_TECHNIQUE",
      "predicate": "CONTRASTS_WITH",
      "target": "OFF_TECHNIQUE"
    },
    {
      "source": "TAMPA_2",
      "predicate": "USES_SHELL",
      "target": "TWO_HIGH_SHELL"
    },
    {
      "source": "TAMPA_2",
      "predicate": "VARIATION_OF",
      "target": "COVER_2"
    },
    {
      "source": "TRAIL_TECHNIQUE",
      "predicate": "CONTRASTS_WITH",
      "target": "CATCH_TECHNIQUE"
    }
  ],
  "lessons": [
    {
      "lesson_id": "man_vs_zone_basics",
      "concept": "MAN_COVERAGE",
      "title": "Man vs. Zone: The Basics",
      "summary": "The single most important distinction in pass coverage -- everything else in this module builds on it.",
      "difficulty": "beginner",
      "order_index": 1,
      "prerequisites": [],
      "steps": [
        {
          "step_type": "teach",
          "content": "Every pass coverage a defense plays is built from one of two basic ideas: man coverage or zone coverage. Man coverage assigns each defender to a specific receiver -- follow him everywhere he goes. Zone coverage assigns each defender to an area of the field -- cover whoever runs into your area."
        },
        {
          "step_type": "show",
          "content": "In man coverage, a defender's eyes are on his receiver the whole play. In zone coverage, a defender's eyes are on the quarterback and the receivers who enter his area -- he never has to run stride-for-stride with any one player."
        },
        {
          "step_type": "explain",
          "content": "This distinction is why the same defensive personnel can play completely different coverages from the same starting alignment. A cornerback lined up across from a receiver could be about to run with him everywhere (man) or drop into a specific patch of grass and pass him off to someone else the moment he leaves it (zone)."
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_man_zone_def_1",
            "ex_man_zone_def_2"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_man_zone_check_1"
          ]
        },
        {
          "step_type": "apply",
          "content": "Every coverage in this module is built from man principles, zone principles, or a hybrid of both -- you'll be asked to identify which as you go."
        }
      ]
    },
    {
      "lesson_id": "cover_0",
      "concept": "COVER_0",
      "title": "Cover 0: All-Out Man",
      "summary": "Zero deep safeties, man everywhere, no help over the top.",
      "difficulty": "beginner",
      "order_index": 2,
      "prerequisites": [
        "man_vs_zone_basics"
      ],
      "steps": [
        {
          "step_type": "teach",
          "content": "Zero deep safeties -- every eligible receiver is covered man-to-man with no safety help over the top."
        },
        {
          "step_type": "show",
          "content": "Pre-snap, there's no safety aligned deep at all -- every defensive back is up near the line of scrimmage, and the defense often shows extra rushers.",
          "diagram_spec": {
            "field_view": "presnap_shell",
            "shell": "no_deep_safety",
            "defenders": [
              {
                "role": "CB",
                "align": "outside_left",
                "assignment": "man",
                "depth": "line"
              },
              {
                "role": "CB",
                "align": "outside_right",
                "assignment": "man",
                "depth": "line"
              },
              {
                "role": "S",
                "align": "underneath",
                "assignment": "man_or_blitz",
                "depth": "shallow"
              }
            ]
          }
        },
        {
          "step_type": "explain",
          "content": "Strengths: Frees up an extra pass rusher, since no safety is held deep; Tight, disruptive coverage on every receiver at the snap. Weaknesses: No help over the top -- one blown 1-on-1 matchup can be a touchdown. Pre-snap tell: No safety aligned deep; often paired with a heavy pressure/blitz look."
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_read_defense_cover0"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_name_concept_cover0"
          ]
        },
        {
          "step_type": "apply",
          "content": "Cover 0 is the highest-risk, highest-reward shell in this module -- it's the baseline every other coverage adds safety help on top of."
        }
      ]
    },
    {
      "lesson_id": "cover_1",
      "concept": "COVER_1",
      "title": "Cover 1: Man-Free",
      "summary": "One deep safety, man coverage everywhere else -- and its Robber variation.",
      "difficulty": "beginner",
      "order_index": 3,
      "prerequisites": [
        "cover_0"
      ],
      "steps": [
        {
          "step_type": "teach",
          "content": "One deep safety in the middle of the field (single-high) with man coverage everywhere underneath, often with an extra rusher or a spy."
        },
        {
          "step_type": "show",
          "content": "Pre-snap tell: A single safety aligned deep in the middle of the field. This is the same single-high look Cover 3 shows -- the defense confirms which one after the snap.",
          "diagram_spec": {
            "field_view": "presnap_shell",
            "shell": "single_high",
            "defenders": [
              {
                "role": "FS",
                "align": "middle",
                "assignment": "deep_middle",
                "depth": "deep"
              },
              {
                "role": "CB",
                "align": "outside_left",
                "assignment": "man",
                "depth": "line"
              },
              {
                "role": "CB",
                "align": "outside_right",
                "assignment": "man",
                "depth": "line"
              }
            ]
          }
        },
        {
          "step_type": "explain",
          "content": "A real variation: A Cover 1 variant where the deep safety, instead of staying deep, drops down to 'rob' or jump underneath routes in the middle of the field. Instead of staying deep, the free safety drops down to jump an underneath route he anticipates."
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_read_defense_cover1"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_name_concept_cover1"
          ]
        },
        {
          "step_type": "apply",
          "content": "Cover 1 and Cover 3 share the exact same pre-snap picture -- a single deep safety. The next lesson (Cover 3) is the first time you'll practice telling them apart."
        }
      ]
    },
    {
      "lesson_id": "cover_2",
      "concept": "COVER_2",
      "title": "Cover 2: Two Deep Halves",
      "summary": "Two safeties split the field, plus the Cover 2 Man and Invert variations.",
      "difficulty": "beginner",
      "order_index": 4,
      "prerequisites": [
        "cover_1"
      ],
      "steps": [
        {
          "step_type": "teach",
          "content": "Two deep safeties split the field evenly, each responsible for a deep half, with zone coverage underneath."
        },
        {
          "step_type": "show",
          "content": "Pre-snap tell: Two safeties aligned deep, split toward each sideline, before the snap -- a pre-snap indicator shared by Cover 2, Cover 4, and Cover 6.",
          "diagram_spec": {
            "field_view": "presnap_shell",
            "shell": "two_high",
            "defenders": [
              {
                "role": "FS",
                "align": "left_half",
                "assignment": "deep_half_left",
                "depth": "deep"
              },
              {
                "role": "SS",
                "align": "right_half",
                "assignment": "deep_half_right",
                "depth": "deep"
              },
              {
                "role": "CB",
                "align": "outside_left",
                "assignment": "flat_left",
                "depth": "underneath"
              },
              {
                "role": "CB",
                "align": "outside_right",
                "assignment": "flat_right",
                "depth": "underneath"
              }
            ]
          }
        },
        {
          "step_type": "explain",
          "content": "Weaknesses: The deep middle of the field, the seam between the two safeties, is a natural soft spot; Corners playing the flat underneath have no deep help on quick outside-breaking routes. Two real variations: Man coverage underneath combined with two deep safeties providing help over the top -- also called 'Man-Under, Two-Deep.' And Cover 2 Invert -- A Cover 2 rotation where the corner and safety swap their traditional roles -- the corner rotates to a deep half while the safety rolls down underneath."
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_read_defense_cover2"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_name_concept_cover2"
          ]
        },
        {
          "step_type": "apply",
          "content": "Cover 2's deep-middle soft spot is exactly what the next lesson, Tampa 2, was invented to fix."
        }
      ]
    },
    {
      "lesson_id": "tampa_2",
      "concept": "TAMPA_2",
      "title": "Tampa 2: Fixing Cover 2's Weakness",
      "summary": "How one linebacker's drop closes Cover 2's deep-middle void.",
      "difficulty": "intermediate",
      "order_index": 5,
      "prerequisites": [
        "cover_2"
      ],
      "steps": [
        {
          "step_type": "teach",
          "content": "A Cover 2 variant, associated with the Tampa Bay Buccaneers under Tony Dungy and Monte Kiffin, where the middle linebacker drops deep down the field into the seam between the two deep safeties -- directly closing Cover 2's biggest weakness."
        },
        {
          "step_type": "show",
          "content": "Same two-deep-safety picture as Cover 2 -- the difference is the middle linebacker, who sprints down the middle of the field after the snap instead of staying shallow.",
          "diagram_spec": {
            "field_view": "presnap_shell",
            "shell": "two_high",
            "defenders": [
              {
                "role": "FS",
                "align": "left_half",
                "assignment": "deep_half_left",
                "depth": "deep"
              },
              {
                "role": "SS",
                "align": "right_half",
                "assignment": "deep_half_right",
                "depth": "deep"
              },
              {
                "role": "MLB",
                "align": "middle",
                "assignment": "deep_middle_seam",
                "depth": "deep_late"
              }
            ]
          }
        },
        {
          "step_type": "explain",
          "content": "Recall Cover 2's weakness: the deep middle seam between the two safeties. Tampa 2 sends the middle linebacker to cover exactly that seam. Requires an athletic middle linebacker who can run with vertical seam routes all the way downfield."
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_name_concept_tampa2"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_read_defense_tampa2"
          ]
        },
        {
          "step_type": "apply",
          "content": "You now know both of the field's classic two-deep-safety shells and why a defense would pick one over the other."
        }
      ]
    },
    {
      "lesson_id": "cover_3",
      "concept": "COVER_3",
      "title": "Cover 3: Three Deep Thirds",
      "summary": "The other single-high shell, plus its Cloud/Sky/Buzz rotations.",
      "difficulty": "beginner",
      "order_index": 6,
      "prerequisites": [
        "tampa_2"
      ],
      "steps": [
        {
          "step_type": "teach",
          "content": "Three deep defenders -- typically both cornerbacks and the free safety -- each cover a deep third of the field, with zone coverage underneath."
        },
        {
          "step_type": "show",
          "content": "Same single-high pre-snap shell as Cover 1 -- both corners and the free safety each own a deep third after the snap.",
          "diagram_spec": {
            "field_view": "presnap_shell",
            "shell": "single_high",
            "defenders": [
              {
                "role": "CB",
                "align": "outside_left",
                "assignment": "deep_third_left",
                "depth": "deep"
              },
              {
                "role": "FS",
                "align": "middle",
                "assignment": "deep_third_middle",
                "depth": "deep"
              },
              {
                "role": "CB",
                "align": "outside_right",
                "assignment": "deep_third_right",
                "depth": "deep"
              }
            ]
          }
        },
        {
          "step_type": "explain",
          "content": "Known weakness: The deep out route, into the void between a corner's deep-third zone and the underneath flat defender, is a well-known Cover 3 vulnerability. Three real rotations you'll see called: Cloud (A Cover 3 rotation where the safety rotates down to help the corner from outside leverage (the 'Cloud' call).), Sky (A Cover 3 rotation where the safety rotates down to help the corner from inside leverage (the 'Sky' call) -- the complementary rotation to Cloud.), and Buzz (A Cover 3 rotation where the safety 'buzzes' down into a shallow underneath zone instead of staying deep.)"
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_read_defense_cover3",
            "ex_pre_post_cover1_vs_cover3"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_name_concept_cover3"
          ]
        },
        {
          "step_type": "apply",
          "content": "You can now recognize both single-high coverages (Cover 1 and Cover 3) and both two-high coverages (Cover 2 and Cover 4, next) by their pre-snap shell."
        }
      ]
    },
    {
      "lesson_id": "cover_4",
      "concept": "COVER_4",
      "title": "Cover 4: Quarters",
      "summary": "Four deep defenders, each owning a quarter of the field.",
      "difficulty": "intermediate",
      "order_index": 7,
      "prerequisites": [
        "cover_3"
      ],
      "steps": [
        {
          "step_type": "teach",
          "content": "Four deep defenders -- both cornerbacks and both safeties -- each responsible for a deep quarter of the field. Often called 'quarters' coverage."
        },
        {
          "step_type": "show",
          "content": "Pre-snap, this looks like Cover 2's two-high shell -- the corners' depth and technique after the snap are what confirm it's actually Cover 4.",
          "diagram_spec": {
            "field_view": "presnap_shell",
            "shell": "two_high",
            "defenders": [
              {
                "role": "CB",
                "align": "outside_left",
                "assignment": "deep_quarter_1",
                "depth": "deep"
              },
              {
                "role": "FS",
                "align": "left_middle",
                "assignment": "deep_quarter_2",
                "depth": "deep"
              },
              {
                "role": "SS",
                "align": "right_middle",
                "assignment": "deep_quarter_3",
                "depth": "deep"
              },
              {
                "role": "CB",
                "align": "outside_right",
                "assignment": "deep_quarter_4",
                "depth": "deep"
              }
            ]
          }
        },
        {
          "step_type": "explain",
          "content": "A real related technique: 'Man Everywhere he Goes' -- a defender plays true man coverage on a receiver regardless of his route, common inside quarters (Cover 4) schemes. Modern quarters defenses are often played as match coverage -- A modern hybrid concept: defenders start in zone drops but convert to man coverage based on the routes receivers actually run -- pattern-matching zone into man."
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_read_defense_cover4"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_name_concept_cover4"
          ]
        },
        {
          "step_type": "apply",
          "content": "Quarters is the foundation for this module's final, most advanced coverage: Cover 6."
        }
      ]
    },
    {
      "lesson_id": "cover_6",
      "concept": "COVER_6",
      "title": "Cover 6: Quarter-Quarter-Half",
      "summary": "Cover 4 on one side of the field, Cover 2 on the other.",
      "difficulty": "advanced",
      "order_index": 8,
      "prerequisites": [
        "cover_4"
      ],
      "steps": [
        {
          "step_type": "teach",
          "content": "A hybrid coverage that plays Cover 4 (quarters) principles on one side of the field and Cover 2 (half) principles on the other -- often called 'quarter-quarter-half.'"
        },
        {
          "step_type": "show",
          "content": "One side of the field plays quarters rules (two defenders splitting a half into quarters); the other side plays a single deep-half defender, Cover 2 style.",
          "diagram_spec": {
            "field_view": "presnap_shell",
            "shell": "two_high_split",
            "defenders": [
              {
                "role": "CB",
                "align": "quarters_side_outside",
                "assignment": "deep_quarter",
                "depth": "deep"
              },
              {
                "role": "S",
                "align": "quarters_side_middle",
                "assignment": "deep_quarter",
                "depth": "deep"
              },
              {
                "role": "S",
                "align": "half_side_middle",
                "assignment": "deep_half",
                "depth": "deep"
              },
              {
                "role": "CB",
                "align": "half_side_outside",
                "assignment": "deep_half",
                "depth": "underneath"
              }
            ]
          }
        },
        {
          "step_type": "explain",
          "content": "Commonly used to match a formation's strength -- quarters to the side with more receivers, a half-field zone to the boundary side."
        },
        {
          "step_type": "interactive_rep",
          "exercise_ids": [
            "ex_read_defense_cover6"
          ]
        },
        {
          "step_type": "check_understanding",
          "exercise_ids": [
            "ex_name_concept_cover6",
            "ex_mastery_all_coverages"
          ]
        },
        {
          "step_type": "apply",
          "content": "You've now covered every shell in this module. The mastery check mixes all of them together -- the real test of whether you can read a defense, not just recite definitions."
        }
      ]
    }
  ],
  "exercises": {
    "ex_man_zone_def_1": {
      "concept": "MAN_COVERAGE",
      "type": "name_the_concept",
      "difficulty": "beginner",
      "prompt": "What is the general term for coverage where each defender is assigned to follow a specific offensive player?",
      "structured": {},
      "options": [
        "Zone coverage",
        "Match coverage",
        "Man coverage",
        "Trap coverage"
      ],
      "correctIndex": 2,
      "explanation": "Man coverage means one defender, one assigned receiver, everywhere he goes."
    },
    "ex_man_zone_def_2": {
      "concept": "ZONE_COVERAGE",
      "type": "name_the_concept",
      "difficulty": "beginner",
      "prompt": "What is the general term for coverage where each defender is responsible for a specific area of the field rather than a specific player?",
      "structured": {},
      "options": [
        "Man coverage",
        "Combo coverage",
        "Zone coverage",
        "Match coverage"
      ],
      "correctIndex": 2,
      "explanation": "Zone coverage means area responsibility, not a specific receiver."
    },
    "ex_man_zone_check_1": {
      "concept": "MAN_COVERAGE",
      "type": "read_the_defense",
      "difficulty": "beginner",
      "prompt": "A cornerback lines up across from a receiver. His eyes are locked on that receiver the entire play, and he mirrors every move the receiver makes. Is this man or zone principle?",
      "structured": {
        "defender_eyes": "on_receiver"
      },
      "options": [
        "Zone principle",
        "Man principle"
      ],
      "correctIndex": 1,
      "explanation": "Following one specific player's movements, regardless of where he goes, is the definition of man coverage."
    },
    "ex_read_defense_cover0": {
      "concept": "COVER_0",
      "type": "read_the_defense",
      "difficulty": "beginner",
      "prompt": "Pre-snap, no safety is aligned deep at all, and the defense shows extra rushers near the line. Which coverage is this most likely to be?",
      "structured": {
        "field_view": "presnap_shell",
        "shell": "no_deep_safety",
        "defenders": [
          {
            "role": "CB",
            "align": "outside_left",
            "assignment": "man",
            "depth": "line"
          },
          {
            "role": "CB",
            "align": "outside_right",
            "assignment": "man",
            "depth": "line"
          },
          {
            "role": "S",
            "align": "underneath",
            "assignment": "man_or_blitz",
            "depth": "shallow"
          }
        ]
      },
      "options": [
        "Cover 0",
        "Cover 1",
        "Cover 2",
        "Tampa 2"
      ],
      "correctIndex": 0,
      "explanation": "Zero deep safeties is Cover 0's signature pre-snap tell."
    },
    "ex_name_concept_cover0": {
      "concept": "COVER_0",
      "type": "name_the_concept",
      "difficulty": "beginner",
      "prompt": "What coverage has zero deep safeties, with all defenders in man coverage and no help over the top?",
      "structured": {},
      "options": [
        "Cover 0",
        "Cover 2",
        "Cover 1",
        "Cover 3"
      ],
      "correctIndex": 0,
      "explanation": "This is the exact workbook definition of Cover 0."
    },
    "ex_read_defense_cover1": {
      "concept": "COVER_1",
      "type": "read_the_defense",
      "difficulty": "beginner",
      "prompt": "Pre-snap, you see exactly one safety aligned deep in the middle of the field. After the snap, every other defensive back turns and runs with a specific receiver. Which coverage is this?",
      "structured": {
        "field_view": "presnap_shell",
        "shell": "single_high",
        "defenders": [
          {
            "role": "FS",
            "align": "middle",
            "assignment": "deep_middle",
            "depth": "deep"
          },
          {
            "role": "CB",
            "align": "outside_left",
            "assignment": "man",
            "depth": "line"
          },
          {
            "role": "CB",
            "align": "outside_right",
            "assignment": "man",
            "depth": "line"
          }
        ]
      },
      "options": [
        "Cover 0",
        "Cover 1",
        "Cover 2",
        "Tampa 2"
      ],
      "correctIndex": 1,
      "explanation": "One deep safety plus man coverage underneath is Cover 1 (Man-Free)."
    },
    "ex_name_concept_cover1": {
      "concept": "COVER_1",
      "type": "name_the_concept",
      "difficulty": "beginner",
      "prompt": "What coverage features one deep safety with man coverage underneath and often a spy or extra rusher?",
      "structured": {},
      "options": [
        "Cover 2",
        "Cover 1",
        "Cover 0",
        "Cover 4"
      ],
      "correctIndex": 1,
      "explanation": "This is the exact workbook definition of Cover 1."
    },
    "ex_read_defense_cover2": {
      "concept": "COVER_2",
      "type": "read_the_defense",
      "difficulty": "beginner",
      "prompt": "Pre-snap, two safeties are aligned deep, split toward each sideline. After the snap, the two corners drop into the flat underneath instead of running deep. Which coverage is this?",
      "structured": {
        "field_view": "presnap_shell",
        "shell": "two_high",
        "defenders": [
          {
            "role": "FS",
            "align": "left_half",
            "assignment": "deep_half_left",
            "depth": "deep"
          },
          {
            "role": "SS",
            "align": "right_half",
            "assignment": "deep_half_right",
            "depth": "deep"
          },
          {
            "role": "CB",
            "align": "outside_left",
            "assignment": "flat_left",
            "depth": "underneath"
          },
          {
            "role": "CB",
            "align": "outside_right",
            "assignment": "flat_right",
            "depth": "underneath"
          }
        ]
      },
      "options": [
        "Cover 0",
        "Cover 1",
        "Cover 2",
        "Tampa 2",
        "Cover 3"
      ],
      "correctIndex": 2,
      "explanation": "Two deep safeties splitting the field into halves, zone underneath, is Cover 2."
    },
    "ex_name_concept_cover2": {
      "concept": "COVER_2",
      "type": "name_the_concept",
      "difficulty": "beginner",
      "prompt": "What coverage features two deep safeties splitting the field, each responsible for a deep half?",
      "structured": {},
      "options": [
        "Cover 1",
        "Cover 4",
        "Cover 2",
        "Cover 3"
      ],
      "correctIndex": 2,
      "explanation": "This is the exact workbook definition of Cover 2."
    },
    "ex_name_concept_tampa2": {
      "concept": "TAMPA_2",
      "type": "name_the_concept",
      "difficulty": "intermediate",
      "prompt": "What famous coverage variant, associated with the Tampa Bay Buccaneers under Tony Dungy and Monte Kiffin, has the middle linebacker drop deep into a Cover 2 shell?",
      "structured": {},
      "options": [
        "Robber coverage",
        "Tampa 2",
        "Cover 3",
        "Cover 4"
      ],
      "correctIndex": 1,
      "explanation": "This is the exact workbook definition of Tampa 2, including its real historical association."
    },
    "ex_read_defense_tampa2": {
      "concept": "TAMPA_2",
      "type": "read_the_defense",
      "difficulty": "intermediate",
      "prompt": "Same two-deep-safety shell as Cover 2, but after the snap the middle linebacker sprints straight down the deep middle of the field. Which coverage is this?",
      "structured": {
        "field_view": "presnap_shell",
        "shell": "two_high",
        "defenders": [
          {
            "role": "FS",
            "align": "left_half",
            "assignment": "deep_half_left",
            "depth": "deep"
          },
          {
            "role": "SS",
            "align": "right_half",
            "assignment": "deep_half_right",
            "depth": "deep"
          },
          {
            "role": "MLB",
            "align": "middle",
            "assignment": "deep_middle_seam",
            "depth": "deep_late"
          }
        ]
      },
      "options": [
        "Cover 2",
        "Cover 4",
        "Tampa 2",
        "Cover 6"
      ],
      "correctIndex": 2,
      "explanation": "The linebacker's deep middle drop, closing Cover 2's seam, is Tampa 2's defining feature."
    },
    "ex_read_defense_cover3": {
      "concept": "COVER_3",
      "type": "read_the_defense",
      "difficulty": "beginner",
      "prompt": "Pre-snap, exactly one safety is aligned deep in the middle of the field -- same as Cover 1. After the snap, both corners bail deep too, and the three of them split the field into thirds. Which coverage is this?",
      "structured": {
        "field_view": "presnap_shell",
        "shell": "single_high",
        "defenders": [
          {
            "role": "CB",
            "align": "outside_left",
            "assignment": "deep_third_left",
            "depth": "deep"
          },
          {
            "role": "FS",
            "align": "middle",
            "assignment": "deep_third_middle",
            "depth": "deep"
          },
          {
            "role": "CB",
            "align": "outside_right",
            "assignment": "deep_third_right",
            "depth": "deep"
          }
        ]
      },
      "options": [
        "Cover 1",
        "Cover 3",
        "Cover 0",
        "Cover 2"
      ],
      "correctIndex": 1,
      "explanation": "Three deep defenders splitting the field into thirds is Cover 3 -- the post-snap rotation is what distinguishes it from Cover 1's identical pre-snap shell."
    },
    "ex_name_concept_cover3": {
      "concept": "COVER_3",
      "type": "name_the_concept",
      "difficulty": "beginner",
      "prompt": "What coverage features three deep defenders (typically two corners and a safety) each covering a deep third of the field?",
      "structured": {},
      "options": [
        "Cover 6",
        "Cover 4",
        "Cover 2",
        "Cover 3"
      ],
      "correctIndex": 3,
      "explanation": "This is the exact workbook definition of Cover 3."
    },
    "ex_pre_post_cover1_vs_cover3": {
      "concept": "COVER_3",
      "type": "pre_snap_post_snap",
      "difficulty": "intermediate",
      "prompt": "You see a single-high safety shell before the snap -- it could be Cover 1 or Cover 3. After the snap, both cornerbacks turn and sprint deep instead of staying with a single receiver. Which coverage does this confirm?",
      "structured": {
        "presnap_shell": "single_high",
        "postsnap_tell": "both_corners_bail_deep"
      },
      "options": [
        "Cover 1",
        "Cover 3"
      ],
      "correctIndex": 1,
      "explanation": "Cover 1 and Cover 3 share an identical pre-snap picture -- only the post-snap corner technique (bailing deep vs. staying on a receiver) tells them apart."
    },
    "ex_read_defense_cover4": {
      "concept": "COVER_4",
      "type": "read_the_defense",
      "difficulty": "intermediate",
      "prompt": "Pre-snap, two safeties are aligned deep -- the same look as Cover 2. But after the snap, both cornerbacks also bail deep instead of dropping to the flat, and four defenders each take a deep quarter. Which coverage is this?",
      "structured": {
        "field_view": "presnap_shell",
        "shell": "two_high",
        "defenders": [
          {
            "role": "CB",
            "align": "outside_left",
            "assignment": "deep_quarter_1",
            "depth": "deep"
          },
          {
            "role": "FS",
            "align": "left_middle",
            "assignment": "deep_quarter_2",
            "depth": "deep"
          },
          {
            "role": "SS",
            "align": "right_middle",
            "assignment": "deep_quarter_3",
            "depth": "deep"
          },
          {
            "role": "CB",
            "align": "outside_right",
            "assignment": "deep_quarter_4",
            "depth": "deep"
          }
        ]
      },
      "options": [
        "Cover 2",
        "Cover 4 (Quarters)",
        "Cover 3",
        "Tampa 2"
      ],
      "correctIndex": 1,
      "explanation": "Four deep defenders each owning a quarter, confirmed by the corners bailing deep, is Cover 4."
    },
    "ex_name_concept_cover4": {
      "concept": "COVER_4",
      "type": "name_the_concept",
      "difficulty": "intermediate",
      "prompt": "What coverage features four deep defenders, often called 'quarters' coverage?",
      "structured": {},
      "options": [
        "Cover 3",
        "Cover 2",
        "Cover 6",
        "Cover 4"
      ],
      "correctIndex": 3,
      "explanation": "This is the exact workbook definition of Cover 4/Quarters."
    },
    "ex_read_defense_cover6": {
      "concept": "COVER_6",
      "type": "read_the_defense",
      "difficulty": "advanced",
      "prompt": "One side of the field has two defenders splitting quarters; the other side has a single deep-half defender. Which coverage combines these two shells?",
      "structured": {
        "field_view": "presnap_shell",
        "shell": "two_high_split",
        "defenders": [
          {
            "role": "CB",
            "align": "quarters_side_outside",
            "assignment": "deep_quarter",
            "depth": "deep"
          },
          {
            "role": "S",
            "align": "quarters_side_middle",
            "assignment": "deep_quarter",
            "depth": "deep"
          },
          {
            "role": "S",
            "align": "half_side_middle",
            "assignment": "deep_half",
            "depth": "deep"
          },
          {
            "role": "CB",
            "align": "half_side_outside",
            "assignment": "deep_half",
            "depth": "underneath"
          }
        ]
      },
      "options": [
        "Cover 4",
        "Cover 2",
        "Cover 6",
        "Tampa 2"
      ],
      "correctIndex": 2,
      "explanation": "Quarters on one side, half-field on the other -- that's Cover 6, quarter-quarter-half."
    },
    "ex_name_concept_cover6": {
      "concept": "COVER_6",
      "type": "name_the_concept",
      "difficulty": "advanced",
      "prompt": "What coverage combines Cover 4 principles on one side of the field with Cover 2 principles on the other, often called 'quarter-quarter-half'?",
      "structured": {},
      "options": [
        "Cover 4",
        "Cover 6",
        "Cover 3",
        "Cover 2"
      ],
      "correctIndex": 1,
      "explanation": "This is the exact workbook definition of Cover 6."
    },
    "ex_mastery_all_coverages": {
      "concept": "COVER_3",
      "type": "read_the_defense",
      "difficulty": "advanced",
      "prompt": "Mastery check: a single-high safety shell rotates, post-snap, into three deep defenders each owning a third of the field, with the safety helping the corner from OUTSIDE leverage on one side. Which specific rotation is this?",
      "structured": {
        "presnap_shell": "single_high",
        "deep_defenders": 3,
        "help_leverage": "outside"
      },
      "options": [
        "Cover 3 Sky",
        "Cover 3 Buzz",
        "Cover 3 Cloud",
        "Cover 1 Robber"
      ],
      "correctIndex": 2,
      "explanation": "Outside-leverage help from the rotating safety is specifically the Cloud call -- Sky is the inside-leverage complement."
    }
  }
};
