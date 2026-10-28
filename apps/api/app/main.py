"""EVIDA FastAPI Application Factory and Entrypoint"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import health, investigations
from app.core.config import get_settings
from app.core.logging import (
    configure_logging,
    ctx_request_id,
    get_logger,
)
from app.domain.investigations.state_machine import LifecycleException

logger = get_logger("evida.api")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    configure_logging(level="INFO" if settings.APP_ENV != "development" else "DEBUG")

    application = FastAPI(
        title="EVIDA API",
        description="Evidence-Driven AI Software Repair Application Backend",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # CORS configuration
    cors_origins = ["*"] if settings.APP_ENV != "production" else settings.CORS_ORIGINS
    cors_origins = ["*"] if settings.APP_ENV != "production" else settings.CORS_ORIGINS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request Tracing & Structured Logging Middleware
    @application.middleware("http")
    async def request_context_middleware(request: Request, call_next: Any) -> Any:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        ctx_token = ctx_request_id.set(req_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = req_id

            logger.info(
                f"{request.method} {request.url.path} completed with {response.status_code}",
                extra={
                    "operation": "http_request",
                    "status": "ok" if response.status_code < 400 else "error",
                    "duration_ms": elapsed_ms,
                },
            )
            return response
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {exc}",
                exc_info=True,
                extra={
                    "operation": "http_request",
                    "status": "fatal",
                    "duration_ms": elapsed_ms,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An internal server error occurred.",
                        "request_id": req_id,
                    }
                },
                headers={"X-Request-ID": req_id},
            )
        finally:
            ctx_request_id.reset(ctx_token)

    # Standardized Exception Handlers
    @application.exception_handler(StarletteHTTPException)
    @application.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException | FastAPIHTTPException
    ) -> JSONResponse:
        req_id = ctx_request_id.get() or str(uuid.uuid4())
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        message = str(exc.detail)

        if isinstance(exc.detail, dict):
            code = exc.detail.get("code", code)
            message = exc.detail.get("message", message)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": req_id,
                }
            },
            headers={"X-Request-ID": req_id},
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = ctx_request_id.get() or str(uuid.uuid4())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters or payload.",
                    "request_id": req_id,
                    "details": exc.errors(),
                }
            },
            headers={"X-Request-ID": req_id},
        )

    @application.exception_handler(LifecycleException)
    async def lifecycle_exception_handler(
        request: Request, exc: LifecycleException
    ) -> JSONResponse:
        req_id = ctx_request_id.get() or str(uuid.uuid4())
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": req_id,
                }
            },
            headers={"X-Request-ID": req_id},
        )

    # Mount API routers under /api/v1
    application.include_router(health.router, prefix="/api/v1")
    application.include_router(investigations.router, prefix="/api/v1")

    return application


app = create_app()
