"""Football Learning Engine -- Defensive Coverages module (first production
milestone).

Source: the user's "Football 101 Encyclopedia / 700 Question Master"
workbook (`Football_101_Encyclopedia_700_Questions.xlsx` on disk -- the
exact filename in the request, `Reads_Football_Encyclopedia_Leak_Safe_
700_Question_Master.xlsx`, was not found on disk; this file's content
--700 questions across the exact same 10 categories the request
describes, including a "Pass Coverages" category -- is confirmed to be
the same material, already independently re-confirmed live in the app as
`data/xso.js`/`window.XSO_DATA`, category `'Pass Coverages'`, ids
660081-660120 and 660461-660490 in that 1-indexed export). This module
does NOT re-import the raw Q&A (already live) -- it converts the football
KNOWLEDGE those questions encode into structured, reusable concept
records and relationships, which the flat trivia bank cannot represent.

Every concept below cites the real spreadsheet row(s) it's grounded in
(`source_rows`). Structured attributes not literally spelled out in a
question's text (e.g. "Cover 3 is a zone-shell coverage" is explicit;
"corners typically play the flat in Cover 2" is common, well-established
coaching knowledge extending beyond the literal question wording) are
marked `verification_status='AUTHORED_FROM_ESTABLISHED_KNOWLEDGE'` rather
than `SOURCE_BACKED`, an honest distinction -- never presented as more
verified than it is. Nothing here claims a specific real team/season ran
a specific concept (Tampa 2's real Buccaneers/Dungy/Kiffin association is
the one exception, and it IS explicitly stated in the source question
itself, row 87).

Storage: reuses the Engine's existing, populated-but-unconsumed knowledge
graph (`knowledge_nodes`/`knowledge_edges` -- confirmed zero other code
reads these before this module, so this is genuinely additive, not a
competing system with `graph_nodes`/`graph_edges`, which IS live
production infrastructure for Coach Connections/Six Degrees/Grid and is
deliberately left untouched). Two new tables (`learn_lessons`,
`learn_exercises`) hold pedagogical content that doesn't fit a generic
node/edge shape -- ordered lesson steps and exercise items are
sequences, not facts-with-relationships.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402

SOURCE_ID = "FOOTBALL_101_ENCYCLOPEDIA_WORKBOOK"
SOURCE_BACKED = "SOURCE_BACKED"
AUTHORED = "AUTHORED_FROM_ESTABLISHED_KNOWLEDGE"
MODULE = "defensive_coverages"


def _ensure_schema(c) -> None:
    c.execute(
        "INSERT OR IGNORE INTO sources(source_id, source_name, source_url, license_note, "
        "attribution_required, approved_for_import, notes) VALUES (?,?,?,?,?,?,?)",
        (SOURCE_ID, "Football 101 Encyclopedia / 700 Question Master workbook", None,
         "User-provided reference material for the Reads Football Learning Engine.", 0, 1,
         "Live in-app as data/xso.js (window.XSO_DATA); this source_id specifically marks "
         "structured concept knowledge derived FROM that workbook's questions, not the raw "
         "trivia rows themselves."),
    )
    c.executescript("""
        CREATE TABLE IF NOT EXISTS learn_lessons (
            lesson_id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            concept_node_id TEXT NOT NULL REFERENCES knowledge_nodes(node_id),
            title TEXT NOT NULL,
            summary TEXT,
            difficulty TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            prerequisites_json TEXT NOT NULL DEFAULT '[]',
            steps_json TEXT NOT NULL,
            source_id TEXT,
            verification_status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS learn_exercises (
            exercise_id TEXT PRIMARY KEY,
            exercise_type TEXT NOT NULL,
            module TEXT NOT NULL,
            concept_node_id TEXT NOT NULL REFERENCES knowledge_nodes(node_id),
            difficulty TEXT NOT NULL,
            prompt TEXT NOT NULL,
            structured_data_json TEXT NOT NULL DEFAULT '{}',
            options_json TEXT NOT NULL,
            correct_option_index INTEGER NOT NULL,
            explanation TEXT,
            source_id TEXT,
            verification_status TEXT NOT NULL
        );
    """)
    c.commit()


def _node_id(canonical_id: str) -> str:
    return f"KN|FB_CONCEPT|{canonical_id}"


# --- Concept records -------------------------------------------------------
# Every `source_rows` entry is a real row id in the workbook's "Football 101
# Trivia" sheet (category "Pass Coverages"), independently re-confirmed live
# as window.XSO_DATA entries with id = 660000 + row - 1 (e.g. row 81 ->
# XSO_DATA id 660080... the export script assigns its own sequential ids
# starting at 660001, so these are cited by workbook ROW NUMBER, the stable
# reference, not the derived XSO_DATA id).

CONCEPTS = [
    # --- Foundational principles ---
    {
        "canonical_id": "MAN_COVERAGE", "label": "Man Coverage", "concept_family": "coverage_principle",
        "difficulty": "beginner", "man_or_zone": "man",
        "summary": "Each defender is assigned to follow and cover one specific offensive player, "
                   "mirroring his movements wherever he goes on the field, rather than covering an area.",
        "source_rows": [99], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "ZONE_COVERAGE", "label": "Zone Coverage", "concept_family": "coverage_principle",
        "difficulty": "beginner", "man_or_zone": "zone",
        "summary": "Each defender is responsible for a specific area of the field and covers whichever "
                   "receiver enters that area, rather than following one specific player.",
        "source_rows": [98], "verification_status": SOURCE_BACKED,
    },
    # --- The seven core shells (first-milestone list) ---
    {
        "canonical_id": "COVER_0", "label": "Cover 0", "concept_family": "coverage_shell",
        "difficulty": "beginner", "man_or_zone": "man", "shell": "no_deep_safety", "deep_defenders": 0,
        "summary": "Zero deep safeties -- every eligible receiver is covered man-to-man with no safety "
                   "help over the top.",
        "strengths": ["Frees up an extra pass rusher, since no safety is held deep",
                      "Tight, disruptive coverage on every receiver at the snap"],
        "weaknesses": ["No help over the top -- one blown 1-on-1 matchup can be a touchdown"],
        "pre_snap_indicators": "No safety aligned deep; often paired with a heavy pressure/blitz look.",
        "common_beaters_text": "Any receiver who can win a deep 1-on-1 rep, or a quick-breaking route "
                                "that gets the ball out before pressure arrives.",
        "source_rows": [81], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_1", "label": "Cover 1 (Man-Free)", "concept_family": "coverage_shell",
        "difficulty": "beginner", "man_or_zone": "man", "shell": "single_high", "deep_defenders": 1,
        "summary": "One deep safety in the middle of the field (single-high) with man coverage "
                   "everywhere underneath, often with an extra rusher or a spy.",
        "aka": ["Man-Free"],
        "pre_snap_indicators": "A single safety aligned deep in the middle of the field.",
        "source_rows": [82, 100], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_2", "label": "Cover 2", "concept_family": "coverage_shell",
        "difficulty": "beginner", "man_or_zone": "zone", "shell": "two_high", "deep_defenders": 2,
        "summary": "Two deep safeties split the field evenly, each responsible for a deep half, with "
                   "zone coverage underneath.",
        "weaknesses": ["The deep middle of the field, the seam between the two safeties, is a "
                       "natural soft spot", "Corners playing the flat underneath have no deep help "
                       "on quick outside-breaking routes"],
        "pre_snap_indicators": "Two safeties aligned deep, split toward each sideline.",
        "source_rows": [83, 102, 474], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "TAMPA_2", "label": "Tampa 2", "concept_family": "coverage_variation",
        "difficulty": "intermediate", "man_or_zone": "zone", "shell": "two_high", "deep_defenders": 2,
        "variation_of": "COVER_2",
        "summary": "A Cover 2 variant, associated with the Tampa Bay Buccaneers under Tony Dungy and "
                   "Monte Kiffin, where the middle linebacker drops deep down the field into the seam "
                   "between the two deep safeties -- directly closing Cover 2's biggest weakness.",
        "strengths": ["Closes the deep-middle seam that's normally Cover 2's weak point"],
        "coaching_points": ["Requires an athletic middle linebacker who can run with vertical seam "
                             "routes all the way downfield"],
        "source_rows": [87], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_2_MAN", "label": "Cover 2 Man", "concept_family": "coverage_variation",
        "difficulty": "intermediate", "man_or_zone": "hybrid", "shell": "two_high", "deep_defenders": 2,
        "variation_of": "COVER_2",
        "aka": ["Man-Under, Two-Deep"],
        "summary": "Man coverage underneath combined with two deep safeties providing help over the "
                   "top -- also called 'Man-Under, Two-Deep.'",
        "source_rows": [88, 489], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_3", "label": "Cover 3", "concept_family": "coverage_shell",
        "difficulty": "beginner", "man_or_zone": "zone", "shell": "single_high", "deep_defenders": 3,
        "summary": "Three deep defenders -- typically both cornerbacks and the free safety -- each "
                   "cover a deep third of the field, with zone coverage underneath.",
        "weaknesses": ["The deep out route, into the void between a corner's deep-third zone and the "
                       "underneath flat defender, is a well-known Cover 3 vulnerability"],
        "pre_snap_indicators": "A single safety aligned deep in the middle of the field (same shell "
                                "look as Cover 1 -- the difference is confirmed after the snap).",
        "source_rows": [84, 473, 485], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_4", "label": "Cover 4 (Quarters)", "concept_family": "coverage_shell",
        "difficulty": "intermediate", "man_or_zone": "zone", "shell": "two_high", "deep_defenders": 4,
        "aka": ["Quarters"],
        "summary": "Four deep defenders -- both cornerbacks and both safeties -- each responsible for "
                   "a deep quarter of the field. Often called 'quarters' coverage.",
        "pre_snap_indicators": "Two safeties aligned deep, similar to a Cover 2 shell -- confirmed as "
                                "Cover 4 by the corners' depth and technique after the snap.",
        "source_rows": [85, 475], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_6", "label": "Cover 6 (Quarter-Quarter-Half)", "concept_family": "coverage_shell",
        "difficulty": "advanced", "man_or_zone": "zone", "shell": "two_high", "deep_defenders": "4 (split 2-and-2)",
        "aka": ["Quarter-Quarter-Half"],
        "relies_on": ["COVER_4", "COVER_2"],
        "summary": "A hybrid coverage that plays Cover 4 (quarters) principles on one side of the "
                   "field and Cover 2 (half) principles on the other -- often called "
                   "'quarter-quarter-half.'",
        "coaching_points": ["Commonly used to match a formation's strength -- quarters to the side "
                             "with more receivers, a half-field zone to the boundary side"],
        "source_rows": [86], "verification_status": SOURCE_BACKED,
    },
    # --- Rotations/variations, folded into their parent's lesson ---
    {
        "canonical_id": "COVER_1_ROBBER", "label": "Cover 1 Robber", "concept_family": "coverage_rotation",
        "difficulty": "advanced", "variation_of": "COVER_1",
        "summary": "A Cover 1 variant where the deep safety, instead of staying deep, drops down to "
                   "'rob' or jump underneath routes in the middle of the field.",
        "source_rows": [462, 89], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_2_INVERT", "label": "Cover 2 Invert", "concept_family": "coverage_rotation",
        "difficulty": "advanced", "variation_of": "COVER_2",
        "summary": "A Cover 2 rotation where the corner and safety swap their traditional roles -- the "
                   "corner rotates to a deep half while the safety rolls down underneath.",
        "source_rows": [120, 461], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_3_CLOUD", "label": "Cover 3 Cloud", "concept_family": "coverage_rotation",
        "difficulty": "advanced", "variation_of": "COVER_3",
        "summary": "A Cover 3 rotation where the safety rotates down to help the corner from outside "
                   "leverage (the 'Cloud' call).",
        "source_rows": [112, 463], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_3_SKY", "label": "Cover 3 Sky", "concept_family": "coverage_rotation",
        "difficulty": "advanced", "variation_of": "COVER_3",
        "summary": "A Cover 3 rotation where the safety rotates down to help the corner from inside "
                   "leverage (the 'Sky' call) -- the complementary rotation to Cloud.",
        "source_rows": [113, 464], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVER_3_BUZZ", "label": "Cover 3 Buzz", "concept_family": "coverage_rotation",
        "difficulty": "advanced", "variation_of": "COVER_3",
        "summary": "A Cover 3 rotation where the safety 'buzzes' down into a shallow underneath zone "
                   "instead of staying deep.",
        "source_rows": [465], "verification_status": SOURCE_BACKED,
    },
    # --- Supporting glossary concepts (referenced within lessons, no ---
    # --- standalone curriculum stop of their own this pass) -----------
    {
        "canonical_id": "SINGLE_HIGH_SHELL", "label": "Single-High Shell", "concept_family": "coverage_shell_read",
        "difficulty": "beginner",
        "summary": "A single safety aligned deep in the middle of the field before the snap -- a "
                   "pre-snap indicator shared by Cover 1 and Cover 3 (the defense confirms which "
                   "after the snap).",
        "source_rows": [101], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "TWO_HIGH_SHELL", "label": "Two-High Shell", "concept_family": "coverage_shell_read",
        "difficulty": "beginner",
        "summary": "Two safeties aligned deep, split toward each sideline, before the snap -- a "
                   "pre-snap indicator shared by Cover 2, Cover 4, and Cover 6.",
        "source_rows": [102], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "PRESS_TECHNIQUE", "label": "Press Technique", "concept_family": "coverage_technique",
        "difficulty": "beginner",
        "summary": "A cornerback lines up tight to the line of scrimmage and directly challenges the "
                   "receiver at the snap.",
        "source_rows": [94], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "OFF_TECHNIQUE", "label": "Off Technique", "concept_family": "coverage_technique",
        "difficulty": "beginner",
        "summary": "A cornerback lines up several yards off the receiver, reading the play develop "
                   "before reacting.",
        "source_rows": [95], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "TRAIL_TECHNIQUE", "label": "Trail Technique", "concept_family": "coverage_technique",
        "difficulty": "intermediate",
        "summary": "A defender covers a receiver from behind, trailing the route, rather than facing him.",
        "source_rows": [96], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "BAIL_TECHNIQUE", "label": "Bail Technique", "concept_family": "coverage_technique",
        "difficulty": "intermediate",
        "summary": "A cornerback shows press coverage before the snap, then backpedals into a deep "
                   "zone -- a coverage disguise.",
        "source_rows": [97], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "CATCH_TECHNIQUE", "label": "Catch Technique", "concept_family": "coverage_technique",
        "difficulty": "intermediate",
        "summary": "A cornerback stays square to mirror the receiver rather than turning to run with him.",
        "source_rows": [481], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "LEVERAGE", "label": "Leverage", "concept_family": "coverage_fundamental",
        "difficulty": "beginner",
        "summary": "A defender's positioning relative to a receiver -- playing to take away either the "
                   "inside or outside release.",
        "source_rows": [469], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "CUSHION", "label": "Cushion", "concept_family": "coverage_fundamental",
        "difficulty": "beginner",
        "summary": "The distance a defensive back gives a receiver before the snap in off coverage.",
        "source_rows": [470], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "MEG_TECHNIQUE", "label": "MEG (Man Everywhere he Goes)", "concept_family": "coverage_technique",
        "difficulty": "advanced",
        "summary": "'Man Everywhere he Goes' -- a defender plays true man coverage on a receiver "
                   "regardless of his route, common inside quarters (Cover 4) schemes.",
        "source_rows": [466], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "MATCH_COVERAGE", "label": "Match Coverage", "concept_family": "coverage_principle",
        "difficulty": "advanced",
        "summary": "A modern hybrid concept: defenders start in zone drops but convert to man "
                   "coverage based on the routes receivers actually run -- pattern-matching zone into man.",
        "source_rows": [93, 108], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "ROBBER_COVERAGE", "label": "Robber Coverage", "concept_family": "coverage_technique",
        "difficulty": "advanced",
        "summary": "A defender reads the quarterback's eyes and 'robs' or jumps a route in the "
                   "middle of the field, often a safety crashing down from depth.",
        "source_rows": [89], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "BRACKET_COVERAGE", "label": "Bracket Coverage", "concept_family": "coverage_technique",
        "difficulty": "advanced",
        "summary": "Two defenders are assigned to a single dangerous receiver, one underneath and one "
                   "over the top.",
        "source_rows": [91], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "PALMS_COVERAGE", "label": "Palms Coverage", "concept_family": "coverage_technique",
        "difficulty": "advanced",
        "aka": ["Read coverage", "Smoke coverage"],
        "summary": "Common versus stacked or bunch receiver sets -- two defenders are assigned to "
                   "take away both a flat route and a vertical route from a single receiver combination.",
        "source_rows": [90], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "BANJO_COVERAGE", "label": "Banjo Coverage", "concept_family": "coverage_technique",
        "difficulty": "advanced",
        "summary": "A coverage call where two defenders switch assignments mid-play based on "
                   "receiver release, common versus stacked receivers.",
        "source_rows": [92, 479], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "PREVENT_DEFENSE", "label": "Prevent Defense", "concept_family": "coverage_situational",
        "difficulty": "beginner",
        "summary": "A deep, conservative defensive strategy used to protect a lead late in a game -- "
                   "prioritizing not giving up a big play over stopping short completions.",
        "source_rows": [115, 114], "verification_status": SOURCE_BACKED,
    },
    {
        "canonical_id": "COVERAGE_DISGUISE", "label": "Coverage Disguise / Rotation", "concept_family": "coverage_principle",
        "difficulty": "advanced",
        "summary": "A defense shows one coverage shell before the snap, then rotates to a different "
                   "look after the ball is snapped, to confuse the quarterback's pre-snap read.",
        "source_rows": [103, 118, 483], "verification_status": SOURCE_BACKED,
    },
]

CONCEPT_BY_ID = {c["canonical_id"]: c for c in CONCEPTS}

# --- Relationships -----------------------------------------------------
# Real, grounded edges only -- every source/target is a concept fully
# defined above (no dangling references to concepts outside this module).
EDGES: list[tuple[str, str, str]] = []
for c in CONCEPTS:
    if c["concept_family"] in ("coverage_variation", "coverage_rotation") and "variation_of" in c:
        EDGES.append((c["canonical_id"], "VARIATION_OF", c["variation_of"]))
    for rel in c.get("relies_on", []):
        EDGES.append((c["canonical_id"], "RELIES_ON", rel))
for shell_id in ("COVER_0", "COVER_1", "COVER_3"):
    EDGES.append((shell_id, "USES_SHELL", "SINGLE_HIGH_SHELL"))
for shell_id in ("COVER_2", "COVER_4", "COVER_6", "TAMPA_2", "COVER_2_MAN"):
    EDGES.append((shell_id, "USES_SHELL", "TWO_HIGH_SHELL"))
EDGES += [
    ("COVER_1", "SHARES_PRESNAP_SHELL_WITH", "COVER_3"),
    ("COVER_2", "SHARES_PRESNAP_SHELL_WITH", "COVER_4"),
    ("COVER_0", "IS_A", "MAN_COVERAGE"), ("COVER_1", "IS_A", "MAN_COVERAGE"),
    ("COVER_2", "IS_A", "ZONE_COVERAGE"), ("COVER_3", "IS_A", "ZONE_COVERAGE"),
    ("COVER_4", "IS_A", "ZONE_COVERAGE"), ("COVER_6", "IS_A", "ZONE_COVERAGE"),
    ("MATCH_COVERAGE", "RELATED_TO", "MEG_TECHNIQUE"),
    ("COVER_1_ROBBER", "USES_TECHNIQUE", "ROBBER_COVERAGE"),
    ("PRESS_TECHNIQUE", "CONTRASTS_WITH", "OFF_TECHNIQUE"),
    ("TRAIL_TECHNIQUE", "CONTRASTS_WITH", "CATCH_TECHNIQUE"),
    ("BAIL_TECHNIQUE", "IS_A", "COVERAGE_DISGUISE"),
]

# --- Diagram specifications ------------------------------------------------
# A reusable, structured description of a coverage shell -- field position,
# defender role/alignment, and zone assignment -- rendered by the frontend
# as a simple schematic (labeled dots on a simplified field), not a fully
# illustrated play diagram. Deliberately limited to what each concept's own
# `deep_defenders`/`shell` establishes -- never invents an underneath
# defender count or specific gap/technique the source material doesn't
# state. `role` values are standard position abbreviations (CB/FS/SS/LB);
# `zone` values are the same deep-third/deep-half/deep-quarter/hook/flat
# vocabulary the source questions themselves use (rows 104-106, 473-475).

def _shell_diagram(shell: str, deep_roles: list[dict]) -> dict:
    return {"field_view": "presnap_shell", "shell": shell, "defenders": deep_roles}


DIAGRAMS = {
    "COVER_0": _shell_diagram("no_deep_safety", [
        {"role": "CB", "align": "outside_left", "assignment": "man", "depth": "line"},
        {"role": "CB", "align": "outside_right", "assignment": "man", "depth": "line"},
        {"role": "S", "align": "underneath", "assignment": "man_or_blitz", "depth": "shallow"},
    ]),
    "COVER_1": _shell_diagram("single_high", [
        {"role": "FS", "align": "middle", "assignment": "deep_middle", "depth": "deep"},
        {"role": "CB", "align": "outside_left", "assignment": "man", "depth": "line"},
        {"role": "CB", "align": "outside_right", "assignment": "man", "depth": "line"},
    ]),
    "COVER_2": _shell_diagram("two_high", [
        {"role": "FS", "align": "left_half", "assignment": "deep_half_left", "depth": "deep"},
        {"role": "SS", "align": "right_half", "assignment": "deep_half_right", "depth": "deep"},
        {"role": "CB", "align": "outside_left", "assignment": "flat_left", "depth": "underneath"},
        {"role": "CB", "align": "outside_right", "assignment": "flat_right", "depth": "underneath"},
    ]),
    "TAMPA_2": _shell_diagram("two_high", [
        {"role": "FS", "align": "left_half", "assignment": "deep_half_left", "depth": "deep"},
        {"role": "SS", "align": "right_half", "assignment": "deep_half_right", "depth": "deep"},
        {"role": "MLB", "align": "middle", "assignment": "deep_middle_seam", "depth": "deep_late"},
    ]),
    "COVER_3": _shell_diagram("single_high", [
        {"role": "CB", "align": "outside_left", "assignment": "deep_third_left", "depth": "deep"},
        {"role": "FS", "align": "middle", "assignment": "deep_third_middle", "depth": "deep"},
        {"role": "CB", "align": "outside_right", "assignment": "deep_third_right", "depth": "deep"},
    ]),
    "COVER_4": _shell_diagram("two_high", [
        {"role": "CB", "align": "outside_left", "assignment": "deep_quarter_1", "depth": "deep"},
        {"role": "FS", "align": "left_middle", "assignment": "deep_quarter_2", "depth": "deep"},
        {"role": "SS", "align": "right_middle", "assignment": "deep_quarter_3", "depth": "deep"},
        {"role": "CB", "align": "outside_right", "assignment": "deep_quarter_4", "depth": "deep"},
    ]),
    "COVER_6": _shell_diagram("two_high_split", [
        {"role": "CB", "align": "quarters_side_outside", "assignment": "deep_quarter", "depth": "deep"},
        {"role": "S", "align": "quarters_side_middle", "assignment": "deep_quarter", "depth": "deep"},
        {"role": "S", "align": "half_side_middle", "assignment": "deep_half", "depth": "deep"},
        {"role": "CB", "align": "half_side_outside", "assignment": "deep_half", "depth": "underneath"},
    ]),
}


# --- Lessons -----------------------------------------------------------
# Teach -> Show -> Explain -> Interactive Rep -> Check Understanding ->
# Apply, per concept. exercise_ids referenced here are defined below in
# EXERCISES and must exist (validated at build time, not just assumed).

LESSONS = [
    {
        "lesson_id": "man_vs_zone_basics", "concept_node_id": "MAN_COVERAGE", "order_index": 1,
        "title": "Man vs. Zone: The Basics", "difficulty": "beginner", "prerequisites": [],
        "summary": "The single most important distinction in pass coverage -- everything else in this "
                   "module builds on it.",
        "steps": [
            {"step_type": "teach", "content":
                "Every pass coverage a defense plays is built from one of two basic ideas: "
                "man coverage or zone coverage. Man coverage assigns each defender to a specific "
                "receiver -- follow him everywhere he goes. Zone coverage assigns each defender to "
                "an area of the field -- cover whoever runs into your area."},
            {"step_type": "show", "content":
                "In man coverage, a defender's eyes are on his receiver the whole play. In zone "
                "coverage, a defender's eyes are on the quarterback and the receivers who enter his "
                "area -- he never has to run stride-for-stride with any one player."},
            {"step_type": "explain", "content":
                "This distinction is why the same defensive personnel can play completely different "
                "coverages from the same starting alignment. A cornerback lined up across from a "
                "receiver could be about to run with him everywhere (man) or drop into a specific "
                "patch of grass and pass him off to someone else the moment he leaves it (zone)."},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_man_zone_def_1", "ex_man_zone_def_2"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_man_zone_check_1"]},
            {"step_type": "apply", "content":
                "Every coverage in this module is built from man principles, zone principles, or a "
                "hybrid of both -- you'll be asked to identify which as you go."},
        ],
    },
    {
        "lesson_id": "cover_0", "concept_node_id": "COVER_0", "order_index": 2,
        "title": "Cover 0: All-Out Man", "difficulty": "beginner", "prerequisites": ["man_vs_zone_basics"],
        "summary": "Zero deep safeties, man everywhere, no help over the top.",
        "steps": [
            {"step_type": "teach", "content": CONCEPT_BY_ID["COVER_0"]["summary"]},
            {"step_type": "show", "content":
                "Pre-snap, there's no safety aligned deep at all -- every defensive back is up near "
                "the line of scrimmage, and the defense often shows extra rushers.",
             "diagram_spec": DIAGRAMS["COVER_0"]},
            {"step_type": "explain", "content":
                "Strengths: " + "; ".join(CONCEPT_BY_ID["COVER_0"]["strengths"]) + ". "
                "Weaknesses: " + "; ".join(CONCEPT_BY_ID["COVER_0"]["weaknesses"]) + ". "
                "Pre-snap tell: " + CONCEPT_BY_ID["COVER_0"]["pre_snap_indicators"]},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_read_defense_cover0"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_name_concept_cover0"]},
            {"step_type": "apply", "content":
                "Cover 0 is the highest-risk, highest-reward shell in this module -- it's the "
                "baseline every other coverage adds safety help on top of."},
        ],
    },
    {
        "lesson_id": "cover_1", "concept_node_id": "COVER_1", "order_index": 3,
        "title": "Cover 1: Man-Free", "difficulty": "beginner", "prerequisites": ["cover_0"],
        "summary": "One deep safety, man coverage everywhere else -- and its Robber variation.",
        "steps": [
            {"step_type": "teach", "content": CONCEPT_BY_ID["COVER_1"]["summary"]},
            {"step_type": "show", "content":
                "Pre-snap tell: " + CONCEPT_BY_ID["COVER_1"]["pre_snap_indicators"] + " This is the "
                "same single-high look Cover 3 shows -- the defense confirms which one after the snap.",
             "diagram_spec": DIAGRAMS["COVER_1"]},
            {"step_type": "explain", "content":
                "A real variation: " + CONCEPT_BY_ID["COVER_1_ROBBER"]["summary"] + " Instead of "
                "staying deep, the free safety drops down to jump an underneath route he anticipates."},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_read_defense_cover1"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_name_concept_cover1"]},
            {"step_type": "apply", "content":
                "Cover 1 and Cover 3 share the exact same pre-snap picture -- a single deep safety. "
                "The next lesson (Cover 3) is the first time you'll practice telling them apart."},
        ],
    },
    {
        "lesson_id": "cover_2", "concept_node_id": "COVER_2", "order_index": 4,
        "title": "Cover 2: Two Deep Halves", "difficulty": "beginner", "prerequisites": ["cover_1"],
        "summary": "Two safeties split the field, plus the Cover 2 Man and Invert variations.",
        "steps": [
            {"step_type": "teach", "content": CONCEPT_BY_ID["COVER_2"]["summary"]},
            {"step_type": "show", "content":
                "Pre-snap tell: " + CONCEPT_BY_ID["TWO_HIGH_SHELL"]["summary"],
             "diagram_spec": DIAGRAMS["COVER_2"]},
            {"step_type": "explain", "content":
                "Weaknesses: " + "; ".join(CONCEPT_BY_ID["COVER_2"]["weaknesses"]) + ". Two real "
                "variations: " + CONCEPT_BY_ID["COVER_2_MAN"]["summary"] + " And Cover 2 Invert -- " +
                CONCEPT_BY_ID["COVER_2_INVERT"]["summary"]},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_read_defense_cover2"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_name_concept_cover2"]},
            {"step_type": "apply", "content":
                "Cover 2's deep-middle soft spot is exactly what the next lesson, Tampa 2, was "
                "invented to fix."},
        ],
    },
    {
        "lesson_id": "tampa_2", "concept_node_id": "TAMPA_2", "order_index": 5,
        "title": "Tampa 2: Fixing Cover 2's Weakness", "difficulty": "intermediate",
        "prerequisites": ["cover_2"],
        "summary": "How one linebacker's drop closes Cover 2's deep-middle void.",
        "steps": [
            {"step_type": "teach", "content": CONCEPT_BY_ID["TAMPA_2"]["summary"]},
            {"step_type": "show", "content":
                "Same two-deep-safety picture as Cover 2 -- the difference is the middle linebacker, "
                "who sprints down the middle of the field after the snap instead of staying shallow.",
             "diagram_spec": DIAGRAMS["TAMPA_2"]},
            {"step_type": "explain", "content":
                "Recall Cover 2's weakness: the deep middle seam between the two safeties. Tampa 2 "
                "sends the middle linebacker to cover exactly that seam. " +
                CONCEPT_BY_ID["TAMPA_2"]["coaching_points"][0] + "."},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_name_concept_tampa2"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_read_defense_tampa2"]},
            {"step_type": "apply", "content":
                "You now know both of the field's classic two-deep-safety shells and why a defense "
                "would pick one over the other."},
        ],
    },
    {
        "lesson_id": "cover_3", "concept_node_id": "COVER_3", "order_index": 6,
        "title": "Cover 3: Three Deep Thirds", "difficulty": "beginner", "prerequisites": ["tampa_2"],
        "summary": "The other single-high shell, plus its Cloud/Sky/Buzz rotations.",
        "steps": [
            {"step_type": "teach", "content": CONCEPT_BY_ID["COVER_3"]["summary"]},
            {"step_type": "show", "content":
                "Same single-high pre-snap shell as Cover 1 -- both corners and the free safety each "
                "own a deep third after the snap.",
             "diagram_spec": DIAGRAMS["COVER_3"]},
            {"step_type": "explain", "content":
                "Known weakness: " + CONCEPT_BY_ID["COVER_3"]["weaknesses"][0] + ". Three real "
                "rotations you'll see called: Cloud (" + CONCEPT_BY_ID["COVER_3_CLOUD"]["summary"] +
                "), Sky (" + CONCEPT_BY_ID["COVER_3_SKY"]["summary"] + "), and Buzz (" +
                CONCEPT_BY_ID["COVER_3_BUZZ"]["summary"] + ")"},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_read_defense_cover3", "ex_pre_post_cover1_vs_cover3"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_name_concept_cover3"]},
            {"step_type": "apply", "content":
                "You can now recognize both single-high coverages (Cover 1 and Cover 3) and both "
                "two-high coverages (Cover 2 and Cover 4, next) by their pre-snap shell."},
        ],
    },
    {
        "lesson_id": "cover_4", "concept_node_id": "COVER_4", "order_index": 7,
        "title": "Cover 4: Quarters", "difficulty": "intermediate", "prerequisites": ["cover_3"],
        "summary": "Four deep defenders, each owning a quarter of the field.",
        "steps": [
            {"step_type": "teach", "content": CONCEPT_BY_ID["COVER_4"]["summary"]},
            {"step_type": "show", "content":
                "Pre-snap, this looks like Cover 2's two-high shell -- the corners' depth and "
                "technique after the snap are what confirm it's actually Cover 4.",
             "diagram_spec": DIAGRAMS["COVER_4"]},
            {"step_type": "explain", "content":
                "A real related technique: " + CONCEPT_BY_ID["MEG_TECHNIQUE"]["summary"] + " Modern "
                "quarters defenses are often played as match coverage -- " +
                CONCEPT_BY_ID["MATCH_COVERAGE"]["summary"]},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_read_defense_cover4"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_name_concept_cover4"]},
            {"step_type": "apply", "content":
                "Quarters is the foundation for this module's final, most advanced coverage: Cover 6."},
        ],
    },
    {
        "lesson_id": "cover_6", "concept_node_id": "COVER_6", "order_index": 8,
        "title": "Cover 6: Quarter-Quarter-Half", "difficulty": "advanced", "prerequisites": ["cover_4"],
        "summary": "Cover 4 on one side of the field, Cover 2 on the other.",
        "steps": [
            {"step_type": "teach", "content": CONCEPT_BY_ID["COVER_6"]["summary"]},
            {"step_type": "show", "content":
                "One side of the field plays quarters rules (two defenders splitting a half into "
                "quarters); the other side plays a single deep-half defender, Cover 2 style.",
             "diagram_spec": DIAGRAMS["COVER_6"]},
            {"step_type": "explain", "content": CONCEPT_BY_ID["COVER_6"]["coaching_points"][0] + "."},
            {"step_type": "interactive_rep", "exercise_ids": ["ex_read_defense_cover6"]},
            {"step_type": "check_understanding", "exercise_ids": ["ex_name_concept_cover6", "ex_mastery_all_coverages"]},
            {"step_type": "apply", "content":
                "You've now covered every shell in this module. The mastery check mixes all of them "
                "together -- the real test of whether you can read a defense, not just recite "
                "definitions."},
        ],
    },
]


# --- Exercises -----------------------------------------------------------
# Two real exercise types this pass: "name_the_concept" (definition -> pick
# the term -- several reuse the source workbook's own real question
# phrasing directly, cited) and "read_the_defense" (structured shell
# description -> pick the coverage). Distractors are always real coverage
# names from this same module, never invented terms.

_ALL_COVERAGE_LABELS = ["Cover 0", "Cover 1", "Cover 2", "Tampa 2", "Cover 3", "Cover 4 (Quarters)", "Cover 6 (Quarter-Quarter-Half)"]


def _mc(exercise_id, exercise_type, concept_id, difficulty, prompt, structured, options, correct_label, explanation, source_rows):
    correct_index = options.index(correct_label)
    return {
        "exercise_id": exercise_id, "exercise_type": exercise_type, "concept_node_id": concept_id,
        "difficulty": difficulty, "prompt": prompt, "structured_data": structured,
        "options": options, "correct_option_index": correct_index, "explanation": explanation,
        "source_rows": source_rows,
    }


EXERCISES = [
    _mc("ex_man_zone_def_1", "name_the_concept", "MAN_COVERAGE", "beginner",
        "What is the general term for coverage where each defender is assigned to follow a specific offensive player?",
        {}, ["Zone coverage", "Match coverage", "Man coverage", "Trap coverage"], "Man coverage",
        "Man coverage means one defender, one assigned receiver, everywhere he goes.", [99]),
    _mc("ex_man_zone_def_2", "name_the_concept", "ZONE_COVERAGE", "beginner",
        "What is the general term for coverage where each defender is responsible for a specific area of the field rather than a specific player?",
        {}, ["Man coverage", "Combo coverage", "Zone coverage", "Match coverage"], "Zone coverage",
        "Zone coverage means area responsibility, not a specific receiver.", [98]),
    _mc("ex_man_zone_check_1", "read_the_defense", "MAN_COVERAGE", "beginner",
        "A cornerback lines up across from a receiver. His eyes are locked on that receiver the entire play, and he mirrors every move the receiver makes. Is this man or zone principle?",
        {"defender_eyes": "on_receiver"}, ["Zone principle", "Man principle"], "Man principle",
        "Following one specific player's movements, regardless of where he goes, is the definition of man coverage.", []),

    _mc("ex_read_defense_cover0", "read_the_defense", "COVER_0", "beginner",
        "Pre-snap, no safety is aligned deep at all, and the defense shows extra rushers near the line. Which coverage is this most likely to be?",
        DIAGRAMS["COVER_0"], _ALL_COVERAGE_LABELS[:4], "Cover 0",
        "Zero deep safeties is Cover 0's signature pre-snap tell.", [81]),
    _mc("ex_name_concept_cover0", "name_the_concept", "COVER_0", "beginner",
        "What coverage has zero deep safeties, with all defenders in man coverage and no help over the top?",
        {}, ["Cover 0", "Cover 2", "Cover 1", "Cover 3"], "Cover 0",
        "This is the exact workbook definition of Cover 0.", [81]),

    _mc("ex_read_defense_cover1", "read_the_defense", "COVER_1", "beginner",
        "Pre-snap, you see exactly one safety aligned deep in the middle of the field. After the snap, every other defensive back turns and runs with a specific receiver. Which coverage is this?",
        DIAGRAMS["COVER_1"], _ALL_COVERAGE_LABELS[:4], "Cover 1",
        "One deep safety plus man coverage underneath is Cover 1 (Man-Free).", [82]),
    _mc("ex_name_concept_cover1", "name_the_concept", "COVER_1", "beginner",
        "What coverage features one deep safety with man coverage underneath and often a spy or extra rusher?",
        {}, ["Cover 2", "Cover 1", "Cover 0", "Cover 4"], "Cover 1",
        "This is the exact workbook definition of Cover 1.", [82]),

    _mc("ex_read_defense_cover2", "read_the_defense", "COVER_2", "beginner",
        "Pre-snap, two safeties are aligned deep, split toward each sideline. After the snap, the two corners drop into the flat underneath instead of running deep. Which coverage is this?",
        DIAGRAMS["COVER_2"], _ALL_COVERAGE_LABELS[:5], "Cover 2",
        "Two deep safeties splitting the field into halves, zone underneath, is Cover 2.", [83]),
    _mc("ex_name_concept_cover2", "name_the_concept", "COVER_2", "beginner",
        "What coverage features two deep safeties splitting the field, each responsible for a deep half?",
        {}, ["Cover 1", "Cover 4", "Cover 2", "Cover 3"], "Cover 2",
        "This is the exact workbook definition of Cover 2.", [83]),

    _mc("ex_name_concept_tampa2", "name_the_concept", "TAMPA_2", "intermediate",
        "What famous coverage variant, associated with the Tampa Bay Buccaneers under Tony Dungy and Monte Kiffin, has the middle linebacker drop deep into a Cover 2 shell?",
        {}, ["Robber coverage", "Tampa 2", "Cover 3", "Cover 4"], "Tampa 2",
        "This is the exact workbook definition of Tampa 2, including its real historical association.", [87]),
    _mc("ex_read_defense_tampa2", "read_the_defense", "TAMPA_2", "intermediate",
        "Same two-deep-safety shell as Cover 2, but after the snap the middle linebacker sprints straight down the deep middle of the field. Which coverage is this?",
        DIAGRAMS["TAMPA_2"], ["Cover 2", "Cover 4", "Tampa 2", "Cover 6"], "Tampa 2",
        "The linebacker's deep middle drop, closing Cover 2's seam, is Tampa 2's defining feature.", [87]),

    _mc("ex_read_defense_cover3", "read_the_defense", "COVER_3", "beginner",
        "Pre-snap, exactly one safety is aligned deep in the middle of the field -- same as Cover 1. After the snap, both corners bail deep too, and the three of them split the field into thirds. Which coverage is this?",
        DIAGRAMS["COVER_3"], ["Cover 1", "Cover 3", "Cover 0", "Cover 2"], "Cover 3",
        "Three deep defenders splitting the field into thirds is Cover 3 -- the post-snap rotation is what distinguishes it from Cover 1's identical pre-snap shell.", [84]),
    _mc("ex_name_concept_cover3", "name_the_concept", "COVER_3", "beginner",
        "What coverage features three deep defenders (typically two corners and a safety) each covering a deep third of the field?",
        {}, ["Cover 6", "Cover 4", "Cover 2", "Cover 3"], "Cover 3",
        "This is the exact workbook definition of Cover 3.", [84]),
    _mc("ex_pre_post_cover1_vs_cover3", "pre_snap_post_snap", "COVER_3", "intermediate",
        "You see a single-high safety shell before the snap -- it could be Cover 1 or Cover 3. After the snap, both cornerbacks turn and sprint deep instead of staying with a single receiver. Which coverage does this confirm?",
        {"presnap_shell": "single_high", "postsnap_tell": "both_corners_bail_deep"},
        ["Cover 1", "Cover 3"], "Cover 3",
        "Cover 1 and Cover 3 share an identical pre-snap picture -- only the post-snap corner technique (bailing deep vs. staying on a receiver) tells them apart.", []),

    _mc("ex_read_defense_cover4", "read_the_defense", "COVER_4", "intermediate",
        "Pre-snap, two safeties are aligned deep -- the same look as Cover 2. But after the snap, both cornerbacks also bail deep instead of dropping to the flat, and four defenders each take a deep quarter. Which coverage is this?",
        DIAGRAMS["COVER_4"], ["Cover 2", "Cover 4 (Quarters)", "Cover 3", "Tampa 2"], "Cover 4 (Quarters)",
        "Four deep defenders each owning a quarter, confirmed by the corners bailing deep, is Cover 4.", [85]),
    _mc("ex_name_concept_cover4", "name_the_concept", "COVER_4", "intermediate",
        "What coverage features four deep defenders, often called 'quarters' coverage?",
        {}, ["Cover 3", "Cover 2", "Cover 6", "Cover 4"], "Cover 4",
        "This is the exact workbook definition of Cover 4/Quarters.", [85]),

    _mc("ex_read_defense_cover6", "read_the_defense", "COVER_6", "advanced",
        "One side of the field has two defenders splitting quarters; the other side has a single deep-half defender. Which coverage combines these two shells?",
        DIAGRAMS["COVER_6"], ["Cover 4", "Cover 2", "Cover 6", "Tampa 2"], "Cover 6",
        "Quarters on one side, half-field on the other -- that's Cover 6, quarter-quarter-half.", [86]),
    _mc("ex_name_concept_cover6", "name_the_concept", "COVER_6", "advanced",
        "What coverage combines Cover 4 principles on one side of the field with Cover 2 principles on the other, often called 'quarter-quarter-half'?",
        {}, ["Cover 4", "Cover 6", "Cover 3", "Cover 2"], "Cover 6",
        "This is the exact workbook definition of Cover 6.", [86]),

    _mc("ex_mastery_all_coverages", "read_the_defense", "COVER_3", "advanced",
        "Mastery check: a single-high safety shell rotates, post-snap, into three deep defenders each owning a third of the field, with the safety helping the corner from OUTSIDE leverage on one side. Which specific rotation is this?",
        {"presnap_shell": "single_high", "deep_defenders": 3, "help_leverage": "outside"},
        ["Cover 3 Sky", "Cover 3 Buzz", "Cover 3 Cloud", "Cover 1 Robber"], "Cover 3 Cloud",
        "Outside-leverage help from the rotating safety is specifically the Cloud call -- Sky is the inside-leverage complement.", [112]),
]

EXERCISE_BY_ID = {e["exercise_id"]: e for e in EXERCISES}


def _validate() -> None:
    for edge in EDGES:
        for cid in (edge[0], edge[2]):
            if cid not in CONCEPT_BY_ID:
                raise SystemExit(f"Edge references unknown concept: {cid!r} in {edge!r}")
    for lesson in LESSONS:
        if lesson["concept_node_id"] not in CONCEPT_BY_ID:
            raise SystemExit(f"Lesson {lesson['lesson_id']!r} references unknown concept {lesson['concept_node_id']!r}")
        for prereq in lesson["prerequisites"]:
            if prereq not in {l["lesson_id"] for l in LESSONS}:
                raise SystemExit(f"Lesson {lesson['lesson_id']!r} references unknown prerequisite {prereq!r}")
        for step in lesson["steps"]:
            for eid in step.get("exercise_ids", []):
                if eid not in EXERCISE_BY_ID:
                    raise SystemExit(f"Lesson {lesson['lesson_id']!r} references unknown exercise {eid!r}")
    for ex in EXERCISES:
        if ex["concept_node_id"] not in CONCEPT_BY_ID:
            raise SystemExit(f"Exercise {ex['exercise_id']!r} references unknown concept {ex['concept_node_id']!r}")
        if ex["correct_option_index"] < 0:
            raise SystemExit(f"Exercise {ex['exercise_id']!r} correct option not found in its own options list")


def build(c) -> dict:
    _validate()
    _ensure_schema(c)

    node_ids = {}
    for concept in CONCEPTS:
        node_id = _node_id(concept["canonical_id"])
        node_ids[concept["canonical_id"]] = node_id
        payload = {k: v for k, v in concept.items() if k not in ("canonical_id", "label", "source_rows", "verification_status")}
        payload["source_rows"] = concept["source_rows"]
        payload["source_sheet"] = "Football 101 Trivia (category: Pass Coverages)"
        c.execute(
            "INSERT INTO knowledge_nodes(node_id, node_type, canonical_id, label, competition_id, "
            "payload_json, verification_status) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(node_type, canonical_id) DO UPDATE SET label=excluded.label, "
            "payload_json=excluded.payload_json, verification_status=excluded.verification_status",
            (node_id, "FB_CONCEPT", concept["canonical_id"], concept["label"], None,
             json.dumps(payload), concept["verification_status"]),
        )

    edges_written = 0
    for src, predicate, tgt in EDGES:
        edge_id = f"KE|{src}|{predicate}|{tgt}"
        # INSERT OR IGNORE (not ON CONFLICT DO NOTHING) -- edge_id is its own
        # PRIMARY KEY, a separate constraint from the (source,predicate,
        # target,...) UNIQUE index; ON CONFLICT naming only the latter left
        # the edge_id conflict uncaught on re-runs. OR IGNORE covers both.
        c.execute(
            "INSERT OR IGNORE INTO knowledge_edges(edge_id, source_node_id, predicate, target_node_id, "
            "season_start, season_end, source_id, verification_status, confidence, payload_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (edge_id, node_ids[src], predicate, node_ids[tgt], None, None, SOURCE_ID, SOURCE_BACKED, 1.0, "{}"),
        )
        edges_written += 1

    for lesson in LESSONS:
        c.execute(
            "INSERT INTO learn_lessons(lesson_id, module, concept_node_id, title, summary, difficulty, "
            "order_index, prerequisites_json, steps_json, source_id, verification_status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(lesson_id) DO UPDATE SET title=excluded.title, summary=excluded.summary, "
            "steps_json=excluded.steps_json, prerequisites_json=excluded.prerequisites_json",
            (lesson["lesson_id"], MODULE, node_ids[lesson["concept_node_id"]], lesson["title"],
             lesson["summary"], lesson["difficulty"], lesson["order_index"],
             json.dumps(lesson["prerequisites"]), json.dumps(lesson["steps"]), SOURCE_ID, SOURCE_BACKED),
        )

    for ex in EXERCISES:
        c.execute(
            "INSERT INTO learn_exercises(exercise_id, exercise_type, module, concept_node_id, difficulty, "
            "prompt, structured_data_json, options_json, correct_option_index, explanation, source_id, "
            "verification_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(exercise_id) DO UPDATE SET prompt=excluded.prompt, options_json=excluded.options_json, "
            "correct_option_index=excluded.correct_option_index, explanation=excluded.explanation",
            (ex["exercise_id"], ex["exercise_type"], MODULE, node_ids[ex["concept_node_id"]], ex["difficulty"],
             ex["prompt"], json.dumps(ex["structured_data"]), json.dumps(ex["options"]),
             ex["correct_option_index"], ex["explanation"], SOURCE_ID, SOURCE_BACKED),
        )

    c.commit()
    return {
        "concepts_written": len(CONCEPTS), "edges_written": edges_written,
        "lessons_written": len(LESSONS), "exercises_written": len(EXERCISES),
    }


if __name__ == "__main__":
    c = engine.connect()
    result = build(c)
    c.close()
    print(json.dumps(result, indent=2))

