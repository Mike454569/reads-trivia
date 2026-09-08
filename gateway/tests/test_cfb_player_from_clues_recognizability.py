"""CFB Player From Clues -- Player Experience pass (user request: "use
players that are more relevant and that casual and normal cfb fans would
know and then make a sicko difficulty where CFB sickos can test
themselves"). Real, confirmed root cause: this mode's only eligibility bar
was "3+ real recorded roster seasons" -- no requirement of ever being a
real, meaningful on-field contributor. Measured directly against the
shipped 3,300-puzzle pack before this fix: 2,843/3,300 (86%) landed in
"Hard" purely because the only prior difficulty signals (All-America, NFL
draft) are each real but rare.

Fixed with a real, non-fabricated third signal (a genuine single-season
statistical threshold from cfb_player_season_stats_real) and a strict
split into two non-overlapping pools: "notable" (Easy/Medium/Hard -- the
real "a normal fan could know this player" pool) and "sicko" (zero
recognizability signal at all, a real explicit deep-cut tier).
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


def test_difficulty_bands_are_a_real_partition_of_the_full_universe():
    from tools.quiz_export import engine
    from tools.director_v04 import cfb_player_from_clues as mod

    c = engine.connect()
    try:
        facts, _indexes, universe_ids = mod.build_universe(c)
    finally:
        c.close()
    assert universe_ids, "expected a real, non-empty universe"
    for pid in universe_ids:
        assert facts[pid]["difficulty_band"] in mod.DIFFICULTY_BANDS, (pid, facts[pid].get("difficulty_band"))


def test_notable_pool_is_a_real_minority_not_the_whole_universe():
    """The real point of this fix: Sicko must be a real, substantial
    majority of the raw universe (most 3-year roster players are
    genuinely obscure), while Notable (Easy+Medium+Hard) is still a real,
    substantial pool in absolute terms -- not vanishingly small the way
    the old Easy+Medium bands (457/3,300 sampled) were."""
    from tools.quiz_export import engine
    from tools.director_v04 import cfb_player_from_clues as mod

    c = engine.connect()
    try:
        facts, _indexes, universe_ids = mod.build_universe(c)
    finally:
        c.close()
    from collections import Counter
    bands = Counter(f["difficulty_band"] for f in facts.values())
    notable = bands["Easy"] + bands["Medium"] + bands["Hard"]
    assert notable >= 5000, f"expected a real, substantial Notable pool, got {notable} ({bands})"
    assert bands["Sicko"] > notable, f"expected Sicko to remain the real majority ({bands})"


def test_notable_and_sicko_generation_pools_never_overlap():
    from tools.director_v04 import cfb_player_from_clues as mod

    notable_pack = mod.generate_pack("pytest-notable-overlap", target_count=150, pool="notable")
    sicko_pack = mod.generate_pack("pytest-sicko-overlap", target_count=150, pool="sicko")
    notable_ids = {p["answer"]["player_id"] for p in notable_pack["puzzles"]}
    sicko_ids = {p["answer"]["player_id"] for p in sicko_pack["puzzles"]}
    assert notable_ids, "expected real notable puzzles"
    assert sicko_ids, "expected real sicko puzzles"
    assert not (notable_ids & sicko_ids), "a player appeared as a target in both pools"
    for p in notable_pack["puzzles"]:
        assert p["difficulty_band"] in ("Easy", "Medium", "Hard")
    for p in sicko_pack["puzzles"]:
        assert p["difficulty_band"] == "Sicko"


def test_generate_pack_rejects_an_unknown_pool():
    from tools.director_v04 import cfb_player_from_clues as mod

    with pytest.raises(ValueError):
        mod.generate_pack("pytest-bad-pool", target_count=10, pool="hardcore")


def test_easy_band_always_has_a_real_all_america_or_early_round_signal():
    """Independently re-derives the real signal straight from the source
    tables (never trusting generate_pack()'s own bookkeeping) for every
    Easy-banded target in a real sample -- must be all_america-certified
    or NFL-bridge-certified with a real round-1/2 draft, exactly as
    _attach_difficulty_bands() itself defines "Easy"."""
    from tools.quiz_export import engine
    from tools.director_v04 import cfb_player_from_clues as mod

    c = engine.connect()
    try:
        pack = mod.generate_pack("pytest-easy-signal", target_count=80, pool="notable")
        easy_ids = [p["answer"]["player_id"] for p in pack["puzzles"] if p["difficulty_band"] == "Easy"]
        assert easy_ids, "expected at least one real Easy puzzle in a real 80-target sample"
        for pid in easy_ids:
            is_all_america = c.execute(
                "SELECT 1 FROM cfb_all_america_certified WHERE cfb_player_id=?", (pid,)
            ).fetchone() is not None
            best_round = c.execute(
                "SELECT MIN(d.draft_round) FROM cfb_nfl_identity_bridge_certified b "
                "JOIN draft_facts d ON b.nfl_player_key = d.player_key WHERE b.cfb_player_id=?", (pid,)
            ).fetchone()[0]
            assert is_all_america or (best_round is not None and best_round <= 2), (
                pid, is_all_america, best_round
            )
    finally:
        c.close()
