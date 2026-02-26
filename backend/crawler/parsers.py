from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from backend.crawler.url_filters import normalize_url


@dataclass(slots=True)
class ParsedContent:
    title: str | None
    h1: str | None
    meta_description: str | None
    canonical: str | None
    robots_meta: str | None
    json_ld: list[dict]
    word_count: int
    internal_links: set[str]
    external_links: set[str]


class _SimpleHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.base_host = urlparse(base_url).hostname or ""
        self.title_parts: list[str] = []
        self.h1_parts: list[str] = []
        self.text_parts: list[str] = []
        self.meta_description: str | None = None
        self.canonical: str | None = None
        self.robots_meta: str | None = None
        self.internal_links: set[str] = set()
        self.external_links: set[str] = set()
        self.json_ld: list[dict] = []
        self.in_title = False
        self.in_h1 = False
        self.in_script_ld = False
        self.script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value for key, value in attrs}
        tag = tag.lower()

        if tag == "title":
            self.in_title = True
        elif tag == "h1" and not self.h1_parts:
            self.in_h1 = True
        elif tag == "meta":
            name = (attrs_dict.get("name") or "").lower()
            if name == "description":
                self.meta_description = attrs_dict.get("content")
            if name == "robots":
                self.robots_meta = attrs_dict.get("content")
        elif tag == "link":
            if (attrs_dict.get("rel") or "").lower() == "canonical" and attrs_dict.get("href"):
                self.canonical = normalize_url(urljoin(self.base_url, attrs_dict["href"]))
        elif tag == "a":
            href = attrs_dict.get("href")
            if not href:
                return
            absolute = normalize_url(urljoin(self.base_url, href))
            if absolute.startswith(("http://", "https://")):
                link_host = urlparse(absolute).hostname or ""
                if link_host == self.base_host:
                    self.internal_links.add(absolute)
                else:
                    self.external_links.add(absolute)
        elif tag == "script":
            script_type = (attrs_dict.get("type") or "").lower()
            if script_type == "application/ld+json":
                self.in_script_ld = True
                self.script_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "script" and self.in_script_ld:
            self.in_script_ld = False
            raw = "".join(self.script_parts).strip()
            if not raw:
                return
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return
            if isinstance(parsed, dict):
                self.json_ld.append(parsed)
            elif isinstance(parsed, list):
                self.json_ld.extend(item for item in parsed if isinstance(item, dict))

    def handle_data(self, data: str) -> None:
        value = unescape(data).strip()
        if not value:
            return
        if self.in_title:
            self.title_parts.append(value)
        if self.in_h1:
            self.h1_parts.append(value)
        if self.in_script_ld:
            self.script_parts.append(data)
        self.text_parts.append(value)


def parse_page_content(html: str, base_url: str) -> ParsedContent:
    parser = _SimpleHTMLParser(base_url=base_url)
    parser.feed(html)
    text = " ".join(parser.text_parts)
    words = re.findall(r"\w+", text, flags=re.UNICODE)

    return ParsedContent(
        title=" ".join(parser.title_parts) or None,
        h1=" ".join(parser.h1_parts) or None,
        meta_description=parser.meta_description,
        canonical=parser.canonical,
        robots_meta=parser.robots_meta,
        json_ld=parser.json_ld,
        word_count=len(words),
        internal_links=parser.internal_links,
        external_links=parser.external_links,
    )
