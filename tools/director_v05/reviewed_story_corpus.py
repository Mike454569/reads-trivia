"""Reviewed seed corpus for press-conference and off-field football lore.

Every item here was manually reviewed against a primary or reputable-media
source before inclusion. Subject IDs are resolved at ingest time from canonical
Reads identity tables; unresolved names fail closed.
"""
from __future__ import annotations

from .reviewed_media_lore import ingest_reviewed_story


REVIEWED_CORPUS = [
    {
        "event_id":"reviewed_herm_edwards_play_to_win_2002",
        "event_type":"PRESS_CONFERENCE",
        "league":"NFL",
        "event_date":"2002-10-30",
        "title":"Herm Edwards' 'play to win the game' press conference",
        "neutral_summary":"Jets coach Herm Edwards delivered his famous postgame response about playing to win after New York fell to 2-5.",
        "source_url":"https://www.nfl.com/videos/this-day-in-history-new-york-jets-coach-herm-edwards-you-play-to-win-the--275209",
        "source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY",
        "subject_type":"COACH",
        "subject_label":"Herm Edwards",
        "tags":["press_conference","coach_quote","jets"],
    },
    {
        "event_id":"reviewed_belichick_on_to_cincinnati_2014",
        "event_type":"PRESS_CONFERENCE",
        "league":"NFL",
        "event_date":"2014-09-29",
        "title":"Bill Belichick repeatedly turns the page to Cincinnati",
        "neutral_summary":"After New England's blowout loss at Kansas City, Bill Belichick repeatedly redirected questions toward the Patriots' next opponent, Cincinnati.",
        "source_url":"https://www.nfl.com/news/belichick-i-could-have-said-on-to-cincinnati-103-times-0ap3000000520281",
        "source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY",
        "subject_type":"COACH",
        "subject_label":"Bill Belichick",
        "tags":["press_conference","patriots","on_to_cincinnati"],
    },
    {
        "event_id":"reviewed_marshawn_media_day_2015",
        "event_type":"PRESS_CONFERENCE",
        "league":"NFL",
        "event_date":"2015-01-27",
        "title":"Marshawn Lynch repeats one answer at Super Bowl media day",
        "neutral_summary":"At Super Bowl XLIX media day, Marshawn Lynch answered question after question with the same basic response while satisfying his media-availability requirement.",
        "source_url":"https://www.espn.com/nfl/playoffs/2014/story/_/id/12237417/marshawn-lynch-seattle-seahawks-uses-same-answer-repetition-super-bowl-media-day-here-get-fined",
        "source_publisher":"ESPN",
        "evidence_tier":"REPUTABLE_MEDIA",
        "subject_type":"NFL_PLAYER",
        "subject_label":"Marshawn Lynch",
        "tags":["press_conference","super_bowl","media_day"],
    },
    {
        "event_id":"reviewed_derek_anderson_mnf_2010",
        "event_type":"PRESS_CONFERENCE",
        "league":"NFL",
        "event_date":"2010-11-29",
        "title":"Derek Anderson walks out after Monday night postgame questions",
        "neutral_summary":"Cardinals quarterback Derek Anderson became angry when repeatedly questioned about a sideline laugh during a loss and ended the postgame news conference by walking out.",
        "source_url":"https://www.espn.com/nfl/news/story?id=5865332",
        "source_publisher":"ESPN",
        "evidence_tier":"REPUTABLE_MEDIA",
        "subject_type":"NFL_PLAYER",
        "subject_label":"Derek Anderson",
        "tags":["press_conference","cardinals","monday_night_football"],
    },
    {
        "event_id":"reviewed_terrell_owens_driveway_2005",
        "event_type":"OFF_FIELD_ODDITY",
        "league":"NFL",
        "event_date":"2005-08-10",
        "title":"Terrell Owens holds a driveway workout in front of reporters",
        "neutral_summary":"While suspended from Eagles training camp, Terrell Owens worked out and did situps outside his home while answering questions from gathered reporters.",
        "source_url":"https://www.espn.com/blog/nflnation/post/_/id/278059/celebrations-catches-and-controversy-terrell-owens-top-moments",
        "source_publisher":"ESPN",
        "evidence_tier":"REPUTABLE_MEDIA",
        "subject_type":"NFL_PLAYER",
        "subject_label":"Terrell Owens",
        "tags":["off_field","workout","eagles","media"],
    },
    {
        "event_id":"reviewed_joe_judge_clown_show_2022",
        "event_type":"PRESS_CONFERENCE",
        "league":"NFL",
        "event_date":"2022-01-02",
        "title":"Joe Judge delivers lengthy defense of Giants program",
        "neutral_summary":"After a loss in Chicago dropped New York to 4-12, Giants coach Joe Judge spent an extended postgame answer defending the program's culture and direction.",
        "source_url":"https://www.nfl.com/news/joe-judge-defends-tenure-after-giants-drop-to-4-12-this-ain-t-some-clown-show-or",
        "source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY",
        "subject_type":"COACH",
        "subject_label":"Joe Judge",
        "tags":["press_conference","giants","coach_rant"],
    },
    {
        "event_id":"reviewed_von_miller_belichick_impression_2018",
        "event_type":"PRESS_CONFERENCE",
        "league":"NFL",
        "event_date":"2018-11-25",
        "title":"Von Miller mimics Belichick's 'On to Cincinnati' routine",
        "neutral_summary":"After Denver beat Pittsburgh, Von Miller stayed in character through his postgame media session by repeatedly redirecting answers toward the Broncos' next opponent, Cincinnati.",
        "source_url":"https://www.nfl.com/news/von-miller-mimics-belichick-after-win-on-to-cincinnati-0ap3000000992773",
        "source_publisher":"NFL.com",
        "evidence_tier":"PRIMARY",
        "subject_type":"NFL_PLAYER",
        "subject_label":"Von Miller",
        "tags":["press_conference","broncos","impression"],
    },
    {
        "event_id":"reviewed_lane_kiffin_popcorn_2021",
        "event_type":"PRESS_CONFERENCE",
        "league":"CFB",
        "event_date":"2021-10-02",
        "title":"Lane Kiffin tells viewers to get their popcorn ready",
        "neutral_summary":"Before Ole Miss played Alabama, Lane Kiffin delivered a memorable pregame line about getting popcorn ready and later acknowledged the comment had not aged well after the loss.",
        "source_url":"https://www.espn.com/college-football/story/_/id/32854267/college-football-best-quotes-2021-lane-kiffin-brian-kelly",
        "source_publisher":"ESPN",
        "evidence_tier":"REPUTABLE_MEDIA",
        "subject_type":"COACH",
        "subject_label":"Lane Kiffin",
        "tags":["press_conference","ole_miss","alabama","pregame"],
    },
]


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _resolve_exact_subject(conn, subject_type, label):
    target = str(label).strip()
    tables = _tables(conn)

    candidates = {
        "NFL_PLAYER": [
            ("canonical_players","player_id",("display_name","player_name","name")),
        ],
        "CFB_PLAYER": [
            ("canonical_cfb_players","cfb_player_id",("display_name","player_name","name")),
            ("cfb_players_canonical","cfb_player_id",("display_name","player_name","name")),
        ],
        "COACH": [
            ("canonical_coaches","coach_id",("display_name","coach_name","name")),
            ("coach_team_seasons","coach_id",("coach_name",)),
        ],
    }.get(str(subject_type), [])

    matches = set()
    for table, id_col, label_cols in candidates:
        if table not in tables:
            continue
        cols = {r[1] for r in conn.execute("PRAGMA table_info(" + table + ")")}
        if id_col not in cols:
            continue
        for label_col in label_cols:
            if label_col not in cols:
                continue
            rows = conn.execute(
                f"SELECT {id_col} FROM {table} WHERE lower(trim({label_col}))=lower(trim(?))",
                (target,),
            ).fetchall()
            matches.update(str(r[0]) for r in rows if r[0] is not None)

    if len(matches) != 1:
        raise ValueError(
            "REVIEWED_CORPUS_SUBJECT_RESOLUTION_" +
            ("MISSING" if not matches else "AMBIGUOUS") +
            ":" + str(subject_type) + ":" + target
        )
    return next(iter(matches))


def ingest_reviewed_corpus(conn, stories=REVIEWED_CORPUS):
    inserted = 0
    rejected = []
    for story in stories:
        try:
            sid = _resolve_exact_subject(
                conn, story["subject_type"], story["subject_label"]
            )
            payload = {
                k:v for k,v in story.items()
                if k not in {"subject_type","subject_label"}
            }
            payload["subjects"] = [{
                "subject_type": story["subject_type"],
                "subject_id": sid,
                "role": "speaker" if story["event_type"] == "PRESS_CONFERENCE" else "subject",
            }]
            ingest_reviewed_story(conn, payload)
            inserted += 1
        except ValueError as exc:
            rejected.append({
                "event_id": story.get("event_id"),
                "subject_label": story.get("subject_label"),
                "reason": str(exc),
            })
    conn.commit()
    return {
        "attempted": len(stories),
        "inserted": inserted,
        "rejected": rejected,
    }
