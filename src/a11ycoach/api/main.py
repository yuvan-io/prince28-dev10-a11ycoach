"""Application factory and startup lifecycle."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from a11ycoach.api.errors import (
    not_found_error_handler,
    validation_error_handler,
)
from a11ycoach.api.middleware import request_context_middleware
from a11ycoach.api.routes import documents, health
from a11ycoach.config import Settings, get_settings
from a11ycoach.logging_setup import setup_logging
from a11ycoach.store import RecordStore

logger = logging.getLogger("a11ycoach")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application with optional test settings."""

    settings = settings or get_settings()
    setup_logging(settings.log_level)

    store = RecordStore(settings.data_file)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Load records when the application starts."""
        app.state.store = store

        try:
            count = store.load()
            logger.info("records loaded", extra={"records": count})
        except (FileNotFoundError, ValueError):
            logger.exception("Could not load records")

        yield

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    app.middleware("http")(request_context_middleware)

    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,
    )
    app.add_exception_handler(404, not_found_error_handler)

    app.include_router(health.router)
    app.include_router(documents.router)

    return app
