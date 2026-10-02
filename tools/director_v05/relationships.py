"""Safe relationship traversal over verified legacy Engine data."""
from __future__ import annotations

RELATIONSHIPS={
 "PLAYER_ROSTER_TEAM":{
   "sql":"""SELECT r.player_id AS subject_id,r.team_code AS object_id,r.season,
            r.source_id,r.verification_status
            FROM canonical_roster_seasons r
            WHERE r.player_id=? AND r.verification_status='SOURCE_BACKED'
            ORDER BY r.season,r.team_code""",
 },
 "PLAYER_DRAFT":{
   "sql":"""SELECT d.player_key AS subject_id,d.draft_team AS object_id,d.draft_season AS season,
            d.draft_round,d.draft_pick_overall,d.source_id,d.verification_status
            FROM draft_facts d WHERE d.player_key=? AND d.verification_status='SOURCE_BACKED'""",
 },
 "PLAYER_ALL_PRO":{
   "sql":"""SELECT COALESCE(a.player_id,a.player_name_raw) AS subject_id,
            a.honor_level AS object_id,a.season,a.position_raw,a.source_id,a.verification_status
            FROM nfl_all_pro_selections a
            WHERE a.player_id=? AND a.is_ap=1 AND a.verification_status='WIKIPEDIA_STRUCTURED_SECONDARY'
            ORDER BY a.season""",
 },
 "SCHOOL_RANKING_HISTORY":{
   "sql":"""SELECT r.school_id AS subject_id,r.rank AS object_id,r.season,r.week,r.poll,
            r.source_id,r.verification_status
            FROM cfb_rankings r WHERE r.school_id=? AND r.verification_status='SOURCE_BACKED'
            ORDER BY r.season,r.week,r.poll""",
 },
}

def traverse(conn,relationship,subject_id,*,limit=500):
    if relationship not in RELATIONSHIPS: raise ValueError("unknown relationship")
    limit=max(1,min(int(limit),5000))
    sql=RELATIONSHIPS[relationship]["sql"]+" LIMIT ?"
    cur=conn.execute(sql,(subject_id,limit))
    keys=[d[0] for d in cur.description]
    return [dict(zip(keys,row)) for row in cur.fetchall()]

def player_career_graph(conn,player_id):
    """One normalized graph payload from independent verified legacy facts."""
    return {
      "player_id":player_id,
      "roster_teams":traverse(conn,"PLAYER_ROSTER_TEAM",player_id),
      "draft":traverse(conn,"PLAYER_DRAFT",player_id),
      "all_pro":traverse(conn,"PLAYER_ALL_PRO",player_id),
    }
