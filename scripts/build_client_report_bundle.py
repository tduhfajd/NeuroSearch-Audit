#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reportgen.builder import apply_branding, render_docx, render_html, render_pdf
from scripts.build_client_report_input import ensure_approved, load_json
from scripts.generate_expert_report import main as generate_expert_report_main


def default_output_dir(package_dir: Path) -> Path:
    root_dir = package_dir.parents[1]
    audit_id = package_dir.name
    return root_dir / "deliverables" / audit_id / "client-report"


def ensure_client_report(package_dir: Path) -> Path:
    report_path = package_dir / "exports" / "expert_report.md"
    input_path = package_dir / "exports" / "client_report_input.json"
    if report_path.exists() and input_path.exists():
        return report_path
    exit_code = generate_expert_report_main(["generate_expert_report.py", str(package_dir)])
    if exit_code != 0:
        raise RuntimeError("expert report generation failed before bundle build")
    return report_path


def build_basename(package_dir: Path) -> str:
    report_input = load_json(package_dir / "exports" / "client_report_input.json")
    domain = report_input.get("site", {}).get("primary_domain", package_dir.name) or package_dir.name
    safe_domain = str(domain).replace("/", "_")
    return f"report_{safe_domain}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build branded client-report bundle from approved audit package")
    parser.add_argument("package_dir", help="Path to audit_package/<audit_id>")
    parser.add_argument("--output-dir", help="Directory for generated deliverables")
    parser.add_argument("--brand", help="Optional path to reportgen brand.yml")
    parser.add_argument(
        "--formats",
        default="pdf,html,docx",
        help="Comma-separated formats: pdf,html,docx (default: pdf,html,docx)",
    )
    return parser.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    package_dir = Path(args.package_dir)
    issues = ensure_approved(package_dir)
    if issues:
        print("client report bundle generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    report_path = ensure_client_report(package_dir)
    markdown = report_path.read_text(encoding="utf-8")
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir(package_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    basename = build_basename(package_dir)
    report_input = load_json(package_dir / "exports" / "client_report_input.json")
    title = f"Аудит сайта: {report_input.get('site', {}).get('primary_domain', package_dir.name)}"
    domain = report_input.get("site", {}).get("primary_domain", package_dir.name)
    formats = {item.strip().lower() for item in args.formats.split(",") if item.strip()}
    brand_path = Path(args.brand) if args.brand else None

    if "pdf" in formats:
        render_pdf(markdown, output_dir / f"{basename}.pdf", domain=domain, resource_dir=output_dir, brand_path=brand_path)
    if "html" in formats:
        render_html(markdown, output_dir / f"{basename}.html", title=title, resource_dir=output_dir, brand_path=brand_path)
    if "docx" in formats:
        render_docx(markdown, output_dir / f"{basename}.docx", resource_dir=output_dir, brand_path=brand_path)

    branded_markdown = apply_branding(markdown, brand_path=brand_path, resource_dir=output_dir)
    (output_dir / f"{basename}.md").write_text(branded_markdown, encoding="utf-8")
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
