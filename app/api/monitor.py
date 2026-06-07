from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk, QALog
from app.database.mysql import get_db_session
from app.retrieval.chroma_store import count_document_chunks
from app.schemas.response import ApiResponse, success_response

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


class QAMetricsData(BaseModel):
    qa_count: int
    cache_hit_count: int
    cache_miss_count: int
    cache_hit_rate: float
    avg_response_time_ms: float
    avg_cache_hit_response_time_ms: float
    avg_cache_miss_response_time_ms: float


class OverviewMetricsData(QAMetricsData):
    document_count: int
    chunk_count: int
    vector_count: int


@router.get("/qa", response_model=ApiResponse[QAMetricsData])
def qa_metrics(db: Session = Depends(get_db_session)) -> ApiResponse[QAMetricsData]:
    return success_response(QAMetricsData(**_qa_metrics(db)))


@router.get("/overview", response_model=ApiResponse[OverviewMetricsData])
def overview_metrics(db: Session = Depends(get_db_session)) -> ApiResponse[OverviewMetricsData]:
    metrics = _qa_metrics(db)
    metrics.update(
        {
            "document_count": int(db.scalar(select(func.count()).select_from(Document)) or 0),
            "chunk_count": int(db.scalar(select(func.count()).select_from(DocumentChunk)) or 0),
            "vector_count": _vector_count(),
        }
    )
    return success_response(OverviewMetricsData(**metrics))


def _qa_metrics(db: Session) -> dict[str, int | float]:
    total = int(db.scalar(select(func.count()).select_from(QALog)) or 0)
    cache_hits = int(
        db.scalar(
            select(func.count()).select_from(QALog).where(QALog.cache_hit.is_(True))
        )
        or 0
    )
    cache_misses = max(total - cache_hits, 0)

    return {
        "qa_count": total,
        "cache_hit_count": cache_hits,
        "cache_miss_count": cache_misses,
        "cache_hit_rate": round(cache_hits / total, 4) if total else 0.0,
        "avg_response_time_ms": _avg_latency(db),
        "avg_cache_hit_response_time_ms": _avg_latency(db, cache_hit=True),
        "avg_cache_miss_response_time_ms": _avg_latency(db, cache_hit=False),
    }


def _avg_latency(db: Session, cache_hit: bool | None = None) -> float:
    statement = select(func.avg(QALog.latency_ms)).where(QALog.latency_ms.is_not(None))
    if cache_hit is not None:
        statement = statement.where(QALog.cache_hit.is_(cache_hit))
    value = db.scalar(statement)
    return round(float(value), 2) if value is not None else 0.0


def _vector_count() -> int:
    try:
        return count_document_chunks()
    except Exception:
        return 0
