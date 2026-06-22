# local-mcp-rag-agent

A **local-first**, open-source AI agent that combines **RAG** (Retrieval-Augmented Generation) with **MCP** (Model Context Protocol) tool calling — all in a single Docker Compose stack.

```
┌──────────────────────────────────────────────────────────────┐
│                     Next.js Chat UI (port 3000)              │
│  ┌────────────────────────┐  ┌────────────────────────────┐  │
│  │      Chat Interface    │  │    Config Panel            │  │
│  │  (streaming SSE)       │  │  (MCP servers + docs)      │  │
│  └────────────────────────┘  └────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST / SSE
┌──────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend (port 8000)                 │
│                                                              │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│   │  ReAct Agent │   │  RAG Pipeline│   │  MCP Client  │   │
│   │  Orchestrator│◄──┤  ChromaDB /  │   │  SSE + stdio │   │
│   │              │   │  LanceDB     │   │  transport   │   │
│   └──────┬───────┘   └──────────────┘   └──────┬───────┘   │
│          │                                       │           │
│   ┌──────▼───────────────────────────────────────▼───────┐  │
│   │           LLM Client (OpenAI / Anthropic / Grok /    │  │
│   │                        Ollama)                       │  │
│   └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Features

- **ReAct-style agent loop** — reason, call a tool, observe, repeat (up to N iterations)
- **MCP tool support** — connects to any MCP server over SSE (HTTP) or stdio; auto-discovers tools
- **Local RAG** — ingest `.txt`, `.md`, `.pdf`, `.html` files; stores embeddings in ChromaDB or LanceDB
- **Multi-provider LLM** — plug in OpenAI, Anthropic, Grok, or a local Ollama model via one env var
- **Streaming** — token-by-token SSE streaming to the UI
- **Clean chat UI** — dark-mode Next.js app with inline Markdown, source citations, tool-call inspector
- **One-command startup** — `docker compose up`
- **Fully local** — no cloud services required when using Ollama + local embedding model

## Quick Start

### Option A — Docker Compose (recommended)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/local-mcp-rag-agent.git
cd local-mcp-rag-agent

# 2. Configure
cp .env.example .env
# Edit .env — at minimum set LLM_PROVIDER and the matching API key

# 3. Run
docker compose up
```

Open [http://localhost:3000](http://localhost:3000) — the UI is ready.

### Option B — Local dev (no Docker)

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # edit as needed
uvicorn backend.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## Configuration

All settings live in `.env` (copy from `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` \| `anthropic` \| `grok` \| `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for the selected provider |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=anthropic` |
| `GROK_API_KEY` | — | Required when `LLM_PROVIDER=grok` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `VECTOR_DB` | `chroma` | `chroma` \| `lancedb` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Any sentence-transformers model |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `RETRIEVAL_TOP_K` | `5` | Chunks returned per query |

### Using Ollama (fully offline)

```bash
# Pull a model
ollama pull llama3

# Set in .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_BASE_URL=http://host.docker.internal:11434  # inside Docker
```

## MCP Server Setup

Edit `mcp_servers.json` to connect MCP servers:

```json
{
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    {
      "name": "github",
      "transport": "sse",
      "url": "http://localhost:3001",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
    }
  ]
}
```

You can also add/remove servers at runtime via the Config Panel in the UI or via the REST API.

### Available MCP transports

| Transport | When to use |
|---|---|
| `sse` | Remote HTTP server — point `url` at any MCP SSE endpoint |
| `stdio` | Local process — `command` + `args` launches it as a subprocess |

## Ingesting Documents

**Via UI** — open the Config Panel (gear icon) → Documents → upload files.

**Via API**
```bash
# Upload a file
curl -X POST http://localhost:8000/api/v1/ingest/file \
  -F "file=@my-notes.pdf"

# Ingest raw text
curl -X POST http://localhost:8000/api/v1/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "source": "my-doc"}'

# Ingest a directory on the server
curl -X POST http://localhost:8000/api/v1/ingest/directory \
  -H "Content-Type: application/json" \
  -d '{"directory": "/app/data/docs", "recursive": true}'
```

**Supported formats:** `.txt`, `.md`, `.pdf`, `.html`

## REST API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/chat` | Send a message; supports streaming |
| `POST` | `/api/v1/ingest/text` | Ingest raw text |
| `POST` | `/api/v1/ingest/file` | Upload a file |
| `POST` | `/api/v1/ingest/directory` | Ingest a server-side directory |
| `DELETE` | `/api/v1/documents` | Clear all documents |
| `GET` | `/api/v1/mcp/servers` | List MCP servers |
| `POST` | `/api/v1/mcp/servers` | Add an MCP server |
| `DELETE` | `/api/v1/mcp/servers/{name}` | Remove an MCP server |
| `GET` | `/api/v1/mcp/tools` | List all tools from all servers |
| `GET` | `/api/v1/health` | Health + stats |

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure

```
local-mcp-rag-agent/
├── backend/
│   ├── core/            # Config (pydantic-settings) + structured logging
│   ├── llm/             # Multi-provider LLM client (OpenAI / Anthropic / Grok / Ollama)
│   ├── mcp/             # MCP client (SSE + stdio), registry, auto-discovery
│   ├── rag/             # Embeddings, chunker, ingestor, retriever, vector store
│   ├── agent/           # ReAct orchestrator + prompts
│   ├── api/             # FastAPI routes, models, server factory
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/         # Next.js app router
│       ├── components/  # ChatInterface, MessageBubble, ConfigPanel, …
│       ├── hooks/       # useChat, useMCPServers
│       ├── lib/         # api.ts (typed fetch wrappers)
│       └── types/       # Shared TypeScript types
├── docs/                # Architecture + guides
├── mcp_servers.json     # MCP server config
├── docker-compose.yml
├── .env.example
└── README.md
```

## Adding a New LLM Provider

1. Create a new adapter class in `backend/llm/client.py` that extends `BaseLLMAdapter`
2. Implement `chat()` and `stream()`
3. Add the provider to the `_ADAPTERS` dict
4. Add the provider name to the `Literal` type in `backend/core/config.py`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs are welcome!

Areas where contributions are especially appreciated:
- New LLM provider adapters
- New vector store backends
- MCP server examples / integrations
- UI improvements
- Test coverage

## License

MIT — see [LICENSE](LICENSE).
