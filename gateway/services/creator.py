"""Reads Engine Gateway -- Game Creator orchestration (v1.8, Part B/C/G/H).

Thin wrapper, same discipline as generation.py's own module docstring
("no Director/Game Factory logic reimplemented here"): every real decision
-- what's feasible, how a package gets generated/QA'd, how it's stored --
already lives in tools/director_v02/feasibility.py, gateway/services/
generation.py, and gateway/services/packages.py. This module only
sequences those calls for the three Creator-specific routes
(gateway/app.py's /v1/creator/*) and shapes their responses.

--- SECURITY (Part L/M) ---
Every function here takes ONLY `request_text` (a plain string, already
length-capped by CreatorFeasibilityRequest/CreatorGenerateRequest at the
Gateway boundary) or an already-validated `package_id` -- never a raw spec,
table name, file path, or code fragment. `request_text` flows through
EXACTLY the same translator -> validator pipeline every other caller
(admin /v1/games/generate, public gameplay) already uses; the Creator gets
no bypass and no elevated trust for its input. See providers/mock.py's own
docstring for why that translator specifically cannot turn attacker text
into an executable value under any input.
"""
from __future__ import annotations

from tools.director_v02 import feasibility as feasibility_mod

from . import generation, packages
from ..errors import GatewayError


def assess_feasibility(request_text: str) -> dict:
    return feasibility_mod.assess(request_text, provider="mock")


def generate_for_review(*, request_text: str, puzzle_count, difficulty, seed) -> dict:
    """Reuses generation.generate() -- the SAME admin single-slot pipeline
    /v1/games/generate already uses, not a second generation path (Part B:
    'reuse the real existing Director/Factory architecture'). A
    Creator-generated package is stored exactly like any other admin
    generation (packages.save_package, review_status starts 'GENERATED')."""
    result = generation.generate(
        request_text=request_text, spec=None, provider="mock",
        puzzle_count=puzzle_count, difficulty=difficulty, seed=seed,
    )
    if result.get("package_id") and result.get("qa_status") == "PASSED":
        return packages.save_package(result)
    return result


def list_review_queue(review_status: str | None) -> list[dict]:
    return packages.list_packages(review_status=review_status)


def set_review_status(package_id: str, review_status: str) -> dict:
    try:
        return packages.set_review_status(package_id, review_status)
    except FileNotFoundError:
        raise GatewayError("PACKAGE_NOT_FOUND", "No such package.")
    except packages.PackageIdInvalid:
        raise GatewayError("PACKAGE_NOT_FOUND", "No such package.")
