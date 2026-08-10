# Reads Engine Gateway -- Staging Gap Analysis (Director v0.7, Part A)

Re-read in full: `READS_ENGINE_GATEWAY_AUDIT.md`, `READS_ENGINE_GATEWAY_SECURITY_REVIEW.md`,
`READS_ENGINE_HOSTING_READINESS.md`, `READS_ENGINE_GATEWAY_V01_REPORT.md`, the
complete `gateway/` implementation, `gateway/tests/`, `tools/director_v02/registry.py`,
`gateway/services/packages.py`, and how the Engine database is currently located
(`tools/quiz_export/engine.py`, `game_factory.py`).

## Environment finding that shapes this whole milestone

**Docker is not installed in this environment** (`docker`, `podman`, `colima`
all absent). Part C/R ask for a container definition and a container smoke
test. The Dockerfile/`.dockerignore` are written as real, correct artifacts
(reasoned through carefully, not guessed), but they could not be literally
`docker build`'d or `docker run`'d here. Part R's smoke test is instead run
as the closest honest equivalent: the Gateway started as a fresh subprocess
using only environment-variable-driven configuration (no code path that
would differ inside an actual container), against mounted-equivalent local
paths. This is disclosed as a real gap, not silently substituted -- see
`READS_ENGINE_STAGING_V01_REPORT.md`'s "remaining blockers" list, which
includes "literally build and run the Dockerfile in a real container
runtime" as an explicit unclosed item.

## Concrete pre-existing risk found during this audit

`game_factory.py`'s `DB = ROOT/'reads_football_v4.0.sqlite'` is a bare
`Path`, and `sqlite3.connect(DB)` **silently creates an empty file** if
nothing exists at that path (confirmed empirically this session, not
assumed). Today, locally, this is harmless because the file always exists.
In any staging environment where the persistent volume might not be
mounted correctly, this would fail *silently and confusingly* -- the
Gateway would start, report itself healthy, and only fail with cryptic "no
such table" errors on first real query, rather than refusing to start at
all. This directly motivates Part D/L's explicit "fail closed, verify
before serving" requirements below.

## Classification

| Requirement | Classification | Notes |
|---|---|---|
| Admin token auth | ALREADY_SATISFIED | v0.6, constant-time, fails closed |
| Structured error contract | ALREADY_SATISFIED | v0.6, one consistent shape incl. validation errors |
| Single-generation-job concurrency guard | ALREADY_SATISFIED | v0.6, verified under real concurrent load |
| Input validation (schema, bounds, path traversal) | ALREADY_SATISFIED | v0.6, defense-in-depth at 2 layers |
| CORS explicit allowlist (not `*`) | ALREADY_SATISFIED for local dev | REQUIRED_BEFORE_STAGING to make it env-configurable (Part J) rather than hardcoded dev origins |
| Configurable Engine DB location | REQUIRED_BEFORE_STAGING | v0.6 hardcoded an absolute local path in 3 places; staging needs a persistent-volume path |
| Fail-closed DB-missing check | REQUIRED_BEFORE_STAGING | See "concrete risk" above -- does not exist today at any layer |
| Readiness vs liveness distinction | REQUIRED_BEFORE_STAGING | v0.6 only has `/v1/health` (liveness-shaped); no check that the Engine is actually usable |
| Rate limiting (requests/time window) | REQUIRED_BEFORE_STAGING | v0.6 has concurrency protection, not rate limiting -- a valid-token caller could still hammer `/preview` sequentially |
| Structured logging (no secrets, request-hashed) | REQUIRED_BEFORE_STAGING | v0.6 logs to local JSONL files (`gateway_audit_log.jsonl`, Director's own `audit_log.jsonl`) but with no consistent per-request operational log line (status/latency/route) separate from the generation-specific audit trail |
| Containerization | REQUIRED_BEFORE_STAGING | v0.6 has never been packaged; local-only `uvicorn` invocation |
| Persistent volume design (DB + packages) | REQUIRED_BEFORE_STAGING | Both currently live on local disk with no volume/mount design |
| Backup + restore (tested, not just planned) | REQUIRED_BEFORE_STAGING | Never attempted before this milestone |
| Secrets management doc / `.env.example` | REQUIRED_BEFORE_STAGING | v0.6 documented the one env var in prose; no machine-checkable example file |
| Graceful shutdown / atomic writes under termination | REQUIRED_BEFORE_STAGING | Package writes were already atomic (v0.6, `Path.replace`); no `SIGTERM` handler existed |
| Process supervision | RECOMMENDED_BEFORE_STAGING | Correctly deferred to the hosting platform per this milestone's own instruction ("do not invent a custom supervisor") -- staging config must be *compatible* with platform supervision, not implement it |
| TLS termination | REQUIRED_BEFORE_STAGING (architecturally) | v0.6 explicitly never implemented TLS (correctly, per its own scope) -- staging needs the platform-proxy boundary *designed*, not homemade TLS in Python |
| Token rotation *procedure* (not a rotation system) | RECOMMENDED_BEFORE_STAGING | A documented manual procedure is enough for admin-only staging; an automated rotation system is not |
| Preview-vs-generate permission separation (RBAC) | PUBLIC_PRODUCTION_ONLY | Explicitly out of scope per this milestone's own "do not build a giant RBAC system" instruction; a single admin token covering both remains correct for admin-only staging |
| Real end-user authentication | PUBLIC_PRODUCTION_ONLY | Not needed while the Gateway remains admin-only |
| WAF / DDoS protection | PUBLIC_PRODUCTION_ONLY | Not proportionate to a private, admin-only, low-traffic staging surface |
| Postgres migration | NOT REQUIRED (explicitly out of scope this milestone) | SQLite remains staging runtime per this milestone's own instruction |
| Horizontal scaling / multi-instance | PUBLIC_PRODUCTION_ONLY | The single-generation-job design is intentionally single-process; do not build for a scale this project doesn't have yet |

## What this milestone does NOT do, on purpose

Per the classification above and this milestone's own restrictions: no RBAC
system, no Postgres migration, no WAF, no real end-user auth, no
multi-instance scaling design. Building any of these now would be exactly
the "blindly implement public-scale infrastructure that private staging
does not yet require" this Part explicitly warns against.
