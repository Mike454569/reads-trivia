"""Chain-aware uniqueness checks for deep-lore multiple-choice answers."""
from __future__ import annotations


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _event_subject(conn, event_id, answer_type, candidate_id):
    row = conn.execute(
        """SELECT 1 FROM universal_event_subject
           WHERE event_id=? AND subject_type=? AND subject_id=? LIMIT 1""",
        (str(event_id), str(answer_type), str(candidate_id)),
    ).fetchone()
    return row is not None


def _structured_match(conn, answer_type, candidate_id, hop):
    tables = _tables(conn)
    relation = str(hop.get("relation") or "")
    obj = str(hop.get("object_id") or "")
    season = hop.get("season")
    sid = str(candidate_id)

    if answer_type == "NFL_PLAYER":
        if relation == "DRAFTED_BY" and "draft_facts" in tables:
            q = """SELECT 1 FROM draft_facts
                   WHERE player_key=? AND draft_team=?
                     AND verification_status='SOURCE_BACKED'"""
            args = [sid, obj]
            if season is not None:
                q += " AND draft_season=?"
                args.append(int(season))
            return conn.execute(q + " LIMIT 1", args).fetchone() is not None

        if relation == "ROSTERED_BY" and "canonical_roster_seasons" in tables:
            q = """SELECT 1 FROM canonical_roster_seasons
                   WHERE player_id=? AND team_code=?
                     AND verification_status='SOURCE_BACKED'"""
            args = [sid, obj]
            if season is not None:
                q += " AND season=?"
                args.append(int(season))
            return conn.execute(q + " LIMIT 1", args).fetchone() is not None

        if relation == "ALL_PRO" and "nfl_all_pro_selections" in tables:
            q = """SELECT 1 FROM nfl_all_pro_selections
                   WHERE player_id=? AND honor_level=? AND is_ap=1
                     AND verification_status='WIKIPEDIA_STRUCTURED_SECONDARY'"""
            args = [sid, obj]
            if season is not None:
                q += " AND season=?"
                args.append(int(season))
            return conn.execute(q + " LIMIT 1", args).fetchone() is not None

        if relation == "PRO_BOWL" and "nfl_pro_bowl_selections" in tables:
            q = """SELECT 1 FROM nfl_pro_bowl_selections
                   WHERE player_id=?
                     AND verification_status='WIKIPEDIA_STRUCTURED_SECONDARY'"""
            args = [sid]
            if season is not None:
                q += " AND season=?"
                args.append(int(season))
            return conn.execute(q + " LIMIT 1", args).fetchone() is not None

    if answer_type == "CFB_PLAYER":
        if relation in {"STARTED_AT", "TRANSFERRED_TO"} and "cfb_transfer_summary" in tables:
            col = "first_school_id" if relation == "STARTED_AT" else "last_school_id"
            season_col = "first_season" if relation == "STARTED_AT" else "last_season"
            q = "SELECT 1 FROM cfb_transfer_summary WHERE cfb_player_id=? AND " + col + "=?"
            args = [sid, obj]
            if season is not None:
                q += " AND " + season_col + "=?"
                args.append(int(season))
            return conn.execute(q + " LIMIT 1", args).fetchone() is not None

    if answer_type == "COACH":
        if relation == "COACHED" and "coach_team_seasons" in tables:
            q = """SELECT 1 FROM coach_team_seasons
                   WHERE coach_id=? AND team_code=?
                     AND verification_status='SOURCE_BACKED'"""
            args = [sid, obj]
            if season is not None:
                q += " AND season=?"
                args.append(int(season))
            return conn.execute(q + " LIMIT 1", args).fetchone() is not None

    return False


def clue_fit_report(conn, question, candidate_id):
    """Measure whether a candidate also satisfies the exact facts shown to the user."""
    chain = ((question.get("provenance") or {}).get("chain") or {})
    hops = chain.get("hops") or []
    selected_relations = [str(c.get("relation") or "") for c in question.get("clues") or []]
    answer_type = str((question.get("answer") or {}).get("type") or "")

    checks = []
    used = set()
    for relation in selected_relations:
        for i, hop in enumerate(hops):
            if i in used or str(hop.get("relation") or "") != relation:
                continue
            used.add(i)
            if relation == "SUBJECT_OF_EVENT":
                matched = _event_subject(
                    conn, hop.get("object_id"), answer_type, candidate_id
                )
            else:
                matched = _structured_match(conn, answer_type, candidate_id, hop)
            checks.append({
                "relation": relation,
                "matched": bool(matched),
                "object_id": hop.get("object_id"),
                "season": hop.get("season"),
            })
            break

    matched = sum(1 for x in checks if x["matched"])
    return {
        "candidate_id": str(candidate_id),
        "checked_clues": len(checks),
        "matched_clues": matched,
        "all_checked_clues_match": bool(checks) and matched == len(checks),
        "checks": checks,
    }


def filter_ambiguous_distractors(conn, question, distractors, *, k=3):
    """Remove any distractor that satisfies every checkable clue."""
    out = []
    rejected = []
    for candidate in distractors:
        report = clue_fit_report(conn, question, candidate["entity_id"])
        if report["all_checked_clues_match"]:
            rejected.append({
                "entity_id": candidate["entity_id"],
                "reason": "DISTRACTOR_FITS_ALL_CLUES",
                "fit": report,
            })
            continue
        item = dict(candidate)
        item["clue_fit"] = report
        out.append(item)
        if len(out) >= k:
            break
    return out, rejected
