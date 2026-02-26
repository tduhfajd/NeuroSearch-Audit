from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from backend.crawler.parsers import parse_page_content
from backend.crawler.url_filters import is_in_scope, normalize_url


@dataclass(slots=True)
class PageFetchResult:
    url: str
    status_code: int
    html: str


@dataclass(slots=True)
class CrawledPage:
    url: str
    status_code: int
    title: str | None
    h1: str | None
    meta_description: str | None
    canonical: str | None
    robots_meta: str | None
    json_ld: list[dict]
    word_count: int
    internal_links: list[str]
    external_links: list[str]
    inlinks_count: int = 0


@dataclass(slots=True)
class CrawlOutput:
    pages: list[CrawledPage]
    visited_urls: list[str]
    timed_out: bool = False
    crawl_errors: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class CrawlConfig:
    root_url: str
    crawl_depth: int = 200
    max_runtime_seconds: float = 120.0
    include_subdomains: bool = False
    retries: int = 2
    backoff_seconds: float = 0.1

    @property
    def normalized_root_url(self) -> str:
        return normalize_url(self.root_url)


class SiteCrawler:
    def __init__(self, config: CrawlConfig) -> None:
        self.config = config

    def build_seed_urls(
        self,
        sitemap_urls: list[str] | None = None,
        homepage_links: list[str] | None = None,
    ) -> list[str]:
        candidates = [self.config.root_url]
        if sitemap_urls:
            candidates.extend(sitemap_urls)
        if homepage_links:
            candidates.extend(homepage_links)

        dedup: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = normalize_url(candidate)
            if normalized in seen:
                continue
            if not is_in_scope(
                normalized, self.config.normalized_root_url, self.config.include_subdomains
            ):
                continue
            seen.add(normalized)
            dedup.append(normalized)
        return dedup

    def crawl(
        self,
        fetcher: Callable[[str], PageFetchResult],
        sitemap_urls: list[str] | None = None,
        homepage_links: list[str] | None = None,
    ) -> CrawlOutput:
        queue: deque[str] = deque(self.build_seed_urls(sitemap_urls, homepage_links))
        visited: set[str] = set()
        pages: dict[str, CrawledPage] = {}
        inlinks_map: dict[str, int] = {}
        crawl_errors: list[dict[str, str]] = []

        started_at = time.monotonic()
        timed_out = False

        while queue and len(visited) < self.config.crawl_depth:
            if time.monotonic() - started_at > self.config.max_runtime_seconds:
                timed_out = True
                break

            current_url = queue.popleft()
            if current_url in visited:
                continue

            fetch_result: PageFetchResult | None = None
            last_error: Exception | None = None
            for attempt in range(self.config.retries + 1):
                try:
                    fetch_result = fetcher(current_url)
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempt < self.config.retries:
                        time.sleep(self.config.backoff_seconds * (attempt + 1))

            if fetch_result is None:
                crawl_errors.append(
                    {"url": current_url, "error": str(last_error or "fetch_failed")}
                )
                visited.add(current_url)
                continue

            visited.add(current_url)
            parsed = parse_page_content(fetch_result.html, fetch_result.url)

            page = CrawledPage(
                url=normalize_url(fetch_result.url),
                status_code=fetch_result.status_code,
                title=parsed.title,
                h1=parsed.h1,
                meta_description=parsed.meta_description,
                canonical=parsed.canonical,
                robots_meta=parsed.robots_meta,
                json_ld=parsed.json_ld,
                word_count=parsed.word_count,
                internal_links=sorted(parsed.internal_links),
                external_links=sorted(parsed.external_links),
            )
            pages[page.url] = page

            for link in parsed.internal_links:
                normalized = normalize_url(link)
                if not is_in_scope(
                    normalized, self.config.normalized_root_url, self.config.include_subdomains
                ):
                    continue
                inlinks_map[normalized] = inlinks_map.get(normalized, 0) + 1
                if normalized not in visited:
                    queue.append(normalized)

        for url, page in pages.items():
            page.inlinks_count = inlinks_map.get(url, 0)

        return CrawlOutput(
            pages=list(pages.values()),
            visited_urls=sorted(visited),
            timed_out=timed_out,
            crawl_errors=crawl_errors,
        )
