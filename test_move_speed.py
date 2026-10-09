"""Movement speed uses Tieru's exact quest flag and live queue command."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_move_speed_read_defaults_to_game_rate():
    with patch.object(panel, "read_global_quest_flags", return_value={}):
        assert panel.read_world_extras()["move_speed_pct"] == 100


def test_move_speed_posts_exact_engine_contract():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command", return_value=("done", 123)) as queue:
        response = panel.app.test_client().post("/manage/move-speed", data={"pct": "150"})
    assert response.status_code == 302
    assert "m2_move_speed_pct" in rows.call_args.args[0]
    assert rows.call_args.args[1] == (150,)
    queue.assert_called_once_with("MOVE_SPEED", "150")


def test_move_speed_rejects_out_of_range_values():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command") as queue:
        client = panel.app.test_client()
        assert client.post("/manage/move-speed", data={"pct": "49"}).status_code == 302
        assert client.post("/manage/move-speed", data={"pct": "201"}).status_code == 302
    rows.assert_not_called()
    queue.assert_not_called()
