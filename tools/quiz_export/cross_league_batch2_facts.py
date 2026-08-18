"""Cross-league value measurement for Knowledge Expansion Batch 2 --
quantifies how the new NFL All-Pro / Pro Bowl / HOF facts connect back to
Batch 1's CFB All-America and transfer facts via the certified
`cfb_nfl_identity_bridge_certified` bridge. Measurement only, per
instruction -- no new game mechanics here.
"""
from __future__ import annotations


def all_america_to_all_pro(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_all_america_certified").fetchone()[0]
    joined = c.execute(
        "SELECT COUNT(DISTINCT a.cfb_player_id) FROM cfb_all_america_certified a "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = a.cfb_player_id "
        "JOIN nfl_all_pro_selections p ON p.player_id = b.nfl_player_key AND p.is_ap = 1"
    ).fetchone()[0]
    return {"all_america_players": total, "also_ap_all_pro": joined,
            "percentage": round(100.0 * joined / total, 1) if total else 0.0}


def all_america_to_pro_bowl(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_all_america_certified").fetchone()[0]
    joined = c.execute(
        "SELECT COUNT(DISTINCT a.cfb_player_id) FROM cfb_all_america_certified a "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = a.cfb_player_id "
        "JOIN nfl_pro_bowl_selections p ON p.player_id = b.nfl_player_key"
    ).fetchone()[0]
    return {"all_america_players": total, "also_pro_bowl": joined,
            "percentage": round(100.0 * joined / total, 1) if total else 0.0}


def all_america_to_hof(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_all_america_certified").fetchone()[0]
    joined = c.execute(
        "SELECT COUNT(DISTINCT a.cfb_player_id) FROM cfb_all_america_certified a "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = a.cfb_player_id "
        "JOIN nfl_hof_inductees h ON h.player_id = b.nfl_player_key AND h.is_player = 1"
    ).fetchone()[0]
    return {"all_america_players": total, "also_hall_of_fame": joined,
            "percentage": round(100.0 * joined / total, 1) if total else 0.0}


def transfer_to_all_pro_pro_bowl_hof(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_transfer_summary WHERE transfer_count > 0").fetchone()[0]
    ap = c.execute(
        "SELECT COUNT(DISTINCT t.cfb_player_id) FROM cfb_transfer_summary t "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = t.cfb_player_id "
        "JOIN nfl_all_pro_selections p ON p.player_id = b.nfl_player_key AND p.is_ap = 1 "
        "WHERE t.transfer_count > 0"
    ).fetchone()[0]
    pb = c.execute(
        "SELECT COUNT(DISTINCT t.cfb_player_id) FROM cfb_transfer_summary t "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = t.cfb_player_id "
        "JOIN nfl_pro_bowl_selections p ON p.player_id = b.nfl_player_key "
        "WHERE t.transfer_count > 0"
    ).fetchone()[0]
    hof = c.execute(
        "SELECT COUNT(DISTINCT t.cfb_player_id) FROM cfb_transfer_summary t "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.cfb_player_id = t.cfb_player_id "
        "JOIN nfl_hof_inductees h ON h.player_id = b.nfl_player_key AND h.is_player = 1 "
        "WHERE t.transfer_count > 0"
    ).fetchone()[0]
    return {"real_transfers": total, "also_ap_all_pro": ap, "also_pro_bowl": pb, "also_hall_of_fame": hof}


def college_to_hof_players(c) -> list[dict]:
    """COLLEGE -> HOF_PLAYERS (aggregate). Real, but note: joins on the
    existing `nfl_players_draft.college` RAW text field (the same field
    nfl_wikipedia_history_import.py's `_college_for_player` already
    relies on) -- not a canonical school_id, since neither
    `canonical_players` nor `canonical_roster_seasons` carry a populated
    school_id for these players. Grouped by the raw college string as-is,
    never normalized/guessed into a canonical school."""
    rows = c.execute(
        "SELECT d.college, COUNT(DISTINCT h.hof_id) n FROM nfl_hof_inductees h "
        "JOIN nfl_players_draft d ON d.pfr_id = (SELECT pfr_id FROM canonical_players WHERE player_id = h.player_id) "
        "WHERE h.is_player = 1 AND d.college IS NOT NULL GROUP BY d.college ORDER BY n DESC LIMIT 10"
    ).fetchall()
    return [dict(r) for r in rows]


def college_to_all_pro_count(c) -> dict:
    """COLLEGE -> NFL_ALL_PROS, aggregate count via the certified bridge
    (distinct AP-confirmed players who also have a real bridged CFB identity)."""
    total = c.execute(
        "SELECT COUNT(DISTINCT p.player_id) FROM nfl_all_pro_selections p "
        "JOIN cfb_nfl_identity_bridge_certified b ON b.nfl_player_key = p.player_id WHERE p.is_ap = 1"
    ).fetchone()[0]
    return {"distinct_ap_all_pro_players_with_cfb_identity": total}
