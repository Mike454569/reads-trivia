"""Compile sourced lore events and derived intelligence into game material."""
from __future__ import annotations
from .query_engine import query_events,query_derived

EVENT_MECHANICS={"MULTIPLE_CHOICE","TRUE_FALSE","THREE_CLUES","TIMELINE","MATCHING",
                 "SORTING","COMMON_LINK","BINGO","RISK_REWARD","SURVIVAL","DAILY","ENDLESS"}
DERIVED_MECHANICS={"MULTIPLE_CHOICE","HIGHER_LOWER","SORTING","BRACKET","ELIMINATION",
                   "RISK_REWARD","SURVIVAL","DAILY","ENDLESS"}

def compile_lore(conn,concept,mechanic,*,league=None,limit=25):
    mechanic=mechanic.upper()
    if mechanic not in EVENT_MECHANICS: raise ValueError("MECHANIC_NOT_EVENT_COMPATIBLE")
    rows=query_events(conn,concept,league=league,limit=limit)
    return [{
      "material_type":"SOURCED_EVENT","concept":concept.upper(),"mechanic":mechanic,
      "event_id":r["event_id"],"title":r["title"],"summary":r["neutral_summary"],
      "event_date":r["event_date"],"source":{"url":r["source_url"],"publisher":r["source_publisher"],
      "evidence_tier":r["evidence_tier"]},"legal_stage":r.get("legal_stage"),
      "disposition":r.get("disposition"),"sensitive":bool(r["sensitive"])
    } for r in rows]

def compile_derived(conn,concept,mechanic,*,limit=25):
    from .creator_concepts import concept as get_concept
    mechanic=mechanic.upper()
    if mechanic not in DERIVED_MECHANICS: raise ValueError("MECHANIC_NOT_DERIVED_COMPATIBLE")
    spec=get_concept(concept)
    metric=spec.get("metric")
    if not metric: raise ValueError("CONCEPT_HAS_NO_DERIVED_METRIC")
    rows=query_derived(conn,metric,limit=limit)
    return [{
      "material_type":"DERIVED_FACT","concept":concept.upper(),"mechanic":mechanic,
      "derived_id":r["derived_id"],"metric":metric,"subject_type":r["subject_type"],
      "subject_id":r["subject_id"],"value":r["value_num"],"label":r["value_text"],
      "formula_version":r["formula_version"],"input_fact_ids_json":r["input_fact_ids_json"]
    } for r in rows]
