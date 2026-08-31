"""Shared pytest fixtures for the Gateway test suite (Director v0.6, Part Q).

Sets a fixed, obviously-fake local test token BEFORE importing the app
(never a real secret, never the value anyone would actually run the
Gateway with) and isolates test-generated packages into their own
directory so running this suite never touches -- and can never collide
with -- gateway/storage/packages/ used by a real local run, nor
generated_games/ (the hand-approved v0.1-v0.4 milestone deliverables).
"""
import os
import shutil
import sys
from pathlib import Path

TEST_ADMIN_TOKEN = "pytest-local-test-token-not-a-real-secret"
os.environ["READS_ENGINE_ADMIN_TOKEN"] = TEST_ADMIN_TOKEN

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from gateway import config  # noqa: E402

# Redirect package storage to a throwaway test directory before the app
# (and therefore gateway.services.packages, which reads config.PACKAGES_DIR
# at call time, not import time) is ever exercised.
TEST_PACKAGES_DIR = REPO_ROOT / "gateway" / "storage" / "test_packages"
config.PACKAGES_DIR = TEST_PACKAGES_DIR
TEST_GAME_STATE_DIR = REPO_ROOT / "gateway" / "storage" / "test_game_state"
config.GAME_STATE_DIR = TEST_GAME_STATE_DIR
config.GATEWAY_AUDIT_LOG_DIR = REPO_ROOT / "gateway" / "storage"
config.GATEWAY_AUDIT_LOG_PATH = config.GATEWAY_AUDIT_LOG_DIR / "test_gateway_audit_log.jsonl"
config.OPERATIONAL_LOG_PATH = config.GATEWAY_AUDIT_LOG_DIR / "test_gateway_operational_log.jsonl"

# v1.4, Part 19: same redirection, for the same reason, for
# tools/director_v02/audit_log.py's LOG_DIR/LOG_PATH -- every test run
# used to append to the real, committed tools/director_v02/logs/
# audit_log.jsonl (no redirect existed at all before this phase), dirtying
# the working tree on every single test run and requiring a manual
# `git restore` before every checkpoint commit. Reassigned as module
# attributes (matching the config.PACKAGES_DIR pattern above) BEFORE
# gateway.app -- and therefore the Director pipeline -- is ever exercised.
from tools.director_v02 import audit_log as director_audit_log  # noqa: E402
director_audit_log.LOG_DIR = REPO_ROOT / "gateway" / "storage" / "test_director_logs"
director_audit_log.LOG_PATH = director_audit_log.LOG_DIR / "audit_log.jsonl"

from gateway.app import (  # noqa: E402
    app, coach_connections_game_limiter, coach_connections_move_limiter,
    coach_connections_search_limiter, creator_job_create_limiter, creator_job_status_limiter,
    generate_limiter, graph_limiter, graph_path_limiter,
    grid_board_limiter, grid_lookup_limiter, preview_limiter,
    public_answer_limiter, public_game_limiter,
    public_six_degrees_answer_limiter, public_six_degrees_game_limiter,
)


@pytest.fixture(scope="session", autouse=True)
def _clean_test_storage():
    if TEST_PACKAGES_DIR.exists():
        shutil.rmtree(TEST_PACKAGES_DIR)
    TEST_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    if TEST_GAME_STATE_DIR.exists():
        shutil.rmtree(TEST_GAME_STATE_DIR)
    TEST_GAME_STATE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Left in place after the run (not deleted) so a failed run's artifacts
    # are inspectable -- next run's setup wipes it fresh anyway.


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    # Every test starts with a clean rate-limit window -- otherwise tests
    # that happen to share the TestClient's fixed test IP (every test does)
    # would see EARLIER tests' /preview or /generate calls count against
    # THEIR limit, which is a test-isolation bug, not evidence about
    # whether the limiter itself works (that's what
    # test_rate_limit_enforced_on_generate below tests directly).
    preview_limiter.reset()
    generate_limiter.reset()
    graph_limiter.reset()
    graph_path_limiter.reset()
    grid_lookup_limiter.reset()
    grid_board_limiter.reset()
    public_game_limiter.reset()
    public_answer_limiter.reset()
    public_six_degrees_game_limiter.reset()
    public_six_degrees_answer_limiter.reset()
    coach_connections_game_limiter.reset()
    coach_connections_move_limiter.reset()
    coach_connections_search_limiter.reset()
    creator_job_create_limiter.reset()
    creator_job_status_limiter.reset()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}


# Production Integrity Fix Pass (2026-08-31), CI hardening: this suite has no
# fixture/mock Football Warehouse -- most tests open the real, multi-GB
# reads_football_v4.0.sqlite via READS_ENGINE_DIR, which is correctly
# gitignored and does not exist on a fresh checkout (a real CI runner has
# none of this project's actual data, on purpose). Without this hook, every
# one of those tests FAILS on a fresh checkout/CI runner rather than being
# recognized as "needs data this environment doesn't have" -- indistinguishable
# from a real regression in CI output.
#
# .ci_needs_real_db.txt is an EMPIRICALLY generated list (not hand-curated):
# the exact 667 node IDs that failed when this suite was run against a
# checkout with no database present at all. When CI_SKIP_DB_TESTS=1 is set
# (see .github/workflows/gateway-tests.yml), those specific tests are marked
# skipped, with a clear reason, instead of counting as failures -- so a fresh
# GitHub Actions run gets a real, meaningful PASS/FAIL signal on the ~426
# tests that never needed a database in the first place, and a new bug in
# ANY of those (or in a test not on this list) still shows up as a genuine
# failure. This is not a substitute for real DB-backed integration coverage
# -- see PRODUCTION_STATUS.md for the actual gap and how to close it (e.g.
# restoring a real database from Fly's own volume snapshots in CI).
def pytest_collection_modifyitems(config, items):
    import os as _os

    if _os.environ.get("CI_SKIP_DB_TESTS") != "1":
        return
    list_path = Path(__file__).with_name(".ci_needs_real_db.txt")
    if not list_path.exists():
        return
    needs_db = {line.strip() for line in list_path.read_text().splitlines() if line.strip()}
    skip_marker = pytest.mark.skip(
        reason="needs the real Football Warehouse DB, not available in this CI job "
               "(see PRODUCTION_STATUS.md, CI section)"
    )
    for item in items:
        if item.nodeid in needs_db:
            item.add_marker(skip_marker)
