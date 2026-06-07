from __future__ import annotations

from sqlalchemy.orm import Session

from app.retrieval.bm25 import bm25_search_document_chunks
from app.retrieval.chroma_store import RetrievedChunk, query_document_chunks


def hybrid_retrieve_chunks(
    db: Session,
    question: str,
    vector_top_k: int = 10,
    bm25_top_k: int = 10,
    candidate_limit: int = 20,
) -> list[RetrievedChunk]:
    vector_chunks = query_document_chunks(
        question,
        top_k=vector_top_k,
        fetch_k=max(vector_top_k * 4, vector_top_k),
        use_mmr=True,
        lambda_param=0.7,
    )
    bm25_chunks = bm25_search_document_chunks(db, question, top_k=bm25_top_k)

    merged: dict[str, RetrievedChunk] = {}
    order: list[str] = []
    for rank, chunk in enumerate(vector_chunks, start=1):
        _merge_candidate(merged, order, chunk, rank, "vector")
    for rank, chunk in enumerate(bm25_chunks, start=1):
        _merge_candidate(merged, order, chunk, rank, "bm25")

    candidates = [merged[key] for key in order]
    _normalize_scores(candidates, "vector")
    _normalize_scores(candidates, "bm25")
    for candidate in candidates:
        candidate.scores["hybrid"] = (
            candidate.scores.get("vector_normalized", 0.0)
            + candidate.scores.get("bm25_normalized", 0.0)
            + candidate.scores.get("rrf", 0.0)
        )

    candidates.sort(key=lambda chunk: chunk.scores.get("hybrid", 0.0), reverse=True)
    return candidates[: max(candidate_limit, 1)]


def _merge_candidate(
    merged: dict[str, RetrievedChunk],
    order: list[str],
    chunk: RetrievedChunk,
    rank: int,
    source: str,
) -> None:
    key = chunk.chroma_id or _content_key(chunk)
    reciprocal_rank_score = 1.0 / (60 + rank)

    if key not in merged:
        merged[key] = chunk
        order.append(key)

    target = merged[key]
    if source not in target.retrieval_sources:
        target.retrieval_sources.append(source)
    for name, score in chunk.scores.items():
        target.scores[name] = max(target.scores.get(name, 0.0), score)
    target.scores["rrf"] = target.scores.get("rrf", 0.0) + reciprocal_rank_score


def _normalize_scores(chunks: list[RetrievedChunk], score_name: str) -> None:
    values = [chunk.scores.get(score_name, 0.0) for chunk in chunks]
    maximum = max(values, default=0.0)
    if maximum <= 0:
        return
    normalized_name = f"{score_name}_normalized"
    for chunk in chunks:
        chunk.scores[normalized_name] = chunk.scores.get(score_name, 0.0) / maximum


def _content_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata
    return "|".join(
        [
            str(metadata.get("document_id") or ""),
            str(metadata.get("page_number") or ""),
            str(metadata.get("chunk_index") or ""),
            chunk.content[:120],
        ]
    )
