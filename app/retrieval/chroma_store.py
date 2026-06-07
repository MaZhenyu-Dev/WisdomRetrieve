from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.config import get_settings
from app.database.models import DocumentChunk

if TYPE_CHECKING:
    from langchain_chroma import Chroma
    from langchain_core.documents import Document as LangChainDocument
    from langchain_core.embeddings import Embeddings
    from langchain_community.embeddings import DashScopeEmbeddings

COLLECTION_NAME = "document_chunks"


@dataclass
class RetrievedChunk:
    chroma_id: str
    content: str
    metadata: dict[str, Any]
    distance: float | None = None
    retrieval_sources: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    rerank_score: float | None = None


@lru_cache
def get_embedding_function() -> "DashScopeEmbeddings":
    try:
        from langchain_community.embeddings import DashScopeEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "langchain-community and dashscope are required for DashScope embeddings."
        ) from exc

    settings = get_settings()
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured.")
    return DashScopeEmbeddings(
        model=settings.dashscope_embedding_model,
        dashscope_api_key=settings.dashscope_api_key,
    )


@lru_cache
def get_vector_store() -> "Chroma":
    try:
        from langchain_chroma import Chroma
    except ImportError as exc:
        raise RuntimeError("langchain-chroma is required for Chroma vector store.") from exc

    settings = get_settings()
    Path(settings.chromadb_path).mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=str(settings.chromadb_path),
        collection_metadata={"hnsw:space": "cosine"},
    )


def add_document_chunks(chunks: list[DocumentChunk]) -> None:
    if not chunks:
        return

    vector_store = get_vector_store()
    vector_store.add_documents(
        documents=[_langchain_document(chunk) for chunk in chunks],
        ids=[chunk.chroma_id for chunk in chunks],
    )


def rebuild_document_chunks(chunks: list[DocumentChunk]) -> None:
    vector_store = get_vector_store()
    try:
        vector_store.delete_collection()
    except Exception:
        _delete_all_documents(vector_store)
    get_vector_store.cache_clear()
    if chunks:
        add_document_chunks(chunks)
    else:
        get_vector_store()


def delete_document_chunks(document_id: int) -> None:
    vector_store = get_vector_store()
    vector_store._collection.delete(where={"document_id": document_id})


def count_document_chunks() -> int:
    return int(get_vector_store()._collection.count())


def query_document_chunks(
    question: str,
    top_k: int = 5,
    fetch_k: int | None = None,
    use_mmr: bool = True,
    lambda_param: float = 0.7,
) -> list[RetrievedChunk]:
    vector_store = get_vector_store()
    if count_document_chunks() <= 0:
        return []

    top_k = max(top_k, 1)
    fetch_k = max(fetch_k or top_k, top_k)
    if use_mmr:
        documents = vector_store.max_marginal_relevance_search(
            question,
            k=top_k,
            fetch_k=fetch_k,
            lambda_mult=min(max(lambda_param, 0.0), 1.0),
        )
        score_by_id = _similarity_scores_by_id(vector_store, question, fetch_k)
        return [
            _retrieved_chunk_from_document(
                document=document,
                distance=score_by_id.get(_document_chroma_id(document)),
            )
            for document in documents
        ]

    results = vector_store.similarity_search_with_score(question, k=top_k)
    return [
        _retrieved_chunk_from_document(document=document, distance=distance)
        for document, distance in results
    ]


def _langchain_document(chunk: DocumentChunk) -> "LangChainDocument":
    from langchain_core.documents import Document as LangChainDocument

    return LangChainDocument(
        page_content=chunk.content,
        metadata=_metadata(chunk),
    )


def _metadata(chunk: DocumentChunk) -> dict[str, Any]:
    return {
        "chroma_id": chunk.chroma_id,
        "document_id": chunk.document_id,
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "file_name": chunk.file_name,
        "title": chunk.title or "",
    }


def _similarity_scores_by_id(
    vector_store: "Chroma",
    question: str,
    fetch_k: int,
) -> dict[str, float | None]:
    try:
        results = vector_store.similarity_search_with_score(question, k=fetch_k)
    except Exception:
        return {}
    return {
        _document_chroma_id(document): float(distance)
        for document, distance in results
        if _document_chroma_id(document)
    }


def _retrieved_chunk_from_document(
    document: "LangChainDocument",
    distance: float | None,
) -> RetrievedChunk:
    metadata = dict(document.metadata or {})
    return RetrievedChunk(
        chroma_id=str(metadata.get("chroma_id") or ""),
        content=document.page_content,
        metadata=metadata,
        distance=distance,
        retrieval_sources=["vector"],
        scores={"vector": _distance_to_similarity(distance)},
    )


def _document_chroma_id(document: "LangChainDocument") -> str:
    return str((document.metadata or {}).get("chroma_id") or "")


def _delete_all_documents(vector_store: "Chroma") -> None:
    try:
        ids = vector_store._collection.get(include=[])["ids"]
    except Exception:
        ids = []
    if ids:
        vector_store.delete(ids=ids)


def _distance_to_similarity(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 - float(distance)))
