from __future__ import annotations

import json
from pathlib import Path

import scripts.publish_analysis_run as publish


def test_publish_run_creates_snapshot_layout(tmp_path: Path, monkeypatch) -> None:
    artifact_root = tmp_path / "artifacts"
    package_dir = artifact_root / "audit_package" / "aud_test"
    runtime_dir = artifact_root / "runtime" / "aud_test" / "attempts" / "001"
    exports_dir = package_dir / "exports"
    analysis_dir = package_dir / "analysis"
    exports_dir.mkdir(parents=True)
    analysis_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)

    (analysis_dir / "entities.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "audit_id": "aud_test",
                "entities": [{"type": "page", "label": "https://example.com/"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_dir / "run_state.json").write_text('{"audit_id":"aud_test"}\n', encoding="utf-8")

    def fake_documents(pkg_dir: Path, bundle_dir: Path, brand_path: Path | None = None) -> None:
        exports = pkg_dir / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        (exports / "client_report_input.json").write_text(
            json.dumps({"site": {"primary_domain": "example.com"}}) + "\n",
            encoding="utf-8",
        )
        (exports / "expert_report.json").write_text('{"schema_version":"1.0.0"}\n', encoding="utf-8")
        (exports / "expert_report.md").write_text("# Report\n", encoding="utf-8")
        (exports / "internal_technical_report.md").write_text("# Internal\n", encoding="utf-8")
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "report_example.com.pdf").write_text("pdf", encoding="utf-8")
        (bundle_dir / "report_example.com.md").write_text("md", encoding="utf-8")

    monkeypatch.setattr(publish, "ensure_documents", fake_documents)

    run_dir = publish.publish_run(artifact_root, "aud_test", tmp_path)

    assert run_dir == tmp_path / "out" / "test-example.com"
    assert (run_dir / "audit_package" / "aud_test" / "exports" / "expert_report.md").exists()
    assert (run_dir / "runtime" / "aud_test" / "attempts" / "001" / "run_state.json").exists()
    assert (run_dir / "deliverables" / "client-report" / "report_example.com.pdf").exists()
    assert (tmp_path / "latest_reports" / "client_report_example.com.pdf").exists()
    assert (tmp_path / "latest_reports" / "internal_technical_report_example.com.md").exists()
    snapshot = json.loads((run_dir / "run_snapshot.json").read_text(encoding="utf-8"))
    assert snapshot["audit_id"] == "aud_test"
    assert snapshot["domain"] == "example.com"
