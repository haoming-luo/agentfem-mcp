"""Detached worker for one AgentFEM run."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("Job record must be a JSON object.")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _payload(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text.strip())
    except (json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def execute(job: Path, command: list[str]) -> int:
    state = _read(job)
    state.update(status="running", started_at=_now(), updated_at=_now())
    _write(job, state)
    completed = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _payload(completed.stdout)
    state = _read(job)
    state.update(
        status="completed" if completed.returncode == 0 else "failed",
        exit_code=int(completed.returncode),
        completed_at=_now(),
        updated_at=_now(),
        agentfem=payload,
        stdout_tail=completed.stdout[-4000:] or None,
        stderr_tail=completed.stderr[-4000:] or None,
    )
    _write(job, state)
    return int(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("worker requires a command after --")
    return execute(Path(args.job).resolve(), command)


if __name__ == "__main__":
    raise SystemExit(main())
