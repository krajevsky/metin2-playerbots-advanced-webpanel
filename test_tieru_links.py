from unittest.mock import patch

import app as panel


def test_tieru_link_uses_public_host_when_config_is_localhost(monkeypatch):
    monkeypatch.setenv("TIERU_PANEL_URL", "http://127.0.0.1:7788")
    with panel.app.test_request_context("http://57.128.176.139:7790/maps"), \
         patch.object(panel, "settings", return_value={"ui_language": "pl"}):
        assert panel.globals_for_templates()["tieru_url"] == "http://57.128.176.139:7788"


def test_tieru_link_preserves_explicit_public_url(monkeypatch):
    monkeypatch.setenv("TIERU_PANEL_URL", "https://panel.example.com:7788/")
    with panel.app.test_request_context("http://57.128.176.139:7790/maps"), \
         patch.object(panel, "settings", return_value={"ui_language": "pl"}):
        assert panel.globals_for_templates()["tieru_url"] == "https://panel.example.com:7788"
