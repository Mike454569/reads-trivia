"""Run both Story Factory production certifications and persist results.

Designed for detached execution on the Fly production machine so certification
is not coupled to a long-lived SSH session. Reads the configured Engine DB;
does not mutate the Story Factory corpus or deploy application code.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import traceback
import datetime as dt

from .certify_story_question_quality import certify_story_question_quality
from .certify_story_game_reach import certify_story_game_reach


def _write_json(path: pathlib.Path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _status(path: pathlib.Path, value: str):
    path.write_text(value + "\n", encoding="utf-8")


def run(out_dir: str):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    status_path = out / "status.txt"
    _status(status_path, "RUNNING")

    meta = {
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "question_quality": None,
        "game_reach": None,
        "errors": [],
    }
    _write_json(out / "meta.json", meta)

    try:
        quality = certify_story_question_quality()
        _write_json(out / "story-question-quality.json", quality)
        meta["question_quality"] = {
            "status": quality.get("status"),
            "promotion_ready": quality.get("promotion_ready"),
            "question_count": quality.get("question_count"),
            "failed": quality.get("failed"),
        }
        _write_json(out / "meta.json", meta)
    except Exception as exc:
        meta["errors"].append({
            "stage": "question_quality",
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        })
        _write_json(out / "story-question-quality.error.json", meta["errors"][-1])
        _write_json(out / "meta.json", meta)

    try:
        reach = certify_story_game_reach(seed="production-story-game-reach")
        _write_json(out / "story-game-reach.json", reach)
        meta["game_reach"] = {
            "promotion_ready": reach.get("promotion_ready"),
            "games_tested": reach.get("games_tested"),
            "games_with_story_content": reach.get("games_with_story_content"),
            "reach_fraction": reach.get("reach_fraction"),
        }
        _write_json(out / "meta.json", meta)
    except Exception as exc:
        meta["errors"].append({
            "stage": "game_reach",
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        })
        _write_json(out / "story-game-reach.error.json", meta["errors"][-1])
        _write_json(out / "meta.json", meta)

    meta["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    complete = (
        not meta["errors"]
        and meta["question_quality"] is not None
        and meta["game_reach"] is not None
    )
    meta["runner_complete"] = complete
    _write_json(out / "meta.json", meta)
    _status(status_path, "COMPLETE" if complete else "FAILED")
    return 0 if complete else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/tmp/reads-story-cert-run")
    args = ap.parse_args()
    raise SystemExit(run(args.out_dir))


if __name__ == "__main__":
    main()
