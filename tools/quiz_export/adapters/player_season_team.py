"""NFL Player + Season -> Team (compiler-generated) -- Phase 3 vertical slice.

This module's entire generation/evaluation behavior is produced by
tools/director_v02/compiler.py's compile_adapter() from the RelationshipSpec
below -- this file itself contains no hand-written query or evaluation
logic, only the declarative spec and the mechanical re-exports needed to
satisfy the standard adapter interface every other tools/quiz_export/
adapters/*.py module also satisfies (CATEGORY, TRACK_ENTITY, safety_check,
fetch_ordered_candidates, evaluate) so game_director_v01.
generate_package_from_spec() and catalog.verify_registry_consistency()'s
`importlib.import_module(runtime_adapter_module)` check both work unchanged.

Real data investigation behind this spec (Phase 3):
- canonical_roster_seasons (60,246 rows, 1999-2026, all SOURCE_BACKED,
  source_id in {NFLVERSE_DATA, NFLVERSE_ROSTERS}) is the real membership
  table; canonical_players (17,113 rows) the real, already-deduplicated
  identity table -- joined on player_id, never on name.
- team_aliases/team_seasons' real coverage is 2002-2026 (not 1999-2026) --
  MIN_SEASON is honestly set to match, excluding 1999-2001 rather than
  fabricating a franchise name for seasons this Engine has no team-identity
  data for.
- team_aliases is the same season-accurate franchise/name source every
  other team-guessing adapter in this codebase already uses
  (resolve_franchise/teams_active_in_season, tools/quiz_export/adapters/
  draft.py) -- reused unchanged here, not reinvented.
- Three real normalization gaps found and handled explicitly: canonical_
  roster_seasons uses a single stable modern code across each relocated/
  renamed franchise's whole history, while team_aliases correctly splits
  each by season -- Rams ("LAR" always vs. "STL" 2002-2015 / "LA" 2016+),
  Chargers ("LAC" always vs. "SD" 2002-2016 / "LAC" 2017+), and Raiders
  ("LV" always vs. "OAK" 2002-2019 / "LV" 2020+). Found by actually running
  the adapter and inspecting its real TEAM_UNRESOLVED rejections, not
  assumed from the Rams case alone -- an earlier version of this spec only
  had the Rams override and silently lost 402 real, resolvable early-2000s
  Chargers/Raiders player-seasons to TEAM_UNRESOLVED before this was
  caught. All three overrides resolve via franchise_id directly rather than
  guessing a season-blind code -- verified against both eras of each
  franchise before being trusted.
"""
from tools.director_v02 import compiler

MIN_SEASON = 2002
MAX_SEASON = 2026

SPEC = compiler.RelationshipSpec(
    capability_id="NFL_PLAYER_SEASON__TEAM_OF_SEASON",
    category="NFL Player Season-Team",
    competition_id="NFL",
    membership_table="canonical_roster_seasons",
    entity_table="canonical_players",
    entity_id_column="player_id",
    entity_name_column="display_name",
    season_column="season",
    team_code_column="team_code",
    required_verification_status="SOURCE_BACKED",
    required_source_ids=("NFLVERSE_DATA", "NFLVERSE_ROSTERS"),
    min_season=MIN_SEASON,
    max_season=MAX_SEASON,
    entity_label="player",
    team_code_overrides={"LAR": "FR_LAR", "LAC": "FR_LAC", "LV": "FR_LV"},
)

_adapter = compiler.compile_adapter(SPEC)

CATEGORY = _adapter.CATEGORY
TRACK_ENTITY = _adapter.TRACK_ENTITY
REQUIRED_SOURCE_IDS = SPEC.required_source_ids


def safety_check(c):
    return _adapter.safety_check(c)


def fetch_ordered_candidates(c, seed: str):
    return _adapter.fetch_ordered_candidates(c, seed)


def evaluate(c, row, rng, guard):
    return _adapter.evaluate(c, row, rng, guard)


def multi_team_exclusions() -> int:
    """Real count from the most recent fetch_ordered_candidates() call."""
    return _adapter.multi_team_exclusions


def name_collision_exclusions() -> int:
    return _adapter.name_collision_exclusions


def raw_pair_count() -> int:
    return _adapter.raw_pair_count


def eligibility_report() -> dict:
    """raw_candidate_count / eligible_candidate_count / excluded_candidate_count
    / eligibility_rate / exclusion_rate -- real, computed from the most
    recent fetch_ordered_candidates() call. This is ELIGIBILITY, distinct
    from health_probe.py's test_sample_rate (what fraction of the eligible
    pool one certification run sampled) -- see compiler.py's
    eligibility_report() docstring for why the two must never be
    conflated (the mistake this function's naming exists to correct)."""
    return _adapter.eligibility_report()
