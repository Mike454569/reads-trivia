"""Build the tiny deterministic SQLite database used by routine CI.

This is deliberately NOT a mock of the entire Reads warehouse. It is a
certified contract fixture: enough real schema/data shape to exercise the
Gateway DB boundary, readiness, public capability catalog/routing parity,
and representative NFL/CFB game rows without copying the multi-GB Fly volume.
Deep candidate coverage remains the responsibility of the full real-DB gate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path


def build(path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(
            """
            PRAGMA journal_mode=DELETE;
            CREATE TABLE meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE draft_facts (
              id INTEGER PRIMARY KEY,
              player_name TEXT NOT NULL,
              draft_year INTEGER NOT NULL,
              team TEXT NOT NULL,
              round INTEGER,
              pick INTEGER
            );
            CREATE TABLE games (
              game_id TEXT PRIMARY KEY,
              season INTEGER NOT NULL,
              week INTEGER,
              competition TEXT NOT NULL,
              home_team TEXT NOT NULL,
              away_team TEXT NOT NULL,
              home_score INTEGER,
              away_score INTEGER,
              status TEXT NOT NULL
            );
            CREATE TABLE capability_catalog (
              capability_id TEXT PRIMARY KEY,
              version INTEGER NOT NULL,
              mechanic TEXT NOT NULL,
              domain TEXT NOT NULL,
              relationship_predicate TEXT NOT NULL,
              input_entity_type TEXT,
              input_scoping_fields TEXT,
              output_entity_type TEXT,
              source_tables TEXT,
              source_columns TEXT,
              required_joins TEXT,
              canonical_identity_fields TEXT,
              identity_resolution_method TEXT,
              identity_resolution_rate REAL,
              season_coverage_min INTEGER,
              season_coverage_max INTEGER,
              season_coverage_notes TEXT,
              team_or_school_coverage TEXT,
              player_coverage TEXT,
              game_coverage TEXT,
              source_id TEXT,
              refresh_dataset_key TEXT,
              freshness_category TEXT,
              freshness_notes TEXT,
              tie_rule TEXT,
              ambiguity_rule TEXT,
              eligible_answer_rule TEXT,
              distractor_scoping_rule TEXT,
              min_candidate_pool_size INTEGER,
              known_limitations TEXT,
              verification_status TEXT NOT NULL,
              human_review_status TEXT,
              compiler_support TEXT,
              runtime_adapter_module TEXT,
              public_availability TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX uq_capability_triple
              ON capability_catalog(mechanic, domain, relationship_predicate);
            """
        )
        con.executemany(
            "INSERT INTO meta(key,value) VALUES (?,?)",
            [
                ("database_version", "ci-certified-v1"),
                ("fixture_kind", "certified-contract"),
            ],
        )
        con.executemany(
            "INSERT INTO draft_facts(player_name,draft_year,team,round,pick) VALUES (?,?,?,?,?)",
            [
                ("CI Quarterback", 2025, "NE", 1, 1),
                ("CI Receiver", 2025, "DAL", 1, 2),
                ("CI Defender", 2024, "BAL", 2, 40),
                ("CI Runner", 2024, "GB", 3, 72),
            ],
        )
        con.executemany(
            "INSERT INTO games(game_id,season,week,competition,home_team,away_team,home_score,away_score,status) VALUES (?,?,?,?,?,?,?,?,?)",
            [
                ("ci-nfl-1", 2025, 1, "NFL", "NE", "NYJ", 24, 17, "FINAL"),
                ("ci-nfl-2", 2025, 2, "NFL", "DAL", "PHI", 21, 27, "FINAL"),
                ("ci-cfb-1", 2025, 1, "CFB", "Alabama", "Georgia", 31, 28, "FINAL"),
                ("ci-cfb-2", 2025, 2, "CFB", "Ohio State", "Michigan", 20, 17, "FINAL"),
            ],
        )

        # Import after base schema exists. PUBLIC_MODES is the actual browser-
        # reachable routing table and registry owns the corresponding adapter.
        from gateway.services.public_game import PUBLIC_MODES
        from tools.director_v02 import registry

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        inserted = set()
        for mode, entry in sorted(PUBLIC_MODES.items()):
            spec = entry["spec"]
            triple = (spec["mechanic"], spec["domain"], spec["relationship_predicate"])
            cap = registry.CAPABILITY_REGISTRY.get(triple)
            if cap is None:
                raise RuntimeError(f"PUBLIC_MODES entry {mode!r} has no registry capability {triple!r}")
            capability_id = f"{triple[1]}__{triple[2]}"
            if capability_id in inserted:
                continue
            adapter = cap.get("adapter")
            con.execute(
                """
                INSERT INTO capability_catalog(
                  capability_id,version,mechanic,domain,relationship_predicate,
                  input_entity_type,output_entity_type,known_limitations,
                  verification_status,human_review_status,compiler_support,
                  runtime_adapter_module,public_availability,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    capability_id, 1, *triple,
                    cap.get("entity_type"), cap.get("answer_type"),
                    json.dumps(list(cap.get("known_limitations", []))),
                    "PUBLIC_ENABLED", "APPROVED", "HAND_WRITTEN",
                    getattr(adapter, "__name__", None), "PUBLIC_ENABLED", now, now,
                ),
            )
            inserted.add(capability_id)

        con.commit()
        quick = con.execute("PRAGMA quick_check").fetchone()[0]
        if quick != "ok":
            raise RuntimeError(f"fixture quick_check failed: {quick}")
        return {
            "path": str(path),
            "bytes": path.stat().st_size,
            "public_capabilities": len(inserted),
            "games": con.execute("SELECT COUNT(*) FROM games").fetchone()[0],
            "draft_facts": con.execute("SELECT COUNT(*) FROM draft_facts").fetchone()[0],
        }
    finally:
        con.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--engine-dir", required=True)
    args = p.parse_args()
    engine_dir = Path(args.engine_dir)
    result = build(engine_dir / "reads_football_v4.0.sqlite")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
