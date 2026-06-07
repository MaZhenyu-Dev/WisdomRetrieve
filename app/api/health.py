from fastapi import APIRouter
from pydantic import BaseModel

from app.cache.redis import ping_redis
from app.database.mysql import ping_mysql
from app.schemas.response import ApiResponse, success_response

router = APIRouter(tags=["health"])


class HealthData(BaseModel):
    status: str
    service: str
    checks: dict[str, bool]


@router.get("/health", response_model=ApiResponse[HealthData])
def health() -> ApiResponse[HealthData]:
    mysql = ping_mysql()
    redis = ping_redis()
    return success_response(
        HealthData(
            status="ok" if mysql and redis else "degraded",
            service="backend",
            checks={
                "mysql": mysql,
                "redis": redis,
            },
        )
    )
