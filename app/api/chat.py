import json
import logging
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session

from app.database.mysql import get_db_session
from app.schemas.chat import ChatHistoryMessage, ChatRequest, ChatResponse, ChatSessionResponse
from app.schemas.response import (
    ApiResponse,
    PageData,
    PARAM_ERROR_CODE,
    SERVER_ERROR_CODE,
    UPSTREAM_ERROR_CODE,
    success_response,
)
from app.service.chat_service import (
    answer_question,
    answer_question_stream,
    delete_chat_session,
    get_chat_history,
    get_chat_sessions,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ApiResponse[ChatResponse])
@router.post("/", response_model=ApiResponse[ChatResponse])
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db_session),
) -> object:
    if request.stream:
        return StreamingResponse(
            _sse_event_stream(
                answer_question_stream(
                    db,
                    session_id=request.session_id,
                    question=request.question,
                    top_k=request.top_k,
                )
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return success_response(
        answer_question(
            db,
            session_id=request.session_id,
            question=request.question,
            top_k=request.top_k,
        )
    )


def _sse_event_stream(events: Iterator[dict[str, Any]]) -> Iterator[str]:
    try:
        for event in events:
            yield _format_sse(event["event"], event["data"])
    except StarletteHTTPException as exc:
        yield _format_sse("error", _http_exception_payload(exc))
    except Exception as exc:
        logger.exception("Unhandled chat streaming error.", exc_info=exc)
        yield _format_sse(
            "error",
            {
                "code": SERVER_ERROR_CODE,
                "msg": "Internal server error.",
                "data": None,
            },
        )


def _format_sse(event: str, data: Any) -> str:
    payload = json.dumps(jsonable_encoder(data), ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _http_exception_payload(exc: StarletteHTTPException) -> dict[str, Any]:
    return {
        "code": _stream_error_code(exc.status_code),
        "msg": str(exc.detail),
        "data": None,
    }


def _stream_error_code(http_status: int) -> int:
    if http_status == 502:
        return UPSTREAM_ERROR_CODE
    if 400 <= http_status < 500:
        return PARAM_ERROR_CODE
    return SERVER_ERROR_CODE


@router.get("/history", response_model=ApiResponse[PageData[ChatHistoryMessage]])
def history(
    session_id: str | None = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_session),
) -> ApiResponse[PageData[ChatHistoryMessage]]:
    total, messages = get_chat_history(
        db,
        session_id=session_id,
        page=page,
        page_size=page_size,
    )
    return success_response(
        PageData(items=messages, total=total, page=page, page_size=page_size)
    )


@router.get("/sessions", response_model=ApiResponse[PageData[ChatSessionResponse]])
def sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_session),
) -> ApiResponse[PageData[ChatSessionResponse]]:
    total, session_rows = get_chat_sessions(db, page=page, page_size=page_size)
    return success_response(
        PageData(items=session_rows, total=total, page=page, page_size=page_size)
    )


@router.delete("/sessions/{session_id}", response_model=ApiResponse[None])
def remove_session(
    session_id: str,
    db: Session = Depends(get_db_session),
) -> ApiResponse[None]:
    delete_chat_session(db, session_id=session_id)
    return success_response(None)
