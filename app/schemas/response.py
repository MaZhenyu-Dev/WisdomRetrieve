from __future__ import annotations

from typing import Any, Generic, TypeVar

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")

SUCCESS_CODE = 200
SUCCESS_MSG = "success"

PARAM_ERROR_CODE = 40001
NOT_FOUND_CODE = 40401
PARSE_ERROR_CODE = 42201
UPSTREAM_ERROR_CODE = 50201
SERVER_ERROR_CODE = 50001


class ApiResponse(BaseModel, Generic[T]):
    code: int
    msg: str
    data: T | None = None


class PageData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


def success_response(data: T | None = None) -> ApiResponse[T]:
    return ApiResponse(code=SUCCESS_CODE, msg=SUCCESS_MSG, data=data)


def error_response(
    code: int,
    msg: str,
    data: Any | None = None,
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    payload = ApiResponse[Any](code=code, msg=msg, data=data)
    return JSONResponse(
        status_code=http_status,
        content=jsonable_encoder(payload),
    )


def http_exception_response(exc: HTTPException) -> JSONResponse:
    code, msg, data = _normalize_http_exception_detail(exc)
    return error_response(
        code=code,
        msg=msg,
        data=data,
        http_status=exc.status_code,
    )


def validation_exception_response(errors: list[Any]) -> JSONResponse:
    return error_response(
        code=PARAM_ERROR_CODE,
        msg="Request validation failed.",
        data={"errors": errors},
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


def _normalize_http_exception_detail(exc: HTTPException) -> tuple[int, str, Any | None]:
    detail = exc.detail
    if isinstance(detail, dict):
        if {"code", "msg", "data"}.issubset(detail):
            return int(detail["code"]), str(detail["msg"]), detail.get("data")

        msg = str(detail.get("message") or _default_message(exc.status_code))
        data = {key: value for key, value in detail.items() if key != "message"} or None
        return _business_code_for_status(exc.status_code), msg, data

    msg = str(detail) if detail else _default_message(exc.status_code)
    return _business_code_for_status(exc.status_code), msg, None


def _business_code_for_status(http_status: int) -> int:
    if http_status == status.HTTP_404_NOT_FOUND:
        return NOT_FOUND_CODE
    if http_status == status.HTTP_422_UNPROCESSABLE_CONTENT:
        return PARSE_ERROR_CODE
    if http_status == status.HTTP_502_BAD_GATEWAY:
        return UPSTREAM_ERROR_CODE
    if 400 <= http_status < 500:
        return PARAM_ERROR_CODE
    return SERVER_ERROR_CODE


def _default_message(http_status: int) -> str:
    if http_status == status.HTTP_404_NOT_FOUND:
        return "Resource not found."
    if http_status == status.HTTP_422_UNPROCESSABLE_CONTENT:
        return "Unprocessable entity."
    if http_status == status.HTTP_502_BAD_GATEWAY:
        return "Upstream service failed."
    if 400 <= http_status < 500:
        return "Bad request."
    return "Internal server error."
