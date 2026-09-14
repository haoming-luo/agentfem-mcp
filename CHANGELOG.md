# Changelog

## Unreleased

- Desktop MCPB connection bundle and pinned, unprivileged discovery container.
- Validation now separates process success from scientific acceptance, and a
  run starts only when both pass.
- Long-run stdout and stderr spill to disk after a bounded in-memory buffer;
  durable job records retain only compact tails and truncation status.
- Release-contract tests keep the Python package, Registry record, MCPB, and
  discovery image versions aligned.

## 0.1.0 — 2026-09-15

- First official AgentFEM MCP boundary.
- Seven compact project, execution, and result tools.
- Approved-root path policy and shell-free execution.
- Detached serial/MPI jobs with durable status records.
- Codex plugin and AgentFEM workflow skill.
