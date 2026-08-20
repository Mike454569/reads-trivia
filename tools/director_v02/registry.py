"""Director v0.2 -- registry of capabilities the Engine can genuinely
execute today.

A capability is only registered here if it has ALREADY executed
successfully in a prior approved pilot or in Director v0.1 -- production-safe
data, working generation logic, working QA, and a usable adapter, all proven,
not merely a predicate name existing somewhere in Game Factory. This is the
same discipline `tools/game_director_v01.py`'s `ADAPTER_REGISTRY` already
follows; this registry extends it with the extra metadata v0.2's validator
needs (bounds, supported difficulties/filters) without touching that file.

Registering a new tuple here is exactly how a second domain should be added
later -- never by loosening validation or writing a generic query engine.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools import game_director_v01 as v01  # noqa: E402
from tools.director_v04 import player_from_clues  # noqa: E402
from tools.director_v04 import cfb_player_from_clues  # noqa: E402
from tools.quiz_export.adapters import cfb_game_result as cfb_game_result_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_heisman as cfb_heisman_adapter  # noqa: E402
from tools.quiz_export.adapters import championship as championship_adapter  # noqa: E402
from tools.quiz_export.adapters import draft as draft_adapter  # noqa: E402
from tools.quiz_export.adapters import draft_college as draft_college_adapter  # noqa: E402
from tools.quiz_export.adapters import lineup as lineup_adapter  # noqa: E402
from tools.quiz_export.adapters import lineup_college as lineup_college_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_game_boxscore as nfl_game_boxscore_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_game_boxscore_sacks as nfl_game_boxscore_sacks_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_game_boxscore_turnovers as nfl_game_boxscore_turnovers_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_game_boxscore_penalties as nfl_game_boxscore_penalties_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_game_result as nfl_game_result_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_super_bowl as nfl_super_bowl_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_season_awards as nfl_season_awards_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_championship as cfb_championship_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_season_stat_leader as nfl_season_stat_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_season_stat_leader as cfb_season_stat_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_coaching as nfl_coaching_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_transfer as cfb_transfer_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_rivalry as cfb_rivalry_adapter  # noqa: E402
from tools.quiz_export.adapters import player_season_team as player_season_team_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_player_season_school as cfb_player_season_school_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_all_pro as nfl_all_pro_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_pro_bowl as nfl_pro_bowl_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_hof as nfl_hof_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_offensive_coordinator as nfl_offensive_coordinator_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_defensive_coordinator as nfl_defensive_coordinator_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_ranking as cfb_ranking_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_upset_ranking as cfb_upset_ranking_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_upset_betting as cfb_upset_betting_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_first_touchdown as nfl_first_touchdown_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_sack as nfl_sack_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_interception as nfl_interception_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_forced_fumble as nfl_forced_fumble_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_fumble_recovery as nfl_fumble_recovery_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_drive_result as nfl_drive_result_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_rushing_compare as cfb_rushing_compare_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_passing_compare as cfb_passing_compare_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_receiving_compare as cfb_receiving_compare_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_rushing_leader as nfl_rushing_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_passing_leader as nfl_passing_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_receiving_leader as nfl_receiving_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_rushing_leader as cfb_rushing_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_passing_leader as cfb_passing_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_receiving_leader as cfb_receiving_leader_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_transfer_path as cfb_transfer_path_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_all_pro_college as nfl_all_pro_college_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_pro_bowl_college as nfl_pro_bowl_college_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_hof_college as nfl_hof_college_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_all_american_to_all_pro as cfb_all_american_to_all_pro_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_all_american_to_pro_bowl as cfb_all_american_to_pro_bowl_adapter  # noqa: E402

PACKAGE_SCHEMA_VERSION = "0.2"

QA_CHECKS_PERFORMED_V02 = [
    "translator.translate() -> structured TranslationResult (LLM or deterministic mock, "
    "never trusted -- see below)",
    "validator.validate_translation() -- exact key-set check (rejects any extra/injected field)",
    "validator: mechanic/domain/relationship_predicate/difficulty checked against a hardcoded allowlist",
    "validator: question_count bounds check (schema-level and capability-specific)",
    "validator: filters/exclusions must be empty (no registered capability supports either yet)",
    "registry.lookup() -- (mechanic, domain, predicate) must be a previously-proven, registered capability",
    *v01.QA_CHECKS_PERFORMED,
]


def _generate_guess_package(validated_spec: dict, capability: dict, *, request_text: str,
                             director_request_id: str, seed: str, target_count: int, id_start: int,
                             freeze_timestamp: str | None) -> dict:
    """Generation dispatch for every `guess`-mechanic capability (Draft,
    Championship) -- maps the small translator-facing DirectorSpec onto the
    full Game-Factory-shaped spec `generate_package_from_spec()` expects.
    entity_type/object_type/answer_type/group_size/competition_id are
    DERIVED from the registered capability, never supplied by the
    translator (see director_v02/schema.py's module docstring for why)."""
    adapter = capability["adapter"]
    factory_spec = {
        "competition_id": capability["competition_id"],
        "mechanic": validated_spec["mechanic"],
        "entity_type": capability["entity_type"],
        "relationship_predicate": validated_spec["relationship_predicate"],
        "object_type": capability["object_type"],
        "answer_type": capability["answer_type"],
        "group_size": capability["group_size"],
        "filters": validated_spec["filters"],
    }
    return v01.generate_package_from_spec(
        factory_spec, adapter,
        request_text=request_text, director_request_id=director_request_id,
        seed=seed, target_count=target_count, id_start=id_start, freeze_timestamp=freeze_timestamp,
        difficulty_filter=validated_spec["difficulty"],
        package_version=PACKAGE_SCHEMA_VERSION,
        qa_checks_performed=QA_CHECKS_PERFORMED_V02,
    )


def _generate_player_from_clues_package(validated_spec: dict, capability: dict, *, request_text: str,
                                         director_request_id: str, seed: str, target_count: int, id_start: int,
                                         freeze_timestamp: str | None) -> dict:
    """Generation dispatch for `identify_player_from_clues` -- structurally
    different from the `guess` path (no options/correctIndex, a progressive
    clue sequence instead), so it calls its own dedicated builder rather
    than being forced through the guess-shaped function above. See
    PLAYER_FROM_CLUES_MECHANIC_SPEC.md."""
    package = player_from_clues.build_package(
        seed=seed, target_count=target_count, id_start=id_start,
        requested_description=request_text, freeze_timestamp=freeze_timestamp,
    )
    package["director_request_id"] = director_request_id
    return package


def _generate_cfb_player_from_clues_package(validated_spec: dict, capability: dict, *, request_text: str,
                                             director_request_id: str, seed: str, target_count: int, id_start: int,
                                             freeze_timestamp: str | None) -> dict:
    """CFB parity for _generate_player_from_clues_package() above -- same
    dispatch shape, calls tools.director_v04.cfb_player_from_clues.build_package()
    instead (its own real, CFB-native identity universe -- see that
    module's docstring)."""
    package = cfb_player_from_clues.build_package(
        seed=seed, target_count=target_count, id_start=id_start,
        requested_description=request_text, freeze_timestamp=freeze_timestamp,
    )
    package["director_request_id"] = director_request_id
    return package


# Key: (mechanic, domain, relationship_predicate) -- the exact triple a
# validated DirectorSpec must match for generation to proceed.
CAPABILITY_REGISTRY: dict[tuple[str, str, str], dict] = {
    ("guess", "NFL_DRAFT", "DRAFTED_BY"): {
        "adapter": draft_adapter,
        "category": draft_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        # Derived, Engine-side spec fields -- never supplied by the translator.
        "competition_id": "NFL",
        "entity_type": "nfl_player",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        # Bounds/support this specific capability actually implements.
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,  # Engine-side post-filter on the adapter's own
                                              # already-computed difficulty_band; never invented.
        "supported_filter_keys": frozenset(),  # none yet
        "supports_exclusions": False,
        "proven_in": [
            "draft-pilot-v1", "draft-pilot-v2-production", "mixed-pilot-300",
            "director-v0.1-first-game",
        ],
        "pipeline_id_start": 610000,
    },
    # Added for the stale-college-feasibility fix: a real gap-check found
    # `draft_facts.college` had always had a `college` column (from the
    # `draft_picks.csv` source) that was never mapped -- backfilled
    # additively (12,914 of 12,927 real draft rows got a real college; the
    # other 13 have none in the source, see tools/quiz_export/adapters/
    # draft_college.py's module docstring). Before this, a general "guess
    # the college of an NFL player" request had NO registered capability at
    # all and fell into feasibility.py's generic, hardcoded "college" signal
    # (a stale 2,542-row citation of a DIFFERENT table,
    # cfb_nfl_identity_bridge_certified, used by the narrower
    # NFL_OFFENSE_LINEUP_COLLEGE capability below). This capability is what
    # makes that data real, generatable content: entity=player, answer=the
    # college that specific player attended, sourced directly from the
    # draft record.
    ("guess", "NFL_DRAFT", "ATTENDED_COLLEGE"): {
        "adapter": draft_college_adapter,
        "category": draft_college_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers only drafted NFL players with a college recorded in the draft record itself "
            "(draft_facts.college, backfilled from nflverse's draft_picks.csv) -- 12,914 of 12,927 real "
            "draft picks (1980-2026) have a known college; the other 13 have none in the source and are "
            "excluded, never guessed. Undrafted players are not covered by this capability at all.",
            "Distinct from the narrower NFL_OFFENSE_LINEUP_COLLEGE capability, which additionally requires "
            "season-specific starting-lineup membership and uses a different, cross-referenced identity "
            "bridge (cfb_nfl_identity_bridge_certified) -- see tools.quiz_export.adapters.draft_college."
            "live_college_coverage() for this capability's own live, current coverage numbers.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_player",
        "object_type": "school",
        "answer_type": "school",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["stale-college-feasibility-fix"],
        "pipeline_id_start": 690000,
    },
    # Added in Director v0.3, Part B. Selected over QB/Season as the second
    # capability specifically because of its prior-pilot ambiguity profile:
    # 296 candidates considered, 296 accepted, ZERO rejections -- "the domain
    # is a primary key by construction" (each team-season pair is already
    # unique; no identity-inconsistency exclusion list was ever needed,
    # unlike QB/Season's 7 excluded QB IDs and 20 midseason-trade rejections).
    # See GAME_DIRECTOR_V03_REPORT.md, Part B1, for the full comparison.
    ("guess", "NFL_CHAMPIONSHIP", "TEAM_POSTSEASON_RESULT"): {
        "adapter": championship_adapter,
        "category": championship_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "competition_id": "NFL",
        "entity_type": "nfl_team_season",
        "object_type": "outcome",
        "answer_type": "outcome",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["championship-award-pilot", "mixed-pilot-300"],
        "pipeline_id_start": 610000,
    },
    # Added in Director v0.4, Part J -- ONLY after player_from_clues.py
    # independently proved (25/25 QA-passing puzzles, deterministic,
    # adversarially tested) it can generate real puzzles. The first
    # capability with a mechanic other than `guess` -- see
    # PLAYER_FROM_CLUES_MECHANIC_SPEC.md for the full contract. Notably has
    # NO Game Factory predicate backing it at all (unlike Draft); candidate
    # generation is entirely this adapter's own multi-table clue assembly,
    # dispatched via its own `generate_fn` rather than the guess-shaped path.
    ("identify_player_from_clues", "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"): {
        "adapter": player_from_clues,
        "category": player_from_clues.CATEGORY,
        "generate_fn": _generate_player_from_clues_package,
        "competition_id": "NFL",
        "entity_type": "nfl_player",
        "object_type": "player",
        "answer_type": "player",
        "group_size": None,  # no fixed option count -- see mechanic spec, Part G
        "min_question_count": 1,
        "max_question_count": 25,  # bounded by this milestone's proven generation run (Part L) -- see report
        "supported_difficulties": frozenset({"any"}),  # difficulty is deliberately null; only "any" (no filter) is valid
        "supports_difficulty_filter": False,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["director-v0.4-player-from-clues"],
        # New, distinct ID block for packages generated THROUGH the pipeline
        # (translator -> validator -> registry -> generate_fn), separate from
        # the 620000-620024 block already used by the direct-call canonical
        # Part L deliverable (generated_games/director-v04-player-from-clues.json)
        # -- same "each generation path gets its own reserved block" discipline
        # already used for 600000s (v0.1 direct)/610000s (v0.2+ pipeline).
        "pipeline_id_start": 630000,
    },
    # Added in v1.8, Part F -- the phase's primary acceptance-test capability.
    # See tools/quiz_export/adapters/lineup.py's module docstring for the
    # full audit trail on why this is a real-player-NAMES lineup puzzle, not
    # the colleges-by-position puzzle originally requested (colleges are not
    # viably present in this database for NFL players). Reuses the `guess`
    # mechanic's exact answer contract (Part D); the only new thing is the
    # `POSITION_LINEUP` visual template (Part E) it declares below.
    ("guess", "NFL_OFFENSE_LINEUP", "TEAM_OF_STARTING_LINEUP"): {
        "adapter": lineup_adapter,
        "category": lineup_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "visual_template": "POSITION_LINEUP",
        # Part C: real, disclosed limitations -- feasibility.py promotes a
        # capability with any of these from SUPPORTED to
        # SUPPORTED_WITH_LIMITATIONS rather than silently claiming full
        # support. See tools/quiz_export/adapters/lineup.py's module
        # docstring for the full audit trail behind each one.
        "known_limitations": [
            "Uses real player NAMES, not colleges. A certified NFL<->CFB college identity bridge does "
            "exist (cfb_nfl_identity_bridge_certified), but real coverage against this exact 10-position "
            "lineup shape is far too thin to support a names-hidden college variant -- see "
            "tools.quiz_export.adapters.lineup.lineup_college_coverage() for live current numbers.",
            "Offensive-line positions are shown as one generic 'OL' group of 5 players, not individually "
            "labeled LT/LG/C/RG/RT slots, because the underlying position data does not reliably "
            "distinguish them across every season.",
            "Covers real seasons 2006-2018 only (the range this capability's real candidate pool spans).",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_team_season_lineup",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["director-v1.8-lineup-proof-game"],
        # New reserved ID block -- see the same discipline noted above.
        "pipeline_id_start": 640000,
    },
    # Added during the production deployment + CFB data enrichment
    # operation -- the FIRST CFB domain ever registered in this pipeline
    # (Part 14: reuses the exact same guess mechanic/Game Director core
    # every NFL capability already uses -- no separate CFB Game Factory,
    # no separate registry, no separate mechanic, matching that phase's
    # explicit "preserve Engine v4.0 architecture" mandate). See
    # tools/quiz_export/adapters/cfb_heisman.py's module docstring for the
    # full audit trail: this is the one CFB award domain this database has
    # (Heisman only -- no All-America, no positional awards exist here),
    # and it was chosen specifically because it is completely clean
    # (91/91 rows fully populated, single verification_status, zero
    # duplicate winners) where cfb_coaches, audited the same session, was
    # found to have real, unresolved data-quality problems and was
    # deliberately NOT built on.
    ("guess", "CFB_HEISMAN", "WON_HEISMAN"): {
        "adapter": cfb_heisman_adapter,
        "category": cfb_heisman_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Distractor schools are not season-scoped (cfb_school_seasons, the real per-season CFB "
            "school-participation table, only covers 2002-2025; Heisman goes back to 1935) -- every "
            "option shown is a real school, but a distractor could be one without a program in that "
            "exact historical year.",
            "Covers only the Heisman Trophy -- this database has no All-America, positional, or "
            "conference CFB award data of any kind.",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_player",
        "object_type": "school",
        "answer_type": "school",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 91,  # the real, total size of this domain -- see the adapter's own audit
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["cfb-data-enrichment-heisman-proof"],
        "pipeline_id_start": 650000,
    },
    # Added during the App-Wide Engine Migration operation -- the first
    # capability built on tools/data_refresh/nfl_games_refresh.py's real,
    # automatically-refreshed `games` table (Mission D/E: prove newly
    # ingested game data can become real, generatable, certified content,
    # not just sit in a table). See tools/quiz_export/adapters/
    # nfl_game_result.py's module docstring for the real, disclosed reason
    # this is scoped to game RESULTS, not stat-line/leader questions: this
    # database has no per-game player stats, only season-level, and this
    # project never fabricates numbers to fill a gap.
    ("guess", "NFL_GAME_RESULT", "WON_GAME"): {
        "adapter": nfl_game_result_adapter,
        "category": nfl_game_result_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers only the final result (winner, score, margin) of a real completed game -- this "
            "database has no per-game player statistics (passing/rushing/receiving lines), only "
            "season-level totals, so stat-leader or stat-line questions are not built on this table.",
            "Games that ended in a tie are excluded -- there is no correct 'which team won' answer "
            "for one.",
            "Real candidate survey (App-Wide Engine Migration operation): 6,484 of 7,261 candidate "
            "games (1999-2025) pass every check -- 777 rejected as TEAM_UNRESOLVED (a historical team "
            "code/season combination team_aliases doesn't resolve, e.g. incomplete alias coverage for "
            "a relocated/renamed franchise in that exact year), never silently guessed at.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_game",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["app-wide-engine-migration-nfl-game-result-proof"],
        "pipeline_id_start": 660000,
    },
    # The CFB mirror of the above -- same architecture, same mechanic, same
    # disclosed limitations, built on cfb_games_refresh.py's real
    # `cfb_games_canonical` table (Mission F: prove the same architecture
    # works for CFB, not a separate CFB content engine). Proven against
    # real historical CFB games; the same code path serves current-season
    # games automatically once cfbfastR-data publishes them.
    # Added for the position+college proof-game fix -- the ORIGINAL v1.8
    # acceptance-test request ("guess the NFL team from the colleges its
    # offensive players attended, by position, names hidden"), now
    # genuinely data-backed for 5 skill positions after a real identity-
    # bridge expansion (tools/data_refresh/nfl_college_identity_bridge.py)
    # grew certified NFL<->college coverage from 2,542 to 7,745+ rows using
    # only already-present Engine data. See tools/quiz_export/adapters/
    # lineup_college.py's own module docstring for the full audit trail,
    # including the real, measured, unfixable reason OL is excluded
    # entirely (~10% per-player college coverage -- 0/412 team-seasons ever
    # have all 5 OL certified, even post-expansion).
    ("guess", "NFL_OFFENSE_LINEUP_COLLEGE", "TEAM_OF_STARTING_LINEUP_BY_COLLEGE"): {
        "adapter": lineup_college_adapter,
        "category": lineup_college_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "known_limitations": [
            "Shows only the 5 skill positions (QB, RB, WR, WR, TE) -- the offensive line is not shown at "
            "all. Certified college identity coverage for offensive linemen is too sparse (~10% per player, "
            "211/2,060 shown OL slots) for any real team-season's full offensive line to be honestly "
            "covered; showing OL anyway would mean guessing or fabricating a college, which this project "
            "does not do.",
            "Real candidate pool is a strict subset of the names-based TEAM_OF_STARTING_LINEUP capability's "
            "own 412 team-seasons: 68 of 412 have a certified college for every shown skill-position player "
            "(see tools.quiz_export.adapters.lineup.lineup_college_coverage() for live current numbers).",
            "Covers real seasons 2006-2018 only (the same range the names-based sibling capability covers).",
            "College identity for ~85 of the 5,340 skill-position-slot player-appearances relies on a "
            "moderate-confidence (0.85) unique-name-plus-chronology match (tools/data_refresh/"
            "nfl_college_identity_bridge.py) rather than the stronger 0.994-0.999 exact-ESPN-ID match the "
            "original certified bridge uses -- still never a blind name join (ambiguous names are excluded "
            "outright), but disclosed as a distinct, lower confidence tier.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_team_season_lineup_college",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 68,  # the real, total size of this domain -- see the adapter's own audit
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["position-college-proof-game-fix"],
        "pipeline_id_start": 680000,
    },
    ("guess", "CFB_GAME_RESULT", "WON_GAME"): {
        "adapter": cfb_game_result_adapter,
        "category": cfb_game_result_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers only the final result (winner, score, margin) of a real completed game -- same "
            "real, disclosed data gap as the NFL version: no per-game player statistics exist in "
            "this database.",
            "Games that ended in a tie are excluded.",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_game",
        "object_type": "school",
        "answer_type": "school",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["app-wide-engine-migration-cfb-game-result-proof"],
        "pipeline_id_start": 670000,
    },
    # Historical Engine Enrichment operation: the first capability built on
    # team_game_stats (real per-game team box scores, cross-verified against
    # a real known final score before being trusted -- see
    # tools/data_refresh/nfl_team_game_stats_refresh.py). Genuinely distinct
    # from NFL_GAME_RESULT's WON_GAME: this asks which team gained more
    # total yards, not who won -- these frequently differ (a team can
    # out-gain its opponent and still lose), so it's real new content, not
    # a reskin. The per-game-player-stats gap NFL_GAME_RESULT's own entry
    # above disclosed is now closed for NFL (player_game_stats/
    # team_game_stats both real and populated) -- a future capability could
    # build stat-line/leader questions directly; this one is scoped to the
    # team-level comparison only, proven first.
    ("guess", "NFL_GAME_BOXSCORE", "HAD_MORE_YARDS"): {
        "adapter": nfl_game_boxscore_adapter,
        "category": nfl_game_boxscore_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Compares real total offensive yards (passing + rushing) between the two teams in a real "
            "completed game -- games where both teams gained exactly equal total yards are excluded "
            "(no correct answer for a tie).",
            "16 real game_ids in team_game_stats don't have exactly two teams' rows recorded (a source "
            "data gap, not a bug) -- excluded rather than guessed at.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_game",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["historical-engine-enrichment-boxscore-proof"],
        "pipeline_id_start": 680000,
    },
    # Creator-gap-audit operation: team_game_stats has real sacks/turnovers/
    # penalties columns alongside the total_yards column HAD_MORE_YARDS
    # already used -- these three were sitting unused. Each is its own
    # capability (not a filter on HAD_MORE_YARDS) because the schema has no
    # filter mechanism yet and because each is a genuinely distinct real
    # question, not a variant of one. Shares its adapter's core logic with
    # the two siblings below via tools/quiz_export/adapters/
    # _boxscore_stat_common.py -- see that module's docstring.
    ("guess", "NFL_GAME_BOXSCORE", "HAD_MORE_SACKS"): {
        "adapter": nfl_game_boxscore_sacks_adapter,
        "category": nfl_game_boxscore_sacks_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Compares each team's own real recorded defensive sack total in a real completed game -- "
            "games where both teams recorded exactly the same number of sacks are excluded (no correct "
            "answer for a tie).",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_game",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-boxscore-stats"],
        "pipeline_id_start": 720000,
    },
    ("guess", "NFL_GAME_BOXSCORE", "HAD_FEWER_TURNOVERS"): {
        "adapter": nfl_game_boxscore_turnovers_adapter,
        "category": nfl_game_boxscore_turnovers_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Compares each team's own real recorded turnover total (interceptions thrown + fumbles "
            "lost) in a real completed game -- games where both teams committed exactly the same "
            "number of turnovers are excluded (no correct answer for a tie).",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_game",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-boxscore-stats"],
        "pipeline_id_start": 730000,
    },
    ("guess", "NFL_GAME_BOXSCORE", "HAD_FEWER_PENALTIES"): {
        "adapter": nfl_game_boxscore_penalties_adapter,
        "category": nfl_game_boxscore_penalties_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Compares each team's own real recorded penalty COUNT (not penalty yardage) in a real "
            "completed game -- games where both teams were penalized the same number of times are "
            "excluded (no correct answer for a tie).",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_game",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-boxscore-stats"],
        "pipeline_id_start": 740000,
    },
    # Added after the NFL Wikipedia history import (Super Bowl championships +
    # AP/SB awards, tools/data_refresh/nfl_wikipedia_history_import.py) --
    # importing the data into nfl_championship_events/nfl_season_awards and
    # the shared `relationships` table alone did NOT make it Creator-usable
    # (confirmed directly: neither predicate existed anywhere in this
    # registry, schema.py's allowlist, or mock.py's translator before this).
    # This entry is what makes the Super Bowl GAME itself (who beat whom) a
    # real playable capability -- genuinely distinct from the pre-existing
    # NFL_CHAMPIONSHIP/TEAM_POSTSEASON_RESULT capability above, which asks
    # how one team's season ended, not who won a specific Super Bowl. See
    # tools/quiz_export/adapters/nfl_super_bowl.py's own module docstring
    # for the real, disclosed 2002+ team-identity-resolution limit (24 of 60
    # real Super Bowls are resolved/playable; the other 36 pre-2002 games
    # are honestly rejected as TEAM_UNRESOLVED, never guessed at).
    ("guess", "NFL_SUPER_BOWL", "WON_CHAMPIONSHIP"): {
        "adapter": nfl_super_bowl_adapter,
        "category": nfl_super_bowl_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers real Super Bowl games (SB I-LX) imported from Wikipedia as a secondary structured "
            "source, but team identity only resolves via team_aliases, which covers seasons 2002+ -- "
            "24 of 60 real Super Bowls (2002-2025 seasons) are playable; the other 36 (1966-2001) are "
            "excluded, never guessed at.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_championship_event",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 24,  # the real, total size of this resolved domain -- see the adapter's own audit
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["nfl-wikipedia-history-import"],
        "pipeline_id_start": 700000,
    },
    # The companion capability from the same import: real NFL individual
    # season awards (AP MVP/OPOY/DPOY/OROY/DROY, kept as distinct awarding
    # predicates internally per the import's own explicit requirement never
    # to combine award bodies -- this capability surfaces all of them plus
    # Super Bowl MVP as one "guess the award winner" game, the award name
    # itself stated in each question so nothing is conflated). The first
    # NFL individual-award capability this registry has ever had -- CFB_
    # HEISMAN above was previously the only award-guessing capability at
    # all. See tools/quiz_export/adapters/nfl_season_awards.py's own module
    # docstring for the real, disclosed identity-resolution limit (238 of
    # 369 real award instances resolve to a canonical player, splitting
    # cleanly at roughly the 2000 season -- a canonical_players coverage
    # limit, not a match-quality problem).
    ("guess", "NFL_AWARDS", "WON_AWARD"): {
        "adapter": nfl_season_awards_adapter,
        "category": nfl_season_awards_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers AP MVP/Offensive Player of the Year/Defensive Player of the Year/Offensive Rookie "
            "of the Year/Defensive Rookie of the Year, plus Super Bowl MVP -- imported from Wikipedia "
            "as a secondary structured source. 238 of 369 real award instances resolve to a canonical "
            "player (splits cleanly at roughly the 2000 season, a canonical_players identity-coverage "
            "limit, not a match-quality problem); unresolved award winners are excluded, never guessed at.",
            "Distractor options are drawn only from the pool of other real award winners across these "
            "six award types (never the full player database) -- see the adapter's own module docstring "
            "for why a wider pool was deliberately rejected.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_award",
        "object_type": "nfl_player",
        "answer_type": "player",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["nfl-wikipedia-history-import"],
        "pipeline_id_start": 710000,
    },
    # Creator-gap-audit operation: cfb_champion_school_links (real school-
    # resolved national championship winners, 1936-2025) had zero Creator
    # capabilities despite being the CFB mirror of NFL_SUPER_BOWL above.
    ("guess", "CFB_CHAMPIONSHIP", "WON_CHAMPIONSHIP"): {
        "adapter": cfb_championship_adapter,
        "category": cfb_championship_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "11 of the 91 real championship seasons (1936-2025) have more than one recognized "
            "national champion (real historical selector disagreements, pre-BCS/CFP era) -- those "
            "seasons are excluded entirely, never guessed at.",
            "Distractor schools are not season-scoped (cfb_school_seasons only covers 2002-2025; "
            "championships go back to 1936) -- every option is a real school, but a distractor could "
            "be one without a program in that exact historical year.",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_championship_season",
        "object_type": "school",
        "answer_type": "school",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 91,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-cfb-championship"],
        "pipeline_id_start": 750000,
    },
    # Creator-gap-audit operation: player_season_stats (43,819 rows, fully
    # populated) had zero Creator capabilities before this.
    ("guess", "NFL_SEASON_STATS", "LED_LEAGUE_IN_STAT"): {
        "adapter": nfl_season_stat_leader_adapter,
        "category": nfl_season_stat_leader_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers 5 real statistical categories (passing/rushing/receiving yards, sacks, "
            "interceptions) -- interceptions here is DEFENSIVE interceptions, verified directly "
            "against real 2019 leader data (Stephon Gilmore/Anthony Harris/Tre'Davious White).",
            "Any (season, category) with a real tie for the league lead is excluded entirely, never "
            "guessed at.",
            "Distractors are the real next-highest finishers in that same season and category (not "
            "random players), for a genuinely plausible, hard question.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_season_stat_leaderboard",
        "object_type": "player",
        "answer_type": "player",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-stat-leaders"],
        "pipeline_id_start": 760000,
    },
    # The CFB mirror of the above -- cfb_player_season_stats_real (78,651
    # rows). This table is CLEANER than the NFL one for interceptions (a
    # real, separate `defensive_interceptions` column already exists, no
    # ambiguity to verify).
    ("guess", "CFB_SEASON_STATS", "LED_LEAGUE_IN_STAT"): {
        "adapter": cfb_season_stat_leader_adapter,
        "category": cfb_season_stat_leader_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers 5 real statistical categories (passing/rushing/receiving yards, sacks, "
            "defensive interceptions), 2002-2025 seasons.",
            "Any (season, category) with a real tie for the national lead is excluded entirely, "
            "never guessed at.",
            "Distractors are the real next-highest finishers in that same season and category.",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_season_stat_leaderboard",
        "object_type": "player",
        "answer_type": "player",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-stat-leaders"],
        "pipeline_id_start": 770000,
    },
    # Creator-gap-audit operation: coach_team_seasons (936 rows, 1999-2026,
    # fully populated) had zero Creator capabilities before this.
    ("guess", "NFL_COACHING", "COACHED_TEAM"): {
        "adapter": nfl_coaching_adapter,
        "category": nfl_coaching_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers real (coach, season) -> team records, 1999-2026. Verified directly before "
            "building: zero (coach, season) pairs map to more than one team, so this direction of "
            "the question is never ambiguous (43 team-seasons DO have two coaches, e.g. a mid-season "
            "interim change -- that's a different, unused direction, not a problem for this one).",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_coach_season",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-coaching"],
        "pipeline_id_start": 780000,
    },
    # Creator-gap-audit operation: cfb_transfer_summary_v17 (109,221 rows;
    # 15,495 real multi-school careers) had zero Creator capabilities
    # before this. Reuses the ATTENDED_COLLEGE predicate (same real-world
    # relationship -- player attended school X -- as the NFL_DRAFT/
    # ATTENDED_COLLEGE capability, just a different domain/table, matching
    # the existing WON_GAME-shared-across-NFL/CFB-domains pattern).
    ("guess", "CFB_TRANSFER", "ATTENDED_COLLEGE"): {
        "adapter": cfb_transfer_adapter,
        "category": cfb_transfer_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers only real players with 2+ real schools on record (15,495 of 109,221 total CFB "
            "players) -- a single-school player is not eligible for this capability at all.",
            "This source table has no per-row source_id/verification_status columns (unlike most "
            "tables in this Engine) -- every row is independently cross-checked against the real, "
            "verified `cfb_roster_seasons_real` table instead (100% of eligible rows verified this way).",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_transfer_player",
        "object_type": "school",
        "answer_type": "school",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-transfer-portal"],
        "pipeline_id_start": 790000,
    },
    # Creator-gap-audit operation: cfb_rivalries (48 real, named rivalries)
    # had zero Creator capabilities before this.
    ("guess", "CFB_RIVALRY", "RIVAL_OF"): {
        "adapter": cfb_rivalry_adapter,
        "category": cfb_rivalry_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers 48 real, named rivalries (96 real question directions, since each rivalry can be "
            "asked from either school's perspective) -- a small, fixed, real domain, not exhaustive "
            "of every real CFB rivalry that exists.",
            "Difficulty is fixed at Medium for every question (no real season/recency axis exists for "
            "a standing rivalry fact) rather than a fabricated recency score -- requesting 'easy' or "
            "'hard' will correctly yield zero results rather than mislabel a question.",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_school",
        "object_type": "school",
        "answer_type": "school",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 96,
        "supported_difficulties": frozenset({"any", "medium"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-gap-audit-rivalry"],
        "pipeline_id_start": 800000,
    },
    # Reliability-design Phase 3: NFL Player + Season -> Team, the first
    # vertical slice proof for the conservative relationship compiler
    # (tools/director_v02/compiler.py). This is NOT the draft capability
    # (which team drafted a player) and NOT the postseason capability (how a
    # team's season ended) -- it answers "which real team did this player
    # play FOR in this real season", built on canonical_roster_seasons
    # (60,246 rows, 1999-2026) joined to canonical_players by player_id.
    ("guess", "NFL_PLAYER_SEASON", "TEAM_OF_SEASON"): {
        "adapter": player_season_team_adapter,
        "category": player_season_team_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Season coverage is 2002-2026, not the full 1999-2026 canonical_roster_seasons range -- "
            "team_aliases/team_seasons (the season-accurate franchise-identity source every "
            "team-guessing adapter in this codebase uses) only covers 2002 forward; 1999-2001 "
            "player-seasons are honestly excluded rather than resolved with a guessed team name.",
            "Multi-team seasons (a player with more than one real team the same season, e.g. a "
            "trade) are excluded entirely, not resolved to either team -- see the adapter's real, "
            "counted multi_team_exclusions().",
            "Same-name collisions (two distinct real players sharing a display name in the same "
            "season) are excluded entirely rather than risk an ambiguous prompt -- see "
            "name_collision_exclusions().",
            "This capability proves ROSTER MEMBERSHIP only (canonical_roster_seasons), not game "
            "participation -- generated questions ask which team a player 'was/is ON', never "
            "'played for' (that would claim evidence this capability doesn't actually join). See "
            "compiler.EvidenceType.",
            "A season with zero verified real regular-season weekly evidence yet (e.g. a "
            "preseason-only snapshot for a season that hasn't started) is excluded entirely, never "
            "presented as a completed-season fact -- see the adapter's real season_status(). An "
            "in-progress season is asked in present tense ('is on ... for'); a finished season "
            "(17+ real regular-season weeks) is asked in past tense ('was on ... during').",
            "Eligibility (not test coverage): 55,404 raw real (player, season) pairs 2002-2026; "
            "51,104 eligible after exclusions (eligibility_rate 92.24%, exclusion_rate 7.76% -- "
            "806 multi-team + 588 name-collision + 2,906 future-season exclusions). See the "
            "adapter's real eligibility_report() for live numbers.",
            "RELEASE SAFEGUARD tracked for Phase 7 before PUBLIC_ENABLED: the current COMPLETE-season "
            "rule is a flat >=17-real-weeks floor, correct for every real season 2002-2025 today but "
            "not itself a season-specific schedule check across the 17-week (2002-2020) and 18-week "
            "(2021+) eras -- must be replaced with real schedule-derived per-season completion before "
            "public release.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_player_season",
        "object_type": "team",
        "answer_type": "team",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["reliability-design-phase-3"],
        "pipeline_id_start": 810000,
    },
    # Reliability-design Phase 4: CFB Player + Season -> School, the second
    # real proof of the conservative relationship compiler's generalization
    # (tools/director_v02/compiler.py) -- same "entity+season->object" shape
    # as Phase 3's NFL capability, a different sport, a different identity-
    # resolution strategy (within the Engine's current 2002-2025 data, zero
    # school IDs map to multiple school names -- no relocation/rename
    # history to normalize TODAY; not a claim CFB schools never rename) and
    # a different season-completeness strategy (real aggregate-outcomes
    # presence, not a fixed week-count floor -- CFB has no single real
    # per-season week count).
    ("guess", "CFB_PLAYER_SEASON", "SCHOOL_OF_SEASON"): {
        "adapter": cfb_player_season_school_adapter,
        "category": cfb_player_season_school_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Season coverage is 2004-2025 (cfb_roster_seasons_real's real range).",
            "Multi-school seasons (a player with more than one real school the same season) are "
            "excluded entirely, not resolved to either school -- see the adapter's real, counted "
            "multi_team_exclusions(). Distinct from the existing CFB_TRANSFER capability, which asks "
            "about a real multi-school CAREER (any school they ever attended), never a specific season.",
            "Same-name collisions (two or more distinct real players sharing a display name in the "
            "same season) are excluded entirely -- real, dramatic example found and verified: FIVE "
            "distinct real players named 'Caleb Williams' were active in CFB in 2023 alone (including "
            "the real 2022 Heisman Trophy winner at USC -- Jayden Daniels, not Caleb Williams, won the "
            "2023 Heisman), all five correctly excluded.",
            "This capability proves ROSTER MEMBERSHIP only (cfb_roster_seasons_real), not game "
            "participation -- generated questions ask which school a player 'was/is ON', never "
            "'played for'. See compiler.EvidenceType.",
            "A season with zero real aggregate-outcomes evidence yet (cfb_school_seasons) is excluded "
            "entirely, never presented as a completed-season fact -- see the adapter's real "
            "season_status(). No CFB season is currently mid-progress (ACTIVE) in the real data; only "
            "COMPLETE (2004-2025, all real) or FUTURE (2026+, no data yet) are reachable today.",
            "RELEASE SAFEGUARD tracked for Phase 7 before PUBLIC_ENABLED: aggregate-presence proves "
            "SOME real season data exists, not that the season is FINISHED -- must be replaced with "
            "schedule-derived or explicit finalized-season status so an active season cannot become "
            "eligible after its first aggregate update.",
            "PERFORMANCE TARGET tracked for Phase 5 (not a Phase 4 blocker): a real target_count=5 "
            "generation call takes ~4s (down from a real, measured 116s before the "
            "max_fetched_candidates fix) -- still slow relative to the other 22 capabilities.",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_player_season",
        "object_type": "school",
        "answer_type": "school",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["reliability-design-phase-4"],
        "pipeline_id_start": 820000,
    },
    # Creator Semantic Routing + Who Am I pass: nfl_all_pro_selections
    # (4,964 rows, WIKIPEDIA_STRUCTURED_SECONDARY) had zero Creator
    # capabilities before this -- the exact real gap behind the "First-Team
    # All-Pro" request silently routing to TEAM_OF_SEASON above. Scoped to
    # is_ap=1 (the AP All-Pro team specifically, 3,207 of 4,964 rows) --
    # see tools/quiz_export/adapters/nfl_all_pro.py's own module docstring
    # for why the other selecting bodies mixed into this table are not
    # combined into one implied "the" All-Pro team.
    ("guess", "NFL_ALL_PRO", "SELECTED_ALL_PRO"): {
        "adapter": nfl_all_pro_adapter,
        "category": nfl_all_pro_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers only the AP All-Pro team (is_ap=1, 3,207 of 4,964 real selection rows) -- other "
            "historical selecting bodies present in this table's own selectors_raw column (NYDN, PFW, "
            "SN, UPI, etc.) are not surfaced as their own separate honor.",
            "Distractor player names are drawn from the full AP All-Pro name pool, not scoped to the "
            "same season or position -- position label text is inconsistent across eras (bracketed "
            "footnote markers, spelling variants), so season/position-scoping would starve older "
            "seasons of a real 3-name distractor pool. Same disclosed tradeoff CFB_HEISMAN's school "
            "distractors already make.",
            "Does not require player_id identity resolution (only 2,765 of 4,964 rows resolve) -- the "
            "correct answer and every distractor are the real, source-verified player_name_raw string, "
            "never a canonical_players join.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_all_pro_selection",
        "object_type": "player",
        "answer_type": "player",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-semantic-routing-all-pro"],
        "pipeline_id_start": 830000,
    },
    # Creator Semantic Routing pass: nfl_pro_bowl_selections (4,216 rows,
    # WIKIPEDIA_STRUCTURED_SECONDARY, seasons 1972-2025) -- same real gap,
    # same fix pattern as NFL_ALL_PRO above. Pro Bowl is a genuinely
    # different, distinct honor from All-Pro (different selection process,
    # different real player pool per season), not a filter on it.
    ("guess", "NFL_PRO_BOWL", "SELECTED_PRO_BOWL"): {
        "adapter": nfl_pro_bowl_adapter,
        "category": nfl_pro_bowl_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers all four real Pro Bowl selection tiers (Starter/Reserve/Alternate/Selected) as one "
            "combined 'selected to the Pro Bowl' honor -- the specific tier is shown in the question's "
            "own notes, but is not itself a filterable axis yet.",
            "Distractor player names are drawn from the full Pro Bowl name pool, not scoped to the same "
            "season or position -- same disclosed tradeoff NFL_ALL_PRO's distractors make, for the same "
            "real reason (inconsistent historical position-label text).",
            "Does not require player_id identity resolution (only 3,042 of 4,216 rows resolve) -- same "
            "real-source-name discipline as NFL_ALL_PRO.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_pro_bowl_selection",
        "object_type": "player",
        "answer_type": "player",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-semantic-routing-pro-bowl"],
        "pipeline_id_start": 840000,
    },
    # Creator Semantic Routing pass: nfl_hof_inductees (387 rows, 336
    # players, WIKIPEDIA_STRUCTURED_SECONDARY, class years 1963-2026) --
    # same real gap. Scoped to is_player=1 (336 of 387 rows) -- the other
    # 51 rows are non-player inductees (coaches, contributors, executives),
    # a genuinely different real question this capability does not ask.
    ("guess", "NFL_HALL_OF_FAME", "INDUCTED_HOF"): {
        "adapter": nfl_hof_adapter,
        "category": nfl_hof_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers only player inductees (is_player=1, 336 of 387 real rows) -- non-player Hall of Fame "
            "inductees (coaches, contributors, executives) are excluded entirely, not asked about.",
            "Distractor player names are drawn from the full HOF player-inductee pool, not scoped to the "
            "same class year -- 336 real names is a comfortable pool for this, but a distractor's real "
            "class year is not guaranteed to be close to the correct answer's.",
            "Does not require player_id identity resolution (only 107 of 387 rows resolve) -- same "
            "real-source-name discipline as NFL_ALL_PRO/NFL_PRO_BOWL.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_hof_inductee",
        "object_type": "player",
        "answer_type": "player",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-semantic-routing-hof"],
        "pipeline_id_start": 850000,
    },
    # Creator Semantic Routing pass: nfl_coordinators (64 rows, ALL season
    # 2026, WIKIPEDIA_STRUCTURED_SECONDARY) -- the exact real gap behind the
    # "offensive coordinator"/"defensive coordinator" requests silently
    # routing to TEAM_OF_STARTING_LINEUP above. Two real, distinct roles as
    # two separate predicates (not a filter on one) -- "which team's OC" and
    # "which team's DC" are different real questions with different real
    # answer pools, same discipline the box-score sack/turnover/penalty
    # split already uses. Coverage is genuinely, disclosedly 2026-only --
    # see tools/quiz_export/adapters/nfl_coordinator.py's own module
    # docstring; this capability never implies historical coverage it does
    # not have.
    ("guess", "NFL_OFFENSIVE_COORDINATOR", "COORDINATED_OFFENSE"): {
        "adapter": nfl_offensive_coordinator_adapter,
        "category": nfl_offensive_coordinator_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers the 2026 season ONLY -- nfl_coordinators has no historical seasons on file yet "
            "(32 real offensive-coordinator rows total, one per NFL team). Requesting any other season "
            "is out of bounds for this capability, not silently answered from 2026 data.",
            "Does not require coach_id identity resolution beyond the team_franchise_id already "
            "resolved for all 64 real rows -- the answer is the real, source-verified coach_name_raw.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_coordinator_season",
        "object_type": "coach",
        "answer_type": "coach",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 32,
        "supported_difficulties": frozenset({"any", "medium"}),  # a single real season has no real recency axis
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-semantic-routing-coordinators"],
        "pipeline_id_start": 860000,
    },
    ("guess", "NFL_DEFENSIVE_COORDINATOR", "COORDINATED_DEFENSE"): {
        "adapter": nfl_defensive_coordinator_adapter,
        "category": nfl_defensive_coordinator_adapter.CATEGORY,
        "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers the 2026 season ONLY -- nfl_coordinators has no historical seasons on file yet "
            "(32 real defensive-coordinator rows total, one per NFL team). Requesting any other season "
            "is out of bounds for this capability, not silently answered from 2026 data.",
            "Does not require coach_id identity resolution beyond the team_franchise_id already "
            "resolved for all 64 real rows -- the answer is the real, source-verified coach_name_raw.",
        ],
        "competition_id": "NFL",
        "entity_type": "nfl_coordinator_season",
        "object_type": "coach",
        "answer_type": "coach",
        "group_size": 4,
        "min_question_count": 1,
        "max_question_count": 32,
        "supported_difficulties": frozenset({"any", "medium"}),
        "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-semantic-routing-coordinators"],
        "pipeline_id_start": 870000,
    },
    # Creator Semantic Routing + Who Am I pass: the CFB parity capability
    # for identify_player_from_clues/NFL_PLAYER_IDENTITY above -- a real,
    # independent CFB-native identity universe (cfb_roster_seasons_real +
    # canonical_cfb_players, joined on cfb_player_id only, never on name),
    # not an alias of the NFL one. See tools/director_v04/
    # cfb_player_from_clues.py's own module docstring for the full real
    # data audit (939 real certified All-Americans, real transfer-summary
    # school counts, a real 3+ minute full-universe-scan timing that
    # motivated its own scan_cap performance guard).
    ("identify_player_from_clues", "CFB_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"): {
        "adapter": cfb_player_from_clues,
        "category": cfb_player_from_clues.CATEGORY,
        "generate_fn": _generate_cfb_player_from_clues_package,
        "known_limitations": [
            "Covers real seasons 2004-2025 (cfb_roster_seasons_real's real coverage) -- a player with no "
            "roster rows in that range is not in the universe at all.",
            "No Heisman clue type -- cfb_award_facts' Heisman winners are matched to a school via "
            "WIKIPEDIA_STRUCTURED text, not to a canonical_cfb_players cfb_player_id, so there is no safe, "
            "direct (never-join-on-name) bridge to this capability's identity key yet.",
            "Real, measured performance guard: an unbounded scan of the full 109,221-player universe was "
            "directly timed at 3+ minutes -- generation stops after scanning up to max(target_count*20, "
            "2000) real candidates (in the deterministic seeded order), which is comfortably enough for "
            "every real target_count this project uses but is not an exhaustive scan of every possible "
            "puzzle.",
            "Only 3-5 progressive clues per puzzle, same bound as the NFL sibling capability.",
        ],
        "competition_id": "CFB",
        "entity_type": "cfb_player",
        "object_type": "player",
        "answer_type": "player",
        "group_size": None,
        "min_question_count": 1,
        "max_question_count": 25,
        "supported_difficulties": frozenset({"any"}),
        "supports_difficulty_filter": False,
        "supported_filter_keys": frozenset(),
        "supports_exclusions": False,
        "proven_in": ["creator-semantic-routing-cfb-who-am-i"],
        "pipeline_id_start": 890000,
    },
    # ============================== Creator Capability Completion pass ==============================
    # Converts every remaining data-backed manual-test category from the
    # semantic-routing pass into a real, GENERATION_VERIFIED capability --
    # see each adapter's own module docstring for its full real-data audit.
    ("guess", "CFB_RANKING", "RANKED_IN_POLL"): {
        "adapter": cfb_ranking_adapter, "category": cfb_ranking_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Scoped to poll='AP Top 25' only -- cfb_rankings also carries Coaches/CFP/FCS/D2/D3/BCS polls, "
            "never silently combined into one implied ranking.",
            "Distractors are drawn from the same real (season, week) ranking snapshot, not season-wide.",
        ],
        "competition_id": "CFB", "entity_type": "cfb_ranking", "object_type": "school", "answer_type": "school",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-rankings"], "pipeline_id_start": 900000,
    },
    ("guess", "CFB_UPSET", "RANKING_UPSET"): {
        "adapter": cfb_upset_ranking_adapter, "category": cfb_upset_ranking_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Definition: the losing team was ranked (AP Top 25) that week and the winning team was "
            "unranked or ranked worse -- kept structurally distinct from CFB_UPSET/BETTING_UPSET.",
            "Distractors are scoped to the 112 real schools that have ever appeared in the AP Top 25, not "
            "the full 805-school universe (real, measured distractor-plausibility fix).",
        ],
        "competition_id": "CFB", "entity_type": "cfb_game", "object_type": "school", "answer_type": "school",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-upsets"], "pipeline_id_start": 901000,
    },
    ("guess", "CFB_UPSET", "BETTING_UPSET"): {
        "adapter": cfb_upset_betting_adapter, "category": cfb_upset_betting_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Definition: the real pregame consensus betting underdog (provider='consensus') won outright "
            "-- kept structurally distinct from CFB_UPSET/RANKING_UPSET.",
            "'Spread' is the source's own recorded value, never labeled 'closing line' (the source does "
            "not itself distinguish closing vs. opening beyond spread/spread_open column names).",
            "Distractors are scoped to other real recorded betting-upset winners by this same definition.",
        ],
        "competition_id": "CFB", "entity_type": "cfb_game", "object_type": "school", "answer_type": "school",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-upsets"], "pipeline_id_start": 902000,
    },
    ("guess", "NFL_SCORING_PLAY", "FIRST_TOUCHDOWN_SCORER"): {
        "adapter": nfl_first_touchdown_adapter, "category": nfl_first_touchdown_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Covers only touchdowns with a real resolved receiver_player_key (91.8% of pass TDs) or "
            "rusher_player_key (91.0% of rush TDs) -- unresolved plays and defensive/special-teams "
            "touchdowns (no offensive scorer key) are excluded, never guessed at.",
            "Answer is GAME -> WHO SCORED, never downgraded to GAME -> WHO WON.",
        ],
        "competition_id": "NFL", "entity_type": "nfl_play", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-pbp-scoring"], "pipeline_id_start": 903000,
    },
    ("guess", "NFL_DEFENSIVE_EVENT", "RECORDED_SACK"): {
        "adapter": nfl_sack_adapter, "category": nfl_sack_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Real resolution rate measured directly: 27,420/30,510 (89.9%) -- unresolved sacks are excluded, never guessed at."],
        "competition_id": "NFL", "entity_type": "nfl_defensive_play", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-defensive-events"], "pipeline_id_start": 904000,
    },
    ("guess", "NFL_DEFENSIVE_EVENT", "RECORDED_INTERCEPTION"): {
        "adapter": nfl_interception_adapter, "category": nfl_interception_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Real resolution rate measured directly: 11,826/13,354 (88.6%) -- unresolved interceptions are excluded, never guessed at."],
        "competition_id": "NFL", "entity_type": "nfl_defensive_play", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-defensive-events"], "pipeline_id_start": 905000,
    },
    ("guess", "NFL_DEFENSIVE_EVENT", "FORCED_FUMBLE"): {
        "adapter": nfl_forced_fumble_adapter, "category": nfl_forced_fumble_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Uses the primary (first) forced-fumble player field only -- a real, rare second-forcer field exists and is not used, to keep one clear answer."],
        "competition_id": "NFL", "entity_type": "nfl_defensive_play", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-defensive-events"], "pipeline_id_start": 906000,
    },
    ("guess", "NFL_DEFENSIVE_EVENT", "RECOVERED_FUMBLE"): {
        "adapter": nfl_fumble_recovery_adapter, "category": nfl_fumble_recovery_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Uses the primary (first) recovery player field only. Either team can recover a fumble -- this asks who recovered it, not which team's defense did."],
        "competition_id": "NFL", "entity_type": "nfl_defensive_play", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-defensive-events"], "pipeline_id_start": 907000,
    },
    ("guess", "NFL_DRIVE", "DRIVE_RESULT"): {
        "adapter": nfl_drive_result_adapter, "category": nfl_drive_result_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "No CFB equivalent exists -- this Engine has no cfb_drives-shaped table at all (cfb_plays has "
            "a drive_id column but no separate drive-level result/summary table); a real, disclosed data "
            "gap, not an unwritten adapter.",
            "Answer is one of 9 real result categories (Punt/Touchdown/Field goal/Turnover/End of half/"
            "Turnover on downs/Missed field goal/Opp touchdown/Safety).",
        ],
        "competition_id": "NFL", "entity_type": "nfl_drive", "object_type": "outcome", "answer_type": "outcome",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-drives"], "pipeline_id_start": 908000,
    },
    ("guess", "CFB_STAT_COMPARISON", "RUSHING_COMPARISON"): {
        "adapter": cfb_rushing_compare_adapter, "category": cfb_rushing_compare_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Both players are always from the same real (season, week) -- the word 'week' alone never routes here from a Weekly Pick'em request; this is a stat comparison, not a matchup pick.", "Ties are excluded, never resolved either way."],
        "competition_id": "CFB", "entity_type": "cfb_player_game_pair", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-stat-comparison"], "pipeline_id_start": 909000,
    },
    ("guess", "CFB_STAT_COMPARISON", "PASSING_COMPARISON"): {
        "adapter": cfb_passing_compare_adapter, "category": cfb_passing_compare_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Same real same-week pairing and tie-exclusion discipline as CFB_STAT_COMPARISON/RUSHING_COMPARISON."],
        "competition_id": "CFB", "entity_type": "cfb_player_game_pair", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-stat-comparison"], "pipeline_id_start": 910000,
    },
    ("guess", "CFB_STAT_COMPARISON", "RECEIVING_COMPARISON"): {
        "adapter": cfb_receiving_compare_adapter, "category": cfb_receiving_compare_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Same real same-week pairing and tie-exclusion discipline as CFB_STAT_COMPARISON/RUSHING_COMPARISON."],
        "competition_id": "CFB", "entity_type": "cfb_player_game_pair", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-stat-comparison"], "pipeline_id_start": 911000,
    },
    ("guess", "NFL_GAME_LEADER", "RUSHING_LEADER"): {
        "adapter": nfl_rushing_leader_adapter, "category": nfl_rushing_leader_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Objective, disclosed definition: the real player with the most rushing yards on their team in one real game. A real tie for the team lead is excluded, never arbitrarily broken."],
        "competition_id": "NFL", "entity_type": "nfl_team_game", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-top-performer"], "pipeline_id_start": 912000,
    },
    ("guess", "NFL_GAME_LEADER", "PASSING_LEADER"): {
        "adapter": nfl_passing_leader_adapter, "category": nfl_passing_leader_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Same objective team-lead definition and tie-exclusion discipline as NFL_GAME_LEADER/RUSHING_LEADER, for passing yards."],
        "competition_id": "NFL", "entity_type": "nfl_team_game", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-top-performer"], "pipeline_id_start": 913000,
    },
    ("guess", "NFL_GAME_LEADER", "RECEIVING_LEADER"): {
        "adapter": nfl_receiving_leader_adapter, "category": nfl_receiving_leader_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Same objective team-lead definition and tie-exclusion discipline as NFL_GAME_LEADER/RUSHING_LEADER, for receiving yards."],
        "competition_id": "NFL", "entity_type": "nfl_team_game", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-top-performer"], "pipeline_id_start": 914000,
    },
    ("guess", "CFB_GAME_LEADER", "RUSHING_LEADER"): {
        "adapter": cfb_rushing_leader_adapter, "category": cfb_rushing_leader_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Same objective, disclosed team-lead definition as NFL_GAME_LEADER/RUSHING_LEADER, for real CFB team-games."],
        "competition_id": "CFB", "entity_type": "cfb_team_game", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-top-performer"], "pipeline_id_start": 915000,
    },
    ("guess", "CFB_GAME_LEADER", "PASSING_LEADER"): {
        "adapter": cfb_passing_leader_adapter, "category": cfb_passing_leader_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Same objective, disclosed team-lead definition as NFL_GAME_LEADER/RUSHING_LEADER, for real CFB team-games, passing yards."],
        "competition_id": "CFB", "entity_type": "cfb_team_game", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-top-performer"], "pipeline_id_start": 916000,
    },
    ("guess", "CFB_GAME_LEADER", "RECEIVING_LEADER"): {
        "adapter": cfb_receiving_leader_adapter, "category": cfb_receiving_leader_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": ["Same objective, disclosed team-lead definition as NFL_GAME_LEADER/RUSHING_LEADER, for real CFB team-games, receiving yards."],
        "competition_id": "CFB", "entity_type": "cfb_team_game", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 100,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-top-performer"], "pipeline_id_start": 917000,
    },
    ("guess", "CFB_TRANSFER_PATH", "ORDERED_PATH_NFL_BRIDGED"): {
        "adapter": cfb_transfer_path_adapter, "category": cfb_transfer_path_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Real, disclosed double-name-join: cfb_transfer_summary_v17's own display_name joined to "
            "nfl_cfb_player_links (match_status='AUTO_HIGH', itself already a bare EXACT_NORMALIZED_NAME "
            "match) -- neither table carries a shared id, and this Engine has no other NFL<->CFB player bridge.",
            "Real, measured eligible pool: 12 total real players (this Engine's NFL<->CFB bridge has only "
            "124 rows total) -- small, disclosed, never padded.",
            "The ordered relationship is the point: every distractor is a real path in a real-but-wrong "
            "order or a different real player's correctly-ordered path, never a same-player membership question.",
        ],
        "competition_id": "CFB", "entity_type": "cfb_transfer_player", "object_type": "ordered_path", "answer_type": "ordered_path",
        "group_size": 4, "min_question_count": 1, "max_question_count": 12,
        "supported_difficulties": frozenset({"any", "easy", "medium", "hard"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-transfer-path"], "pipeline_id_start": 918000,
    },
    ("guess", "NFL_ALL_PRO_COLLEGE", "ATTENDED_COLLEGE_ALL_PRO"): {
        "adapter": nfl_all_pro_college_adapter, "category": nfl_all_pro_college_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Real, measured multi-valid-answer risk: 107 real colleges have more than one distinct real "
            "AP All-Pro alumnus -- those colleges are excluded outright (AMBIGUOUS_MULTIPLE_HONORED_ALUMNI), "
            "never resolved by arbitrarily picking one.",
            "Real eligible pool: 58 unique candidates (of 842 real All-Pro-player-season rows with a "
            "resolved college) after the ambiguity exclusion.",
            "Never strips the All-Pro qualifier -- the question is always 'which All-Pro', never generic college trivia.",
        ],
        "competition_id": "NFL", "entity_type": "nfl_all_pro_player", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 58,
        "supported_difficulties": frozenset({"any", "medium"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-honors-college"], "pipeline_id_start": 919000,
    },
    ("guess", "NFL_PRO_BOWL_COLLEGE", "ATTENDED_COLLEGE_PRO_BOWL"): {
        "adapter": nfl_pro_bowl_college_adapter, "category": nfl_pro_bowl_college_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Same real multi-valid-answer exclusion as NFL_ALL_PRO_COLLEGE -- a college with more than "
            "one real Pro Bowl alumnus is excluded outright.",
            "Real eligible pool: 75 unique candidates (of 1,092 real Pro-Bowl-player-season rows with a resolved college).",
        ],
        "competition_id": "NFL", "entity_type": "nfl_pro_bowl_player", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 75,
        "supported_difficulties": frozenset({"any", "medium"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-honors-college"], "pipeline_id_start": 920000,
    },
    ("guess", "NFL_HOF_COLLEGE", "ATTENDED_COLLEGE_HOF"): {
        "adapter": nfl_hof_college_adapter, "category": nfl_hof_college_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Same real multi-valid-answer exclusion as NFL_ALL_PRO_COLLEGE -- a college with more than "
            "one real Hall of Fame alumnus is excluded outright.",
            "Real eligible pool: 44 unique candidates (of 104 real HOF players with a resolved college).",
        ],
        "competition_id": "NFL", "entity_type": "nfl_hof_player", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 44,
        "supported_difficulties": frozenset({"any", "medium"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-honors-college"], "pipeline_id_start": 921000,
    },
    ("guess", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_ALL_PRO"): {
        "adapter": cfb_all_american_to_all_pro_adapter, "category": cfb_all_american_to_all_pro_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Real, disclosed double-name-join (same methodology as CFB_TRANSFER_PATH -- see that "
            "capability's own known_limitations for the full disclosure).",
            "Real, measured eligible pool: 4 total real players (Reggie Bush, Christian McCaffrey, Lamar "
            "Jackson, Aidan Hutchinson) -- the smallest real pool in this registry, disclosed, never padded.",
        ],
        "competition_id": "NFL", "entity_type": "cross_league_player", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 4,
        "supported_difficulties": frozenset({"any", "medium"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-cross-league-honors"], "pipeline_id_start": 922000,
    },
    ("guess", "CROSS_LEAGUE_HONORS", "ALL_AMERICAN_TO_PRO_BOWL"): {
        "adapter": cfb_all_american_to_pro_bowl_adapter, "category": cfb_all_american_to_pro_bowl_adapter.CATEGORY, "generate_fn": _generate_guess_package,
        "known_limitations": [
            "Same real double-name-join methodology as CROSS_LEAGUE_HONORS/ALL_AMERICAN_TO_ALL_PRO.",
            "Real, measured eligible pool: 11 total real players.",
            "All-American -> Hall of Fame is NOT registered -- real, measured overlap is 0 (a genuine "
            "data-gap limitation, not an unwritten adapter).",
        ],
        "competition_id": "NFL", "entity_type": "cross_league_player", "object_type": "player", "answer_type": "player",
        "group_size": 4, "min_question_count": 1, "max_question_count": 11,
        "supported_difficulties": frozenset({"any", "medium"}), "supports_difficulty_filter": True,
        "supported_filter_keys": frozenset(), "supports_exclusions": False,
        "proven_in": ["creator-capability-completion-cross-league-honors"], "pipeline_id_start": 923000,
    },
}


def lookup(mechanic: str, domain: str, predicate: str) -> dict | None:
    return CAPABILITY_REGISTRY.get((mechanic, domain, predicate))


def all_capability_keys() -> list[tuple[str, str, str]]:
    return list(CAPABILITY_REGISTRY.keys())
