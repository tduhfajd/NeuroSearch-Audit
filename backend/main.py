import socket
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.routers.audits import router as audits_router
from backend.routers.reports import router as reports_router


def _check_db_socket(database_url: str) -> bool:
    parsed = urlparse(database_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def create_app() -> FastAPI:
    app = FastAPI(title="NeuroSearch Audit")
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
    app.include_router(reports_router, prefix="/audits", tags=["reports"])
    return app


app = create_app()
