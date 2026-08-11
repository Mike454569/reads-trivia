"""Director v0.8 -- Mechanic Registry (v1.8, Part D).

A mechanic is WHAT the player does and how an answer is validated -- kept
strictly separate from a visual template (HOW the puzzle is presented, see
visual_templates.py). This registry does not change how any capability
actually generates or validates content (that logic already lives in
registry.py's CAPABILITY_REGISTRY / each generate_fn); it is a documented,
queryable index over the mechanics that already exist, built by auditing the
real, already-proven pipeline rather than inventing a parallel system.

Three mechanics are real today:
  - `guess`: N options (currently always 4), single `correctIndex`, server-
    authoritative validation (`options[correctIndex]` / `answer` string
    equality). Every CAPABILITY_REGISTRY entry with mechanic="guess"
    (Draft, Championship, and this milestone's new lineup capability) shares
    this exact contract, regardless of visual template.
  - `identify_player_from_clues`: a progressive clue sequence, no fixed
    option count -- see PLAYER_FROM_CLUES_MECHANIC_SPEC.md.
  - `connection_path`: step-by-step path-guessing between two graph nodes
    (Six Degrees / Coach Connections). Not in CAPABILITY_REGISTRY at all --
    it has no Director-pipeline capability entry; it is served directly by
    gateway/services/public_six_degrees.py against graph_path_cache. Listed
    here for completeness (Part D asks this registry to audit and reuse
    EXISTING mechanics, which includes this one), not because the Director
    pipeline can generate it.
"""
from __future__ import annotations

MECHANIC_REGISTRY: dict[str, dict] = {
    "guess": {
        "description": "Single-select multiple choice. A fixed set of options, one server-known "
                        "correctIndex, validated by exact (case-folded) string match against the "
                        "chosen option's label -- never client-supplied truth.",
        "answer_contract": "options: list[str], correctIndex: int, client sends only the chosen "
                            "option's text (or index); server is the sole source of truth.",
        "used_by_capabilities": [
            ("guess", "NFL_DRAFT", "DRAFTED_BY"),
            ("guess", "NFL_CHAMPIONSHIP", "TEAM_POSTSEASON_RESULT"),
            ("guess", "NFL_OFFENSE_LINEUP", "TEAM_OF_STARTING_LINEUP"),
        ],
    },
    "identify_player_from_clues": {
        "description": "A progressively-revealed sequence of real clues about one real player; the "
                        "player guesses the identity, not a multiple-choice label.",
        "answer_contract": "clues: list[str] revealed one at a time; answer: player display name, "
                            "validated server-side by normalized exact match.",
        "used_by_capabilities": [
            ("identify_player_from_clues", "NFL_PLAYER_IDENTITY", "IDENTIFY_FROM_CLUES"),
        ],
    },
    "connection_path": {
        "description": "Step-by-step path guessing between two real graph nodes (players/teams/coaches) "
                        "via a real shared-team edge at each step. No Director-pipeline capability entry -- "
                        "served directly by gateway/services/public_six_degrees.py.",
        "answer_contract": "step_options: list[node] per step, client submits a chosen index, server "
                            "validates against the precomputed real path.",
        "used_by_capabilities": [],  # not Director-pipeline-generated -- see module docstring
    },
}


def lookup(mechanic_id: str) -> dict | None:
    return MECHANIC_REGISTRY.get(mechanic_id)


def all_mechanic_ids() -> list[str]:
    return list(MECHANIC_REGISTRY.keys())
