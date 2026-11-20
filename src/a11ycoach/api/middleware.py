"""Request ID and request timing middleware."""

import logging
import time
import uuid

from fastapi import Request

from a11ycoach.logging_setup import request_id_ctx

logger = logging.getLogger("a11ycoach")


async def request_context_middleware(
    request: Request,
    call_next,
):
    """Attach a request ID and log request details."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    token = request_id_ctx.set(request_id)
    start = time.perf_counter()

    try:
        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
    finally:
        request_id_ctx.reset(token)
