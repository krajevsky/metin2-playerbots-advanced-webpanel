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


def test_market_offers_category_filter_applies_to_count_and_page():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?category=10")
    assert response.status_code == 200
    count_sql, count_params = count_rows.call_args.args
    page_sql, page_params = read_rows.call_args.args
    assert "ip.type" in count_sql and "ip.type" in page_sql
    assert "i.vnum IN" in count_sql and "i.vnum IN" in page_sql
    assert count_params == (10,)
    assert page_params == [10, 51, 0]
    assert render.call_args.kwargs["category"] == 10


def test_market_offers_subcategory_is_scoped_to_category():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?category=6&subcategory=3")
    assert response.status_code == 200
    assert "i.socket0" in count_rows.call_args.args[0]
    assert "i.socket0" in read_rows.call_args.args[0]
    assert count_rows.call_args.args[1] == (6, 3)
    assert read_rows.call_args.args[1] == [6, 3, 51, 0]
    assert render.call_args.kwargs["subcategory"] == 3

    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        panel.app.test_client().get("/economy/offers?category=2&subcategory=3")
    assert count_rows.call_args.args[1] == (2,)
    assert render.call_args.kwargs["subcategory"] == 0


def test_market_offers_refine_range_matches_proto_name_suffix():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?rmin=7&rmax=9")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "ip.locale_name REGEXP" in sql
    assert "SUBSTRING_INDEX(ip.locale_name,'+',-1)" in sql
    assert params == (7, 9)
    assert render.call_args.kwargs["refine_inputs"] == {"rmin": "7", "rmax": "9"}


def test_market_offers_rejects_reversed_refine_range():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        panel.app.test_client().get("/economy/offers?rmin=9&rmax=7")
    assert count_rows.call_args.args[1] == ()
    assert render.call_args.kwargs["refine_inputs"] == {"rmin": "", "rmax": ""}


def test_market_offers_class_filter_uses_proto_antiflags_and_book_skill():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?cls=4")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "ip.antiflag" in sql and "i.socket0" in sql
    assert params == (4,)
    assert render.call_args.kwargs["class_bit"] == 4


def test_market_offers_required_level_range_uses_both_proto_limits():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?lmin=30&lmax=90")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "ip.limittype1=1" in sql and "ip.limittype0=1" in sql
    assert params == (30, 90)
    assert render.call_args.kwargs["level_inputs"] == {"lmin": "30", "lmax": "90"}


def test_market_offers_rejects_reversed_level_range():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        panel.app.test_client().get("/economy/offers?lmin=200&lmax=30")
    assert count_rows.call_args.args[1] == ()
    assert render.call_args.kwargs["level_inputs"] == {"lmin": "", "lmax": ""}


@pytest.mark.parametrize("sort,fragment", [
    ("newest", "ORDER BY i.id DESC"),
    ("plus_desc", "SUBSTRING_INDEX(ip.locale_name,'+',-1)"),
    ("level_desc", "ip.limittype1=1"),
    ("level_asc", "ASC, price ASC, i.id DESC"),
])
def test_market_offers_extra_sort_orders_are_whitelisted(sort, fragment):
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}), \
            patch.object(panel, "rows", return_value=[]) as read_rows, \
            patch.object(panel, "render_template", return_value="ok"):
        response = panel.app.test_client().get(f"/economy/offers?sort={sort}")
    assert response.status_code == 200
    assert fragment in read_rows.call_args.args[0]


def test_market_filter_chips_remove_one_filter_and_reset_page():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}), \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get(
            "/economy/offers?q=Miecz&category=2&seller=bot&sort=newest&size=25&page=3")
    assert response.status_code == 200
    chips = render.call_args.kwargs["active_filters"]
    category_chip = next(chip for chip in chips if chip["label"] == "Kategoria")
    assert "q=Miecz" in category_chip["url"]
    assert "seller=bot" in category_chip["url"]
    assert "sort=newest" in category_chip["url"]
    assert "size=25" in category_chip["url"]
    assert "category=" not in category_chip["url"]
    assert "page=" not in category_chip["url"]


def test_market_filter_chips_use_english_labels():
    with patch.object(panel, "settings", return_value={**SETTINGS, "ui_language": "en"}), \
            patch.object(panel, "one", return_value={"total": 0}), \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?seller_name=Merchant")
    assert response.status_code == 200
    assert render.call_args.kwargs["active_filters"][0]["label"] == "Seller nickname"


def test_market_bonus_line_count_matches_tieru_non_damage_lines():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?nbmin=3")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "i.attrtype0 NOT IN (0,121,122) AND i.attrvalue0<>0" in sql
    assert "i.attrtype6 NOT IN (0,121,122) AND i.attrvalue6<>0" in sql
    assert params == (3,)
    assert render.call_args.kwargs["bonus_min"] == 3


def test_market_bonus_line_count_rejects_out_of_range():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        panel.app.test_client().get("/economy/offers?nbmin=99")
    assert count_rows.call_args.args[1] == ()
    assert render.call_args.kwargs["bonus_min"] == 0


def test_market_can_sort_by_normal_bonus_lines():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}), \
            patch.object(panel, "rows", return_value=[]) as offers, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?sort=bonus_count")
    assert response.status_code == 200
    sql = offers.call_args.args[0]
    assert "i.attrtype0 NOT IN (0,121,122) AND i.attrvalue0<>0" in sql
    assert "i.attrtype6 NOT IN (0,121,122) AND i.attrvalue6<>0" in sql
    assert ") DESC, price ASC, i.id DESC LIMIT %s OFFSET %s" in sql
    assert render.call_args.kwargs["sort"] == "bonus_count"


def test_market_damage_ranges_use_tieru_points_and_last_nonzero_line():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get(
            "/economy/offers?avgmin=30&avgmax=55&sklmin=10&sklmax=20")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "NULLIF(IF(i.attrtype6=122,i.attrvalue6,0),0)" in sql
    assert "NULLIF(IF(i.attrtype0=121,i.attrvalue0,0),0)" in sql
    assert params == (30, 55, 10, 20)
    assert render.call_args.kwargs["damage_inputs"]["avgmin"] == "30"


def test_market_damage_ranges_reject_reversed_and_out_of_range():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        panel.app.test_client().get("/economy/offers?avgmin=90&avgmax=20&sklmin=201")
    assert count_rows.call_args.args[1] == ()
    assert render.call_args.kwargs["damage_inputs"] == {
        "avgmin": "", "avgmax": "", "sklmin": "", "sklmax": ""}


def test_market_stone_filter_only_matches_weapon_or_armor_sockets():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?ks=has")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "ip.type IN (1,2)" in sql
    assert "i.socket0 BETWEEN 28000 AND 28999" in sql
    assert "i.socket2 BETWEEN 28000 AND 28999" in sql
    assert params == ()
    assert render.call_args.kwargs["has_stone"] is True


def test_market_specific_stone_vnum_overrides_generic_stone_filter():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?ks=has&stone=28130")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "ip.type IN (1,2)" in sql
    assert "i.socket0=%s OR i.socket1=%s OR i.socket2=%s" in sql
    assert params == (28130, 28130, 28130)
    assert render.call_args.kwargs["has_stone"] is False
    assert render.call_args.kwargs["stone_vnum"] == 28130


def test_market_shop_owner_filter_uses_item_owner_id():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get("/economy/offers?shop=2005")
    assert response.status_code == 200
    assert "i.owner_id=%s" in count_rows.call_args.args[0]
    assert count_rows.call_args.args[1] == (2005,)
    assert render.call_args.kwargs["shop_owner"] == 2005


def test_market_shop_owner_filter_rejects_invalid_ids():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        panel.app.test_client().get("/economy/offers?shop=999999999999")
    assert count_rows.call_args.args[1] == ()
    assert render.call_args.kwargs["shop_owner"] == 0


def test_market_three_bonus_filters_match_seven_attribute_slots():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = panel.app.test_client().get(
            "/economy/offers?b1=44&b1v=10&b2=48&b2v=15&b3=43&b3v=0")
    assert response.status_code == 200
    sql, params = count_rows.call_args.args
    assert "i.attrtype0=%s AND i.attrvalue0>=%s" in sql
    assert "i.attrtype6=%s AND i.attrvalue6>=%s" in sql
    assert params == ((44, 10) * 7 + (48, 15) * 7 + (43, 0) * 7)
    assert render.call_args.kwargs["bonus_params"]["b3v"] == 0
    chips = render.call_args.kwargs["active_filters"]
    assert len(chips) == 3
    assert "b3v=0" in chips[0]["url"]
    assert "b1=" not in chips[0]["url"]


def test_market_bonus_points_use_tieru_whitelist_and_value_bounds():
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "one", return_value={"total": 0}) as count_rows, \
            patch.object(panel, "rows", return_value=[]), \
            patch.object(panel, "render_template", return_value="ok") as render:
        panel.app.test_client().get("/economy/offers?b1=9999&b2=44&b2v=999999")
    assert count_rows.call_args.args[1] == (44, 1) * 7
    assert render.call_args.kwargs["bonus_params"] == {"b2": 44, "b2v": 1}
