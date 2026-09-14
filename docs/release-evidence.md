# Release evidence

AgentFEM MCP keeps four questions separate: does the Python package build, does
the MCP protocol work, can it drive a real solver, and did that particular
scientific result satisfy a verification contract?

## Version 0.1.0

Accepted on 2026-09-15:

- Python 3.11 and 3.12 unit-test matrix defined in CI;
- lint, four unit/contract tests, wheel and source-distribution builds passed;
- MCP `server.json` passed the official 2025-12-11 Registry schema;
- the Codex plugin manifest and AgentFEM workflow Skill passed their validators;
- a separate stdio process exposed exactly the seven documented tools;
- the full project lifecycle completed against AgentFEM 0.3.7.dev0,
  DOLFINx 0.11.0, PETSc 3.25.2 and MPICH 5.0.1 on macOS arm64.

The real-solver smoke test created and checked the official `static-solid`
template, submitted an isolated run, observed its durable job identity, and
read the resulting `SimulationResult`. The solve completed with a relative
force-balance error of approximately `1.91e-12`, an energy-balance error of
approximately `2.55e-11`, and a complete provenance seal.

Its scientific trust level was `computed`, not `verified`, because the smoke
model did not declare an independent acceptance criterion. The adapter
preserved that distinction. This is a successful orchestration acceptance test,
not an external validation benchmark.
