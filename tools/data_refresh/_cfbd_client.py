"""Shared CollegeFootballData.com (CFBD) live REST API client -- Engine-gap-
audit operation, continuation (CFBD-key-dependent domains: rankings,
standings/records, bowl/CFP game identification, betting lines, play-by-play).

Credential: environment variable `CFBD_API_KEY`, user-supplied. Never read
from a file, never hardcoded, never logged, never included in any package
output -- exact same discipline as `ANTHROPIC_API_KEY`
(tools/director_v02/providers/anthropic_provider.py). If unset, `get()`
raises `RuntimeError` immediately; every caller in this module family treats
that as a real, honest "this domain is unavailable" condition -- never a
crash, never a silent skip.

Real, confirmed-live constraint found before building: the `/games/weather`
endpoint requires a paid Patreon Tier 1+ subscription (confirmed via a real
401 with an explicit message, not assumed) -- CFB weather stays a real,
disclosed gap, not attempted here. Every other endpoint this module family
uses (games, rankings, records, lines, plays) was confirmed reachable on
the free tier before any importer was written.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API_BASE = "https://api.collegefootballdata.com"
CREDENTIAL_ENV_VAR = "CFBD_API_KEY"
_RETRYABLE_HTTP_STATUSES = frozenset({429, 500, 502, 503, 504})


class CfbdUnavailable(RuntimeError):
    """Raised when CFBD_API_KEY is unset -- callers treat this as an honest
    'this domain is unavailable right now' condition, never a crash."""


def get(path: str, params: dict, *, timeout: int = 30, max_attempts: int = 3) -> object:
    """One GET request against the CFBD API, JSON-decoded. Retries transient
    infrastructure failures (429/5xx/timeout) with a short backoff -- never
    retries a genuine 4xx content/auth error (e.g. the paid-tier-required
    401 on /games/weather), since retrying an identical request against an
    identical auth state can't fix that."""
    api_key = os.environ.get(CREDENTIAL_ENV_VAR)
    if not api_key:
        raise CfbdUnavailable(
            f"{CREDENTIAL_ENV_VAR} is not set -- CFBD-dependent domains are unavailable. "
            f"Set this environment variable to a valid CollegeFootballData.com API key to enable them."
        )
    from urllib.parse import urlencode

    url = f"{API_BASE}{path}?{urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Reads-Football-Data-Refresh/1.0",
        "Accept": "application/json",
    })
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code not in _RETRYABLE_HTTP_STATUSES or attempt == max_attempts:
                raise
            last_err = e
            time.sleep(2.0 * attempt)
        except Exception as e:
            if attempt == max_attempts:
                raise
            last_err = e
            time.sleep(2.0 * attempt)
    raise last_err  # pragma: no cover -- unreachable, loop always returns or raises
