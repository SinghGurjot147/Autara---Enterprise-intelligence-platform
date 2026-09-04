"""Bridge PPT RAG mode to the existing project RAG pipeline.

This deliberately calls the existing `rag.query.run_rag` instead of creating
another vector/BM25/embedding pipeline.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("presentations.rag_context")

@dataclass
class RetrievedChunk:
    text: str
    document: str
    page: int | None = None

def retrieve_context(query: str, document_ids: list[str], top_k: int = 12) -> tuple[list[RetrievedChunk], list[str]]:
    warnings: list[str] = []
    try:
        from rag.query import run_rag
        result = run_rag(query)
        answer = (result.get("answer") or "").strip()
        sources = result.get("sources") or []
        if not answer:
            warnings.append("Existing RAG returned no usable context; generated from the topic alone.")
            return [], warnings
        # Preserve the existing RAG answer as grounded context. The planner is
        # explicitly instructed to use only this material for factual claims.
        chunks = []
        if sources:
            for src in sources[:top_k]:
                chunks.append(RetrievedChunk(
                    text=answer,
                    document=str(src.get("source", "Knowledge Base")),
                    page=src.get("page"),
                ))
        else:
            chunks.append(RetrievedChunk(text=answer, document="Knowledge Base", page=None))
        return chunks, warnings
    except Exception as e:
        logger.warning("Existing RAG retrieval failed: %s", e)
        warnings.append(f"Document retrieval failed ({e}) â€” generated from the topic alone.")
        return [], warnings

