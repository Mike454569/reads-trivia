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

Two exclusion rules are baked into fetch_ordered_candidates(), both
conservative (exclude and count, never guess):

1. Multi-team seasons: a real (entity_id, season) pair with more than one
   distinct team_code that season is excluded entirely -- Phase 3 does not
   attempt to pick "the" team for a traded/multi-stint player-season.
2. Same-name collisions: two distinct real entities sharing a (name, season)
   among the single-team-season set would make the generated prompt
   ("Name -- Season") genuinely ambiguous to answer -- both are excluded.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from tools.quiz_export import difficulty as difficulty_mod
from tools.quiz_export import engine, safety, serializer
from tools.quiz_export.adapters.draft import resolve_franchise, teams_active_in_season


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
    team_code_overrides: dict = field(default_factory=dict)  # {roster_code: franchise_id}, evidence-based only


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
        self.raw_pair_count = 0

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

        final_rows = [r for r in single_team_rows if (r["entity_name"], r["season"]) not in colliding_keys]

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

        question = f"Which {spec.competition_id} team did {row['entity_name']} play for in the {season} season?"
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

        notes = f"{row['entity_name']} played for the {franchise['full_name']} in {season}."

        return {
            "category": spec.category, "difficulty": diff_label, "question": question,
            "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
            "_audit": {
                "season": season, "entity_id": row["entity_id"], "team_code": row["team_code"],
                "franchise_id": franchise["franchise_id"], "correct_answer_text": franchise["full_name"],
                "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
                "verification_status": row["verification_status"], "source_id": row["source_id"],
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
        excluded = self.multi_team_exclusions + self.name_collision_exclusions
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
            },
        }


def compile_adapter(spec: RelationshipSpec) -> CompiledAdapter:
    return CompiledAdapter(spec)
