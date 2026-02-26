from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.analyzer.ai_bridge_selectors import ChatGPTSelectorAdapter
from backend.analyzer.ai_bridge_session import (
    DEFAULT_STORAGE_STATE_PATH,
    SessionStateError,
    load_storage_state,
    setup_session_state,
)


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

    # Keep default import path wired for future ai-analyze implementation.
    _ = ChatGPTSelectorAdapter()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
