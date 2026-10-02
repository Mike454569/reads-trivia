from tools.director_v05 import certify_deep_lore_delivery as cert


def _package(band):
    return {
        "package_id":"GGP39:" + ("a" * 24),
        "qa_status":"PASSED",
        "review_status":"UNREVIEWED",
        "question_count":1,
        "questions":[{
            "id":"q1",
            "question":"Who am I?",
            "clues":[
                "I was drafted by Green Bay in 2020.",
                "I made the Pro Bowl in 2022.",
                "In 2023, I scored on a bizarre broken play.",
            ],
            "options":["A","B","C","D"],
            "correctIndex":1,
            "answer":"B",
            "difficulty":band,
        }],
    }


def test_certifier_passes_only_when_every_band_is_clean(monkeypatch):
    monkeypatch.setattr(cert, "build_package", lambda **kw: _package(kw["difficulty"]))
    result = cert.certify(seeds_per_band=2, target_count=1)
    assert result["status"] == "PASSED"
    assert result["public_promotion_ready"] is True
    assert result["passed_packages"] == 6


def test_certifier_blocks_robotic_copy(monkeypatch):
    def bad(**kw):
        p = _package(kw["difficulty"])
        p["questions"][0]["clues"][2] = "I was involved in the strangest verified moment."
        return p
    monkeypatch.setattr(cert, "build_package", bad)
    result = cert.certify(seeds_per_band=1, target_count=1)
    assert result["status"] == "FAILED"
    assert result["public_promotion_ready"] is False


def test_certifier_blocks_shortfall(monkeypatch):
    monkeypatch.setattr(cert, "build_package", lambda **kw: _package(kw["difficulty"]))
    result = cert.certify(seeds_per_band=1, target_count=2)
    assert result["status"] == "FAILED"
    assert result["public_promotion_ready"] is False
