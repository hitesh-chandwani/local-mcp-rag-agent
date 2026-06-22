"""
Pydantic request/response models for the REST API.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    history: List[ChatMessage] = Field(default_factory=list)
    session_id: Optional[str] = None
    stream: bool = False


class ToolCallInfo(BaseModel):
    tool: str
    arguments: Dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[str] = []
    tool_calls: List[ToolCallInfo] = []
    iterations: int = 1


# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    source: str
    chunks: int
    ids: List[str]


class IngestDirectoryRequest(BaseModel):
    directory: str
    recursive: bool = True


# ── MCP ───────────────────────────────────────────────────────────────────────

class MCPServerConfig(BaseModel):
    name: str
    transport: str = "sse"
    url: Optional[str] = None
    command: Optional[str] = None
    args: List[str] = []
    headers: Dict[str, str] = {}
    env: Optional[Dict[str, str]] = None


class MCPServerStatus(BaseModel):
    name: str
    connected: bool
    transport: str
    tool_count: int
    tools: List[str]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    vector_db: str
    llm_provider: str
    mcp_servers: int
    document_count: int
