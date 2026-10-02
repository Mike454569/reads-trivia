from types import SimpleNamespace

from tools.director_v05 import lore_question_bank as bank


def _q(qid, answer, event, signature=("DRAFTED_BY","SUBJECT_OF_EVENT")):
    return {
        "question_id": qid,
        "answer": {"id": answer},
        "rarity_score": 8.0,
        "difficulty_score": 75.0,
        "depth": 4,
        "clues": [{"relation": r, "text": r} for r in signature],
        "provenance": {
            "chain": {
                "hops": [
                    {"object_type": "EVENT", "object_id": event},
                    {"object_type": "NFL_TEAM", "object_id": "T"},
                ]
            }
        },
    }


def test_bank_caps_answers_and_events(monkeypatch):
    chains = {
        "p1": [SimpleNamespace(chain_id="c1")],
        "p2": [SimpleNamespace(chain_id="c2")],
        "p3": [SimpleNamespace(chain_id="c3")],
    }
    questions = {
        "c1": [_q("q1","p1","e1"), _q("q1b","p1","e2")],
        "c2": [_q("q2","p2","e1"), _q("q2b","p2","e3")],
        "c3": [_q("q3","p3","e4")],
    }

    monkeypatch.setattr(bank, "discover_lore_chains",
                        lambda conn, typ, aid, **kw: chains[aid])
    monkeypatch.setattr(bank, "compile_lore_chain_variants",
                        lambda conn, chain, **kw: questions[chain.chain_id])

    result = bank.build_lore_question_bank(
        None,
        [("NFL_PLAYER","p1"),("NFL_PLAYER","p2"),("NFL_PLAYER","p3")],
        target=3,
        max_per_answer=1,
    )

    answers = [q["answer"]["id"] for q in result["selected"]]
    assert len(answers) == len(set(answers))
    events = []
    for q in result["selected"]:
        events.extend(
            h["object_id"] for h in q["provenance"]["chain"]["hops"]
            if h["object_type"] == "EVENT"
        )
    assert len(events) == len(set(events))


def test_bank_respects_recent_history(monkeypatch):
    monkeypatch.setattr(
        bank,
        "discover_lore_chains",
        lambda conn, typ, aid, **kw: [SimpleNamespace(chain_id="recent-chain"), SimpleNamespace(chain_id="fresh-chain")],
    )
    monkeypatch.setattr(
        bank,
        "compile_lore_chain_variants",
        lambda conn, chain, **kw: (
            [_q("recent-q","p1","e1")] if chain.chain_id == "recent-chain"
            else [_q("fresh-q","p1","e2")]
        ),
    )

    result = bank.build_lore_question_bank(
        None,
        [("NFL_PLAYER","p1")],
        recent_chain_ids={"recent-chain"},
        recent_question_ids={"recent-q"},
        target=5,
    )
    assert [q["question_id"] for q in result["selected"]] == ["fresh-q"]


def test_bank_limits_repeated_clue_shapes(monkeypatch):
    monkeypatch.setattr(
        bank,
        "discover_lore_chains",
        lambda conn, typ, aid, **kw: [SimpleNamespace(chain_id="c-" + aid)],
    )
    monkeypatch.setattr(
        bank,
        "compile_lore_chain_variants",
        lambda conn, chain, **kw: [
            _q("q-" + chain.chain_id, chain.chain_id, "e-" + chain.chain_id)
        ],
    )

    anchors = [("NFL_PLAYER", f"p{i}") for i in range(5)]
    result = bank.build_lore_question_bank(
        None, anchors, target=5, max_per_signature=2
    )
    assert result["selected_count"] == 2
    assert result["unique_clue_signatures"] == 1
