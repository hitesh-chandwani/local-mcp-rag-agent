"""
Retriever: embeds a query and fetches the most relevant chunks.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .embeddings import get_embedding_service
from .vectordb import get_vector_store
from ..core import get_logger, get_settings

logger = get_logger(__name__)


class Retriever:
    def __init__(self):
        self._embeddings = get_embedding_service()
        self._store = get_vector_store()
        settings = get_settings()
        self._top_k = settings.retrieval_top_k
        self._min_score = settings.retrieval_min_score

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        k = top_k or self._top_k
        threshold = min_score if min_score is not None else self._min_score

        query_vec = self._embeddings.embed_one(query)
        results = self._store.search(query_vec, top_k=k, min_score=threshold)

        logger.debug("retrieval_done", query_len=len(query), results=len(results))
        return results

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("source", "unknown")
            parts.append(f"[{i}] (source: {source})\n{r['text']}")
        return "\n\n---\n\n".join(parts)
