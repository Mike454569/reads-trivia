import signal
import time

from gateway.services import public_mechanics


class _LaunchTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _LaunchTimeout()


def test_every_discoverable_public_mechanic_launches_under_budget():
    signal.signal(signal.SIGALRM, _alarm_handler)
    failures = []
    timings = []

    modes = [
        mode for mode, entry in public_mechanics.PUBLIC_MECHANIC_MODES.items()
        if entry.get("discoverable", True)
    ]
    assert modes, "no public mechanic modes were registered"

    for mode in modes:
        started = time.monotonic()
        try:
            signal.setitimer(signal.ITIMER_REAL, 8.0)
            result = public_mechanics.start_public_round(mode=mode)
            elapsed = time.monotonic() - started
            if not result.get("round_id") or not isinstance(result.get("view"), dict):
                failures.append(f"{mode}: invalid first-screen payload")
            timings.append((mode, elapsed, "PASS"))
        except _LaunchTimeout:
            elapsed = time.monotonic() - started
            failures.append(f"{mode}: exceeded 8.0s launch budget")
            timings.append((mode, elapsed, "TIMEOUT"))
        except Exception as exc:
            elapsed = time.monotonic() - started
            failures.append(f"{mode}: {type(exc).__name__}: {exc}")
            timings.append((mode, elapsed, "ERROR"))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    for mode, elapsed, status in sorted(timings, key=lambda row: row[1], reverse=True):
        print(f"LAUNCH {status:7s} {elapsed:7.3f}s {mode}")

    assert not failures, "Public mechanic launch certification failures:\n" + "\n".join(failures)
