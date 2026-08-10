"""Reads Engine Gateway -- graph/Six Degrees service (v0.7 port).

Thin wrapper around Reads_Football_Data_Engine_v4.0/graph_explorer.py --
same "no Director/Game Factory/graph logic lives in gateway/app.py" rule
generation.py already follows (see its own module docstring), just for a
different underlying engine module. graph_explorer.py's search/shortest_path/
random_six are NOT re-implemented here, only called and translated into this
Gateway's request/response and error conventions.

Deliberately NOT registered in tools.director_v02.registry's
CAPABILITY_REGISTRY / exposed via generation.list_capabilities(): that
registry is built around the Director's translate -> validate -> generate
pipeline for quiz-style (mechanic, domain, predicate) capabilities. Graph
search/shortest-path/Six Degrees is direct graph traversal, not that shape,
and forcing it into a (mechanic, domain, predicate) tuple would be a worse
fit than a small parallel service -- see list_graph_capabilities() below for
how these are still made discoverable through GET /v1/capabilities.

Same database file as everything else in the Engine
(Reads_Football_Data_Engine_v4.0/reads_football_v4.0.sqlite) -- so the
existing GET /v1/ready check (tools.quiz_export.engine.check_engine_readiness)
already covers this service's data availability too; no separate readiness
check needed here.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_ROOT / "Reads_Football_Data_Engine_v4.0"
if str(ENGINE_DIR) not in sys.path:
    # graph_explorer.py resolves its own DB path via Path(__file__).with_name(...),
    # so it must be imported from its own directory being on sys.path (not just
    # the repo root generation.py adds) -- this mirrors how a plain
    # `python3 graph_explorer.py` invocation would already work from that dir.
    sys.path.insert(0, str(ENGINE_DIR))

from .. import config  # noqa: E402
from ..errors import GatewayError  # noqa: E402

try:
    import graph_explorer  # noqa: E402
except Exception as e:  # pragma: no cover - exercised only if the engine dir/file is missing
    graph_explorer = None
    _import_error = e
else:
    _import_error = None


def _ensure_engine_importable() -> None:
    if graph_explorer is None:
        raise GatewayError(
            "SERVICE_UNAVAILABLE",
            f"Graph engine module could not be imported: {_import_error}",
        )


# NOTE on node-type validation: deliberately NOT a hardcoded whitelist here.
# An earlier draft of this file guessed at the real set of graph_nodes.node_type
# values instead of querying them, which risked hard-rejecting a real,
# legitimate type this Gateway had never seen tested. graph_explorer.py's own
# queries are already fully parameterized (no injection risk from an unknown
# type string), and passing a nonexistent node_type just yields an honest
# "found: false" / empty result -- the same behavior a search for a real type
# that simply has no match would produce. Basic non-empty/length sanity
# checks below are enough; a real enum can be added later once the actual
# distinct node_type values have been confirmed against the live database
# (see the audit note in READS_ENGINE_GATEWAY_V01_REPORT.md's pattern of
# citing evidence, not assumptions).
MAX_NODE_TYPE_LENGTH = 64
MAX_NODE_ID_LENGTH = 256


def _validate_node_type(field_name: str, value: str) -> None:
    if not value or not value.strip():
        raise GatewayError("INVALID_REQUEST", f"{field_name} must not be empty.")
    if len(value) > MAX_NODE_TYPE_LENGTH:
        raise GatewayError("INVALID_REQUEST", f"{field_name} exceeds {MAX_NODE_TYPE_LENGTH} characters.")


def search(*, query: str, limit: int) -> List[Dict[str, Any]]:
    _ensure_engine_importable()
    q = (query or "").strip()
    if not q:
        raise GatewayError("INVALID_REQUEST", "query must not be empty.")
    if not (1 <= limit <= config.GRAPH_SEARCH_LIMIT_MAX):
        raise GatewayError("INVALID_REQUEST", f"limit must be between 1 and {config.GRAPH_SEARCH_LIMIT_MAX}.")
    try:
        rows = graph_explorer.search(q, limit=limit)
    except Exception as e:
        raise _wrap_engine_error(e)
    return [dict(r) for r in rows]


def shortest_path(*, start_type: str, start_id: str, end_type: str, end_id: str,
                   max_depth: Optional[int]) -> Dict[str, Any]:
    _ensure_engine_importable()
    for field_name, value in (("start_type", start_type), ("end_type", end_type)):
        _validate_node_type(field_name, value)
    if start_id and len(start_id) > MAX_NODE_ID_LENGTH:
        raise GatewayError("INVALID_REQUEST", f"start_id exceeds {MAX_NODE_ID_LENGTH} characters.")
    if end_id and len(end_id) > MAX_NODE_ID_LENGTH:
        raise GatewayError("INVALID_REQUEST", f"end_id exceeds {MAX_NODE_ID_LENGTH} characters.")
    if not start_id or not start_id.strip():
        raise GatewayError("INVALID_REQUEST", "start_id must not be empty.")
    if not end_id or not end_id.strip():
        raise GatewayError("INVALID_REQUEST", "end_id must not be empty.")
    depth = max_depth if max_depth is not None else config.GRAPH_PATH_DEFAULT_MAX_DEPTH
    if not (1 <= depth <= config.GRAPH_PATH_MAX_DEPTH_LIMIT):
        raise GatewayError("INVALID_REQUEST", f"max_depth must be between 1 and {config.GRAPH_PATH_MAX_DEPTH_LIMIT}.")
    try:
        path = graph_explorer.shortest_path(start_type, start_id, end_type, end_id, max_depth=depth)
    except Exception as e:
        raise _wrap_engine_error(e)
    return {
        "start": {"type": start_type, "id": start_id},
        "end": {"type": end_type, "id": end_id},
        "max_depth": depth,
        "found": path is not None,
        "path": path,
        "degrees": len(path) if path is not None else None,
    }


def six_degrees(*, seed: str, min_len: Optional[int], max_len: Optional[int]) -> Dict[str, Any]:
    _ensure_engine_importable()
    s = (seed or "").strip()
    if not s:
        raise GatewayError("INVALID_REQUEST", "seed must not be empty.")
    lo = min_len if min_len is not None else config.SIX_DEGREES_DEFAULT_MIN_LEN
    hi = max_len if max_len is not None else config.SIX_DEGREES_DEFAULT_MAX_LEN
    if not (1 <= lo <= hi <= config.SIX_DEGREES_MAX_LEN_LIMIT):
        raise GatewayError(
            "INVALID_REQUEST",
            f"min_len/max_len must satisfy 1 <= min_len <= max_len <= {config.SIX_DEGREES_MAX_LEN_LIMIT} "
            f"(got min_len={lo}, max_len={hi}).",
        )
    try:
        puzzle = graph_explorer.random_six(seed=s, min_len=lo, max_len=hi)
    except Exception as e:
        raise _wrap_engine_error(e)
    if not puzzle:
        raise GatewayError(
            "GENERATION_FAILED",
            f"No cached Six Degrees puzzle satisfies min_len={lo}/max_len={hi} for seed={s!r} "
            f"(graph_path_cache has a limited, pre-computed set of paths -- not every "
            f"seed/length combination is guaranteed to have one).",
        )
    return puzzle


def _wrap_engine_error(e: Exception) -> GatewayError:
    """Never lets a raw graph_explorer/sqlite3 exception reach the HTTP
    response (Part I, same rule every other route in this Gateway already
    follows) -- the real message still reaches the operator via app.py's
    unhandled_exception_handler-style stderr log at the call site, this just
    gives route handlers one GatewayError type to catch/let propagate."""
    return GatewayError("INTERNAL_ERROR", f"Graph engine error: {e}")


# --- discoverability (spec Part 15, "Mode Registry") ------------------------
# Deliberately NOT merged into generation.list_capabilities()'s return shape
# (that function's entries have mechanic/domain/relationship_predicate/
# difficulty fields that don't mean anything for a graph traversal op) --
# app.py's capabilities() route exposes this as its own top-level key instead,
# so a client that wants "everything this Gateway can do" still only has to
# hit one endpoint.
GRAPH_CAPABILITIES: List[Dict[str, Any]] = [
    {
        "id": "graph_search",
        "route": "GET /v1/graph/search",
        "description": "Entity search over the knowledge graph (players, teams, coaches, etc.) by display name.",
        "requires_admin": True,
    },
    {
        "id": "graph_path",
        "route": "GET /v1/graph/path",
        "description": "Shortest path (BFS, cached where available) between two typed graph nodes.",
        "requires_admin": True,
    },
    {
        "id": "six_degrees",
        "route": "GET /v1/six-degrees",
        "description": "Deterministic Six Degrees puzzle generation from a seed, drawn from the pre-computed path cache.",
        "requires_admin": True,
    },
]


def list_graph_capabilities() -> List[Dict[str, Any]]:
    return list(GRAPH_CAPABILITIES)
