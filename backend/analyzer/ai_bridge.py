from __future__ import annotations

import argparse
import asyncio
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sqlalchemy.orm import Session

from backend.analyzer.ai_bridge_parser import METRIC_KEYS, parse_with_retries
from backend.analyzer.ai_bridge_prompt import build_page_prompt
from backend.analyzer.ai_bridge_selectors import ChatGPTSelectorAdapter
from backend.analyzer.ai_bridge_session import (
    DEFAULT_STORAGE_STATE_PATH,
    SessionStateError,
    load_storage_state,
    setup_session_state,
)
from backend.analyzer.scoring import calculate_avri_score
from backend.db.models import Audit, Page


class DomainError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ReauthRequiredError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__("reauth_required", message, retryable=False)


class RateLimitError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__("rate_limit", message, retryable=True)


class ChatGPTTransport(Protocol):
    def send_prompt(self, prompt: str) -> str: ...


@dataclass(slots=True)
class AIAnalyzeSummary:
    audit_id: int
    status: str
    processed_pages: int
    avri_score: float | None
    errors: list[str]


class PlaywrightChatGPTTransport:
    def __init__(self, storage_state_path: Path = DEFAULT_STORAGE_STATE_PATH) -> None:
        self.storage_state_path = storage_state_path
        self.adapter = ChatGPTSelectorAdapter()

    def _send_prompt_sync(self, prompt: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("playwright is not available") from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(storage_state=str(self.storage_state_path))
                page = context.new_page()
                page.goto("https://chat.openai.com/", wait_until="domcontentloaded", timeout=60000)
                self.adapter.send_prompt(page, prompt)
                page.wait_for_timeout(1200)
                return self.adapter.latest_response_text(page)
            finally:
                browser.close()

    def send_prompt(self, prompt: str) -> str:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return self._send_prompt_sync(prompt)

        result: dict[str, str] = {}
        error: dict[str, Exception] = {}

        def _target() -> None:
            try:
                result["value"] = self._send_prompt_sync(prompt)
            except Exception as exc:  # noqa: BLE001
                error["value"] = exc

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        thread.join()

        if "value" in error:
            raise error["value"]
        return result["value"]


def setup_cli(storage_state_path: Path = DEFAULT_STORAGE_STATE_PATH) -> int:
    try:
        state = setup_session_state(storage_state_path=storage_state_path)
    except SessionStateError as exc:
        print(f"setup failed: {exc}")
        return 1

    print(f"storage_state_saved={state.path}")
    print(f"cookies_count={len(state.data.get('cookies', []))}")
    print(f"origins_count={len(state.data.get('origins', []))}")
    return 0


def session_health(storage_state_path: Path = DEFAULT_STORAGE_STATE_PATH) -> tuple[bool, str]:
    try:
        state = load_storage_state(storage_state_path)
    except SessionStateError as exc:
        return False, str(exc)

    cookies = state.data.get("cookies", [])
    if not cookies:
        return False, "storage state has no cookies"
    return True, "ok"


def _top_pages_for_ai(db: Session, audit_id: int, limit: int = 10) -> list[Page]:
    return (
        db.query(Page)
        .filter(Page.audit_id == audit_id)
        .order_by(Page.inlinks_count.desc(), Page.url.asc())
        .limit(limit)
        .all()
    )


def _extract_metric_rows(pages: list[Page]) -> list[dict[str, float]]:
    metric_rows: list[dict[str, float]] = []
    for page in pages:
        payload = page.ai_scores or {}
        if not isinstance(payload, dict):
            continue
        scores = payload.get("scores")
        if not isinstance(scores, dict):
            continue
        try:
            metric_rows.append({key: float(scores[key]) for key in METRIC_KEYS})
        except (TypeError, ValueError, KeyError):
            continue
    return metric_rows


def _send_with_backoff(
    send_prompt: Callable[[str], str],
    prompt: str,
    *,
    max_retries: int,
    sleep_func: Callable[[float], None],
    initial_backoff_seconds: float = 2.0,
) -> str:
    delay = initial_backoff_seconds
    for attempt in range(max_retries + 1):
        try:
            return send_prompt(prompt)
        except RateLimitError:
            if attempt >= max_retries:
                raise
            sleep_func(delay)
            delay *= 2.0


def run_ai_analyze(
    db: Session,
    audit_id: int,
    *,
    transport: ChatGPTTransport,
    storage_state_path: Path = DEFAULT_STORAGE_STATE_PATH,
    min_interval_seconds: float = 15.0,
    max_rate_limit_retries: int = 2,
    sleep_func: Callable[[float], None] = time.sleep,
    time_func: Callable[[], float] = time.monotonic,
) -> AIAnalyzeSummary:
    audit = db.get(Audit, audit_id)
    if audit is None:
        raise LookupError(f"audit {audit_id} not found")

    ok, detail = session_health(storage_state_path)
    if not ok:
        raise ReauthRequiredError(detail)

    pages = _top_pages_for_ai(db, audit_id=audit_id, limit=10)
    errors: list[str] = []
    last_prompt_time: float | None = None

    for page in pages:
        if last_prompt_time is not None:
            elapsed = time_func() - last_prompt_time
            wait_seconds = min_interval_seconds - elapsed
            if wait_seconds > 0:
                sleep_func(wait_seconds)

        prompt = build_page_prompt(page)
        try:
            parsed_result = parse_with_retries(
                lambda current_prompt: _send_with_backoff(
                    transport.send_prompt,
                    current_prompt,
                    max_retries=max_rate_limit_retries,
                    sleep_func=sleep_func,
                ),
                prompt,
                max_attempts=3,
            )
        except RateLimitError:
            page.ai_scores = {
                "scores": None,
                "recommendations": None,
                "raw_response": None,
                "diagnostics": {
                    "attempts": max_rate_limit_retries + 1,
                    "valid_json": False,
                    "error": "rate_limit",
                },
                "status": "rate_limit_error",
            }
            errors.append(f"rate_limit_error:{page.url}")
            last_prompt_time = time_func()
            continue

        last_prompt_time = time_func()
        if parsed_result.diagnostics["valid_json"]:
            scores = {k: parsed_result.parsed[k] for k in METRIC_KEYS}
            page.ai_scores = {
                "scores": scores,
                "recommendations": parsed_result.parsed["recommendations"],
                "raw_response": parsed_result.raw_response,
                "diagnostics": parsed_result.diagnostics,
            }
        else:
            page.ai_scores = {
                "scores": None,
                "recommendations": None,
                "raw_response": parsed_result.raw_response,
                "diagnostics": parsed_result.diagnostics,
                "status": "parse_error",
            }
            errors.append(f"parse_error:{page.url}")

    avri = calculate_avri_score(_extract_metric_rows(pages))
    audit.avri_score = avri
    db.commit()

    status = "partial" if errors else "ok"
    return AIAnalyzeSummary(
        audit_id=audit_id,
        status=status,
        processed_pages=len(pages),
        avri_score=avri,
        errors=errors,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Bridge utilities")
    parser.add_argument("--setup", action="store_true", help="capture Playwright storage state")
    parser.add_argument("--health", action="store_true", help="check local storage_state health")
    parser.add_argument(
        "--storage-state",
        default=str(DEFAULT_STORAGE_STATE_PATH),
        help="path to Playwright storage state",
    )
    args = parser.parse_args()

    storage_state_path = Path(args.storage_state)

    if args.setup:
        return setup_cli(storage_state_path)

    if args.health:
        ok, message = session_health(storage_state_path)
        print(json.dumps({"status": "ok" if ok else "reauth_required", "detail": message}))
        return 0 if ok else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
