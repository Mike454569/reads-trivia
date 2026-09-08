"""Player Experience pass (Parts 8/9): the owner directly observed the
deployed Football 101 interface with "Show Responsibilities" enabled
rendering multiple overlapping paragraphs of assignment text around a
real formation.

Root cause, found by reading football-field.js's own
labelCollidesWithPlayer()/playerMarkerSVG() (the SVG diagram renderer):
each player's responsibility tag was placed by searching for a Y-offset
that avoided every PLAYER MARKER, but never checked against OTHER
RESPONSIBILITY TAGS already placed in the same render pass -- so a
tightly-packed real group (an offensive line: LT/LG/C/RG/RT, all within a
few units of each other, each with a real, independently-authored
assignment) could each individually clear every player marker while their
own tags overlapped each other.

This project has no JavaScript test runner (a plain static site, no build
step -- confirmed via package.json's own description) and no Node.js is
available in this environment, so this file re-implements the exact same
geometry (verified line-for-line against football-field.js at the time of
writing) in Python and runs it against the real diagram data every player
actually sees (data/football-diagrams.js) -- the same evidence-over-code-
inspection standard this project already applies everywhere else. If this
test ever starts failing, re-verify by reading football-field.js's own
current constants (CHAR_WIDTH_ESTIMATE, LABEL_LINE_HALF_HEIGHT,
PLAYER_VISUAL_FOOTPRINT_RADIUS, the candidates list, and the tag max
length) and update the Python mirror below to match, don't just relax the
assertion.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

CHAR_WIDTH_ESTIMATE = 1.35
LABEL_LINE_HALF_HEIGHT = 1.1
PLAYER_VISUAL_FOOTPRINT_RADIUS = 2.6
CANDIDATES = [6.5, 9, 11.5, 14, 16.5, 19, 21.5, -6.5, -9, -11.5, -14, -16.5, -19, -21.5]
MAX_TAG_LEN = 22

# The 9 diagrams this pass's own required QA list names, plus their real
# category/key path in data/football-diagrams.js.
NAMED_DIAGRAMS = {
    "Shotgun Trips": ("formations", "FORMATION_3X1_TRIPS"),
    "I-Formation": ("formations", "FORMATION_I_FORMATION"),
    "4-2-5": ("fronts", "DEFPERSONNEL_NICKEL_4_2_5"),
    "Cover 3": ("coverages", "COVER_3"),
    "Cover 4": ("coverages", "COVER_4"),
    "Mesh": ("passConcepts", "PASSCONCEPT_MESH"),
    "Four Verticals": ("passConcepts", "PASSCONCEPT_FOUR_VERTICALS"),
    "Inside Zone": ("runConcepts", "RUN_INSIDE_ZONE"),
    "Power": ("runConcepts", "RUN_POWER"),
}


@pytest.fixture(scope="module")
def diagrams_data() -> dict:
    path = REPO_ROOT / "data" / "football-diagrams.js"
    content = path.read_text()
    start = content.index("{")
    end = content.rindex("}")
    return json.loads(content[start:end + 1])


def _dist(ax, ay, bx, by):
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def _clamp_label_x(text: str, x: float) -> float:
    half = (len(text) * CHAR_WIDTH_ESTIMATE) / 2
    if x - half < 1:
        return half + 1
    if x + half > 99:
        return 99 - half
    return x


def _collides_with_player(x, y, players, exclude_id, half_w) -> bool:
    for pl in players:
        if pl["id"] == exclude_id:
            continue
        closest_x = max(x - half_w, min(pl["x"], x + half_w))
        closest_y = max(y - LABEL_LINE_HALF_HEIGHT, min(pl["y"], y + LABEL_LINE_HALF_HEIGHT))
        if _dist(closest_x, closest_y, pl["x"], pl["y"]) < PLAYER_VISUAL_FOOTPRINT_RADIUS:
            return True
    return False


def _collides_with_placed(x, y, half_w, placed) -> bool:
    for t in placed:
        if abs(x - t["x"]) < (half_w + t["halfWidth"] + 0.4) and abs(y - t["y"]) < (LABEL_LINE_HALF_HEIGHT * 2 + 0.2):
            return True
    return False


def simulate_tag_placements(players: list) -> list:
    """Mirrors football-field.js's playerMarkerSVG() responsibility-tag
    placement loop exactly (including the sibling-tag collision check
    this pass added). Returns the list of final placed tag rects."""
    real_players = [p for p in players if not p.get("ghost")]
    placed = []
    for p in players:
        if p.get("ghost") or not p.get("assignment"):
            continue
        assignment = p["assignment"]
        short = assignment if len(assignment) <= MAX_TAG_LEN else assignment[:MAX_TAG_LEN - 1] + "…"
        tag_x = _clamp_label_x(short, p["x"])
        half_w = (len(short) * CHAR_WIDTH_ESTIMATE) / 2
        tag_y_offset = 6.5
        for c in CANDIDATES:
            cy = p["y"] + c
            if cy < 1 or cy > 99:
                continue
            if _collides_with_player(tag_x, cy, real_players, p["id"], half_w):
                continue
            if _collides_with_placed(tag_x, cy, half_w, placed):
                continue
            tag_y_offset = c
            break
        placed.append({"x": tag_x, "y": p["y"] + tag_y_offset, "halfWidth": half_w, "id": p["id"]})
    return placed


def count_overlaps(placed: list) -> list:
    overlaps = []
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            a, b = placed[i], placed[j]
            if abs(a["x"] - b["x"]) < (a["halfWidth"] + b["halfWidth"]) and abs(a["y"] - b["y"]) < (LABEL_LINE_HALF_HEIGHT * 2):
                overlaps.append((a["id"], b["id"]))
    return overlaps


def test_football_field_js_still_has_the_sibling_tag_collision_check():
    """Structural guard against silently reverting the actual fix -- the
    real bug was that labelCollidesWithPlayer() never checked sibling
    tags at all; this asserts the new check is still wired into the
    placement loop, not just present somewhere in the file."""
    src = (REPO_ROOT / "football-field.js").read_text()
    assert "labelCollidesWithPlacedTags" in src
    assert re.search(r"placedTags\.push\(", src)


@pytest.mark.parametrize("name", list(NAMED_DIAGRAMS))
def test_named_diagram_has_zero_responsibility_tag_overlaps(name, diagrams_data):
    cat, key = NAMED_DIAGRAMS[name]
    diagram = diagrams_data[cat][key]
    placed = simulate_tag_placements(diagram["players"])
    overlaps = count_overlaps(placed)
    assert overlaps == [], f"{name}: real tag-vs-tag overlaps found: {overlaps}"


def test_every_real_diagram_in_the_app_has_zero_responsibility_tag_overlaps(diagrams_data):
    """Broader than the 9 explicitly named diagrams -- Part 1's own
    instruction is to eliminate the failure CLASS, not patch only the
    reported examples. Checks all 55 real diagrams currently in the app."""
    total_diagrams = 0
    all_overlaps = []
    for cat, items in diagrams_data.items():
        if not isinstance(items, dict):
            continue
        for key, diagram in items.items():
            players = diagram.get("players", [])
            if not players:
                continue
            total_diagrams += 1
            overlaps = count_overlaps(simulate_tag_placements(players))
            if overlaps:
                all_overlaps.append((diagram.get("display_name", key), overlaps))
    assert total_diagrams >= 50, f"only {total_diagrams} diagrams found -- did the data file move?"
    assert all_overlaps == [], f"real tag-vs-tag overlaps found: {all_overlaps}"


def test_before_the_fix_these_same_diagrams_really_did_overlap():
    """Proves the test harness itself is meaningful (not silently passing
    regardless of the algorithm) by re-running the OLD, pre-fix algorithm
    (no sibling-tag check, 8 candidates, 34-char tags) against a known-bad
    real diagram and confirming it really did produce real overlaps."""
    old_candidates = [6.5, 9, 11.5, 14, -6.5, -9, -11.5, -14]

    def simulate_old(players):
        real_players = [p for p in players if not p.get("ghost")]
        placed = []
        for p in players:
            if p.get("ghost") or not p.get("assignment"):
                continue
            assignment = p["assignment"]
            short = assignment if len(assignment) <= 34 else assignment[:33] + "…"
            tag_x = _clamp_label_x(short, p["x"])
            half_w = (len(short) * CHAR_WIDTH_ESTIMATE) / 2
            tag_y_offset = 6.5
            for c in old_candidates:
                cy = p["y"] + c
                if cy < 1 or cy > 99:
                    continue
                if _collides_with_player(tag_x, cy, real_players, p["id"], half_w):
                    continue
                tag_y_offset = c
                break
            placed.append({"x": tag_x, "y": p["y"] + tag_y_offset, "halfWidth": half_w, "id": p["id"]})
        return placed

    path = REPO_ROOT / "data" / "football-diagrams.js"
    content = path.read_text()
    start = content.index("{")
    end = content.rindex("}")
    data = json.loads(content[start:end + 1])
    diagram = data["formations"]["FORMATION_SHOTGUN"]
    overlaps = count_overlaps(simulate_old(diagram["players"]))
    assert len(overlaps) > 0, "the pre-fix algorithm should have shown real overlaps on Shotgun -- test harness may be wrong"
