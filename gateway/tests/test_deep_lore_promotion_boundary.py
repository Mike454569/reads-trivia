from gateway import config
from gateway.services import public_game
from tools.director_v02 import mechanic_engine
from tools.director_v05 import lore_promotion


def test_deep_lore_is_registered_for_creator_but_not_public():
    assert "DEEP_LORE_GUESS" in mechanic_engine.TAXONOMY_IDS
    assert "UNIVERSAL_DEEP_LORE" in mechanic_engine.VARIANTS["DEEP_LORE_GUESS"]
    assert "deep_lore_guess" in public_game.KNOWN_NOT_YET_PUBLIC_MODES
    assert "deep_lore_guess" not in public_game.PUBLIC_MODES
    assert "deep_lore_guess" not in config.PUBLIC_MODE_ALLOWLIST


def test_promotion_policy_rejects_small_sample(monkeypatch):
    monkeypatch.setattr(
        lore_promotion,
        "certify",
        lambda **kw: {
            "status":"PASSED",
            "passed_packages":3,
            "failures":[],
        },
    )
    result = lore_promotion.assess_public_promotion(seeds_per_band=1, target_count=3)
    assert result["promotion_ready"] is False
    assert "SAMPLE_TOO_SMALL" in result["reasons"]


def test_promotion_policy_requires_zero_failures(monkeypatch):
    monkeypatch.setattr(
        lore_promotion,
        "certify",
        lambda **kw: {
            "status":"FAILED",
            "passed_packages":29,
            "failures":[{"band":"hard","seed":"x"}],
        },
    )
    result = lore_promotion.assess_public_promotion(seeds_per_band=10, target_count=3)
    assert result["promotion_ready"] is False
    assert "CERTIFICATION_FAILED" in result["reasons"]
    assert "CERTIFICATION_FAILURES_PRESENT" in result["reasons"]


def test_promotion_policy_can_pass_without_auto_exposing_mode(monkeypatch):
    monkeypatch.setattr(
        lore_promotion,
        "certify",
        lambda **kw: {
            "status":"PASSED",
            "passed_packages":30,
            "failures":[],
        },
    )
    result = lore_promotion.assess_public_promotion(seeds_per_band=10, target_count=3)
    assert result["promotion_ready"] is True
    assert result["policy"]["automatic_public_promotion"] is False
    assert "deep_lore_guess" not in public_game.PUBLIC_MODES
