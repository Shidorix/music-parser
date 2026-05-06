"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from backend.api.exception_handlers import (
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from backend.api.v1 import router as api_v1_router
from backend.core.exceptions import AppException
from backend.core.settings import get_settings
from backend.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Run application startup and shutdown hooks."""
    if get_settings().auto_create_tables:
        await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Playlist Parser API",
        version="0.1.0",
        description=(
            "Research-driven API for parsing unstructured music lists and "
            "matching tracks with explainable fuzzy algorithms."
        ),
        lifespan=lifespan,
    )
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parsed_cors_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
