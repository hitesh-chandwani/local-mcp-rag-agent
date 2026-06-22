"""
Pluggable vector store abstraction.
Supports ChromaDB (default) and LanceDB.
Switch via VECTOR_DB env var: "chroma" | "lancedb"
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..core import get_logger, get_settings

logger = get_logger(__name__)


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict]) -> List[str]: ...

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int, min_score: float) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def delete(self, ids: List[str]) -> None: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def reset(self) -> None: ...


# ── ChromaDB ─────────────────────────────────────────────────────────────────

class ChromaStore(VectorStore):
    def __init__(self):
        import chromadb
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("chroma_store_ready", collection=settings.collection_name)

    def upsert(self, texts, embeddings, metadatas) -> List[str]:
        ids = [str(uuid4()) for _ in texts]
        self._collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        return ids

    def search(self, query_embedding, top_k=5, min_score=0.35) -> List[Dict[str, Any]]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(self._collection.count(), 1)),
            include=["documents", "metadatas", "distances"],
        )
        output = []
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            score = 1.0 - dist  # cosine distance → similarity
            if score >= min_score:
                output.append({"id": results["ids"][0][i], "text": doc, "metadata": meta, "score": score})
        return sorted(output, key=lambda x: x["score"], reverse=True)

    def delete(self, ids: List[str]) -> None:
        self._collection.delete(ids=ids)

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.create_collection(name, metadata={"hnsw:space": "cosine"})


# ── LanceDB ───────────────────────────────────────────────────────────────────

class LanceStore(VectorStore):
    def __init__(self):
        import lancedb
        import pyarrow as pa
        settings = get_settings()
        self._db = lancedb.connect(settings.lancedb_uri)
        self._table_name = settings.collection_name
        self._schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float32())),
            pa.field("source", pa.string()),
        ])
        if self._table_name not in self._db.table_names():
            self._table = self._db.create_table(self._table_name, schema=self._schema)
        else:
            self._table = self._db.open_table(self._table_name)
        logger.info("lancedb_store_ready", table=self._table_name)

    def upsert(self, texts, embeddings, metadatas) -> List[str]:
        import pyarrow as pa
        ids = [str(uuid4()) for _ in texts]
        records = [
            {"id": i, "text": t, "vector": e, "source": m.get("source", "")}
            for i, t, e, m in zip(ids, texts, embeddings, metadatas)
        ]
        self._table.add(records)
        return ids

    def search(self, query_embedding, top_k=5, min_score=0.35) -> List[Dict[str, Any]]:
        results = (
            self._table.search(query_embedding)
            .limit(top_k)
            .to_list()
        )
        output = []
        for r in results:
            score = 1.0 - r.get("_distance", 1.0)
            if score >= min_score:
                output.append({"id": r["id"], "text": r["text"], "metadata": {"source": r.get("source", "")}, "score": score})
        return output

    def delete(self, ids: List[str]) -> None:
        for i in ids:
            self._table.delete(f"id = '{i}'")

    def count(self) -> int:
        return len(self._table)

    def reset(self) -> None:
        self._db.drop_table(self._table_name)
        self._table = self._db.create_table(self._table_name, schema=self._schema)


# ── Factory ───────────────────────────────────────────────────────────────────

_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _store_instance
    if _store_instance is None:
        settings = get_settings()
        if settings.vector_db == "lancedb":
            _store_instance = LanceStore()
        else:
            _store_instance = ChromaStore()
    return _store_instance
