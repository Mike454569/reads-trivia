"""Reads Engine Gateway -- request/response models (Part G: strict input
validation at the HTTP boundary, in front of -- not instead of --
tools/director_v02/validator.py's own independent checks).

Every request model uses `extra="forbid"` -- an unrecognized field is a
400, not a silently-ignored field. This is deliberate defense-in-depth: the
Director validator already rejects unknown DirectorSpec fields, but a
Gateway-level field (e.g. an attempted `sql`/`table`/`path` key on the
outer request body, not inside `spec`) never even reaches that layer if
Pydantic rejects it first.

Uses `typing.Optional`/`Union` rather than the `X | None` syntax --
this project's Python (3.9) can only evaluate that PEP 604 syntax at
runtime with an extra `eval_type_backport` dependency; `Optional` needs
nothing extra and keeps Part B's "keep dependencies minimal" intact.
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import config


class GameRequestBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_text: Optional[str] = Field(default=None, max_length=config.MAX_REQUEST_TEXT_CHARS)
    spec: Optional[Dict[str, Any]] = None
    provider: Literal["mock", "anthropic"] = "mock"

    @model_validator(mode="after")
    def _exactly_one_of_request_text_or_spec(self) -> "GameRequestBase":
        has_text = bool(self.request_text and self.request_text.strip())
        has_spec = self.spec is not None
        if has_text == has_spec:  # both or neither
            raise ValueError("provide exactly one of request_text or spec, not both/neither")
        return self


class PreviewRequest(GameRequestBase):
    """POST /v1/games/preview -- never generates anything."""
    pass


class GenerateRequest(GameRequestBase):
    """POST /v1/games/generate. Only the fields explicitly named in Part D
    are accepted -- puzzle_count/difficulty/seed -- nothing resembling a
    table name, adapter name, file path, or raw execution parameter."""
    puzzle_count: Optional[int] = Field(default=None, ge=1, le=config.MAX_PUZZLE_COUNT)
    difficulty: Optional[Literal["any", "easy", "medium", "hard"]] = None
    seed: Optional[str] = Field(default=None, min_length=1, max_length=128)


class GridBoardRequest(BaseModel):
    """POST /v1/grid/board -- v0.7 Grid roster-merge port. Mirrors
    buildGridAttempt()'s 3-row/3-col shape (app.js:2527) exactly; season is
    optional (data/grid.js's own criteria are season-agnostic 'ever played
    for' checks -- see gateway/services/grid.py's module docstring)."""
    model_config = ConfigDict(extra="forbid")

    row_ids: List[str] = Field(min_length=3, max_length=3)
    col_ids: List[str] = Field(min_length=3, max_length=3)
    season: Optional[int] = Field(default=None, ge=1920, le=2100)


class GridValidateRequest(BaseModel):
    """POST /v1/grid/validate. player_name is free text (unchanged frontend
    input shape) -- resolved to a canonical node_id server-side, never
    trusted as an identity by itself. See validate_answer()'s docstring."""
    model_config = ConfigDict(extra="forbid")

    row_id: str = Field(min_length=1, max_length=64)
    col_id: str = Field(min_length=1, max_length=64)
    player_name: str = Field(min_length=1, max_length=200)
    season: Optional[int] = Field(default=None, ge=1920, le=2100)


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody
