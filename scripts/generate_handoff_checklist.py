#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_contracts, validate_evidence, validate_prompts


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_approved(package_dir: Path) -> list[str]:
    issues = validate_contracts(package_dir) + validate_evidence(package_dir) + validate_prompts(package_dir)
    manifest = load_json(package_dir / "manifest.json")
    if manifest.get("stage_status", {}).get("validate") != "completed":
        issues.append("package validate stage is not completed")
    normalized: list[str] = []
    for issue in issues:
        if isinstance(issue, str):
            normalized.append(issue)
        else:
            normalized.append(f"{issue.path}: {issue.message}")
    return normalized


def handoff_dir_for(package_dir: Path) -> Path:
    return package_dir.parent.parent / "handoff" / package_dir.name


def render_checklist(manifest: dict) -> str:
    audit_id = manifest["audit_id"]
    lines: list[str] = []
    lines.append("# Handoff Checklist")
    lines.append("")
    lines.append(f"- Audit ID: `{audit_id}`")
    lines.append("- Preconditions:")
    lines.append("  - `manifest.stage_status.validate == completed`")
    lines.append("  - `exports/review_brief.md` exists")
    lines.append("  - `exports/backlog.json` exists")
    lines.append("")
    lines.append("## Steps")
    lines.append("")
    lines.append("1. Open `exports/review_brief.md` and confirm top gaps and contradictions are understood.")
    lines.append("2. Open `exports/backlog.json` and confirm priority recommendations are usable.")
    lines.append("3. Confirm the prompt pack in `prompts/` is present and package approval is still valid.")
    lines.append("4. Record `review_prepared` using `scripts/record_handoff_event.py`.")
    lines.append("5. Handoff the approved package and prompt pack to the external AI workflow.")
    lines.append("6. Record `ai_handoff_sent` with the exact artifacts used.")
    lines.append("7. After receiving AI outputs, record `post_handoff_captured` with notes about follow-up actions.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_handoff_checklist.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("handoff checklist blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    manifest = load_json(package_dir / "manifest.json")
    handoff_dir = handoff_dir_for(package_dir)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    (handoff_dir / "handoff_checklist.md").write_text(render_checklist(manifest) + "\n", encoding="utf-8")

    print("handoff checklist generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
