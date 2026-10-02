"""Verified distractor pools from existing Engine tables."""
from __future__ import annotations
from .distractor_intelligence import Candidate

def nfl_players_same_position_era(conn,*,position,season,exclude_player_id=None,window=4,limit=300):
    rows=conn.execute(
      """SELECT DISTINCT cp.player_id,cp.display_name,rs.season,rs.team_code
         FROM canonical_roster_seasons rs
         JOIN canonical_players cp ON cp.player_id=rs.player_id
         WHERE rs.verification_status='SOURCE_BACKED'
           AND rs.season BETWEEN ? AND ?
           AND EXISTS(
             SELECT 1 FROM player_game_stats g
             WHERE g.player_key=rs.player_id AND g.season=rs.season
               AND g.verification_status='SOURCE_BACKED')
         ORDER BY ABS(rs.season-?),cp.display_name LIMIT ?""",
      (season-window,season+window,season,max(10,min(int(limit),2000)))
    ).fetchall()
    out=[]
    for r in rows:
        if exclude_player_id and str(r["player_id"])==str(exclude_player_id):continue
        # canonical roster does not guarantee a normalized position in every
        # historical row, so position is supplied by the caller only when
        # independently verified; never fabricate a position match here.
        out.append(Candidate(str(r["player_id"]),r["display_name"],r["season"],None,r["team_code"],None,None,True))
    return out

def cfb_schools_same_poll_week(conn,*,season,week,poll,exclude_school_id=None):
    rows=conn.execute(
      """SELECT school_id,school_name_raw,rank FROM cfb_rankings
         WHERE season=? AND week=? AND poll=? AND season_type='regular'
           AND verification_status='SOURCE_BACKED'
         ORDER BY rank""",(season,week,poll)).fetchall()
    return [Candidate(str(r["school_id"]),r["school_name_raw"],season,None,None,"TOP25",float(r["rank"]),True)
            for r in rows if not exclude_school_id or str(r["school_id"])!=str(exclude_school_id)]

def nfl_draft_same_round_era(conn,*,season,round_no,exclude_player_id=None,window=3,limit=500):
    rows=conn.execute(
      """SELECT player_key,player_name,draft_season,draft_round,draft_pick_overall,draft_team
         FROM draft_facts WHERE verification_status='SOURCE_BACKED'
           AND draft_round=? AND draft_season BETWEEN ? AND ?
         ORDER BY ABS(draft_season-?),draft_pick_overall LIMIT ?""",
      (round_no,season-window,season+window,season,max(10,min(int(limit),3000)))).fetchall()
    return [Candidate(str(r["player_key"]),r["player_name"],r["draft_season"],None,r["draft_team"],
                      f"ROUND_{r['draft_round']}",float(r["draft_pick_overall"] or 0),True)
            for r in rows if not exclude_player_id or str(r["player_key"])!=str(exclude_player_id)]
