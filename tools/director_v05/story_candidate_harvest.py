"""Bulk candidate-story harvest for football lore.

This collector deliberately stores *candidates*, not verified lore. It fans out
across approved football-news domains and multiple story families using the
GDELT DOC 2.0 article index. Every harvested URL lands in REVIEW_REQUIRED and
must later pass source, subject, and factual-context review before promotion.

One full run is designed to collect thousands of unique URLs without turning
search-index metadata into gameplay facts.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from urllib.parse import urlparse

from tools.quiz_export import engine as engine_bootstrap
from .story_sqlite import (
    prepare_write_connection as _prepare_write_connection,
    commit_with_retry as _commit_with_retry,
)

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

APPROVED_DOMAINS = (
    "nfl.com",
    "espn.com",
    "cbssports.com",
    "foxsports.com",
    "si.com",
    "ncaa.org",
    "sports.yahoo.com",
    "usatoday.com",
)

QUERY_FAMILIES = {
    # Exact high-depth families used by Story Volume Certification v3.
    "BIZARRE_MOMENT": (
        '"bizarre play" football', '"weird play" football', '"strangest play" football',
        '"unusual touchdown" football', '"crazy ending" football game',
        '"rare play" football', '"accidental touchdown" football',
    ),
    "DRAFT_BUST": (
        '"draft bust" NFL', '"first-round bust" NFL', '"failed draft pick" NFL',
        '"draft disaster" NFL', '"draft-day mistake" NFL', '"historic draft miss" NFL',
    ),
    "TRADE_ODDITY": (
        '"weird trade" NFL', '"shocking trade" NFL', '"blockbuster trade" NFL',
        '"trade request" NFL player', '"draft-day trade" NFL', '"trade deadline" NFL unusual',
    ),
    "DISCIPLINE_LEGAL": (
        'NFL suspension player', '"college football" suspension player',
        'NFL discipline player', '"college football" discipline player',
        'NFL fine player incident', '"college football" fine player incident',
        'NFL arrest player', '"college football" arrest player',
    ),
    "COMEBACK_RETURN": (
        'NFL comeback retirement player', '"college football" comeback player',
        '"came out of retirement" NFL', '"returned to football" player',
        '"unretired" NFL player', '"career comeback" football player',
    ),
    "SIDELINE_INCIDENT": (
        '"sideline incident" football', '"sideline argument" football',
        '"sideline altercation" football', '"sideline confrontation" football',
        '"sideline penalty" football', '"bench incident" football',
    ),
    "COACHING_MELTDOWN": (
        '"coach rant" football', '"coach meltdown" football',
        '"coach quote" football bizarre', '"postgame rant" football',
        '"press conference" coach angry football', '"viral quote" coach football',
    ),
    "CELEBRATION_CONTROVERSY": (
        '"touchdown celebration" controversy', '"celebration penalty" football',
        '"taunting penalty" football', '"end zone celebration" football',
        '"celebration fine" NFL', '"sideline celebration" controversy',
    ),
    "RECRUITING_CHAOS": (
        '"college football" recruiting controversy', '"recruiting flip" football',
        '"signing day" chaos football', '"recruiting saga" football',
        '"commitment flip" football', '"recruiting surprise" college football',
    ),
    "RECORD_ODDITY": (
        '"NFL record" bizarre', '"college football record" bizarre',
        '"record-breaking" unusual football', '"first player ever" football record',
        '"rare record" football', '"strange record" football',
    ),
    "INFAMOUS_MISTAKE": (
        '"infamous mistake" football', '"costly mistake" football game',
        '"forgot the rules" football player', '"wrong way" football player',
        '"botched play" football historic', '"historic blunder" football',
    ),
    "OFF_FIELD_ODDITY": (
        '"off-field" football bizarre', '"Hard Knocks" unusual',
        '"training camp" funny football', 'football bizarre player',
        '"viral" football player', 'football prank player',
        'football costume player', '"strange story" football player',
    ),
    "RIVALRY_INCIDENT": (
        '"rivalry incident" college football', '"rivalry prank" college football',
        '"rivalry trophy" unusual', '"rivalry fight" college football',
        '"rivalry controversy" football', '"rivalry game" crazy ending football',
    ),
    "TRANSFER_NIL_CHAOS": (
        '"transfer portal" chaos football', '"transfer portal" surprise football',
        '"NIL" controversy college football', '"NIL deal" football unusual',
        '"transfer flip" college football', '"portal commitment" football surprise',
    ),
    "PLAYOFF_FORGOTTEN": (
        '"forgotten playoff" NFL', '"forgotten playoff moment" football',
        '"forgotten bowl game" college football', '"playoff upset" football historic',
        '"wild card" forgotten moment NFL', '"college football playoff" forgotten moment',
    ),

    # Supporting families retained because they produce useful context and
    # preserve compatibility with already-harvested corpus rows.
    "PRESS_CONFERENCE": (
        '"press conference"', '"postgame" coach', '"postgame" quarterback',
        '"media availability"', '"news conference"', '"locker room" interview',
        '"viral quote" football', '"memorable quote" football',
    ),
    "RULE_ODDITY": (
        'NFL unusual rule', '"college football" unusual rule', 'NFL rule change',
        'NCAA football rule change', '"obscure rule" football',
        '"rare penalty" football', '"rule loophole" football',
    ),
    # Legacy aliases are harvestable for backwards-compatible ad-hoc runs,
    # but the production A/B/C groups now target the exact v3 families above.
    "DRAFT_CHAOS": ('"NFL Draft" surprise pick', '"NFL Draft" slide player'),
    "TRADE_CHAOS": ('NFL trade shocking player', '"blockbuster trade" NFL'),
    "BUST_REDEMPTION": ('"draft bust" NFL player', '"career turnaround" NFL player'),
    "GAME_ODDITY": ('"weird play" NFL', '"bizarre play" football'),
    "COACHING_ODDITY": ('"coach rant" football', '"sideline incident" coach football'),
    "RIVALRY_ODDITY": ('"rivalry prank" college football', '"rivalry game" crazy ending football'),
    "CELEBRATION_FAN": ('football celebration', '"touchdown celebration"', 'football fan unusual'),
}

PRIMARY_DOMAINS = {"nfl.com", "ncaa.org"}

SENSITIVE_HINT_FAMILIES = {"DISCIPLINE_LEGAL"}


def _ensure_schema(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS football_story_candidates (
            candidate_id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            domain TEXT NOT NULL,
            seen_date TEXT,
            language TEXT,
            source_country TEXT,
            family_hint TEXT NOT NULL,
            query_text TEXT NOT NULL,
            evidence_tier_hint TEXT NOT NULL,
            sensitive_hint INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'REVIEW_REQUIRED',
            first_harvested_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            review_notes TEXT,
            promoted_event_id TEXT
        )
    """)
    c.execute(
        "CREATE INDEX IF NOT EXISTS ix_story_candidates_status "
        "ON football_story_candidates(status,family_hint)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS ix_story_candidates_domain "
        "ON football_story_candidates(domain,seen_date)"
    )
    _commit_with_retry(c)


def _candidate_id(url):
    return "storycand_" + hashlib.sha256(str(url).encode()).hexdigest()[:24]


def _canonical_url(url):
    parsed = urllib.parse.urlsplit(str(url).strip())
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    query = [
        (k, v) for k, v in query
        if not k.casefold().startswith("utm_")
        and k.casefold() not in {"fbclid", "gclid", "cmpid", "cid"}
    ]
    return urllib.parse.urlunsplit((
        parsed.scheme.casefold(),
        parsed.netloc.casefold(),
        parsed.path,
        urllib.parse.urlencode(query),
        "",
    ))


def _domain(url):
    return (urlparse(str(url)).hostname or "").casefold().removeprefix("www.")


def _fetch(query, *, max_records=250, timespan="1y", timeout=45):
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": max(1, min(int(max_records), 250)),
        "timespan": timespan,
        "format": "json",
        "sort": "datedesc",
    }
    url = GDELT_DOC_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Reads-Football-Lore-Harvester/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _articles(payload):
    if isinstance(payload, dict):
        rows = payload.get("articles")
        if isinstance(rows, list):
            return rows
    return []


def _evidence_hint(domain):
    return "PRIMARY" if domain in PRIMARY_DOMAINS else "REPUTABLE_MEDIA"


def harvest_story_candidates(
    *,
    domains=APPROVED_DOMAINS,
    query_families=QUERY_FAMILIES,
    max_records_per_query=250,
    timespan="1y",
    sleep_seconds=0.35,
):
    c = _prepare_write_connection(engine_bootstrap.connect())
    _ensure_schema(c)

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    metrics = Counter()
    failures = []
    unique_seen = set()

    try:
        for family, terms in query_families.items():
            for domain in domains:
                for term in terms:
                    query = f"({term}) (NFL OR \"college football\") domainis:{domain}"
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
                        # Never trust GDELT domain metadata over the URL itself.
                        if found_domain != domain:
                            metrics["domain_mismatch"] += 1
                            continue

                        cid = _candidate_id(url)
                        if cid in unique_seen:
                            metrics["duplicate_in_run"] += 1
                            continue
                        unique_seen.add(cid)

                        sensitive = 1 if family in SENSITIVE_HINT_FAMILIES else 0
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
                                term,
                                _evidence_hint(found_domain),
                                sensitive,
                                "REVIEW_REQUIRED",
                                now,
                                now,
                            ),
                        )
                        metrics["accepted_candidates"] += 1

                    _commit_with_retry(c)
                    if sleep_seconds:
                        time.sleep(float(sleep_seconds))
    finally:
        totals = c.execute(
            """SELECT status,COUNT(*) n
               FROM football_story_candidates
               GROUP BY status"""
        ).fetchall()
        by_family = c.execute(
            """SELECT family_hint,COUNT(*) n
               FROM football_story_candidates
               GROUP BY family_hint ORDER BY n DESC"""
        ).fetchall()
        c.close()

    return {
        "metrics": dict(metrics),
        "failures": failures[:100],
        "queue_totals": {str(r["status"]): int(r["n"]) for r in totals},
        "family_totals": {str(r["family_hint"]): int(r["n"]) for r in by_family},
        "theoretical_max_raw_per_run":
            len(domains)
            * sum(len(v) for v in query_families.values())
            * min(int(max_records_per_query), 250),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--timespan", default="1y")
    ap.add_argument("--max-records-per-query", type=int, default=250)
    args = ap.parse_args()
    print(json.dumps(
        harvest_story_candidates(
            timespan=args.timespan,
            max_records_per_query=args.max_records_per_query,
        ),
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
