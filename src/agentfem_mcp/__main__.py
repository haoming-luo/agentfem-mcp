"""Run AgentFEM MCP over a local stdio transport."""

from __future__ import annotations

import argparse
import os


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agentfem-mcp",
        description="Expose an installed AgentFEM runtime to MCP-compatible AI agents.",
    )
    parser.add_argument(
        "--root",
        action="append",
        help="Approved project root. Repeat to allow multiple roots.",
    )
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args(argv)
    if args.version:
        from . import __version__

        print(f"AgentFEM MCP {__version__}")
        return 0
    if args.root:
        os.environ["AGENTFEM_MCP_ROOTS"] = os.pathsep.join(args.root)
    from .server import mcp

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
