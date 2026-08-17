"""Conservative relationship compiler -- Phase 3's first real instantiation
of the "compiler-generated adapter" concept from the original approved
architecture (deliberately deferred through Phases 1-2: "do not build the
compiler... during Phase 1/2").

Deliberately narrow, per the "conservative compiler" instruction: this
compiles exactly ONE relationship SHAPE --

    one real entity, scoped to one season, maps to exactly one team that
    season, via a membership table joined to an entity-identity table (both
    keyed by a real, already-canonical id -- never by name), with the team
    normalized to a season-accurate franchise via team_aliases.

-- not a general query-building engine. A RelationshipSpec instance
describes the shape's real, checked parameters (source tables, columns,
season bounds, verification status, any evidence-based team-code
overrides); compile_adapter() turns that spec into a real, working
CompiledAdapter implementing the exact same interface every hand-written
tools/quiz_export/adapters/*.py module implements (safety_check /
fetch_ordered_candidates / evaluate / CATEGORY / TRACK_ENTITY), so
game_director_v01.generate_package_from_spec() drives it with zero changes.

A capability's adapter MODULE (e.g. tools/quiz_export/adapters/
player_season_team.py) is a thin, mechanical re-export of one
compile_adapter(SPEC) call -- it exists only so catalog.
verify_registry_consistency()'s `importlib.import_module(runtime_adapter_module)`
check (a real, load-bearing part of Phase 2's registry/adapter consistency
enforcement) has a real, static, importable module to point at. All actual
behavior lives here, generated from the spec, not hand-authored per capability.

Reusing this same compiler for a DIFFERENT relationship of the same shape
(e.g. a future CFB player+season->school capability) would be the real proof
this generalizes -- that reuse is left to a later phase; Phase 3 proves the
shape once, for real, end-to-end, against NFL_PLAYER_SEASON/TEAM_OF_SEASON.

Three exclusion rules are baked into fetch_ordered_candidates(), all
conservative (exclude and count, never guess):

1. Multi-team seasons: a real (entity_id, season) pair with more than one
   distinct team_code that season is excluded entirely -- Phase 3 does not
   attempt to pick "the" team for a traded/multi-stint player-season.
2. Same-name collisions: two distinct real entities sharing a (name, season)
   among the single-team-season set would make the generated prompt
   ("Name -- Season") genuinely ambiguous to answer -- both are excluded.
3. Seasons with no verified regular-season weekly evidence yet ("FUTURE" --
   see EvidenceType/_season_status below) are excluded entirely, never
   treated as completed-season facts.

--- EVIDENCE SEMANTICS (owner-required correction, Phase 3 closeout) -------
`canonical_roster_seasons` proves ROSTER MEMBERSHIP for a season -- it does
NOT prove the player actually appeared in a game. The generated question
wording and `evidence_type` reflect exactly that:

  ROSTER_MEMBERSHIP  -- this capability's evidence today. "was on / is on
                        the roster", never "played for".
  GAME_PARTICIPATION -- would require joining a real per-game appearance
                        source (e.g. player_game_stats) for THIS entity in
                        THIS season -- not done by this capability; a
                        future capability that does this join may use
                        "played" wording, but only then.
  STARTED_GAME       -- a strictly narrower claim than GAME_PARTICIPATION
                        (a starting-lineup record) -- same rule: only a
                        capability that actually joins that evidence may
                        claim it.

A season's own COMPLETENESS is a separate, real, measured fact: `weekly_
evidence_table` (player_game_stats for this capability) is checked for real
regular-season week rows for that season, independent of entity. Zero such
rows -> FUTURE (excluded from the pool entirely -- a preseason/training-camp
roster snapshot is not a completed-season fact). 1-16 rows worth of weeks ->
ACTIVE (present tense: "is on ... for"). Reaching the real, verified
17-week regular-season floor (true for every season 2002-2025 in this
capability's range, confirmed directly, never assumed per-era) -> COMPLETE
(past tense: "was on ... during")."""
from __future__ import annotations

from dataclasses import dataclass, field

from tools.quiz_export import difficulty as difficulty_mod
from tools.quiz_export import engine, safety, serializer
from tools.quiz_export.adapters.draft import resolve_franchise, teams_active_in_season


class EvidenceType:
    """What kind of real evidence backs a generated round's relationship
    claim -- stored internally (_audit / package provenance), never
    silently upgraded to a stronger claim than the join actually proves."""
    ROSTER_MEMBERSHIP = "ROSTER_MEMBERSHIP"
    GAME_PARTICIPATION = "GAME_PARTICIPATION"
    STARTED_GAME = "STARTED_GAME"


# A season needs real weekly regular-season evidence covering at least this
# many distinct weeks before it counts as COMPLETE -- verified directly
# against player_game_stats for every real season 2002-2025 in this
# capability's range (every one reaches 17 or 18; 17 is the real, checked
# floor, never assumed from a hardcoded per-era games-played constant).
_COMPLETE_SEASON_MIN_WEEKS = 17


@dataclass(frozen=True)
class RelationshipSpec:
    capability_id: str
    category: str
    competition_id: str
    membership_table: str          # e.g. "canonical_roster_seasons"
    entity_table: str              # e.g. "canonical_players"
    entity_id_column: str          # e.g. "player_id" -- must exist on both tables
    entity_name_column: str        # e.g. "display_name" (on entity_table)
    season_column: str             # e.g. "season" (on membership_table)
    team_code_column: str          # e.g. "team_code" (on membership_table)
    required_verification_status: str
    required_source_ids: tuple     # one or more approved source_id values
    min_season: int                # real, checked lower bound (never guessed)
    max_season: int
    entity_label: str              # e.g. "player" -- used in the generated question text
    evidence_type: str = EvidenceType.ROSTER_MEMBERSHIP  # what THIS capability's join actually proves
    # Real, weekly-grain source used ONLY to determine season completeness
    # (never joined per-entity -- that would upgrade evidence_type, which
    # this capability deliberately does not do). None of these three
    # columns need to be on membership_table/entity_table.
    weekly_evidence_table: str | None = None            # e.g. "player_game_stats"
    weekly_evidence_season_column: str | None = None     # e.g. "season"
    weekly_evidence_week_column: str | None = None        # e.g. "week"
    weekly_evidence_season_type_column: str | None = None  # e.g. "season_type"
    weekly_evidence_regular_season_value: str | None = None  # e.g. "REG"
    team_code_overrides: dict = field(default_factory=dict)  # {roster_code: franchise_id}, evidence-based only


def _phrase_membership_question(*, competition_id: str, entity_name: str, team_full_name: str,
                                 season: int, season_status: str) -> tuple[str, str]:
    """Pure, DB-free wording function -- independently testable without
    needing real franchise/distractor resolution. `season_status` must be
    "ACTIVE" or "COMPLETE" (never "FUTURE" -- that's excluded upstream).
    Returns (question, notes)."""
    if season_status == "ACTIVE":
        question = f"Which {competition_id} team is {entity_name} on for the {season} season?"
        notes = f"{entity_name} is on the {team_full_name} roster for the {season} season."
    else:  # COMPLETE
        question = f"Which {competition_id} team was {entity_name} on during the {season} season?"
        notes = f"{entity_name} was on the {team_full_name} roster during the {season} season."
    return question, notes


def _season_status(c, spec: RelationshipSpec, season: int, *, _cache: dict) -> str:
    """Returns "COMPLETE", "ACTIVE", or "FUTURE" for a real season, driven
    entirely by real weekly-evidence rows -- never wall-clock date, so this
    self-corrects automatically as real data is refreshed (a season that is
    FUTURE today becomes ACTIVE, then COMPLETE, purely by the normal data
    pipeline adding real weeks -- no code change needed). `_cache` is a
    plain dict the caller keeps alive across a whole fetch/evaluate run, so
    this is one query per distinct season, not one per candidate row."""
    if season in _cache:
        return _cache[season]
    if not spec.weekly_evidence_table:
        _cache[season] = "COMPLETE"  # no weekly-evidence source configured -- nothing to gate on
        return _cache[season]
    max_week = c.execute(
        f"SELECT MAX({spec.weekly_evidence_week_column}) FROM {spec.weekly_evidence_table} "
        f"WHERE {spec.weekly_evidence_season_column}=? AND {spec.weekly_evidence_season_type_column}=?",
        (season, spec.weekly_evidence_regular_season_value),
    ).fetchone()[0]
    if max_week is None:
        status = "FUTURE"
    elif max_week >= _COMPLETE_SEASON_MIN_WEEKS:
        status = "COMPLETE"
    else:
        status = "ACTIVE"
    _cache[season] = status
    return status


def _normalize_franchise(c, spec: RelationshipSpec, team_code: str, season: int):
    """Resolves a membership-table team_code to a season-accurate franchise.
    Most codes go straight through team_aliases (resolve_franchise, the same
    helper every other team-guessing adapter in this codebase already uses).
    `team_code_overrides` exists only for a real, checked divergence: a
    membership table using one stable code across a franchise's whole
    history while team_aliases correctly splits it by season (e.g. the Rams:
    canonical_roster_seasons always says "LAR"; team_aliases has "STL"
    2002-2015 and "LA" 2016+) -- resolved by franchise_id directly rather
    than guessing a season-blind code."""
    override_franchise_id = spec.team_code_overrides.get(team_code)
    if override_franchise_id:
        row = c.execute(
            "SELECT franchise_id, full_name FROM team_aliases "
            "WHERE franchise_id=? AND ?>=season_start AND (season_end IS NULL OR ?<=season_end)",
            (override_franchise_id, season, season),
        ).fetchone()
        if row is None:
            return None, "TEAM_UNRESOLVED"
        return {"franchise_id": row["franchise_id"], "full_name": row["full_name"]}, None
    return resolve_franchise(c, team_code, season)


class CompiledAdapter:
    """Real, working adapter object compiled from a RelationshipSpec. Same
    shape as every hand-written tools/quiz_export/adapters/*.py module."""

    def __init__(self, spec: RelationshipSpec):
        self.spec = spec
        self.CATEGORY = spec.category
        self.TRACK_ENTITY = True
        # Populated by the most recent fetch_ordered_candidates() call --
        # real, checked exclusion counts, never estimated. Consumed by
        # eligibility_report() below, not by the generation pipeline
        # itself. Naming correction (owner-flagged): these are ELIGIBILITY
        # numbers (how much of the raw real-world pair set survives this
        # capability's own exclusion rules), a DIFFERENT concept from
        # health_probe.py's test_sample_rate (how much of the eligible pool
        # one certification run happened to sample) -- never conflate the
        # two; eligibility_report() below is the one place both are shown
        # side by side, deliberately labeled apart.
        self.multi_team_exclusions = 0
        self.name_collision_exclusions = 0
        self.future_season_exclusions = 0
        self.raw_pair_count = 0
        self._season_status_cache: dict = {}

    def safety_check(self, c) -> dict:
        return safety.check_table_wide_safety(c, self.spec.membership_table, self.spec.required_source_ids)

    def fetch_ordered_candidates(self, c, seed: str):
        spec = self.spec
        rows = c.execute(
            f"SELECT m.{spec.season_column} AS season, m.{spec.team_code_column} AS team_code, "
            f"m.{spec.entity_id_column} AS entity_id, e.{spec.entity_name_column} AS entity_name, "
            f"m.verification_status AS verification_status, m.source_id AS source_id "
            f"FROM {spec.membership_table} m "
            f"JOIN {spec.entity_table} e ON e.{spec.entity_id_column} = m.{spec.entity_id_column} "
            f"WHERE m.{spec.season_column} BETWEEN ? AND ?",
            (spec.min_season, spec.max_season),
        ).fetchall()

        team_counts: dict = {}
        for r in rows:
            key = (r["entity_id"], r["season"])
            team_counts.setdefault(key, set()).add(r["team_code"])
        self.raw_pair_count = len(team_counts)
        multi_team_keys = {k for k, teams in team_counts.items() if len(teams) > 1}
        self.multi_team_exclusions = len(multi_team_keys)

        seen_keys = set()
        single_team_rows = []
        for r in rows:
            key = (r["entity_id"], r["season"])
            if key in multi_team_keys or key in seen_keys:
                continue
            seen_keys.add(key)
            single_team_rows.append(r)

        name_season_counts: dict = {}
        for r in single_team_rows:
            key = (r["entity_name"], r["season"])
            name_season_counts.setdefault(key, set()).add(r["entity_id"])
        colliding_keys = {k for k, ids in name_season_counts.items() if len(ids) > 1}
        self.name_collision_exclusions = sum(
            1 for r in single_team_rows if (r["entity_name"], r["season"]) in colliding_keys
        )

        non_colliding_rows = [r for r in single_team_rows if (r["entity_name"], r["season"]) not in colliding_keys]

        # Future-season exclusion: a season with zero verified real
        # regular-season weekly evidence is never treated as a completed-
        # season fact -- excluded from the pool entirely (see module
        # docstring's EVIDENCE SEMANTICS section). Cached per distinct
        # season, not queried per row.
        self._season_status_cache = {}
        final_rows = []
        future_excluded = 0
        for r in non_colliding_rows:
            status = _season_status(c, self.spec, r["season"], _cache=self._season_status_cache)
            if status == "FUTURE":
                future_excluded += 1
                continue
            final_rows.append(r)
        self.future_season_exclusions = future_excluded

        rng_order = engine.seeded(seed)
        final_rows = list(final_rows)
        rng_order.shuffle(final_rows)
        return final_rows

    def evaluate(self, c, row, rng, guard):
        spec = self.spec
        if row["verification_status"] != spec.required_verification_status:
            return "ROW_NOT_VERIFIED"
        if row["source_id"] not in spec.required_source_ids:
            return "ROW_NOT_VERIFIED"
        if not row["entity_name"] or not row["team_code"]:
            return "MISSING_FIELD"

        season = row["season"]
        # A FUTURE-status season should already be excluded upstream by
        # fetch_ordered_candidates() -- re-checked here defensively (e.g. a
        # caller invoking evaluate() directly against a raw row) rather than
        # trusted blindly; never emit a completed-season claim for one.
        season_status = _season_status(c, spec, season, _cache=self._season_status_cache)
        if season_status == "FUTURE":
            return "SEASON_NOT_YET_VERIFIED"

        franchise, err = _normalize_franchise(c, spec, row["team_code"], season)
        if err:
            return err

        active = teams_active_in_season(c, season)
        pool = {fid: name for fid, name in active.items() if fid != franchise["franchise_id"]}
        if len(pool) < 3:
            return "INSUFFICIENT_DISTRACTOR_POOL"
        distractor_names = rng.sample(list(pool.values()), 3)

        options = [franchise["full_name"]] + distractor_names
        if len(set(options)) != 4:
            return "DUPLICATE_OPTIONS"

        # Evidence-correct wording (owner-required, Phase 3 closeout): this
        # capability's evidence_type is ROSTER_MEMBERSHIP -- "was/is ON",
        # never "played for" (that would claim GAME_PARTICIPATION, which
        # nothing here actually joins). Tense follows the season's real,
        # measured completeness, never wall-clock guessing.
        question, notes = _phrase_membership_question(
            competition_id=spec.competition_id, entity_name=row["entity_name"],
            team_full_name=franchise["full_name"], season=season, season_status=season_status,
        )

        if guard.question_seen(question):
            return "DUPLICATE_QUESTION"
        entity_key = f"{spec.capability_id}:{row['entity_id']}:{season}"
        if guard.entity_seen(entity_key):
            return "DUPLICATE_ENTITY_SEASON"

        shuffled_options, correct_index = serializer.finalize_options(rng, franchise["full_name"], distractor_names)
        if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != franchise["full_name"]:
            return "INVALID_CORRECT_INDEX"

        diff_score = (spec.max_season - season) / max(spec.max_season - spec.min_season, 1)
        band = engine.band(diff_score)
        diff_label = difficulty_mod.map_band(band)

        return {
            "category": spec.category, "difficulty": diff_label, "question": question,
            "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
            "_audit": {
                "season": season, "entity_id": row["entity_id"], "team_code": row["team_code"],
                "franchise_id": franchise["franchise_id"], "correct_answer_text": franchise["full_name"],
                "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
                "verification_status": row["verification_status"], "source_id": row["source_id"],
                "evidence_type": spec.evidence_type, "season_status": season_status,
            },
        }

    def eligibility_report(self) -> dict:
        """Real, computed from the most recent fetch_ordered_candidates()
        call -- raw_candidate_count is the total real (entity, season)
        pairs before this capability's own exclusion rules; eligible_
        candidate_count is what remains after multi-team and same-name-
        collision exclusion; eligibility_rate/exclusion_rate are the two
        ratios, always summing to 1.0. This is ELIGIBILITY (how much of the
        raw real-world pair set is usable), not test sampling (how much of
        the eligible pool one certification run happened to draw from --
        see health_probe.py's test_sample_rate) and not a general coverage
        claim -- the three are never interchangeable."""
        raw = self.raw_pair_count
        excluded = self.multi_team_exclusions + self.name_collision_exclusions + self.future_season_exclusions
        eligible = raw - excluded
        return {
            "raw_candidate_count": raw,
            "eligible_candidate_count": eligible,
            "excluded_candidate_count": excluded,
            "eligibility_rate": round(eligible / raw, 4) if raw else 0.0,
            "exclusion_rate": round(excluded / raw, 4) if raw else 0.0,
            "excluded_breakdown": {
                "multi_team_exclusions": self.multi_team_exclusions,
                "name_collision_exclusions": self.name_collision_exclusions,
                "future_season_exclusions": self.future_season_exclusions,
            },
        }


def compile_adapter(spec: RelationshipSpec) -> CompiledAdapter:
    return CompiledAdapter(spec)
