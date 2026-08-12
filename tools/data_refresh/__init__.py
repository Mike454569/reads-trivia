"""Automatic NFL + CFB production data refresh (Reads Engine Gateway).

Orchestration ONLY -- every module in this package calls into the existing,
already-tested Engine importers (Reads_Football_Data_Engine_v4.0/
fetch_nflverse_current.py, import_data.py, identity_bridge_v16.py,
backup_manager.py) rather than reimplementing their logic. That directory
is vendored Engine code and is never edited by this project (the same rule
tools/quiz_export/engine.py already documents) -- this package is where the
NEW production-safety layer those scripts don't have on their own lives:
backup-before/sanity-check-after/restore-on-failure, run tracking, and the
admin-facing orchestration the Gateway calls.

See safety.py, nfl_refresh.py, cfb_refresh.py.
"""
