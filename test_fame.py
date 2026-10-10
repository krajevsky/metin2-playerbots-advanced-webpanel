"""The fame page uses the engine's validated PB7F1 snapshot."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_fame_snapshot_is_ranked_and_colored_like_tieru(tmp_path):
    path = tmp_path / "playerbot_live_fame.tsv"
    path.write_text("PB7F1 1 2\n100 125 10 0\n200 100 6 0\n", encoding="ascii")
    with patch.object(panel, "FAME_FILE", path):
        fame = panel.playerbot_fame()
        assert panel.playerbot_fame() is fame
    assert fame[100] == {"pid": 100, "points": 125, "level": 10, "rank": 1,
                         "color": "#FFD700"}
    assert fame[200]["rank"] == 2


def test_fame_snapshot_rejects_duplicate_and_disordered_rows(tmp_path):
    path = tmp_path / "fame.tsv"
    path.write_text("PB7F1 1 2\n100 125 10 0\n100 130 6 0\n", encoding="ascii")
    with patch.object(panel, "FAME_FILE", path):
        assert panel.playerbot_fame() == {}
    path.write_text("PB7F1 1 1\n100 125 11 0\n", encoding="ascii")
    with patch.object(panel, "FAME_FILE", path):
        assert panel.playerbot_fame() == {}


def test_fame_page_uses_parameterized_character_ids_and_english(tmp_path):
    path = tmp_path / "fame.tsv"
    path.write_text("PB7F1 1 1\n100 125 10 0\n", encoding="ascii")
    with patch.object(panel, "FAME_FILE", path), \
            patch.object(panel, "settings", return_value={**SETTINGS, "ui_language": "en"}), \
            patch.object(panel, "rows", return_value=[{"id": 100, "name": "Hero"}]) as read_rows:
        response = panel.app.test_client().get("/fame")
    assert response.status_code == 200
    assert "Fame ranking" in response.get_data(as_text=True)
    assert "Hero" in response.get_data(as_text=True)
    assert "125" in response.get_data(as_text=True)
    assert read_rows.call_args.args[1] == (100,)


def test_fame_page_handles_missing_snapshot_without_query(tmp_path):
    with patch.object(panel, "FAME_FILE", tmp_path / "missing"), \
            patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "rows") as read_rows:
        response = panel.app.test_client().get("/fame")
    assert response.status_code == 200
    assert "nie opublikował" in response.get_data(as_text=True)
    read_rows.assert_not_called()
