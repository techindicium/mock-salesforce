import asyncio
import json

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from mock_salesforce.errors import http_exception_handler, validation_exception_handler


def _fake_request() -> Request:
    return Request(scope={"type": "http", "headers": []})


def _decode(response):
    return json.loads(response.body.decode())


def test_validation_exception_handler_malformed_json():
    exc = RequestValidationError(
        [{"type": "json_invalid", "loc": ("body", 0), "msg": "JSON decode error", "input": {}}]
    )
    response = asyncio.run(validation_exception_handler(_fake_request(), exc))

    assert response.status_code == 400
    assert _decode(response) == {
        "error": "MALFORMED_JSON",
        "message": "Request body is not valid JSON",
    }


def test_validation_exception_handler_field_validation():
    exc = RequestValidationError(
        [{"type": "missing", "loc": ("body", "name"), "msg": "Field required", "input": {}}]
    )
    response = asyncio.run(validation_exception_handler(_fake_request(), exc))

    assert response.status_code == 422
    assert _decode(response) == {
        "error": "VALIDATION_ERROR",
        "message": "name: Field required",
    }


def test_http_exception_handler_string_detail():
    exc = StarletteHTTPException(status_code=404, detail="Not found")
    response = asyncio.run(http_exception_handler(_fake_request(), exc))

    assert response.status_code == 404
    assert _decode(response) == {"error": "HTTP_ERROR", "message": "Not found"}


def test_http_exception_handler_dict_detail():
    exc = StarletteHTTPException(
        status_code=404,
        detail={"error": "ACCOUNT_NOT_FOUND", "message": "Account 123 not found"},
    )
    response = asyncio.run(http_exception_handler(_fake_request(), exc))

    assert response.status_code == 404
    assert _decode(response) == {
        "error": "ACCOUNT_NOT_FOUND",
        "message": "Account 123 not found",
    }
