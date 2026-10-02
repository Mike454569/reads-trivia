"""Compile v0.5 concepts into Creator-ready capabilities."""
from __future__ import annotations
from .creator_concepts import CONCEPTS

def compile_capabilities(coverage:dict)->dict:
    families=coverage.get("families",coverage)
    out={}
    for name,spec in CONCEPTS.items():
        required=tuple(spec.get("families",()))
        states={f:(families.get(f) or {}).get("status","MISSING") for f in required}
        missing=[f for f,s in states.items() if s=="MISSING"]
        partial=[f for f,s in states.items() if s=="PARTIAL"]
        if missing: status="UNSUPPORTED"
        elif partial: status="SUPPORTED_WITH_LIMITATIONS"
        else: status="SUPPORTED"
        out[name]={
            "status":status,
            "required_families":required,
            "family_status":states,
            "metric":spec.get("metric"),
            "tags":spec.get("tags",()),
            "sensitive":bool(spec.get("sensitive")),
            "requires_verified_evidence":bool(spec.get("sensitive")),
        }
    return out

def eligible_event_where(concept:str)->tuple[str,list]:
    spec=CONCEPTS[concept.upper()]
    clauses=["verification_status='VERIFIED'"]
    args=[]
    if spec.get("sensitive"):
        clauses.append("source_url<>''")
        clauses.append("evidence_tier IN ('PRIMARY','AUTHORITATIVE','REPUTABLE_MEDIA')")
    tags=tuple(spec.get("tags",()))
    if tags:
        clauses.append("event_id IN (SELECT event_id FROM universal_event_tag WHERE tag IN (%s))" %
                       ",".join("?" for _ in tags))
        args.extend(tags)
    return " AND ".join(clauses),args
