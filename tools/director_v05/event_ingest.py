"""Validated ingestion for universal football events."""
from __future__ import annotations
import hashlib, json
from urllib.parse import urlparse
from .universal_schema import install

TIERS={"PRIMARY","AUTHORITATIVE","REPUTABLE_MEDIA","SECONDARY"}
LEGAL_TYPES={"LEGAL_EVENT","ARREST","CHARGE","CONVICTION","ACQUITTAL","DISMISSAL","INVESTIGATION"}
LEGAL_STAGES={"REPORTED","ARRESTED","CHARGED","INDICTED","PLEADED","TRIED","CONVICTED","ACQUITTED","DISMISSED","CLOSED","UNKNOWN"}

def _required(event,k):
    v=event.get(k)
    if v is None or (isinstance(v,str) and not v.strip()):
        raise ValueError("missing required event field: "+k)
    return v

def validate_event(event):
    for k in ("event_type","title","neutral_summary","source_url","source_publisher","evidence_tier"):
        _required(event,k)
    if event["evidence_tier"] not in TIERS: raise ValueError("invalid evidence tier")
    u=urlparse(event["source_url"])
    if u.scheme not in ("http","https") or not u.netloc: raise ValueError("invalid source URL")
    typ=str(event["event_type"]).upper()
    sensitive=bool(event.get("sensitive")) or typ in LEGAL_TYPES
    if sensitive and event["evidence_tier"]=="SECONDARY":
        raise ValueError("sensitive events require primary/authoritative/reputable-media evidence")
    if typ in LEGAL_TYPES:
        if not event.get("allegation_or_offense") and typ not in {"ACQUITTAL","DISMISSAL","INVESTIGATION"}:
            raise ValueError("legal events require allegation_or_offense")
        stage=_required(event,"legal_stage").upper()
        if stage not in LEGAL_STAGES: raise ValueError("invalid legal stage")
        _required(event,"jurisdiction")
    return True

def stable_event_id(event):
    seed="|".join(str(event.get(k,"")).strip().lower() for k in
                  ("event_type","event_date","title","source_url"))
    return "evt_"+hashlib.sha256(seed.encode()).hexdigest()[:24]

def upsert_event(conn,event):
    validate_event(event); install(conn)
    eid=event.get("event_id") or stable_event_id(event)
    cols=("event_id","event_type","league","event_date","title","neutral_summary","source_url",
          "source_publisher","source_date","evidence_tier","verification_status","jurisdiction",
          "legal_stage","allegation_or_offense","disposition","disposition_date","sensitive")
    vals=[eid]+[event.get(k) for k in cols[1:-1]]+[1 if event.get("sensitive") or str(event.get("event_type","")).upper() in LEGAL_TYPES else 0]
    q="INSERT INTO universal_event("+",".join(cols)+") VALUES("+",".join("?" for _ in cols)+") ON CONFLICT(event_id) DO UPDATE SET "+",".join(c+"=excluded."+c for c in cols[1:])
    conn.execute(q,vals)
    conn.execute("DELETE FROM universal_event_evidence WHERE event_id=?",(eid,))
    evidence=event.get("evidence") or [{
      "source_url":event["source_url"],"publisher":event["source_publisher"],
      "published_date":event.get("source_date"),"evidence_tier":event["evidence_tier"],
      "supports_fields":["event"]
    }]
    for ev in evidence:
        tier=ev.get("evidence_tier")
        if tier not in TIERS: raise ValueError("invalid evidence tier")
        u=urlparse(ev.get("source_url",""))
        if u.scheme not in ("http","https") or not u.netloc: raise ValueError("invalid evidence URL")
        if sensitive and tier=="SECONDARY": raise ValueError("sensitive evidence cannot be secondary")
        conn.execute("""INSERT OR REPLACE INTO universal_event_evidence
          (event_id,source_url,publisher,published_date,evidence_tier,supports_fields_json)
          VALUES(?,?,?,?,?,?)""",(eid,ev["source_url"],ev["publisher"],ev.get("published_date"),
          tier,json.dumps(sorted(set(ev.get("supports_fields",["event"]))))))
    conn.execute("DELETE FROM universal_event_subject WHERE event_id=?",(eid,))
    for s in event.get("subjects",()):
        conn.execute("INSERT OR IGNORE INTO universal_event_subject(event_id,subject_type,subject_id,role) VALUES(?,?,?,?)",
                     (eid,s["subject_type"],s["subject_id"],s.get("role","subject")))
    conn.execute("DELETE FROM universal_event_tag WHERE event_id=?",(eid,))
    for tag in sorted(set(str(t).strip().lower() for t in event.get("tags",()) if str(t).strip())):
        conn.execute("INSERT OR IGNORE INTO universal_event_tag(event_id,tag) VALUES(?,?)",(eid,tag))
    conn.commit()
    return eid
