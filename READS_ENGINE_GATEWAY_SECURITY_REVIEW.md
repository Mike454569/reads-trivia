# Reads Engine Gateway -- Security Reality Check (Director v0.6, Part S)

Explicit classification per deployment stage, per this milestone's
instruction not to call anything production-ready merely because tests
pass. All 25 automated tests (`gateway/tests/`) and every manual scenario
in `READS_ENGINE_GATEWAY_V01_REPORT.md` passing proves the Gateway behaves
correctly under the conditions tested -- it does not by itself prove any
of the three classifications below.

## Local development -- SAFE

What's actually true today:
- Bound to `127.0.0.1` only (never `0.0.0.0`) -- confirmed by how it's run
  (`uvicorn gateway.app:app --host 127.0.0.1`); nothing outside the machine
  can reach it regardless of any other setting.
- Admin token required for every route that costs compute or returns
  generated content (`/v1/games/preview`, `/v1/games/generate`,
  `/v1/games/{package_id}`); fails closed (missing-token-on-server ==
  unauthorized, not open) -- verified by `test_generate_missing_token_unauthorized`
  and `test_generate_invalid_token_unauthorized`.
- Constant-time token comparison (`hmac.compare_digest`) -- a timing side
  channel against a token no attacker on the same machine needs to time-attack
  anyway, but cheap and correct to do regardless.
- Strict input validation at two independent layers (Pydantic at the HTTP
  boundary, `tools.director_v02.validator` underneath) -- verified against
  real injection-shaped payloads (SQL-looking strings, path traversal,
  extra/forbidden fields) in both the automated suite and manual testing.
- Single-generation-job concurrency guard, verified under real concurrent
  load (`test_concurrent_generation_protected`: 4 simultaneous requests ->
  exactly 1 succeeds, 3 get a clean `429 GENERATION_BUSY`).
- No stack trace or raw exception text ever reaches an HTTP response
  (verified by `test_internal_exception_never_leaks_traceback` against a
  real injected failure).
- CORS restricted to an explicit local-origin allowlist, never `*`.

**Verdict: safe for local development as-is.** This is the only stage this
milestone actually targets.

## Private / admin staging -- NOT YET SAFE

What would need to change before even a small, trusted, non-public staging
deployment (e.g. a VPN-only host, or a cloud host with an IP allowlist and
still no public DNS):

- **Token rotation / distribution has no story.** `READS_ENGINE_ADMIN_TOKEN`
  is a single shared secret read from one environment variable. There is no
  mechanism to issue, rotate, revoke, or scope tokens per-user. Fine for
  "one developer, one local process"; not fine the moment a second person
  or automated system needs access.
- **No rate limiting beyond the single-generation-job guard.** That guard
  protects the Engine SQLite file from concurrent generation, but nothing
  stops a caller with a valid token from hammering `/v1/games/preview`
  (cheap, but not free) or repeatedly polling `/v1/games/generate` the
  instant the lock frees up.
- **No HTTPS/TLS.** Even on a private network, the admin token currently
  travels as plaintext in the `Authorization` header over whatever
  transport is in front of it -- acceptable on `127.0.0.1` (loopback,
  never leaves the machine), not acceptable the moment this listens on any
  real network interface.
- **No process supervision.** `uvicorn ... &` (or equivalent) has no
  restart-on-crash, no health-check-triggered restart, no log rotation.
  A staging environment needs at least systemd/supervisord-level babysitting.
- **No structured logging destination.** `gateway/storage/gateway_audit_log.jsonl`
  and `tools/director_v02/logs/audit_log.jsonl` are local files with no
  rotation, shipping, or alerting -- fine for a local dev loop, not for
  anything another person needs to monitor.
- **SQLite persistence strategy is unexamined under real concurrent staging
  load.** The single-generation-lock protects the Gateway's own generation
  calls from colliding with each other, but the audit in
  `READS_ENGINE_GATEWAY_AUDIT.md` found seven other legacy servers that can
  independently open connections to the exact same SQLite file with zero
  coordination with the Gateway. A staging environment where those might
  also be running needs an actual answer for this, not just "the Gateway
  behaves itself."

**Verdict: not yet safe for private/admin staging.** Closest gap to closing
is TLS + a supervised process; token scoping and rate limiting are real
but smaller follow-on work.

## Public internet exposure -- NOT SAFE, NOT CLOSE

Everything in the staging list above, plus:

- **No real authentication.** A single bearer token is categorically not
  suitable for a public-facing admin surface -- no user identity, no
  audit-by-person, no revocation without rotating the one shared secret
  for everyone.
- **No reverse proxy / WAF / host firewall.** Nothing between the internet
  and a Python process holding a live connection to the Engine database.
- **No abuse protection.** No IP-based rate limiting, no CAPTCHA-equivalent,
  no anomaly detection -- the concurrency guard prevents two generations
  from *overlapping*, it does not prevent a very large number of
  *sequential* generation requests from a single hostile actor draining
  compute one at a time (each one waits for `GENERATION_BUSY` to clear,
  then runs).
- **No resource isolation.** The Gateway process, the Engine SQLite file,
  and (if colocated) any of the seven legacy servers all share the same
  filesystem, memory, and CPU with no containerization or cgroup limits in
  this milestone's implementation.
- **No secrets management.** `READS_ENGINE_ADMIN_TOKEN` is a plain
  environment variable -- adequate for one developer's shell, not for a
  real deployment (needs a real secrets manager: environment injection from
  a vault, not a value someone has to remember to set correctly on a host).
- **No backup strategy for either the 1.65GB Engine SQLite file or the
  Gateway's own generated-package storage.**
- **CORS is currently a local-dev allowlist** (`localhost`/`127.0.0.1`
  only) -- correctly rejects the eventual production origin
  (`https://reads.football`) by design; that origin is documented, not
  enabled (see `READS_ENGINE_HOSTING_READINESS.md`), and enabling it is
  itself a real, deliberate step this milestone does not take.
- **This milestone's own restrictions explicitly forbid taking this step**
  ("Do NOT deploy publicly," "Do NOT expose a public port") -- this
  section exists to make the gap concrete and legible for a future
  milestone, not because anything here was close to ready.

**Verdict: not safe for public internet exposure, and no part of this
milestone's implementation should be read as a step toward skipping the
above.**
