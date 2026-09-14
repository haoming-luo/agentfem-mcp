from __future__ import annotations

import asyncio

from mcp import Client

from agentfem_mcp.server import build_server


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
