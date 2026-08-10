
"""
Reads Football Game Template DSL compiler.
Supports the built-in YAML-like templates without external dependencies.
"""
from pathlib import Path
import sqlite3, json, hashlib, re

DB=Path(__file__).with_name("reads_football_v4.0.sqlite")

def parse_simple_yaml(text):
    out={}
    stack=[(-1,out)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"): continue
        indent=len(raw)-len(raw.lstrip())
        key,sep,val=raw.strip().partition(":")
        if not sep: continue
        while stack and indent<=stack[-1][0]:
            stack.pop()
        parent=stack[-1][1]
        if val.strip()=="":
            parent[key]={}; stack.append((indent,parent[key]))
        else:
            v=val.strip()
            if v.isdigit(): v=int(v)
            else:
                try: v=float(v)
                except: pass
            parent[key]=v
    return out

def seedint(seed):
    return int(hashlib.sha256(str(seed).encode()).hexdigest()[:16],16)

def compile_template(template_id,seed="daily"):
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    r=c.execute("SELECT template_yaml FROM game_templates WHERE template_id=? AND enabled=1",(template_id,)).fetchone()
    if not r:
        c.close(); return None
    t=parse_simple_yaml(r[0])
    mechanic=t.get("mechanic")
    comp=t.get("competition")
    n=int(t.get("group_size",4))
    h=seedint(f"{template_id}|{seed}")

    if template_id=="draft_team_connections":
        groups=[]
        for team in [x[0] for x in c.execute("SELECT DISTINCT draft_team FROM draft_facts WHERE draft_team IS NOT NULL")]:
            members=[dict(id=x[0],label=x[1]) for x in c.execute(
                "SELECT player_key,player_name FROM draft_facts WHERE draft_team=? ORDER BY player_name",(team,))]
            if len(members)>=n: groups.append((team,members))
        team,members=groups[h%len(groups)]
        chosen=[members[(h+i*17)%len(members)] for i in range(n)]
        result={"template_id":template_id,"competition":"NFL","mechanic":"connections",
                "prompt":"What connects these four NFL players?","items":chosen,"answer":team,
                "relationship":"All were drafted by the same NFL team."}

    elif template_id=="same_school_connections":
        groups=[]
        schools=[tuple(x) for x in c.execute("SELECT school_id,school_name FROM schools ORDER BY school_name")]
        for sid,sname in schools:
            members=[]
            for x in c.execute("""SELECT p.cfb_player_id,p.player_name FROM cfb_player_school_links l
                                  JOIN cfb_players p ON p.cfb_player_id=l.cfb_player_id WHERE l.school_id=?""",(sid,)):
                members.append({"type":"player","id":x[0],"label":x[1]})
            for x in c.execute("""SELECT c.cfb_coach_id,c.coach_name FROM cfb_coach_school_links l
                                  JOIN cfb_coaches c ON c.cfb_coach_id=l.cfb_coach_id WHERE l.school_id=?""",(sid,)):
                members.append({"type":"coach","id":x[0],"label":x[1]})
            ded={m["label"]:m for m in members}
            members=list(ded.values())
            if len(members)>=n: groups.append((sid,sname,members))
        sid,sname,members=groups[h%len(groups)]
        chosen=[members[(h+i*19)%len(members)] for i in range(n)]
        result={"template_id":template_id,"competition":"CFB","mechanic":"connections",
                "prompt":"What connects these four college football names?","items":chosen,
                "answer":sname,"school_id":sid}

    elif template_id=="ordered_draft_picks":
        pool=[dict(id=x[0],label=x[1],value=x[2]) for x in c.execute(
            "SELECT player_key,player_name,draft_pick_overall FROM draft_facts WHERE draft_pick_overall IS NOT NULL")]
        chosen=[]; vals=set()
        for i in range(len(pool)):
            x=pool[(h+i*23)%len(pool)]
            if x["value"] not in vals:
                chosen.append(x);vals.add(x["value"])
            if len(chosen)>=n:break
        scrambled=sorted(chosen,key=lambda x:seedint(seed+x["id"]))
        result={"template_id":template_id,"competition":"NFL","mechanic":"ordering",
                "prompt":"Order these players by draft position, earliest pick to latest.",
                "items":[{"id":x["id"],"label":x["label"]} for x in scrambled],
                "solution":[x["id"] for x in sorted(chosen,key=lambda x:x["value"])]}

    elif template_id=="cfb_award_ordering":
        pool=[dict(id=x[0],label=f"{x[1]} — {x[2]}",value=x[3]) for x in c.execute(
            "SELECT award_fact_id,player_name,award_name,award_year FROM cfb_award_facts WHERE award_year IS NOT NULL")]
        chosen=[];vals=set()
        for i in range(len(pool)):
            x=pool[(h+i*29)%len(pool)]
            if x["value"] not in vals:
                chosen.append(x);vals.add(x["value"])
            if len(chosen)>=n:break
        scrambled=sorted(chosen,key=lambda x:seedint(seed+x["id"]))
        result={"template_id":template_id,"competition":"CFB","mechanic":"ordering",
                "prompt":"Put these college football award items in chronological order.",
                "items":[{"id":x["id"],"label":x["label"]} for x in scrambled],
                "solution":[x["id"] for x in sorted(chosen,key=lambda x:x["value"])]}
    else:
        result={"error":"template not implemented","template_id":template_id}

    c.close()
    return result

if __name__=="__main__":
    import sys
    tid=sys.argv[1] if len(sys.argv)>1 else "draft_team_connections"
    seed=sys.argv[2] if len(sys.argv)>2 else "daily"
    print(json.dumps(compile_template(tid,seed),indent=2))
