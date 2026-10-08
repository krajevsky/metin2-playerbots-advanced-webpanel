"""The English panel (ui_language=en): translations.py and the pages it reaches."""
import html
from datetime import datetime
from unittest.mock import patch

import app as panel
import translations


def english_settings(**extra):
    return dict(panel.DEFAULT_SETTINGS, ui_language="en", setup_complete="1", auth_enabled="0", **extra)


def english(text):
    """translate_string() on plain text: it takes and gives HTML-escaped text."""
    return html.unescape(translations.translate_string(html.escape(text)))


def test_an_item_is_named_by_its_official_english_name():
    assert translations.translate_string("Miecz+0") == "Sword+0"
    assert translations.translate_string("Długi Miecz+1") == "Long Sword+1"
    assert translations.translate_string("Sejmitar+2") == "Crescent Sword+2"
    markup = translations.translate_html('<b>Sejmitar+2</b><img alt="Miecz+0">', "en")
    assert markup == '<b>Crescent Sword+2</b><img alt="Sword+0">'
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
    for polish, translated in (("Góra Sohan", "Mount Sohan"), ("Ognista Ziemia", "Doyyumhwaji"),
                               ("Las", "Ghost Wood"), ("Czerwony Las", "Red Wood"),
                               ("Loch Pająków V1", "Spider Dungeon"), ("Loch Pająków V2", "Spider Dungeon 2"),
                               ("Loch Małp Normalny", "Monkey Dungeon II"), ("Loch Małp Trudny", "Monkey Dungeon III"),
                               ("Chunjo M2 — Bokjung", "Chunjo M2 — Bokjung")):
        assert translations.translate_string(polish) == translated
    for name in panel.MAP_NAMES.values():
        assert name in translations.EXACT, name


def test_a_map_inside_a_longer_text():
    assert translations.translate_string("Dolina Orków, współrzędne 512, 300.") == "Orc Valley, coordinates 512, 300."
    assert translations.translate_string("Poza aktywnym światem (mapa #113)") == "Outside the active world (map #113)"
    assert translations.translate_string("Czerwony Las · 5") == "Red Wood · 5"
    assert translations.translate_string("Czerwony Lasek") == "Czerwony Lasek"


def test_an_events_name_and_its_map_in_the_history_and_the_running_lines():
    for polish, translated in (
            ("Zuo: deszcz Metinów · Bokjung", "Zuo: Metin rain · Bokjung"),
            ("Pirat Tanaka · Dolina Orków", "Pirate Tanaka · Orc Valley"),
            ("Pirat Tanaka · Wybiera event", "Pirate Tanaka · Event's choice"),
            ("Zuo: deszcz Metinów · Las Duchów", "Zuo: Metin rain · Ghost Wood"),
            ("brak statystyk", "no statistics"), ("12 szkatułek", "12 chests"),
            ("📍 Wybiera event: Dolina Orków · do 08:43", "📍 Event's choice: Orc Valley · until 08:43"),
            ("Pyongmoo · 3 szt. · do 02.10 08:43 · 3 na mapie · 2 pokonanych · 5 botów",
             "Pyongmoo · 3 pcs. · until 02.10 08:43 · 3 on the map · 2 defeated · 5 bots"),
            ("do 08:43", "until 08:43"), ("Aktywny do 08:43", "Active until 08:43"),
            ("Event zakończony: Pirat Tanaka · Ognista Ziemia", "Event ended: Pirate Tanaka · Doyyumhwaji"),
            ("Event zakończony: Doświadczenie", "Event ended: Experience"),
            ("Wydropiono 12 szkatułek.", "12 chests dropped."),
            ("Edytuj: Szkatułki Blasku Księżyca (20:00–21:00)", "Edit: Moonlight Treasure Chests (20:00–21:00)"),
            ("Piraci naraz", "Pirates at once"), ("Środa", "Wednesday"), ("Śr", "Wed")):
        assert english(polish) == translated
    for _index, label in panel.EVENT_MAPS:
        # a village (Yongan, Bokjung...) is called the same in English
        assert label in translations.EXACT or label.isascii(), label


def _events_page_in_english(theme):
    finished = datetime(2026, 10, 2, 10, 30)
    runs = [{"id": 1, "kind": "zuo@64", "value": 8, "started_at": finished, "ended_at": finished,
             "chest_count": None, "yang_extra": None},
            {"id": 2, "kind": "tanaka@0", "value": 3, "started_at": finished, "ended_at": finished,
             "chest_count": None, "yang_extra": None},
            {"id": 3, "kind": "chest", "value": 0, "started_at": finished, "ended_at": finished,
             "chest_count": 12, "yang_extra": None}]
    panel.app.config["TESTING"] = True
    with patch.object(panel, "settings", return_value={**english_settings(), "theme": theme}), \
            patch.object(panel, "rows", side_effect=lambda sql, params=(): runs if "web_seban_event_runs" in sql else []), \
            patch.object(panel, "check_all_notifications"), \
            patch.object(panel, "read_events", return_value=([], {})), \
            patch.object(panel, "read_events_status", return_value={}), \
            patch.object(panel, "read_world_events_status", return_value={}), \
            patch.object(panel, "read_event_settings", return_value={"bots": 50}):
        return panel.app.test_client().get("/events").get_data(as_text=True)


def test_the_events_page_history_in_english_in_the_laka_theme():
    body = _events_page_in_english("laka")
    assert "<b>Zuo: Metin rain · Orc Valley</b>" in body
    assert "<b>Pirate Tanaka · Event&#x27;s choice</b>" in body
    assert "<small>no statistics</small>" in body and "<small>12 chests</small>" in body
    assert "<option value=\"67\">Ghost Wood</option>" in body


def test_the_events_page_history_in_english():
    body = _events_page_in_english("empire")
    assert "<td>Zuo: Metin rain · Orc Valley</td>" in body
    assert "<td>Pirate Tanaka · Event&#x27;s choice</td>" in body
    assert "<td>no statistics</td>" in body and "<td>12 chests</td>" in body
    assert "<option value=\"67\">Ghost Wood</option>" in body


def test_what_players_and_bots_wrote_is_never_translated():
    page = ('<p>Wołaj i Handel</p><a href="/p/1" translate="no">Las</a>'
            '<span translate="no">Szukam grupy, poziom 40 · Dolina Orków</span>'
            '<span translate="no">Miecz+0<script>var a = "<b>x</b>";</script></span><b>Miecz+0</b>')
    assert translations.translate_html(page, "en") == (
        '<p>Call and Trade</p><a href="/p/1" translate="no">Las</a>'
        '<span translate="no">Szukam grupy, poziom 40 · Dolina Orków</span>'
        '<span translate="no">Miecz+0<script>var a = "<b>x</b>";</script></span><b>Sword+0</b>')
    assert translations.translate_html(page, "pl") == page


def test_the_raids_notices_and_the_chat_channels_in_english():
    assert english("Drużyna Lider (Chunjo) pokonała Azraela w Katakumbach Diabła!") == \
        "Lider's party (Chunjo) defeated Azrael in the Devil's Catacomb!"
    assert english("Bohater pokonał Umarłego Rozpruwacza na dziewiątym piętrze Wieży Demonów! Ostatni cios: Seban.") == \
        "Bohater defeated the Death Reaper on the ninth floor of the Demon Tower! Last blow: Seban."
    # The boss is the core's Polish mob_proto name, put into the game's English.
    assert english("Boty z królestwa Jinno pokonały: Dziewięć Ogonów (6 min).") == \
        "Bots of the Jinno kingdom defeated: Nine Tails (6 min)."
    assert english("Boty z królestwa nieznanego królestwa pokonały: Królowa Pająków (1 min).") == \
        "Bots of an unknown kingdom defeated: Queen Spider (1 min)."
    assert english("Boty z królestwa Jinno pokonały: Dziewiec Ogonow (6 min).") == \
        "Bots of the Jinno kingdom defeated: Dziewiec Ogonow (6 min)."
    for polish, translated in (("WOŁAJ", "CALL"), ("HANDEL", "TRADE"), ("Rajd na Azraela", "Azrael raid"),
                               ("Pokonany boss", "Boss defeated")):
        assert english(polish) == translated
    # a whole text node that is a monster's name is somebody's name as often as not
    assert english("Wilk") == "Wilk"


def test_the_live_chat_refresh_arrives_translated_with_the_lines_as_written():
    stamp = datetime(2026, 10, 2, 10, 30)
    shout = {"id": "p:1", "sort_at": stamp, "time": "10:30:00", "type": "SHOUT", "author": "Las",
             "message": "Szukam grupy, poziom 40", "player_id": 1, "job": 0, "empire": 2}
    notice = {"id": "n:1", "sort_at": stamp, "time": "10:31:00", "type": "NOTICE", "author": "Boty Jinno",
              "message": "Boty z królestwa Jinno pokonały: Dziewięć Ogonów (6 min).", "player_id": 0,
              "job": 0, "empire": 3, "notice_label": "Pokonany boss"}
    panel.app.config["TESTING"] = True
    with patch.object(panel, "settings", return_value=english_settings()), \
            patch.object(panel, "live_chat_messages", return_value=[shout, notice]):
        fragment = panel.app.test_client().get("/api/live-chat").get_json()["html"]
    assert 'translate="no">Las</a>' in fragment
    assert 'translate="no">Szukam grupy, poziom 40</span>' in fragment
    assert "CALL" in fragment and "WOŁAJ" not in fragment
    assert "<b>Boss defeated</b><span>Bots of the Jinno kingdom defeated: Nine Tails (6 min).</span>" in fragment
