#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXAMPLE_DIR = ROOT / "branding" / "example"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a ready-to-edit branding folder from the example template.")
    parser.add_argument(
        "target",
        nargs="?",
        default="branding/my-brand",
        help="Target directory for the branding bundle (default: branding/my-brand)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target directory if it already exists",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Ask for brand name and company details, then write them into brand.yml",
    )
    return parser.parse_args()


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def write_brand_yaml(path: Path, data: dict[str, str]) -> None:
    requisites = [item.strip() for item in data["requisites"].split("|") if item.strip()]
    lines = [
        f'name: "{data["name"]}"',
        'logo: "logo.png"',
        "",
        "colors:",
        '  primary: "#1F4ED8"',
        '  secondary: "#0F172A"',
        '  accent: "#475569"',
        "",
        "company:",
        f'  display_name: "{data["display_name"]}"',
        f'  legal_name: "{data["legal_name"]}"',
        f'  website: "{data["website"]}"',
        f'  email: "{data["email"]}"',
        f'  phone: "{data["phone"]}"',
        f'  address: "{data["address"]}"',
        "  requisites:",
    ]
    if requisites:
        for item in requisites:
            lines.append(f'    - "{item}"')
    else:
        lines.append('    - "ИНН 0000000000"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    target = Path(args.target)
    if not target.is_absolute():
        target = (ROOT / target).resolve()

    if target.exists():
        if not args.force:
            print(f"Target already exists: {target}")
            print("Re-run with --force to overwrite it.")
            return 1
        shutil.rmtree(target)

    shutil.copytree(EXAMPLE_DIR, target)

    source_logo = (ROOT / "logo.png").resolve()
    target_logo = target / "logo.png"
    if source_logo.exists() and not target_logo.exists():
        shutil.copy2(source_logo, target_logo)

    if args.interactive:
        defaults = {
            "name": "Мой Бренд",
            "display_name": "Мой Бренд",
            "legal_name": 'ООО «Мой Бренд»',
            "website": "https://example.com",
            "email": "hello@example.com",
            "phone": "+7 (999) 123-45-67",
            "address": "Россия, Москва, Примерная улица, 1",
            "requisites": "ИНН 7700000000 | ОГРН 1027700000000 | р/с 40702810000000000000 в АО «Банк» | БИК 044525000",
        }
        data = {key: prompt(key.replace("_", " ").capitalize(), default) for key, default in defaults.items()}
        write_brand_yaml(target / "brand.yml", data)

    print(f"Branding bundle created: {target}")
    print(f"Edit this file first: {target / 'brand.yml'}")
    print(f"Replace this logo file: {target / 'logo.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
