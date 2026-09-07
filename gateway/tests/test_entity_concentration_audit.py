"""Absolute Final Closeout (Item 6): entity concentration audit.

Three real concerns were raised: Patriots overrepresentation in NFL Super
Bowl History, USC/Miami overrepresentation in One School Missing, and
Alabama/Saban/Ohio State clustering in CFB Rivalry Trivia. Measured
directly against the CURRENT real data (not assumed from memory):

- NFL Super Bowl History: the previously-measured ~20.8% Patriots share was
  an artifact of this same closeout's OWN team-resolution fix being
  incomplete at the time it was measured -- team_aliases only covers
  2002-2026, so the old 24-of-60-resolvable pool skewed toward the
  Patriots' own 2000s-2010s dynasty. Now that all 60 real Super Bowls
  resolve (see nfl_super_bowl.py's resolve_franchise_by_name()), the real,
  complete distribution is Patriots/Steelers at 6/60 = 10.0% each -- exactly
  proportional to their real 6 Super Bowl wins apiece, not filtering bias.
- One School Missing: already well-distributed (top real entity at 3.8%)
  as a side effect of the earlier 5-source _group_board_common pool
  expansion (595 real boards spanning 1966-2026) -- no further change
  needed.
- CFB Rivalry Trivia: Alabama/Ohio State appear in question TEXT more than
  average (Alabama in 3 of 43 real named rivalry packs -- Iron Bowl, Third
  Saturday in October, LSU-Alabama) because they are genuinely
  historically rivalry-rich programs, a real fact about the sport -- but
  as the CORRECT ANSWER they're a small minority (Alabama 1.4%, Saban 1.0%,
  Ohio State 0.9% of the full 1,272-question bank). Not suppressed further
  per the explicit instruction not to erase legitimate dominance.

No code changes were needed for this item -- these tests exist to lock in
the measurements so a future regression (e.g. a bad rivalry-pack import,
or team-resolution breaking again) is caught immediately.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_no_single_franchise_dominates_nfl_super_bowl_history():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import nfl_super_bowl

    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_super_bowl_result",
        "relationship_predicate": "WON_CHAMPIONSHIP", "object_type": "team",
        "answer_type": "team", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, nfl_super_bowl, request_text="pytest", director_request_id="pytest",
        seed="pytest-concentration-sb", target_count=200, id_start=1,
    )
    assert len(pkg["questions"]) == 60, "all 60 real Super Bowls must resolve -- see nfl_super_bowl.py"
    cnt = Counter(q["answer"] for q in pkg["questions"])
    top_franchise, top_count = cnt.most_common(1)[0]
    share = top_count / len(pkg["questions"])
    # Real, measured ceiling: 6/60 = 10.0% (Patriots and Steelers, both with
    # 6 real Super Bowl wins) -- a generous bound well above that, so this
    # only fires on a real regression, not normal seed-to-seed noise.
    assert share <= 0.15, f"{top_franchise} is {share:.1%} of real Super Bowl wins -- investigate before assuming bias"


def test_one_school_missing_college_answers_stay_well_distributed():
    from tools import game_director_v01 as v01
    from tools.quiz_export.adapters import cfb_one_school_missing

    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "nfl_sb_champion_offense_board_college",
        "relationship_predicate": "MISSING_COLLEGE", "object_type": "college",
        "answer_type": "college", "group_size": 4, "filters": {},
    }
    pkg = v01.generate_package_from_spec(
        spec, cfb_one_school_missing, request_text="pytest", director_request_id="pytest",
        seed="pytest-concentration-osm", target_count=500, id_start=1,
    )
    assert len(pkg["questions"]) >= 300
    cnt = Counter(q["answer"] for q in pkg["questions"])
    top_college, top_count = cnt.most_common(1)[0]
    share = top_count / len(pkg["questions"])
    # Real, measured ceiling: USC at 3.8% of 500 real candidates. A generous
    # bound above that.
    assert share <= 0.08, f"{top_college} is {share:.1%} of One School Missing answers -- real regression?"
    usc_and_miami = sum(1 for q in pkg["questions"] if q["answer"] in ("USC", "Miami (FL)", "Miami"))
    assert usc_and_miami / len(pkg["questions"]) <= 0.15


def test_cfb_rivalry_trivia_named_programs_stay_a_small_minority_of_correct_answers():
    """Alabama/Ohio State legitimately headline more real named rivalry
    packs than an average program (a real fact about the sport -- Alabama
    alone is one of the two schools in 3 of the 43 real packs: Iron Bowl,
    Third Saturday in October, LSU-Alabama), so their real question-TEXT
    mention rate is naturally higher than average. What must NOT happen is
    those programs dominating the CORRECT ANSWER distribution -- checked
    directly against the full 1,272-row curated bank, not a random sample."""
    from tools.quiz_export import engine

    c = engine.connect()
    rows = c.execute(
        "SELECT option_a, option_b, option_c, option_d, correct_letter FROM cfb_trivia_bank"
    ).fetchall()
    assert len(rows) == 1272, "the curated trivia bank's real row count changed -- re-verify this test's bounds"
    letter_col = {"A": "option_a", "B": "option_b", "C": "option_c", "D": "option_d"}
    correct_texts = [r[letter_col[r["correct_letter"]]] for r in rows]
    for needle in ("Alabama", "Nick Saban", "Ohio State"):
        matches = sum(1 for t in correct_texts if t and needle in t)
        share = matches / len(rows)
        # Real, measured ceiling: Alabama/Saban at 1.0-1.4%, Ohio State at
        # 0.9%. A generous bound (well under "dominates the deck") above
        # that -- this test exists to catch a real future regression (e.g.
        # a lopsided rivalry-pack import), not to suppress legitimate
        # historical prominence.
        assert share <= 0.05, f"{needle} is {share:.1%} of real correct answers -- investigate before assuming bias"
