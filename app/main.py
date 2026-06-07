import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.chat import router as chat_router
from app.api.document import router as document_router
from app.api.health import router as health_router
from app.api.monitor import router as monitor_router
from app.config import get_settings
from app.database.mysql import init_mysql_tables
from app.schemas.response import (
    SERVER_ERROR_CODE,
    error_response,
    http_exception_response,
    validation_exception_response,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Enterprise RAG knowledge base QA backend.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    application.include_router(document_router)
    application.include_router(chat_router)
    application.include_router(monitor_router)

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_, exc: StarletteHTTPException) -> JSONResponse:
        return http_exception_response(exc)

    @application.exception_handler(RequestValidationError)
    async def handle_validation_exception(_, exc: RequestValidationError) -> JSONResponse:
        return validation_exception_response(exc.errors())

    @application.exception_handler(Exception)
    async def handle_unexpected_exception(_, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error.", exc_info=exc)
        return error_response(
            code=SERVER_ERROR_CODE,
            msg="Internal server error.",
            data=None,
            http_status=500,
        )

    @application.on_event("startup")
    def startup() -> None:
        try:
            init_mysql_tables()
        except Exception:
            logger.exception("MySQL table initialization failed.")

    return application


app = create_app()
