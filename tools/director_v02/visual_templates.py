"""Director v0.8 -- Visual Template Registry (v1.8, Part E).

Separate from the Mechanic Registry (mechanics.py) on purpose: a mechanic is
WHAT the player does (answer validation contract); a visual template is HOW
the puzzle is PRESENTED (what the frontend renders). Two capabilities can
share one mechanic while using different templates -- e.g. Draft and this
milestone's new lineup capability both use the `guess` mechanic's exact
4-option answer contract, but the lineup capability renders as a real
position-lineup board (`POSITION_LINEUP`) instead of a single-sentence
prompt (`DEFAULT_MULTIPLE_CHOICE`).

A template is only registered here once a real frontend renderer for its
`payload_schema` actually exists (same "proven, not aspirational" discipline
`registry.py`'s CAPABILITY_REGISTRY already documents) -- see
`app.js`/`engine-game-ui.js` for `renderVisualTemplate()`.

Every `GeneratedGamePackage` question carries `visual_template` (a key into
this registry) and `visual_payload` (arbitrary JSON matching that template's
`payload_schema`, or None for templates that need none) -- see
`tools/game_director_v01.py`'s `generate_package_from_spec()` and
`tools/quiz_export/contract.py`'s OPTIONAL_KEYS.
"""
from __future__ import annotations

VISUAL_TEMPLATE_REGISTRY: dict[str, dict] = {
    "DEFAULT_MULTIPLE_CHOICE": {
        "description": "A single question sentence with 4 answer buttons -- the pre-v1.8 implicit "
                        "rendering every existing mode (Draft, Championship) already uses.",
        "payload_schema": None,
        "renderer": "renderDefaultMultipleChoice (app.js / engine-game-ui.js)",
        "proven_in": ["draft_guess", "championship_guess"],
    },
    "POSITION_LINEUP": {
        "description": "A football position-lineup board (QB/RB/WR/WR/TE/OL x5) instead of a sentence, "
                        "with the same 4-option guess-the-team answer contract underneath.",
        "payload_schema": {
            "positions": "list[{position: str, name: str, starts: int}], in board display order",
            "season": "int",
        },
        "renderer": "renderPositionLineup (engine-game-ui.js)",
        "proven_in": ["nfl_offense_lineup_guess"],
    },
    "POSITION_LINEUP_COLLEGE": {
        "description": "The names-hidden sibling of POSITION_LINEUP: a 5-slot skill-position board (QB/RB/"
                        "WR/WR/TE only -- no OL row, see adapters/lineup_college.py for why) showing each "
                        "player's real COLLEGE instead of their name.",
        "payload_schema": {
            "positions": "list[{position: str, college: str}], in board display order, skill positions only",
            "season": "int",
        },
        "renderer": "renderPositionLineupCollegeBoard (engine-game-ui.js)",
        "proven_in": ["nfl_offense_lineup_college_guess"],
    },
}


def lookup(template_id: str) -> dict | None:
    return VISUAL_TEMPLATE_REGISTRY.get(template_id)


def all_template_ids() -> list[str]:
    return list(VISUAL_TEMPLATE_REGISTRY.keys())
