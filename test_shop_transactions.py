"""The transaction tracker uses one completed purchase record for both actors."""
from datetime import datetime
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}
SALE = {
    "id": 101, "time": datetime(2026, 10, 11, 20, 35, 57),
    "buyer_id": 106, "buyer_name": "Kupujący", "buyer_is_bot": 0,
    "seller_id": 751, "seller_name": "Sprzedawca", "seller_is_bot": 1,
    "vnum": 30021, "quantity": 3, "yang": 67900, "cheque": 0,
    "itemid": 36024379, "proto_name": "Kawałek Klejnotu", "socket0": None,
}


def test_transaction_api_returns_both_actors_from_buy_item():
    with patch.object(panel, "settings", return_value=SETTINGS), patch.object(panel, "rows", return_value=[SALE]) as read:
        response = panel.app.test_client().get("/api/shop-transactions")
    assert response.status_code == 200
    transaction = response.json["transactions"][0]
    assert (transaction["buyer"], transaction["seller"]) == ("Kupujący", "Sprzedawca")
    assert (transaction["buyer_id"], transaction["seller_id"]) == (106, 751)
    assert (transaction["quantity"], transaction["yang"], transaction["vnum"]) == (3, 67900, 30021)
    sql, params = read.call_args.args
    assert "l.what='BUY_ITEM'" in sql and "LOCK_ITEM_TO_BUY" not in sql
    assert "l.who AS buyer_id" in sql and "l.shop_owner AS seller_id" in sql
    assert params == (41,)


def test_transaction_cursors_are_bounded_and_parameterized():
    with patch.object(panel, "settings", return_value=SETTINGS), patch.object(panel, "rows", return_value=[SALE]) as read:
        client = panel.app.test_client()
        assert client.get("/api/shop-transactions?before=102").status_code == 200
        assert "l.id < %s" in read.call_args.args[0]
        assert read.call_args.args[1] == (102, 41)
        assert client.get("/api/shop-transactions?after=100").status_code == 200
        assert "l.id > %s" in read.call_args.args[0] and "ORDER BY l.id ASC" in read.call_args.args[0]
        assert read.call_args.args[1] == (100, 101)
        read.reset_mock()
        assert client.get("/api/shop-transactions?after=0").status_code == 400
        assert client.get("/api/shop-transactions?before=1%20OR%201=1").status_code == 400
        assert client.get("/api/shop-transactions?before=1&after=2").status_code == 400
        read.assert_not_called()
