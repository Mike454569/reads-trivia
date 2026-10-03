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

    eligible = []
    seen_question_ids = set()

    # Do not consume answer/signature/event freshness here. Those caps belong
    # to the actual scheduler selection, otherwise a high-ranked candidate
    # that never makes the bank can poison later choices.
    for q in candidates:
        answer_id = str((q.get("answer") or {}).get("id") or "")
        if not answer_id:
            continue
        qid = str(q.get("question_id") or "")
        if not qid or qid in seen_question_ids:
            continue
        seen_question_ids.add(qid)
        eligible.append(q)

    # Give mix policy a real bench to choose from. Passing exactly target
    # rotated questions made a 40% story floor impossible whenever rotation
    # happened to return too few story candidates.
    rotation_target = min(len(eligible), max(target, target * 3))
    rotation = select_rotated_questions(
        conn,
        eligible,
        target=rotation_target,
        recent_families=recent_families,
        max_sensitive=max_sensitive,
        require_league_balance=True,
        max_per_answer=max_per_answer,
        max_per_signature=max_per_signature,
        no_repeat_events=True,
    )
    mix = enforce_mix_policy(
        rotation["selected"],
        target=target,
        max_draft_fraction=0.25,
        min_story_fraction=0.40,
    )
    selected = mix["selected"]

    # Final option pass: recent_distractor_ids is only a ranking penalty in
    # distractor_intelligence, so it does NOT guarantee session uniqueness.
    # Re-attach options to the actually selected bank and hard-forbid every
    # distractor already used in this bank.
    if with_options and selected:
        all_answer_ids = {
            str((q.get("answer") or {}).get("id") or "")
            for q in selected
        }
        used_distractors = {str(x) for x in recent_distractor_ids}
        rebuilt = []
        for q in selected:
            try:
                enriched = attach_deep_lore_options(
                    conn,
                    q,
                    all_correct_ids=all_answer_ids | used_distractors,
                    recent_distractor_ids=used_distractors,
                    difficulty_band=difficulty_band,
                )
            except ValueError:
                continue
            ids = {
                str(d.get("entity_id"))
                for d in (enriched.get("distractors") or [])
                if d.get("entity_id") is not None
            }
            if ids & used_distractors:
                continue
            used_distractors.update(ids)
            rebuilt.append(enriched)
        selected = rebuilt

    # Recompute final-bank metrics after rotation/mix policy so reporting reflects what
    # was actually selected, not the larger eligible pool.
    final_answers = {str((q.get("answer") or {}).get("id") or "") for q in selected}
    final_signatures = {_signature(q) for q in selected}
    final_events = set()
    family_counts = Counter()
    league_counts = Counter()
    final_mix_counts = Counter()
    final_sensitive_count = 0
    for q in selected:
        profile = question_lore_profile(conn, q)
        family_counts.update(profile["families"])
        league_counts.update(profile["leagues"])
        final_events.update(profile["event_ids"])
        final_mix_counts.update(__import__(
            "tools.director_v05.lore_mix_policy",
            fromlist=["question_mix_tags"],
        ).question_mix_tags(q))
        final_sensitive_count += int(profile["sensitive"])

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
        "sensitive_count": final_sensitive_count,
        "available_family_counts": rotation["available_family_counts"],
        "mix_counts": dict(final_mix_counts),
        "draft_fraction": round(final_mix_counts.get("DRAFT", 0) / max(1, len(selected)), 4),
        "story_fraction": round(final_mix_counts.get("STORY", 0) / max(1, len(selected)), 4),
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
