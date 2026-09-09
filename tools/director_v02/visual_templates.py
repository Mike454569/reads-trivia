"""Director v0.8 -- Visual Template Registry (v1.8, Part E), extended by the
Reusable Game Format System pass into the real FORMAT registry that pass's
own spec asks for.

Separate from the Mechanic Registry (mechanic_engine.py) on purpose: a
mechanic is WHAT the player does (answer validation contract); a FORMAT
(this module's own `visual_template` field, same concept, Reads' own prior
name for it) is HOW the puzzle is PRESENTED (what the frontend renders).
Two capabilities can share one mechanic while using different formats --
e.g. Draft and the lineup capability both use the `guess` mechanic's exact
4-option answer contract, but the lineup capability renders as a real
position-lineup board (`POSITION_LINEUP`) instead of a single-sentence
prompt (`DEFAULT_MULTIPLE_CHOICE`). Two different MECHANICS can also share
one format (`HEAD_TO_HEAD` backs both a 2-option `guess` question and the
`higher_lower` mechanic's own compare-and-decide moment).

A format is only registered here once a real frontend renderer for its
`payload_schema` actually exists (same "proven, not aspirational" discipline
`registry.py`'s CAPABILITY_REGISTRY already documents) -- see
`app.js`/`engine-game-ui.js` for `renderVisualTemplate()`/
`renderMechanicPilotBody()`.

Every `GeneratedGamePackage` question carries `visual_template` (a key into
this registry) and `visual_payload` (arbitrary JSON matching that template's
`payload_schema`, or None for templates that need none) -- see
`tools/game_director_v01.py`'s `generate_package_from_spec()` and
`tools/quiz_export/contract.py`'s OPTIONAL_KEYS. The 4 real Mechanic Pilot
taxonomies (MATCHING/SORTING_TIMELINE/HIGHER_LOWER_STREAK/
ELIMINATION_SURVIVAL, plus the new COMPARISON_BRACKET) do NOT flow through
that exact field today -- they're a separate architecture
(mechanic_engine.py's own client_safe_view()) -- so their format entries
below carry `existing_renderer_note` instead of a `visual_payload`-shaped
`payload_schema`, and format SELECTION for them is threaded through
gateway/services/creator.py (see FORMAT_COMPATIBILITY below), not this
module's `visual_template` field.

Reusable Game Format System pass, real audit finding: the workbook's own
GAME_LAYOUT_CATALOG (32 layout ideas) already self-classifies 4 as
"WORKING NOW" (an existing Reads mode already covers it) and 28 as
"PLANNED (concept only)". This registry only ever gains a NEW_THIS_PASS
entry once a real renderer/adapter/mechanic backs it end-to-end -- see
each entry's own `production_status` and the format inventory report this
pass produces for the full, honest classification of all 32.
"""
from __future__ import annotations

VISUAL_TEMPLATE_REGISTRY: dict[str, dict] = {
    "DEFAULT_MULTIPLE_CHOICE": {
        "description": "A single question sentence with 4 answer buttons -- the pre-v1.8 implicit "
                        "rendering every existing mode (Draft, Championship) already uses.",
        "payload_schema": None,
        "renderer": "renderDefaultMultipleChoice (app.js / engine-game-ui.js)",
        "proven_in": ["draft_guess", "championship_guess"],
        "supported_mechanics": ["guess"],
        "min_items": 4, "max_items": 4,
        "interaction_model": "Tap one of 4 buttons.",
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
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
        "supported_mechanics": ["guess"],
        "min_items": 4, "max_items": 4,
        "interaction_model": "View a real lineup board, tap one of 4 team-name buttons.",
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
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
        "supported_mechanics": ["guess"],
        "min_items": 4, "max_items": 4,
        "interaction_model": "View a real college-lineup board, tap one of 4 team-name buttons.",
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    # --- Reusable Game Format System pass: NEW formats, built this pass ---
    "SORT_LIST_DEFAULT": {
        "description": "The Mechanic Pilot shell's own current generic rendering for a SORTING_TIMELINE "
                        "round: a real vertical list of shuffled items, reorder them, submit.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'sorting' kind (engine-game-ui.js) -- the "
                                   "real predecessor TIMELINE_RIBBON below is a genuine visual alternative "
                                   "to, both backed by the identical real SORTING_TIMELINE mechanic/data.",
        "proven_in": ["NFL_DRAFT_PICK_ORDER", "CFB_HEISMAN_YEAR_ORDER"],
        "supported_mechanics": ["sorting"],
        "min_items": 4, "max_items": 6,
        "interaction_model": "Reorder a vertical list, submit.",
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "TIMELINE_RIBBON": {
        "description": "A horizontal, tap-to-reorder ribbon of real, date-stamped items the player puts "
                        "into chronological order -- generic over whatever real SORTING_TIMELINE variant "
                        "produced the items (NFL draft-pick order, Heisman winner year order, and any "
                        "future sortable domain, e.g. a real transfer/coaching timeline).",
        "payload_schema": {
            "ordered_items": "list[{item_id: str, label: str}], in CURRENT (shuffled/reordered) display order",
            "round_index": "int", "round_count": "int",
        },
        "renderer": "renderTimelineRibbon (engine-game-ui.js)",
        "proven_in": ["NFL_DRAFT_PICK_ORDER", "CFB_HEISMAN_YEAR_ORDER"],
        "supported_mechanics": ["sorting"],
        "min_items": 4, "max_items": 6,
        "interaction_model": "Tap two cards to swap their position (no drag-only interaction, per mobile "
                              "rule: tap-to-swap works with one thumb, never requires a sustained drag).",
        "mobile_verified": False, "creator_selectable": True, "production_status": "NEW_THIS_PASS",
    },
    "BRACKET_TREE": {
        "description": "A real 8-entry single-elimination bracket (quarterfinals/semifinals/final) the "
                        "player predicts matchup by matchup -- generic over whatever real COMPARISON_BRACKET "
                        "variant produced the entrants (NFL/CFB team-season real win totals today; any "
                        "future tie-free comparable real attribute could back a new variant).",
        "payload_schema": {
            "rounds": "list[{round_index, round_label, matchups: list[{match_id, entrant_a, entrant_b, "
                      "your_pick?, real_winner?, correct?}]}]",
            "picks_made": "int", "total_matchups": "int", "correct_count": "int", "completed": "bool",
        },
        "renderer": "renderBracketTree (engine-game-ui.js)",
        "proven_in": ["NFL_TEAM_SEASON_WINS_BRACKET", "CFB_TEAM_SEASON_WINS_BRACKET"],
        "supported_mechanics": ["comparison"],
        "min_items": 8, "max_items": 8,
        "interaction_model": "Round-by-round mobile paging (never a full zoomed tree); tap one of 2 real "
                              "entrant names per matchup to predict the winner, revealed immediately.",
        "mobile_verified": False, "creator_selectable": True, "production_status": "NEW_THIS_PASS",
    },
    # --- Registered/generalized: real, already-existing renderers, given a
    # real format identity for the first time so Creator can reason about
    # them the same way as the new formats above. No rendering code changed
    # for these three -- see each note for the real, distinct architecture
    # it actually lives in. ---
    "GUESS_LADDER": {
        "description": "A real streak/ladder: guess higher-or-lower against the next real value; one miss "
                        "ends the run. Matches the workbook's own Guess Ladder concept exactly.",
        "payload_schema": None,
        "existing_renderer_note": "app.js's standalone Higher or Lower mode -- entirely CLIENT-SIDE "
                                   "(every value already sits in a static data file before the guess is "
                                   "made; see tools/director_v04/higher_lower.py's own docstring for why "
                                   "that's a real, disclosed defect and NOT the same architecture as the "
                                   "server-authoritative 'higher_lower' mechanic). Deliberately a DISTINCT "
                                   "mechanic id below (never claimed compatible with the real server "
                                   "mechanic's payload) -- see COMPARE_CARD_DEFAULT for that real one.",
        "proven_in": ["higherLower (app.js, client-side only)"],
        "supported_mechanics": ["client_higher_lower"],
        "min_items": 8, "max_items": None,
        "interaction_model": "Tap Higher or Lower against the next real value.",
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "HEAD_TO_HEAD": {
        "description": "Two real entities side by side; tap one. Matches the workbook's own Head-to-Head "
                        "Split Screen concept.",
        "payload_schema": None,
        "existing_renderer_note": "renderBinaryChoiceHtml (app.js) is a real, already-generic 2-card "
                                   "component -- currently has exactly one call site (a real 2-option "
                                   "`guess` question in the Engine Pilot shell). Not yet reused by "
                                   "Higher/Lower or the Mechanic Pilot's own higher_lower kind, each of "
                                   "which still renders its own separate hand-built compare markup -- a "
                                   "real, disclosed consolidation opportunity, not attempted this pass to "
                                   "avoid regressing either already-shipped mode.",
        "proven_in": ["guess (2-option questions, engine-game-ui.js)"],
        # Deliberately does NOT list "higher_lower"/"client_higher_lower"
        # here despite the note above -- neither actually renders through
        # this component today ("proven, not aspirational" discipline);
        # consolidating them onto it is real future work, not a current fact.
        "supported_mechanics": ["guess"],
        "min_items": 2, "max_items": 2,
        "interaction_model": "Tap one of 2 side-by-side cards.",
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "GRID_BOARD": {
        "description": "A 3x3 (or up to 4x4) grid where row/column headers are real categories and the "
                        "player fills cells with a matching real answer. Matches the workbook's own Grid "
                        "Board concept exactly (NFL/CFB Immaculate Grid already ship this).",
        "payload_schema": None,
        "existing_renderer_note": "renderGridBoard (NFL) / renderCfbGridBoard (CFB), both in app.js, are "
                                   "fully duplicated per-league implementations over an already-generic "
                                   "rows/cols/cells shape -- real, disclosed de-duplication opportunity, "
                                   "not attempted this pass.",
        "proven_in": ["grid (NFL Immaculate Grid)", "cfbGrid (CFB Immaculate Grid)"],
        # Deliberately NOT "matching" -- Immaculate Grid is its own separate,
        # bespoke pipeline (never routes through mechanic_engine.py's real
        # MATCHING taxonomy/generate_matching_round()), and its rows/cols/
        # cells payload is structurally incompatible with that taxonomy's
        # real left_items/right_items shape. A distinct mechanic id keeps
        # auto-selection/compatibility checks from ever treating the two as
        # interchangeable just because both are conceptually "matching."
        "supported_mechanics": ["grid_matching"],
        "min_items": 9, "max_items": 16,
        "interaction_model": "Tap a cell, then tap a real matching answer from a candidate list.",
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    # --- Minimal "default" entries for the 3 Mechanic Pilot kinds that have
    # no distinctly-branded existing format yet (unlike GUESS_LADDER/
    # GRID_BOARD/CARD_STACK above, each of which names a real, mature,
    # separately-shipped mode) -- registered so the compatibility matrix
    # never reports these real, working mechanics as format-incompatible,
    # and so TIMELINE_RIBBON/a future MATCH format have a real predecessor
    # to be judged an alternative TO, honestly reflecting that these are
    # today's only real rendering for their mechanic (flag-off, pre-launch). ---
    "MATCH_LIST_DEFAULT": {
        "description": "The Mechanic Pilot shell's own current generic rendering for a MATCHING round: "
                        "two columns of real items, tap one from each side to pair them.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'matching' kind (engine-game-ui.js).",
        "proven_in": ["NFL_DRAFT_CLASS_MATCH", "CFB_HEISMAN_SCHOOL_MATCH"],
        "supported_mechanics": ["matching"],
        "min_items": 4, "max_items": 4,
        "interaction_model": "Tap a left item, then tap its matching right item.",
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "COMPARE_CARD_DEFAULT": {
        "description": "The Mechanic Pilot shell's own current generic rendering for a HIGHER_LOWER_STREAK "
                        "round: the current real item vs. the next one, guess higher or lower.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'higher_lower' kind (engine-game-ui.js) -- its "
                                   "own separate hand-built compare markup, not yet HEAD_TO_HEAD (see above).",
        "proven_in": ["NFL_TEAM_SEASON_WINS", "CFB_TEAM_SEASON_WINS"],
        "supported_mechanics": ["higher_lower"],
        "min_items": 8, "max_items": None,
        "interaction_model": "Tap Higher or Lower against the next real value.",
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "SURVIVAL_PROMPT_DEFAULT": {
        "description": "The Mechanic Pilot shell's own current generic rendering for an ELIMINATION_SURVIVAL "
                        "round: a real True/False membership prompt, one miss ends the run.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'elimination' kind (engine-game-ui.js).",
        "proven_in": ["NFL_SUPER_BOWL_CHAMPION_SURVIVAL", "CFB_NATIONAL_CHAMPION_SURVIVAL"],
        "supported_mechanics": ["elimination"],
        "min_items": 8, "max_items": None,
        "interaction_model": "Tap True or False for the current real prompt.",
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "CARD_STACK": {
        "description": "A vertical stack of progressively-revealed real clue cards; guess the identity "
                        "before the stack runs out. Matches the workbook's own Card Stack Progressive Clue "
                        "concept exactly (Player From Clues / Who Am I already ships this).",
        "payload_schema": None,
        "existing_renderer_note": "app.js's Player From Clues (NFL/CFB) and Silhouette modes each "
                                   "duplicate this same real progressive-clue shape independently -- real, "
                                   "disclosed de-duplication opportunity, not attempted this pass.",
        "proven_in": ["playerClues (NFL Player From Clues)", "cfbPlayerClues (CFB Player From Clues)"],
        "supported_mechanics": ["clue"],
        "min_items": 3, "max_items": 5,
        "interaction_model": "Tap to reveal the next clue, or submit a guess at any point.",
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
}

# Reusable Game Format System pass, Section 6: the real compatibility
# matrix -- which formats a given real mechanic can back, derived from each
# format's own `supported_mechanics` above (never hand-guessed a second
# time). Keyed by the SAME mechanic identifiers `mechanic_engine.py`'s
# TAXONOMY_IDS/`schema.py`'s ALLOWED_MECHANICS use (lowercase for the
# guess-family mechanics, matching schema.py; the 5 Mechanic Pilot taxonomy
# names are their own real identifiers, already established elsewhere).
FORMAT_COMPATIBILITY: dict[str, list[str]] = {}
for _format_id, _entry in VISUAL_TEMPLATE_REGISTRY.items():
    for _mechanic in _entry.get("supported_mechanics", []):
        FORMAT_COMPATIBILITY.setdefault(_mechanic, []).append(_format_id)
del _format_id, _entry, _mechanic


def lookup(template_id: str) -> dict | None:
    return VISUAL_TEMPLATE_REGISTRY.get(template_id)


def all_template_ids() -> list[str]:
    return list(VISUAL_TEMPLATE_REGISTRY.keys())


def formats_for_mechanic(mechanic: str) -> list[str]:
    """Real, derived compatibility lookup -- the list a Creator format
    selector or auto-selection routine should actually use, never a
    second hand-maintained mapping."""
    return list(FORMAT_COMPATIBILITY.get(mechanic, []))


def default_format_for_mechanic(mechanic: str) -> str | None:
    """Deterministic auto-selection (Reusable Game Format System pass,
    Section 9): the first real compatible format in registration order --
    documented, not random. Every mechanic's PRODUCTION_READY existing
    format is registered before any NEW_THIS_PASS alternative, so a caller
    that never requests a format keeps getting today's real, already-
    proven default rendering."""
    candidates = formats_for_mechanic(mechanic)
    return candidates[0] if candidates else None


def is_format_compatible(format_id: str, mechanic: str) -> bool:
    return format_id in formats_for_mechanic(mechanic)
