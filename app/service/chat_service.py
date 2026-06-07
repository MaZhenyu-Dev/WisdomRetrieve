from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, TypedDict

from fastapi import HTTPException, status
from langgraph.graph import END, START, StateGraph
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.cache.redis import get_json, get_knowledge_base_version, set_json
from app.config import get_settings
from app.database.models import ChatHistory, ChatSession, QALog
from app.llm.qwen import QwenClientError, chat_completion, chat_completion_stream
from app.retrieval.chroma_store import RetrievedChunk
from app.retrieval.context_builder import build_context
from app.retrieval.hybrid import hybrid_retrieve_chunks
from app.retrieval.rerank import rerank_retrieved_chunks
from app.schemas.chat import ChatHistoryMessage, ChatResponse, ChatSessionResponse, ChatSource
from app.service.query_rewrite import rewrite_query

NOT_FOUND_ANSWER = "知识库中未找到相关信息。"
MAX_HISTORY_MESSAGES = 6
logger = logging.getLogger(__name__)


class QAState(TypedDict, total=False):
    db: Session
    session_id: str
    question: str
    top_k: int
    started_at: float
    normalized_question: str
    question_hash: str
    knowledge_base_version: str | None
    cache_key: str | None
    cache_hit: bool
    history: list[ChatHistory]
    rewritten_question: str
    candidates: list[RetrievedChunk]
    chunks: list[RetrievedChunk]
    answer: str
    sources: list[ChatSource]
    document_ids: list[int]
    user_history_written: bool


def answer_question(db: Session, session_id: str, question: str, top_k: int = 5) -> ChatResponse:
    state = get_qa_graph().invoke(_initial_state(db, session_id, question, top_k))
    return ChatResponse(answer=state["answer"], sources=state.get("sources", []))


def answer_question_stream(
    db: Session,
    session_id: str,
    question: str,
    top_k: int = 5,
) -> Iterator[dict[str, Any]]:
    state = _initial_state(db, session_id, question, top_k)
    try:
        state = _prepare_question_node(state)
        state = _ensure_session_node(state)
        state = _read_cache_node(state)

        if state.get("cache_hit"):
            yield from _yield_cached_stream(state)
            return

        state = _rewrite_question_node(state)
        state = _hybrid_retrieve_node(state)
        state = _rerank_node(state)
        state = _build_sources_node(state)
        yield _stream_event("sources", _dump_sources(state.get("sources", [])))

        chunks = state.get("chunks", [])
        if not chunks:
            answer = NOT_FOUND_ANSWER
            yield _stream_event("answer_delta", {"content": answer})
            state = {**state, "answer": answer}
        else:
            messages = _build_messages(
                question=state["normalized_question"],
                rewritten_question=state["rewritten_question"],
                chunks=chunks,
                history=state.get("history", []),
            )
            answer_parts: list[str] = []
            try:
                for delta in chat_completion_stream(messages):
                    answer_parts.append(delta)
                    yield _stream_event("answer_delta", {"content": delta})
            except QwenClientError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(exc),
                ) from exc
            answer_text = "".join(answer_parts).strip() or NOT_FOUND_ANSWER
            state = {**state, "answer": answer_text}

        state = _write_side_effects_node(state)
        yield _stream_done_event(state)
    except Exception:
        db.rollback()
        raise


def _initial_state(db: Session, session_id: str, question: str, top_k: int) -> QAState:
    return {
        "db": db,
        "session_id": session_id,
        "question": question,
        "top_k": top_k,
        "started_at": time.perf_counter(),
        "cache_hit": False,
        "user_history_written": False,
    }


def _yield_cached_stream(state: QAState) -> Iterator[dict[str, Any]]:
    sources = state.get("sources", [])
    yield _stream_event("sources", _dump_sources(sources))
    yield _stream_event("answer_delta", {"content": state["answer"]})
    state = _write_side_effects_node(state)
    yield _stream_done_event(state)


def _stream_done_event(state: QAState) -> dict[str, Any]:
    return _stream_event(
        "done",
        {
            "answer": state["answer"],
            "sources": _dump_sources(state.get("sources", [])),
        },
    )


def _stream_event(event: str, data: Any) -> dict[str, Any]:
    return {"event": event, "data": data}


def _dump_sources(sources: list[ChatSource]) -> list[dict[str, Any]]:
    return [source.model_dump() for source in sources]


@lru_cache
def get_qa_graph():
    graph = StateGraph(QAState)
    graph.add_node("prepare", _prepare_question_node)
    graph.add_node("ensure_session", _ensure_session_node)
    graph.add_node("read_cache", _read_cache_node)
    graph.add_node("rewrite_question", _rewrite_question_node)
    graph.add_node("hybrid_retrieve", _hybrid_retrieve_node)
    graph.add_node("rerank", _rerank_node)
    graph.add_node("build_sources", _build_sources_node)
    graph.add_node("generate_answer", _generate_answer_node)
    graph.add_node("write_side_effects", _write_side_effects_node)

    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "ensure_session")
    graph.add_edge("ensure_session", "read_cache")
    graph.add_conditional_edges(
        "read_cache",
        _route_after_cache,
        {
            "hit": "write_side_effects",
            "miss": "rewrite_question",
        },
    )
    graph.add_edge("rewrite_question", "hybrid_retrieve")
    graph.add_edge("hybrid_retrieve", "rerank")
    graph.add_edge("rerank", "build_sources")
    graph.add_edge("build_sources", "generate_answer")
    graph.add_edge("generate_answer", "write_side_effects")
    graph.add_edge("write_side_effects", END)
    return graph.compile()


def _prepare_question_node(state: QAState) -> QAState:
    normalized_question = state["question"].strip()
    if not normalized_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    question_hash = _question_hash(normalized_question)
    knowledge_base_version = get_knowledge_base_version()
    return {
        **state,
        "normalized_question": normalized_question,
        "question_hash": question_hash,
        "knowledge_base_version": knowledge_base_version,
        "cache_key": _qa_cache_key(
            question_hash=question_hash,
            knowledge_base_version=knowledge_base_version,
            session_id=state["session_id"],
            top_k=state["top_k"],
        ),
    }


def _ensure_session_node(state: QAState) -> QAState:
    _ensure_chat_session(state["db"], state["session_id"], state["normalized_question"])
    return state


def _read_cache_node(state: QAState) -> QAState:
    cached_response = _read_cached_response(state.get("cache_key"))
    if cached_response is None:
        return state

    answer, sources, document_ids = cached_response
    return {
        **state,
        "answer": answer,
        "sources": sources,
        "document_ids": document_ids,
        "cache_hit": True,
    }


def _route_after_cache(state: QAState) -> str:
    return "hit" if state.get("cache_hit") else "miss"


def _rewrite_question_node(state: QAState) -> QAState:
    history = _recent_history(state["db"], state["session_id"])
    rewritten_question = rewrite_query(state["normalized_question"], history)
    return {**state, "history": history, "rewritten_question": rewritten_question}


def _hybrid_retrieve_node(state: QAState) -> QAState:
    _append_history(state["db"], state["session_id"], "user", state["normalized_question"])
    candidates = hybrid_retrieve_chunks(
        state["db"],
        state["rewritten_question"],
        vector_top_k=10,
        bm25_top_k=10,
        candidate_limit=20,
    )
    return {**state, "candidates": candidates, "user_history_written": True}


def _rerank_node(state: QAState) -> QAState:
    chunks = rerank_retrieved_chunks(
        state["rewritten_question"],
        state.get("candidates", []),
        top_k=state["top_k"],
    )
    return {**state, "chunks": chunks}


def _build_sources_node(state: QAState) -> QAState:
    sources = _build_sources(state.get("chunks", []))
    return {
        **state,
        "sources": sources,
        "document_ids": _source_document_ids(sources),
    }


def _generate_answer_node(state: QAState) -> QAState:
    chunks = state.get("chunks", [])
    if not chunks:
        return {**state, "answer": NOT_FOUND_ANSWER}

    messages = _build_messages(
        question=state["normalized_question"],
        rewritten_question=state["rewritten_question"],
        chunks=chunks,
        history=state.get("history", []),
    )
    try:
        answer = chat_completion(messages)
    except QwenClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return {**state, "answer": answer.strip() or NOT_FOUND_ANSWER}


def _write_side_effects_node(state: QAState) -> QAState:
    db = state["db"]
    session_id = state["session_id"]
    answer = state["answer"]
    sources = state.get("sources", [])
    document_ids = state.get("document_ids") or _source_document_ids(sources)
    cache_hit = bool(state.get("cache_hit"))

    if not state.get("user_history_written"):
        _append_history(db, session_id, "user", state["normalized_question"])
    _append_history(db, session_id, "assistant", answer)

    if not cache_hit and state.get("cache_key"):
        _write_cached_response(
            state["cache_key"],
            answer=answer,
            sources=sources,
            document_ids=document_ids,
            question_hash=state["question_hash"],
            knowledge_base_version=state.get("knowledge_base_version"),
            ttl_seconds=get_settings().qa_cache_ttl_seconds,
        )

    latency_ms = int((time.perf_counter() - state["started_at"]) * 1000)
    _write_qa_log(
        db,
        session_id=session_id,
        question=state["normalized_question"],
        answer=answer,
        sources=sources,
        latency_ms=latency_ms,
        cache_hit=cache_hit,
        question_hash=state["question_hash"],
        knowledge_base_version=state.get("knowledge_base_version"),
        document_ids=document_ids,
    )
    db.commit()
    _log_qa_response(
        session_id=session_id,
        cache_hit=cache_hit,
        latency_ms=latency_ms,
        question_hash=state["question_hash"],
        knowledge_base_version=state.get("knowledge_base_version"),
    )
    return {**state, "document_ids": document_ids}


def get_chat_history(
    db: Session,
    session_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[int, list[ChatHistoryMessage]]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    statement = select(ChatHistory)
    count_statement = select(func.count()).select_from(ChatHistory)

    if session_id:
        statement = statement.where(ChatHistory.session_id == session_id)
        count_statement = count_statement.where(ChatHistory.session_id == session_id)

    total = db.scalar(count_statement) or 0
    rows = list(
        db.scalars(
            statement.order_by(ChatHistory.create_time.asc(), ChatHistory.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return total, [ChatHistoryMessage.model_validate(row) for row in rows]


def get_chat_sessions(
    db: Session,
    page: int = 1,
    page_size: int = 50,
) -> tuple[int, list[ChatSessionResponse]]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    total = db.scalar(select(func.count()).select_from(ChatSession)) or 0
    rows = list(
        db.scalars(
            select(ChatSession)
            .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return total, [ChatSessionResponse.model_validate(row) for row in rows]


def delete_chat_session(db: Session, session_id: str) -> str:
    session = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    db.execute(delete(ChatHistory).where(ChatHistory.session_id == session_id))
    db.execute(delete(QALog).where(QALog.session_id == session_id))
    db.delete(session)
    db.commit()
    return session_id


def _ensure_chat_session(db: Session, session_id: str, question: str) -> None:
    session = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
    if session is None:
        db.add(ChatSession(session_id=session_id, title=question[:255]))


def _append_history(db: Session, session_id: str, role: str, content: str) -> None:
    db.add(ChatHistory(session_id=session_id, role=role, content=content))
    db.flush()


def _recent_history(db: Session, session_id: str) -> list[ChatHistory]:
    rows = list(
        db.scalars(
            select(ChatHistory)
            .where(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.create_time.desc(), ChatHistory.id.desc())
            .limit(MAX_HISTORY_MESSAGES)
        )
    )
    return list(reversed(rows))


def _build_messages(
    question: str,
    rewritten_question: str,
    chunks: list[RetrievedChunk],
    history: list[ChatHistory],
) -> list[dict[str, str]]:
    context = build_context(chunks, max_chars=get_settings().rag_context_max_chars)
    history_text = "\n".join(
        f"{'用户' if row.role == 'user' else '助手'}: {row.content}"
        for row in history
    )
    user_prompt = (
        "请基于以下知识库上下文回答问题。\n\n"
        f"历史对话:\n{history_text or '无'}\n\n"
        f"原始问题: {question}\n"
        f"检索改写问题: {rewritten_question}\n\n"
        f"知识库上下文:\n{context}\n\n"
        "回答要求:\n"
        "1. 严格依据知识库上下文回答。\n"
        "2. 能引用编号、制度名称、页码时尽量引用。\n"
        "3. 如果上下文没有答案，只回答“知识库中未找到相关信息。”"
    )
    return [
        {
            "role": "system",
            "content": (
                "你是一名企业知识库问答助手。必须严格依据提供的知识库上下文回答。"
                "如果无法从上下文找到答案，只回复“知识库中未找到相关信息。”"
                "禁止编造、猜测或使用上下文之外的信息。"
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def _build_sources(chunks: list[RetrievedChunk]) -> list[ChatSource]:
    sources: list[ChatSource] = []
    seen: set[tuple[int | None, int | None, int | None]] = set()
    for chunk in chunks:
        metadata = chunk.metadata
        source = ChatSource(
            document_id=_optional_int(metadata.get("document_id")),
            file=str(metadata.get("file_name") or ""),
            page=_optional_int(metadata.get("page_number")),
            title=str(metadata.get("title") or "") or None,
            chunk_index=_optional_int(metadata.get("chunk_index")),
            retrieval_sources=list(chunk.retrieval_sources),
            vector_score=_optional_float(chunk.scores.get("vector")),
            bm25_score=_optional_float(chunk.scores.get("bm25")),
            hybrid_score=_optional_float(chunk.scores.get("hybrid")),
            rerank_score=_optional_float(chunk.scores.get("rerank")),
        )
        key = (source.document_id, source.page, source.chunk_index)
        if source.file and key not in seen:
            sources.append(source)
            seen.add(key)
    return sources


def _normalize_question_for_hash(question: str) -> str:
    return " ".join(question.strip().split()).casefold()


def _question_hash(question: str) -> str:
    return hashlib.sha256(_normalize_question_for_hash(question).encode("utf-8")).hexdigest()


def _qa_cache_key(
    question_hash: str,
    knowledge_base_version: str | None,
    session_id: str,
    top_k: int,
) -> str | None:
    if not knowledge_base_version:
        return None
    scope_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
    return f"qa:{question_hash}:kb:{knowledge_base_version}:scope:{scope_hash}:top_k:{top_k}"


def _read_cached_response(cache_key: str | None) -> tuple[str, list[ChatSource], list[int]] | None:
    if not cache_key:
        return None
    payload = get_json(cache_key)
    if not payload:
        return None

    answer = payload.get("answer")
    raw_sources = payload.get("sources")
    if not isinstance(answer, str) or not isinstance(raw_sources, list):
        return None

    try:
        sources = [
            ChatSource.model_validate(source)
            for source in raw_sources
            if isinstance(source, dict)
        ]
    except Exception:
        return None

    raw_document_ids = payload.get("document_ids")
    document_ids = [
        int(document_id)
        for document_id in raw_document_ids
        if _can_cast_int(document_id)
    ] if isinstance(raw_document_ids, list) else _source_document_ids(sources)
    return answer, sources, document_ids


def _write_cached_response(
    cache_key: str,
    answer: str,
    sources: list[ChatSource],
    document_ids: list[int],
    question_hash: str,
    knowledge_base_version: str | None,
    ttl_seconds: int,
) -> None:
    set_json(
        cache_key,
        {
            "answer": answer,
            "sources": [source.model_dump() for source in sources],
            "document_ids": document_ids,
            "question_hash": question_hash,
            "knowledge_base_version": knowledge_base_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        ttl_seconds=ttl_seconds,
    )


def _source_document_ids(sources: list[ChatSource]) -> list[int]:
    document_ids = {
        source.document_id
        for source in sources
        if source.document_id is not None
    }
    return sorted(document_ids)


def _can_cast_int(value: Any) -> bool:
    try:
        int(value)
    except (TypeError, ValueError):
        return False
    return True


def _log_qa_response(
    session_id: str,
    cache_hit: bool,
    latency_ms: int,
    question_hash: str,
    knowledge_base_version: str | None,
) -> None:
    logger.info(
        "qa_response session_id=%s cache_hit=%s latency_ms=%s question_hash=%s kb_version=%s",
        session_id,
        cache_hit,
        latency_ms,
        question_hash,
        knowledge_base_version,
    )


def _write_qa_log(
    db: Session,
    session_id: str,
    question: str,
    answer: str,
    sources: list[ChatSource],
    latency_ms: int,
    cache_hit: bool,
    question_hash: str,
    knowledge_base_version: str | None,
    document_ids: list[int],
) -> None:
    db.add(
        QALog(
            session_id=session_id,
            question=question,
            answer=answer,
            sources=json.dumps(
                [source.model_dump() for source in sources],
                ensure_ascii=False,
            ),
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            question_hash=question_hash,
            knowledge_base_version=knowledge_base_version,
            document_ids=json.dumps(document_ids, ensure_ascii=False),
        )
    )


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
