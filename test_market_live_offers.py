"""Live item offers use IkarusShop listings and bound sort choices."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_economy_item_lists_active_offers_and_unit_price():
    raw_offer = {"id": 101, "owner_id": 7, "vnum": 42, "quantity": 4, "socket0": 0,
                 "price": 1000, "seller": "Handlarz", "shop_name": "Sklep Handlarza",
                 "map_index": 1, "channel": 2, "empire": 1, "is_bot": 1}
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=[{"vnum": 42, "item_name": "Przedmiot"}, {"at": None}]), \
            patch.object(panel, "rows", side_effect=[[], [], [raw_offer]]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/item/42?offer_sort=price_asc")
    assert response.status_code == 200
    sql = read_rows.call_args_list[2].args[0]
    assert "IKASHOP_OFFLINESHOP" in sql
    assert "s.duration>0" in sql
    assert "ORDER BY price ASC" in sql
    offer = render.call_args.kwargs["offers"][0]
    assert offer["price"] == 1000 and offer["unit_price"] == 250
    assert offer["channel"] == 2 and offer["pid"] == 7


def test_economy_item_groups_listings_by_empire_and_keeps_all_view():
    raw_offers = [
        {"id": n, "owner_id": n, "vnum": 42, "quantity": 1, "price": 100,
         "seller": f"Seller {n}", "shop_name": "Shop", "map_index": 1,
         "channel": 1, "empire": empire, "is_bot": 0}
        for n, empire in enumerate((3, 1, 2, 3, 0), start=1)
    ]
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=[{"vnum": 42, "item_name": "Przedmiot"}, {"at": None}]), \
            patch.object(panel, "rows", side_effect=[[], [], raw_offers]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/item/42")
    assert response.status_code == 200
    groups = render.call_args.kwargs["offer_groups"]
    assert [group["name"] for group in groups] == ["Shinsoo", "Jinno", "Chunjo", "Wszystkie"]
    assert [[offer["item_id"] for offer in group["offers"]] for group in groups] == [[2], [1, 4], [3], [1, 2, 3, 4, 5]]


def test_economy_item_rejects_untrusted_sort_sql():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=[{"vnum": 42, "item_name": "Przedmiot"}, {"at": None}]), \
            patch.object(panel, "rows", side_effect=[[], [], []]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/item/42?offer_sort=price;DROP%20TABLE%20item")
    assert response.status_code == 200
    assert "DROP" not in read_rows.call_args_list[2].args[0]
    assert render.call_args.kwargs["offer_sort"] == "price_asc"


def test_economy_item_price_history_uses_weighted_active_listing_value():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=[{"vnum": 42, "item_name": "Przedmiot"}, {"at": None}]), \
            patch.object(panel, "rows", side_effect=[[], [{"captured_at": "10-10 10:00", "unit_price": 250}], []]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/item/42")
    assert response.status_code == 200
    price_query = read_rows.call_args_list[1]
    assert "SUM(total_value)/NULLIF(SUM(total_units),0)" in price_query.args[0]
    assert "web_seban_shop_item_snapshot" in price_query.args[0]
    assert price_query.args[1] == (42, 0)
    assert render.call_args.kwargs["price_history"][0]["unit_price"] == 250


def test_economy_item_price_history_filters_skill_book_variant():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", side_effect=[{"vnum": 50300, "item_name": "Księga"}, {"at": None}]), \
            patch.object(panel, "rows", side_effect=[[], [], []]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok"):
        response = panel.app.test_client().get("/economy/item/50300?socket0=7")
    assert response.status_code == 200
    assert read_rows.call_args_list[1].args[1] == (50300, 7)
