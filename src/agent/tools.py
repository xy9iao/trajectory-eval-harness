"""MCP client wiring: spawn the stdio server and expose its tools as LangChain tools (GUIDE §5).

Lifecycle note (the pitfall): with langchain-mcp-adapters 0.3.0, MultiServerMCPClient is built once
and `await client.get_tools()` returns tools that open a short-lived stdio session per call — fine
for a single run. For eval-at-scale (Phase 3), hold one `client.session(...)` open and bind tools to
it so we don't spawn a subprocess per tool call. Keep the client alive while the tools are in use.
"""
from __future__ import annotations

import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


def make_mcp_client() -> MultiServerMCPClient:
    """Client that launches src/mcp/server.py over stdio using THIS venv's interpreter.

    The server subprocess inherits the parent's working directory (the project root), so
    `-m src.mcp.server` resolves the package.
    """
    return MultiServerMCPClient(
        {
            "triage": {
                "command": sys.executable,
                "args": ["-m", "src.mcp.server"],
                "transport": "stdio",
            }
        }
    )


async def load_triage_tools(client: MultiServerMCPClient | None = None):
    """Discover the 4 triage tools. Keep the returned client alive while the tools are in use."""
    client = client or make_mcp_client()
    return await client.get_tools()
