"""CFB Player + Season -> School (compiler-generated) -- Phase 4 vertical
slice, the second real proof of tools/director_v02/compiler.py's
generalization claim (its own docstring: "Reusing this same compiler for a
DIFFERENT relationship of the same shape... would be the real proof this
generalizes").

Real data investigation behind this spec (Phase 4):
- cfb_roster_seasons_real (282,124 rows, 2004-2025, all SOURCE_BACKED,
  source_id=SPORTSDATAVERSE_CFB) is the real membership table;
  canonical_cfb_players (109,221 rows) the real identity table -- joined on
  cfb_player_id, never on name. Zero unjoined rows (perfect referential
  integrity, checked directly).
- Within the Engine's current 2002-2025 data, zero school_ids map to more
  than one distinct school_name across cfb_school_seasons' full range
  (checked directly) -- a statement about what THIS dataset currently
  contains, not a claim that CFB schools never rename in the real world.
  No season-scoped franchise resolution or code-history override is needed
  today. identity_resolution_strategy="stable_identity_table" resolves
  school_id -> schools.school_name with a direct lookup; distractors are
  drawn from cfb_school_seasons (schools with a real recorded season that
  year), the same real season-scoping discipline the NFL capability uses
  via team_aliases.
- Season completeness uses "aggregate_presence" (cfb_school_seasons real
  row presence), not a fixed week-count floor -- CFB has no single
  real per-season week count (division/conference/playoff-format variation,
  e.g. the 2020 COVID-shortened season, and cfb_games_canonical's own
  bowl_name/playoff_round_name coverage is genuinely sparse for older
  seasons, checked directly, so it cannot be used as a universal terminal
  marker). This deliberately avoids repeating the exact "flat threshold"
  flaw the owner flagged for the NFL capability (Phase 3 closeout) -- see
  compiler.py's RelationshipSpec.season_completeness_strategy docstring.
  RELEASE SAFEGUARD tracked for Phase 7 before PUBLIC_ENABLED (owner-
  required): presence alone proves SOME real aggregate data exists, not
  that the season is FINISHED -- if cfb_school_seasons is ever updated
  incrementally mid-season, an active season could become eligible (and
  phrased in the past tense) after its first aggregate update. Must be
  replaced with a schedule-derived or explicit finalized-season status
  check before public release.
- Real, dramatic same-name-collision finding: FIVE distinct real players
  named "Caleb Williams" were active in CFB in 2023 alone (Furman, Lamar,
  Pittsburgh, Tennessee, USC -- including Caleb Williams, the real 2022
  Heisman Trophy winner, at USC) -- all five correctly excluded by the
  existing name-collision rule, proving the protection matters even for a
  single, real, famous name. (Jayden Daniels, not Caleb Williams, won the
  2023 Heisman.)
- PERFORMANCE TARGET tracked for Phase 5 (not a Phase 4 blocker): a real
  target_count=5 generation call takes ~4s after the max_fetched_candidates
  fix below (was 116s) -- still slow relative to the other 22 capabilities.
"""
from tools.director_v02 import compiler

MIN_SEASON = 2004  # cfb_roster_seasons_real's real coverage floor
MAX_SEASON = 2025

SPEC = compiler.RelationshipSpec(
    capability_id="CFB_PLAYER_SEASON__SCHOOL_OF_SEASON",
    category="CFB Player Season-School",
    competition_id="CFB",
    membership_table="cfb_roster_seasons_real",
    entity_table="canonical_cfb_players",
    entity_id_column="cfb_player_id",
    entity_name_column="display_name",
    season_column="season",
    team_code_column="school_id",
    required_verification_status="SOURCE_BACKED",
    required_source_ids=("SPORTSDATAVERSE_CFB",),
    min_season=MIN_SEASON,
    max_season=MAX_SEASON,
    entity_label="player",
    object_label="school",
    evidence_type=compiler.EvidenceType.ROSTER_MEMBERSHIP,
    season_completeness_strategy="aggregate_presence",
    aggregate_presence_table="cfb_school_seasons",
    aggregate_presence_season_column="season",
    identity_resolution_strategy="stable_identity_table",
    identity_table="schools",
    identity_id_column="school_id",
    identity_name_column="school_name",
    identity_pool_table="cfb_school_seasons",
    identity_pool_season_column="season",
    identity_pool_id_column="school_id",
    # Real, measured performance safeguard: this capability's real eligible
    # pool (269,882) is ~5x the NFL capability's (51,104), and
    # generate_package_from_spec() evaluates every returned candidate
    # unconditionally -- a real target_count=5 call took 116s before this
    # cap (confirmed by direct timing). 5,000 (post-shuffle, chosen after
    # every real exclusion count is already computed from the full set --
    # see max_fetched_candidates' own docstring) preserves huge real
    # diversity while keeping generation well within a normal request
    # timeout. eligibility_report() still reports the true 269,882, never
    # this number.
    max_fetched_candidates=5000,
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
    return _adapter.multi_team_exclusions


def name_collision_exclusions() -> int:
    return _adapter.name_collision_exclusions


def future_season_exclusions() -> int:
    return _adapter.future_season_exclusions


def raw_pair_count() -> int:
    return _adapter.raw_pair_count


def season_status(c, season: int) -> str:
    from tools.director_v02.compiler import _season_status
    return _season_status(c, SPEC, season, _cache=_adapter._season_status_cache)


def eligibility_report() -> dict:
    return _adapter.eligibility_report()
