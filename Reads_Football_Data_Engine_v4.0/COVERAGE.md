# Reads Football v1.3 coverage

The database ships with the same cumulative validated data foundation as v1.1, plus refresh automation for future seasons.

## NFL
- Existing game/draft/history foundation retained.
- Current player/roster refresher: `fetch_nflverse_current.py`.
- Current nflverse release binaries must be fetched on a normal outbound-HTTPS host.

## College Football
- Real schedules/results already present through the shipped data coverage.
- Real 2024–2025 roster-season foundation retained.
- `update_cfb.py` can fetch any published season from the SportsDataverse/cfbfastR-data schedule and roster paths and update the same canonical tables.
- Event-derived player-stat downloads are analysis/validation-only until exact totals reconcile to trusted aggregate totals.

The database `data_coverage` table remains the source of truth for which domains are production-safe.
