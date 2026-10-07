"""A bot's EXP lock on /player and the operator's override of it (Playerbots 2.x)."""
import html
import re
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import app as panel
import translations

PANEL_SETTINGS = {"setup_complete": "1", "auth_enabled": "0"}


def english(text):
    return html.unescape(translations.translate_string(html.escape(text)))


def fake_database(bot=1, companion=False, affect=False, flags=(), last=None):
    """one()/rows() answering the queries bot_exp_lock_view makes."""
    def one(sql, params=()):
        if "AS bot" in sql:
            return {"bot": bot}
        if "playerbot_sidekick" in sql:
            return {"n": 1} if companion else {}
        if "player.affect" in sql:
            assert params[1] == panel.AFFECT_EXP_BLOCK_MT2009 == 310
            return {"n": 1} if affect else {}
        if "web_admin_queue" in sql:
            return dict(last) if last else {}
        raise AssertionError(sql)

    def rows(sql, params=()):
        assert "player.quest" in sql and "exp_unlocked" in sql and "persona_lock_lv" in sql
        return [{"szState": state, "lValue": value} for state, value in flags]
    return one, rows


def view(live=None, engine=True, **database):
    one, rows = fake_database(**database)
    with patch.object(panel, "ENGINE_MT2009", engine), patch.object(panel, "one", side_effect=one), \
            patch.object(panel, "rows", side_effect=rows):
        return panel.bot_exp_lock_view({"id": 7, "name": "Grinder7"}, live)


def test_the_status_file_carries_the_two_columns_and_an_older_one_still_reads():
    with tempfile.TemporaryDirectory() as tmp:
        new = Path(tmp, "channel1", "game1")
        old = Path(tmp, "channel2", "game1")
        new.mkdir(parents=True)
        old.mkdir(parents=True)
        (new / "playerbot_status.tsv").write_text(
            "pid\tpersonality\tambition\trole\tin_party\tgoal\taction\tupdated_ms\tmap\tx\ty\thp\tmax_hp\t"
            "persona\tmood\tmood_lock\tlock_level\texp_block\texp_unlock\tstatus\n"
            "7\t0\t0\t0\t0\t0\t2\t1\t21\t1\t2\t3\t4\t0\t1\t0\t30\t0\t1\tWalcze z Wilk\n", encoding="cp1250")
        (old / "playerbot_status.tsv").write_text(
            "pid\tpersonality\tambition\trole\tin_party\tgoal\taction\tupdated_ms\tmap\tx\ty\thp\tmax_hp\t"
            "persona\tmood\tmood_lock\tlock_level\tstatus\n"
            "8\t0\t0\t0\t0\t0\t2\t1\t21\t1\t2\t3\t4\t0\t1\t0\t30\tWalcze z Wilk\n", encoding="cp1250")
        with patch.object(panel, "CHANNEL_VAR_ROOT", Path(tmp)):
            found = panel.live_statuses()
    assert found[7]["exp_block"] == 0 and found[7]["exp_unlock"] == 1 and found[7]["lock_level"] == 30
    assert found[7]["status"] == "Walcze z Wilk"
    assert "exp_block" not in found[8] and "exp_unlock" not in found[8] and found[8]["status"] == "Walcze z Wilk"


def test_a_bot_out_of_the_game_reads_its_saved_lock():
    card = view(affect=True, flags=((b"persona_lock_lv", 31), ("exp_unlocked", 0)))
    assert card["online"] is False and card["blocked"] is True and card["lock_level"] == 30
    assert card["unlocked"] is False and card["pending"] is None and card["wants_unlocked"] is False
    assert card["companion"] is False
    # A saved lock level of 1 is no lock at all.
    assert view(flags=(("persona_lock_lv", 1),))["lock_level"] is None


def test_a_bot_in_the_game_reads_the_status_file_over_the_saved_rows():
    card = view(live={"exp_block": 0, "exp_unlock": 1, "lock_level": 30}, affect=True,
                flags=(("exp_unlocked", 0),))
    assert card["online"] and card["blocked"] is False and card["unlocked"] is True and card["wants_unlocked"]
    # A core from before the columns: the saved rows answer for them.
    card = view(live={"lock_level": 0}, affect=True, flags=(("exp_unlocked", 1),))
    assert card["blocked"] is True and card["unlocked"] is True and card["lock_level"] is None


def test_a_request_still_waiting_is_what_the_button_follows():
    created = datetime(2026, 10, 7, 14, 5)
    card = view(affect=True, last={"cmd": "EXPUNLOCK", "status": "await", "created": created})
    assert card["pending"] == {"kind": "EXPUNLOCK", "applying": False, "since": "07.10.2026 14:05"}
    assert card["unlocked"] is False and card["wants_unlocked"] is True
    card = view(flags=(("exp_unlocked", 1),), last={"cmd": "EXPLOCK", "status": "w0000010000000200000003", "created": created})
    assert card["pending"]["applying"] and card["wants_unlocked"] is False
    # An answered request is no longer waiting.
    for status in ("done", "cancelled", "not_allowed"):
        assert view(last={"cmd": "EXPUNLOCK", "status": status, "created": created})["pending"] is None


def test_no_card_on_r40250_or_for_a_person_and_no_button_for_a_companion():
    assert view(engine=False) is None
    assert view(bot=0) is None
    assert view(companion=True)["companion"] is True


class FakeCursor:
    def __init__(self):
        self.calls = []
        self.lastrowid = 4242

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=()):
        self.calls.append((query, params))


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self.cursor_instance


def test_the_request_cancels_the_older_one_and_waits_as_await():
    assert "not_allowed" in panel.QUEUE_FINAL_STATUSES
    connection = FakeConnection()
    answers = iter([{"status": "await"}, {"status": "w0000010000000200001092"}, {"status": "done"}])
    with patch.object(panel, "db", return_value=connection), \
            patch.object(panel, "one", side_effect=lambda sql, params=(): next(answers)) as polled, \
            patch.object(panel.time, "sleep"):
        assert panel.queue_bot_exp_override("Grinder7", "EXPUNLOCK") == ("done", 4242)
    (cancel, cancel_params), (insert, insert_params) = connection.cursor_instance.calls
    assert "SET status='cancelled'" in cancel and "IN ('pending','await')" in cancel
    assert "('EXPUNLOCK','EXPLOCK')" in cancel and cancel_params == ("Grinder7",)
    assert "INSERT INTO player.web_admin_queue" in insert and "'await')" in insert
    assert insert_params == ("Grinder7", "EXPUNLOCK")
    assert all(call.args[1] == (4242,) for call in polled.call_args_list)


def test_a_bot_out_of_the_game_leaves_its_request_waiting():
    connection = FakeConnection()
    with patch.object(panel, "db", return_value=connection), \
            patch.object(panel, "one", return_value={"status": "await"}), \
            patch.object(panel.time, "sleep"):
        assert panel.queue_bot_exp_override("Grinder7", "EXPLOCK", wait=0.05) == ("await", 4242)
    # Nothing but the cancel of the older request and the insert: no timeout cancels this one.
    assert len(connection.cursor_instance.calls) == 2


BOT_CARD = {"companion": False}


def post(mode="unlock", engine=True, card=BOT_CARD, status="done"):
    """POST the card's button; card is what bot_exp_lock_view answers (None
    for a character that is not a bot)."""
    panel.app.config["TESTING"] = True
    with patch.object(panel, "settings", return_value=PANEL_SETTINGS), \
            patch.object(panel, "ENGINE_MT2009", engine), \
            patch.object(panel, "one", return_value={"id": 7, "name": "Grinder7"}), \
            patch.object(panel, "live_statuses", return_value={}), \
            patch.object(panel, "bot_exp_lock_view", return_value=card), \
            patch.object(panel, "queue_bot_exp_override", return_value=(status, 4242)) as queued:
        client = panel.app.test_client()
        response = client.post("/player/7/action/exp-lock", data={"mode": mode})
        with client.session_transaction() as saved:
            flashes = saved.get("_flashes", [])
    assert response.status_code == 302 and response.headers["Location"].endswith("/player/7")
    return queued, flashes


def test_the_button_queues_the_command_and_says_what_the_core_answered():
    queued, flashes = post("unlock")
    queued.assert_called_once_with("Grinder7", "EXPUNLOCK")
    assert flashes == [("success", "Grinder7: exp odblokowany, bot zdobywa doświadczenie.")]
    queued, flashes = post("restore")
    queued.assert_called_once_with("Grinder7", "EXPLOCK")
    assert flashes == [("success", "Grinder7: blokada przywrócona, o blokadzie decyduje osobowość.")]
    assert "nie jest teraz w grze" in post(status="await")[1][0][1]
    assert "właśnie wykonuje zmianę" in post(status="w0000010000000200001092")[1][0][1]
    assert post(status="not_allowed")[1][0] == ("error", "Panel nie zmienia blokady exp tej postaci: to nie jest bot "
                                                       "z rejestru albo to towarzysz gracza.")
    assert post(status="gone")[1][0] == ("error", "Nie udało się zmienić blokady exp (gone).")


def test_nothing_is_queued_for_a_companion_a_person_r40250_or_a_bad_mode():
    for kwargs in ({"card": {"companion": True}}, {"card": None}, {"engine": False}, {"mode": "both"}):
        queued, flashes = post(**kwargs)
        queued.assert_not_called()
        assert len(flashes) == 1 and flashes[0][0] == "error"


def test_the_card_and_its_messages_in_english():
    template = (Path(panel.__file__).parent / "templates" / "player.html").read_text(encoding="utf-8")
    source = Path(panel.__file__).read_text(encoding="utf-8")
    card_texts = (
        "⚡ Doświadczenie (EXP)", "🔒 Exp zablokowany: bot nie zdobywa doświadczenia",
        "✅ Exp leci: bot zdobywa doświadczenie", "Bota nie ma w grze, stan z ostatniego zapisu postaci.",
        "🔓 Operator odblokował exp: osobowość nie blokuje tego bota.",
        "Bez zmiany operatora: o blokadzie decyduje osobowość.", "Przywróć blokadę", "🔓 Odblokuj exp",
        "Towarzysz gracza: jego exp zależy od Pierścienia Anty-Exp właściciela i jego własnego limitu, nie od panelu.",
    )
    for text in card_texts:
        assert text in template
        assert text in translations.EXACT and english(text) != text
    help_text = re.search(r"<small class=\"muted\">(„Odblokuj exp”[^<]+)</small>", template).group(1)
    assert english(help_text).startswith('"Unlock EXP" lets the bot gain experience')
    assert "Panel nie zmienia blokady exp tej postaci: to nie jest bot z rejestru " in source
    assert english("Panel nie zmienia blokady exp tej postaci: to nie jest bot z rejestru albo to towarzysz gracza.") \
        == "The panel does not change this character's EXP lock: it is not a registered bot, or it is a player's companion."
    assert english("Osobowość trzyma go na poziomie 30.") == "Its personality holds it at level 30."
    assert english("⏳ Odblokowanie czeka na wejście bota do gry (zlecone 07.10.2026 14:05).") == \
        "⏳ The unlock waits for the bot to come into the game (asked 07.10.2026 14:05)."
    assert english("⏳ Przywrócenie blokady czeka na wejście bota do gry (zlecone 07.10.2026 14:05).") == \
        "⏳ Restoring the lock waits for the bot to come into the game (asked 07.10.2026 14:05)."
    assert english("⏳ Rdzeń bota właśnie wykonuje zmianę (zlecone 07.10.2026 14:05).") == \
        "⏳ The bot's core is making the change right now (asked 07.10.2026 14:05)."
    for name in ("Grinder7", "[GA]Seban", "Dolina"):
        assert english(f"{name}: exp odblokowany, bot zdobywa doświadczenie.") == \
            f"{name}: EXP unlocked, the bot gains experience."
        assert english(f"{name}: blokada przywrócona, o blokadzie decyduje osobowość.") == \
            f"{name}: the lock is restored, its personality decides."
        assert english(f"{name} nie jest teraz w grze albo jego rdzeń jeszcze nie odpowiedział. Zmiana czeka "
                       f"i wykona ją rdzeń bota, gdy bot będzie w grze.") == \
            f"{name} is not in the game now, or its core has not answered yet. The change waits, and the bot's " \
            f"core makes it once the bot is in the game."
        assert english(f"Rdzeń bota {name} właśnie wykonuje zmianę. Odśwież stronę za chwilę.") == \
            f"The core of {name} is making the change right now. Reload the page in a moment."
    assert english("Nie udało się zmienić blokady exp (gone).") == "Could not change the EXP lock (gone)."
    assert english("Normalny · blokada expa na 30 lvl").endswith("EXP locked at level 30")
    assert english("Normalny · exp odblokowany przez operatora").endswith("EXP unlocked by the operator")
    # Polish stays byte for byte as Jinja made it.
    assert translations.translate_html("<b>🔓 Odblokuj exp</b>", "pl") == "<b>🔓 Odblokuj exp</b>"


def render_card(exp_lock):
    """The card as player.html renders it, cut out of the template itself."""
    template = (Path(panel.__file__).parent / "templates" / "player.html").read_text(encoding="utf-8")
    start = template.index("{% if exp_lock %}")
    end = template.index("{% endif %}", template.index("</form>", start)) + len("{% endif %}")
    with panel.app.test_request_context("/player/7"):
        return panel.app.jinja_env.from_string(template[start:end]).render(
            exp_lock=exp_lock, character={"id": 7})


def test_the_card_renders_its_state_and_one_button():
    panel.app.jinja_env.get_template("player.html")
    blocked = render_card({"companion": False, "online": False, "blocked": True, "unlocked": False,
                           "lock_level": 30, "pending": None, "wants_unlocked": False})
    assert 'action="/player/7/action/exp-lock"' in blocked
    assert "🔒 Exp zablokowany" in blocked and "Osobowość trzyma go na poziomie 30." in blocked
    assert "stan z ostatniego zapisu postaci" in blocked
    assert 'name="mode" value="unlock"><button>🔓 Odblokuj exp</button>' in blocked
    assert "Przywróć blokadę</button>" not in blocked
    waiting = render_card({"companion": False, "online": True, "blocked": True, "unlocked": False, "lock_level": None,
                           "pending": {"kind": "EXPUNLOCK", "applying": False, "since": "07.10.2026 14:05"},
                           "wants_unlocked": True})
    assert "⏳ Odblokowanie czeka na wejście bota do gry (zlecone 07.10.2026 14:05)." in waiting
    assert 'name="mode" value="restore"><button class="secondary">Przywróć blokadę</button>' in waiting
    assert "Odblokuj exp</button>" not in waiting
    assert "stan z ostatniego zapisu" not in waiting
    english_page = html.unescape(translations.translate_html(waiting, "en"))
    for text in ("⚡ Experience (EXP)", "🔒 EXP blocked: the bot gains no experience",
                 "⏳ The unlock waits for the bot to come into the game (asked 07.10.2026 14:05).",
                 "No operator override: its personality decides the lock.", ">Restore the lock</button>",
                 '"Unlock EXP" lets the bot gain experience'):
        assert text in english_page
    assert not re.search(r"[ąćęłńóśźż]", re.sub(r"<[^>]+>", "", english_page), re.I)
    companion = render_card({"companion": True})
    assert "Towarzysz gracza" in companion and "<button" not in companion
    assert render_card(None).strip() == ""
