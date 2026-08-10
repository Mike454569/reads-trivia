"""Reads Engine Gateway -- configuration.

Everything here is a constant or an environment-variable read -- no logic.
Centralizing these in one module (rather than scattering `os.environ.get`
calls across route handlers) is what lets READS_ENGINE_GATEWAY_SECURITY_REVIEW.md
make a single, auditable statement about exactly what's configurable and how.

Director v0.7 additions (Parts D, F, G, J, N, O): every new setting below
defaults to the exact same local-dev behavior v0.6 had when its env var is
unset -- staging-specific behavior only activates when a staging deployment
explicitly sets it. See .env.example for the full list with placeholders.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SERVICE_NAME = "reads-engine-gateway"
API_VERSION = "v1"

# --- Storage (Part D) ------------------------------------------------------
# Both overridable so a staging deployment can point them at a persistent
# volume mount -- see READS_ENGINE_STAGING_V01_REPORT.md's persistent-volume
# design. Gateway-generated packages remain SEPARATE from generated_games/
# (the hand-reviewed v0.1-v0.4 milestone deliverables) regardless of where
# this points -- see gateway/services/packages.py.
PACKAGES_DIR = Path(os.environ.get("READS_ENGINE_PACKAGES_DIR", str(REPO_ROOT / "gateway" / "storage" / "packages")))
GATEWAY_AUDIT_LOG_DIR = Path(os.environ.get("READS_ENGINE_LOG_DIR", str(REPO_ROOT / "gateway" / "storage")))
GATEWAY_AUDIT_LOG_PATH = GATEWAY_AUDIT_LOG_DIR / "gateway_audit_log.jsonl"
OPERATIONAL_LOG_PATH = GATEWAY_AUDIT_LOG_DIR / "gateway_operational_log.jsonl"  # Part M -- per-request log line

# --- Auth (Part F) -----------------------------------------------------
ADMIN_TOKEN_ENV_VAR = "READS_ENGINE_ADMIN_TOKEN"
MIN_ADMIN_TOKEN_LENGTH = 32  # ~192 bits if generated with a decent random source (e.g. `openssl rand -hex 32` -> 64 hex chars)


def admin_token() -> str | None:
    """Read fresh on every check (never cached at import time) so rotating
    the env var and restarting the process is the only way to change it --
    no code path holds a stale copy in memory longer than one request."""
    return os.environ.get(ADMIN_TOKEN_ENV_VAR)


def admin_token_weak_reason(token: str) -> str | None:
    """Part F: 'minimum token-strength validation at startup'. Deliberately
    simple heuristics (length + not-a-known-placeholder), not a full entropy
    estimator -- enough to catch the realistic mistake (forgetting to
    generate a real token and leaving a placeholder/short value in an env
    file) without pretending to be a real secret-strength auditor. Returns
    None if the token passes, else a human-readable reason."""
    if len(token) < MIN_ADMIN_TOKEN_LENGTH:
        return f"shorter than the minimum {MIN_ADMIN_TOKEN_LENGTH} characters"
    obvious_placeholders = {"changeme", "change-me", "your-token-here", "admin", "password", "secret", "test", "placeholder"}
    if token.lower() in obvious_placeholders:
        return "matches a known placeholder value"
    if len(set(token)) <= 3:
        return "too little character variety to be a real generated secret"
    return None


# --- CORS (Part J) -------------------------------------------------------
ALLOWED_ORIGINS_ENV_VAR = "READS_ENGINE_ALLOWED_ORIGINS"
# Local development origins only -- used when READS_ENGINE_ALLOWED_ORIGINS
# is unset, preserving v0.6's exact local-dev behavior. NOT a wildcard, and
# nothing resembling a production origin is enabled here -- see
# READS_ENGINE_HOSTING_READINESS.md for why https://reads.football is
# documented, not configured.
DEV_CORS_ORIGINS = [
    "http://localhost:8934",
    "http://127.0.0.1:8934",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
PRODUCTION_ORIGIN_DOCUMENTED_NOT_ENABLED = "https://reads.football"


def allowed_origins() -> list[str]:
    """Comma-separated list from READS_ENGINE_ALLOWED_ORIGINS, falling back
    to DEV_CORS_ORIGINS when unset -- never a wildcard, never inferred from
    the request itself (Part J: 'do not automatically trust arbitrary
    origins'). Validated at startup (see app.py's startup check) -- an
    entry that isn't a well-formed http(s) origin is rejected loudly rather
    than silently allowed through."""
    raw = os.environ.get(ALLOWED_ORIGINS_ENV_VAR)
    if not raw:
        return list(DEV_CORS_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


# --- Input bounds (Part H) ----------------------------------------------
MAX_REQUEST_TEXT_CHARS = 500  # matches director_v02.providers.base.MAX_REQUEST_TEXT_CHARS
MAX_BODY_BYTES = 32 * 1024  # 32KB -- generous for this API's small JSON payloads, small enough to block abuse
MAX_PUZZLE_COUNT = 100  # matches director_v02.schema.QUESTION_COUNT_MAX (the outer bound; each
                         # capability's own registry entry may be tighter, e.g. Player From Clues caps at 25)
MAX_SEED_LENGTH = 128  # matches gateway/models.py's existing Field(max_length=128)
ALLOWED_DIFFICULTIES = frozenset({"any", "easy", "medium", "hard"})
ALLOWED_PROVIDERS = frozenset({"mock", "anthropic"})

# --- Concurrency / timeouts (Part H, carried from v0.6) -------------------
GENERATION_TIMEOUT_SECONDS = 45  # observed worst case (Player From Clues, full 4,506-player universe
                                  # scan) is ~3.5s (see GAME_DIRECTOR_V04_REPORT.md) -- generous headroom,
                                  # not tuned to be barely-sufficient.

# --- Rate limiting (Part G) ------------------------------------------------
# Deliberately conservative and configurable -- see gateway/ratelimit.py for
# the in-process, single-instance-only implementation and why that's the
# right scope for admin-only staging. Generation is stricter than preview
# per the milestone's explicit instruction.
PREVIEW_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_PREVIEW_RATE_LIMIT", "30"))
PREVIEW_RATE_LIMIT_WINDOW_SECONDS = 60.0
GENERATE_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_GENERATE_RATE_LIMIT", "10"))
GENERATE_RATE_LIMIT_WINDOW_SECONDS = 60.0

# --- Graph / Six Degrees (v0.7 port of Reads_Football_Data_Engine_v4.0/
# graph_explorer.py into this Gateway) --------------------------------------
# search()/path() are read-only lookups against an already-open connection
# (cheap), so their limit sits with preview's; shortest_path can fall back to
# a real BFS over graph_edges (1.4M+ rows) on a cache miss, which is the one
# genuinely expensive case here -- kept on its own limiter, not lumped in
# with search/six-degrees, so a burst of cache-miss path queries can't also
# starve unrelated search traffic.
GRAPH_SEARCH_LIMIT_MAX = 50  # matches graph_explorer.search()'s own reasonable ceiling for a LIKE query
GRAPH_PATH_DEFAULT_MAX_DEPTH = 6  # matches graph_explorer.shortest_path()'s own default
GRAPH_PATH_MAX_DEPTH_LIMIT = 8  # hard ceiling -- BFS cost grows fast with depth on a 1.4M-edge graph
SIX_DEGREES_DEFAULT_MIN_LEN = 2  # matches graph_explorer.random_six()'s own default
SIX_DEGREES_DEFAULT_MAX_LEN = 4  # matches graph_explorer.random_six()'s own default
SIX_DEGREES_MAX_LEN_LIMIT = 6  # graph_path_cache only holds pre-computed short paths; no reason to allow more

GRAPH_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_GRAPH_RATE_LIMIT", "30"))
GRAPH_RATE_LIMIT_WINDOW_SECONDS = 60.0
GRAPH_PATH_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_GRAPH_PATH_RATE_LIMIT", "10"))
GRAPH_PATH_RATE_LIMIT_WINDOW_SECONDS = 60.0

# --- Grid roster/eligibility (v0.7 Grid roster-merge port, content-pipeline
# model -- gateway/services/grid.py) -------------------------------------
# Admin/QA-only (see that module's docstring): /v1/grid/criteria and
# /v1/grid/player/{id} are cheap indexed point lookups, grouped with
# search's limit; /v1/grid/board and /v1/grid/validate each run multiple
# _players_matching() calls (board: up to 6 criteria x a season filter;
# multi_team/one_team pulls all 28,617 PLAYED_FOR rows once per call), kept
# on their own stricter limiter for the same reason graph_path is split out.
GRID_LOOKUP_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_GRID_LOOKUP_RATE_LIMIT", "30"))
GRID_LOOKUP_RATE_LIMIT_WINDOW_SECONDS = 60.0
GRID_BOARD_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_GRID_BOARD_RATE_LIMIT", "15"))
GRID_BOARD_RATE_LIMIT_WINDOW_SECONDS = 60.0
