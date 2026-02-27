from datetime import datetime
from threading import Lock, Thread

from fastapi import APIRouter
from pydantic import BaseModel

from backend.analyzer.ai_bridge import session_health
from backend.analyzer.ai_bridge_session import SessionStateError, setup_session_state

router = APIRouter()
_SETUP_LOCK = Lock()
_SETUP_STATUS: dict[str, str | None] = {
    "status": "idle",
    "detail": None,
    "started_at": None,
    "finished_at": None,
}


class AIBridgeHealthResponse(BaseModel):
    status: str
    detail: str


@router.get("/health", response_model=AIBridgeHealthResponse)
async def ai_bridge_health() -> AIBridgeHealthResponse:
    ok, detail = session_health()
    return AIBridgeHealthResponse(status="ok" if ok else "reauth_required", detail=detail)


class AIBridgeSetupResponse(BaseModel):
    status: str
    detail: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


def _snapshot_setup() -> AIBridgeSetupResponse:
    with _SETUP_LOCK:
        return AIBridgeSetupResponse(
            status=_SETUP_STATUS["status"] or "idle",
            detail=_SETUP_STATUS["detail"],
            started_at=_SETUP_STATUS["started_at"],
            finished_at=_SETUP_STATUS["finished_at"],
        )


def _run_setup_task() -> None:
    with _SETUP_LOCK:
        _SETUP_STATUS["status"] = "running"
        _SETUP_STATUS["detail"] = "Open browser window and complete ChatGPT login."
        _SETUP_STATUS["started_at"] = datetime.utcnow().isoformat()
        _SETUP_STATUS["finished_at"] = None

    try:
        setup_session_state()
    except SessionStateError as exc:
        with _SETUP_LOCK:
            _SETUP_STATUS["status"] = "failed"
            _SETUP_STATUS["detail"] = str(exc)
            _SETUP_STATUS["finished_at"] = datetime.utcnow().isoformat()
        return
    except Exception as exc:  # noqa: BLE001
        with _SETUP_LOCK:
            _SETUP_STATUS["status"] = "failed"
            _SETUP_STATUS["detail"] = f"unexpected setup error: {exc}"
            _SETUP_STATUS["finished_at"] = datetime.utcnow().isoformat()
        return

    with _SETUP_LOCK:
        _SETUP_STATUS["status"] = "completed"
        _SETUP_STATUS["detail"] = "Session state saved successfully."
        _SETUP_STATUS["finished_at"] = datetime.utcnow().isoformat()


@router.get("/setup/status", response_model=AIBridgeSetupResponse)
async def ai_bridge_setup_status() -> AIBridgeSetupResponse:
    return _snapshot_setup()


@router.post("/setup/start", response_model=AIBridgeSetupResponse)
async def ai_bridge_setup_start() -> AIBridgeSetupResponse:
    snapshot = _snapshot_setup()
    if snapshot.status == "running":
        return snapshot

    worker = Thread(target=_run_setup_task, daemon=True)
    worker.start()
    return _snapshot_setup()
