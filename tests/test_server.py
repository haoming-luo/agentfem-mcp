from __future__ import annotations

import asyncio

from mcp import Client

from agentfem_mcp.server import build_server


def test_focused_success_retains_contract_and_failed_run_remains_status(monkeypatch):
    from agentfem_mcp import server

    record = {"schema": "agentfem.api-callable", "parameters": [{"name": "mesh"}]}
    calls = []

    class ReadBridge:
        def describe(self, **kwargs):
            calls.append(kwargs)
            return record

        def get_run_status(self, path, job_id):
            return {"status": "failed", "job_id": job_id, "error": {"code": "SOLVE"}}

    monkeypatch.setattr(server, "bridge", lambda: ReadBridge())

    async def exercise():
        async with Client(build_server()) as client:
            result = await client.call_tool(
                "describe_system", {"api": "fields.displacement"}
            )
            assert not result.is_error
            assert result.structured_content == record
            status = await client.call_tool(
                "get_run_status", {"path": "project", "job_id": "known"}
            )
            assert not status.is_error
            assert status.structured_content["status"] == "failed"

    asyncio.run(exercise())
    assert calls == [{"detail": "summary", "topic": None, "api": "fields.displacement"}]


def test_runtime_discovery_failure_has_protocol_flag(monkeypatch):
    from agentfem_mcp import server
    from agentfem_mcp.bridge import BridgeError

    def unavailable():
        raise BridgeError("AFM-MCP-RUNTIME", "Install or select the runtime.")

    monkeypatch.setattr(server, "bridge", unavailable)

    async def exercise():
        async with Client(build_server()) as client:
            result = await client.call_tool("describe_system", {})
            assert result.is_error
            assert result.structured_content["error"]["code"] == "AFM-MCP-RUNTIME"

    asyncio.run(exercise())


def test_tool_failure_has_protocol_flag_and_structured_details(monkeypatch):
    from agentfem_mcp import server
    from agentfem_mcp.bridge import BridgeError

    class FailedBridge:
        def describe(self, **kwargs):
            raise BridgeError("AFM-TEST", "missing query", details={"option": "test"})

    monkeypatch.setattr(server, "bridge", lambda: FailedBridge())

    async def exercise():
        async with Client(build_server()) as client:
            result = await client.call_tool("describe_system", {"topic": "materials"})
            assert result.is_error
            assert result.structured_content["error"]["code"] == "AFM-TEST"
            assert result.structured_content["error"]["details"] == {"option": "test"}

    asyncio.run(exercise())


def test_mcp_contract_exposes_only_the_seven_workflow_tools() -> None:
    async def exercise() -> None:
        async with Client(build_server()) as client:
            tools = (await client.list_tools()).tools
            names = {tool.name for tool in tools}
            assert names == {
                "create_project",
                "describe_system",
                "get_result_summary",
                "get_run_status",
                "inspect_project",
                "submit_run",
                "validate_project",
            }
            by_name = {tool.name: tool for tool in tools}
            assert by_name["describe_system"].annotations.read_only_hint is True
            assert by_name["submit_run"].annotations.destructive_hint is False

    asyncio.run(exercise())
