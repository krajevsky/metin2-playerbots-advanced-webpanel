"""A GM grant reaches the running game (issue #606 of Playerbots 2.x).

A game core reads common.gmlist when it boots and on /reload a, never at a
login, so the row the panel writes grants nothing until one of the two. Every
grant now queues GMRELOAD - a row naming nobody, status 'await', which the
suite's game cores from 2.2.139 answer by reloading the list themselves -
beside the old GM_RELOAD for each online IMPLEMENTOR, and says what came of it.
"""
import html
from unittest.mock import patch

import app as panel
import translations


def english(text):
    return html.unescape(translations.translate_string(html.escape(text)))


class FakeCursor:
    def __init__(self, store):
        self.store = store
        self.lastrowid = None
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=()):
        if sql.startswith("INSERT INTO player.web_admin_queue"):
            self.store["next"] += 1
            self.lastrowid = self.store["next"]
            if "'GMRELOAD'" in sql:
                assert "'await'" in sql and "('',"in sql
                self.store["queue"][self.lastrowid] = ("", "GMRELOAD", "await")
            else:
                self.store["queue"][self.lastrowid] = (params[0], "GM_RELOAD", "pending")
            return 1
        if sql.startswith("SELECT mName FROM common.gmlist"):
            self._result = [{"mName": name} for name in self.store["implementors"]]
            return len(self._result)
        raise AssertionError(sql)

    def fetchall(self):
        return self._result


class FakeConnection:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def cursor(self):
        return FakeCursor(self.store)


def run(engine=True, implementors=(), answers=None):
    """queue_gm_reload against a fake queue; `answers` maps a command to the
    status the game gives its row."""
    store = {"next": 0, "queue": {}, "implementors": list(implementors), "deleted": []}
    answers = answers or {}

    def rows(sql, params=()):
        if sql.startswith("SELECT status FROM player.web_admin_queue"):
            out = []
            for qid in params:
                name, cmd, status = store["queue"][qid]
                if cmd in answers:
                    status = answers[cmd]
                    store["queue"][qid] = (name, cmd, status)
                out.append({"status": status})
            return out
        if sql.startswith("DELETE FROM player.web_admin_queue"):
            assert "status IN ('pending','await')" in sql
            for qid in params:
                if store["queue"][qid][2] in ("pending", "await"):
                    store["deleted"].append(store["queue"][qid][1])
            return []
        raise AssertionError(sql)

    with patch.object(panel, "ENGINE_MT2009", engine), \
            patch.object(panel, "db", lambda: FakeConnection(store)), \
            patch.object(panel, "rows", side_effect=rows), \
            patch.object(panel, "GM_RELOAD_WAIT_SECONDS", 1.5), \
            patch.object(panel.time, "sleep", lambda s: None):
        result = panel.queue_gm_reload()
    return result, store


def test_a_core_reloads_the_list_with_nobody_online():
    done, store = run(answers={"GMRELOAD": "done"})
    assert done is True
    assert [cmd for _, cmd, _ in store["queue"].values()] == ["GMRELOAD"]
    assert store["deleted"] == []


def test_an_online_implementor_still_reloads_an_old_server():
    done, store = run(implementors=["Admin"], answers={"GM_RELOAD": "done"})
    assert done is True
    # The GMRELOAD nobody claimed is withdrawn, never left for a later core.
    assert store["deleted"] == ["GMRELOAD"]


def test_nothing_answers_and_both_rows_are_withdrawn():
    done, store = run(implementors=["Admin"])
    assert done is False
    assert sorted(store["deleted"]) == ["GMRELOAD", "GM_RELOAD"]


def test_r40250_asks_no_core():
    done, store = run(engine=False)
    assert done is False
    assert store["queue"] == {}


def test_the_hints_name_the_two_ways_and_never_the_next_login():
    assert "/reload a" in panel.GM_RELOAD_FAILED_HINT
    assert "restarcie serwera" in panel.GM_RELOAD_FAILED_HINT
    assert "przelogowania" in panel.GM_RELOAD_DONE_HINT
    for text in (panel.GM_RELOAD_DONE_HINT, panel.GM_RELOAD_FAILED_HINT,
                 "Utworzono konto „sosen111” i postać GM „GM”. " + panel.GM_RELOAD_FAILED_HINT,
                 "Ranga GM „GM” nadana postaci Friend. " + panel.GM_RELOAD_DONE_HINT):
        translated = english(text)
        assert "Gra " not in translated and "Utworzono" not in translated and "nadana" not in translated, translated
