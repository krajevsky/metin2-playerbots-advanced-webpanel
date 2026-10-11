"""Generate static quest titles from the game's Polish Lua locale and scripts.

Usage on the game host:
  python3 tools/generate_quest_catalog.py PATH_TO_TRANSLATE_LUA PATH_TO_QUEST_DIR

The output is JSON on stdout. It contains only quest names, localized titles,
and the first NPC VNUM explicitly named by a quest script. The panel resolves
that VNUM against its own mob_proto, so the catalog stays server-independent.
"""

import json
import re
import sys
from pathlib import Path


VALUE = re.compile(r'^gameforge\.(\w+)\.(_[\w]+)\s*=\s*"(.*)"\s*$')
QUEST = re.compile(r'\bquest\s+([\w]+)\s+begin')
NPC = re.compile(r'\b(\d{4,6})\.chat\b')
NUMBER = re.compile(r'^_(\d+)')
ACTION = re.compile(r'^(?:idź|wróć|zapytaj|spotkaj|przynieś|dostarcz|znajdź|zanieś|zdobądź)\b', re.I)
# These are verbatim alternatives in translate.lua where a generic NPC or
# mid-quest prompt scores above the quest's clearer game title.
TITLE_KEYS = {
    "main_quest_lv10": "_110_sayTitle",
    "subquest_30": "_100_sendLetter",
    "subquest_31": "_100_sendLetter",
    "subquest_34": "_90_sendLetter",
    "subquest_41": "_10_targetVid",
    "find_brother_article": "_130_sendLetter",
}


def title_score(key, value):
    lower = key.lower()
    if "set_title" in lower or "settitle" in lower:
        score = 112 if "qsettitle" not in lower else 78
    elif "sendletter" in lower:
        score = 110
    elif "saytitle" in lower:
        score = 100
    elif "npcchat" in lower:
        score = 90
    elif "targetvid" in lower:
        score = 75
    elif "makequestbutton" in lower:
        score = 70
    else:
        return -1000
    number = NUMBER.match(key)
    stage = int(number.group(1)) if number else 0
    # A late letter usually starts a follow-up stage (e.g. main quest 7's
    # "Kredyt" at step 180), rather than naming the original quest.
    if "sendletter" in lower and stage > 70:
        return -1000
    score -= stage / 10
    if ACTION.search(value):
        score -= 20
    if "npcchat" in lower and ("?" in value or "..." in value):
        score -= 30
    if value.endswith(":") or ": " in value:
        score -= 45
    if len(value) < 5:
        score -= 20
    return score


def catalog(translation_file, quest_dir):
    translated = {}
    for line in translation_file.read_bytes().decode("cp1250", "replace").splitlines():
        match = VALUE.match(line)
        if not match:
            continue
        value = match.group(3).replace("[ENTER]", " ").strip()
        if 3 <= len(value) <= 70 and "%" not in value and "[" not in value:
            translated.setdefault(match.group(1), []).append((match.group(2), value))

    result = {}
    for path in quest_dir.rglob("*.quest"):
        source = path.read_bytes().decode("cp1250", "replace")
        match = QUEST.search(source)
        if not match:
            continue
        name = match.group(1)
        if not (re.fullmatch(r"(?:main_quest_lv|new_quest_lv|subquest_)\d+", name)
                or name in ("find_brother_article", "find_squareguard")):
            continue
        aliases = {path.stem, name}
        # Some early files are subquest_01.quest but persist as subquest_1.
        candidates = [(title_score(key, value), value) for alias in aliases
                      for key, value in translated.get(alias, [])]
        candidates = [pair for pair in candidates if pair[0] > 0]
        if not candidates:
            continue
        score, title = max(candidates, key=lambda pair: pair[0])
        if name in TITLE_KEYS:
            title = next((value for alias in aliases for key, value in translated.get(alias, [])
                          if key == TITLE_KEYS[name]), title)
        # The first chat in the opening information/start state is the
        # character's first explicit contact. Later chats may be recipients.
        first_npc = None
        for opening in re.finditer(r'\bstate (?:information|start) begin\b(.*?)(?=\n\s*state\s+\w+\s+begin|\Z)',
                                   source, re.S):
            first_npc = NPC.search(opening.group(1))
            if first_npc:
                break
        result[name] = {"title": title, "npc_vnum": int(first_npc.group(1)) if first_npc else None}
    return dict(sorted(result.items()))


if __name__ == "__main__":
    print(json.dumps(catalog(Path(sys.argv[1]), Path(sys.argv[2])), ensure_ascii=False, indent=2))
