from __future__ import annotations

import base64
from pathlib import Path

import scripts.build_client_report_bundle as bundle


def test_build_client_report_bundle_html_and_docx(tmp_path: Path, monkeypatch) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True)
    (exports_dir / "expert_report.md").write_text("# Test report\n\nHello\n", encoding="utf-8")
    (exports_dir / "client_report_input.json").write_text(
        '{"site":{"primary_domain":"example.com"},"schema_version":"1.0.0"}\n',
        encoding="utf-8",
    )
    (package_dir / "manifest.json").write_text('{"stage_status":{"validate":"completed"}}\n', encoding="utf-8")
    monkeypatch.setattr(bundle, "ensure_approved", lambda _package_dir: [])

    output_dir = tmp_path / "out"
    exit_code = bundle.main(
        [
            "build_client_report_bundle.py",
            str(package_dir),
            "--output-dir",
            str(output_dir),
            "--formats",
            "html,docx",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "report_example.com.html").exists()
    assert (output_dir / "report_example.com.docx").exists()
    assert (output_dir / "report_example.com.md").exists()


def test_build_client_report_bundle_with_custom_brand(tmp_path: Path, monkeypatch) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    exports_dir = package_dir / "exports"
    brand_dir = tmp_path / "brand"
    exports_dir.mkdir(parents=True)
    brand_dir.mkdir(parents=True)

    (exports_dir / "expert_report.md").write_text("# Test report\n\nHello\n", encoding="utf-8")
    (exports_dir / "client_report_input.json").write_text(
        '{"site":{"primary_domain":"example.com"},"schema_version":"1.0.0"}\n',
        encoding="utf-8",
    )
    (package_dir / "manifest.json").write_text('{"stage_status":{"validate":"completed"}}\n', encoding="utf-8")
    (brand_dir / "brand.yml").write_text(
        "\n".join(
            [
                'name: "Custom Brand"',
                'logo: "logo.png"',
                "company:",
                '  display_name: "Custom Brand"',
                '  legal_name: "ООО Custom Brand"',
                '  email: "hello@example.com"',
                "  requisites:",
                '    - "ИНН 1234567890"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (brand_dir / "logo.png").write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn1l7sAAAAASUVORK5CYII="))
    monkeypatch.setattr(bundle, "ensure_approved", lambda _package_dir: [])

    output_dir = tmp_path / "out"
    exit_code = bundle.main(
        [
            "build_client_report_bundle.py",
            str(package_dir),
            "--output-dir",
            str(output_dir),
            "--formats",
            "html",
            "--brand",
            str(brand_dir / "brand.yml"),
        ]
    )

    assert exit_code == 0
    report_markdown = (output_dir / "report_example.com.md").read_text(encoding="utf-8")
    assert "Custom Brand" in report_markdown
    assert "ИНН 1234567890" in report_markdown
    assert (output_dir / "logo.png").exists()
