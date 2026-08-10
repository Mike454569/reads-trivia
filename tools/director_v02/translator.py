"""Provider-agnostic translator entrypoint: `translate(request_text) -> dict`.

This module contains zero provider-specific logic and zero football-database
access -- it only selects and calls a `providers.base.Translator`
implementation. Callers (the v0.2 pipeline) depend on this module, never on
a specific provider module, so swapping providers never touches pipeline code.
"""
from __future__ import annotations

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
    raise ValueError(f"Unknown translator provider '{provider}' (known: mock, anthropic)")


def translate(request_text: str, *, provider: str = DEFAULT_PROVIDER) -> dict:
    """Returns a TranslationResult dict. See providers/base.py for the exact shape."""
    translator = get_translator(provider)
    return translator.translate(request_text)
