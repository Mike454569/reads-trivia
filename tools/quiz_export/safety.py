"""Production-safety gates.

Two distinct functions, not one forced generalization -- the underlying
Engine mechanism genuinely differs per domain. Draft's NFL_DRAFT domain has
a `data_coverage` summary row to check directly; QB starts and postseason
results have no such row, so those domains fall back to an exhaustive
row-level check instead. Merging these into one function with a fallback
branch would risk silently treating "no data_coverage row" as equivalent to
"verified," which would be a real weakening of the gate. See
QUIZ_EXPORT_FRAMEWORK_REFACTOR_PLAN.md.
"""
from __future__ import annotations


def check_domain_coverage_safety(c, domain_id: str) -> dict:
    """Draft's pattern: verify via an existing data_coverage domain row."""
    cov = c.execute(
        "SELECT domain_id,competition_id,dataset_name,coverage_start,coverage_end,"
        "completeness,production_safe,source_id FROM data_coverage WHERE domain_id=?",
        (domain_id,),
    ).fetchone()
    if not cov or not cov["production_safe"]:
        raise SystemExit(f"ABORT: {domain_id} is not marked production_safe in data_coverage.")
    src = c.execute(
        "SELECT source_id,source_name,approved_for_import FROM sources WHERE source_id=?",
        (cov["source_id"],),
    ).fetchone()
    if not src or not src["approved_for_import"]:
        raise SystemExit(f"ABORT: source {cov['source_id']} is not approved_for_import.")
    return {
        "domain_id": cov["domain_id"], "competition_id": cov["competition_id"],
        "dataset_name": cov["dataset_name"], "coverage_start": cov["coverage_start"],
        "coverage_end": cov["coverage_end"], "completeness": cov["completeness"],
        "production_safe": bool(cov["production_safe"]), "source_id": src["source_id"],
        "source_name": src["source_name"], "approved_for_import": bool(src["approved_for_import"]),
    }


def check_table_wide_safety(c, table: str, required_source, where_extra: str | None = None) -> dict:
    """QB/Championship's pattern: no data_coverage row exists, so verify the
    source(s) are approved and exhaustively check every relevant row is
    SOURCE_BACKED/matching one of those sources -- not sampled, every row.

    `required_source` accepts a single source_id (str, original behavior,
    every existing call site keeps working unchanged) or an iterable of
    source_ids -- needed once v0.8's modern roster import gave
    canonical_players two legitimate, independently-approved provenances
    (NFLVERSE_DATA's original 2006-2019 rows, NFLVERSE_ROSTERS' 2020-2026
    extension) instead of one. Still an exhaustive allow-list check, not a
    weakening of it: a row whose source_id isn't in the given set still
    fails the gate exactly as before."""
    sources_list = [required_source] if isinstance(required_source, str) else list(required_source)
    placeholders = ",".join("?" for _ in sources_list)
    src_rows = c.execute(
        f"SELECT source_id, source_name, approved_for_import FROM sources WHERE source_id IN ({placeholders})",
        sources_list,
    ).fetchall()
    found_ids = {r["source_id"] for r in src_rows}
    missing = [s for s in sources_list if s not in found_ids]
    if missing:
        raise SystemExit(f"ABORT: source(s) {missing} not found in the sources registry.")
    unapproved = [r["source_id"] for r in src_rows if not r["approved_for_import"]]
    if unapproved:
        raise SystemExit(f"ABORT: source(s) {unapproved} are not approved_for_import.")
    where = f"WHERE {where_extra}" if where_extra else ""
    total = c.execute(f"SELECT COUNT(*) FROM {table} {where}").fetchone()[0]
    where2 = (where + " AND " if where else "WHERE ") + f"verification_status='SOURCE_BACKED' AND source_id IN ({placeholders})"
    clean = c.execute(f"SELECT COUNT(*) FROM {table} {where2}", sources_list).fetchone()[0]
    if clean != total:
        raise SystemExit(
            f"ABORT: {table} has {total - clean} row(s) that are not "
            f"SOURCE_BACKED/{sources_list}; this assumed uniform provenance."
        )
    name_by_id = {r["source_id"]: r["source_name"] for r in src_rows}
    names = [name_by_id[s] for s in sources_list]
    return {
        "source_id": sources_list[0] if len(sources_list) == 1 else sources_list,
        "source_name": names[0] if len(names) == 1 else names,
        "approved_for_import": True,
        f"{table}_rows_total": total, f"{table}_rows_verified": clean,
    }


def check_verification_status_safety(c, table: str, source_id: str, status_value: str,
                                      where_extra: str | None = None) -> dict:
    """A third, distinct pattern (CFB data enrichment operation) -- for a
    "fact" table that carries its own exact `verification_status` string but
    has NO per-row `source_id` column at all (unlike Draft/Championship/
    Lineup's NFL tables, which all do). `cfb_award_facts` is the first real
    case: 91 rows, verification_status='SOURCE_BACKED_FROM_CFB_MASTER',
    checked directly against the real schema (audited before writing this,
    not assumed) -- there is no `source_id` column to filter by, so trying
    to reuse `check_table_wide_safety()` as-is would raise a real SQL error
    ("no such column: source_id"), not just a safe ABORT. Same discipline as
    the two functions above: source registered + approved_for_import
    checked once, then an EXHAUSTIVE (not sampled) per-row check that every
    row carries the exact expected status string -- a row with any other
    value still fails the gate exactly as before."""
    src = c.execute(
        "SELECT source_id, source_name, approved_for_import FROM sources WHERE source_id=?",
        (source_id,),
    ).fetchone()
    if not src:
        raise SystemExit(f"ABORT: source {source_id!r} not found in the sources registry.")
    if not src["approved_for_import"]:
        raise SystemExit(f"ABORT: source {source_id!r} is not approved_for_import.")
    where = f"WHERE {where_extra}" if where_extra else ""
    total = c.execute(f"SELECT COUNT(*) FROM {table} {where}").fetchone()[0]
    where2 = (where + " AND " if where else "WHERE ") + "verification_status=?"
    clean = c.execute(f"SELECT COUNT(*) FROM {table} {where2}", (status_value,)).fetchone()[0]
    if clean != total:
        raise SystemExit(
            f"ABORT: {table} has {total - clean} row(s) that are not verification_status={status_value!r}; "
            f"this assumed uniform provenance."
        )
    return {
        "source_id": source_id, "source_name": src["source_name"], "approved_for_import": True,
        f"{table}_rows_total": total, f"{table}_rows_verified": clean,
    }


def check_source_id_only_safety(c, table: str, source_id: str, where_extra: str | None = None) -> dict:
    """A fourth, distinct pattern (App-Wide Engine Migration operation) --
    the mirror image of check_verification_status_safety() above: a table
    that carries a per-row `source_id` column but has NO `verification_status`
    column at all. `games` (the NFL games/schedule/score table nfl_games_
    refresh.py populates) is the first real case, confirmed directly against
    the real schema (audited before writing this, not assumed) -- 35
    columns, no `verification_status` among them. Trying to reuse
    check_table_wide_safety() as-is would raise a real SQL error ("no such
    column: verification_status"), not just a safe ABORT. Same discipline
    as the other three functions in this module: source registered +
    approved_for_import checked once, then an EXHAUSTIVE (not sampled)
    per-row check that every row's source_id matches the expected value --
    a row from any other source still fails the gate exactly as before."""
    src = c.execute(
        "SELECT source_id, source_name, approved_for_import FROM sources WHERE source_id=?",
        (source_id,),
    ).fetchone()
    if not src:
        raise SystemExit(f"ABORT: source {source_id!r} not found in the sources registry.")
    if not src["approved_for_import"]:
        raise SystemExit(f"ABORT: source {source_id!r} is not approved_for_import.")
    where = f"WHERE {where_extra}" if where_extra else ""
    total = c.execute(f"SELECT COUNT(*) FROM {table} {where}").fetchone()[0]
    where2 = (where + " AND " if where else "WHERE ") + "source_id=?"
    clean = c.execute(f"SELECT COUNT(*) FROM {table} {where2}", (source_id,)).fetchone()[0]
    if clean != total:
        raise SystemExit(
            f"ABORT: {table} has {total - clean} row(s) with a source_id other than {source_id!r}; "
            f"this assumed uniform provenance."
        )
    return {
        "source_id": source_id, "source_name": src["source_name"], "approved_for_import": True,
        f"{table}_rows_total": total, f"{table}_rows_verified": clean,
    }


def check_season_coverage_safety(c, table: str, season_col: str, expected_min_season: int,
                                  where_extra: str | None = None) -> dict:
    """Final Technical Risk Cleanup pass: a fifth, distinct pattern -- none
    of the four checks above catch DEPTH drift (a table that's internally
    consistent and fully SOURCE_BACKED, but has silently lost most of its
    real historical row range). The real incident this guards: production's
    `cfb_standings` held only the current season's 138 rows (a real,
    correctly-provenanced, but drastically incomplete slice) after only the
    routine "current season only" scheduled refresh had ever run there --
    every other safety check in this module would have reported that slice
    as perfectly clean, since every row in it genuinely was SOURCE_BACKED.

    Read-only reporting, deliberately -- unlike the ABORT-on-violation
    checks above (each gates an active refresh run before it writes), this
    is meant to be called from a diagnostic/regression context (a pytest
    assertion, or an admin diagnostics route) that wants to OBSERVE
    coverage, not block a write in progress. Returns `min_season`/
    `max_season`/`distinct_seasons`/`row_count`, plus `coverage_ok` (True
    only if real rows exist at or before `expected_min_season`) for the
    caller to assert on."""
    where = f"WHERE {where_extra}" if where_extra else ""
    row = c.execute(
        f"SELECT MIN({season_col}), MAX({season_col}), COUNT(DISTINCT {season_col}), COUNT(*) FROM {table} {where}"
    ).fetchone()
    min_season, max_season, distinct_seasons, row_count = row[0], row[1], row[2], row[3]
    return {
        "table": table, "min_season": min_season, "max_season": max_season,
        "distinct_seasons": distinct_seasons, "row_count": row_count,
        "expected_min_season": expected_min_season,
        "coverage_ok": min_season is not None and min_season <= expected_min_season,
    }
