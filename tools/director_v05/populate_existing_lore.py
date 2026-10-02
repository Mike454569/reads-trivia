"""Populate universal events from certified Engine tables."""
from __future__ import annotations
import json
from .event_ingest import upsert_event

def populate_transfer_events(c, limit=None):
    sql = "SELECT cfb_player_id,display_name,first_school_id,last_school_id,first_season,last_season,path_json FROM cfb_transfer_summary WHERE transfer_count>0 ORDER BY last_season,cfb_player_id"
    if limit: sql += " LIMIT " + str(int(limit))
    count = 0
    for row in c.execute(sql):
        season = row["last_season"] or row["first_season"]
        try: path = json.loads(row["path_json"] or "[]")
        except Exception: path = []
        subjects = [{"subject_type":"CFB_PLAYER","subject_id":row["cfb_player_id"],"role":"player"}]
        if row["first_school_id"]: subjects.append({"subject_type":"SCHOOL","subject_id":row["first_school_id"],"role":"from_school"})
        if row["last_school_id"]: subjects.append({"subject_type":"SCHOOL","subject_id":row["last_school_id"],"role":"to_school"})
        upsert_event(c, {"event_type":"TRANSFER","league":"CFB","event_date":str(int(season))+"-01-01" if season else None,
          "title":str(row["display_name"])+" transfer path","neutral_summary":"Verified multi-school career path with "+str(len(path) or 2)+" recorded stops.",
          "source_url":"https://collegefootballdata.com/","source_publisher":"CollegeFootballData","evidence_tier":"AUTHORITATIVE",
          "verification_status":"VERIFIED","subjects":subjects,"tags":["transfer","portal"],"sensitive":False})
        count += 1
    return {"inserted":count}

def populate_contract_events(c, limit=None):
    sql = "SELECT contract_id,player_key,team_code,year_signed,contract_years,value,apy,guaranteed FROM nfl_player_contracts WHERE verification_status='SOURCE_BACKED' ORDER BY year_signed,contract_id"
    if limit: sql += " LIMIT " + str(int(limit))
    count = 0
    for row in c.execute(sql):
        subjects = [{"subject_type":"NFL_PLAYER","subject_id":row["player_key"],"role":"signer"}]
        if row["team_code"]: subjects.append({"subject_type":"NFL_TEAM","subject_id":row["team_code"],"role":"team"})
        parts=[]
        if row["contract_years"] is not None: parts.append(str(row["contract_years"])+" years")
        if row["value"] is not None: parts.append("total value "+str(int(row["value"])))
        if row["guaranteed"] is not None: parts.append("guaranteed value "+str(int(row["guaranteed"])))
        upsert_event(c, {"event_type":"CONTRACT","league":"NFL","event_date":str(row["year_signed"])+"-01-01",
          "title":"NFL contract record from "+str(row["year_signed"]),"neutral_summary":"; ".join(parts) or "Verified historical NFL contract record.",
          "source_url":"https://github.com/nflverse/nflverse-data/releases/tag/contracts","source_publisher":"nflverse historical contracts",
          "evidence_tier":"AUTHORITATIVE","verification_status":"VERIFIED","subjects":subjects,"tags":["contract","money"],"sensitive":False})
        count += 1
    return {"inserted":count}

def populate_existing(c):
    return {"contracts":populate_contract_events(c),"transfers":populate_transfer_events(c)}
