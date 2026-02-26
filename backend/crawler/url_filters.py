from urllib.parse import ParseResult, parse_qsl, urlencode, urlparse, urlunparse

TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {"gclid", "fbclid", "yclid", "_openstat"}


def _normalize_query(parsed: ParseResult) -> str:
    clean_pairs: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        if key in TRACKING_QUERY_KEYS:
            continue
        if any(key.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES):
            continue
        clean_pairs.append((key, value))
    clean_pairs.sort()
    return urlencode(clean_pairs, doseq=True)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()

    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse((scheme, netloc, path, "", _normalize_query(parsed), ""))


def is_in_scope(url: str, root_url: str, include_subdomains: bool = False) -> bool:
    current = urlparse(url)
    root = urlparse(root_url)
    current_host = current.hostname or ""
    root_host = root.hostname or ""

    if not current_host or not root_host:
        return False
    if include_subdomains:
        return current_host == root_host or current_host.endswith(f".{root_host}")
    return current_host == root_host
