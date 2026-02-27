from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.reports.service import ReportServiceError, generate_report_artifact

router = APIRouter()


def _error_detail(code: str, message: str, *, retryable: bool) -> dict[str, object]:
    return {"code": code, "message": message, "retryable": retryable}


@router.get("/{audit_id}/report/pdf")
async def download_report_pdf(
    audit_id: int,
    db: Session = Depends(get_db),  # noqa: B008
) -> FileResponse:
    try:
        artifact = generate_report_artifact(db, audit_id=audit_id, report_type="full_report")
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_detail("not_found", "Audit not found", retryable=False),
        ) from exc
    except ReportServiceError as exc:
        status_code = 409 if exc.code == "reauth_required" else 422
        raise HTTPException(
            status_code=status_code,
            detail=_error_detail(exc.code, str(exc), retryable=exc.retryable),
        ) from exc

    return FileResponse(
        path=str(artifact.file_path),
        media_type="application/pdf",
        filename=artifact.file_name,
    )


@router.get("/{audit_id}/report/kp")
async def download_report_kp(
    audit_id: int,
    db: Session = Depends(get_db),  # noqa: B008
) -> FileResponse:
    try:
        artifact = generate_report_artifact(db, audit_id=audit_id, report_type="kp")
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_detail("not_found", "Audit not found", retryable=False),
        ) from exc
    except ReportServiceError as exc:
        status_code = 409 if exc.code == "reauth_required" else 422
        raise HTTPException(
            status_code=status_code,
            detail=_error_detail(exc.code, str(exc), retryable=exc.retryable),
        ) from exc

    return FileResponse(
        path=str(artifact.file_path),
        media_type="application/pdf",
        filename=artifact.file_name,
    )
