from __future__ import annotations

from pathlib import Path
import json
import sys

from python.common.contracts import TechnicalPageInput, load_json
from python.semantic.page_blocks import build_page_blocks


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m python.semantic.cli <technical-page.json>", file=sys.stderr)
        return 1

    path = Path(argv[1])
    payload = load_json(path)
    page = TechnicalPageInput.from_json(payload)
    result = build_page_blocks(page)
    print(json.dumps(result.to_json(), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
