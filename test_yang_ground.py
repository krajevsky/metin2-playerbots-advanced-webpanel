"""Player Yang payout uses Tieru's exact persistent flag and live command."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_yang_ground_read_defaults_to_purse():
    with patch.object(panel, "read_global_quest_flags", return_value={}):
        assert panel.read_world_extras()["yang_ground"] == 0


def test_yang_ground_posts_exact_engine_contract():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command", return_value=("done", 123)) as queue:
        response = panel.app.test_client().post("/manage/yang-ground", data={"ground": "1"})
    assert response.status_code == 302
    assert "m2_yang_ground" in rows.call_args.args[0]
    assert rows.call_args.args[1] == (1,)
    queue.assert_called_once_with("YANG_GROUND", "1")


def test_yang_ground_rejects_invalid_value():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command") as queue:
        response = panel.app.test_client().post("/manage/yang-ground", data={"ground": "99"})
    assert response.status_code == 302
    rows.assert_not_called()
    queue.assert_not_called()
