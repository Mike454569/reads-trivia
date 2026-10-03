"""Automatic multi-hop lore chaining across verified events and structured football facts."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from .lore_trivia import gameplay_eligibility
from .entity_labels import resolve_label, resolve_required_label
from .lore_phrasing import render_chain_clues, question_stem
from .lore_question_writer import select_clues, variant_id, writer_quality

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


def _structured_edges(conn, subject_type, subject_id, *, season_hint=None):
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

        if "universal_derived_fact" in tables and "universal_fact_evidence" in tables:
            rows = conn.execute(
                """SELECT d.derived_id,d.metric,d.value_num,d.formula_version,
                          e.source_url,e.evidence_tier
                   FROM universal_derived_fact d
                   JOIN universal_fact_evidence e ON e.fact_id=d.derived_id
                   WHERE d.subject_type='NFL_PLAYER' AND d.subject_id=?
                     AND d.eligible_for_gameplay=1
                   ORDER BY d.metric,d.derived_id,e.source_url""",
                (sid,),
            ).fetchall()
            seen_derived = set()
            for r in rows:
                did = str(r["derived_id"])
                if did in seen_derived:
                    continue
                seen_derived.add(did)
                out.append(LoreHop(
                    "DERIVED_" + str(r["metric"]).upper(),
                    "NFL_PLAYER", sid, "DERIVED_FACT", did,
                    None, "DERIVED_FACT", str(r["source_url"]), "SOURCE_BACKED_DERIVED",
                ))

    elif subject_type == "CFB_PLAYER":
        # Build school-history edges from the verified game-log table itself.
        # This avoids treating a derived transfer-summary table name as if it
        # were evidence. Every emitted hop carries a real source_id from an
        # underlying SOURCE_BACKED_DERIVED row.
        if "cfb_player_game_stats_real" in tables:
            rows = conn.execute(
                """SELECT school_id,MIN(season) first_season,MAX(season) last_season,
                          MIN(source_id) source_id
                   FROM cfb_player_game_stats_real
                   WHERE cfb_player_id=?
                     AND verification_status='SOURCE_BACKED_DERIVED'
                     AND school_id IS NOT NULL AND source_id IS NOT NULL
                   GROUP BY school_id
                   ORDER BY first_season,school_id""",
                (sid,),
            ).fetchall()
            if rows:
                for index, r in enumerate(rows):
                    relation = "STARTED_AT" if index == 0 else "TRANSFERRED_TO"
                    out.append(LoreHop(
                        relation,
                        "CFB_PLAYER", sid, "SCHOOL", str(r["school_id"]),
                        int(r["first_season"]) if r["first_season"] is not None else None,
                        "STRUCTURED_FACT", str(r["source_id"]), "SOURCE_BACKED_DERIVED",
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

    elif subject_type == "NFL_TEAM":
        # Controlled reverse traversal: team -> nearby drafted/rostered players.
        # Season proximity keeps fanout useful instead of exploding across an
        # entire franchise history.
        if "draft_facts" in tables:
            if season_hint is not None:
                rows = conn.execute(
                    """SELECT player_key,draft_season,source_id,verification_status
                       FROM draft_facts
                       WHERE draft_team=? AND verification_status='SOURCE_BACKED'
                         AND player_key IS NOT NULL
                         AND draft_season BETWEEN ? AND ?
                       ORDER BY ABS(draft_season-?),draft_pick_overall,player_key
                       LIMIT 10""",
                    (sid, int(season_hint)-3, int(season_hint)+3, int(season_hint)),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT player_key,draft_season,source_id,verification_status
                       FROM draft_facts
                       WHERE draft_team=? AND verification_status='SOURCE_BACKED'
                         AND player_key IS NOT NULL
                       ORDER BY draft_season DESC,draft_pick_overall,player_key
                       LIMIT 8""",
                    (sid,),
                ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "DRAFTED_PLAYER", "NFL_TEAM", sid, "NFL_PLAYER", str(r["player_key"]),
                    int(r["draft_season"]) if r["draft_season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

        if "coach_team_seasons" in tables:
            if season_hint is not None:
                rows = conn.execute(
                    """SELECT coach_id,season,source_id,verification_status
                       FROM coach_team_seasons
                       WHERE team_code=? AND verification_status='SOURCE_BACKED'
                         AND coach_id IS NOT NULL
                         AND season BETWEEN ? AND ?
                       ORDER BY ABS(season-?),season,coach_id
                       LIMIT 6""",
                    (sid, int(season_hint)-2, int(season_hint)+2, int(season_hint)),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT coach_id,season,source_id,verification_status
                       FROM coach_team_seasons
                       WHERE team_code=? AND verification_status='SOURCE_BACKED'
                         AND coach_id IS NOT NULL
                       ORDER BY season DESC,coach_id
                       LIMIT 6""",
                    (sid,),
                ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "TEAM_COACH", "NFL_TEAM", sid, "COACH", str(r["coach_id"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

        if "canonical_roster_seasons" in tables:
            if season_hint is not None:
                rows = conn.execute(
                    """SELECT player_id,season,source_id,verification_status
                       FROM canonical_roster_seasons
                       WHERE team_code=? AND verification_status='SOURCE_BACKED'
                         AND player_id IS NOT NULL
                         AND season BETWEEN ? AND ?
                       ORDER BY ABS(season-?),season,player_id
                       LIMIT 12""",
                    (sid, int(season_hint)-1, int(season_hint)+1, int(season_hint)),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT player_id,season,source_id,verification_status
                       FROM canonical_roster_seasons
                       WHERE team_code=? AND verification_status='SOURCE_BACKED'
                         AND player_id IS NOT NULL
                       ORDER BY season DESC,player_id
                       LIMIT 10""",
                    (sid,),
                ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "ROSTERED_PLAYER", "NFL_TEAM", sid, "NFL_PLAYER", str(r["player_id"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", r["source_id"], r["verification_status"],
                ))

    elif subject_type == "SCHOOL":
        # Controlled reverse traversal: school -> nearby players with verified
        # game-log rows, plus the existing ranking-history edges below.
        if "cfb_player_game_stats_real" in tables:
            if season_hint is not None:
                rows = conn.execute(
                    """SELECT cfb_player_id,MIN(season) season,MIN(source_id) source_id
                       FROM cfb_player_game_stats_real
                       WHERE school_id=? AND verification_status='SOURCE_BACKED_DERIVED'
                         AND cfb_player_id IS NOT NULL AND source_id IS NOT NULL
                         AND season BETWEEN ? AND ?
                       GROUP BY cfb_player_id
                       ORDER BY ABS(MIN(season)-?),cfb_player_id
                       LIMIT 12""",
                    (sid, int(season_hint)-2, int(season_hint)+2, int(season_hint)),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT cfb_player_id,MAX(season) season,MIN(source_id) source_id
                       FROM cfb_player_game_stats_real
                       WHERE school_id=? AND verification_status='SOURCE_BACKED_DERIVED'
                         AND cfb_player_id IS NOT NULL AND source_id IS NOT NULL
                       GROUP BY cfb_player_id
                       ORDER BY MAX(season) DESC,cfb_player_id
                       LIMIT 10""",
                    (sid,),
                ).fetchall()
            for r in rows:
                out.append(LoreHop(
                    "SCHOOL_PLAYER", "SCHOOL", sid, "CFB_PLAYER", str(r["cfb_player_id"]),
                    int(r["season"]) if r["season"] is not None else None,
                    "STRUCTURED_FACT", str(r["source_id"]), "SOURCE_BACKED_DERIVED",
                ))

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


def _neighbors(conn, node_type, node_id, *, season_hint=None):
    if node_type == "EVENT":
        return _event_subject_edges(conn, node_id)
    out = _event_edges(conn, node_type, node_id)
    out.extend(_structured_edges(conn, node_type, node_id, season_hint=season_hint))
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

        season_hint = hops[-1].season if hops else None
        for hop in _neighbors(conn, node_type, node_id, season_hint=season_hint):
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


def compile_lore_chain_question(conn, chain, *, difficulty_band="HARD", variant=0):
    """Compile a discovered mixed-source chain into human-sounding deep trivia."""
    if not chain.gameplay_eligible or not chain.provenance_complete:
        raise ValueError("CHAIN_NOT_GAMEPLAY_ELIGIBLE")
    if chain.depth < 3:
        raise ValueError("CHAIN_TOO_SHALLOW")
    if chain.anchor_type not in {"NFL_PLAYER", "CFB_PLAYER", "COACH"}:
        raise ValueError("NATURAL_COPY_UNSUPPORTED_ANCHOR")

    raw_clues = render_chain_clues(conn, chain)
    clues = select_clues(raw_clues, difficulty_band, variant=variant)
    quality = writer_quality(clues)
    if quality["status"] != "PASSED":
        raise ValueError("WRITER_QA_FAILED:" + ",".join(quality["errors"]))

    answer = str(chain.anchor_id)
    answer_label = resolve_required_label(conn, chain.anchor_type, answer)

    combined = " ".join(c["text"] for c in clues).casefold()
    if answer_label and answer_label.casefold() in combined:
        raise ValueError("CHAIN_ANSWER_LEAKAGE")

    qid = variant_id(chain.chain_id, difficulty_band, variant, clues)
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "THREE_CLUES",
        "question_family": "DEEP_LORE_CHAIN",
        "question": question_stem(chain.anchor_type),
        "clues": clues,
        "answer": {"id": answer, "label": answer_label, "type": chain.anchor_type},
        "chain_id": chain.chain_id,
        "depth": chain.depth,
        "rarity_score": chain.rarity_score,
        "difficulty_score": chain.difficulty_score,
        "difficulty_band": str(difficulty_band).upper(),
        "variant": int(variant),
        "writer_quality": quality,
        "provenance": {
            "provenance_complete": chain.provenance_complete,
            "chain": chain_payload(chain),
        },
    }


def compile_lore_chain_variants(conn, chain, *, bands=("CASUAL", "HARD", "SICKO"), variants_per_band=2):
    """Generate multiple deterministic, non-identical presentations of one chain."""
    out = []
    seen = set()
    for band in bands:
        for variant in range(max(1, int(variants_per_band))):
            try:
                question = compile_lore_chain_question(
                    conn, chain, difficulty_band=band, variant=variant
                )
            except ValueError:
                continue
            signature = tuple(c["text"] for c in question["clues"])
            if signature in seen:
                continue
            seen.add(signature)
            out.append(question)
    return out


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
    relation_counts = defaultdict(int)
    anchor_type_counts = defaultdict(int)
    cross_entity_chains = 0
    for row in rows:
        chains = discover_lore_chains(
            conn, row["subject_type"], row["subject_id"],
            max_depth=max_depth, max_chains=20,
        )
        total += len(chains)
        for chain in chains:
            counts[f"depth_{chain.depth}"] += 1
            anchor_type_counts[chain.anchor_type] += 1
            for hop in chain.hops:
                relation_counts[hop.relation] += 1
            if any(h.relation in {"DRAFTED_PLAYER","ROSTERED_PLAYER","SCHOOL_PLAYER","TEAM_COACH"} for h in chain.hops):
                cross_entity_chains += 1
            if chain.source_diversity >= 2:
                counts["mixed_source"] += 1
            try:
                variants = compile_lore_chain_variants(conn, chain, variants_per_band=2)
                if not variants:
                    raise ValueError("NO_HUMAN_VARIANTS")
                question = variants[0]
                human_playable += len(variants)
                counts["human_playable"] += len(variants)
                for variant_question in variants:
                    counts["band_" + variant_question["difficulty_band"]] += 1
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
        "relation_counts": dict(relation_counts),
        "anchor_type_counts": dict(anchor_type_counts),
        "cross_entity_chains": cross_entity_chains,
        "human_playable_rate": round(human_playable / max(1, total), 4),
        "label_rejections": sum(
            n for reason, n in rejects.items()
            if reason.startswith("UNRESOLVED_ENTITY_LABEL")
        ),
        "examples": examples,
    }
