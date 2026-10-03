import sqlite3

from tools.director_v05.reviewed_story_corpus import REVIEWED_CORPUS, ingest_reviewed_corpus
from tools.director_v05.universal_schema import install


def _conn_with_all_subjects():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    install(c)
    c.execute("""CREATE TABLE canonical_players(
        player_id TEXT PRIMARY KEY, display_name TEXT
    )""")
    c.execute("""CREATE TABLE canonical_coaches(
        coach_id TEXT PRIMARY KEY, display_name TEXT
    )""")

    seen = set()
    for i, story in enumerate(REVIEWED_CORPUS, start=1):
        key = (story["subject_type"], story["subject_label"])
        if key in seen:
            continue
        seen.add(key)
        if story["subject_type"] == "NFL_PLAYER":
            c.execute(
                "INSERT INTO canonical_players VALUES(?,?)",
                ("player-" + str(i), story["subject_label"]),
            )
        elif story["subject_type"] == "COACH":
            c.execute(
                "INSERT INTO canonical_coaches VALUES(?,?)",
                ("coach-" + str(i), story["subject_label"]),
            )
        else:
            raise AssertionError("unexpected corpus subject type: " + story["subject_type"])
    return c


def test_full_reviewed_corpus_passes_ingestion_contract():
    c = _conn_with_all_subjects()
    out = ingest_reviewed_corpus(c)
    assert out["attempted"] == len(REVIEWED_CORPUS)
    assert out["inserted"] == len(REVIEWED_CORPUS)
    assert out["rejected"] == []
    assert c.execute("SELECT COUNT(*) FROM universal_event").fetchone()[0] == len(REVIEWED_CORPUS)


def test_corpus_has_both_press_and_off_field_depth():
    types = [x["event_type"] for x in REVIEWED_CORPUS]
    assert types.count("PRESS_CONFERENCE") >= 8
    assert types.count("OFF_FIELD_ODDITY") >= 5


def test_every_reviewed_story_has_stable_id_and_reviewed_source():
    ids = [x["event_id"] for x in REVIEWED_CORPUS]
    assert len(ids) == len(set(ids))
    for story in REVIEWED_CORPUS:
        assert story["source_url"].startswith("https://")
        assert story["evidence_tier"] in {"PRIMARY", "REPUTABLE_MEDIA"}
        assert story["neutral_summary"].strip()
        assert story["subject_label"].strip()
