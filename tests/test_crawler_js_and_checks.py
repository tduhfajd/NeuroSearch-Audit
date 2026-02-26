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


from backend.crawler.pagespeed import (  # noqa: E402
    GooglePageSpeedProvider,
    HybridPageSpeedProvider,
    LighthouseProvider,
    collect_pagespeed_scores,
    top_pages_by_inlinks,
)
from backend.crawler.site_checks import check_robots_and_sitemap  # noqa: E402


def test_robots_and_sitemap_statuses_are_reported() -> None:
    codes = {
        "https://example.com/robots.txt": 200,
        "https://example.com/sitemap.xml": 404,
    }

    status = check_robots_and_sitemap(
        base_url="https://example.com", fetch_status=lambda url: codes[url]
    )

    assert status.robots_status == "ok"
    assert status.sitemap_status == "missing"


def test_top10_selection_prefers_higher_inlinks() -> None:
    pages = [{"url": f"https://example.com/{idx}", "inlinks_count": idx} for idx in range(15)]

    top = top_pages_by_inlinks(pages, limit=10)

    assert len(top) == 10
    assert top[0]["inlinks_count"] == 14
    assert top[-1]["inlinks_count"] == 5


def test_pagespeed_api_primary_is_used_when_available() -> None:
    provider = HybridPageSpeedProvider(
        primary=GooglePageSpeedProvider(
            api_key="token",
            requester=lambda _: {
                "lighthouseResult": {"categories": {"performance": {"score": 0.73}}}
            },
        ),
        fallback=LighthouseProvider(runner=lambda _: "{}"),
    )

    result = provider.get_score_with_source("https://example.com")

    assert result.score == 73.0
    assert result.source == "pagespeed_api"


def test_pagespeed_fallback_to_lighthouse_without_api_key() -> None:
    provider = HybridPageSpeedProvider(
        primary=GooglePageSpeedProvider(api_key=None),
        fallback=LighthouseProvider(
            runner=lambda _: '{"categories": {"performance": {"score": 0.81}}}'
        ),
    )

    result = provider.get_score_with_source("https://example.com")

    assert result.score == 81.0
    assert result.source == "lighthouse"


def test_collect_pagespeed_scores_respects_top10_limit() -> None:
    pages = [{"url": f"https://example.com/{idx}", "inlinks_count": idx} for idx in range(30)]
    provider = HybridPageSpeedProvider(
        primary=GooglePageSpeedProvider(api_key=None),
        fallback=LighthouseProvider(
            runner=lambda _: '{"categories": {"performance": {"score": 0.5}}}'
        ),
    )

    results = collect_pagespeed_scores(pages, provider, limit=10)

    assert len(results) == 10
    assert all(item.source == "lighthouse" for item in results)
