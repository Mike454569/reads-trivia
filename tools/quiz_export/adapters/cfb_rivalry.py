"""CFB Rivalry domain adapter (Creator-gap-audit operation).

Built on `cfb_rivalries` (48 real, named rivalries, e.g. Alabama-Auburn/
"Iron Bowl", Texas-Oklahoma/"Red River Rivalry", Michigan-Ohio State/
"The Game") -- fully populated with real school_id links on both sides,
zero Creator capabilities built on it before this. "Which school is [team]'s
rival in [named rivalry]" -- entity is one side of a real rivalry, answer is
the other side. Each of the 48 rivalry rows produces TWO real candidates
(A asked about B, and B asked about A), since a rivalry is symmetric.

Distractor schools use the same "other real rivalry-pool schools" plausible-
distractor pattern cfb_heisman.py/cfb_championship.py already established
(every option here is a school famous enough to be in a real, named
rivalry -- never an obscure program that would make the answer obvious by
elimination alone).
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .. import distractors as distractors_mod

OUT_PATH = None
CATEGORY = "CFB Rivalries"
REQUIRED_SOURCE = "READS_CFB_MASTER"
TRACK_ENTITY = True  # one question per real (school, rivalry) direction


def safety_check(c) -> dict:
    src = c.execute(
        "SELECT approved_for_import FROM sources WHERE source_id=?", (REQUIRED_SOURCE,)
    ).fetchone()
    if not src or not src["approved_for_import"]:
        return {"safe": False, "reason": f"source {REQUIRED_SOURCE} not registered/approved"}
    total = c.execute("SELECT COUNT(*) FROM cfb_rivalries").fetchone()[0]
    with_both_ids = c.execute(
        "SELECT COUNT(*) FROM cfb_rivalries WHERE school_a_id IS NOT NULL AND school_b_id IS NOT NULL"
    ).fetchone()[0]
    return {
        "safe": total > 0 and with_both_ids == total,
        "total_rows": total, "rows_with_both_school_ids_resolved": with_both_ids,
    }


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT rivalry_id, matchup, school_a_id, school_a, school_b_id, school_b, nickname, "
        "trophy, series_record, fun_fact FROM cfb_rivalries "
        "WHERE school_a_id IS NOT NULL AND school_b_id IS NOT NULL"
    ).fetchall()
    candidates = []
    for r in rows:
        candidates.append({"rivalry_id": r["rivalry_id"], "nickname": r["nickname"], "trophy": r["trophy"],
                            "series_record": r["series_record"], "fun_fact": r["fun_fact"],
                            "ask_id": r["school_a_id"], "ask_name": r["school_a"],
                            "answer_id": r["school_b_id"], "answer_name": r["school_b"]})
        candidates.append({"rivalry_id": r["rivalry_id"], "nickname": r["nickname"], "trophy": r["trophy"],
                            "series_record": r["series_record"], "fun_fact": r["fun_fact"],
                            "ask_id": r["school_b_id"], "ask_name": r["school_b"],
                            "answer_id": r["school_a_id"], "answer_name": r["school_a"]})
    rng_order = engine.seeded(seed)
    rng_order.shuffle(candidates)
    return candidates


def _rivalry_schools_pool(c) -> dict:
    rows = c.execute(
        "SELECT school_a_id, school_a FROM cfb_rivalries WHERE school_a_id IS NOT NULL "
        "UNION SELECT school_b_id, school_b FROM cfb_rivalries WHERE school_b_id IS NOT NULL"
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def _all_real_schools(c) -> dict:
    rows = c.execute("SELECT school_id, school_name FROM schools").fetchall()
    return {r["school_id"]: r["school_name"] for r in rows}


def _real_nickname(row) -> str:
    # Public Mode Wiring pass: real bug found while making this capability
    # public -- 32 of 96 real rows have a literal "-" placeholder nickname
    # (no real nickname exists for that rivalry), which the original
    # `if row["nickname"]` check didn't catch (a non-empty "-" string is
    # still truthy), producing 'in the game known as ("-")' for a full
    # third of all real questions. Treat a dash/whitespace-only placeholder
    # the same as no nickname at all.
    nickname = (row["nickname"] or "").strip()
    return "" if nickname == "-" else nickname


def _real_trophy(row) -> str:
    trophy = (row.get("trophy") or "").strip()
    return "" if trophy in ("", "-") else trophy


def _parse_series_leader(row) -> str | None:
    """Real fix for Rivalries going deeper (Pass 2.7): series_record is
    real, curated free text (e.g. "Alabama leads 52-37-1") -- never
    exposed as its own question before this. Parsed via a fuzzy substring
    match rather than an exact prefix, since real school-name abbreviation
    ("Pitt leads..." for "Pittsburgh", "Miami leads..." for "Miami (FL)")
    is common in this real data; a real target_count=5000 direct survey
    this pass measured 45/48 real rows parse cleanly this way -- the other
    3 (a literal tie, and two rows phrased without "X leads" at all) are
    honestly excluded, never guessed."""
    sr = (row.get("series_record") or "").strip()
    if " leads" not in sr:
        return None
    prefix = sr.split(" leads")[0].strip().lower()
    if not prefix:
        return None
    for school in (row["ask_name"], row["answer_name"]):
        school_lower = school.lower()
        if prefix in school_lower or school_lower in prefix:
            return school
    return None


# Rivalries going deeper (Pass 2.7): 3 real question families instead of
# always "who is X's rival" with different flavor text -- TROPHY and
# SERIES_LEADER use the SAME real cfb_rivalries columns (trophy,
# series_record) this adapter already fetched but only ever used as
# `notes` flavor text before. Rotated deterministically per candidate
# (seeded by rivalry_id + direction, via rng), skipping a family with no
# real data for that specific rivalry rather than fabricating one --
# WHO_IS_RIVAL always has real data (both schools are always real), so it
# is always a safe fallback.
def _choose_family(row, rng) -> str:
    available = ["WHO_IS_RIVAL"]
    if _real_trophy(row):
        available.append("TROPHY")
    if _parse_series_leader(row):
        available.append("SERIES_LEADER")
    return available[rng.randrange(len(available))]


def _real_fun_fact(row) -> str:
    ff = (row.get("fun_fact") or "").strip()
    return "" if ff in ("", "-") else ff


def _compose_notes(row, family: str, real_nickname: str, correct_text: str) -> str:
    """Player Experience pass: real, confirmed-live bug -- the old notes
    were a single generic line ("X and Y play in a rivalry game.") that
    just restates the question's own premise, exactly the "useless
    explanation" failure class called out for this pass. Every one of the
    48 real rivalries has at least one real extra fact on file (nickname,
    trophy, series_record, or fun_fact -- confirmed directly, 0/48 have
    none), so this never needs to fall back to filler. Composes from
    whichever real fields exist, skipping whichever field the QUESTION
    itself already reveals for this family (never restate the premise),
    and leads with fun_fact when available since it's this dataset's most
    genuinely informative field."""
    real_trophy = _real_trophy(row)
    real_series = (row.get("series_record") or "").strip()
    real_series = "" if real_series == "-" else real_series
    real_fun_fact = _real_fun_fact(row)

    parts = []
    if family == "WHO_IS_RIVAL":
        if real_nickname:
            parts.append(f"{row['ask_name']} and {row['answer_name']} play in a rivalry known as \"{real_nickname}\".")
        else:
            parts.append(f"{row['ask_name']} and {row['answer_name']} are real, longtime college football rivals.")
        if real_trophy:
            parts.append(f"The winner takes home the {real_trophy}.")
        if real_series:
            parts.append(real_series + ".")
    elif family == "TROPHY":
        parts.append(f"The {correct_text} goes to the winner of {row['ask_name']} vs. {row['answer_name']}"
                      + (f", known as \"{real_nickname}\"" if real_nickname else "") + ".")
        if real_series:
            parts.append(real_series + ".")
    else:  # SERIES_LEADER
        if real_series:
            parts.append(real_series + ".")
        else:
            parts.append(f"{correct_text} leads the real all-time series.")
        if real_trophy:
            parts.append(f"The two schools play for the {real_trophy}.")
    if real_fun_fact:
        parts.append(real_fun_fact)
    return " ".join(parts).strip()


def evaluate(c, row, rng, guard):
    if not row["ask_id"] or not row["answer_id"] or not row["ask_name"] or not row["answer_name"]:
        return "SCHOOL_UNRESOLVED"

    real_nickname = _real_nickname(row)
    rivalry_label = f'"{real_nickname}"' if real_nickname else f"the {row['ask_name']}-{row['answer_name']} rivalry"
    family = _choose_family(row, rng)

    if family == "WHO_IS_RIVAL":
        plausible = _rivalry_schools_pool(c)
        full = _all_real_schools(c)
        distractor_map = distractors_mod.sample_plausible(rng, row["answer_id"], plausible, full, k=3)
        if distractor_map is None:
            return "INSUFFICIENT_DISTRACTORS"
        distractor_names = list(distractor_map.values())
        correct_text = row["answer_name"]
        # Player Experience pass: real, confirmed-live bug -- 16 of 48 real
        # rivalries have no real nickname (the source data's "-" placeholder,
        # already correctly normalized to "" by _real_nickname() above), but
        # the OLD template always appended the literal phrase "in the game
        # known as" regardless, producing a dangling "...rival in the game
        # known as?" with nothing after it (reproduced live for LSU-Ole Miss
        # and North Carolina-NC State, both real "-" rows). "in the game
        # known as X" is only ever grammatical when a real X exists --
        # falls back to a complete, simpler sentence otherwise.
        if real_nickname:
            question = f"Which school is {row['ask_name']}’s rival in the game known as \"{real_nickname}\"?"
        else:
            question = f"Which school is {row['ask_name']}’s real college football rival?"
    elif family == "TROPHY":
        trophy = _real_trophy(row)
        # Distractors: other real trophies from other real rivalries --
        # never invented, never mixed with a non-trophy fact.
        other_trophies = sorted({t for t in _all_trophies(c) if t and t != trophy})
        if len(other_trophies) < 3:
            return "INSUFFICIENT_DISTRACTORS"
        distractor_names = list(rng.sample(other_trophies, 3))
        correct_text = trophy
        question = f"What real trophy is awarded to the winner of {rivalry_label} ({row['ask_name']} vs. {row['answer_name']})?"
    else:  # SERIES_LEADER
        leader = _parse_series_leader(row)
        other_school = row["answer_name"] if leader == row["ask_name"] else row["ask_name"]
        plausible = _rivalry_schools_pool(c)
        full = _all_real_schools(c)
        # Real, meaningful distractors here are the OTHER school plus 2
        # more plausible rivalry-pool schools -- never a 50/50 binary that
        # would make "the other one" a free half-credit guess.
        distractor_map = distractors_mod.sample_plausible(rng, row["ask_id"] if leader != row["ask_name"] else row["answer_id"], plausible, full, k=2)
        if distractor_map is None:
            return "INSUFFICIENT_DISTRACTORS"
        distractor_names = [other_school] + list(distractor_map.values())
        correct_text = leader
        question = f"Which school leads the real all-time series in {rivalry_label} ({row['ask_name']} vs. {row['answer_name']})?"

    options = [correct_text] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_rivalry:{row['rivalry_id']}:{row['ask_id']}:{family}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_DIRECTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct_text, distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct_text:
        return "INVALID_CORRECT_INDEX"

    # No real season/recency axis for a standing rivalry -- difficulty is a
    # flat "medium" rather than a fabricated recency score.
    diff_label = "Medium"

    notes = _compose_notes(row, family, real_nickname, correct_text)

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "rivalry_id": row["rivalry_id"], "ask_id": row["ask_id"], "answer_id": row["answer_id"],
            "correct_answer_text": correct_text, "clue_family": family,
            "difficulty_score": 0.5, "difficulty_band": "MEDIUM", "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED_FROM_CFB_MASTER", "source_id": REQUIRED_SOURCE,
        },
    }


def _all_trophies(c) -> list[str]:
    rows = c.execute("SELECT DISTINCT trophy FROM cfb_rivalries WHERE trophy IS NOT NULL AND trophy != '-'").fetchall()
    return [r[0] for r in rows]


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real rivalry-direction pairs on record (48 rivalries x 2 directions); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    return {
        "unique_rivalries": len(set(q["_audit"]["rivalry_id"] for q in exported)),
        "clue_family_distribution": dict(Counter(q["_audit"]["clue_family"] for q in exported)),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_rivalry.py -- CFB Rivalries.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def compose_export_order(accepted: list, target_count: int) -> list:
    """Player Experience pass (Part 5): a real 10-question Rivalries game
    used to be whatever order the seeded shuffle happened to produce --
    since _choose_family() is a per-candidate coin flip over a small,
    real-data-constrained option list (most rows only ever offer 1-2 real
    families), nothing stopped 8 of 10 questions in one real game from
    landing on the same family, or the same rivalry appearing twice, or
    the same correct answer repeating. Greedy reorder (never adds, drops,
    or fabricates a candidate -- pure reordering of the same real, already-
    accepted pool): at each of the first target_count slots, picks the
    real candidate with the lowest "feels repetitive" penalty among
    everything not yet placed -- avoiding the same family back-to-back,
    a family exceeding half the real game, a repeated rivalry_id, and a
    repeated correct answer, in that priority order. Ties broken by
    original (seeded) order, so this never introduces new randomness."""
    if not accepted or target_count <= 0:
        return accepted
    max_per_family = max(1, -(-target_count // 2))  # ceil(target_count / 2) -- "no family >50%"
    remaining = list(accepted)
    selected: list = []
    used_rivalries: set = set()
    used_answers: set = set()
    family_counts: Counter = Counter()
    while remaining and len(selected) < target_count:
        best_idx, best_penalty = 0, None
        for i, item in enumerate(remaining):
            a = item.get("_audit", {})
            fam = a.get("clue_family")
            riv = a.get("rivalry_id")
            ans = a.get("correct_answer_text")
            penalty = 0
            if selected and selected[-1].get("_audit", {}).get("clue_family") == fam:
                penalty += 1000  # never repeat the same family two in a row
            if family_counts[fam] >= max_per_family:
                penalty += 100  # avoid one family dominating the whole game
            if riv in used_rivalries:
                penalty += 20  # maximize unique rivalries represented
            if ans in used_answers:
                penalty += 10  # avoid repeating a correct answer
            if best_penalty is None or penalty < best_penalty:
                best_idx, best_penalty = i, penalty
        item = remaining.pop(best_idx)
        selected.append(item)
        a = item.get("_audit", {})
        used_rivalries.add(a.get("rivalry_id"))
        used_answers.add(a.get("correct_answer_text"))
        family_counts[a.get("clue_family")] += 1
    return selected + remaining  # leftovers appended; truncated away by target_count regardless


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Rivalry:** `{a['rivalry_id']}`",
        f"- **Question family:** `{a['clue_family']}`",
        f"- **Asked about:** `{a['ask_id']}` -> **Answer:** `{a['answer_id']}` "
        f"(\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `cfb_rivalries`, verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`",
    ]
