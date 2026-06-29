"""The Chroma vector store (Phase 15).

Chroma stores document embeddings on disk and does semantic (nearest-neighbor)
search. One persistent collection holds our incident knowledge base.
"""

from __future__ import annotations

from langchain_chroma import Chroma

from app.ai.embeddings import get_embeddings
from app.core.config import settings

_COLLECTION = "incident_knowledge"


def get_vector_store() -> Chroma:
    """Return the persistent Chroma vector store (created on first use)."""
    return Chroma(
        collection_name=_COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=settings.CHROMA_DIR,
    )
