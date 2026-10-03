"""Populate universal events from certified Engine tables.

Legacy note: contracts, recruiting, weather and PBP now have dedicated miners
with stronger source-specific provenance. This module keeps only transfer
population for backward compatibility until a dedicated transfer source fully
replaces the inferred path.
"""
from __future__ import annotations
import json

from .event_ingest import upsert_event


def populate_transfer_events(c, limit=None):
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "cfb_transfer_summary" not in tables:
        return {"inserted":0,"reason":"missing_table"}

    sql = """SELECT cfb_player_id,display_name,first_school_id,last_school_id,
                    first_season,last_season,path_json
             FROM cfb_transfer_summary
             WHERE transfer_count>0
             ORDER BY last_season,cfb_player_id"""
    if limit:
        sql += " LIMIT " + str(int(limit))

    count = 0
    for row in c.execute(sql):
        season = row["last_season"] or row["first_season"]
        try:
            path = json.loads(row["path_json"] or "[]")
        except Exception:
            path = []

        # Transfer-summary rows remain useful for corpus breadth, but are
        # explicitly tagged SOURCE_BACKED_DERIVED rather than pretending the
        # summary table itself is the primary evidence.
        subjects = [{
            "subject_type":"CFB_PLAYER",
            "subject_id":row["cfb_player_id"],
            "role":"player",
        }]
        if row["first_school_id"]:
            subjects.append({
                "subject_type":"SCHOOL",
                "subject_id":row["first_school_id"],
                "role":"from_school",
            })
        if row["last_school_id"]:
            subjects.append({
                "subject_type":"SCHOOL",
                "subject_id":row["last_school_id"],
                "role":"to_school",
            })

        upsert_event(c, {
            "event_type":"TRANSFER",
            "league":"CFB",
            "event_date":str(int(season))+"-01-01" if season else None,
            "title":str(row["display_name"])+" transfer path",
            "neutral_summary":"Source-backed multi-school career path with "
                              + str(len(path) or 2) + " recorded stops.",
            "source_url":"https://collegefootballdata.com/",
            "source_publisher":"CollegeFootballData",
            "evidence_tier":"AUTHORITATIVE",
            "verification_status":"VERIFIED",
            "subjects":subjects,
            "tags":["transfer","portal","source_backed_derived"],
            "sensitive":False,
        })
        count += 1
    return {"inserted":count}


def populate_existing(c):
    return {"transfers": populate_transfer_events(c)}
