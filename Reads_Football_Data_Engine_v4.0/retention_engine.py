"""Reads v1.8 retention engine: telemetry, empirical difficulty, personalization, XP/ranks/streaks/challenges."""
from pathlib import Path
import sqlite3,json,hashlib,math,random,datetime as dt

ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"

def db(): 
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def uid(): return "EV:"+hashlib.sha1((str(dt.datetime.now(dt.timezone.utc))+str(random.random())).encode()).hexdigest()[:22]
def division(r):
    if r<900:return "ROOKIE"
    if r<1050:return "BRONZE"
    if r<1200:return "SILVER"
    if r<1400:return "GOLD"
    if r<1600:return "PLATINUM"
    if r<1800:return "DIAMOND"
    if r<2000:return "ALL-PRO"
    return "GOAT"
def band(score):
    return "EASY" if score<.35 else "MEDIUM" if score<.55 else "HARD" if score<.75 else "EXPERT"

def ensure_user(c,user):
    c.execute("INSERT OR IGNORE INTO users_game_profile(user_id) VALUES(?)",(user,))

def record_event(user,mode,event_type,puzzle=None,correct=None,response_ms=None,wrong=0,hints=0,competition=None,metadata=None):
    c=db(); ensure_user(c,user)
    eid=uid()
    c.execute("""INSERT INTO gameplay_events(event_id,user_id,puzzle_id,mode_id,competition_id,event_type,is_correct,
      response_ms,wrong_guesses,hints_used,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
      (eid,user,puzzle,mode,competition,event_type,None if correct is None else int(correct),response_ms,wrong,hints,json.dumps(metadata or {})))
    c.execute("UPDATE users_game_profile SET last_active_at=CURRENT_TIMESTAMP WHERE user_id=?",(user,))
    if event_type in ("ANSWER","COMPLETE","ABANDON") and puzzle: calibrate_puzzle(c,puzzle)
    if event_type=="ANSWER": update_skill(c,user,mode,bool(correct),response_ms)
    c.commit(); c.close()
    return eid

def calibrate_puzzle(c,puzzle):
    rows=c.execute("""SELECT event_type,is_correct,response_ms,wrong_guesses,hints_used FROM gameplay_events
                      WHERE puzzle_id=? AND event_type IN ('ANSWER','ABANDON')""",(puzzle,)).fetchall()
    if not rows:return
    attempts=len(rows); correct=sum(1 for r in rows if r["is_correct"]==1)
    solved=[r for r in rows if r["is_correct"] is not None]
    times=[r["response_ms"] for r in solved if r["response_ms"] is not None]
    aband=sum(1 for r in rows if r["event_type"]=="ABANDON")
    sr=correct/attempts; ar=aband/attempts
    aw=sum(r["wrong_guesses"] or 0 for r in rows)/attempts
    ah=sum(r["hints_used"] or 0 for r in rows)/attempts
    avg=sum(times)/len(times) if times else None
    # difficulty rises with misses, abandonment, wrong guesses, hints and slow answers.
    time_component=min(1,(avg or 15000)/45000)
    score=max(0,min(1,.58*(1-sr)+.14*ar+.10*min(1,aw/3)+.08*min(1,ah/2)+.10*time_component))
    conf=min(1,attempts/50)
    c.execute("""INSERT OR REPLACE INTO puzzle_difficulty_live VALUES
      (?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
      (puzzle,attempts,correct,sr,avg,aw,ah,ar,score,band(score),conf))

def update_skill(c,user,mode,correct,response_ms):
    row=c.execute("SELECT * FROM mode_user_skill WHERE user_id=? AND mode_id=?",(user,mode)).fetchone()
    rating=float(row["rating"]) if row else 1000
    games=int(row["games_played"]) if row else 0
    wins=int(row["wins"]) if row else 0
    ca=int(row["correct_answers"]) if row else 0
    att=int(row["attempts"]) if row else 0
    oldavg=row["avg_response_ms"] if row else None
    # Single-player skill update: expectation against a 50% baseline; speed is a small bonus only when correct.
    delta=(16 if correct else -12)
    if correct and response_ms is not None and response_ms<10000: delta+=2
    rating=max(100,min(2500,rating+delta))
    games+=1; wins+=int(correct); ca+=int(correct); att+=1
    avg=response_ms if oldavg is None else (oldavg*(att-1)+(response_ms or oldavg))/att
    c.execute("""INSERT OR REPLACE INTO mode_user_skill(
              user_id,mode_id,rating,games_played,wins,correct_answers,attempts,avg_response_ms,skill_band,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
              (user,mode,rating,games,wins,ca,att,avg,division(rating)))

def ranked_result(user,queue,won,opponent_rating=1000,season="S2026_PRESEASON"):
    c=db(); ensure_user(c,user)
    r=c.execute("SELECT * FROM ranked_ratings WHERE season_id=? AND user_id=? AND queue_id=?",(season,user,queue)).fetchone()
    rating=float(r["rating"]) if r else 1000
    gp=int(r["games_played"]) if r else 0; w=int(r["wins"]) if r else 0; l=int(r["losses"]) if r else 0
    exp=1/(1+10**((opponent_rating-rating)/400)); actual=1 if won else 0
    k=40 if gp<10 else 24
    nr=round(rating+k*(actual-exp),1)
    peak=max(float(r["peak_rating"]) if r else 1000,nr)
    c.execute("""INSERT OR REPLACE INTO ranked_ratings(season_id,user_id,queue_id,rating,games_played,wins,losses,draws,peak_rating,division,updated_at)
                 VALUES(?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",(season,user,queue,nr,gp+1,w+int(won),l+int(not won),0,peak,division(nr)))
    xp=40 if won else 15
    c.execute("UPDATE users_game_profile SET total_xp=total_xp+?, level=1+CAST((total_xp+?)/500 AS INTEGER) WHERE user_id=?",(xp,xp,user))
    c.commit(); c.close(); return {"rating":nr,"division":division(nr),"delta":round(nr-rating,1),"xp":xp}

def update_streak(user,date=None):
    date=date or dt.date.today().isoformat(); c=db(); ensure_user(c,user)
    c.execute("""INSERT INTO daily_streak_events(user_id,streak_date,qualifying_plays,qualified) VALUES(?,?,1,1)
                 ON CONFLICT(user_id,streak_date) DO UPDATE SET qualifying_plays=qualifying_plays+1,qualified=1""",(user,date))
    prof=c.execute("SELECT current_streak,longest_streak,last_streak_date FROM users_game_profile WHERE user_id=?",(user,)).fetchone()
    d=dt.date.fromisoformat(date); last=dt.date.fromisoformat(prof["last_streak_date"]) if prof["last_streak_date"] else None
    cur=prof["current_streak"]
    if last==d: pass
    elif last==d-dt.timedelta(days=1): cur+=1
    else: cur=1
    longest=max(prof["longest_streak"],cur)
    c.execute("UPDATE users_game_profile SET current_streak=?,longest_streak=?,last_streak_date=? WHERE user_id=?",(cur,longest,date,user))
    c.commit(); c.close(); return {"current_streak":cur,"longest_streak":longest}

def personalized_feed(user,limit=20):
    c=db(); ensure_user(c,user)
    skills={r["mode_id"]:r["rating"] for r in c.execute("SELECT * FROM mode_user_skill WHERE user_id=?",(user,))}
    played={r[0] for r in c.execute("SELECT DISTINCT puzzle_id FROM gameplay_events WHERE user_id=? AND puzzle_id IS NOT NULL",(user,))}
    rows=c.execute("""SELECT p.puzzle_id,p.mode_id,p.difficulty_score,p.difficulty_band,
                     COALESCE(d.empirical_score,p.difficulty_score) AS live_diff,
                     COALESCE(d.confidence,0) AS diff_conf
                     FROM puzzle_catalog p LEFT JOIN puzzle_difficulty_live d USING(puzzle_id)
                     WHERE p.eligible=1 ORDER BY RANDOM() LIMIT 2500""").fetchall()
    scored=[]
    for r in rows:
        if r["puzzle_id"] in played: continue
        rating=skills.get(r["mode_id"],1000)
        target=max(.15,min(.9,.45+(rating-1000)/1800))
        challenge_fit=1-abs(float(r["live_diff"] or .5)-target)
        novelty=1.0 if r["mode_id"] not in skills else .72
        empirical=.05*float(r["diff_conf"] or 0)
        score=.72*challenge_fit+.23*novelty+empirical+random.random()*.02
        reason="New mode for you" if r["mode_id"] not in skills else "Matched to your current skill"
        scored.append((score,r["puzzle_id"],r["mode_id"],reason))
    scored.sort(reverse=True)
    out=scored[:limit]
    c.execute("DELETE FROM personalization_feed_cache WHERE user_id=?",(user,))
    for i,x in enumerate(out,1):
        c.execute("INSERT INTO personalization_feed_cache(user_id,slot,puzzle_id,mode_id,reason,score) VALUES(?,?,?,?,?,?)",
                  (user,i,x[1],x[2],x[3],x[0]))
    c.commit(); c.close()
    return [{"puzzle_id":x[1],"mode_id":x[2],"reason":x[3],"score":round(x[0],4)} for x in out]

def create_challenge(user,mode,count=5,opponent=None):
    c=db(); ensure_user(c,user)
    rows=c.execute("SELECT puzzle_id FROM puzzle_catalog WHERE mode_id=? AND eligible=1 ORDER BY RANDOM() LIMIT ?",(mode,count)).fetchall()
    ids=[x[0] for x in rows]
    seed=hashlib.sha1(("|".join(ids)+user).encode()).hexdigest()[:16]
    cid="CH:"+hashlib.sha1((seed+str(dt.datetime.now())).encode()).hexdigest()[:20]
    c.execute("INSERT INTO challenges(challenge_id,creator_user_id,opponent_user_id,mode_id,seed,puzzle_ids_json) VALUES(?,?,?,?,?,?)",
              (cid,user,opponent,mode,seed,json.dumps(ids)))
    c.commit();c.close();return {"challenge_id":cid,"mode_id":mode,"seed":seed,"puzzle_ids":ids}

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    f=sp.add_parser("feed"); f.add_argument("user"); f.add_argument("--limit",type=int,default=10)
    e=sp.add_parser("event"); e.add_argument("user"); e.add_argument("mode"); e.add_argument("type"); e.add_argument("--puzzle"); e.add_argument("--correct",type=int); e.add_argument("--ms",type=int)
    r=sp.add_parser("ranked"); r.add_argument("user"); r.add_argument("queue"); r.add_argument("--won",type=int,required=True); r.add_argument("--opponent-rating",type=float,default=1000)
    s=sp.add_parser("streak"); s.add_argument("user"); s.add_argument("--date")
    ch=sp.add_parser("challenge"); ch.add_argument("user"); ch.add_argument("mode"); ch.add_argument("--count",type=int,default=5)
    a=ap.parse_args()
    if a.cmd=="feed": out=personalized_feed(a.user,a.limit)
    elif a.cmd=="event": out={"event_id":record_event(a.user,a.mode,a.type,a.puzzle,a.correct,a.ms)}
    elif a.cmd=="ranked": out=ranked_result(a.user,a.queue,bool(a.won),a.opponent_rating)
    elif a.cmd=="streak": out=update_streak(a.user,a.date)
    else: out=create_challenge(a.user,a.mode,a.count)
    print(json.dumps(out,indent=2))
