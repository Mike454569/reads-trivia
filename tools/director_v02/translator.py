"""Provider-agnostic translator entrypoint: `translate(request_text) -> dict`.

This module contains zero provider-specific logic and zero football-database
access -- it only selects and calls a `providers.base.Translator`
implementation. Callers (the v0.2 pipeline) depend on this module, never on
a specific provider module, so swapping providers never touches pipeline code.

`provider="auto"` (added for the Production LLM Integration for Game Creator
milestone): the real production selection policy. Uses the real Anthropic
provider when a credential is configured, with an honest, bounded fallback to
the deterministic mock translator -- never an invented spec, never a crash.
Exactly two decision points, both narrow:
  1. No `ANTHROPIC_API_KEY` configured at all -> go straight to mock. This is
     the ordinary case for local dev/most environments, not an error.
  2. A credential IS configured and the real provider was called, but
     `providers.anthropic_provider` reports `provider_error: True` on its
     result (see that module's docstring -- set ONLY for a genuine
     infrastructure/parsing failure, e.g. exhausted retries on a network
     error, non-JSON reply, wrong shape) -> retry the SAME request through
     mock rather than surfacing a bare provider failure to the caller.
A real model judgment (TRANSLATED / UNDERSTOOD_UNSUPPORTED_MECHANIC /
NEEDS_CLARIFICATION / a content-level NO_MATCH) is NOT a provider_error and
is never overridden by falling back to mock -- see anthropic_provider.py's
own docstring for why that distinction matters (mock re-guessing over a real,
confident model answer would make results LESS honest, not more resilient).
Every result this returns also carries `fallback_used: bool` and, when true,
`primary_provider_attempted`/`fallback_reason`, so callers (audit_log via
pipeline.py) can see exactly which path served a given request."""
from __future__ import annotations

import os

from .providers.base import Translator
from .providers.mock import MockDeterministicTranslator

DEFAULT_PROVIDER = "mock"


def get_translator(provider: str = DEFAULT_PROVIDER) -> Translator:
    if provider == "mock":
        return MockDeterministicTranslator()
    if provider == "anthropic":
        # Imported lazily -- this import has no side effects at module load
        # time other than reading (not printing) an env var inside __init__,
        # but keeping it lazy means `providers.mock`-only test runs never
        # even import urllib/network-facing code.
        from .providers.anthropic_provider import AnthropicTranslator
        return AnthropicTranslator()
    raise ValueError(f"Unknown translator provider '{provider}' (known: mock, anthropic, auto)")


def _translate_auto(request_text: str) -> dict:
    from .providers.anthropic_provider import CREDENTIAL_ENV_VAR

    if not os.environ.get(CREDENTIAL_ENV_VAR):
        result = MockDeterministicTranslator().translate(request_text)
        result["fallback_used"] = True
        result["primary_provider_attempted"] = None
        result["fallback_reason"] = f"{CREDENTIAL_ENV_VAR} is not configured on this server."
        return result

    from .providers.anthropic_provider import AnthropicTranslator
    primary = AnthropicTranslator().translate(request_text)
    if not primary.get("provider_error"):
        primary["fallback_used"] = False
        return primary

    fallback = MockDeterministicTranslator().translate(request_text)
    fallback["fallback_used"] = True
    fallback["primary_provider_attempted"] = "anthropic"
    fallback["fallback_reason"] = primary.get("translator_notes", "anthropic provider_error")
    return fallback


def translate(request_text: str, *, provider: str = DEFAULT_PROVIDER) -> dict:
    """Returns a TranslationResult dict. See providers/base.py for the exact
    shape (provider="auto" additionally sets fallback_used and friends --
    see module docstring)."""
    if provider == "auto":
        return _translate_auto(request_text)
    translator = get_translator(provider)
    return translator.translate(request_text)
