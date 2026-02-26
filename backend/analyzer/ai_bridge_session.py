from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

DEFAULT_STORAGE_STATE_PATH = Path("chatgpt_session/storage_state.json")
CHATGPT_URL = "https://chat.openai.com/"


class SessionStateError(RuntimeError):
    pass


class SessionBridge(Protocol):
    def capture(self, url: str, storage_state_path: Path) -> None: ...


@dataclass(slots=True)
class StorageState:
    path: Path
    data: dict


def load_storage_state(path: Path = DEFAULT_STORAGE_STATE_PATH) -> StorageState:
    if not path.exists():
        raise SessionStateError(f"storage state not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionStateError(f"invalid storage state JSON: {path}") from exc

    if not isinstance(payload, dict) or "cookies" not in payload or "origins" not in payload:
        raise SessionStateError("storage state must contain 'cookies' and 'origins'")

    return StorageState(path=path, data=payload)


def save_storage_state(payload: dict, path: Path = DEFAULT_STORAGE_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class PlaywrightSessionBridge:
    def capture(self, url: str, storage_state_path: Path) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # noqa: BLE001
            raise SessionStateError("playwright is not available") from exc

        storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            try:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    input(
                        "Complete ChatGPT login in browser, "
                        "then press Enter to save session state... "
                    )
                except EOFError:
                    page.wait_for_timeout(5000)
                page.context.storage_state(path=str(storage_state_path))
            finally:
                browser.close()


def setup_session_state(
    *,
    bridge: SessionBridge | None = None,
    storage_state_path: Path = DEFAULT_STORAGE_STATE_PATH,
) -> StorageState:
    active_bridge = bridge or PlaywrightSessionBridge()
    active_bridge.capture(CHATGPT_URL, storage_state_path)
    return load_storage_state(storage_state_path)
