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


class PublicAnswerRequest(BaseModel):
    """POST /v1/public/game/answer (v1.2). game_id is the opaque package_id
    the matching GET /v1/public/game response returned -- see
    gateway/services/public_game.py's docstring for why reusing the
    existing content-addressed package_id scheme (rather than inventing a
    new session token) is enough to make guessing a valid, unissued game_id
    impractical without new cryptography. answer is free text (matches the
    existing Reads Quiz UX -- a picked option's label), resolved against the
    stored package's real answer server-side, never trusted from the client."""
    model_config = ConfigDict(extra="forbid")

    game_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(min_length=1, max_length=200)


class PublicSixDegreesAnswerRequest(BaseModel):
    """POST /v1/public/six_degrees/answer (v1.7). game_id is the same opaque
    package_id scheme PublicAnswerRequest already uses. step_index/choice_index
    are plain small integers (an index into the CURRENT step's options list,
    never a raw graph node id -- see gateway/services/public_six_degrees.py's
    docstring) -- the server looks up what they actually mean against the
    stored puzzle, never trusting either value's meaning from the client."""
    model_config = ConfigDict(extra="forbid")

    game_id: str = Field(min_length=1, max_length=64)
    step_index: int = Field(ge=0, le=20)
    choice_index: int = Field(ge=0, le=20)


class PublicSixDegreesRevealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game_id: str = Field(min_length=1, max_length=64)


class PublicCoachConnectionsMoveRequest(BaseModel):
    """POST /v1/public/coach_connections/move -- unlike Six Degrees v1's
    step_index/choice_index (an index into a small server-fixed option
    list), this mode's move is free-text: node_type/node_id identify a real
    graph node the player found via /v1/public/coach_connections/search.
    Still never trusted as "correct" here -- gateway/services/
    public_coach_connections.py.submit_move() validates it against the live
    graph (coach_connections_graph.is_legal_move) before accepting it, and
    against server-held progress state (game_state.py), never a
    client-supplied "current position"."""
    model_config = ConfigDict(extra="forbid")

    game_id: str = Field(min_length=1, max_length=64)
    node_type: str = Field(min_length=1, max_length=32)
    node_id: str = Field(min_length=1, max_length=128)


class PublicCoachConnectionsRevealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game_id: str = Field(min_length=1, max_length=64)


class CreatorJobTier2CertificationRequest(BaseModel):
    """POST /v1/admin/creator-jobs/tier2-certification (Phase 2). Admin-only
    (require_admin, same as every other /v1/admin/* route). capability_ids
    is an explicit allow-list, never "all registered capabilities" implied
    by an empty/missing field -- a caller must name what it wants certified,
    matching this whole design's "never silently do more than asked" rule."""
    model_config = ConfigDict(extra="forbid")

    capability_ids: list[str] = Field(min_length=1, max_length=100)


class CreatorFeasibilityRequest(BaseModel):
    """POST /v1/creator/feasibility (v1.8, Part B/C). request_text-only --
    unlike GameRequestBase, the Creator never accepts a raw `spec` dict from
    the browser (Part L/M: the Creator's only input surface is natural-
    language text funneled through the same translator every other request
    already goes through, never a structured spec a client could hand-craft
    to try to reach an unregistered/internal capability triple directly)."""
    model_config = ConfigDict(extra="forbid")

    request_text: str = Field(min_length=1, max_length=config.MAX_REQUEST_TEXT_CHARS)


class CreatorIdeasRequest(BaseModel):
    """POST /v1/creator/ideas (Phase 5, Creator Intelligence). Same
    request_text-only restriction as CreatorFeasibilityRequest -- ideas are
    retrieved purely from tools.director_v02.creator_intelligence.py's real,
    registry-derived matching, never from a client-supplied spec."""
    model_config = ConfigDict(extra="forbid")

    request_text: str = Field(min_length=1, max_length=config.MAX_REQUEST_TEXT_CHARS)
    max_ideas: Optional[int] = Field(default=10, ge=1, le=25)


class CreatorConceptsRequest(BaseModel):
    """POST /v1/creator/concepts (Phase 5 correction). Builds real,
    packaged CONCEPTS (mechanic + round structure + scoring + ...) on top
    of CreatorIdeasRequest's retrieval, via tools.director_v02.concepts.py.
    Same request_text-only restriction -- never a client-supplied spec."""
    model_config = ConfigDict(extra="forbid")

    request_text: str = Field(min_length=1, max_length=config.MAX_REQUEST_TEXT_CHARS)
    request_type: Literal["IDEAS", "PLAYABLE_IDEAS", "MIXED"] = "IDEAS"
    requested_count: int = Field(default=10, ge=1, le=25)
    exclude_concept_ids: Optional[List[str]] = Field(default=None, max_length=200)


class MechanicRoundRequest(BaseModel):
    """POST /v1/creator/mechanics/round (Phase 6, common mechanic execution
    contract). Generates one real PRIVATE round/contest via
    tools.director_v02.mechanic_engine.py -- the caller names a taxonomy_id
    and the real knobs that taxonomy needs; unused knobs for a given
    taxonomy_id are simply ignored by the route handler, never silently
    reinterpreted. Never accepts an answer key, a private value, or any
    other server-only field -- only generation PARAMETERS."""
    model_config = ConfigDict(extra="forbid")

    taxonomy_id: Literal[
        "MULTIPLE_CHOICE_SINGLE_FACT", "PROGRESSIVE_CLUE_IDENTIFY", "MATCHING",
        "SORTING_TIMELINE", "HIGHER_LOWER_STREAK", "ELIMINATION_SURVIVAL", "POSITION_LINEUP_GRID",
    ]
    variant: Optional[str] = Field(default=None, max_length=64)
    domain: Optional[str] = Field(default=None, max_length=64)
    relationship_predicate: Optional[str] = Field(default=None, max_length=64)
    round_count: Optional[int] = Field(default=None, ge=1, le=25)
    pair_count: Optional[int] = Field(default=None, ge=4, le=6)
    item_count: Optional[int] = Field(default=None, ge=4, le=6)
    sequence_length: Optional[int] = Field(default=None, ge=8, le=25)
    question_count: Optional[int] = Field(default=None, ge=1, le=25)
    seed: Optional[str] = Field(default=None, min_length=1, max_length=128)


class MechanicSubmitRequest(BaseModel):
    """POST /v1/creator/mechanics/round/{round_id}/submit. `submission`'s
    exact shape is mechanic-specific (answer/mapping/order/guess/
    guess_name/action) -- validated by tools.director_v02.mechanic_engine.
    evaluate_submission() against the real stored round, never trusted as
    truth by this model. Bounded size (Part F's MAX_BODY_BYTES middleware
    already caps the whole request; this field-level cap is defense in
    depth against a pathologically large single field)."""
    model_config = ConfigDict(extra="forbid")

    submission: Dict[str, Any] = Field(default_factory=dict)


class CreatorGenerateRequest(BaseModel):
    """POST /v1/creator/generate -- same request_text-only restriction as
    CreatorFeasibilityRequest, plus the same puzzle_count/difficulty/seed
    knobs GenerateRequest already exposes (still capability-bounds-checked
    by the same validator, never a new trust surface)."""
    model_config = ConfigDict(extra="forbid")

    request_text: str = Field(min_length=1, max_length=config.MAX_REQUEST_TEXT_CHARS)
    puzzle_count: Optional[int] = Field(default=None, ge=1, le=config.MAX_PUZZLE_COUNT)
    difficulty: Optional[Literal["any", "easy", "medium", "hard"]] = None
    seed: Optional[str] = Field(default=None, min_length=1, max_length=128)


class CreatorReviewRequest(BaseModel):
    """POST /v1/creator/review -- the approve/reject step (Part G/H). Only
    the three human-set review statuses are ever accepted here -- GENERATED
    is set exclusively by generation itself (packages.save_package), never
    by this route."""
    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(min_length=1, max_length=64)
    review_status: Literal["REVIEWED", "APPROVED", "REJECTED"]


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody
