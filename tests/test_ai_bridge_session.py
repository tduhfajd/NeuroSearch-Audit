from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.analyzer.ai_bridge import session_health
from backend.analyzer.ai_bridge_selectors import ChatGPTSelectorAdapter
from backend.analyzer.ai_bridge_session import (
    SessionStateError,
    load_storage_state,
    save_storage_state,
    setup_session_state,
)


class DummyBridge:
    def capture(self, url: str, storage_state_path: Path) -> None:
        _ = url
        save_storage_state(
            {
                "cookies": [{"name": "session", "value": "x"}],
                "origins": [{"origin": "https://chat.openai.com"}],
            },
            storage_state_path,
        )


def test_setup_saves_storage_state(tmp_path: Path) -> None:
    storage = tmp_path / "state.json"

    state = setup_session_state(bridge=DummyBridge(), storage_state_path=storage)

    assert storage.exists()
    assert state.path == storage
    assert len(state.data["cookies"]) == 1


def test_storage_state_loader_validates_required_fields(tmp_path: Path) -> None:
    storage = tmp_path / "state.json"
    storage.write_text(json.dumps({"cookies": []}), encoding="utf-8")

    with pytest.raises(SessionStateError):
        load_storage_state(storage)


def test_session_loader_reports_missing_file(tmp_path: Path) -> None:
    ok, detail = session_health(tmp_path / "missing.json")
    assert ok is False
    assert "not found" in detail


class FakeLocator:
    def __init__(self, count_value: int = 0, text: str = "") -> None:
        self._count = count_value
        self._text = text
        self.filled = ""
        self.clicked = False

    def count(self) -> int:
        return self._count

    def first(self) -> "FakeLocator":
        return self

    def fill(self, text: str) -> None:
        self.filled = text

    def click(self) -> None:
        self.clicked = True

    def inner_text(self) -> str:
        return self._text


class FakePage:
    def __init__(self, mapping: dict[str, FakeLocator]) -> None:
        self.mapping = mapping

    def locator(self, selector: str) -> FakeLocator:
        return self.mapping.get(selector, FakeLocator())


def test_selectors_fallback_resolves_first_available_input_and_send() -> None:
    adapter = ChatGPTSelectorAdapter()
    input_locator = FakeLocator(count_value=1)
    send_locator = FakeLocator(count_value=1)
    response_locator = FakeLocator(count_value=1, text="assistant response")

    page = FakePage(
        {
            "textarea": input_locator,
            "button:has-text('Send')": send_locator,
            ".markdown.prose": response_locator,
        }
    )

    adapter.send_prompt(page, "hello")

    assert input_locator.filled == "hello"
    assert send_locator.clicked is True


def test_response_block_extracts_non_empty_text() -> None:
    adapter = ChatGPTSelectorAdapter()
    response_locator = FakeLocator(count_value=1, text="final answer")
    page = FakePage({".markdown.prose": response_locator})

    assert adapter.latest_response_text(page) == "final answer"
