from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_body(code: str, message: str) -> dict:
    return {"error": code, "message": message}


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    if first.get("type") == "json_invalid":
        # Verified against fastapi==0.141.1 / pydantic==2.13.5: a malformed JSON
        # body raises a single error with type "json_invalid".
        return JSONResponse(
            status_code=400,
            content=error_body("MALFORMED_JSON", "Request body is not valid JSON"),
        )
    field = ".".join(str(p) for p in first["loc"] if p != "body")
    return JSONResponse(
        status_code=422,
        content=error_body("VALIDATION_ERROR", f"{field}: {first['msg']}"),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    content = exc.detail if isinstance(exc.detail, dict) else error_body(
        "HTTP_ERROR", str(exc.detail)
    )
    return JSONResponse(status_code=exc.status_code, content=content)
