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
    "itemid": 36024379, "proto_name": "Kawałek Klejnotu", "socket0": None, "item_size": 2,
}


def test_new_playerbots_goal_is_fishing():
    assert panel.live_label("goal", 12) == "Łowienie ryb"


def test_transaction_api_returns_both_actors_from_buy_item():
    with patch.object(panel, "settings", return_value=SETTINGS), patch.object(panel, "rows", return_value=[SALE]) as read:
        response = panel.app.test_client().get("/api/shop-transactions")
    assert response.status_code == 200
    transaction = response.json["transactions"][0]
    assert (transaction["buyer"], transaction["seller"]) == ("Kupujący", "Sprzedawca")
    assert (transaction["buyer_id"], transaction["seller_id"]) == (106, 751)
    assert (transaction["quantity"], transaction["yang"], transaction["vnum"]) == (3, 67900, 30021)
    assert transaction["item_size"] == 2
    sql, params = read.call_args.args
    assert "l.what='BUY_ITEM'" in sql and "LOCK_ITEM_TO_BUY" not in sql
    assert "l.who AS buyer_id" in sql and "l.shop_owner AS seller_id" in sql
    assert "l.time >= NOW() - INTERVAL 7 DAY" in sql
    assert params == (41,)


def test_recent_shop_sales_uses_completed_purchase_for_both_names():
    sale = {
        "time": SALE["time"], "buyer_id": 106, "seller_id": 751,
        "buyer": "Kupujący", "seller": "Sprzedawca", "empire": 2,
        "vnum": 50300, "qty": 1, "price": 125000, "socket0": 4,
    }
    with patch.object(panel, "rows", return_value=[sale]) as read, \
         patch.object(panel, "_item_display_name", return_value="Silne ciało — Księga Umiejętności"), \
         patch.object(panel, "item_icon_url", return_value="/book.png"), \
         patch.object(panel, "settings", return_value=SETTINGS):
        result = panel.recent_shop_sales(10)
    assert (result[0]["buyer"], result[0]["seller"]) == ("Kupujący", "Sprzedawca")
    assert (result[0]["buyer_id"], result[0]["seller_id"]) == (106, 751)
    assert result[0]["item_name"] == "Silne ciało — Księga Umiejętności"
    sql, params = read.call_args.args
    assert "l.what='BUY_ITEM'" in sql and "l.who AS buyer_id" in sql
    assert "l.shop_owner AS seller_id" in sql and "skillbook_identity" in sql
    assert params == (10,)


def test_skill_book_ranking_keeps_known_skills_separate_from_unknown():
    sales = [
        {"vnum": 50300, "time": SALE["time"], "qty": 1, "price": 120000, "socket0": 4},
        {"vnum": 50300, "time": SALE["time"], "qty": 1, "price": 90000, "socket0": 0},
    ]
    with patch.object(panel, "rows", return_value=sales) as read, \
         patch.object(panel, "_item_display_name", return_value="Silne ciało — Księga Umiejętności"):
        result = panel.shop_sales_velocity(24, 5, only_skillbooks=True)
    assert len(result) == 1 and result[0]["socket0"] == 4
    assert result[0]["sales"] == 1 and result[0]["avg_price"] == 120000
    assert "l.what='BUY_ITEM'" in read.call_args.args[0]
    assert "skillbook_identity" in read.call_args.args[0]


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
        assert client.get("/api/shop-transactions?q=" + "a" * 81).status_code == 400
        read.assert_not_called()


def test_transaction_item_search_uses_item_proto_and_parameterized_query():
    with patch.object(panel, "settings", return_value=SETTINGS), patch.object(panel, "rows", return_value=[SALE]) as read:
        response = panel.app.test_client().get("/api/shop-transactions?q=Klejnot")
    assert response.status_code == 200
    sql, params = read.call_args.args
    assert "ip.locale_name LIKE %s" in sql and "ip.name LIKE %s" in sql
    assert "Klejnot" not in sql
    assert params == (-1, "%Klejnot%", "%Klejnot%", 41)


def test_disabled_tracker_never_reads_transactions_or_loads_polling_script():
    disabled = {**SETTINGS, "shop_transaction_tracker": "0"}
    with patch.object(panel, "settings", return_value=disabled), patch.object(panel, "shop_transaction_rows") as read:
        client = panel.app.test_client()
        api = client.get("/api/shop-transactions")
        page = client.get("/economy/transactions")
    assert api.status_code == 503 and api.json["error"] == "tracker_disabled"
    assert page.status_code == 200
    assert b"shop-transactions.js" not in page.data
    read.assert_not_called()


def test_tracker_switch_saves_setting_and_english_ui():
    english = {**SETTINGS, "ui_language": "en", "shop_transaction_tracker": "1"}
    with patch.object(panel, "settings", return_value=english), patch.object(panel, "write_settings") as write:
        client = panel.app.test_client()
        page = client.get("/economy/transactions")
        response = client.post("/manage/panel/shop-transaction-tracker", data={"enabled": "0"})
    assert page.status_code == 200
    assert b"Shop transactions" in page.data and b"Search item" in page.data
    assert response.status_code == 302
    write.assert_called_once_with({"shop_transaction_tracker": "0"})
