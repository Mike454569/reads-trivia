"""Conservative canonical subject matching for harvested football stories."""
from __future__ import annotations

import re
from collections import defaultdict


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _cols(conn, table):
    return {r[1] for r in conn.execute("PRAGMA table_info(" + table + ")")}


ENTITY_SOURCES = {
    "NFL_PLAYER": (
        ("canonical_players", "player_id", ("display_name", "player_name", "name")),
    ),
    "CFB_PLAYER": (
        ("canonical_cfb_players", "cfb_player_id", ("display_name", "player_name", "name")),
        ("cfb_players_canonical", "cfb_player_id", ("display_name", "player_name", "name")),
    ),
    "COACH": (
        ("canonical_coaches", "coach_id", ("display_name", "coach_name", "name")),
        ("coach_team_seasons", "coach_id", ("coach_name",)),
    ),
    "NFL_TEAM": (
        ("team_aliases", "team_code", ("full_name",)),
        ("nfl_teams", "team_code", ("team_name", "display_name", "full_name", "name")),
    ),
    "SCHOOL": (
        ("schools", "school_id", ("school_name", "display_name", "name")),
        ("cfb_schools", "school_id", ("school_name", "display_name", "name")),
    ),
}

STOP_LABELS = {
    "football", "college football", "nfl", "ncaa", "coach", "player",
}


def _norm(value):
    return " ".join(re.sub(r"[^a-z0-9' -]+", " ", str(value).casefold()).split())


def build_subject_index(conn):
    tables = _tables(conn)
    label_map = defaultdict(set)
    display = {}

    for entity_type, sources in ENTITY_SOURCES.items():
        for table, id_col, label_cols in sources:
            if table not in tables:
                continue
            cols = _cols(conn, table)
            if id_col not in cols:
                continue
            usable = [c for c in label_cols if c in cols]
            if not usable:
                continue
            sql = "SELECT " + id_col + "," + ",".join(usable) + " FROM " + table
            for row in conn.execute(sql):
                entity_id = row[0]
                if entity_id is None:
                    continue
                for idx in range(1, len(usable) + 1):
                    value = row[idx]
                    label = str(value or "").strip()
                    norm = _norm(label)
                    if len(norm) < 5 or norm in STOP_LABELS:
                        continue
                    key = (entity_type, str(entity_id))
                    label_map[norm].add(key)
                    display[key] = label
                    break

    # Only exact labels mapping to one entity are eligible for auto-promotion.
    unique = {
        label: next(iter(ids))
        for label, ids in label_map.items()
        if len(ids) == 1
    }
    return {"labels": unique, "display": display}


def match_subjects(index, *, title, text, max_matches=8):
    norm_title = _norm(title)
    norm_text = _norm(text)
    matches = []

    # Longer labels first prevents a short alias from crowding out a full name.
    for label in sorted(index["labels"], key=len, reverse=True):
        in_title = bool(re.search(r"(?<![a-z0-9])" + re.escape(label) + r"(?![a-z0-9])", norm_title))
        in_text = bool(re.search(r"(?<![a-z0-9])" + re.escape(label) + r"(?![a-z0-9])", norm_text))
        if not in_title and not in_text:
            continue
        entity_type, entity_id = index["labels"][label]
        matches.append({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "label": index["display"].get((entity_type, entity_id), label),
            "in_title": in_title,
            "in_text": in_text,
            "label_chars": len(label),
        })
        if len(matches) >= int(max_matches):
            break

    return matches


def primary_identity_match(matches):
    """One clear person identity is required for automatic story questions."""
    people = [
        m for m in matches
        if m["entity_type"] in {"NFL_PLAYER", "CFB_PLAYER", "COACH"}
        and m["in_text"]
    ]
    title_people = [m for m in people if m["in_title"]]
    if len(title_people) == 1:
        return title_people[0]
    if len(people) == 1:
        return people[0]
    return None
