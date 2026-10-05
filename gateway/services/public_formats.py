"""Unified public format facade for Reads gameplay.

The browser should not need to know whether a certified format is backed by
public_game (single-question Director packages) or public_mechanics (stateful
mechanic_engine rounds). This module is the one compatibility boundary between
those two proven backends.

It deliberately does NOT reimplement generation or grading. It resolves a
public mode id against the existing certified registries, delegates to the
existing service, and normalizes the response shape. That keeps every existing
safety/QA gate authoritative while giving the frontend one launch and one
submit contract.
"""
from __future__ import annotations

from typing import Any, Optional

from ..errors import GatewayError
from . import game_state, public_game, public_mechanics


def list_public_formats() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in public_game.list_public_modes():
        rows.append({
            "mode": row["mode"],
            "competition": row.get("competition"),
            "title": row.get("title"),
            "instructions": row.get("instructions"),
            "kind": row.get("kind") or "multiple_choice",
            "engine_kind": "question",
            "available": row.get("available", True),
        })
    for row in public_mechanics.list_public_mechanic_modes():
        rows.append({
            "mode": row["mode"],
            "competition": row.get("competition"),
            "title": row.get("title"),
            "instructions": row.get("instructions"),
            "kind": row.get("kind"),
            "engine_kind": "mechanic",
            "available": row.get("available", True),
        })
    return rows


def _normalize_question_round(payload: dict[str, Any]) -> dict[str, Any]:
    p = payload["payload"]
    return {
        "round_id": payload["game_id"],
        "mode": payload["mode"],
        "engine_kind": "question",
        "kind": "multiple_choice",
        "title": payload["title"],
        "instructions": payload["instructions"],
        "competition": payload.get("competition"),
        "view": {
            "prompt": p["prompt"],
            "options": list(p["options"]),
            "visual_template": p.get("visual_template"),
            "visual_payload": p.get("visual_payload"),
            "difficulty": payload.get("difficulty"),
            "completed": False,
        },
        "metadata": payload.get("metadata") or {},
    }


def _normalize_mechanic_round(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "round_id": payload["round_id"],
        "mode": payload["mode"],
        "engine_kind": "mechanic",
        "kind": payload["kind"],
        "title": payload["title"],
        "instructions": payload["instructions"],
        "view": payload["view"],
        "metadata": payload.get("metadata") or {},
    }


def start_public_format(
    *,
    mode: str,
    difficulty: Optional[str] = None,
    seed: Optional[str] = None,
    exclude_game_ids: Optional[list[str]] = None,
    stage_index: Optional[int] = None,
    filter_value: Optional[str] = None,
    client_id: Optional[str] = None,
) -> dict[str, Any]:
    if mode in public_mechanics.PUBLIC_MECHANIC_MODES:
        if any(v is not None for v in (difficulty, seed, stage_index, filter_value, client_id)) or exclude_game_ids:
            # Mechanic generators intentionally own their server-selected
            # parameters. Reject irrelevant knobs instead of pretending they
            # influence a mechanic round.
            raise GatewayError("INVALID_REQUEST", f"mode={mode!r} does not accept question-mode launch parameters.")
        return _normalize_mechanic_round(public_mechanics.start_public_round(mode=mode))

    if mode in public_game.PUBLIC_MODES:
        return _normalize_question_round(public_game.get_public_game(
            mode=mode,
            difficulty=difficulty,
            seed=seed,
            exclude_game_ids=exclude_game_ids,
            stage_index=stage_index,
            filter_value=filter_value,
            client_id=client_id,
        ))

    raise GatewayError("INVALID_MODE", f"mode={mode!r} is not a recognized public format.")


def submit_public_format(*, round_id: str, submission: dict[str, Any]) -> dict[str, Any]:
    """Grade one unified public round.

    Mechanic rounds already have authoritative mutable state containing the
    public_mode marker. Question rounds intentionally do not. That lets the
    facade route by server-owned state instead of trusting a client-provided
    backend/type discriminator.
    """
    try:
        progress = game_state.load_state(round_id)
    except game_state.StateIdInvalid:
        progress = None

    if progress is not None and "public_mode" in progress:
        payload = public_mechanics.submit_public_round(round_id=round_id, submission=submission)
        return {
            "round_id": round_id,
            "mode": payload["mode"],
            "engine_kind": "mechanic",
            "result": payload["result"],
            "view": payload["view"],
        }

    answer = submission.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise GatewayError(
            "INVALID_REQUEST",
            "This question round requires submission.answer as a non-empty string.",
        )
    result = public_game.validate_public_answer(game_id=round_id, answer=answer)
    return {
        "round_id": round_id,
        "engine_kind": "question",
        "result": result,
    }
