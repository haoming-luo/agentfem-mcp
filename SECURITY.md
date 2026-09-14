# Security policy

## Supported versions

Security fixes are applied to the latest release.

## Trust boundary

AgentFEM MCP is a local orchestration boundary for an installed scientific
runtime. It does not accept shell commands, arbitrary Python source, network
destinations, or paths outside configured project roots. Tool inputs can still
start computational work and create files inside those roots; MCP hosts should
therefore ask for approval on mutating tools.

Scientific model files are executable Python by design. Review projects from
untrusted sources before validating or running them, and use an isolated
environment when appropriate.

## Report a vulnerability

Do not disclose a suspected vulnerability in a public issue. Use GitHub's
private security advisory flow for the `haoming-luo/agentfem-mcp` repository.
Include affected versions, reproduction steps, and the expected impact. Do not
include private scientific models or results.
