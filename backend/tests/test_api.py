"""
Integration tests for the FastAPI routes.
Uses httpx test client with a mocked orchestrator and registry.
"""
import os
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_orchestrator():
    orch = AsyncMock()
    orch.run.return_value = {
        "session_id": "test-session",
        "answer": "This is a test answer.",
        "sources": ["doc1.txt"],
        "tool_calls": [],
        "iterations": 1,
    }
    return orch


@pytest.fixture
def mock_registry():
    reg = MagicMock()
    reg.status.return_value = []
    reg.list_all_tools.return_value = []
    return reg


@pytest.fixture
async def client(mock_orchestrator, mock_registry):
    from backend.api.server import create_app
    app = create_app()

    # Bypass lifespan by injecting state directly
    app.state.orchestrator = mock_orchestrator
    app.state.mcp_registry = mock_registry

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client, mock_registry):
    with patch("backend.api.routes.get_vector_store") as mock_vs:
        mock_vs.return_value.count.return_value = 42
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_chat(client, mock_orchestrator):
    resp = await client.post("/api/v1/chat", json={"query": "Hello", "history": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "This is a test answer."
    assert data["sources"] == ["doc1.txt"]


@pytest.mark.asyncio
async def test_list_mcp_servers(client, mock_registry):
    resp = await client.get("/api/v1/mcp/servers")
    assert resp.status_code == 200
    assert resp.json() == []
