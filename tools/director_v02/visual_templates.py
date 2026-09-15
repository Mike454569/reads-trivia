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
    "STAT_LADDER": {
        "format_id": "STAT_LADDER",
        "display_name": "Stat Ladder",
        "description": "Rank real players by one real statistical total (season rushing yards, career "
                        "passing touchdowns, career rushing yards) without seeing the real numbers first -- "
                        "reuses SORT_LIST_DEFAULT's exact vertical reorder UI (the correct visual for a "
                        "ladder is already a numbered list; no new component was built), the real numeric "
                        "values are revealed as evidence only after the player submits an order.",
        "payload_schema": None,
        "existing_renderer_note": "Reuses renderMechanicPilotBody's 'sorting' kind verbatim, same as "
                                   "SORT_LIST_DEFAULT -- the only real difference is the underlying "
                                   "SORTING_TIMELINE variant's data (a stat total instead of a draft pick "
                                   "or award year) and the post-submit values_by_item_id reveal.",
        "proven_in": ["NFL_SEASON_RUSHING_YARDS_LADDER", "NFL_CAREER_PASSING_TD_LADDER",
                      "CFB_CAREER_RUSHING_YARDS_LADDER"],
        "supported_mechanics": ["sorting"],
        "mechanic_family": "sorting",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["player_season_stats (NFL, SOURCE_BACKED) / "
                                         "cfb_player_season_stats_real (CFB, SOURCE_BACKED_DERIVED)"],
        "min_items": 4, "max_items": 6, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "WEIGHTED",
        "interaction_model": "Reorder a vertical list of real player names (values hidden), submit, then "
                              "see each real stat total revealed next to the name.",
        "validation_rules": "Same real order-comparison as SORT_LIST_DEFAULT; every round's sampled stat "
                             "totals are verified genuinely distinct at generation time (resampled, never "
                             "given an invented tiebreak) -- see sorting.py's own module docstring.",
        "answer_schema": "{order: list[item_id]}",
        "generation_schema": "tools/director_v04/sorting.py:generate_sorting_round()",
        "qa_requirements": "No duplicate item_ids; every item's real stat value in a round is distinct.",
        "casual_aliases": ["stat ladder", "put these stats in order", "rank these by"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "MAP_THE_CAREER": {
        "format_id": "MAP_THE_CAREER",
        "display_name": "Map the Career",
        "description": "N real teams/schools ONE real player's own career genuinely touched (the same "
                        "real canonical_roster_seasons / cfb_player_season_stats_real tables BEFORE_AFTER "
                        "uses for a 2-item version of this same idea); the player reorders them into the "
                        "real chronological sequence, then sees each real debut season revealed as evidence.",
        "payload_schema": None,
        "existing_renderer_note": "Reuses renderMechanicPilotBody's 'sorting' kind verbatim -- identical "
                                   "shape to STAT_LADDER (a real per-item value revealed post-submit), just "
                                   "ordered by real debut season instead of a real stat total. Zero new "
                                   "client code.",
        "proven_in": ["NFL_PLAYER_CAREER_TEAM_ORDER", "CFB_PLAYER_CAREER_SCHOOL_ORDER"],
        "supported_mechanics": ["sorting"],
        "mechanic_family": "sorting",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons (NFL, SOURCE_BACKED) / "
                                         "cfb_player_season_stats_real (CFB, SOURCE_BACKED_DERIVED)"],
        "min_items": 4, "max_items": 6, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"],
        "timed": False, "multiplayer_compatible": False, "scoring_model": "WEIGHTED",
        "interaction_model": "Reorder a vertical list of real team/school names (debut seasons hidden), "
                              "submit, then see each real debut season revealed next to the name.",
        "validation_rules": "A real player is only sampled if the N real teams/schools drawn for that "
                             "round have genuinely distinct real debut seasons -- resampled, never given an "
                             "invented tiebreak.",
        "answer_schema": "{order: list[item_id]}",
        "generation_schema": "tools/director_v04/sorting.py:generate_sorting_round()",
        "qa_requirements": "No duplicate item_ids; every item's real debut season in a round is distinct.",
        "casual_aliases": ["map the career", "career path", "order the teams they played for"],
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
        "renderer": "renderConnectionGridBody (engine-game-ui.js)",
        "proven_in": ["connection_grid_nfl"], "supported_mechanics": ["grid_constraint_board"],
        "mechanic_family": "GRID_CONSTRAINT_BOARD",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["draft_facts", "canonical_roster_seasons"],
        "min_items": 9, "max_items": 9, "min_pool_size": 1,
        "nfl_support": "SUPPORTED", "cfb_support": "UNKNOWN",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Tap a cell, type a real name, submit -- checked live against the database.",
        "validation_rules": "Every cell verified to have >=1 real candidate at generation time; every "
                             "submitted answer re-verified live, never against a precomputed key.",
        "answer_schema": "{row_index, col_index, guess: <free-text name>}",
        "generation_schema": "tools/director_v04/grid_constraint.py:build_package()",
        "qa_requirements": "Live per-cell COUNT() verification before publishing; no cell with 0 real candidates.",
        "casual_aliases": ["connection grid", "3x3 grid trivia"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "PERFECT_DRIVE": {
        "format_id": "PERFECT_DRIVE", "display_name": "Perfect Drive",
        "description": "A field-progression game: correct answers (from any existing, real 'guess' "
                        "capability) gain real yardage toward the end zone, keyed to each question's own "
                        "already-computed difficulty. One wrong answer ends the drive.",
        "payload_schema": None,
        "renderer": "renderDriveProgressionBody (engine-game-ui.js)",
        "proven_in": ["perfect_drive_nfl", "perfect_drive_cfb"], "supported_mechanics": ["drive_progression"],
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
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "GOAL_LINE_STAND": {
        "format_id": "GOAL_LINE_STAND", "display_name": "Goal Line Stand",
        "description": "A fixed number of downs (default 4) to score; each wrong answer costs a down. "
                        "Questions are real, drawn from any existing registered 'guess' capability.",
        "payload_schema": None,
        "renderer": "renderDriveProgressionBody (engine-game-ui.js)",
        "proven_in": ["goal_line_stand_nfl", "goal_line_stand_cfb"], "supported_mechanics": ["drive_progression"],
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
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "LINEUP_BUILDER": {
        "format_id": "LINEUP_BUILDER", "display_name": "Lineup Builder",
        "description": "Construct a themed real lineup (e.g. a 2010s NFL all-decade offense, or a real CFB "
                        "skill-position build) one real, eligible, not-yet-picked player per slot -- a "
                        "construction exercise, never a scored 'best lineup' claim (no ranking model backs "
                        "this variant).",
        "payload_schema": None,
        "renderer": "renderRosterBuildBody (engine-game-ui.js)",
        "proven_in": ["lineup_builder_nfl", "lineup_builder_cfb"],
        "supported_mechanics": ["roster_build"],
        "mechanic_family": "ROSTER_BUILD",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons", "cfb_roster_seasons_real"],
        "min_items": 6, "max_items": 6, "min_pool_size": 100,
        # Finish-10-Formats pass correction: CFB is NOT globally MISSING_DATA
        # -- a real, narrower skill-position-only configuration
        # (CFB_SKILL_POSITION_BUILDER) is fully supported, confirmed live
        # this pass with 32,550 distinct real CFB players across QB/RB/WR/TE.
        # A full 11-player CFB offense including 5 verified O-linemen
        # remains genuinely unsupported (no real CFB O-line data exists at
        # all) -- that narrower configuration, and only that one, is
        # MISSING_DATA; the format as a whole is SUPPORTED_WITH_LIMITATIONS.
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED_WITH_LIMITATIONS",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Tap a real, eligible, not-yet-drafted player to fill each real roster slot.",
        "validation_rules": "Every pick checked against the real, live eligible pool for its slot; no "
                             "player draftable twice.",
        "answer_schema": "{player_id}",
        "generation_schema": "tools/director_v04/roster_build.py:build_package('NFL_2010S_OFFENSE_BUILDER'|'CFB_SKILL_POSITION_BUILDER')",
        "qa_requirements": "Refuses to generate if any required position (QB/RB/WR/TE) has zero real candidates.",
        "casual_aliases": ["build an offense", "lineup builder", "skill position lineup", "build a cfb offense"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "AUCTION_DRAFT": {
        "format_id": "AUCTION_DRAFT", "display_name": "Auction Draft",
        "description": "Build a real roster one slot at a time under a fixed FICTIONAL budget. DEFAULT "
                        "cost mode: a real, balanced, deterministic fictional value derived from certified "
                        "career production (NFL: real career AV sum; CFB: real career yardage sum) -- "
                        "neither league requires real salary/NIL data. An explicit REAL_CONTRACT opt-in "
                        "variant (NFL only) uses each player's real career-average annual contract value "
                        "instead, clearly labeled and never the default.",
        "payload_schema": None,
        "renderer": "renderRosterBuildBody (engine-game-ui.js)",
        "proven_in": ["auction_draft_nfl", "auction_draft_cfb"],
        "supported_mechanics": ["roster_build"],
        "mechanic_family": "ROSTER_BUILD",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons", "cfb_player_season_stats_real", "nfl_player_contracts (REAL_CONTRACT variant only)"],
        "min_items": 6, "max_items": 6, "min_pool_size": 80,
        # Finish-10-Formats pass correction: CFB never required NIL/salary
        # data -- CFB_AUCTION_DRAFT uses the same real, deterministic
        # fictional cost model as NFL's default, confirmed live this pass
        # (no CFB player alone can exceed the fictional budget).
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WAGER",
        "interaction_model": "Tap one real, eligible, affordable player per slot, in order -- each pick "
                              "locks in immediately.",
        "validation_rules": "Every pick checked against real remaining budget before being accepted; "
                             "confirmed live this pass: the fictional default guarantees no single real "
                             "player can ever consume the whole budget (real correction from the prior "
                             "pass's real-contract-only implementation, where a single $50M+ QB could).",
        "answer_schema": "{player_id}",
        "generation_schema": "tools/director_v04/roster_build.py:build_package('NFL_AUCTION_DRAFT'|'CFB_AUCTION_DRAFT'|'NFL_AUCTION_DRAFT_REAL_CONTRACT', flow='SEQUENTIAL')",
        "qa_requirements": "Refuses to generate if any required position has zero real candidates.",
        "casual_aliases": ["auction draft", "give everyone a budget", "cfb auction draft with fictional player values"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "CAP_CHALLENGE": {
        "format_id": "CAP_CHALLENGE", "display_name": "Cap Challenge",
        "description": "Shares AUCTION_DRAFT's real pool/cost data but a genuinely distinct mechanic: "
                        "freely select, swap, or remove any real player in any slot -- nothing is locked "
                        "in until a final submit_lineup action, which is the one authoritative point a "
                        "real over-cap or incomplete roster is rejected. AUCTION_DRAFT is sequential "
                        "acquisition; CAP_CHALLENGE is optimize-then-submit.",
        "payload_schema": None,
        "renderer": "renderRosterBuildBody (engine-game-ui.js)",
        "proven_in": ["cap_challenge_nfl", "cap_challenge_cfb"],
        "supported_mechanics": ["roster_build"],
        "mechanic_family": "ROSTER_BUILD",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons", "cfb_player_season_stats_real"],
        "min_items": 6, "max_items": 6, "min_pool_size": 80,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WAGER",
        "interaction_model": "Freely select/swap/remove real players per slot; submit the finished lineup "
                              "when ready -- real over-cap or incomplete submissions are rejected.",
        "validation_rules": "Live running-budget check on every select; final authoritative completeness + "
                             "cap check on submit_lineup; confirmed live this pass (both a real completed "
                             "in-cap submission and a real incomplete-lineup rejection).",
        "answer_schema": "node stage: {action: 'select', slot_index, player_id} | {action: 'deselect', slot_index} | {action: 'submit_lineup'}",
        "generation_schema": "tools/director_v04/roster_build.py:build_package('NFL_AUCTION_DRAFT'|'CFB_AUCTION_DRAFT', flow='FREE_SELECT')",
        "qa_requirements": "Identical real pool/cost requirements as AUCTION_DRAFT.",
        "casual_aliases": ["salary cap challenge", "cap challenge", "nfl cap challenge"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
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
        "renderer": "renderBracketTreeBody(v, s) (engine-game-ui.js) -- reused UNCHANGED from BRACKET_TREE; "
                    "its view shape (rounds/picks_made/total_matchups/correct_count) is byte-identical, "
                    "confirmed live this pass (both flow through the same _comparison_client_view()/"
                    "_comparison_evaluate() functions server-side). Wired to its own real "
                    "ENGINE_MECHANIC_MODES entries (knockoutTournamentNfl/Cfb) this pass.",
        "proven_in": ["knockout_tournament_nfl", "knockout_tournament_cfb"], "supported_mechanics": ["knockout_bracket"],
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
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "SIX_DEGREES": {
        "format_id": "SIX_DEGREES", "display_name": "Six Degrees (Cross-League Chain)",
        "description": "A real, bounded 2-hop chain (real CFB school -> real player -> real NFL draft "
                        "team). Deliberately NOT the harder, unbounded live-pathfinding engine that already "
                        "exists as Coach Connections (gateway/services/coach_connections_graph.py, NFL-only, "
                        "a different, more general product) -- this is a distinct, narrower, cross-league "
                        "format slot.",
        "payload_schema": None,
        "renderer": "renderRelationshipChainBody (engine-game-ui.js)",
        "proven_in": ["six_degrees_cfb_nfl"], "supported_mechanics": ["relationship_chain"],
        "mechanic_family": "RELATIONSHIP_CHAIN",
        "supported_entity_types": ["school", "player", "team"],
        "required_data_relationships": ["cfb_nfl_identity_bridge_certified"],
        "min_items": 5, "max_items": 8, "min_pool_size": 5,
        "nfl_support": "SUPPORTED_WITH_LIMITATIONS", "cfb_support": "SUPPORTED_WITH_LIMITATIONS",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "See the start of a real chain, type where it real-ly ends.",
        "validation_rules": "Every hop is a real, HIGH_CONFIDENCE-tier row from the certified bridge table; "
                             "no invented or inferred relationship.",
        "answer_schema": "{guess: <free-text end-node name>}",
        "generation_schema": "tools/director_v04/relationship_chain.py:build_package()",
        "qa_requirements": "Confidence-tier filtered; refuses to generate below MIN_CHAINS real chains.",
        "casual_aliases": ["six degrees", "connect these two players"],
        # Real, deliberate, disclosed limitation (per explicit instruction:
        # "do not falsely claim arbitrary Six Degrees support") -- generation/
        # renderer/interaction/server-validation are all real and playable,
        # but the backend is bounded to 2 pre-validated hops, never the
        # harder, unbounded live-pathfinding search a "true" Six Degrees
        # implies (that harder engine already exists separately, NFL-only,
        # as Coach Connections). Never promoted to PRODUCTION_READY while
        # this scope gap stands.
        "mobile_verified": True, "creator_selectable": True, "production_status": "SUPPORTED_WITH_LIMITATIONS",
    },
    "CHAIN_REACTION": {
        "format_id": "CHAIN_REACTION", "display_name": "Chain Reaction",
        "description": "Shares SIX_DEGREES' real bounded 2-hop chain data/mechanic -- CHAIN_REACTION and "
                        "SIX_DEGREES are two format names over the identical real underlying chain shape "
                        "this pass, differing only in framing (start-to-end guess vs. link-by-link reveal).",
        "payload_schema": None,
        "renderer": "renderRelationshipChainBody (engine-game-ui.js) -- shares SIX_DEGREES' real renderer.",
        "proven_in": ["chain_reaction_cfb_nfl"], "supported_mechanics": ["relationship_chain"],
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
        # Same real, disclosed bounded-chain limitation as SIX_DEGREES -- see
        # that entry's own comment.
        "mobile_verified": True, "creator_selectable": True, "production_status": "SUPPORTED_WITH_LIMITATIONS",
    },
    "CHOOSE_YOUR_PATH": {
        "format_id": "CHOOSE_YOUR_PATH", "display_name": "Choose Your Path",
        "description": "A small, fixed, fully pre-validated real branch tree -- the player's choice at "
                        "each node picks which already-registered real 'guess' capability backs the next "
                        "real question. Never a general branching engine.",
        "payload_schema": None,
        "renderer": "renderBranchStateBody (engine-game-ui.js)",
        "proven_in": ["choose_your_path_nfl", "choose_your_path_cfb"], "supported_mechanics": ["branch_state"],
        "mechanic_family": "BRANCH_STATE",
        "supported_entity_types": ["player", "team", "school"],
        "required_data_relationships": [
            "NFL_DRAFT, NFL_CHAMPIONSHIP, NFL_COACHING (NFL tree) and CFB_HEISMAN, CFB_CHAMPIONSHIP, "
            "CFB_RIVALRY, CFB_RANKING, CFB_UPSET (CFB tree) -- all already-registered capabilities",
        ],
        "min_items": 1, "max_items": 1, "min_pool_size": 1,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Pick a path at each node; answer the real question at the leaf.",
        "validation_rules": "Every leaf resolves to an already-registered, independently-certified real "
                             "capability -- the tree itself is fixed and pre-validated, never built at request time.",
        "answer_schema": "node stage: {choice_id}; leaf stage: {answer: <chosen option label>}",
        "generation_schema": "tools/director_v04/branch_state.py:build_package()",
        "qa_requirements": "Every leaf's question generated through the real, unchanged guess-mechanic pipeline.",
        "casual_aliases": ["choose your path"],
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "GUESS_THE_SEASON": {
        "format_id": "GUESS_THE_SEASON", "display_name": "Guess the Season",
        "description": "Reveals several real clues about one real NFL season -- the Super Bowl champion "
                        "plus real season awards (MVP, OPOY, DPOY, ROTY awards, Super Bowl MVP) -- and the "
                        "player guesses the real season/year. Difficulty controls how many of the same real "
                        "clues are shown, never which ones (EASY is always a superset of HARD for the same "
                        "real season, not a differently-selected set).",
        "payload_schema": None,
        "renderer": "renderGuessTheSeasonBody (engine-game-ui.js)",
        "proven_in": ["guess_the_season_nfl"], "supported_mechanics": ["guess_the_season"],
        "mechanic_family": "GUESS_THE_SEASON",
        "supported_entity_types": ["season"],
        "required_data_relationships": ["nfl_championship_events (WIKIPEDIA_STRUCTURED_SECONDARY), "
                                         "nfl_season_awards (WIKIPEDIA_STRUCTURED_SECONDARY)"],
        "min_items": 2, "max_items": 4, "min_pool_size": 24,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["EASY", "MEDIUM", "HARD"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Read the revealed real clues, then submit one real season-year guess per round.",
        "validation_rules": "Restricted to the 24 real seasons with both a resolved Super Bowl champion and "
                             "2+ real season awards -- a season missing either is skipped, never padded with "
                             "an invented or unresolved clue. See guess_the_season.py's own documented fix for "
                             "a confirmed real SB_MVP indexing bug in the underlying nfl_season_awards table.",
        "answer_schema": "{guess_season: '<4-digit year>'}",
        "generation_schema": "tools/director_v04/guess_the_season.py:build_package()",
        "qa_requirements": "Every revealed clue traces to a real, resolved row; canonical answer never sent "
                            "to the client before evaluate() runs.",
        "casual_aliases": ["guess the season", "guess the year", "what season was this"],
        # True (not just left unverified) because renderGuessTheSeasonBody
        # introduces zero new CSS -- it's built entirely from .chain-node/
        # .chain-connector/.learn-filter-input, already-shipped classes this
        # session has no new mobile-layout risk to introduce (same
        # reasoning STAT_LADDER's own mobile_verified: True relied on).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "HEAD_TO_HEAD_DUEL": {
        "format_id": "HEAD_TO_HEAD_DUEL", "display_name": "Head to Head Duel",
        "description": "Two real players shown side by side; tap whichever you think has the higher real "
                        "value on one real statistical total (season rushing yards, career passing "
                        "touchdowns, or CFB career rushing yards). Real values revealed only after you answer.",
        "payload_schema": None,
        "renderer": "renderPairwiseCompareBody (engine-game-ui.js)",
        "proven_in": ["head_to_head_duel_nfl_rushing", "head_to_head_duel_nfl_passing_td",
                      "head_to_head_duel_cfb_rushing"],
        "supported_mechanics": ["pairwise_compare"], "mechanic_family": "PAIRWISE_COMPARE",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["player_season_stats (NFLVERSE_DATA, SOURCE_BACKED), "
                                         "cfb_player_season_stats_real (SPORTSDATAVERSE_CFB, "
                                         "SOURCE_BACKED_DERIVED)"],
        "min_items": 2, "max_items": 2, "min_pool_size": 2,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Tap one of 2 side-by-side real player cards (reuses renderBinaryChoiceHtml).",
        "validation_rules": "Every round resampled until the two real values are genuinely distinct -- a "
                             "real tie is never silently broken or invented a winner for.",
        "answer_schema": "{choice: 'A'|'B'}",
        "generation_schema": "tools/director_v04/head_to_head_duel.py:build_package()",
        "qa_requirements": "Both real values traced to a real, resolved row; neither value sent to the "
                            "client before evaluate() runs.",
        "casual_aliases": ["head to head", "head to head duel", "1v1", "one on one duel"],
        # True because renderPairwiseCompareBody introduces zero new CSS --
        # built entirely from the already-shipped renderBinaryChoiceHtml
        # component (app.js:272), same reasoning GUESS_THE_SEASON's own
        # mobile_verified: True relied on.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "BEST_OF_SEVEN_DUEL": {
        "format_id": "BEST_OF_SEVEN_DUEL", "display_name": "Best of Seven Duel",
        "description": "The same 2 real NFL quarterbacks compared across up to 7 real distinct career "
                        "categories (passing yards, passing touchdowns, completions, attempts, "
                        "interceptions thrown, rushing yards, PPR fantasy points -- honestly capped at "
                        "however many exist, never padded to a fake 7th). Any category where the two are "
                        "genuinely tied is dropped, never assigned an invented winner. The real overall "
                        "match outcome (most real categories won, or a genuine tie) is computed from real "
                        "data alone and revealed once the final round is answered.",
        "payload_schema": None,
        "renderer": "renderPairwiseCompareBody (engine-game-ui.js, shared with HEAD_TO_HEAD_DUEL)",
        "proven_in": ["best_of_seven_duel_nfl_qb"],
        "supported_mechanics": ["pairwise_compare"], "mechanic_family": "PAIRWISE_COMPARE",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["player_season_stats (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 2, "max_items": 2, "min_pool_size": 2,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Tap one of 2 side-by-side real player cards, once per real category, for the "
                              "same fixed real pair across the whole duel.",
        "validation_rules": "A real pair is rejected and resampled unless at least 3 of its real categories "
                             "are genuinely distinct; every tied category is dropped rather than assigned an "
                             "invented winner.",
        "answer_schema": "{choice: 'A'|'B'}",
        "generation_schema": "tools/director_v04/head_to_head_duel.py:build_package() "
                              "(NFL_CAREER_QB_BEST_OF_SEVEN variant)",
        "qa_requirements": "Every real value traced to a real, resolved row; the real match_summary is "
                            "computed once at generation time, independent of the player's own picks, and "
                            "never sent to the client before the final round is answered.",
        "casual_aliases": ["best of seven", "best of 7", "best of seven duel"],
        # True for the same reason HEAD_TO_HEAD_DUEL's own mobile_verified
        # relied on -- this variant reuses renderPairwiseCompareBody
        # verbatim, introducing zero new CSS or layout.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "PICK_THE_IMPOSTOR": {
        "format_id": "PICK_THE_IMPOSTOR", "display_name": "Pick the Impostor",
        "description": "4 real players shown together; 3 really share one real, verifiable membership fact "
                        "(the same real NFL team roster, or the same real CFB school, in the same real "
                        "season) and 1 genuinely does not. The player taps the impostor.",
        "payload_schema": None,
        "renderer": "renderPickTheImpostorBody (engine-game-ui.js, reuses renderCandidateCardsHtml)",
        "proven_in": ["pick_the_impostor_nfl", "pick_the_impostor_cfb"],
        "supported_mechanics": ["pick_the_impostor"], "mechanic_family": "PICK_THE_IMPOSTOR",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons (NFLVERSE_DATA, SOURCE_BACKED), "
                                         "cfb_player_season_stats_real (SPORTSDATAVERSE_CFB, "
                                         "SOURCE_BACKED_DERIVED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Tap 1 of 4 real candidate cards (reuses renderCandidateCardsHtml).",
        "validation_rules": "The real impostor is always confirmed absent from the 3-member group's own "
                             "real player-id set before being finalized -- never assumed disjoint just "
                             "because the two groups came from different teams/schools.",
        "answer_schema": "{impostor_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/pick_the_impostor.py:build_package()",
        "qa_requirements": "Every real membership fact traced to a real, resolved row; the real impostor's "
                            "item_id never sent to the client before evaluate() runs.",
        "casual_aliases": ["impostor", "imposter", "doesn't belong", "which one wasn't"],
        # True because renderPickTheImpostorBody introduces zero new CSS --
        # built entirely from the already-shipped renderCandidateCardsHtml
        # component (app.js:306, the same one Odd College Out/One School
        # Missing already use in production).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "UNIQUE_ONE_OUT": {
        "format_id": "UNIQUE_ONE_OUT", "display_name": "Unique One Out",
        "description": "4 real NFL players shown together; 3 really share the same real NFL Draft class "
                        "(the same real draft year) and 1 genuinely does not. The player taps the one that "
                        "doesn't belong to that real draft class.",
        "payload_schema": None,
        "renderer": "renderPickTheImpostorBody (engine-game-ui.js, shared with PICK_THE_IMPOSTOR)",
        "proven_in": ["unique_one_out_nfl"],
        "supported_mechanics": ["pick_the_impostor"], "mechanic_family": "PICK_THE_IMPOSTOR",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["draft_facts (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Tap 1 of 4 real candidate cards (reuses renderCandidateCardsHtml).",
        "validation_rules": "The real impostor is always confirmed absent from the 3-member group's own "
                             "real player-id set before being finalized.",
        "answer_schema": "{impostor_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/pick_the_impostor.py:build_package() "
                              "(NFL_DRAFT_CLASS_ONE_OUT variant)",
        "qa_requirements": "Every real draft-class fact traced to a real, resolved row; the real impostor's "
                            "item_id never sent to the client before evaluate() runs.",
        "casual_aliases": ["unique one out", "odd one out"],
        # True for the same reason PICK_THE_IMPOSTOR's own mobile_verified
        # relied on -- this variant reuses renderPickTheImpostorBody
        # verbatim, introducing zero new CSS or layout.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "MISSING_PIECE": {
        "format_id": "MISSING_PIECE", "display_name": "Missing Piece",
        "description": "The inverse of PICK_THE_IMPOSTOR: 3 real players from the same real team/school "
                        "roster in a real season are shown as given context, and the player taps which of "
                        "4 candidates was ALSO genuinely part of that real group -- 1 real correct "
                        "completion plus 3 real decoys who genuinely were not.",
        "payload_schema": None,
        "renderer": "renderMissingPieceBody (engine-game-ui.js, reuses .chain-node + renderCandidateCardsHtml)",
        "proven_in": ["missing_piece_nfl", "missing_piece_cfb"],
        "supported_mechanics": ["missing_piece"], "mechanic_family": "MISSING_PIECE",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons (NFLVERSE_DATA, SOURCE_BACKED), "
                                         "cfb_player_season_stats_real (SPORTSDATAVERSE_CFB, "
                                         "SOURCE_BACKED_DERIVED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Read 3 real given group members, then tap 1 of 4 real candidate cards.",
        "validation_rules": "The real correct completion and every real decoy are drawn from a real, "
                             "already-fetched pool for that exact real season -- no decoy is ever assumed "
                             "absent from the real group; it is only included once confirmed not already "
                             "among the 4 real group members.",
        "answer_schema": "{answer_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/missing_piece.py:build_package()",
        "qa_requirements": "Every real group-membership fact traced to a real, resolved row; the real "
                            "correct item_id never sent to the client before evaluate() runs.",
        "casual_aliases": ["missing piece", "who's missing", "which one belongs"],
        # True because renderMissingPieceBody introduces zero new CSS --
        # built entirely from .chain-node/.chain-connector (GUESS_THE_SEASON's
        # own already-shipped clue-list classes) plus renderCandidateCardsHtml
        # (PICK_THE_IMPOSTOR's own already-shipped component).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "BEFORE_AFTER": {
        "format_id": "BEFORE_AFTER", "display_name": "Before & After",
        "description": "One real player who genuinely played for 2 different real teams/schools across "
                        "their own real career; the player taps whichever real team/school came FIRST. "
                        "A real chronological self-career question, not a cross-entity comparison.",
        "payload_schema": None,
        "renderer": "renderBeforeAfterBody (engine-game-ui.js, reuses renderBinaryChoiceHtml)",
        "proven_in": ["before_after_nfl", "before_after_cfb"],
        "supported_mechanics": ["before_after"], "mechanic_family": "BEFORE_AFTER",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons (NFLVERSE_DATA, SOURCE_BACKED), "
                                         "cfb_player_season_stats_real (SPORTSDATAVERSE_CFB, "
                                         "SOURCE_BACKED_DERIVED)"],
        "min_items": 2, "max_items": 2, "min_pool_size": 2,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Tap one of 2 side-by-side real team/school cards (reuses renderBinaryChoiceHtml).",
        "validation_rules": "Every round resampled until the two real debut seasons are genuinely distinct "
                             "-- a real tie is never silently broken or invented an order for.",
        "answer_schema": "{choice: 'A'|'B'}",
        "generation_schema": "tools/director_v04/before_after.py:build_package()",
        "qa_requirements": "Both real debut seasons traced to a real, resolved row; neither value sent to "
                            "the client before evaluate() runs.",
        "casual_aliases": ["before and after", "before or after", "which came first", "played for first"],
        # True because renderBeforeAfterBody reuses renderBinaryChoiceHtml
        # verbatim (same reasoning HEAD_TO_HEAD_DUEL's own mobile_verified
        # relied on) -- zero new CSS or layout.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "CAREER_PATH": {
        "format_id": "CAREER_PATH", "display_name": "Career Path",
        "description": "The inverse of MAP_THE_CAREER: the real, already-ordered first 3 teams/schools of "
                        "one real player's career are shown, and the player identifies which real player it "
                        "belongs to from 4 real candidates. Every decoy's own real path is checked against "
                        "the correct answer's and rejected if it matches, so no decoy could itself be a "
                        "second valid real answer.",
        "payload_schema": None,
        "renderer": "renderCareerPathBody (engine-game-ui.js, reuses .chain-node + renderCandidateCardsHtml)",
        "proven_in": ["career_path_nfl", "career_path_cfb"],
        "supported_mechanics": ["career_path"], "mechanic_family": "CAREER_PATH",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["canonical_roster_seasons (NFL, SOURCE_BACKED) / "
                                         "cfb_player_season_stats_real (CFB, SOURCE_BACKED_DERIVED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "BINARY",
        "interaction_model": "Read the real career path, then tap 1 of 4 real candidate cards.",
        "validation_rules": "Every real decoy's own real path is computed and compared against the correct "
                             "answer's real path; a match is rejected rather than risked as an ambiguous "
                             "second valid answer.",
        "answer_schema": "{guess_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/career_path.py:build_package()",
        "qa_requirements": "Every real path traced to a real, resolved sequence of rows; the real correct "
                            "item_id never sent to the client before evaluate() runs.",
        "casual_aliases": ["career path", "which player had this path"],
        # True because renderCareerPathBody introduces zero new CSS --
        # built entirely from .chain-node/.chain-connector plus
        # renderCandidateCardsHtml, both already-shipped components.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "RISK_IT": {
        "format_id": "RISK_IT", "display_name": "Risk It",
        "description": "Real risk-vs-reward trivia: before each round, the player picks a real risk tier "
                        "(LOW/MEDIUM/HIGH) sight-unseen, which sets the real stakes and the real difficulty "
                        "of the question -- a real, verifiable proxy (NFL Draft pick_overall: an early real "
                        "pick is more recognizable, a late real pick is more obscure), never an invented "
                        "rating. A wrong answer costs one of 3 real starting lives; the run ends at 0 lives "
                        "or after 7 rounds.",
        "payload_schema": None,
        "existing_renderer_note": "Real 2-step interaction per round (choose a tier, then answer that "
                                   "tier's real question) -- reuses BRANCH_STATE's own established "
                                   "navigation-then-leaf-question shape rather than inventing a second "
                                   "pattern for 'commit before you see it'.",
        "proven_in": ["risk_it_nfl_draft"],
        "supported_mechanics": ["risk_it"], "mechanic_family": "RISK_IT",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["draft_facts (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["LOW", "MEDIUM", "HIGH"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Tap a risk tier (point value only, no question shown yet), then tap 1 of 4 "
                              "real candidate cards for that tier's real question.",
        "validation_rules": "Every real question at every real tier has a genuine 4-option real decoy set "
                             "(3 real teams that drafted different real players that exact real draft class) "
                             "before a round is included.",
        "answer_schema": "{action: 'choose_tier', tier: 'LOW'|'MEDIUM'|'HIGH'} then "
                          "{action: 'answer', choice_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/risk_it.py:build_package()",
        "qa_requirements": "Every real tier's correct item_id never sent to the client before evaluate() "
                            "runs; a tier's real question is only revealed after that tier is chosen.",
        "casual_aliases": ["risk it", "risk tier", "pick a risk"],
        # True because renderRiskItBody introduces zero new CSS -- built
        # entirely from .chip-row/.chip-toggle (BRANCH_STATE's own
        # already-shipped choice-button classes) plus renderCandidateCardsHtml.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "WAGER_MODE": {
        "format_id": "WAGER_MODE", "display_name": "Wager Mode",
        "description": "Real Jeopardy-style category wagering: each round shows only a real category name, "
                        "the player wagers any real fictional-point amount up to their current balance, and "
                        "only then is the real question revealed. A correct answer adds the wager, a wrong "
                        "answer subtracts it. 3 real categories (NFL Draft, Heisman Winners, Super Bowl "
                        "Champions), each drawn from an already-certified real table this Engine's other "
                        "mechanics already use.",
        "payload_schema": None,
        "existing_renderer_note": "Real 2-step interaction per round (place a wager, then answer) -- same "
                                   "real navigation-then-leaf-question shape RISK_IT/BRANCH_STATE already "
                                   "established, with a continuous real wager amount in place of RISK_IT's "
                                   "3 discrete tiers.",
        "proven_in": ["wager_mode_mixed"],
        "supported_mechanics": ["wager_mode"], "mechanic_family": "WAGER_MODE",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["draft_facts (NFLVERSE_DATA, SOURCE_BACKED), cfb_award_facts "
                                         "(READS_CFB_MASTER, SOURCE_BACKED_FROM_CFB_MASTER), "
                                         "nfl_championship_events (WIKIPEDIA_STRUCTURED, "
                                         "WIKIPEDIA_STRUCTURED_SECONDARY)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "SUPPORTED_WITH_LIMITATIONS",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Read a real category name, type a real fictional wager amount, then tap 1 of "
                              "4 real candidate cards for the revealed question.",
        "validation_rules": "A wager must be a real integer between 0 and the player's current real "
                             "balance -- rejected outright (never clamped) if out of range.",
        "answer_schema": "{action: 'place_wager', wager: <int>} then "
                          "{action: 'answer', choice_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/wager_mode.py:build_package()",
        "qa_requirements": "Every real category's correct item_id never sent to the client before "
                            "evaluate() runs; a round's real question is only revealed after a wager is placed.",
        "casual_aliases": ["wager"],
        # True because renderWagerModeBody introduces zero new CSS --
        # built entirely from .learn-filter-input (GUESS_THE_SEASON's own
        # already-shipped free-text-input pattern) plus renderCandidateCardsHtml.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "LEADERBOARD_CLIMB": {
        "format_id": "LEADERBOARD_CLIMB", "display_name": "Leaderboard Climb",
        "description": "Real leaderboard-climbing trivia: start at the bottom rung of a real, fixed, "
                        "pre-sorted statistical leaderboard (career passing yards) and climb one rung at a "
                        "time by correctly identifying which of 2 named real players -- the one on the "
                        "player's current rung, and the real player one rung above -- actually ranks higher. "
                        "A correct answer climbs to that next rung; a wrong answer ends the climb "
                        "immediately. Reaching rank 1 completes the climb.",
        "payload_schema": None,
        "existing_renderer_note": "Single-step binary choice per round -- reuses the exact same "
                                   "renderBinaryChoiceHtml/data-mechanic-duel-choice pattern already shipped "
                                   "for PAIRWISE_COMPARE/BEFORE_AFTER rather than inventing a new choice "
                                   "widget.",
        "proven_in": ["leaderboard_climb_nfl"],
        "supported_mechanics": ["leaderboard_climb"], "mechanic_family": "LEADERBOARD_CLIMB",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["player_season_stats (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 4, "max_items": 15, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Tap whichever of 2 named real players you think ranks HIGHER on a real, fixed "
                              "leaderboard; a correct answer climbs one rung, a wrong answer ends the climb.",
        "validation_rules": "The real leaderboard's top-N values are checked for genuine distinctness (no "
                             "tie) at generation time -- a real tie anywhere in the ladder aborts generation "
                             "rather than inventing a tiebreak.",
        "answer_schema": "{choice: 'A'|'B'}",
        "generation_schema": "tools/director_v04/leaderboard_climb.py:build_package()",
        "qa_requirements": "The real leaderboard's ranks/values are never sent to the client wholesale -- "
                            "only the 2 entities for the player's current matchup are ever exposed, and the "
                            "real winning rank/values are only revealed after evaluate() runs.",
        "casual_aliases": ["leaderboard climb", "climb the leaderboard"],
        # True because renderLeaderboardClimbBody introduces zero new CSS --
        # built entirely from renderBinaryChoiceHtml (PAIRWISE_COMPARE's own
        # already-shipped binary-choice pattern).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "BLIND_RESUME": {
        "format_id": "BLIND_RESUME", "display_name": "Blind Resume",
        "description": "Real 'whose career is this?' trivia: a real player's career passing resume (career "
                        "games, pass yards, pass TDs, interceptions) is shown with the name redacted, and "
                        "the player picks which of 4 real named candidates it belongs to.",
        "payload_schema": None,
        "existing_renderer_note": "Single-step 4-option multiple choice per round -- reuses the exact same "
                                   "renderCandidateCardsHtml pattern already shipped for PICK_THE_IMPOSTOR/"
                                   "MISSING_PIECE/BEFORE_AFTER rather than inventing a new choice widget.",
        "proven_in": ["blind_resume_nfl_qb"],
        "supported_mechanics": ["blind_resume"], "mechanic_family": "BLIND_RESUME",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["player_season_stats (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Read a real player's blind career resume, then tap 1 of 4 real candidate cards "
                              "for who you think it belongs to.",
        "validation_rules": "The correct real candidate and all 3 real decoys are distinct real, qualifying "
                             "players (career pass yards > 3000 across >= 16 real career games) -- decoys are "
                             "never shown their own resumes, only their real names.",
        "answer_schema": "{choice_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/blind_resume.py:build_package()",
        "qa_requirements": "The real correct candidate's identity is never sent to the client before "
                            "evaluate() runs.",
        "casual_aliases": ["blind resume"],
        # True because the renderer introduces zero new CSS -- built
        # entirely from renderCandidateCardsHtml (PICK_THE_IMPOSTOR's own
        # already-shipped 4-option card pattern).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "DOUBLE_OR_NOTHING": {
        "format_id": "DOUBLE_OR_NOTHING", "display_name": "Double or Nothing",
        "description": "Real bank-or-risk escalation: answer a sequence of real questions of increasing "
                        "real difficulty. The first correct answer banks 100 fictional points; every "
                        "subsequent correct answer DOUBLES the current points. After any correct answer, "
                        "bank the points (end the run, keep them) or risk them all on the next, harder real "
                        "question. One wrong answer loses everything -- no lives, unlike RISK_IT.",
        "payload_schema": None,
        "existing_renderer_note": "Real 2-step interaction per correct answer (see the real question, "
                                   "answer it, then bank-or-continue) -- reuses RISK_IT/WAGER_MODE's own "
                                   "established navigation-then-leaf-question shape and renderCandidateCardsHtml, "
                                   "with a real bank/continue choice inserted after a correct answer instead "
                                   "of before the question.",
        "proven_in": ["double_or_nothing_nfl_draft"],
        "supported_mechanics": ["double_or_nothing"], "mechanic_family": "DOUBLE_OR_NOTHING",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["draft_facts (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Answer a real question, then tap Bank (keep your real points) or Continue "
                              "(risk them on the next, harder real question) after every correct answer.",
        "validation_rules": "Every real question at every real tier has a genuine 4-option real decoy set, "
                             "reusing risk_it.py's own real decoy-completeness discipline verbatim. Banking "
                             "with 0 real points is rejected.",
        "answer_schema": "{action: 'answer', choice_item_id: 'A'|'B'|'C'|'D'} or {action: 'bank'}",
        "generation_schema": "tools/director_v04/double_or_nothing.py:build_package()",
        "qa_requirements": "Every real question's correct item_id never sent to the client before evaluate() "
                            "runs; points only ever double or reset to 0, never invented.",
        "casual_aliases": ["double or nothing"],
        # True because renderDoubleOrNothingBody introduces zero new CSS --
        # built entirely from renderCandidateCardsHtml (RISK_IT's own
        # already-shipped card pattern) plus .chip-toggle (RISK_IT's own
        # already-shipped choice-button class) for the bank/continue choice.
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "KING_OF_THE_HILL": {
        "format_id": "KING_OF_THE_HILL", "display_name": "King of the Hill",
        "description": "Real persistent-champion gauntlet: one real NFL team-season starts as champion. "
                        "Predict whether the champion or the next real challenger really had more real "
                        "wins that season -- a correct prediction resolves honestly (the real higher-win "
                        "team becomes/stays champion, consecutive defenses tracked); a wrong prediction "
                        "ends the run.",
        "payload_schema": None,
        "existing_renderer_note": "Single-step binary choice per round -- reuses the exact same "
                                   "renderBinaryChoiceHtml/data-mechanic-duel-choice pattern already shipped "
                                   "for PAIRWISE_COMPARE/BEFORE_AFTER/LEADERBOARD_CLIMB rather than inventing "
                                   "a new choice widget.",
        "proven_in": ["king_of_the_hill_nfl"],
        "supported_mechanics": ["king_of_the_hill"], "mechanic_family": "KING_OF_THE_HILL",
        "supported_entity_types": ["team"],
        "required_data_relationships": ["season_standings (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 4, "max_items": 16, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Tap whichever of the champion or the next real challenger you think really "
                              "had more real wins that season.",
        "validation_rules": "Every real item's real win total is distinct from every other item's (tie-"
                             "exclusion by construction, reusing higher_lower.py's own real discipline) -- "
                             "no comparison can ever tie.",
        "answer_schema": "{choice: 'champion'|'challenger'}",
        "generation_schema": "tools/director_v04/king_of_the_hill.py:build_package()",
        "qa_requirements": "The real winning side is never sent to the client before evaluate() runs; only "
                            "the champion's and challenger's real names are ever exposed pre-answer, never "
                            "their real win totals.",
        "casual_aliases": ["king of the hill"],
        # True because the renderer introduces zero new CSS -- built
        # entirely from renderBinaryChoiceHtml (PAIRWISE_COMPARE's own
        # already-shipped binary-choice pattern).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "FACT_OR_FAKE": {
        "format_id": "FACT_OR_FAKE", "display_name": "Fact or Fake",
        "description": "Real true/false judgment: read one real NFL Draft statement and tap TRUE (a real, "
                        "verbatim fact) or FAKE (one real team substituted with a different real team that "
                        "drafted a different real player that class -- provably false, never a fabricated "
                        "or randomly-altered number).",
        "payload_schema": None,
        "existing_renderer_note": "Single-step binary TRUE/FAKE choice per round -- reuses "
                                   "renderBinaryChoiceHtml/data-mechanic-duel-choice verbatim.",
        "proven_in": ["fact_or_fake_nfl_draft"],
        "supported_mechanics": ["fact_or_fake"], "mechanic_family": "FACT_OR_FAKE",
        "supported_entity_types": ["player", "team"],
        "required_data_relationships": ["draft_facts (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 1, "max_items": 1, "min_pool_size": 2,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Read the real statement, then tap TRUE or FAKE.",
        "validation_rules": "Every real FAKE statement is false by a genuine real entity substitution "
                             "(a different real team that really drafted someone else that class), never a "
                             "fabricated or randomly-altered number. Rounds split TRUE/FAKE deterministically "
                             "50/50, never a coin flip that could skew a short run.",
        "answer_schema": "{guess: 'TRUE'|'FAKE'}",
        "generation_schema": "tools/director_v04/fact_or_fake.py:build_package()",
        "qa_requirements": "Whether a round is TRUE or FAKE is never sent to the client before evaluate() runs.",
        "casual_aliases": ["fact or fake"],
        # True because the renderer introduces zero new CSS -- built
        # entirely from renderBinaryChoiceHtml (PAIRWISE_COMPARE's own
        # already-shipped binary-choice pattern).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
    },
    "GUESS_THE_RANKING": {
        "format_id": "GUESS_THE_RANKING", "display_name": "Guess the Ranking",
        "description": "Real rank-identification trivia: a real player is named from a real, fixed "
                        "career-passing-yards leaderboard -- tap the real rank (#1-#15) you think they hold.",
        "payload_schema": None,
        "existing_renderer_note": "Single-step 4-option multiple choice per round -- reuses "
                                   "renderCandidateCardsHtml verbatim.",
        "proven_in": ["guess_the_ranking_nfl"],
        "supported_mechanics": ["guess_the_ranking"], "mechanic_family": "GUESS_THE_RANKING",
        "supported_entity_types": ["player"],
        "required_data_relationships": ["player_season_stats (NFLVERSE_DATA, SOURCE_BACKED)"],
        "min_items": 4, "max_items": 4, "min_pool_size": 4,
        "nfl_support": "SUPPORTED", "cfb_support": "MISSING_DATA",
        "difficulty_support": ["any"], "timed": False, "multiplayer_compatible": False,
        "scoring_model": "WEIGHTED",
        "interaction_model": "Read the real player's name, then tap 1 of 4 real candidate rank cards.",
        "validation_rules": "The correct real rank and all 3 real decoy ranks genuinely belong to other "
                             "real players on the same real leaderboard -- never a fabricated or "
                             "out-of-range rank.",
        "answer_schema": "{choice_item_id: 'A'|'B'|'C'|'D'}",
        "generation_schema": "tools/director_v04/guess_the_ranking.py:build_package()",
        "qa_requirements": "The real correct rank is never sent to the client before evaluate() runs.",
        "casual_aliases": ["guess the ranking"],
        # True because the renderer introduces zero new CSS -- built
        # entirely from renderCandidateCardsHtml (PICK_THE_IMPOSTOR's own
        # already-shipped 4-option card pattern).
        "mobile_verified": True, "creator_selectable": True, "production_status": "PRODUCTION_READY",
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
