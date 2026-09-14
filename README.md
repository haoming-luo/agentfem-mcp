<p align="center"><img src="https://raw.githubusercontent.com/haoming-luo/agentfem/main/logo/AgentFEM_logo.png" alt="AgentFEM" width="240"></p>

# AgentFEM MCP

[![CI](https://github.com/haoming-luo/agentfem-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/haoming-luo/agentfem-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/agentfem-mcp.svg)](https://pypi.org/project/agentfem-mcp/)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-listed-6750A4)](https://registry.modelcontextprotocol.io/?q=io.github.haoming-luo%2Fagentfem)

**One finite-element platform. Any compatible agent. Evidence intact.**

AgentFEM MCP gives Codex, Claude, and other MCP-compatible agents a small,
stable tool surface for building and running inspectable finite-element
projects. AgentFEM remains the deterministic scientific engine; the agent
interprets intent and explains evidence.

[Install from PyPI](https://pypi.org/project/agentfem-mcp/) ·
[Discover in the official MCP Registry](https://registry.modelcontextprotocol.io/?q=io.github.haoming-luo%2Fagentfem) ·
[Read the AgentFEM agent guide](https://haoming-luo.github.io/agentfem/agents/)

It exposes seven tools—not hundreds of solver internals:

| Tool | Purpose |
|---|---|
| `describe_system` | Inspect the installed runtime and a compact capability map |
| `create_project` | Start from a version-matched AgentFEM template |
| `validate_project` | Fail closed before a solve |
| `inspect_project` | Read project and recent-run identity |
| `submit_run` | Launch an isolated serial or MPI process |
| `get_run_status` | Observe a durable background job |
| `get_result_summary` | Read a compact result and trust state; request full evidence only when needed |

## Bring it to life

AgentFEM must already be installed. With `uvx`, Codex needs one command and the
adapter remains isolated from the numerical environment:

```bash
codex mcp add agentfem \
  --env AGENTFEM_MCP_ROOTS=/absolute/path/to/AgentFEMProjects \
  -- uvx --from agentfem-mcp agentfem-mcp
```

Or install the lightweight adapter in the active environment:

```bash
python -m pip install agentfem-mcp
```

The 0.1.0 lifecycle is acceptance-tested with the public AgentFEM 0.3.3 CLI
contracts and the current 0.3.7 development line.

Give your agent a project root, not your whole home directory.

### Codex

Codex officially supports local stdio MCP servers. Confirm the connection with
`codex mcp list`, then begin with:

> Use AgentFEM to create, validate, run, verify, and briefly explain a 2D
> cantilever. Keep the project and result paths visible.

### Claude Desktop and compatible clients

Claude Code:

```bash
claude mcp add agentfem --scope user \
  --env AGENTFEM_MCP_ROOTS=/absolute/path/to/AgentFEMProjects \
  -- uvx --from agentfem-mcp agentfem-mcp
```

Claude Desktop configuration:

```json
{
  "mcpServers": {
    "agentfem": {
      "command": "agentfem-mcp",
      "env": {
        "AGENTFEM_MCP_ROOTS": "/absolute/path/to/AgentFEMProjects"
      }
    }
  }
}
```

If a desktop app cannot see the activated conda environment, set
`AGENTFEM_COMMAND` to the absolute `agentfem` executable. The official macOS
runtime, AgentFEM WSL2 runtime, and common `agentfem-env`/`fenicsx-env` layouts
are also detected automatically.

### VS Code and other models

VS Code can place the same local server in `.vscode/mcp.json`:

```json
{
  "servers": {
    "agentfem": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "agentfem-mcp", "agentfem-mcp"],
      "env": {
        "AGENTFEM_MCP_ROOTS": "${workspaceFolder}"
      }
    }
  }
}
```

The server is model-neutral. A DeepSeek or other model can use it through any
host that implements local MCP tools. ChatGPT connectors require a public HTTPS
server; AgentFEM will add that route only with a real authenticated compute and
artifact boundary, rather than silently uploading local models through this
adapter.

### Local Codex plugin

This repository contains a portable AgentFEM workflow skill and a local Codex
marketplace under `.agents/plugins/`. It combines scientific operating guidance
with the same MCP server; it does not create a second solver interface.

## The contract

```text
AI agent
   │  seven typed MCP tools
   ▼
AgentFEM MCP ── process + path boundary
   │  versioned JSON contracts
   ▼
AgentFEM CLI → Study → Model → Step → SimulationResult
   ▼
FEniCSx / PETSc / MPI
```

- No language model or API key is embedded in AgentFEM MCP.
- No shell command or arbitrary Python string is accepted from a tool call.
- All project paths must remain under explicitly approved roots.
- Numerical runs occur in child processes, isolating PETSc/MPI lifetime from
  the MCP server.
- `completed`, `verified`, and `validated` remain different scientific states.

## Environment controls

| Variable | Meaning |
|---|---|
| `AGENTFEM_MCP_ROOTS` | Approved project roots separated by the platform path separator |
| `AGENTFEM_COMMAND` | Absolute path to a specific `agentfem` executable |

With no root configured, the server restricts access to its working directory.
The default maximum is 16 MPI ranks and can only be changed by the server
operator, not by an agent tool call.

## Development

```bash
python -m pip install -e '.[test]'
ruff check .
pytest
python -m build
```

See [SECURITY.md](SECURITY.md) for the trust boundary and
[CONTRIBUTING.md](CONTRIBUTING.md) for contribution expectations. The
[first release evidence](docs/release-evidence.md) records protocol, package,
and real-solver acceptance separately.

AgentFEM MCP is Apache-2.0 licensed and maintained as an official companion to
[AgentFEM](https://github.com/haoming-luo/agentfem).

<!-- mcp-name: io.github.haoming-luo/agentfem -->
