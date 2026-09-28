from datetime import datetime

import app as panel


def test_parses_azrael_notice():
    event = panel.legendary_announcement_from_syslog(
        "Sep 28 14:05:09 :: PLAYERBOT_CATACOMB: azrael down leader=Gabrysia18cm empire=2 after_min=17",
        2026,
    )
    assert event["kind"] == "announcement"
    assert event["method"] == "Rajd na Azraela"
    assert event["empire"] == 2
    assert event["time"] == datetime(2026, 9, 28, 14, 5, 9)
    assert event["message"] == "Drużyna Gabrysia18cm (Chunjo) pokonała Azraela w Katakumbach Diabła!"


def test_parses_reaper_notice_with_last_blow():
    event = panel.legendary_announcement_from_syslog(
        "Sep 28 14:06:10 :: PLAYERBOT_TOWER: reaper down map=660001 told=1 who=Rycerze last_blow=Seban after_s=932",
        2026,
    )
    assert event["method"] == "Wieża Demonów"
    assert "Umarłego Rozpruwacza" in event["message"]
    assert event["message"].endswith("Ostatni cios: Seban.")


def test_parses_world_boss_notice_and_ignores_unrelated_log():
    event = panel.legendary_announcement_from_syslog(
        "Sep 28 14:07:11 :: PLAYERBOT_RAID: killed boss=Dziewiec Ogonow race=1901 map=64 empire=3 members=12 after_s=367 reinforced=1",
        2026,
    )
    assert event["method"] == "Pokonany boss"
    assert event["message"] == "Boty z królestwa Jinno pokonały: Dziewiec Ogonow (6 min)."
    assert panel.legendary_announcement_from_syslog("Sep 28 14:07:12 :: PLAYERBOT_AI: idle", 2026) is None


def test_both_feeds_render_the_sparkle_variant():
    event = {
        "kind": "announcement", "cursor": "2026-09-28 14:05:09", "time_label": "14:05",
        "time_full": "28.09.2026 14:05", "day_label": "Dziś", "method": "Rajd na Azraela",
        "message": "Drużyna Gabrysia18cm pokonała Azraela!", "actor": "Gabrysia18cm",
        "player_id": 0, "job": 0, "empire": 2, "refine_tier": 0, "vnum": 0,
    }
    chat = dict(event, type="NOTICE", time="14:05:09", notice_label=event["method"])
    with panel.app.test_request_context("/"):
        live_html = panel.render_template("partials/live_chat_messages.html", messages=[chat])
        world_html = panel.render_template("partials/world_feed_events.html", events=[event])
    assert "metin-chat-line--legendary" in live_html and "legendary-sparkles" in live_html
    assert "feed-card--announcement" in world_html and "legendary-sparkles" in world_html
