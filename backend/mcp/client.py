"""
MCP client supporting both SSE (HTTP) and stdio transport.

Each MCPClient wraps a single MCP server connection. The registry holds
multiple clients, one per configured server.
"""
from __future__ import annotations

import asyncio
import json
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from ..core import get_logger

logger = get_logger(__name__)


class Transport(str, Enum):
    SSE = "sse"
    STDIO = "stdio"


class MCPToolCall(Exception):
    """Raised to signal the agent should call an MCP tool."""


class MCPClient:
    """
    Thin async MCP client.

    For SSE servers: calls /tools/list and /tools/call over HTTP.
    For stdio servers: spawns the process and communicates via JSON-RPC.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.transport = Transport(config.get("transport", "sse"))
        self.config = config
        self._tools: List[Dict[str, Any]] = []
        self._ready = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def connect(self) -> None:
        if self.transport == Transport.SSE:
            await self._connect_sse()
        else:
            await self._connect_stdio()
        self._ready = True
        logger.info("mcp_connected", server=self.name, transport=self.transport, tools=len(self._tools))

    async def disconnect(self) -> None:
        if self.transport == Transport.STDIO and hasattr(self, "_process"):
            self._process.terminate()
            await self._process.wait()
        self._ready = False

    # ── SSE transport ─────────────────────────────────────────────────────

    async def _connect_sse(self) -> None:
        url = self.config["url"].rstrip("/")
        timeout = self.config.get("timeout", 30)
        headers = self.config.get("headers", {})

        async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
            resp = await client.get(f"{url}/tools/list")
            resp.raise_for_status()
            data = resp.json()
            self._tools = data.get("tools", [])
            self._base_url = url
            self._headers = headers
            self._timeout = timeout

    async def _call_tool_sse(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/tools/call",
                json={"name": tool_name, "arguments": arguments},
            )
            resp.raise_for_status()
            return resp.json()

    # ── stdio transport ───────────────────────────────────────────────────

    async def _connect_stdio(self) -> None:
        cmd = self.config["command"]
        args = self.config.get("args", [])
        env = self.config.get("env", None)

        self._process = await asyncio.create_subprocess_exec(
            cmd,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._req_id = 0

        # Send initialize
        await self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}})
        result = await self._rpc("tools/list", {})
        self._tools = result.get("tools", [])

    async def _rpc(self, method: str, params: Dict) -> Any:
        self._req_id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self._req_id, "method": method, "params": params})
        self._process.stdin.write((payload + "\n").encode())
        await self._process.stdin.drain()

        line = await self._process.stdout.readline()
        data = json.loads(line.decode().strip())
        if "error" in data:
            raise RuntimeError(f"MCP RPC error: {data['error']}")
        return data.get("result", {})

    async def _call_tool_stdio(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        return await self._rpc("tools/call", {"name": tool_name, "arguments": arguments})

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def tools(self) -> List[Dict[str, Any]]:
        return self._tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not self._ready:
            raise RuntimeError(f"MCP client '{self.name}' not connected")
        logger.info("mcp_tool_call", server=self.name, tool=tool_name)
        if self.transport == Transport.SSE:
            return await self._call_tool_sse(tool_name, arguments)
        return await self._call_tool_stdio(tool_name, arguments)

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        """Convert MCP tool descriptors to OpenAI function-calling format."""
        result = []
        for tool in self._tools:
            result.append({
                "type": "function",
                "function": {
                    "name": f"{self.name}__{tool['name']}",
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
                },
            })
        return result
