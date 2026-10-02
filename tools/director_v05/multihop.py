"""Multi-hop intelligence: turn verified relationship graphs into deep trivia clues."""
from __future__ import annotations
import hashlib
from .relationships import player_career_graph, traverse

def _uniq(rows,key):
    seen=set(); out=[]
    for r in rows:
        v=r.get(key)
        if v is not None and v not in seen: seen.add(v); out.append(v)
    return out

def _fact_ref(kind,row):
    raw=kind+"|"+"|".join(str(row.get(k,"")) for k in sorted(row))
    return "chain_"+hashlib.sha256(raw.encode()).hexdigest()[:24]

def player_chain(conn,player_id):
    g=player_career_graph(conn,player_id)
    games=traverse(conn,"PLAYER_GAME_LOG",player_id,limit=5000)
    teams=_uniq(g["roster_teams"],"object_id")
    draft=g["draft"][:1]; all_pro=g["all_pro"]
    best_pass=max((r.get("pass_yards") or 0 for r in games),default=0)
    best_rush=max((r.get("rush_yards") or 0 for r in games),default=0)
    best_rec=max((r.get("receiving_yards") or 0 for r in games),default=0)
    refs=[]
    for kind,rows in (("roster",g["roster_teams"]),("draft",draft),("all_pro",all_pro),("game",games)):
        refs.extend(_fact_ref(kind,r) for r in rows)
    clues=[]
    if draft:
        d=draft[0]; clues.append({"type":"draft","text":f"Drafted by {d['object_id']} in round {d['draft_round']} (pick {d['draft_pick_overall']}).","weight":1.0})
    if len(teams)>1: clues.append({"type":"journey","text":f"Played for {len(teams)} NFL teams.","weight":1.4})
    if all_pro: clues.append({"type":"honor","text":f"Earned {len(all_pro)} AP All-Pro selection(s).","weight":1.8})
    peaks=[("passing",best_pass),("rushing",best_rush),("receiving",best_rec)]
    cat,val=max(peaks,key=lambda x:x[1])
    if val>0: clues.append({"type":"peak_game","text":f"Recorded a career game high of at least {int(val)} {cat} yards in the verified game log.","weight":1.6})
    depth=len({c["type"] for c in clues})
    score=round(sum(c["weight"] for c in clues)+max(0,depth-2)*.75,2)
    return {"subject_type":"player","subject_id":player_id,"teams":teams,"clues":clues,
            "depth":depth,"depth_score":score,"input_fact_ids":sorted(set(refs))}

def mechanic_payload(chain,mechanic):
    mechanic=mechanic.upper()
    if chain["depth"]<2: raise ValueError("chain too shallow for deep trivia")
    clues=sorted(chain["clues"],key=lambda c:(c["weight"],c["type"]))
    if mechanic in {"WHO_AM_I","THREE_CLUES","SURVIVAL","ENDLESS","DAILY"}:
        take=3 if mechanic=="THREE_CLUES" else min(4,len(clues))
        return {"mechanic":mechanic,"answer_type":chain["subject_type"],"answer_id":chain["subject_id"],
                "clues":clues[:take],"depth_score":chain["depth_score"],
                "input_fact_ids":chain["input_fact_ids"],"requires_unique_answer":True}
    raise ValueError("mechanic not supported for relationship chain")
