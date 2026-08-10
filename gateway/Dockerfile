# Reads Engine Gateway -- container definition (Director v0.7, Part C).
#
# Build context is the REPO ROOT (nfl-trivia/), not gateway/ -- this image
# needs tools/ (director_v02, director_v04, quiz_export) alongside
# gateway/ itself. Build with:
#   docker build -f gateway/Dockerfile -t reads-engine-gateway:v0.7 .
#
# Deliberately does NOT contain the Football Warehouse (Engine .py modules
# + the 1.65GB reads_football_v4.0.sqlite file) -- those are coupled to
# each other (game_factory.py resolves its DB file relative to its own
# location on disk, not via any env var -- see tools/quiz_export/engine.py's
# docstring) and both live together on a persistent volume mounted at
# runtime, set via READS_ENGINE_DIR. See
# READS_ENGINE_STAGING_V01_REPORT.md's persistent-volume design for the
# full reasoning and READS_ENGINE_STAGING_FLY_DEPLOYMENT_PLAN.md for the
# concrete mount path this milestone chose.

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.title="reads-engine-gateway" \
      org.opencontainers.image.description="Local/staging API gateway in front of the Reads Football Warehouse (Director v0.2-v0.6)."

# --- system deps -----------------------------------------------------------
# None beyond what python:3.11-slim-bookworm already provides -- this image
# needs no compiler, no curl, no extra OS packages. sqlite3 ships in the
# Python standard library; no system sqlite package is required.

# --- non-root runtime user (Part C) -----------------------------------------
RUN groupadd --system gateway && useradd --system --gid gateway --home-dir /app --no-create-home gateway

WORKDIR /app

# --- pinned dependencies (Part C) -------------------------------------------
# Only the runtime requirements file -- requirements-dev.txt (pytest) is
# intentionally never copied into this image; a production/staging
# container has no business running the test suite.
COPY gateway/requirements.txt /app/gateway/requirements.txt
RUN pip install --no-cache-dir --no-compile -r /app/gateway/requirements.txt

# --- application code --------------------------------------------------------
# Only what the Gateway actually imports at runtime -- NOT data/, assets/,
# app.js/index.html/styles.css (the static Reads frontend, a completely
# separate deployable with its own hosting, unaffected by this image), NOT
# generated_games/ (hand-approved milestone deliverables, not Gateway
# runtime state), NOT any Engine code (see the module docstring above).
COPY tools/ /app/tools/
COPY gateway/ /app/gateway/

# Package storage lives in the image only as an empty, correctly-owned
# directory -- the actual persistent data is a mounted volume at runtime
# (see fly.toml). Creating it here means a fresh container that hasn't had
# a volume attached yet still starts cleanly (packages just won't survive a
# restart until a real volume is mounted -- readiness reflects the Engine
# DB's state, not this).
RUN mkdir -p /app/gateway/storage/packages && chown -R gateway:gateway /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    READS_ENGINE_PACKAGES_DIR=/data/packages \
    READS_ENGINE_LOG_DIR=/data/logs

# Documented, not baked in: READS_ENGINE_DIR (Engine volume mount path),
# READS_ENGINE_ADMIN_TOKEN, READS_ENGINE_ALLOWED_ORIGINS -- see .env.example
# and READS_ENGINE_STAGING_V01_REPORT.md's secrets-management section. No
# secret of any kind is set with ENV in this file.

EXPOSE 8850

USER gateway

# Liveness-only, matching /v1/health's own scope (Part L) -- readiness
# (/v1/ready, which checks the Engine DB) is deliberately NOT what decides
# whether the container gets killed and restarted: an unmounted/still-
# initializing volume should make the platform stop ROUTING traffic here
# (a job for /v1/ready via the platform's readiness check, see fly.toml),
# not repeatedly kill and restart an otherwise-healthy process.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8850/v1/health', timeout=3).status == 200 else 1)"

# No TLS here -- plain HTTP on an internal port, terminated by the
# platform/reverse proxy in front of this container. See
# READS_ENGINE_STAGING_V01_REPORT.md, Part I.
CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8850"]
