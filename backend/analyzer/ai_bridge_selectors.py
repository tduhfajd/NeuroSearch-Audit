from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LocatorLike(Protocol):
    def count(self) -> int: ...

    def first(self) -> LocatorLike: ...

    def fill(self, text: str) -> None: ...

    def click(self) -> None: ...

    def inner_text(self) -> str: ...


class PageLike(Protocol):
    def locator(self, selector: str) -> LocatorLike: ...


@dataclass(frozen=True, slots=True)
class SelectorSet:
    input_selectors: tuple[str, ...]
    send_selectors: tuple[str, ...]
    response_selectors: tuple[str, ...]


DEFAULT_SELECTORS = SelectorSet(
    input_selectors=(
        "textarea[data-id='prompt-textarea']",
        "textarea[placeholder*='Message']",
        "#prompt-textarea",
        "textarea",
    ),
    send_selectors=(
        "button[data-testid='send-button']",
        "button[aria-label='Send message']",
        "button:has-text('Send')",
    ),
    response_selectors=(
        "[data-message-author-role='assistant']",
        "article[data-testid='conversation-turn-assistant']",
        ".markdown.prose",
    ),
)


class ChatGPTSelectorAdapter:
    def __init__(self, selectors: SelectorSet = DEFAULT_SELECTORS) -> None:
        self.selectors = selectors

    def _resolve_first(self, page: PageLike, selector_candidates: tuple[str, ...]) -> LocatorLike:
        for selector in selector_candidates:
            locator = page.locator(selector)
            if locator.count() > 0:
                return locator.first()
        raise LookupError("no matching selector found")

    def resolve_input(self, page: PageLike) -> LocatorLike:
        return self._resolve_first(page, self.selectors.input_selectors)

    def resolve_send_button(self, page: PageLike) -> LocatorLike:
        return self._resolve_first(page, self.selectors.send_selectors)

    def resolve_response_block(self, page: PageLike) -> LocatorLike:
        return self._resolve_first(page, self.selectors.response_selectors)

    def send_prompt(self, page: PageLike, prompt: str) -> None:
        input_box = self.resolve_input(page)
        input_box.fill(prompt)
        self.resolve_send_button(page).click()

    def latest_response_text(self, page: PageLike) -> str:
        text = self.resolve_response_block(page).inner_text().strip()
        if not text:
            raise LookupError("assistant response is empty")
        return text
