"""MCP tools for AgentFEM's existing scientific execution contracts."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from ._version import __version__
from .bridge import AgentFEMBridge, BridgeError

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)
WRITE_ONCE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=False,
)
COMPUTE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=False,
)


@lru_cache(maxsize=1)
def bridge() -> AgentFEMBridge:
    return AgentFEMBridge()


def _call(operation, *args, **kwargs) -> dict[str, Any]:
    try:
        return operation(*args, **kwargs)
    except BridgeError as exc:
        return exc.as_dict()


def build_server() -> MCPServer:
    server = MCPServer(
        name="AgentFEM",
        version=__version__,
        instructions=(
            "Use AgentFEM as a deterministic finite-element platform. Validate before "
            "running, preserve the returned project and run identities, and never describe "
            "a merely completed result as verified unless its result record says so."
        ),
    )

    @server.tool(
        title="Describe AgentFEM",
        description="Inspect the installed AgentFEM runtime and approved roots. Use summary first; request full only when selecting an advanced capability.",
        annotations=READ_ONLY,
    )
    def describe_system(
        detail: Literal["summary", "full"] = "summary",
    ) -> dict[str, Any]:
        return _call(bridge().describe, detail=detail)

    @server.tool(
        title="Create AgentFEM project",
        description="Create a new project from one version-matched official AgentFEM template inside an approved root.",
        annotations=WRITE_ONCE,
    )
    def create_project(
        path: str, template: str = "static-solid", name: str | None = None
    ) -> dict[str, Any]:
        return _call(bridge().create_project, path, template=template, name=name)

    @server.tool(
        title="Validate AgentFEM project",
        description="Run fail-closed structural and compatibility checks without solving the project.",
        annotations=READ_ONLY,
    )
    def validate_project(path: str) -> dict[str, Any]:
        return _call(bridge().validate_project, path)

    @server.tool(
        title="Inspect AgentFEM project",
        description="Read project validation and recent immutable run identities without modifying the project.",
        annotations=READ_ONLY,
    )
    def inspect_project(path: str) -> dict[str, Any]:
        return _call(bridge().inspect_project, path)

    @server.tool(
        title="Submit AgentFEM run",
        description="After preflight, start a finite-element run in a separate process and return a durable job identity immediately.",
        annotations=COMPUTE,
    )
    def submit_run(
        path: str, name: str = "agent", mpi_ranks: int = 1
    ) -> dict[str, Any]:
        return _call(bridge().submit_run, path, name=name, mpi_ranks=mpi_ranks)

    @server.tool(
        title="Get AgentFEM run status",
        description="Read one submitted run's status and any AgentFEM execution evidence currently available.",
        annotations=READ_ONLY,
    )
    def get_run_status(path: str, job_id: str) -> dict[str, Any]:
        return _call(bridge().get_run_status, path, job_id)

    @server.tool(
        title="Get AgentFEM result summary",
        description="Read the structured scientific result for a completed job or the project's latest run, including its trust state.",
        annotations=READ_ONLY,
    )
    def get_result_summary(
        path: str,
        job_id: str | None = None,
        detail: Literal["summary", "full"] = "summary",
    ) -> dict[str, Any]:
        return _call(bridge().get_result_summary, path, job_id=job_id, detail=detail)

    return server


mcp = build_server()


__all__ = ["build_server", "mcp"]
