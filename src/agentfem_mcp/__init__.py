"""AgentFEM's model-neutral MCP boundary."""

from ._version import __version__
from .bridge import AgentFEMBridge, BridgeError

__all__ = ["AgentFEMBridge", "BridgeError", "__version__"]
