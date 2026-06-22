"""
Embedding service using sentence-transformers (runs fully locally).
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from ..core import get_logger, get_settings

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self._model_name = settings.embedding_model
        self._device = settings.embedding_device
        self._model = None  # lazy-load

    def _ensure_loaded(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("loading_embedding_model", model=self._model_name, device=self._device)
            self._model = SentenceTransformer(self._model_name, device=self._device)

    def embed(self, texts: List[str]) -> List[List[float]]:
        self._ensure_loaded()
        vectors = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        self._ensure_loaded()
        return self._model.get_sentence_embedding_dimension()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
