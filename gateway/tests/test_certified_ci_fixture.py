from __future__ import annotations

import sqlite3

from gateway.services import public_game
from tools.director_v02 import registry
from tools.quiz_export import engine


def test_certified_fixture_passes_gateway_readiness():
    result = engine.check_engine_readiness()
    assert result["ready"] is True
    assert result["database_version"] == "ci-certified-v1"
    assert result["draft_facts_row_count"] >= 4


def test_certified_fixture_has_representative_nfl_and_cfb_games():
    c = engine.connect()
    try:
        rows = c.execute(
            "SELECT competition, COUNT(*) n FROM games GROUP BY competition ORDER BY competition"
        ).fetchall()
    finally:
        c.close()
    assert {row[0]: row[1] for row in rows} == {"CFB": 2, "NFL": 2}


def test_certified_fixture_public_catalog_matches_actual_public_routes():
    expected = {
        (
            entry["spec"]["mechanic"],
            entry["spec"]["domain"],
            entry["spec"]["relationship_predicate"],
        )
        for entry in public_game.PUBLIC_MODES.values()
    }
    c = engine.connect()
    try:
        actual = {
            (row[0], row[1], row[2])
            for row in c.execute(
                "SELECT mechanic,domain,relationship_predicate FROM capability_catalog "
                "WHERE public_availability='PUBLIC_ENABLED'"
            )
        }
    finally:
        c.close()
    assert actual == expected


def test_every_fixture_public_capability_is_still_registered():
    c = engine.connect()
    try:
        triples = [
            tuple(row)
            for row in c.execute(
                "SELECT mechanic,domain,relationship_predicate FROM capability_catalog"
            )
        ]
    finally:
        c.close()
    missing = [triple for triple in triples if triple not in registry.CAPABILITY_REGISTRY]
    assert missing == []


def test_certified_fixture_is_small_enough_for_routine_ci():
    path = engine.db_path()
    assert path.stat().st_size < 5 * 1024 * 1024
