from tools.director_v04 import player_from_clues as pfc


def _fixture():
    rows = {
        "p1": dict(display_name="Target Player", college="Alabama", position="WR", draft_year=2020, draft_round=1,
                   draft_pick_overall=12, drafting_franchise="Raiders", team_history="Raiders",
                   career_span=(2020, 2026), postseason_participation=True, won_super_bowl=True),
        "p2": dict(display_name="Two", college="Alabama", position="WR", draft_year=2020, draft_round=2,
                   draft_pick_overall=40, drafting_franchise="Raiders", team_history="Raiders",
                   career_span=(2020, 2025), postseason_participation=True, won_super_bowl=False),
        "p3": dict(display_name="Three", college="Alabama", position="RB", draft_year=2020, draft_round=1,
                   draft_pick_overall=15, drafting_franchise="Raiders", team_history="Broncos",
                   career_span=(2020, 2026), postseason_participation=True, won_super_bowl=False),
        "p4": dict(display_name="Four", college="Georgia", position="WR", draft_year=2020, draft_round=1,
                   draft_pick_overall=18, drafting_franchise="Raiders", team_history="Raiders",
                   career_span=(2020, 2026), postseason_participation=True, won_super_bowl=True),
        "p5": dict(display_name="Five", college="Alabama", position="WR", draft_year=2019, draft_round=1,
                   draft_pick_overall=20, drafting_franchise="Giants", team_history="Raiders",
                   career_span=(2019, 2024), postseason_participation=False, won_super_bowl=False),
        "p6": dict(display_name="Six", college="LSU", position="WR", draft_year=2020, draft_round=1,
                   draft_pick_overall=22, drafting_franchise="Raiders", team_history="Chiefs",
                   career_span=(2020, 2026), postseason_participation=True, won_super_bowl=True),
        "p7": dict(display_name="Seven", college="Alabama", position="TE", draft_year=2021, draft_round=3,
                   draft_pick_overall=80, drafting_franchise="Bills", team_history="Raiders",
                   career_span=(2021, 2026), postseason_participation=True, won_super_bowl=False),
        "p8": dict(display_name="Eight", college="Clemson", position="WR", draft_year=2022, draft_round=1,
                   draft_pick_overall=9, drafting_franchise="Raiders", team_history="Raiders",
                   career_span=(2022, 2026), postseason_participation=True, won_super_bowl=False),
    }
    indexes = {k: {} for k in (
        "draft_year", "draft_round", "draft_pick_overall", "position", "drafting_franchise",
        "team_history", "career_span", "college", "postseason_participation", "won_super_bowl",
    )}
    for pid, fact in rows.items():
        for ct in indexes:
            value = fact.get(ct)
            if ct in ("postseason_participation", "won_super_bowl"):
                if not value:
                    continue
                value = True
            if value is None:
                continue
            indexes[ct].setdefault(value, set()).add(pid)
    return rows, indexes, frozenset(rows)


def test_who_am_i_v2_builds_human_first_composite_ladder():
    facts, indexes, universe = _fixture()
    puzzle, reason = pfc.build_puzzle("p1", facts, indexes, universe)
    assert reason is None
    assert puzzle["who_am_i_v2"]["version"] == 2
    assert 3 <= len(puzzle["clues"]) <= 5
    assert puzzle["final_candidate_count"] == 1
    assert puzzle["clues"][0]["clue_type"] not in {"position", "postseason_participation"}
    assert all(clue["candidates_after"] < clue["candidates_before"] for clue in puzzle["clues"])
    assert all("clue_intelligence" in clue for clue in puzzle["clues"])
    assert any(clue["clue_intelligence"]["composite"] for clue in puzzle["clues"])
    assert puzzle["clues"][1]["clue_intelligence"]["composite"] is True
    assert puzzle["clues"][1]["clue_type"] not in {"draft_round", "draft_year", "position"}
    assert pfc.validate_puzzle_qa(puzzle, universe, indexes) == []


def test_who_am_i_v2_qa_rederives_composite_truth():
    facts, indexes, universe = _fixture()
    puzzle, reason = pfc.build_puzzle("p1", facts, indexes, universe)
    assert reason is None
    composite = next(clue for clue in puzzle["clues"] if clue["clue_intelligence"]["composite"])
    original = composite["value"]
    values = list(original)
    values[0] = "Definitely Not A Real Matching Value"
    composite["value"] = tuple(values)
    issues = pfc.validate_puzzle_qa(puzzle, universe, indexes)
    assert any(x.startswith("CLUE_NOT_TRUE_FOR_TARGET_") for x in issues)
