"""The English panel (ui_language=en): translations.py and the pages it reaches."""
from unittest.mock import patch

import app as panel
import translations


def english_settings(**extra):
    return dict(panel.DEFAULT_SETTINGS, ui_language="en", setup_complete="1", auth_enabled="0", **extra)


def test_an_item_is_named_by_its_official_english_name():
    assert translations.translate_string("Miecz+0") == "Sword+0"
    assert translations.translate_string("Długi Miecz+1") == "Long Sword+1"
    assert translations.translate_string("Sejmitar+2") == "Crescent Sword+2"
    html = translations.translate_html('<b>Sejmitar+2</b><img alt="Miecz+0">', "en")
    assert html == '<b>Crescent Sword+2</b><img alt="Sword+0">'
    assert translations.translate_html('<b>Sejmitar+2</b>', "pl") == '<b>Sejmitar+2</b>'


def test_a_polish_name_two_items_share_stays_polish():
    # 22000 is the Town Scroll, 22001 "Back to town": the name alone cannot say which.
    assert "Zwój Powrotu Do Miasta" not in translations.ITEM_NAMES
    assert translations.translate_string("Zwój Powrotu Do Miasta") == "Zwój Powrotu Do Miasta"


def test_the_panel_keeps_its_own_word_where_an_item_shares_it():
    assert translations.translate_string("Wiadomości") == "Messages"


def test_item_search_answers_with_english_names_and_count():
    items = [{"vnum": 10, "name": "Sword", "locale_name": "Miecz+0", "type": 1, "subtype": 0,
              "size": 2, "gold": 0, "shop_buy_price": 0}]

    def rows(sql, params=()):
        return [{"count": 1}] if "COUNT(*)" in sql else [dict(item) for item in items]

    panel.app.config["TESTING"] = True
    for language, name in (("en", "Sword+0"), ("pl", "Miecz+0")):
        with patch.object(panel, "settings", return_value=dict(english_settings(), ui_language=language)), \
                patch.object(panel, "rows", side_effect=rows):
            data = panel.app.test_client().get("/api/items?q=Mie").get_json()
        assert "<b>%s</b>" % name in data["html"]
    assert data["count_label"] == "1 przedmiotów pasuje do wyszukiwania"
    assert translations.translate_string(data["count_label"]) == "1 items match the search"
    assert translations.translate_string(
        "6001 przedmiotów · pełna lista bez stron (pokazano pierwsze 500 — zawęź wyszukiwanie)") == \
        "6001 items · full list, no pages (showing the first 500 — narrow the search)"


def test_an_english_panel_finds_an_item_by_its_english_name():
    assert 32 in translations.item_vnums_named("crescent sword")
    assert 22000 in translations.item_vnums_named("Town Scroll")
    assert translations.item_vnums_named("  ") == []
    seen = []

    def rows(sql, params=()):
        seen.append((sql, list(params)))
        return [{"count": 0}] if "COUNT(*)" in sql else []

    panel.app.config["TESTING"] = True
    for language in ("en", "pl"):
        seen.clear()
        with patch.object(panel, "settings", return_value=dict(english_settings(), ui_language=language)), \
                patch.object(panel, "rows", side_effect=rows):
            assert panel.app.test_client().get("/api/items?q=Crescent").status_code == 200
        searched = [(sql, params) for sql, params in seen if "FROM player.item_proto p WHERE" in sql]
        assert searched
        for sql, params in searched:
            assert ("p.vnum IN (" in sql and 32 in params) == (language == "en")


def test_a_map_is_named_by_the_games_own_english_name():
    for polish, english in (("Góra Sohan", "Mount Sohan"), ("Ognista Ziemia", "Doyyumhwaji"),
                            ("Las", "Ghost Wood"), ("Czerwony Las", "Red Wood"),
                            ("Loch Pająków V1", "Spider Dungeon"), ("Loch Pająków V2", "Spider Dungeon 2"),
                            ("Loch Małp Normalny", "Monkey Dungeon II"), ("Loch Małp Trudny", "Monkey Dungeon III"),
                            ("Chunjo M2 — Bokjung", "Chunjo M2 — Bokjung")):
        assert translations.translate_string(polish) == english
    for name in panel.MAP_NAMES.values():
        assert name in translations.EXACT, name


def test_a_map_inside_a_longer_text():
    assert translations.translate_string("Dolina Orków, współrzędne 512, 300.") == "Orc Valley, coordinates 512, 300."
    assert translations.translate_string("Poza aktywnym światem (mapa #113)") == "Outside the active world (map #113)"
    assert translations.translate_string("Czerwony Las · 5") == "Red Wood · 5"
    assert translations.translate_string("Czerwony Lasek") == "Czerwony Lasek"
