# Contributing

AgentFEM MCP deliberately stays small. New tools are accepted only when they
represent a stable, reusable AgentFEM contract and cannot be expressed by an
existing tool.

Contributions should preserve these invariants:

- call documented AgentFEM CLI or public result contracts;
- never import private DOLFINx/PETSc runtime objects into the server;
- never accept arbitrary shell commands or code strings;
- restrict filesystem access to approved roots;
- keep tool results concise and structured;
- distinguish execution success from scientific verification;
- add a failure test as well as a success test.

Run `ruff check .`, `pytest`, and `python -m build` before opening a pull
request. Numerical capabilities belong in AgentFEM itself, not in this adapter.
