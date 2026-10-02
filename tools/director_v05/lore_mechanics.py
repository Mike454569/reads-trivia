"""Advanced gameplay mechanics backed by verified universal football lore."""
from __future__ import annotations

import hashlib
from collections import defaultdict

from .lore_trivia import (
    _evidence, _safe_clues, _season, _subjects, gameplay_eligibility,
)

IDENTITY_TYPES = {"NFL_PLAYER", "CFB_PLAYER", "COACH"}
COMMON_LINK_TYPES = {"NFL_PLAYER", "CFB_PLAYER", "COACH", "NFL_TEAM", "SCHOOL"}


def _qid(mechanic, parts):
    seed = "|".join([mechanic] + [str(x) for x in parts])
    return "qlorex_" + hashlib.sha256(seed.encode()).hexdigest()[:24]


def _event(conn, event_id):
    row = conn.execute("SELECT * FROM universal_event WHERE event_id=?", (event_id,)).fetchone()
    if not row:
        raise ValueError("UNKNOWN_EVENT")
    event = dict(row)
    gate = gameplay_eligibility(conn, event)
    if not gate["eligible"]:
        raise ValueError("LORE_NOT_GAMEPLAY_ELIGIBLE:" + ",".join(gate["reasons"]))
    return event, gate


def _prov(conn, event_ids):
    evidence = []
    for event_id in event_ids:
        evidence.extend({"event_id": event_id, **row} for row in _evidence(conn, event_id))
    return {
        "provenance_complete": bool(evidence),
        "event_ids": list(event_ids),
        "evidence": evidence,
    }


def _identity_subject(subjects):
    candidates = [s for s in subjects if s["subject_type"] in IDENTITY_TYPES]
    unique = {(s["subject_type"], str(s["subject_id"])) for s in candidates}
    if len(unique) != 1:
        raise ValueError("AMBIGUOUS_IDENTITY_ANSWER")
    typ, sid = next(iter(unique))
    return {"subject_type": typ, "subject_id": sid}


def compile_progressive_identity(conn, event_id):
    """Turn one event into a progressive Who Am I / Three Clues contract."""
    event, gate = _event(conn, event_id)
    identity = _identity_subject(_subjects(conn, event_id))
    clues = _safe_clues(event)
    if len(clues) < 3:
        raise ValueError("INSUFFICIENT_PROGRESSIVE_CLUES")

    # Reveal broad context first, event-specific detail last.
    broad = [c for c in clues if c.startswith("League: ") or c.startswith("Season: ")]
    specific = [c for c in clues if c not in broad]
    ordered = broad + specific
    if len(ordered) < 3:
        raise ValueError("INSUFFICIENT_PROGRESSIVE_CLUES")

    qid = _qid("PROGRESSIVE_IDENTITY", [event_id, identity["subject_type"], identity["subject_id"]] + ordered)
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "PROGRESSIVE_CLUE",
        "question_family": "LORE_IDENTITY",
        "question": "Who am I?",
        "clues": [{"step": i + 1, "text": clue} for i, clue in enumerate(ordered)],
        "answer": {
            "id": identity["subject_id"],
            "label": identity["subject_id"],
            "type": identity["subject_type"],
        },
        "event_id": event_id,
        "sensitive": gate["sensitive"],
        "provenance": _prov(conn, [event_id]),
    }


def compile_fact_or_fake(conn, event_id, *, fake=False):
    """Emit a sourced statement. Fake variants alter a structural fact, never legal wording."""
    event, gate = _event(conn, event_id)
    if gate["sensitive"] and fake:
        raise ValueError("NO_FAKE_VARIANTS_FOR_SENSITIVE_LORE")

    clues = _safe_clues(event)
    if len(clues) < 2:
        raise ValueError("INSUFFICIENT_LORE_CLUES")

    season = _season(event.get("event_date"))
    typ = str(event.get("event_type") or "")
    if fake:
        if season:
            wrong = str(int(season) + 1)
            statement = "This verified football event occurred in the " + wrong + " season."
            mutation = {"field": "season", "actual": season, "shown": wrong}
        elif typ:
            statement = "This event was classified as a Trade."
            mutation = {"field": "event_type", "actual": typ, "shown": "TRADE"}
            if typ == "TRADE":
                statement = "This event was classified as a Contract."
                mutation["shown"] = "CONTRACT"
        else:
            raise ValueError("NO_SAFE_FAKE_MUTATION")
        answer = False
    else:
        statement = clues[0]
        mutation = None
        answer = True

    qid = _qid("FACT_OR_FAKE", [event_id, str(fake), statement])
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "FACT_OR_FAKE",
        "question_family": "LORE_EVENT",
        "question": statement,
        "context_clues": clues[1:],
        "answer": {"id": "FACT" if answer else "FAKE", "label": "Fact" if answer else "Fake", "type": "BOOLEAN"},
        "mutation": mutation,
        "event_id": event_id,
        "sensitive": gate["sensitive"],
        "provenance": _prov(conn, [event_id]),
    }


def compile_timeline(conn, event_ids):
    """Order four or more verified lore events by season."""
    ids = [str(x) for x in event_ids]
    if len(ids) < 4:
        raise ValueError("TIMELINE_NEEDS_FOUR_EVENTS")
    rows = []
    for event_id in ids:
        event, _ = _event(conn, event_id)
        season = _season(event.get("event_date"))
        if not season:
            raise ValueError("TIMELINE_EVENT_MISSING_SEASON")
        rows.append((event_id, int(season), str(event.get("title") or event_id)))
    seasons = [r[1] for r in rows]
    if len(set(seasons)) != len(seasons):
        raise ValueError("TIMELINE_REQUIRES_UNIQUE_SEASONS")

    chronological = sorted(rows, key=lambda r: (r[1], r[0]))
    qid = _qid("TIMELINE", [x[0] for x in chronological])
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "SORTING_TIMELINE",
        "question_family": "LORE_TIMELINE",
        "question": "Put these verified football events in chronological order.",
        "items": [{"id": event_id, "label": title} for event_id, _, title in rows],
        "answer_order": [event_id for event_id, _, _ in chronological],
        "explanation": [{"event_id": event_id, "season": season} for event_id, season, _ in chronological],
        "provenance": _prov(conn, ids),
    }


def compile_matching(conn, event_ids):
    """Match verified event descriptions to their unique player/team/coach subject."""
    ids = [str(x) for x in event_ids]
    if len(ids) < 3:
        raise ValueError("MATCHING_NEEDS_THREE_EVENTS")

    pairs = []
    seen_answers = set()
    for event_id in ids:
        event, _ = _event(conn, event_id)
        subjects = [s for s in _subjects(conn, event_id) if s["subject_type"] in COMMON_LINK_TYPES]
        unique = {(s["subject_type"], str(s["subject_id"])) for s in subjects}
        if len(unique) != 1:
            raise ValueError("MATCHING_EVENT_AMBIGUOUS_SUBJECT")
        subject_type, subject_id = next(iter(unique))
        if (subject_type, subject_id) in seen_answers:
            raise ValueError("MATCHING_DUPLICATE_ANSWER")
        seen_answers.add((subject_type, subject_id))
        clues = _safe_clues(event)
        if not clues:
            raise ValueError("MATCHING_EVENT_NO_CLUE")
        pairs.append({
            "event_id": event_id,
            "prompt": clues[0],
            "answer_id": subject_id,
            "answer_label": subject_id,
            "answer_type": subject_type,
        })

    qid = _qid("MATCHING", ids + [p["answer_id"] for p in pairs])
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "MATCHING",
        "question_family": "LORE_MATCHING",
        "question": "Match each verified football event to its subject.",
        "prompts": [{"id": p["event_id"], "text": p["prompt"]} for p in pairs],
        "answers": [{"id": p["answer_id"], "label": p["answer_label"], "type": p["answer_type"]} for p in pairs],
        "solution": {p["event_id"]: p["answer_id"] for p in pairs},
        "provenance": _prov(conn, ids),
    }


def compile_common_link(conn, subject_type, subject_id, *, min_events=3, limit=5):
    """Build a common-link question from several verified events sharing one subject."""
    subject_type = str(subject_type)
    subject_id = str(subject_id)
    if subject_type not in COMMON_LINK_TYPES:
        raise ValueError("UNSUPPORTED_COMMON_LINK_SUBJECT")

    rows = conn.execute(
        """SELECT e.event_id
           FROM universal_event e
           JOIN universal_event_subject s ON s.event_id=e.event_id
           WHERE s.subject_type=? AND s.subject_id=?
             AND e.verification_status='VERIFIED'
           ORDER BY e.event_date,e.event_id""",
        (subject_type, subject_id),
    ).fetchall()

    clues = []
    event_ids = []
    for row in rows:
        event_id = str(row["event_id"])
        try:
            event, _ = _event(conn, event_id)
        except ValueError:
            continue
        safe = _safe_clues(event)
        if not safe:
            continue
        clues.append(safe[0])
        event_ids.append(event_id)
        if len(clues) >= limit:
            break

    if len(clues) < min_events:
        raise ValueError("INSUFFICIENT_COMMON_LINK_EVENTS")

    qid = _qid("COMMON_LINK", [subject_type, subject_id] + event_ids)
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "COMMON_LINK",
        "question_family": "LORE_COMMON_LINK",
        "question": "What football subject connects all of these verified events?",
        "clues": clues,
        "answer": {"id": subject_id, "label": subject_id, "type": subject_type},
        "event_ids": event_ids,
        "provenance": _prov(conn, event_ids),
    }


def _stat_fact_for_subject(conn, subject):
    """Return one source-backed structured football fact for mixed lore+stat play."""
    typ = subject["subject_type"]
    sid = str(subject["subject_id"])

    if typ == "NFL_PLAYER":
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "draft_facts" in tables:
            row = conn.execute(
                """SELECT draft_season,draft_round,draft_pick_overall,draft_team,verification_status
                   FROM draft_facts
                   WHERE player_key=? AND verification_status='SOURCE_BACKED'
                   ORDER BY draft_season LIMIT 1""",
                (sid,),
            ).fetchone()
            if row:
                return {
                    "kind": "DRAFT",
                    "text": "Drafted in " + str(row["draft_season"]) +
                            " in round " + str(row["draft_round"]) +
                            " with pick " + str(row["draft_pick_overall"]) + ".",
                }

    if typ == "CFB_PLAYER":
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "cfb_player_game_stats_real" in tables:
            row = conn.execute(
                """SELECT season,MAX(COALESCE(passing_yards,0)+COALESCE(rushing_yards,0)+COALESCE(receiving_yards,0)) total
                   FROM cfb_player_game_stats_real
                   WHERE cfb_player_id=? AND verification_status='SOURCE_BACKED_DERIVED'
                   GROUP BY season ORDER BY total DESC,season DESC LIMIT 1""",
                (sid,),
            ).fetchone()
            if row:
                return {
                    "kind": "GAME_STAT",
                    "text": "Had a recorded single-game combined yardage high of " + str(int(row["total"] or 0)) +
                            " in the " + str(row["season"]) + " season.",
                }

    return None


def compile_mixed_lore_stat(conn, event_id):
    """Combine one verified lore event with one independent structured stat/fact."""
    event, gate = _event(conn, event_id)
    if gate["sensitive"]:
        raise ValueError("SENSITIVE_LORE_EXCLUDED_FROM_MIXED_STAT")
    identity = _identity_subject(_subjects(conn, event_id))
    stat = _stat_fact_for_subject(conn, identity)
    if not stat:
        raise ValueError("NO_STRUCTURED_STAT_FOR_LORE_SUBJECT")

    lore = _safe_clues(event)
    if not lore:
        raise ValueError("INSUFFICIENT_LORE_CLUES")
    clues = [lore[0], stat["text"]]
    qid = _qid("MIXED_LORE_STAT", [event_id, identity["subject_id"], stat["kind"]] + clues)
    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "THREE_CLUES",
        "question_family": "MIXED_LORE_STAT",
        "question": "Which football player matches both the verified story and the structured football fact?",
        "clues": clues,
        "answer": {"id": identity["subject_id"], "label": identity["subject_id"], "type": identity["subject_type"]},
        "event_id": event_id,
        "structured_fact_kind": stat["kind"],
        "provenance": _prov(conn, [event_id]),
    }


def advanced_lore_report(conn, *, limit_events=1000):
    """Measure how much of the lore corpus can power advanced mechanics."""
    counts = defaultdict(int)
    rejects = defaultdict(int)
    rows = conn.execute(
        """SELECT event_id FROM universal_event
           WHERE verification_status='VERIFIED'
           ORDER BY event_date,event_id LIMIT ?""",
        (int(limit_events),),
    ).fetchall()

    eligible_ids = []
    for row in rows:
        event_id = str(row["event_id"])
        eligible_ids.append(event_id)
        for name, fn in (
            ("PROGRESSIVE_CLUE", compile_progressive_identity),
            ("FACT_OR_FAKE", compile_fact_or_fake),
            ("MIXED_LORE_STAT", compile_mixed_lore_stat),
        ):
            try:
                fn(conn, event_id)
                counts[name] += 1
            except ValueError as exc:
                rejects[name + ":" + str(exc).split(":")[0]] += 1

    # Bundle mechanics are sampled from the same verified pool.
    for i in range(0, len(eligible_ids) - 3, 4):
        group = eligible_ids[i:i+4]
        try:
            compile_timeline(conn, group)
            counts["SORTING_TIMELINE"] += 1
        except ValueError as exc:
            rejects["SORTING_TIMELINE:" + str(exc).split(":")[0]] += 1
        try:
            compile_matching(conn, group)
            counts["MATCHING"] += 1
        except ValueError as exc:
            rejects["MATCHING:" + str(exc).split(":")[0]] += 1

    subjects = conn.execute(
        """SELECT subject_type,subject_id,COUNT(DISTINCT event_id) n
           FROM universal_event_subject
           WHERE subject_type IN ('NFL_PLAYER','CFB_PLAYER','COACH','NFL_TEAM','SCHOOL')
           GROUP BY subject_type,subject_id HAVING n>=3
           ORDER BY n DESC,subject_type,subject_id LIMIT 250"""
    ).fetchall()
    for row in subjects:
        try:
            compile_common_link(conn, row["subject_type"], row["subject_id"])
            counts["COMMON_LINK"] += 1
        except ValueError as exc:
            rejects["COMMON_LINK:" + str(exc).split(":")[0]] += 1

    return {
        "events_scanned": len(rows),
        "playable_by_mechanic": dict(counts),
        "rejections": dict(rejects),
    }
