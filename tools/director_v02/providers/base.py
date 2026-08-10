"""Provider-agnostic translator interface.

A provider's ONLY job is: user text in, a TranslationResult dict out.
Nothing else. Enforced by convention here (see the docstring on `translate`)
and by the fact that no provider module imports `tools.quiz_export`,
`game_factory`, `game_director`, or opens a database connection -- a
provider has no way to reach football data even if it wanted to.

TranslationResult shape (every provider must return exactly this):
    {
        "raw_request_text": str,
        "translator_id": str,           # e.g. "mock-deterministic-v1", "anthropic:claude-sonnet-5"
        "translation_status": str,      # one of TRANSLATION_STATUSES below
        "spec": dict | None,            # a dict matching schema.ALL_SPEC_KEYS, or None
        "translator_notes": str,        # human-readable, informational only -- NEVER executed,
                                         # NEVER interpolated into any query/path/command

        # Only present when translation_status == "NEEDS_CLARIFICATION" (see
        # Director v0.3 Part D / DIRECTOR_V03_CLARIFICATION_CONTRACT.md):
        "understood": dict | None,          # structured fields the translator IS confident
                                             # about (e.g. {"competition": "NFL"}) -- values
                                             # here still go through the same allowlist checks
                                             # as a normal spec would, never trusted as-is.
        "missing_fields": list[str] | None, # which DirectorSpec fields remain unresolved
        "clarifying_question": str | None,  # a short question to show a human -- display
                                             # text only, never executed or parsed as intent.
    }

`translation_status` values:
    TRANSLATED                    -- spec is populated and, in the translator's
                                      judgment, matches an allowlisted shape.
                                      (Still re-validated independently by
                                      validator.py -- this is not trusted.)
    UNDERSTOOD_UNSUPPORTED_MECHANIC -- the translator recognized a specific,
                                      real game concept but it has no
                                      expressible/registered mapping (e.g.
                                      "identify a player from clues", or a
                                      compound request where at least one
                                      part has no supported data). spec is None.
    NEEDS_CLARIFICATION           -- the translator recognized SOME relevant
                                      signal (e.g. "NFL", "player") but not
                                      enough to resolve to a specific
                                      capability or a specific unsupported
                                      concept. Must NOT guess -- surfaces
                                      `understood`/`missing_fields`/
                                      `clarifying_question` instead. spec is None.
    NO_MATCH                      -- the translator could not confidently map
                                      the request to anything. spec is None.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

TRANSLATION_STATUSES = frozenset({
    "TRANSLATED",
    "UNDERSTOOD_UNSUPPORTED_MECHANIC",
    "NEEDS_CLARIFICATION",
    "NO_MATCH",
})

# Production controls every provider implementation must respect (see
# GAME_DIRECTOR_V02_REPORT.md Section "Cost and resource controls" for why).
MAX_REQUEST_TEXT_CHARS = 500


class Translator(ABC):
    translator_id: str = "unset"

    @abstractmethod
    def translate(self, request_text: str) -> dict:
        """Returns a TranslationResult dict (see module docstring). Must not
        raise for ordinary bad/hostile input -- return NO_MATCH instead.
        May raise only for genuine infrastructure failure (e.g. network
        error in a real provider), which callers must treat as a translation
        failure, not a crash of the whole pipeline."""
        raise NotImplementedError

    def _truncate(self, request_text: str) -> str:
        """Shared guard: never forward more than MAX_REQUEST_TEXT_CHARS to
        any provider, real or mock. Applied before any provider-specific
        logic runs."""
        return request_text[:MAX_REQUEST_TEXT_CHARS]
