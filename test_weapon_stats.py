"""A weapon's attack and attack speed on the player card as the game's tooltip
shows them (Ziółek, 22.10: Olbrz. Topór+6 read 110-144 and 15% here, 122-159
and 25% in the game). static/item_defs.json is the r40250 table; on mt2009 the
card reads the world's player.item_proto."""
from unittest.mock import patch

import pymysql

import app as panel

# This world's rows (mt2009): type, subtype, value0..5, the level limit.
WORLD = {
    3086: (1, 3, (0, 0, 0, 77, 114, 45), 40),   # Olbrz. Topór+6
    3216: (1, 3, (0, 0, 0, 72, 109, 38), 30),   # Ostrze Z Czerw. Stali+6
    5116: (1, 4, (0, 35, 60, 50, 70, 38), 30),  # Antyczny Dzwon+6
    7094: (1, 5, (0, 64, 96, 58, 76, 22), 45),  # Wachlarz Feniksa+4
}


def world_rows(sql, params=()):
    if "FROM player.item_proto" in sql and "WHERE" not in sql:
        out = []
        for vnum, (kind, sub, values, level) in WORLD.items():
            row = dict(vnum=vnum, type=kind, subtype=sub, limittype0=1, limitvalue0=level,
                       limittype1=0, limitvalue1=0)
            row.update({"value%d" % i: v for i, v in enumerate(values)})
            out.append(row)
        return out
    return []


def card(engine_mt2009, vnum, speed, apply_type, source=world_rows):
    panel._WORLD_ITEM_BASE.update(rows={}, loaded=0.0, tried=0.0)
    item = dict(id=1, vnum=vnum, count=1, window="EQUIPMENT", pos=4, socket0=1, socket1=1, socket2=1,
                applytype0=apply_type, applyvalue0=speed, applytype1=0, applyvalue1=0,
                applytype2=0, applyvalue2=0, item_size=3, item_name="x",
                **{"attrtype%d" % i: 0 for i in range(7)}, **{"attrvalue%d" % i: 0 for i in range(7)})
    with patch.object(panel, "ENGINE_MT2009", engine_mt2009), patch.object(panel, "rows", source):
        panel._enrich_items([item])
    return item["base_stats"], [b["text"] for b in item["bonuses"]]


def test_mt2009_reads_the_worlds_numbers():
    stats, bonuses = card(True, 3086, 25, 17)
    assert "Wartość ataku: 122–159" in stats
    assert "Wymagany poziom: 40" in stats
    assert not [s for s in stats if "magicznego" in s]
    assert bonuses == ["Szybkość ataku +25%"]
    stats, bonuses = card(True, 3216, 25, 17)
    assert "Wartość ataku: 110–147" in stats
    assert bonuses == ["Szybkość ataku +25%"]


def test_mt2009_shaman_weapons():
    stats, bonuses = card(True, 5116, 15, 17)
    assert "Wartość ataku: 88–108" in stats
    assert "Wartość magicznego ataku: 73–98" in stats
    assert bonuses == ["Szybkość ataku +15%"]
    stats, _ = card(True, 7094, 28, 17)
    assert "Wartość ataku: 80–98" in stats
    assert "Wartość magicznego ataku: 86–118" in stats


def test_static_table_while_the_database_is_silent():
    def silent(sql, params=()):
        raise pymysql.MySQLError("not yet")
    stats, _ = card(True, 3086, 25, 17, silent)
    assert "Wartość ataku: 110–144" in stats


def test_r40250_keeps_the_static_table_and_its_two_hander_rule():
    stats, bonuses = card(False, 3086, 25, 7)
    assert "Wartość ataku: 110–144" in stats
    assert bonuses == ["Szybkość ataku +15%"]
