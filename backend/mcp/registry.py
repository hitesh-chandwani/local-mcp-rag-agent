"""
MCPToolRegistry manages all connected MCP servers and provides a unified
interface for tool discovery and invocation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .client import MCPClient
from .discovery import load_mcp_config
from ..core import get_logger

logger = get_logger(__name__)


class MCPToolRegistry:
    """
    Holds one MCPClient per configured server. Provides:
    - list_all_tools()  → OpenAI-compatible tool descriptors
    - call_tool()       → routes "server__tool" calls to the right client
    - status()          → health of each server
    """

    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}

    async def load_and_connect(self, configs: Optional[List[Dict]] = None) -> None:
        """Connect to all servers from config (or auto-loaded config)."""
        server_configs = configs or load_mcp_config()
        for cfg in server_configs:
            name = cfg.get("name")
            if not name:
                logger.warning("mcp_server_missing_name", config=cfg)
                continue
            client = MCPClient(name=name, config=cfg)
            try:
                await client.connect()
                self._clients[name] = client
            except Exception as exc:
                logger.error("mcp_connect_failed", server=name, error=str(exc))

    async def disconnect_all(self) -> None:
        for client in self._clients.values():
            try:
                await client.disconnect()
            except Exception:
                pass
        self._clients.clear()

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """Return OpenAI-format tool descriptors for every connected server."""
        tools = []
        for client in self._clients.values():
            tools.extend(client.to_openai_tools())
        return tools

    def _resolve(self, qualified_name: str) -> Tuple[MCPClient, str]:
        """Resolve 'server__tool' → (client, tool_name)."""
        parts = qualified_name.split("__", 1)
        if len(parts) != 2:
            raise ValueError(f"Tool name must be 'server__tool', got: {qualified_name!r}")
        server_name, tool_name = parts
        client = self._clients.get(server_name)
        if not client:
            raise KeyError(f"No connected MCP server named '{server_name}'")
        return client, tool_name

    async def call_tool(self, qualified_name: str, arguments: Dict[str, Any]) -> Any:
        client, tool_name = self._resolve(qualified_name)
        return await client.call_tool(tool_name, arguments)

    def status(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "connected": client._ready,
                "transport": client.transport,
                "tool_count": len(client.tools),
                "tools": [t["name"] for t in client.tools],
            }
            for name, client in self._clients.items()
        ]

    def add_server(self, config: Dict[str, Any]) -> MCPClient:
        """Dynamically add a server at runtime (call connect() separately)."""
        name = config["name"]
        client = MCPClient(name=name, config=config)
        self._clients[name] = client
        return client

    def remove_server(self, name: str) -> None:
        client = self._clients.pop(name, None)
        if client:
            import asyncio
            asyncio.create_task(client.disconnect())
