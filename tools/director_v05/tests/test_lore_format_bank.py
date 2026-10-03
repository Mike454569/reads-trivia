from tools.director_v05 import lore_format_bank as bank


def _q(qid, fmt, event_ids):
    mechanic = "SORTING_TIMELINE" if fmt == "TIMELINE" else "MULTIPLE_CHOICE"
    return {
        "question_id": qid,
        "mechanic": mechanic,
        "question_family": "LORE_" + fmt,
        "provenance": {"event_ids": event_ids},
    }


def test_multiformat_bank_rotates_formats_and_avoids_event_reuse(monkeypatch):
    discovered = {
        "COMMON_LINK": [
            _q("c1","COMMON_LINK",["e1","e2","e3"]),
            _q("c2","COMMON_LINK",["e10","e11","e12"]),
        ],
        "BEFORE_AFTER": [
            _q("b1","BEFORE_AFTER",["e4","e5"]),
            _q("b2","BEFORE_AFTER",["e13","e14"]),
        ],
        "TIMELINE": [
            _q("t1","TIMELINE",["e6","e7","e8","e9"]),
            _q("t2","TIMELINE",["e15","e16","e17","e18"]),
        ],
    }
    monkeypatch.setattr(bank, "discover_multiformat_candidates", lambda conn, limit=250: discovered)

    out = bank.build_multiformat_bank(None, target=6, max_per_format=2)
    assert out["selected_count"] == 6
    assert out["format_counts"] == {
        "COMMON_LINK":2,
        "BEFORE_AFTER":2,
        "TIMELINE":2,
    }

    seen = set()
    for q in out["selected"]:
        ids = set(q["provenance"]["event_ids"])
        assert not (ids & seen)
        seen.update(ids)


def test_recent_format_moves_later_in_rotation(monkeypatch):
    discovered = {
        "COMMON_LINK":[_q("c1","COMMON_LINK",["e1"])],
        "BEFORE_AFTER":[_q("b1","BEFORE_AFTER",["e2"])],
        "TIMELINE":[_q("t1","TIMELINE",["e3"])],
    }
    monkeypatch.setattr(bank, "discover_multiformat_candidates", lambda conn, limit=250: discovered)
    out = bank.build_multiformat_bank(
        None,
        target=2,
        recent_formats=("COMMON_LINK",),
        max_per_format=1,
    )
    assert [q["question_id"] for q in out["selected"]] == ["b1","t1"]


def test_duplicate_event_candidate_is_skipped(monkeypatch):
    discovered = {
        "COMMON_LINK":[_q("c1","COMMON_LINK",["e1","e2"])],
        "BEFORE_AFTER":[
            _q("b1","BEFORE_AFTER",["e2","e3"]),
            _q("b2","BEFORE_AFTER",["e4","e5"]),
        ],
        "TIMELINE":[],
    }
    monkeypatch.setattr(bank, "discover_multiformat_candidates", lambda conn, limit=250: discovered)
    out = bank.build_multiformat_bank(None, target=2, max_per_format=2)
    ids = [q["question_id"] for q in out["selected"]]
    assert "c1" in ids
    assert "b1" not in ids
    assert "b2" in ids
