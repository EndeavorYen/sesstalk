from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "sesstalk.py"


def run_cli(
    home: Path,
    *args: str,
    check: bool = True,
    timeout: float | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SESSTALK_HOME"] = str(home)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-S", str(CLI), *args],
        check=check,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def payload(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def start_receive(home: Path, name: str, timeout: int = 8) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["SESSTALK_HOME"] = str(home)
    return subprocess.Popen(
        [sys.executable, "-S", str(CLI), "receive", "--name", name, "--timeout", str(timeout)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
