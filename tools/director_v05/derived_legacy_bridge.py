"""Derived bridge for legacy tables whose provenance lives in source rows."""
from __future__ import annotations
import hashlib

def iter_verified_cfb_transfers(conn,*,limit=None):
    sql="""SELECT t.cfb_player_id,t.display_name,t.school_count,t.first_season,t.last_season,t.schools,
           GROUP_CONCAT(DISTINCT r.source_id) AS source_ids
           FROM cfb_transfer_summary_v17 t
           JOIN cfb_roster_seasons_real r ON r.cfb_player_id=t.cfb_player_id
             AND r.verification_status='SOURCE_BACKED'
           WHERE t.school_count>=2
           GROUP BY t.cfb_player_id,t.display_name,t.school_count,t.first_season,t.last_season,t.schools
           ORDER BY t.cfb_player_id"""
    args=[]
    if limit is not None: sql+=" LIMIT ?"; args.append(max(1,min(int(limit),100000)))
    for row in conn.execute(sql,args):
        d=dict(row)
        seed="cfb_transfer|"+str(d["cfb_player_id"])+"|"+str(d["schools"])
        yield {"fact_id":"legacy_"+hashlib.sha256(seed.encode()).hexdigest()[:24],
               "kind":"TRANSFER","legacy_table":"cfb_transfer_summary_v17",
               "verification_status":"SOURCE_BACKED_INHERITED",
               "source_id":d.pop("source_ids"),"data":d}

def transfer_path(conn,player_id):
    row=conn.execute("""SELECT t.cfb_player_id,t.display_name,t.first_season,t.last_season,t.schools
                        FROM cfb_transfer_summary_v17 t
                        WHERE t.cfb_player_id=? AND t.school_count>=2
                        AND EXISTS(SELECT 1 FROM cfb_roster_seasons_real r
                          WHERE r.cfb_player_id=t.cfb_player_id AND r.verification_status='SOURCE_BACKED')""",
                     (player_id,)).fetchone()
    if not row:return None
    d=dict(row); d["schools"]=[x.strip() for x in (d["schools"] or "").split(",") if x.strip()]
    return d
