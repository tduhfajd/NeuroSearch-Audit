from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from backend.config import settings
from backend.crawler.pagespeed import (
    GooglePageSpeedProvider,
    HybridPageSpeedProvider,
    LighthouseProvider,
    collect_pagespeed_scores,
)
from backend.crawler.parsers import parse_page_content
from backend.crawler.persistence import upsert_pages
from backend.crawler.playwright_utils import PlaywrightRenderer, render_with_timeout_policy
from backend.crawler.site_checks import SiteCheckStatus, check_robots_and_sitemap
from backend.crawler.spider import CrawlOutput, PageFetchResult, crawl_site
from backend.db.models import Audit
from backend.db.session import SessionLocal
from backend.runtime_settings import get_pagespeed_api_key


@dataclass(slots=True)
class QueueJob:
    job_id: str
    func: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@dataclass(slots=True)
class InMemoryQueueClient:
    jobs: list[QueueJob] = field(default_factory=list)

    def enqueue(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        job_id = f"job-{len(self.jobs) + 1}"
        self.jobs.append(QueueJob(job_id=job_id, func=func, args=args, kwargs=kwargs))
        return job_id

    def drain(self) -> None:
        while self.jobs:
            job = self.jobs.pop(0)
            job.func(*job.args, **job.kwargs)


INMEMORY_QUEUE = InMemoryQueueClient()


def get_queue_client() -> InMemoryQueueClient:
    # RQ/Redis adapter can be added transparently later, while preserving this interface.
    _ = settings
    return INMEMORY_QUEUE


def enqueue_crawl_job(audit_id: int) -> str:
    queue = get_queue_client()
    return queue.enqueue(run_crawl_job, audit_id)


def _build_http_fetcher() -> tuple[Callable[[str], PageFetchResult], dict[str, int]]:
    diagnostics = {"spa_timeout_count": 0, "spa_fallback_count": 0, "spa_retry_count": 0}

    def _http_fetcher(url: str) -> PageFetchResult:
        req = Request(url, headers={"User-Agent": "NeuroSearchAuditBot/1.0"})
        with urlopen(req, timeout=15) as response:  # noqa: S310
            html = response.read().decode("utf-8", errors="ignore")
            status_code = getattr(response, "status", 200)
        try:
            outcome = render_with_timeout_policy(
                url=url,
                http_html=html,
                renderer=PlaywrightRenderer(),
                timeout_steps_ms=(4000, 10000, 15000),
                retry_budget=1,
            )
        except Exception:  # noqa: BLE001
            outcome = None

        if outcome is None:
            return PageFetchResult(url=url, status_code=status_code, html=html)

        if outcome.timed_out:
            diagnostics["spa_timeout_count"] += 1
        if outcome.reason.endswith("timeout_fallback"):
            diagnostics["spa_fallback_count"] += 1
        diagnostics["spa_retry_count"] += outcome.retries_used
        return PageFetchResult(url=url, status_code=status_code, html=outcome.html)

    return _http_fetcher, diagnostics


def _fetch_status_code(url: str) -> int:
    try:
        req = Request(url, headers={"User-Agent": "NeuroSearchAuditBot/1.0"})
        with urlopen(req, timeout=10) as response:  # noqa: S310
            return int(getattr(response, "status", 200))
    except Exception:  # noqa: BLE001
        return 0


def _get_sitemap_urls(root_url: str) -> list[str]:
    sitemap_url = urljoin(root_url, "/sitemap.xml")
    try:
        req = Request(sitemap_url, headers={"User-Agent": "NeuroSearchAuditBot/1.0"})
        with urlopen(req, timeout=10) as response:  # noqa: S310
            payload = response.read().decode("utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return []

    urls: list[str] = []
    for token in payload.split("<loc>")[1:]:
        value = token.split("</loc>", 1)[0].strip()
        if value:
            urls.append(value)
    return urls


def _get_homepage_links(root_url: str) -> list[str]:
    try:
        fetcher, _ = _build_http_fetcher()
        homepage = fetcher(root_url)
    except Exception:  # noqa: BLE001
        return []
    parsed = parse_page_content(homepage.html, root_url)
    return sorted(parsed.internal_links)


def execute_crawl_pipeline(audit: Audit) -> dict[str, Any]:
    fetcher, spa_diagnostics = _build_http_fetcher()
    site_check: SiteCheckStatus = check_robots_and_sitemap(
        base_url=audit.url,
        fetch_status=_fetch_status_code,
    )

    sitemap_urls = _get_sitemap_urls(audit.url)
    homepage_links = _get_homepage_links(audit.url)

    crawl_result: CrawlOutput = crawl_site(
        root_url=audit.url,
        fetcher=fetcher,
        crawl_depth=audit.crawl_depth,
        max_runtime_seconds=120,
        retries=2,
        backoff_seconds=0.1,
        sitemap_urls=sitemap_urls,
        homepage_links=homepage_links,
    )

    page_payloads = [
        {
            "url": page.url,
            "status_code": page.status_code,
            "title": page.title,
            "h1": page.h1,
            "meta_description": page.meta_description,
            "canonical": page.canonical,
            "robots_meta": page.robots_meta,
            "json_ld": page.json_ld,
            "word_count": page.word_count,
            "inlinks_count": page.inlinks_count,
        }
        for page in crawl_result.pages
    ]

    audit_meta = audit.meta if isinstance(audit.meta, dict) else {}
    meta_api_key = audit_meta.get("pagespeed_api_key")
    effective_pagespeed_api_key = (
        meta_api_key.strip()
        if isinstance(meta_api_key, str) and meta_api_key.strip()
        else (get_pagespeed_api_key() or settings.pagespeed_api_key)
    )

    provider = HybridPageSpeedProvider(
        primary=GooglePageSpeedProvider(api_key=effective_pagespeed_api_key),
        fallback=LighthouseProvider(),
    )
    page_speed_scores = collect_pagespeed_scores(page_payloads, provider, limit=10)
    speed_map = {item.url: item for item in page_speed_scores}
    for payload in page_payloads:
        ps = speed_map.get(payload["url"])
        payload["pagespeed_score"] = ps.score if ps else None

    return {
        "pages": page_payloads,
        "crawl_errors": crawl_result.crawl_errors,
        "timed_out": crawl_result.timed_out,
        "spa_diagnostics": spa_diagnostics,
        "robots_status": site_check.robots_status,
        "sitemap_status": site_check.sitemap_status,
        "pagespeed_source": {item.url: item.source for item in page_speed_scores},
    }


def _merge_meta(meta: dict[str, Any] | None, patch: dict[str, Any]) -> dict[str, Any]:
    current = dict(meta or {})
    current.update(patch)
    return current


def _error_payload(exc: Exception) -> dict[str, Any]:
    message = str(exc) or exc.__class__.__name__
    if isinstance(exc, TimeoutError):
        return {"code": "timeout", "message": message, "retryable": True}
    return {"code": "crawler_error", "message": message, "retryable": False}


def run_crawl_job(audit_id: int, db_session: Session | None = None) -> None:
    manage_session = db_session is None
    db = db_session or SessionLocal()

    try:
        audit = db.get(Audit, audit_id)
        if audit is None:
            return

        audit.status = "crawling"
        audit.meta = _merge_meta(audit.meta, {"progress": 10, "queue_backend": "inmemory"})
        db.commit()

        result = execute_crawl_pipeline(audit)
        upsert_pages(db, audit_id=audit.id, page_payloads=result["pages"], batch_size=100)

        audit.pages_crawled = len(result["pages"])
        audit.status = "completed"
        audit.completed_at = datetime.utcnow()
        audit.meta = _merge_meta(
            audit.meta,
            {
                "progress": 100,
                "robots_status": result["robots_status"],
                "sitemap_status": result["sitemap_status"],
                "crawl_errors": result["crawl_errors"],
                "timed_out": result["timed_out"],
                "spa_diagnostics": result.get("spa_diagnostics", {}),
                "pagespeed_source": result["pagespeed_source"],
            },
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        audit = db.get(Audit, audit_id)
        if audit is not None:
            audit.status = "failed"
            audit.meta = _merge_meta(
                audit.meta,
                {
                    "error": _error_payload(exc),
                    "crawl_errors": [*(_extract_crawl_errors(audit.meta)), _error_payload(exc)],
                    "progress": 100,
                },
            )
            db.commit()
        raise
    finally:
        if manage_session:
            db.close()


def queue_snapshot_json() -> str:
    queue = get_queue_client()
    return json.dumps([{"job_id": job.job_id, "args": job.args} for job in queue.jobs])


def _extract_crawl_errors(meta: dict[str, Any] | None) -> list[dict[str, Any]]:
    payload = meta if isinstance(meta, dict) else {}
    value = payload.get("crawl_errors")
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            normalized.append(item)
        elif isinstance(item, str):
            normalized.append({"code": "crawler_error", "message": item, "retryable": False})
    return normalized
