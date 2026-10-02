"""Allowlisted universal queries for Creator. Never accepts raw SQL."""
from __future__ import annotations
from .capability_compiler import eligible_event_where
from .creator_concepts import CONCEPTS

ALLOWED_LEAGUES={"NFL","CFB","AFL","AAFC","USFL","XFL","UFL"}

def query_events(conn,concept,league=None,start_date=None,end_date=None,subject_id=None,limit=25):
    concept=concept.upper()
    if concept not in CONCEPTS: raise ValueError("unknown concept")
    if league is not None and league not in ALLOWED_LEAGUES: raise ValueError("unsupported league")
    limit=max(1,min(int(limit),100))
    where,args=eligible_event_where(concept)
    clauses=[where]
    if league:
        clauses.append("league=?"); args.append(league)
    if start_date:
        clauses.append("event_date>=?"); args.append(start_date)
    if end_date:
        clauses.append("event_date<=?"); args.append(end_date)
    if subject_id:
        clauses.append("event_id IN (SELECT event_id FROM universal_event_subject WHERE subject_id=?)")
        args.append(subject_id)
    sql=("SELECT event_id,event_type,league,event_date,title,neutral_summary,source_url,"
         "source_publisher,source_date,evidence_tier,verification_status,legal_stage,disposition,sensitive "
         "FROM universal_event WHERE "+" AND ".join(clauses)+
         " ORDER BY event_date DESC,event_id LIMIT ?")
    args.append(limit)
    cur=conn.execute(sql,args)
    keys=[d[0] for d in cur.description]
    return [dict(zip(keys,row)) for row in cur.fetchall()]

def query_derived(conn,metric,league=None,limit=25):
    # Metric must already be declared by a Creator concept; arbitrary columns/
    # expressions never cross this boundary.
    metrics={s.get("metric") for s in CONCEPTS.values() if s.get("metric")}
    if metric not in metrics: raise ValueError("unknown derived metric")
    limit=max(1,min(int(limit),100))
    cur=conn.execute(
      "SELECT derived_id,metric,subject_type,subject_id,value_num,value_text,formula_version,input_fact_ids_json "
      "FROM universal_derived_fact WHERE metric=? AND eligible_for_gameplay=1 ORDER BY value_num DESC LIMIT ?",
      (metric,limit))
    keys=[d[0] for d in cur.description]
    return [dict(zip(keys,row)) for row in cur.fetchall()]
