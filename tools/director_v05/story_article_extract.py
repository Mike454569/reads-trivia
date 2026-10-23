"""Safe article extraction for story-to-trivia promotion.

Only approved domains are fetchable. Redirects must remain on an approved
domain. Extraction is intentionally small: metadata plus paragraph text needed
for evidence checks, never a permanent full-article archive.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

# Avoid importing the harvesting module here: it imports the full engine,
# which is expensive and unnecessary for individual article fetch workers.
# Keep this list aligned with the harvester's approved-domain policy.
APPROVED_DOMAINS = (
    "nfl.com", "espn.com", "cbssports.com", "foxsports.com",
    "si.com", "ncaa.org", "sports.yahoo.com", "usatoday.com",
)

MAX_RESPONSE_BYTES = 1_500_000
MAX_TEXT_CHARS = 18_000
TIMEOUT_SECONDS = 20


def _host(url):
    return (urlparse(str(url)).hostname or "").casefold().removeprefix("www.")


class _ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_p = False
        self.in_script = False
        self.in_style = False
        self.parts = []
        self.meta = {}
        self.jsonld = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "p":
            self.in_p = True
        elif tag == "script":
            self.in_script = True
            self._script_type = str(attrs.get("type") or "").casefold()
            self._script_buf = []
        elif tag == "style":
            self.in_style = True
        elif tag == "meta":
            key = str(attrs.get("property") or attrs.get("name") or "").casefold()
            value = str(attrs.get("content") or "").strip()
            if key and value:
                self.meta[key] = value

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_p = False
            self.parts.append("\n")
        elif tag == "script":
            if getattr(self, "_script_type", "") == "application/ld+json":
                raw = "".join(getattr(self, "_script_buf", []))
                if raw.strip():
                    self.jsonld.append(raw)
            self.in_script = False
        elif tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_script:
            self._script_buf.append(data)
        elif self.in_p and not self.in_style:
            self.parts.append(data)


def _clean(text):
    text = html.unescape(str(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _jsonld_articles(raw_blobs):
    out = []
    for raw in raw_blobs:
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        stack = parsed if isinstance(parsed, list) else [parsed]
        while stack:
            item = stack.pop()
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            if isinstance(graph, list):
                stack.extend(graph)
            typ = item.get("@type")
            types = set(typ if isinstance(typ, list) else [typ])
            if types & {"Article", "NewsArticle", "ReportageNewsArticle", "SportsEvent"}:
                out.append(item)
    return out


def fetch_article(url, *, timeout=TIMEOUT_SECONDS):
    """Fetch in a killable child process with a hard, total deadline.

    DNS lookups and some native TLS/network calls cannot be reliably
    interrupted by Python SIGALRM. subprocess.run(timeout=...) kills and
    reaps the child, even if it is blocked in a native library. No network
    operation or HTML parsing occurs in the caller's process.
    """
    if _host(url) not in APPROVED_DOMAINS:
        raise ValueError("ARTICLE_DOMAIN_NOT_APPROVED")
    deadline = max(1.0, float(timeout))
    argv = [
        sys.executable, "-m", "tools.director_v05.story_article_extract",
        "--fetch-worker", str(url), str(deadline),
    ]
    try:
        result = subprocess.run(
            argv, capture_output=True, text=True, timeout=deadline + 1.0,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("ARTICLE_TOTAL_FETCH_DEADLINE") from exc
    if result.returncode != 0:
        detail = result.stderr.strip()[-300:] or "WORKER_FAILED"
        raise ValueError("ARTICLE_WORKER_FAILED:" + detail)
    try:
        payload = json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise ValueError("ARTICLE_WORKER_INVALID_JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
        raise ValueError("ARTICLE_WORKER_INVALID_RESULT")
    return payload

def _fetch_article_impl(url, *, timeout=TIMEOUT_SECONDS):
    requested_host = _host(url)
    if requested_host not in APPROVED_DOMAINS:
        raise ValueError("ARTICLE_DOMAIN_NOT_APPROVED")

    req = urllib.request.Request(
        str(url),
        headers={
            "User-Agent": "Reads-Football-Lore-Review/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final_url = resp.geturl()
        final_host = _host(final_url)
        if final_host not in APPROVED_DOMAINS:
            raise ValueError("ARTICLE_REDIRECT_LEFT_APPROVED_DOMAINS")
        content_type = str(resp.headers.get("Content-Type") or "").casefold()
        if "html" not in content_type:
            raise ValueError("ARTICLE_NOT_HTML")
        raw = resp.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("ARTICLE_TOO_LARGE")

    text = raw.decode("utf-8", errors="replace")
    parser = _ArticleParser()
    parser.feed(text)
    paragraphs = _clean("".join(parser.parts))[:MAX_TEXT_CHARS]
    structured = _jsonld_articles(parser.jsonld)

    headline = parser.meta.get("og:title") or parser.meta.get("twitter:title")
    description = (
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
    )
    published = (
        parser.meta.get("article:published_time")
        or parser.meta.get("date")
        or parser.meta.get("datepublished")
    )
    article_body = None
    author = None
    for item in structured:
        headline = headline or item.get("headline") or item.get("name")
        description = description or item.get("description")
        article_body = article_body or item.get("articleBody")
        published = published or item.get("datePublished")
        author = author or item.get("author")

    body = _clean(article_body) if article_body else paragraphs
    if len(body) < 250:
        raise ValueError("ARTICLE_TEXT_TOO_THIN")

    return {
        "requested_url": str(url),
        "final_url": final_url,
        "domain": final_host,
        "headline": _clean(headline),
        "description": _clean(description),
        "published": _clean(published),
        "author": author,
        "text": body[:MAX_TEXT_CHARS],
        "text_chars": min(len(body), MAX_TEXT_CHARS),
    }


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "--fetch-worker":
        raise SystemExit("Usage: python -m tools.director_v05.story_article_extract --fetch-worker URL TIMEOUT")
    try:
        article = _fetch_article_impl(sys.argv[2], timeout=float(sys.argv[3]))
    except Exception as exc:
        print(type(exc).__name__ + ":" + str(exc)[:240], file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(article, ensure_ascii=False))
