"""Creator Intelligence -- Phase 5, tightly scoped to the already-approved
design. Reuses, never redesigns: the capability catalog (tools/director_v02/
catalog.py), feasibility vocabulary (tools/director_v02/feasibility.py), and
the existing private-preview flow (POST /v1/games/generate + GET /v1/games/
{package_id} + POST /v1/creator/review, unchanged, zero new generation
code). The async job system (creator_jobs.py) and compiler (compiler.py)
are NOT touched by this module -- generating ideas is fast and synchronous
(a bag-of-words scoring pass over 23 registered capabilities), and no idea
here ever creates a NEW capability; it only surfaces REAL, already-
registered ones. Reusing them would be scope creep this phase doesn't need.

Deliberately narrow completion target (owner-specified): plain-language
request -> distinct ranked ideas -> honest feasibility -> no duplicates ->
playable private preview when supported. This module delivers exactly the
first four; the fifth is the existing Gateway generate/load/review flow,
reused as-is by feeding a chosen idea's own (mechanic, domain,
relationship_predicate) as a `spec` to the ALREADY-EXISTING, admin-only
POST /v1/games/generate -- the same route any other admin caller already
uses, no new trust surface.

--- RETRIEVAL: real, not fabricated ---
Every idea maps to one real row in registry.CAPABILITY_REGISTRY -- this
module never invents a (mechanic, domain, predicate) triple. Matching is a
real bag-of-words overlap between the request text and each capability's
own REAL metadata already on file (category, domain, relationship_predicate,
entity_type, object_type, competition_id) -- no separate keyword list to
maintain or drift out of sync with the registry, unlike providers/mock.py's
hand-maintained, single-best-match keyword tree (deliberately NOT reused
here: that module is designed to pick exactly ONE winner via a sequential
if/elif chain, the opposite of what "distinct ranked ideas" -- plural --
needs; building a second, parallel single-match matcher would be the kind
of redesign this phase was told to avoid).

--- DEDUPLICATION: structural, not a filter ---
Each idea corresponds to exactly one dict key in CAPABILITY_REGISTRY --
iterating the registry's own keys makes duplicate ideas structurally
impossible, not merely filtered after the fact.

--- FEASIBILITY: honest, catalog-backed ---
Every idea's `catalog_status`/`catalog_vocabulary_status`/`can_preview`
come directly from feasibility.catalog_status_for()/raw_catalog_state_for()
-- the SAME real, corrected vocabulary Phase 1-3 already built and tested.
`can_preview` is True only for the vocabulary states that are actually
proven to generate (SUPPORTED, SUPPORTED_WITH_LIMITATIONS,
VERIFIED_NOT_RELEASED) -- never claimed for a capability that hasn't
reached at least GENERATION_VERIFIED, matching the exact real bug
("labeled SUPPORTED but generation returned Load failed") this whole
reliability effort exists to prevent.
"""
from __future__ import annotations

import re

from . import feasibility as feasibility_mod
from . import registry

_WORD_RE = re.compile(r"[a-z]+")

# Vocabulary states honestly proven to generate -- see feasibility.py's
# own _CATALOG_STATE_TO_VOCAB mapping (Phase 1-3, unchanged here).
_PREVIEWABLE_VOCAB = frozenset({"SUPPORTED", "SUPPORTED_WITH_LIMITATIONS", "VERIFIED_NOT_RELEASED"})

# Deterministic tie-break ranking for feasibility tiers -- higher is better.
_VOCAB_RANK = {
    "SUPPORTED": 3,
    "SUPPORTED_WITH_LIMITATIONS": 2,
    "VERIFIED_NOT_RELEASED": 1,
    "IMPLEMENTED_NOT_VERIFIED": 0,
    "DATA_EXISTS_UNVERIFIED": 0,
    "UNDERSTOOD_NOT_IMPLEMENTED": 0,
    "TEMPORARILY_UNAVAILABLE": 0,
    None: -1,
}


def _words(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _capability_signature_words(mechanic: str, domain: str, predicate: str, cap: dict) -> set[str]:
    """Real words derived ONLY from this capability's own already-registered
    metadata -- never a separately hand-maintained keyword list."""
    parts = [
        cap.get("category", ""),
        domain.replace("_", " "),
        predicate.replace("_", " "),
        mechanic.replace("_", " "),
        str(cap.get("entity_type", "")).replace("_", " "),
        str(cap.get("object_type", "")).replace("_", " "),
        str(cap.get("competition_id", "")),
    ]
    return _words(" ".join(parts))


# Corpus-frequency stopwords -- computed from the REAL registry, not a
# hand-typed list. A word appearing in nearly every capability's own
# signature (e.g. "guess", present in 96% of the 23 real capabilities
# today since almost all share the "guess" mechanic) carries no real
# discriminative signal and would otherwise inflate every idea's score
# roughly equally, diluting genuinely relevant matches with noise. Words
# still common but meaningfully distinguishing (e.g. "nfl" at ~70%, real
# signal against a "cfb"-worded request) are deliberately kept -- the bar
# is set high (>90%) so only truly universal words are dropped.
_STOPWORD_DOC_FREQUENCY_THRESHOLD = 0.90


def _compute_stopwords() -> frozenset:
    doc_count: dict[str, int] = {}
    total = len(registry.CAPABILITY_REGISTRY)
    for (mechanic, domain, predicate), cap in registry.CAPABILITY_REGISTRY.items():
        for w in _capability_signature_words(mechanic, domain, predicate, cap):
            doc_count[w] = doc_count.get(w, 0) + 1
    return frozenset(w for w, n in doc_count.items() if total and n / total > _STOPWORD_DOC_FREQUENCY_THRESHOLD)


_STOPWORDS = _compute_stopwords()


def generate_ideas(request_text: str, *, max_ideas: int = 10) -> list[dict]:
    """Real, deterministic, synchronous. Returns up to `max_ideas` DISTINCT
    ideas (one per real registered capability, structurally impossible to
    duplicate), ranked by (match strength, feasibility tier, domain,
    predicate) -- never padded below the real qualified count (a request
    matching only 2 real capabilities returns exactly 2, never invented
    filler). An idea with zero real word overlap against the request is
    never included -- "distinct ranked ideas" means real candidates, not
    every registered capability listed regardless of relevance."""
    request_words = _words(request_text) - _STOPWORDS
    scored: list[tuple[int, int, str, str, dict]] = []

    for (mechanic, domain, predicate), cap in registry.CAPABILITY_REGISTRY.items():
        sig_words = _capability_signature_words(mechanic, domain, predicate, cap) - _STOPWORDS
        overlap = request_words & sig_words
        match_score = len(overlap)
        if match_score == 0:
            continue

        try:
            catalog_status = feasibility_mod.raw_catalog_state_for(mechanic, domain, predicate)
            catalog_vocabulary_status = feasibility_mod.catalog_status_for(mechanic, domain, predicate)
        except Exception:
            catalog_status = None
            catalog_vocabulary_status = None

        can_preview = catalog_vocabulary_status in _PREVIEWABLE_VOCAB
        vocab_rank = _VOCAB_RANK.get(catalog_vocabulary_status, -1)

        idea = {
            "mechanic": mechanic,
            "domain": domain,
            "relationship_predicate": predicate,
            "category": cap.get("category"),
            "match_score": match_score,
            "matched_words": sorted(overlap),
            "catalog_status": catalog_status,
            "catalog_vocabulary_status": catalog_vocabulary_status,
            "can_preview": can_preview,
            "known_limitations": list(cap.get("known_limitations", [])),
        }
        # Sort key: higher match_score first, higher vocab_rank first, then
        # deterministic alphabetical tie-break -- never randomized, so the
        # same request always returns the same order.
        scored.append((-match_score, -vocab_rank, domain, predicate, idea))

    scored.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
    return [t[4] for t in scored[:max_ideas]]
