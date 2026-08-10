# Reads v3.0 — AI Game Director

v3.0 adds the first natural-language orchestration layer above the cumulative Reads football engine.

## Pipeline
**Describe → Parse → Plan → Feasibility → Generate → QA → Publish**

The Director does not invent joins or bypass the existing source/identity rules. Unsupported requests remain BLOCKED until Reads has the required data or identity support.

## What it can do now
The Director inherits Game Factory's supported mechanics and adds an explicit graph/data plan. Initial high-confidence intents include:
- CFB same-school + same-position Connections
- CFB school/position odd-one-out
- NFL same draft-team + position groups
- CFB transfer-count games
- temporal teammate games
- CFB award → NFL draft sequences when the identity bridge is production-safe

## Safety rule
Natural language is not authority. `feasibility()` is authority. Game Factory remains the sole publication layer.

## API
Run `python game_director_api.py` on port 8800.

Endpoints:
- `POST /v3/director/interpret`
- `POST /v3/director/preview`
- `POST /v3/director/publish`
- `GET /v3/director/examples`

Open `game_director_dashboard.html` for the UI.
