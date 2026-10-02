"""Authoritative 100-format production launch matrix.

A format is not considered playable merely because it exists in
VISUAL_TEMPLATE_REGISTRY. Every distinct format must resolve to:
  * a real player-facing launch target (public mechanic, public game, or
    legacy client route), and
  * a UI/presentation proof token that exists in the shipped frontend.

Runtime certification launches every unique server target against the real
production-sized DB fork; presentation aliases do not count as distinct.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools.director_v02.visual_templates import VISUAL_TEMPLATE_REGISTRY

ROOT = Path(__file__).resolve().parents[2]

# Three registry entries predate the current public-mode naming and therefore
# cannot be inferred mechanically from proven_in.
FORMAT_LAUNCH_OVERRIDES: dict[str, tuple[str, str]] = {
    "POSITION_LINEUP": ("public_game", "lineup_guess"),
    "POSITION_LINEUP_COLLEGE": ("public_game", "lineup_college_guess"),
    # HEAD_TO_HEAD is the generic two-card presentation for a 2-option guess.
    # NFL game-result questions are a real public two-team choice and exercise
    # the same public guess + binary-card path.
    "HEAD_TO_HEAD": ("public_game", "nfl_game_result_guess"),
}

# Formats whose proof is an old client-only route rather than a Gateway call.
CLIENT_ROUTE_OVERRIDES: dict[str, str] = {
    "GUESS_LADDER": "higherLower",
    "GRID_BOARD": "grid",
    "CARD_STACK": "playerClues",
}

# Presentation-specific UI probes for formats that intentionally share one
# backend with another format.
UI_PROBE_OVERRIDES: dict[str, tuple[str, str]] = {
    "DEFAULT_MULTIPLE_CHOICE": ("engine-game-ui.js", "renderEnginePilotPromptHtml"),
    "TIMELINE_RIBBON": ("engine-game-ui.js", "TIMELINE_RIBBON"),
    "HEAD_TO_HEAD": ("engine-game-ui.js", "renderBinaryChoiceHtml"),
    "POSITION_LINEUP": ("engine-game-ui.js", "renderPositionLineup"),
    "POSITION_LINEUP_COLLEGE": ("engine-game-ui.js", "renderPositionLineupCollegeBoard"),
    "GUESS_LADDER": ("app.js", "higherLower"),
    "GRID_BOARD": ("app.js", "renderGridBoard"),
    "CARD_STACK": ("app.js", "playerClues"),
}

def _frontend_sources() -> dict[str, str]:
    return {
        "app.js": (ROOT / "app.js").read_text(encoding="utf-8"),
        "engine-game-ui.js": (ROOT / "engine-game-ui.js").read_text(encoding="utf-8"),
        "reads-config.js": (ROOT / "reads-config.js").read_text(encoding="utf-8"),
    }

def _public_mode_maps():
    from gateway.services.public_game import PUBLIC_MODES
    from gateway.services.public_mechanics import PUBLIC_MECHANIC_MODES

    mechanic_by_variant = {}
    for mode_id, entry in PUBLIC_MECHANIC_MODES.items():
        if entry.get("discoverable", True) is True:
            mechanic_by_variant.setdefault(str(entry.get("variant")), mode_id)
    return PUBLIC_MODES, PUBLIC_MECHANIC_MODES, mechanic_by_variant

def _renderer_probe(entry: dict[str, Any]) -> tuple[str, str] | None:
    renderer = entry.get("renderer")
    if renderer:
        # First JS-ish identifier is sufficient to prove the shipped function/
        # branch exists; line numbers/comments are deliberately ignored.
        m = re.search(r"([A-Za-z_$][A-Za-z0-9_$]*)", str(renderer))
        if m:
            return ("engine-game-ui.js", m.group(1))
    family = str(entry.get("mechanic_family") or "")
    generic = {
        "sorting": ("engine-game-ui.js", "renderMechanicPilotBody"),
        "matching": ("engine-game-ui.js", "renderMechanicPilotBody"),
        "higher_lower": ("engine-game-ui.js", "renderMechanicPilotBody"),
        "elimination": ("engine-game-ui.js", "renderMechanicPilotBody"),
        "guess": ("engine-game-ui.js", "renderEnginePilotPromptHtml"),
        "client_higher_lower": ("app.js", "higherLower"),
        "grid_matching": ("app.js", "renderGridBoard"),
        "identify_player_from_clues": ("app.js", "playerClues"),
    }
    if family in generic:
        return generic[family]
    # Modern named mechanic formats all render through the shared mechanic
    # shell. Strategy Arcade has one shared body; named v04 mechanics dispatch
    # through renderMechanicPilotBody.
    if family:
        if entry.get("renderer"):
            return _renderer_probe(entry)
        return ("engine-game-ui.js", "renderMechanicPilotBody")
    return None

def build_format_launch_matrix() -> list[dict[str, Any]]:
    public_games, public_mechanics, mechanic_by_variant = _public_mode_maps()
    rows = []

    for format_id, entry in VISUAL_TEMPLATE_REGISTRY.items():
        if entry.get("presentation_alias_of"):
            continue

        target = FORMAT_LAUNCH_OVERRIDES.get(format_id)
        proven = list(entry.get("proven_in") or [])

        if target is None and format_id in CLIENT_ROUTE_OVERRIDES:
            target = ("client", CLIENT_ROUTE_OVERRIDES[format_id])

        if target is None:
            for token in proven:
                if token in public_mechanics and public_mechanics[token].get("discoverable", True) is True:
                    target = ("mechanic", token)
                    break
                if token in public_games:
                    target = ("public_game", token)
                    break

        if target is None:
            for token in proven:
                if token in mechanic_by_variant:
                    target = ("mechanic", mechanic_by_variant[token])
                    break

        # Strategy Arcade and other newer formats use their format id itself
        # as the backend variant rather than repeating every mode id in
        # proven_in.
        if target is None and format_id in mechanic_by_variant:
            target = ("mechanic", mechanic_by_variant[format_id])

        # Last-resort legacy client proof from proven_in's first identifier.
        if target is None:
            app = (ROOT / "app.js").read_text(encoding="utf-8")
            for token in proven:
                m = re.match(r"([A-Za-z0-9_]+)", token)
                if m and re.search(r"\bid\s*:\s*['\"]" + re.escape(m.group(1)) + r"['\"]", app):
                    target = ("client", m.group(1))
                    break

        probe = UI_PROBE_OVERRIDES.get(format_id) or _renderer_probe(entry)

        rows.append({
            "format_id": format_id,
            "display_name": entry.get("display_name"),
            "production_status": entry.get("production_status"),
            "mobile_verified": entry.get("mobile_verified") is True,
            "target_type": target[0] if target else None,
            "target_id": target[1] if target else None,
            "ui_file": probe[0] if probe else None,
            "ui_probe": probe[1] if probe else None,
        })
    return rows

def validate_format_launch_matrix() -> dict[str, Any]:
    rows = build_format_launch_matrix()
    sources = _frontend_sources()

    unresolved = [r["format_id"] for r in rows if not r["target_type"] or not r["target_id"]]
    missing_ui = []
    for row in rows:
        f, token = row["ui_file"], row["ui_probe"]
        if not f or not token or token not in sources.get(f, ""):
            missing_ui.append(row["format_id"])

    non_mobile = [r["format_id"] for r in rows if not r["mobile_verified"]]

    return {
        "distinct_format_count": len(rows),
        "resolved_launch_count": len(rows) - len(unresolved),
        "ui_proven_count": len(rows) - len(missing_ui),
        "unresolved": unresolved,
        "missing_ui_proof": missing_ui,
        "mobile_unverified": non_mobile,
        "rows": rows,
    }

def unique_server_targets() -> list[tuple[str, str]]:
    seen = set()
    out = []
    for row in build_format_launch_matrix():
        pair = (row["target_type"], row["target_id"])
        if pair[0] not in {"mechanic", "public_game"} or pair in seen:
            continue
        seen.add(pair)
        out.append(pair)
    return out
