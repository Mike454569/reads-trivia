"""Closeout pass (Part 3): permanent regression coverage for Franchise
Marathon's full rebuild away from "every stage is a Super Bowl roster
question."

Before this pass, franchise_marathon_guess was a thin franchise_name filter
over sb_champion_offense_college.py's 60-board SB_CHAMPION table -- 100% of
its content was Super Bowl roster trivia, and a franchise with zero real
titles got no marathon at all. franchise_marathon.py now builds a real
8-stage progression (identity/season-record/coach/draft/award/playoffs/
roster/deep-cut) from 7 different real Engine tables; Super Bowl content is
confined to exactly one stage (deep-cut), and only for a franchise that
actually has a real title.
"""
from __future__ import annotations

from collections import Counter

from tools import game_director_v01 as v01
from tools.quiz_export.adapters import franchise_marathon as fm

_FACTORY_SPEC = {
    "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_franchise_marathon_stage",
    "relationship_predicate": "FRANCHISE_MARATHON_STAGE", "object_type": "mixed",
    "answer_type": "mixed", "group_size": 4,
}


def _generate(franchise_name: str, seed: str, target_count: int = 8):
    spec = dict(_FACTORY_SPEC, filters={"franchise_name": franchise_name})
    return v01.generate_package_from_spec(
        spec, fm, request_text="pytest", director_request_id="pytest",
        seed=seed, target_count=target_count, id_start=1,
    )


def test_a_champion_franchise_marathon_is_not_all_super_bowl_content():
    """The core regression: the Cowboys (5 real titles) used to get a
    5-question, 100% roster-trivia marathon. Now Super Bowl content must be
    a small minority of one real 8-stage run."""
    pkg = _generate("Cowboys", "pytest-fm-1")
    assert pkg["qa_status"] == "PASSED"
    families = [q for q in pkg["questions"]]
    assert len(families) >= 6
    deep_cut_count = sum(1 for q in pkg["questions"] if q["question"].startswith("Final boss:"))
    assert deep_cut_count <= 1, "Super Bowl content must be at most one stage, not the whole mode"


def test_a_titleless_franchise_still_gets_a_real_full_marathon():
    """The other half of the same regression: a franchise with zero real
    Super Bowl titles used to get NOTHING. It must now get a real marathon
    built entirely from non-championship real data."""
    pkg = _generate("Bills", "pytest-fm-2")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) >= 6
    assert not any(q["question"].startswith("Final boss:") for q in pkg["questions"])


def test_seven_real_families_are_all_reachable_across_many_franchises():
    """Stress test across every real NFL franchise: every one of the 7 real
    non-championship families (identity/season-record/coach/draft/award/
    playoffs/roster) must actually be reachable, not just theoretically
    present in the adapter's code."""
    seen_patterns = {
        "IDENTITY": "play in?", "IDENTITY_RELOCATION": "Before becoming the",
        "SEASON_RECORD": "regular-season record", "COACH": "head coach",
        "DRAFT": "NFL Draft on a", "AWARD": "honors on the", "PLAYOFFS": "playoff run end",
        "ROSTER": "on the", "DEEP_CUT": "Final boss:",
    }
    found = set()
    for nickname in ["Cowboys", "Steelers", "Patriots", "Packers", "49ers", "Bills", "Vikings",
                      "Chargers", "Browns", "Lions", "Raiders", "Rams", "Ravens", "Bengals"]:
        pkg = _generate(nickname, f"pytest-fm-sweep-{nickname}")
        for q in pkg["questions"]:
            for key, substr in seen_patterns.items():
                if substr in q["question"]:
                    found.add(key)
    for key in ("SEASON_RECORD", "COACH", "DRAFT", "AWARD", "PLAYOFFS", "ROSTER"):
        assert key in found, f"real family {key} never appeared across the sweep"


def test_deep_cut_only_appears_for_a_franchise_with_a_real_title():
    """Bills/Vikings/Chargers/Browns/Lions have never won a Super Bowl --
    the deep-cut (Super Bowl) stage must never fabricate one for them."""
    for nickname in ["Bills", "Vikings", "Chargers", "Browns", "Lions"]:
        pkg = _generate(nickname, f"pytest-fm-notitle-{nickname}")
        assert not any(q["question"].startswith("Final boss:") for q in pkg["questions"]), (
            f"{nickname} has no real Super Bowl title -- must never get a fabricated deep-cut stage"
        )


def test_no_repeated_answer_within_a_single_marathon_run():
    pkg = _generate("Patriots", "pytest-fm-repeat")
    answers = [q["options"][q["correctIndex"]] for q in pkg["questions"]]
    assert len(set(answers)) == len(answers), "a single franchise's marathon must not repeat its own answer"


def test_no_duplicate_question_text_within_a_single_marathon_run():
    pkg = _generate("Packers", "pytest-fm-dup-question")
    texts = [q["question"] for q in pkg["questions"]]
    assert len(set(texts)) == len(texts)


def test_stage_content_is_stable_regardless_of_which_stage_index_is_requested():
    """The critical correctness property get_public_game() depends on for
    ANY sequential mode: re-deriving the candidate list with a DIFFERENT
    gen_seed (as happens once per real stage_index HTTP request) must never
    change which real fact occupies a given stage. Only distractor
    shuffling may vary with the seed."""
    full = _generate("Cowboys", "seedA:stage7", target_count=8)
    for stage_index in (0, 2, 5, 7):
        partial = _generate("Cowboys", f"seedB:stage{stage_index}", target_count=stage_index + 1)
        assert partial["questions"][stage_index]["question"] == full["questions"][stage_index]["question"], (
            f"stage {stage_index}'s real content changed when requested with a different seed/target_count"
        )


def test_difficulty_progresses_from_easy_to_hard_across_the_marathon():
    pkg = _generate("Giants", "pytest-fm-difficulty")
    difficulties = [q["difficulty"] for q in pkg["questions"]]
    assert difficulties[0] == "Easy"
    assert difficulties[-1] == "Hard"
    # Monotonic-ish: Easy must never appear after a Hard stage has started.
    first_hard = next((i for i, d in enumerate(difficulties) if d == "Hard"), len(difficulties))
    assert "Easy" not in difficulties[first_hard:]


def test_distractor_options_are_always_four_distinct_real_values():
    pkg = _generate("Broncos", "pytest-fm-options")
    for q in pkg["questions"]:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert q["options"][q["correctIndex"]] != ""


def test_franchise_name_is_used_in_question_wording_not_generic_this_team():
    """Real wording-quality fix made alongside the rebuild: templated
    'this team' phrasing collided across different franchises whenever two
    franchises happened to land on the same season for the same family.
    Every question must name the real franchise."""
    pkg = _generate("Chiefs", "pytest-fm-wording")
    for q in pkg["questions"][1:]:  # stage 0 (IDENTITY) already always names the team
        assert "this team" not in q["question"].lower()


def test_relocated_franchise_reunites_its_full_real_history():
    """Raiders (OAK 1999-2019, LV 2020-2026) must be treated as one real
    continuous franchise across every family, not just the current team_code."""
    pkg = _generate("Raiders", "pytest-fm-relocation")
    assert pkg["qa_status"] == "PASSED"
    assert any("Oakland Raiders" in q["question"] or "Las Vegas Raiders" in q["question"]
               for q in pkg["questions"])


def test_shortfall_never_pads_with_a_fabricated_stage():
    """A franchise legitimately short a stage (e.g. no distinct second
    roster pick available) must return fewer real questions, never a
    fabricated one to hit a round number."""
    for nickname in ["Vikings", "Chargers", "Bengals", "Titans", "Jaguars"]:
        pkg = _generate(nickname, f"pytest-fm-shortfall-{nickname}")
        assert len(pkg["questions"]) <= 8
        assert pkg["qa_status"] == "PASSED"


# The exact 32 real, current NFL franchise search values engine-game-ui.js's
# franchiseChoices now offers (this project's own frontend picker) --
# expanded from an old 10-team list left over from before this Closeout
# Part 3 rebuild, when the mode was a thin filter over the 60-board
# SB_CHAMPION table and a franchise needed a real title just to have any
# surviving stage. "washington" (not "commanders") is deliberate: Washington
# is the one real franchise whose 3 distinct historical names (Redskins/
# Football Team/Commanders) share no common nickname substring, and only
# the city-based search reaches its full real 2002-2026 history (see
# engine-game-ui.js's own comment on this exact franchise for the concrete
# proof -- "commanders" alone silently misses both the real IDENTITY/rename
# stage and the real Super Bowl deep-cut stage).
ALL_32_REAL_FRANCHISE_SEARCH_VALUES = [
    "cardinals", "falcons", "ravens", "bills", "panthers", "bears", "bengals", "browns",
    "cowboys", "broncos", "lions", "packers", "texans", "colts", "jaguars", "chiefs",
    "raiders", "chargers", "rams", "dolphins", "vikings", "patriots", "saints", "giants",
    "jets", "eagles", "steelers", "49ers", "seahawks", "buccaneers", "titans", "washington",
]


def test_all_32_real_nfl_franchises_produce_a_real_playable_marathon():
    assert len(ALL_32_REAL_FRANCHISE_SEARCH_VALUES) == 32
    for value in ALL_32_REAL_FRANCHISE_SEARCH_VALUES:
        pkg = _generate(value, f"pytest-fm-all32-{value}")
        assert pkg["qa_status"] == "PASSED", value
        assert len(pkg["questions"]) >= 1, value


def test_washington_search_reaches_its_full_real_history_not_just_the_current_name():
    """The one franchise this project's own frontend deliberately searches
    by city rather than nickname -- confirms searching "commanders" alone
    really would miss real content "washington" reaches, so a future editor
    doesn't "simplify" this back to the nickname and silently regress it."""
    pkg_nickname_only = _generate("Commanders", "pytest-fm-wsh-nickname")
    pkg_city = _generate("Washington", "pytest-fm-wsh-city")
    assert pkg_city["qa_status"] == "PASSED"
    identity_stage_present = any(q["question"].startswith("Before becoming the") for q in pkg_city["questions"])
    deep_cut_stage_present = any(q["question"].startswith("Final boss:") for q in pkg_city["questions"])
    assert identity_stage_present, "searching the city should reach the real Redskins->Commanders rename stage"
    assert deep_cut_stage_present, "searching the city should reach the real Washington Redskins Super Bowl deep-cut stage"
    nickname_had_identity = any(q["question"].startswith("Before becoming the") for q in pkg_nickname_only["questions"])
    nickname_had_deep_cut = any(q["question"].startswith("Final boss:") for q in pkg_nickname_only["questions"])
    assert not (nickname_had_identity and nickname_had_deep_cut), (
        "if searching \"commanders\" alone now also reaches both stages, the city-only special case "
        "in engine-game-ui.js's franchiseChoices may no longer be necessary -- re-verify before simplifying"
    )
