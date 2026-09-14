"""Safe process boundary between MCP and an installed AgentFEM runtime."""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from ._version import __version__

_RUN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class BridgeError(RuntimeError):
    """An addressable configuration or AgentFEM command failure."""

    def __init__(
        self, code: str, message: str, *, details: Mapping[str, Any] | None = None
    ):
        self.code = str(code)
        self.details = dict(details or {})
        super().__init__(message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "failed",
            "error": {
                "code": self.code,
                "message": str(self),
                "details": self.details,
            },
        }


@dataclass(frozen=True)
class CommandOutcome:
    """One bounded AgentFEM CLI call."""

    ok: bool
    exit_code: int
    payload: Mapping[str, Any]
    stderr: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "exit_code": self.exit_code,
            "payload": dict(self.payload),
            "stderr": self.stderr or None,
        }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BridgeError("AFM-MCP-JOB-404", f"Unknown job: {path.stem}.") from exc
    except json.JSONDecodeError as exc:
        raise BridgeError(
            "AFM-MCP-JOB-INVALID",
            f"Job state is not valid JSON: {path}.",
        ) from exc
    if not isinstance(value, dict):
        raise BridgeError(
            "AFM-MCP-JOB-INVALID", f"Job state must be an object: {path}."
        )
    return value


def _parse_json_output(text: str) -> Mapping[str, Any]:
    selected = text.strip()
    if not selected:
        return {}
    try:
        value = json.loads(selected)
    except json.JSONDecodeError as exc:
        raise BridgeError(
            "AFM-MCP-CLI-OUTPUT",
            "AgentFEM did not return its documented JSON contract.",
            details={"output_tail": selected[-2000:]},
        ) from exc
    if not isinstance(value, dict):
        raise BridgeError(
            "AFM-MCP-CLI-OUTPUT", "AgentFEM JSON output must be an object."
        )
    return value


class AgentFEMBridge:
    """Expose AgentFEM's existing process contracts inside approved roots.

    The bridge never evaluates user-supplied code strings and never invokes a
    shell. A project remains an ordinary, inspectable AgentFEM project. Actual
    solves execute in a child process so PETSc and MPI do not enter the MCP
    server's lifetime.
    """

    def __init__(
        self,
        *,
        roots: Sequence[str | Path] | None = None,
        command: Sequence[str] | None = None,
        timeout_seconds: float = 120.0,
        max_mpi_ranks: int = 16,
    ) -> None:
        configured_roots = tuple(roots or self._environment_roots())
        if not configured_roots:
            configured_roots = (Path.cwd(),)
        self.roots = tuple(
            Path(item).expanduser().resolve() for item in configured_roots
        )
        self.command = tuple(command or self._discover_command())
        self.timeout_seconds = float(timeout_seconds)
        self.max_mpi_ranks = int(max_mpi_ranks)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")
        if self.max_mpi_ranks <= 0:
            raise ValueError("max_mpi_ranks must be positive.")

    @staticmethod
    def _environment_roots() -> tuple[Path, ...]:
        raw = os.environ.get("AGENTFEM_MCP_ROOTS", "")
        return tuple(Path(item) for item in raw.split(os.pathsep) if item.strip())

    @staticmethod
    def _discover_command() -> tuple[str, ...]:
        configured = os.environ.get("AGENTFEM_COMMAND", "").strip()
        if configured:
            path = Path(configured).expanduser()
            if not path.is_file():
                raise BridgeError(
                    "AFM-MCP-RUNTIME-001",
                    f"AGENTFEM_COMMAND does not name a file: {path}.",
                )
            return (str(path.resolve()),)
        executable = shutil.which("agentfem")
        if executable:
            return (str(Path(executable).resolve()),)
        # GUI-launched agents often do not inherit an activated conda PATH.
        # Recognize AgentFEM's documented runtimes and common conda layouts so
        # the normal installer remains a zero-configuration experience.
        home = Path.home()
        candidates = [Path("/opt/conda/bin/agentfem")]
        candidates.extend(
            sorted(
                (home / "Library").glob("AgentFEMRuntime-*/bin/agentfem"),
                key=lambda item: item.parent.parent.name,
                reverse=True,
            )
        )
        conda_roots = (
            home / ".conda" / "envs",
            home / "miniforge3" / "envs",
            home / "mambaforge" / "envs",
            Path("/opt/homebrew/Caskroom/miniforge/base/envs"),
        )
        # Prefer the documented AgentFEM environment across all conda roots;
        # retain fenicsx-env only as the legacy developer fallback.
        for environment in ("agentfem-env", "fenicsx-env"):
            candidates.extend(
                conda_root / environment / "bin" / "agentfem"
                for conda_root in conda_roots
            )
        available = tuple(item.resolve() for item in candidates if item.is_file())
        if available:
            return (str(available[0]),)
        return (sys.executable, "-m", "agentfem.cli")

    def describe(
        self, *, detail: Literal["summary", "full"] = "summary"
    ) -> dict[str, Any]:
        """Describe one runtime without flooding an agent's working context."""

        doctor = self._require(self._run(("doctor", "--json")))
        capabilities = self._require(self._run(("capabilities", "--json")))
        result: dict[str, Any] = {
            "schema": "agentfem.mcp-system",
            "schema_version": "0.1.0",
            "server_version": __version__,
            "roots": [str(item) for item in self.roots],
            "max_mpi_ranks": self.max_mpi_ranks,
            "runtime": self._runtime_summary(doctor),
            "capabilities": self._capability_summary(capabilities),
        }
        if detail == "full":
            result["runtime"] = doctor
            result["capabilities"] = capabilities
        return result

    def create_project(
        self,
        path: str,
        *,
        template: str = "static-solid",
        name: str | None = None,
    ) -> dict[str, Any]:
        target = self._path(path, must_exist=False)
        if target.exists():
            if not target.is_dir():
                raise BridgeError(
                    "AFM-MCP-PROJECT-EXISTS",
                    f"Project target is not a directory: {target}.",
                )
            if any(target.iterdir()):
                raise BridgeError(
                    "AFM-MCP-PROJECT-EXISTS",
                    f"Refusing to write into non-empty directory: {target}.",
                )
        arguments = ["init", str(target), "--template", str(template), "--json"]
        if name:
            arguments.extend(("--name", name))
        return self._require(self._run(arguments))

    def validate_project(self, path: str) -> dict[str, Any]:
        project = self._path(path, must_exist=True)
        outcome = self._run(("check", "--project", str(project), "--json"))
        result = outcome.as_dict()
        result["accepted"] = self._validation_passed(outcome)
        result["project_root"] = str(project)
        return result

    def inspect_project(self, path: str) -> dict[str, Any]:
        project = self._path(path, must_exist=True)
        check = self.validate_project(str(project))
        recent = self._run(
            ("runs", "--project", str(project), "--limit", "5", "--json")
        )
        return {
            "schema": "agentfem.mcp-project",
            "schema_version": "0.1.0",
            "project_root": str(project),
            "validation": check,
            "recent_runs": recent.as_dict(),
        }

    def submit_run(
        self, path: str, *, name: str = "agent", mpi_ranks: int = 1
    ) -> dict[str, Any]:
        project = self._path(path, must_exist=True)
        if not _RUN_NAME.fullmatch(str(name)):
            raise BridgeError(
                "AFM-MCP-RUN-NAME",
                "Run name must contain only letters, numbers, '.', '_' or '-' and be at most 64 characters.",
            )
        ranks = int(mpi_ranks)
        if not 1 <= ranks <= self.max_mpi_ranks:
            raise BridgeError(
                "AFM-MCP-MPI-LIMIT",
                f"mpi_ranks must be between 1 and {self.max_mpi_ranks}.",
            )
        validation = self._run(("check", "--project", str(project), "--json"))
        if not self._validation_passed(validation):
            raise BridgeError(
                "AFM-MCP-PREFLIGHT",
                "AgentFEM project validation failed; the run was not started.",
                details=validation.as_dict(),
            )
        job_id = (
            f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
        )
        job_path = self._job_path(project, job_id)
        state = {
            "schema": "agentfem.mcp-job",
            "schema_version": "0.1.0",
            "job_id": job_id,
            "run_id": job_id,
            "run_name": name,
            "project_root": str(project),
            "mpi_ranks": ranks,
            "status": "submitted",
            "submitted_at": _utc_now(),
            "updated_at": _utc_now(),
            "runtime_command": list(self.command),
        }
        _atomic_json(job_path, state)
        worker = [
            sys.executable,
            "-m",
            "agentfem_mcp.worker",
            "--job",
            str(job_path),
            "--",
            *self.command,
            "run",
            "--project",
            str(project),
            "--run-id",
            job_id,
            "--name",
            name,
            "--mpi",
            str(ranks),
            "--json",
        ]
        log_directory = job_path.parent
        stdout = (log_directory / "worker.stdout.log").open("ab")
        stderr = (log_directory / "worker.stderr.log").open("ab")
        try:
            process = subprocess.Popen(
                worker,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
        finally:
            stdout.close()
            stderr.close()
        # The worker may already have advanced the record. Merge the PID into
        # its latest state instead of accidentally reverting "running" or a
        # very fast "completed" result back to "submitted".
        current = _read_json(job_path)
        current["worker_pid"] = process.pid
        current["updated_at"] = _utc_now()
        _atomic_json(job_path, current)
        return current

    def get_run_status(self, path: str, job_id: str) -> dict[str, Any]:
        project = self._path(path, must_exist=True)
        state = _read_json(self._job_path(project, job_id))
        if Path(str(state.get("project_root", ""))).resolve() != project:
            raise BridgeError(
                "AFM-MCP-JOB-ROOT", "Job does not belong to this project."
            )
        result = dict(state)
        result["agentfem_execution"] = None
        # Polling a long job must remain a cheap file read. Importing the full
        # numerical runtime on every heartbeat wastes memory and CPU; query the
        # immutable AgentFEM run index only after a terminal state is reached.
        if state.get("status") in {"completed", "failed"}:
            run_index = self._run(
                ("runs", "--project", str(project), "--limit", "20", "--json")
            )
            runs = (
                run_index.payload.get("runs", ())
                if isinstance(run_index.payload, Mapping)
                else ()
            )
            result["agentfem_execution"] = next(
                (
                    item
                    for item in runs
                    if isinstance(item, Mapping) and item.get("run_id") == job_id
                ),
                None,
            )
        return result

    def get_result_summary(
        self,
        path: str,
        *,
        job_id: str | None = None,
        detail: Literal["summary", "full"] = "summary",
    ) -> dict[str, Any]:
        project = self._path(path, must_exist=True)
        if job_id:
            state = _read_json(self._job_path(project, job_id))
            payload = state.get("agentfem")
            if not isinstance(payload, Mapping):
                raise BridgeError(
                    "AFM-MCP-RESULT-PENDING",
                    f"Job {job_id} has not produced an AgentFEM result yet.",
                    details={"status": state.get("status")},
                )
            manifest = payload.get("result_manifest")
            if not manifest:
                raise BridgeError(
                    "AFM-MCP-RESULT-MISSING",
                    f"Job {job_id} did not publish a SimulationResult.",
                )
            manifest_path = Path(str(manifest)).expanduser().resolve(strict=False)
            if not (manifest_path == project or manifest_path.is_relative_to(project)):
                raise BridgeError(
                    "AFM-MCP-RESULT-PATH",
                    "AgentFEM published a result path outside the approved project.",
                )
            outcome = self._run(("show", str(manifest_path), "--json"))
        else:
            outcome = self._run(("show", "latest", "--project", str(project), "--json"))
        result = self._require(outcome)
        return result if detail == "full" else self._result_summary(result)

    def _job_path(self, project: Path, job_id: str) -> Path:
        if not _RUN_NAME.fullmatch(str(job_id)):
            raise BridgeError("AFM-MCP-JOB-ID", "Invalid job identifier.")
        return project / ".agentfem-mcp" / "jobs" / str(job_id) / "job.json"

    def _path(self, value: str | Path, *, must_exist: bool) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.roots[0] / path
        selected = path.resolve(strict=False)
        if not any(
            selected == root or selected.is_relative_to(root) for root in self.roots
        ):
            raise BridgeError(
                "AFM-MCP-PATH-001",
                f"Path is outside the approved AgentFEM roots: {selected}.",
                details={"approved_roots": [str(item) for item in self.roots]},
            )
        if must_exist and not selected.is_dir():
            raise BridgeError(
                "AFM-MCP-PATH-404", f"Project directory does not exist: {selected}."
            )
        return selected

    def _run(self, arguments: Sequence[str]) -> CommandOutcome:
        try:
            completed = subprocess.run(
                (*self.command, *tuple(arguments)),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise BridgeError(
                "AFM-MCP-RUNTIME-001",
                "AgentFEM executable was not found. Install AgentFEM in this environment or set AGENTFEM_COMMAND.",
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise BridgeError(
                "AFM-MCP-CLI-TIMEOUT",
                f"AgentFEM command exceeded {self.timeout_seconds:g} seconds.",
            ) from exc
        try:
            payload = _parse_json_output(completed.stdout)
        except BridgeError as exc:
            exc.details.update(
                {
                    "exit_code": int(completed.returncode),
                    "stderr_tail": completed.stderr.strip()[-2000:] or None,
                    "command": [*self.command, *tuple(arguments)],
                }
            )
            raise
        return CommandOutcome(
            ok=completed.returncode == 0,
            exit_code=int(completed.returncode),
            payload=payload,
            stderr=completed.stderr.strip()[-4000:],
        )

    @staticmethod
    def _require(outcome: CommandOutcome) -> dict[str, Any]:
        if outcome.ok:
            return dict(outcome.payload)
        raise BridgeError(
            "AFM-MCP-CLI-FAILED",
            "AgentFEM rejected the requested operation.",
            details=outcome.as_dict(),
        )

    @staticmethod
    def _validation_passed(outcome: CommandOutcome) -> bool:
        """Require both process success and non-negative scientific semantics."""

        if not outcome.ok:
            return False
        if outcome.payload.get("valid") is False:
            return False
        status = str(outcome.payload.get("status", "")).strip().lower()
        return status not in {"error", "failed", "invalid", "rejected"}

    @staticmethod
    def _runtime_summary(report: Mapping[str, Any]) -> dict[str, Any]:
        packages = report.get("packages")
        optional = report.get("optional")
        platform = report.get("platform")
        execution = report.get("execution")
        return {
            "schema": report.get("schema"),
            "schema_version": report.get("schema_version"),
            "healthy": report.get(
                "healthy",
                report.get(
                    "solver_ready",
                    report.get("status") not in {"failed", "unhealthy"},
                ),
            ),
            "python": report.get("python"),
            "machine": report.get("machine"),
            "packages": dict(packages) if isinstance(packages, Mapping) else packages,
            "optional": [
                {
                    "capability": item.get("capability"),
                    "available": item.get("available"),
                    "version": item.get("version"),
                }
                for item in optional or ()
                if isinstance(item, Mapping)
            ],
            "platform": dict(platform) if isinstance(platform, Mapping) else platform,
            "execution": dict(execution)
            if isinstance(execution, Mapping)
            else execution,
        }

    @staticmethod
    def _capability_summary(report: Mapping[str, Any]) -> dict[str, Any]:
        constitutive = report.get("constitutive") or ()
        providers = report.get("step_providers") or ()
        return {
            "schema": report.get("schema"),
            "schema_version": report.get("schema_version"),
            "agentfem_version": report.get("agentfem_version"),
            "commands": list(report.get("commands") or ()),
            "templates": list(report.get("templates") or ()),
            "constitutive": [
                {"name": item.get("name"), "maturity": item.get("maturity")}
                for item in constitutive
                if isinstance(item, Mapping)
            ],
            "step_providers": [
                {
                    "name": item.get("name"),
                    "analyses": list(item.get("analyses") or ()),
                    "procedure": item.get("procedure"),
                }
                for item in providers
                if isinstance(item, Mapping)
            ],
        }

    @staticmethod
    def _result_summary(report: Mapping[str, Any]) -> dict[str, Any]:
        seal = report.get("provenance_seal")
        runtime = report.get("runtime")
        scientific_inputs = report.get("scientific_inputs")
        metadata = report.get("metadata")
        run = metadata.get("run") if isinstance(metadata, Mapping) else None
        verification = report.get("verification")
        quantities = report.get("quantity_records") or ()
        return {
            "schema": report.get("schema"),
            "schema_version": report.get("schema_version"),
            "status": report.get("status"),
            "trust_level": report.get("trust_level", report.get("trust")),
            "name": report.get("name"),
            "run_id": report.get("run_id")
            or (run.get("run_id") if isinstance(run, Mapping) else None),
            "quantities": [
                {
                    "name": item.get("name"),
                    "value": item.get("value"),
                    "unit": item.get("unit"),
                    "kind": item.get("kind"),
                }
                for item in quantities
                if isinstance(item, Mapping)
            ],
            "fields": list(report.get("fields") or ()),
            "artifacts": dict(report.get("artifacts") or {}),
            "verification": (
                {
                    key: verification.get(key)
                    for key in ("status", "accepted", "profile", "policy", "summary")
                    if key in verification
                }
                if isinstance(verification, Mapping)
                else verification
            ),
            "scientific_inputs": (
                {
                    "complete": scientific_inputs.get("complete"),
                    "fingerprint": scientific_inputs.get("fingerprint"),
                    "missing_count": len(scientific_inputs.get("missing") or ()),
                }
                if isinstance(scientific_inputs, Mapping)
                else None
            ),
            "provenance": (
                {
                    "completeness": seal.get("completeness"),
                    "seal_id": seal.get("seal_id"),
                    "producer_version": seal.get("producer_version"),
                }
                if isinstance(seal, Mapping)
                else None
            ),
            "runtime_fingerprint": (
                runtime.get("fingerprint") if isinstance(runtime, Mapping) else None
            ),
        }


__all__ = ["AgentFEMBridge", "BridgeError", "CommandOutcome"]
