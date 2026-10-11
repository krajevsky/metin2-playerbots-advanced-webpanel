from unittest.mock import patch

import app as panel


def test_legacy_theme_is_locked_to_laka():
    with patch.object(panel, "rows", return_value=[{"name": "theme", "value": "ocean"}]):
        assert panel.settings()["theme"] == "laka"
    values, error = panel.validate_display_settings({"panel_name": "Test", "theme": "ember"})
    assert error is None
    assert values["theme"] == "laka"


def test_language_switch_only_updates_language_and_uses_safe_redirect():
    panel.app.config["TESTING"] = True
    with patch.object(panel, "settings", return_value={"auth_enabled": "0", "setup_complete": "1"}), \
         patch.object(panel, "write_settings") as write:
        client = panel.app.test_client()
        response = client.post("/language", data={"language": "en", "next": "/players?page=2"})
        assert response.status_code == 302
        assert response.location.endswith("/players?page=2")
        write.assert_called_once_with({"ui_language": "en"})
        response = client.post("/language", data={"language": "pl", "next": "//evil.example/"})
        assert response.status_code == 302
        assert response.location.endswith("/")
        assert client.post("/language", data={"language": "de"}).status_code == 400
