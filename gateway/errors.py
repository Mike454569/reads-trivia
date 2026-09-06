"""Reads Engine Gateway -- one consistent error shape (Part I).

Every error response, from every route, looks like:

    {"error": {"code": "...", "message": "...", "request_id": "..."}}

Never a raw stack trace, never a bare exception string (see
READS_ENGINE_GATEWAY_AUDIT.md's finding on production_api.py's
`{"error": str(e)}` pattern -- this module exists specifically so the new
Gateway cannot repeat that mistake). Technical detail is logged locally
(see services/audit.py) and never included in the HTTP response body.
"""
from __future__ import annotations

ERROR_CODES = frozenset({
    "INVALID_REQUEST",
    "UNAUTHORIZED",
    "NEEDS_CLARIFICATION",
    "UNDERSTOOD_BUT_UNSUPPORTED",
    "BLOCKED_INFEASIBLE",
    "GENERATION_BUSY",
    "GENERATION_FAILED",
    "PACKAGE_NOT_FOUND",
    "PACKAGE_INVALID",
    "NOT_FOUND",  # Director v0.7, Grid roster-merge port -- generic "well-formed id, no such
                  # resource" for routes with no more specific noun of their own (e.g.
                  # /v1/grid/player/{node_id}). PACKAGE_NOT_FOUND stays package-specific.
    "INTERNAL_ERROR",  # not in the milestone's explicit list, but required so a genuinely
                        # unexpected exception still gets a real code instead of falling
                        # back to something misleading like GENERATION_FAILED
    "RATE_LIMITED",  # Director v0.7, Part G -- distinct from GENERATION_BUSY (the single-
                      # generation-job concurrency guard): this is a per-caller request-
                      # frequency limit, checked before the concurrency guard is ever reached.
    "SERVICE_UNAVAILABLE",  # Director v0.7, Part L -- readiness failed (DB missing/unreadable,
                             # package directory unavailable) -- distinct from an ordinary 500.
    "INVALID_MODE",       # v1.2 public gameplay -- requested mode isn't a recognized string at all.
    "MODE_UNAVAILABLE",   # v1.2 -- a recognized mode, but not on the public allow-list (e.g. admin-only
                           # Director capabilities that were never vetted for direct public delivery).
    "NO_ELIGIBLE_GAME",   # v1.2 -- generation ran but produced no QA-passed question (distinct from a
                           # genuine infra failure -- GENERATION_FAILED already covers that).
    "INVALID_GAME_ID",    # v1.2 -- game_id doesn't resolve to a real, stored package (malformed or
                           # simply unknown -- never distinguished to the client, same reasoning
                           # packages.load_package's docstring already gives for PACKAGE_NOT_FOUND).
    "GAME_EXPIRED",       # v1.2 -- reserved for a future TTL on public game sessions; not enforced yet
                           # (packages are retained indefinitely, same as admin-generated ones), but the
                           # code exists now so a client's error-handling switch statement is future-proof.
    "SEQUENCE_COMPLETE",  # Public Mode Wiring pass -- a "sequential" mode (Franchise Marathon, Era
                           # Gauntlet) requesting stage_index N got a real, QA-passed generation result
                           # with fewer than N+1 real candidates -- the sequence has honestly run out of
                           # real content (e.g. a franchise's real title count), not a transient failure.
                           # Routed through this same 200-status "well-defined structured outcome" shape as
                           # NEEDS_CLARIFICATION/etc, not a 5xx -- a client should show "marathon complete!",
                           # never a retry button.
})

# HTTP status per code -- kept alongside the code itself so a raise site
# never has to remember (or get wrong) which status a given code implies.
STATUS_FOR_CODE = {
    "INVALID_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "NEEDS_CLARIFICATION": 200,  # a real, structured, non-error result -- see GatewayError docstring
    "UNDERSTOOD_BUT_UNSUPPORTED": 200,
    "BLOCKED_INFEASIBLE": 200,
    "GENERATION_BUSY": 429,
    "GENERATION_FAILED": 502,
    "PACKAGE_NOT_FOUND": 404,
    "PACKAGE_INVALID": 500,
    "NOT_FOUND": 404,
    "INTERNAL_ERROR": 500,
    "RATE_LIMITED": 429,
    "SERVICE_UNAVAILABLE": 503,
    "INVALID_MODE": 400,
    "MODE_UNAVAILABLE": 404,
    "NO_ELIGIBLE_GAME": 503,
    "INVALID_GAME_ID": 404,
    "GAME_EXPIRED": 410,
    "SEQUENCE_COMPLETE": 200,
}


class GatewayError(Exception):
    """The one exception type every route handler raises for a structured,
    documented failure. NEEDS_CLARIFICATION/UNDERSTOOD_BUT_UNSUPPORTED/
    BLOCKED_INFEASIBLE are technically not "errors" in the everyday sense
    (they're the Director's own well-defined structured outcomes, already
    proven safe across v0.2-v0.5) but are routed through this same shape for
    a single consistent contract -- callers branch on `code`, not on HTTP
    status, for these three specifically (status 200 is used for them so a
    generic HTTP client doesn't treat "the request was fine, the game
    concept just isn't supported yet" as a transport-level failure)."""

    def __init__(self, code: str, message: str, *, extra: dict | None = None):
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code {code!r}")
        self.code = code
        self.message = message
        self.status_code = STATUS_FOR_CODE[code]
        self.extra = extra or {}
        super().__init__(message)

    def body(self, request_id: str) -> dict:
        out = {"error": {"code": self.code, "message": self.message, "request_id": request_id}}
        if self.extra:
            out["error"].update(self.extra)
        return out
