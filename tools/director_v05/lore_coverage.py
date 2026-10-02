"""Measure universal football knowledge depth and identify thin families."""
from __future__ import annotations
from .lore_taxonomy import EVENT_FAMILIES

TYPE_MAP={
 "ON_FIELD_ODDITY":["ON_FIELD_ODDITY"],"CELEBRATION":["CELEBRATION"],
 "PRESS_CONFERENCE":["PRESS_CONFERENCE"],"MASCOT_FAN_MOMENT":["MASCOT_FAN_MOMENT"],
 "WEATHER_CHAOS":["WEATHER_CHAOS"],"RULE_ODDITY":["RULE_ODDITY"],"ICONIC_PLAY":["ICONIC_PLAY"],
 "UPSET":["UPSET"],"COMEBACK":["COMEBACK"],"RECORD_EVENT":["RECORD_EVENT"],
 "TRADE":["TRADE"],"SIGNING_RELEASE":["SIGNING","RELEASE","WAIVER"],"CONTRACT":["CONTRACT"],
 "COACHING_MOVE":["COACH_HIRE","COACH_FIRE","COACH_RESIGNATION"],"RECRUITING":["RECRUITING"],
 "TRANSFER":["TRANSFER"],"INJURY":["INJURY"],"LEAGUE_DISCIPLINE":["SUSPENSION","FINE","DISCIPLINE"],
 "LEGAL_EVENT":["ARREST","CHARGE","CONVICTION","ACQUITTAL","DISMISSAL","LEGAL_EVENT"],
 "CONTROVERSY":["CONTROVERSY"],"OFF_FIELD_ODDITY":["OFF_FIELD_ODDITY"],
 "HISTORICAL_MILESTONE":["HISTORICAL_MILESTONE"],
}
TARGETS={
 "TRADE":1000,"CONTRACT":5000,"TRANSFER":3000,"ICONIC_PLAY":500,"UPSET":500,"COMEBACK":500,
 "RECORD_EVENT":1000,"ON_FIELD_ODDITY":500,"OFF_FIELD_ODDITY":300,"PRESS_CONFERENCE":300,
 "WEATHER_CHAOS":150,"RULE_ODDITY":300,"LEAGUE_DISCIPLINE":500,"LEGAL_EVENT":500,
 "COACHING_MOVE":1000,"RECRUITING":1000,"HISTORICAL_MILESTONE":1000,
}

def coverage(conn):
    raw={r["event_type"]:r["n"] for r in conn.execute("SELECT event_type,COUNT(*) n FROM universal_event WHERE verification_status='VERIFIED' GROUP BY event_type")}
    families={}
    for fam in EVENT_FAMILIES:
        count=sum(raw.get(t,0) for t in TYPE_MAP.get(fam,[fam]))
        target=TARGETS.get(fam,250)
        families[fam]={"verified":count,"target":target,"coverage":round(min(1,count/target),4),"gap":max(0,target-count)}
    thin=sorted(({"family":k,**v} for k,v in families.items()),key=lambda x:(-x["gap"],x["family"]))
    return {"total_verified":sum(raw.values()),"event_types":raw,"families":families,"priority_gaps":thin}
