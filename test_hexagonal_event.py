"""Kiciamol's Hexagonal Chest event in the event planner (mt2009 only).

_dumitrualexandru, 16 October: the planner had no hexagonal option, and a
save here rewrote playerbot_events.tsv with the six kinds it knew, so the
classic panel's hexagonal rows and "activate now" line were lost. The kind
is valueless like a Moonlight window, and the page writes the quest's own
file, hexagonal_event.tsv, as Tieru's files/hexagonal_events.py does.
"""
import html
import importlib.util
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pymysql

import translations

HERE = Path(__file__).resolve().parent


def _refuse(*args, **kwargs):
    raise pymysql.MySQLError("test: no database")


def _load(name, engine):
    spec = importlib.util.spec_from_file_location(name, HERE / "app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    environment = {"PLAYERBOTS_ENGINE": engine, "DB_USER": os.environ.get("DB_USER", "test"),
                   "DB_PASSWORD": os.environ.get("DB_PASSWORD", "test")}
    with patch.dict(os.environ, environment), patch.object(pymysql, "connect", _refuse):
        spec.loader.exec_module(module)
    return module


mt2009 = _load("app_hexagonal_mt2009", "mt2009")
r40250 = _load("app_hexagonal_r40250", "r40250")

ROWS = [
    {"kind": "hexagonal", "days": [1, 3], "start": "20:00", "end": "21:00", "value": 0, "on": True, "map": 0},
    {"kind": "hexagonal", "days": [5], "start": "22:00", "end": "02:00", "value": 0, "on": True, "map": 0},
    {"kind": "hexagonal", "days": [6], "start": "10:00", "end": "11:00", "value": 0, "on": False, "map": 0},
    {"kind": "hexagonal", "days": [], "start": "10:00", "end": "11:00", "value": 0, "on": True, "map": 0},
    {"kind": "chest", "days": [1, 2, 3, 4, 5, 6, 7], "start": "18:00", "end": "19:00", "value": 0, "on": True, "map": 0},
]


class _Spool:
    def __init__(self, panel=mt2009):
        self.panel, self.dir = panel, tempfile.TemporaryDirectory()
        base = Path(self.dir.name)
        self.events, self.state, self.chance = (base / "playerbot_events.tsv", base / "hexagonal_event.tsv",
                                                base / "hexagonal_settings.json")
        self.patches = [patch.object(panel, "RATES_SPOOL", base), patch.object(panel, "EVENTS_FILE", self.events),
                        patch.object(panel, "HEXAGONAL_STATE_FILE", self.state),
                        patch.object(panel, "HEXAGONAL_SETTINGS_FILE", self.chance)]

    def __enter__(self):
        for item in self.patches:
            item.start()
        return self

    def __exit__(self, *exc):
        for item in self.patches:
            item.stop()
        self.dir.cleanup()


def _page(theme, language="en", post=None):
    settings = dict(mt2009.DEFAULT_SETTINGS, ui_language=language, setup_complete="1", auth_enabled="0", theme=theme)
    mt2009.app.config["TESTING"] = True
    until = int(time.time()) + 600
    with patch.object(mt2009, "settings", return_value=settings), \
            patch.object(mt2009, "rows", return_value=[]), \
            patch.object(mt2009, "check_all_notifications"), \
            patch.object(mt2009, "read_events_status", return_value={"hexagonal": mt2009.event_status_texts(
                {"scheduled": True, "active": True, "value": 0, "until": until, "next_start": 0})}), \
            patch.object(mt2009, "read_world_events_status", return_value={}):
        client = mt2009.app.test_client()
        if post is not None:
            return client.post("/events", data=post)
        return client.get("/events").get_data(as_text=True)


def test_the_kind_is_mt2009s_alone():
    assert "hexagonal" in mt2009.EVENT_KINDS and "hexagonal" not in r40250.EVENT_KINDS
    assert mt2009.EVENT_KINDS[:6] == r40250.EVENT_KINDS
    assert "hexagonal" in mt2009.EVENT_VALUELESS and "hexagonal" not in mt2009.EVENT_WORLD_KINDS


def test_the_quests_file():
    stamp = 1792160000
    text = mt2009.hexagonal_state_text(ROWS, {"hexagonal": {"until": stamp + 600}}, 200, stamp)
    assert text == "M2HEX1\nchance\t200\nnow\t%d\nweekly\t1,3\t1200\t1260\nweekly\t5\t1320\t120\n" % (stamp + 600)
    assert mt2009.hexagonal_state_text(ROWS, {"hexagonal": {"until": stamp - 1}}, 0, stamp) == \
        "M2HEX1\nchance\t0\nweekly\t1,3\t1200\t1260\nweekly\t5\t1320\t120\n"


def test_the_chance_as_the_classic_panel_keeps_it():
    with _Spool() as spool:
        assert mt2009.hexagonal_chance_permille() == 200
        spool.chance.write_text('{"format": 1, "permille": 125}\n', encoding="utf-8")
        assert mt2009.hexagonal_chance_permille() == 125
        spool.chance.write_text('{"permille": 2000}', encoding="utf-8")
        assert mt2009.hexagonal_chance_permille() == 0
        spool.chance.write_text("not json", encoding="utf-8")
        assert mt2009.hexagonal_chance_permille() == 0
    assert mt2009.hexagonal_percent_text(125) == "12.5"


def test_a_save_keeps_the_rows_and_writes_both_files():
    with _Spool() as spool:
        until = int(time.time()) + 3600
        mt2009.write_events(ROWS, {"hexagonal": {"kind": "hexagonal", "until": until, "value": 0}}, {"bots": 50})
        events = spool.events.read_text(encoding="utf-8")
        assert "hexagonal\t1,3\t20:00\t21:00\t0\n" in events
        assert "#off\thexagonal\t6\t10:00\t11:00\t0\n" in events
        assert "now\thexagonal\t%d\t0\n" % until in events
        rows, nows = mt2009.read_events()
        assert [r for r in rows if r["kind"] == "hexagonal"] == [r for r in ROWS if r["kind"] == "hexagonal"]
        assert nows["hexagonal"]["until"] == until
        assert spool.state.read_text(encoding="utf-8") == \
            "M2HEX1\nchance\t200\nnow\t%d\nweekly\t1,3\t1200\t1260\nweekly\t5\t1320\t120\n" % until


def test_r40250_writes_no_quest_file():
    with _Spool(r40250) as spool:
        r40250.write_events([ROWS[-1]], {}, {"bots": 50})
        assert spool.events.exists() and not spool.state.exists()


def test_the_planner_offers_the_kind_in_both_themes():
    with _Spool():
        for theme in ("empire", "laka"):
            body = _page(theme)
            assert '<option value="hexagonal">Hexagonal Treasure Chests</option>' in body
            assert "Chance per Metin:" in body and 'const valueless=["chest", "hexagonal"];' in body
            card = body.split('<input type="hidden" name="kind" value="hexagonal">', 1)[1].split("</form>", 1)[0]
            assert 'name="value"' not in card
        assert '<option value="hexagonal">Heksagonalne Szkatułki</option>' in _page("empire", "pl")


def test_activate_now_and_stop():
    with _Spool() as spool:
        spool.chance.write_text('{"format": 1, "permille": 0}\n', encoding="utf-8")
        assert _page("empire", post={"action": "now", "kind": "hexagonal", "minutes": "30"}).status_code == 302
        line = [l for l in spool.events.read_text(encoding="utf-8").splitlines() if l.startswith("now\t")][0]
        _now, kind, until, value = line.split("\t")
        assert (kind, value) == ("hexagonal", "0")
        assert spool.state.read_text(encoding="utf-8") == "M2HEX1\nchance\t0\nnow\t%s\n" % until
        _page("empire", post={"action": "stop", "kind": "hexagonal"})
        assert "now\thexagonal" not in spool.events.read_text(encoding="utf-8")
        assert spool.state.read_text(encoding="utf-8") == "M2HEX1\nchance\t0\n"


def test_the_english_texts():
    def english(text):
        return html.unescape(translations.translate_string(html.escape(text)))
    assert english("Okno heksagonalnych szkatułek zapisane na 30 minut, ale ich szansa dropu wynosi 0%. "
                   "Ustaw ją na stronie Eventy panelu klasycznego.") == \
        "Hexagonal chest window saved for 30 minutes, but their drop chance is 0%. Set it on the classic panel's Events page."
    assert english("Event zakończony: Heksagonalne Szkatułki") == "Event ended: Hexagonal Treasure Chests"
    assert english("Edytuj: Heksagonalne Szkatułki (20:00–21:00)") == "Edit: Hexagonal Treasure Chests (20:00–21:00)"
