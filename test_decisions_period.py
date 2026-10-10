"""The decisions time filter keeps SQL parameters separate from user input."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_decisions_period_and_bot_use_bounded_parameters():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows", return_value=[]) as read_rows:
        response = panel.app.test_client().get("/diagnostics/decisions?hours=72&bot=123")
    assert response.status_code == 200
    sql, params = read_rows.call_args.args
    assert "INTERVAL %s HOUR" in sql
    assert "l.pid=%s" in sql
    assert params == [72, 123]
    assert 'value="72" selected' in response.get_data(as_text=True)


def test_decisions_invalid_period_falls_back_to_unfiltered_history():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows", return_value=[]) as read_rows:
        response = panel.app.test_client().get("/diagnostics/decisions?hours=999999")
    assert response.status_code == 200
    sql, params = read_rows.call_args.args
    assert "INTERVAL" not in sql
    assert params == []
    assert 'value="all" selected' in response.get_data(as_text=True)


def test_decisions_period_labels_are_translated():
    with patch.object(panel, "settings", return_value={**SETTINGS, "ui_language": "en"}), \
            patch.object(panel, "rows", return_value=[]):
        response = panel.app.test_client().get("/diagnostics/decisions?hours=1")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "All history" in body
    assert "Period" in body
    assert "Latest 60 entries from the selected period" in body
