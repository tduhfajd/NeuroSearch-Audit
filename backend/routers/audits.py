from datetime import datetime
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.crawler.jobs import enqueue_crawl_job
from backend.db.models import Audit
from backend.db.session import get_db

router = APIRouter()


class AuditGoal(StrEnum):
    leads = "leads"
    info = "info"
    local = "local"
    b2b = "b2b"


class AuditCreateRequest(BaseModel):
    url: HttpUrl
    client_name: str | None = None
    niche: str | None = None
    region: str | None = None
    goal: AuditGoal | None = None
    crawl_depth: int = 200

    @field_validator("crawl_depth")
    @classmethod
    def validate_crawl_depth(cls, value: int) -> int:
        if value < 1 or value > 500:
            raise ValueError("crawl_depth must be between 1 and 500")
        return value


class AuditReadResponse(BaseModel):
    id: int
    url: str
    client_name: str | None = None
    status: str
    seo_score: float | None = None
    avri_score: float | None = None
    pages_crawled: int
    created_at: datetime


class AuditCreateResponse(AuditReadResponse):
    queue_job_id: str


def _to_response(audit: Audit) -> AuditReadResponse:
    return AuditReadResponse(
        id=audit.id,
        url=audit.url,
        client_name=audit.client_name,
        status=audit.status,
        seo_score=audit.seo_score,
        avri_score=audit.avri_score,
        pages_crawled=audit.pages_crawled,
        created_at=audit.created_at,
    )


@router.post("", response_model=AuditCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_audit(
    payload: AuditCreateRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> AuditCreateResponse:
    try:
        audit = Audit(
            url=str(payload.url),
            client_name=payload.client_name,
            niche=payload.niche,
            region=payload.region,
            goal=payload.goal.value if payload.goal else None,
            crawl_depth=payload.crawl_depth,
            status="pending",
            pages_crawled=0,
            meta={"progress": 0, "crawl_errors": []},
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)

        job_id = enqueue_crawl_job(audit.id)
        audit.meta = {**(audit.meta or {}), "queue_job_id": job_id}
        db.commit()
        db.refresh(audit)

        return AuditCreateResponse(**_to_response(audit).model_dump(), queue_job_id=job_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("", response_model=list[AuditReadResponse])
async def list_audits(db: Session = Depends(get_db)) -> list[AuditReadResponse]:  # noqa: B008
    try:
        rows = db.query(Audit).order_by(Audit.id.desc()).all()
    except SQLAlchemyError:
        return []
    return [_to_response(row) for row in rows]
