"""Retrieval over the rules/sources vector database built by rag/build_vector_db.py.

The database is a local ChromaDB store checked out of the repo at rag/chroma_db/
(gitignored, rebuilt via `python rag/build_vector_db.py`). It has two collections:
``rules`` (one document per seeded rule) and ``sources`` (chunked scraped guidance
pages). This module only does retrieval — no Anthropic calls — so it works even
when AI assist is not configured.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb

CHROMA_DIR = Path(__file__).resolve().parents[3] / "rag" / "chroma_db"
_REQUIRED_COLLECTIONS = {"rules", "sources"}


@lru_cache(maxsize=1)
def _get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def vector_db_available() -> bool:
    """True if the persistent store exists and both collections are present."""
    if not CHROMA_DIR.exists():
        return False
    try:
        names = {c.name for c in _get_client().list_collections()}
    except Exception:
        return False
    return _REQUIRED_COLLECTIONS.issubset(names)


def collection_counts() -> tuple[int, int]:
    """Returns (rule_count, source_chunk_count). Caller must check availability first."""
    client = _get_client()
    return client.get_collection("rules").count(), client.get_collection("sources").count()


def retrieve_excerpt_for_source(query: str, source_url: str, *, n: int = 2) -> list[dict[str, Any]]:
    """Semantic search restricted to chunks of one specific source page.

    Used to ground an AI explanation of a triggered rule in the actual text of
    the official page it cites, rather than only the rule's own description.
    Returns an empty list if the vector DB is unavailable or the URL has no
    scraped chunks (e.g. it was added after the last `build_vector_db.py` run)
    — callers must treat this as a best-effort enrichment, not a dependency.
    """
    if not vector_db_available():
        return []
    try:
        result = _get_client().get_collection("sources").query(
            query_texts=[query], n_results=n, where={"url": source_url},
        )
    except Exception:
        return []
    if not result["documents"][0]:
        return []
    return [
        {"document": doc, **meta}
        for doc, meta in zip(result["documents"][0], result["metadatas"][0])
    ]


def retrieve_context(question: str, *, n_rules: int = 5, n_chunks: int = 6) -> dict[str, list[dict[str, Any]]]:
    """Semantic search over both collections for the given question."""
    client = _get_client()

    rule_result = client.get_collection("rules").query(query_texts=[question], n_results=n_rules)
    chunk_result = client.get_collection("sources").query(query_texts=[question], n_results=n_chunks)

    rules = [
        {"document": doc, **meta}
        for doc, meta in zip(rule_result["documents"][0], rule_result["metadatas"][0])
    ]
    chunks = [
        {"document": doc, **meta}
        for doc, meta in zip(chunk_result["documents"][0], chunk_result["metadatas"][0])
    ]
    return {"rules": rules, "chunks": chunks}
