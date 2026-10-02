"""Indexes required by v0.5's relationship traversal on legacy tables.

These do not alter fact data. They only make the new subject-first query
patterns efficient on the production-sized Engine DB.
"""
from __future__ import annotations

INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS ix_v05_player_game_stats_player ON player_game_stats(player_key, season, game_id)",
    "CREATE INDEX IF NOT EXISTS ix_v05_roster_player ON canonical_roster_seasons(player_id, season, team_code)",
    "CREATE INDEX IF NOT EXISTS ix_v05_draft_player ON draft_facts(player_key, draft_season)",
    "CREATE INDEX IF NOT EXISTS ix_v05_all_pro_player ON nfl_all_pro_selections(player_id, season)",
    "CREATE INDEX IF NOT EXISTS ix_v05_cfb_game_stats_player ON cfb_player_game_stats_real(cfb_player_id, season, game_id)",
    "CREATE INDEX IF NOT EXISTS ix_v05_coach_history ON coach_team_seasons(coach_id, season)",
    "CREATE INDEX IF NOT EXISTS ix_v05_rank_school ON cfb_rankings(school_id, season, week)",
)

def install(conn):
    tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    installed=[]
    skipped=[]
    for ddl in INDEX_DDL:
        table=ddl.split(" ON ",1)[1].split("(",1)[0].strip()
        if table not in tables:
            skipped.append(table); continue
        conn.execute(ddl); installed.append(table)
    conn.commit()
    return {"installed":installed,"skipped_missing_tables":skipped}
