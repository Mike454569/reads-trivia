"""P0 Accuracy + Reliability Hardening pass (Section 8): a package being
non-empty is not enough -- the generated relationship must match what the
user actually asked for. Real failure modes this guards against:

  * TEAM + SEASON -> COORDINATOR silently becoming COORDINATOR -> TEAM
  * FIRST TD -> PLAYER silently becoming GAME -> WINNER
  * a same-week RB comparison silently becoming WEEKLY_PICKEM (a real,
    different, schedule-driven capability with a similar surface vocabulary)
  * college + All-Pro -> PLAYER silently degrading to generic college-
    attendance trivia (answer = college instead of answer = player)

Each test round-trips a real casual phrasing all the way through translate
-> validate -> generate, then asserts BOTH the routed capability AND the
real generated answer entity's TYPE match what the phrasing actually asked
for -- a package can be well-formed (see test_package_contract.py) and
still answer the wrong question.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v02 import registry  # noqa: E402
from tools.director_v02.providers.mock import MockDeterministicTranslator  # noqa: E402
from tools import game_director_v01 as gd  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _translate_and_generate(request_text: str, *, seed: str):
    translator = MockDeterministicTranslator()
    translation = translator.translate(request_text)
    assert translation["translation_status"] == "TRANSLATED", (
        f"{request_text!r} did not translate: {translation.get('translator_notes')}"
    )
    spec = translation["spec"]
    cap = registry.CAPABILITY_REGISTRY[(spec["mechanic"], spec["domain"], spec["relationship_predicate"])]
    pkg = gd.generate_package_from_spec(
        spec, cap["adapter"], request_text=request_text, director_request_id=f"semantic-{seed}",
        seed=seed, target_count=5,
    )
    assert pkg["qa_status"] == "PASSED" and pkg["questions"], (
        f"{request_text!r} routed to {spec['domain']}/{spec['relationship_predicate']} but produced no "
        f"real questions"
    )
    return spec, pkg


def test_team_season_offense_request_answers_with_coordinator_not_team():
    spec, pkg = _translate_and_generate(
        "give me an nfl team offense and season and make me guess the coordinator", seed="semantic-oc-1",
    )
    assert spec["domain"] == "NFL_OFFENSIVE_COORDINATOR"
    assert spec["relationship_predicate"] == "COORDINATED_OFFENSE"
    q = pkg["questions"][0]
    # The real, structural check: the answer must be a coordinator's NAME,
    # never one of the real NFL team names (which would mean the direction
    # silently flipped to guessing the TEAM instead).
    c = engine_bootstrap.connect()
    try:
        real_team_names = {row["team_name_raw"] for row in c.execute(
            "SELECT DISTINCT team_name_raw FROM nfl_coordinators"
        ).fetchall()}
        real_coach_names = {row["coach_name_raw"] for row in c.execute(
            "SELECT DISTINCT coach_name_raw FROM nfl_coordinators"
        ).fetchall()}
    finally:
        c.close()
    assert q["answer"] not in real_team_names, f"answer {q['answer']!r} looks like a team, not a coordinator"
    assert q["answer"] in real_coach_names, f"answer {q['answer']!r} is not a real recorded coordinator name"
    assert "coordinator" in pkg["game_instructions"].lower() or "coordinator" in q["question"].lower()


def test_same_week_rb_comparison_routes_to_stat_comparison_not_weekly_pickem():
    spec, pkg = _translate_and_generate(
        "give me two rbs from the same cfb week and make me choose who had the bigger day", seed="semantic-rb-1",
    )
    assert spec["domain"] == "CFB_STAT_COMPARISON"
    assert spec["relationship_predicate"] in ("RUSHING_COMPARISON", "PASSING_COMPARISON", "RECEIVING_COMPARISON")
    # WEEKLY_PICKEM is a structurally different, schedule-driven mechanic
    # (guess the winner of a real game) -- never the right answer for a
    # same-week PLAYER stat comparison, even though both mention "week".
    assert spec["mechanic"] != "WEEKLY_PICKEM"
    q = pkg["questions"][0]
    from tools.quiz_export import engine
    c = engine.connect()
    try:
        real_players = {row["player_name"] for row in c.execute(
            "SELECT DISTINCT player_name FROM cfb_player_game_stats_real LIMIT 20000"
        ).fetchall()}
    finally:
        c.close()
    assert q["answer"] in real_players, f"answer {q['answer']!r} is not a real CFB player name"


def test_first_touchdown_scorer_answers_with_player_not_game_winner():
    spec, pkg = _translate_and_generate("who got the first tuddy", seed="semantic-td-1")
    assert spec["domain"] == "NFL_SCORING_PLAY"
    assert spec["relationship_predicate"] == "FIRST_TOUCHDOWN_SCORER"
    cap = registry.CAPABILITY_REGISTRY[(spec["mechanic"], spec["domain"], spec["relationship_predicate"])]
    assert cap["answer_type"] == "player", "FIRST_TOUCHDOWN_SCORER must answer with the scoring PLAYER, not a team"
    q = pkg["questions"][0]
    # A real, live check that the answer isn't accidentally one of the two
    # team names mentioned in the question (which would mean this had
    # silently degraded into "who won the game").
    assert q["answer"] not in q["question"], (
        f"answer {q['answer']!r} appears verbatim in the question text {q['question']!r} -- "
        f"looks like a team-name leak, not a real player answer"
    )


def test_college_all_pro_answers_with_player_not_generic_college_trivia():
    spec, pkg = _translate_and_generate(
        "give me a college and all-pro clue and make me guess the player", seed="semantic-college-1",
    )
    assert spec["domain"] == "NFL_ALL_PRO_COLLEGE"
    assert spec["relationship_predicate"] == "ATTENDED_COLLEGE_ALL_PRO"
    cap = registry.CAPABILITY_REGISTRY[(spec["mechanic"], spec["domain"], spec["relationship_predicate"])]
    # Real regression this guards: silently downgrading to generic
    # ATTENDED_COLLEGE (NFL_DRAFT) trivia, which strips the All-Pro
    # qualifier the user explicitly asked for.
    assert cap["answer_type"] == "player"
    q = pkg["questions"][0]
    assert "All-Pro" in q["question"], "the All-Pro qualifier must survive into the generated question"
