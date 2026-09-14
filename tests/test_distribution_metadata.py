from __future__ import annotations

import asyncio
import json
import tomllib
from pathlib import Path

from agentfem_mcp._version import __version__
from agentfem_mcp.server import build_server

ROOT = Path(__file__).resolve().parents[1]


def test_public_distribution_versions_are_one_contract() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))

    assert project["project"]["name"] == "agentfem-mcp"
    assert project["project"]["version"] == __version__
    assert registry["name"] == "io.github.haoming-luo/agentfem"
    assert registry["version"] == __version__
    assert registry["packages"][0]["identifier"] == "agentfem-mcp"
    assert registry["packages"][0]["version"] == __version__


def test_mcpb_manifest_tracks_public_server_contract() -> None:
    manifest = json.loads(
        (ROOT / "packaging" / "mcpb" / "manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["name"] == "agentfem"
    assert manifest["version"] == __version__
    assert manifest["server"]["type"] == "uv"
    assert manifest["server"]["mcp_config"]["env"] == {
        "AGENTFEM_MCP_ROOTS": "${user_config.project_root}"
    }
    assert {item["name"] for item in manifest["tools"]} == {
        tool.name for tool in asyncio.run(build_server().list_tools())
    }


def test_discovery_container_is_pinned_and_unprivileged() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.12-slim-bookworm@sha256:" in dockerfile
    assert f"ARG AGENTFEM_MCP_VERSION={__version__}" in dockerfile
    assert '"agentfem-mcp==${AGENTFEM_MCP_VERSION}"' in dockerfile
    assert "USER agentfem" in dockerfile
    assert 'ENTRYPOINT ["agentfem-mcp"]' in dockerfile
