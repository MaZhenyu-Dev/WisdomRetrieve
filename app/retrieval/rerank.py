from __future__ import annotations

from app.llm.qwen import QwenClientError, rerank_documents
from app.retrieval.chroma_store import RetrievedChunk


def rerank_retrieved_chunks(
    question: str,
    chunks: list[RetrievedChunk],
    top_k: int = 5,
) -> list[RetrievedChunk]:
    if not chunks:
        return []

    limit = min(max(top_k, 1), len(chunks))
    try:
        results = rerank_documents(
            query=question,
            documents=[chunk.content for chunk in chunks],
            top_n=limit,
        )
    except QwenClientError:
        return chunks[:limit]

    selected: list[RetrievedChunk] = []
    seen_indexes: set[int] = set()
    for result in results:
        if result.index < 0 or result.index >= len(chunks) or result.index in seen_indexes:
            continue
        chunk = chunks[result.index]
        chunk.rerank_score = result.relevance_score
        chunk.scores["rerank"] = result.relevance_score
        if "rerank" not in chunk.retrieval_sources:
            chunk.retrieval_sources.append("rerank")
        selected.append(chunk)
        seen_indexes.add(result.index)
        if len(selected) >= limit:
            return selected

    for index, chunk in enumerate(chunks):
        if index not in seen_indexes:
            selected.append(chunk)
        if len(selected) >= limit:
            break
    return selected
