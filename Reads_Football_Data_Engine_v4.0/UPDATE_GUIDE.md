# Updating Reads Football

You only need the newest release package.

## Update college football

Run:

```bash
python update_cfb.py
```

Default behavior: tries the prior and current calendar season, downloading any published SportsDataverse/cfbfastR-data schedule and roster CSVs.

Specific seasons:

```bash
python update_cfb.py --seasons 2025 2026
```

Also download/register the event-derived player-stat feed for internal validation:

```bash
python update_cfb.py --seasons 2025 2026 --stats
```

Exact season-total trivia from the event-derived stat feed remains disabled until reconciliation checks pass.

## Update NFL

```bash
python fetch_nflverse_current.py --players --rosters 2025 2026
```

## Update both

```bash
python update_everything.py
```

The updater uses transactions, source hashes, source-release records, relationship rebuilds, puzzle collision gates, coverage metadata, and foreign-key validation. Missing unpublished season files are skipped cleanly unless `--strict` is supplied.
