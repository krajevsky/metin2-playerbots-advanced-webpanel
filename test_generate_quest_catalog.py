from tools.generate_quest_catalog import catalog


def test_catalog_matches_padded_filename_to_saved_quest_name(tmp_path):
    locale = tmp_path / "translate.lua"
    locale.write_bytes('gameforge.subquest_01._10_sendLetter = "Chory Brat"\n'.encode("cp1250"))
    quests = tmp_path / "quests"
    quests.mkdir()
    (quests / "subquest_01.quest").write_text(
        "quest subquest_1 begin\n"
        " state information begin\n"
        "  when 9003.chat.\"Hej\" begin\n"
        "  end\n"
        " end\n"
        " state later begin\n"
        "  when 9004.chat.\"Pa\" begin\n"
        "  end\n"
        " end\n"
        "end\n", encoding="utf-8")
    assert catalog(locale, quests) == {
        "subquest_1": {"title": "Chory Brat", "npc_vnum": 9003}
    }
