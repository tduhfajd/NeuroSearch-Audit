from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from typing import Protocol


class HTMLRenderer(Protocol):
    def render(self, url: str, timeout_ms: int = 15000, wait_until: str = "domcontentloaded") -> str: ...


@dataclass(slots=True)
class RenderDecision:
    use_playwright: bool
    reason: str


@dataclass(slots=True)
class RenderOutcome:
    html: str
    used_playwright: bool
    reason: str
    timed_out: bool
    fallback_attempts: int
    retries_used: int


def should_use_playwright(html: str, url: str) -> RenderDecision:
    script_count = html.lower().count("<script")
    text_words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", html), flags=re.UNICODE))

    indicators = (
        "__NEXT_DATA__" in html
        or "data-reactroot" in html
        or 'id="app"' in html
        or "id='app'" in html
    )

    if indicators and text_words < 80:
        return RenderDecision(True, "spa-indicator-low-text")
    if script_count >= 8 and text_words < 50:
        return RenderDecision(True, "script-heavy-low-text")
    if url.endswith(".js"):
        return RenderDecision(True, "js-endpoint")
    return RenderDecision(False, "http-sufficient")


class PlaywrightRenderer:
    def render(self, url: str, timeout_ms: int = 15000, wait_until: str = "domcontentloaded") -> str:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("playwright is not available") from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                return page.content()
            finally:
                browser.close()


def render_with_timeout_policy(
    *,
    url: str,
    http_html: str,
    renderer: HTMLRenderer,
    timeout_steps_ms: Iterable[int] = (5000, 10000, 15000),
    retry_budget: int = 1,
) -> RenderOutcome:
    decision = should_use_playwright(http_html, url)
    if not decision.use_playwright:
        return RenderOutcome(
            html=http_html,
            used_playwright=False,
            reason=decision.reason,
            timed_out=False,
            fallback_attempts=0,
            retries_used=0,
        )

    steps = tuple(timeout_steps_ms)
    if not steps:
        raise ValueError("timeout_steps_ms must not be empty")

    attempts = 0
    timed_out = False
    for retry in range(retry_budget + 1):
        for timeout_ms in steps:
            attempts += 1
            try:
                rendered = renderer.render(url=url, timeout_ms=timeout_ms, wait_until="domcontentloaded")
                return RenderOutcome(
                    html=rendered,
                    used_playwright=True,
                    reason=decision.reason,
                    timed_out=timed_out,
                    fallback_attempts=attempts,
                    retries_used=retry,
                )
            except TimeoutError:
                timed_out = True

    return RenderOutcome(
        html=http_html,
        used_playwright=False,
        reason=f"{decision.reason}:timeout_fallback",
        timed_out=timed_out,
        fallback_attempts=attempts,
        retries_used=retry_budget,
    )


def render_with_fallback(
    *,
    url: str,
    http_html: str,
    renderer: HTMLRenderer,
    timeout_ms: int = 15000,
) -> tuple[str, bool, str]:
    outcome = render_with_timeout_policy(
        url=url,
        http_html=http_html,
        renderer=renderer,
        timeout_steps_ms=(timeout_ms,),
        retry_budget=0,
    )
    return outcome.html, outcome.used_playwright, outcome.reason
