"""40-Format Expansion pass -- bridges the two-track format-compatibility gap
documented in tools/director_v02/visual_templates.py's own module docstring:
gateway/services/creator.py's `_resolve_format()` already does real
explicit-compatible / unspecified-auto-select / explicit-incompatible
resolution for the 6 direct-mechanic NL-bridge taxonomies, but the much
larger 60-entry `CAPABILITY_REGISTRY` ("guess"/"identify_player_from_clues")
track never consulted `visual_templates.py` at all -- each capability just
hardcodes its own `visual_template` string literal (or falls back to
DEFAULT_MULTIPLE_CHOICE).

`resolve_format_for_capability()` is the analogous entry point for that
track, called from validator.py.validate_translation(). It deliberately
does NOT reproduce creator.py's "auto-select the mechanic's first-registered
default" behavior for the unspecified case -- that would silently override
capabilities like lineup.py/lineup_college.py, which already set their OWN
real non-default visual_template (POSITION_LINEUP/POSITION_LINEUP_COLLEGE)
per capability, breaking their real rendering. Instead: unspecified always
means "keep this capability's own existing, already-proven default,
unchanged" -- a true no-op, matching this pass's explicit backward-
compatibility requirement.

When a format IS explicitly requested, it's accepted only if BOTH:
  1. it's mechanic-compatible (visual_templates.FORMAT_COMPATIBILITY), and
  2. it's structurally safe to apply to ANY capability sharing that
     mechanic -- i.e. its payload_schema is None (needs no adapter-specific
     extra data beyond the question/options every 'guess'/'identify_player_
     from_clues' capability already produces), or it already equals this
     capability's own existing default (a real, harmless confirmation).
A format whose payload_schema requires adapter-specific data (e.g.
POSITION_LINEUP's `positions` list) is correctly rejected as
FORMAT_INCOMPATIBLE for any capability that doesn't already natively
produce that shape -- this is real payload-shape safety, not just a
mechanic-family check, since forcing e.g. POSITION_LINEUP onto the Draft
capability would ask the frontend to render a lineup board Draft's adapter
never populates.
"""
from __future__ import annotations

from . import visual_templates

# Real, disclosed schema-mechanic -> format-registry-mechanic mapping. The
# format registry's FORMAT_COMPATIBILITY is keyed by the same lowercase
# strings schema.py's ALLOWED_MECHANICS/mechanic_engine.py's generator
# functions use for the 5 "direct" mechanics, but "identify_player_from_clues"
# (the DirectorSpec-facing name) is registered in the format registry under
# the shorter "clue" key (see CARD_STACK's own supported_mechanics) -- this
# is the one real translation point between the two naming conventions for
# the guess-mechanic track, mirroring creator.py's own
# _TAXONOMY_TO_FORMAT_MECHANIC pattern exactly.
_SCHEMA_MECHANIC_TO_FORMAT_MECHANIC = {
    "guess": "guess",
    "identify_player_from_clues": "clue",
}

# Real finding: "identify_player_from_clues" capabilities never set their
# own "visual_template" key (neither generation function for that mechanic
# reads/writes it -- the frontend's Player From Clues screen is a dedicated
# UI, not visual_template-driven). "DEFAULT_MULTIPLE_CHOICE" is only the
# correct fallback for the "guess" mechanic; CARD_STACK is this mechanic's
# real, already-registered format.
_DEFAULT_VISUAL_TEMPLATE_BY_MECHANIC = {
    "guess": "DEFAULT_MULTIPLE_CHOICE",
    "identify_player_from_clues": "CARD_STACK",
}


class FormatIncompatibleError(ValueError):
    """Raised by resolve_format_for_capability() when an explicitly
    requested format cannot honestly apply -- callers (validator.py)
    convert this into a real GateResult, never let it propagate raw."""

    def __init__(self, message: str, suggested_formats: list[str]):
        super().__init__(message)
        self.suggested_formats = suggested_formats


def resolve_format_for_capability(capability: dict, spec_mechanic: str, requested_format: str | None) -> str:
    """Returns the real visual_template string that should back this
    capability's generated questions. Never silently substitutes a
    different format than what was asked for -- raises FormatIncompatibleError
    instead (mirroring creator.py._resolve_format()'s raise-not-substitute
    discipline for the other track)."""
    existing_default = capability.get(
        "visual_template", _DEFAULT_VISUAL_TEMPLATE_BY_MECHANIC.get(spec_mechanic, "DEFAULT_MULTIPLE_CHOICE")
    )

    if requested_format is None:
        return existing_default

    if requested_format == existing_default:
        return requested_format

    format_mechanic = _SCHEMA_MECHANIC_TO_FORMAT_MECHANIC.get(spec_mechanic)
    if format_mechanic is None or not visual_templates.is_format_compatible(requested_format, format_mechanic):
        raise FormatIncompatibleError(
            f"format={requested_format!r} is not compatible with mechanic {spec_mechanic!r}.",
            suggested_formats=visual_templates.formats_for_mechanic(format_mechanic or ""),
        )

    entry = visual_templates.lookup(requested_format)
    if entry is not None and entry.get("payload_schema") is not None:
        raise FormatIncompatibleError(
            f"format={requested_format!r} requires adapter-specific data "
            f"({sorted(entry['payload_schema'].keys())}) this capability's adapter does not produce.",
            suggested_formats=[existing_default],
        )

    return requested_format
