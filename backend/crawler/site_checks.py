from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass(slots=True)
class SiteCheckStatus:
    robots_url: str
    robots_status: str
    sitemap_url: str
    sitemap_status: str


def _status_from_code(code: int) -> str:
    if 200 <= code < 300:
        return "ok"
    if code == 404:
        return "missing"
    return "error"


def check_robots_and_sitemap(
    *,
    base_url: str,
    fetch_status: Callable[[str], int],
) -> SiteCheckStatus:
    robots_url = urljoin(base_url, "/robots.txt")
    sitemap_url = urljoin(base_url, "/sitemap.xml")

    robots_code = fetch_status(robots_url)
    sitemap_code = fetch_status(sitemap_url)

    return SiteCheckStatus(
        robots_url=robots_url,
        robots_status=_status_from_code(robots_code),
        sitemap_url=sitemap_url,
        sitemap_status=_status_from_code(sitemap_code),
    )
