"""Reads v2.2 Growth Engine: SEO, referrals, sharing, experiments, creator discovery."""
from pathlib import Path
import sqlite3,json,hashlib,re,secrets,datetime as dt,math,html
ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"
BASE_URL="https://reads.football"

def db():
    c=sqlite3.connect(DB,timeout=60);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");return c
def hid(prefix,*parts): return prefix+":"+hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:24]
def slugify(s):
    s=re.sub(r"[^a-z0-9]+","-",str(s).lower()).strip("-")
    return s[:80] or "item"
def unique_slug(c,base,entity_id):
    slug=base
    row=c.execute("SELECT entity_id FROM seo_entities WHERE slug=?",(slug,)).fetchone()
    if row and row["entity_id"]!=entity_id: slug=f"{base}-{hashlib.sha1(entity_id.encode()).hexdigest()[:7]}"
    return slug
def build_seo_entities():
    c=db();counts={}
    # NFL players
    n=0
    for r in c.execute("SELECT player_id,display_name,primary_position,primary_school_id FROM canonical_players WHERE verification_status IN ('SOURCE_BACKED','VERIFIED_STABLE_ID')"):
        base="nfl-player-"+slugify(r["display_name"]);slug=unique_slug(c,base,r["player_id"])
        title=f"{r['display_name']} NFL Trivia, Career & College | Reads"
        desc=f"Play football trivia about {r['display_name']} and explore verified NFL career, draft, college and teammate connections on Reads."
        payload={"name":r["display_name"],"position":r["primary_position"],"school_id":r["primary_school_id"]}
        c.execute("""INSERT OR REPLACE INTO seo_entities(seo_id,entity_type,entity_id,slug,title,meta_description,canonical_path,indexable,priority,payload_json,updated_at)
                     VALUES(?,?,?,?,?,?,?,1,.72,?,CURRENT_TIMESTAMP)""",
                  (hid("SEO","nfl_player",r["player_id"]),"nfl_player",r["player_id"],slug,title,desc,f"/football/nfl/players/{slug}",json.dumps(payload,sort_keys=True)));n+=1
    counts["nfl_players"]=n
    # CFB players
    n=0
    for r in c.execute("SELECT cfb_player_id,display_name,hometown_state FROM canonical_cfb_players WHERE verification_status='SOURCE_BACKED'"):
        base="cfb-player-"+slugify(r["display_name"]);slug=unique_slug(c,base,r["cfb_player_id"])
        title=f"{r['display_name']} College Football Trivia | Reads"
        desc=f"Play college football trivia about {r['display_name']} and explore verified school, roster, transfer and NFL connections on Reads."
        c.execute("""INSERT OR REPLACE INTO seo_entities(seo_id,entity_type,entity_id,slug,title,meta_description,canonical_path,indexable,priority,payload_json,updated_at)
                     VALUES(?,?,?,?,?,?,?,1,.58,?,CURRENT_TIMESTAMP)""",
                  (hid("SEO","cfb_player",r["cfb_player_id"]),"cfb_player",r["cfb_player_id"],slug,title,desc,f"/football/cfb/players/{slug}",json.dumps({"name":r["display_name"],"state":r["hometown_state"]},sort_keys=True)));n+=1
    counts["cfb_players"]=n
    # Schools
    n=0
    for r in c.execute("SELECT school_id,school_name FROM schools WHERE status='CANONICAL'"):
        slug=unique_slug(c,"college-"+slugify(r["school_name"]),r["school_id"])
        title=f"{r['school_name']} Football Trivia, Players & History | Reads"
        desc=f"Play {r['school_name']} football trivia and explore verified players, NFL draft connections, games, rivals and history."
        c.execute("""INSERT OR REPLACE INTO seo_entities VALUES(?,?,?,?,?,?,?,1,.86,?,CURRENT_TIMESTAMP)""",
                  (hid("SEO","school",r["school_id"]),"school",r["school_id"],slug,title,desc,f"/football/college/{slug}",json.dumps({"name":r["school_name"]})));n+=1
    counts["schools"]=n
    # NFL franchises
    n=0
    for r in c.execute("SELECT franchise_id,display_name,team_codes FROM franchises"):
        slug=unique_slug(c,"nfl-"+slugify(r["display_name"]),r["franchise_id"])
        title=f"{r['display_name']} Trivia, Players & History | Reads"
        desc=f"Play {r['display_name']} trivia and explore verified players, drafts, seasons, championships and football connections."
        c.execute("""INSERT OR REPLACE INTO seo_entities VALUES(?,?,?,?,?,?,?,1,.94,?,CURRENT_TIMESTAMP)""",
                  (hid("SEO","franchise",r["franchise_id"]),"franchise",r["franchise_id"],slug,title,desc,f"/football/nfl/teams/{slug}",json.dumps({"name":r["display_name"],"codes":r["team_codes"]})));n+=1
    counts["franchises"]=n
    c.commit();c.close();return counts

def rebuild_internal_links():
    c=db();c.execute("DELETE FROM seo_internal_links");n=0
    # NFL player -> school
    for p in c.execute("""SELECT e.seo_id,e.entity_id,cp.primary_school_id,cp.display_name FROM seo_entities e
                         JOIN canonical_players cp ON cp.player_id=e.entity_id
                         WHERE e.entity_type='nfl_player' AND cp.primary_school_id IS NOT NULL"""):
        s=c.execute("SELECT seo_id FROM seo_entities WHERE entity_type='school' AND entity_id=?",(p["primary_school_id"],)).fetchone()
        if s:
            c.execute("INSERT OR IGNORE INTO seo_internal_links VALUES(?,?,?,?,?)",(p["seo_id"],s[0],p["display_name"]+" college","ATTENDED",1.0));n+=1
    # Stable/production CFB-NFL identity links in both directions.
    for r in c.execute("SELECT cfb_player_id,nfl_player_key FROM cross_league_identity_bridge WHERE production_safe=1"):
        a=c.execute("SELECT seo_id,title FROM seo_entities WHERE entity_type='cfb_player' AND entity_id=?",(r["cfb_player_id"],)).fetchone()
        b=c.execute("SELECT seo_id,title FROM seo_entities WHERE entity_type='nfl_player' AND entity_id=?",(r["nfl_player_key"],)).fetchone()
        if a and b:
            c.execute("INSERT OR IGNORE INTO seo_internal_links VALUES(?,?,?,?,?)",(a[0],b[0],"NFL career","SAME_PERSON",1.3))
            c.execute("INSERT OR IGNORE INTO seo_internal_links VALUES(?,?,?,?,?)",(b[0],a[0],"college career","SAME_PERSON",1.3));n+=2
    c.commit();c.close();return n

def render_seo_page(slug):
    c=db();e=c.execute("SELECT * FROM seo_entities WHERE slug=? AND indexable=1",(slug,)).fetchone()
    if not e:c.close();return None
    links=[dict(r) for r in c.execute("""SELECT t.canonical_path,t.title,l.anchor_text,l.relationship
      FROM seo_internal_links l JOIN seo_entities t ON t.seo_id=l.target_seo_id
      WHERE l.source_seo_id=? ORDER BY l.weight DESC LIMIT 20""",(e["seo_id"],))]
    puzzles=[dict(r) for r in c.execute("""SELECT puzzle_id,mode_id,difficulty_band FROM puzzle_catalog
      WHERE eligible=1 AND source_entity_id=? ORDER BY popularity_proxy DESC LIMIT 12""",(e["entity_id"],))]
    c.close()
    payload=json.loads(e["payload_json"])
    structured={"@context":"https://schema.org","@type":"WebPage","name":e["title"],
                "description":e["meta_description"],"url":BASE_URL+e["canonical_path"],
                "about":{"@type":"Thing","name":payload.get("name",e["title"])}}
    return {"slug":e["slug"],"title":e["title"],"meta_description":e["meta_description"],
            "canonical_url":BASE_URL+e["canonical_path"],"entity_type":e["entity_type"],
            "entity_id":e["entity_id"],"payload":payload,"json_ld":structured,
            "internal_links":links,"featured_puzzles":puzzles}

def create_referral(user,campaign="organic"):
    code=hashlib.sha1((user+"|"+campaign).encode()).hexdigest()[:9]
    c=db();c.execute("INSERT OR IGNORE INTO referral_codes(referral_code,owner_user_id,campaign) VALUES(?,?,?)",(code,user,campaign));c.commit();c.close()
    return {"referral_code":code,"url":f"{BASE_URL}/?ref={code}"}

def attribute_referral(code,user=None,anonymous_id=None,source="share",medium="referral",object_type=None,object_id=None):
    c=db();r=c.execute("SELECT * FROM referral_codes WHERE referral_code=? AND active=1",(code,)).fetchone()
    if not r:c.close();return {"status":"INVALID"}
    if r["max_uses"] is not None and r["use_count"]>=r["max_uses"]:c.close();return {"status":"EXHAUSTED"}
    aid=hid("ATTR",code,user or anonymous_id or secrets.token_hex(4))
    c.execute("""INSERT OR IGNORE INTO referral_attribution(
      attribution_id,referral_code,referred_user_id,anonymous_id,source,medium,campaign,object_type,object_id)
      VALUES(?,?,?,?,?,?,?,?,?)""",(aid,code,user,anonymous_id,source,medium,r["campaign"],object_type,object_id))
    c.execute("UPDATE referral_codes SET use_count=use_count+1 WHERE referral_code=?",(code,))
    c.commit();c.close();return {"status":"ATTRIBUTED","attribution_id":aid}

def mark_referral_signup(user):
    c=db();c.execute("UPDATE referral_attribution SET referred_user_id=?,signup_at=CURRENT_TIMESTAMP WHERE referred_user_id IS NULL AND attribution_id=(SELECT attribution_id FROM referral_attribution WHERE referred_user_id IS NULL ORDER BY first_touch_at DESC LIMIT 1)",(user,));c.commit();c.close()

def create_share(user,share_type,object_type,object_id,headline,body=None,visual=None):
    code=secrets.token_urlsafe(7).replace("-","").replace("_","")[:9]
    sid=hid("SHARE",code,object_type,object_id)
    deep=f"{BASE_URL}/s/{code}"
    c=db();c.execute("""INSERT INTO share_artifacts(share_id,user_id,share_type,object_type,object_id,share_code,headline,body_text,visual_payload_json,deep_link)
      VALUES(?,?,?,?,?,?,?,?,?,?)""",(sid,user,share_type,object_type,object_id,code,headline,body,json.dumps(visual or {},sort_keys=True),deep))
    c.commit();c.close();return {"share_id":sid,"share_code":code,"deep_link":deep}

def daily_share(user,slate_date,score,streak=None,results=None):
    results=results or []
    # Spoiler-safe blocks: result states only, no answers.
    blocks=["🟩" if x in (True,1,"correct") else "🟥" for x in results]
    visual={"date":slate_date,"score":score,"streak":streak,"grid":"".join(blocks),"spoiler_safe":True}
    body=f"Reads Daily {slate_date} — {score} pts"+(f" • 🔥 {streak}" if streak else "")
    return create_share(user,"DAILY_RESULT","daily_slate",slate_date,"Reads Daily",body,visual)

def challenge_share(user,challenge_id,headline="Think you can beat me?"):
    c=db();ch=c.execute("SELECT * FROM challenges WHERE challenge_id=?",(challenge_id,)).fetchone()
    if not ch:c.close();raise KeyError(challenge_id)
    code=secrets.token_urlsafe(7).replace("-","").replace("_","")[:9];vid=hid("VCH",challenge_id,code)
    link=f"{BASE_URL}/challenge/{code}"
    c.execute("""INSERT INTO viral_challenge_links(viral_link_id,challenge_id,creator_user_id,share_code,headline,deep_link,expires_at)
      VALUES(?,?,?,?,?,?,?)""",(vid,challenge_id,user,code,headline,link,ch["expires_at"]))
    c.commit();c.close()
    create_share(user,"CHALLENGE","challenge",challenge_id,headline,"Same puzzles. Same rules. Beat my score.",{"spoiler_safe":True,"mode_id":ch["mode_id"]})
    return {"viral_link_id":vid,"share_code":code,"deep_link":link}

def assign_experiment(experiment_id,subject_key):
    c=db();old=c.execute("SELECT variant_key FROM experiment_assignments WHERE experiment_id=? AND subject_key=?",(experiment_id,subject_key)).fetchone()
    if old:c.close();return old[0]
    e=c.execute("SELECT * FROM growth_experiments WHERE experiment_id=? AND status='RUNNING'",(experiment_id,)).fetchone()
    if not e:c.close();return None
    variants=json.loads(e["variants_json"])
    bucket=int(hashlib.sha256((experiment_id+"|"+subject_key).encode()).hexdigest()[:8],16)%10000/100
    cumulative=0;chosen=None
    for v in variants:
        cumulative+=float(v["weight"]); 
        if bucket<cumulative:chosen=v["key"];break
    chosen=chosen or variants[-1]["key"]
    c.execute("INSERT INTO experiment_assignments VALUES(?,?,?,CURRENT_TIMESTAMP)",(experiment_id,subject_key,chosen));c.commit();c.close();return chosen

def track(event_name,user=None,anonymous_id=None,share_code=None,referral_code=None,campaign_id=None,object_type=None,object_id=None,properties=None):
    eid=hid("GE",event_name,user or anonymous_id or "anon",dt.datetime.now().timestamp())
    c=db();c.execute("INSERT INTO growth_events VALUES(?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
      (eid,user,anonymous_id,event_name,share_code,referral_code,campaign_id,object_type,object_id,json.dumps(properties or {},sort_keys=True)))
    if share_code and event_name=="share_click":c.execute("UPDATE share_artifacts SET click_count=click_count+1 WHERE share_code=?",(share_code,))
    c.commit();c.close();return eid

def rebuild_creator_discovery():
    c=db();c.execute("DELETE FROM creator_discovery_scores");n=0
    for cr in c.execute("SELECT * FROM creator_profiles"):
        metrics=c.execute("""SELECT COALESCE(SUM(m.plays),0),COALESCE(SUM(m.likes),0),COALESCE(AVG(m.quality_score),0),
          COALESCE(SUM(m.reports),0),COALESCE(SUM(m.completions),0)
          FROM community_games g LEFT JOIN community_game_metrics m USING(community_game_id)
          WHERE g.creator_user_id=? AND g.publish_status='PUBLISHED'""",(cr["user_id"],)).fetchone()
        plays,likes,quality,reports,completions=metrics
        completion_quality=min(100,(completions/max(1,plays))*100)
        trending=math.log1p(plays)*9+math.log1p(likes)*12
        follower_velocity=math.log1p(cr["follower_count"])*8
        play_velocity=math.log1p(plays)*10
        penalty=min(100,reports*12)
        score=max(0,trending*.3+quality*.25+follower_velocity*.15+play_velocity*.2+completion_quality*.1-penalty)
        c.execute("INSERT INTO creator_discovery_scores VALUES(?,?,?,?,?,?,?, ?,CURRENT_TIMESTAMP)",
                  (cr["user_id"],trending,quality,follower_velocity,play_velocity,completion_quality,penalty,score));n+=1
    c.commit();c.close();return n

def evaluate_referral_rewards(owner_user_id):
    c=db()
    refs=list(c.execute("SELECT referral_code FROM referral_codes WHERE owner_user_id=?",(owner_user_id,)))
    earned=[]
    for rr in c.execute("SELECT * FROM referral_reward_rules WHERE active=1"):
        total=0
        for rc in refs:
            if rr["milestone_type"]=="QUALIFIED_REFERRALS":
                total+=c.execute("SELECT COUNT(*) FROM referral_attribution WHERE referral_code=? AND qualified_at IS NOT NULL",(rc[0],)).fetchone()[0]
        if total>=rr["milestone_value"]:
            for rc in refs[:1]:
                rid=hid("RWD",rr["reward_rule_id"],owner_user_id,rc[0])
                c.execute("""INSERT OR IGNORE INTO referral_rewards_earned(reward_id,reward_rule_id,owner_user_id,referral_code)
                             VALUES(?,?,?,?)""",(rid,rr["reward_rule_id"],owner_user_id,rc[0]))
                earned.append({"rule":rr["reward_rule_id"],"reward":json.loads(rr["reward_payload_json"])})
    c.commit();c.close();return earned

def queue_social_content(content_type,object_type,object_id,headline,hook=None,payload=None):
    cid=hid("SOC",content_type,object_type,object_id,headline)
    c=db();c.execute("""INSERT OR REPLACE INTO social_content_queue(content_id,content_type,object_type,object_id,headline,hook_text,payload_json)
      VALUES(?,?,?,?,?,?,?)""",(cid,content_type,object_type,object_id,headline,hook,json.dumps(payload or {},sort_keys=True)))
    c.commit();c.close();return {"content_id":cid}

def queue_daily_social(slate_date):
    c=db();rows=list(c.execute("SELECT slot_key,mode_id,puzzle_id FROM daily_slates WHERE slate_date=? AND status='READY'",(slate_date,)));c.close()
    if not rows:return {"status":"NO_SLATE"}
    return queue_social_content("DAILY_PROMO","daily_slate",slate_date,
        f"Today's Reads Football challenge is live",
        "Six football tests. One Daily score. How many can you solve?",
        {"slate_date":slate_date,"slots":[dict(r) for r in rows],"deep_link":f"{BASE_URL}/daily/{slate_date}"})

def build_daily_growth_metrics(date=None):
    date=date or dt.date.today().isoformat();c=db()
    metrics={}
    queries={
      "share_clicks":"SELECT COUNT(*) FROM growth_events WHERE event_name='share_click' AND date(occurred_at)=?",
      "referral_first_touches":"SELECT COUNT(*) FROM referral_attribution WHERE date(first_touch_at)=?",
      "referral_signups":"SELECT COUNT(*) FROM referral_attribution WHERE date(signup_at)=?",
      "shares_created":"SELECT COUNT(*) FROM share_artifacts WHERE date(created_at)=?",
      "challenge_links_created":"SELECT COUNT(*) FROM viral_challenge_links WHERE date(created_at)=?"
    }
    for key,q in queries.items():
        val=c.execute(q,(date,)).fetchone()[0];metrics[key]=val
        c.execute("INSERT OR REPLACE INTO growth_daily_metrics VALUES(?,?,?)",(date,key,val))
    c.commit();c.close();return metrics
