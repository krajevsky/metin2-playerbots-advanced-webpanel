"""The player speed action uses the same long-lived quest command as Tieru."""
from unittest.mock import patch

import app as panel


def test_speed_action_uses_thirty_day_duration_and_normal_resets():
    settings = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}
    for speed in (60, 0):
        with patch.object(panel, "settings", return_value=settings), \
                patch.object(panel, "one", return_value={"id": 7, "name": "Bot"}), \
                patch.object(panel, "queue_player_admin_command", return_value=("done", 1)) as queue:
            response = panel.app.test_client().post(
                "/player/7/action/game", data={"command": "SPEED", "speed": str(speed)})
        assert response.status_code == 302
        queue.assert_called_once_with("Bot", "SPEED", speed, 2_592_000)
