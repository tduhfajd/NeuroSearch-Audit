from datetime import datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl, field_validator
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


class AuditGoal(str, Enum):
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


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_audit(payload: AuditCreateRequest) -> dict[str, str]:
    _ = payload
    raise HTTPException(status_code=501, detail="Audit workflow is not implemented in Phase 1")


@router.get("", response_model=list[AuditReadResponse])
async def list_audits() -> list[AuditReadResponse]:
    return []
