
from pathlib import Path
import sqlite3,csv,json,hashlib,uuid,datetime as dt,sys,re

ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def norm_school(s):
    return re.sub(r"[^a-z0-9]+"," ",str(s or "").lower()).strip()

def parse_int(v):
    try:
        if v in (None,""): return None
        return int(float(v))
    except: return None

def col(row,*names):
    for n in names:
        if n in row and row[n] not in (None,""): return row[n]
    return None

def resolve_school(conn,name):
    if not name: return None
    target=norm_school(name)
    for sid,sname in conn.execute("SELECT school_id,school_name FROM schools"):
        if norm_school(sname)==target: return sid
    for alias,sid in conn.execute("SELECT alias_name,school_id FROM school_aliases"):
        if norm_school(alias)==target: return sid
    return None

def begin_batch(conn,dataset,source_id,path):
    bid="BATCH:"+uuid.uuid4().hex[:20]
    conn.execute("""INSERT INTO import_batches(batch_id,dataset_name,source_id,source_file,source_sha256,status,transform_version)
                    VALUES (?,?,?,?,?,'STAGING','reads-import-v0.9')""",
                 (bid,dataset,source_id,str(path),sha256(path)))
    conn.commit()
    return bid

def reject(conn,bid,rownum,code,detail,raw):
    conn.execute("""INSERT INTO import_rejections(batch_id,row_number,reason_code,detail,raw_json)
                    VALUES (?,?,?,?,?)""",(bid,rownum,code,detail,json.dumps(raw,sort_keys=True)))

def stage_players(conn,bid,path):
    read=staged=rejected=0
    with open(path,newline="",encoding="utf-8-sig") as f:
        for i,row in enumerate(csv.DictReader(f),start=2):
            read+=1
            gsis=col(row,"gsis_id","player_id")
            name=col(row,"display_name","full_name","player_name")
            if not gsis or not name:
                reject(conn,bid,i,"MISSING_ID_OR_NAME","Player row needs stable ID + name",row);rejected+=1;continue
            h=col(row,"height","height_in")
            if h and isinstance(h,str) and "-" in h:
                try:
                    ft,inch=h.split("-",1); h=int(ft)*12+int(inch)
                except: h=None
            else: h=parse_int(h)
            vals=(bid,i,gsis,name,col(row,"birth_date"),h,parse_int(col(row,"weight","weight_lb")),
                  col(row,"college_name","college"),col(row,"position","pos"),
                  parse_int(col(row,"draft_year")),parse_int(col(row,"draft_round")),
                  parse_int(col(row,"draft_pick","draft_number")),col(row,"pfr_id"),
                  json.dumps(row,sort_keys=True))
            conn.execute("""INSERT INTO staging_players VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",vals);staged+=1
    return read,staged,rejected

def publish_players(conn,bid):
    published=0
    for r in conn.execute("""SELECT gsis_id,display_name,birth_date,height_in,weight_lb,college_name,position,
                             draft_year,draft_round,draft_pick,pfr_id FROM staging_players WHERE batch_id=?""",(bid,)):
        gsis,name,dob,h,w,college,pos,dy,dr,dp,pfr=r
        sid=resolve_school(conn,college)
        pid="GSIS:"+gsis
        conn.execute("""INSERT INTO canonical_players(player_id,gsis_id,pfr_id,display_name,birth_date,height_in,weight_lb,
                        primary_position,primary_school_id,verification_status,source_id)
                        VALUES (?,?,?,?,?,?,?,?,?,'SOURCE_BACKED','NFLVERSE_PLAYERS')
                        ON CONFLICT(player_id) DO UPDATE SET
                          gsis_id=excluded.gsis_id,pfr_id=COALESCE(excluded.pfr_id,canonical_players.pfr_id),
                          display_name=excluded.display_name,birth_date=COALESCE(excluded.birth_date,canonical_players.birth_date),
                          height_in=COALESCE(excluded.height_in,canonical_players.height_in),
                          weight_lb=COALESCE(excluded.weight_lb,canonical_players.weight_lb),
                          primary_position=COALESCE(excluded.primary_position,canonical_players.primary_position),
                          primary_school_id=COALESCE(excluded.primary_school_id,canonical_players.primary_school_id),
                          verification_status='SOURCE_BACKED',source_id='NFLVERSE_PLAYERS'""",
                     (pid,gsis,pfr,name,dob,h,w,pos,sid))
        if college and not sid:
            conn.execute("""INSERT INTO qa_issues(severity,entity_type,entity_id,field_name,issue_type,detail)
                            VALUES('WARN','canonical_player',?,'primary_school_id','UNMAPPED_SCHOOL',?)""",
                         (pid,f"Could not map college '{college}'"))
        published+=1
    return published

def stage_rosters(conn,bid,path):
    read=staged=rejected=0
    with open(path,newline="",encoding="utf-8-sig") as f:
        for i,row in enumerate(csv.DictReader(f),start=2):
            read+=1
            season=parse_int(col(row,"season"))
            team=col(row,"team","team_code")
            gsis=col(row,"gsis_id","player_id")
            name=col(row,"full_name","display_name","player_name")
            if not season or not team or not gsis:
                reject(conn,bid,i,"MISSING_ROSTER_KEY","Roster row needs season/team/player ID",row);rejected+=1;continue
            vals=(bid,i,season,team,gsis,name,col(row,"position","pos"),parse_int(col(row,"jersey_number","jersey")),
                  col(row,"status","roster_status"),col(row,"college_name","college"),json.dumps(row,sort_keys=True))
            conn.execute("INSERT INTO staging_rosters VALUES (?,?,?,?,?,?,?,?,?,?,?)",vals);staged+=1
    return read,staged,rejected

def publish_rosters(conn,bid):
    published=0
    for r in conn.execute("""SELECT season,team_code,gsis_id,full_name,position,jersey_number,roster_status,college_name
                             FROM staging_rosters WHERE batch_id=?""",(bid,)):
        season,team,gsis,name,pos,jersey,status,college=r
        pid="GSIS:"+gsis
        if not conn.execute("SELECT 1 FROM canonical_players WHERE player_id=?",(pid,)).fetchone():
            # roster feed can seed minimal player row, but mark incomplete.
            conn.execute("""INSERT OR IGNORE INTO canonical_players(player_id,gsis_id,display_name,primary_position,
                            verification_status,source_id) VALUES (?,?,?,?,'INCOMPLETE','NFLVERSE_ROSTERS')""",
                         (pid,gsis,name or gsis,pos))
        sid=resolve_school(conn,college)
        conn.execute("""INSERT INTO canonical_roster_seasons(season,team_code,player_id,jersey_number,position,roster_status,
                        school_id,verification_status,source_id)
                        VALUES (?,?,?,?,?,?,?,'SOURCE_BACKED','NFLVERSE_ROSTERS')
                        ON CONFLICT(season,team_code,player_id) DO UPDATE SET
                          jersey_number=excluded.jersey_number,position=excluded.position,
                          roster_status=excluded.roster_status,school_id=COALESCE(excluded.school_id,canonical_roster_seasons.school_id),
                          verification_status='SOURCE_BACKED',source_id='NFLVERSE_ROSTERS'""",
                     (season,team,pid,jersey,pos,status,sid))
        published+=1
    return published

def stage_cfb_games(conn,bid,path):
    read=staged=rejected=0
    with open(path,newline="",encoding="utf-8-sig") as f:
        for i,row in enumerate(csv.DictReader(f),start=2):
            read+=1
            season=parse_int(col(row,"season"))
            home=col(row,"home_school","home_team")
            away=col(row,"away_school","away_team")
            if not season or not home or not away:
                reject(conn,bid,i,"MISSING_GAME_KEY","CFB game row needs season/home/away",row);rejected+=1;continue
            gid=col(row,"game_id") or f"CFB:{season}:{col(row,'week') or 'X'}:{norm_school(away)}:{norm_school(home)}"
            vals=(bid,i,gid,season,parse_int(col(row,"week")),col(row,"game_date","date"),home,away,
                  parse_int(col(row,"home_score")),parse_int(col(row,"away_score")),
                  col(row,"stadium_name","stadium"),parse_int(col(row,"conference_game")),json.dumps(row,sort_keys=True))
            conn.execute("INSERT INTO staging_cfb_games VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",vals);staged+=1
    return read,staged,rejected

def publish_cfb_games(conn,bid):
    published=0
    for r in conn.execute("""SELECT game_id,season,week,game_date,home_school,away_school,home_score,away_score,
                             stadium_name,conference_game FROM staging_cfb_games WHERE batch_id=?""",(bid,)):
        gid,season,week,date,home,away,hs,as_,stadium,conf=r
        hid=resolve_school(conn,home); aid=resolve_school(conn,away)
        if not hid or not aid:
            conn.execute("""INSERT INTO qa_issues(severity,entity_type,entity_id,issue_type,detail)
                            VALUES('WARN','cfb_game',?,'UNMAPPED_SCHOOL',?)""",
                         (gid,f"home={home} mapped={hid}; away={away} mapped={aid}"))
            continue
        conn.execute("""INSERT INTO cfb_games_canonical(
                        game_id,season,week,game_date,home_school_id,away_school_id,
                        home_score,away_score,stadium_name,conference_game,verification_status,source_id)
                        VALUES (?,?,?,?,?,?,?,?,?,?,'SOURCE_BACKED','READS_CFB_MASTER')
                        ON CONFLICT(game_id) DO UPDATE SET season=excluded.season,week=excluded.week,game_date=excluded.game_date,
                        home_school_id=excluded.home_school_id,away_school_id=excluded.away_school_id,
                        home_score=excluded.home_score,away_score=excluded.away_score,stadium_name=excluded.stadium_name,
                        conference_game=excluded.conference_game,verification_status='SOURCE_BACKED',
                        source_id='READS_CFB_MASTER'""",
                     (gid,season,week,date,hid,aid,hs,as_,stadium,conf))
        published+=1
    return published

def rebuild_relationships(conn):
    preds=["PLAYED_FOR","WORE_NUMBER","PLAYED_POSITION","TEAMMATE_OF","ATTENDED","CFB_PLAYED_GAME","CFB_BEAT","CFB_LOST_TO"]
    for p in preds:
        conn.execute("DELETE FROM relationships WHERE predicate=?",(p,))
    rel=[]
    # roster/player edges
    for season,team,pid,jersey,pos,status,sid,*_ in conn.execute("SELECT * FROM canonical_roster_seasons"):
        rel.append(("nfl_player",pid,"PLAYED_FOR","team",team,season,season,"NFLVERSE_ROSTERS","SOURCE_BACKED"))
        if jersey is not None:
            rel.append(("nfl_player",pid,"WORE_NUMBER","jersey_number",str(jersey),season,season,"NFLVERSE_ROSTERS","SOURCE_BACKED"))
        if pos:
            rel.append(("nfl_player",pid,"PLAYED_POSITION","position",pos,season,season,"NFLVERSE_ROSTERS","SOURCE_BACKED"))
        if sid:
            rel.append(("nfl_player",pid,"ATTENDED","school",sid,None,None,"NFLVERSE_ROSTERS","SOURCE_BACKED"))
    # teammate edges, season/team bounded
    groups={}
    for season,team,pid in conn.execute("SELECT season,team_code,player_id FROM canonical_roster_seasons"):
        groups.setdefault((season,team),[]).append(pid)
    for (season,team),players in groups.items():
        # full pair graph can get large; store undirected canonical ordered pairs once.
        players=sorted(set(players))
        for i,a in enumerate(players):
            for b in players[i+1:]:
                rel.append(("nfl_player",a,"TEAMMATE_OF","nfl_player",b,season,season,"NFLVERSE_ROSTERS","DERIVED_SOURCE_BACKED"))
    # CFB game edges
    for gid,season,week,date,hid,aid,hs,as_,stadium,conf,*_ in conn.execute("SELECT * FROM cfb_games_canonical"):
        rel.append(("school",hid,"CFB_PLAYED_GAME","cfb_game",gid,season,season,"READS_CFB_MASTER","SOURCE_BACKED"))
        rel.append(("school",aid,"CFB_PLAYED_GAME","cfb_game",gid,season,season,"READS_CFB_MASTER","SOURCE_BACKED"))
        if hs is not None and as_ is not None:
            if hs>as_:
                rel.append(("school",hid,"CFB_BEAT","school_game_opponent",f"{gid}:{aid}",season,season,"READS_CFB_MASTER","SOURCE_BACKED"))
                rel.append(("school",aid,"CFB_LOST_TO","school_game_opponent",f"{gid}:{hid}",season,season,"READS_CFB_MASTER","SOURCE_BACKED"))
            elif as_>hs:
                rel.append(("school",aid,"CFB_BEAT","school_game_opponent",f"{gid}:{hid}",season,season,"READS_CFB_MASTER","SOURCE_BACKED"))
                rel.append(("school",hid,"CFB_LOST_TO","school_game_opponent",f"{gid}:{aid}",season,season,"READS_CFB_MASTER","SOURCE_BACKED"))
    conn.executemany("""INSERT OR IGNORE INTO relationships(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end,source_id,verification_status)
                        VALUES (?,?,?,?,?,?,?,?,?)""",rel)
    # mirror newly built relationships
    conn.executemany("DELETE FROM graph_edges WHERE predicate=?",[(p,) for p in preds])
    conn.execute("""INSERT OR IGNORE INTO graph_edges(subject_type,subject_id,predicate,object_type,object_id,season_start,season_end,source_id,verification_status)
                    SELECT subject_type,subject_id,predicate,object_type,object_id,season_start,season_end,source_id,verification_status
                    FROM relationships WHERE predicate IN ('PLAYED_FOR','WORE_NUMBER','PLAYED_POSITION','TEAMMATE_OF','ATTENDED','CFB_PLAYED_GAME','CFB_BEAT','CFB_LOST_TO')""")

def import_file(dataset,path):
    path=Path(path)
    conn=sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")
    source={"nflverse_players":"NFLVERSE_PLAYERS","nflverse_rosters":"NFLVERSE_ROSTERS","cfb_games":"READS_CFB_MASTER"}[dataset]
    bid=begin_batch(conn,dataset,source,path)
    try:
        conn.execute("BEGIN")
        if dataset=="nflverse_players":
            read,staged,rejected=stage_players(conn,bid,path);published=publish_players(conn,bid)
        elif dataset=="nflverse_rosters":
            read,staged,rejected=stage_rosters(conn,bid,path);published=publish_rosters(conn,bid)
        elif dataset=="cfb_games":
            read,staged,rejected=stage_cfb_games(conn,bid,path);published=publish_cfb_games(conn,bid)
        else:
            raise KeyError(dataset)
        rebuild_relationships(conn)
        qa=conn.execute("SELECT COUNT(*) FROM qa_issues WHERE status='OPEN'").fetchone()[0]
        conn.execute("""UPDATE import_batches SET finished_at=?,status='PUBLISHED',rows_read=?,rows_staged=?,rows_published=?,
                        rows_rejected=?,qa_issue_count=? WHERE batch_id=?""",
                     (dt.datetime.utcnow().isoformat()+"Z",read,staged,published,rejected,qa,bid))
        conn.commit()
        return {"batch_id":bid,"status":"PUBLISHED","rows_read":read,"rows_staged":staged,"rows_published":published,"rows_rejected":rejected,"open_qa":qa}
    except Exception as e:
        conn.rollback()
        conn.execute("""UPDATE import_batches SET finished_at=?,status='ROLLED_BACK',notes=? WHERE batch_id=?""",
                     (dt.datetime.utcnow().isoformat()+"Z",repr(e),bid))
        conn.commit()
        return {"batch_id":bid,"status":"ROLLED_BACK","error":repr(e)}
    finally:
        conn.close()

if __name__=="__main__":
    if len(sys.argv)!=3:
        print("Usage: python import_data.py <nflverse_players|nflverse_rosters|cfb_games> <file.csv>")
        raise SystemExit(2)
    print(json.dumps(import_file(sys.argv[1],sys.argv[2]),indent=2))
