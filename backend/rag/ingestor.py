"""
Document ingestor: reads files, chunks them, embeds, and stores in the vector DB.
Supports: .txt, .md, .pdf, .html
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from .chunker import Chunk, Chunker
from .embeddings import get_embedding_service
from .vectordb import get_vector_store
from ..core import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".html"}


def _read_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == ".html":
        from bs4 import BeautifulSoup
        with path.open(encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        return soup.get_text(separator="\n")
    with path.open(encoding="utf-8", errors="replace") as f:
        return f.read()


class Ingestor:
    def __init__(self):
        self._chunker = Chunker()
        self._embeddings = get_embedding_service()
        self._store = get_vector_store()

    def ingest_file(self, file_path: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {path.suffix}. Supported: {SUPPORTED_EXTENSIONS}")

        logger.info("ingesting_file", path=str(path))
        text = _read_file(path)
        file_hash = hashlib.md5(text.encode()).hexdigest()

        metadata = {
            "source": path.name,
            "source_path": str(path),
            "file_hash": file_hash,
            **(extra_metadata or {}),
        }

        return self._process_text(text, metadata, source_id=path.stem)

    def ingest_text(self, text: str, source: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        metadata = {"source": source, **(extra_metadata or {})}
        return self._process_text(text, metadata, source_id=source)

    def _process_text(self, text: str, metadata: Dict, source_id: str) -> Dict[str, Any]:
        chunks: List[Chunk] = self._chunker.split(text, metadata)
        if not chunks:
            return {"source": source_id, "chunks": 0, "ids": []}

        texts = [c.text for c in chunks]
        metas = [c.metadata for c in chunks]

        vectors = self._embeddings.embed(texts)
        ids = self._store.upsert(texts, vectors, metas)

        logger.info("ingestion_complete", source=source_id, chunks=len(chunks))
        return {"source": source_id, "chunks": len(chunks), "ids": ids}

    def ingest_directory(self, directory: str, recursive: bool = True) -> List[Dict[str, Any]]:
        base = Path(directory)
        if not base.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        glob = "**/*" if recursive else "*"
        results = []
        for file_path in base.glob(glob):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    result = self.ingest_file(str(file_path))
                    results.append(result)
                except Exception as exc:
                    logger.error("ingest_file_failed", path=str(file_path), error=str(exc))
        return results
