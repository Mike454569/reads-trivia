# Reads v3.1 — Autonomous Game Expansion + Director Memory

v3.1 teaches Reads to inspect its own verified data relationships, recommend what kind of game each relationship can sustain, remember approved mechanics, and understand a wider set of natural-language constraints.

## New systems
- Autonomous mode discovery
- Candidate-depth estimation
- ENDLESS / STANDARD_MODE / ROTATING_PACK / DAILY_OR_EVENT recommendations
- Pre-publication auto-certification
- Persistent Director template memory
- Advanced operators: exactly, at least, at most, before, after, ranges, NOT, AND, OR
- Memory-aware Director routing

## Core rule
Discovery is not publication. Reads may propose a game automatically, but only certified relationships can proceed to the existing Game Factory/QA publication pipeline.

## API
Run `python autonomous_api.py` on port 8801.

Endpoints:
- `GET /v3.1/discover`
- `GET /v3.1/memory?q=...`
- `POST /v3.1/direct`
- `POST /v3.1/memory`
- `POST /v3.1/certify`
