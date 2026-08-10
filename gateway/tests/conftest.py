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
config.GATEWAY_AUDIT_LOG_DIR = REPO_ROOT / "gateway" / "storage"
config.GATEWAY_AUDIT_LOG_PATH = config.GATEWAY_AUDIT_LOG_DIR / "test_gateway_audit_log.jsonl"
config.OPERATIONAL_LOG_PATH = config.GATEWAY_AUDIT_LOG_DIR / "test_gateway_operational_log.jsonl"

from gateway.app import (  # noqa: E402
    app, generate_limiter, graph_limiter, graph_path_limiter,
    grid_board_limiter, grid_lookup_limiter, preview_limiter,
)


@pytest.fixture(scope="session", autouse=True)
def _clean_test_storage():
    if TEST_PACKAGES_DIR.exists():
        shutil.rmtree(TEST_PACKAGES_DIR)
    TEST_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
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
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}
