# Drop-in import workflow

Put approved CSV files in `imports/` or anywhere accessible locally.

Commands:

```bash
python import_data.py nflverse_players /path/to/players.csv
python import_data.py nflverse_rosters /path/to/roster_2025.csv
python import_data.py cfb_games /path/to/cfb_games.csv
```

Each import:
1. creates an immutable batch ID
2. hashes the source file
3. stages rows
4. rejects malformed rows instead of guessing
5. maps canonical schools conservatively
6. publishes in one transaction
7. rebuilds graph relationships
8. records QA counts
9. rolls back the publish transaction on failure

Generated relationships after roster import:
- `PLAYED_FOR`
- `WORE_NUMBER`
- `PLAYED_POSITION`
- `ATTENDED`
- `TEAMMATE_OF`

Generated CFB game relationships:
- `CFB_PLAYED_GAME`
- `CFB_BEAT`
- `CFB_LOST_TO`

Same-name people are never merged without stable IDs.
