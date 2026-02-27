import asyncio
import socket
from collections.abc import AsyncIterator
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.crawler.jobs import get_queue_client
from backend.routers.ai_bridge import router as ai_bridge_router
from backend.routers.audits import router as audits_router
from backend.routers.reports import router as reports_router
from backend.routers.settings import router as settings_router


def _check_db_socket(database_url: str) -> bool:
    parsed = urlparse(database_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


async def _queue_drain_loop() -> None:
    queue = get_queue_client()
    while True:
        queue.drain()
        await asyncio.sleep(0.5)


async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    task: asyncio.Task[None] | None = None
    if settings.auto_drain_queue:
        task = asyncio.create_task(_queue_drain_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


def create_app() -> FastAPI:
    app = FastAPI(title="NeuroSearch Audit", lifespan=_lifespan)
    static_dir = Path(__file__).resolve().parents[1] / "frontend" / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/static/index.html")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/db")
    async def health_db() -> dict[str, str]:
        return {"status": "ok" if _check_db_socket(settings.database_url) else "degraded"}

    app.include_router(audits_router, prefix="/audits", tags=["audits"])
    app.include_router(ai_bridge_router, prefix="/ai-bridge", tags=["ai-bridge"])
    app.include_router(settings_router, prefix="/settings", tags=["settings"])
    app.include_router(reports_router, prefix="/audits", tags=["reports"])
    return app


app = create_app()
