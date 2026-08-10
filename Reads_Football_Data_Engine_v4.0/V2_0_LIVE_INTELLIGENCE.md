# Reads v2.0 — Live Football Intelligence

v2.0 connects the existing Reads football database, Game Factory, personalization, competitive system and community platform into a continuously refreshable content loop.

## Production loop

```text
NFL / CFB source refresh
        ↓
source + freshness audit
        ↓
change detection
        ↓
QA / hold unsafe changes
        ↓
verified football events
        ↓
live event puzzle generation
        ↓
admin publish queue
        ↓
puzzle catalog + Daily slate
        ↓
notification outbox
        ↓
Reads UI / personalization / community
```

## Live feeds

The database ships with feed definitions for:
- NFL players
- NFL rosters
- NFL schedules/results
- CFB rosters
- CFB schedules/results
- CFB stats (analysis-only until stat reconciliation passes)

`live_data_feeds` stores refresh policy, source, production-safety state and last-run status.

## Freshness

`freshness_registry` defines expected refresh intervals and stale thresholds. The engine can surface stale-domain alerts without deleting or fabricating data.

## Live events

Verified structured events live in `live_event_catalog`.

Completed game finals use a direct structured generator instead of relying on natural-language parsing. A verified final can immediately create:
- game-winner puzzle
- home-score puzzle
- away-score puzzle

Other event types can route into Game Factory rules.

## Publishing safety

Live content is generated as **PREVIEW** first. `publish_live_event()` moves verified event puzzles into `puzzle_catalog` only after approval.

Rejected or unverified events remain held.

## Daily slate

`READS_DAILY` currently contains:
- Daily Connections
- Daily NFL
- Daily CFB
- Daily Hard
- Daily Throwback
- Daily Cross-League

Selection is deterministic by date/slot seed, so everyone can receive the same official Daily challenge.

## Push-ready architecture

Publishing a live event can create a record in `notification_outbox`. Your production push provider can consume that queue later. No provider credentials are embedded in this package.

## Admin

Run:

```bash
python live_admin_api.py
```

Default port: `8792`.

Open `live_admin_dashboard.html`.

Read endpoints:
- `/v2/live/feeds`
- `/v2/live/alerts`
- `/v2/live/queue`
- `/v2/live/events`
- `/v2/live/slate`
- `/v2/live/outbox`

Write endpoints:
- `/v2/live/run`
- `/v2/live/event`
- `/v2/live/publish`
- `/v2/live/reject`

## Main command

```bash
python live_intelligence.py --update
```

On an ordinary internet-enabled host this can run the existing data refreshers first, then freshness/event/slate processing.

Without `--update`, it uses the data already present in the database.

## Frontend rule

Nothing in v2.0 requires replacing Reads' current visual design. The frontend can consume these APIs incrementally.
