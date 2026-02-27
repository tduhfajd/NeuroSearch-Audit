from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

SETTINGS_PATH = Path("chatgpt_session/app_settings.json")
_LOCK = Lock()


def _read_raw() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_raw(payload: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_settings() -> dict[str, Any]:
    with _LOCK:
        return _read_raw()


def save_settings(*, pagespeed_api_key: str | None) -> dict[str, Any]:
    normalized = pagespeed_api_key.strip() if isinstance(pagespeed_api_key, str) else None
    with _LOCK:
        payload = _read_raw()
        payload["pagespeed_api_key"] = normalized or None
        _write_raw(payload)
        return payload


def get_pagespeed_api_key() -> str | None:
    payload = load_settings()
    value = payload.get("pagespeed_api_key")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
