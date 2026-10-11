import app as panel


def test_mission_ranking_uses_persisted_quest_states(monkeypatch):
    calls = []

    def fake_rows(sql, params=()):
        calls.append((sql, params))
        return []

    monkeypatch.setattr(panel, "rows", fake_rows)
    panel.bot_ranking("story")
    assert "main_quest_lv[0-9]+" in calls[-1][0]
    assert "subquest_[0-9]+" in calls[-1][0]
    assert "new_quest_lv[0-9]+" in calls[-1][0]
    assert calls[-1][1] == (panel.QUEST_COMPLETE_STATE,)
    panel.bot_ranking("hunting")
    assert "huntingProgress" in calls[-1][0]
    assert "levelup" not in calls[-1][0]


def test_completed_quests_use_log_only_for_dates(monkeypatch):
    def fake_rows(sql, params=()):
        if "FROM player.quest" in sql:
            return [{"szName": "main_quest_lv1", "lValue": panel.QUEST_COMPLETE_STATE},
                    {"szName": "subquest_16", "lValue": panel.QUEST_COMPLETE_STATE},
                    {"szName": "main_quest_lv2", "lValue": 1}]
        return [{"quest_name": "main_quest_lv1", "finished_at": "2026-10-11 12:00"},
                {"quest_name": "main_quest_lv2", "finished_at": "2026-10-11 12:01"}]

    monkeypatch.setattr(panel, "biologist_missions", lambda: ("make_herb_lv4",))
    monkeypatch.setattr(panel, "rows", fake_rows)
    monkeypatch.setattr(panel, "one", lambda *_: {"lValue": 0})
    completed = panel.character_completed_quests(1)
    assert [quest["key"] for quest in completed] == ["main_quest_lv1", "subquest_16"]
    assert completed[0]["date"] == "2026-10-11 12:00"
    assert completed[1]["date"] is None


def test_core_quest_and_investment_snapshots(tmp_path, monkeypatch):
    quest = tmp_path / "playerbot_quest_bots.tsv"
    quest.write_text("#PB15B1\tunix_ts\tpid\n100\t40\tskupiony\tsubquest_49\tgain_ice\t18\t50\tidzie_do_celu\t7\t0\t3\tCzym jest Bingsu?\n")
    investment = tmp_path / "playerbot_investment.tsv"
    investment.write_text("#PB17E1\n40\t45\t100\t900\t0\t350\t250\t35\t0\t0\t3098\t0\t0\t0\t0\t0\t0\t0\t100\n")
    monkeypatch.setattr(panel, "channel_paths", lambda name: [(1, tmp_path / name)])
    monkeypatch.setattr(panel, "_profile_snapshots", {
        "quest": {"until": 0, "rows": {}}, "investment": {"until": 0, "rows": {}}})
    current = panel.bot_profile_snapshots("quest")[40]
    assert current["title"] == "Czym jest Bingsu?"
    assert current["have"] == 18 and current["need"] == 50
    summary = panel.investment_summary(panel.bot_profile_snapshots("investment")[40])
    assert summary["share"] == 10.0
    assert summary["gap"] == 250 and summary["goal_vnum"] == 3098


def test_item_value_prefers_listing_then_market_then_npc(monkeypatch):
    def fake_rows(sql, params=()):
        if "GROUP BY vnum" in sql:
            return [{"vnum": 10, "n": 2, "y": 200}]
        if "FROM player.item WHERE owner_id" in sql and "SAFEBOX" not in sql:
            return []
        if "FROM player.item WHERE owner_id" in sql:
            return []
        if "FROM player.item_proto" in sql:
            return [{"vnum": 10, "gold": 20}, {"vnum": 11, "gold": 15}]
        return []

    items = [{"window": "INVENTORY", "vnum": 10, "count": 2, "ikashop_data": None},
             {"window": "EQUIPMENT", "vnum": 11, "count": 1, "ikashop_data": None},
             {"window": "IKASHOP_OFFLINESHOP", "vnum": 10, "count": 1,
              "ikashop_data": '{"yang": 300}'}]

    def item_rows(sql, params=()):
        if "AND `window` IN" in sql:
            return items
        return fake_rows(sql, params)

    monkeypatch.setattr(panel, "rows", item_rows)
    monkeypatch.setattr(panel, "time", type("Clock", (), {"time": staticmethod(lambda: 1000)})())
    monkeypatch.setattr(panel, "_ITEM_VALUE_PRICES", {"at": 0.0, "prices": {}})
    value = panel.character_item_value(1, None)
    assert value["value"] == {"equip": 15, "inv": 200, "safe": 0, "shop": 300, "total": 515}
    assert value["how"] == {"listed": 1, "market": 1, "npc": 1, "none": 0}
