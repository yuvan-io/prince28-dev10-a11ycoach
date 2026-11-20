"""Problem Details error responses."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def problem(
    status: int,
    title: str,
    detail: str,
    request: Request,
    errors: list[dict[str, str]] | None = None,
) -> JSONResponse:
    """Build an RFC 9457-style Problem Details response."""
    body: dict[str, object] = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", None),
    }

    if errors is not None:
        body["errors"] = errors

    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return validation errors in a structured format."""
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]

    return problem(
        422,
        "Unprocessable Entity",
        "The request contains invalid data.",
        request,
        errors,
    )


async def not_found_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a standard 404 Problem Details response."""
    detail = str(exc.detail) if hasattr(exc, "detail") else "The requested resource was not found."

    return problem(404, "Not Found", detail, request)
