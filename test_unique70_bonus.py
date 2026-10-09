"""The level-70 sixth-bonus switch uses Tieru's exact quest flag and queue command."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_read_unique70_bonus_flag():
    with patch.object(panel, "read_global_quest_flags", return_value={"m2_unique70_bonus_off": 1}):
        assert panel.read_world_extras()["unique70_off"] == 1


def test_unique70_bonus_posts_exact_engine_contract():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command", return_value=("done", 123)) as queue:
        response = panel.app.test_client().post("/manage/unique70-bonus", data={"off": "1"})
    assert response.status_code == 302
    assert "m2_unique70_bonus_off" in rows.call_args.args[0]
    assert rows.call_args.args[1] == (1,)
    queue.assert_called_once_with("UNIQUE70_BONUS", "1")


def test_unique70_bonus_rejects_invalid_value_before_write():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command") as queue:
        response = panel.app.test_client().post("/manage/unique70-bonus", data={"off": "2"})
    assert response.status_code == 302
    rows.assert_not_called()
    queue.assert_not_called()
