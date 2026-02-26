from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote
from urllib.request import urlopen


class PageSpeedProvider(Protocol):
    def get_score(self, url: str) -> float | None: ...


@dataclass(slots=True)
class PageSpeedResult:
    url: str
    score: float | None
    source: str


class GooglePageSpeedProvider:
    def __init__(
        self, api_key: str | None = None, requester: Callable[[str], dict] | None = None
    ) -> None:
        self.api_key = api_key
        self.requester = requester or self._default_requester

    @staticmethod
    def _default_requester(url: str) -> dict:
        with urlopen(url, timeout=20) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    def get_score(self, url: str) -> float | None:
        if not self.api_key:
            return None
        endpoint = (
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?strategy=mobile"
            f"&url={quote(url, safe='')}&key={self.api_key}"
        )
        try:
            data = self.requester(endpoint)
            score = (
                data.get("lighthouseResult", {})
                .get("categories", {})
                .get("performance", {})
                .get("score")
            )
            if score is None:
                return None
            return float(score) * 100
        except Exception:  # noqa: BLE001
            return None


class LighthouseProvider:
    def __init__(self, runner: Callable[[str], str] | None = None) -> None:
        self.runner = runner or self._default_runner

    @staticmethod
    def _default_runner(url: str) -> str:
        command = [
            "lighthouse",
            url,
            "--quiet",
            "--output=json",
            "--output-path=stdout",
            "--chrome-flags=--headless",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)  # noqa: S603
        return result.stdout

    def get_score(self, url: str) -> float | None:
        try:
            payload = self.runner(url)
            data = json.loads(payload)
            score = data.get("categories", {}).get("performance", {}).get("score")
            if score is None:
                return None
            return float(score) * 100
        except Exception:  # noqa: BLE001
            return None


class HybridPageSpeedProvider:
    def __init__(
        self,
        primary: PageSpeedProvider,
        fallback: PageSpeedProvider,
    ) -> None:
        self.primary = primary
        self.fallback = fallback

    def get_score_with_source(self, url: str) -> PageSpeedResult:
        primary_score = self.primary.get_score(url)
        if primary_score is not None:
            return PageSpeedResult(url=url, score=primary_score, source="pagespeed_api")

        fallback_score = self.fallback.get_score(url)
        return PageSpeedResult(url=url, score=fallback_score, source="lighthouse")


def top_pages_by_inlinks(pages: list[dict], limit: int = 10) -> list[dict]:
    sorted_pages = sorted(
        pages,
        key=lambda p: (p.get("inlinks_count") or 0, p.get("url") or ""),
        reverse=True,
    )
    return sorted_pages[:limit]


def collect_pagespeed_scores(
    pages: list[dict],
    provider: HybridPageSpeedProvider,
    limit: int = 10,
) -> list[PageSpeedResult]:
    selected = top_pages_by_inlinks(pages, limit=limit)
    return [provider.get_score_with_source(page["url"]) for page in selected if page.get("url")]
