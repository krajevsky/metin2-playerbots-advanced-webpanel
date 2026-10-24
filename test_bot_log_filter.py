"""A character's live log shows the lines about it alone (Kordyl13, 23 October).

bot_log_line_is_about is taken out of app.py by its source, so the test needs
neither the database nor Flask.
"""
import ast
import os
import re

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")


def _matcher():
    tree = ast.parse(open(APP, encoding="utf-8").read())
    wanted = {"BOT_LOG_PID_RE", "BOT_LOG_NAME_RE", "bot_log_line_is_about", "bot_log_lines_about"}
    nodes = [n for n in tree.body
             if (isinstance(n, ast.FunctionDef) and n.name in wanted)
             or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in wanted for t in n.targets))]
    ns = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), APP, "exec"), ns)
    return ns


T = "Oct 23 23:29:21 :: "
CASES = [
    (T + "PLAYERBOT_HUNT: errand pid=2189 name=SAJBER map=61 mob=Lodowy Golem", "SAJBER", 2189, True),
    (T + "PLAYERBOT_HUNT: errand pid=2189 name=SAJBER map=61 mob=Lodowy Golem", "lodowy", 3001, False),
    (T + "PLAYERBOT_PARTY: assist pid=115 name=Viktoria target=Lodowy Golem", "Lodowy", 3001, False),
    (T + "PLAYERBOT_ESCORT: formed leader=2213 name=Art shaman=2170 shaman_name=Filantrop", "Filantrop", 2170, False),
    (T + "PLAYERBOT_X: pid=12 name=botgrom2 map=1", "botgrom", 11, False),
    (T + "PLAYERBOT_SHOP: line home pid=1747 reason=stale", "XxxUFOxxX", 1747, True),
    (T + "GIVE_GOLD: LastPhoenix 4290", "LastPhoenix", 9, True),
    (T + "LastPhoenix: USE_ITEM Czerwona Mikstura(D) (inven 1, cell: 0)", "LastPhoenix", 9, True),
    (T + "SECTREE DIFFER: fraaaanek 25x130 was 26x130 dist 1.0m", "fraaaanek", 9, True),
    (T + "HorseSummon : Brygadzista lv:45 bSummon:1 fromFar:0 (vnum 20105)", "Brygadzista", 9, True),
    (T + "NieBijOddam CHAIN INDEX 0 DAM 964 DT 8", "NieBijOddam", 9, True),
    (T + "QUEST [REWARD] item 50255 to WspanialyCzlowiek", "WspanialyCzlowiek", 9, True),
    (T + "CRUSH! zawszenadziewiec -> Lodowy Robak (492100 227935) -> (491912 228003)", "Lodowy", 9, False),
    (T + "AddAffect Lodowy Wieloryb Zab. type 210 apply 0 0 flag 6 duration 3", "Lodowy", 9, False),
    (T + "DROP_ITEM: Futro Yeti 429912 196717 from Elit. Ork Zwiadowca", "Zwiadowca", 9, False),
    (T + "SAVE: Lodowy 829328x471375", "lodowy", 9, False),
]


def test_lines_about_the_character_alone():
    about = _matcher()["bot_log_line_is_about"]
    for line, name, pid, expected in CASES:
        assert about(line, name, pid) is expected, (line, name, pid)


def test_a_line_by_pid_alone_is_kept():
    lines_about = _matcher()["bot_log_lines_about"]
    lines = [c[0] for c in CASES]
    assert len(lines_about(lines, "XxxUFOxxX", 1747)) == 1
    assert len(lines_about(lines, "LastPhoenix", 9)) == 2
