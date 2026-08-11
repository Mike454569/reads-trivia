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
# Local development origins -- used when READS_ENGINE_ALLOWED_ORIGINS is
# unset. NOT a wildcard, never inferred from the request itself.
DEV_CORS_ORIGINS = [
    "http://localhost:8934",
    "http://127.0.0.1:8934",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
# v0.7-v1.1 left this documented-but-not-enabled (the comment here used to
# cite READS_ENGINE_HOSTING_READINESS.md for the reasoning -- re-checked
# this phase and that file doesn't actually contain CORS-specific reasoning,
# just disk/memory sizing; noted honestly rather than left mis-cited).
# v1.2 explicitly authorizes connecting the real Reads frontend to the
# Gateway (this phase's stated objective), so the production origin is now
# enabled BY DEFAULT for the NEW public gameplay routes specifically --
# admin routes remain unaffected in practice since they're still gated by
# the bearer token regardless of which origin the request comes from; CORS
# only controls which origins can read the response, not who can guess the
# right token. Still not a wildcard, still env-overridable.
PRODUCTION_READS_ORIGIN = "https://reads.football"
DEFAULT_CORS_ORIGINS = DEV_CORS_ORIGINS + [PRODUCTION_READS_ORIGIN]


def allowed_origins() -> list[str]:
    """Comma-separated list from READS_ENGINE_ALLOWED_ORIGINS, falling back
    to DEFAULT_CORS_ORIGINS (dev origins + the real production Reads origin,
    as of v1.2) when unset -- never a wildcard, never inferred from the
    request itself (Part J: 'do not automatically trust arbitrary origins').
    Validated at startup (see app.py's startup check) -- an entry that isn't
    a well-formed http(s) origin is rejected loudly rather than silently
    allowed through."""
    raw = os.environ.get(ALLOWED_ORIGINS_ENV_VAR)
    if not raw:
        return list(DEFAULT_CORS_ORIGINS)
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

# --- Public gameplay (v1.2, Part 17) --------------------------------------
# Deliberately much more generous than every admin limiter above -- this is
# real end-user gameplay traffic, not internal/QA tooling. /v1/public/game
# calls generation.generate() (the same single-slot-concurrency-guarded
# Director pipeline /v1/games/generate uses -- Part 9: no competing
# generator), so its limit is still meaningfully tighter than the answer
# limiter (a real player submits many more answers than fresh-game
# requests in a session). /v1/public/game/answer is a cheap package lookup
# + string comparison (no generation), so it can be looser.
PUBLIC_GAME_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_PUBLIC_GAME_RATE_LIMIT", "20"))
PUBLIC_GAME_RATE_LIMIT_WINDOW_SECONDS = 60.0
PUBLIC_ANSWER_RATE_LIMIT_MAX = int(os.environ.get("READS_ENGINE_PUBLIC_ANSWER_RATE_LIMIT", "60"))
PUBLIC_ANSWER_RATE_LIMIT_WINDOW_SECONDS = 60.0

# Draft-guessing (v1.2) and championship-guessing (v1.3) are public-safe as
# of v1.3 (Part 3/33: explicit, hand-certified mode allow-list, never "every
# registered Director capability is now public" -- adding a mode here is a
# deliberate certification decision made in gateway/services/public_game.py,
# not an automatic consequence of the internal capability registry growing).
# Keyed by the public-facing mode id (NOT the internal (mechanic, domain,
# predicate) tuple) so the public contract's vocabulary stays independent
# of internal registry naming.
PUBLIC_MODE_ALLOWLIST = frozenset({"draft_guess", "championship_guess"})

# --- Production rollout controls (v1.4, Parts 10/11) -----------------------
# TWO independent control layers, deliberately not one:
#   1. This module's PUBLIC_GAME_ENABLED -- can the Gateway serve ANY public
#      gameplay at all? A real operator emergency switch: flip one env var
#      and every /v1/public/game* route returns a clean, structured
#      SERVICE_UNAVAILABLE instead of a redeploy or code change. Defaults to
#      enabled (matches every environment this has ever tested in --
#      gateway/tests/test_public_game.py's 41 tests all call these routes
#      expecting them to work when unset) -- this is an OPERATOR kill
#      switch for an already-shipped feature, not a "ship it disabled by
#      default" gate. That gate is the frontend's own feature flags
#      (app.js's ENABLE_ENGINE_DRAFT_PILOT_V01 / _CHAMPIONSHIP_PILOT_V01,
#      both default OFF, Part 42) -- a real end user reaching this Gateway
#      at all already implies a frontend flag was deliberately turned on.
#   2. PUBLIC_MODES_ALLOWED (below) -- WHICH of the code-certified modes are
#      currently allowed, for staged per-mode rollout (e.g. launch Draft
#      days before Championship without touching code). This can only ever
#      NARROW PUBLIC_MODE_ALLOWLIST, never expand it -- public certification
#      (Part 33) remains a code-level decision, never an env var's to grant.
PUBLIC_GAME_ENABLED = os.environ.get("READS_PUBLIC_GAME_ENABLED", "true").strip().lower() not in ("false", "0", "no", "off")


def public_modes_allowed() -> frozenset[str]:
    """READS_PUBLIC_MODES unset -> every code-certified mode (today's
    behavior, unchanged). Set -> intersected with PUBLIC_MODE_ALLOWLIST, so
    e.g. READS_PUBLIC_MODES=draft_guess,not_a_real_mode is equivalent to
    just draft_guess -- an operator can only ever ROLL BACK to a subset of
    what's already code-certified, never grant a new mode through config
    alone."""
    raw = os.environ.get("READS_PUBLIC_MODES")
    if not raw:
        return PUBLIC_MODE_ALLOWLIST
    requested = {m.strip() for m in raw.split(",") if m.strip()}
    return frozenset(requested & PUBLIC_MODE_ALLOWLIST)
