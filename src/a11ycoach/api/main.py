"""App factory: build a fully wired FastAPI app from settings."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import APIRouter, FastAPI

from a11ycoach.api.errors import register_error_handlers
from a11ycoach.api.middleware import request_context_middleware
from a11ycoach.api.routes import chat, documents, health, ingest
from a11ycoach.config import Settings, get_settings
from a11ycoach.db.llm_calls import make_recorder
from a11ycoach.db.session import make_engine, make_sessionmaker
from a11ycoach.llm.gateway import build_gateway
from a11ycoach.logging_setup import setup_logging

logger = logging.getLogger("a11ycoach")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    engine = make_engine(settings)  # no connection is opened yet

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("starting", extra={"status": settings.app_env})
        worker = None
        if settings.worker_in_api:  # no separate worker service here: run one in this process
            from a11ycoach.workers.main import run_embedded  # imported late: it reads .env

            worker = asyncio.create_task(run_embedded(settings))
        yield
        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker
        if getattr(app.state, "queue", None):
            await app.state.queue.close()
        await engine.dispose()  # close every pooled connection on shutdown

    app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.system_prompt = chat.load_prompt(settings.prompts_dir)  # missing file: no start
    app.state.gateway = build_gateway(settings, make_recorder(app.state.sessionmaker))

    app.middleware("http")(request_context_middleware)
    register_error_handlers(app)

    v1 = APIRouter(prefix="/v1")
    v1.include_router(documents.router)
    v1.include_router(chat.router)
    v1.include_router(ingest.router)
    app.include_router(health.router)
    app.include_router(v1)
    return app
