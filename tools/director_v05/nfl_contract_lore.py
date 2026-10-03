"""Mine source-backed NFL contract rows into universal CONTRACT lore."""
from __future__ import annotations

from collections import defaultdict

from .entity_labels import resolve_required_label
from .event_ingest import upsert_event

SOURCE_URL = "https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv.gz"
SOURCE_PUBLISHER = "nflverse historical contracts"


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def mine_nfl_contract_lore(conn, *, limit_rows=None, min_value=1_000_000):
    if "nfl_player_contracts" not in _tables(conn):
        return {"events": 0, "reason": "missing_table"}

    rows = conn.execute(
        """SELECT contract_id,player_key,team_code,position,year_signed,contract_years,
                  value,apy,guaranteed,source_id,verification_status
           FROM nfl_player_contracts
           WHERE source_id='NFLVERSE_DATA'
             AND verification_status='SOURCE_BACKED'
             AND player_key IS NOT NULL
             AND year_signed IS NOT NULL
           ORDER BY year_signed,contract_id"""
    ).fetchall()

    inserted = 0
    skipped_unresolved = 0
    kinds = defaultdict(int)

    for index, row in enumerate(rows):
        if limit_rows and index >= int(limit_rows):
            break
        value = float(row["value"]) if row["value"] is not None else None
        apy = float(row["apy"]) if row["apy"] is not None else None
        guaranteed = float(row["guaranteed"]) if row["guaranteed"] is not None else None
        if value is not None and value < float(min_value):
            continue

        try:
            player_label = resolve_required_label(conn, "NFL_PLAYER", str(row["player_key"]))
        except ValueError:
            skipped_unresolved += 1
            continue

        facts = []
        if row["contract_years"] is not None:
            facts.append(str(int(row["contract_years"])) + "-year")
        if value is not None:
            facts.append("$" + f"{value:,.0f}" + " total value")
        if apy is not None:
            facts.append("$" + f"{apy:,.0f}" + " average per year")
        if guaranteed is not None:
            facts.append("$" + f"{guaranteed:,.0f}" + " guaranteed")
        if not facts:
            continue

        team = str(row["team_code"]) if row["team_code"] is not None else None
        summary = player_label + " signed a " + ", ".join(facts) + " contract"
        if team:
            summary += " associated with " + team
        summary += "."

        subjects = [
            {"subject_type":"NFL_PLAYER","subject_id":str(row["player_key"]),"role":"player"},
        ]
        if team:
            subjects.append({"subject_type":"NFL_TEAM","subject_id":team,"role":"team"})

        upsert_event(conn, {
            "event_type": "CONTRACT",
            "league": "NFL",
            "event_date": str(row["year_signed"]) + "-01-01",
            "title": player_label + " contract in " + str(row["year_signed"]),
            "neutral_summary": summary,
            "source_url": SOURCE_URL,
            "source_publisher": SOURCE_PUBLISHER,
            "evidence_tier": "AUTHORITATIVE",
            "verification_status": "VERIFIED",
            "subjects": subjects,
            "tags": ["contract", "money", "transaction"],
            "sensitive": False,
        })
        inserted += 1
        kinds["CONTRACT"] += 1

    conn.commit()
    return {
        "rows_scanned": min(len(rows), int(limit_rows) if limit_rows else len(rows)),
        "events": inserted,
        "skipped_unresolved_labels": skipped_unresolved,
        "kinds": dict(kinds),
    }
