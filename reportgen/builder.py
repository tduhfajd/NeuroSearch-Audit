from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _resolve_brand_path(template_dir: Path, brand_path: Path | None = None) -> Path:
    return brand_path.resolve() if brand_path else (template_dir / "brand.yml").resolve()


def _load_brand(template_dir: Path, brand_path: Path | None = None) -> dict[str, Any]:
    path = _resolve_brand_path(template_dir, brand_path)
    if not path.exists():
        return {}
    try:
        import yaml
    except Exception:
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _resolve_logo_source(template_dir: Path, brand_path: Path | None = None) -> Path | None:
    brand = _load_brand(template_dir, brand_path)
    logo = brand.get("logo")
    if not logo:
        return None
    base_dir = _resolve_brand_path(template_dir, brand_path).parent
    source = (base_dir / str(logo)).resolve()
    if source.exists():
        return source
    return None


def _copy_logo(template_dir: Path, resource_dir: Path, brand_path: Path | None = None) -> None:
    source = _resolve_logo_source(template_dir, brand_path)
    if source is None:
        return
    target = resource_dir / "logo.png"
    if source.suffix.lower() == ".png":
        shutil.copy2(source, target)
        return
    png_fallback = source.with_suffix(".png")
    if png_fallback.exists():
        shutil.copy2(png_fallback, target)


def _pdf_engine() -> str:
    for candidate in ("lualatex", "xelatex", "pdflatex"):
        if shutil.which(candidate):
            return candidate
    raise RuntimeError("No LaTeX engine found; install lualatex, xelatex, or pdflatex")


def _run_pandoc(cmd: list[str], cwd: Path | None = None) -> None:
    env = os.environ.copy()
    tex_bin = Path("/Library/TeX/texbin")
    if tex_bin.exists():
        env["PATH"] = f"{tex_bin}:{env.get('PATH', '')}"
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"pandoc failed with exit {result.returncode}: {err[:600]}")


def _write_temp(markdown: str, resource_dir: Path | None, suffix: str) -> tuple[Path, Path | None]:
    if resource_dir is not None:
        path = resource_dir / suffix
        path.write_text(markdown, encoding="utf-8")
        return path, path
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False)
    try:
        handle.write(markdown)
    finally:
        handle.close()
    path = Path(handle.name)
    return path, None


def _brand_contact_lines(brand: dict[str, Any]) -> list[str]:
    company = brand.get("company", {}) or {}
    lines: list[str] = []

    display_name = str(company.get("display_name") or brand.get("name") or "").strip()
    legal_name = str(company.get("legal_name") or "").strip()
    if display_name:
        lines.append(f"**{display_name}**")
    if legal_name and legal_name != display_name:
        lines.append(legal_name)

    contact_parts = []
    for key in ("website", "email", "phone", "address"):
        value = str(company.get(key) or "").strip()
        if value:
            contact_parts.append(value)
    if contact_parts:
        lines.append(" | ".join(contact_parts))

    requisites = company.get("requisites", []) or []
    for item in requisites:
        value = str(item).strip()
        if value:
            lines.append(value)
    return lines


def apply_branding(markdown: str, brand_path: Path | None = None, resource_dir: Path | None = None) -> str:
    template_dir = Path(__file__).resolve().parent / "templates" / "default"
    brand = _load_brand(template_dir, brand_path)
    if not brand:
        return markdown

    lines: list[str] = []
    if resource_dir is not None:
        _copy_logo(template_dir, resource_dir, brand_path)
        if (resource_dir / "logo.png").exists():
            lines.append("![](logo.png){ width=100% }")
            lines.append("")

    lines.extend(_brand_contact_lines(brand))
    if not lines:
        return markdown
    return "\n".join(lines).strip() + "\n\n---\n\n" + markdown.lstrip()


def render_pdf(
    markdown: str,
    output_path: Path,
    domain: str = "",
    resource_dir: Path | None = None,
    brand_path: Path | None = None,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template_dir = Path(__file__).resolve().parent / "templates" / "default"
    if resource_dir is None:
        resource_dir = output_path.parent
    resource_dir.mkdir(parents=True, exist_ok=True)
    branded_markdown = apply_branding(markdown.replace("\u2192", "->"), brand_path=brand_path, resource_dir=resource_dir)
    md_path, cleanup_path = _write_temp(branded_markdown, resource_dir, "_client_report_pdf.md")
    header_template = template_dir / "include-header.tex"
    header_path: Path | None = None
    try:
        if header_template.exists():
            header_content = header_template.read_text(encoding="utf-8").replace("REPORTDOMAIN", domain)
            brand = _load_brand(template_dir, brand_path)
            primary = str(brand.get("colors", {}).get("primary", "#1976D2")).strip("#")
            header_content = header_content.replace("1976D2", primary.upper())
            with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", encoding="utf-8", delete=False) as handle:
                handle.write(header_content)
                header_path = Path(handle.name)
        cmd = [
            "pandoc",
            md_path.name if md_path.parent == resource_dir else str(md_path),
            "-o",
            output_path.name if output_path.parent == resource_dir else str(output_path),
            f"--pdf-engine={_pdf_engine()}",
            "--template",
            str(template_dir / "default.latex"),
            "--include-in-header",
            str(header_path) if header_path else str(template_dir / "include-header.tex"),
            "-V",
            "documentclass=article",
            "-V",
            "papersize=a4",
            "-V",
            "geometry:margin=2.5cm",
            "-V",
            "mainfont=Helvetica",
            "-V",
            "sansfont=Helvetica",
            "-V",
            "monofont=Menlo",
        ]
        _run_pandoc(cmd, cwd=resource_dir if md_path.parent == resource_dir else None)
    finally:
        if cleanup_path is not None:
            cleanup_path.unlink(missing_ok=True)
        if header_path is not None:
            header_path.unlink(missing_ok=True)


def render_html(
    markdown: str,
    output_path: Path,
    title: str = "Клиентский отчет",
    resource_dir: Path | None = None,
    brand_path: Path | None = None,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if resource_dir is None:
        resource_dir = output_path.parent
    resource_dir.mkdir(parents=True, exist_ok=True)
    branded_markdown = apply_branding(markdown.replace("\u2192", "->"), brand_path=brand_path, resource_dir=resource_dir)
    md_path, cleanup_path = _write_temp(branded_markdown, resource_dir, "_client_report_html.md")
    try:
        cmd = [
            "pandoc",
            md_path.name if resource_dir and md_path.parent == resource_dir else str(md_path),
            "-o",
            output_path.name if resource_dir and output_path.parent == resource_dir else str(output_path),
            "-s",
            "--toc",
            "--number-sections",
            "--metadata",
            f"title={title}",
        ]
        _run_pandoc(cmd, cwd=resource_dir if resource_dir and md_path.parent == resource_dir else None)
    finally:
        if cleanup_path is not None:
            cleanup_path.unlink(missing_ok=True)


def render_docx(
    markdown: str,
    output_path: Path,
    resource_dir: Path | None = None,
    reference_doc: Path | None = None,
    brand_path: Path | None = None,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if resource_dir is None:
        resource_dir = output_path.parent
    resource_dir.mkdir(parents=True, exist_ok=True)
    branded_markdown = apply_branding(markdown.replace("\u2192", "->"), brand_path=brand_path, resource_dir=resource_dir)
    md_path, cleanup_path = _write_temp(branded_markdown, resource_dir, "_client_report_docx.md")
    try:
        cmd = [
            "pandoc",
            md_path.name if resource_dir and md_path.parent == resource_dir else str(md_path),
            "-o",
            output_path.name if resource_dir and output_path.parent == resource_dir else str(output_path),
            "--toc",
            "--number-sections",
        ]
        if reference_doc and reference_doc.exists():
            cmd.extend(["--reference-doc", str(reference_doc)])
        _run_pandoc(cmd, cwd=resource_dir if resource_dir and md_path.parent == resource_dir else None)
    finally:
        if cleanup_path is not None:
            cleanup_path.unlink(missing_ok=True)
