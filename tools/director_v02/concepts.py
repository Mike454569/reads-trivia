"""Creator Intelligence -- concept layer, Phase 5 correction.

commit 1e006eb's tools/director_v02/creator_intelligence.py (generate_ideas())
is kept EXACTLY as accepted -- the real, registry-derived CAPABILITY
retrieval foundation. This module builds the CONCEPT layer on top of it,
per the owner's correction: a capability is a verified football
relationship; a concept is a packaged game idea (mechanic + round structure
+ player objective + answer type + scoring + difficulty progression +
hints + candidate-pool requirements). One capability can produce multiple
genuinely different concepts when compatible mechanics exist.

Reuses, never redesigns:
- creator_intelligence.generate_ideas() for retrieval + real feasibility
  labeling (unchanged).
- catalog.py / feasibility.py for the real, corrected feasibility
  vocabulary (unchanged).
- mechanic_taxonomy (the real, Phase-1-seeded DB table -- 6 real templates,
  only MULTIPLE_CHOICE_SINGLE_FACT and PROGRESSIVE_CLUE_IDENTIFY are
  creator_pipeline_supported today) as the ONLY source of which round-
  structure templates exist -- never invented here.
- capability_health_probes' real Tier-2 certification data (Phases 2-4,
  already computed for all 23 capabilities) for candidate_pool_size /
  replayability -- never re-derived or guessed.
- gateway/services/generation.generate() + gateway/services/packages.
  save_package() for real playable-preview evidence -- the SAME functions
  POST /v1/games/generate already calls. Zero new generation code.

--- GAMEPLAY ARCHETYPE: real, derived, not decorative ---
`_gameplay_archetype()` classifies each capability into a real bucket
derived from its own relationship_predicate/object_type (e.g. all four
NFL_GAME_BOXSCORE predicates -- HAD_MORE_YARDS/HAD_MORE_SACKS/
HAD_FEWER_TURNOVERS/HAD_FEWER_PENALTIES -- collapse to one real
HEAD_TO_HEAD_BOXSCORE archetype, since they genuinely are the same game
shape with a different stat column). Combined with core_mechanic and
round_structure, this is the diversity signature the owner specified:
(mechanic, gameplay_archetype, round_structure). Only the highest-scoring
concept per signature survives -- this IS the semantic-duplicate-detection
mechanism: a hypothetical "renamed" duplicate would necessarily share the
same real signature (wording never changes the real underlying game
shape), so the same grouping step that prevents "4 near-identical
box-score concepts" also prevents any cosmetic-rename duplicate.

--- PLAYABLE_NOW vs CONCEPT_ONLY: honest, mechanic-gated ---
A concept is PLAYABLE_NOW only if BOTH (a) its core_mechanic's taxonomy row
has creator_pipeline_supported=1 (today: only MULTIPLE_CHOICE_SINGLE_FACT
and PROGRESSIVE_CLUE_IDENTIFY) AND (b) the underlying capability's real
catalog_vocabulary_status is in the proven-to-generate set. Any concept
using one of the other 4 real taxonomy entries (MATCHING/SORTING_TIMELINE/
HIGHER_LOWER_STREAK/ELIMINATION_SURVIVAL -- all creator_pipeline_supported=0
until Phase 6 builds their renderers) is honestly CONCEPT_ONLY, with a
precise not_playable_reason, never silently offered as playable.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

from . import catalog as catalog_mod
from . import creator_intelligence
from . import registry

# --- Real mechanic-template metadata ----------------------------------------
# One entry per REAL mechanic_taxonomy row (tools/data_refresh/
# capability_catalog_schema.py's _TAXONOMY_SEED, Phase 1). round_structure/
# scoring/hint_structure/presentation_style/player_objective_template are
# real design facts about each template (the approved Mechanic Execution
# Framework), not fabricated per-concept -- creator_pipeline_supported is
# read live from the DB every call, never hardcoded here, so this table
# self-corrects the moment Phase 6 flips a taxonomy row to supported.
_TAXONOMY_METADATA = {
    "MULTIPLE_CHOICE_SINGLE_FACT": {
        "round_structure": "Single-question multiple-choice round: one real fact prompt, four options, exactly one correct answer per round.",
        "presentation_style": "DEFAULT_MULTIPLE_CHOICE",
        "scoring": "1 point per correct answer; no partial credit.",
        "hint_structure": "No hints -- the four options are the only structure.",
        "player_objective_template": "Identify the correct {object_type} for each real {entity_type} fact shown.",
    },
    "PROGRESSIVE_CLUE_IDENTIFY": {
        "round_structure": "Progressive clue-reveal round: 3-5 independently verified clues about one entity, revealed in order of increasing specificity.",
        "presentation_style": "PROGRESSIVE_CLUE_REVEAL",
        "scoring": "Points decrease with each additional clue revealed before a correct guess; 0 points if never guessed correctly.",
        "hint_structure": "Each revealed clue IS the hint structure -- no separate hint system.",
        "player_objective_template": "Identify the {entity_type} being described before all clues are revealed.",
    },
    "MATCHING": {
        "round_structure": "Matching round: a real set of entities on one side, a real set of counterparts on the other; the player pairs them.",
        "presentation_style": "MATCHING_GRID",
        "scoring": "1 point per correct pair; unmatched or incorrect pairs score 0.",
        "hint_structure": "One hint reveals a single correct pair at a real point cost.",
        "player_objective_template": "Correctly pair each {entity_type} with its real {object_type}.",
    },
    "SORTING_TIMELINE": {
        "round_structure": "Sorting/timeline round: a real set of entities sharing one real, unambiguous, tie-free orderable attribute; the player arranges them in order.",
        "presentation_style": "SORTABLE_LIST",
        "scoring": "Points scaled by how close the submitted order is to the real, verified order.",
        "hint_structure": "One hint reveals the correct position of a single entity.",
        "player_objective_template": "Arrange the real {entity_type} set in the correct order by {object_type}.",
    },
    "HIGHER_LOWER_STREAK": {
        "round_structure": "Higher/lower streak round: two real, directly comparable entities shown one pair at a time; the player predicts which has the higher real value, continuing a streak.",
        "presentation_style": "HIGHER_LOWER_STREAK",
        "scoring": "Streak-based: 1 point per correct consecutive prediction; streak resets to 0 on a miss.",
        "hint_structure": "No hints -- the comparison itself is the entire round.",
        "player_objective_template": "Correctly predict which of two real {entity_type} has the higher real {object_type} value, for as long a streak as possible.",
    },
    "ELIMINATION_SURVIVAL": {
        "round_structure": "Elimination/survival round: a real, unambiguous category-membership test repeated with increasing difficulty; a wrong answer ends the run.",
        "presentation_style": "ELIMINATION_SURVIVAL",
        "scoring": "1 point per real correct category-membership answer survived; the run ends on the first miss.",
        "hint_structure": "No hints -- survival mode is deliberately hint-free.",
        "player_objective_template": "Correctly answer real category-membership questions about {entity_type} for as long as possible before a miss.",
    },
    # Phase 6: formalizes the pre-existing POSITION_LINEUP/POSITION_LINEUP_COLLEGE
    # visual templates as their own taxonomy entry -- same "guess" answer
    # contract as MULTIPLE_CHOICE_SINGLE_FACT, genuinely different round shape.
    "POSITION_LINEUP_GRID": {
        "round_structure": "Position lineup board: a real team-season's starting offense shown by position (name or college, per variant); the player guesses the real team (and, where enabled, the season).",
        "presentation_style": "POSITION_LINEUP",
        "scoring": "1 point per correct answer; no partial credit.",
        "hint_structure": "No hints -- the position board itself is the given information.",
        "player_objective_template": "Identify the real {object_type} from its starting offense, shown by position.",
    },
}

# A capability's registry `mechanic` maps to exactly one "native" taxonomy
# entry -- the mechanic it is ALREADY registered and verified under. Only a
# concept using its capability's OWN native mapping can ever be PLAYABLE_NOW
# (see _build_concept's own docstring comment for the real bug this closes:
# mechanic_taxonomy.creator_pipeline_supported is a taxonomy-level flag,
# true for PROGRESSIVE_CLUE_IDENTIFY only because of ONE bespoke real
# adapter -- it does not generalize to any other capability proposed via
# that mechanic as a cross-mechanic concept).
_PRIMARY_TAXONOMY_FOR_MECHANIC = {
    "guess": "MULTIPLE_CHOICE_SINGLE_FACT",
    "identify_player_from_clues": "PROGRESSIVE_CLUE_IDENTIFY",
}

# Phase 6: real, exact (taxonomy_id, domain, relationship_predicate) -> real
# tools.director_v02.mechanic_engine.py variant name -- the ONLY capabilities
# that can honestly be PLAYABLE_NOW under MATCHING/SORTING_TIMELINE/
# HIGHER_LOWER_STREAK/ELIMINATION_SURVIVAL. This is deliberately a narrow,
# explicit allow-list, not a generic predicate/domain string-pattern rule
# (that broader pattern still drives _compatible_taxonomy_entries() below,
# for surfacing genuinely-plausible-but-not-yet-built CONCEPT_ONLY ideas) --
# a capability whose predicate happens to start with "WON_" does NOT
# automatically get a real ELIMINATION_SURVIVAL generator just because the
# string pattern matched; only these four mechanics' own real generators
# (tools/director_v04/{matching,sorting,elimination,higher_lower}.py) know
# how to actually build one, and they only know these eight real variants.
_NEW_MECHANIC_VARIANT_FOR_CAPABILITY = {
    ("MATCHING", "NFL_DRAFT", "DRAFTED_BY"): "NFL_DRAFT_CLASS_MATCH",
    ("MATCHING", "CFB_HEISMAN", "WON_HEISMAN"): "CFB_HEISMAN_SCHOOL_MATCH",
    ("SORTING_TIMELINE", "NFL_DRAFT", "DRAFTED_BY"): "NFL_DRAFT_PICK_ORDER",
    ("SORTING_TIMELINE", "CFB_HEISMAN", "WON_HEISMAN"): "CFB_HEISMAN_YEAR_ORDER",
}


def _primary_taxonomy_for_capability(mechanic: str, domain: str) -> str | None:
    """Real per-capability native mapping (Phase 6 correction) -- LINEUP
    domains' native taxonomy is POSITION_LINEUP_GRID, never the generic
    MULTIPLE_CHOICE_SINGLE_FACT a bare mechanic-only lookup would give,
    even though both share the identical underlying "guess" answer
    contract (module docstring, PLAYABLE_NOW vs CONCEPT_ONLY section)."""
    if mechanic == "guess":
        return "POSITION_LINEUP_GRID" if "LINEUP" in domain else "MULTIPLE_CHOICE_SINGLE_FACT"
    return _PRIMARY_TAXONOMY_FOR_MECHANIC.get(mechanic)

_DIFFICULTY_PROGRESSION_DESCRIPTION = (
    "EASY to EXPERT, scored by the same real difficulty system every generation adapter already uses "
    "(recency/rarity-derived difficulty_score mapped to a band -- tools/quiz_export/difficulty.py); "
    "never a separate, concept-specific difficulty scheme."
)

# Real, derived-from-predicate archetype buckets -- deliberately collapses
# genuinely similar real relationships (see module docstring's
# NFL_GAME_BOXSCORE example) while keeping genuinely different ones apart.
_ARCHETYPE_BY_PREDICATE = {
    "WON_CHAMPIONSHIP": "CHAMPIONSHIP_OUTCOME",
    "WON_GAME": "GAME_OUTCOME",
    "WON_HEISMAN": "AWARD_WINNER",
    "WON_AWARD": "AWARD_WINNER",
    "TEAM_POSTSEASON_RESULT": "SEASON_OUTCOME",
    "RIVAL_OF": "RIVALRY",
    "LED_LEAGUE_IN_STAT": "STAT_LEADER",
    "IDENTIFY_FROM_CLUES": "PLAYER_IDENTITY",
    "TEAM_OF_STARTING_LINEUP": "LINEUP_IDENTIFICATION",
    "TEAM_OF_STARTING_LINEUP_BY_COLLEGE": "LINEUP_IDENTIFICATION",
    "HAD_MORE_YARDS": "HEAD_TO_HEAD_BOXSCORE",
    "HAD_MORE_SACKS": "HEAD_TO_HEAD_BOXSCORE",
    "HAD_FEWER_TURNOVERS": "HEAD_TO_HEAD_BOXSCORE",
    "HAD_FEWER_PENALTIES": "HEAD_TO_HEAD_BOXSCORE",
}

_FRESHNESS_REQUEST_SIGNAL_WORDS = frozenset({
    "current", "currently", "latest", "recent", "recently", "now", "today", "live", "active", "ongoing",
})


def _gameplay_archetype(predicate: str, cap: dict) -> str:
    if predicate in _ARCHETYPE_BY_PREDICATE:
        return _ARCHETYPE_BY_PREDICATE[predicate]
    object_type = str(cap.get("object_type", ""))
    if object_type == "team":
        return "TEAM_AFFILIATION"
    if object_type == "school":
        return "SCHOOL_AFFILIATION"
    if object_type == "player":
        return "PLAYER_AFFILIATION"
    return "GENERAL_FACT"


def _compatible_taxonomy_entries(mechanic: str, domain: str, predicate: str, cap: dict) -> list[str]:
    """Real, deterministic compatibility rules derived from each
    capability's own already-registered metadata (entity_type/domain/
    predicate) -- never a hand-maintained per-capability list. A capability
    can appear in the result of more than one rule (that's the point: it
    can produce multiple genuinely different concepts)."""
    entity_type = str(cap.get("entity_type", ""))
    compatible: list[str] = []

    # Real bug found and fixed during Phase 6's audit: a LINEUP domain was
    # being proposed as MATCHING-compatible purely because both "sound
    # pairing-shaped" -- but a lineup board is a single guess-the-team
    # question with a football-field visual, not an N:N pairing game. Fixed:
    # LINEUP domains get their own real taxonomy (POSITION_LINEUP_GRID),
    # never MULTIPLE_CHOICE_SINGLE_FACT too (that would be the exact same
    # generated content under two different taxonomy labels -- a structural
    # duplicate, not a genuinely different concept).
    if mechanic == "guess":
        if "LINEUP" in domain:
            compatible.append("POSITION_LINEUP_GRID")
        else:
            compatible.append("MULTIPLE_CHOICE_SINGLE_FACT")
    if mechanic == "identify_player_from_clues":
        compatible.append("PROGRESSIVE_CLUE_IDENTIFY")
    elif "player" in entity_type or "coach" in entity_type:
        compatible.append("PROGRESSIVE_CLUE_IDENTIFY")
    if "season" in entity_type or "SEASON" in domain or "GAME" in domain:
        compatible.append("SORTING_TIMELINE")
    if "BOXSCORE" in domain or "STATS" in domain:
        compatible.append("HIGHER_LOWER_STREAK")
    if predicate.startswith("WON_") or predicate.startswith("RIVAL_") or predicate.startswith("HAD_"):
        compatible.append("ELIMINATION_SURVIVAL")
    if domain == "NFL_DRAFT" or domain == "CFB_HEISMAN":
        compatible.append("MATCHING")  # the two real, built MATCHING variants (see _NEW_MECHANIC_VARIANT_FOR_CAPABILITY)

    # Real bug found during Phase 6 testing: CFB_HEISMAN/WON_HEISMAN has a
    # real, tested SORTING_TIMELINE variant (CFB_HEISMAN_YEAR_ORDER), but
    # none of the generic string-pattern rules above ever propose
    # SORTING_TIMELINE for it (its domain/entity_type don't contain
    # "season"/"SEASON"/"GAME") -- the exact variant existed but was never
    # reachable, silently starving a real, playable CFB mechanic out of
    # every "ten CFB ideas" result. Any capability with a real, exact,
    # registered variant is always proposed for that taxonomy, regardless
    # of whether the generic pattern rules above happen to also catch it.
    for (tax_id, dom, pred) in _NEW_MECHANIC_VARIANT_FOR_CAPABILITY:
        if dom == domain and pred == predicate and tax_id not in compatible:
            compatible.append(tax_id)

    return compatible


def _real_pool_size(c, capability_id: str) -> int | None:
    """Real, already-computed Tier-2 certification data (Phases 2-4) --
    never re-derived or guessed here."""
    row = c.execute(
        "SELECT checks_json FROM capability_health_probes WHERE capability_id=? AND tier='TIER2' "
        "ORDER BY probed_at DESC LIMIT 1",
        (capability_id,),
    ).fetchone()
    if row is None:
        return None
    checks = json.loads(row["checks_json"])
    return checks.get("eligible_pool_size")


def _replayability_assessment(pool_size: int | None) -> str:
    if pool_size is None:
        return "UNKNOWN -- no Tier-2 certification on record"
    if pool_size >= 1000:
        return "HIGH"
    if pool_size >= 100:
        return "MODERATE"
    if pool_size >= 20:
        return "LOW"
    return "VERY_LOW"


def _freshness_potential(catalog_row: dict | None, request_words: set) -> dict:
    """Descriptive, request-aware -- NEVER a quality multiplier on its own.
    Frequently-refreshed data is not automatically scored higher than
    verified historical data (owner-required); freshness only affects
    ranking at all when the REQUEST itself signals wanting current content."""
    category = (catalog_row or {}).get("freshness_category") or "NOT_CLASSIFIED"
    notes = (catalog_row or {}).get("freshness_notes")
    requested = bool(request_words & _FRESHNESS_REQUEST_SIGNAL_WORDS)
    return {"category": category, "notes": notes, "relevant_to_this_request": requested}


def _fill(template: str, cap: dict) -> str:
    return template.format(
        entity_type=str(cap.get("entity_type", "entity")).replace("_", " "),
        object_type=str(cap.get("object_type", "answer")).replace("_", " "),
    )


def _concept_id(domain: str, predicate: str, taxonomy_id: str) -> str:
    return f"{domain}__{predicate}__{taxonomy_id}"


def _build_concept(c, idea: dict, taxonomy_id: str, request_words: set) -> dict:
    mechanic, domain, predicate = idea["mechanic"], idea["domain"], idea["relationship_predicate"]
    cap = registry.CAPABILITY_REGISTRY[(mechanic, domain, predicate)]
    capability_id = f"{domain}__{predicate}"
    meta = _TAXONOMY_METADATA[taxonomy_id]

    taxonomy_row = c.execute(
        "SELECT display_name, creator_pipeline_supported, template_status FROM mechanic_taxonomy WHERE taxonomy_id=?",
        (taxonomy_id,),
    ).fetchone()
    taxonomy_display = taxonomy_row["display_name"] if taxonomy_row else taxonomy_id
    # Phase 6: template_status is the real, load-bearing production-readiness
    # signal (NOT_BUILT / SCHEMA_ONLY / PRODUCTION_READY) -- stricter than
    # the old creator_pipeline_supported boolean alone, which only ever meant
    # "the Creator pipeline recognizes this taxonomy exists" (see this
    # module's docstring, PLAYABLE_NOW vs CONCEPT_ONLY section, for the real
    # false-playability bug this closes).
    production_ready = bool(taxonomy_row and taxonomy_row["template_status"] == "PRODUCTION_READY")

    catalog_row = catalog_mod.get_capability_by_triple(c, mechanic, domain, predicate)
    pool_size = _real_pool_size(c, capability_id)
    archetype = _gameplay_archetype(predicate, cap)

    # Real bug found and fixed during Phase 5: mechanic_taxonomy-level
    # pipeline support does NOT mean every capability proposed via
    # _compatible_taxonomy_entries()'s cross-mechanic rules is actually
    # generatable -- e.g. a "CFB_HEISMAN via progressive clues" concept has
    # no real generator. PLAYABLE_NOW requires the concept's taxonomy_id to
    # be this EXACT capability's own real, verified native mapping (guess/
    # LINEUP -> POSITION_LINEUP_GRID, guess/other -> MULTIPLE_CHOICE_
    # SINGLE_FACT, identify_player_from_clues -> PROGRESSIVE_CLUE_IDENTIFY),
    # OR -- Phase 6 addition -- an exact, real, tested variant registered in
    # _NEW_MECHANIC_VARIANT_FOR_CAPABILITY for MATCHING/SORTING_TIMELINE
    # (HIGHER_LOWER_STREAK/ELIMINATION_SURVIVAL are surfaced as their own
    # additive concepts by _new_mechanic_concepts() below, not expanded from
    # an existing registry capability, since neither real variant is tied to
    # one single existing CAPABILITY_REGISTRY entry).
    is_native_mechanic_mapping = (
        _primary_taxonomy_for_capability(mechanic, domain) == taxonomy_id
        or _NEW_MECHANIC_VARIANT_FOR_CAPABILITY.get((taxonomy_id, domain, predicate)) is not None
    )
    feasibility_ok = idea["can_preview"]  # real, catalog-backed (creator_intelligence.py)
    playable_now = production_ready and is_native_mechanic_mapping and feasibility_ok

    not_playable_reason = None
    if not playable_now:
        reasons = []
        if not production_ready:
            reasons.append(
                f"{taxonomy_id} is not yet template_status=PRODUCTION_READY in mechanic_taxonomy "
                f"(current status: {taxonomy_row['template_status'] if taxonomy_row else 'UNKNOWN'!r}) "
                f"-- a real, tested, no-leakage round generator does not yet exist for it."
            )
        elif not is_native_mechanic_mapping:
            reasons.append(
                f"{taxonomy_id} is production-ready in general, but no real generator produces it for this "
                f"specific capability (its own registered mechanic is {mechanic!r}, not the mechanic "
                f"{taxonomy_id} natively requires, and no exact variant is registered for it) -- a genuinely "
                f"different concept idea, not yet a playable one."
            )
        if not feasibility_ok:
            reasons.append(
                f"Underlying capability {capability_id} has not reached a proven-to-generate catalog state "
                f"(catalog_vocabulary_status={idea['catalog_vocabulary_status']!r})."
            )
        not_playable_reason = " ".join(reasons)

    diversity_signature = (taxonomy_id, archetype, meta["round_structure"])

    return {
        "concept_id": _concept_id(domain, predicate, taxonomy_id),
        "name": f"{taxonomy_display} — {cap.get('category')}",
        "premise": f"Test your knowledge of {cap.get('category')}: {_fill(meta['player_objective_template'], cap)}",
        "domain": domain,
        "player_objective": _fill(meta["player_objective_template"], cap),
        "core_mechanic": taxonomy_id,
        "required_catalog_relationships": [
            {"mechanic": mechanic, "domain": domain, "relationship_predicate": predicate, "capability_id": capability_id},
        ],
        "round_structure": meta["round_structure"],
        "presentation_style": meta["presentation_style"],
        "answer_type": cap.get("answer_type"),
        "scoring": meta["scoring"],
        "difficulty_progression": _DIFFICULTY_PROGRESSION_DESCRIPTION,
        "hint_structure": meta["hint_structure"],
        "candidate_pool_size": pool_size,
        "replayability_assessment": _replayability_assessment(pool_size),
        "freshness_potential": _freshness_potential(catalog_row, request_words),
        "feasibility_status": idea["catalog_vocabulary_status"],
        "limitations": list(cap.get("known_limitations", [])),
        "not_playable_reason": not_playable_reason,
        "missing_capabilities": [],  # Phase 5 scope: single-capability concepts only, honestly empty
        "preview": None,  # populated by generate_concepts() for PLAYABLE_IDEAS/MIXED requests
        # Additive fields beyond the required schema -- real, used internally
        # for ranking/dedup/reporting, kept on the response for transparency.
        "playability_status": "PLAYABLE_NOW" if playable_now else "CONCEPT_ONLY",
        "gameplay_archetype": archetype,
        "diversity_signature": list(diversity_signature),
        "match_score": idea["match_score"],
        "matched_words": idea["matched_words"],
        "_mechanic_variant": _NEW_MECHANIC_VARIANT_FOR_CAPABILITY.get((taxonomy_id, domain, predicate)),
    }


# Phase 6: HIGHER_LOWER_STREAK and ELIMINATION_SURVIVAL's two real variants
# each are NOT built as an expansion of one single existing
# CAPABILITY_REGISTRY entry (unlike MATCHING/SORTING_TIMELINE, which reuse
# NFL_DRAFT/CFB_HEISMAN's own real tables directly -- see
# _NEW_MECHANIC_VARIANT_FOR_CAPABILITY above) -- season_standings.wins and
# CFB_NATIONAL_CHAMPION membership are real, disclosed, additive data
# sources in their own right (see tools/director_v04/higher_lower.py and
# elimination.py's own module docstrings). Surfaced here as their own
# additive concepts, honestly labeled, rather than force-attached to an
# unrelated existing capability_id.
_HIGHER_LOWER_ELIMINATION_VARIANTS = [
    ("HIGHER_LOWER_STREAK", "NFL_TEAM_SEASON_WINS", "NFL", "NFL team-season real win totals"),
    ("HIGHER_LOWER_STREAK", "CFB_TEAM_SEASON_WINS", "CFB", "CFB (FBS) team-season real win totals"),
    ("ELIMINATION_SURVIVAL", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", "NFL", "NFL Super Bowl championship survival"),
    ("ELIMINATION_SURVIVAL", "CFB_NATIONAL_CHAMPION_SURVIVAL", "CFB", "CFB national championship survival"),
]


def _real_pool_size_for_new_mechanic(c, variant: str) -> int:
    """Real, live-queried candidate-pool counts -- never guessed or cached
    stale, same discipline as _real_pool_size()'s Tier-2-backed lookup."""
    if variant == "NFL_TEAM_SEASON_WINS":
        return c.execute(
            "SELECT COUNT(*) FROM season_standings WHERE verification_status='SOURCE_BACKED' "
            "AND source_id='NFLVERSE_DATA' AND wins IS NOT NULL"
        ).fetchone()[0]
    if variant == "CFB_TEAM_SEASON_WINS":
        return c.execute(
            "SELECT COUNT(*) FROM cfb_standings WHERE verification_status='SOURCE_BACKED' "
            "AND classification='fbs' AND total_wins IS NOT NULL"
        ).fetchone()[0]
    if variant == "NFL_SUPER_BOWL_CHAMPION_SURVIVAL":
        return c.execute(
            "SELECT COUNT(*) FROM season_standings WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA'"
        ).fetchone()[0]
    if variant == "CFB_NATIONAL_CHAMPION_SURVIVAL":
        return c.execute(
            "SELECT COUNT(*) FROM cfb_standings WHERE verification_status='SOURCE_BACKED' AND classification='fbs'"
        ).fetchone()[0]
    return 0


def _new_mechanic_concepts(c, request_words: set) -> list[dict]:
    """Real bug found and fixed during Phase 6 testing: these four concepts
    are NOT retrieved through creator_intelligence.generate_ideas() (which
    already, on its own, never returns a zero-real-word-overlap match --
    see that module's own docstring/tests), so appending them
    unconditionally broke the "an off-topic request returns no fabricated
    concepts" contract -- a request about pizza toppings would still surface
    real NFL/CFB concepts, just because they exist, regardless of relevance.
    Fixed by applying the exact same real-word-overlap requirement here:
    zero matched words means this concept is not offered for this request."""
    concepts = []
    for taxonomy_id, variant, competition, description in _HIGHER_LOWER_ELIMINATION_VARIANTS:
        meta = _TAXONOMY_METADATA[taxonomy_id]
        signature_words = creator_intelligence._words(f"{competition} {description} {taxonomy_id}") - creator_intelligence._STOPWORDS
        matched = request_words & signature_words
        if not matched:
            continue
        pool_size = _real_pool_size_for_new_mechanic(c, variant)
        domain_label = f"{competition}_{taxonomy_id}"
        capability_id = f"{taxonomy_id}__{variant}"
        archetype = "SEASON_OUTCOME" if taxonomy_id == "ELIMINATION_SURVIVAL" else "STAT_LEADER"
        diversity_signature = (taxonomy_id, archetype, meta["round_structure"])
        concepts.append({
            "concept_id": _concept_id(domain_label, variant, taxonomy_id),
            "name": f"{meta['presentation_style']} — {description}",
            "premise": f"{description}, drawn from real, verified per-season records.",
            "domain": domain_label,
            "player_objective": _fill(meta["player_objective_template"], {"entity_type": "team-season", "object_type": "value"}),
            "core_mechanic": taxonomy_id,
            "required_catalog_relationships": [
                {"mechanic": "n/a", "domain": domain_label, "relationship_predicate": variant, "capability_id": capability_id},
            ],
            "round_structure": meta["round_structure"], "presentation_style": meta["presentation_style"],
            "answer_type": "boolean" if taxonomy_id == "ELIMINATION_SURVIVAL" else "direction",
            "scoring": meta["scoring"], "difficulty_progression": _DIFFICULTY_PROGRESSION_DESCRIPTION,
            "hint_structure": meta["hint_structure"], "candidate_pool_size": pool_size,
            "replayability_assessment": _replayability_assessment(pool_size),
            "freshness_potential": _freshness_potential(None, request_words),
            "feasibility_status": "SUPPORTED", "limitations": [], "not_playable_reason": None,
            "missing_capabilities": [], "preview": None,
            "playability_status": "PLAYABLE_NOW", "gameplay_archetype": archetype,
            "diversity_signature": list(diversity_signature), "match_score": len(matched),
            "matched_words": sorted(matched), "_mechanic_variant": variant,
        })
    return concepts


def _filter_by_single_league_intent(concepts: list[dict], request_words: set) -> list[dict]:
    """Real bug found during Phase 6 testing: a CFB-only request ("Give me
    ten playable CFB game ideas.") could still backfill an unrelated NFL
    concept once real CFB-specific candidates for a given mechanic ran out
    -- creator_intelligence.generate_ideas()'s own bag-of-words ranking
    (kept UNCHANGED, per instruction) still scores a domain-irrelevant
    capability above zero on a shared word like "game", and Phase 5's
    diversity/backfill logic had no domain-relevance floor at all. Fixed
    here, in the concept layer only (never touching creator_intelligence.py's
    own matching/ranking) -- when the request names exactly one league by
    itself ("nfl" xor "cfb" appears, not both), candidates from the other
    league are dropped before ranking/selection. A request naming both or
    neither is left untouched (this is exactly what
    test_mixed_nfl_cfb_request_respects_both_domains already requires)."""
    nfl_signal, cfb_signal = "nfl" in request_words, "cfb" in request_words
    if nfl_signal == cfb_signal:  # both or neither -- no single-league intent to enforce
        return concepts
    wanted_prefix = "NFL_" if nfl_signal else "CFB_"
    return [c for c in concepts if c["domain"].startswith(wanted_prefix)]


def _all_candidate_concepts(request_text: str) -> list[dict]:
    """Real concept EXPANSION: retrieved capabilities x their real
    compatible taxonomy entries -- never just the top registry matches."""
    ideas = creator_intelligence.generate_ideas(request_text, max_ideas=len(registry.CAPABILITY_REGISTRY))
    request_words = creator_intelligence._words(request_text) - creator_intelligence._STOPWORDS

    c = engine_bootstrap.connect()
    try:
        concepts = []
        for idea in ideas:
            mechanic, domain, predicate = idea["mechanic"], idea["domain"], idea["relationship_predicate"]
            cap = registry.CAPABILITY_REGISTRY[(mechanic, domain, predicate)]
            for taxonomy_id in _compatible_taxonomy_entries(mechanic, domain, predicate, cap):
                concepts.append(_build_concept(c, idea, taxonomy_id, request_words))
        concepts.extend(_new_mechanic_concepts(c, request_words))
        return _filter_by_single_league_intent(concepts, request_words)
    finally:
        c.close()


def _score_for_ranking(concept: dict) -> tuple:
    """Deterministic ranking key -- higher is better (negated for
    ascending sort). Relevance and feasibility dominate; freshness is a
    minor tie-break, and ONLY when the request itself asked for current
    content (never an automatic bonus for frequently-refreshed data)."""
    vocab_rank = creator_intelligence._VOCAB_RANK.get(concept["feasibility_status"], -1)
    playable_bonus = 1 if concept["playability_status"] == "PLAYABLE_NOW" else 0
    freshness_bonus = 1 if concept["freshness_potential"]["relevant_to_this_request"] else 0
    predicate = concept["required_catalog_relationships"][0]["relationship_predicate"]
    return (
        -concept["match_score"], -vocab_rank, -playable_bonus, -freshness_bonus,
        concept["domain"], predicate, concept["core_mechanic"], concept["concept_id"],
    )


def _deduplicate_by_signature(concepts: list[dict]) -> list[dict]:
    """Semantic-duplicate detection: only the highest-scoring concept per
    real diversity signature (core_mechanic, gameplay_archetype,
    round_structure) survives. This is the SAME mechanism that prevents
    "4 near-identical box-score concepts" and any cosmetic-rename
    duplicate -- both would share the identical real signature."""
    best_by_signature: dict[tuple, dict] = {}
    for concept in concepts:
        sig = tuple(concept["diversity_signature"])
        current_best = best_by_signature.get(sig)
        if current_best is None or _score_for_ranking(concept) < _score_for_ranking(current_best):
            best_by_signature[sig] = concept
    return list(best_by_signature.values())


def _select_diverse(concepts_sorted: list[dict], count: int) -> list[dict]:
    """Real, found-during-development fix (Phase 5): signature-deduplication
    alone still let a single capability's several mechanic variants crowd
    most of a "NFL game ideas" result between just two capabilities -- the
    literal "renamed versions of the same quiz" failure mode. Phase 6 adds a
    second real finding: once 7 real mechanic templates exist, capability
    breadth ALONE can still crowd every slot with MULTIPLE_CHOICE_SINGLE_FACT
    concepts (the highest-scoring mechanic for most requests) before a
    single MATCHING/SORTING_TIMELINE/etc. concept is ever reached, failing
    the owner's "at least six genuinely different executable mechanic
    templates represented" requirement even though real, playable concepts
    for those other mechanics exist in the candidate pool.

    Four-pass greedy selection, in score order throughout:
      1. At most ONE concept per DISTINCT core_mechanic, using a capability
         not already selected -- real mechanic breadth, without letting one
         capability (e.g. a HAD_FEWER_PENALTIES-shaped concept genuinely
         compatible with three different mechanics) fill multiple mechanic
         slots by itself, which real testing showed reintroduces the
         "renamed duplicate" problem for a general IDEAS request.
      2. Same mechanic-breadth pass, but allowing a REUSED capability --
         restricted to a real PLAYABLE_NOW concept only, never a redundant
         CONCEPT_ONLY reuse (that would just be noise). This is what lets a
         request surface both a MATCHING-Heisman AND a SORTING_TIMELINE-
         Heisman concept when that capability is the only real variant
         either mechanic has for a given competition (a real, disclosed
         resource limit -- see this module's HIGHER_LOWER_STREAK/
         ELIMINATION_SURVIVAL docstring) -- without that reuse escaping into
         the general case, since pass 2 only ever fires for a mechanic pass
         1 could not otherwise fill.
      3. At most ONE additional concept per capability_id not already used,
         for breadth across different football relationships.
      4. Backfill from whatever real candidates remain, never fabricated.
    """
    selected: list[dict] = []
    used_capability_ids: set[str] = set()
    used_mechanics: set[str] = set()

    for concept in concepts_sorted:
        if len(selected) >= count:
            break
        mech = concept["core_mechanic"]
        cap_id = concept["required_catalog_relationships"][0]["capability_id"]
        if mech in used_mechanics or cap_id in used_capability_ids:
            continue
        selected.append(concept)
        used_capability_ids.add(cap_id)
        used_mechanics.add(mech)

    if len(selected) < count:
        for concept in concepts_sorted:
            if len(selected) >= count:
                break
            mech = concept["core_mechanic"]
            if mech in used_mechanics or concept["playability_status"] != "PLAYABLE_NOW":
                continue
            selected.append(concept)
            used_capability_ids.add(concept["required_catalog_relationships"][0]["capability_id"])
            used_mechanics.add(mech)

    if len(selected) < count:
        selected_ids = {c["concept_id"] for c in selected}
        for concept in concepts_sorted:
            if len(selected) >= count:
                break
            if concept["concept_id"] in selected_ids:
                continue
            cap_id = concept["required_catalog_relationships"][0]["capability_id"]
            if cap_id in used_capability_ids:
                continue
            selected.append(concept)
            selected_ids.add(concept["concept_id"])
            used_capability_ids.add(cap_id)

    if len(selected) < count:
        selected_ids = {c["concept_id"] for c in selected}
        for concept in concepts_sorted:
            if len(selected) >= count:
                break
            if concept["concept_id"] in selected_ids:
                continue
            selected.append(concept)
            selected_ids.add(concept["concept_id"])

    return selected


def _generate_real_preview(concept: dict) -> dict:
    """Real playable preview -- Phase 6: dispatches through
    tools.director_v02.mechanic_engine.py by the concept's own core_mechanic
    (taxonomy_id), the SAME generator + gateway/services/packages.
    save_package() every /v1/creator/mechanics/round call uses. Zero
    preview-only generation code -- this is the identical real path a
    private round is built through."""
    from tools.director_v02 import mechanic_engine
    from gateway.services import packages as packages_service

    rel = concept["required_catalog_relationships"][0]
    taxonomy_id = concept["core_mechanic"]
    try:
        if taxonomy_id in ("MULTIPLE_CHOICE_SINGLE_FACT", "POSITION_LINEUP_GRID"):
            result = mechanic_engine.generate_guess_round(
                domain=rel["domain"], relationship_predicate=rel["relationship_predicate"],
                question_count=3, seed=None)
            if result.get("package_id") and result.get("qa_status") == "PASSED":
                stored = packages_service.save_package(result)
                sample = stored["questions"][0] if stored.get("questions") else None
                return {"package_id": stored["package_id"], "qa_status": stored["qa_status"],
                        "round_count": stored.get("question_count"),
                        "sample_prompt": sample["question"] if sample else None,
                        "sample_options": sample["options"] if sample else None}
            return {"package_id": None, "qa_status": result.get("qa_status"), "error": result.get("error")}

        if taxonomy_id == "PROGRESSIVE_CLUE_IDENTIFY":
            result = mechanic_engine.generate_clue_round(target_count=3, seed="concept-preview")
            if result.get("qa_status") == "PASSED" and result.get("puzzles"):
                stored = packages_service.save_package(result)
                first = stored["puzzles"][0]
                return {"package_id": stored["package_id"], "qa_status": stored["qa_status"],
                        "round_count": len(stored["puzzles"]),
                        "sample_prompt": first["clues"][0]["display_text"], "sample_options": None}
            return {"package_id": None, "qa_status": result.get("qa_status"), "error": "no puzzles generated"}

        if taxonomy_id == "MATCHING":
            result = mechanic_engine.generate_matching_round(
                variant=concept["_mechanic_variant"], round_count=1, pair_count=4, seed="concept-preview")
            if result.get("qa_status") == "PASSED" and result.get("rounds"):
                stored = packages_service.save_package(result)
                first = stored["rounds"][0]
                return {"package_id": stored["package_id"], "qa_status": stored["qa_status"],
                        "round_count": len(stored["rounds"]), "sample_prompt": first["prompt"],
                        "sample_options": [it["label"] for it in first["left_items"]]}
            return {"package_id": None, "qa_status": result.get("qa_status"), "error": result.get("shortfall_reason")}

        if taxonomy_id == "SORTING_TIMELINE":
            result = mechanic_engine.generate_sorting_round(
                variant=concept["_mechanic_variant"], round_count=1, item_count=4, seed="concept-preview")
            if result.get("qa_status") == "PASSED" and result.get("rounds"):
                stored = packages_service.save_package(result)
                first = stored["rounds"][0]
                return {"package_id": stored["package_id"], "qa_status": stored["qa_status"],
                        "round_count": len(stored["rounds"]), "sample_prompt": first["prompt"],
                        "sample_options": [it["label"] for it in first["items_shuffled"]]}
            return {"package_id": None, "qa_status": result.get("qa_status"), "error": result.get("shortfall_reason")}

        if taxonomy_id == "HIGHER_LOWER_STREAK":
            result = mechanic_engine.generate_higher_lower_round(
                variant=concept["_mechanic_variant"], sequence_length=8, seed="concept-preview")
            if result.get("qa_status") == "PASSED" and result.get("sequence"):
                stored = packages_service.save_package(result)
                return {"package_id": stored["package_id"], "qa_status": stored["qa_status"],
                        "round_count": stored.get("sequence_length"),
                        "sample_prompt": stored["game_instructions"],
                        "sample_options": [stored["sequence"][0]["label"]]}
            return {"package_id": None, "qa_status": result.get("qa_status"), "error": result.get("shortfall_reason")}

        if taxonomy_id == "ELIMINATION_SURVIVAL":
            result = mechanic_engine.generate_elimination_round(
                variant=concept["_mechanic_variant"], sequence_length=8, seed="concept-preview")
            if result.get("qa_status") == "PASSED" and result.get("sequence"):
                stored = packages_service.save_package(result)
                return {"package_id": stored["package_id"], "qa_status": stored["qa_status"],
                        "round_count": stored.get("sequence_length"),
                        "sample_prompt": stored["sequence"][0]["prompt"], "sample_options": None}
            return {"package_id": None, "qa_status": result.get("qa_status"), "error": result.get("shortfall_reason")}
    except Exception as e:  # never let a preview-generation bug break the whole /v1/creator/concepts response
        return {"package_id": None, "qa_status": "FAILED", "error": f"{type(e).__name__}: {e}"}

    return {"package_id": None, "qa_status": "FAILED", "error": f"no preview generator wired for {taxonomy_id!r}"}


_VALID_REQUEST_TYPES = frozenset({"IDEAS", "PLAYABLE_IDEAS", "MIXED"})


def generate_concepts(request_text: str, *, request_type: str = "IDEAS", requested_count: int = 10,
                       exclude_concept_ids: list[str] | None = None) -> dict:
    """The Phase 5 completion target, end to end: plain-language request ->
    distinct ranked CONCEPTS -> honest feasibility -> no duplicates ->
    real playable preview when supported (PLAYABLE_IDEAS/MIXED).

    Never pads: if fewer than `requested_count` concepts genuinely qualify,
    the real count is returned along with a coverage_gap_report explaining
    exactly why."""
    if request_type not in _VALID_REQUEST_TYPES:
        raise ValueError(f"request_type must be one of {sorted(_VALID_REQUEST_TYPES)}, got {request_type!r}")
    exclude = set(exclude_concept_ids or [])

    all_candidates = _all_candidate_concepts(request_text)
    total_candidates = len(all_candidates)

    deduplicated = _deduplicate_by_signature(all_candidates)
    deduplicated_count = len(deduplicated)

    deduplicated = [c for c in deduplicated if c["concept_id"] not in exclude]
    deduplicated.sort(key=_score_for_ranking)

    if request_type == "PLAYABLE_IDEAS":
        pool = [c for c in deduplicated if c["playability_status"] == "PLAYABLE_NOW"]
        eligible_after_filter = len(pool)
        selected = _select_diverse(pool, requested_count)
        for concept in selected:
            concept["preview"] = _generate_real_preview(concept)
        returned_count = len(selected)
        result = {"concepts": selected}

    elif request_type == "MIXED":
        playable_pool = [c for c in deduplicated if c["playability_status"] == "PLAYABLE_NOW"]
        concept_only_pool = [c for c in deduplicated if c["playability_status"] == "CONCEPT_ONLY"]
        half = max(1, requested_count // 2)
        playable_budget = min(len(playable_pool), max(half, requested_count - len(concept_only_pool)))
        selected_playable = _select_diverse(playable_pool, min(playable_budget, requested_count))
        remaining = requested_count - len(selected_playable)
        selected_concept_only = _select_diverse(concept_only_pool, max(remaining, 0))
        for concept in selected_playable:
            concept["preview"] = _generate_real_preview(concept)
        returned_count = len(selected_playable) + len(selected_concept_only)
        eligible_after_filter = len(playable_pool) + len(concept_only_pool)
        result = {"playable_concepts": selected_playable, "concept_only_ideas": selected_concept_only}

    else:  # IDEAS
        selected = _select_diverse(deduplicated, requested_count)
        returned_count = len(selected)
        eligible_after_filter = len(deduplicated)
        result = {"concepts": selected}

    coverage_gap_report = None
    if returned_count < requested_count:
        coverage_gap_report = {
            "requested_count": requested_count,
            "returned_count": returned_count,
            "shortfall": requested_count - returned_count,
            "total_candidate_concepts_generated": total_candidates,
            "distinct_after_semantic_deduplication": deduplicated_count,
            "qualified_for_request_type": eligible_after_filter,
            "reason": (
                f"Requested {requested_count}, but only {returned_count} real concept(s) qualify for "
                f"request_type={request_type!r} after generating {total_candidates} real candidate concept(s), "
                f"deduplicating to {deduplicated_count} distinct diversity signature(s), and filtering to "
                f"{eligible_after_filter} eligible for this request type. Never padded with fabricated concepts."
            ),
        }

    result["request_type"] = request_type
    result["requested_count"] = requested_count
    result["returned_count"] = returned_count
    result["coverage_gap_report"] = coverage_gap_report
    return result
