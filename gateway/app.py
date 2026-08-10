"""Reads Engine Gateway -- FastAPI app (Director v0.6, hardened for private
staging in v0.7).

    Private Admin -> HTTPS -> staging Gateway -> Director -> Football Warehouse -> QA -> GeneratedGamePackage

Route handlers are intentionally thin: parse/validate the HTTP request,
call one function in `services/`, shape the response. No Director, Game
Factory, or SQL logic lives in this file -- see gateway/services/*.py and
tools/director_v02/*.py for where that logic actually lives (already
proven across Director v0.2-v0.5).

Run locally with:  uvicorn gateway.app:app --port 8850
(port chosen to avoid the 8787-8801 range already used by the eight
existing Engine servers audited in READS_ENGINE_GATEWAY_AUDIT.md). In a
container, this listens on plain HTTP on an internal port -- TLS
termination is the platform/reverse-proxy's job, never homemade in this
process. See READS_ENGINE_STAGING_V01_REPORT.md, Part I.
"""
from __future__ import annotations

import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from . import config  # noqa: E402
from .auth import require_admin, startup_token_check  # noqa: E402
from .errors import GatewayError  # noqa: E402
from .models import GenerateRequest, GridBoardRequest, GridValidateRequest, PreviewRequest  # noqa: E402
from .ratelimit import SlidingWindowRateLimiter  # noqa: E402
from .services import generation, packages  # noqa: E402
from .services import graph as graph_service  # noqa: E402
from .services import grid as grid_service  # noqa: E402
from .services import audit as gateway_audit  # noqa: E402
from .services import oplog  # noqa: E402
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

preview_limiter = SlidingWindowRateLimiter(
    max_requests=config.PREVIEW_RATE_LIMIT_MAX, window_seconds=config.PREVIEW_RATE_LIMIT_WINDOW_SECONDS)
generate_limiter = SlidingWindowRateLimiter(
    max_requests=config.GENERATE_RATE_LIMIT_MAX, window_seconds=config.GENERATE_RATE_LIMIT_WINDOW_SECONDS)
graph_limiter = SlidingWindowRateLimiter(
    max_requests=config.GRAPH_RATE_LIMIT_MAX, window_seconds=config.GRAPH_RATE_LIMIT_WINDOW_SECONDS)
graph_path_limiter = SlidingWindowRateLimiter(
    max_requests=config.GRAPH_PATH_RATE_LIMIT_MAX, window_seconds=config.GRAPH_PATH_RATE_LIMIT_WINDOW_SECONDS)
grid_lookup_limiter = SlidingWindowRateLimiter(
    max_requests=config.GRID_LOOKUP_RATE_LIMIT_MAX, window_seconds=config.GRID_LOOKUP_RATE_LIMIT_WINDOW_SECONDS)
grid_board_limiter = SlidingWindowRateLimiter(
    max_requests=config.GRID_BOARD_RATE_LIMIT_MAX, window_seconds=config.GRID_BOARD_RATE_LIMIT_WINDOW_SECONDS)


def _validate_origins_or_die() -> list[str]:
    origins = config.allowed_origins()
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise SystemExit(
                f"FATAL: {config.ALLOWED_ORIGINS_ENV_VAR} contains a malformed origin {origin!r} "
                f"-- refusing to start with an invalid CORS configuration (Part J)."
            )
    return origins


ALLOWED_ORIGINS = _validate_origins_or_die()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup (Part F/L/N) ---
    weak_reason = startup_token_check()
    if weak_reason:
        print(f"[gateway] WARNING: {config.ADMIN_TOKEN_ENV_VAR} looks weak ({weak_reason}). "
              f"Not fatal, but should be regenerated before real staging use.", file=sys.stderr)
    readiness = engine_bootstrap.check_engine_readiness()
    if readiness["ready"]:
        print(f"[gateway] startup OK -- Engine DB ready (database_version={readiness.get('database_version')}, "
              f"draft_facts_row_count={readiness.get('draft_facts_row_count')})", file=sys.stderr)
    else:
        print(f"[gateway] WARNING: Engine DB not ready at startup: {readiness['reason']}. "
              f"Service will report itself unready via /v1/ready until this is fixed.", file=sys.stderr)
    print(f"[gateway] CORS allowed origins: {ALLOWED_ORIGINS}", file=sys.stderr)
    yield
    # --- shutdown (Part K) ---
    # No explicit action needed beyond this log line: package writes are
    # already atomic (temp file + os.replace in gateway/services/packages.py),
    # so a request cut off mid-generation during shutdown never leaves a
    # corrupt/partial package visible under its real name -- worst case is
    # an abandoned .tmp file, not a broken one. uvicorn's own default
    # SIGTERM handling (stop accepting new connections, let in-flight
    # requests finish) is sufficient; no custom signal handler was needed.
    print("[gateway] shutdown -- no in-progress generation state to flush (atomic writes only).", file=sys.stderr)


app = FastAPI(title="Reads Engine Gateway", version=config.API_VERSION, docs_url="/v1/docs",
              openapi_url="/v1/openapi.json", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # NOT "*" -- see Part J / config.py
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_id_and_body_limit(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > config.MAX_BODY_BYTES:
        oplog.record(request_id=request_id, route=request.url.path, method=request.method,
                      status_code=400, latency_ms=0.0, error_code="INVALID_REQUEST")
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_REQUEST",
                                "message": f"Request body exceeds the {config.MAX_BODY_BYTES}-byte limit.",
                                "request_id": request_id}},
        )

    t0 = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - t0) * 1000
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{latency_ms:.1f}"
    oplog.record(request_id=request_id, route=request.url.path, method=request.method,
                 status_code=response.status_code, latency_ms=latency_ms)
    return response


def _rate_limit(limiter: SlidingWindowRateLimiter, request: Request) -> None:
    # Keyed by client IP -- meaningful even though every legitimate caller
    # currently shares one admin token (Part F explicitly keeps this to a
    # single shared secret for v0.7), because this guards against a
    # request-frequency flood regardless of whether the caller ever
    # supplies a valid token -- an unauthenticated flood of guesses is
    # exactly as capable of exhausting this limit as an authenticated one.
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = limiter.allow(client_ip)
    if not allowed:
        raise GatewayError(
            "RATE_LIMITED",
            f"Rate limit exceeded for this endpoint. Retry after ~{retry_after:.1f}s.",
            extra={"retry_after_seconds": round(retry_after, 1)},
        )


def rate_limit_preview(request: Request) -> None:
    _rate_limit(preview_limiter, request)


def rate_limit_generate(request: Request) -> None:
    _rate_limit(generate_limiter, request)


def rate_limit_graph(request: Request) -> None:
    _rate_limit(graph_limiter, request)


def rate_limit_graph_path(request: Request) -> None:
    _rate_limit(graph_path_limiter, request)


def rate_limit_grid_lookup(request: Request) -> None:
    _rate_limit(grid_lookup_limiter, request)


def rate_limit_grid_board(request: Request) -> None:
    _rate_limit(grid_board_limiter, request)


@app.exception_handler(GatewayError)
async def gateway_error_handler(request: Request, exc: GatewayError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(status_code=exc.status_code, content=exc.body(request_id))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Part I: ONE consistent error shape for every error, including FastAPI's
    # own request-body/query validation failures (malformed JSON, a field
    # failing its Pydantic constraint, an extra/forbidden field) -- without
    # this handler these would fall through to FastAPI's own default
    # `{"detail": [...]}` shape instead, which would make this "one
    # consistent API error shape" claim false for a whole class of errors.
    request_id = getattr(request.state, "request_id", "unknown")
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", []) if p != "body") or None
    message = first.get("msg", "Invalid request.")
    if field:
        message = f"{field}: {message}"
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "INVALID_REQUEST", "message": message, "request_id": request_id}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Part I: never expose a stack trace or raw exception text to the client.
    # The technical detail is logged locally (stderr, picked up by whatever
    # runs this process) -- never in the HTTP response body.
    request_id = getattr(request.state, "request_id", "unknown")
    print(f"[gateway] INTERNAL_ERROR request_id={request_id}: {exc!r}", file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred.", "request_id": request_id}},
    )


@app.get("/v1/health")
def health():
    """Liveness only: 'is the Gateway process alive?' Unauthenticated,
    free, reveals nothing sensitive (Part F), and deliberately does NOT
    check the Engine database -- see /v1/ready for that. A platform health
    check that only needs to know "should I restart this process" should
    hit this, not /v1/ready (Part L)."""
    return {"status": "ok", "service": config.SERVICE_NAME, "api_version": config.API_VERSION}


@app.get("/v1/ready")
def ready():
    """Readiness: 'can this instance actually serve Engine requests?' Part L:
    lightweight (a PRAGMA quick_check plus one indexed COUNT, not a full
    generation-scale audit), unauthenticated for the same reason /v1/health
    is (platform health checks generally can't supply an admin token, and
    this reveals nothing beyond 'is the DB there and readable'). Returns
    503 (not 200) when unready, matching how a platform's health-check
    mechanism actually distinguishes healthy from unhealthy."""
    readiness = engine_bootstrap.check_engine_readiness()
    packages_dir_ok = True
    packages_dir_reason = None
    try:
        config.PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
        probe = config.PACKAGES_DIR / ".readiness-probe"
        probe.write_text("ok")
        probe.unlink()
    except OSError as e:
        packages_dir_ok = False
        packages_dir_reason = str(e)

    body = {
        "status": "ready" if (readiness["ready"] and packages_dir_ok) else "not_ready",
        "engine_database": readiness,
        "package_storage": {"writable": packages_dir_ok, "reason": packages_dir_reason},
    }
    if body["status"] != "ready":
        return JSONResponse(status_code=503, content=body)
    return body


@app.get("/v1/capabilities")
def capabilities():
    """Unauthenticated -- see auth.py's module docstring for why. Returns
    only genuinely registered, executable capabilities (Part D) -- never a
    predicate merely because it exists somewhere in Engine code.

    `graph_capabilities` is a second, separate list (not merged into
    `capabilities`) -- Director capabilities are (mechanic, domain,
    relationship_predicate) tuples describing generated quiz content; the
    three graph operations are direct read/traversal endpoints with no
    equivalent shape. Kept as two lists under one response so a client
    still only needs to call this one route to discover everything, without
    pretending the two are the same kind of thing (see graph.py's module
    docstring for the full reasoning)."""
    return {
        "capabilities": generation.list_capabilities(),
        "graph_capabilities": graph_service.list_graph_capabilities(),
        "grid_capabilities": grid_service.list_grid_capabilities(),
    }


@app.post("/v1/games/preview")
def games_preview(body: PreviewRequest, request: Request,
                   _rl=Depends(rate_limit_preview), _admin=Depends(require_admin)):
    result = generation.preview(request_text=body.request_text, spec=body.spec, provider=body.provider)
    gateway_audit.record_preview(request_id=request.state.request_id, body=body, result=result)
    return result


@app.post("/v1/games/generate")
def games_generate(body: GenerateRequest, request: Request,
                    _rl=Depends(rate_limit_generate), _admin=Depends(require_admin)):
    t0 = time.perf_counter()
    result = generation.generate(
        request_text=body.request_text, spec=body.spec, provider=body.provider,
        puzzle_count=body.puzzle_count, difficulty=body.difficulty, seed=body.seed,
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    stored = None
    if result.get("package_id") and result.get("qa_status") == "PASSED":
        stored = packages.save_package(result)

    gateway_audit.record_generate(request_id=request.state.request_id, body=body, result=result, latency_ms=latency_ms)

    if stored is not None:
        return stored
    return result


@app.get("/v1/games/{package_id}")
def games_get(package_id: str, _admin=Depends(require_admin)):
    try:
        record = packages.load_package(package_id)
    except packages.PackageIdInvalid:
        raise GatewayError("PACKAGE_NOT_FOUND", "No such package.")
    if record is None:
        raise GatewayError("PACKAGE_NOT_FOUND", "No such package.")
    return record


# --- Graph / Six Degrees (v0.7 port) ----------------------------------------
# Admin-gated like every other Engine-DB-touching route in this Gateway
# (Part F's private-staging scope) -- see graph.py's module docstring for
# why these are three separate routes rather than folded into
# /v1/games/preview|generate's (mechanic, domain, predicate) shape.

@app.get("/v1/graph/search")
def graph_search(request: Request, query: str = Query(..., min_length=1, max_length=200),
                  limit: int = Query(default=20, ge=1, le=config.GRAPH_SEARCH_LIMIT_MAX),
                  _rl=Depends(rate_limit_graph), _admin=Depends(require_admin)):
    results = graph_service.search(query=query, limit=limit)
    return {"query": query, "limit": limit, "count": len(results), "results": results}


@app.get("/v1/graph/path")
def graph_path(request: Request,
                start_type: str = Query(..., min_length=1, max_length=graph_service.MAX_NODE_TYPE_LENGTH),
                start_id: str = Query(..., min_length=1, max_length=graph_service.MAX_NODE_ID_LENGTH),
                end_type: str = Query(..., min_length=1, max_length=graph_service.MAX_NODE_TYPE_LENGTH),
                end_id: str = Query(..., min_length=1, max_length=graph_service.MAX_NODE_ID_LENGTH),
                max_depth: Optional[int] = Query(default=None, ge=1, le=config.GRAPH_PATH_MAX_DEPTH_LIMIT),
                _rl=Depends(rate_limit_graph_path), _admin=Depends(require_admin)):
    return graph_service.shortest_path(
        start_type=start_type, start_id=start_id, end_type=end_type, end_id=end_id, max_depth=max_depth)


@app.get("/v1/six-degrees")
def six_degrees_route(request: Request,
                       seed: str = Query(default="daily", min_length=1, max_length=128),
                       min_len: Optional[int] = Query(default=None, ge=1, le=config.SIX_DEGREES_MAX_LEN_LIMIT),
                       max_len: Optional[int] = Query(default=None, ge=1, le=config.SIX_DEGREES_MAX_LEN_LIMIT),
                       _rl=Depends(rate_limit_graph), _admin=Depends(require_admin)):
    return graph_service.six_degrees(seed=seed, min_len=min_len, max_len=max_len)


# --- Grid roster/eligibility (v0.7 Grid roster-merge port) ------------------
# Content-pipeline model, confirmed with the user before building this (see
# gateway/services/grid.py's module docstring): admin/QA-only, never called
# by the live frontend. data/grid.js and app.js's Grid game are UNCHANGED by
# this section -- these routes let content ops verify/QA data/grid.js
# entries against the Engine's real graph.

@app.get("/v1/grid/criteria")
def grid_criteria(request: Request, _rl=Depends(rate_limit_grid_lookup), _admin=Depends(require_admin)):
    return grid_service.list_supported_criteria()


@app.post("/v1/grid/board")
def grid_board(body: GridBoardRequest, request: Request,
                _rl=Depends(rate_limit_grid_board), _admin=Depends(require_admin)):
    return grid_service.build_board(row_ids=body.row_ids, col_ids=body.col_ids, season=body.season)


@app.get("/v1/grid/intersection")
def grid_intersection(request: Request,
                       row_id: str = Query(..., min_length=1, max_length=64),
                       col_id: str = Query(..., min_length=1, max_length=64),
                       season: Optional[int] = Query(default=None, ge=1920, le=2100),
                       _rl=Depends(rate_limit_grid_lookup), _admin=Depends(require_admin)):
    return grid_service.resolve_intersection(row_id=row_id, col_id=col_id, season=season)


@app.post("/v1/grid/validate")
def grid_validate(body: GridValidateRequest, request: Request,
                   _rl=Depends(rate_limit_grid_board), _admin=Depends(require_admin)):
    return grid_service.validate_answer(row_id=body.row_id, col_id=body.col_id, player_name=body.player_name, season=body.season)


@app.get("/v1/grid/player/{node_id}")
def grid_player(node_id: str, request: Request,
                 _rl=Depends(rate_limit_grid_lookup), _admin=Depends(require_admin)):
    return grid_service.player_metadata(node_id=node_id)
