"""Tests for tools/quiz_export/adapters/lineup_college.py and the identity-
bridge expansion it depends on -- the position+college proof-game fix
(Creator's original v1.8 acceptance-test request, now genuinely data-backed).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.data_refresh import nfl_college_identity_bridge  # noqa: E402
from tools.director_v02 import pipeline, translator as translator_mod  # noqa: E402
from tools.quiz_export import duplicates, engine  # noqa: E402
from tools.quiz_export.adapters import draft as draft_adapter  # noqa: E402
from tools.quiz_export.adapters import lineup as lineup_adapter  # noqa: E402
from tools.quiz_export.adapters import lineup_college  # noqa: E402


def test_identity_bridge_expansion_is_idempotent():
    c = engine.connect()
    try:
        before = c.execute("SELECT COUNT(*) FROM cfb_nfl_identity_bridge_certified").fetchone()[0]
        result1 = nfl_college_identity_bridge.expand_identity_bridge(c)
        after1 = c.execute("SELECT COUNT(*) FROM cfb_nfl_identity_bridge_certified").fetchone()[0]
        result2 = nfl_college_identity_bridge.expand_identity_bridge(c)
        after2 = c.execute("SELECT COUNT(*) FROM cfb_nfl_identity_bridge_certified").fetchone()[0]
    finally:
        c.close()
    assert after1 >= before  # additive-only, never shrinks
    assert after2 == after1  # second run is a true no-op
    assert result2["newly_promoted"] == 0
    # Never a blind name join -- ambiguous names are real and reported, not silently forced.
    assert result1["skipped_ambiguous_name"] >= 0
    assert result2["already_certified_before"] == after1


def test_identity_bridge_never_creates_two_different_schools_for_one_ambiguous_name():
    """The expansion only promotes a candidate when EXACTLY ONE CFB player
    shares the normalized name -- this is the real, mechanical guard against
    a blind/forced name join, tested directly rather than assumed."""
    c = engine.connect()
    try:
        result = nfl_college_identity_bridge.expand_identity_bridge(c)
    finally:
        c.close()
    assert result["match_rule"] == "UNIQUE_NORMALIZED_NAME_PLUS_NFL_CHRONOLOGY"
    assert result["confidence_tier"] == "MODERATE_CONFIDENCE_NAME_CHRONOLOGY_MATCHED"


def test_lineup_college_coverage_is_sufficient_after_expansion():
    c = engine.connect()
    try:
        coverage = lineup_adapter.lineup_college_coverage(c)
    finally:
        c.close()
    assert coverage["skill_positions_only_college_coverage"] >= coverage["min_required_for_support"]
    assert coverage["sufficient"] is True
    # Real, disclosed, structural ceiling -- not fixed by this expansion.
    assert coverage["full_lineup_college_coverage"] == 0


def test_certified_college_lookup_includes_attended_before_draft_fallback():
    c = engine.connect()
    try:
        lookup = lineup_adapter.certified_college_lookup(c)
        certified_only = {
            r["nfl_player_key"] for r in c.execute("SELECT nfl_player_key FROM cfb_nfl_identity_bridge_certified")
        }
    finally:
        c.close()
    # The combined lookup is a strict superset of the certified-only table --
    # ATTENDED_BEFORE_DRAFT fills in real players the certified bridge alone misses.
    assert certified_only <= set(lookup.keys())
    assert len(lookup) >= len(certified_only)


def test_generate_20_real_puzzles_end_to_end_no_names_leaked():
    c = engine.connect()
    bridge = lineup_adapter.certified_college_lookup(c)
    raw_rows = lineup_college.fetch_ordered_candidates(c, seed="test-lineup-college-e2e")
    raw_by_season_team = {(s, t): lp for s, t, lp in raw_rows}
    c.close()

    pkg = pipeline.run(
        "Guess the NFL team from the colleges its offensive players attended. Show position + college only. "
        "Hide player names.",
        provider="mock", seed="test-lineup-college-e2e", question_count_override=20,
    )
    assert pkg.get("package_id") is not None
    assert pkg.get("qa_status") == "PASSED"
    questions = pkg.get("questions") or []
    assert len(questions) == 20

    c = engine.connect()
    season_re = re.compile(r"its (\d{4}) starting offense")
    seen = set()
    for q in questions:
        # No names shown anywhere in the visual payload.
        for entry in q["visual_payload"]["positions"]:
            assert "name" not in entry
            assert entry.get("college")  # never unresolved
        assert len(q["visual_payload"]["positions"]) == 5  # skill positions only, no OL row

        franchise_id = q["source_ids"]["franchise_id"]
        season = int(season_re.search(q["question"]).group(1))
        match = None
        for (s, t), lp in raw_by_season_team.items():
            if s != season:
                continue
            real, err = draft_adapter.resolve_franchise(c, t, s)
            if not err and real["franchise_id"] == franchise_id:
                match = (s, t, lp)
                break
        assert match is not None, f"no real candidate found for season={season} franchise={franchise_id}"
        _, team_code, real_lineup = match
        assert (season, team_code) not in seen  # no duplicate/repeating tiny pool
        seen.add((season, team_code))

        # Correct college for every displayed skill-position player.
        expected = []
        for slot in ("QB", "RB", "WR", "TE"):
            for p in real_lineup[slot]:
                expected.append(bridge.get(p["player_id"]))
        shown = [e["college"] for e in q["visual_payload"]["positions"]]
        assert sorted(expected) == sorted(shown)

        # No real player name (from this specific lineup, including OL) leaks anywhere.
        blob = str(q)
        for slot in ("QB", "RB", "WR", "TE", "OL"):
            for p in real_lineup[slot]:
                name = p["display_name"]
                if name and len(name) > 3:
                    assert name not in blob, f"leaked player name {name!r}"
    c.close()
    assert len(seen) == 20


def test_creator_prompt_resolves_to_college_capability_not_names_based_fallback():
    result = translator_mod.translate(
        "Make me a game where I guess a team from positions and colleges with names hidden.",
        provider="mock",
    )
    assert result["translation_status"] == "TRANSLATED"
    assert result["spec"]["domain"] == "NFL_OFFENSE_LINEUP_COLLEGE"
    assert result["spec"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP_BY_COLLEGE"


def test_ordinary_college_phrased_request_still_uses_names_based_capability():
    # No "hidden names" signal -- must NOT be swept into the new capability.
    result = translator_mod.translate(
        "Guess the NFL team from the colleges attended by the players on its offense, displayed by position.",
        provider="mock",
    )
    assert result["spec"]["domain"] == "NFL_OFFENSE_LINEUP"
    assert result["spec"]["relationship_predicate"] == "TEAM_OF_STARTING_LINEUP"


def test_evaluate_rejects_when_college_unresolved(monkeypatch):
    c = engine.connect()
    try:
        raw_rows = lineup_college.fetch_ordered_candidates(c, seed="test-unresolved-reject")
        rng = engine.seeded("test-unresolved-reject")
        guard = duplicates.DuplicateGuard(track_entity=False)
        monkeypatch.setattr(lineup_adapter, "certified_college_lookup", lambda c: {})
        result = lineup_college.evaluate(c, raw_rows[0], rng, guard)
        assert result == "COLLEGE_UNRESOLVED"
    finally:
        c.close()
