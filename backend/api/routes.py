"""
FastAPI route handlers.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from .models import (
    ChatRequest, ChatResponse, ToolCallInfo,
    IngestTextRequest, IngestResponse, IngestDirectoryRequest,
    MCPServerConfig, MCPServerStatus,
    HealthResponse,
)
from ..agent import AgentOrchestrator
from ..mcp import MCPToolRegistry
from ..rag import Ingestor
from ..rag.vectordb import get_vector_store
from ..core import get_logger, get_settings

logger = get_logger(__name__)
router = APIRouter()


# ── Dependency providers ──────────────────────────────────────────────────────

def get_orchestrator(request: Any) -> AgentOrchestrator:
    return request.app.state.orchestrator


def get_registry(request: Any) -> MCPToolRegistry:
    return request.app.state.mcp_registry


def get_ingestor() -> Ingestor:
    return Ingestor()


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Any,
):
    orchestrator: AgentOrchestrator = get_orchestrator(request)
    history = [{"role": m.role, "content": m.content} for m in body.history]

    if body.stream:
        async def event_stream():
            async for token in await orchestrator.stream(
                query=body.query,
                chat_history=history,
                session_id=body.session_id,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    result = await orchestrator.run(
        query=body.query,
        chat_history=history,
        session_id=body.session_id,
    )
    return ChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
        sources=result["sources"],
        tool_calls=[ToolCallInfo(**tc) for tc in result["tool_calls"]],
        iterations=result["iterations"],
    )


# ── Ingest ────────────────────────────────────────────────────────────────────

@router.post("/ingest/text", response_model=IngestResponse)
async def ingest_text(body: IngestTextRequest):
    ingestor = get_ingestor()
    result = ingestor.ingest_text(body.text, source=body.source, extra_metadata=body.metadata)
    return IngestResponse(**result)


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    import tempfile, os
    suffix = os.path.splitext(file.filename or "upload")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        ingestor = get_ingestor()
        result = ingestor.ingest_file(tmp_path, extra_metadata={"source": file.filename})
        result["source"] = file.filename or result["source"]
        return IngestResponse(**result)
    finally:
        os.unlink(tmp_path)


@router.post("/ingest/directory", response_model=list)
async def ingest_directory(body: IngestDirectoryRequest):
    ingestor = get_ingestor()
    results = ingestor.ingest_directory(body.directory, recursive=body.recursive)
    return results


@router.delete("/documents")
async def clear_documents():
    store = get_vector_store()
    store.reset()
    return {"message": "All documents cleared"}


# ── MCP Servers ───────────────────────────────────────────────────────────────

@router.get("/mcp/servers", response_model=list)
async def list_mcp_servers(request: Any):
    registry: MCPToolRegistry = get_registry(request)
    return registry.status()


@router.post("/mcp/servers")
async def add_mcp_server(body: MCPServerConfig, request: Any):
    registry: MCPToolRegistry = get_registry(request)
    client = registry.add_server(body.model_dump())
    try:
        await client.connect()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to connect: {exc}")
    return {"message": f"Server '{body.name}' connected", "tools": len(client.tools)}


@router.delete("/mcp/servers/{name}")
async def remove_mcp_server(name: str, request: Any):
    registry: MCPToolRegistry = get_registry(request)
    registry.remove_server(name)
    return {"message": f"Server '{name}' removed"}


@router.get("/mcp/tools")
async def list_all_tools(request: Any):
    registry: MCPToolRegistry = get_registry(request)
    return registry.list_all_tools()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health(request: Any):
    settings = get_settings()
    registry: MCPToolRegistry = get_registry(request)
    store = get_vector_store()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        vector_db=settings.vector_db,
        llm_provider=settings.llm_provider,
        mcp_servers=len([s for s in registry.status() if s["connected"]]),
        document_count=store.count(),
    )
