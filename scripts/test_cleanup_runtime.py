from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.cleanup_runtime import cleanup_runtime


def _touch_dir(path: Path, modified_at: datetime) -> None:
    path.mkdir(parents=True, exist_ok=True)
    timestamp = modified_at.timestamp()
    path.touch()
    for parent in [path]:
        parent.touch()
        import os

        os.utime(parent, (timestamp, timestamp))


def test_cleanup_runtime_dry_run_and_apply(tmp_path: Path) -> None:
    now = datetime(2026, 3, 12, tzinfo=timezone.utc)
    old_attempt = tmp_path / "runtime" / "aud_old" / "attempts" / "001"
    fresh_attempt = tmp_path / "runtime" / "aud_new" / "attempts" / "001"
    old_batch = tmp_path / "runtime_batches" / "batch_old"
    package_dir = tmp_path / "audit_package" / "aud_old"

    _touch_dir(old_attempt, now - timedelta(days=10))
    _touch_dir(fresh_attempt, now - timedelta(days=1))
    _touch_dir(old_batch, now - timedelta(days=8))
    package_dir.mkdir(parents=True, exist_ok=True)

    dry_run = cleanup_runtime(tmp_path, retention_days=7, apply=False, now=now)
    assert len(dry_run["candidates"]) == 2
    assert len(dry_run["deleted"]) == 0
    assert old_attempt.exists()
    assert old_batch.exists()
    assert package_dir.exists()

    applied = cleanup_runtime(tmp_path, retention_days=7, apply=True, now=now)
    deleted_paths = {item["path"] for item in applied["deleted"]}
    assert "runtime/aud_old/attempts/001" in deleted_paths
    assert "runtime_batches/batch_old" in deleted_paths
    assert not old_attempt.exists()
    assert not old_batch.exists()
    assert fresh_attempt.exists()
    assert package_dir.exists()
