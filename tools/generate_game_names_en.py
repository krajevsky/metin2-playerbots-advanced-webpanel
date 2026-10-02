# -*- coding: utf-8 -*-
"""The official English names of the world's items and monsters, for the panel.

    python tools/generate_game_names_en.py \\
        --names-tsv  <server>/linux-port/docker/game/playerbot_names_en.tsv \\
        --world-sql  <server>/linux-port/docker/mariadb/initdb.d/dumps/world.sql \\
        --apply-sh   <server>/linux-port/docker/mariadb/playerbot/apply.sh \\
        --out-dir    static

Writes static/item_names_en.json and static/mob_names_en.json, one line a
vnum: "10": ["Miecz+0", "Sword+0"] - the Polish name of the world's proto
(item_proto/mob_proto.locale_name, what the panel reads from the database
and prints) and the official English name the Playerbots core says to a
player whose client reads English. translations.py turns them into
"Polish name -> English name" for the English panel.

Nothing is translated here. playerbot_names_en.tsv is Playerbots' own file
(Tieru's tools/generate_english_names.py, shipped with every 2.x server in
the game image's share): Gameforge's English names from the client's locale
pack, and this world's own items and monsters named by hand where Gameforge
never named them. Each of its lines carries the FNV-1a hash of the Polish
proto name the English one was matched to; a line is taken here, as the core
takes it, only while the world still calls that vnum by that name - a proto
renamed since is left in Polish rather than given another item's English.
The world's names are read from the 2.x database dump, after the renames the
migrator (apply.sh) makes at every start. Deterministic; run again after a
server update brings a new names file or new protos.
"""
import argparse
import json
import os
import re
import sys

STRING = r"'((?:[^'\\]|\\.)*)'"
# INSERT rows of both protos begin with vnum, name, locale_name.
ROW = re.compile(r"[(]\s*(\d+)\s*,\s*" + STRING + r"\s*,\s*" + STRING + r"\s*,")
UNESCAPE = {"0": "\0", "b": "\b", "n": "\n", "r": "\r", "t": "\t", "Z": "\x1a"}
TABLES = {"i": "item_proto", "m": "mob_proto"}
OUTPUT = {"i": "item_names_en.json", "m": "mob_names_en.json"}


def unescape(text):
    return re.sub(r"\\(.)", lambda m: UNESCAPE.get(m.group(1), m.group(1)), text)


def fnv1a(raw):
    """The core's playerbot_names::HashProtoName, over the CP1250 bytes."""
    value = 2166136261
    for byte in raw:
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value


def load_world(path):
    """kind -> vnum -> [name, locale_name] of the dump's two protos."""
    with open(path, encoding="utf-8", errors="replace", newline="") as handle:
        text = handle.read()
    world = {}
    for kind, table in TABLES.items():
        block = re.search(r"INSERT INTO `%s` VALUES(.*?);\n" % table, text, re.S)
        if not block:
            sys.exit("generate_game_names_en: no INSERT INTO `%s` in %s" % (table, path))
        world[kind] = {int(m.group(1)): [unescape(m.group(2)), unescape(m.group(3))]
                       for m in ROW.finditer(block.group(1))}
    return world


def apply_renames(world, path):
    """What the migrator's UPDATEs of a proto's locale_name leave of it."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    renamed = []
    statement = (r"UPDATE world\.(item_proto|mob_proto) SET (.*?) "
                 r"WHERE vnum\s*(?:=\s*(\d+)|IN\s*\(([^)]*)\))")
    for m in re.finditer(statement, text):
        kind = "i" if m.group(1) == "item_proto" else "m"
        vnums = [int(m.group(3))] if m.group(3) else [int(v) for v in re.findall(r"\d+", m.group(4))]
        literal = re.search(r"(?:^|[\s,])locale_name\s*=\s*" + STRING, m.group(2))
        korean = re.search(r"(?:^|[\s,])locale_name\s*=\s*name\b", m.group(2))
        if not literal and not korean:
            continue
        for vnum in vnums:
            row = world[kind].get(vnum)
            if row:
                row[1] = unescape(literal.group(1)) if literal else row[0]
                renamed.append("%s%d" % (kind, vnum))
    return renamed


def read_names(path):
    """(kind, vnum, English name, hash) of every line of playerbot_names_en.tsv."""
    lines = []
    with open(path, encoding="ascii") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            kind, vnum, name, digest = line.rstrip("\r\n").split("\t")
            lines.append((kind, int(vnum), name, int(digest, 16)))
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--names-tsv", required=True, help="Playerbots' playerbot_names_en.tsv")
    parser.add_argument("--world-sql", required=True, help="the 2.x database dump, dumps/world.sql")
    parser.add_argument("--apply-sh", default="", help="the migrator, mariadb/playerbot/apply.sh")
    parser.add_argument("--out-dir", default="static")
    args = parser.parse_args()

    world = load_world(args.world_sql)
    renamed = apply_renames(world, args.apply_sh) if args.apply_sh else []
    taken = {"i": {}, "m": {}}
    left = {"not_in_world": [], "renamed_since": []}
    for kind, vnum, english, digest in read_names(args.names_tsv):
        row = world.get(kind, {}).get(vnum)
        if row is None:
            left["not_in_world"].append("%s%d" % (kind, vnum))
            continue
        try:
            same = fnv1a(row[1].encode("cp1250")) == digest
        except UnicodeEncodeError:
            same = False
        if not same:
            left["renamed_since"].append("%s%d" % (kind, vnum))
            continue
        taken[kind][vnum] = [row[1], english]

    for kind, filename in OUTPUT.items():
        body = ",\n".join("%s: %s" % (json.dumps(str(vnum)), json.dumps(pair, ensure_ascii=False))
                          for vnum, pair in sorted(taken[kind].items()))
        path = os.path.join(args.out_dir, filename)
        with open(path + ".tmp", "w", encoding="utf-8", newline="\n") as handle:
            handle.write("{\n" + body + "\n}\n")
        os.replace(path + ".tmp", path)
        print("generate_game_names_en: wrote %s (%d names)" % (path, len(taken[kind])))
    if renamed:
        print("  renamed by the migrator: %s" % " ".join(renamed))
    for reason, vnums in left.items():
        if vnums:
            print("  left out, %s %d: %s" % (reason, len(vnums), " ".join(vnums)))


if __name__ == "__main__":
    main()
