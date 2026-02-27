from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_settings_default_is_empty(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("backend.runtime_settings.SETTINGS_PATH", tmp_path / "app_settings.json")

    response = client.get("/settings")

    assert response.status_code == 200
    assert response.json() == {
        "pagespeed_api_key_present": False,
        "pagespeed_api_key_preview": None,
    }


def test_settings_save_and_read(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("backend.runtime_settings.SETTINGS_PATH", tmp_path / "app_settings.json")

    save_response = client.post("/settings", json={"pagespeed_api_key": "AIzaTestKey123"})
    assert save_response.status_code == 200
    assert save_response.json()["pagespeed_api_key_present"] is True

    read_response = client.get("/settings")
    payload = read_response.json()
    assert payload["pagespeed_api_key_present"] is True
    assert payload["pagespeed_api_key_preview"] is not None


def test_settings_clear_key(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("backend.runtime_settings.SETTINGS_PATH", tmp_path / "app_settings.json")
    client.post("/settings", json={"pagespeed_api_key": "AIzaWillBeCleared"})

    clear_response = client.post("/settings", json={"pagespeed_api_key": None})

    assert clear_response.status_code == 200
    assert clear_response.json() == {
        "pagespeed_api_key_present": False,
        "pagespeed_api_key_preview": None,
    }
