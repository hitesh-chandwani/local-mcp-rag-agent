"""
ReAct-style agent orchestrator.

Loop:
  1. Retrieve relevant document context (RAG)
  2. Ask LLM – with MCP tools available – to reason and optionally call a tool
  3. If the LLM calls a tool, execute it via MCPToolRegistry and loop
  4. Once the LLM produces a final answer (no tool call), return it

Max iterations are configurable to prevent infinite loops.
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from .prompts import SYSTEM_PROMPT, build_react_prompt
from ..llm import LLMClient, LLMMessage
from ..mcp import MCPToolRegistry
from ..rag import Retriever
from ..core import get_logger, get_settings

logger = get_logger(__name__)

MAX_ITERATIONS = 6


class AgentOrchestrator:
    """
    Stateless orchestrator – create one instance per application lifetime
    and call `run()` for each user turn.
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        retriever: Optional[Retriever] = None,
        mcp_registry: Optional[MCPToolRegistry] = None,
    ):
        self._llm = llm or LLMClient()
        self._retriever = retriever or Retriever()
        self._mcp = mcp_registry or MCPToolRegistry()
        self._settings = get_settings()

    # ── Main entry-point ─────────────────────────────────────────────────

    async def run(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query and return a structured response dict.

        Args:
            query: The user's question.
            chat_history: Previous turns as [{"role": "user"|"assistant", "content": ...}].
            session_id: Optional trace ID.

        Returns:
            {
                "session_id": str,
                "answer": str,
                "sources": list[str],
                "tool_calls": list[dict],
                "iterations": int,
            }
        """
        sid = session_id or str(uuid4())
        logger.info("agent_run_start", session=sid, query_len=len(query))

        rag_results = self._retriever.retrieve(query)
        context = self._retriever.format_context(rag_results)
        sources = list({r.get("metadata", {}).get("source", "") for r in rag_results if r.get("metadata", {}).get("source")})

        messages = self._build_messages(query, context, chat_history or [])
        tools = self._mcp.list_all_tools()

        tool_calls_made: List[Dict] = []
        thoughts: List[str] = []
        final_answer = ""

        for iteration in range(1, MAX_ITERATIONS + 1):
            logger.debug("agent_iteration", session=sid, iteration=iteration)

            response = await self._llm.chat(messages, tools=tools or None)

            if response.tool_calls:
                for tc in response.tool_calls:
                    fn = tc.get("function", {})
                    tool_name = fn.get("name", "")
                    raw_args = fn.get("arguments", "{}")
                    arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                    logger.info("tool_call", session=sid, tool=tool_name, args=arguments)
                    tool_result = await self._mcp.call_tool(tool_name, arguments)
                    tool_calls_made.append({"tool": tool_name, "arguments": arguments, "result": tool_result})

                    # Feed tool result back
                    messages.append(LLMMessage(role="assistant", content="", tool_calls=response.tool_calls))
                    messages.append(LLMMessage(
                        role="tool",
                        content=json.dumps(tool_result),
                        tool_call_id=tc.get("id", ""),
                    ))
            else:
                final_answer = response.content
                thoughts.append(final_answer)
                break

        if not final_answer and thoughts:
            final_answer = thoughts[-1]

        logger.info("agent_run_complete", session=sid, iterations=iteration, sources=sources)

        return {
            "session_id": sid,
            "answer": final_answer,
            "sources": sources,
            "tool_calls": tool_calls_made,
            "iterations": iteration,
        }

    # ── Streaming variant ─────────────────────────────────────────────────

    async def stream(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Yields tokens as they arrive from the LLM.
        NOTE: Tool calling is not supported in streaming mode – the agent
        will do a single RAG-augmented LLM call.
        """
        sid = session_id or str(uuid4())
        rag_results = self._retriever.retrieve(query)
        context = self._retriever.format_context(rag_results)
        messages = self._build_messages(query, context, chat_history or [])

        async_iter = await self._llm.stream(messages)
        async for token in async_iter:
            yield token

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_messages(
        self,
        query: str,
        context: str,
        history: List[Dict[str, str]],
    ) -> List[LLMMessage]:
        msgs: List[LLMMessage] = [LLMMessage(role="system", content=SYSTEM_PROMPT)]

        for turn in history:
            msgs.append(LLMMessage(role=turn["role"], content=turn["content"]))

        user_content = build_react_prompt(query=query, context=context, iteration=1)
        msgs.append(LLMMessage(role="user", content=user_content))
        return msgs
