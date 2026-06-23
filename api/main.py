from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from api.auth.router import router as auth_router
from api.config import load_api_config
from api.routers.activity import router as activity_router
from api.routers.audit import router as audit_router
from api.routers.cases import router as cases_router
from api.routers.dashboard import router as dashboard_router
from api.routers.enforcement import router as enforcement_router
from api.routers.events import router as events_router
from api.routers.groups import router as groups_router
from api.routers.health import router as health_router
from api.routers.indicators import router as indicators_router
from api.routers.officers import router as officers_router
from api.routers.reports import router as reports_router
from api.routers.users import router as users_router
from app.config import load_config
from app.core.logging import generate_request_id, get_logger, setup_logging
from app.database.session import init_db, init_secadmin_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    setup_logging(config.log_level, config.log_format)
    await init_db(config)
    await init_secadmin_db(config)
    logger.info("SecAdmin database initialized")
    yield


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Any]],
    ) -> Any:
        req_id = generate_request_id()
        request.state.req_id = req_id

        start = time.monotonic()
        method = request.method
        path = request.url.path

        logger.info("Request started", req_id=req_id, method=method, path=path)

        try:
            response = await call_next(request)
            elapsed = time.monotonic() - start
            logger.info(
                "Request completed",
                req_id=req_id,
                method=method,
                path=path,
                status=response.status_code,
                elapsed_ms=round(elapsed * 1000),
            )
            return response
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error(
                "Request failed",
                req_id=req_id,
                method=method,
                path=path,
                error=str(e),
                elapsed_ms=round(elapsed * 1000),
            )
            raise


def create_app() -> FastAPI:
    api_config = load_api_config()

    app = FastAPI(
        title="SecAdmin API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if api_config.debug else None,
        redoc_url="/redoc" if api_config.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(activity_router)
    app.include_router(dashboard_router)
    app.include_router(events_router)
    app.include_router(indicators_router)
    app.include_router(users_router)
    app.include_router(groups_router)
    app.include_router(cases_router)
    app.include_router(officers_router)
    app.include_router(audit_router)
    app.include_router(enforcement_router)
    app.include_router(reports_router)

    return app


app = create_app()
