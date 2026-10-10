"""GM item stacks follow the game and Tieru's smallint unsigned limit."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_gm_item_accepts_largest_engine_stack():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=[{"id": 5, "name": "Hero"}, {"vnum": 19}]), \
            patch.object(panel, "queue_player_admin_command", return_value=("done", 1)) as queue:
        response = panel.app.test_client().post("/player/5/action/game", data={
            "command": "ITEM", "vnum": "19", "count": "65535"})
    assert response.status_code == 302
    queue.assert_called_once_with("Hero", "ITEM", 19, 65535)


def test_gm_item_rejects_quantity_above_engine_stack():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"id": 5, "name": "Hero"}) as lookup, \
            patch.object(panel, "queue_player_admin_command") as queue:
        response = panel.app.test_client().post("/player/5/action/game", data={
            "command": "ITEM", "vnum": "19", "count": "65536"})
    assert response.status_code == 302
    assert lookup.call_count == 1
    queue.assert_not_called()
