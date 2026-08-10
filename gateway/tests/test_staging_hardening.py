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
