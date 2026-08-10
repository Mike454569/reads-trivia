import json, sqlite3
import game_factory as gf

def ck(x,msg):
    if not x: raise AssertionError(msg)

cases=[]

s=gf.compile_description('Four NFL players drafted by the same team and same position')
f=gf.feasibility(s)
ck(s['relationship_predicate']=='NFL_SAME_DRAFT_TEAM_POSITION','NFL composite parse')
ck(f['status']=='SUPPORTED','NFL composite support')
p=gf.preview(s,6,'v14-nfl-composite')
ck(len(p['preview'])>0,'NFL composite preview')
cases.append(('NFL composite',len(p['preview'])))

s=gf.compile_description('Five CFB players: four from the same school and same position, but the fifth is from the same school and a different position')
f=gf.feasibility(s)
ck(s['relationship_predicate']=='CFB_SCHOOL_POSITION_CONTRAST','CFB contrast parse')
ck(f['status']=='SUPPORTED','CFB contrast support')
p=gf.preview(s,6,'v14-cfb-contrast')
ck(len(p['preview'])>0,'CFB contrast preview')
for x in p['preview']:
    labels=[i['label'] for i in x['payload']['items']]
    ck(x['payload']['answer'] in labels,'contrast answer visible')
cases.append(('CFB contrast',len(p['preview'])))

s=gf.compile_description('Four CFB players who transferred exactly once')
f=gf.feasibility(s)
ck(s['relationship_predicate']=='CFB_TRANSFER_COUNT','transfer parse')
ck(f['status']=='SUPPORTED' and f['estimated_candidates']>1000,'transfer support')
p=gf.preview(s,6,'v14-transfer')
ck(len(p['preview'])>0,'transfer preview')
cases.append(('CFB transfer exactly once',len(p['preview'])))

s=gf.compile_description('Four NFL players who were teammates before 2015')
f=gf.feasibility(s)
ck(s['relationship_predicate']=='NFL_TEAMMATE_TIME','temporal teammate parse')
ck(s['filters'].get('season_max')==2014,'before year filter')
ck(f['status']=='SUPPORTED','temporal support')
p=gf.preview(s,6,'v14-teammates')
ck(len(p['preview'])>0,'temporal teammate preview')
cases.append(('NFL teammate before 2015',len(p['preview'])))

s=gf.compile_description('Four players who won an award before being drafted')
f=gf.feasibility(s)
ck(f['status']=='NEEDS_IDENTITY','cross-domain identity must block')
cases.append(('award-before-draft blocked',f['status']))

# publish/unpublish smoke on advanced mode
p=gf.preview('Four CFB players who transferred exactly once',4,'v14-publish')
r=gf.publish(p['spec_id'],'factory_v14_transfer_test',40,'v14-publish-full')
ck(r['status']=='PUBLISHED' and r['published_puzzles']>0,'publish advanced')
u=gf.unpublish('factory_v14_transfer_test')
ck(u['status']=='UNPUBLISHED','unpublish advanced')

c=sqlite3.connect(gf.DB)
ck(not c.execute('PRAGMA foreign_key_check').fetchall(),'foreign keys')
ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity')
c.close()
print(json.dumps({'status':'PASS','cases':cases,'publish':r,'unpublish':u},indent=2))
