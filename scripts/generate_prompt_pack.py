#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


PROMPTS = {
    "client_report_prompt.md": {
        "role": "Presale strategist preparing a client-facing audit report.",
        "audience": "Agency client decision-makers.",
        "structure": [
            "Executive summary",
            "Top risks and opportunities",
            "Evidence-backed findings",
            "Recommended next steps",
        ],
    },
    "tech_audit_prompt.md": {
        "role": "Technical lead preparing a technical audit.",
        "audience": "SEO and engineering team.",
        "structure": [
            "Technical state overview",
            "Evidence-backed issues",
            "Contradictions and risks",
            "Technical remediation priorities",
        ],
    },
    "optimization_plan_prompt.md": {
        "role": "Optimization planner creating an implementation roadmap.",
        "audience": "Delivery lead and stakeholders.",
        "structure": [
            "Priority workstreams",
            "P0/P1/P2 initiatives",
            "Expected impact",
            "Acceptance criteria",
        ],
    },
    "work_backlog_prompt.md": {
        "role": "Delivery manager creating a work backlog.",
        "audience": "Implementation team.",
        "structure": [
            "Backlog overview",
            "Tasks grouped by priority",
            "Evidence references",
            "Acceptance criteria",
        ],
    },
    "commercial_offer_prompt.md": {
        "role": "Commercial lead preparing a proposal.",
        "audience": "Prospective client buyer group.",
        "structure": [
            "Commercial framing",
            "Problem-to-solution mapping",
            "Work package outline",
            "Business rationale",
        ],
    },
}

ALLOWED_INPUTS = [
    "analysis/entities.json",
    "analysis/normalized_facts.json",
    "analysis/coverage_report.json",
    "analysis/contradictions.json",
    "analysis/ai_readiness_scores.json",
    "analysis/recommendations.json",
    "manifest.json",
]


def render_prompt(name: str, config: dict[str, object]) -> str:
    sections = "\n".join(f"- {item}" for item in config["structure"])
    inputs = "\n".join(f"- {item}" for item in ALLOWED_INPUTS)
    return (
        f"Role: {config['role']}\n\n"
        f"Audience: {config['audience']}\n\n"
        "Allowed Inputs:\n"
        f"{inputs}\n\n"
        "Document Structure:\n"
        f"{sections}\n\n"
        "Evidence Rules:\n"
        "- Use only facts and findings from the allowed inputs.\n"
        "- Cite evidence in the format `Evidence: [url=<...>; finding=<...>; source=<file>; score=<...>]`.\n"
        "- If evidence is missing, write `Evidence: [data_gap=<description>]`.\n\n"
        "No Fabrication Policy:\n"
        "- Do not invent facts, metrics, URLs, or client context.\n"
        "- Contradictions must be called out as requiring verification.\n"
        "- No fabrication is allowed under any circumstance.\n\n"
        "Output Constraints:\n"
        "- Language: Russian.\n"
        "- Tone: evidence-first, direct, and business-usable.\n"
        "- Keep recommendations tied to the supplied findings.\n"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_prompt_pack.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    prompts_dir = package_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    for filename, config in PROMPTS.items():
        (prompts_dir / filename).write_text(render_prompt(filename, config), encoding="utf-8")

    print("prompt pack generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
