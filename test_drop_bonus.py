"""Monster-drop bonus chance matches Tieru's quest flag and live command."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_drop_bonus_read_defaults_to_game_rate():
    with patch.object(panel, "read_global_quest_flags", return_value={}):
        assert panel.read_world_extras()["drop_bonus_pct"] == 100


def test_drop_bonus_posts_exact_engine_contract():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command", return_value=("done", 123)) as queue:
        response = panel.app.test_client().post("/manage/drop-bonus", data={"pct": "250"})
    assert response.status_code == 302
    assert "m2_drop_bonus_pct" in rows.call_args.args[0]
    assert rows.call_args.args[1] == (250,)
    queue.assert_called_once_with("DROP_BONUS", "250")


def test_drop_bonus_rejects_out_of_range_values():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command") as queue:
        client = panel.app.test_client()
        assert client.post("/manage/drop-bonus", data={"pct": "9"}).status_code == 302
        assert client.post("/manage/drop-bonus", data={"pct": "1001"}).status_code == 302
    rows.assert_not_called()
    queue.assert_not_called()
