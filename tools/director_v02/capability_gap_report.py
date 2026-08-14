"""Capability gap detector -- run this after any data import to see whether
new real facts landed in the Engine with no way for the Game Creator to ask
about them yet.

Why this exists, and why it does NOT auto-register anything: registry.py's
own module docstring is explicit that a capability is only ever registered
after a real, hand-written, tested adapter proves the data is playable --
"never by loosening validation or writing a generic query engine." A
predicate existing in `relationships` does not by itself mean the data is
clean enough, resolvable enough, or shaped right for a fair four-option
guessing game (see nfl_season_awards.py's own module docstring for a real
example: a wide, ungated distractor pool produces obviously-wrong options a
real fan would never mistake for plausible). This script closes the other
half of the gap instead -- the discovery half. Before the NFL Wikipedia
history import's own capabilities were registered, someone had to ask "does
the Creator have this?" and get a real, manually-typed answer; this script
answers that question automatically, for every predicate, going forward.
It still leaves "is this predicate's data good enough for a real capability"
as a human/adapter-author judgment call -- same as it always was.

Usage:  python3 -m tools.director_v02.capability_gap_report
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine  # noqa: E402
from tools.director_v02 import registry, schema  # noqa: E402


def registered_predicates() -> set[str]:
    return {predicate for (_mechanic, _domain, predicate) in registry.all_capability_keys()}


def scan_for_capability_gaps(c) -> dict:
    """Every distinct `relationships.predicate` value with real rows,
    cross-referenced against what the Creator can actually generate a game
    from today. Three real buckets, not a single pass/fail:

    - `registered`: a capability already exists for this predicate.
    - `schema_only`: the predicate is expressible in schema.py's allowlist
      (someone already scoped it for a future capability) but no adapter/
      registry entry exists yet -- the exact `UNDERSTOOD_BUT_UNSUPPORTED`
      gap validator.py itself already detects at request time, surfaced
      here proactively instead of only when a user happens to ask.
    - `undiscovered`: real data sitting in `relationships` with NO trace in
      schema.py at all -- the case this script exists for: genuinely new
      information (e.g. a fresh import) that nobody has looked at yet from
      the Creator's point of view.
    """
    rows = c.execute(
        "SELECT predicate, subject_type, object_type, COUNT(*) as n, "
        "MIN(season_start) as min_season, MAX(season_end) as max_season, "
        "GROUP_CONCAT(DISTINCT source_id) as source_ids "
        "FROM relationships GROUP BY predicate, subject_type, object_type ORDER BY predicate"
    ).fetchall()

    registered = registered_predicates()
    schema_predicates = set(schema.ALLOWED_PREDICATES)

    registered_bucket, schema_only_bucket, undiscovered_bucket = [], [], []
    for r in rows:
        entry = {
            "predicate": r["predicate"], "subject_type": r["subject_type"], "object_type": r["object_type"],
            "row_count": r["n"], "min_season": r["min_season"], "max_season": r["max_season"],
            "source_ids": r["source_ids"],
        }
        if r["predicate"] in registered:
            registered_bucket.append(entry)
        elif r["predicate"] in schema_predicates:
            schema_only_bucket.append(entry)
        else:
            undiscovered_bucket.append(entry)

    return {
        "registered": registered_bucket,
        "schema_only_not_registered": schema_only_bucket,
        "undiscovered": undiscovered_bucket,
    }


def print_report(report: dict) -> None:
    print(f"registered (Creator can generate a game today): {len(report['registered'])} predicate/type combos")
    for e in report["registered"]:
        print(f"  OK   {e['predicate']:<28} {e['subject_type']}->{e['object_type']:<20} {e['row_count']} rows")

    print(f"\nschema-only, not registered (known gap, no adapter yet): {len(report['schema_only_not_registered'])}")
    for e in report["schema_only_not_registered"]:
        print(f"  WARN {e['predicate']:<28} {e['subject_type']}->{e['object_type']:<20} {e['row_count']} rows")

    print(f"\nUNDISCOVERED (new data, nobody has looked at this from the Creator's side yet): "
          f"{len(report['undiscovered'])}")
    for e in report["undiscovered"]:
        seasons = f"{e['min_season']}-{e['max_season']}" if e["min_season"] else "no season range"
        print(f"  NEW  {e['predicate']:<28} {e['subject_type']}->{e['object_type']:<20} "
              f"{e['row_count']} rows ({seasons}, source={e['source_ids']})")

    if not report["undiscovered"] and not report["schema_only_not_registered"]:
        print("\nNo gaps -- every real relationships predicate is already Creator-registered.")


if __name__ == "__main__":
    conn = engine.connect()
    try:
        result = scan_for_capability_gaps(conn)
    finally:
        conn.close()
    print_report(result)
