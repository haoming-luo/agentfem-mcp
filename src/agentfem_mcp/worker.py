"""Detached worker for one AgentFEM run."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_CAPTURE_MEMORY_LIMIT = 1024 * 1024
_PARSE_TAIL_LIMIT = 1024 * 1024
_STATE_TAIL_LIMIT = 4000


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("Job record must be a JSON object.")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
            stream.write("\n")
            temporary = Path(stream.name)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _payload(text: str) -> dict[str, Any] | None:
    candidates = (text.strip(), *reversed(text.splitlines()))
    for candidate in candidates:
        if not candidate.strip():
            continue
        try:
            value = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _tail(stream, limit: int) -> tuple[str, bool]:
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(max(0, size - limit))
    value = stream.read().decode("utf-8", errors="replace")
    return value, size > limit


def execute(job: Path, command: list[str]) -> int:
    state = _read(job)
    state.update(status="running", started_at=_now(), updated_at=_now())
    _write(job, state)
    # Scientific runtimes can emit substantial compiler, PETSc, or MPI logs.
    # Spooling prevents a long solve from retaining those streams in memory.
    with (
        tempfile.SpooledTemporaryFile(max_size=_CAPTURE_MEMORY_LIMIT) as stdout,
        tempfile.SpooledTemporaryFile(max_size=_CAPTURE_MEMORY_LIMIT) as stderr,
    ):
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
        stdout_text, stdout_truncated = _tail(stdout, _PARSE_TAIL_LIMIT)
        stderr_text, stderr_truncated = _tail(stderr, _PARSE_TAIL_LIMIT)
    payload = _payload(stdout_text)
    state = _read(job)
    state.update(
        status="completed" if completed.returncode == 0 else "failed",
        exit_code=int(completed.returncode),
        completed_at=_now(),
        updated_at=_now(),
        agentfem=payload,
        stdout_tail=stdout_text[-_STATE_TAIL_LIMIT:] or None,
        stderr_tail=stderr_text[-_STATE_TAIL_LIMIT:] or None,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
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
