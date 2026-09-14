from __future__ import annotations

import stat
import time
from pathlib import Path

import pytest

from agentfem_mcp.bridge import AgentFEMBridge, BridgeError, CommandOutcome

FAKE_AGENTFEM = r"""#!/usr/bin/env python3
import json
from pathlib import Path
import sys

args = sys.argv[1:]
command = args[0]

def option(name, default=None):
    try:
        return args[args.index(name) + 1]
    except ValueError:
        return default

if command == "doctor":
    print(json.dumps({"schema": "agentfem.runtime-report", "schema_version": "0.1.0", "python": "3.11", "machine": "test", "packages": {"agentfem": "0.test"}, "optional": [], "platform": {"system": "test"}, "execution": {"mode": "installed_distribution"}}))
elif command == "capabilities":
    print(json.dumps({"schema": "agentfem.capabilities", "schema_version": "0.2.3", "agentfem_version": "0.test", "commands": ["run"], "templates": ["static-solid"], "constitutive": [{"name": "linear_elasticity", "maturity": "fem_integrated", "limitations": ["large omitted field"]}], "step_providers": [{"name": "linear_static_operators", "analyses": ["linear_static"], "procedure": "standard/linear", "options": {"accepted": ["K", "F"]}}]}))
elif command == "init":
    target = Path(args[1])
    target.mkdir(parents=True, exist_ok=True)
    (target / "case.py").write_text("# generated\n")
    print(json.dumps({"schema": "agentfem.project", "status": "created", "project_root": str(target)}))
elif command == "check":
    print(json.dumps({"schema": "agentfem.project-check", "status": "passed", "valid": True}))
elif command == "runs":
    print(json.dumps({"schema": "agentfem.runs", "runs": []}))
elif command == "run":
    project = Path(option("--project"))
    run_id = option("--run-id")
    result = project / "outputs" / run_id / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps({"schema": "agentfem.simulation-result", "trust": "verified", "run_id": run_id}))
    print(json.dumps({"schema": "agentfem.run", "status": "completed", "run_id": run_id, "result_manifest": str(result)}))
elif command == "show":
    target = args[1]
    if target == "latest":
        print(json.dumps({"schema": "agentfem.simulation-result", "trust": "verified"}))
    else:
        print(Path(target).read_text())
else:
    print(json.dumps({"status": "failed", "error": {"code": "TEST-UNKNOWN"}}))
    raise SystemExit(2)
"""


@pytest.fixture
def fake_agentfem(tmp_path: Path) -> Path:
    executable = tmp_path / "agentfem"
    executable.write_text(FAKE_AGENTFEM, encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return executable


def test_describe_is_compact_by_default(tmp_path: Path, fake_agentfem: Path) -> None:
    bridge = AgentFEMBridge(roots=[tmp_path], command=[str(fake_agentfem)])
    report = bridge.describe()
    assert report["capabilities"]["agentfem_version"] == "0.test"
    assert "limitations" not in report["capabilities"]["constitutive"][0]
    assert bridge.describe(detail="full")["capabilities"]["constitutive"][0][
        "limitations"
    ]


def test_runtime_summary_honors_solver_ready() -> None:
    summary = AgentFEMBridge._runtime_summary(
        {"schema": "agentfem.runtime-report", "solver_ready": False}
    )
    assert summary["healthy"] is False


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (CommandOutcome(True, 0, {"status": "passed", "valid": True}), True),
        (CommandOutcome(True, 0, {"status": "passed", "valid": False}), False),
        (CommandOutcome(True, 0, {"status": "failed"}), False),
        (CommandOutcome(False, 2, {"status": "passed", "valid": True}), False),
    ],
)
def test_preflight_requires_process_and_scientific_success(
    outcome: CommandOutcome, expected: bool
) -> None:
    assert AgentFEMBridge._validation_passed(outcome) is expected


def test_path_policy_and_non_empty_project_fail_closed(
    tmp_path: Path, fake_agentfem: Path
) -> None:
    bridge = AgentFEMBridge(roots=[tmp_path], command=[str(fake_agentfem)])
    with pytest.raises(BridgeError, match="outside"):
        bridge.validate_project(str(tmp_path.parent))
    outside = tmp_path.parent / "outside-project"
    outside.mkdir(exist_ok=True)
    linked = tmp_path / "linked-project"
    linked.symlink_to(outside, target_is_directory=True)
    with pytest.raises(BridgeError, match="outside"):
        bridge.validate_project(str(linked))
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("user data", encoding="utf-8")
    with pytest.raises(BridgeError, match="non-empty"):
        bridge.create_project(str(occupied))


def test_create_submit_observe_and_read_result(
    tmp_path: Path, fake_agentfem: Path
) -> None:
    bridge = AgentFEMBridge(roots=[tmp_path], command=[str(fake_agentfem)])
    project = tmp_path / "cantilever"
    created = bridge.create_project(str(project))
    assert created["status"] == "created"
    assert bridge.validate_project(str(project))["ok"] is True

    submitted = bridge.submit_run(str(project), name="baseline")
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        status = bridge.get_run_status(str(project), submitted["job_id"])
        if status["status"] in {"completed", "failed"}:
            break
        time.sleep(0.02)
    assert status["status"] == "completed"
    assert status["worker_pid"] > 0
    result = bridge.get_result_summary(str(project), job_id=submitted["job_id"])
    assert result["trust_level"] == "verified"
    assert "trust" not in result
    full = bridge.get_result_summary(
        str(project), job_id=submitted["job_id"], detail="full"
    )
    assert full["trust"] == "verified"
