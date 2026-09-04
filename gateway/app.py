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

import shutil
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import BackgroundTasks, Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from . import config  # noqa: E402
from .auth import require_admin, startup_token_check  # noqa: E402
from .errors import GatewayError  # noqa: E402
from .models import (AdminPickemGameStatusRequest, CreatorConceptsRequest, CreatorFeasibilityRequest,  # noqa: E402
                      CreatorGenerateRequest,
                      CreatorIdeasRequest, CreatorJobTier2CertificationRequest,
                      CreatorReviewRequest,
                      GenerateRequest, GridBoardRequest, GridValidateRequest,
                      MechanicRoundRequest, MechanicSubmitRequest, PreviewRequest,
                      PublicAnswerRequest, PublicCoachConnectionsMoveRequest, PublicCoachConnectionsRevealRequest,
                      PublicMechanicSubmitRequest, PublicPickemSubmitRequest,
                      PublicSixDegreesAnswerRequest, PublicSixDegreesRevealRequest)
from .ratelimit import SlidingWindowRateLimiter  # noqa: E402
from .services import creator as creator_service  # noqa: E402
from .services import generation, packages, game_state  # noqa: E402
from .services import graph as graph_service  # noqa: E402
from .services import grid as grid_service  # noqa: E402
from .services import admin_refresh  # noqa: E402
from .services import admin_pickem  # noqa: E402
from .services import public_coach_connections  # noqa: E402
from .services import public_game  # noqa: E402
from .services import public_mechanics  # noqa: E402
from .services import public_pickem  # noqa: E402
from .services import public_six_degrees  # noqa: E402
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
public_game_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_GAME_RATE_LIMIT_MAX, window_seconds=config.PUBLIC_GAME_RATE_LIMIT_WINDOW_SECONDS)
public_answer_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_ANSWER_RATE_LIMIT_MAX, window_seconds=config.PUBLIC_ANSWER_RATE_LIMIT_WINDOW_SECONDS)
public_six_degrees_game_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_SIX_DEGREES_GAME_RATE_LIMIT_MAX,
    window_seconds=config.PUBLIC_SIX_DEGREES_GAME_RATE_LIMIT_WINDOW_SECONDS)
public_six_degrees_answer_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_SIX_DEGREES_ANSWER_RATE_LIMIT_MAX,
    window_seconds=config.PUBLIC_SIX_DEGREES_ANSWER_RATE_LIMIT_WINDOW_SECONDS)
coach_connections_game_limiter = SlidingWindowRateLimiter(
    max_requests=config.COACH_CONNECTIONS_GAME_RATE_LIMIT_MAX,
    window_seconds=config.COACH_CONNECTIONS_GAME_RATE_LIMIT_WINDOW_SECONDS)
coach_connections_move_limiter = SlidingWindowRateLimiter(
    max_requests=config.COACH_CONNECTIONS_MOVE_RATE_LIMIT_MAX,
    window_seconds=config.COACH_CONNECTIONS_MOVE_RATE_LIMIT_WINDOW_SECONDS)
coach_connections_search_limiter = SlidingWindowRateLimiter(
    max_requests=config.COACH_CONNECTIONS_SEARCH_RATE_LIMIT_MAX,
    window_seconds=config.COACH_CONNECTIONS_SEARCH_RATE_LIMIT_WINDOW_SECONDS)
creator_job_create_limiter = SlidingWindowRateLimiter(
    max_requests=config.CREATOR_JOB_CREATE_RATE_LIMIT_MAX,
    window_seconds=config.CREATOR_JOB_CREATE_RATE_LIMIT_WINDOW_SECONDS)
creator_job_status_limiter = SlidingWindowRateLimiter(
    max_requests=config.CREATOR_JOB_STATUS_RATE_LIMIT_MAX,
    window_seconds=config.CREATOR_JOB_STATUS_RATE_LIMIT_WINDOW_SECONDS)
public_pickem_view_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_PICKEM_VIEW_RATE_LIMIT_MAX,
    window_seconds=config.PUBLIC_PICKEM_VIEW_RATE_LIMIT_WINDOW_SECONDS)
public_pickem_submit_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_PICKEM_SUBMIT_RATE_LIMIT_MAX,
    window_seconds=config.PUBLIC_PICKEM_SUBMIT_RATE_LIMIT_WINDOW_SECONDS)
public_mechanic_round_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_MECHANIC_ROUND_RATE_LIMIT_MAX,
    window_seconds=config.PUBLIC_MECHANIC_ROUND_RATE_LIMIT_WINDOW_SECONDS)
public_mechanic_submit_limiter = SlidingWindowRateLimiter(
    max_requests=config.PUBLIC_MECHANIC_SUBMIT_RATE_LIMIT_MAX,
    window_seconds=config.PUBLIC_MECHANIC_SUBMIT_RATE_LIMIT_WINDOW_SECONDS)


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
    # Readiness-latency fix: startup is the one place a real, full
    # PRAGMA quick_check (up to ~166s against the production Fly volume,
    # measured directly) is genuinely acceptable -- once per process boot,
    # never on the polled /v1/ready hot path. See
    # tools/quiz_export/engine.py's check_engine_readiness_deep() docstring
    # for the full incident this split fixes.
    readiness = engine_bootstrap.check_engine_readiness_deep()
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


def rate_limit_public_game(request: Request) -> None:
    _rate_limit(public_game_limiter, request)


def rate_limit_public_answer(request: Request) -> None:
    _rate_limit(public_answer_limiter, request)


def rate_limit_public_six_degrees_game(request: Request) -> None:
    _rate_limit(public_six_degrees_game_limiter, request)


def rate_limit_public_six_degrees_answer(request: Request) -> None:
    _rate_limit(public_six_degrees_answer_limiter, request)


def rate_limit_coach_connections_game(request: Request) -> None:
    _rate_limit(coach_connections_game_limiter, request)


def rate_limit_coach_connections_move(request: Request) -> None:
    _rate_limit(coach_connections_move_limiter, request)


def rate_limit_coach_connections_search(request: Request) -> None:
    _rate_limit(coach_connections_search_limiter, request)


def rate_limit_creator_job_create(request: Request) -> None:
    _rate_limit(creator_job_create_limiter, request)


def rate_limit_creator_job_status(request: Request) -> None:
    _rate_limit(creator_job_status_limiter, request)


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
    lightweight (DB opens + one indexed COUNT + a schema-marker lookup, not
    a full generation-scale audit, and -- since the readiness-latency
    incident -- deliberately NOT a PRAGMA quick_check; see
    tools/quiz_export/engine.py's check_engine_readiness() docstring),
    unauthenticated for the same reason /v1/health is (platform health
    checks generally can't supply an admin token, and this reveals nothing
    beyond 'is the DB there and readable'). Returns
    503 (not 200) when unready, matching how a platform's health-check
    mechanism actually distinguishes healthy from unhealthy.

    v1.4, Part 6: a real gap found by actually reading this route's output,
    not assumed -- `engine_database`/`package_storage` used to embed the
    real server filesystem path (via `check_engine_readiness()`'s `reason`
    string and `db_path`, and a raw `OSError` message that can itself
    contain a path) directly in this PUBLIC, unauthenticated response body.
    Now only a safe, fixed-vocabulary `reason_code` and non-path fields are
    exposed here; the full path-bearing detail still goes to the operator
    stderr log at startup (see the lifespan handler above) and is available
    to whoever operates the platform's own log viewer, never to an
    anonymous HTTP caller. Part 4: also confirms the public mode registry
    and capability registry both loaded without error -- in practice this
    can only fail if the process itself failed to start (both are built at
    import time), but an explicit check here is cheap and matches Part 4's
    ask directly rather than relying on that being true by construction."""
    readiness = engine_bootstrap.check_engine_readiness()
    safe_engine_status: dict = {"ready": readiness["ready"]}
    if readiness["ready"]:
        safe_engine_status["database_version"] = readiness.get("database_version")
    else:
        safe_engine_status["reason_code"] = readiness.get("reason_code", "UNKNOWN")

    packages_dir_ok = True
    try:
        config.PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
        probe = config.PACKAGES_DIR / ".readiness-probe"
        probe.write_text("ok")
        probe.unlink()
    except OSError:
        packages_dir_ok = False

    registry_ok = True
    try:
        public_game.list_public_modes()
        generation.list_capabilities()
    except Exception:
        registry_ok = False

    # Production Integrity Fix Pass: the real 2026-08-31 outage was a 100%-full
    # volume, invisible to every check above -- packages_dir_ok/registry_ok
    # only fail once the disk is ALREADY full enough to break a write, and
    # engine_database.ready only checks the DB opens, not free space. Fly
    # already polls this endpoint every 30s (fly.toml) as its readiness
    # check, so surfacing disk headroom here -- and failing readiness before
    # a full disk actually breaks anything -- reuses that existing polling
    # loop instead of standing up new infrastructure. Only reports a
    # percentage (never a path), same "no filesystem detail to an anonymous
    # caller" rule as the rest of this route.
    disk_ok = True
    disk_status: dict = {}
    try:
        usage = shutil.disk_usage(config.PACKAGES_DIR)
        free_pct = round(100 * usage.free / usage.total, 1) if usage.total else 0.0
        disk_status = {"free_percent": free_pct}
        if free_pct < config.DISK_FREE_PERCENT_MIN:
            disk_ok = False
    except OSError:
        disk_ok = False
        disk_status = {"free_percent": None}

    body = {
        "status": "ready" if (readiness["ready"] and packages_dir_ok and registry_ok and disk_ok) else "not_ready",
        "engine_database": safe_engine_status,
        "package_storage": {"writable": packages_dir_ok},
        "mode_registry": {"loaded": registry_ok},
        "disk": disk_status,
    }
    if body["status"] != "ready":
        return JSONResponse(status_code=503, content=body)
    return body


@app.get("/v1/admin/diagnostics/db-integrity")
def admin_db_integrity(request: Request, _admin=Depends(require_admin)):
    """Readiness-latency fix: the full PRAGMA quick_check this route used to
    run on every /v1/ready poll now lives ONLY here (admin-gated, on-demand)
    and at process startup (gateway/app.py's lifespan handler) -- never on
    the polled hot path. A real, deliberately slow (can take minutes against
    the production volume, same as it always could) structural integrity
    certification for manual/maintenance use, not a frequently-called
    endpoint. See tools/quiz_export/engine.py's check_engine_readiness_deep()
    docstring for the incident this split fixes."""
    result = engine_bootstrap.check_engine_readiness_deep()
    safe: dict = {"ready": result["ready"], "deep_integrity_checked": result.get("deep_integrity_checked", True)}
    if result["ready"]:
        safe["database_version"] = result.get("database_version")
        safe["draft_facts_row_count"] = result.get("draft_facts_row_count")
    else:
        safe["reason_code"] = result.get("reason_code", "UNKNOWN")
    return safe


@app.get("/v1/admin/diagnostics/data-coverage")
def admin_data_coverage(request: Request, _admin=Depends(require_admin)):
    """Final Technical Risk Cleanup pass: a DIFFERENT, distinct diagnostic
    from db-integrity above -- that route certifies STRUCTURE (the file
    opens, the schema is intact); this one certifies real historical DEPTH
    on the multi-season tables ELIMINATION_SURVIVAL and other capabilities
    depend on. The real incident this exists to make visible without an
    SSH session next time: production's `cfb_standings` silently held only
    the current season (138 rows) after only the routine "current season
    only" scheduled refresh had ever run there -- every row present was
    genuinely SOURCE_BACKED, so no existing integrity/safety check caught
    it. See tools/quiz_export/safety.py's check_season_coverage_safety()."""
    from tools.quiz_export import safety as quiz_safety
    c = engine_bootstrap.connect()
    try:
        checks = {
            "season_standings": quiz_safety.check_season_coverage_safety(
                c, "season_standings", "season", 2002),
            "cfb_standings": quiz_safety.check_season_coverage_safety(
                c, "cfb_standings", "season", 2002, where_extra="classification='fbs'"),
        }
    finally:
        c.close()
    return {"coverage_ok": all(v["coverage_ok"] for v in checks.values()), "checks": checks}


# --- NFL/CFB production data refresh (admin-triggered, background) --------
# See gateway/services/admin_refresh.py's module docstring for why this
# runs as a BackgroundTask rather than synchronously: a real refresh
# (download + ~1.6GB DB backup + stage/publish + sanity check) can take
# minutes, well past what the Netlify Scheduled Function that triggers this
# in production budgets for a single HTTP call. The route returns as soon
# as the run is scheduled (or immediately reports ALREADY_RUNNING); the
# real result is read back via /v1/admin/refresh/status.

def _refresh_import_guard(fn, *args):
    """tools.data_refresh imports Engine scripts from a volume mounted only
    in production (see admin_refresh.py's module docstring on the real
    crash-loop this caused when that import was eager) -- routes call
    through this so a missing file on a given deployment's volume degrades
    this ONE feature to a clean 503, never a raw 500 (and never anything
    that could take the route, let alone the app, down)."""
    try:
        return fn(*args)
    except ImportError as e:
        raise GatewayError("SERVICE_UNAVAILABLE", f"Data refresh is unavailable on this deployment: {e}")


# One parameterized route rather than four near-identical copies -- dataset_key
# is validated against admin_refresh's own known set (nfl/cfb rosters,
# nfl_games/cfb_games) so an unrecognized segment 400s cleanly instead of
# reaching _runners() at all. /v1/admin/refresh/nfl and /v1/admin/refresh/cfb
# (rosters) keep responding exactly as before -- the already-deployed Netlify
# scheduled function calls those two paths unchanged.
_REFRESH_DATASET_KEYS = {"nfl", "cfb", "nfl_games", "cfb_games", "nfl_draft", "nfl_player_stats", "nfl_player_game_stats", "nfl_team_game_stats", "cfb_player_stats",
                          "nfl_contracts", "nfl_injuries", "nfl_pbp", "nfl_passer_rating", "cfb_all_america",
                          "cfb_betting_lines", "cfb_games_postseason", "cfb_pbp", "cfb_rankings", "cfb_standings",
                          "cfb_weather"}


@app.post("/v1/admin/refresh/{dataset_key}")
def admin_refresh_trigger(dataset_key: str, request: Request, background_tasks: BackgroundTasks,
                           _admin=Depends(require_admin)):
    if dataset_key not in _REFRESH_DATASET_KEYS:
        raise GatewayError("INVALID_REQUEST", f"dataset_key must be one of {sorted(_REFRESH_DATASET_KEYS)}.")
    check = _refresh_import_guard(admin_refresh.check_can_start, dataset_key)
    if check["status"] == "ALREADY_RUNNING":
        return check
    background_tasks.add_task(_refresh_import_guard(admin_refresh.run_fn_for, dataset_key))
    return {"status": "STARTED", "league": check["league"], "dataset": check["dataset"]}


@app.get("/v1/admin/refresh/status")
def admin_refresh_status_route(request: Request, _admin=Depends(require_admin)):
    return _refresh_import_guard(admin_refresh.refresh_status)


# --- Reliability-design Phase 2: async Creator jobs -------------------------
# Same lazy-import-guard reasoning as _refresh_import_guard above (creator_jobs
# -> health_probe -> registry imports EVERY adapter module in one combined
# statement -- one missing dependency on a given deployment must degrade
# this ONE feature to a clean 503, never crash-loop the whole app).

def _creator_jobs_import_guard(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ImportError as e:
        raise GatewayError("SERVICE_UNAVAILABLE", f"Creator jobs are unavailable on this deployment: {e}")


@app.post("/v1/admin/creator-jobs/tier2-certification")
def creator_job_create_tier2_certification(
    body: CreatorJobTier2CertificationRequest, request: Request,
    background_tasks: BackgroundTasks, _admin=Depends(require_admin), _rl=Depends(rate_limit_creator_job_create),
):
    from tools.director_v02 import creator_jobs
    from tools.quiz_export import engine as engine_bootstrap

    def _create_and_start():
        c = engine_bootstrap.connect()
        try:
            if creator_jobs.any_job_running(c):
                return None
            job_id = creator_jobs.create_job(
                c, job_type="TIER2_CERTIFICATION_SWEEP",
                capability_ids=body.capability_ids, created_by="admin",
            )
            return job_id
        finally:
            c.close()

    job_id = _creator_jobs_import_guard(_create_and_start)
    if job_id is None:
        return {"status": "ALREADY_RUNNING"}
    background_tasks.add_task(_creator_jobs_import_guard, creator_jobs.run_job, job_id)
    return {"status": "STARTED", "job_id": job_id, "requested_count": len(body.capability_ids)}


@app.get("/v1/admin/creator-jobs/{job_id}")
def creator_job_status_route(job_id: str, request: Request,
                              _admin=Depends(require_admin), _rl=Depends(rate_limit_creator_job_status)):
    from tools.director_v02 import creator_jobs
    from tools.quiz_export import engine as engine_bootstrap

    def _get():
        c = engine_bootstrap.connect()
        try:
            status = creator_jobs.get_job_status(c, job_id)
            if status is None:
                raise GatewayError("INVALID_REQUEST", f"No such job {job_id!r}.")
            return status
        finally:
            c.close()

    return _creator_jobs_import_guard(_get)


@app.post("/v1/admin/creator-jobs/{job_id}/cancel")
def creator_job_cancel_route(job_id: str, request: Request,
                              _admin=Depends(require_admin), _rl=Depends(rate_limit_creator_job_status)):
    from tools.director_v02 import creator_jobs
    from tools.quiz_export import engine as engine_bootstrap

    def _cancel():
        c = engine_bootstrap.connect()
        try:
            return creator_jobs.cancel_job(c, job_id)
        finally:
            c.close()

    return _creator_jobs_import_guard(_cancel)


@app.post("/v1/admin/creator-jobs/{job_id}/retry")
def creator_job_retry_route(job_id: str, request: Request, background_tasks: BackgroundTasks,
                             _admin=Depends(require_admin), _rl=Depends(rate_limit_creator_job_create)):
    from tools.director_v02 import creator_jobs
    from tools.quiz_export import engine as engine_bootstrap

    def _retry():
        c = engine_bootstrap.connect()
        try:
            return creator_jobs.retry_failed_items(c, job_id)
        finally:
            c.close()

    result = _creator_jobs_import_guard(_retry)
    if result.get("ok"):
        background_tasks.add_task(_creator_jobs_import_guard, creator_jobs.run_job, job_id)
    return result


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


# --- Game Creator (v1.8, Part B/C/G/H) ---------------------------------------
# Admin-only like every other Engine-DB-touching/generation route in this
# Gateway -- require_admin on every route below, no exception. The Creator
# is NOT a new trust boundary: request_text is capped and forbid-extra at
# the Pydantic layer (models.py), then flows through the exact same
# translator -> validator pipeline every other caller already uses (Part
# L/M -- see gateway/services/creator.py's own module docstring).

@app.post("/v1/creator/feasibility")
def creator_feasibility(body: CreatorFeasibilityRequest, request: Request,
                         _rl=Depends(rate_limit_preview), _admin=Depends(require_admin)):
    return creator_service.assess_feasibility(body.request_text)


@app.post("/v1/creator/ideas")
def creator_ideas(body: CreatorIdeasRequest, request: Request,
                   _rl=Depends(rate_limit_preview), _admin=Depends(require_admin)):
    """Phase 5, Creator Intelligence -- tightly scoped: plain-language
    request -> distinct ranked ideas -> honest feasibility -> no
    duplicates. Reuses the same rate limiter as /v1/creator/feasibility
    (same cost profile -- fast, synchronous, no Engine DB candidate
    generation). Playable preview for any returned idea is the EXISTING,
    unchanged POST /v1/games/generate (spec={mechanic, domain,
    relationship_predicate, ...}) + GET /v1/games/{package_id} + POST
    /v1/creator/review flow -- no new generation code."""
    from tools.director_v02 import creator_intelligence

    ideas = creator_intelligence.generate_ideas(body.request_text, max_ideas=body.max_ideas)
    return {"ideas": ideas}


@app.post("/v1/creator/concepts")
def creator_concepts(body: CreatorConceptsRequest, request: Request,
                      _rl=Depends(rate_limit_generate), _admin=Depends(require_admin)):
    """Phase 5 correction -- real, packaged CONCEPTS (mechanic + round
    structure + scoring + hints + candidate-pool requirements + honest
    feasibility), not bare registry rows. Builds on /v1/creator/ideas'
    retrieval (creator_intelligence.generate_ideas(), unchanged) via
    tools/director_v02/concepts.py. Rate-limited like /v1/creator/generate
    (not /v1/creator/feasibility's cheaper limiter) since request_type=
    PLAYABLE_IDEAS/MIXED triggers real generation calls for each playable
    result, the same real cost as any other generation request."""
    from tools.director_v02 import concepts

    return concepts.generate_concepts(
        body.request_text, request_type=body.request_type, requested_count=body.requested_count,
        exclude_concept_ids=body.exclude_concept_ids,
    )


# --- Phase 6: real, private, playable mechanic rounds -----------------------
# Admin-gated like every other Engine-DB-touching/generation route (Part F's
# private-staging scope is unchanged by this phase -- these are PRIVATE
# preview rounds, never wired into the unauthenticated /v1/public/* surface;
# public rollout of any of these mechanics is a separate, later decision,
# same boundary Part 3/33 already established for /v1/public/game's own
# certified-mode allowlist). Round state (packages.py for the immutable
# round definition, game_state.py for mutable progress) is the SAME
# infrastructure Coach Connections v2 and every guess-mechanic package
# already use -- no new storage layer.

def _mechanic_round_not_found() -> "GatewayError":
    return GatewayError("PACKAGE_NOT_FOUND", "No such round -- it may have expired or never existed.")


@app.post("/v1/creator/mechanics/round")
def mechanics_start_round(body: MechanicRoundRequest, request: Request,
                           _rl=Depends(rate_limit_generate), _admin=Depends(require_admin)):
    """Generates one real private round/contest for the given taxonomy_id
    and returns only the client-safe view (never the private answer data --
    see mechanic_engine.client_safe_view()'s per-mechanic allow-list)."""
    from tools.director_v02 import mechanic_engine

    t = body.taxonomy_id
    if t in ("MULTIPLE_CHOICE_SINGLE_FACT", "POSITION_LINEUP_GRID"):
        domain, predicate = body.domain, body.relationship_predicate
        if t == "POSITION_LINEUP_GRID" and body.variant:
            cfg = mechanic_engine.VARIANTS["POSITION_LINEUP_GRID"].get(body.variant)
            if cfg is None:
                raise GatewayError("INVALID_REQUEST", f"Unknown POSITION_LINEUP_GRID variant {body.variant!r}.")
            domain, predicate = cfg["domain"], cfg["relationship_predicate"]
        if not domain or not predicate:
            raise GatewayError("INVALID_REQUEST", "domain and relationship_predicate (or a POSITION_LINEUP_GRID variant) are required.")
        package = mechanic_engine.generate_guess_round(
            domain=domain, relationship_predicate=predicate,
            question_count=body.question_count or 5, seed=body.seed)
    elif t == "PROGRESSIVE_CLUE_IDENTIFY":
        package = mechanic_engine.generate_clue_round(target_count=body.round_count or 5, seed=body.seed or "mechanics-round")
    elif t == "MATCHING":
        if body.variant not in mechanic_engine.VARIANTS["MATCHING"]:
            raise GatewayError("INVALID_REQUEST", f"variant must be one of {sorted(mechanic_engine.VARIANTS['MATCHING'])}.")
        package = mechanic_engine.generate_matching_round(
            variant=body.variant, round_count=body.round_count or 5, pair_count=body.pair_count or 4,
            seed=body.seed or "mechanics-round")
    elif t == "SORTING_TIMELINE":
        if body.variant not in mechanic_engine.VARIANTS["SORTING_TIMELINE"]:
            raise GatewayError("INVALID_REQUEST", f"variant must be one of {sorted(mechanic_engine.VARIANTS['SORTING_TIMELINE'])}.")
        package = mechanic_engine.generate_sorting_round(
            variant=body.variant, round_count=body.round_count or 5, item_count=body.item_count or 4,
            seed=body.seed or "mechanics-round")
    elif t == "HIGHER_LOWER_STREAK":
        if body.variant not in mechanic_engine.VARIANTS["HIGHER_LOWER_STREAK"]:
            raise GatewayError("INVALID_REQUEST", f"variant must be one of {sorted(mechanic_engine.VARIANTS['HIGHER_LOWER_STREAK'])}.")
        package = mechanic_engine.generate_higher_lower_round(
            variant=body.variant, sequence_length=body.sequence_length or 12, seed=body.seed or "mechanics-round")
    elif t == "ELIMINATION_SURVIVAL":
        if body.variant not in mechanic_engine.VARIANTS["ELIMINATION_SURVIVAL"]:
            raise GatewayError("INVALID_REQUEST", f"variant must be one of {sorted(mechanic_engine.VARIANTS['ELIMINATION_SURVIVAL'])}.")
        package = mechanic_engine.generate_elimination_round(
            variant=body.variant, sequence_length=body.sequence_length or 12, seed=body.seed or "mechanics-round")
    elif t == "WEEKLY_PICKEM":
        if body.variant not in mechanic_engine.VARIANTS["WEEKLY_PICKEM"]:
            raise GatewayError("INVALID_REQUEST", f"variant must be one of {sorted(mechanic_engine.VARIANTS['WEEKLY_PICKEM'])}.")
        if body.season is None or body.week is None:
            raise GatewayError("INVALID_REQUEST", "WEEKLY_PICKEM requires both season and week.")
        package = mechanic_engine.generate_weekly_pickem_round(
            variant=body.variant, season=body.season, week=body.week, seed=body.seed or "mechanics-round")
    elif t == "LIVE_WEEKLY_FANTASY_DRAFT":
        if body.variant not in mechanic_engine.VARIANTS["LIVE_WEEKLY_FANTASY_DRAFT"]:
            raise GatewayError("INVALID_REQUEST", f"variant must be one of {sorted(mechanic_engine.VARIANTS['LIVE_WEEKLY_FANTASY_DRAFT'])}.")
        if body.season is None or body.week is None:
            raise GatewayError("INVALID_REQUEST", "LIVE_WEEKLY_FANTASY_DRAFT requires both season and week.")
        package = mechanic_engine.generate_fantasy_draft_round(
            variant=body.variant, season=body.season, week=body.week, seed=body.seed or "mechanics-round")
    else:
        raise GatewayError("INVALID_REQUEST", f"Unknown taxonomy_id {t!r}.")

    if package.get("qa_status") != "PASSED":
        raise GatewayError(
            "NO_ELIGIBLE_GAME",
            package.get("shortfall_reason") or f"No qualifying {t} round could be generated right now.",
        )

    stored = packages.save_package(package)
    progress = mechanic_engine.initial_progress(t)
    progress["taxonomy_id"] = t
    game_state.create_state(stored["package_id"], progress)

    view = mechanic_engine.client_safe_view(t, stored, progress)
    return {"round_id": stored["package_id"], "taxonomy_id": t, "view": view}


@app.get("/v1/creator/mechanics/round/{round_id}")
def mechanics_get_round(round_id: str, request: Request, _admin=Depends(require_admin)):
    from tools.director_v02 import mechanic_engine

    try:
        stored = packages.load_package(round_id)
        progress = game_state.load_state(round_id)
    except (packages.PackageIdInvalid, game_state.StateIdInvalid):
        raise _mechanic_round_not_found()
    if stored is None or progress is None:
        raise _mechanic_round_not_found()

    view = mechanic_engine.client_safe_view(progress["taxonomy_id"], stored, progress)
    return {"round_id": round_id, "taxonomy_id": progress["taxonomy_id"], "view": view}


@app.post("/v1/creator/mechanics/round/{round_id}/submit")
def mechanics_submit_round(round_id: str, body: MechanicSubmitRequest, request: Request,
                            _rl=Depends(rate_limit_preview), _admin=Depends(require_admin)):
    from tools.director_v02 import mechanic_engine

    try:
        stored = packages.load_package(round_id)
        progress = game_state.load_state(round_id)
    except (packages.PackageIdInvalid, game_state.StateIdInvalid):
        raise _mechanic_round_not_found()
    if stored is None or progress is None:
        raise _mechanic_round_not_found()

    taxonomy_id = progress["taxonomy_id"]
    try:
        result, new_progress = mechanic_engine.evaluate_submission(taxonomy_id, stored, progress, body.submission)
    except mechanic_engine.MechanicError as e:
        raise GatewayError("INVALID_REQUEST", str(e))
    except (KeyError, IndexError, TypeError, AttributeError, ValueError):
        # Real bug found during the public-readiness punch-list's own
        # malformed-input verification (item 7): a MATCHING submission
        # shaped {"mapping": "not-a-dict"} crashed _matching_evaluate()'s
        # `mapping.items()` call with an uncaught AttributeError -- a real
        # 500, not a clean 400. TypeError/AttributeError/ValueError are
        # exactly the class of error a wrong-shaped submission (string
        # instead of dict/list, wrong nesting, etc.) raises across any
        # mechanic's evaluate function -- caught here as a single, systemic
        # safety net rather than defensively type-checking every mechanic's
        # own evaluate() body.
        raise GatewayError("INVALID_REQUEST", "This round has no more rounds/items to submit against, "
                            "or the submission was not shaped correctly for this mechanic.")

    new_progress["taxonomy_id"] = taxonomy_id
    game_state.save_state(round_id, new_progress)
    view = mechanic_engine.client_safe_view(taxonomy_id, stored, new_progress)
    return {"round_id": round_id, "taxonomy_id": taxonomy_id, "result": result, "view": view}


@app.post("/v1/creator/generate")
def creator_generate(body: CreatorGenerateRequest, request: Request,
                      _rl=Depends(rate_limit_generate), _admin=Depends(require_admin)):
    t0 = time.perf_counter()
    result = creator_service.generate_for_review(
        request_text=body.request_text, puzzle_count=body.puzzle_count,
        difficulty=body.difficulty, seed=body.seed,
    )
    latency_ms = (time.perf_counter() - t0) * 1000
    gateway_audit.record_generate(
        request_id=request.state.request_id,
        body=GenerateRequest(request_text=body.request_text, puzzle_count=body.puzzle_count,
                              difficulty=body.difficulty, seed=body.seed),
        result=result, latency_ms=latency_ms, endpoint="/v1/creator/generate",
    )
    return result


@app.get("/v1/creator/queue")
def creator_queue(request: Request,
                   review_status: Optional[str] = Query(default=None, max_length=20),
                   _rl=Depends(rate_limit_preview), _admin=Depends(require_admin)):
    if review_status is not None and review_status not in packages.REVIEW_STATUSES:
        raise GatewayError("INVALID_REQUEST", f"review_status must be one of {sorted(packages.REVIEW_STATUSES)}.")
    return {"packages": creator_service.list_review_queue(review_status)}


@app.post("/v1/creator/review")
def creator_review(body: CreatorReviewRequest, request: Request,
                    _rl=Depends(rate_limit_preview), _admin=Depends(require_admin)):
    return creator_service.set_review_status(body.package_id, body.review_status)


@app.get("/v1/creator/capabilities")
def creator_capabilities(request: Request, _rl=Depends(rate_limit_preview), _admin=Depends(require_admin)):
    """What's already possible, for the Creator's own reference view --
    every registered capability's real support status (Part C)."""
    from tools.director_v02 import feasibility as feasibility_mod
    return {"capabilities": feasibility_mod.list_capability_support_summary()}


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


# --- Public gameplay (v1.2 pilot) --------------------------------------
# NO require_admin on any route in this section -- that is the entire
# point (Part 3/6: the browser never receives, and never needs, the admin
# token). Safety instead comes from: a hard mode allow-list
# (gateway/services/public_game.py), its own separate rate limiters (Part
# 17, above), strict Pydantic request validation (extra="forbid" on
# PublicAnswerRequest), and the same never-leak-internals error contract
# every other route already uses (gateway_error_handler, unchanged).
# CORS (gateway/config.py's DEFAULT_CORS_ORIGINS) is what actually decides
# which real browser origins can read these responses.

@app.get("/v1/public/modes")
def public_modes():
    # v1.7, Part C8: one unified discovery response -- Six Degrees composed
    # in here alongside the Director-pipeline guess modes, not a second
    # catalog endpoint a client would need to know to call separately.
    # Coach Connections v2 (public_coach_connections.py) REPLACES the old
    # six_degrees_guess entry in this list -- same product slot ("Coach
    # Connections"), real graph-driven generation instead of a 23-puzzle
    # cache. The old routes/module stay mounted below (harmless, unused by
    # a client that only ever discovers modes through this endpoint) rather
    # than deleted outright, so nothing breaks for an in-flight old-frontend
    # session during the deploy window.
    return {"modes": public_game.list_public_modes() + [public_coach_connections.list_coach_connections_capability()]}


@app.get("/v1/public/game")
def public_game_route(request: Request,
                       mode: str = Query(..., min_length=1, max_length=64),
                       difficulty: Optional[str] = Query(default=None),
                       seed: Optional[str] = Query(default=None, min_length=1, max_length=config.MAX_SEED_LENGTH),
                       exclude: Optional[str] = Query(default=None, max_length=2000),
                       _rl=Depends(rate_limit_public_game)):
    if difficulty is not None and difficulty not in config.ALLOWED_DIFFICULTIES:
        raise GatewayError("INVALID_REQUEST", f"difficulty must be one of {sorted(config.ALLOWED_DIFFICULTIES)}.")
    exclude_ids = [x for x in (exclude.split(",") if exclude else []) if x][:50]
    return public_game.get_public_game(mode=mode, difficulty=difficulty, seed=seed, exclude_game_ids=exclude_ids)


@app.get("/v1/public/six_degrees/game")
def public_six_degrees_game_route(request: Request,
                                   seed: Optional[str] = Query(default=None, min_length=1, max_length=config.MAX_SEED_LENGTH),
                                   _rl=Depends(rate_limit_public_six_degrees_game)):
    return public_six_degrees.get_public_six_degrees(seed=seed)


@app.post("/v1/public/six_degrees/answer")
def public_six_degrees_answer_route(body: PublicSixDegreesAnswerRequest, request: Request,
                                     _rl=Depends(rate_limit_public_six_degrees_answer)):
    return public_six_degrees.submit_public_six_degrees_answer(
        game_id=body.game_id, step_index=body.step_index, choice_index=body.choice_index)


@app.post("/v1/public/six_degrees/reveal")
def public_six_degrees_reveal_route(body: PublicSixDegreesRevealRequest, request: Request,
                                     _rl=Depends(rate_limit_public_six_degrees_answer)):
    return public_six_degrees.reveal_public_six_degrees(game_id=body.game_id)


# --- Coach Connections v2 (graph-driven rebuild) ----------------------------
# Progressive-reveal, free-text-move, multi-path contract -- see
# gateway/services/public_coach_connections.py's module docstring for how
# this differs from the six_degrees routes above. Same trust boundary:
# server remains fully authoritative (gateway/services/game_state.py holds
# real per-game progress, never trusted from the client), same
# never-leak-internals error contract (gateway_error_handler, unchanged).

@app.get("/v1/public/coach_connections/game")
def public_coach_connections_game_route(request: Request,
                                         seed: Optional[str] = Query(default=None, min_length=1, max_length=config.MAX_SEED_LENGTH),
                                         exclude: Optional[str] = Query(default=None, max_length=2000),
                                         _rl=Depends(rate_limit_coach_connections_game)):
    exclude_ids = [x for x in (exclude.split(",") if exclude else []) if x][:50]
    return public_coach_connections.get_coach_connections_game(seed=seed, exclude_game_ids=exclude_ids)


@app.post("/v1/public/coach_connections/move")
def public_coach_connections_move_route(body: PublicCoachConnectionsMoveRequest, request: Request,
                                         _rl=Depends(rate_limit_coach_connections_move)):
    return public_coach_connections.submit_move(game_id=body.game_id, node_type=body.node_type, node_id=body.node_id)


@app.post("/v1/public/coach_connections/reveal")
def public_coach_connections_reveal_route(body: PublicCoachConnectionsRevealRequest, request: Request,
                                           _rl=Depends(rate_limit_coach_connections_move)):
    return public_coach_connections.reveal(game_id=body.game_id)


@app.get("/v1/public/coach_connections/search")
def public_coach_connections_search_route(request: Request,
                                           q: str = Query(..., min_length=2, max_length=64),
                                           node_type: Optional[str] = Query(default=None, min_length=1, max_length=32),
                                           _rl=Depends(rate_limit_coach_connections_search)):
    if node_type is not None and node_type not in public_coach_connections.ccg.PUBLIC_NODE_TYPES:
        raise GatewayError("INVALID_REQUEST",
                            f"node_type must be one of {sorted(public_coach_connections.ccg.PUBLIC_NODE_TYPES)}.")
    return {"results": public_coach_connections.search_nodes(query=q, node_type=node_type)}


@app.post("/v1/public/game/answer")
def public_game_answer(body: PublicAnswerRequest, request: Request,
                        _rl=Depends(rate_limit_public_answer)):
    return public_game.validate_public_answer(game_id=body.game_id, answer=body.answer)


# --- Public mechanics (punch-list closure pass) ------------------------------
# NO require_admin on any route here -- same reasoning as the public_game
# section above (Part 3/6): a real anonymous browser session never receives
# the admin token. See gateway/services/public_mechanics.py's own module
# docstring for the full "why these four, why this is safe" reasoning.

def rate_limit_public_mechanic_round(request: Request) -> None:
    _rate_limit(public_mechanic_round_limiter, request)


def rate_limit_public_mechanic_submit(request: Request) -> None:
    _rate_limit(public_mechanic_submit_limiter, request)


@app.get("/v1/public/mechanics/modes")
def public_mechanic_modes():
    return {"modes": public_mechanics.list_public_mechanic_modes()}


@app.get("/v1/public/mechanics/round")
def public_mechanics_start_round(request: Request,
                                  mode: str = Query(..., min_length=1, max_length=64),
                                  _rl=Depends(rate_limit_public_mechanic_round)):
    return public_mechanics.start_public_round(mode=mode)


@app.get("/v1/public/mechanics/round/{round_id}")
def public_mechanics_get_round(round_id: str, request: Request):
    return public_mechanics.get_public_round(round_id=round_id)


@app.post("/v1/public/mechanics/round/{round_id}/submit")
def public_mechanics_submit_round(round_id: str, body: PublicMechanicSubmitRequest, request: Request,
                                   _rl=Depends(rate_limit_public_mechanic_submit)):
    return public_mechanics.submit_public_round(round_id=round_id, submission=body.submission)


# --- Public Weekly Pick'em (Dynamic Weekly Pick'em pass) --------------------
# NO require_admin on any route here -- see gateway/services/public_pickem.py's
# own module docstring for why this is the real per-user session/room
# infrastructure the punch-list pass above deliberately deferred.

def rate_limit_public_pickem_view(request: Request) -> None:
    _rate_limit(public_pickem_view_limiter, request)


def rate_limit_public_pickem_submit(request: Request) -> None:
    _rate_limit(public_pickem_submit_limiter, request)


@app.get("/v1/public/pickem/{league}")
def public_pickem_current(league: str, request: Request,
                           client_id: Optional[str] = Query(default=None, min_length=6, max_length=64),
                           slate: Optional[str] = Query(default=None, min_length=1, max_length=24),
                           conference: Optional[str] = Query(default=None, min_length=1, max_length=40),
                           _rl=Depends(rate_limit_public_pickem_view)):
    return public_pickem.get_pickem_view(league=league, season=None, week=None, client_id=client_id,
                                          slate=slate, conference=conference)


@app.get("/v1/public/pickem/{league}/{season}/{week}")
def public_pickem_specific(league: str, season: int, week: str, request: Request,
                            client_id: Optional[str] = Query(default=None, min_length=6, max_length=64),
                            slate: Optional[str] = Query(default=None, min_length=1, max_length=24),
                            conference: Optional[str] = Query(default=None, min_length=1, max_length=40),
                            _rl=Depends(rate_limit_public_pickem_view)):
    return public_pickem.get_pickem_view(league=league, season=season, week=week, client_id=client_id,
                                          slate=slate, conference=conference)


@app.post("/v1/public/pickem/{league}/{season}/{week}/pick")
def public_pickem_pick(league: str, season: int, week: str, body: PublicPickemSubmitRequest, request: Request,
                        _rl=Depends(rate_limit_public_pickem_submit)):
    return public_pickem.submit_pick(league=league, season=season, week=week, client_id=body.client_id,
                                      game_id=body.game_id, predicted_winner=body.predicted_winner)


@app.post("/v1/admin/pickem/game-status")
def admin_pickem_game_status(body: AdminPickemGameStatusRequest, request: Request, _admin=Depends(require_admin)):
    return admin_pickem.set_game_status(league=body.league, game_id=body.game_id, status=body.status, reason=body.reason)
