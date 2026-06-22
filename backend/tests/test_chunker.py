"""Tests for the text chunker."""
import os
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

from backend.rag.chunker import Chunker


def test_short_text_returns_single_chunk():
    chunker = Chunker()
    chunks = chunker.split("Hello world")
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world"


def test_long_text_splits():
    chunker = Chunker()
    long_text = "word " * 400  # ~2000 chars
    chunks = chunker.split(long_text)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= chunker._size + chunker._overlap + 10


def test_metadata_propagated():
    chunker = Chunker()
    chunks = chunker.split("Some text", metadata={"source": "test.txt"})
    assert chunks[0].metadata["source"] == "test.txt"
    assert "chunk_index" in chunks[0].metadata


def test_empty_text_returns_no_chunks():
    chunker = Chunker()
    chunks = chunker.split("   \n\n   ")
    assert len(chunks) == 0
