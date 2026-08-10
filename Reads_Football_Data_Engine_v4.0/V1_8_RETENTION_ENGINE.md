# Reads v1.8 — Personalization & Competitive Intelligence

v1.8 adds a retention layer without changing the existing Reads visual design.

## Telemetry
Send ANSWER / COMPLETE / ABANDON events to `retention_engine.py` or `retention_api.py`.
The engine records solve rate, response time, wrong guesses, hints and abandonment.

## Empirical difficulty
`puzzle_difficulty_live` learns difficulty from real player behavior. Confidence ramps with attempts, so low-sample telemetry cannot instantly overpower the curated difficulty score.

## Personalization
`personalized_feed()` combines each user's per-mode skill with puzzle difficulty and novelty. It avoids puzzles the user has already played and returns a reason for each recommendation.

## Competitive
- seasonal ratings
- Rookie → Bronze → Silver → Gold → Platinum → Diamond → All-Pro → GOAT
- provisional higher-K rating movement for new players
- XP + levels
- daily/longest streaks
- achievements

## Challenges
`create_challenge()` freezes a puzzle set and seed so both players get the same content.

## API
Run:
```bash
python retention_api.py
```
Default local port: `8788`.

Endpoints:
- `GET /v1/feed?user=...`
- `GET /v1/streak?user=...`
- `POST /v1/event`
- `POST /v1/ranked/result`
- `POST /v1/challenge`

The frontend can adopt these endpoints incrementally; no visual redesign is required.
