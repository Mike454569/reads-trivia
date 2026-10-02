"""Compile verified universal lore events into gameplay-ready trivia.

This is intentionally parallel to relationship-chain trivia. Event questions need
different provenance, sensitivity, ambiguity and distractor rules.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict

SENSITIVE_TYPES = {
    "INJURY", "SUSPENSION", "FINE", "DISCIPLINE", "LEAGUE_DISCIPLINE",
    "LEGAL_EVENT", "ARREST", "CHARGE", "CONVICTION", "ACQUITTAL",
    "DISMISSAL", "INVESTIGATION", "CONTROVERSY",
}
LEGAL_TYPES = {
    "LEGAL_EVENT", "ARREST", "CHARGE", "CONVICTION",
    "ACQUITTAL", "DISMISSAL", "INVESTIGATION",
}
PLAYABLE_DIMENSIONS = {"TEAM", "SEASON", "EVENT_TYPE"}

def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def _humanize(value):
    return str(value or "").replace("_", " ").strip().title()

def _season(event_date):
    raw = str(event_date or "")
    if len(raw) >= 4 and raw[:4].isdigit():
        return raw[:4]
    return None

def _evidence(conn, event_id):
    return [dict(r) for r in conn.execute(
        """SELECT source_url,publisher,published_date,evidence_tier,supports_fields_json
           FROM universal_event_evidence WHERE event_id=? ORDER BY evidence_tier,source_url""",
        (event_id,),
    )]

def _subjects(conn, event_id):
    return [dict(r) for r in conn.execute(
        """SELECT subject_type,subject_id,role FROM universal_event_subject
           WHERE event_id=? ORDER BY subject_type,subject_id,role""",
        (event_id,),
    )]

def gameplay_eligibility(conn, event):
    """Fail-closed eligibility for turning an event into public trivia."""
    reasons = []
    if str(event.get("verification_status") or "").upper() != "VERIFIED":
        reasons.append("NOT_VERIFIED")

    evidence = _evidence(conn, event["event_id"])
    if not evidence:
        reasons.append("NO_EVIDENCE")

    sensitive = bool(event.get("sensitive")) or str(event.get("event_type") or "").upper() in SENSITIVE_TYPES
    tiers = {str(e.get("evidence_tier") or "").upper() for e in evidence}
    if sensitive:
        # Sensitive trivia needs corroboration, or a primary/authoritative source.
        strong = bool(tiers & {"PRIMARY", "AUTHORITATIVE"})
        if not strong and len({e["source_url"] for e in evidence}) < 2:
            reasons.append("SENSITIVE_NEEDS_CORROBORATION")
        if "SECONDARY" in tiers:
            reasons.append("SENSITIVE_SECONDARY_EVIDENCE")

    typ = str(event.get("event_type") or "").upper()
    if typ in LEGAL_TYPES:
        if not str(event.get("legal_stage") or "").strip():
            reasons.append("LEGAL_STAGE_MISSING")
        if typ not in {"ACQUITTAL", "DISMISSAL", "INVESTIGATION"} and not str(event.get("allegation_or_offense") or "").strip():
            reasons.append("LEGAL_OFFENSE_MISSING")
        if not str(event.get("jurisdiction") or "").strip():
            reasons.append("LEGAL_JURISDICTION_MISSING")

    return {
        "eligible": not reasons,
        "reasons": reasons,
        "evidence_count": len(evidence),
        "sensitive": sensitive,
    }

def _safe_clues(event):
    typ = str(event.get("event_type") or "").upper()
    clues = []

    # Neutral summaries are already validated at ingestion. Legal events get
    # structured language so an allegation is never rewritten as guilt.
    if typ in LEGAL_TYPES:
        stage = _humanize(event.get("legal_stage"))
        if stage:
            clues.append("Recorded legal stage: " + stage + ".")
        offense = str(event.get("allegation_or_offense") or "").strip()
        if offense:
            clues.append("Reported allegation or offense: " + offense + ".")
        jurisdiction = str(event.get("jurisdiction") or "").strip()
        if jurisdiction:
            clues.append("Jurisdiction: " + jurisdiction + ".")
        disposition = str(event.get("disposition") or "").strip()
        if disposition:
            clues.append("Recorded disposition: " + disposition + ".")
    else:
        summary = str(event.get("neutral_summary") or "").strip()
        if summary:
            clues.append(summary)
        title = str(event.get("title") or "").strip()
        if title and title.casefold() not in summary.casefold():
            clues.append("Event label: " + title + ".")

    season = _season(event.get("event_date"))
    if season:
        clues.append("Season: " + season + ".")
    league = str(event.get("league") or "").strip()
    if league:
        clues.append("League: " + league + ".")

    # Preserve order while removing duplicates.
    out = []
    seen = set()
    for clue in clues:
        key = clue.casefold()
        if key not in seen:
            seen.add(key)
            out.append(clue)
    return out

def _qid(event_id, dimension, answer_id, clues):
    seed = "|".join([str(event_id), dimension, str(answer_id)] + clues)
    return "qlore_" + hashlib.sha256(seed.encode()).hexdigest()[:24]

def _candidate_team_subjects(subjects):
    return [s for s in subjects if s["subject_type"] in {"NFL_TEAM", "SCHOOL"}]

def _team_distractors(conn, correct, league, limit=3):
    subject_type = correct["subject_type"]
    rows = conn.execute(
        """SELECT DISTINCT s.subject_id
           FROM universal_event_subject s
           JOIN universal_event e ON e.event_id=s.event_id
           WHERE s.subject_type=? AND s.subject_id<>?
             AND e.verification_status='VERIFIED'
             AND (? IS NULL OR e.league=?)
           ORDER BY s.subject_id LIMIT ?""",
        (subject_type, correct["subject_id"], league, league, limit),
    ).fetchall()
    return [str(r[0]) for r in rows]

def _season_distractors(conn, correct, league, limit=3):
    rows = conn.execute(
        """SELECT DISTINCT substr(event_date,1,4) season
           FROM universal_event
           WHERE verification_status='VERIFIED'
             AND event_date IS NOT NULL
             AND substr(event_date,1,4)<>?
             AND (? IS NULL OR league=?)
           ORDER BY ABS(CAST(substr(event_date,1,4) AS INTEGER)-CAST(? AS INTEGER)),season
           LIMIT ?""",
        (correct, league, league, correct, limit),
    ).fetchall()
    return [str(r[0]) for r in rows if r[0]]

def _type_distractors(conn, correct, league, limit=3):
    rows = conn.execute(
        """SELECT DISTINCT event_type FROM universal_event
           WHERE verification_status='VERIFIED'
             AND event_type<>?
             AND (? IS NULL OR league=?)
           ORDER BY event_type LIMIT ?""",
        (correct, league, league, limit),
    ).fetchall()
    return [str(r[0]) for r in rows]

def compile_event_question(conn, event_id, dimension, *, recent_question_ids=()):
    """Compile one verified event into a deterministic gameplay question."""
    dimension = str(dimension).upper()
    if dimension not in PLAYABLE_DIMENSIONS:
        raise ValueError("UNSUPPORTED_LORE_DIMENSION")

    row = conn.execute("SELECT * FROM universal_event WHERE event_id=?", (event_id,)).fetchone()
    if not row:
        raise ValueError("UNKNOWN_EVENT")
    event = dict(row)

    gate = gameplay_eligibility(conn, event)
    if not gate["eligible"]:
        raise ValueError("LORE_NOT_GAMEPLAY_ELIGIBLE:" + ",".join(gate["reasons"]))

    subjects = _subjects(conn, event_id)
    clues = _safe_clues(event)
    league = event.get("league")

    if dimension == "TEAM":
        candidates = _candidate_team_subjects(subjects)
        if len(candidates) != 1:
            raise ValueError("AMBIGUOUS_TEAM_ANSWER")
        correct = candidates[0]
        answer_id = str(correct["subject_id"])
        answer_label = answer_id
        distractors = _team_distractors(conn, correct, league)
        question = "Which team or school is the verified subject of this football event?"
        answer_type = correct["subject_type"]
    elif dimension == "SEASON":
        answer_id = _season(event.get("event_date"))
        if not answer_id:
            raise ValueError("MISSING_EVENT_SEASON")
        answer_label = answer_id
        distractors = _season_distractors(conn, answer_id, league)
        question = "In which season did this verified football event occur?"
        answer_type = "SEASON"
        clues = [c for c in clues if not c.startswith("Season: ")]
    else:
        answer_id = str(event.get("event_type") or "")
        if not answer_id:
            raise ValueError("MISSING_EVENT_TYPE")
        answer_label = _humanize(answer_id)
        distractor_ids = _type_distractors(conn, answer_id, league)
        distractors = [_humanize(x) for x in distractor_ids]
        question = "What type of verified football event do these clues describe?"
        answer_type = "EVENT_TYPE"

    if len(clues) < 2:
        raise ValueError("INSUFFICIENT_LORE_CLUES")
    if len(distractors) < 3:
        raise ValueError("INSUFFICIENT_LORE_DISTRACTORS")

    qid = _qid(event_id, dimension, answer_id, clues)
    if qid in {str(x) for x in recent_question_ids}:
        raise ValueError("RECENT_QUESTION_REPEAT")

    options = [answer_label] + distractors[:3]
    if len({str(x).casefold() for x in options}) != 4:
        raise ValueError("DUPLICATE_LORE_OPTIONS")

    return {
        "contract_version": "1.0.0",
        "question_id": qid,
        "mechanic": "MULTIPLE_CHOICE",
        "question_family": "LORE_EVENT",
        "dimension": dimension,
        "question": question,
        "clues": clues,
        "answer": {"id": answer_id, "label": answer_label, "type": answer_type},
        "options": options,
        "explanation": " ".join(clues),
        "event_id": event_id,
        "sensitive": gate["sensitive"],
        "provenance": {
            "provenance_complete": True,
            "event_id": event_id,
            "evidence": _evidence(conn, event_id),
            "verification_status": event.get("verification_status"),
        },
    }

def iter_playable_event_questions(conn, *, dimensions=("TEAM", "SEASON", "EVENT_TYPE"), limit=None):
    """Yield playable lore questions, skipping ambiguous/under-sourced events."""
    sql = "SELECT event_id FROM universal_event WHERE verification_status='VERIFIED' ORDER BY event_date,event_id"
    if limit is not None:
        sql += " LIMIT " + str(max(1, int(limit)))
    for row in conn.execute(sql):
        for dimension in dimensions:
            try:
                yield compile_event_question(conn, row["event_id"], dimension)
            except ValueError:
                continue

def lore_gameplay_report(conn, *, limit_events=None):
    questions = 0
    by_dimension = defaultdict(int)
    eligible_events = 0
    rejected = defaultdict(int)

    sql = "SELECT * FROM universal_event WHERE verification_status='VERIFIED' ORDER BY event_date,event_id"
    if limit_events is not None:
        sql += " LIMIT " + str(max(1, int(limit_events)))
    rows = [dict(r) for r in conn.execute(sql)]

    for event in rows:
        gate = gameplay_eligibility(conn, event)
        if gate["eligible"]:
            eligible_events += 1
        else:
            for reason in gate["reasons"]:
                rejected[reason] += 1
            continue
        for dimension in PLAYABLE_DIMENSIONS:
            try:
                compile_event_question(conn, event["event_id"], dimension)
                questions += 1
                by_dimension[dimension] += 1
            except ValueError as exc:
                rejected[str(exc).split(":")[0]] += 1

    return {
        "events_scanned": len(rows),
        "eligible_events": eligible_events,
        "playable_questions": questions,
        "by_dimension": dict(by_dimension),
        "rejections": dict(rejected),
    }
