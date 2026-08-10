"""Reads Football v1.9 Community + Creator engine."""
from pathlib import Path
import sqlite3, json, hashlib, datetime as dt, random, re
import game_factory

ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"

def db():
    c=sqlite3.connect(DB,timeout=30); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c

def hid(prefix,*parts):
    raw="|".join(str(x) for x in parts)+(str(dt.datetime.now(dt.timezone.utc).timestamp()) if prefix in {"PLAY","NOTE","COMMENT","REPORT","ACTION"} else "")
    return prefix+":"+hashlib.sha1(raw.encode()).hexdigest()[:22]

def ensure_user(c,user):
    c.execute("INSERT OR IGNORE INTO users_game_profile(user_id) VALUES(?)",(user,))

def create_creator(user,handle,display_name=None,bio=None):
    c=db(); ensure_user(c,user)
    handle=re.sub(r"[^a-zA-Z0-9_]+","",handle)[:24]
    if len(handle)<3: raise ValueError("handle must be at least 3 characters")
    c.execute("""INSERT INTO creator_profiles(user_id,handle,display_name,bio) VALUES(?,?,?,?)
                 ON CONFLICT(user_id) DO UPDATE SET handle=excluded.handle,
                 display_name=COALESCE(excluded.display_name,creator_profiles.display_name),
                 bio=COALESCE(excluded.bio,creator_profiles.bio),updated_at=CURRENT_TIMESTAMP""",
              (user,handle,display_name,bio))
    c.commit(); c.close(); return {"user_id":user,"handle":handle}

def create_from_description(user,title,description,game_description,preview_limit=12,tags=None):
    c=db(); ensure_user(c,user)
    if not c.execute("SELECT 1 FROM creator_profiles WHERE user_id=?",(user,)).fetchone():
        c.close(); raise ValueError("creator profile required")
    c.close()

    pv=game_factory.preview(game_description,limit=preview_limit,seed="community_preview")
    feas=pv["feasibility"]
    if feas["status"]!="SUPPORTED":
        return {"status":"NEEDS_DATA","feasibility":feas,"preview":pv.get("preview",[])}

    spec=pv["spec"]; sid=pv["spec_id"]
    gid=hid("CG",user,title,sid)
    c=db()
    c.execute("""INSERT INTO community_games(
      community_game_id,creator_user_id,title,description,competition_id,mechanic,source_spec_id,
      visibility,moderation_status,publish_status,difficulty_label,estimated_puzzle_count,
      tags_json,rules_json)
      VALUES(?,?,?,?,?,?,?,'PRIVATE','DRAFT','DRAFT',?,?,?,?)""",
      (gid,user,title[:80],description[:500] if description else None,spec.get("competition_id"),
       spec.get("mechanic"),sid,
       pv["preview"][0]["difficulty_band"] if pv["preview"] else None,
       int(feas.get("estimated_candidates",0)),
       json.dumps(tags or []),json.dumps(spec,sort_keys=True)))
    c.execute("INSERT INTO community_game_metrics(community_game_id) VALUES(?)",(gid,))
    c.commit();c.close()
    return {"status":"DRAFT_CREATED","community_game_id":gid,"spec_id":sid,
            "feasibility":feas,"preview":pv["preview"],"excluded_by_qa":pv["excluded_by_qa"]}

def submit_for_review(user,gid,visibility="PUBLIC"):
    c=db()
    g=c.execute("SELECT * FROM community_games WHERE community_game_id=? AND creator_user_id=?",(gid,user)).fetchone()
    if not g: c.close(); raise KeyError(gid)
    c.execute("""UPDATE community_games SET visibility=?,moderation_status='PENDING_REVIEW',
                 publish_status='READY',updated_at=CURRENT_TIMESTAMP WHERE community_game_id=?""",(visibility,gid))
    c.commit(); c.close(); return {"status":"PENDING_REVIEW","community_game_id":gid}

def moderate(gid,action,moderator="SYSTEM",reason=None):
    action=action.upper()
    if action not in {"APPROVE","REJECT","HIDE"}: raise ValueError(action)
    c=db(); g=c.execute("SELECT * FROM community_games WHERE community_game_id=?",(gid,)).fetchone()
    if not g: c.close(); raise KeyError(gid)
    status={"APPROVE":"APPROVED","REJECT":"REJECTED","HIDE":"HIDDEN"}[action]
    publish="READY" if action=="APPROVE" else "DRAFT" if action=="REJECT" else "UNPUBLISHED"
    aid=hid("ACTION",gid,action,moderator)
    c.execute("UPDATE community_games SET moderation_status=?,publish_status=?,updated_at=CURRENT_TIMESTAMP WHERE community_game_id=?",
              (status,publish,gid))
    c.execute("INSERT INTO moderation_actions VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)",(aid,gid,moderator,action,reason))
    c.commit();c.close();return {"community_game_id":gid,"moderation_status":status}

def publish(user,gid,puzzle_limit=250):
    c=db(); g=c.execute("SELECT * FROM community_games WHERE community_game_id=? AND creator_user_id=?",(gid,user)).fetchone()
    if not g: c.close(); raise KeyError(gid)
    if g["moderation_status"]!="APPROVED":
        c.close(); return {"status":"NOT_PUBLISHED","reason":"MODERATION_REQUIRED"}
    sid=g["source_spec_id"]; c.close()

    mode="community_"+gid.split(":")[-1][:12]
    pub=game_factory.publish(sid,mode_id=mode,candidate_limit=puzzle_limit,seed=gid)
    if pub.get("status")!="PUBLISHED": return pub

    c=db()
    ids=[r[0] for r in c.execute("SELECT puzzle_id FROM puzzle_catalog WHERE mode_id=? AND eligible=1 ORDER BY puzzle_id",(mode,))]
    c.execute("DELETE FROM community_game_puzzles WHERE community_game_id=?",(gid,))
    c.executemany("INSERT INTO community_game_puzzles VALUES(?,?,?,NULL)",[(gid,i+1,p) for i,p in enumerate(ids)])
    c.execute("""UPDATE community_games SET publish_status='PUBLISHED',visibility='PUBLIC',
                 published_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE community_game_id=?""",(gid,))
    c.execute("""UPDATE creator_profiles SET published_count=(SELECT COUNT(*) FROM community_games
                 WHERE creator_user_id=? AND publish_status='PUBLISHED'),updated_at=CURRENT_TIMESTAMP WHERE user_id=?""",(user,user))
    c.commit();c.close()
    return {"status":"PUBLISHED","community_game_id":gid,"mode_id":mode,"puzzle_count":len(ids)}

def unpublish(user,gid):
    c=db(); g=c.execute("SELECT source_spec_id FROM community_games WHERE community_game_id=? AND creator_user_id=?",(gid,user)).fetchone()
    if not g:c.close();raise KeyError(gid)
    c.execute("UPDATE community_games SET publish_status='UNPUBLISHED',visibility='PRIVATE',updated_at=CURRENT_TIMESTAMP WHERE community_game_id=?",(gid,))
    c.commit();c.close();return {"status":"UNPUBLISHED","community_game_id":gid}

def follow(user,creator,enabled=True):
    if user==creator: raise ValueError("cannot follow yourself")
    c=db();ensure_user(c,user);ensure_user(c,creator)
    if enabled:c.execute("INSERT OR IGNORE INTO creator_follows VALUES(?,?,CURRENT_TIMESTAMP)",(user,creator))
    else:c.execute("DELETE FROM creator_follows WHERE follower_user_id=? AND creator_user_id=?",(user,creator))
    c.execute("UPDATE creator_profiles SET follower_count=(SELECT COUNT(*) FROM creator_follows WHERE creator_user_id=?),updated_at=CURRENT_TIMESTAMP WHERE user_id=?",(creator,creator))
    c.execute("UPDATE creator_profiles SET following_count=(SELECT COUNT(*) FROM creator_follows WHERE follower_user_id=?),updated_at=CURRENT_TIMESTAMP WHERE user_id=?",(user,user))
    if enabled:
        nid=hid("NOTE",creator,user,"follow")
        c.execute("INSERT INTO creator_notifications(notification_id,user_id,notification_type,actor_user_id,message) VALUES(?,?, 'FOLLOW',?,?)",
                  (nid,creator,user,f"{user} followed you"))
    c.commit();c.close();return {"following":enabled}

def _toggle(table,user,gid,enabled,metric):
    c=db()
    if enabled:c.execute(f"INSERT OR IGNORE INTO {table}(community_game_id,user_id) VALUES(?,?)",(gid,user))
    else:c.execute(f"DELETE FROM {table} WHERE community_game_id=? AND user_id=?",(gid,user))
    c.execute(f"UPDATE community_game_metrics SET {metric}=(SELECT COUNT(*) FROM {table} WHERE community_game_id=?),updated_at=CURRENT_TIMESTAMP WHERE community_game_id=?",(gid,gid))
    if metric=="likes":
        creator=c.execute("SELECT creator_user_id FROM community_games WHERE community_game_id=?",(gid,)).fetchone()
        if creator:
            cu=creator[0]
            c.execute("""UPDATE creator_profiles SET total_likes=(SELECT COALESCE(SUM(m.likes),0) FROM community_game_metrics m
                         JOIN community_games g USING(community_game_id) WHERE g.creator_user_id=?),updated_at=CURRENT_TIMESTAMP WHERE user_id=?""",(cu,cu))
    recompute_scores(c,gid)
    c.commit();c.close();return {metric:enabled}

def like(user,gid,enabled=True): return _toggle("community_game_likes",user,gid,enabled,"likes")
def save(user,gid,enabled=True): return _toggle("community_game_saves",user,gid,enabled,"saves")

def start_play(gid,user=None):
    c=db(); g=c.execute("SELECT publish_status FROM community_games WHERE community_game_id=?",(gid,)).fetchone()
    if not g or g[0]!="PUBLISHED":c.close();raise ValueError("game is not published")
    pid=hid("PLAY",gid,user or "anon")
    n=c.execute("SELECT COUNT(*) FROM community_game_puzzles WHERE community_game_id=?",(gid,)).fetchone()[0]
    c.execute("INSERT INTO community_game_plays(play_id,community_game_id,user_id,puzzle_count) VALUES(?,?,?,?)",(pid,gid,user,n))
    c.commit();c.close();return {"play_id":pid,"puzzle_count":n}

def complete_play(play_id,correct,total_ms):
    c=db(); r=c.execute("SELECT community_game_id,puzzle_count FROM community_game_plays WHERE play_id=?",(play_id,)).fetchone()
    if not r:c.close();raise KeyError(play_id)
    gid,n=r; score=(correct/max(1,n))*100
    c.execute("""UPDATE community_game_plays SET completed_at=CURRENT_TIMESTAMP,correct_count=?,total_response_ms=?,score=? WHERE play_id=?""",(correct,total_ms,score,play_id))
    c.execute("""UPDATE community_game_metrics SET
      plays=(SELECT COUNT(*) FROM community_game_plays WHERE community_game_id=?),
      completions=(SELECT COUNT(*) FROM community_game_plays WHERE community_game_id=? AND completed_at IS NOT NULL),
      avg_score=(SELECT AVG(score) FROM community_game_plays WHERE community_game_id=? AND completed_at IS NOT NULL),
      avg_completion_ms=(SELECT AVG(total_response_ms) FROM community_game_plays WHERE community_game_id=? AND completed_at IS NOT NULL),
      updated_at=CURRENT_TIMESTAMP WHERE community_game_id=?""",(gid,gid,gid,gid,gid))
    creator=c.execute("SELECT creator_user_id FROM community_games WHERE community_game_id=?",(gid,)).fetchone()[0]
    c.execute("""UPDATE creator_profiles SET total_plays=(SELECT COUNT(*) FROM community_game_plays p JOIN community_games g
                 USING(community_game_id) WHERE g.creator_user_id=?),updated_at=CURRENT_TIMESTAMP WHERE user_id=?""",(creator,creator))
    recompute_scores(c,gid)
    c.commit();c.close();return {"score":score}

def comment(user,gid,body):
    body=(body or "").strip()
    if not body or len(body)>500: raise ValueError("comment must be 1-500 characters")
    c=db(); cid=hid("COMMENT",gid,user,body)
    c.execute("INSERT INTO community_game_comments VALUES(?,?,?,?,'VISIBLE',CURRENT_TIMESTAMP)",(cid,gid,user,body))
    c.execute("UPDATE community_game_metrics SET comments=(SELECT COUNT(*) FROM community_game_comments WHERE community_game_id=? AND status='VISIBLE') WHERE community_game_id=?",(gid,gid))
    recompute_scores(c,gid);c.commit();c.close();return {"comment_id":cid}

def report(user,gid,reason,detail=None):
    c=db();rid=hid("REPORT",gid,user,reason)
    c.execute("INSERT INTO community_game_reports(report_id,community_game_id,reporter_user_id,reason_code,detail) VALUES(?,?,?,?,?)",(rid,gid,user,reason,detail))
    c.execute("UPDATE community_game_metrics SET reports=(SELECT COUNT(*) FROM community_game_reports WHERE community_game_id=? AND status='OPEN') WHERE community_game_id=?",(gid,gid))
    reports=c.execute("SELECT COUNT(*) FROM community_game_reports WHERE community_game_id=? AND status='OPEN'",(gid,)).fetchone()[0]
    if reports>=5:
        c.execute("UPDATE community_games SET moderation_status='PENDING_REVIEW' WHERE community_game_id=?",(gid,))
    recompute_scores(c,gid);c.commit();c.close();return {"report_id":rid,"open_reports":reports}

def share(user,gid):
    c=db();code=hashlib.sha1(f"{gid}|{user}".encode()).hexdigest()[:10]
    c.execute("INSERT OR IGNORE INTO community_share_links(share_code,community_game_id,created_by) VALUES(?,?,?)",(code,gid,user))
    c.commit();c.close();return {"share_code":code}

def remix(user,parent_gid,title=None):
    c=db();p=c.execute("SELECT * FROM community_games WHERE community_game_id=? AND publish_status='PUBLISHED'",(parent_gid,)).fetchone()
    if not p:c.close();raise KeyError(parent_gid)
    ensure_user(c,user)
    gid=hid("CG",user,parent_gid,title or p["title"])
    c.execute("""INSERT INTO community_games(community_game_id,creator_user_id,title,description,competition_id,mechanic,
      source_spec_id,source_template_id,visibility,moderation_status,publish_status,difficulty_label,estimated_puzzle_count,
      cover_text,tags_json,rules_json) VALUES(?,?,?,?,?,?,?,?, 'PRIVATE','DRAFT','DRAFT',?,?,?,?,?)""",
      (gid,user,title or ("Remix: "+p["title"]),p["description"],p["competition_id"],p["mechanic"],p["source_spec_id"],p["source_template_id"],
       p["difficulty_label"],p["estimated_puzzle_count"],p["cover_text"],p["tags_json"],p["rules_json"]))
    c.execute("INSERT INTO community_game_metrics(community_game_id) VALUES(?)",(gid,))
    c.execute("INSERT INTO community_game_remixes VALUES(?,?,?,CURRENT_TIMESTAMP)",(gid,parent_gid,user))
    c.commit();c.close();return {"community_game_id":gid,"parent_game_id":parent_gid}

def recompute_scores(c,gid):
    m=c.execute("SELECT * FROM community_game_metrics WHERE community_game_id=?",(gid,)).fetchone()
    if not m:return
    plays=m["plays"]; likes=m["likes"]; saves=m["saves"]; comments=m["comments"]; reports=m["reports"]
    completion=(m["completions"]/plays) if plays else 0
    quality=max(0,min(100,45+20*completion+min(15,likes*.6)+min(10,saves*.8)-min(40,reports*8)))
    trending=math_log(1+plays)*8 + math_log(1+likes)*14 + math_log(1+saves)*10 + math_log(1+comments)*5 - reports*12
    c.execute("UPDATE community_game_metrics SET quality_score=?,trending_score=?,updated_at=CURRENT_TIMESTAMP WHERE community_game_id=?",(quality,trending,gid))
    creator=c.execute("SELECT creator_user_id FROM community_games WHERE community_game_id=?",(gid,)).fetchone()
    if creator:
        uid=creator[0]
        score=c.execute("""SELECT COALESCE(SUM(m.quality_score*0.2 + m.trending_score),0)
                           FROM community_game_metrics m JOIN community_games g USING(community_game_id)
                           WHERE g.creator_user_id=? AND g.publish_status='PUBLISHED'""",(uid,)).fetchone()[0]
        c.execute("UPDATE creator_profiles SET creator_score=?,updated_at=CURRENT_TIMESTAMP WHERE user_id=?",(score,uid))

def math_log(x):
    import math
    return math.log(x)

def trending(limit=20):
    c=db();rows=[dict(r) for r in c.execute("SELECT * FROM v_community_trending LIMIT ?",(limit,))];c.close();return rows


def following_feed(user,limit=30):
    c=db()
    rows=[dict(r) for r in c.execute("""
      SELECT g.community_game_id,g.title,g.creator_user_id,g.competition_id,g.mechanic,g.difficulty_label,
             g.published_at,m.plays,m.likes,m.saves,m.trending_score
      FROM creator_follows f JOIN community_games g ON g.creator_user_id=f.creator_user_id
      LEFT JOIN community_game_metrics m USING(community_game_id)
      WHERE f.follower_user_id=? AND g.publish_status='PUBLISHED'
        AND g.moderation_status='APPROVED' AND g.visibility='PUBLIC'
      ORDER BY g.published_at DESC,m.trending_score DESC LIMIT ?
    """,(user,limit))]
    c.close();return rows

def saved_games(user,limit=100):
    c=db()
    rows=[dict(r) for r in c.execute("""
      SELECT g.community_game_id,g.title,g.creator_user_id,g.competition_id,g.mechanic,g.difficulty_label,s.created_at
      FROM community_game_saves s JOIN community_games g USING(community_game_id)
      WHERE s.user_id=? ORDER BY s.created_at DESC LIMIT ?
    """,(user,limit))]
    c.close();return rows

def creator_profile(user):
    c=db()
    row=c.execute("SELECT * FROM creator_profiles WHERE user_id=?",(user,)).fetchone()
    if not row:c.close();return None
    out=dict(row)
    out["games"]=[dict(r) for r in c.execute("""
      SELECT g.community_game_id,g.title,g.competition_id,g.mechanic,g.difficulty_label,g.published_at,
             m.plays,m.likes,m.saves,m.trending_score,m.quality_score
      FROM community_games g LEFT JOIN community_game_metrics m USING(community_game_id)
      WHERE g.creator_user_id=? AND g.publish_status='PUBLISHED'
      ORDER BY g.published_at DESC LIMIT 50
    """,(user,))]
    c.close();return out

def creator_leaderboard(limit=20):
    c=db();rows=[dict(r) for r in c.execute("SELECT * FROM v_creator_leaderboard LIMIT ?",(limit,))];c.close();return rows

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("creator");a.add_argument("user");a.add_argument("handle");a.add_argument("--name")
    a=sp.add_parser("create");a.add_argument("user");a.add_argument("title");a.add_argument("description")
    a=sp.add_parser("trending");a.add_argument("--limit",type=int,default=10)
    args=ap.parse_args()
    if args.cmd=="creator":out=create_creator(args.user,args.handle,args.name)
    elif args.cmd=="create":out=create_from_description(args.user,args.title,None,args.description)
    else:out=trending(args.limit)
    print(json.dumps(out,indent=2))
