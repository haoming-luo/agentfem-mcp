from __future__ import annotations

import json
import sys
from pathlib import Path

from agentfem_mcp.worker import _CAPTURE_MEMORY_LIMIT, execute


def test_worker_spools_verbose_output_and_keeps_final_json(tmp_path: Path) -> None:
    job = tmp_path / "job.json"
    job.write_text(json.dumps({"status": "submitted"}), encoding="utf-8")
    script = (
        "import json; "
        f"print('x' * ({_CAPTURE_MEMORY_LIMIT} + 100)); "
        "print(json.dumps({'status': 'completed', 'result_manifest': 'result.json'}))"
    )

    assert execute(job, [sys.executable, "-c", script]) == 0

    state = json.loads(job.read_text(encoding="utf-8"))
    assert state["status"] == "completed"
    assert state["agentfem"]["status"] == "completed"
    assert state["stdout_truncated"] is True
    assert len(state["stdout_tail"]) <= 4000
    assert state["stderr_truncated"] is False
