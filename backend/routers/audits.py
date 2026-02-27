from datetime import datetime
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.analyzer.ai_bridge import (
    PlaywrightChatGPTTransport,
    ReauthRequiredError,
    run_ai_analyze,
)
from backend.analyzer.service import analyze_audit
from backend.crawler.jobs import enqueue_crawl_job
from backend.db.models import Audit, Issue
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


class AnalyzeAuditResponse(BaseModel):
    audit_id: int
    issues_created: int
    by_priority: dict[str, int]
    seo_score: float


class AIAnalyzeResponse(BaseModel):
    audit_id: int
    status: str
    processed_pages: int
    avri_score: float | None = None
    errors: list[str]


class IssueReadResponse(BaseModel):
    id: int
    rule_id: str
    priority: str
    title: str
    description: str
    recommendation: str
    affected_url: str | None = None


class GroupedIssuesResponse(BaseModel):
    P0: list[IssueReadResponse]
    P1: list[IssueReadResponse]
    P2: list[IssueReadResponse]
    P3: list[IssueReadResponse]


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


@router.get("/{audit_id}", response_model=AuditReadResponse)
async def get_audit(
    audit_id: int,
    db: Session = Depends(get_db),  # noqa: B008
) -> AuditReadResponse:
    audit = db.get(Audit, audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    return _to_response(audit)


@router.post("/{audit_id}/analyze", response_model=AnalyzeAuditResponse)
async def analyze_audit_endpoint(
    audit_id: int,
    db: Session = Depends(get_db),  # noqa: B008
) -> AnalyzeAuditResponse:
    try:
        summary = analyze_audit(db, audit_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Audit not found") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    return AnalyzeAuditResponse(
        audit_id=summary.audit_id,
        issues_created=summary.issues_created,
        by_priority=summary.by_priority,
        seo_score=summary.seo_score,
    )


@router.post("/{audit_id}/ai-analyze", response_model=AIAnalyzeResponse)
async def ai_analyze_audit_endpoint(
    audit_id: int,
    db: Session = Depends(get_db),  # noqa: B008
) -> AIAnalyzeResponse:
    try:
        summary = run_ai_analyze(db, audit_id, transport=PlaywrightChatGPTTransport())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Audit not found") from exc
    except ReauthRequiredError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "reauth_required", "message": str(exc)},
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    return AIAnalyzeResponse(
        audit_id=summary.audit_id,
        status=summary.status,
        processed_pages=summary.processed_pages,
        avri_score=summary.avri_score,
        errors=summary.errors,
    )


@router.get("/{audit_id}/issues", response_model=GroupedIssuesResponse)
async def get_grouped_issues(
    audit_id: int,
    db: Session = Depends(get_db),  # noqa: B008
) -> GroupedIssuesResponse:
    audit = db.get(Audit, audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit not found")

    grouped: dict[str, list[IssueReadResponse]] = {"P0": [], "P1": [], "P2": [], "P3": []}
    rows = db.query(Issue).filter(Issue.audit_id == audit_id).order_by(Issue.id.asc()).all()
    for row in rows:
        if row.priority not in grouped:
            continue
        grouped[row.priority].append(
            IssueReadResponse(
                id=row.id,
                rule_id=row.rule_id,
                priority=row.priority,
                title=row.title,
                description=row.description,
                recommendation=row.recommendation,
                affected_url=row.affected_url,
            )
        )

    return GroupedIssuesResponse(**grouped)
