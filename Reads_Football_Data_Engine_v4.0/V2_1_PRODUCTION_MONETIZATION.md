# Reads v2.1 — Production Hardening + Monetization Foundation

v2.1 preserves v2.0 and adds the backend controls needed before serious traffic and monetization.

## Accounts + cloud sync
`production_engine.py` adds account identities, hashed bearer sessions, device registry and optimistic-revision cloud sync. Sync conflicts return the server revision rather than silently overwriting another device.

## Security / abuse
- RBAC roles: PLAYER, CREATOR, MODERATOR, EDITOR, ADMIN
- rate-limit buckets
- single-use ranked match tokens
- server-generated seeds and puzzle-set commitments
- replay, expiry, puzzle-set tamper and impossible-speed signals
- anti-cheat review queue

This is an application-level foundation; a production deployment should still terminate TLS at a real reverse proxy and use a managed identity/email provider rather than storing passwords here.

## PostgreSQL
Run `python postgres_migration_v2_1.py` to regenerate `postgres_v2_1_schema.sql`.

The package keeps SQLite as the portable source artifact. The generated PostgreSQL schema is the production migration target. Existing production-readiness work already included a migration layer; v2.1 extends the schema to the new account, security and monetization tables.

## Backups
`backup_manager.py` performs SQLite's online backup API, then runs `PRAGMA integrity_check`, SHA-256 hashes the result and records it in `backup_registry`.

## Observability
`service_health_events` and `request_metrics` provide a local persistence layer for health/error/latency data. In production, ship these to your monitoring stack.

## Reads+
The entitlement system is live, but charging is intentionally OFF by default.

Feature flags:
- `reads_plus_enabled = 0`
- `payments_enabled = 0`
- `sponsorships_enabled = 0`

No price was invented. `READS_PLUS_MONTHLY.price_cents` is NULL until you choose pricing and a payment provider.

Planned PLUS entitlements:
- ad-free
- unlimited creator games
- advanced stats
- private leagues
- premium ranked events
- unlimited profile cosmetics
- cloud sync

Free keeps cloud sync and core gameplay.

## Sponsorship architecture
Three disabled slots are defined:
- home feed between game cards
- post-game result
- Daily footer

They are placements only. No ad network is wired into the database and nothing changes the current Reads UI unless the frontend explicitly enables a slot.

## Analytics
`analytics_events` + `analytics_daily_funnel` track:
landing → game start → completion → account → streak → subscription.

## API
`python production_api.py` starts the local v2.1 service on port 8793.

## Important
This release does not claim that payments, email authentication, Redis/CDN caching, TLS, managed PostgreSQL, or an external observability provider are deployed. Those require production credentials/infrastructure. v2.1 supplies the schemas, controls, APIs and migration artifacts so they can be connected without redesigning the trivia engine.
