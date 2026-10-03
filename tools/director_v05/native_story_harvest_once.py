"""One-off primary-source Story Factory population for production certification.

This file is intentionally executed from a temporary workflow branch. It reads
NFL.com's official HTML article sitemap and NCAA.com's official football RSS
feeds, inserts candidate metadata into the existing Story Factory queue, then
runs the normal safe promotion/question/review pipeline.

It does not auto-promote sensitive/legal candidates.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.story_candidate_harvest import (
    _candidate_id,
    _canonical_url,
    _ensure_schema,
)
from tools.director_v05.story_candidate_triage import triage_candidates
from tools.director_v05.story_review_assistant import run_review_assistant
from tools.director_v05.story_to_trivia_factory import run_story_to_trivia_factory


LOW_SIGNAL = (
    "fantasy football",
    "power rankings",
    "mock draft",
    "betting",
    "odds",
    "where to watch",
    "how to watch",
    "ticket terms",
    "news roundup",
    "schedule",
    "projections",
    "ranking 32",
    "rankings, week",
    "top 100 players",
)

SENSITIVE = (
    "arrest",
    "arrested",
    "charged",
    "indicted",
    "investigation",
    "investigating",
    "suspended",
    "suspension",
    "fined",
    " fine ",
    "lawsuit",
    "allegation",
    "accuse",
    "accused",
    "discipline",
    "domestic violence",
    "misconduct",
)

RULE = (
    "rule",
    "rules",
    "penalty",
    "kickoff",
    "overtime",
    "targeting",
    "onside",
    "taunting",
    "replay",
    "roughing",
    "tush push",
)

CELEBRATION = (
    "celebration",
    "celebrates",
    "celebrate",
    "dance",
    "dancing",
    "taunt",
    "mascot",
    " fan ",
    " fans ",
    "crowd",
    "sideline celebration",
    "viral celebration",
)

ODDITY = (
    "hard knocks",
    "bizarre",
    "weird",
    "unusual",
    "funny",
    "viral",
    "prank",
    "costume",
    "social media",
    "off-field",
    "off field",
    "tattoo",
    "wedding",
    "retirement",
    "retires",
    " retire ",
    "mic'd up",
    "mic’d up",
    "behind the scenes",
)

PRESS = (
    "press conference",
    "news conference",
    "postgame",
    "media availability",
    "reporters",
    "says",
    " said ",
    "explains",
    "admits",
    "believes",
    "expects",
    "wants",
    " calls ",
    "dismisses",
    "responds",
    "reacts",
    "laments",
    "confident",
    "hoping",
    " feels ",
    " thinks ",
    "on future",
    "on loss",
    "on win",
    "on return",
)


def classify(title: str):
    text = " " + re.sub(r"\s+", " ", html.unescape(title)).casefold() + " "
    if any(term in text for term in LOW_SIGNAL):
        return None
    if any(term in text for term in SENSITIVE):
        return "DISCIPLINE_LEGAL", 1
    if any(term in text for term in RULE):
        return "RULE_ODDITY", 0
    if any(term in text for term in CELEBRATION):
        return "CELEBRATION_FAN", 0
    if any(term in text for term in ODDITY):
        return "OFF_FIELD_ODDITY", 0
    if (
        "'" in title
        or '"' in title
        or "‘" in title
        or "’" in title
        or any(term in text for term in PRESS)
    ):
        return "PRESS_CONFERENCE", 0
    return None


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or self._href is None:
            return
        text = re.sub(r"\s+", " ", "".join(self._text)).strip()
        if text:
            self.links.append((self._href, text))
        self._href = None
        self._text = []


def fetch(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Reads-Football-Story-Archive/1.0",
            "Accept": "text/html,application/xml,application/rss+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def insert_candidate(
    conn,
    *,
    url: str,
    title: str,
    domain: str,
    family: str,
    sensitive: int,
    seen_date: str | None,
    query_text: str,
):
    url = _canonical_url(url)
    cid = _candidate_id(url)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO football_story_candidates(
           candidate_id,source_url,title,domain,seen_date,language,source_country,
           family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
           first_harvested_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(source_url) DO UPDATE SET
             title=excluded.title,
             seen_date=COALESCE(
               excluded.seen_date,
               football_story_candidates.seen_date
             ),
             last_seen_at=excluded.last_seen_at""",
        (
            cid,
            url,
            title,
            domain,
            seen_date,
            "English",
            "United States",
            family,
            query_text,
            "PRIMARY",
            int(sensitive),
            "REVIEW_REQUIRED_SENSITIVE" if sensitive else "REVIEW_PRIORITY",
            now,
            now,
        ),
    )
    return cid


def main():
    conn = engine_bootstrap.connect()
    conn.execute("PRAGMA busy_timeout=30000")
    _ensure_schema(conn)

    metrics = {
        "nfl_pages": 0,
        "nfl_classified_links": 0,
        "nfl_inserted": 0,
        "ncaa_items": 0,
        "ncaa_inserted": 0,
        "failures": [],
    }
    seen_urls = set()

    # Four seasons of NFL.com's official archive is already thousands of
    # potential primary-source story headlines while keeping this first run
    # reasonably bounded.
    today = dt.date.today()
    for year in range(2023, today.year + 1):
        end_month = today.month if year == today.year else 12
        for month in range(1, end_month + 1):
            page = f"https://www.nfl.com/sitemap/html/articles/{year}/{month}"
            try:
                parser = LinkParser()
                parser.feed(fetch(page).decode("utf-8", "replace"))
                metrics["nfl_pages"] += 1

                for href, title in parser.links:
                    url = urllib.parse.urljoin("https://www.nfl.com", href)
                    if "/news/" not in url:
                        continue
                    if url in seen_urls:
                        continue
                    classified = classify(title)
                    if not classified:
                        continue

                    family, sensitive = classified
                    seen_urls.add(url)
                    insert_candidate(
                        conn,
                        url=url,
                        title=title,
                        domain="nfl.com",
                        family=family,
                        sensitive=sensitive,
                        seen_date=f"{year:04d}{month:02d}01",
                        query_text="NFL_OFFICIAL_SITEMAP",
                    )
                    metrics["nfl_classified_links"] += 1
                    metrics["nfl_inserted"] += 1

                # Commit monthly so a later source failure never discards
                # already collected official archive rows.
                conn.commit()
            except Exception as exc:
                metrics["failures"].append(
                    {
                        "source": page,
                        "reason": type(exc).__name__ + ":" + str(exc),
                    }
                )

    feeds = (
        ("FBS", "https://www.ncaa.com/news/football/fbs/rss.xml"),
        ("FCS", "https://www.ncaa.com/news/football/fcs/rss.xml"),
        ("DII", "https://www.ncaa.com/news/football/d2/rss.xml"),
        ("DIII", "https://www.ncaa.com/news/football/d3/rss.xml"),
    )

    for division, url in feeds:
        try:
            root = ET.fromstring(fetch(url))
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not link or link in seen_urls:
                    continue

                metrics["ncaa_items"] += 1
                classified = classify(title)
                if not classified:
                    lowered = title.casefold()
                    if any(
                        term in lowered
                        for term in (
                            "history",
                            "milestone",
                            "transfer",
                            "heisman",
                            "record",
                            "overtime",
                            "first ",
                            "longest",
                            "championship",
                        )
                    ):
                        classified = ("OFF_FIELD_ODDITY", 0)
                    else:
                        continue

                family, sensitive = classified
                pub = (item.findtext("pubDate") or "").strip()
                seen_date = None
                if pub:
                    try:
                        parsed = email.utils.parsedate_to_datetime(pub)
                        seen_date = parsed.strftime("%Y%m%d")
                    except Exception:
                        pass

                seen_urls.add(link)
                insert_candidate(
                    conn,
                    url=link,
                    title=title,
                    domain="ncaa.com",
                    family=family,
                    sensitive=sensitive,
                    seen_date=seen_date,
                    query_text=f"NCAA_{division}_RSS",
                )
                metrics["ncaa_inserted"] += 1

            conn.commit()
        except Exception as exc:
            metrics["failures"].append(
                {
                    "source": url,
                    "reason": type(exc).__name__ + ":" + str(exc),
                }
            )

    conn.close()

    # Use the normal production gates after source-native collection.
    # Factory first preserves the explicit PRIMARY review priority inserted
    # above; triage then organizes whatever remains.
    factory = run_story_to_trivia_factory(limit=150)
    triage = triage_candidates(minimum_priority_score=30)
    review = run_review_assistant(limit=400, include_sensitive=True)

    conn = engine_bootstrap.connect()
    counts = {
        row["status"]: int(row["n"])
        for row in conn.execute(
            """SELECT status,COUNT(*) n
               FROM football_story_candidates
               GROUP BY status"""
        ).fetchall()
    }
    total = sum(counts.values())
    if conn.execute(
        """SELECT 1 FROM sqlite_master
           WHERE type='table' AND name='story_generated_questions'"""
    ).fetchone():
        question_total = int(
            conn.execute(
                "SELECT COUNT(*) FROM story_generated_questions"
            ).fetchone()[0]
        )
    else:
        question_total = 0
    conn.close()

    print(
        json.dumps(
            {
                "metrics": metrics,
                "candidate_total": total,
                "candidate_status": counts,
                "factory": factory,
                "triage": triage,
                "review_assistant": review,
                "question_total": question_total,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
