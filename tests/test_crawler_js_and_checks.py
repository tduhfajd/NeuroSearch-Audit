from backend.crawler.playwright_utils import render_with_fallback, should_use_playwright


class FakeRenderer:
    def __init__(self, html: str) -> None:
        self.html = html
        self.called = False

    def render(self, url: str, timeout_ms: int = 15000) -> str:
        _ = (url, timeout_ms)
        self.called = True
        return self.html


def test_playwright_fallback_triggers_for_spa_like_content() -> None:
    html = "<html><body><div id='app'></div><script></script><script></script></body></html>"
    decision = should_use_playwright(html, "https://example.com")

    assert decision.use_playwright is True
    assert decision.reason in {"spa-indicator-low-text", "script-heavy-low-text"}


def test_playwright_fallback_skips_when_http_has_content() -> None:
    html = "<html><body><h1>Title</h1><p>" + "word " * 120 + "</p></body></html>"
    decision = should_use_playwright(html, "https://example.com")

    assert decision.use_playwright is False
    assert decision.reason == "http-sufficient"


def test_js_render_path_uses_renderer() -> None:
    html = "<html><body><div id='app'></div></body></html>"
    renderer = FakeRenderer("<html><body><h1>Rendered</h1></body></html>")

    result_html, used, reason = render_with_fallback(
        url="https://example.com", http_html=html, renderer=renderer
    )

    assert used is True
    assert renderer.called is True
    assert "Rendered" in result_html
    assert reason in {"spa-indicator-low-text", "script-heavy-low-text"}


def test_js_render_path_keeps_http_when_not_needed() -> None:
    http_html = "<html><body><p>" + "text " * 100 + "</p></body></html>"
    renderer = FakeRenderer("<html><body><h1>Rendered</h1></body></html>")

    result_html, used, reason = render_with_fallback(
        url="https://example.com", http_html=http_html, renderer=renderer
    )

    assert used is False
    assert renderer.called is False
    assert result_html == http_html
    assert reason == "http-sufficient"
