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
