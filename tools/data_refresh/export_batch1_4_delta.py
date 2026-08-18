"""Builds a small, portable SQLite "delta" file containing ONLY the real,
new data added by Knowledge Expansion Batches 1-4 -- not a copy of the
full 2.6GB production database.

Why this exists: local (this checkout's `Reads_Football_Data_Engine_v4.0/
reads_football_v4.0.sqlite`) and production (a separate, manually-managed
Fly.io persistent volume) are NOT synced by any CI/CD -- they are two real,
independently-drifting copies. Overwriting production's file with the
local one would discard whatever's changed on production since the last
manual sync. This script instead extracts exactly what Batches 1-4 added,
so that can be merged into production additively (see
apply_batch1_4_delta.py), leaving everything else on production untouched.

--- WHAT COUNTS AS "NEW" (verified directly against the real local DB) ---
12 brand-new tables (created fresh by these batches, safe to copy whole):
  cfb_all_america_certified, nfl_hof_inductees, nfl_hof_inductee_teams,
  nfl_all_pro_selections, nfl_pro_bowl_selections, nfl_coordinators,
  cfb_coordinators, nfl_player_background, cfb_player_game_stats_real,
  nfl_plays_defense_ext, nfl_drives_real, cfb_player_game_kicking_ext

4 EXISTING shared tables that got new ROWS added (filtered, not copied
whole, since these already hold production data this script must not
touch or duplicate):
  relationships  -- filtered to the 9 real predicate values these
                    batches introduced (HALL_OF_FAME_INDUCTEE,
                    AP_FIRST_TEAM_ALL_PRO, AP_SECOND_TEAM_ALL_PRO,
                    PRO_BOWL_SELECTION, SERVED_AS_*)
  coaches        -- filtered to source_id='WIKIPEDIA_STRUCTURED' (the 49
                    real coordinator identities Batch 2 added; existing
                    NFLVERSE_DATA-sourced rows are never touched)
  cfb_coaches    -- filtered to status LIKE '%WIKIPEDIA%' (the 21 real
                    CFB coordinator identities Batch 2 added)
  sources        -- the single real new row (ESPN_BOXSCORE_API); the
                    rest already exist on production and are re-inserted
                    with ON CONFLICT DO NOTHING by the apply script, never
                    duplicated

2 EXISTING large tables that got new INDEXES only (no new rows) --
`nfl_plays` and `cfb_plays`: no data to export, apply_batch1_4_delta.py
just runs `CREATE INDEX IF NOT EXISTS` directly against production for
these six real, measured indexes (see pbp_index_migration.py).

Nothing here is a new identity system, a new predicate scheme, or a
schema change to any existing production table -- purely additive.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

ENGINE_DIR = engine_bootstrap.ENGINE_DIR
LOCAL_DB = ENGINE_DIR / "reads_football_v4.0.sqlite"

NEW_TABLES = [
    "cfb_all_america_certified", "nfl_hof_inductees", "nfl_hof_inductee_teams",
    "nfl_all_pro_selections", "nfl_pro_bowl_selections", "nfl_coordinators",
    "cfb_coordinators", "nfl_player_background", "cfb_player_game_stats_real",
    "nfl_plays_defense_ext", "nfl_drives_real", "cfb_player_game_kicking_ext",
]

NEW_RELATIONSHIP_PREDICATES = [
    "HALL_OF_FAME_INDUCTEE", "AP_FIRST_TEAM_ALL_PRO", "AP_SECOND_TEAM_ALL_PRO",
    "PRO_BOWL_SELECTION", "SERVED_AS_OFFENSIVE_COORDINATOR", "SERVED_AS_DEFENSIVE_COORDINATOR",
    "SERVED_AS_CO_OFFENSIVE_COORDINATOR", "SERVED_AS_CO_DEFENSIVE_COORDINATOR",
    "SERVED_AS_SPECIAL_TEAMS_COORDINATOR",
]

NEW_INDEXES = [
    ("idx_nfl_plays_passer", "nfl_plays", "passer_player_key"),
    ("idx_nfl_plays_receiver", "nfl_plays", "receiver_player_key"),
    ("idx_nfl_plays_rusher", "nfl_plays", "rusher_player_key"),
    ("idx_nfl_plays_touchdown", "nfl_plays", "touchdown"),
    ("idx_cfb_plays_drive", "cfb_plays", "drive_id"),
    ("idx_cfb_plays_play_type", "cfb_plays", "play_type"),
]


def build_delta(out_path: Path) -> dict:
    if out_path.exists():
        out_path.unlink()

    src = sqlite3.connect(str(LOCAL_DB))
    src.execute(f"ATTACH DATABASE '{out_path}' AS delta")

    report: dict = {"tables": {}, "filtered_tables": {}, "indexes": [i[0] for i in NEW_INDEXES]}

    for t in NEW_TABLES:
        create_sql = src.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)
        ).fetchone()[0]
        src.execute(create_sql.replace(f"CREATE TABLE {t}", f"CREATE TABLE delta.{t}", 1))
        for idx_sql in src.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL", (t,)
        ).fetchall():
            src.execute(idx_sql[0].replace("CREATE INDEX ", "CREATE INDEX delta.", 1)
                        if "CREATE INDEX " in idx_sql[0]
                        else idx_sql[0].replace("CREATE UNIQUE INDEX ", "CREATE UNIQUE INDEX delta.", 1))
        src.execute(f"INSERT INTO delta.{t} SELECT * FROM main.{t}")
        n = src.execute(f"SELECT COUNT(*) FROM delta.{t}").fetchone()[0]
        report["tables"][t] = n

    # Filtered shared-table rows -- explicit column lists so this never
    # silently breaks if either schema gains a column later.
    src.execute("""
        CREATE TABLE delta.relationships (
            relationship_id INTEGER, subject_type TEXT, subject_id TEXT, predicate TEXT,
            object_type TEXT, object_id TEXT, season_start INTEGER, season_end INTEGER,
            source_id TEXT, verification_status TEXT
        )
    """)
    placeholders = ",".join("?" for _ in NEW_RELATIONSHIP_PREDICATES)
    src.execute(
        f"INSERT INTO delta.relationships SELECT * FROM main.relationships WHERE predicate IN ({placeholders})",
        NEW_RELATIONSHIP_PREDICATES,
    )
    report["filtered_tables"]["relationships"] = src.execute("SELECT COUNT(*) FROM delta.relationships").fetchone()[0]

    src.execute("CREATE TABLE delta.coaches (coach_id TEXT, coach_name TEXT, source_id TEXT, verification_status TEXT)")
    src.execute("INSERT INTO delta.coaches SELECT * FROM main.coaches WHERE source_id='WIKIPEDIA_STRUCTURED'")
    report["filtered_tables"]["coaches"] = src.execute("SELECT COUNT(*) FROM delta.coaches").fetchone()[0]

    src.execute(
        "CREATE TABLE delta.cfb_coaches (cfb_coach_id TEXT, coach_name TEXT, school_context TEXT, "
        "source_contexts TEXT, first_year TEXT, last_year TEXT, status TEXT)"
    )
    src.execute("INSERT INTO delta.cfb_coaches SELECT * FROM main.cfb_coaches WHERE status LIKE '%WIKIPEDIA%'")
    report["filtered_tables"]["cfb_coaches"] = src.execute("SELECT COUNT(*) FROM delta.cfb_coaches").fetchone()[0]

    src.execute(
        "CREATE TABLE delta.sources (source_id TEXT, source_name TEXT, source_url TEXT, license_note TEXT, "
        "attribution_required INTEGER, approved_for_import INTEGER, notes TEXT)"
    )
    src.execute("INSERT INTO delta.sources SELECT * FROM main.sources WHERE source_id IN ('ESPN_BOXSCORE_API','WIKIPEDIA_STRUCTURED')")
    report["filtered_tables"]["sources"] = src.execute("SELECT COUNT(*) FROM delta.sources").fetchone()[0]

    src.commit()
    src.execute("DETACH DATABASE delta")
    src.close()

    report["file_size_bytes"] = out_path.stat().st_size
    report["indexes_to_create_directly"] = [
        {"name": n, "table": t, "column": c} for n, t, c in NEW_INDEXES
    ]
    return report


if __name__ == "__main__":
    import json
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("batch1_4_delta.sqlite")
    result = build_delta(out)
    print(json.dumps(result, indent=2, default=str))
    print(f"\nDelta written to: {out.resolve()}")
