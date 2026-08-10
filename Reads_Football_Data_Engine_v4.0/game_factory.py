from __future__ import annotations
from pathlib import Path
import sqlite3, json, hashlib, random, re, argparse
import game_factory_legacy as legacy

ROOT=Path(__file__).parent
DB=ROOT/'reads_football_v4.0.sqlite'
legacy.DB=DB

band=legacy.band
norm=legacy.norm
hid=legacy.hid
seeded=legacy.seeded

def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c


def _year_filter(n, spec):
    m=re.search(r'after\s+(19\d{2}|20\d{2})',n)
    if m: spec['filters']['season_min']=int(m.group(1))+1
    m=re.search(r'before\s+(19\d{2}|20\d{2})',n)
    if m: spec['filters']['season_max']=int(m.group(1))-1


def compile_description(description:str)->dict:
    """Game Factory v1.4 parser with composite/count/temporal/contrast rules.

    Conservative by design: if a cross-domain identity or source isn't verified,
    the rule is returned as NEEDS_* rather than silently approximated.
    """
    spec=legacy.compile_description(description)
    n=norm(description)
    spec['rule_version']='1.4'
    spec['rules']=[]
    spec['complexity_score']=0.0
    spec['required_capabilities']=[]

    # Ensure explicit NFL wins over conference words like SEC.
    if 'nfl' in n or 'pro football' in n:
        spec['competition_id']='NFL'
    elif any(x in n for x in ['college','cfb','ncaa']):
        spec['competition_id']='CFB'

    _year_filter(n,spec)

    # Cross-domain event sequence: intentionally blocked until identity bridge is verified.
    if ('award' in n or 'heisman' in n) and 'draft' in n and any(x in n for x in ['before','after']):
        spec.update(mechanic='connections',entity_type='person',relationship_predicate='AWARD_DRAFT_SEQUENCE',object_type='sequence',answer_type='sequence')
        spec['rules']=[{'kind':'cross_domain_sequence','events':['CFB_AWARD','NFL_DRAFT'],'order':'award_before_draft' if 'before' in n else 'draft_before_award'}]
        spec['required_capabilities']=['XLEAGUE_AWARD_DRAFT']
        spec['complexity_score']=0.95
        spec['intent_status']='PARSED'
        return spec

    # Transfer count rules.
    transfer=re.search(r'transfer(?:red)?\s+(?:exactly\s+)?(once|twice|\d+\s+times?)',n)
    if transfer and spec['competition_id']=='CFB':
        raw=transfer.group(1)
        count=1 if raw=='once' else 2 if raw=='twice' else int(re.search(r'\d+',raw).group())
        spec.update(entity_type='cfb_player',relationship_predicate='CFB_TRANSFER_COUNT',object_type='transfer_count',answer_type='property')
        spec['rules']=[{'kind':'count_condition','metric':'transfer_count','operator':'eq','value':count}]
        spec['required_capabilities']=['CFB_TRANSFER_COUNT']
        spec['complexity_score']=0.55
        spec['intent_status']='PARSED'
        return spec

    # Temporal teammates: actual overlap rather than generic TEAMMATE edge.
    if 'teammate' in n and any(x in n for x in ['before','after','in 20','in 19']):
        comp=spec['competition_id']
        spec.update(entity_type='nfl_player' if comp=='NFL' else 'cfb_player',relationship_predicate=f'{comp}_TEAMMATE_TIME',object_type='team_season',answer_type='team')
        spec['rules']=[{'kind':'temporal_relationship','predicate':'TEAMMATE_OF','filters':dict(spec['filters'])}]
        spec['required_capabilities']=[f'{comp}_TEAMMATE_TIME']
        spec['complexity_score']=0.68
        spec['intent_status']='PARSED'
        return spec

    same_position=any(x in n for x in ['same position','same pos'])
    same_school=any(x in n for x in ['same school','same college'])
    same_draft_team=('draft' in n and any(x in n for x in ['same team','drafted by the same team','same draft team']))
    contrast=any(x in n for x in ['but the fifth','fifth only','one only','different position','one didnt','one did not'])

    # X+Y vs X-only contrast.
    if contrast and same_position and (same_school or same_draft_team):
        spec['mechanic']='elimination'
        if spec['competition_id']=='CFB' and same_school:
            spec.update(entity_type='cfb_player',relationship_predicate='CFB_SCHOOL_POSITION_CONTRAST',object_type='school_position',answer_type='player')
            spec['required_capabilities']=['CFB_CONTRAST_SCHOOL_POSITION']
        elif spec['competition_id']=='NFL' and same_draft_team:
            spec.update(entity_type='nfl_player',relationship_predicate='NFL_DRAFT_TEAM_POSITION_CONTRAST',object_type='draft_team_position',answer_type='player')
            spec['required_capabilities']=['NFL_CONTRAST_DRAFT_TEAM_POSITION']
        spec['rules']=[{'kind':'contrast','shared':['group','position'],'outsider_shares':['group'],'outsider_differs':['position']}]
        spec['complexity_score']=0.82
        spec['intent_status']='PARSED'
        return spec

    # Composite same-X-and-Y grouping.
    if same_position and (same_school or same_draft_team):
        spec['mechanic']='connections' if spec['mechanic']=='guess' else spec['mechanic']
        if spec['competition_id']=='CFB' and same_school:
            spec.update(entity_type='cfb_player',relationship_predicate='CFB_SAME_SCHOOL_POSITION',object_type='school_position',answer_type='school_position')
            spec['required_capabilities']=['CFB_COMPOSITE_SCHOOL_POSITION']
        elif spec['competition_id']=='NFL' and same_draft_team:
            spec.update(entity_type='nfl_player',relationship_predicate='NFL_SAME_DRAFT_TEAM_POSITION',object_type='draft_team_position',answer_type='draft_team_position')
            spec['required_capabilities']=['NFL_COMPOSITE_DRAFT_TEAM_POSITION']
        spec['rules']=[{'kind':'composite_same','group_by':['group','position']}]
        spec['complexity_score']=0.72
        spec['intent_status']='PARSED'
        return spec

    # Promote legacy filter rules into the AST.
    if spec.get('filters'):
        spec['rules'].append({'kind':'attribute_filters','filters':dict(spec['filters'])})
        spec['complexity_score']=0.25+0.08*len(spec['filters'])
    if spec.get('relationship_predicate'):
        spec['rules'].append({'kind':'relationship','predicate':spec['relationship_predicate']})
    return spec


def feasibility(spec:dict)->dict:
    req=spec.get('required_capabilities',[])
    if req:
        c=connect(); missing=[]; supported=[]
        try:
            for cap in req:
                r=c.execute('SELECT supported,source_table,notes FROM factory_rule_capabilities WHERE capability_id=?',(cap,)).fetchone()
                if not r or not r['supported']: missing.append({'capability':cap,'notes':r['notes'] if r else 'Unknown capability'})
                else: supported.append({'capability':cap,'source_table':r['source_table'],'notes':r['notes']})
        finally: c.close()
        if missing:
            status='NEEDS_IDENTITY' if any('IDENTITY' in x['capability'] or 'AWARD' in x['capability'] for x in missing) else 'NEEDS_DATA'
            return {'status':status,'estimated_candidates':0,'reason':missing[0]['notes'],'missing':missing,'supported_capabilities':supported}

    pred=spec.get('relationship_predicate')
    c=connect()
    try:
        if pred=='AWARD_DRAFT_SEQUENCE':
            count=c.execute("SELECT COUNT(*) FROM cross_league_identity_bridge WHERE production_safe=1").fetchone()[0]
            return {'status':'SUPPORTED' if count else 'NEEDS_IDENTITY','estimated_candidates':count,'reason':'Production-safe v1.6 CFB↔NFL identity bridge; stable ESPN IDs are preferred.','missing':[],'source_table':'cross_league_identity_bridge_v16'}
        if pred=='CFB_TRANSFER_COUNT':
            val=spec['rules'][0]['value']; count=c.execute('SELECT COUNT(*) FROM cfb_transfer_summary WHERE transfer_count=?',(val,)).fetchone()[0]
            return {'status':'SUPPORTED' if count>=spec.get('group_size',4) else 'NEEDS_DENSITY','estimated_candidates':count,'reason':'Roster-derived transfer history.','missing':[],'source_table':'cfb_transfer_summary'}
        if pred in ('CFB_SAME_SCHOOL_POSITION','CFB_SCHOOL_POSITION_CONTRAST'):
            count=c.execute('''SELECT COUNT(*) FROM (SELECT school_id,position,COUNT(DISTINCT cfb_player_id) n FROM cfb_roster_seasons_real WHERE position IS NOT NULL GROUP BY school_id,position HAVING n>=?)''',(max(3,spec.get('group_size',4)-1),)).fetchone()[0]
            return {'status':'SUPPORTED' if count else 'NEEDS_DENSITY','estimated_candidates':count,'reason':'CFB school+position composite groups.','missing':[],'source_table':'cfb_roster_seasons_real'}
        if pred in ('NFL_SAME_DRAFT_TEAM_POSITION','NFL_DRAFT_TEAM_POSITION_CONTRAST'):
            count=c.execute('''SELECT COUNT(*) FROM (SELECT draft_team,position,COUNT(*) n FROM draft_facts WHERE draft_team IS NOT NULL AND position IS NOT NULL GROUP BY draft_team,position HAVING n>=?)''',(max(3,spec.get('group_size',4)-1),)).fetchone()[0]
            return {'status':'SUPPORTED' if count else 'NEEDS_DENSITY','estimated_candidates':count,'reason':'NFL draft team+position composite groups.','missing':[],'source_table':'draft_facts'}
        if pred=='NFL_TEAMMATE_TIME':
            mn=spec.get('filters',{}).get('season_min',2006); mx=spec.get('filters',{}).get('season_max',2019)
            count=c.execute('SELECT COUNT(*) FROM canonical_roster_seasons WHERE season BETWEEN ? AND ?',(mn,mx)).fetchone()[0]
            return {'status':'SUPPORTED' if count else 'NEEDS_DATA','estimated_candidates':count,'reason':'Historical NFL roster overlap (2006-2019).','missing':[],'source_table':'canonical_roster_seasons'}
        if pred=='CFB_TEAMMATE_TIME':
            mn=spec.get('filters',{}).get('season_min',2024); mx=spec.get('filters',{}).get('season_max',2025)
            count=c.execute('SELECT COUNT(*) FROM cfb_roster_seasons_real WHERE season BETWEEN ? AND ?',(mn,mx)).fetchone()[0]
            return {'status':'SUPPORTED' if count else 'NEEDS_DATA','estimated_candidates':count,'reason':'CFB roster overlap (2024-2025).','missing':[],'source_table':'cfb_roster_seasons_real'}
    finally: c.close()
    return legacy.feasibility(spec)


def _filtered_year(spec,season):
    f=spec.get('filters',{})
    return (f.get('season_min') is None or season>=f['season_min']) and (f.get('season_max') is None or season<=f['season_max'])


def generate_candidates(spec:dict,limit=100,seed='preview'):
    feas=feasibility(spec)
    if feas['status']!='SUPPORTED': return [],feas
    pred=spec.get('relationship_predicate'); rng=seeded(seed); c=connect(); out=[]; n=int(spec.get('group_size',4))
    try:
        if pred=='AWARD_DRAFT_SEQUENCE':
            rows=c.execute("""SELECT b.bridge_id,b.player_name,b.nfl_draft_year,b.nfl_draft_team,a.award_name,a.award_year
                              FROM cross_league_identity_bridge b JOIN cfb_award_facts a ON a.cfb_player_id=b.cfb_player_id
                              WHERE b.production_safe=1 AND a.award_year<=b.nfl_draft_year""").fetchall()
            for r in rows[:limit]:
                payload={'mechanic':'cross_domain_sequence','prompt':f"What happened first for {r[1]}?",
                         'items':[{'id':'award','label':f"Won {r[4]} ({r[5]})"},{'id':'draft','label':f"Drafted by {r[3]} ({r[2]})"}],
                         'answer':f"Won {r[4]} ({r[5]})",'bridge_id':r[0],
                         'explanation':f"{r[1]} won {r[4]} in {r[5]} before being drafted by {r[3]} in {r[2]}."}
                out.append((payload,.62,0,['cross_league_identity_bridge','cfb_award_facts']))
            return out,feas
        if pred=='CFB_TRANSFER_COUNT':
            val=spec['rules'][0]['value']
            rows=[dict(id=r[0],label=r[1],count=r[2],path=json.loads(r[3])) for r in c.execute('SELECT cfb_player_id,display_name,transfer_count,path_json FROM cfb_transfer_summary WHERE transfer_count=?',(val,))]
            for _ in range(min(limit,max(1,len(rows)//n))):
                chosen=rng.sample(rows,n)
                payload={'mechanic':'connections','prompt':f'What connects these {n} college football players?','items':[{'id':x['id'],'label':x['label']} for x in chosen],'answer':f'Transferred exactly {val} time'+('' if val==1 else 's'),'rule':{'transfer_count':val},'evidence':{x['id']:x['path'] for x in chosen}}
                out.append((payload,.62,0,['cfb_transfer_summary']))
            return out,feas

        if pred in ('CFB_SAME_SCHOOL_POSITION','CFB_SCHOOL_POSITION_CONTRAST'):
            sql='''SELECT r.school_id,s.school_name,r.position,r.cfb_player_id,p.display_name,r.season FROM cfb_roster_seasons_real r JOIN canonical_cfb_players p ON p.cfb_player_id=r.cfb_player_id JOIN schools s ON s.school_id=r.school_id WHERE r.position IS NOT NULL'''
            groups={}
            byschool={}
            for sid,sname,pos,pid,name,season in c.execute(sql):
                if not _filtered_year(spec,season): continue
                groups.setdefault((sid,sname,pos),{})[pid]={'id':pid,'label':name,'season':season,'position':pos}
                byschool.setdefault((sid,sname),{}).setdefault(pos,{})[pid]={'id':pid,'label':name,'season':season,'position':pos}
            good=[(k,list(v.values())) for k,v in groups.items() if len(v)>= (n if pred=='CFB_SAME_SCHOOL_POSITION' else n-1)]
            attempts=0
            while len(out)<limit and attempts<limit*30 and good:
                attempts+=1; (sid,sname,pos),items=rng.choice(good)
                if pred=='CFB_SAME_SCHOOL_POSITION':
                    chosen=rng.sample(items,n)
                    payload={'mechanic':'connections','prompt':'What connects these college football players?','items':[{'id':x['id'],'label':x['label']} for x in chosen],'answer':f'{sname} — {pos}','school':sname,'position':pos,'rule':'same_school_and_position'}
                else:
                    core=rng.sample(items,n-1); alt=[]
                    for opos,pmap in byschool[(sid,sname)].items():
                        if opos!=pos: alt.extend(pmap.values())
                    alt=[x for x in alt if x['id'] not in {y['id'] for y in core}]
                    if not alt: continue
                    outsider=rng.choice(alt); allitems=core+[outsider]; rng.shuffle(allitems)
                    payload={'mechanic':'elimination','prompt':'Which player is the odd one out?','items':[{'id':x['id'],'label':x['label']} for x in allitems],'answer':outsider['label'],'answer_id':outsider['id'],'explanation':f'The other {n-1} were {pos}s at {sname}; {outsider["label"]} was at {sname} but played {outsider["position"]}.','shared_school':sname,'shared_position':pos}
                out.append((payload,.72 if pred.endswith('POSITION') else .78,0,['cfb_roster_seasons_real']))
            return out,feas

        if pred in ('NFL_SAME_DRAFT_TEAM_POSITION','NFL_DRAFT_TEAM_POSITION_CONTRAST'):
            rows=c.execute('SELECT draft_team,position,player_key,player_name,draft_season FROM draft_facts WHERE draft_team IS NOT NULL AND position IS NOT NULL').fetchall()
            groups={}; byteam={}
            for team,pos,pid,name,season in rows:
                if not _filtered_year(spec,season): continue
                groups.setdefault((team,pos),{})[pid]={'id':pid,'label':name,'season':season,'position':pos}
                byteam.setdefault(team,{}).setdefault(pos,{})[pid]={'id':pid,'label':name,'season':season,'position':pos}
            good=[(k,list(v.values())) for k,v in groups.items() if len(v)>=(n if pred=='NFL_SAME_DRAFT_TEAM_POSITION' else n-1)]
            attempts=0
            while len(out)<limit and attempts<limit*30 and good:
                attempts+=1;(team,pos),items=rng.choice(good)
                if pred=='NFL_SAME_DRAFT_TEAM_POSITION':
                    chosen=rng.sample(items,n)
                    payload={'mechanic':'connections','prompt':'What connects these NFL players?','items':[{'id':x['id'],'label':x['label']} for x in chosen],'answer':f'{team} — {pos}','draft_team':team,'position':pos,'rule':'same_draft_team_and_position'}
                else:
                    core=rng.sample(items,n-1);alt=[]
                    for opos,pmap in byteam[team].items():
                        if opos!=pos: alt.extend(pmap.values())
                    if not alt: continue
                    outsider=rng.choice(alt);allitems=core+[outsider];rng.shuffle(allitems)
                    payload={'mechanic':'elimination','prompt':'Which player is the odd one out?','items':[{'id':x['id'],'label':x['label']} for x in allitems],'answer':outsider['label'],'answer_id':outsider['id'],'explanation':f'The other {n-1} were {pos}s drafted by {team}; {outsider["label"]} was drafted by {team} at {outsider["position"]}.','draft_team':team,'shared_position':pos}
                out.append((payload,.7,0,['draft_facts']))
            return out,feas

        if pred in ('NFL_TEAMMATE_TIME','CFB_TEAMMATE_TIME'):
            f=spec.get('filters',{}); mn=f.get('season_min',2006 if pred.startswith('NFL') else 2024); mx=f.get('season_max',2019 if pred.startswith('NFL') else 2025)
            if pred.startswith('NFL'):
                groups={}
                for season,team,pid,name in c.execute('''SELECT r.season,r.team_code,r.player_id,p.display_name FROM canonical_roster_seasons r JOIN canonical_players p ON p.player_id=r.player_id WHERE r.season BETWEEN ? AND ?''',(mn,mx)):
                    groups.setdefault((season,team),{})[pid]={'id':pid,'label':name,'season':season}
            else:
                groups={}
                for season,sid,pid,name in c.execute('''SELECT r.season,r.school_id,r.cfb_player_id,p.display_name FROM cfb_roster_seasons_real r JOIN canonical_cfb_players p ON p.cfb_player_id=r.cfb_player_id WHERE r.season BETWEEN ? AND ?''',(mn,mx)):
                    groups.setdefault((season,sid),{})[pid]={'id':pid,'label':name,'season':season}
            good=[(k,list(v.values())) for k,v in groups.items() if len(v)>=n]
            for _ in range(min(limit,len(good))):
                (season,team),items=rng.choice(good);chosen=rng.sample(items,n)
                label=team
                if pred.startswith('CFB'):
                    r=c.execute('SELECT school_name FROM schools WHERE school_id=?',(team,)).fetchone();label=r[0] if r else team
                payload={'mechanic':'connections','prompt':f'What connects these {n} players?','items':[{'id':x['id'],'label':x['label']} for x in chosen],'answer':f'Teammates at {label} in {season}','team_or_school':label,'season':season,'rule':'teammates_in_time_window'}
                out.append((payload,.66,0,[feas['source_table']]))
            return out,feas
    finally:
        c.close()
    return legacy.generate_candidates(spec,limit,seed)


def qa_candidate(payload):
    issues=legacy.qa_candidate(payload)
    if payload.get('mechanic')=='connections' and len(payload.get('items',[]))<2:
        issues.append({'severity':'ERROR','issue_type':'TOO_FEW_ITEMS','detail':'Connection puzzle needs multiple items.'})
    return issues


def create_spec(spec:dict,created_from='natural_language')->str:
    sid=legacy.create_spec(spec,created_from)
    c=connect();feas=feasibility(spec)
    c.execute('''UPDATE game_factory_specs SET rules_json=?,rule_version='1.4',complexity_score=?,required_capabilities_json=?,missing_capabilities_json=?,source_coverage_json=?,feasibility_status=?,estimated_candidates=? WHERE spec_id=?''',(
        json.dumps(spec.get('rules',[]),sort_keys=True),float(spec.get('complexity_score',0)),json.dumps(spec.get('required_capabilities',[])),json.dumps(feas.get('missing',[]),sort_keys=True),json.dumps(feas,sort_keys=True),feas['status'],int(feas.get('estimated_candidates',0)),sid))
    c.commit();c.close();return sid


def preview(description_or_spec,limit=12,seed='preview'):
    spec=compile_description(description_or_spec) if isinstance(description_or_spec,str) else description_or_spec
    sid=create_spec(spec,'natural_language' if isinstance(description_or_spec,str) else 'structured_spec')
    rows,feas=generate_candidates(spec,limit,seed)
    c=connect();accepted=[];excluded=0
    for i,(payload,diff,amb,sources) in enumerate(rows):
        cid=hid(sid,seed,i,json.dumps(payload,sort_keys=True),prefix='CAND')
        issues=qa_candidate(payload); eligible=0 if any(x['severity']=='ERROR' for x in issues) else 1
        reason=issues[0]['issue_type'] if not eligible else None
        c.execute('''INSERT OR REPLACE INTO game_factory_candidates(candidate_id,spec_id,seed_text,difficulty_score,difficulty_band,ambiguity_score,eligible,exclusion_reason,payload_json,source_refs_json) VALUES (?,?,?,?,?,?,?,?,?,?)''',(cid,sid,str(seed),diff,band(diff),amb,eligible,reason,json.dumps(payload,sort_keys=True),json.dumps(sources)))
        for issue in issues:
            c.execute('INSERT INTO game_factory_qa(spec_id,candidate_id,severity,issue_type,detail) VALUES (?,?,?,?,?)',(sid,cid,issue['severity'],issue['issue_type'],issue['detail']))
        if eligible: accepted.append({'candidate_id':cid,'difficulty_score':round(diff,3),'difficulty_band':band(diff),'payload':payload})
        else: excluded+=1
    c.execute('UPDATE game_factory_specs SET eligible_candidates=?,ambiguity_rate=?,feasibility_status=? WHERE spec_id=?',(len(accepted),excluded/max(1,len(rows)),feas['status'],sid))
    c.commit();c.close()
    return {'spec_id':sid,'spec':spec,'feasibility':feas,'preview':accepted,'excluded_by_qa':excluded}


def publish(spec_id,mode_id=None,candidate_limit=5000,seed='publish'):
    c=connect();r=c.execute('SELECT * FROM game_factory_specs WHERE spec_id=?',(spec_id,)).fetchone()
    if not r: c.close(); raise KeyError(spec_id)
    spec={'description':r['description'],'competition_id':r['competition_id'],'mechanic':r['mechanic'],'answer_type':r['answer_type'],'entity_type':r['entity_type'],'relationship_predicate':r['relationship_predicate'],'object_type':r['object_type'],'filters':json.loads(r['filters_json']),'group_size':r['group_size'],'difficulty':{'min':r['difficulty_min'],'max':r['difficulty_max']},'rules':json.loads(r['rules_json'] or '[]'),'required_capabilities':json.loads(r['required_capabilities_json'] or '[]'),'complexity_score':r['complexity_score'],'intent_status':'PARSED'}
    c.close()
    feas=feasibility(spec)
    if feas['status']!='SUPPORTED': return {'status':'NOT_PUBLISHED','reason':feas['status'],'detail':feas.get('reason')}
    # v1.4 preview/generation then legacy-compatible persistence.
    rows,_=generate_candidates(spec,candidate_limit,seed)
    c=connect();rejected=0
    for i,(payload,diff,amb,sources) in enumerate(rows):
        cid=hid(spec_id,seed,i,json.dumps(payload,sort_keys=True),prefix='CAND')
        issues=qa_candidate(payload);eligible=0 if any(x['severity']=='ERROR' for x in issues) else 1
        rejected += 0 if eligible else 1
        c.execute('''INSERT OR IGNORE INTO game_factory_candidates(candidate_id,spec_id,seed_text,difficulty_score,difficulty_band,ambiguity_score,eligible,exclusion_reason,payload_json,source_refs_json) VALUES (?,?,?,?,?,?,?,?,?,?)''',(cid,spec_id,seed,diff,band(diff),amb,eligible,issues[0]['issue_type'] if issues else None,json.dumps(payload,sort_keys=True),json.dumps(sources)))
    mode_id=mode_id or ('factory_'+spec_id.split(':')[-1][:10])
    eligible_rows=c.execute('SELECT candidate_id,difficulty_score,difficulty_band,payload_json FROM game_factory_candidates WHERE spec_id=? AND eligible=1',(spec_id,)).fetchall();pubcount=0
    for cr in eligible_rows:
        pz='PZGF:'+cr['candidate_id'].split(':')[-1]
        c.execute('''INSERT OR IGNORE INTO puzzle_catalog(puzzle_id,mode_id,source_entity_type,source_entity_id,season,difficulty_score,difficulty_band,ambiguity_score,popularity_proxy,eligible,exclusion_reason,verification_status,source_id,payload_json) VALUES (?,?,?,?,NULL,?,?,0,0.5,1,NULL,'FACTORY_QA_PASSED','GAME_FACTORY',?)''',(pz,mode_id,spec.get('answer_type') or 'entity',cr['candidate_id'],cr['difficulty_score'],cr['difficulty_band'],cr['payload_json']))
        pubcount+=c.execute('SELECT changes()').fetchone()[0]
    pubid=hid(spec_id,mode_id,prefix='PUB')
    c.execute('INSERT OR REPLACE INTO game_factory_publications(publication_id,spec_id,mode_id,active,candidate_count,notes) VALUES (?,?,?,1,?,?)',(pubid,spec_id,mode_id,pubcount,'Published by Game Factory v1.4'))
    c.execute("UPDATE game_factory_specs SET status='PUBLISHED',eligible_candidates=? WHERE spec_id=?",(len(eligible_rows),spec_id));c.commit();c.close()
    return {'status':'PUBLISHED','publication_id':pubid,'mode_id':mode_id,'published_puzzles':pubcount,'qa_rejected':rejected}

unpublish=legacy.unpublish
capabilities=legacy.capabilities


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
        s=compile_description(a.description);out={'spec':s,'feasibility':feasibility(s)}
    elif a.cmd=='publish': out=publish(a.spec_id,a.mode_id,a.limit)
    elif a.cmd=='unpublish': out=unpublish(a.mode_id)
    else: out=capabilities()
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
