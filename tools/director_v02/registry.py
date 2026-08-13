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
from tools.quiz_export.adapters import cfb_game_result as cfb_game_result_adapter  # noqa: E402
from tools.quiz_export.adapters import cfb_heisman as cfb_heisman_adapter  # noqa: E402
from tools.quiz_export.adapters import championship as championship_adapter  # noqa: E402
from tools.quiz_export.adapters import draft as draft_adapter  # noqa: E402
from tools.quiz_export.adapters import lineup as lineup_adapter  # noqa: E402
from tools.quiz_export.adapters import lineup_college as lineup_college_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_game_boxscore as nfl_game_boxscore_adapter  # noqa: E402
from tools.quiz_export.adapters import nfl_game_result as nfl_game_result_adapter  # noqa: E402

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
}


def lookup(mechanic: str, domain: str, predicate: str) -> dict | None:
    return CAPABILITY_REGISTRY.get((mechanic, domain, predicate))


def all_capability_keys() -> list[tuple[str, str, str]]:
    return list(CAPABILITY_REGISTRY.keys())
