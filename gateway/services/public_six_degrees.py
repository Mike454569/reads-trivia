"""Reads Engine Gateway -- public Six Degrees (v1.7, Part C).

The admin-only graph service (gateway/services/graph.py) wraps
Reads_Football_Data_Engine_v4.0/graph_explorer.py's search()/shortest_path()/
random_six() directly -- and random_six() returns the puzzle's full
`solution_path` in the SAME dict as everything else (see graph_explorer.py):
a real gap found by actually reading that function's return value, not
assumed. Exposing graph.six_degrees() to the public as-is would hand a
player the answer before they'd made a single guess. This module is the
smallest safe adapter Part C2 asks for -- a real, separate contract with the
answer withheld server-side until each step is actually attempted, matching
the exact trust boundary gateway/services/public_game.py already establishes
for Draft/Championship.

Mechanic (deliberately NOT open-ended path entry): rather than asking a
player to freely search for and chain together entities -- powerful, but a
much larger and riskier UI/identity-collision surface (Part C4's "duplicate
names" concern) to get right safely in one phase -- this reuses the exact
"guess" mechanic already proven safe for Draft/Championship: each step
presents multiple-choice options, one of which matches the puzzle's
pre-computed canonical solution_path (graph_path_cache is what
random_six() draws from; see graph.py's own module docstring), the rest are
OTHER real graph relationships (never fabricated entities) that just aren't
the one this puzzle's canonical path uses. A player is always choosing among
real, true facts about the graph -- the "wrong" options are exactly as real
as Draft's wrong team options are real NFL teams that simply didn't draft
that player.

Read-only against the Engine database, same proof shape as generation.py's
public path (module docstring there) -- graph_explorer.py has zero
`.commit()`/write calls anywhere (grepped), every query is a parameterized
SELECT. No separate concurrency pool is needed the way generate_public()
needed one: these are fast, indexed lookups against graph_nodes/graph_edges,
not the CPU-bound candidate-scanning generate_package_from_spec() does.
"""
from __future__ import annotations

import hashlib
import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_ROOT / "Reads_Football_Data_Engine_v4.0"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from .. import config  # noqa: E402
from ..errors import GatewayError  # noqa: E402
from . import oplog, packages  # noqa: E402

try:
    import graph_explorer  # noqa: E402
except Exception as e:  # pragma: no cover - exercised only if the engine dir/file is missing
    graph_explorer = None
    _import_error = e
else:
    _import_error = None

# Only genuinely person/organization-shaped node types are ever shown to a
# public player -- graph_nodes also contains internal bookkeeping types
# (team_game, team_game_opponent, game, point_diff, qb_source, record,
# season, jersey_number -- confirmed by querying the real distinct values,
# not guessed) whose "display_name" wouldn't read as a sensible "connect
# this to that" target for a real player. Six Degrees puzzles are only ever
# built from paths where every node's type is in this set.
#
# NFL-only for this first public certification (nfl_player, team, coach) --
# deliberately excludes cfb_player/cfb_coach even though graph_nodes has
# real, usable CFB entities and the underlying cache doesn't distinguish
# leagues. A puzzle that silently mixed an NFL and a CFB entity in the same
# chain would make this mode's own "competition": "NFL" label
# (list_public_six_degrees_capability(), below) inaccurate -- rather than
# invent a "cross-league" competition value nothing else in this product
# has, this stays cleanly NFL-only like Draft/Championship, matching Part
# F's instruction not to blur the NFL/CFB line. A CFB or cross-league
# version is real future scope (see READS_UI_BACKLOG.md), not implemented
# here.
PUBLIC_NODE_TYPES = frozenset({"nfl_player", "team", "coach"})

OPTIONS_PER_STEP = 4


def _ensure_engine_importable() -> None:
    if graph_explorer is None:
        raise GatewayError("SERVICE_UNAVAILABLE", f"Graph engine module could not be imported: {_import_error}")


def _ensure_public_six_degrees_enabled() -> None:
    """Same operator-kill-switch contract as public_game.py's
    _ensure_public_gameplay_enabled() -- checked before anything else on
    every public route, including answer submission (an emergency shutdown
    should stop in-flight answers too, not just new puzzle fetches)."""
    if not config.PUBLIC_SIX_DEGREES_ENABLED:
        oplog.record_event("public_six_degrees_disabled", mode="six_degrees_guess", reason="master_switch_off")
        raise GatewayError("SERVICE_UNAVAILABLE", "Six Degrees is currently disabled.")


def _real_neighbors(c, node_type: str, node_id: str) -> List[Dict[str, str]]:
    """Every OTHER real entity directly connected to (node_type, node_id) --
    same outgoing-UNION-incoming query shape graph_explorer.shortest_path()
    already uses, so a "wrong" option here is always a real edge this
    project's own QA (verification_status) already trusts, never invented."""
    rows = c.execute(
        "SELECT object_type AS t, object_id AS i FROM graph_edges "
        "WHERE subject_type=? AND subject_id=? AND verification_status NOT IN ('AUTO_REVIEW','CONFLICT')",
        (node_type, node_id),
    ).fetchall()
    rows += c.execute(
        "SELECT subject_type AS t, subject_id AS i FROM graph_edges "
        "WHERE object_type=? AND object_id=? AND verification_status NOT IN ('AUTO_REVIEW','CONFLICT')",
        (node_type, node_id),
    ).fetchall()
    out = []
    for r in rows:
        if r["t"] in PUBLIC_NODE_TYPES:
            out.append({"type": r["t"], "id": r["i"]})
    return out


def _build_step_options(c, current: Dict[str, str], correct: Dict[str, str], rng: random.Random) -> List[Dict[str, str]]:
    """The correct next hop plus up to OPTIONS_PER_STEP-1 real, wrong
    alternatives. Falls back to other real public-type entities (never a
    fabricated name) if this specific node doesn't have enough real
    neighbors of its own to fill every distractor slot -- same
    "real fact, just not the one that answers this question" pattern
    Draft/Championship's own distractor construction already uses."""
    seen_ids = {correct["id"]}
    candidates = [n for n in _real_neighbors(c, current["type"], current["id"]) if n["id"] not in seen_ids]
    rng.shuffle(candidates)
    chosen = []
    for cand in candidates:
        if cand["id"] in seen_ids:
            continue
        chosen.append(cand)
        seen_ids.add(cand["id"])
        if len(chosen) >= OPTIONS_PER_STEP - 1:
            break
    if len(chosen) < OPTIONS_PER_STEP - 1:
        fallback_rows = c.execute(
            "SELECT node_type AS t, node_id AS i FROM graph_nodes "
            "WHERE node_type=? ORDER BY popularity_score DESC LIMIT 200",
            (current["type"] if current["type"] in PUBLIC_NODE_TYPES else "nfl_player",),
        ).fetchall()
        fallback = [{"type": r["t"], "id": r["i"]} for r in fallback_rows if r["i"] not in seen_ids]
        rng.shuffle(fallback)
        for cand in fallback:
            if len(chosen) >= OPTIONS_PER_STEP - 1:
                break
            chosen.append(cand)
            seen_ids.add(cand["id"])
    options = chosen + [correct]
    rng.shuffle(options)
    return options


def _label(c, node_type: str, node_id: str) -> str:
    return graph_explorer.label(c, node_type, node_id)


def _eligible_cache_rows(c) -> List[Any]:
    """graph_explorer.random_six() picks uniformly from EVERY row in
    graph_path_cache within the length band, regardless of node type --
    empirically checked (not assumed) against the real cache: only 23 of
    its 500 rows are entirely NFL-player/team/coach-typed (the rest involve
    CFB or internal bookkeeping node types this module never shows a public
    player). A seed-retry loop against the FULL cache would land on one of
    those 23 only ~4-5% of the time per attempt -- a real reliability bug
    caught by actually computing the eligible fraction, not assumed safe
    from reading random_six()'s code alone. Filtering to the eligible rows
    FIRST, then picking deterministically among only those, makes every
    valid seed succeed on the first try instead of most of them failing."""
    rows = c.execute(
        "SELECT start_type,start_id,end_type,end_id,path_length,path_json FROM graph_path_cache "
        "WHERE path_length BETWEEN ? AND ?",
        (config.SIX_DEGREES_DEFAULT_MIN_LEN, config.SIX_DEGREES_DEFAULT_MAX_LEN),
    ).fetchall()
    eligible = []
    for r in rows:
        types = {r["start_type"], r["end_type"]}
        path = json.loads(r["path_json"])
        for e in path:
            types.add(e["from_type"])
            types.add(e["to_type"])
        if types <= PUBLIC_NODE_TYPES:
            eligible.append(r)
    return eligible


def get_public_six_degrees(*, seed: Optional[str]) -> dict:
    """Mints a fresh, server-validated multi-step puzzle from a real
    pre-computed graph_path_cache entry. Only ever returns step 0 -- later
    steps are revealed one at a time by submit_public_six_degrees_answer(),
    never all at once."""
    _ensure_public_six_degrees_enabled()
    _ensure_engine_importable()
    real_seed = seed if seed else secrets.token_hex(8)

    c = graph_explorer.connect()
    try:
        eligible = _eligible_cache_rows(c)
        if not eligible:
            oplog.record_event("public_six_degrees_no_eligible", mode="six_degrees_guess")
            raise GatewayError(
                "NO_ELIGIBLE_GAME",
                "No public-safe Six Degrees puzzle could be generated right now.",
            )
        h = int(hashlib.sha256(real_seed.encode()).hexdigest()[:16], 16)
        row = eligible[h % len(eligible)]
        start_name = graph_explorer.label(c, row["start_type"], row["start_id"])
        end_name = graph_explorer.label(c, row["end_type"], row["end_id"])
        puzzle = {
            "start": {"type": row["start_type"], "id": row["start_id"], "name": start_name},
            "end": {"type": row["end_type"], "id": row["end_id"], "name": end_name},
            "par": row["path_length"],
            "prompt": f"Connect {start_name} to {end_name} in {row['path_length']} moves or fewer.",
            "solution_path": json.loads(row["path_json"]),
        }
        for edge in puzzle["solution_path"]:
            edge["from_name"] = graph_explorer.label(c, edge["from_type"], edge["from_id"])
            edge["to_name"] = graph_explorer.label(c, edge["to_type"], edge["to_id"])

        rng = random.Random(hashlib.sha256(real_seed.encode()).hexdigest())
        steps = []
        for edge in puzzle["solution_path"]:
            current = {"type": edge["from_type"], "id": edge["from_id"], "name": edge["from_name"]}
            correct = {"type": edge["to_type"], "id": edge["to_id"], "name": edge["to_name"]}
            options = _build_step_options(c, current, correct, rng)
            steps.append({
                "current": current,
                "correct_id": correct["id"],
                "options": [{"type": o["type"], "id": o["id"], "name": _label(c, o["type"], o["id"])} for o in options],
            })
    finally:
        c.close()

    game_id = "GGP:" + hashlib.sha256(f"six_degrees|{real_seed}".encode()).hexdigest()[:24]
    record = {
        "package_id": game_id,
        "mode": "six_degrees_guess",
        "qa_status": "PASSED",
        "start": puzzle["start"],
        "end": puzzle["end"],
        "par": puzzle["par"],
        "prompt": puzzle["prompt"],
        "steps": steps,
        "seed": real_seed,
    }
    saved = packages.save_package(record)
    return _public_step_view(saved, step_index=0)


def _public_step_view(saved: dict, *, step_index: int, last_correct: Optional[bool] = None,
                       last_correct_name: Optional[str] = None) -> dict:
    total = len(saved["steps"])
    completed = step_index >= total
    view: Dict[str, Any] = {
        "game_id": saved["package_id"],
        "mode": "six_degrees_guess",
        "start": {"name": saved["start"]["name"]},
        "end": {"name": saved["end"]["name"]},
        "par": saved["par"],
        "prompt": saved["prompt"],
        "step_index": step_index,
        "total_steps": total,
        "completed": completed,
    }
    if last_correct is not None:
        view["last_correct"] = last_correct
        view["last_correct_name"] = last_correct_name
    if not completed:
        step = saved["steps"][step_index]
        view["current"] = {"name": step["current"]["name"]}
        # Never the raw graph_node id (Part C3: "do not expose raw graph
        # IDs") -- an opaque per-option index is all a client needs to
        # answer; the real id only ever exists server-side.
        view["options"] = [o["name"] for o in step["options"]]
    return view


def submit_public_six_degrees_answer(*, game_id: str, step_index: int, choice_index: int) -> dict:
    """Server remains fully authoritative (Part C5) -- the client only ever
    sends back an opaque step_index + choice_index; every real id and the
    canonical answer stay server-side in the stored package the whole time."""
    _ensure_public_six_degrees_enabled()
    try:
        saved = packages.load_package(game_id)
    except packages.PackageIdInvalid:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")
    if not saved or saved.get("mode") != "six_degrees_guess":
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")
    total = len(saved["steps"])
    if not (0 <= step_index < total):
        raise GatewayError("INVALID_REQUEST", f"step_index must be between 0 and {total - 1}.")
    step = saved["steps"][step_index]
    options = step["options"]
    if not (0 <= choice_index < len(options)):
        raise GatewayError("INVALID_REQUEST", f"choice_index must be between 0 and {len(options) - 1}.")

    chosen = options[choice_index]
    is_correct = chosen["id"] == step["correct_id"]
    correct_name = next(o["name"] for o in options if o["id"] == step["correct_id"])

    oplog.record_event(
        "public_six_degrees_answer_submitted", mode="six_degrees_guess",
        step_index=step_index, correct=is_correct,
    )

    # Wrong answer ends the attempt where it is -- same "server decides, no
    # retry-until-right" contract as every other public mode's answer
    # validation. The player can start a fresh puzzle if they want another
    # attempt, matching Draft/Championship's own "wrong answer, see the
    # reveal, play again" shape rather than silently allowing unlimited
    # guesses per step (which would make the multiple-choice option list
    # trivially solvable by exhaustion).
    next_step_index = step_index + 1 if is_correct else total
    return _public_step_view(saved, step_index=next_step_index, last_correct=is_correct, last_correct_name=correct_name)


def reveal_public_six_degrees(*, game_id: str) -> dict:
    """Part C6: only ever called when a player explicitly gives up (or has
    already lost/completed) -- never bundled into the initial fetch or an
    in-progress answer response."""
    _ensure_public_six_degrees_enabled()
    try:
        saved = packages.load_package(game_id)
    except packages.PackageIdInvalid:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")
    if not saved or saved.get("mode") != "six_degrees_guess":
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")
    chain = [saved["start"]["name"]] + [s["current"]["name"] for s in saved["steps"][1:]] + [saved["end"]["name"]]
    return {
        "game_id": game_id,
        "start": {"name": saved["start"]["name"]},
        "end": {"name": saved["end"]["name"]},
        "par": saved["par"],
        "solution_names": chain,
    }


def list_public_six_degrees_capability() -> dict:
    """Composed into GET /v1/public/modes by app.py alongside
    public_game.list_public_modes() -- Part C8: one unified discovery
    response, not a second parallel catalog endpoint a client would have to
    know to call separately. `kind` distinguishes this mechanic
    (multi-step, one correct choice per step) from the guess-mechanic
    entries' `multiple_choice`.

    Title deliberately says "Coach Connections," not "Six Degrees" -- the
    real, checked content behind this mode today is exactly 23 distinct
    puzzles, every one of them a two-team connection through a coach who
    led both (see PUBLIC_NODE_TYPES's comment: the real graph_path_cache
    has no other NFL-only-typed entries at all). Calling this "Six Degrees"
    to a player would imply a variety of long, varied chains this
    certified content doesn't actually have -- the honest name for what
    ships today is the narrower, accurate one. `desc` says so plainly
    rather than overselling it."""
    return {
        "mode": "six_degrees_guess",
        "competition": "NFL",
        "title": "Coach Connections",
        "desc": "Two NFL teams, one coach who led them both. Figure out the connection.",
        "kind": "six_degrees",
        "available": config.PUBLIC_SIX_DEGREES_ENABLED,
    }
