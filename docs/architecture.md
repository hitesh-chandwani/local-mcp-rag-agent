# Architecture

## Overview

`local-mcp-rag-agent` is composed of two services:

- **Backend** — Python FastAPI application containing the agent, RAG pipeline, and MCP client layer
- **Frontend** — Next.js application providing the chat UI and configuration panel

## Request Lifecycle

```
User types a message
        │
        ▼
ChatInterface (React)
        │  POST /api/v1/chat  (or SSE stream)
        ▼
FastAPI route → AgentOrchestrator.run()
        │
        ├─ 1. Retrieve relevant document chunks (RAG)
        │       Retriever → EmbeddingService → VectorStore
        │
        ├─ 2. Build messages: [system prompt, history, user query + context]
        │
        ├─ 3. Call LLM with tool descriptors
        │       LLMClient → OpenAI / Anthropic / Grok / Ollama
        │
        ├─ 4. If LLM returns a tool call:
        │       MCPToolRegistry.call_tool() → MCPClient → MCP server
        │       Append tool result → loop back to step 3
        │
        └─ 5. Return final answer → stream or JSON response
```

## Agent Loop (ReAct)

The orchestrator implements a simplified ReAct (Reason + Act) loop:

```
Thought:  LLM reasons about the question and available context
Action:   LLM optionally calls a tool (MCP function call)
Observe:  Tool result is appended to the conversation
... repeat up to MAX_ITERATIONS (default: 6)
Answer:   LLM produces a final textual response
```

## RAG Pipeline

```
Document file (pdf/txt/md/html)
        │
        ▼
Ingestor.ingest_file()
        │
        ├─ _read_file()  →  raw text
        ├─ Chunker.split()  →  List[Chunk] (recursive char splitter)
        ├─ EmbeddingService.embed()  →  List[List[float]]
        └─ VectorStore.upsert()  →  persisted in ChromaDB / LanceDB

At query time:
        query → EmbeddingService.embed_one() → VectorStore.search() → top-K chunks
```

## MCP Integration

The `MCPToolRegistry` maintains a pool of `MCPClient` instances, one per server.

- **SSE transport**: HTTP POST to `/tools/call` on the remote server
- **stdio transport**: spawns a local process and communicates over JSON-RPC 2.0

Tool names are namespaced as `{server_name}__{tool_name}` to avoid collisions when multiple servers expose tools with the same name.

## Vector Store Abstraction

Both `ChromaStore` and `LanceStore` implement the `VectorStore` ABC:

```python
class VectorStore(ABC):
    def upsert(texts, embeddings, metadatas) -> List[str]: ...
    def search(query_embedding, top_k, min_score) -> List[Dict]: ...
    def delete(ids) -> None: ...
    def count() -> int: ...
    def reset() -> None: ...
```

Switch between them with `VECTOR_DB=chroma` or `VECTOR_DB=lancedb`.

## LLM Client Abstraction

All providers implement `BaseLLMAdapter`:

```python
class BaseLLMAdapter(ABC):
    async def chat(messages, tools, temperature, max_tokens) -> LLMResponse: ...
    async def stream(messages, temperature, max_tokens) -> AsyncIterator[str]: ...
```

Add new providers by subclassing and registering in the `_ADAPTERS` dict.
