"""
Recursive character-based text chunker with configurable size and overlap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..core import get_settings


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


class Chunker:
    def __init__(self):
        settings = get_settings()
        self._size = settings.chunk_size
        self._overlap = settings.chunk_overlap
        self._separators = ["\n\n", "\n", ". ", " ", ""]

    def split(self, text: str, metadata: dict | None = None) -> List[Chunk]:
        meta = metadata or {}
        raw_chunks = self._recursive_split(text, self._separators)
        chunks = []
        for i, c in enumerate(raw_chunks):
            if c.strip():
                chunks.append(Chunk(text=c.strip(), metadata={**meta, "chunk_index": i}))
        return chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self._size:
            return [text]

        sep = separators[0]
        if sep == "" or sep not in text:
            if len(separators) > 1:
                return self._recursive_split(text, separators[1:])
            # Hard split
            return self._hard_split(text)

        parts = text.split(sep)
        chunks: List[str] = []
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= self._size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > self._size and len(separators) > 1:
                    chunks.extend(self._recursive_split(part, separators[1:]))
                else:
                    current = part

        if current:
            chunks.append(current)

        # Apply overlap
        return self._apply_overlap(chunks)

    def _hard_split(self, text: str) -> List[str]:
        return [text[i: i + self._size] for i in range(0, len(text), self._size - self._overlap)]

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        if self._overlap == 0 or len(chunks) < 2:
            return chunks
        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-self._overlap:]
            result.append(prev_tail + " " + chunks[i])
        return result
