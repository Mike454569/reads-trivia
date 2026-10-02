"""Build diverse deep-lore question banks without hammering the same answers or clue shapes."""
from __future__ import annotations

from collections import Counter

from .lore_chains import discover_lore_chains, compile_lore_chain_variants


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
    selected = []
    seen_events = set()

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
        # Avoid repeating the exact same lore event inside one generated bank.
        if event_ids and event_ids & seen_events:
            continue

        selected.append(q)
        answer_counts[answer_id] += 1
        signature_counts[sig] += 1
        seen_events.update(event_ids)

        if len(selected) >= target:
            break

    return {
        "difficulty_band": str(difficulty_band).upper(),
        "target": target,
        "selected": selected,
        "selected_count": len(selected),
        "candidate_count": len(candidates),
        "unique_answers": len(answer_counts),
        "unique_clue_signatures": len(signature_counts),
        "unique_events": len(seen_events),
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
