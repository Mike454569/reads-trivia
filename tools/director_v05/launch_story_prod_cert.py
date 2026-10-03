"""Spawn the Story production certification as a fully detached process."""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/tmp/reads-story-cert-run")
    args = ap.parse_args()

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "runner.log"
    pid_path = out / "runner.pid"

    env = os.environ.copy()
    with log_path.open("ab", buffering=0) as log:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "tools.director_v05.run_story_prod_cert_bundle",
                "--out-dir",
                str(out),
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=os.getcwd(),
            start_new_session=True,
            close_fds=True,
        )
    pid_path.write_text(str(proc.pid) + "\n", encoding="utf-8")
    print(proc.pid)


if __name__ == "__main__":
    main()
