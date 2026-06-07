from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import DocumentChunk
from app.retrieval.chroma_store import RetrievedChunk

BM25_K1 = 1.5
BM25_B = 0.75


@dataclass(frozen=True)
class _IndexedChunk:
    row: DocumentChunk
    tokens: list[str]
    term_counts: Counter[str]


def bm25_search_document_chunks(db: Session, question: str, top_k: int = 10) -> list[RetrievedChunk]:
    rows = list(db.scalars(select(DocumentChunk).order_by(DocumentChunk.id.asc())))
    if not rows:
        return []

    query_tokens = tokenize(question)
    if not query_tokens:
        return []

    indexed_chunks = [_index_chunk(row) for row in rows]
    document_count = len(indexed_chunks)
    average_length = sum(len(chunk.tokens) for chunk in indexed_chunks) / max(document_count, 1)
    doc_frequency = _document_frequency(indexed_chunks)

    scored: list[tuple[float, DocumentChunk]] = []
    for indexed in indexed_chunks:
        score = _bm25_score(
            query_tokens=query_tokens,
            indexed=indexed,
            doc_frequency=doc_frequency,
            document_count=document_count,
            average_length=average_length,
        )
        if score > 0:
            scored.append((score, indexed.row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        RetrievedChunk(
            chroma_id=row.chroma_id,
            content=row.content,
            metadata={
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "page_number": row.page_number,
                "file_name": row.file_name,
                "title": row.title or "",
            },
            retrieval_sources=["bm25"],
            scores={"bm25": score},
        )
        for score, row in scored[: max(top_k, 1)]
    ]


def tokenize(text: str) -> list[str]:
    normalized = text.lower()
    tokens: list[str] = []

    tokens.extend(re.findall(r"[a-z0-9]+(?:[-_/][a-z0-9]+)+", normalized))
    tokens.extend(re.findall(r"[a-z]+", normalized))
    tokens.extend(re.findall(r"\d+", normalized))

    cjk_runs = re.findall(r"[\u4e00-\u9fff]+", normalized)
    for run in cjk_runs:
        tokens.extend(run)
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
        tokens.extend(run[index : index + 3] for index in range(len(run) - 2))

    return [token for token in tokens if token.strip()]


def _index_chunk(row: DocumentChunk) -> _IndexedChunk:
    text = " ".join(filter(None, [row.file_name, row.title or "", row.content]))
    tokens = tokenize(text)
    return _IndexedChunk(row=row, tokens=tokens, term_counts=Counter(tokens))


def _document_frequency(indexed_chunks: list[_IndexedChunk]) -> Counter[str]:
    frequency: Counter[str] = Counter()
    for indexed in indexed_chunks:
        frequency.update(set(indexed.tokens))
    return frequency


def _bm25_score(
    query_tokens: list[str],
    indexed: _IndexedChunk,
    doc_frequency: Counter[str],
    document_count: int,
    average_length: float,
) -> float:
    score = 0.0
    doc_length = max(len(indexed.tokens), 1)
    for token in query_tokens:
        term_frequency = indexed.term_counts.get(token, 0)
        if term_frequency <= 0:
            continue

        frequency = doc_frequency.get(token, 0)
        idf = math.log(1 + (document_count - frequency + 0.5) / (frequency + 0.5))
        denominator = term_frequency + BM25_K1 * (
            1 - BM25_B + BM25_B * doc_length / max(average_length, 1)
        )
        score += idf * (term_frequency * (BM25_K1 + 1)) / denominator
    return score
