from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


class HTMLRenderer(Protocol):
    def render(self, url: str, timeout_ms: int = 15000) -> str:
        ...


@dataclass(slots=True)
class RenderDecision:
    use_playwright: bool
    reason: str


def should_use_playwright(html: str, url: str) -> RenderDecision:
    script_count = html.lower().count("<script")
    text_words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", html), flags=re.UNICODE))

    indicators = (
        "__NEXT_DATA__" in html
        or "data-reactroot" in html
        or "id=\"app\"" in html
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
    def render(self, url: str, timeout_ms: int = 15000) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("playwright is not available") from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                return page.content()
            finally:
                browser.close()


def render_with_fallback(
    *,
    url: str,
    http_html: str,
    renderer: HTMLRenderer,
    timeout_ms: int = 15000,
) -> tuple[str, bool, str]:
    decision = should_use_playwright(http_html, url)
    if not decision.use_playwright:
        return http_html, False, decision.reason

    rendered = renderer.render(url=url, timeout_ms=timeout_ms)
    return rendered, True, decision.reason
