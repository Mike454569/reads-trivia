"""Safe relationship traversal over verified legacy Engine data."""
from __future__ import annotations

RELATIONSHIPS={
 "PLAYER_GAME_LOG":{
   "sql":"""SELECT g.player_key AS subject_id,g.game_id AS object_id,g.season,g.week,g.team_code,
            g.pass_yards,g.rush_yards,g.receiving_yards,g.source_id,g.verification_status
            FROM player_game_stats g WHERE g.player_key=? AND g.verification_status='SOURCE_BACKED'
            ORDER BY g.season,g.week,g.game_id""",
 },
 "COACH_TEAM_HISTORY":{
   "sql":"""SELECT c.coach_id AS subject_id,c.team_code AS object_id,c.season,c.games_observed,
            c.source_id,c.verification_status FROM coach_team_seasons c
            WHERE c.coach_id=? AND c.verification_status='SOURCE_BACKED' ORDER BY c.season""",
 },
 "CFB_PLAYER_GAME_LOG":{
   "sql":"""SELECT g.cfb_player_id AS subject_id,g.game_id AS object_id,g.season,g.school_id,
            g.passing_yards,g.rushing_yards,g.receiving_yards,g.source_id,g.verification_status
            FROM cfb_player_game_stats_real g WHERE g.cfb_player_id=?
            AND g.verification_status='SOURCE_BACKED_DERIVED' ORDER BY g.season,g.game_id""",
 },
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
