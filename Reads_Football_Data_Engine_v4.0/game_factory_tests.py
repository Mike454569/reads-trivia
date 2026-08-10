import json, sqlite3
import game_factory

def check(cond,msg):
    if not cond: raise AssertionError(msg)

# NL parsing and support checks
s=game_factory.compile_description('Four NFL players drafted by the same team')
check(s['competition_id']=='NFL' and s['relationship_predicate']=='DRAFTED_BY','draft parser')
check(game_factory.feasibility(s)['status']=='SUPPORTED','draft feasibility')

s=game_factory.compile_description('Five NFL players, four attended SEC schools and one did not')
check(s['competition_id']=='NFL','explicit NFL must beat SEC CFB hint')
check(game_factory.feasibility(s)['status']=='NEEDS_DATA','missing NFL college data must be blocked')

x=game_factory.preview('Five FBS college players: four from the same school and one odd one out',limit=8,seed='test-suite')
check(x['feasibility']['status']=='SUPPORTED','CFB roster feasibility')
check(len(x['preview'])>0,'CFB preview empty')
for p in x['preview']:
    labels=[i['label'] for i in p['payload']['items']]
    check(len(labels)==len(set(labels)),'duplicate display items')
    check(p['payload']['answer'] in labels,'odd-one-out answer not displayed')

x=game_factory.preview('Order four NFL players by draft pick',limit=5,seed='test-order')
check(x['feasibility']['status']=='SUPPORTED' and len(x['preview'])==5,'ordering preview')
for p in x['preview']:
    check(len(p['payload']['solution'])==4,'ordering solution size')

c=sqlite3.connect(game_factory.DB)
check(not c.execute('PRAGMA foreign_key_check').fetchall(),'foreign key errors')
c.close()
print(json.dumps({'status':'PASS','tests':5},indent=2))
