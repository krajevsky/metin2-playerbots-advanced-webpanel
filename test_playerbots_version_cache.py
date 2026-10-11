"""A cached dashboard must not override a newer installed Playerbots version."""
import time
from unittest.mock import patch

import app as panel


def test_cached_dashboard_uses_current_playerbots_version():
    current = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl", "theme": "laka"}
    cached = {"at": time.time(), "data": {"world_summary": {
        "version": "2.2.87",
        "release": {"installed": "2.2.87", "latest": "2.2.88", "behind": True},
    }}}
    updated = {"installed": "2.2.88", "latest": "2.2.88", "behind": False,
               "tone": "current", "label": "Aktualna"}
    with patch.object(panel, "settings", return_value=current), \
         patch.object(panel, "_read_dashboard_deferred_cache", return_value=cached), \
         patch.object(panel, "installed_playerbots_version", return_value="2.2.88"), \
         patch.object(panel, "playerbots_release_status", return_value=updated) as release:
        response = panel.app.test_client().get("/api/dashboard-deferred")
    assert response.status_code == 200
    assert response.json["world_summary"]["version"] == "2.2.88"
    assert response.json["world_summary"]["release"] == updated
    assert cached["data"]["world_summary"]["version"] == "2.2.87"
    release.assert_called_once_with(check_remote=False, latest_override="2.2.88")


def test_release_comparison_can_reuse_cached_latest_without_network():
    with patch.object(panel, "installed_playerbots_version", return_value="2.2.88"), \
         patch.object(panel, "latest_playerbots_release") as github:
        release = panel.playerbots_release_status(check_remote=False, latest_override="2.2.88")
    assert release["installed"] == "2.2.88"
    assert release["behind"] is False
    github.assert_not_called()
