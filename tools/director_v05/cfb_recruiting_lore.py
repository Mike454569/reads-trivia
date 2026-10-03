"""Mine source-backed CFBD recruiting rows into universal RECRUITING lore."""
from __future__ import annotations

import hashlib

from .event_ingest import upsert_event

SOURCE_URL = "https://api.collegefootballdata.com/recruiting/players"
SOURCE_PUBLISHER = "CollegeFootballData.com recruiting"


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def mine_cfb_recruiting_lore(conn, *, limit_rows=None):
    if "cfb_recruits" not in _tables(conn):
        return {"events": 0, "reason": "missing_table"}

    rows = conn.execute(
        """SELECT recruit_id,cfb_player_id,class_year,recruit_type,ranking,recruit_name,
                  high_school,committed_school_id,committed_school_name,position,stars,rating,
                  source_id,verification_status
           FROM cfb_recruits
           WHERE source_id='CFBD_API_LIVE'
             AND verification_status='SOURCE_BACKED'
             AND committed_school_id IS NOT NULL
           ORDER BY class_year,ranking,recruit_id"""
    ).fetchall()

    inserted = 0
    for index, row in enumerate(rows):
        if limit_rows and index >= int(limit_rows):
            break

        details = []
        if row["stars"] is not None:
            details.append(str(int(row["stars"])) + "-star")
        if row["ranking"] is not None:
            details.append("No. " + str(int(row["ranking"])) + " overall")
        if row["rating"] is not None:
            details.append("rating " + str(round(float(row["rating"]), 4)))
        if row["position"]:
            details.append(str(row["position"]))

        summary = str(row["recruit_name"]) + " committed to " + str(row["committed_school_name"])
        if details:
            summary += " as a " + ", ".join(details)
        summary += " recruit in the " + str(row["class_year"]) + " class."

        subjects = [{
            "subject_type": "SCHOOL",
            "subject_id": str(row["committed_school_id"]),
            "role": "commitment",
        }]
        if row["cfb_player_id"]:
            subjects.append({
                "subject_type": "CFB_PLAYER",
                "subject_id": str(row["cfb_player_id"]),
                "role": "recruit",
            })

        event_id = "evt_recruit_" + hashlib.sha256(
            ("CFBD_API_LIVE|" + str(row["recruit_id"])).encode()
        ).hexdigest()[:20]

        upsert_event(conn, {
            "event_id": event_id,
            "event_type": "RECRUITING",
            "league": "CFB",
            "event_date": str(row["class_year"]) + "-01-01",
            "title": str(row["recruit_name"]) + " commitment to " + str(row["committed_school_name"]),
            "neutral_summary": summary,
            "source_url": SOURCE_URL,
            "source_publisher": SOURCE_PUBLISHER,
            "evidence_tier": "AUTHORITATIVE",
            "verification_status": "VERIFIED",
            "subjects": subjects,
            "tags": ["recruiting", "commitment", "recruit"],
            "sensitive": False,
        })
        inserted += 1

    conn.commit()
    return {"rows_scanned": min(len(rows), int(limit_rows) if limit_rows else len(rows)), "events": inserted}
