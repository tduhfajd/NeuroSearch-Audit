from backend.crawler.spider import CrawlConfig, PageFetchResult, SiteCrawler


def _static_fetcher(pages: dict[str, str]):
    def _fetch(url: str) -> PageFetchResult:
        html = pages.get(url, "<html><body>empty</body></html>")
        return PageFetchResult(url=url, status_code=200, html=html)

    return _fetch


def test_seed_uses_sitemap_and_homepage_with_dedup() -> None:
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com"))

    seeds = crawler.build_seed_urls(
        sitemap_urls=["https://example.com/a", "https://example.com/a?utm_source=x"],
        homepage_links=["https://example.com/b", "https://other.com/skip"],
    )

    assert "https://example.com/" in seeds
    assert "https://example.com/a" in seeds
    assert "https://example.com/b" in seeds
    assert all("other.com" not in url for url in seeds)


def test_scope_respects_strict_host_by_default() -> None:
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com", include_subdomains=False))

    seeds = crawler.build_seed_urls(
        sitemap_urls=["https://blog.example.com/post", "https://example.com/main"]
    )

    assert "https://example.com/main" in seeds
    assert "https://blog.example.com/post" not in seeds


def test_scope_includes_subdomains_when_enabled() -> None:
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com", include_subdomains=True))

    seeds = crawler.build_seed_urls(sitemap_urls=["https://blog.example.com/post"])

    assert "https://blog.example.com/post" in seeds


def test_limits_stop_crawl_at_crawl_depth() -> None:
    pages = {
        "https://example.com/": "<a href='/a'>A</a>",
        "https://example.com/a": "<a href='/b'>B</a>",
        "https://example.com/b": "<a href='/c'>C</a>",
    }
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com", crawl_depth=2))

    result = crawler.crawl(fetcher=_static_fetcher(pages))

    assert len(result.visited_urls) == 2


def test_limits_stop_crawl_by_runtime_timeout() -> None:
    pages = {"https://example.com/": "<a href='/a'>A</a>"}
    crawler = SiteCrawler(
        CrawlConfig(root_url="https://example.com", crawl_depth=10, max_runtime_seconds=0.0)
    )

    result = crawler.crawl(fetcher=_static_fetcher(pages))

    assert result.timed_out is True


def test_scope_records_retry_error_after_retries() -> None:
    crawler = SiteCrawler(
        CrawlConfig(root_url="https://example.com", retries=2, backoff_seconds=0.0)
    )

    def broken_fetcher(url: str) -> PageFetchResult:
        raise RuntimeError(f"failed for {url}")

    result = crawler.crawl(fetcher=broken_fetcher)

    assert len(result.crawl_errors) == 1
    assert "failed for" in result.crawl_errors[0]["error"]


def test_extract_page_fields_from_html() -> None:
    html = """
    <html>
      <head>
        <title>Example Title</title>
        <meta name='description' content='meta text'>
        <meta name='robots' content='index,follow'>
        <link rel='canonical' href='https://example.com/canonical/'>
      </head>
      <body>
        <h1>Main Heading</h1>
        <p>Hello crawler world</p>
      </body>
    </html>
    """
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com"))

    result = crawler.crawl(
        fetcher=lambda url: PageFetchResult(url=url, status_code=200, html=html),
        sitemap_urls=["https://example.com/page"],
    )

    page = result.pages[0]
    assert page.title == "Example Title"
    assert page.h1 == "Main Heading"
    assert page.meta_description == "meta text"
    assert page.robots_meta == "index,follow"
    assert page.canonical == "https://example.com/canonical"
    assert page.word_count >= 3


def test_links_split_internal_and_external_sets() -> None:
    html = """
    <html><body>
      <a href='/inner'>Inner</a>
      <a href='https://example.com/also-inner'>Inner 2</a>
      <a href='https://other.net/ext'>Ext</a>
    </body></html>
    """
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com"))

    result = crawler.crawl(
        fetcher=lambda url: PageFetchResult(url=url, status_code=200, html=html),
        sitemap_urls=["https://example.com/page"],
    )

    page = result.pages[0]
    assert "https://example.com/inner" in page.internal_links
    assert "https://example.com/also-inner" in page.internal_links
    assert "https://other.net/ext" in page.external_links


def test_jsonld_extract_supports_object_and_list() -> None:
    html = """
    <html><body>
      <script type='application/ld+json'>
        {"@type": "Organization", "name": "Acme"}
      </script>
      <script type='application/ld+json'>
        [{"@type": "FAQPage"}, {"@type": "Article"}]
      </script>
    </body></html>
    """
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com"))

    result = crawler.crawl(
        fetcher=lambda url: PageFetchResult(url=url, status_code=200, html=html),
        sitemap_urls=["https://example.com/page"],
    )

    page = result.pages[0]
    types = {item.get("@type") for item in page.json_ld}
    assert {"Organization", "FAQPage", "Article"}.issubset(types)


def test_inlinks_count_is_computed_from_internal_graph() -> None:
    pages = {
        "https://example.com/": "<a href='/a'>A</a><a href='/b'>B</a>",
        "https://example.com/a": "<a href='/b'>B</a>",
        "https://example.com/b": "<p>end</p>",
    }
    crawler = SiteCrawler(CrawlConfig(root_url="https://example.com", crawl_depth=3))
    result = crawler.crawl(fetcher=_static_fetcher(pages))

    by_url = {page.url: page for page in result.pages}
    assert by_url["https://example.com/b"].inlinks_count == 2
