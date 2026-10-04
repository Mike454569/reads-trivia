"""CFB-specific Story Factory candidate harvest.

This expands college-football coverage independently of the mixed NFL/CFB
harvest. It uses CFB-only query families plus canonical school names from the
Engine when available, while still storing candidates only. Promotion remains
subject/evidence gated downstream.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import time
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap

from .story_candidate_harvest import (
    _articles,
    _candidate_id,
    _canonical_url,
    _domain,
    _ensure_schema,
    _evidence_hint,
    _fetch,
)

CFB_DOMAINS = (
    "ncaa.org",
    "espn.com",
    "cbssports.com",
    "foxsports.com",
    "si.com",
    "usatoday.com",
)

CFB_QUERY_FAMILIES = {
    "PRESS_CONFERENCE": (
        '"college football" "press conference"',
        '"college football" postgame coach',
        '"college football" postgame quarterback',
        '"college football" "media availability"',
        '"college football" reporters coach',
    ),
    "OFF_FIELD_ODDITY": (
        '"college football" bizarre',
        '"college football" unusual story',
        '"college football" funny player',
        '"college football" viral player',
        '"college football" training camp unusual',
    ),
    "CELEBRATION_FAN": (
        '"college football" celebration',
        '"college football" mascot',
        '"college football" fan unusual',
        '"college football" sideline celebration',
    ),
    "RULE_ODDITY": (
        '"college football" rule change',
        '"college football" unusual rule',
        '"NCAA football" rule change',
    ),
    "DISCIPLINE_LEGAL": (
        '"college football" suspension player',
        '"college football" arrest player',
        '"college football" discipline player',
    ),
}

SENSITIVE_FAMILIES = {"DISCIPLINE_LEGAL"}


def _table_columns(c, table):
    try:
        return [str(r[1]) for r in c.execute(f"PRAGMA table_info({table})")]
    except sqlite3.Error:
        return []


def _school_names(c, *, limit=80):
    """Best-effort canonical FBS/P4 school labels for school-specific fanout."""
    tables = {
        str(r[0]) for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    names = []
    for table in ("schools", "school_aliases"):
        if table not in tables:
            continue
        cols = _table_columns(c, table)
        label_col = next(
            (x for x in ("school_name", "name", "display_name", "canonical_name", "alias")
             if x in cols),
            None,
        )
        if not label_col:
            continue
        try:
            rows = c.execute(
                f"""SELECT DISTINCT {label_col}
                    FROM {table}
                    WHERE {label_col} IS NOT NULL
                      AND TRIM({label_col})<>''
                    ORDER BY {label_col}
                    LIMIT ?""",
                (max(1, int(limit)),),
            ).fetchall()
            names.extend(str(r[0]).strip() for r in rows if r[0])
        except sqlite3.Error:
            continue
    deduped = []
    seen = set()
    for name in names:
        key = name.casefold()
        if key in seen or len(name) < 3:
            continue
        seen.add(key)
        deduped.append(name)
    return deduped[: max(1, int(limit))]


def harvest_cfb_story_candidates(
    *,
    max_records_per_query=250,
    timespan="5y",
    school_limit=80,
    school_query_limit=120,
    sleep_seconds=0.25,
):
    c = engine_bootstrap.connect()
    _ensure_schema(c)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    metrics = Counter()
    failures = []
    unique_seen = set()

    schools = _school_names(c, limit=school_limit)
    school_terms = []
    for school in schools:
        school_terms.extend([
            ("PRESS_CONFERENCE", f'"{school}" football postgame'),
            ("OFF_FIELD_ODDITY", f'"{school}" football unusual'),
            ("CELEBRATION_FAN", f'"{school}" football celebration'),
        ])
    school_terms = school_terms[: max(0, int(school_query_limit))]

    query_jobs = []
    for family, terms in CFB_QUERY_FAMILIES.items():
        for domain in CFB_DOMAINS:
            for term in terms:
                query_jobs.append((family, domain, term))
    # School-specific fanout is deliberately primary-heavy to control volume.
    for family, term in school_terms:
        for domain in ("ncaa.org", "espn.com", "cbssports.com"):
            query_jobs.append((family, domain, term))

    try:
        for family, domain, term in query_jobs:
            query = f"({term}) domainis:{domain}"
            try:
                payload = _fetch(
                    query,
                    max_records=max_records_per_query,
                    timespan=timespan,
                )
            except Exception as exc:
                failures.append({
                    "family": family,
                    "domain": domain,
                    "query": term,
                    "reason": type(exc).__name__ + ":" + str(exc),
                })
                metrics["query_failures"] += 1
                continue

            metrics["queries_succeeded"] += 1
            rows = _articles(payload)
            metrics["raw_articles"] += len(rows)

            for article in rows:
                raw_url = str(article.get("url") or "").strip()
                title = str(article.get("title") or "").strip()
                if not raw_url or not title:
                    metrics["missing_url_or_title"] += 1
                    continue

                url = _canonical_url(raw_url)
                found_domain = _domain(url)
                if found_domain != domain:
                    metrics["domain_mismatch"] += 1
                    continue
                cid = _candidate_id(url)
                if cid in unique_seen:
                    metrics["duplicate_in_run"] += 1
                    continue
                unique_seen.add(cid)

                sensitive = 1 if family in SENSITIVE_FAMILIES else 0
                c.execute(
                    """INSERT INTO football_story_candidates(
                       candidate_id,source_url,title,domain,seen_date,language,
                       source_country,family_hint,query_text,evidence_tier_hint,
                       sensitive_hint,status,first_harvested_at,last_seen_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(source_url) DO UPDATE SET
                         title=excluded.title,
                         seen_date=COALESCE(excluded.seen_date,football_story_candidates.seen_date),
                         language=COALESCE(excluded.language,football_story_candidates.language),
                         source_country=COALESCE(excluded.source_country,football_story_candidates.source_country),
                         last_seen_at=excluded.last_seen_at""",
                    (
                        cid,
                        url,
                        title,
                        found_domain,
                        article.get("seendate"),
                        article.get("language"),
                        article.get("sourcecountry"),
                        family,
                        "CFB:" + term,
                        _evidence_hint(found_domain),
                        sensitive,
                        "REVIEW_REQUIRED",
                        now,
                        now,
                    ),
                )
                metrics["accepted_candidates"] += 1
            c.commit()
            if sleep_seconds:
                time.sleep(float(sleep_seconds))
    finally:
        totals = c.execute(
            """SELECT family_hint,COUNT(*) n
               FROM football_story_candidates
               WHERE query_text LIKE 'CFB:%'
               GROUP BY family_hint ORDER BY n DESC"""
        ).fetchall()
        c.close()

    return {
        "metrics": dict(metrics),
        "failures": failures[:100],
        "school_names_used": len(schools),
        "query_jobs": len(query_jobs),
        "cfb_family_totals": {str(r["family_hint"]): int(r["n"]) for r in totals},
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--timespan", default="5y")
    ap.add_argument("--school-limit", type=int, default=80)
    ap.add_argument("--school-query-limit", type=int, default=120)
    args = ap.parse_args()
    print(json.dumps(harvest_cfb_story_candidates(
        timespan=args.timespan,
        school_limit=args.school_limit,
        school_query_limit=args.school_query_limit,
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
