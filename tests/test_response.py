import json
import unittest

from fastapi import HTTPException, status

from app.schemas.response import (
    ApiResponse,
    PageData,
    http_exception_response,
    success_response,
    validation_exception_response,
)


class ResponseSchemaTests(unittest.TestCase):
    def test_success_response_wraps_data(self) -> None:
        response = success_response({"answer": "ok"})

        self.assertEqual(
            response.model_dump(),
            {"code": 200, "msg": "success", "data": {"answer": "ok"}},
        )

    def test_success_response_uses_null_for_empty_data(self) -> None:
        response = success_response(None)

        self.assertEqual(response.model_dump(), {"code": 200, "msg": "success", "data": None})

    def test_page_data_shape(self) -> None:
        response = ApiResponse[PageData[int]](
            code=200,
            msg="success",
            data=PageData(items=[1, 2], total=2, page=1, page_size=20),
        )

        self.assertEqual(
            response.model_dump(),
            {
                "code": 200,
                "msg": "success",
                "data": {"items": [1, 2], "total": 2, "page": 1, "page_size": 20},
            },
        )


class ErrorResponseTests(unittest.TestCase):
    def test_http_exception_maps_not_found_code(self) -> None:
        response = http_exception_response(
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.body),
            {"code": 40401, "msg": "Document not found.", "data": None},
        )

    def test_http_exception_maps_parse_error_detail_data(self) -> None:
        response = http_exception_response(
            HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "PDF parsing failed.",
                    "file_id": 1,
                    "error": "bad pdf",
                },
            )
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.body),
            {
                "code": 42201,
                "msg": "PDF parsing failed.",
                "data": {"file_id": 1, "error": "bad pdf"},
            },
        )

    def test_validation_error_uses_standard_wrapper(self) -> None:
        response = validation_exception_response([{"loc": ["body", "question"], "msg": "missing"}])

        self.assertEqual(response.status_code, 422)
        self.assertEqual(json.loads(response.body)["code"], 40001)
        self.assertEqual(json.loads(response.body)["msg"], "Request validation failed.")


if __name__ == "__main__":
    unittest.main()
