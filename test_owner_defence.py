"""Owner defence uses Tieru's exact persistent flag and live queue command."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_owner_defence_defaults_to_enabled():
    with patch.object(panel, "read_global_quest_flags", return_value={}):
        assert panel.read_world_extras()["owner_defence_off"] == 0


def test_owner_defence_posts_exact_engine_contract():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command", return_value=("done", 123)) as queue:
        response = panel.app.test_client().post("/manage/owner-defence", data={"off": "1"})
    assert response.status_code == 302
    assert "m2_owner_defence_off" in rows.call_args.args[0]
    assert rows.call_args.args[1] == (1,)
    queue.assert_called_once_with("OWNER_DEFENCE", "1")


def test_owner_defence_rejects_invalid_value():
    with patch.object(panel, "ENGINE_MT2009", True), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as rows, \
            patch.object(panel, "queue_game_admin_command") as queue:
        response = panel.app.test_client().post("/manage/owner-defence", data={"off": "on"})
    assert response.status_code == 302
    rows.assert_not_called()
    queue.assert_not_called()
