"""Embedding model factory (Phase 15).

Embeddings turn text into vectors that capture meaning. We use a local, free
Ollama embedding model so RAG stays $0 and offline.
"""

from __future__ import annotations

from langchain_ollama import OllamaEmbeddings

from app.core.config import settings


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_HOST,
    )
