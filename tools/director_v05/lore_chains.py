"""Automatic multi-hop lore chaining across verified events and structured football facts."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from .lore_trivia import gameplay_eligibility
from .entity_labels import resolve_label
from .lore_phrasing import render_chain_clues, order_clues, question_stem

VERIFIED_RELATION_STATUSES = {
    "SOURCE_BACKED", "SOURCE_BACKED_DERIVED",
    "WIKIPEDIA_STRUCTURED_SECONDARY", "SOURCE_BACKED_INHERITED",
}

@dataclass(frozen=True)
class LoreHop:
    relation: str
    subject_type: str
    subject_id: str
    object_type: str
    object_id: str
    season: int | None = None
    source_kind: str | None = None
    source_id: str | None = None
    verification_status: str | None = None

@dataclass(frozen=True)
class LoreChain:
    chain_id: str
    anchor_type: str
    anchor_id: str
    hops: tuple[LoreHop, ...]
    depth: int
    source_diversity: int
    rarity_score: float
    difficulty_score: float
    provenance_complete: bool
    gameplay_eligible: bool


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _stable_chain_id(anchor_type, anchor_id, hops):
    seed = "|".join(
        [anchor_type, str(anchor_id)]
        + [
            f"{h.relation}:{h.subject_type}:{h.subject_id}:{h.object_type}:{h.object_id}:{h.season}"
            for h in hops
        ]
    )
    return "lchain_" + hashlib.sha256(seed.encode()).hexdigest()[:24]


def _event_edges(conn, subject_type, subject_id):
    rows = conn.execute(
        """SELECT e.*, s.role
           FROM universal_event_subject s
           JOIN universal_event e ON e.event_id=s.event_id
           WHERE s.subject_type=? AND s.subject_id=?
             AND e.verification_status='VERIFIED'
           ORDER BY e.event_date,e.event_id""",
        (subject_type, str(subject_id)),
    ).fetchall()
    out = []
    for row in rows:
        event = dict(row)
        gate = gameplay_eligibility(conn, event)
        if not gate["eligible"]:
            continue
        season = None
        raw = str(event.get("event_date") or "")
        if len(raw) >= 4 and raw[:4].isdigit():
            season = int(raw[:4])
        out.append(LoreHop(
            "SUBJECT_OF_EVENT",
            subject_type,
            str(subject_id),
            "EVENT",
            str(event["event_id"]),
            season,
            "LORE_EVENT",
            str(event["event_id"]),
            "VERIFIED",
        ))
    return out


def _event_subject_edges(conn, event_id):
    rows = conn.execute(
        """SELECT subject_type,subject_id,role
           FROM universal_event_subject
           WHERE event_id=?
           ORDER BY subject_type,subject_id,role""",
        (str(event_id),),
    ).fetchall()
    out = []
    for row in rows:
        if row["subject_type"] == "GAME":
            continue
        out.append(LoreHop(
            "EVENT_SUBJECT",
            "EVENT",
            str(event_id),
            str(row["subject_type"]),
            str(row["subject_id"]),
            None,
            "LORE_EVENT",
            str(event_id),
            "VERIFIED",
        ))
    return out


def _structured_edges(conn, subject_type, subject_id):
    """Expose only source-backed structured relationships for graph traversal."""
    sid = str(subject_id)
    tables = _tables(conn)
    out = []

    if subject_type == "NFL_PLAYER":
        if "draft_facts" in tables:
            rows = conn.execute(
                """SELECT draft_team,draft_season,source_id,verification_status
                   FROM draft_facts
                   WHERE player_key=? AND verification_status='SOURCE_BACKED'
                     AND draft_team IS NOT NULL""",
                (sid,),
            ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "DRAFTED_BY", "NFL_PLAYER", sid, "NFL_TEAM", str(r["draft_team"]),
                    int(r["draft_season"]) if r["draft_season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

        if "canonical_roster_seasons" in tables:
            rows = conn.execute(
                """SELECT team_code,season,source_id,verification_status
                   FROM canonical_roster_seasons
                   WHERE player_id=? AND verification_status='SOURCE_BACKED'
                   ORDER BY season,team_code""",
                (sid,),
            ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "ROSTERED_BY", "NFL_PLAYER", sid, "NFL_TEAM", str(r["team_code"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

        if "nfl_all_pro_selections" in tables:
            rows = conn.execute(
                """SELECT honor_level,season,source_id,verification_status
                   FROM nfl_all_pro_selections
                   WHERE player_id=? AND is_ap=1
                     AND verification_status='WIKIPEDIA_STRUCTURED_SECONDARY'
                   ORDER BY season""",
                (sid,),
            ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "ALL_PRO", "NFL_PLAYER", sid, "AWARD", str(r["honor_level"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

        if "nfl_pro_bowl_selections" in tables:
            rows = conn.execute(
                """SELECT tier,season,source_id,verification_status
                   FROM nfl_pro_bowl_selections
                   WHERE player_id=?
                     AND verification_status='WIKIPEDIA_STRUCTURED_SECONDARY'
                   ORDER BY season""",
                (sid,),
            ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "PRO_BOWL", "NFL_PLAYER", sid, "AWARD", str(r["tier"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

        if "universal_derived_fact" in tables:
            rows = conn.execute(
                """SELECT derived_id,metric,value_num,formula_version
                   FROM universal_derived_fact
                   WHERE subject_type='NFL_PLAYER' AND subject_id=?
                     AND eligible_for_gameplay=1
                   ORDER BY metric,derived_id""",
                (sid,),
            ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "DERIVED_" + str(r["metric"]).upper(),
                    "NFL_PLAYER", sid, "DERIVED_FACT", str(r["derived_id"]),
                    None, "DERIVED_FACT", str(r["formula_version"]), "SOURCE_BACKED_DERIVED",
                ))

    elif subject_type == "CFB_PLAYER":
        if "cfb_transfer_summary" in tables:
            row = conn.execute(
                """SELECT first_school_id,last_school_id,first_season,last_season
                   FROM cfb_transfer_summary
                   WHERE cfb_player_id=? AND transfer_count>0 LIMIT 1""",
                (sid,),
            ).fetchone()
            if row:
                if row["first_school_id"]:
                    out.append(LoreHop(
                        "STARTED_AT", "CFB_PLAYER", sid, "SCHOOL", str(row["first_school_id"]),
                        int(row["first_season"]) if row["first_season"] is not None else None,
                        "STRUCTURED_FACT", "cfb_transfer_summary", "SOURCE_BACKED_DERIVED",
                    ))
                if row["last_school_id"]:
                    out.append(LoreHop(
                        "TRANSFERRED_TO", "CFB_PLAYER", sid, "SCHOOL", str(row["last_school_id"]),
                        int(row["last_season"]) if row["last_season"] is not None else None,
                        "STRUCTURED_FACT", "cfb_transfer_summary", "SOURCE_BACKED_DERIVED",
                    ))

    elif subject_type == "COACH":
        if "coach_team_seasons" in tables:
            rows = conn.execute(
                """SELECT team_code,season,source_id,verification_status
                   FROM coach_team_seasons
                   WHERE coach_id=? AND verification_status='SOURCE_BACKED'
                   ORDER BY season""",
                (sid,),
            ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "COACHED", "COACH", sid, "NFL_TEAM", str(r["team_code"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

    elif subject_type == "SCHOOL":
        if "cfb_rankings" in tables:
            rows = conn.execute(
                """SELECT rank,season,source_id,verification_status
                   FROM cfb_rankings
                   WHERE school_id=? AND verification_status='SOURCE_BACKED'
                   ORDER BY season,week,poll LIMIT 12""",
                (sid,),
            ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "RANKED", "SCHOOL", sid, "RANK", str(r["rank"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

    return out


def _neighbors(conn, node_type, node_id):
    if node_type == "EVENT":
        return _event_subject_edges(conn, node_id)
    out = _event_edges(conn, node_type, node_id)
    out.extend(_structured_edges(conn, node_type, node_id))
    return out


def _hop_verified(hop):
    if hop.source_kind == "LORE_EVENT":
        return hop.verification_status == "VERIFIED"
    return bool(hop.source_id) and hop.verification_status in VERIFIED_RELATION_STATUSES


def _score(hops):
    diversity = len({h.source_kind for h in hops if h.source_kind})
    relations = len({h.relation for h in hops})
    object_types = len({h.object_type for h in hops})
    event_hops = sum(1 for h in hops if h.source_kind == "LORE_EVENT")
    mixed_bonus = 2.0 if diversity >= 2 else 0.0
    rarity = min(10.0, 1.2 * relations + 0.8 * object_types + 0.6 * event_hops + mixed_bonus)
    difficulty = min(100.0, 18 + len(hops) * 12 + rarity * 3.5 + diversity * 4)
    complete = all(_hop_verified(h) for h in hops)
    gameplay = complete and len(hops) >= 3 and diversity >= 2 and relations >= 2
    return diversity, round(rarity, 3), round(difficulty, 2), complete, gameplay


def discover_lore_chains(conn, anchor_type, anchor_id, *, max_depth=5, max_chains=50):
    """Breadth-first traversal with loop prevention and mixed-source gameplay gating."""
    max_depth = max(3, min(int(max_depth), 7))
    max_chains = max(1, min(int(max_chains), 500))
    anchor_type = str(anchor_type)
    anchor_id = str(anchor_id)

    queue = deque([(anchor_type, anchor_id, tuple(), {(anchor_type, anchor_id)})])
    candidates = []

    while queue:
        node_type, node_id, hops, visited = queue.popleft()
        if len(hops) >= max_depth:
            continue

        for hop in _neighbors(conn, node_type, node_id):
            next_node = (hop.object_type, str(hop.object_id))
            if next_node in visited:
                continue
            new_hops = hops + (hop,)
            diversity, rarity, difficulty, complete, gameplay = _score(new_hops)
            if len(new_hops) >= 3 and gameplay:
                candidates.append(LoreChain(
                    _stable_chain_id(anchor_type, anchor_id, new_hops),
                    anchor_type,
                    anchor_id,
                    new_hops,
                    len(new_hops),
                    diversity,
                    rarity,
                    difficulty,
                    complete,
                    gameplay,
                ))
            if len(new_hops) < max_depth:
                queue.append((next_node[0], next_node[1], new_hops, visited | {next_node}))

    # Keep one best chain for an identical terminal signature.
    best = {}
    for chain in candidates:
        terminal = (chain.hops[-1].object_type, chain.hops[-1].object_id, tuple(h.relation for h in chain.hops))
        current = best.get(terminal)
        if current is None or (chain.difficulty_score, chain.rarity_score, chain.depth) > (
            current.difficulty_score, current.rarity_score, current.depth
        ):
            best[terminal] = chain

    ranked = sorted(
        best.values(),
        key=lambda c: (c.rarity_score, c.difficulty_score, c.depth, c.chain_id),
        reverse=True,
    )
    return ranked[:max_chains]


def chain_payload(chain):
    payload = asdict(chain)
    payload["hops"] = [asdict(h) for h in chain.hops]
    return payload


def compile_lore_chain_question(conn, chain):
    """Compile a discovered mixed-source chain into human-sounding deep trivia."""
    if not chain.gameplay_eligible or not chain.provenance_complete:
        raise ValueError("CHAIN_NOT_GAMEPLAY_ELIGIBLE")
    if chain.depth < 3:
        raise ValueError("CHAIN_TOO_SHALLOW")
    if chain.anchor_type not in {"NFL_PLAYER", "CFB_PLAYER", "COACH"}:
        raise ValueError("NATURAL_COPY_UNSUPPORTED_ANCHOR")

    clues = order_clues(render_chain_clues(conn, chain), chain.difficulty_score)
    answer = str(chain.anchor_id)
    answer_label = resolve_label(conn, chain.anchor_type, answer)

    combined = " ".join(c["text"] for c in clues).casefold()
    if answer_label and answer_label.casefold() in combined:
        raise ValueError("CHAIN_ANSWER_LEAKAGE")

    qid = "qdeep_" + hashlib.sha256((chain.chain_id + "|" + answer).encode()).hexdigest()[:24]
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "THREE_CLUES" if len(clues) <= 4 else "PROGRESSIVE_CLUE",
        "question_family": "DEEP_LORE_CHAIN",
        "question": question_stem(chain.anchor_type),
        "clues": clues,
        "answer": {"id": answer, "label": answer_label, "type": chain.anchor_type},
        "chain_id": chain.chain_id,
        "depth": chain.depth,
        "rarity_score": chain.rarity_score,
        "difficulty_score": chain.difficulty_score,
        "provenance": {
            "provenance_complete": chain.provenance_complete,
            "chain": chain_payload(chain),
        },
    }


def lore_chain_report(conn, *, limit_anchors=250, max_depth=5):
    """Measure automatic chain depth/coverage on event-linked football subjects."""
    rows = conn.execute(
        """SELECT subject_type,subject_id,COUNT(DISTINCT event_id) event_count
           FROM universal_event_subject
           WHERE subject_type IN ('NFL_PLAYER','CFB_PLAYER','COACH','NFL_TEAM','SCHOOL')
           GROUP BY subject_type,subject_id
           ORDER BY event_count DESC,subject_type,subject_id
           LIMIT ?""",
        (int(limit_anchors),),
    ).fetchall()

    counts = defaultdict(int)
    rejects = defaultdict(int)
    examples = []
    total = 0
    human_playable = 0
    for row in rows:
        chains = discover_lore_chains(
            conn, row["subject_type"], row["subject_id"],
            max_depth=max_depth, max_chains=20,
        )
        total += len(chains)
        for chain in chains:
            counts[f"depth_{chain.depth}"] += 1
            if chain.source_diversity >= 2:
                counts["mixed_source"] += 1
            try:
                question = compile_lore_chain_question(conn, chain)
                human_playable += 1
                counts["human_playable"] += 1
                if len(examples) < 10:
                    examples.append({
                        "chain_id": chain.chain_id,
                        "anchor_type": chain.anchor_type,
                        "answer_label": question["answer"]["label"],
                        "question": question["question"],
                        "clues": [c["text"] for c in question["clues"]],
                        "depth": chain.depth,
                        "rarity_score": chain.rarity_score,
                        "difficulty_score": chain.difficulty_score,
                    })
            except ValueError as exc:
                rejects[str(exc).split(":")[0]] += 1

    return {
        "anchors_scanned": len(rows),
        "playable_chains": total,
        "human_playable_questions": human_playable,
        "counts": dict(counts),
        "rejections": dict(rejects),
        "examples": examples,
    }
