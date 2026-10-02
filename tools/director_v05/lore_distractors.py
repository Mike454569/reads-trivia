"""Deep-lore distractor pools and profile-aware scoring."""
from __future__ import annotations

import hashlib
from collections import defaultdict

from .distractor_intelligence import Candidate, select_distractors, validate_distractors
from .entity_labels import resolve_label


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _nfl_profile(conn, player_id):
    tables = _tables(conn)
    sid = str(player_id)
    era = None
    team = None
    tier = None
    numeric = None
    position = None

    if "draft_facts" in tables:
        r = conn.execute(
            """SELECT draft_season,draft_round,draft_pick_overall,draft_team
               FROM draft_facts
               WHERE player_key=? AND verification_status='SOURCE_BACKED'
               ORDER BY draft_season LIMIT 1""",
            (sid,),
        ).fetchone()
        if r:
            era = r["draft_season"]
            team = r["draft_team"]
            tier = ("ROUND_" + str(r["draft_round"])) if r["draft_round"] is not None else None
            numeric = float(r["draft_pick_overall"]) if r["draft_pick_overall"] is not None else None

    if "nfl_all_pro_selections" in tables:
        r = conn.execute(
            """SELECT position_raw FROM nfl_all_pro_selections
               WHERE player_id=? AND is_ap=1
               ORDER BY season DESC LIMIT 1""",
            (sid,),
        ).fetchone()
        if r and r["position_raw"]:
            position = str(r["position_raw"])

    if position is None and "nfl_pro_bowl_selections" in tables:
        r = conn.execute(
            """SELECT position_raw FROM nfl_pro_bowl_selections
               WHERE player_id=?
               ORDER BY season DESC LIMIT 1""",
            (sid,),
        ).fetchone()
        if r and r["position_raw"]:
            position = str(r["position_raw"])

    return Candidate(
        sid,
        resolve_label(conn, "NFL_PLAYER", sid),
        era,
        position,
        team,
        tier,
        numeric,
        True,
    )


def _nfl_candidate_ids(conn, correct_id, profile, *, limit=1000):
    tables = _tables(conn)
    ids = set()
    params = []

    if "draft_facts" in tables and profile.era is not None:
        rows = conn.execute(
            """SELECT DISTINCT player_key
               FROM draft_facts
               WHERE verification_status='SOURCE_BACKED'
                 AND player_key<>?
                 AND draft_season BETWEEN ? AND ?
               ORDER BY ABS(draft_season-?),draft_pick_overall
               LIMIT ?""",
            (
                str(correct_id),
                int(profile.era) - 5,
                int(profile.era) + 5,
                int(profile.era),
                int(limit),
            ),
        ).fetchall()
        ids.update(str(r["player_key"]) for r in rows)

    if "canonical_roster_seasons" in tables and profile.team:
        rows = conn.execute(
            """SELECT DISTINCT player_id
               FROM canonical_roster_seasons
               WHERE verification_status='SOURCE_BACKED'
                 AND team_code=? AND player_id<>?
               ORDER BY season DESC
               LIMIT ?""",
            (profile.team, str(correct_id), int(limit)),
        ).fetchall()
        ids.update(str(r["player_id"]) for r in rows)

    if "nfl_all_pro_selections" in tables and profile.position:
        rows = conn.execute(
            """SELECT DISTINCT player_id
               FROM nfl_all_pro_selections
               WHERE is_ap=1
                 AND verification_status='WIKIPEDIA_STRUCTURED_SECONDARY'
                 AND position_raw=? AND player_id IS NOT NULL AND player_id<>?
               ORDER BY season DESC
               LIMIT ?""",
            (profile.position, str(correct_id), int(limit)),
        ).fetchall()
        ids.update(str(r["player_id"]) for r in rows)

    return sorted(ids)


def nfl_lore_distractors(
    conn,
    correct_player_id,
    *,
    all_correct_ids=(),
    recent_distractor_ids=(),
    k=3,
    difficulty_band="HARD",
):
    """Select plausible NFL player distractors from era/team/position/draft context."""
    correct = _nfl_profile(conn, correct_player_id)
    pool = []
    for pid in _nfl_candidate_ids(conn, correct_player_id, correct):
        candidate = _nfl_profile(conn, pid)
        if candidate.label == candidate.entity_id:
            # No trustworthy human label means it is not user-facing ready.
            continue
        pool.append(candidate)

    selected = select_distractors(
        correct,
        pool,
        k=max(k, 8),
        forbidden_ids=all_correct_ids,
        recent_ids=recent_distractor_ids,
    )
    band = str(difficulty_band).upper()
    if band not in {"CASUAL","HARD","SICKO"}:
        raise ValueError("UNKNOWN_DISTRACTOR_DIFFICULTY_BAND")
    if band == "CASUAL":
        # Easier choices: still plausible, but avoid the three closest lookalikes.
        chosen = selected[-k:] if len(selected) >= k else selected
    elif band == "SICKO":
        chosen = selected[:k]
    else:
        # Hard sits between casual and sicko while keeping quality high.
        start = 1 if len(selected) >= k + 1 else 0
        chosen = selected[start:start+k]
        if len(chosen) < k:
            chosen = selected[:k]
    selected = chosen
    problem = validate_distractors(
        correct,
        selected,
        all_correct_ids=all_correct_ids,
    )
    if problem:
        raise ValueError(problem)
    if len(selected) < k:
        raise ValueError("INSUFFICIENT_DEEP_LORE_DISTRACTORS")
    return {
        "correct": correct,
        "selected": selected,
        "pool_size": len(pool),
    }


def _ordered_options(question_id, labels):
    """Deterministically shuffle options so the correct answer has no fixed slot."""
    return sorted(
        labels,
        key=lambda label: hashlib.sha256(
            (str(question_id) + "|" + str(label)).encode()
        ).hexdigest(),
    )


def attach_deep_lore_options(
    conn,
    question,
    *,
    all_correct_ids=(),
    recent_distractor_ids=(),
    difficulty_band=None,
):
    """Attach plausible four-choice options to supported deep-lore questions."""
    answer = question.get("answer") or {}
    answer_type = str(answer.get("type") or "")
    answer_id = str(answer.get("id") or "")

    if answer_type != "NFL_PLAYER":
        raise ValueError("DEEP_LORE_DISTRACTORS_UNSUPPORTED_ANSWER_TYPE")

    band = str(difficulty_band or question.get("difficulty_band") or "HARD").upper()
    result = nfl_lore_distractors(
        conn,
        answer_id,
        all_correct_ids=set(str(x) for x in all_correct_ids) | {answer_id},
        recent_distractor_ids=recent_distractor_ids,
        k=3,
        difficulty_band=band,
    )
    options = _ordered_options(
        question.get("question_id"),
        [answer["label"]] + [d["label"] for d in result["selected"]],
    )

    out = dict(question)
    out["mechanic"] = "MULTIPLE_CHOICE"
    out["question"] = "Who am I?"
    out["options"] = options
    out["distractors"] = result["selected"]
    out["distractor_pool_size"] = result["pool_size"]
    out["distractor_difficulty_band"] = band
    return out


def distractor_report(conn, questions):
    counts = defaultdict(int)
    examples = []
    for q in questions:
        try:
            enriched = attach_deep_lore_options(conn, q)
            counts["PASSED"] += 1
            if len(examples) < 10:
                examples.append({
                    "question_id": enriched["question_id"],
                    "answer": enriched["answer"]["label"],
                    "distractors": [d["label"] for d in enriched["distractors"]],
                })
        except ValueError as exc:
            counts[str(exc).split(":")[0]] += 1
    return {"counts": dict(counts), "examples": examples}
