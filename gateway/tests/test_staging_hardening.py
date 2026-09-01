"""Reads Engine Gateway -- staging-hardening test suite (Director v0.7).

Covers everything added this milestone that v0.6's test_gateway.py doesn't:
rate limiting, liveness/readiness distinction, and the security-regression
checks Part U explicitly asks to re-run and preserve (restated here so this
milestone has its own standalone evidence, not just a claim that v0.6's
suite still passes).
"""
import time
from concurrent.futures import ThreadPoolExecutor

from gateway import config

DRAFT_REQUEST = "Make a guessing game where I see an NFL player and have to guess which NFL team drafted him."
CLUES_REQUEST = "Make me a game where you give me clues about an NFL player and I have to identify him."


# --- liveness vs readiness (Part L) -----------------------------------------

def test_health_is_liveness_only_and_fast(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "reads-engine-gateway", "api_version": "v1"}


def test_ready_reports_real_engine_status(client):
    r = client.get("/v1/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["engine_database"]["ready"] is True
    assert body["engine_database"]["database_version"] == "4.0.0"
    assert body["package_storage"]["writable"] is True
    assert "disk" in body
    assert isinstance(body["disk"]["free_percent"], (int, float))


# --- disk headroom (Reliability Cleanup pass) --------------------------------
# Regression coverage for the real, twice-confirmed production incident: the
# Fly volume filling to 100% broke every request (oplog couldn't open its log
# file) with no warning, because nothing checked disk headroom before it was
# already too late. /v1/ready now fails BELOW config.DISK_FREE_PERCENT_MIN so
# Fly's own already-polling health check (every 30s) catches this before a
# full disk actually breaks anything.

import shutil as _shutil_module
from collections import namedtuple

_DiskUsage = namedtuple("_DiskUsage", ["total", "used", "free"])


def _fake_disk_usage(free_percent):
    total = 1000
    free = int(total * free_percent / 100)
    return _DiskUsage(total=total, used=total - free, free=free)


def test_ready_fails_below_the_disk_free_percent_threshold(client, monkeypatch):
    monkeypatch.setattr(config, "DISK_FREE_PERCENT_MIN", 10.0)
    monkeypatch.setattr(_shutil_module, "disk_usage", lambda path: _fake_disk_usage(5.0))

    r = client.get("/v1/ready")

    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "not_ready"
    assert body["disk"]["free_percent"] == 5.0


def test_ready_passes_right_at_and_above_the_disk_free_percent_threshold(client, monkeypatch):
    monkeypatch.setattr(config, "DISK_FREE_PERCENT_MIN", 10.0)
    monkeypatch.setattr(_shutil_module, "disk_usage", lambda path: _fake_disk_usage(10.0))

    r = client.get("/v1/ready")

    assert r.status_code == 200
    assert r.json()["status"] == "ready"
    assert r.json()["disk"]["free_percent"] == 10.0


def test_ready_reports_disk_ok_false_but_does_not_crash_on_a_disk_usage_error(client, monkeypatch):
    monkeypatch.setattr(config, "DISK_FREE_PERCENT_MIN", 10.0)

    def _raise(path):
        raise OSError("simulated disk_usage failure")

    monkeypatch.setattr(_shutil_module, "disk_usage", _raise)

    r = client.get("/v1/ready")

    assert r.status_code == 503
    assert r.json()["disk"]["free_percent"] is None


# --- rate limiting (Part G) --------------------------------------------------

def test_rate_limit_enforced_on_generate(client, auth_headers, monkeypatch):
    from gateway.app import generate_limiter
    monkeypatch.setattr(generate_limiter, "max_requests", 3)
    generate_limiter.reset()

    responses = [
        client.post("/v1/games/generate", json={"request_text": DRAFT_REQUEST, "puzzle_count": 1, "seed": f"ratelimit-{i}"},
                     headers=auth_headers)
        for i in range(5)
    ]
    statuses = [r.status_code for r in responses]
    assert statuses.count(429) >= 2, f"expected at least 2 rate-limited responses, got {statuses}"
    limited = [r for r in responses if r.status_code == 429][0]
    body = limited.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert "retry_after_seconds" in body["error"]
    generate_limiter.reset()
    monkeypatch.setattr(generate_limiter, "max_requests", config.GENERATE_RATE_LIMIT_MAX)


def test_rate_limit_enforced_on_preview(client, auth_headers, monkeypatch):
    from gateway.app import preview_limiter
    monkeypatch.setattr(preview_limiter, "max_requests", 2)
    preview_limiter.reset()

    responses = [
        client.post("/v1/games/preview", json={"request_text": DRAFT_REQUEST}, headers=auth_headers)
        for _ in range(4)
    ]
    statuses = [r.status_code for r in responses]
    assert statuses.count(429) >= 1, f"expected at least 1 rate-limited response, got {statuses}"
    preview_limiter.reset()
    monkeypatch.setattr(preview_limiter, "max_requests", config.PREVIEW_RATE_LIMIT_MAX)


def test_rate_limit_does_not_bypass_generation_busy(client, auth_headers):
    # Part G explicitly requires "existing GENERATION_BUSY behavior
    # preserved" -- confirm both protections coexist: within the
    # rate-limit's own bounds, concurrent generation still hits the
    # single-job guard, not just the rate limiter.
    def call(i):
        return client.post("/v1/games/generate",
                            json={"request_text": CLUES_REQUEST, "puzzle_count": 2, "seed": f"busy-check-{i}"},
                            headers=auth_headers)

    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(call, range(3)))
    codes = sorted(r.json().get("error", {}).get("code") or "OK" for r in results)
    assert "OK" in codes
    assert codes.count("GENERATION_BUSY") == 2


# --- security regression (Part U) -------------------------------------------

def test_no_admin_secret_in_openapi_schema(client):
    r = client.get("/v1/openapi.json")
    assert r.status_code == 200
    assert config.admin_token() not in r.text


def test_capabilities_response_has_no_engine_internals(client):
    r = client.get("/v1/capabilities")
    text = r.text
    for forbidden in ("sqlite3", "reads_football_v4.0.sqlite", "/Users/", "game_factory.py"):
        assert forbidden not in text
