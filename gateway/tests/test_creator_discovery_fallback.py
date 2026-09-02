"""Creator/Game Quality Correction pass -- Creator Discovery fallback
regression tests (the pass's own prompts 63-70). Before this pass, every
one of these broad-but-clearly-football-related requests fell all the way
to a flat NO_MATCH just because it didn't name an exact registered
mechanic. Fixed by wiring tools/director_v02/creator_intelligence.py's
existing (but previously unused) generate_ideas() into
providers/mock.py's translate() as a real fallback, plus a few curated
overrides for topic clusters (named school/franchise, quarterbacks,
defenders/big plays, college stars in the NFL) where the generic bag-of-
words matcher's only real overlap was a single over-broad word.

Do not call NO_MATCH here a bug that must always be exactly
NEEDS_CLARIFICATION -- the assertion is "not NO_MATCH" (a real, playable
menu of options was surfaced), matching this pass's own instruction to
return/generate a relevant supported concept rather than NO_MATCH,
without claiming a fixed exact-match domain the fallback was never
designed to guarantee for a genuinely broad request.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

_DISCOVERY_PROMPTS = [
    "What cool game can you make about Alabama?",
    "Make me something fun about NFL quarterbacks.",
    "Give me a weird college football game.",
    "Make me something about players who transferred.",
    "Give me a game about college stars in the NFL.",
    "Make me something about famous Super Bowl teams.",
    "Give me a game about defenders making big plays.",
    "Make me something about rankings and chaos.",
]


@pytest.mark.parametrize("request_text", _DISCOVERY_PROMPTS)
def test_broad_football_prompt_never_returns_no_match(request_text):
    from tools.director_v02.providers.mock import MockDeterministicTranslator

    r = MockDeterministicTranslator().translate(request_text)
    assert r["translation_status"] != "NO_MATCH", (
        f"{request_text!r} still returns NO_MATCH -- Creator Discovery fallback did not fire"
    )


@pytest.mark.parametrize("request_text", _DISCOVERY_PROMPTS)
def test_broad_football_prompt_suggestions_are_real_registered_capabilities(request_text):
    """Whatever the fallback suggests must be real (a real registry.py
    entry), never a fabricated domain/predicate string -- 'only suggest
    concepts that are actually playable'."""
    from tools.director_v02 import registry
    from tools.director_v02.providers.mock import MockDeterministicTranslator

    r = MockDeterministicTranslator().translate(request_text)
    if r["translation_status"] == "TRANSLATED":
        spec = r["spec"]
        assert (spec["mechanic"], spec["domain"], spec["relationship_predicate"]) in registry.CAPABILITY_REGISTRY
    elif r["translation_status"] == "NEEDS_CLARIFICATION":
        suggested = (r.get("understood") or {}).get("suggested_capabilities") or []
        assert suggested, f"{request_text!r}: NEEDS_CLARIFICATION with no real suggestions offered"
        for s in suggested:
            assert ("guess", s["domain"], s["relationship_predicate"]) in registry.CAPABILITY_REGISTRY or \
                   ("identify_player_from_clues", s["domain"], s["relationship_predicate"]) in registry.CAPABILITY_REGISTRY


def test_genuinely_offtopic_request_is_unaffected_by_discovery_fallback():
    """The fallback must never fire for real off-topic content -- confirms
    it didn't loosen Rule D's existing off-topic handling."""
    from tools.director_v02.providers.mock import MockDeterministicTranslator

    r = MockDeterministicTranslator().translate("What's my favorite food?")
    assert r["translation_status"] in ("NO_MATCH", "UNDERSTOOD_UNSUPPORTED_MECHANIC")
