from tools.director_v05 import lore_information_gain as lig

def _question():
    return {
        "difficulty_band":"HARD",
        "clues":[
            {"relation":"A","text":"A"},
            {"relation":"B","text":"B"},
            {"relation":"C","text":"C"},
        ],
        "distractors":[
            {"entity_id":"d1"},
            {"entity_id":"d2"},
            {"entity_id":"d3"},
        ],
    }

def test_hard_and_sicko_reveal_orders_differ(monkeypatch):
    monkeypatch.setattr(
        lig,
        "_candidate_match_map",
        lambda conn, question, ids: {
            0:{"survival_rate":0.9,"information_gain":0.1,"distractors_checked":3,"distractors_still_plausible":3},
            1:{"survival_rate":0.5,"information_gain":0.5,"distractors_checked":3,"distractors_still_plausible":2},
            2:{"survival_rate":0.1,"information_gain":0.9,"distractors_checked":3,"distractors_still_plausible":0},
        },
    )
    hard=lig.calibrate_reveal_order(None,_question(),difficulty_band="HARD")
    sicko=lig.calibrate_reveal_order(None,_question(),difficulty_band="SICKO")

    hard_order=[c["relation"] for c in hard["clues"]]
    sicko_order=[c["relation"] for c in sicko["clues"]]

    assert sicko_order==["A","B","C"]
    assert hard_order!=sicko_order
    assert hard_order[-1]=="C"
