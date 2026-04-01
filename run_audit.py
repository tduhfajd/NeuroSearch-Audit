#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a full NeuroSearch site audit and generate a client report bundle."
    )
    parser.add_argument("url", help="Site URL, for example https://example.com")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=1,
        help="Crawl depth for the audit run (default: 1)",
    )
    parser.add_argument(
        "--brand",
        help="Optional path to brand.yml with custom logo and company details",
    )
    return parser.parse_args()


def ensure_url(url: str) -> str:
    value = url.strip()
    if not value:
        raise ValueError("URL is required")
    if "://" not in value:
        value = f"https://{value}"
    return value


def ensure_file(path: Path, description: str) -> None:
    if not path.exists():
        raise RuntimeError(f"{description} not found: {path}")


def ensure_command(name: str, install_hint: str) -> None:
    if shutil.which(name):
        return
    raise RuntimeError(f"Command `{name}` was not found. {install_hint}")


def preflight(brand: str | None = None) -> None:
    ensure_file(ROOT / "go.mod", "Go module file")
    ensure_file(ROOT / "requirements.txt", "Python requirements file")
    ensure_file(ROOT / "scripts" / "render_page.mjs", "Playwright render script")
    ensure_file(ROOT / "package.json", "Node.js package file")

    ensure_command("go", "Install Go and run the setup script again.")
    ensure_command("node", "Install Node.js and run the setup script again.")
    ensure_command("npm", "Install Node.js/npm and run the setup script again.")
    ensure_command("npx", "Install Node.js/npm and run the setup script again.")
    ensure_command("pandoc", "Install Pandoc and run the setup script again.")

    if not any(shutil.which(candidate) for candidate in ("lualatex", "xelatex", "pdflatex")):
        raise RuntimeError(
            "No LaTeX engine was found. Install one of: lualatex, xelatex, pdflatex."
        )
    if brand:
        brand_path = Path(brand).expanduser()
        if not brand_path.is_absolute():
            brand_path = (ROOT / brand_path).resolve()
        ensure_file(brand_path, "Brand config")


def latest_report_dir(out_dir: Path) -> Path | None:
    if not out_dir.exists():
        return None
    dirs = [path for path in out_dir.iterdir() if path.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda path: path.stat().st_mtime)


def print_report_paths(run_dir: Path) -> None:
    bundle_dir = run_dir / "deliverables" / "client-report"
    package_dirs = sorted((run_dir / "audit_package").glob("*/"))
    internal_report = None
    latest_reports_dir = ROOT / "latest_reports"
    if package_dirs:
        candidate = package_dirs[0] / "exports" / "internal_technical_report.md"
        if candidate.exists():
            internal_report = candidate
    if not bundle_dir.exists():
        print(f"Audit completed. Results were published to: {run_dir}")
        if latest_reports_dir.exists():
            print(f"Easy-access reports: {latest_reports_dir}")
        if internal_report is not None:
            print(f"Internal technical report: {internal_report}")
        return

    print("\nAudit completed.")
    print(f"Results directory: {run_dir}")
    if latest_reports_dir.exists():
        print(f"Easy-access reports: {latest_reports_dir}")

    for extension in ("pdf", "html", "docx", "md"):
        matches = sorted(bundle_dir.glob(f"*.{extension}"))
        if matches:
            print(f"{extension.upper()} report: {matches[0]}")
    if internal_report is not None:
        print(f"Internal technical report: {internal_report}")


def main() -> int:
    args = parse_args()
    try:
        url = ensure_url(args.url)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    try:
        preflight(args.brand)
    except RuntimeError as error:
        print(f"Preflight check failed: {error}", file=sys.stderr)
        print("Run the setup script first and then try again.", file=sys.stderr)
        return 2

    before = latest_report_dir(ROOT / "out")
    cmd = [
        "go",
        "run",
        "./cmd/runtime",
        "--url",
        url,
        "--project-root",
        str(ROOT),
        "--python-bin",
        sys.executable,
        "--max-depth",
        str(args.max_depth),
    ]
    if args.brand:
        brand_path = Path(args.brand).expanduser()
        if not brand_path.is_absolute():
            brand_path = (ROOT / brand_path).resolve()
        cmd.extend(["--brand", str(brand_path)])

    print(f"Starting audit for {url}", flush=True)
    print(f"Working directory: {ROOT}", flush=True)
    print("Preflight check passed. Running audit...", flush=True)

    env = os.environ.copy()
    result = subprocess.run(cmd, cwd=ROOT, env=env)
    if result.returncode != 0:
        return result.returncode

    after = latest_report_dir(ROOT / "out")
    if after is not None and after != before:
        print_report_paths(after)
    elif after is not None:
        print_report_paths(after)
    else:
        print("Audit completed, but no published report directory was found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
