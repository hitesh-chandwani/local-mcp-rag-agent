"""
Unified LLM client that abstracts OpenAI, Anthropic, Grok, and Ollama.
Add a new provider by subclassing BaseLLMAdapter.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel

from ..core import get_logger, get_settings

logger = get_logger(__name__)


class LLMMessage(BaseModel):
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class LLMResponse(BaseModel):
    content: str
    model: str
    finish_reason: str = "stop"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Dict[str, int] = {}


# ── Adapters ─────────────────────────────────────────────────────────────────

class BaseLLMAdapter(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]: ...


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self):
        from openai import AsyncOpenAI
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens

    async def chat(self, messages, tools=None, temperature=None, max_tokens=None) -> LLMResponse:
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "temperature": temperature or self._temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = await self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        msg = choice.message
        return LLMResponse(
            content=msg.content or "",
            model=resp.model,
            finish_reason=choice.finish_reason,
            tool_calls=[tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None,
            usage=dict(resp.usage) if resp.usage else {},
        )

    async def stream(self, messages, temperature=None, max_tokens=None) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[m.model_dump(exclude_none=True) for m in messages],
            temperature=temperature or self._temperature,
            max_tokens=max_tokens or self._max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class AnthropicAdapter(BaseLLMAdapter):
    def __init__(self):
        import anthropic
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens

    async def chat(self, messages, tools=None, temperature=None, max_tokens=None) -> LLMResponse:
        system_msg = next((m.content for m in messages if m.role == "system"), None)
        user_msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]

        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": user_msgs,
            "temperature": temperature or self._temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        if system_msg:
            kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = tools

        resp = await self._client.messages.create(**kwargs)
        content = next((b.text for b in resp.content if hasattr(b, "text")), "")
        return LLMResponse(
            content=content,
            model=resp.model,
            finish_reason=resp.stop_reason or "stop",
        )

    async def stream(self, messages, temperature=None, max_tokens=None) -> AsyncIterator[str]:
        system_msg = next((m.content for m in messages if m.role == "system"), None)
        user_msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": user_msgs,
            "temperature": temperature or self._temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        if system_msg:
            kwargs["system"] = system_msg
        async with self._client.messages.stream(**kwargs) as s:
            async for text in s.text_stream:
                yield text


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for local Ollama models (no API key required)."""

    def __init__(self):
        import httpx
        settings = get_settings()
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens
        self._http = httpx.AsyncClient(timeout=120)

    async def chat(self, messages, tools=None, temperature=None, max_tokens=None) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature or self._temperature,
                "num_predict": max_tokens or self._max_tokens,
            },
        }
        resp = await self._http.post(f"{self._base_url}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            content=data["message"]["content"],
            model=self._model,
            finish_reason="stop",
        )

    async def stream(self, messages, temperature=None, max_tokens=None) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature or self._temperature},
        }
        async with self._http.stream("POST", f"{self._base_url}/api/chat", json=payload) as resp:
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content


class GrokAdapter(OpenAIAdapter):
    """Grok uses an OpenAI-compatible API."""

    def __init__(self):
        from openai import AsyncOpenAI
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.grok_api_key,
            base_url="https://api.x.ai/v1",
        )
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens


# ── Factory ──────────────────────────────────────────────────────────────────

_ADAPTERS: Dict[str, type] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "ollama": OllamaAdapter,
    "grok": GrokAdapter,
}


class LLMClient:
    """High-level LLM client – get one via dependency injection."""

    def __init__(self):
        settings = get_settings()
        provider = settings.llm_provider
        adapter_cls = _ADAPTERS.get(provider)
        if not adapter_cls:
            raise ValueError(f"Unknown LLM provider '{provider}'. Choose from: {list(_ADAPTERS)}")
        self._adapter: BaseLLMAdapter = adapter_cls()
        logger.info("llm_client_ready", provider=provider, model=settings.llm_model)

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        return await self._adapter.chat(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)

    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        return self._adapter.stream(messages, temperature=temperature, max_tokens=max_tokens)
