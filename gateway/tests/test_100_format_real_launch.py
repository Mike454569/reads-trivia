import signal
import time

from gateway.services import public_game, public_mechanics
from tools.director_v02.format_launch_matrix import (
    validate_format_launch_matrix,
    unique_server_targets,
)


class _LaunchTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _LaunchTimeout()


def _enable_public_services_for_isolated_certification(monkeypatch):
    monkeypatch.setattr(public_game.config, "PUBLIC_GAME_ENABLED", True)
    monkeypatch.setattr(public_mechanics.config, "PUBLIC_GAME_ENABLED", True)
    monkeypatch.setattr(
        public_game.config,
        "public_modes_allowed",
        lambda: set(public_game.PUBLIC_MODES),
    )


def test_all_100_formats_are_mapped_before_real_launch():
    result = validate_format_launch_matrix()
    assert result["distinct_format_count"] == 100
    assert result["resolved_launch_count"] == 100, result["unresolved"]
    assert result["ui_proven_count"] == 100, result["missing_ui_proof"]
    assert result["mobile_unverified"] == []


def test_every_unique_server_target_used_by_100_formats_launches_on_real_db(monkeypatch):
    _enable_public_services_for_isolated_certification(monkeypatch)
    signal.signal(signal.SIGALRM, _alarm_handler)

    failures = []
    timings = []
    targets = unique_server_targets()
    assert targets, "100-format matrix resolved no server launch targets"

    for target_type, target_id in targets:
        started = time.monotonic()
        try:
            signal.setitimer(signal.ITIMER_REAL, 8.0)
            if target_type == "mechanic":
                payload = public_mechanics.start_public_round(mode=target_id)
                valid = bool(payload.get("round_id")) and isinstance(payload.get("view"), dict)
            elif target_type == "public_game":
                payload = public_game.get_public_game(
                    mode=target_id,
                    difficulty="any",
                    seed=f"100-format-cert-{target_id}",
                    exclude_game_ids=[],
                    client_id="100-format-cert",
                )
                public_payload = payload.get("payload") or {}
                valid = (
                    bool(payload.get("game_id"))
                    and bool(public_payload.get("prompt"))
                    and bool(public_payload.get("options"))
                )
            else:
                raise AssertionError(f"unexpected server target type {target_type!r}")

            elapsed = time.monotonic() - started
            if not valid:
                failures.append(f"{target_type}:{target_id}: invalid playable payload")
            status = "PASS" if valid else "INVALID"
            timings.append((elapsed, target_type, target_id, status))
            print(f"FORMAT-LAUNCH {status:7s} {elapsed:7.3f}s {target_type}:{target_id}", flush=True)
        except _LaunchTimeout:
            elapsed = time.monotonic() - started
            failures.append(f"{target_type}:{target_id}: exceeded 8.0s launch budget")
            timings.append((elapsed, target_type, target_id, "TIMEOUT"))
            print(f"FORMAT-LAUNCH TIMEOUT {elapsed:7.3f}s {target_type}:{target_id}", flush=True)
        except Exception as exc:
            elapsed = time.monotonic() - started
            failures.append(f"{target_type}:{target_id}: {type(exc).__name__}: {exc}")
            timings.append((elapsed, target_type, target_id, "ERROR"))
            print(f"FORMAT-LAUNCH ERROR   {elapsed:7.3f}s {target_type}:{target_id} :: {type(exc).__name__}: {exc}", flush=True)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    print(f"100-FORMAT SERVER TARGETS: {len(targets)}", flush=True)

    assert not failures, "100-format real launch failures:\n" + "\n".join(failures)
