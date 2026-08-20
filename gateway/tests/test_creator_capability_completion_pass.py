"""Creator Capability Completion pass -- regression battery for the 24 new
real, GENERATION_VERIFIED capabilities this pass adds (rankings, upsets,
NFL PBP scoring, NFL defensive events, drives, CFB same-week stat
comparisons, top single-game performers, ordered transfer paths, honors +
college compositions, cross-league honors). See tools/director_v02/
providers/mock.py's "Creator Capability Completion pass" section and each
adapter's own module docstring for the real data audit behind each one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


# ============================== previously-deferred manual failures, now real ==============================

def test_manual_failure_01_cfb_rankings_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me a game about college football rankings.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_RANKING"


def test_manual_failure_05_first_touchdown_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an NFL game and make me guess who scored the first touchdown.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_SCORING_PLAY"
    assert r["capability"]["relationship_predicate"] == "FIRST_TOUCHDOWN_SCORER"


def test_manual_failure_06_cfb_same_week_stat_comparison_now_playable():
    from gateway.services import creator
    r = creator.assess_feasibility(
        "Give me two college running backs from the same week and make me pick who rushed for more yards."
    )
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_STAT_COMPARISON"
    assert r["capability"]["relationship_predicate"] == "RUSHING_COMPARISON"


def test_manual_failure_07_top_performer_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me a team and game and make me guess their top offensive performer.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] in ("NFL_GAME_LEADER", "CFB_GAME_LEADER")


def test_manual_failure_08_all_american_to_all_pro_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an All-American who later became an NFL All-Pro and make me guess the player.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CROSS_LEAGUE_HONORS"
    assert r["capability"]["relationship_predicate"] == "ALL_AMERICAN_TO_ALL_PRO"


def test_manual_failure_09_transfer_ordered_path_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me a transfer player who later made the NFL and make me guess his college path.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_TRANSFER_PATH"


def test_manual_failure_10_all_pro_plus_college_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me guess which NFL All-Pro attended this college.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "NFL_ALL_PRO_COLLEGE"


def test_manual_failure_11_cfb_upsets_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me something about crazy college football upsets.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CFB_UPSET"
    assert r["capability"]["relationship_predicate"] == "RANKING_UPSET"  # default interpretation, disclosed


def test_manual_failure_12_fuzzy_college_to_nfl_stardom_now_playable():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me a game about dudes who were great in college and then became stars in the NFL.")
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS"
    assert r["capability"]["domain"] == "CROSS_LEAGUE_HONORS"


# ============================== category-specific routing ==============================

def test_betting_upset_explicit_signal_routes_correctly():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me some huge betting upsets in college football.")
    assert r["capability"]["domain"] == "CFB_UPSET"
    assert r["capability"]["relationship_predicate"] == "BETTING_UPSET"


def test_ranking_upset_explicit_signal_routes_correctly():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me a game about unranked teams beating ranked teams.")
    assert r["capability"]["relationship_predicate"] == "RANKING_UPSET"


@pytest.mark.parametrize("text,expected_predicate", [
    ("Who got the sack in this NFL game?", "RECORDED_SACK"),
    ("Who picked off the QB in this game?", "RECORDED_INTERCEPTION"),
    ("Which defender forced the fumble?", "FORCED_FUMBLE"),
    ("Who recovered the fumble?", "RECOVERED_FUMBLE"),
])
def test_defensive_event_paraphrases_route_to_correct_predicate(text, expected_predicate):
    from tools.director_v02 import feasibility
    r = feasibility.assess(text)
    assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS", text
    assert r["capability"]["domain"] == "NFL_DEFENSIVE_EVENT", text
    assert r["capability"]["relationship_predicate"] == expected_predicate, text


def test_ambiguous_fumble_request_asks_for_clarification():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me guess about a fumble in this NFL game.")
    assert r["support_status"] == "UNKNOWN"
    assert r["clarifying_question"]


def test_nfl_drive_routes_correctly():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an NFL drive and make me guess how it ended.")
    assert r["capability"]["domain"] == "NFL_DRIVE"


def test_cfb_drive_is_genuine_data_gap_not_wrong_route():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me a CFB drive and make me guess how it ended.")
    assert r["support_status"] == "UNDERSTOOD_BUT_UNSUPPORTED"
    assert r["capability"] is None


@pytest.mark.parametrize("text,expected_predicate", [
    ("Which two CFB quarterbacks had more passing yards the same week?", "PASSING_COMPARISON"),
    ("Which two CFB receivers had more receiving yards the same week?", "RECEIVING_COMPARISON"),
])
def test_stat_comparison_category_routing(text, expected_predicate):
    from tools.director_v02 import feasibility
    r = feasibility.assess(text)
    assert r["capability"]["domain"] == "CFB_STAT_COMPARISON", text
    assert r["capability"]["relationship_predicate"] == expected_predicate, text


def test_cfb_pbp_player_scoring_is_genuine_data_gap_not_wrong_route():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me a CFB game and make me guess who scored the first touchdown.")
    assert r["support_status"] == "UNDERSTOOD_BUT_UNSUPPORTED"
    assert r["capability"] is None


def test_all_american_to_hof_is_genuine_data_gap_not_wrong_route():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Give me an All-American who later became an NFL Hall of Famer and make me guess the player.")
    assert r["support_status"] == "UNDERSTOOD_BUT_UNSUPPORTED"
    assert r["capability"] is None


def test_pro_bowl_plus_college_composition_routes_correctly():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me guess which NFL Pro Bowler attended this college.")
    assert r["capability"]["domain"] == "NFL_PRO_BOWL_COLLEGE"


def test_hof_plus_college_composition_routes_correctly():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Make me guess which NFL Hall of Famer attended this college.")
    assert r["capability"]["domain"] == "NFL_HOF_COLLEGE"


def test_all_american_to_pro_bowl_routes_correctly():
    from tools.director_v02 import feasibility
    r = feasibility.assess("Which All-American later became an NFL Pro Bowler?")
    assert r["capability"]["domain"] == "CROSS_LEAGUE_HONORS"
    assert r["capability"]["relationship_predicate"] == "ALL_AMERICAN_TO_PRO_BOWL"


# ============================== end-to-end playability (real generation) ==============================

@pytest.mark.parametrize("request_text,expected_domain", [
    ("Make me a game about college football rankings.", "CFB_RANKING"),
    ("Make me something about crazy college football upsets.", "CFB_UPSET"),
    ("Give me some huge betting upsets in college football.", "CFB_UPSET"),
    ("Give me an NFL game and make me guess who scored the first touchdown.", "NFL_SCORING_PLAY"),
    ("Who got the sack in this NFL game?", "NFL_DEFENSIVE_EVENT"),
    ("Who picked off the QB in this game?", "NFL_DEFENSIVE_EVENT"),
    ("Which defender forced the fumble?", "NFL_DEFENSIVE_EVENT"),
    ("Who recovered the fumble?", "NFL_DEFENSIVE_EVENT"),
    ("Give me an NFL drive and make me guess how it ended.", "NFL_DRIVE"),
    ("Give me two college running backs from the same week and make me pick who rushed for more yards.", "CFB_STAT_COMPARISON"),
    ("Give me a team and game and make me guess their top offensive performer.", "NFL_GAME_LEADER"),
    ("Give me a transfer player who later made the NFL and make me guess his college path.", "CFB_TRANSFER_PATH"),
    ("Make me guess which NFL All-Pro attended this college.", "NFL_ALL_PRO_COLLEGE"),
    ("Make me guess which NFL Pro Bowler attended this college.", "NFL_PRO_BOWL_COLLEGE"),
    ("Make me guess which NFL Hall of Famer attended this college.", "NFL_HOF_COLLEGE"),
    ("Give me an All-American who later became an NFL All-Pro and make me guess the player.", "CROSS_LEAGUE_HONORS"),
    ("Which All-American later became an NFL Pro Bowler?", "CROSS_LEAGUE_HONORS"),
])
def test_new_capabilities_generate_real_playable_questions(request_text, expected_domain):
    from gateway.services import creator
    result = creator.generate_for_review(request_text=request_text, puzzle_count=3, difficulty="any", seed=f"e2e-{expected_domain}")
    assert result.get("qa_status") == "PASSED", result
    questions = result.get("questions", [])
    assert len(questions) >= 1
    for q in questions:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert 0 <= q["correctIndex"] <= 3


# ============================== answer leakage / multiple valid answer QA ==============================

def test_defensive_event_question_never_names_the_answer():
    from gateway.services import creator
    result = creator.generate_for_review(request_text="Who got the sack in this NFL game?", puzzle_count=5, difficulty="any", seed="leak-check-sack")
    for q in result["questions"]:
        answer = q["options"][q["correctIndex"]]
        assert answer.lower() not in q["question"].lower()


def test_stat_comparison_never_reveals_the_compared_value_in_question():
    """The question legitimately discloses the real season/week as context
    (e.g. "In Week 1 of the 2021 college football season...") -- that's not
    a leak, every other capability in this codebase discloses season the
    same way. The real thing to check is that the compared stat value
    itself (e.g. rushing yards) never appears pre-answer -- checked by
    stripping the known, adapter-authored season/week prefix first, then
    confirming no digit sequence remains in what's left."""
    import re

    from gateway.services import creator
    result = creator.generate_for_review(
        request_text="Give me two college running backs from the same week and make me pick who rushed for more yards.",
        puzzle_count=5, difficulty="any", seed="leak-check-statcompare",
    )
    prefix_re = re.compile(r"^In Week \d+ of the \d{4} college football season, ")
    for q in result["questions"]:
        remainder = prefix_re.sub("", q["question"])
        assert not re.search(r"\b\d{2,4}\b", remainder), q["question"]


def test_honor_college_composition_never_has_multiple_valid_answers_from_same_college():
    """Direct check on the real ambiguity fix: no generated question's
    correct answer shares a college with any of its own distractors."""
    from tools.quiz_export import engine
    from tools.quiz_export.adapters import nfl_all_pro_college
    import random

    c = engine.connect()
    rows = nfl_all_pro_college.fetch_ordered_candidates(c, "ambiguity-check")

    class Guard:
        def __init__(self):
            self.q, self.e = set(), set()

        def question_seen(self, q):
            if q in self.q:
                return True
            self.q.add(q)
            return False

        def entity_seen(self, e):
            if e in self.e:
                return True
            self.e.add(e)
            return False

    guard, rng = Guard(), random.Random(1)
    checked = 0
    for row in rows[:100]:
        r = nfl_all_pro_college.evaluate(c, row, rng, guard)
        if isinstance(r, dict):
            checked += 1
            correct_college = r["_audit"]["college"]
            for opt in r["options"]:
                if opt == r["options"][r["correctIndex"]]:
                    continue
                distractor_college_row = c.execute(
                    "SELECT d.college FROM canonical_players cp JOIN nfl_players_draft d ON d.player_key = cp.player_id "
                    "WHERE cp.display_name = ?", (opt,),
                ).fetchone()
                if distractor_college_row:
                    assert distractor_college_row["college"] != correct_college, (opt, correct_college)
    assert checked > 0


# ============================== NFL/CFB domain isolation ==============================

def test_nfl_defensive_event_capabilities_are_nfl_only():
    from tools.director_v02 import registry
    for predicate in ("RECORDED_SACK", "RECORDED_INTERCEPTION", "FORCED_FUMBLE", "RECOVERED_FUMBLE"):
        cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_DEFENSIVE_EVENT", predicate)]
        assert cap["competition_id"] == "NFL"


def test_cfb_stat_comparison_capabilities_are_cfb_only():
    from tools.director_v02 import registry
    for predicate in ("RUSHING_COMPARISON", "PASSING_COMPARISON", "RECEIVING_COMPARISON"):
        cap = registry.CAPABILITY_REGISTRY[("guess", "CFB_STAT_COMPARISON", predicate)]
        assert cap["competition_id"] == "CFB"


def test_game_leader_capabilities_stay_in_their_own_league():
    from tools.director_v02 import registry
    for predicate in ("RUSHING_LEADER", "PASSING_LEADER", "RECEIVING_LEADER"):
        nfl_cap = registry.CAPABILITY_REGISTRY[("guess", "NFL_GAME_LEADER", predicate)]
        cfb_cap = registry.CAPABILITY_REGISTRY[("guess", "CFB_GAME_LEADER", predicate)]
        assert nfl_cap["competition_id"] == "NFL"
        assert cfb_cap["competition_id"] == "CFB"


# ============================== all 24 capabilities registered + GENERATION_VERIFIED ==============================

def test_all_24_new_capabilities_are_generation_verified():
    from tools.director_v02 import feasibility as feasibility_mod

    triples = [
        ("guess", "CFB_RANKING", "RANKED_IN_POLL"),
        ("guess", "CFB_UPSET", "RANKING_UPSET"),
        ("guess", "CFB_UPSET", "BETTING_UPSET"),
        ("guess", "NFL_SCORING_PLAY", "FIRST_TOUCHDOWN_SCORER"),
        ("guess", "NFL_DEFENSIVE_EVENT", "RECORDED_SACK"),
        ("guess", "NFL_DEFENSIVE_EVENT", "RECORDED_INTERCEPTION"),
        ("guess", "NFL_DEFENSIVE_EVENT", "FORCED_FUMBLE"),
        ("guess", "NFL_DEFENSIVE_EVENT", "RECOVERED_FUMBLE"),
        ("guess", "NFL_DRIVE", "DRIVE_RESULT"),
        ("guess", "CFB_STAT_COMPARISON", "RUSHING_COMPARISON"),
        ("guess", "CFB_STAT_COMPARISON", "PASSING_COMPARISON"),
        ("guess", "CFB_STAT_COMPARISON", "RECEIVING_COMPARISON"),
        ("guess", "NFL_GAME_LEADER", "RUSHING_LEADER"),
        ("guess", "NFL_GAME_LEADER", "PASSING_LEADER"),
        ("guess", "NFL_GAME_LEADER", "RECEIVING_LEADER"),
        ("guess", "CFB_GAME_LEADER", "RUSHING_LEADER"),
        ("guess", "CFB_GAME_LEADER", "PASSING_LEADER"),
        ("guess", "CFB_GAME_LEADER", "RECEIVING_LEADER"),
        ("guess", "CFB_TRANSFER_PATH", "ORDERED_PATH_NFL_BRIDGED"),
        ("guess", "NFL_ALL_PRO_COLLEGE", "ATTENDED_COLLEGE_ALL_PRO"),
        ("guess", "NFL_PRO_BOWL_COLLEGE", "ATTENDED_COLLEGE_PRO_BOWL"),
        ("guess", "NFL_HOF_COLLEGE", "ATTENDED_COLLEGE_HOF"),
        ("guess", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_ALL_PRO"),
        ("guess", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_PRO_BOWL"),
    ]
    for mechanic, domain, predicate in triples:
        # 3, not 5 -- CROSS_LEAGUE_HONORS/ALL_AMERICAN_TO_ALL_PRO has a real,
        # honest, disclosed pool of only 4 candidates (see that capability's
        # own Tier-2 certification); 3 fits every real pool in this list
        # without asking any of them to loosen a genuine small-pool bound.
        spec = {"mechanic": mechanic, "domain": domain, "relationship_predicate": predicate,
                "question_count": 3, "difficulty": "any", "filters": {}, "exclusions": []}
        r = feasibility_mod.assess(spec=spec, provider="mock")
        assert r["support_status"] == "SUPPORTED_WITH_LIMITATIONS", (domain, predicate, r)
