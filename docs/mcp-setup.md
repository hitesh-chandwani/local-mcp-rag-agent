# MCP Server Setup Guide

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) (MCP) is an open standard that allows AI agents to call tools exposed by external servers. Each MCP server advertises a list of typed tools, and the agent can call them during a conversation.

## Configuration File

`mcp_servers.json` at the project root is loaded on startup. It follows this schema:

```json
{
  "servers": [
    {
      "name": "unique-server-name",
      "transport": "sse | stdio",
      ...transport-specific fields...
    }
  ]
}
```

Environment variable substitution is supported: `${MY_TOKEN}` or `${MY_TOKEN:default_value}`.

## SSE Transport

Connect to a remote (or local) HTTP MCP server:

```json
{
  "name": "github",
  "transport": "sse",
  "url": "http://localhost:3001",
  "headers": {
    "Authorization": "Bearer ${GITHUB_TOKEN}"
  },
  "timeout": 30
}
```

The server must expose:
- `GET /tools/list` → `{ "tools": [...] }`
- `POST /tools/call` with body `{ "name": "tool_name", "arguments": {...} }`

## stdio Transport

Launch a local process and communicate over stdin/stdout:

```json
{
  "name": "filesystem",
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/expose"]
}
```

The process must implement the [MCP JSON-RPC protocol](https://spec.modelcontextprotocol.io/specification/basic/transports/).

## Popular MCP Servers

| Server | Transport | Install |
|---|---|---|
| Filesystem | stdio | `npx @modelcontextprotocol/server-filesystem` |
| GitHub | stdio | `npx @modelcontextprotocol/server-github` |
| Fetch (web) | stdio | `npx @modelcontextprotocol/server-fetch` |
| Brave Search | stdio | `npx @modelcontextprotocol/server-brave-search` |
| SQLite | stdio | `npx @modelcontextprotocol/server-sqlite` |

## Adding Servers at Runtime

Via the Config Panel in the UI, or via the REST API:

```bash
curl -X POST http://localhost:8000/api/v1/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-server",
    "transport": "sse",
    "url": "http://my-server:3001"
  }'
```

## Building Your Own MCP Server

Any HTTP server that implements:
1. `GET /tools/list` returning tool descriptors with JSON Schema input schemas
2. `POST /tools/call` accepting `{name, arguments}` and returning a result

...will work with this agent. See the [MCP specification](https://spec.modelcontextprotocol.io/) for details.
