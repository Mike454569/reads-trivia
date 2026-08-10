# Reads v2.3 — Launch Intelligence + Quality Control

v2.3 makes the Reads football engine self-auditing and formalizes the Reads Knowledge Graph.

## Truth Engine
Verified/source-backed graph facts are normalized into `qa_truth_claims`. Singular predicates can be scanned for contradictory values. Contradictions are recorded instead of silently overwriting data.

## Puzzle QA
Every puzzle is audited for verification status, source presence, payload validity and ambiguity. Exact duplicate payloads inside a mode are separately tracked.

The shipped audit intentionally does **not** auto-delete failed puzzles. A QA failure means HOLD/review; destructive correction should be source-backed.

## Difficulty calibration
`player_answer_stats` turns real answer telemetry into empirical difficulty after users play. With no attempts, existing designed difficulty remains unchanged.

## Mode quality
`mode_quality_metrics` scores modes using ambiguity, duplication and—when available—player skip/correct telemetry. Dead or unhealthy modes can be held without removing their underlying data.

## Coverage map
Coverage declarations and puzzle modes are converted into scored coverage dimensions. This exposes where Reads is strong and where additional source data is required.

## Reads Knowledge Graph
The formal graph contains verified football nodes and edges plus production-safe CFB↔NFL identity edges. It can traverse paths such as player → school, player → NFL team, and cross-league identity.

This is the foundation for the future natural-language Game Director: requests can be translated into graph paths and then passed to Game Factory only when the relationship is actually supported.

## Game Factory opportunities
v2.3 seeds graph-based expansion candidates for:
- verified two-hop paths
- CFB↔NFL identity traversal
- career relationship chains

Candidates remain reviewable instead of automatically publishing new modes.

## Daily / Live QA
`daily_qa_certifications` and `live_qa_certifications` provide PASS/HOLD gates before content publication.

## Reads Health Score
The health model combines:
- data truth
- puzzle quality
- coverage
- live freshness
- growth readiness
- infrastructure integrity

## Release certification
Every build can receive PASS / HOLD / FAIL with explicit blockers. Database integrity, foreign keys, compile state, truth contradictions and health score are part of the gate.

## API
Run `python quality_api.py` on port 8795.

Core endpoints:
- `GET /v2.3/health`
- `GET /v2.3/graph/query`
- `POST /v2.3/audit`
- `POST /v2.3/daily/certify`
- `POST /v2.3/release/certify`

Open `quality_dashboard.html` for the command center.

## Important interpretation
The v2.3 QA score measures the rules implemented here; it is not a claim that every historical football fact in the database has been independently researched by a human. Failed rows are surfaced for source-backed correction, and empirical difficulty improves as real play telemetry arrives.
