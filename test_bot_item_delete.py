"""DELITEM must be limited to the exact item currently held by a bot."""
from unittest.mock import patch

import pytest
import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "1", "ui_language": "pl"}
ITEM = {"id": 71, "window": "INVENTORY", "pos": 3, "count": 2, "vnum": 19}
PAYLOAD = {"pid": 7, "item_id": 71, "vnum": 19, "count": 2, "mode": "delete"}


@pytest.fixture(autouse=True)
def mt2009_engine():
    with patch.object(panel, "ENGINE_MT2009", True):
        yield


def client():
    result = panel.app.test_client()
    with result.session_transaction() as session:
        session["seban_admin"] = True
        session["seban_item_delete_csrf"] = "test-token"
    return result


def request(client, payload=PAYLOAD, token="test-token"):
    return client.post("/api/bot-item-delete", json=payload,
                       headers={"X-CSRF-Token": token})


def fake_one(sql, params=()):
    if "FROM player.player p" in sql:
        return {"name": "bot7", "is_bot": 1}
    if "FROM player.item" in sql:
        return ITEM
    raise AssertionError(sql)


def test_delete_rejects_missing_csrf_and_non_bot_without_queueing():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=fake_one), \
            patch.object(panel, "queue_bot_item_delete") as queue:
        assert request(client(), token="wrong").status_code == 403
        with patch.object(panel, "one", return_value={"name": "human", "is_bot": 0}):
            response = request(client())
        assert response.status_code == 403
        assert response.json["status"] == "not_allowed"
        queue.assert_not_called()


def test_delete_rejects_changed_item_and_shop_window():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=fake_one), \
            patch.object(panel, "queue_bot_item_delete") as queue:
        changed = request(client(), {**PAYLOAD, "count": 1})
        assert changed.json["status"] == "changed"
        with patch.object(panel, "one", side_effect=lambda sql, params=():
                          {"name": "bot7", "is_bot": 1} if "FROM player.player p" in sql
                          else {**ITEM, "window": "IKASHOP_OFFLINESHOP"}):
            shop = request(client())
        assert shop.json["status"] == "no_item"
        queue.assert_not_called()


def test_delete_queues_exact_item_and_returns_engine_answer():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=fake_one), \
            patch.object(panel, "queue_bot_item_delete", return_value=("done", 101)) as queue:
        response = request(client())
    assert response.status_code == 200
    assert response.json["ok"] is True and response.json["status"] == "done"
    queue.assert_called_once_with("bot7", 71, 19, 2)


def test_pending_deletion_reports_cancellable_status_in_english():
    with patch.object(panel, "settings", return_value={**SETTINGS, "ui_language": "en"}), \
            patch.object(panel, "one", side_effect=fake_one), \
            patch.object(panel, "queue_bot_item_delete", return_value=("await", 102)):
        response = request(client())
    assert response.json["status"] == "await" and response.json["ok"] is True
    assert "pending" in response.json["message"]
