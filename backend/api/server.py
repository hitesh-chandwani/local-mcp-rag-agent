"""
FastAPI application factory with lifespan management.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from ..agent import AgentOrchestrator
from ..mcp import MCPToolRegistry
from ..core import get_logger, get_settings, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info("app_starting", version=settings.app_version, env=settings.environment)

    # Boot MCP registry
    registry = MCPToolRegistry()
    await registry.load_and_connect()
    app.state.mcp_registry = registry

    # Boot agent (LLM + retriever share the registry)
    from ..llm import LLMClient
    from ..rag import Retriever
    app.state.orchestrator = AgentOrchestrator(
        llm=LLMClient(),
        retriever=Retriever(),
        mcp_registry=registry,
    )

    logger.info("app_ready", mcp_servers=len(registry.status()))
    yield

    # Shutdown
    await registry.disconnect_all()
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="local-mcp-rag-agent",
        description="Local-first RAG agent with MCP tool support",
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "name": "local-mcp-rag-agent",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return app
