from __future__ import annotations
from pathlib import Path
import sqlite3, json, hashlib, random, re, argparse, datetime as dt
from collections import defaultdict

ROOT = Path(__file__).parent
DB = ROOT / "reads_football_v4.0.sqlite"

BANDS = [(0.30,"EASY"),(0.50,"MEDIUM"),(0.70,"HARD"),(1.01,"EXPERT")]

def band(x: float) -> str:
    for cut,name in BANDS:
        if x < cut:
            return name
    return "EXPERT"

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()

def hid(*parts, prefix="GF"):
    raw="|".join(map(str,parts))
    return prefix+":"+hashlib.sha1(raw.encode()).hexdigest()[:20]

def seeded(seed: str) -> random.Random:
    return random.Random(int(hashlib.sha256(str(seed).encode()).hexdigest()[:16],16))

def connect():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

# ---------------- Natural-language -> spec ----------------

def compile_description(description: str) -> dict:
    """Translate common game descriptions into a stable Game Factory spec.

    This parser is deliberately conservative: unsupported ideas are returned as
    NEEDS_DATA/NEEDS_RULE rather than guessed into a different game.
    """
    d=description.strip(); n=norm(d)
    if "nfl" in n or "pro football" in n:
        comp="NFL"
    elif any(x in n for x in ["college", "cfb", "ncaa", "sec", "big ten", "acc", "big 12"]):
        comp="CFB"
    else:
        comp="NFL"

    if any(x in n for x in ["odd one out","one didnt","one did not","doesnt belong","does not belong"]): mechanic="elimination"
    elif any(x in n for x in ["order ","put in order","rank ","earliest to latest","draft order"]): mechanic="ordering"
    elif any(x in n for x in ["match each","matching","match them"]): mechanic="matching"
    elif any(x in n for x in ["six degrees","shortest path","connect any two","path from"]): mechanic="path"
    elif any(x in n for x in ["what connects","what do these","connections","all share","same "]): mechanic="connections"
    else: mechanic="guess"

    group_size=5 if re.search(r"\b5\b|\bfive\b",n) else 4
    filters={}
    m=re.search(r"after\s+(19\d{2}|20\d{2})",n)
    if m: filters["season_min"]=int(m.group(1))+1
    m=re.search(r"before\s+(19\d{2}|20\d{2})",n)
    if m: filters["season_max"]=int(m.group(1))-1
    if "quarterback" in n or re.search(r"\bqb\b",n): filters["position"]="QB"
    if "fbs" in n: filters["division"]="fbs"
    for conf in ["SEC","Big Ten","ACC","Big 12","Pac-12"]:
        if norm(conf) in n: filters["conference"]=conf

    spec={
        "description":d,"competition_id":comp,"mechanic":mechanic,
        "entity_type":None,"relationship_predicate":None,"object_type":None,
        "answer_type":None,"group_size":group_size,"filters":filters,
        "difficulty":{"min":0.0,"max":1.0},"intent_status":"PARSED"
    }

    # Strong intent mappings.
    if "draft" in n and any(x in n for x in ["team", "drafted by", "same team", "connections", "odd"]):
        spec.update(entity_type="nfl_player", relationship_predicate="DRAFTED_BY", object_type="team", answer_type="team")
    elif "draft" in n and mechanic=="ordering":
        spec.update(entity_type="nfl_player", relationship_predicate="DRAFT_PICK_ORDER", object_type="draft_pick", answer_type="ordering")
    elif "teammate" in n:
        spec.update(entity_type="nfl_player" if comp=="NFL" else "cfb_player", relationship_predicate="TEAMMATE_OF", object_type=spec["entity_type"], answer_type="player")
    elif any(x in n for x in ["played for","same nfl team","same team"] ) and comp=="NFL":
        spec.update(entity_type="nfl_player", relationship_predicate="PLAYED_FOR", object_type="team", answer_type="team")
    elif any(x in n for x in ["school","college","attended","same school"]) and comp=="CFB":
        spec.update(entity_type="cfb_player", relationship_predicate="CFB_ROSTER_SCHOOL", object_type="school", answer_type="school")
    elif any(x in n for x in ["school","college","attended"]) and comp=="NFL":
        spec.update(entity_type="nfl_player", relationship_predicate="NFL_ATTENDED_SCHOOL", object_type="school", answer_type="school")
    elif "conference" in n and comp=="CFB":
        spec.update(entity_type="school", relationship_predicate="CFB_MEMBER_OF_CONFERENCE", object_type="conference", answer_type="conference")
    elif "coach" in n and "school" in n and comp=="CFB":
        spec.update(entity_type="cfb_coach", relationship_predicate="COACHED_AT_CFB_SCHOOL", object_type="school", answer_type="school")
    elif "rival" in n and comp=="CFB":
        spec.update(entity_type="school", relationship_predicate="RIVAL_OF", object_type="school", answer_type="school")
    elif mechanic=="path":
        spec.update(entity_type="entity", relationship_predicate="GRAPH_PATH", object_type="entity", answer_type="path")
    else:
        spec["intent_status"]="NEEDS_RULE"

    return spec

# ---------------- Feasibility ----------------

def _source_for_predicate(pred: str):
    return {
        "DRAFTED_BY":("relationships","NFL draft data"),
        "PLAYED_FOR":("relationships","NFL roster history"),
        "TEAMMATE_OF":("relationships","roster relationship graph"),
        "CFB_ROSTER_SCHOOL":("cfb_roster_seasons_real","CFB rosters"),
        "CFB_MEMBER_OF_CONFERENCE":("relationships","CFB school-season data"),
        "COACHED_AT_CFB_SCHOOL":("relationships","CFB coach master"),
        "RIVAL_OF":("relationships","CFB rivalry master"),
        "DRAFT_PICK_ORDER":("draft_facts","NFL draft data"),
        "GRAPH_PATH":("graph_edges","football knowledge graph"),
        "NFL_ATTENDED_SCHOOL":(None,"current NFL player/college enrichment"),
    }.get(pred,(None,"unknown"))

def feasibility(spec: dict) -> dict:
    pred=spec.get("relationship_predicate")
    if spec.get("intent_status")=="NEEDS_RULE" or not pred:
        return {"status":"NEEDS_RULE","estimated_candidates":0,"reason":"The description does not map to a supported relationship yet.","missing":[]}
    if pred=="NFL_ATTENDED_SCHOOL":
        return {"status":"NEEDS_DATA","estimated_candidates":0,"reason":"NFL player→college edges are not populated in the current production-safe database.","missing":["modern NFL player college enrichment"]}
    c=connect()
    try:
        if pred=="CFB_ROSTER_SCHOOL":
            q="SELECT COUNT(*) FROM cfb_roster_seasons_real"
            count=c.execute(q).fetchone()[0]
        elif pred=="DRAFT_PICK_ORDER":
            count=c.execute("SELECT COUNT(*) FROM draft_facts WHERE draft_pick_overall IS NOT NULL").fetchone()[0]
        elif pred=="GRAPH_PATH":
            count=c.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
        else:
            count=c.execute("SELECT COUNT(*) FROM relationships WHERE predicate=?",(pred,)).fetchone()[0]
        table,source=_source_for_predicate(pred)
        if not count:
            return {"status":"NEEDS_DATA","estimated_candidates":0,"reason":f"No production rows exist for {pred}.","missing":[source]}
        # Rough candidate estimate: group mechanics depend on object groups, ordering on combinations.
        est=count
        if spec["mechanic"] in ("connections","elimination","matching"):
            est=max(1,count//max(1,spec.get("group_size",4)))
        return {"status":"SUPPORTED","estimated_candidates":int(est),"reason":f"Backed by {source}.","missing":[],"source_table":table}
    finally: c.close()

# ---------------- Candidate pools ----------------

def _player_label(c, typ, pid):
    if typ=="nfl_player":
        r=c.execute("SELECT display_name FROM canonical_players WHERE player_id=?",(pid,)).fetchone()
        if not r: r=c.execute("SELECT player_name FROM nfl_players_draft WHERE player_key=?",(pid,)).fetchone()
    elif typ=="cfb_player": r=c.execute("SELECT display_name FROM canonical_cfb_players WHERE cfb_player_id=?",(pid,)).fetchone()
    elif typ=="cfb_coach": r=c.execute("SELECT coach_name FROM cfb_coaches WHERE cfb_coach_id=?",(pid,)).fetchone()
    elif typ=="school": r=c.execute("SELECT school_name FROM schools WHERE school_id=?",(pid,)).fetchone()
    else: r=None
    return r[0] if r else pid

def _object_label(c, typ, oid):
    if typ=="school":
        r=c.execute("SELECT school_name FROM schools WHERE school_id=?",(oid,)).fetchone(); return r[0] if r else oid
    return oid

def _groups(c,spec):
    pred=spec["relationship_predicate"]; et=spec["entity_type"]; ot=spec["object_type"]
    groups=defaultdict(list)
    if pred=="CFB_ROSTER_SCHOOL":
        sql='''SELECT r.school_id,r.cfb_player_id,p.display_name,r.season,r.position
               FROM cfb_roster_seasons_real r
               JOIN canonical_cfb_players p ON p.cfb_player_id=r.cfb_player_id
               LEFT JOIN cfb_school_seasons ss ON ss.season=r.season AND ss.school_id=r.school_id'''
        params=[]; wh=[]
        f=spec.get("filters",{})
        if f.get("season_min") is not None: wh.append("r.season>=?");params.append(f["season_min"])
        if f.get("season_max") is not None: wh.append("r.season<=?");params.append(f["season_max"])
        if f.get("position"): wh.append("upper(r.position)=?");params.append(f["position"].upper())
        if f.get("division"): wh.append("lower(ss.division)=?");params.append(f["division"].lower())
        if f.get("conference"): wh.append("lower(ss.conference)=?");params.append(f["conference"].lower())
        if wh: sql+=" WHERE "+" AND ".join(wh)
        for oid,pid,label,season,pos in c.execute(sql,params):
            groups[oid].append({"id":pid,"label":label,"season":season,"position":pos})
    elif pred=="DRAFTED_BY":
        sql='''SELECT draft_team,player_key,player_name,draft_season,position FROM draft_facts WHERE draft_team IS NOT NULL'''
        f=spec.get("filters",{}); wh=[];params=[]
        if f.get("season_min") is not None: wh.append("draft_season>=?");params.append(f["season_min"])
        if f.get("season_max") is not None: wh.append("draft_season<=?");params.append(f["season_max"])
        if f.get("position"): wh.append("upper(position)=?");params.append(f["position"].upper())
        if wh: sql+=" AND "+" AND ".join(wh)
        for oid,pid,label,season,pos in c.execute(sql,params):
            groups[oid].append({"id":pid,"label":label,"season":season,"position":pos})
    else:
        # Generic source-backed relationship groups.
        sql='''SELECT object_id,subject_id,season_start,season_end FROM relationships
               WHERE predicate=? AND subject_type=? AND object_type=?'''
        for oid,pid,ss,se in c.execute(sql,(pred,et,ot)):
            groups[oid].append({"id":pid,"label":_player_label(c,et,pid),"season":ss or se})
    # de-dupe within each group by entity ID.
    out={}
    for oid,items in groups.items():
        d={x["id"]:x for x in items}
        if len(d)>=max(2,spec.get("group_size",4)-1): out[oid]=list(d.values())
    return out

def _difficulty(items, group_count, mechanic):
    eras=[x.get("season") for x in items if isinstance(x.get("season"),int)]
    old=0.35
    if eras: old=max(0,min(1,(2026-max(eras))/30))
    rarity=max(0,min(1,1-(len(items)/60)))
    mech={"connections":.10,"elimination":.18,"matching":.12,"ordering":.15,"guess":.05}.get(mechanic,.12)
    return max(.05,min(.95,.42*old+.38*rarity+mech))

def generate_candidates(spec: dict, limit=100, seed="preview"):
    feas=feasibility(spec)
    if feas["status"]!="SUPPORTED": return [],feas
    rng=seeded(seed); c=connect(); out=[]
    try:
        mech=spec["mechanic"]; n=int(spec.get("group_size",4)); pred=spec["relationship_predicate"]
        if pred=="DRAFT_PICK_ORDER":
            rows=[dict(id=r[0],label=r[1],value=r[2],season=r[3]) for r in c.execute(
                "SELECT player_key,player_name,draft_pick_overall,draft_season FROM draft_facts WHERE draft_pick_overall IS NOT NULL")]
            for k in range(min(limit,max(1,len(rows)//n))):
                sample=rng.sample(rows,n); vals={x['value'] for x in sample}
                if len(vals)<n: continue
                shuffled=sample[:];rng.shuffle(shuffled)
                diff=.35+.35*max(0,min(1,(2026-max(x['season'] or 2000 for x in sample))/40))
                payload={"mechanic":"ordering","prompt":"Order these NFL players by overall draft pick, earliest pick to latest.",
                         "items":[{"id":x['id'],"label":x['label']} for x in shuffled],
                         "solution":[x['id'] for x in sorted(sample,key=lambda x:x['value'])],
                         "values":{x['id']:x['value'] for x in sample}}
                out.append((payload,diff,0,["draft_facts"]))
            return out,feas
        if pred=="GRAPH_PATH":
            return [],{"status":"SUPPORTED","estimated_candidates":0,"reason":"Path games are generated on demand by graph_explorer; no static pool required.","missing":[]}

        groups=_groups(c,spec)
        good=[(oid,items) for oid,items in groups.items() if len(items)>=n]
        if not good: return [],{"status":"NEEDS_DENSITY","estimated_candidates":0,"reason":"Relationship exists but not enough groups contain the requested number of unique entities.","missing":[]}
        object_ids=[x[0] for x in good]
        attempts=0
        seen=set()
        while len(out)<limit and attempts<limit*30:
            attempts+=1
            oid,items=rng.choice(good)
            chosen=rng.sample(items,n)
            key=(oid,tuple(sorted(x['id'] for x in chosen)),mech)
            if key in seen: continue
            seen.add(key)
            answer=_object_label(c,spec["object_type"],oid)
            diff=_difficulty(chosen,len(groups),mech)
            ambiguity=0
            if mech=="connections":
                payload={"mechanic":"connections","prompt":"What connects these names?",
                         "items":[{"id":x['id'],"label":x['label']} for x in chosen],"answer":answer,
                         "answer_id":oid,"relationship":pred}
            elif mech=="elimination":
                # Three from core, one outsider from a different object group.
                if len(object_ids)<2: continue
                core=rng.sample(items,n-1)
                other_oid=rng.choice([x for x in object_ids if x!=oid])
                outsiders=groups[other_oid]
                outsider=rng.choice(outsiders)
                # Avoid an outsider that also belongs to core group.
                if any(x['id']==outsider['id'] for x in items): continue
                allitems=core+[outsider];rng.shuffle(allitems)
                payload={"mechanic":"elimination","prompt":"Which one is the odd one out?",
                         "items":[{"id":x['id'],"label":x['label']} for x in allitems],
                         "answer":outsider['label'],"answer_id":outsider['id'],
                         "explanation":f"The other {n-1} share {answer} via {pred}.","shared_answer":answer}
            elif mech=="matching":
                # Pick entities from distinct object groups, then shuffle right column.
                selected=[]
                for g_oid,g_items in rng.sample(good,min(n,len(good))):
                    selected.append((rng.choice(g_items),g_oid))
                if len(selected)<n: continue
                right=[{"id":go,"label":_object_label(c,spec['object_type'],go)} for _,go in selected];rng.shuffle(right)
                payload={"mechanic":"matching","prompt":"Match each item to the correct answer.",
                         "left":[{"id":x['id'],"label":x['label']} for x,_ in selected],"right":right,
                         "solution":{x['id']:go for x,go in selected},"relationship":pred}
            else: # guess
                x=rng.choice(chosen)
                payload={"mechanic":"guess","prompt":f"Which {spec['object_type']} is linked to {x['label']}?",
                         "answer":answer,"answer_id":oid,"entity":{"id":x['id'],"label":x['label']},"relationship":pred}
            out.append((payload,diff,ambiguity,[feas.get("source_table")]))
        return out,feas
    finally: c.close()

# ---------------- QA / persistence ----------------

def qa_candidate(payload: dict) -> list[dict]:
    issues=[]
    answer=payload.get("answer")
    if payload.get("mechanic") not in ("ordering","matching") and not answer:
        issues.append({"severity":"ERROR","issue_type":"MISSING_ANSWER","detail":"Candidate has no canonical answer."})
    labels=[]
    for key in ("items","left","right"):
        for x in payload.get(key,[]) or []: labels.append(norm(x.get("label")))
    if labels and len(labels)!=len(set(labels)):
        issues.append({"severity":"ERROR","issue_type":"DUPLICATE_DISPLAY_ITEM","detail":"Candidate contains duplicate visible labels."})
    if payload.get("mechanic")=="elimination" and norm(answer) not in labels:
        issues.append({"severity":"ERROR","issue_type":"ANSWER_NOT_VISIBLE","detail":"Odd-one-out answer is not one of the displayed items."})
    return issues

def create_spec(spec: dict, created_from="natural_language") -> str:
    feas=feasibility(spec)
    sid=hid(spec.get('description'),json.dumps(spec,sort_keys=True),prefix="SPEC")
    c=connect()
    c.execute('''INSERT OR REPLACE INTO game_factory_specs(
      spec_id,created_from,description,competition_id,mechanic,answer_type,entity_type,relationship_predicate,object_type,
      filters_json,group_size,difficulty_min,difficulty_max,status,feasibility_status,estimated_candidates,source_coverage_json,notes)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'DRAFT',?,?,?,?)''',(
      sid,created_from,spec.get('description'),spec['competition_id'],spec['mechanic'],spec.get('answer_type'),spec.get('entity_type'),
      spec.get('relationship_predicate'),spec.get('object_type'),json.dumps(spec.get('filters',{}),sort_keys=True),int(spec.get('group_size',4)),
      float(spec.get('difficulty',{}).get('min',0)),float(spec.get('difficulty',{}).get('max',1)),feas['status'],int(feas.get('estimated_candidates',0)),
      json.dumps(feas,sort_keys=True),feas.get('reason')))
    c.commit();c.close();return sid

def preview(description_or_spec, limit=12, seed="preview") -> dict:
    spec=compile_description(description_or_spec) if isinstance(description_or_spec,str) else description_or_spec
    sid=create_spec(spec,"natural_language" if isinstance(description_or_spec,str) else "structured_spec")
    rows,feas=generate_candidates(spec,limit,seed)
    c=connect(); accepted=[]; excluded=0
    for i,(payload,diff,amb,sources) in enumerate(rows):
        cid=hid(sid,seed,i,json.dumps(payload,sort_keys=True),prefix="CAND")
        issues=qa_candidate(payload); eligible=0 if any(x['severity']=='ERROR' for x in issues) else 1
        reason=issues[0]['issue_type'] if not eligible else None
        c.execute('''INSERT OR REPLACE INTO game_factory_candidates(candidate_id,spec_id,seed_text,difficulty_score,difficulty_band,
                     ambiguity_score,eligible,exclusion_reason,payload_json,source_refs_json)
                     VALUES (?,?,?,?,?,?,?,?,?,?)''',(cid,sid,str(seed),diff,band(diff),amb,eligible,reason,json.dumps(payload,sort_keys=True),json.dumps(sources)))
        for issue in issues:
            c.execute('INSERT INTO game_factory_qa(spec_id,candidate_id,severity,issue_type,detail) VALUES (?,?,?,?,?)',
                      (sid,cid,issue['severity'],issue['issue_type'],issue['detail']))
        if eligible:
            accepted.append({"candidate_id":cid,"difficulty_score":round(diff,3),"difficulty_band":band(diff),"payload":payload})
        else: excluded+=1
    c.execute('''UPDATE game_factory_specs SET eligible_candidates=?,ambiguity_rate=?,feasibility_status=? WHERE spec_id=?''',
              (len(accepted), excluded/max(1,len(rows)),feas['status'],sid))
    c.commit();c.close()
    return {"spec_id":sid,"spec":spec,"feasibility":feas,"preview":accepted,"excluded_by_qa":excluded}

def publish(spec_id: str, mode_id: str|None=None, candidate_limit=5000, seed="publish") -> dict:
    c=connect(); r=c.execute('SELECT * FROM game_factory_specs WHERE spec_id=?',(spec_id,)).fetchone()
    if not r: c.close(); raise KeyError(spec_id)
    if r['feasibility_status'] not in ('SUPPORTED','NEEDS_DENSITY'):
        c.close(); return {"status":"NOT_PUBLISHED","reason":r['feasibility_status']}
    spec={"description":r['description'],"competition_id":r['competition_id'],"mechanic":r['mechanic'],"answer_type":r['answer_type'],
          "entity_type":r['entity_type'],"relationship_predicate":r['relationship_predicate'],"object_type":r['object_type'],
          "filters":json.loads(r['filters_json']),"group_size":r['group_size'],"difficulty":{"min":r['difficulty_min'],"max":r['difficulty_max']}}
    c.close()
    rows,feas=generate_candidates(spec,candidate_limit,seed)
    c=connect(); inserted=0; rejected=0
    existing={x[0] for x in c.execute('SELECT candidate_id FROM game_factory_candidates WHERE spec_id=?',(spec_id,))}
    for i,(payload,diff,amb,sources) in enumerate(rows):
        cid=hid(spec_id,seed,i,json.dumps(payload,sort_keys=True),prefix="CAND")
        if cid in existing: continue
        issues=qa_candidate(payload); eligible=0 if any(x['severity']=='ERROR' for x in issues) else 1
        if eligible: inserted+=1
        else: rejected+=1
        c.execute('''INSERT OR IGNORE INTO game_factory_candidates(candidate_id,spec_id,seed_text,difficulty_score,difficulty_band,
                     ambiguity_score,eligible,exclusion_reason,payload_json,source_refs_json) VALUES (?,?,?,?,?,?,?,?,?,?)''',
                  (cid,spec_id,seed,diff,band(diff),amb,eligible,issues[0]['issue_type'] if issues else None,json.dumps(payload,sort_keys=True),json.dumps(sources)))
    mode_id=mode_id or ("factory_"+spec_id.split(':')[-1][:10])
    # Publish eligible candidates into the standard puzzle catalog. This is additive and UI-compatible.
    eligible_rows=c.execute('SELECT candidate_id,difficulty_score,difficulty_band,payload_json FROM game_factory_candidates WHERE spec_id=? AND eligible=1',(spec_id,)).fetchall()
    pubcount=0
    for cr in eligible_rows:
        pz="PZGF:"+cr['candidate_id'].split(':')[-1]
        payload=json.loads(cr['payload_json'])
        answer_entity=spec.get('answer_type') or 'entity'
        c.execute('''INSERT OR IGNORE INTO puzzle_catalog(puzzle_id,mode_id,source_entity_type,source_entity_id,season,difficulty_score,difficulty_band,
                    ambiguity_score,popularity_proxy,eligible,exclusion_reason,verification_status,source_id,payload_json)
                    VALUES (?,?,?,?,NULL,?,?,0,0.5,1,NULL,'FACTORY_QA_PASSED','GAME_FACTORY',?)''',
                  (pz,mode_id,answer_entity,cr['candidate_id'],cr['difficulty_score'],cr['difficulty_band'],cr['payload_json']))
        pubcount += c.execute('SELECT changes()').fetchone()[0]
    pubid=hid(spec_id,mode_id,dt.datetime.utcnow().isoformat(),prefix='PUB')
    c.execute('INSERT INTO game_factory_publications(publication_id,spec_id,mode_id,active,candidate_count,notes) VALUES (?,?,?,1,?,?)',
              (pubid,spec_id,mode_id,pubcount,'Published by Game Factory v1.4'))
    c.execute("UPDATE game_factory_specs SET status='PUBLISHED',eligible_candidates=? WHERE spec_id=?",(len(eligible_rows),spec_id))
    # Refresh mode health for this mode only.
    vals=[x[0] for x in c.execute('SELECT difficulty_score FROM puzzle_catalog WHERE mode_id=? AND eligible=1',(mode_id,))]
    if vals:
        counts={b:c.execute('SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id=? AND eligible=1 AND difficulty_band=?',(mode_id,b)).fetchone()[0] for b in ['EASY','MEDIUM','HARD','EXPERT']}
        c.execute('''INSERT OR REPLACE INTO mode_health(mode_id,eligible_puzzles,easy_count,medium_count,hard_count,expert_count,min_difficulty,max_difficulty,notes)
                     VALUES (?,?,?,?,?,?,?,?,?)''',(mode_id,len(vals),counts['EASY'],counts['MEDIUM'],counts['HARD'],counts['EXPERT'],min(vals),max(vals),'Game Factory v1.4 publication'))
    c.commit();c.close()
    return {"status":"PUBLISHED","publication_id":pubid,"mode_id":mode_id,"published_puzzles":pubcount,"qa_rejected":rejected}

def unpublish(mode_id: str) -> dict:
    c=connect()
    n=c.execute('SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id=? AND eligible=1',(mode_id,)).fetchone()[0]
    c.execute("UPDATE puzzle_catalog SET eligible=0,exclusion_reason='factory_unpublished' WHERE mode_id=?",(mode_id,))
    c.execute("UPDATE game_factory_publications SET active=0,unpublished_at=CURRENT_TIMESTAMP WHERE mode_id=? AND active=1",(mode_id,))
    c.execute("UPDATE game_factory_specs SET status='UNPUBLISHED' WHERE spec_id IN (SELECT spec_id FROM game_factory_publications WHERE mode_id=?)",(mode_id,))
    c.commit();c.close();return {"status":"UNPUBLISHED","mode_id":mode_id,"disabled_puzzles":n}

def capabilities():
    c=connect(); out=[dict(r) for r in c.execute('SELECT * FROM game_factory_capabilities ORDER BY competition_id,mechanic,capability_id')];c.close();return out

def main():
    ap=argparse.ArgumentParser(description='Reads Football Game Factory v1.4')
    sp=ap.add_subparsers(dest='cmd',required=True)
    p=sp.add_parser('preview');p.add_argument('description');p.add_argument('--limit',type=int,default=12);p.add_argument('--seed',default='preview')
    p=sp.add_parser('analyze');p.add_argument('description')
    p=sp.add_parser('publish');p.add_argument('spec_id');p.add_argument('--mode-id');p.add_argument('--limit',type=int,default=5000)
    p=sp.add_parser('unpublish');p.add_argument('mode_id')
    sp.add_parser('capabilities')
    a=ap.parse_args()
    if a.cmd=='preview': out=preview(a.description,a.limit,a.seed)
    elif a.cmd=='analyze':
        spec=compile_description(a.description);out={"spec":spec,"feasibility":feasibility(spec)}
    elif a.cmd=='publish': out=publish(a.spec_id,a.mode_id,a.limit)
    elif a.cmd=='unpublish': out=unpublish(a.mode_id)
    else: out=capabilities()
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
