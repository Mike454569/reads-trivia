"""Reads Football v1.6 stable-ID NFL <-> CFB identity bridge.

Run after downloading/importing the nflverse player master:
    python identity_bridge_v16.py

Primary join:
  SportsDataverse CFB ESPN athlete ID == nflverse players espn_id

Secondary corroboration:
  normalized name, PFR ID, GSIS ID, CFB roster years, draft year,
  college/school evidence, position and NFL roster history.

Exact ESPN-ID matches are the preferred production identity link. Name-only
matches remain conservative and are never used when ambiguous.
"""
from pathlib import Path
import sqlite3,csv,json,re,hashlib,datetime as dt,sys

ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"
PLAYERS=ROOT/"imports"/"nflverse_players.csv"

def norm(s):
    s=(s or "").lower().replace("’","'").replace(".","").replace("'","")
    s=re.sub(r"\b(jr|sr|ii|iii|iv)\b","",s)
    return re.sub(r"[^a-z0-9]+","",s)

def ival(v):
    try:
        return int(float(v)) if v not in (None,"","NA","nan") else None
    except Exception:
        return None

def clean(v):
    return None if v in (None,"","NA","nan") else str(v).strip()

def col(row,*names):
    for n in names:
        if n in row and clean(row[n]) is not None:
            return clean(row[n])
    return None

def school_norm(s):
    return re.sub(r"[^a-z0-9]+"," ",str(s or "").lower()).strip()

def resolve_school(c,name):
    if not name:return None
    n=school_norm(name)
    for sid,sname in c.execute("SELECT school_id,school_name FROM schools"):
        if school_norm(sname)==n:return sid
    for alias,sid in c.execute("SELECT alias_name,school_id FROM school_aliases"):
        if school_norm(alias)==n:return sid
    return None

def main():
    if not PLAYERS.exists():
        print(json.dumps({"status":"NEEDS_PLAYER_MASTER","expected_file":str(PLAYERS),
          "next":"Run: python fetch_nflverse_current.py --players"} ,indent=2))
        return 2

    sha=hashlib.sha256(PLAYERS.read_bytes()).hexdigest()
    with PLAYERS.open(newline="",encoding="utf-8-sig") as f:
        nflrows=list(csv.DictReader(f))

    c=sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("BEGIN IMMEDIATE")

    # Add useful nflverse enrichment columns without breaking older DB readers.
    cols={x[1] for x in c.execute("PRAGMA table_info(canonical_players)")}
    for name,typ in [("espn_id","TEXT"),("college_name","TEXT"),("draft_year","INTEGER"),
                     ("draft_team","TEXT"),("last_season","INTEGER")]:
        if name not in cols:
            c.execute(f"ALTER TABLE canonical_players ADD COLUMN {name} {typ}")

    # Index current player master by stable ESPN athlete ID.
    nfl_by_espn={}
    duplicate_espn=set()
    for r in nflrows:
        espn=col(r,"espn_id")
        if not espn:continue
        if espn in nfl_by_espn: duplicate_espn.add(espn)
        nfl_by_espn[espn]=r
    for x in duplicate_espn:nfl_by_espn.pop(x,None)

    promoted=[]
    rejected_name_mismatch=0
    considered=0
    for cfbid,espnid,cname,first,last,h,w,city,state,country,headshot,ver,src in c.execute(
        "SELECT * FROM canonical_cfb_players WHERE espn_athlete_id IS NOT NULL"):
        considered+=1
        nr=nfl_by_espn.get(str(espnid))
        if not nr:continue

        gsis=col(nr,"gsis_id")
        pfr=col(nr,"pfr_id")
        nname=col(nr,"display_name","football_name","short_name") or cname
        nflkey=("GSIS:"+gsis) if gsis else ("PFR:"+pfr) if pfr else ("ESPN_NFL:"+str(espnid))
        dy=ival(col(nr,"draft_year"))
        dteam=col(nr,"draft_team")
        pos=col(nr,"position")
        college=col(nr,"college_name")
        lastseason=ival(col(nr,"last_season"))
        birth=col(nr,"birth_date")
        height=ival(col(nr,"height"))
        weight=ival(col(nr,"weight"))

        # Stable ID is primary proof. Name mismatch is retained as QA rather than silently hidden.
        same_name=(norm(cname)==norm(nname))
        if not same_name:
            rejected_name_mismatch+=1
            # Still allow very strong stable ID, but explicitly mark corroboration mismatch.
        school_rows=list(c.execute("""SELECT r.school_id,s.school_name,MIN(r.season),MAX(r.season)
                                      FROM cfb_roster_seasons_real r JOIN schools s ON s.school_id=r.school_id
                                      WHERE r.cfb_player_id=? GROUP BY r.school_id,s.school_name""",(cfbid,)))
        school_ids=[x[0] for x in school_rows]
        school_names=[x[1] for x in school_rows]
        latest=max([x[3] for x in school_rows],default=None)
        college_sid=resolve_school(c,college)
        school_corroborated=(college_sid in school_ids) if college_sid else None
        chronology_ok=(dy is None or latest is None or latest<=dy<=latest+5)

        evidence={
          "primary_key":{"cfb_espn_id":str(espnid),"nfl_espn_id":str(espnid),"exact":True},
          "name":{"cfb":cname,"nfl":nname,"normalized_equal":same_name},
          "cfb_schools":[{"school_id":x[0],"school_name":x[1],"first":x[2],"last":x[3]} for x in school_rows],
          "nfl_college_name":college,"college_school_id":college_sid,"school_corroborated":school_corroborated,
          "draft_year":dy,"draft_team":dteam,"position":pos,"cfb_last_year":latest,
          "chronology_ok":chronology_ok,"gsis_id":gsis,"pfr_id":pfr,
          "player_master_sha256":sha
        }

        # ESPN-ID exact remains production-safe, but impossible chronology is quarantined.
        safe=1 if chronology_ok else 0
        confidence=1.0 if same_name and chronology_ok else .999 if chronology_ok else .60
        decision="PROMOTED_STABLE_ID" if safe else "REJECTED_CHRONOLOGY"
        bid="BRIDGE16:"+hashlib.sha1(f"{cfbid}|{nflkey}".encode()).hexdigest()[:20]

        cand="CAND16:"+hashlib.sha1(f"{cfbid}|{nflkey}".encode()).hexdigest()[:20]
        c.execute("""INSERT OR REPLACE INTO cross_league_identity_candidates(
          candidate_id,cfb_player_id,nfl_player_key,player_name,school_id,school_name,
          cfb_last_evidence_year,nfl_draft_year,nfl_draft_team,nfl_position,espn_id,gsis_id,pfr_id,
          match_rule,confidence,decision,production_safe,evidence_json)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (cand,cfbid,nflkey,cname,school_ids[-1] if school_ids else None,school_names[-1] if school_names else None,
           latest,dy,dteam,pos,str(espnid),gsis,pfr,"EXACT_ESPN_ID",confidence,decision,safe,json.dumps(evidence,sort_keys=True)))

        if not safe:continue
        c.execute("""INSERT OR REPLACE INTO cross_league_identity_bridge_v16(
          bridge_id,cfb_player_id,nfl_player_key,player_name,school_id,school_name,
          cfb_last_evidence_year,nfl_draft_year,nfl_draft_team,nfl_position,espn_id,gsis_id,pfr_id,
          match_rule,confidence,verification_status,evidence_json)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (bid,cfbid,nflkey,cname,school_ids[-1] if school_ids else None,school_names[-1] if school_names else None,
           latest,dy,dteam,pos,str(espnid),gsis,pfr,"EXACT_ESPN_ID",confidence,"VERIFIED_STABLE_ID",json.dumps(evidence,sort_keys=True)))

        # Upsert canonical NFL player with source-backed IDs and immutable-ish metadata.
        if gsis:
            pid="GSIS:"+gsis
            c.execute("""INSERT INTO canonical_players(
                player_id,gsis_id,pfr_id,display_name,birth_date,height_in,weight_lb,primary_position,
                primary_school_id,verification_status,source_id,espn_id,college_name,draft_year,draft_team,last_season)
                VALUES (?,?,?,?,?,?,?,?,?,'SOURCE_BACKED','NFLVERSE_PLAYERS',?,?,?,?,?)
                ON CONFLICT(player_id) DO UPDATE SET
                  pfr_id=COALESCE(excluded.pfr_id,canonical_players.pfr_id),
                  display_name=excluded.display_name,birth_date=COALESCE(excluded.birth_date,canonical_players.birth_date),
                  height_in=COALESCE(excluded.height_in,canonical_players.height_in),
                  weight_lb=COALESCE(excluded.weight_lb,canonical_players.weight_lb),
                  primary_position=COALESCE(excluded.primary_position,canonical_players.primary_position),
                  primary_school_id=COALESCE(excluded.primary_school_id,canonical_players.primary_school_id),
                  espn_id=excluded.espn_id,college_name=excluded.college_name,draft_year=excluded.draft_year,
                  draft_team=excluded.draft_team,last_season=excluded.last_season,
                  verification_status='SOURCE_BACKED',source_id='NFLVERSE_PLAYERS'""",
              (pid,gsis,pfr,nname,birth,height,weight,pos,college_sid,str(espnid),college,dy,dteam,lastseason))
        promoted.append((bid,cfbid,nflkey,cname,school_rows,dy,dteam,pos))

    # Rebuild stable-ID identity edges while keeping the safe legacy bridge.
    c.execute("DELETE FROM relationships WHERE predicate='SAME_PERSON_AS' AND verification_status='VERIFIED_STABLE_ID'")
    c.execute("DELETE FROM graph_edges WHERE predicate='SAME_PERSON_AS' AND verification_status='VERIFIED_STABLE_ID'")
    for bid,cfbid,nflkey,cname,schools,dy,dteam,pos in promoted:
        latest=max([x[3] for x in schools],default=None)
        c.execute("""INSERT OR IGNORE INTO relationships(subject_type,subject_id,predicate,object_type,object_id,
          season_start,season_end,source_id,verification_status)
          VALUES('cfb_player',?,'SAME_PERSON_AS','nfl_player',?,?,?,'READS_IDENTITY_BRIDGE','VERIFIED_STABLE_ID')""",
          (cfbid,nflkey,latest,dy))
        for sid,sname,fy,ly in schools:
            c.execute("""INSERT OR IGNORE INTO relationships(subject_type,subject_id,predicate,object_type,object_id,
              season_start,season_end,source_id,verification_status)
              VALUES('school',?,'PRODUCED_NFL_PLAYER','nfl_player',?,?,?,'READS_IDENTITY_BRIDGE','VERIFIED_STABLE_ID')""",
              (sid,nflkey,ly,dy))

    c.execute("""INSERT OR IGNORE INTO graph_edges(subject_type,subject_id,predicate,object_type,object_id,
      season_start,season_end,source_id,verification_status)
      SELECT subject_type,subject_id,predicate,object_type,object_id,season_start,season_end,source_id,verification_status
      FROM relationships WHERE source_id='READS_IDENTITY_BRIDGE'
      AND verification_status='VERIFIED_STABLE_ID'""")

    runid="BRIDGERUN:"+hashlib.sha1((sha+str(dt.datetime.utcnow())).encode()).hexdigest()[:18]
    c.execute("""INSERT INTO identity_bridge_runs(
      run_id,player_master_sha256,cfb_players_considered,nfl_players_considered,exact_espn_links,
      exact_pfr_links,legacy_evidence_links,rejected_ambiguous,total_production_links,notes)
      VALUES (?,?,?,?,?,?,?,?,?,?)""",
      (runid,sha,considered,len(nflrows),len(promoted),0,
       c.execute("SELECT COUNT(*) FROM cross_league_identity_bridge_v16 WHERE match_rule!='EXACT_ESPN_ID'").fetchone()[0],
       rejected_name_mismatch,c.execute("SELECT COUNT(*) FROM cross_league_identity_bridge_v16").fetchone()[0],
       "Exact ESPN athlete ID is primary stable-ID bridge; chronology quarantine enabled."))

    c.commit()
    total=c.execute("SELECT COUNT(*) FROM cross_league_identity_bridge_v16").fetchone()[0]
    out={"status":"OK","player_master_rows":len(nflrows),"cfb_players_considered":considered,
         "exact_espn_links_promoted":len(promoted),"name_mismatch_on_exact_id":rejected_name_mismatch,
         "total_production_bridge_links":total,
         "foreign_key_errors":len(c.execute("PRAGMA foreign_key_check").fetchall())}
    c.close()
    import subprocess,sys
    rb=subprocess.run([sys.executable,str(ROOT/"rebuild_cross_league.py")],capture_output=True,text=True)
    try: out["cross_league_rebuild"]=json.loads(rb.stdout) if rb.stdout.strip() else {}
    except Exception: out["cross_league_rebuild"]={"stdout":rb.stdout.strip()}
    out["cross_league_rebuild_code"]=rb.returncode
    print(json.dumps(out,indent=2))
    return 0 if rb.returncode==0 else 1

if __name__=="__main__":
    raise SystemExit(main())
