import sqlite3

from tools.director_v05 import cfb_story_candidate_harvest as harvest
from tools.director_v05.story_candidate_harvest import _ensure_schema


def _connect_factory(path):
    def _connect():
        c = sqlite3.connect(path)
        c.row_factory = sqlite3.Row
        return c
    return _connect


def test_school_names_use_canonical_school_table(tmp_path):
    path = str(tmp_path / "cfb.sqlite")
    c = _connect_factory(path)()
    c.execute("CREATE TABLE schools(name TEXT)")
    c.executemany(
        "INSERT INTO schools(name) VALUES(?)",
        [("Alabama",), ("Auburn",), ("Georgia",), ("Alabama",)],
    )
    c.commit()
    names = harvest._school_names(c, limit=10)
    c.close()
    assert names == ["Alabama", "Auburn", "Georgia"]


def test_cfb_harvest_marks_candidates_as_cfb_sourced_and_review_only(
    tmp_path, monkeypatch
):
    path = str(tmp_path / "cfb.sqlite")
    c = _connect_factory(path)()
    _ensure_schema(c)
    c.execute("CREATE TABLE schools(name TEXT)")
    c.execute("INSERT INTO schools(name) VALUES('Alabama')")
    c.commit()
    c.close()

    monkeypatch.setattr(
        harvest.engine_bootstrap,
        "connect",
        _connect_factory(path),
    )

    counter = {"n": 0}
    def fake_fetch(query, **kwargs):
        counter["n"] += 1
        domain = "ncaa.org"
        if "domainis:espn.com" in query:
            domain = "espn.com"
        elif "domainis:cbssports.com" in query:
            domain = "cbssports.com"
        elif "domainis:foxsports.com" in query:
            domain = "foxsports.com"
        elif "domainis:si.com" in query:
            domain = "si.com"
        elif "domainis:usatoday.com" in query:
            domain = "usatoday.com"
        return {
            "articles": [{
                "url": f"https://{domain}/story-{counter['n']}",
                "title": f"College football story {counter['n']}",
                "seendate": "20261003T120000Z",
                "language": "English",
                "sourcecountry": "United States",
            }]
        }

    monkeypatch.setattr(harvest, "_fetch", fake_fetch)
    monkeypatch.setattr(harvest.time, "sleep", lambda *_: None)

    out = harvest.harvest_cfb_story_candidates(
        max_records_per_query=1,
        timespan="1y",
        school_limit=1,
        school_query_limit=1,
        sleep_seconds=0,
    )
    assert out["metrics"]["accepted_candidates"] > 0
    assert out["school_names_used"] == 1

    c = _connect_factory(path)()
    rows = c.execute(
        """SELECT query_text,status,sensitive_hint
           FROM football_story_candidates"""
    ).fetchall()
    c.close()
    assert rows
    assert all(str(r["query_text"]).startswith("CFB:") for r in rows)
    assert all(r["status"] == "REVIEW_REQUIRED" for r in rows)
    assert any(int(r["sensitive_hint"]) == 1 for r in rows)
