"""Build diverse deep-lore question banks without hammering the same answers or clue shapes."""
from __future__ import annotations

from collections import Counter

from .lore_chains import discover_lore_chains, compile_lore_chain_variants
from .lore_distractors import attach_deep_lore_options
from .lore_rotation import select_rotated_questions, question_lore_profile
from .lore_mix_policy import enforce_mix_policy


def _signature(question):
    return tuple(sorted(str(c.get("relation") or "") for c in question.get("clues") or []))


def build_lore_question_bank(
    conn,
    anchors,
    *,
    difficulty_band="HARD",
    target=25,
    recent_question_ids=(),
    recent_answer_ids=(),
    recent_chain_ids=(),
    max_per_answer=1,
    max_per_signature=3,
    with_options=True,
    recent_distractor_ids=(),
    recent_families=(),
    max_sensitive=1,
):
    """Compile a diverse bank from ranked chains while enforcing session freshness."""
    target = max(1, min(int(target), 500))
    recent_q = {str(x) for x in recent_question_ids}
    recent_a = {str(x) for x in recent_answer_ids}
    recent_c = {str(x) for x in recent_chain_ids}

    candidates = []
    for anchor_type, anchor_id in anchors:
        if str(anchor_id) in recent_a:
            continue
        chains = discover_lore_chains(
            conn, str(anchor_type), str(anchor_id), max_depth=6, max_chains=20
        )
        for chain in chains:
            if chain.chain_id in recent_c:
                continue
            variants = compile_lore_chain_variants(
                conn, chain, bands=(difficulty_band,), variants_per_band=3
            )
            for question in variants:
                if question["question_id"] in recent_q:
                    continue
                if with_options:
                    try:
                        question = attach_deep_lore_options(
                            conn,
                            question,
                            all_correct_ids={anchor_id},
                            recent_distractor_ids=recent_distractor_ids,
                        )
                    except ValueError:
                        continue
                candidates.append(question)

    # Harder / rarer questions first, but freshness caps decide what survives.
    candidates.sort(
        key=lambda q: (
            float(q.get("rarity_score") or 0),
            float(q.get("difficulty_score") or 0),
            int(q.get("depth") or 0),
            q["question_id"],
        ),
        reverse=True,
    )

    answer_counts = Counter()
    signature_counts = Counter()
    eligible = []
    seen_events = set()

    # First enforce hard anti-repeat constraints. Rotation happens only among
    # questions that are already safe to serve.
    for q in candidates:
        answer_id = str((q.get("answer") or {}).get("id") or "")
        if not answer_id:
            continue
        if answer_counts[answer_id] >= max_per_answer:
            continue

        sig = _signature(q)
        if signature_counts[sig] >= max_per_signature:
            continue

        event_ids = {
            str(h.get("object_id"))
            for h in ((q.get("provenance") or {}).get("chain") or {}).get("hops", [])
            if h.get("object_type") == "EVENT"
        }
        if event_ids and event_ids & seen_events:
            continue

        eligible.append(q)
        answer_counts[answer_id] += 1
        signature_counts[sig] += 1
        seen_events.update(event_ids)

    rotation = select_rotated_questions(
        conn,
        eligible,
        target=target,
        recent_families=recent_families,
        max_sensitive=max_sensitive,
        require_league_balance=True,
    )
    mix = enforce_mix_policy(
        rotation["selected"],
        target=target,
        max_draft_fraction=0.25,
        min_story_fraction=0.40,
    )
    selected = mix["selected"]

    # Recompute final-bank metrics after rotation/mix policy so reporting reflects what
    # was actually selected, not the larger eligible pool.
    final_answers = {str((q.get("answer") or {}).get("id") or "") for q in selected}
    final_signatures = {_signature(q) for q in selected}
    final_events = set()
    family_counts = Counter()
    league_counts = Counter()
    for q in selected:
        profile = question_lore_profile(conn, q)
        family_counts.update(profile["families"])
        league_counts.update(profile["leagues"])
        final_events.update(profile["event_ids"])

    return {
        "difficulty_band": str(difficulty_band).upper(),
        "target": target,
        "selected": selected,
        "selected_count": len(selected),
        "candidate_count": len(candidates),
        "unique_answers": len(final_answers),
        "unique_clue_signatures": len(final_signatures),
        "unique_events": len(final_events),
        "family_counts": dict(family_counts),
        "league_counts": dict(league_counts),
        "sensitive_count": rotation["sensitive_count"],
        "available_family_counts": rotation["available_family_counts"],
        "mix_counts": mix["mix_counts"],
        "draft_fraction": mix["draft_fraction"],
        "story_fraction": mix["story_fraction"],
        "with_options": bool(with_options),
    }


def bank_report(conn, *, limit_anchors=100, target=25):
    rows = conn.execute(
        """SELECT subject_type,subject_id,COUNT(DISTINCT event_id) n
           FROM universal_event_subject
           WHERE subject_type IN ('NFL_PLAYER','CFB_PLAYER','COACH')
           GROUP BY subject_type,subject_id
           ORDER BY n DESC,subject_type,subject_id
           LIMIT ?""",
        (int(limit_anchors),),
    ).fetchall()
    anchors = [(r["subject_type"], r["subject_id"]) for r in rows]
    return {
        band: build_lore_question_bank(
            conn, anchors, difficulty_band=band, target=target
        )
        for band in ("CASUAL", "HARD", "SICKO")
    }
