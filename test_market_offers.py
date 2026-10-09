"""Global IkarusShop offer browser applies bounded, parameterised filters."""
from unittest.mock import patch

import app as panel
import pytest


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_market_offers_filters_and_price():
    offer = {"id": 91, "owner_id": 7, "vnum": 42, "quantity": 4, "price": 1000,
             "item_name": "Przedmiot", "seller": "Handlarz", "shop_name": "Sklep",
             "map_index": 1, "channel": 2, "empire": 1, "is_bot": 1}
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 200}) as count_rows, \
            patch.object(panel, "rows", return_value=[offer]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get(
            "/economy/offers?q=Przedmiot&seller=bot&empire=1&sort=unit_asc&page=2")
    assert response.status_code == 200
    sql, params = read_rows.call_args.args
    assert "IKASHOP_OFFLINESHOP" in sql and "s.duration>0" in sql
    assert "LEFT(a.login,10)='playerbot_'" in sql
    assert "price / GREATEST(i.`count`,1) ASC" in sql
    assert params == [-1, "%Przedmiot%", 1, 51, 50]
    count_sql, count_params = count_rows.call_args.args
    assert "COUNT(*) AS total" in count_sql
    assert count_params == (-1, "%Przedmiot%", 1)
    assert render.call_args.kwargs["offers"][0]["unit_price"] == 250
    assert render.call_args.kwargs["total"] == 200


def test_market_offers_uses_sort_whitelist_and_caps_page():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 200}), \
            patch.object(panel, "rows", return_value=[]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get(
            "/economy/offers?sort=price;DROP&seller=invalid&empire=99&page=999")
    assert response.status_code == 200
    sql, params = read_rows.call_args.args
    assert "DROP" not in sql and "ORDER BY price ASC" in sql
    assert params == [51, 4950]
    assert render.call_args.kwargs["seller_type"] == "all"
    assert render.call_args.kwargs["empire"] == 0
    assert render.call_args.kwargs["page"] == 100


@pytest.mark.parametrize("text,value", [("500k", 500_000), ("1.5kk", 1_500_000),
                                         ("2kkk", 2_000_000_000), ("1 500 000", 1_500_000),
                                         ("2,5kk Yang", 2_500_000), ("", None)])
def test_market_price_parser_matches_tieru(text, value):
    assert panel.parse_market_price(text) == value


@pytest.mark.parametrize("text", ["abc", "1.2", "-5k", "100000000000000"])
def test_market_price_parser_rejects_invalid(text):
    with pytest.raises(ValueError):
        panel.parse_market_price(text)


def test_market_offers_price_filter_uses_units_and_bound_parameters():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 200}), \
            patch.object(panel, "rows", return_value=[]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok"):
        response = panel.app.test_client().get("/economy/offers?pmin=500k&pmax=2kk&unit=1")
    assert response.status_code == 200
    sql, params = read_rows.call_args.args
    assert "GREATEST(i.`count`,1)" in sql
    assert ">=%s" in sql and "<=%s" in sql
    assert params == [500000, 2000000, 51, 0]


def test_market_offers_filters_seller_and_shop_names_with_parameters():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 200}), \
            patch.object(panel, "rows", return_value=[]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get(
            "/economy/offers?seller_name=Handlarz&shop_name=Tanie%20miejsce&q=42")
    assert response.status_code == 200
    sql, params = read_rows.call_args.args
    assert "p.name LIKE %s" in sql and "s.name LIKE %s" in sql
    assert params == [42, "%42%", "%Handlarz%", "%Tanie miejsce%", 51, 0]
    assert render.call_args.kwargs["seller_name"] == "Handlarz"
    assert render.call_args.kwargs["shop_name"] == "Tanie miejsce"


@pytest.mark.parametrize("size,expected", [(25, 25), (50, 50), (100, 100), (999, 50)])
def test_market_offers_page_size_is_bounded_and_changes_offset(size, expected):
    offer = {"id": 1, "owner_id": 7, "vnum": 42, "quantity": 1, "price": 1000}
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 200}), \
            patch.object(panel, "rows", return_value=[offer] * (expected + 1)) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get(f"/economy/offers?size={size}&page=2")
    assert response.status_code == 200
    assert read_rows.call_args.args[1] == [expected + 1, expected]
    assert render.call_args.kwargs["page_size"] == expected
    assert render.call_args.kwargs["has_next"] is True
