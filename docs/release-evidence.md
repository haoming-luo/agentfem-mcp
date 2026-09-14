# Release evidence

AgentFEM MCP keeps four questions separate: does the Python package build, does
the MCP protocol work, can it drive a real solver, and did that particular
scientific result satisfy a verification contract?

## Version 0.1.0

Accepted on 2026-09-15:

- Python 3.11 and 3.12 unit-test matrix defined in CI;
- lint, seven unit/contract tests, wheel and source-distribution builds passed;
- MCP `server.json` passed the official 2025-12-11 Registry schema;
- the Codex plugin manifest and AgentFEM workflow Skill passed their validators;
- a separate stdio process exposed exactly the seven documented tools;
- the full project lifecycle completed against AgentFEM 0.3.7.dev0,
  DOLFINx 0.11.0, PETSc 3.25.2 and MPICH 5.0.1 on macOS arm64.
- the same create, check, detached-run, status, and compact-result lifecycle
  also completed against the installed public AgentFEM 0.3.3 contracts.
- the final artifacts were published from GitHub Actions to PyPI through OIDC,
  with digital attestations and without a persistent package token;
- `io.github.haoming-luo/agentfem` version 0.1.0 was accepted by the official
  MCP Registry and exposed as its latest active record;
- a clean environment installed `agentfem-mcp==0.1.0` from public PyPI,
  exposed exactly the seven documented tools, and completed the same real
  AgentFEM 0.3.3 lifecycle.
- the official MCPB 0.4 schema accepted the 1.6 kB desktop connection bundle;
  a clean UV environment installed its pinned public dependency and a real
  stdio handshake returned exactly the seven documented tools;
- the directory-health container pins the public package, runs as an
  unprivileged user, and is kept separate from the real local solver runtime.
- Glama claimed the repository to its maintainer, started the server through
  that container contract, and published its public directory score.

The real-solver smoke test created and checked the official `static-solid`
template, submitted an isolated run, observed its durable job identity, and
read the resulting `SimulationResult`. The solve completed with a relative
force-balance error of approximately `1.91e-12`, an energy-balance error of
approximately `2.55e-11`, and a complete provenance seal.

Its scientific trust level was `computed`, not `verified`, because the smoke
model did not declare an independent acceptance criterion. The adapter
preserved that distinction. This is a successful orchestration acceptance test,
not an external validation benchmark.

Public records:

- [GitHub Actions publish evidence](https://github.com/haoming-luo/agentfem-mcp/actions/runs/34878639416)
- [PyPI package and attestations](https://pypi.org/project/agentfem-mcp/0.1.0/)
- [official MCP Registry listing](https://registry.modelcontextprotocol.io/?q=io.github.haoming-luo%2Fagentfem)
- [Glama directory record](https://glama.ai/mcp/servers/haoming-luo/agentfem-mcp)
