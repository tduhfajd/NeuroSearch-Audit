from __future__ import annotations

from pathlib import Path
import json
import sys

from python.analysis.normalize import normalize_page_blocks
from python.common.contracts import load_json


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m python.analysis.cli <page-blocks.json>", file=sys.stderr)
        return 1

    path = Path(argv[1])
    payload = load_json(path)
    entities, facts = normalize_page_blocks(payload)
    print(
        json.dumps(
            {
                "entities": entities.to_json(),
                "facts": facts.to_json(),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
