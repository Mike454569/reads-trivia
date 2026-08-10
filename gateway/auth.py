"""Reads Engine Gateway -- admin authentication (Part F).

Minimal admin-token mechanism, exactly as the milestone specifies: a single
shared secret in `READS_ENGINE_ADMIN_TOKEN`, checked with a constant-time
comparison, never logged, never echoed back in any response (including
error responses -- see errors.py, which never includes request bodies or
headers in its `extra` payload).

This is NOT full user authentication. It is an interim, local-admin-only
gate on the two endpoints that cost real compute and produce persisted
output (`/v1/games/preview`, `/v1/games/generate`) and on package retrieval
(`/v1/games/{package_id}` -- generated-but-unreviewed content, kept behind
the same gate rather than left world-readable). `/v1/health` and
`/v1/capabilities` are deliberately left unauthenticated -- see the
reasoning in READS_ENGINE_GATEWAY_V01_REPORT.md, Part F: both are read-only,
free, and reveal nothing this project hasn't already published in its own
public milestone reports (the exact three registered capabilities are
already documented in GAME_DIRECTOR_V03_REPORT.md/GAME_DIRECTOR_V04_REPORT.md).
"""
import hmac
from typing import Optional

from fastapi import Header

from . import config
from .errors import GatewayError


def require_admin(authorization: Optional[str] = Header(default=None)) -> None:
    """FastAPI dependency. Raises GatewayError("UNAUTHORIZED", ...) for:
    - no token configured on the server at all (fail closed, not open)
    - missing/malformed Authorization header
    - a token that doesn't match, compared in constant time
    Never raises for any other reason, and never includes the provided or
    expected token value anywhere in the exception."""
    expected = config.admin_token()
    if not expected:
        raise GatewayError("UNAUTHORIZED", "Admin token is not configured on this server.")
    if not authorization or not authorization.startswith("Bearer "):
        raise GatewayError("UNAUTHORIZED", "Missing admin token. Send 'Authorization: Bearer <token>'.")
    provided = authorization[len("Bearer "):]
    if not hmac.compare_digest(provided, expected):
        raise GatewayError("UNAUTHORIZED", "Invalid admin token.")


def startup_token_check() -> Optional[str]:
    """Director v0.7, Part F: 'minimum token-strength validation at
    startup' -- called once, from app.py's startup handler, NOT per-request
    (that would waste cycles re-checking a value that can't change without a
    restart). Returns a human-readable warning string if the configured
    token looks weak, or None if it's fine or genuinely unset (an unset
    token is v0.6's existing fail-closed behavior -- every admin route
    already refuses to work at all, which is a louder and safer signal than
    a startup warning would be, so this function does not treat "unset" as
    a weakness to warn about)."""
    token = config.admin_token()
    if not token:
        return None
    return config.admin_token_weak_reason(token)
