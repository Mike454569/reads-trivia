"""Director v0.8 -- Visual Template Registry (v1.8, Part E), extended by the
Reusable Game Format System pass, and extended AGAIN by the 40-Format
Expansion pass into the real, fuller FORMAT registry that pass's own spec
asks for (format_id/display_name/mechanic_family/supported_entity_types/
required_data_relationships/min_pool_size/nfl_support/cfb_support/
difficulty_support/timed/multiplayer_compatible/scoring_model/
validation_rules/answer_schema/generation_schema/qa_requirements/
casual_aliases, on top of the fields the Reusable Game Format System pass
already established).

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
`app.js`/`engine-game-ui.js` for the real renderer functions named in each
entry's own `renderer`/`existing_renderer_note` field.

Every `GeneratedGamePackage` question carries `visual_template` (a key into
this registry) and `visual_payload` (arbitrary JSON matching that template's
`payload_schema`, or None for templates that need none) -- see
`tools/game_director_v01.py`'s `generate_package_from_spec()` and
`tools/quiz_export/contract.py`'s OPTIONAL_KEYS. The Mechanic Pilot
taxonomies (MATCHING/SORTING_TIMELINE/HIGHER_LOWER_STREAK/
ELIMINATION_SURVIVAL/COMPARISON_BRACKET, plus the 40-Format Expansion pass's
new taxonomies) do NOT flow through that exact field today -- they're a
separate architecture (mechanic_engine.py's own client_safe_view()) -- so
their format entries below carry `existing_renderer_note` instead of a
`visual_payload`-shaped `payload_schema`, and format SELECTION for them is
threaded through gateway/services/creator.py (see FORMAT_COMPATIBILITY
below), not this module's `visual_template` field.

`production_status` (40-Format Expansion pass): a real 5-value taxonomy,
replacing the prior 2-value `PRODUCTION_READY|NEW_THIS_PASS` enum now that
TIMELINE_RIBBON/BRACKET_TREE are proven, shipped, and no longer "new":
    PRODUCTION_READY          -- generation + renderer + answer-checking +
                                  validation all real and verified; no
                                  placeholder content anywhere.
    BETA                      -- real generation/renderer/answer-checking
                                  work, but a disclosed limitation (thin
                                  pool, single league, or an unhardened
                                  trust boundary) not yet resolved.
    SUPPORTED_WITH_LIMITATIONS -- real and shippable, but permanently
                                  scoped down vs. the ideal shape because
                                  the underlying data itself is limited
                                  (e.g. no true depth-chart rank column).
    BLOCKED_DATA              -- the format cannot honestly ship because
                                  required data is missing or uncertified.
    BLOCKED_RENDERER          -- generation/data is real but no frontend
                                  renderer exists yet.

`nfl_support`/`cfb_support` reuse the EXACT existing Creator capability
status vocabulary (SUPPORTED | SUPPORTED_WITH_LIMITATIONS | MISSING_DATA |
UNKNOWN | FORMAT_INCOMPATIBLE) -- see feasibility.py -- so a format's
per-league readiness is expressed the same way a capability's already is,
never a second, format-specific vocabulary.
"""
from __future__ import annotations

VISUAL_TEMPLATE_REGISTRY: dict[str, dict] = {
    "DEFAULT_MULTIPLE_CHOICE": {
        "format_id": "DEFAULT_MULTIPLE_CHOICE",
        "display_name": "Multiple Choice",
        "description": "A single question sentence with 4 answer buttons -- the pre-v1.8 implicit "
                        "rendering every existing mode (Draft, Championship) already uses.",
        "payload_schema": None,
        "renderer": "renderDefaultMultipleChoice (app.js / engine-game-ui.js)",
        "proven_in": ["draft_guess", "championship_guess"],
        "supported_mechanics": ["guess"],
        "mechanic_family": "guess",
        "supported_entity_types": ["player", "team", "coach", "season"],
        "required_data_relationships": ["any registered 'guess' capability's own candidate table(s)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["easy", "medium", "hard", "any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "BINARY",
        "interaction_model": "Tap one of 4 buttons.",
        "validation_rules": "Answer must equal the adapter's private options[correctIndex]; distractors "
                             "come from the same adapter's real candidate pool, never invented.",
        "answer_schema": "{game_id, answer: <chosen option label, exact string match>}",
        "generation_schema": "tools/game_director_v01.py:generate_package_from_spec()",
        "qa_requirements": "QA_CHECKS_PERFORMED_V02 (registry.py) -- duplicate/missing-answer checks.",
        "casual_aliases": [],
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "POSITION_LINEUP": {
        "format_id": "POSITION_LINEUP",
        "display_name": "Position Lineup Board",
        "description": "A football position-lineup board (QB/RB/WR/WR/TE/OL x5) instead of a sentence, "
                        "with the same 4-option guess-the-team answer contract underneath.",
        "payload_schema": {
            "positions": "list[{position: str, name: str, starts: int}], in board display order",
            "season": "int",
        },
        "renderer": "renderPositionLineup (engine-game-ui.js)",
        "proven_in": ["nfl_offense_lineup_guess"],
        "supported_mechanics": ["guess"],
        "mechanic_family": "guess",
        "supported_entity_types": ["team", "season"],
        "required_data_relationships": ["canonical_roster_seasons (starts-based single-starter proxy)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["easy", "medium", "hard", "any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "BINARY",
        "interaction_model": "View a real lineup board, tap one of 4 team-name buttons.",
        "validation_rules": "Board is a real (season, team) starts-based lineup; no fabricated slot filled "
                             "when real data is absent (slot omitted, never guessed).",
        "answer_schema": "{game_id, answer: <chosen team label>}",
        "generation_schema": "tools/quiz_export/adapters/lineup.py",
        "qa_requirements": "QA_CHECKS_PERFORMED_V02 (registry.py).",
        "casual_aliases": [],
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "POSITION_LINEUP_COLLEGE": {
        "format_id": "POSITION_LINEUP_COLLEGE",
        "display_name": "Position Lineup Board (by College)",
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
        "mechanic_family": "guess",
        "supported_entity_types": ["team", "season"],
        "required_data_relationships": ["canonical_roster_seasons", "nfl_players_draft.college"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["easy", "medium", "hard", "any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "BINARY",
        "interaction_model": "View a real college-lineup board, tap one of 4 team-name buttons.",
        "validation_rules": "Skill positions only; no OL row (real, disclosed data limit).",
        "answer_schema": "{game_id, answer: <chosen team label>}",
        "generation_schema": "tools/quiz_export/adapters/lineup_college.py",
        "qa_requirements": "QA_CHECKS_PERFORMED_V02 (registry.py).",
        "casual_aliases": [],
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    # --- Reusable Game Format System pass: formats built that pass ---
    "SORT_LIST_DEFAULT": {
        "format_id": "SORT_LIST_DEFAULT",
        "display_name": "Sort List",
        "description": "The Mechanic Pilot shell's own current generic rendering for a SORTING_TIMELINE "
                        "round: a real vertical list of shuffled items, reorder them, submit.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'sorting' kind (engine-game-ui.js) -- "
                                   "TIMELINE_RIBBON below is a genuine visual alternative, both backed by "
                                   "the identical real SORTING_TIMELINE mechanic/data.",
        "proven_in": ["NFL_DRAFT_PICK_ORDER", "CFB_HEISMAN_YEAR_ORDER"],
        "supported_mechanics": ["sorting"],
        "mechanic_family": "sorting",
        "supported_entity_types": ["player", "team", "season"],
        "required_data_relationships": ["any registered SORTING_TIMELINE variant's real ordered dataset"],
        "min_items": 4, "max_items": 6, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "WEIGHTED",
        "interaction_model": "Reorder a vertical list, submit.",
        "validation_rules": "Submitted order compared against the private real correct order; "
                             "correct_positions/exact_match reported, never a fabricated 'close enough'.",
        "answer_schema": "{order: list[item_id]}",
        "generation_schema": "tools/director_v04/sorting.py:generate_sorting_round()",
        "qa_requirements": "No duplicate item_ids; real, verified chronological/ranked order.",
        "casual_aliases": ["put these in order", "sort these"],
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "TIMELINE_RIBBON": {
        "format_id": "TIMELINE_RIBBON",
        "display_name": "Timeline Ribbon",
        "description": "A horizontal, tap-to-reorder ribbon of real, date-stamped items the player puts "
                        "into chronological order -- generic over whatever real SORTING_TIMELINE variant "
                        "produced the items (NFL draft-pick order, Heisman winner year order, and any "
                        "future sortable domain, e.g. a real transfer/coaching timeline).",
        "payload_schema": {
            "ordered_items": "list[{item_id: str, label: str}], in CURRENT (shuffled/reordered) display order",
            "round_index": "int", "round_count": "int",
        },
        "existing_renderer_note": "No standalone render function exists -- the real ribbon UI is an "
                                   "inline branch inside renderMechanicPilotBody's 'sorting' kind "
                                   "(engine-game-ui.js, gated on client state s.sortFormat==='TIMELINE_RIBBON'), "
                                   "not a separate function. Corrected during the 40-Format Expansion pass "
                                   "-- this entry previously claimed a nonexistent renderTimelineRibbon().",
        "proven_in": ["NFL_DRAFT_PICK_ORDER", "CFB_HEISMAN_YEAR_ORDER"],
        "supported_mechanics": ["sorting"],
        "mechanic_family": "sorting",
        "supported_entity_types": ["player", "team", "season"],
        "required_data_relationships": ["any registered SORTING_TIMELINE variant's real ordered dataset"],
        "min_items": 4, "max_items": 6, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "WEIGHTED",
        "interaction_model": "Tap two cards to swap their position (no drag-only interaction, per mobile "
                              "rule: tap-to-swap works with one thumb, never requires a sustained drag).",
        "validation_rules": "Identical to SORT_LIST_DEFAULT -- same real order, same private answer key; "
                             "this format only changes presentation, never the underlying data/mechanic.",
        "answer_schema": "{order: list[item_id]}",
        "generation_schema": "tools/director_v04/sorting.py:generate_sorting_round()",
        "qa_requirements": "No duplicate item_ids; real, verified chronological/ranked order.",
        "casual_aliases": ["timeline", "put these on a timeline"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "BRACKET_TREE": {
        "format_id": "BRACKET_TREE",
        "display_name": "Bracket Tree",
        "description": "A real single-elimination bracket the player predicts matchup by matchup -- "
                        "generic over whatever real COMPARISON_BRACKET variant produced the entrants "
                        "(NFL/CFB team-season real win totals today; any future tie-free comparable real "
                        "attribute could back a new variant). The renderer itself has no hardcoded bracket "
                        "size (verified directly against engine-game-ui.js during the 40-Format Expansion "
                        "pass) -- KNOCKOUT_TOURNAMENT reuses it for a variable-size field.",
        "payload_schema": {
            "rounds": "list[{round_index, round_label, matchups: list[{match_id, entrant_a, entrant_b, "
                      "your_pick?, real_winner?, correct?}]}]",
            "picks_made": "int", "total_matchups": "int", "correct_count": "int", "completed": "bool",
        },
        "renderer": "renderBracketTreeBody(v, s) (engine-game-ui.js:1318)",
        "proven_in": ["NFL_TEAM_SEASON_WINS_BRACKET", "CFB_TEAM_SEASON_WINS_BRACKET"],
        "supported_mechanics": ["comparison"],
        "mechanic_family": "comparison",
        "supported_entity_types": ["team", "season"],
        "required_data_relationships": ["any registered COMPARISON_BRACKET variant's real, tie-free attribute"],
        "min_items": 8, "max_items": 8, "min_pool_size": 8,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "BINARY",
        "interaction_model": "Round-by-round mobile paging (never a full zoomed tree); tap one of 2 real "
                              "entrant names per matchup to predict the winner, revealed immediately.",
        "validation_rules": "Every matchup's real winner is pre-determined at generation time from a real, "
                             "tie-free attribute -- never computed/invented at request time.",
        "answer_schema": "{match_id, predicted_winner}",
        "generation_schema": "tools/director_v04/comparison.py:build_package()",
        "qa_requirements": "Bracket entrants real and distinct; no bye/placeholder entrant.",
        "casual_aliases": ["bracket", "make a bracket"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    # --- Registered/generalized: real, already-existing renderers, given a
    # real format identity so Creator can reason about them the same way as
    # the newer formats above. No rendering code changed for these three. ---
    "GUESS_LADDER": {
        "format_id": "GUESS_LADDER",
        "display_name": "Guess Ladder",
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
        "mechanic_family": "client_higher_lower",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["static client-side data file (real, disclosed architectural gap)"],
        "min_items": 8, "max_items": None, "min_pool_size": 8,
        "nfl_support": "SUPPORTED_WITH_LIMITATIONS", "cfb_support": "SUPPORTED_WITH_LIMITATIONS",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "STREAK",
        "interaction_model": "Tap Higher or Lower against the next real value.",
        "validation_rules": "Client-side only -- real values, but not server-authoritative (disclosed).",
        "answer_schema": "n/a (client-side)",
        "generation_schema": "tools/director_v04/higher_lower.py (client-side data file)",
        "qa_requirements": "n/a (client-side)",
        "casual_aliases": [],
        "mobile_verified": True, "creator_selectable": False, "production_status": "SUPPORTED_WITH_LIMITATIONS",
    },
    "HEAD_TO_HEAD": {
        "format_id": "HEAD_TO_HEAD",
        "display_name": "Head to Head",
        "description": "Two real entities side by side; tap one. Matches the workbook's own Head-to-Head "
                        "Split Screen concept.",
        "payload_schema": None,
        "existing_renderer_note": "renderBinaryChoiceHtml (app.js:257) is a real, already-generic 2-card "
                                   "component -- currently has exactly one call site (a real 2-option "
                                   "`guess` question in the Engine Pilot shell). Not yet reused by "
                                   "Higher/Lower or the Mechanic Pilot's own higher_lower kind, each of "
                                   "which still renders its own separate hand-built compare markup -- a "
                                   "real, disclosed consolidation opportunity, not attempted this pass to "
                                   "avoid regressing either already-shipped mode. HEAD_TO_HEAD_DUEL (the "
                                   "new generic format, 40-Format Expansion pass) reuses this same "
                                   "component directly.",
        "proven_in": ["guess (2-option questions, engine-game-ui.js)"],
        # Deliberately does NOT list "higher_lower"/"client_higher_lower"
        # here despite the note above -- neither actually renders through
        # this component today ("proven, not aspirational" discipline);
        # consolidating them onto it is real future work, not a current fact.
        "supported_mechanics": ["guess"],
        "mechanic_family": "guess",
        "supported_entity_types": ["player", "team", "season", "coach"],
        "required_data_relationships": ["any registered 2-option 'guess' capability's own candidate table(s)"],
        "min_items": 2, "max_items": 2, "min_pool_size": 2,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "BINARY",
        "interaction_model": "Tap one of 2 side-by-side cards.",
        "validation_rules": "Real 2-option comparison; the losing side is a real, verified value, never invented.",
        "answer_schema": "{game_id, answer: <chosen side's label>}",
        "generation_schema": "tools/game_director_v01.py:generate_package_from_spec() (2-option guess capabilities)",
        "qa_requirements": "QA_CHECKS_PERFORMED_V02 (registry.py).",
        "casual_aliases": [],
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "GRID_BOARD": {
        "format_id": "GRID_BOARD",
        "display_name": "Grid Board (Immaculate Grid)",
        "description": "A 3x3 (or up to 4x4) grid where row/column headers are real categories and the "
                        "player fills cells with a matching real answer. Matches the workbook's own Grid "
                        "Board concept exactly (NFL/CFB Immaculate Grid already ship this).",
        "payload_schema": None,
        "existing_renderer_note": "renderGridBoard (NFL) / renderCfbGridBoard (CFB), both in app.js, are "
                                   "fully duplicated per-league implementations over an already-generic "
                                   "rows/cols/cells shape -- real, disclosed de-duplication opportunity, "
                                   "not attempted this pass. CONFIRMED fully client-side (submitGridGuess() "
                                   "does a local static-array lookup, no server submit endpoint at all) -- "
                                   "this is NOT the template CONNECTION_GRID (the new, server-authoritative "
                                   "format) follows; CONNECTION_GRID is a deliberately distinct, new "
                                   "server-authoritative taxonomy, never routed through this client-side path.",
        "proven_in": ["grid (NFL Immaculate Grid)", "cfbGrid (CFB Immaculate Grid)"],
        # Deliberately NOT "matching" -- Immaculate Grid is its own separate,
        # bespoke pipeline (never routes through mechanic_engine.py's real
        # MATCHING taxonomy/generate_matching_round()), and its rows/cols/
        # cells payload is structurally incompatible with that taxonomy's
        # real left_items/right_items shape. A distinct mechanic id keeps
        # auto-selection/compatibility checks from ever treating the two as
        # interchangeable just because both are conceptually "matching."
        "supported_mechanics": ["grid_matching"],
        "mechanic_family": "grid_matching",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["static client-side data file (real, disclosed architectural gap)"],
        "min_items": 9, "max_items": 16, "min_pool_size": 9,
        "nfl_support": "SUPPORTED_WITH_LIMITATIONS", "cfb_support": "SUPPORTED_WITH_LIMITATIONS",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "BINARY",
        "interaction_model": "Tap a cell, then tap a real matching answer from a candidate list.",
        "validation_rules": "Client-side only -- real player data, but not server-authoritative (disclosed).",
        "answer_schema": "n/a (client-side)",
        "generation_schema": "app.js's static GRID_PLAYERS data array",
        "qa_requirements": "n/a (client-side)",
        "casual_aliases": [],
        "mobile_verified": True, "creator_selectable": False, "production_status": "SUPPORTED_WITH_LIMITATIONS",
    },
    # --- Minimal "default" entries for the 3 Mechanic Pilot kinds that have
    # no distinctly-branded existing format yet (unlike GUESS_LADDER/
    # GRID_BOARD/CARD_STACK above, each of which names a real, mature,
    # separately-shipped mode) -- registered so the compatibility matrix
    # never reports these real, working mechanics as format-incompatible. ---
    "MATCH_LIST_DEFAULT": {
        "format_id": "MATCH_LIST_DEFAULT",
        "display_name": "Match List",
        "description": "The Mechanic Pilot shell's own current generic rendering for a MATCHING round: "
                        "two columns of real items, tap one from each side to pair them.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'matching' kind (engine-game-ui.js).",
        "proven_in": ["NFL_DRAFT_CLASS_MATCH", "CFB_HEISMAN_SCHOOL_MATCH"],
        "supported_mechanics": ["matching"],
        "mechanic_family": "matching",
        "supported_entity_types": ["player", "team", "school"],
        "required_data_relationships": ["any registered MATCHING variant's real left/right item pairs"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "WEIGHTED",
        "interaction_model": "Tap a left item, then tap its matching right item.",
        "validation_rules": "Submitted mapping checked pair-by-pair against a private, real answer key.",
        "answer_schema": "{mapping: {left_item_id: right_item_id}}",
        "generation_schema": "tools/director_v04/matching.py:generate_matching_round()",
        "qa_requirements": "No duplicate left/right item_ids; every pair independently real and verified.",
        "casual_aliases": ["match these up", "pair these"],
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "COMPARE_CARD_DEFAULT": {
        "format_id": "COMPARE_CARD_DEFAULT",
        "display_name": "Compare Card",
        "description": "The Mechanic Pilot shell's own current generic rendering for a HIGHER_LOWER_STREAK "
                        "round: the current real item vs. the next one, guess higher or lower.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'higher_lower' kind (engine-game-ui.js) -- its "
                                   "own separate hand-built compare markup, not yet HEAD_TO_HEAD (see above).",
        "proven_in": ["NFL_TEAM_SEASON_WINS", "CFB_TEAM_SEASON_WINS"],
        "supported_mechanics": ["higher_lower"],
        "mechanic_family": "higher_lower",
        "supported_entity_types": ["player", "team", "season"],
        "required_data_relationships": ["any registered HIGHER_LOWER_STREAK variant's real ordered sequence"],
        "min_items": 8, "max_items": None, "min_pool_size": 8,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "STREAK",
        "interaction_model": "Tap Higher or Lower against the next real value.",
        "validation_rules": "Real, hidden next value revealed only after a guess; one miss ends the run.",
        "answer_schema": "{guess: 'higher'|'lower'}",
        "generation_schema": "tools/director_v04/higher_lower.py:generate_higher_lower_round() (server variant)",
        "qa_requirements": "Sequence values real and distinct enough to avoid ties at the compare boundary.",
        "casual_aliases": [],
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "SURVIVAL_PROMPT_DEFAULT": {
        "format_id": "SURVIVAL_PROMPT_DEFAULT",
        "display_name": "Survival Prompt",
        "description": "The Mechanic Pilot shell's own current generic rendering for an ELIMINATION_SURVIVAL "
                        "round: a real True/False membership prompt, one miss ends the run.",
        "payload_schema": None,
        "existing_renderer_note": "renderMechanicPilotBody's 'elimination' kind (engine-game-ui.js).",
        "proven_in": ["NFL_SUPER_BOWL_CHAMPION_SURVIVAL", "CFB_NATIONAL_CHAMPION_SURVIVAL"],
        "supported_mechanics": ["elimination"],
        "mechanic_family": "elimination",
        "supported_entity_types": ["team", "season"],
        "required_data_relationships": ["any registered ELIMINATION_SURVIVAL variant's real membership set"],
        "min_items": 8, "max_items": None, "min_pool_size": 8,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "STREAK",
        "interaction_model": "Tap True or False for the current real prompt.",
        "validation_rules": "Membership is a real, verified fact (never an invented negative); one miss ends the run.",
        "answer_schema": "{guess: true|false}",
        "generation_schema": "tools/director_v04/elimination.py:generate_elimination_round()",
        "qa_requirements": "Every prompt's real membership independently verified before publishing.",
        "casual_aliases": [],
        "mobile_verified": False, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    "CARD_STACK": {
        "format_id": "CARD_STACK",
        "display_name": "Card Stack",
        "description": "A vertical stack of progressively-revealed real clue cards; guess the identity "
                        "before the stack runs out. Matches the workbook's own Card Stack Progressive Clue "
                        "concept exactly (Player From Clues / Who Am I already ships this).",
        "payload_schema": None,
        "existing_renderer_note": "app.js's Player From Clues (NFL/CFB) and Silhouette modes each "
                                   "duplicate this same real progressive-clue shape independently -- real, "
                                   "disclosed de-duplication opportunity, not attempted this pass.",
        "proven_in": ["playerClues (NFL Player From Clues)", "cfbPlayerClues (CFB Player From Clues)"],
        "supported_mechanics": ["clue"],
        "mechanic_family": "identify_player_from_clues",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["player_from_clues.py / cfb_player_from_clues.py's real candidate pools"],
        "min_items": 3, "max_items": 5, "min_pool_size": 50,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "WEIGHTED",
        "interaction_model": "Tap to reveal the next clue, or submit a guess at any point.",
        "validation_rules": "Every clue independently verified to monotonically narrow a real candidate "
                             "universe to exactly one target; no leaked name substring.",
        "answer_schema": "{guess: <free-text player name>}",
        "generation_schema": "tools/director_v04/player_from_clues.py / cfb_player_from_clues.py",
        "qa_requirements": "Candidate-narrowing chain independently recomputed and checked for contiguity.",
        "casual_aliases": ["who am i", "guess the player from clues"],
        "mobile_verified": True, "creator_selectable": False, "production_status": "PRODUCTION_READY",
    },
    # --- 40-Format Expansion pass: 6 new backend taxonomies (mechanic_engine.py),
    # each with a real, live-verified generator (tools/director_v04/) and
    # real answer-checking -- but NO frontend renderer wiring was built this
    # pass (a new client-side mode-config entry in engine-game-ui.js's
    # ENGINE_MECHANIC_MODES is required even where an existing renderer
    # FUNCTION could technically be reused, e.g. KNOCKOUT_BRACKET's view
    # shape is byte-identical to COMPARISON_BRACKET's). Honestly marked
    # BLOCKED_RENDERER, never claimed PRODUCTION_READY without a real,
    # reachable player-facing UI -- per this pass's own explicit "choose
    # accuracy over completeness" standard. Reachable today via the admin
    # Creator/mechanics API for real JSON package inspection, not by a
    # player through the app. ---
    "CONNECTION_GRID": {
        "format_id": "CONNECTION_GRID", "display_name": "Connection Grid",
        "description": "A 3x3 grid where each cell's real answer must satisfy both a row and a column "
                        "criterion (e.g. drafted in Round 1 x played for the Cowboys). Server-authoritative: "
                        "every submitted name is checked live against the real database, never a "
                        "precomputed client-visible answer key.",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- see tools/director_v04/"
                                   "grid_constraint.py for the real, tested backend (generation + live "
                                   "per-cell answer verification, confirmed against real data).",
        "proven_in": [], "supported_mechanics": ["grid_constraint_board"],
        "mechanic_family": "GRID_CONSTRAINT_BOARD",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["draft_facts", "canonical_roster_seasons"],
        "min_items": 9, "max_items": 9, "min_pool_size": 1,
        "nfl_support": "SUPPORTED", "cfb_support": "UNKNOWN",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Type a real name for each of 9 cells; checked live against the database.",
        "validation_rules": "Every cell verified to have >=1 real candidate at generation time; every "
                             "submitted answer re-verified live, never against a precomputed key.",
        "answer_schema": "{row_index, col_index, guess: <free-text name>}",
        "generation_schema": "tools/director_v04/grid_constraint.py:build_package()",
        "qa_requirements": "Live per-cell COUNT() verification before publishing; no cell with 0 real candidates.",
        "casual_aliases": ["connection grid", "3x3 grid trivia"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "PERFECT_DRIVE": {
        "format_id": "PERFECT_DRIVE", "display_name": "Perfect Drive",
        "description": "A field-progression game: correct answers (from any existing, real 'guess' "
                        "capability) gain real yardage toward the end zone, keyed to each question's own "
                        "already-computed difficulty. One wrong answer ends the drive.",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- see tools/director_v04/"
                                   "drive_progression.py for the real, tested backend (YARDAGE mode).",
        "proven_in": [], "supported_mechanics": ["drive_progression"],
        "mechanic_family": "DRIVE_PROGRESSION",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["any registered 'guess' capability's own real question pool"],
        "min_items": 1, "max_items": 25, "min_pool_size": 10,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "PROGRESSION",
        "interaction_model": "Answer real questions; correct answers gain real yardage.",
        "validation_rules": "Every question is a real, already-QA'd question from a registered capability; "
                             "yardage-per-difficulty is a disclosed fixed scale, never fabricated per question.",
        "answer_schema": "{answer: <chosen option label>}",
        "generation_schema": "tools/director_v04/drive_progression.py:build_package(mode='YARDAGE')",
        "qa_requirements": "Inherits the underlying capability's own real QA pipeline unchanged.",
        "casual_aliases": ["perfect drive", "drive down the field"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "GOAL_LINE_STAND": {
        "format_id": "GOAL_LINE_STAND", "display_name": "Goal Line Stand",
        "description": "A fixed number of downs (default 4) to score; each wrong answer costs a down. "
                        "Questions are real, drawn from any existing registered 'guess' capability.",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- see tools/director_v04/"
                                   "drive_progression.py for the real, tested backend (DOWNS mode).",
        "proven_in": [], "supported_mechanics": ["drive_progression"],
        "mechanic_family": "DRIVE_PROGRESSION",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["any registered 'guess' capability's own real question pool"],
        "min_items": 1, "max_items": 10, "min_pool_size": 10,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "PROGRESSION",
        "interaction_model": "Answer real questions; a wrong answer costs one of a fixed number of downs.",
        "validation_rules": "Same real question source/QA as PERFECT_DRIVE; downs_total is a disclosed "
                             "fixed constant (default 4), never fabricated.",
        "answer_schema": "{answer: <chosen option label>}",
        "generation_schema": "tools/director_v04/drive_progression.py:build_package(mode='DOWNS')",
        "qa_requirements": "Inherits the underlying capability's own real QA pipeline unchanged.",
        "casual_aliases": ["goal line stand", "four downs"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "LINEUP_BUILDER": {
        "format_id": "LINEUP_BUILDER", "display_name": "Lineup Builder",
        "description": "Construct a themed real lineup (e.g. a 2010s all-decade offense) one real, "
                        "eligible, not-yet-picked player per slot -- a construction exercise, never a "
                        "scored 'best lineup' claim (no ranking model backs this variant).",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- see tools/director_v04/"
                                   "roster_build.py for the real, tested backend (NFL_2010S_OFFENSE_BUILDER).",
        "proven_in": [], "supported_mechanics": ["roster_build"],
        "mechanic_family": "ROSTER_BUILD",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons"],
        "min_items": 6, "max_items": 6, "min_pool_size": 100,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Pick one real, eligible, not-yet-drafted player per real roster slot.",
        "validation_rules": "Every pick checked against the real, live eligible pool for its slot; no "
                             "player draftable twice.",
        "answer_schema": "{player_id}",
        "generation_schema": "tools/director_v04/roster_build.py:build_package('NFL_2010S_OFFENSE_BUILDER')",
        "qa_requirements": "Refuses to generate if any required position (QB/RB/WR/TE) has zero real candidates.",
        "casual_aliases": ["build an offense", "lineup builder"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "AUCTION_DRAFT": {
        "format_id": "AUCTION_DRAFT", "display_name": "Auction Draft",
        "description": "Build a real roster under a fixed FICTIONAL budget, where every player's cost is "
                        "their real career-average annual contract value (nfl_player_contracts). The "
                        "budget itself is fictional; every dollar figure backing a cost is real.",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- see tools/director_v04/"
                                   "roster_build.py for the real, tested backend (NFL_AUCTION_DRAFT), "
                                   "including a real, verified live budget-affordability check.",
        "proven_in": [], "supported_mechanics": ["roster_build"],
        "mechanic_family": "ROSTER_BUILD",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["nfl_player_contracts", "canonical_players"],
        "min_items": 6, "max_items": 6, "min_pool_size": 80,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WAGER",
        "interaction_model": "Pick one real, eligible, affordable, not-yet-drafted player per real roster slot.",
        "validation_rules": "Every pick checked against real remaining budget (fictional total, real "
                             "per-player cost) before being accepted -- confirmed live during this pass "
                             "(a real over-budget pick was correctly rejected).",
        "answer_schema": "{player_id}",
        "generation_schema": "tools/director_v04/roster_build.py:build_package('NFL_AUCTION_DRAFT')",
        "qa_requirements": "Refuses to generate if any required position has zero real, resolved-contract candidates.",
        "casual_aliases": ["auction draft", "give everyone a budget"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "CAP_CHALLENGE": {
        "format_id": "CAP_CHALLENGE", "display_name": "Cap Challenge",
        "description": "The same real budget-constrained roster build as AUCTION_DRAFT, framed as "
                        "optimization under a cap rather than bidding -- identical real mechanic/data, "
                        "different presentation framing only.",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- shares AUCTION_DRAFT's real, "
                                   "tested backend (tools/director_v04/roster_build.py, NFL_AUCTION_DRAFT).",
        "proven_in": [], "supported_mechanics": ["roster_build"],
        "mechanic_family": "ROSTER_BUILD",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["nfl_player_contracts", "canonical_players"],
        "min_items": 6, "max_items": 6, "min_pool_size": 80,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WAGER",
        "interaction_model": "Same as AUCTION_DRAFT -- pick real, eligible, affordable players per slot.",
        "validation_rules": "Identical to AUCTION_DRAFT.",
        "answer_schema": "{player_id}",
        "generation_schema": "tools/director_v04/roster_build.py:build_package('NFL_AUCTION_DRAFT')",
        "qa_requirements": "Identical to AUCTION_DRAFT.",
        "casual_aliases": ["salary cap challenge", "cap challenge"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "KNOCKOUT_TOURNAMENT": {
        "format_id": "KNOCKOUT_TOURNAMENT", "display_name": "Knockout Tournament",
        "description": "A real single-elimination field (4, 8, or 16 real team-seasons) -- generalizes "
                        "BRACKET_TREE to a variable field size using a standard, real tournament reseeding "
                        "algorithm, same real win-total data source.",
        "payload_schema": {
            "rounds": "list[{round_index, round_label, matchups: list[{match_id, entrant_a, entrant_b, "
                      "your_pick?, real_winner?, correct?}]}]",
            "picks_made": "int", "total_matchups": "int", "correct_count": "int", "completed": "bool",
        },
        "existing_renderer_note": "The view shape is byte-identical to BRACKET_TREE's (confirmed during "
                                   "this pass -- both flow through the same _comparison_client_view()/"
                                   "_comparison_evaluate() functions), so renderBracketTreeBody(v, s) "
                                   "(engine-game-ui.js:1318) would work UNCHANGED if wired up -- but no new "
                                   "client-side mode-config entry (ENGINE_MECHANIC_MODES) was added this "
                                   "pass, so it is not yet reachable by a real player.",
        "proven_in": [], "supported_mechanics": ["knockout_bracket"],
        "mechanic_family": "KNOCKOUT_BRACKET",
        "supported_entity_types": ["team", "season"],
        "required_data_relationships": ["season_standings", "cfb_standings"],
        "min_items": 4, "max_items": 16, "min_pool_size": 16,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Same as BRACKET_TREE -- tap a real entrant name per matchup.",
        "validation_rules": "Every matchup's real winner fully determined at generation time from a real, "
                             "tie-free win total; standard recursive reseeding algorithm, not fabricated pairing.",
        "answer_schema": "{match_id, predicted_winner}",
        "generation_schema": "tools/director_v04/knockout_bracket.py:build_package()",
        "qa_requirements": "Refuses to generate if fewer than the required real, tie-free entrants exist.",
        "casual_aliases": ["knockout tournament", "elimination bracket"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "SIX_DEGREES": {
        "format_id": "SIX_DEGREES", "display_name": "Six Degrees (Cross-League Chain)",
        "description": "A real, bounded 2-hop chain (real CFB school -> real player -> real NFL draft "
                        "team). Deliberately NOT the harder, unbounded live-pathfinding engine that already "
                        "exists as Coach Connections (gateway/services/coach_connections_graph.py, NFL-only, "
                        "a different, more general product) -- this is a distinct, narrower, cross-league "
                        "format slot.",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- see tools/director_v04/"
                                   "relationship_chain.py for the real, tested backend.",
        "proven_in": [], "supported_mechanics": ["relationship_chain"],
        "mechanic_family": "RELATIONSHIP_CHAIN",
        "supported_entity_types": ["school", "player", "team"],
        "required_data_relationships": ["cfb_nfl_identity_bridge_certified"],
        "min_items": 5, "max_items": 8, "min_pool_size": 5,
        "nfl_support": "SUPPORTED_WITH_LIMITATIONS", "cfb_support": "SUPPORTED_WITH_LIMITATIONS",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "See the start of a real chain, guess where it real-ly ends.",
        "validation_rules": "Every hop is a real, HIGH_CONFIDENCE-tier row from the certified bridge table; "
                             "no invented or inferred relationship.",
        "answer_schema": "{guess: <free-text end-node name>}",
        "generation_schema": "tools/director_v04/relationship_chain.py:build_package()",
        "qa_requirements": "Confidence-tier filtered; refuses to generate below MIN_CHAINS real chains.",
        "casual_aliases": ["six degrees", "connect these two players"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "CHAIN_REACTION": {
        "format_id": "CHAIN_REACTION", "display_name": "Chain Reaction",
        "description": "Shares SIX_DEGREES' real bounded 2-hop chain data/mechanic -- CHAIN_REACTION and "
                        "SIX_DEGREES are two format names over the identical real underlying chain shape "
                        "this pass, differing only in framing (start-to-end guess vs. link-by-link reveal).",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- shares SIX_DEGREES' real, "
                                   "tested backend (tools/director_v04/relationship_chain.py).",
        "proven_in": [], "supported_mechanics": ["relationship_chain"],
        "mechanic_family": "RELATIONSHIP_CHAIN",
        "supported_entity_types": ["school", "player", "team"],
        "required_data_relationships": ["cfb_nfl_identity_bridge_certified"],
        "min_items": 5, "max_items": 8, "min_pool_size": 5,
        "nfl_support": "SUPPORTED_WITH_LIMITATIONS", "cfb_support": "SUPPORTED_WITH_LIMITATIONS",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Same as SIX_DEGREES.",
        "validation_rules": "Identical to SIX_DEGREES.",
        "answer_schema": "{guess: <free-text end-node name>}",
        "generation_schema": "tools/director_v04/relationship_chain.py:build_package()",
        "qa_requirements": "Identical to SIX_DEGREES.",
        "casual_aliases": ["chain reaction"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
    "CHOOSE_YOUR_PATH": {
        "format_id": "CHOOSE_YOUR_PATH", "display_name": "Choose Your Path",
        "description": "A small, fixed, fully pre-validated real branch tree -- the player's choice at "
                        "each node picks which already-registered real 'guess' capability backs the next "
                        "real question. Never a general branching engine.",
        "payload_schema": None,
        "existing_renderer_note": "No frontend renderer built this pass -- see tools/director_v04/"
                                   "branch_state.py for the real, tested backend.",
        "proven_in": [], "supported_mechanics": ["branch_state"],
        "mechanic_family": "BRANCH_STATE",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["NFL_DRAFT", "NFL_CHAMPIONSHIP", "NFL_COACHING (already-registered capabilities)"],
        "min_items": 1, "max_items": 1, "min_pool_size": 1,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Pick a path at each node; answer the real question at the leaf.",
        "validation_rules": "Every leaf resolves to an already-registered, independently-certified real "
                             "capability -- the tree itself is fixed and pre-validated, never built at request time.",
        "answer_schema": "node stage: {choice_id}; leaf stage: {answer: <chosen option label>}",
        "generation_schema": "tools/director_v04/branch_state.py:build_package()",
        "qa_requirements": "Every leaf's question generated through the real, unchanged guess-mechanic pipeline.",
        "casual_aliases": ["choose your path"],
        "mobile_verified": False, "creator_selectable": True, "production_status": "BLOCKED_RENDERER",
    },
}

# Reusable Game Format System pass, Section 6: the real compatibility
# matrix -- which formats a given real mechanic can back, derived from each
# format's own `supported_mechanics` above (never hand-guessed a second
# time). Keyed by the SAME mechanic identifiers `mechanic_engine.py`'s
# TAXONOMY_IDS/`schema.py`'s ALLOWED_MECHANICS use (lowercase for the
# guess-family mechanics, matching schema.py; the Mechanic Pilot taxonomy
# names are their own real identifiers, already established elsewhere).
FORMAT_COMPATIBILITY: dict[str, list[str]] = {}
for _format_id, _entry in VISUAL_TEMPLATE_REGISTRY.items():
    for _mechanic in _entry.get("supported_mechanics", []):
        FORMAT_COMPATIBILITY.setdefault(_mechanic, []).append(_format_id)
del _format_id, _entry, _mechanic

PRODUCTION_STATUS_VALUES = frozenset({
    "PRODUCTION_READY", "BETA", "SUPPORTED_WITH_LIMITATIONS", "BLOCKED_DATA", "BLOCKED_RENDERER",
})


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
    format is registered before any newer alternative, so a caller
    that never requests a format keeps getting today's real, already-
    proven default rendering."""
    candidates = formats_for_mechanic(mechanic)
    return candidates[0] if candidates else None


def is_format_compatible(format_id: str, mechanic: str) -> bool:
    return format_id in formats_for_mechanic(mechanic)
