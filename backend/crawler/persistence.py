from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import Page


PAGE_FIELD_NAMES = {
    "url",
    "status_code",
    "title",
    "h1",
    "meta_description",
    "canonical",
    "robots_meta",
    "json_ld",
    "word_count",
    "inlinks_count",
    "pagespeed_score",
    "ai_scores",
}


def _apply_page_fields(page: Page, payload: dict) -> None:
    for field in PAGE_FIELD_NAMES:
        if field in payload:
            setattr(page, field, payload[field])
    page.crawled_at = payload.get("crawled_at") or datetime.utcnow()


def upsert_pages(
    db: Session,
    *,
    audit_id: int,
    page_payloads: Iterable[dict],
    batch_size: int = 100,
) -> int:
    payload_list = list(page_payloads)
    if not payload_list:
        return 0

    total = 0
    for idx in range(0, len(payload_list), batch_size):
        batch = payload_list[idx : idx + batch_size]
        urls = [payload["url"] for payload in batch if payload.get("url")]
        existing_rows = db.execute(
            select(Page).where(Page.audit_id == audit_id, Page.url.in_(urls))
        ).scalars()
        existing_by_url = {row.url: row for row in existing_rows}

        for payload in batch:
            url = payload["url"]
            row = existing_by_url.get(url)
            if row is None:
                row = Page(audit_id=audit_id, url=url)
                db.add(row)
            _apply_page_fields(row, payload)
            total += 1

        db.flush()

    return total
