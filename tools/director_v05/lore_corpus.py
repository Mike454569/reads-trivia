"""Reviewed football-lore corpus ingestion with rejection reporting."""
from __future__ import annotations
import json
from pathlib import Path
from .event_ingest import upsert_event

REQUIRED=("event_type","title","neutral_summary","source_url","source_publisher","evidence_tier","verification_status")

def ingest_records(conn,records):
    inserted=0; rejected=[]
    for i,row in enumerate(records,1):
        try:
            missing=[k for k in REQUIRED if not row.get(k)]
            if missing: raise ValueError("missing required fields: "+",".join(missing))
            upsert_event(conn,row); inserted+=1
        except Exception as exc:
            rejected.append({"record":i,"title":row.get("title"),"error":type(exc).__name__+":"+str(exc)})
    conn.commit()
    return {"inserted":inserted,"rejected":len(rejected),"errors":rejected[:100]}

def ingest_jsonl(conn,path):
    records=[]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if line and not line.startswith("#"): records.append(json.loads(line))
    return ingest_records(conn,records)
