import json
import hashlib
import logging
import os
import hmac
import socket
import time
import re
import uuid
import zlib
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta
from functools import wraps

import pymysql
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SEBAN_SESSION_SECRET", "change-this-before-public-use")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
    # Cookies are scoped to the host, not the port. A dedicated name prevents
    # the classic Tieru panel on :7788 from overwriting this panel on :7789.
    SESSION_COOKIE_NAME=os.environ.get("SEBAN_SESSION_COOKIE_NAME", "seban_panel_session"),
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

# Nazwy wiosek pochodzą z questów silnika: new_quest_lv52 czyta pierwsze
# wioski jako { "Yongan", "Joan", "Pyongmoo" } wg królestwa, a new_quest_lv7
# nazywa drugie Jayang, Bokjung i Bakra.
MAP_NAMES = {
    1: "Shinsoo M1 — Yongan", 3: "Shinsoo M2 — Jayang", 4: "Shinsoo M3 — Jungrang",
    5: "Loch Małp Shinsoo", 44: "Jinno M3 — Imha", 45: "Loch Małp Jinno",
    21: "Chunjo M1 — Joan", 23: "Chunjo M2 — Bokjung",
    24: "Chunjo M3 — Waryong", 25: "Loch Małp Chunjo",
    41: "Jinno M1 — Pyongmoo", 43: "Jinno M2 — Bakra",
    61: "Góra Sohan", 63: "Pustynia Yongbi", 64: "Dolina Orków", 104: "Loch Pająków V1",
    65: "Świątynia Hwang", 71: "Loch Pająków V2",
    108: "Loch Małp Normalny", 109: "Loch Małp Trudny",
    67: "Las", 68: "Czerwony Las", 66: "Wieża Demonów",
}
MAP_BOUNDS = {
    1: (409600, 896000, 102400, 128000), 3: (307200, 819200, 102400, 102400),
    4: (128000, 0, 51200, 51200), 5: (768000, 435200, 76800, 76800),
    41: (921600, 204800, 102400, 128000), 43: (819200, 204800, 102400, 102400),
    44: (230400, 0, 51200, 51200), 45: (921600, 435200, 76800, 76800),
    21: (0, 102400, 102400, 128000), 23: (102400, 204800, 102400, 102400),
    24: (179200, 0, 51200, 51200), 25: (844800, 435200, 76800, 76800),
    61: (358400, 153600, 153600, 153600), 63: (204800, 486400, 153600, 153600),
    64: (256000, 665600, 153600, 153600), 104: (51200, 486400, 76800, 76800),
    65: (537600, 51200, 102400, 102400), 71: (665600, 435200, 102400, 102400),
    108: (128000, 640000, 76800, 76800), 109: (128000, 716800, 76800, 76800),
    # Re-derived 2026-09-15 straight from each map's own Setting.txt
    # (BasePosition + MapSize x 25600, the same formula that reproduces
    # Chunjo M1's already-correct (0,102400,102400,128000) from its own
    # MapSize 4x5 / BasePosition 0,102400) -- the original values here were
    # wrong on all three axes for at least one of the three maps each,
    # flagged by Tieru testing the exported panel.
    67: (281600, 0, 51200, 51200), 68: (1049600, 0, 76800, 76800),
    66: (128000, 793600, 76800, 76800),
}
# "Boty CH1/CH2 na mapach" tile (dashboard-charts.js) used to draw the full
# map name under each bar in 9px text -- fine for "M1"/"M2"/"M3" (matched by
# map_short_code's regex) but any dungeon/special zone has no "M<n>" in its
# name, so it fell back to the FULL long name at that same tiny size:
# unreadable, overlapping neighbours. Operator's fix (2026-09-22): a small
# item icon of that map's own well-known material drop instead -- same icon
# for every kingdom's M1/M2/M3 (the tiers drop the same material regardless
# of kingdom), disambiguated by a tiny kingdom flag drawn next to it.
MAP_ICON_VNUM = {
    1: 30010, 21: 30010, 41: 30010,  # M1 -> Żółć Niedźwiedzia
    3: 30021, 23: 30021, 43: 30021,  # M2 -> Kawałek Klejnotu
    # M3: no material drop reads well as a tiny icon here (operator's call,
    # 2026-09-22) -- falls back to the "M3" text code + kingdom flag instead,
    # same as any other map with no entry in this dict.
    5: 50050, 25: 50050, 45: 50050, 108: 50050, 109: 50050,  # Loch Małp -> Medal Konny
    64: 30006,  # Dolina Orków -> Ząb Orka
    63: 30022,  # Pustynia Yongbi -> Ogon Węża
    61: 30042,  # Góra Sohan -> Pazur Tygrysa
}
MAP_KINGDOM = {1: 1, 3: 1, 4: 1, 5: 1, 21: 2, 23: 2, 24: 2, 25: 2, 41: 3, 43: 3, 44: 3, 45: 3}
TRACKED_MAP_OPTIONS = tuple((index, MAP_NAMES[index]) for index in MAP_BOUNDS)
MAP_RESPAWN_OPTIONS = (
    (1, "Shinsoo M1 — Yongan"), (3, "Shinsoo M2 — Jayang"), (21, "Chunjo M1 — Joan"),
    (23, "Chunjo M2 — Bokjung"), (41, "Jinno M1 — Pyongmoo"), (43, "Jinno M2 — Bakra"),
    (4, "Shinsoo M3 — Jungrang"), (24, "Chunjo M3 — Waryong"), (44, "Jinno M3 — Imha"),
    (5, "Loch Małp Shinsoo"), (45, "Loch Małp Jinno"),
    (25, "Loch Małp Chunjo"), (61, "Góra Sohan"), (63, "Pustynia Yongbi"), (64, "Dolina Orków"),
    (104, "Loch Pająków V1"), (71, "Loch Pająków V2"), (108, "Loch Małp Normalny"), (109, "Loch Małp Trudny"),
)
# Monkey Dungeons and Spider Dungeon V1 ship no stone.txt, so only their mob
# respawns can be configured. The explicit allowlist also protects the helper.
MAP_STONE_RESPAWN_IDS = frozenset(index for index, _name in MAP_RESPAWN_OPTIONS if index not in {5, 25, 45, 104, 71, 108, 109})
CHANNEL_VAR_ROOT = Path(os.environ.get("PLAYERBOTS_VAR_ROOT", "/opt/metin2/var"))
GUILD_TIERS = {0: "Elitarna", 1: "Silna", 2: "Średnia", 3: "Zwykła"}


def discovered_channels():
    """Sorted channel numbers with a live /opt/metin2/var/channelN directory --
    scales past CH2 automatically if the engine ever ships CH3+, instead of the
    CH1-only paths Tieru's own stock panel still hardcodes."""
    found = []
    try:
        for path in CHANNEL_VAR_ROOT.glob("channel*"):
            match = re.fullmatch(r"channel(\d+)", path.name)
            if match and path.is_dir():
                found.append(int(match.group(1)))
    except OSError:
        pass
    return sorted(found) or [1]


def channel_paths(filename):
    """Yield (channel, Path) for filename under every core of every known
    channel, e.g. (2, .../channel2/game1/playerbot_status.tsv)."""
    for channel in discovered_channels():
        try:
            for path in CHANNEL_VAR_ROOT.glob(f"channel{channel}/*/{filename}"):
                yield channel, path
        except OSError:
            continue
RATES_SPOOL = Path("/opt/m2spool")
UPDATE_SPOOL = Path("/opt/m2update")
# "Diagnostyka -> Logi panelu": a persistent, downloadable record of what
# actually crashed and when, so a bug report can come with proof instead of
# "it just broke" -- operator's ask, 2026-09-22. RATES_SPOOL is already a
# named Docker volume mounted into this container (survives recreates/
# updates, unlike the container's own filesystem), so the log file does too.
# Flask/Werkzeug already call app.logger.error() with the full traceback for
# every unhandled exception reaching the WSGI layer (that's what docker logs
# has shown all session) -- this just adds a second, rotating destination for
# the exact same messages, nothing more to wire up per-route.
PANEL_LOG_DIR = RATES_SPOOL / "panel-logs"
PANEL_LOG_FILE = PANEL_LOG_DIR / "panel.log"
try:
    PANEL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    _panel_log_handler = RotatingFileHandler(PANEL_LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    _panel_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _panel_log_handler.setLevel(logging.WARNING)
    app.logger.addHandler(_panel_log_handler)
    app.logger.setLevel(logging.WARNING)
except OSError:
    pass
UPDATE_WATCHER_MAX_AGE_SECONDS = 90
PLAYERBOTS_RELEASE_URL = "https://api.github.com/repos/TieruYT/metin2-playerbots/releases/latest"
PLAYERBOTS_RELEASE_CACHE_SECONDS = 900
_playerbots_release_cache = {"checked_at": 0.0, "latest": None, "error": None}
SERVER_SETTINGS_READY_MAX_AGE_SECONDS = 20
SERVER_SETTINGS_STALE_SECONDS = 600
GAME_HOST = os.environ.get("PLAYERBOTS_GAME_HOST", "metin2-game")
GAME_LOGIN_PORT = int(os.environ.get("PLAYERBOTS_LOGIN_PORT", "11000"))
GAME_WORLD_PORT = int(os.environ.get("PLAYERBOTS_WORLD_PORT", "13000"))
RATE_NAMES = ("exp", "drop", "yang")
REGEN_DELAY_FLAGS = {"boss": "fastBossSpawn", "mob": "fastMobSpawn"}
REGEN_COUNT_FLAGS = {"boss": "m2_boss_count", "mob": "m2_mob_count"}
REGEN_DELAY_MIN = 10
REGEN_COUNT_CHOICES = (100, 150, 200, 250, 300, 400)
QUEUE_FINAL_STATUSES = frozenset((
    "done", "bad_args", "failed", "unknown_cmd", "cancelled", "no_gm",
))
AI_WEIGHTS_FILE = RATES_SPOOL / "playerbot_weights.tsv"
# Ported from Tieru's classic panel (admin_panel.py's /ai/items) -- confirmed
# the engine itself reads this exact path live, like the weights file
# (playerbot_config.h's PLAYERBOT_ITEM_POLICY_PATH), 2026-09-26 audit.
AI_ITEM_POLICY_FILE = RATES_SPOOL / "playerbot_item_policy.tsv"
AI_ITEM_POLICY_WORDS = ("keep", "stall", "merchant", "drop", "zostaw", "stragan", "handlarz", "wyrzuc")
AI_WEIGHT_KEYS = (
    ("RESTOCK", "Mikstury", "🧪"), ("REFINE", "Kowal", "🔨"),
    ("SKILL", "Księgi umiejętności", "📖"), ("HORSE", "Koń", "🐎"),
    ("BIOLOG", "Biolog", "🧬"), ("METIN", "Metiny", "🗿"),
    ("PARTY", "Grupy", "👥"), ("HUNTING", "Misje polowania", "🏹"),
    ("LEVEL", "Bicie potworów", "⚔️"), ("FISHING", "Wędkowanie", "🎣"),
    ("TRADE", "Stragany", "🏪"),
)
AI_WEIGHT_MIN, AI_WEIGHT_MAX, AI_WEIGHT_NEUTRAL = 25, 250, 100
# These values share the live weight file with goal weights, but the core treats
# them as switches or direct settings rather than 25–250% goal weights.
AI_LIVE_DEFAULTS = {"CHAT": 1, "BOOKS": 1, "NIGHT": 1, "LIFE": 0, "WARS": 1, "TOWER": 1, "ISHOP": 1, "PERSONA": 1,
                     "SCRAP": 0, "REST": 100, "KINGDOMPVP": 0, "SCROLL_FROM": 1, "CHEST": None, "CHEST_STONE": None}
AI_SPECIAL_WEIGHT_KEYS = frozenset(AI_LIVE_DEFAULTS)
BIOLOGIST_COMPLETE_STATE = 557528158
# Tieru 1.29.10 adds the Orc Tooth task after the six classic Biologist
# missions. The database lookup below also discovers future missions as soon
# as the game has created their quest rows, while this list keeps the complete
# progress scale correct before anyone has started a new task.
BIOLOGIST_FALLBACK_MISSIONS = (
    "make_herb_lv4", "make_herb_lv7", "make_herb_lv10", "make_herb_lv15",
    "make_herb_lv20", "make_herb_lv25", "collect_quest_lv30",
)
PANEL_VERSION_FILE = Path(__file__).parent / "VERSION"
GM_JOB_OPTIONS = ((0, "Wojownik"), (1, "Ninja"), (2, "Sura"), (3, "Szaman"))
# Nadawanie/odbieranie rangi GM istniejącej postaci z jej karty -- dotąd
# szło tylko przy zakładaniu konta. Audyt vs panel Tieru (/gm na 7788).
GM_RANK_OPTIONS = (("", "Gracz (brak rangi)"), ("LOW_WIZARD", "Pomocnik"), ("GOD", "GM"),
                    ("HIGH_WIZARD", "Wyższy GM"), ("IMPLEMENTOR", "Właściciel"))
GM_RANK_SET = frozenset(rank for rank, _ in GM_RANK_OPTIONS if rank)
# Race IDs are stored in player.job.  0–3 retain the classic class/gender
# pair; IDs 4–7 are the alternate client portraits and character models.
GM_GENDER_OPTIONS = (("classic", "Klasyczna dla klasy"), ("male", "Mężczyzna"), ("female", "Kobieta"))
GM_RACE_BY_CLASS_GENDER = {
    (0, "classic"): 0, (1, "classic"): 1, (2, "classic"): 2, (3, "classic"): 3,
    (0, "male"): 0, (0, "female"): 4,
    (1, "male"): 5, (1, "female"): 1,
    (2, "male"): 2, (2, "female"): 6,
    (3, "male"): 7, (3, "female"): 3,
}
CLASS_PROFILES = {
    0: {"name": "Wojownik", "gender": "Mężczyzna", "portrait": "warrior_m.bmp"},
    4: {"name": "Wojownik", "gender": "Kobieta", "portrait": "warrior_w.bmp"},
    1: {"name": "Ninja", "gender": "Kobieta", "portrait": "assassin_w.bmp"},
    5: {"name": "Ninja", "gender": "Mężczyzna", "portrait": "assassin_m.bmp"},
    2: {"name": "Sura", "gender": "Mężczyzna", "portrait": "sura_m.bmp"},
    6: {"name": "Sura", "gender": "Kobieta", "portrait": "sura_w.bmp"},
    3: {"name": "Szaman", "gender": "Kobieta", "portrait": "shaman_w.bmp"},
    7: {"name": "Szaman", "gender": "Mężczyzna", "portrait": "shaman_m.bmp"},
}
GM_JOB_STARTS = {0: (6, 4, 3, 3, 600, 200), 1: (4, 3, 6, 3, 650, 200), 2: (5, 3, 3, 6, 650, 200), 3: (3, 5, 3, 5, 700, 200)}
GM_EMPIRE_STARTS = {1: (469300, 964200, 1), 2: (55700, 157900, 21), 3: (969600, 278400, 41)}
GM_NAME_PATTERN = r"[A-Za-z0-9\[\]]{2,24}"
EMPIRES = {1: {"name": "Shinsoo", "flag": "shinsoo.png"}, 2: {"name": "Chunjo", "flag": "chunjo.png"}, 3: {"name": "Jinno", "flag": "jinno.png"}}
try:
    PANEL_VERSION = os.environ.get("SEBAN_PANEL_VERSION") or PANEL_VERSION_FILE.read_text(encoding="utf-8").strip()
except OSError:
    PANEL_VERSION = os.environ.get("SEBAN_PANEL_VERSION", "dev")
DEFAULT_SETTINGS = {
    "panel_name": "Metin2 Singleplayer", "stuck_minutes": "5", "theme": "empire", "monitor_mode": "vps", "cursor": "custom",
    # Existing installations without this key stay usable. Fresh installations
    # receive setup_complete=0 from the collector and enter the setup wizard.
    "setup_complete": "1", "auth_enabled": "0", "auth_password_hash": "", "allow_student_chest": "0", "allow_moonlight_chest": "0", "keep_demo_characters": "0", "update_seban_panel": "0",
}
try:
    ITEM_DEFS = json.loads((Path(__file__).parent / "static" / "item_defs.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    ITEM_DEFS = {}
# EPlayerBotPersonality (playerbot_types.h): MERCHANT to 5, WANDERER 6.
# Ta tabela miala 5 jako wedrowca i konczyla sie na nim, wiec straganiarz
# czytal sie jako wedrowiec, a piec dopisanych od tamtej pory osobowosci
# nie czytalo sie wcale.
BOT_PERSONALITIES = {0: "Wytrwały poszukiwacz", 1: "Pogromca Metinów", 2: "Towarzysz drużyny", 3: "Mistrz ekwipunku", 4: "Rozważny zbieracz", 5: "Handlarz", 6: "Wędrowiec", 7: "Dropek Metinów", 8: "Dropek z M3", 9: "Dropek z M2", 10: "Dropek medali"}
# One colour per personality, for /players/personalities -- purely cosmetic,
# picked for contrast against the dark theme and against each other.
BOT_PERSONALITY_COLORS = {0: "#69a6ff", 1: "#ff6b6b", 2: "#79e3af", 3: "#f2c34d", 4: "#c084fc",
                           5: "#4dd0e1", 6: "#ffa94d", 7: "#ff8fa3", 8: "#a3e635", 9: "#38bdf8", 10: "#fbbf24"}
BOT_AMBITIONS = {0: "Poziom", 1: "Ekwipunek", 2: "Metiny", 3: "Koń", 4: "Biolog", 5: "Umiejętności", 6: "Handel"}
BOT_GOALS = {0: "Zdobywanie poziomu", 1: "Przetrwanie", 2: "Wybór profesji", 3: "Zdobycie ekwipunku", 4: "Uzupełnienie zapasów", 5: "Ulepszanie EQ", 6: "Rozwój umiejętności", 7: "Polowanie na Metiny", 8: "Silne cele w PT", 9: "Misja Biologa", 10: "Misja Polowania", 11: "Rozwój konia"}
# 18 (Kopie rudę) byla dopisana do playerbot_types.h u Tieru, ale nie tutaj -
# boty kopiące rudę pokazywały gołe "#18" zamiast etykiety (audyt vs panel
# Tieru na 7788, 2026-09-14).
BOT_ACTIONS = {0: "Planuje następny ruch", 1: "Podróżuje", 2: "Walczy", 3: "Podnosi łup", 4: "Regeneruje się", 5: "Wybiera profesję", 6: "Handluje", 7: "Ulepsza EQ", 8: "Czyta KU", 9: "Wkłada KD", 10: "Organizuje PT", 11: "Robi Biologa", 12: "Odwiedza Stajennego", 13: "Prowadzi stragan", 14: "Łowi ryby", 15: "Przegląda stragany", 16: "Wabi potwory", 17: "Odpoczywa w mieście", 18: "Kopie rudę"}
# Akcje, w których bot stoi w miejscu z własnej woli: stragan, wędka, przegląd
# straganów, lada NPC, kowal, trener, odpoczynek, kopanie rudy. Bez tego każdy
# straganiarz był "Możliwie zawieszony" - a flaga z tekstu statusu łapała
# tylko wędkarzy.
STATIONARY_ACTIONS = {5, 6, 7, 13, 14, 15, 17, 18}
# "System osobowości v2.0" Iwakury (playerbot_persona.h/playerbot_persona_rules.h),
# doszedł do silnika po podstawowych "osobowościach" (BOT_PERSONALITIES powyżej)
# -- włączany/wyłączany globalnie przełącznikiem PERSONA w wagach AI. Pod
# kątem statusu bota to zupełnie osobna, dodatkowa etykieta (perona) plus
# nastrój (mood) i ewentualna blokada nastroju (mood_lock). 255 w pliku
# statusu = "PERSONA wyłączone", nie osobny typ. Audyt vs panel Tieru
# (admin_panel.py, 7788), 2026-09-21.
PLAYERBOT_PERSONA_NONE = 255
BOT_PERSONAS = {0: "Grinder", 1: "Zdobywca", 2: "Handlarz", 3: "Hazardzista", 4: "Perfekcjonista",
                5: "Pogromca metinów", 6: "Górnik", 7: "Rybak", 8: "Najemnik", 9: "Towarzysz"}
BOT_MOODS = {0: "Słaby", 1: "Normalny", 2: "Bardzo dobry"}
BOT_MOOD_LOCKS = {1: "euforia po ulepszeniu", 2: "kapitulacja (Anty-PK)"}
ITEM_TYPE_NAMES = (
    "ITEM_NONE", "ITEM_WEAPON", "ITEM_ARMOR", "ITEM_USE", "ITEM_AUTOUSE", "ITEM_MATERIAL", "ITEM_SPECIAL", "ITEM_TOOL", "ITEM_LOTTERY", "ITEM_ELK",
    "ITEM_METIN", "ITEM_CONTAINER", "ITEM_FISH", "ITEM_ROD", "ITEM_RESOURCE", "ITEM_CAMPFIRE", "ITEM_UNIQUE", "ITEM_SKILLBOOK", "ITEM_QUEST", "ITEM_POLYMORPH",
    "ITEM_TREASURE_BOX", "ITEM_TREASURE_KEY", "ITEM_SKILLFORGET", "ITEM_GIFTBOX", "ITEM_PICK", "ITEM_HAIR", "ITEM_TOTEM", "ITEM_BLEND", "ITEM_COSTUME", "ITEM_DS",
    "ITEM_SPECIAL_DS", "ITEM_EXTRACT", "ITEM_SECONDARY_COIN", "ITEM_RING", "ITEM_BELT", "ITEM_PET", "ITEM_MEDIUM", "ITEM_GACHA", "ITEM_SOUL", "ITEM_PASSIVE",
)
# Renumbered 2026-09-15: was consistently off by one or more across several
# 6-8 entry runs (18..23 "Silny przeciw", 30..39 "Odporność na", ...),
# reported as swapped bonus text on real equipped items ([GA]Seban's
# Kolczyki Z Niebiań.Łez+9 showing "Odporność na dzwony/miecze" and "Silny
# przeciw mistykom" for what the in-game tooltip calls wachlarze/broń
# dwuręczną/Nieumarłym). Re-keyed against Tieru's own APPLY_META table
# (admin_panel.py, 7788) entry by entry -- POINT_TO_APPLY below already
# matched Tieru's exactly, so only the label side was wrong. Gaps at
# 51/57/77/83 are Tieru's too (no player-visible text for those points).
APPLY_LABELS = {
    1: ("Maks. PŻ", ""), 2: ("Maks. PM", ""), 3: ("Witalność", ""), 4: ("Inteligencja", ""), 5: ("Siła", ""), 6: ("Zręczność", ""), 7: ("Szybkość ataku", "%"), 8: ("Szybkość ruchu", "%"), 9: ("Szybkość zaklęcia", "%"), 10: ("Regeneracja PŻ", "%"), 11: ("Regeneracja PM", "%"), 12: ("Szansa na otrucie", "%"), 13: ("Szansa na omdlenie", "%"), 14: ("Szansa na spowolnienie", "%"), 15: ("Szansa na cios krytyczny", "%"), 16: ("Szansa na przeszywający", "%"), 17: ("Silny przeciw ludziom", "%"), 18: ("Silny przeciw zwierzętom", "%"), 19: ("Silny przeciw orkom", "%"), 20: ("Silny przeciw mistykom", "%"), 21: ("Silny przeciw nieumarłym", "%"), 22: ("Silny przeciw diabłom", "%"), 23: ("Kradzież PŻ", "%"), 24: ("Kradzież PM", "%"), 25: ("Szansa na kradzież PM", "%"), 26: ("Odzyskanie PM po obrażeniach", "%"), 27: ("Szansa na blok", "%"), 28: ("Szansa na unik strzał", "%"), 29: ("Odporność na miecze", "%"), 30: ("Odporność na broń dwuręczną", "%"), 31: ("Odporność na sztylety", "%"), 32: ("Odporność na dzwony", "%"), 33: ("Odporność na wachlarze", "%"), 34: ("Odporność na strzały", "%"), 35: ("Odporność na ogień", "%"), 36: ("Odporność na błyskawice", "%"), 37: ("Odporność na magię", "%"), 38: ("Odporność na wiatr", "%"), 39: ("Odbicie obrażeń fizycznych", "%"), 40: ("Odbicie klątwy", "%"), 41: ("Odporność na trucizny", "%"), 42: ("Odzyskanie PM po zabiciu", "%"), 43: ("Bonus doświadczenia", "%"), 44: ("Bonus Yang", "%"), 45: ("Bonus dropu przedmiotów", "%"), 46: ("Bonus mikstur", "%"), 47: ("Odzyskanie PŻ po zabiciu", "%"), 48: ("Odporność na omdlenie", ""), 49: ("Odporność na spowolnienie", ""), 50: ("Odporność na przewrócenie", ""), 52: ("Zasięg łuku", "m"), 53: ("Wartość ataku", ""), 54: ("Wartość obrony", ""), 55: ("Wartość magicznego ataku", ""), 56: ("Magiczna wartość obrony", ""), 58: ("Maks. wytrzymałość", ""), 59: ("Silny przeciw wojownikom", "%"), 60: ("Silny przeciw ninja", "%"), 61: ("Silny przeciw surom", "%"), 62: ("Silny przeciw szamanom", "%"), 63: ("Silny przeciw potworom", "%"), 64: ("Wartość ataku", "%"), 65: ("Wartość obrony", "%"), 66: ("Bonus doświadczenia", "%"), 67: ("Szansa na zdobycie przedmiotów", ""), 68: ("Szansa na zdobycie Yang", ""), 69: ("Maks. PŻ", "%"), 70: ("Maks. PM", "%"), 71: ("Obrażenia umiejętności", "%"), 72: ("Średnie obrażenia", "%"), 73: ("Odporność na obrażenia umiejętności", "%"), 74: ("Odporność na średnie obrażenia", "%"), 75: ("Bonus doświadczenia (iCafe)", "%"), 76: ("Bonus dropu przedmiotów (iCafe)", "%"), 78: ("Odporność na wojowników", "%"), 79: ("Odporność na ninja", "%"), 80: ("Odporność na sury", "%"), 81: ("Odporność na szamanów", "%"), 82: ("Energia", ""), 84: ("Bonus kostiumu", "%"), 85: ("Magiczny atak", "%"), 86: ("Magiczny/fizyczny atak", "%"), 87: ("Odporność na lód", "%"), 88: ("Odporność na ziemię", "%"), 89: ("Odporność na mrok", "%"), 90: ("Odporność na cios krytyczny", "%"), 91: ("Odporność na przeszywający", "%"), 1138: ("Terror", "%"), 1139: ("Regeneracja wytrzymałości", "%"), 1140: ("Atak sztyletem przeciw potworom", ""), 1141: ("Wartość ataku przeciw potworom", ""), 1142: ("Odporność na potwory", "‰"), 1143: ("Pochłanianie obrażeń", "%"), 1144: ("Pochłanianie obrażeń od potworów", "%"), 1145: ("Przełamanie odporności na ogłuszenie", ""), 1146: ("Przełamanie klątwy świątyni", ""), 1147: ("Czas trwania umiejętności", "%"), 1148: ("Silny przeciw potworom z Doliny Orków", "%"), 1149: ("Silny przeciw Metinom", "%"), 1150: ("Silny przeciw bossom", "%"), 1151: ("Magiczny atak przeciw potworom", "%"), 1152: ("Przełamanie odporności na miecz", "%"), 1153: ("Przełamanie odporności na broń dwuręczną", "%"), 1154: ("Przełamanie odporności na sztylet", "%"), 1155: ("Przełamanie odporności na dzwonek", "%"), 1156: ("Przełamanie odporności na wachlarz", "%"), 1157: ("Przełamanie odporności na łuk", "%"), 1158: ("Szansa na zbieranie", "%"), 1159: ("Szansa na naukę", "%"), 1160: ("Odporność na ludzi", "%"), 1161: ("Magiczny atak", ""), 1162: ("Szansa na podpalenie", "%"), 1163: ("Zamiana obrażeń na PE", "%"), 1164: ("Szansa na rzadki łup", "%"), 1165: ("Magiczna wartość ataku przeciw potworom", ""), 1166: ("Szansa na unieruchomienie", "%"), 1167: ("Atak specjalny", ""), 1168: ("Kara za śmierć", "%")}
# 71 i 72 są w tablicy powyżej, we właściwej kolejności: common/length.h
# niesie numery we własnych komentarzach - APPLY_SKILL_DAMAGE_BONUS to 71,
# APPLY_NORMAL_HIT_DAMAGE_BONUS to 72. Stała tu wcześniej poprawka
# nadpisująca błędną tablicę i tłumacząca ją tym, że "w tej kompilacji pola
# są odwrotne" - nic ich nie odwraca. Uzasadnienie było nieprawdziwe, a samo
# nadpisanie sięgało tylko opisów przedmiotów, więc ranking - który bierze
# dane z osobnego zapytania - pokazywał je zamienione jeszcze długo potem.
# Which engine the panel looks at (PLAYERBOTS_ENGINE). mt2009 keeps an
# item's bonus lines as POINT_* numbers: the two damage lines are 121 and
# 122 there, every attrtype goes through POINT_TO_APPLY before APPLY_LABELS,
# account.account has no empire column and player.player no bank_value.
PANEL_ENGINE = os.environ.get("PLAYERBOTS_ENGINE", "r40250").strip().lower()
ENGINE_MT2009 = PANEL_ENGINE == "mt2009"
# Four /manage controls (target bot count, per-map respawn, student chest
# toggle, +9 refine announcements) read/write quest and wiring files this
# panel's own patch_*.py scripts (or, for +9 announcements, a hand-added
# NOTICE command in web_admin.quest) add to the managed tree -- a
# fresh/public install of this panel does not have them, so those controls
# would silently do nothing there: e.g. a queued NOTICE command would sit
# as "pending" forever with nothing compiled in to pick it up.
# Off by default (public release); this VPS's own .env turns it on since
# the patches are actually applied here. First three flagged by Tieru
# testing the exported zip on a clean install, 2026-09-15; +9 announcements
# added same day and gated the same way from the start.
CUSTOM_PATCHES_ENABLED = os.environ.get("M2_PANEL_CUSTOM_PATCHES", "0").strip().lower() in ("1", "true", "yes", "on")
ATTR_SKILL_DAMAGE = 121 if ENGINE_MT2009 else 71
ATTR_AVG_DAMAGE = 122 if ENGINE_MT2009 else 72
POINT_TO_APPLY = {6: 1, 8: 2, 13: 3, 15: 4, 12: 5, 14: 6, 17: 7, 19: 8, 21: 9, 32: 10, 33: 11,
 37: 12, 38: 13, 39: 14, 40: 15, 41: 16, 43: 17, 44: 18, 45: 19, 46: 20, 47: 21,
 48: 22, 63: 23, 64: 24, 65: 25, 66: 26, 67: 27, 68: 28, 69: 29, 70: 30, 71: 31,
 72: 32, 73: 33, 74: 34, 75: 35, 76: 36, 77: 37, 78: 38, 79: 39, 81: 41, 82: 42,
 83: 43, 84: 44, 85: 45, 86: 46, 87: 47, 88: 48, 89: 49, 90: 50, 28: 51, 34: 52,
 # 93/94 (POINT_ATT_BONUS/POINT_DEF_BONUS, server/common/length.h) were
 # missing here entirely -- fell through unmapped and showed as the raw,
 # untranslated "Bonus #93"/"Bonus #94". Sit right between the already-
 # mapped GRADE_BONUS pair (95/96 -> flat 53/54) in the engine's own enum,
 # same naming split elsewhere in this table between a flat and a percent
 # variant of the same stat -- mapped to the percent pair (64/65) on that
 # basis. Reported (Buty Z Brązu+0 showing "Bonus #94 +1"), [GA]Seban, 2026-09-22.
 93: 64, 94: 65,
 95: 53, 96: 54, 22: 55, 23: 56, 42: 57, 10: 58, 54: 59, 55: 60, 56: 61, 57: 62,
 53: 63, 114: 64, 115: 65, 116: 66, 117: 67, 118: 68, 119: 69, 120: 70, 121: 71,
 122: 72, 123: 73, 124: 74, 125: 75, 126: 76, 59: 78, 60: 79, 61: 80, 62: 81,
 128: 82, 16: 83, 130: 84, 131: 85, 132: 86, 133: 87, 134: 88, 135: 89, 136: 90,
 137: 91,
 # mt2009 points with no APPLY id at all (length.h 138..168 - the engine
 # applies them straight from the item). A pseudo key of 1000 + point, so
 # the label tables can name them; without it the panel wrote "Bonus #139".
 138: 1138, 139: 1139, 140: 1140, 141: 1141, 142: 1142, 143: 1143, 144: 1144, 145: 1145, 146: 1146, 147: 1147, 148: 1148, 149: 1149, 150: 1150, 151: 1151, 152: 1152, 153: 1153, 154: 1154, 155: 1155, 156: 1156, 157: 1157, 158: 1158, 159: 1159, 160: 1160, 161: 1161, 162: 1162, 163: 1163, 164: 1164, 165: 1165, 166: 1166, 167: 1167, 168: 1168}
# The kingdom of a character: the index, then (r40250 only) the account.
EMPIRE_EXPR = "COALESCE(NULLIF(pi.empire,0),0)" if ENGINE_MT2009 else "COALESCE(NULLIF(pi.empire,0),a.empire,0)"

JOB_NAMES = ("Wojownik", "Ninja", "Sura", "Szaman")
SKILLS = {
    # Exact vnum/name pairs from Tieru's current panel. The old mapping put
    # display names next to the wrong VNUMs, hence correct icons looked wrong.
    (0, 1): ((1, "Trzystronne Cięcie"), (2, "Wir Miecza"), (3, "Berserk"), (4, "Aura Miecza"), (5, "Szarża")),
    (0, 2): ((16, "Duchowe Uderzenie"), (17, "Tąpnięcie"), (18, "Uderzenie Miecza"), (19, "Silne Ciało"), (20, "Walnięcie")),
    (1, 1): ((31, "Zasadzka"), (32, "Szybki Atak"), (33, "Wirujący Sztylet"), (34, "Krycie się"), (35, "Trująca Chmura")),
    (1, 2): ((46, "Powtarzalny Strzał"), (47, "Deszcz Strzał"), (48, "Ognista Strzała"), (49, "Bezszelestny Chód"), (50, "Trująca Strzała")),
    (2, 1): ((61, "Uderzenie Palcem"), (62, "Smoczy Wir"), (63, "Czarowane Ostrze"), (64, "Strach"), (65, "Czarowana Zbroja"), (66, "Rozproszenie Magii")),
    (2, 2): ((76, "Mroczne Uderzenie"), (77, "Ogniste Uderzenie"), (78, "Ognisty Duch"), (79, "Mroczna Ochrona"), (80, "Duchowy Cios"), (81, "Mroczna Sfera")),
    (3, 1): ((91, "Latający Talizman"), (92, "Strzelający Smok"), (93, "Smoczy Skowyt"), (94, "Błogosławieństwo"), (95, "Odbicie"), (96, "Pomoc Smoka")),
    (3, 2): ((106, "Błyskawiczny Rzut"), (107, "Przywołanie Błyskawicy"), (108, "Burzowy Szpon"), (109, "Leczenie"), (110, "Zwinność"), (111, "Zwiększenie Ataku")),
}
try:
    ITEM_ICONS = json.loads((Path(__file__).parent / "static" / "item_icons.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    ITEM_ICONS = {}
try:
    EXP_LEVELS = json.loads((Path(__file__).parent / "static" / "exp_levels.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    EXP_LEVELS = [0]
try:
    GM_COMMANDS = (Path(__file__).parent / "gm_commands.txt").read_text(encoding="utf-8", errors="replace")
except OSError:
    GM_COMMANDS = "Brak pliku z komendami."


# MyISAM nie przezywa nieczystego zatrzymania, a ten panel czyta na stronie
# glownej najruchliwsza tabele w calym swiecie - log.log, dla rankingu wedkarzy.
# Gdy jest uszkodzona, kazde zapytanie do niej rzuca wyjatkiem, Flask pokazuje
# wlasne "Internal Server Error", i to zrzut ekranu tej strony trafia na
# Discorda - bez nazwy tabeli, bez przyczyny, bez niczego do zrobienia
# (archonek, 10 wrzesnia: "klikam i blad wyskakuje"; zwykly panel dzialal, bo
# jego strona glowna do log.log nie zaglada). Aktualizacja tego nie naprawia:
# uszkodzenie siedzi w danych na wolumenie, nie w obrazie.
#
# Numery bledow: 1194 "is marked as crashed and should be repaired",
# 1195 i 144 "last repair failed", 145 to samo dla starszych serwerow.
CRASHED_TABLE_ERRNOS = (144, 145, 1194, 1195)


@app.errorhandler(pymysql.err.OperationalError)
def handle_crashed_table(error):
    errno = error.args[0] if error.args else 0
    message = str(error.args[1]) if len(error.args) > 1 else str(error)
    if errno not in CRASHED_TABLE_ERRNOS:
        # Nie nasza sprawa - niech Flask pokaze swoje 500 i zapisze slad.
        raise error
    table = ""
    match = re.search(r"Table '([^']+)'", message)
    if match:
        table = match.group(1).replace("./", "").replace("/", ".")
    named = ("Tabela <code>%s</code>" % escape(table)) if table else "Jedna z tabel bazy"
    body = """<!doctype html><html lang="pl"><head><meta charset="utf-8">
<title>Uszkodzona tabela bazy</title>
<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:52em;margin:3em auto;padding:0 1.5em;line-height:1.6;color:#222}
h1{font-size:1.5em}code{background:#f2f2f2;padding:.15em .35em;border-radius:3px}
pre{background:#f2f2f2;padding:1em;border-radius:5px;overflow-x:auto}
.note{background:#fff8e1;border-left:4px solid #e0a800;padding:.8em 1em;margin:1.5em 0}</style>
</head><body>
<h1>Uszkodzona tabela bazy danych</h1>
<p>%s jest oznaczona jako uszkodzona, wiec panel nie moze jej odczytac.
Silnik gry uzywa tabel MyISAM, a te nie przezywaja nagłego zatrzymania -
wystarczy zamkniecie Dockera w trakcie zapisu albo zanik zasilania.</p>
<div class="note"><strong>Aktualizacja serwera tego nie naprawi.</strong>
Uszkodzenie jest w danych na dysku, a nie w programie - nowa wersja czyta te
same pliki.</div>
<h2>Jak naprawic</h2>
<p>Otworz PowerShell w folderze serwera, w podkatalogu <code>linux-port\\docker</code>
(w launcherze przycisk FOLDER SERWERA), i uruchom:</p>
<pre>docker compose exec mariadb mysqlcheck -uroot -p --auto-repair --databases log player account common</pre>
<p>Zapyta o haslo - to <code>M2_DB_ROOT_PASSWORD</code> z pliku <code>.env</code>
w tym samym folderze. Naprawa duzej tabeli logow potrafi potrwac kilka minut.</p>
<h2>Jesli naprawa sie nie uda</h2>
<p>Baza <code>log</code> to wylacznie historia: co kto podniosl, ulepszyl i
powiedzial. Gra jej nie czyta i zadna postac, przedmiot ani bot od niej nie
zaleza. Jesli <code>mysqlcheck</code> zglosi, ze nie da rady, mozna te tabele
oproznic bez straty dla swiata:</p>
<pre>docker compose exec mariadb mariadb -uroot -p -e "TRUNCATE log.log; TRUNCATE log.levellog; TRUNCATE log.shout_log;"</pre>
<div class="note">Nie rob tego dla baz <code>player</code>, <code>account</code>
ani <code>common</code> - tam sa postacie, konta i boty.</div>
<p style="margin-top:2em;color:#666;font-size:.9em">Blad bazy: %s (%s)</p>
</body></html>""" % (named, errno, escape(message))
    return body, 500



def db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "mariadb"), port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=True,
    )


def rows(sql, params=()):
    with db() as con:
        with con.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def one(sql, params=()):
    result = rows(sql, params)
    return result[0] if result else {}


def read_regen_settings():
    """Read MT2009's persistent global respawn flags (100 means defaults)."""
    result = {"delay": {kind: 100 for kind in REGEN_DELAY_FLAGS},
              "count": {kind: 100 for kind in REGEN_COUNT_FLAGS}}
    try:
        with db() as con, con.cursor() as cur:
            for kind, flag in REGEN_DELAY_FLAGS.items():
                cur.execute("SELECT lValue FROM player.quest WHERE dwPID=0 AND szName=%s LIMIT 1", (flag,))
                row = cur.fetchone()
                if row and REGEN_DELAY_MIN <= int(row["lValue"]) < 100:
                    result["delay"][kind] = int(row["lValue"])
            for kind, flag in REGEN_COUNT_FLAGS.items():
                cur.execute("SELECT lValue FROM player.quest WHERE dwPID=0 AND szName=%s LIMIT 1", (flag,))
                row = cur.fetchone()
                if row and 100 < int(row["lValue"]) <= max(REGEN_COUNT_CHOICES):
                    result["count"][kind] = int(row["lValue"])
    except (KeyError, TypeError, ValueError, pymysql.MySQLError):
        pass
    return result


def persist_regen_settings(kind, values):
    flags = REGEN_DELAY_FLAGS if kind == "delay" else REGEN_COUNT_FLAGS
    with db() as con, con.cursor() as cur:
        for target, flag in flags.items():
            value = int(values[target])
            stored = 0 if (kind == "delay" and value >= 100) or (kind == "count" and value <= 100) else value
            cur.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', %s)",
                        (flag, stored))


def queue_game_admin_command(command, arg1, wait=12.0):
    """Use the same queue processed by MT2009's web_admin.quest."""
    with db() as con, con.cursor() as cur:
        cur.execute("INSERT INTO player.web_admin_queue (player_name, cmd, arg1, arg2) VALUES ('', %s, %s, '')",
                    (command, str(arg1)))
        queue_id = cur.lastrowid
    deadline = time.time() + wait
    while time.time() < deadline:
        time.sleep(0.5)
        result = one("SELECT status FROM player.web_admin_queue WHERE id=%s", (queue_id,))
        status = result.get("status")
        if not result:
            return "gone", queue_id
        if status in QUEUE_FINAL_STATUSES:
            return status, queue_id
    return "timeout", queue_id


def cancel_pending_admin_command(queue_id):
    try:
        rows("UPDATE player.web_admin_queue SET status='cancelled' WHERE id=%s AND status='pending'", (queue_id,))
    except pymysql.MySQLError:
        pass


def _ensure_collector_tables():
    """Same schema collector.py's own init() creates, run here too at
    startup. Without this, a panel that comes up before the collector's
    first successful cycle (e.g. right after `docker compose up`, before
    MariaDB finishes its own startup) 500s on every web_seban_* table --
    and if that first collector attempt fails, it does not retry until its
    full interval (default 300s) has passed, not right away. Reported by
    players as the panel "Internal Server Error"-ing for the first ~5
    minutes after an update (sizowski, 2026-09-14)."""
    try:
        import collector
        with db() as con, con.cursor() as cur:
            collector.init(cur)
    except pymysql.MySQLError as exc:
        app.logger.warning("could not pre-create collector tables at startup: %s", exc)


_ensure_collector_tables()


def game_text(value):
    if isinstance(value, bytes):
        for encoding in ("cp1250", "utf-8", "latin1"):
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                pass
        return value.decode("cp1250", "replace")
    return value or ""


def cp1250_hex_text(value):
    """Decode a Polish item name without trusting the log table's charset."""
    try:
        return bytes.fromhex(str(value or "")).decode("cp1250")
    except (TypeError, ValueError, UnicodeDecodeError):
        return ""


def map_name(index):
    """Name only maps which this Playerbots world actually runs."""
    index = int(index or 0)
    return MAP_NAMES.get(index, f"Poza aktywnym światem (mapa #{index})")


def changelog_entries():
    """Read version notes from the repository file for the public in-panel log."""
    path = Path(__file__).parent / "CHANGELOG.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    entries, current = [], None
    via_pattern = re.compile(r"^!\[via ([A-Za-z0-9 ]+)\]")
    for line in lines:
        if line.startswith("## "):
            if current:
                entries.append(current)
            heading = line[3:].strip()
            timestamp, separator, version = heading.partition(" · ")
            current = {"timestamp": timestamp if separator else "Wcześniejsza wersja", "version": version if separator else heading, "changes": [], "via": None, "via_agent": None, "via_author": None}
        elif current and line.startswith("- "):
            current["changes"].append(line[2:].strip())
        elif current:
            # Attribution badge line at the bottom of an entry, e.g.
            # "![via Claude by Seban](https://img.shields.io/badge/via-...)"
            # -- shows as an actual badge on GitHub, and as a small local
            # chip here (no outbound request from the panel itself, see
            # CSS .changelog-via/.via-claude/.via-codex/.via-tieru). Split on
            # " by " so "Seban" gets its own rainbow/star treatment in the
            # template -- a plain "Tieru" entry (his own code, merged in
            # directly, not AI-assisted) has no author half at all.
            match = via_pattern.match(line.strip())
            if match:
                via_agent, _, via_author = match.group(1).strip().partition(" by ")
                current["via"] = match.group(1).strip()
                current["via_agent"] = via_agent.strip()
                current["via_author"] = via_author.strip() or None
    if current:
        entries.append(current)
    return entries


def settings():
    values = dict(DEFAULT_SETTINGS)
    try:
        for row in rows("SELECT name,value FROM player.web_seban_settings"):
            if row["name"] in values:
                values[row["name"]] = str(row["value"])
    except pymysql.MySQLError:
        pass
    return values


def write_settings(values):
    """Persist panel-only configuration without relying on environment secrets."""
    with db() as con:
        with con.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_settings (
              name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(255) NOT NULL,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
            cur.executemany(
                "INSERT INTO player.web_seban_settings (name,value) VALUES (%s,%s) ON DUPLICATE KEY UPDATE value=VALUES(value)",
                tuple(values.items()),
            )


def validate_display_settings(form):
    name = form.get("panel_name", "").strip()[:48]
    try:
        stuck = max(1, min(120, int(form.get("stuck_minutes", "5"))))
    except (TypeError, ValueError):
        stuck = 5
    theme, monitor_mode = form.get("theme", "empire"), form.get("monitor_mode", "vps")
    cursor_choice = form.get("cursor", "custom")
    if not name:
        return None, "Nazwa panelu nie może być pusta."
    if theme not in ("ocean", "ember", "forest", "empire") or monitor_mode not in ("vps", "docker"):
        return None, "Nieprawidłowe ustawienia wyglądu lub monitoringu."
    if cursor_choice not in ("custom", "system"):
        return None, "Nieprawidłowy wybór kursora."
    return {"panel_name": name, "stuck_minutes": str(stuck), "theme": theme, "monitor_mode": monitor_mode, "cursor": cursor_choice}, None


def skill_rank(master_type, level):
    master_type, level = int(master_type or 0), int(level or 0)
    if master_type >= 3 or level >= 40:
        return "P"
    if master_type == 2 or level >= 30:
        return f"G{max(1, level - 29)}"
    if master_type == 1 or level >= 20:
        return f"M{max(1, level - 19)}"
    return str(level)


def skill_icon_suffix(master_type, level):
    """Select the client icon stage for normal, M, G and Perfect skills."""
    master_type, level = int(master_type or 0), int(level or 0)
    if master_type >= 3 or level >= 40:
        return "_p"
    if master_type == 2 or level >= 30:
        return "_g"
    if master_type == 1 or level >= 20:
        return "_m"
    return ""


def experience_progress(level, exp):
    level, exp = int(level or 0), max(0, int(exp or 0))
    required = int(EXP_LEVELS[min(max(level, 0), len(EXP_LEVELS) - 1)] or 0)
    return {"current": exp, "required": required, "percent": min(100, round(exp * 100 / required, 1)) if required else 100}


def honor_rank(value):
    """The core stores alignment in tenths; return the in-game value and colour."""
    points = int(float(value or 0) / 10)
    bands = (
        (12000, "Rycerski", "knightly"), (8000, "Szlachetny", "noble"),
        (4000, "Dobry", "good"), (1000, "Przyjazny", "friendly"),
        (0, "Neutralny", "neutral"), (-3999, "Agresywny", "aggressive"),
        (-7999, "Nieuczciwy", "dishonest"), (-11999, "Złośliwy", "malicious"),
        (-20000, "Okrutny", "cruel"),
    )
    for threshold, title, css in bands:
        if points >= threshold:
            return {"points": points, "title": title, "css": css}
    return {"points": points, "title": "Okrutny", "css": "cruel"}


def live_label(field, value):
    labels = {"personality": BOT_PERSONALITIES, "ambition": BOT_AMBITIONS, "goal": BOT_GOALS, "action": BOT_ACTIONS}.get(field, {})
    value = int(value or 0)
    return labels.get(value, f"#{value}")


def is_stationary_activity(status, action=None):
    try:
        if int(action or 0) in STATIONARY_ACTIONS:
            return True
    except (TypeError, ValueError):
        pass
    text = str(status or "").casefold()
    return any(marker in text for marker in ("łowi", "lowi", "ryb", "fishing", "czekam na branie"))


def apply_text(apply_type, value):
    key = int(apply_type or 0)
    if ENGINE_MT2009:
        key = POINT_TO_APPLY.get(key, key)
    name, suffix = APPLY_LABELS.get(key, (f"Bonus #{apply_type}", ""))
    value = int(value or 0)
    return f"{name} {value:+d}{suffix}"


def item_base_stats(vnum):
    """Client-side item properties displayed by the in-game tooltip.
    value1-4 alone are the item's +0 base -- refine level adds value5, once
    for a weapon's attack/magic-attack range and twice for Body/Shield (per
    Tieru's own tooltip JS, admin_panel.py 7788). Missing this made every
    refined weapon/armor show its +0 numbers: Różowa Szata+9 read 29
    defense here vs. 83 in the live client (29 + 27*2); Antyczny Dzwon+9
    read 50-70/35-60 here vs. 120-140/105-130 live (both +70). Reported by
    [GA]Seban, 2026-09-15."""
    proto = ITEM_DEFS.get(str(int(vnum or 0)), {})
    if not proto:
        return []
    stats, item_type, subtype = [], int(proto.get("type") or 0), int(proto.get("subtype") or 0)
    level = int(proto.get("level") or 0)
    if level:
        stats.append(f"Wymagany poziom: {level}")
    value = lambda index: int(proto.get(f"value{index}") or 0)
    refine_bonus = value(5)
    if item_type == 1:  # ITEM_WEAPON: magic 1/2, physical 3/4.
        attack_min, attack_max = value(3) + refine_bonus, value(4) + refine_bonus
        magic_min, magic_max = value(1) + refine_bonus, value(2) + refine_bonus
        if attack_min or attack_max:
            stats.append(f"Wartość ataku: {attack_min}–{attack_max}" if attack_min != attack_max else f"Wartość ataku: {attack_max}")
        if magic_min or magic_max:
            stats.append(f"Wartość magicznego ataku: {magic_min}–{magic_max}" if magic_min != magic_max else f"Wartość magicznego ataku: {magic_max}")
    elif item_type == 2:  # ITEM_ARMOR. Only these four subtypes show a flat
        # defense number in the client at all; jewelry (necklace/earring/
        # wrist) shows none, same as the real tooltip. Head (subtype 1) was
        # x1 here from launch -- an unverified guess, unlike body/shield
        # which had a real reported example backing x2 (see docstring).
        # Every helmet's displayed defense was wrong as a result; fixed to
        # x2 to match body/shield once actually reported. [GA]Seban, 2026-09-22.
        multiplier = {0: 2, 1: 2, 2: 2, 4: 1}.get(subtype)
        if multiplier:
            defense = value(1) + refine_bonus * multiplier
            if defense:
                stats.append(f"Wartość obrony: {defense}")
    return stats


# ITEM_ROD (13). Ground truth: quest/libs/fishing/fishing.lua --
# FISHING_ROD_SOCKET_CURRENT_POINTS=0 (current progress lives on the live
# item's own socket0, not item_proto -- this is also exactly the column the
# stone-lookup bug above was misreading as a gem vnum), level is not stored
# anywhere at all but derived straight from the vnum itself
# (get_rod_level(): (vnum-27400)/10 -- every refine level is its own +10
# vnum, which is also why it happens to equal the "+N" in the item's own
# name), and value0/value2/value5 are FISHING_ROD_VALUE_BONUS/_NEEDED_POINTS/
# _BONUS_FISH_CHANCE from the same file's constant list. value0 reads 20 on
# a rod whose real client tooltip (reported by [GA]Seban, 2026-09-22) showed
# "+2" for that same line -- panel_bonus divides by 10 to match.
def fishing_rod_stats(vnum, current_points):
    vnum = int(vnum or 0)
    proto = ITEM_DEFS.get(str(vnum), {})
    if int(proto.get("type") or 0) != 13:
        return []
    stats = [f"Poziom: {max(0, (vnum - 27400) // 10)}"]
    needed = int(proto.get("value2") or 0)
    if needed:
        stats.append(f"Punkty {int(current_points or 0)} / {needed}")
    pool_bonus = int(proto.get("value0") or 0) // 10
    if pool_bonus:
        stats.append(f"Bonus puli rybołówstwa +{pool_bonus}")
    catch_chance = int(proto.get("value5") or 0)
    if catch_chance:
        stats.append(f"Szansa na pomyślne wyłowienie +{catch_chance}%")
    return stats


def empire_info(empire):
    try:
        return EMPIRES.get(int(empire), {"name": "—", "flag": ""})
    except (TypeError, ValueError):
        return {"name": "—", "flag": ""}


def empire_flag_path(empire):
    return empire_info(empire)["flag"]

def class_profile(job):
    try:
        return CLASS_PROFILES.get(int(job), CLASS_PROFILES[0])
    except (TypeError, ValueError):
        return CLASS_PROFILES[0]


def parse_skills(raw, job, group):
    if isinstance(raw, memoryview): raw = raw.tobytes()
    if isinstance(raw, str): raw = raw.encode("latin1", "ignore")
    raw = raw or b""
    result = []
    for vnum, name in SKILLS.get((int(job or 0) % 4, int(group or 0)), ()):
        offset = vnum * 6
        master, level = (raw[offset] if offset < len(raw) else 0), (raw[offset + 1] if offset + 1 < len(raw) else 0)
        rank = skill_rank(master, level)
        if level:
            result.append({"vnum": vnum, "name": name, "level": level, "master_type": master, "rank": rank,
                           "icon_suffix": skill_icon_suffix(master, level)})
    return result


# The client stores support skills alongside class skills. Tieru's panel does
# not ship their artwork, which made this section fall back to text only.
PASSIVE_SKILLS = {
    121: "Dowodzenie", 122: "Combo", 123: "Wędkarstwo", 124: "Górnictwo", 125: "Kowalstwo",
    126: "Język Shinsoo", 127: "Język Chunjo", 128: "Język Jinno", 129: "Polimorfia",
    130: "Poziom konia", 131: "Przywołanie konia",
}


def parse_passive_skills(raw):
    if isinstance(raw, memoryview): raw = raw.tobytes()
    if isinstance(raw, str): raw = raw.encode("latin1", "ignore")
    raw = raw or b""
    result = []
    for vnum, name in PASSIVE_SKILLS.items():
        offset = vnum * 6
        master, level = (raw[offset] if offset < len(raw) else 0), (raw[offset + 1] if offset + 1 < len(raw) else 0)
        if level:
            # Horse riding and calling a horse use their own 1–30 numeric
            # progression in the client. They are not M/G/P skills even when
            # their value crosses 20, 30 or 40.
            horse_skill = vnum in (130, 131)
            result.append({"vnum": vnum, "name": name, "level": level, "master_type": master,
                           "rank": str(level) if horse_skill else skill_rank(master, level),
                           "icon_suffix": "" if horse_skill else skill_icon_suffix(master, level)})
    return result


SKILL_NAMES = {vnum: name for skill_set in SKILLS.values() for vnum, name in skill_set}
# Every ordinary Skill Book is vnum 50300 no matter which skill it teaches --
# the skill itself only lives in socket0 (the "Instr." vnums from 50401 up
# already carry their skill in locale_name and never need this). Kept as a
# set, not a bare constant, in case another generic-book vnum shows up later.
SKILLBOOK_VNUMS = {50300}


def resolve_item_display_name(vnum, socket0, base_name):
    """base_name with the real skill substituted in for a generic Skill Book.
    Takes vnum/socket0 as plain values, not an item row, so it can be called
    from a GROUP BY (vnum, socket0) aggregate later too (see economy()/
    economy_shops(), which today count every Skill Book as one vnum) -- not
    only from a single player's item row."""
    if int(vnum or 0) in SKILLBOOK_VNUMS:
        skill_name = SKILL_NAMES.get(int(socket0 or 0))
        if skill_name:
            return f"{skill_name} — Księga Umiejętności"
    return base_name


_season_cache = {"at": 0.0, "weekly": [], "records": {}}


def _news_event_source_rows(since, before=None, scan_limit=900):
    """Raw log.log candidate rows for a rare achievement (skill masteries,
    Małż finds), before classification. Refines are NOT sourced from here
    -- see _refine_event_rows()/log.refinelog, which also carries the
    upgrade method (blacksmith vs scroll) that log.log's hint never did.
    Shared by the dashboard ticker (news_feed_events) and the full history
    page (news_feed_history) so the detection rules only live in one place
    (_classify_news_events).

    Filter in SQL before the limit: a busy server produces thousands of
    ordinary events per minute, taking its newest rows first made rare
    achievements disappear from the feed altogether.
    """
    clauses, params = ["l.time >= %s"], [since]
    if before:
        clauses.append("l.time < %s")
        params.append(before)
    return rows(f"""SELECT l.time,l.how,l.hint,HEX(l.hint) AS hint_hex,l.what,l.who,p.name,p.job,
        {EMPIRE_EXPR} AS empire
      FROM log.log l JOIN player.player p ON p.id=l.who
      LEFT JOIN player.player_index pi ON pi.id=p.account_id
      LEFT JOIN account.account a ON a.id=p.account_id
      WHERE {' AND '.join(clauses)}
        AND (
          l.how='SKILLUP'
          OR (l.how='GET' AND LOWER(CONVERT(l.hint USING utf8mb4)) COLLATE utf8mb4_general_ci LIKE '%%małż%%')
        )
      ORDER BY l.time DESC LIMIT %s""", params + [scan_limit])


def _classify_news_events(raw):
    events, seen = [], set()
    for row in raw:
        # `how` is VARBINARY on mt2009 and arrives as bytes; str() of that is
        # "b'GET'" and matches nothing below.
        how, name = game_text(row.get("how")), game_text(row.get("name"))
        hint = cp1250_hex_text(row.get("hint_hex")) or game_text(row.get("hint"))
        key = f"{how}:{row.get('who')}:{row.get('what')}:{row.get('time')}"
        if key in seen or not name:
            continue
        message, kind = None, None
        if how == "SKILLUP":
            skill_match = re.search(r"SkillUp:\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)", hint)
            if skill_match:
                vnum, master, level = map(int, skill_match.groups())
                rank = skill_rank(master, level)
                if (rank.startswith("M") and rank != "M1") or rank.startswith("G") or rank == "P":
                    message, kind = f"{name} rozwinął {SKILL_NAMES.get(vnum, f'umiejętność #{vnum}')} na {rank}", "skill"
        elif how == "GET" and "małż" in hint.casefold():
            message, kind = f"{name} znalazł Małż podczas połowu", "find"
        if not message:
            continue
        seen.add(key)
        events.append({
            "key": key, "time": row["time"], "message": message, "kind": kind, "actor": name, "method": None,
            "refine_tier": 0, "player_id": int(row.get("who") or 0), "job": int(row.get("job") or 0),
            "empire": int(row.get("empire") or 0), "vnum": 0, "socket0": 0,
        })
    return events


# log.log's REFINE SUCCESS hint is just "<item name>+<level>" -- no way to
# tell a blacksmith refine from a scroll one. The engine's own refine log
# (LogManager::RefineLog, char_item.cpp) writes that distinction into
# log.refinelog.setType: "POWER" (blacksmith NPC), "GUILD" (guild forge),
# "DEVILTOWER" (the yang-only device), or "SCROLL:<vnum>" (used an item
# directly). Confirmed live 2026-09-25: this build only ever produces
# POWER and SCROLL:<vnum> so far. Operator's ask the same day: show which
# one on /world-feed.
REFINE_METHOD_LABELS = {"POWER": "u kowala", "GUILD": "w kuźni gildii", "DEVILTOWER": "Wieżą Diabła"}


def _refine_event_rows(since, before=None, scan_limit=200_000):
    """Rare (+7/+8/+9) successful upgrades from log.refinelog -- a smaller,
    purpose-built InnoDB table (280K rows vs log.log's 6.4M), so this scan
    is cheap even without a `time` index (checked live: ~150ms)."""
    clauses, params = ["r.time >= %s", "r.is_success=1", "r.step IN (7,8,9)"], [since]
    if before:
        clauses.append("r.time < %s")
        params.append(before)
    return rows(f"""SELECT r.pid,r.item_name,r.item_id,r.step,r.time,r.setType,p.name,p.job,{EMPIRE_EXPR} AS empire
      FROM log.refinelog r JOIN player.player p ON p.id=r.pid
      LEFT JOIN player.player_index pi ON pi.id=p.account_id
      LEFT JOIN account.account a ON a.id=p.account_id
      WHERE {' AND '.join(clauses)}
      ORDER BY r.time DESC LIMIT %s""", params + [scan_limit])


def _classify_refine_events(raw):
    scroll_vnums = {int(r["setType"].split(":", 1)[1]) for r in raw
                    if r.get("setType") and str(r["setType"]).startswith("SCROLL:") and str(r["setType"]).split(":", 1)[1].isdigit()}
    scroll_names = {}
    if scroll_vnums:
        marks = ",".join(["%s"] * len(scroll_vnums))
        scroll_names = {r["vnum"]: game_text(r["locale_name"]) for r in
                        rows(f"SELECT vnum,locale_name FROM player.item_proto WHERE vnum IN ({marks})", list(scroll_vnums))}
    events, seen = [], set()
    for row in raw:
        name = game_text(row.get("name"))
        item_name = game_text(row.get("item_name"))
        if not name or not item_name:
            continue
        key = f"REFINE:{row.get('pid')}:{row.get('item_id')}:{row.get('time')}"
        if key in seen:
            continue
        seen.add(key)
        set_type = str(row.get("setType") or "")
        method_vnum = 0
        if set_type in REFINE_METHOD_LABELS:
            method = REFINE_METHOD_LABELS[set_type]
        elif set_type.startswith("SCROLL:"):
            scroll_vnum = set_type.split(":", 1)[1]
            method_vnum = int(scroll_vnum) if scroll_vnum.isdigit() else 0
            scroll_name = scroll_names.get(method_vnum)
            method = f"zwojem ({scroll_name})" if scroll_name else "zwojem"
        else:
            method = "innym sposobem"
        events.append({
            "key": key, "time": row["time"], "message": f"{name} ulepszył {item_name}", "kind": "refine",
            "actor": name, "method": method, "refine_tier": int(row.get("step") or 0),
            "player_id": int(row.get("pid") or 0), "job": int(row.get("job") or 0),
            # `vnum` doubles as "which item was used to refine" here (the
            # item that was upgraded is destroyed, so there's no vnum for
            # it to show anyway) -- item_icon(vnum) in the template shows
            # the scroll/manual actually used instead of a text label
            # (operator's ask, 2026-09-26); 0 for plain blacksmith (POWER),
            # rendered with static/refine-method/kowal.png instead.
            "empire": int(row.get("empire") or 0), "vnum": method_vnum, "socket0": 0,
        })
    return events


NEWS_SYNC_INTERVAL = 300  # seconds -- see sync_news_events() docstring


def sync_news_events():
    """Keep web_seban_news_event (a small, time-indexed local cache) caught
    up with log.log, throttled to run the expensive underlying scan at most
    once per NEWS_SYNC_INTERVAL system-wide -- not once per page load.

    log.log has no index on `time` (only who/what/how): EXPLAIN on the
    achievement-detection WHERE clause showed a how_idx range scan
    examining ~1.7M rows *regardless of the time window*, taking 5-7s per
    call either way (checked live, 2026-09-25 -- both the old 12h ticker
    query and a 14-day history query cost the same). Operator's call the
    same day: no schema changes to the live game log table (MyISAM, would
    rebuild the whole 573MB table and risk blocking game writes) -- accept
    up to ~5 minutes of lag on new achievements instead, paid by whichever
    request happens to be first past the throttle window rather than by
    every single one.
    """
    try:
        con = db()
    except pymysql.MySQLError:
        return
    try:
        with con.cursor() as cur:
            now = time.time()
            cur.execute("""UPDATE player.web_seban_settings SET value=%s
              WHERE name='news_sync_last_run' AND (value IS NULL OR value='' OR CAST(value AS DECIMAL(20,3)) < %s)""",
              (str(now), now - NEWS_SYNC_INTERVAL))
            claimed = cur.rowcount == 1
            if not claimed:
                cur.execute("INSERT IGNORE INTO player.web_seban_settings (name,value) VALUES ('news_sync_last_run', %s)", (str(now),))
                claimed = cur.rowcount == 1
            if not claimed:
                return  # another request already claimed this window
            cur.execute("SELECT value FROM player.web_seban_settings WHERE name='news_scan_last_time'")
            cursor_row = cur.fetchone()
            since = cursor_row["value"] if cursor_row and cursor_row.get("value") else "2020-01-01 00:00:00"
            events = _classify_news_events(_news_event_source_rows(since=since, scan_limit=2_000_000))
            events += _classify_refine_events(_refine_event_rows(since=since))
            if events:
                cur.executemany("""INSERT IGNORE INTO player.web_seban_news_event
                  (event_key,time,kind,message,actor,player_id,job,empire,vnum,socket0,refine_tier,method)
                  VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                  [(e["key"], e["time"], e["kind"], e["message"], e["actor"], e["player_id"], e["job"],
                    e["empire"], e["vnum"], e["socket0"], e["refine_tier"], e["method"]) for e in events])
                newest = max(e["time"] for e in events)
                cur.execute("REPLACE INTO player.web_seban_settings (name,value) VALUES ('news_scan_last_time', %s)",
                            (newest.strftime("%Y-%m-%d %H:%M:%S"),))
    except pymysql.MySQLError:
        app.logger.exception("Nie można zsynchronizować feedu wydarzeń")
    finally:
        con.close()


def news_feed_events():
    """Curate rare achievements for the dashboard's live ticker -- last 12h,
    newest 30, read from the fast local cache (see sync_news_events()).
    Shape (string HH:MM `time`) matches what static/news-feed.js expects."""
    sync_news_events()
    raw = rows("""SELECT event_key,time,message,refine_tier,method FROM player.web_seban_news_event
      WHERE time >= NOW() - INTERVAL 12 HOUR ORDER BY time DESC LIMIT 30""")
    return [{"key": r["event_key"], "time": r["time"].strftime("%H:%M"),
             "message": f"{r['message']} — {r['method']}" if r.get("method") else r["message"],
             "refine_tier": r["refine_tier"]} for r in reversed(raw)]


def news_feed_day_label(when):
    today = datetime.now().date()
    day = when.date()
    if day == today:
        return "Dziś"
    if day == today - timedelta(days=1):
        return "Wczoraj"
    return day.strftime("%d.%m.%Y")


def news_feed_history(before=None, limit=40, days=14):
    """Full paginated history for /world-feed -- reads the same fast local
    cache table sync_news_events() keeps caught up with log.log, so this
    page load never has to pay that scan's cost itself."""
    sync_news_events()
    clauses, params = ["time >= %s"], [datetime.now() - timedelta(days=days)]
    if before:
        clauses.append("time < %s")
        params.append(before)
    raw = rows(f"""SELECT event_key,time,kind,message,actor,player_id,job,empire,vnum,socket0,refine_tier,method
      FROM player.web_seban_news_event WHERE {' AND '.join(clauses)}
      ORDER BY time DESC LIMIT %s""", params + [limit])
    events = []
    for r in raw:
        events.append({
            "key": r["event_key"], "time": r["time"], "message": r["message"], "kind": r["kind"],
            "refine_tier": r["refine_tier"], "player_id": r["player_id"], "job": r["job"], "empire": r["empire"],
            "vnum": r["vnum"], "socket0": r["socket0"], "actor": r["actor"], "method": r["method"],
            "time_label": r["time"].strftime("%H:%M"), "time_full": r["time"].strftime("%d.%m.%Y %H:%M"),
            "day_label": news_feed_day_label(r["time"]), "cursor": r["time"].strftime("%Y-%m-%d %H:%M:%S"),
        })
    return events


# Kolumny pliku statusu sprzed "systemu osobowości v2.0" -- rdzeń starszy niż
# Iwakury personas pisze dokładnie te czternaście, bez nagłówka. Ostatnia
# kolumna to zawsze wolny tekst statusu.
PLAYERBOT_STATUS_LEGACY_COLUMNS = ("pid", "personality", "ambition", "role", "in_party", "goal",
                                    "action", "updated_ms", "map_index", "x", "y", "hp", "max_hp", "status")
_LIVE_STATUS_INT_FIELDS = ("personality", "ambition", "role", "goal", "action", "updated_ms",
                            "map_index", "x", "y", "hp", "max_hp", "persona", "mood", "mood_lock", "lock_level")


def live_statuses():
    """Odczytuje najnowsze migawki statusu botów ze wszystkich rdzeni.

    Format kolumn czytany jest z nagłówka pliku (linia zaczynająca się od
    "pid\\t"), a nie na sztywno -- od "systemu osobowości v2.0" (Iwakura)
    rdzeń dopisuje persona/mood/mood_lock/lock_level przed status, więc stary
    podział na 14 sztywnych kolumn wcinał te cztery pola w tekst statusu
    zamiast je odczytać (naprawione 2026-09-21, audyt vs panel Tieru na 7788
    -- do tego dnia status wyświetlał się z doklejonymi cyframi z przodu).
    Rdzeń sprzed Iwakury pisze starych czternaście bez nagłówka wcale --
    wtedy używamy PLAYERBOT_STATUS_LEGACY_COLUMNS jako fallbacku.
    """
    result = {}
    for channel, path in channel_paths("playerbot_status.tsv"):
        try:
            if datetime.now().timestamp() - path.stat().st_mtime > 25:
                continue
            columns = None
            for line in path.read_text(encoding="cp1250", errors="replace").splitlines():
                if line.startswith("pid\t"):
                    columns = line.rstrip("\r\n").split("\t")
                    continue
                names = columns or PLAYERBOT_STATUS_LEGACY_COLUMNS
                parts = line.rstrip("\r\n").split("\t", len(names) - 1)
                if len(parts) != len(names) or names[-1] != "status":
                    continue
                row = dict(zip(names, parts))
                if "map" in row and "map_index" not in row:
                    row["map_index"] = row["map"]
                try:
                    pid = int(row["pid"])
                    entry = {name: int(row[name]) for name in _LIVE_STATUS_INT_FIELDS if name in row}
                except (KeyError, ValueError):
                    continue
                entry["in_party"] = bool(int(row.get("in_party", 0) or 0))
                entry["status"] = row.get("status", "")
                entry["channel"] = channel
                persona = entry.get("persona", PLAYERBOT_PERSONA_NONE)
                mood = entry.get("mood", PLAYERBOT_PERSONA_NONE)
                entry["persona"] = None if persona == PLAYERBOT_PERSONA_NONE else persona
                entry["mood"] = None if mood == PLAYERBOT_PERSONA_NONE else mood
                result[pid] = entry
        except OSError:
            continue
    return result


def guild_statuses():
    """Scal raporty rdzeni Playerbots (odświeżane co minutę), ze wszystkich
    kanałów naraz -- gildie są bytem serwerowym, nie kanałowym.
    Pola wspólne gildii bierzemy raz; botów online i exp sumujemy ze wszystkich
    rdzeni, bo każdy rdzeń widzi tylko własną część świata."""
    gathered, newest = {}, 0.0
    for _channel, path in channel_paths("playerbot_guild_status.tsv"):
        try:
            mtime = path.stat().st_mtime
            lines = path.read_text(encoding="cp1250", errors="replace").splitlines()
        except OSError:
            continue
        if not lines:
            continue
        newest = max(newest, mtime)
        columns = lines[0].rstrip("\r").split("\t")
        for line in lines[1:]:
            values = line.rstrip("\r").split("\t")
            if len(values) < len(columns):
                continue
            row = dict(zip(columns, values))
            try:
                gid, online = int(row.get("guild_id", 0)), int(row.get("online", 0))
                strength, offered = int(row.get("avg_strength", 0)), int(row.get("exp_offered_here", 0))
            except ValueError:
                continue
            if gid <= 0:
                continue
            guild = gathered.get(gid)
            if guild is None:
                guild = {"id": gid, "name": row.get("name", ""), "online": 0,
                         "strength_sum": 0, "exp_offered": 0, "master": row.get("master", ""),
                         "war_with": row.get("war_with", ""), "next_war_in_s": None}
                for key in ("empire", "tier", "level", "members", "master_pid", "ladder", "wins", "draws", "losses", "war_score", "war_enemy_score"):
                    try: guild[key] = int(row.get(key, 0))
                    except ValueError: guild[key] = 0
                gathered[gid] = guild
            guild["online"] += online
            guild["strength_sum"] += strength * online
            guild["exp_offered"] += offered
            if not guild["master"] and row.get("master"):
                guild["master"] = row["master"]
            if not guild["war_with"] and row.get("war_with"):
                guild["war_with"] = row["war_with"]
            try: next_war = int(row.get("next_war_in_s", -1))
            except ValueError: next_war = -1
            previous = guild["next_war_in_s"]
            if next_war >= 0 and (previous is None or previous < 0 or next_war < previous):
                guild["next_war_in_s"] = next_war
    if not gathered or time.time() - newest > 300:
        return [], None
    result = []
    for guild in gathered.values():
        guild["avg_strength"] = guild["strength_sum"] // guild["online"] if guild["online"] else 0
        guild["tier_label"] = GUILD_TIERS.get(guild["tier"], "Zwykła")
        result.append(guild)
    result.sort(key=lambda g: (g["tier"], -g["level"], -g["members"], g["name"].casefold()))
    return result, newest


def guild_war_text(seconds):
    if seconds is None or seconds < 0:
        return "brak zaplanowanej"
    if seconds == 0:
        return "trwa teraz"
    minutes = max(1, (seconds + 59) // 60)
    return f"za ok. {minutes} min"


def live_map_counts(channel=None):
    """channel=None sums every channel together (existing behaviour); pass a
    channel number to scope the count to just that channel."""
    counts = {}
    for entry in live_statuses().values():
        if channel is not None and entry.get("channel") != channel:
            continue
        index = entry["map_index"]
        counts[index] = counts.get(index, 0) + 1
    return [{"map_index": index, "character_count": count} for index, count in sorted(counts.items(), key=lambda item: -item[1])]


def live_bots():
    statuses = live_statuses()
    if not statuses:
        return []
    ids = list(statuses)
    placeholders = ",".join(["%s"] * len(ids))
    roster = rows(f"""
        SELECT p.id, p.name, p.level, p.exp, p.job, p.horse_level, """ + EMPIRE_EXPR + f""" AS empire FROM player.player p
        LEFT JOIN account.account a ON a.id=p.account_id
        LEFT JOIN player.player_index pi ON pi.id=p.account_id
        WHERE p.id IN ({placeholders}) AND (LEFT(a.login,10)='playerbot_' OR p.name LIKE 'bot%%')
    """, ids)
    threshold = max(1, min(120, int(settings().get("stuck_minutes", "5"))))
    historical = {}
    try:
        prior = rows("""SELECT s.pid,s.map_index,s.x,s.y FROM player.web_seban_bot_position_snapshot s
          JOIN (SELECT pid, MAX(captured_at) captured_at FROM player.web_seban_bot_position_snapshot
                WHERE captured_at <= NOW() - INTERVAL %s MINUTE GROUP BY pid) old
          ON old.pid=s.pid AND old.captured_at=s.captured_at WHERE s.pid IN (""" + placeholders + ")", (threshold, *ids))
        historical = {row["pid"]: row for row in prior}
    except pymysql.MySQLError:
        pass
    result = []
    for bot in roster:
        state = statuses.get(bot["id"])
        if state and state["map_index"] in MAP_BOUNDS:
            old = historical.get(bot["id"])
            stuck = bool(old and old["map_index"] == state["map_index"] and (old["x"] - state["x"]) ** 2 + (old["y"] - state["y"]) ** 2 < 40000 and not is_stationary_activity(state.get("status"), state.get("action")))
            # The free-text status is diagnostic and can be stale; action is the authoritative core state.
            result.append({
                **bot, **state,
                "personality_label": live_label("personality", state["personality"]),
                "ambition_label": live_label("ambition", state["ambition"]),
                "goal_label": live_label("goal", state["goal"]),
                "action_label": live_label("action", state["action"]),
                "persona_label": BOT_PERSONAS.get(state.get("persona")) if state.get("persona") is not None else None,
                "mood_label": BOT_MOODS.get(state.get("mood")) if state.get("mood") is not None else None,
                "mood_lock_label": BOT_MOOD_LOCKS.get(state.get("mood_lock") or 0),
                "stuck": stuck,
                "fighting_metin": int(state.get("goal") or 0) == 7 and int(state.get("action") or 0) == 2,
            })
    return result



def fishing_diagnostics():
    bots = live_bots()
    anglers = [bot for bot in bots if int(bot.get("action") or 0) == 14]
    matches = []
    for channel, path in channel_paths("syslog"):
        try:
            with path.open("rb") as handle:
                handle.seek(max(0, path.stat().st_size - 262144))
                text = handle.read().decode("latin-1", "ignore")
        except OSError:
            continue
        for line in text.splitlines():
            if re.search(r"fish|fishing|w[ęe]dk|rod", line, re.I):
                matches.append({"core": f"ch{channel}/{path.parent.name}", "line": line[-300:]})
    database_events = 0
    try:
        found = one("SELECT COUNT(*) AS total FROM log.log WHERE how LIKE %s OR hint LIKE %s", ("%FISH%", "%FISH%"))
        database_events = int(found.get("total") or 0) if found else 0
    except pymysql.MySQLError:
        pass
    return {"weights": read_ai_weights(), "online": len(bots), "anglers": anglers,
            "log_matches": matches[-80:], "database_events": database_events}

def read_rates():
    values = {name: 100 for name in RATE_NAMES}
    status = read_rate_status()
    if all(str(status.get(name, "")).isdigit() for name in RATE_NAMES):
        return {name: int(status[name]) for name in RATE_NAMES}
    try:
        for row in rows("SELECT name, value FROM player.web_admin_rates"):
            if row["name"] in values:
                values[row["name"]] = int(row["value"])
    except (KeyError, ValueError, pymysql.MySQLError):
        pass
    return values


def read_rate_status():
    result = {}
    try:
        for line in (RATES_SPOOL / "rates.status").read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                result[key.strip()] = value.strip()
    except OSError:
        pass
    return result


def read_map_regen_status():
    status_file = RATES_SPOOL / "map-regens.status"
    result = {"state": "idle", "message": "Brak zapisanej zmiany", "values": {}, "stones": {}}
    try:
        for line in status_file.read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition("=")
            if not separator:
                continue
            if key.startswith("map_stone_") and key[10:].isdigit():
                result["stones"][int(key[10:])] = value
            elif key.startswith("map_") and key[4:].isdigit():
                result["values"][int(key[4:])] = value
            else:
                result[key] = value
    except OSError:
        pass
    return result


def read_spool_values(path):
    """Read a small key=value status file written by a fixed helper."""
    result = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                result[key.strip()] = value.strip()
    except OSError:
        pass
    return result


def update_status():
    """State exposed by Tieru's isolated updater through its tiny spool."""
    result = read_spool_values(UPDATE_SPOOL / "update.status")
    try:
        age = max(0, int(time.time() - (UPDATE_SPOOL / "watcher").stat().st_mtime))
    except OSError:
        age = None
    result["watcher_age"] = age
    result["watcher_ready"] = age is not None and age < UPDATE_WATCHER_MAX_AGE_SECONDS
    result["state"] = result.get("state", "idle")
    try:
        step, steps = int(result.get("step", 0)), int(result.get("steps", 5))
        result["percent"] = max(0, min(100, round(step * 100 / max(steps, 1))))
    except ValueError:
        result["percent"] = 0
    if result["state"] == "running":
        result["percent"] = max(5, result["percent"])
    result["message"] = result.get("message", "Aktualizator czeka na zlecenie." if result["watcher_ready"] else "Aktualizator nie jest uruchomiony.")
    try:
        result["log"] = (UPDATE_SPOOL / "update.log").read_text(encoding="utf-8", errors="replace").splitlines()[-18:]
    except OSError:
        result["log"] = []
    return result


def installed_playerbots_version():
    """Read the live MT2009 version reported by the isolated updater watcher."""
    current = update_status()
    reported = str(current.get("version") or "").strip()
    if version_key(reported):
        return reported
    if current.get("state") == "ok":
        match = re.search(r"version ([0-9]+(?:\.[0-9]+)+)", current.get("message", ""))
        if match:
            return match.group(1)
    return os.environ.get("PLAYERBOTS_VERSION", "nieustawiona")

def version_key(value):
    match = re.fullmatch(r"v?([0-9]+(?:\.[0-9]+)+)", str(value or "").strip(), re.I)
    return tuple(int(part) for part in match.group(1).split(".")) if match else None


def latest_playerbots_release():
    """Read GitHub's latest release, cached so page loads never hammer the API."""
    now = time.time()
    if now - _playerbots_release_cache["checked_at"] < PLAYERBOTS_RELEASE_CACHE_SECONDS:
        return dict(_playerbots_release_cache)
    result = {"checked_at": now, "latest": None, "error": None}
    try:
        request_github = Request(PLAYERBOTS_RELEASE_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": "Metin2-Singleplayer-Panel"})
        with urlopen(request_github, timeout=3) as response:
            payload = json.load(response)
        tag = str(payload.get("tag_name") or "").strip()
        if not version_key(tag):
            raise ValueError("GitHub nie zwrócił poprawnego numeru wydania.")
        result["latest"] = tag.lstrip("vV")
    except (OSError, ValueError, HTTPError, URLError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)[:120] or "Nie udało się połączyć z GitHub."
    _playerbots_release_cache.clear()
    _playerbots_release_cache.update(result)
    return dict(result)


def playerbots_release_status():
    installed = installed_playerbots_version().strip()
    latest_info = latest_playerbots_release()
    latest = latest_info.get("latest")
    installed_key, latest_key = version_key(installed), version_key(latest)
    if installed_key and latest_key:
        behind = installed_key < latest_key
        if not behind:
            tone = "current"
        else:
            installed_parts = (installed_key + (0, 0, 0))[:3]
            latest_parts = (latest_key + (0, 0, 0))[:3]
            same_release_line = installed_parts[:2] == latest_parts[:2]
            patch_gap = latest_parts[2] - installed_parts[2]
            tone = "warning" if same_release_line and 1 <= patch_gap <= 3 else "outdated"
        return {"installed": installed, "latest": latest, "behind": behind,
                "tone": tone, "label": f"Dostępna {latest}" if behind else "Aktualna"}
    return {"installed": installed, "latest": latest, "behind": False, "tone": "unknown",
            "label": "Nie sprawdzono GitHub" if latest_info.get("error") else "Brak wersji lokalnej"}


def update_csrf_token():
    token = session.get("seban_update_csrf")
    if not token:
        token = uuid.uuid4().hex
        session["seban_update_csrf"] = token
    return token


def queue_tieru_update(update_seban_panel=False):
    """Request only the updater's fixed sequence; no command, URL or path crosses this boundary."""
    current = update_status()
    if not current["watcher_ready"]:
        raise RuntimeError("Aktualizator nie jest gotowy. Administrator musi uruchomić usługę updater.")
    if current.get("state") == "running":
        raise RuntimeError("Aktualizacja już trwa. Poczekaj na jej zakończenie.")
    version = installed_playerbots_version().strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
        version = "0"
    request_id = "seban-" + uuid.uuid4().hex
    UPDATE_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = UPDATE_SPOOL / (request_id + ".new")
    try:
        update_panel = "1" if update_seban_panel else "0"
        temporary.write_text(
            f"id={request_id}\nversion={version}\ntime={int(time.time())}\nupdate_seban_panel={update_panel}\n",
            encoding="utf-8",
        )
        temporary.chmod(0o660)
        # replace is atomic. The worker records the id before doing work, so a
        # completed request never runs twice after a container recreation.
        os.replace(temporary, UPDATE_SPOOL / "request")
    finally:
        temporary.unlink(missing_ok=True)



EVENTS_FILE = RATES_SPOOL / "playerbot_events.tsv"
EVENT_KINDS = ("chest", "exp", "drop", "yang")
EVENT_LABELS = {
    "chest": "Szkatułki Blasku Księżyca",
    "exp": "Doświadczenie",
    "drop": "Drop przedmiotów",
    "yang": "Yang",
}
EVENT_DAY_NAMES = ("Pn", "Wt", "Śr", "Cz", "Pt", "Sb", "Nd")
EVENT_NOW_MINUTES = (15, 30, 60, 120, 180, 360)
EVENT_HHMM = re.compile(r"^([01]?\d|2[0-4]):([0-5]\d)$")


def event_hhmm(text):
    match = EVENT_HHMM.match((text or "").strip())
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour == 24 and minute != 0:
        return None
    return f"{hour:02d}:{minute:02d}"


def read_events():
    rows, nows = [], {}
    try:
        lines = EVENTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return rows, nows
    for line in lines:
        line = line.rstrip("\r")
        if not line.strip():
            continue
        enabled = True
        if line.startswith("#off\t"):
            enabled, line = False, line[5:]
        elif line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) >= 4 and fields[0] == "now" and fields[1] in EVENT_KINDS:
            try:
                nows[fields[1]] = {"until": int(fields[2]), "value": int(fields[3])}
            except ValueError:
                pass
            continue
        if len(fields) < 5 or fields[0] not in EVENT_KINDS:
            continue
        start, end = event_hhmm(fields[2]), event_hhmm(fields[3])
        if not start or not end:
            continue
        try:
            value = int(fields[4])
        except ValueError:
            value = 0
        days = list(range(1, 8)) if fields[1] == "*" else [day for day in range(1, 8) if str(day) in fields[1].split(",")]
        rows.append({"kind": fields[0], "days": days, "start": start, "end": end,
                     "value": value, "on": enabled})
    return rows, nows


def write_events(rows, nows):
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    body = [
        "# Metin2 Playerbots -- timed events, written by Seban Panel.",
        "# kind<TAB>days<TAB>from<TAB>to<TAB>value | now<TAB>kind<TAB>until_epoch<TAB>value",
        "# days: * or 1..7 (1 = Monday); #off keeps a disabled plan row.",
        "",
    ]
    for row in rows:
        days = "*" if len(row["days"]) == 7 else (",".join(str(day) for day in row["days"]) or "-")
        line = "%s\t%s\t%s\t%s\t%d" % (row["kind"], days, row["start"], row["end"], int(row["value"]))
        body.append(line if row.get("on", True) else "#off\t" + line)
    for kind in EVENT_KINDS:
        now_event = nows.get(kind)
        if now_event and int(now_event.get("until", 0)) > time.time():
            body.append("now\t%s\t%d\t%d" % (kind, int(now_event["until"]), int(now_event.get("value", 0))))
    temporary = EVENTS_FILE.with_suffix(".tsv.new")
    temporary.write_text("\n".join(body) + "\n", encoding="utf-8")
    os.replace(temporary, EVENTS_FILE)


def read_events_status():
    newest, newest_written = {}, 0
    for _channel, path in channel_paths("playerbot_events_status.tsv"):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        current, written = {}, 0
        for line in lines[1:]:
            fields = line.rstrip("\r").split("\t")
            if len(fields) < 8 or fields[0] not in EVENT_KINDS:
                continue
            try:
                current[fields[0]] = {"scheduled": fields[1] == "1", "active": fields[2] == "1", "value": int(fields[3]), "until": int(fields[4]), "next_start": int(fields[5]), "next_value": int(fields[6])}
                written = int(fields[7])
            except ValueError:
                continue
        if current and written > newest_written:
            newest, newest_written = current, written
    if not newest or time.time() - newest_written > 300:
        return {}
    for item in newest.values():
        for key in ("until", "next_start"):
            stamp = item.get(key, 0)
            if stamp:
                item[key + "_text"] = time.strftime("%H:%M" if time.localtime(stamp).tm_yday == time.localtime().tm_yday else "%d.%m %H:%M", time.localtime(stamp))
    return newest


# vnum Szkatułki Blasku Księżyca (special_item_group.moonlight.txt) -- jedyny
# event z konkretnym, policzalnym przedmiotem.
MOONLIGHT_CHEST_VNUM = 50011


def event_run_stats(kind, started_at, ended_at, value):
    """Statystyki dla zakończonego okna eventu, liczone z log.log (zdarzenia,
    nie stan ekwipunku/konta -- działa niezależnie od tego czy bot szkatułkę
    otworzył, sprzedał czy zatrzymał)."""
    if kind == "chest":
        found = one("SELECT COUNT(*) AS n FROM log.log WHERE how='GET' AND vnum=%s AND time BETWEEN %s AND %s",
                     (MOONLIGHT_CHEST_VNUM, started_at, ended_at))
        return {"chest_count": int(found["n"]) if found else 0, "yang_extra": None}
    if kind == "yang":
        found = one("SELECT COALESCE(SUM(what),0) AS total FROM log.log WHERE how='GET_GOLD' AND time BETWEEN %s AND %s",
                     (started_at, ended_at))
        total = int(found["total"]) if found else 0
        # "value" to bonus w % dołożony na czas eventu -- zakładając że suma
        # już go zawiera, sam bonus to total * value/(100+value). Orientacyjne
        # (nie znamy dokładnego wzoru rdzenia), ale rząd wielkości jest dobry.
        extra = round(total * value / (100 + value)) if value > 0 else 0
        return {"chest_count": None, "yang_extra": extra}
    return {"chest_count": None, "yang_extra": None}


def create_notification(kind, title, body=None, link_url=None, ref_id=None):
    """Wspólny wpis do dzwoneczka powiadomień (base.html, każda strona) --
    źródła: koniec eventu, nowa wersja Playerbots, podsumowanie dnia.
    INSERT IGNORE + UNIQUE(kind,ref_id) (collector.py init()) -- powiadomienia
    powstają przy okazji zwykłego ruchu na stronie (żaden osobny proces w
    tle), więc dwa równoległe żądania (2 workery gunicorn x 4 wątki) mogły
    oba zobaczyć ten sam "otwarty" event/dzień przed zapisem drugiego i
    wstawić dwa identyczne wpisy -- duplikaty w dzwoneczku, zgłoszone przez
    [GA]Seban 2026-09-21. Druga wstawka jest teraz po prostu cicho ignorowana."""
    rows("INSERT IGNORE INTO player.web_seban_notifications (kind,title,body,link_url,ref_id) VALUES (%s,%s,%s,%s,%s)",
         (kind, title, body, link_url, ref_id))


def check_finished_events():
    """Wykrywa start/koniec eventów czasowych (ręcznych i z harmonogramu) i
    dopisuje/finalizuje wiersze w web_seban_event_runs -- wywoływane przy
    okazji zwykłego ruchu na dashboardzie (co ok. 30s przez otwarte karty),
    nie osobnym procesem w tle. Idempotentne: bezpieczne wołać wielokrotnie."""
    try:
        status = read_events_status()
        open_runs = {row["kind"]: row for row in rows(
            "SELECT id,kind,value,started_at FROM player.web_seban_event_runs WHERE ended_at IS NULL")}
        for kind in EVENT_KINDS:
            live = status.get(kind)
            active = bool(live and live.get("active"))
            open_run = open_runs.get(kind)
            if active and not open_run:
                rows("INSERT INTO player.web_seban_event_runs (kind,value,started_at) VALUES (%s,%s,NOW())",
                     (kind, int(live.get("value") or 0)))
            elif not active and open_run:
                stats = event_run_stats(kind, open_run["started_at"], datetime.now(), open_run["value"])
                rows("UPDATE player.web_seban_event_runs SET ended_at=NOW(), chest_count=%s, yang_extra=%s WHERE id=%s",
                     (stats["chest_count"], stats["yang_extra"], open_run["id"]))
                label = EVENT_LABELS.get(kind, kind)
                summary = (f"Wydropiono {stats['chest_count']} szkatułek." if stats["chest_count"] is not None
                           else f"Gracze wydropili o {stats['yang_extra']:,} więcej yang.".replace(",", " ") if stats["yang_extra"] is not None
                           else None)
                create_notification("event_ended", f"Event zakończony: {label}", summary,
                                     f"/events#run-{open_run['id']}", open_run["id"])
    except pymysql.MySQLError:
        pass


def check_version_notification():
    """Powiadomienie o nowej wersji Playerbots na GitHubie -- jedno na wersję
    (znacznik w common.m2_switches, ten sam mechanizm co reszta przełączników
    panelu), klik prowadzi prosto na stronę wydania."""
    try:
        release = playerbots_release_status()
        latest = release.get("latest")
        if not latest or not release.get("behind"):
            return
        last_notified = one("SELECT value FROM common.m2_switches WHERE name='last_notified_version'")
        if (last_notified.get("value") if last_notified else None) == latest:
            return
        rows("INSERT INTO common.m2_switches (name,value) VALUES ('last_notified_version',%s) "
             "ON DUPLICATE KEY UPDATE value=VALUES(value)", (latest,))
        # ref_id z CRC32 numeru wersji (deterministyczne, mieści się w
        # BIGINT UNSIGNED) -- bez tego dwa równoległe żądania omijałyby
        # UNIQUE(kind,ref_id) na ref_id=NULL (NULL nigdy nie koliduje samo ze
        # sobą w unikalnym indeksie) i dalej dublowałyby to powiadomienie.
        create_notification("version_update", f"Nowa wersja Playerbots: {latest}",
                             f"Masz zainstalowaną {release.get('installed')}.",
                             "https://github.com/TieruYT/metin2-playerbots/releases/latest",
                             zlib.crc32(latest.encode()))
    except pymysql.MySQLError:
        pass


def metric_at_or_before(name, when):
    row = one("SELECT value FROM player.web_seban_metric_snapshot WHERE metric=%s AND captured_at<=%s "
              "ORDER BY captured_at DESC LIMIT 1", (name, when))
    return int(row["value"]) if row else None


def metric_at_or_after(name, when):
    row = one("SELECT value FROM player.web_seban_metric_snapshot WHERE metric=%s AND captured_at>=%s "
              "ORDER BY captured_at ASC LIMIT 1", (name, when))
    return int(row["value"]) if row else None


def check_daily_summary():
    """Wykrywa przekroczenie granicy dnia (00:00) i generuje "Podsumowanie
    dnia" za dzień, który się właśnie skończył -- start/koniec kilku metryk
    (migawki co 5 min z collector.py) plus liczniki zdarzeń z tego okna.
    Dzień 1 = dzień najstarszej migawki, czyli mniej więcej start tego
    świata (nie ma osobnego znacznika "world started at")."""
    try:
        today = datetime.now().date()
        last_row = one("SELECT MAX(summary_date) AS d FROM player.web_seban_daily_summary")
        last_date = last_row.get("d") if last_row else None
        first_seen = one("SELECT MIN(captured_at) AS t FROM player.web_seban_system_snapshot")
        world_start = first_seen.get("t") if first_seen else None
        if not world_start:
            return
        target_date = (last_date + timedelta(days=1)) if last_date else world_start.date()
        if target_date >= today:
            return  # dzień jeszcze trwa, nic do podsumowania
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        day_number = (target_date - world_start.date()).days + 1

        def bounds(metric):
            return metric_at_or_after(metric, day_start), metric_at_or_before(metric, day_end)

        bots_start, bots_end = bounds("bots_count")
        yang_start, yang_end = bounds("total_yang")
        cash_start, cash_end = bounds("dragon_coins")
        shops_start, shops_end = bounds("shops_count")
        # Tylko postacie Playerbots -- konto GM/admina z wysokim poziomem
        # fałszowałoby "najwyższy poziom" (audyt operatora, 2026-09-21).
        level_start = one("""SELECT COALESCE(MAX(p.level),0) AS v FROM player.player p
          LEFT JOIN account.account a ON a.id=p.account_id
          WHERE LEFT(a.login,10)='playerbot_' AND p.last_play<%s""", (day_end,)).get("v", 0)
        level_end = one("""SELECT COALESCE(MAX(p.level),0) AS v FROM player.player p
          LEFT JOIN account.account a ON a.id=p.account_id
          WHERE LEFT(a.login,10)='playerbot_'""").get("v", 0)
        refine9 = one("SELECT COUNT(*) AS n FROM log.log WHERE how='REFINE SUCCESS' AND hint LIKE '%%+9' AND time BETWEEN %s AND %s",
                       (day_start, day_end)).get("n", 0)
        metins = one("SELECT COUNT(*) AS n FROM log.log WHERE how='STONE_KILL' AND time BETWEEN %s AND %s",
                      (day_start, day_end)).get("n", 0)
        bosses = one("SELECT COUNT(*) AS n FROM log.log WHERE how='BOSS_KILL' AND time BETWEEN %s AND %s",
                      (day_start, day_end)).get("n", 0)
        # log.fish_log -- same table the "Wyłowione ryby" ranking reads
        # (found 2026-09-23), has its own `time` column so a daily window
        # works directly, unlike player_special_flag's stat_fishing which is
        # a cumulative all-time counter with no history to diff against.
        fish = one("SELECT COALESCE(SUM(count),0) AS n FROM log.fish_log WHERE time BETWEEN %s AND %s",
                    (day_start, day_end)).get("n", 0)
        # Mining has no dedicated per-event log table and no timestamped
        # counter -- player_special_flag's stat_mining is cumulative only.
        # The actual source is log.money_log(type='DROP'), which every ore
        # drop writes to via mining.cpp's SendMoneyLog(MONEY_LOG_DROP,
        # oreVnum, count) call -- but that same log entry also fires for
        # ordinary monster-kill item drops (item_manager.cpp) and other item
        # creation (char_item.cpp), so it only isolates mining by filtering
        # to the 19 raw-ore vnums mining.cpp actually hands out (50601-50619,
        # mining.cpp's `info[MAX_ORE]` table) -- confirmed against those exact
        # vnums live before wiring this in.
        mining = one("""SELECT COALESCE(SUM(gold),0) AS n FROM log.money_log
          WHERE type='DROP' AND vnum BETWEEN 50601 AND 50619 AND time BETWEEN %s AND %s""",
                      (day_start, day_end)).get("n", 0)
        events_count = one("SELECT COUNT(*) AS n FROM player.web_seban_event_runs WHERE ended_at BETWEEN %s AND %s",
                            (day_start, day_end)).get("n", 0)
        # Broń z najwyższymi średnimi obrażeniami aktualnie noszona przez
        # kogokolwiek -- to samo zapytanie co ranking "+30 broni" na
        # /rankings (APPLY_NORMAL_HIT_DAMAGE_BONUS), tylko bierzemy #1.
        top_weapon_vnum = top_weapon_name = top_weapon_avg = top_weapon_pid = top_weapon_owner = None
        try:
            weapon_top = bot_ranking("weapon30", sort_by="avg")
            if weapon_top and int(weapon_top[0].get("avg_damage") or 0) > 0:
                w = weapon_top[0]
                top_weapon_vnum, top_weapon_name = w["vnum"], w["item_name"]
                top_weapon_avg, top_weapon_pid, top_weapon_owner = w["avg_damage"], w["id"], w["name"]
        except pymysql.MySQLError:
            pass
        rows("""INSERT INTO player.web_seban_daily_summary
          (summary_date,day_number,bots_start,bots_end,yang_start,yang_end,refine9_count,metin_count,
           cash_start,cash_end,events_count,level_start,level_end,shops_start,shops_end,
           top_weapon_vnum,top_weapon_name,top_weapon_avg_damage,top_weapon_owner_pid,top_weapon_owner_name,
           fish_count,mining_count,boss_count)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
          (target_date, day_number, bots_start, bots_end, yang_start, yang_end, refine9, metins,
           cash_start, cash_end, events_count, level_start, level_end, shops_start, shops_end,
           top_weapon_vnum, top_weapon_name, top_weapon_avg, top_weapon_pid, top_weapon_owner,
           fish, mining, bosses))
        new_id = one("SELECT id FROM player.web_seban_daily_summary WHERE summary_date=%s", (target_date,)).get("id")
        create_notification("daily_summary", f"Podsumowanie dnia {day_number}",
                             f"{target_date.strftime('%d.%m.%Y')} — kliknij, żeby zobaczyć szczegóły.",
                             f"/daily-summary/{new_id}", new_id)
    except pymysql.MySQLError:
        pass


def check_all_notifications():
    check_finished_events()
    check_version_notification()
    check_daily_summary()


def read_ai_weights():
    """Read Tieru's live Playerbots goal weights; absent entries are neutral."""
    values = {key: AI_WEIGHT_NEUTRAL for key, _, _ in AI_WEIGHT_KEYS}
    values.update(AI_LIVE_DEFAULTS)
    try:
        for line in AI_WEIGHTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            fields = line.split("#", 1)[0].split()
            if len(fields) >= 2 and fields[0].upper() in values:
                try:
                    key, raw_value = fields[0].upper(), fields[1]
                    if key in ("CHAT", "BOOKS", "NIGHT", "LIFE", "WARS", "TOWER", "ISHOP", "PERSONA"):
                        values[key] = 0 if raw_value.lower() in ("0", "off", "no") else 1
                    elif key in ("SCRAP", "REST", "KINGDOMPVP"):
                        values[key] = max(0, min(100, int(raw_value)))
                    elif key == "SCROLL_FROM":
                        values[key] = max(1, min(9, int(raw_value)))
                    elif key in ("CHEST", "CHEST_STONE"):
                        values[key] = max(0, min(1000, int(raw_value)))
                    else:
                        values[key] = max(AI_WEIGHT_MIN, min(AI_WEIGHT_MAX, int(raw_value)))
                except ValueError:
                    pass
    except OSError:
        pass
    return values


def preserved_ai_weight_lines():
    """Keep new core keys this panel does not know about yet on every save."""
    known = {key for key, _, _ in AI_WEIGHT_KEYS} | AI_SPECIAL_WEIGHT_KEYS
    preserved = []
    try:
        for line in AI_WEIGHTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            fields = line.split("#", 1)[0].split()
            if len(fields) != 2:
                continue
            key, value = fields[0].upper(), fields[1]
            if key not in known and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", key) and re.fullmatch(r"-?\d{1,10}", value):
                preserved.append(f"{key}\t{value}")
    except OSError:
        pass
    return preserved


def write_ai_weights(values):
    """Atomically replace known values without erasing newer-core settings."""
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    content = [
        "# Metin2 Playerbots — wagi celów ustawione przez Seban Panel.",
        "# 25 = rzadko · 100 = domyślnie · 250 = często.",
        "# Rdzeń odczytuje plik co pięć sekund; restart nie jest wymagany.", "",
    ]
    content.extend(f"{key}\t{values[key]}" for key, _, _ in AI_WEIGHT_KEYS)
    content.append(f"CHAT\t{1 if values.get('CHAT', 1) else 0}")
    content.append(f"BOOKS\t{1 if values.get('BOOKS', 1) else 0}")
    content.append(f"NIGHT\t{1 if values.get('NIGHT', 1) else 0}")
    content.append(f"LIFE\t{1 if values.get('LIFE', 0) else 0}")
    content.append(f"WARS\t{1 if values.get('WARS', 1) else 0}")
    content.append(f"TOWER\t{1 if values.get('TOWER', 1) else 0}")
    content.append(f"ISHOP\t{1 if values.get('ISHOP', 1) else 0}")
    content.append(f"PERSONA\t{1 if values.get('PERSONA', 1) else 0}")
    content.append(f"SCRAP\t{max(0, min(100, int(values.get('SCRAP', 0))))}")
    content.append(f"REST\t{max(0, min(100, int(values.get('REST', 100))))}")
    content.append(f"KINGDOMPVP\t{max(0, min(100, int(values.get('KINGDOMPVP', 0))))}")
    content.append(f"SCROLL_FROM\t{max(1, min(9, int(values.get('SCROLL_FROM', 1))))}")
    for key in ("CHEST", "CHEST_STONE"):
        if values.get(key) is not None:
            content.append(f"{key}\t{max(0, min(1000, int(values[key])))}")
    content.extend(preserved_ai_weight_lines())
    temporary = AI_WEIGHTS_FILE.with_suffix(".tsv.new")
    temporary.write_text("\n".join(content) + "\n", encoding="utf-8")
    os.replace(temporary, AI_WEIGHTS_FILE)


def read_ai_item_policy():
    try:
        return AI_ITEM_POLICY_FILE.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_ai_item_policy(text):
    """Line numbers the core would silently skip, so a typo is caught here
    instead of a bot just ignoring the rule with no error anywhere."""
    bad = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        key = parts[0].lower()
        ok_key = key.isdigit() or (key.startswith("type:") and key[5:].isdigit())
        if len(parts) != 2 or not ok_key or parts[1].lower() not in AI_ITEM_POLICY_WORDS:
            bad.append(number)
    return bad


def write_ai_item_policy(text):
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = AI_ITEM_POLICY_FILE.with_suffix(".tsv.new")
    temporary.write_text(text.replace("\r\n", "\n").rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, AI_ITEM_POLICY_FILE)


BOT_HOLD_FILE = RATES_SPOOL / "playerbot_hold"


def read_bot_hold():
    """Czy boty stoją teraz przy drzwiach (M2_PLAYERBOT_START_HELD przy świeżym
    siewie, albo ten przełącznik ręcznie później) -- plik, którego brak albo
    nieczytelność znaczy tyle co "nie ma trzymania"."""
    try:
        return BOT_HOLD_FILE.read_text(encoding="utf-8", errors="replace")[:32].strip().startswith("1")
    except OSError:
        return False


def write_bot_hold(held):
    """Rdzeń czyta ten plik na tym samym pięciosekundowym zegarze co wagi AI,
    więc wpuszczenie/zatrzymanie botów nie wymaga restartu ani nie rozłącza
    nikogo -- świat wypełnia się zwykłym oknem spawnu."""
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = BOT_HOLD_FILE.with_suffix(".tmp")
    temporary.write_text("1\n" if held else "0\n", encoding="utf-8")
    os.replace(temporary, BOT_HOLD_FILE)


def queue_tower_now():
    """"Teraz" dla Wieży Demonów gildii botów -- rdzeń patrzy na mtime tego
    pliku (PLAYERBOT_TOWER_NOW_PATH) i przy najbliższym sprawdzeniu wywołuje
    najazd, jeśli żaden akurat nie trwa."""
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    path = RATES_SPOOL / "playerbot_tower_now"
    path.touch(exist_ok=True)
    os.utime(path, None)


def port_open(port):
    try:
        with socket.create_connection((GAME_HOST, port), timeout=0.4):
            return True
    except OSError:
        return False


def restart_progress():
    result = {}
    try:
        for line in (RATES_SPOOL / "server-settings.status").read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep:
                result[key] = value
        result["percent"] = max(0, min(100, int(result.get("percent", 0))))
        result["stage"] = result.get("message", "Oczekiwanie na stan serwera")
        if (RATES_SPOOL / "server-settings.request").exists() and result.get("state") != "running":
            result.update(state="running", percent=5, stage="Zlecenie oczekuje na serwer")
        return result
    except (OSError, ValueError):
        pass
    status = read_rate_status()
    auth, world = port_open(GAME_LOGIN_PORT), port_open(GAME_WORLD_PORT)
    state = status.get("state", "unknown")
    if state == "running":
        if not auth:
            return {"percent": 25, "stage": "Zatrzymywanie procesów gry", "state": state}
        if not world:
            return {"percent": 65, "stage": "Serwer logowania działa — uruchamianie świata", "state": state}
        return {"percent": 85, "stage": "Sprawdzanie kanału i usług", "state": state}
    if state == "ok" and auth and world:
        return {"percent": 100, "stage": "Serwer działa", "state": state}
    if state == "failed":
        return {"percent": 100, "stage": status.get("message", "Restart nie powiódł się"), "state": state}
    return {"percent": 100 if auth and world else 40, "stage": "Serwer działa" if auth and world else "Oczekiwanie na usługi", "state": state}


# On the mt2009 line a rate is not a rewritten table but six event flags the
# engine multiplies by (mob_exp / mob_item / mob_gold and their "_buyer"
# twins for premium accounts): rows of player.quest with dwPID = 0, read by the
# db core at boot and pushed to every game core. The game container has no
# database client, so the panel writes the rows and the restart it queues
# below is what makes the cores read them. See files/admin_panel.py, which
# also tries the in-game helper first; this console is a restart console.
MT2009_RATE_FLAGS = {
    "exp":  ("mob_exp",  "mob_exp_buyer"),
    "drop": ("mob_item", "mob_item_buyer"),
    "yang": ("mob_gold", "mob_gold_buyer"),
}


def persist_rates_mt2009(values):
    with db() as connection, connection.cursor() as cursor:
        for name, flags in MT2009_RATE_FLAGS.items():
            for flag in flags:
                cursor.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', %s)",
                               (flag, int(values[name])))
        # The classic panel's table too, so both pages show the same numbers.
        try:
            for name in RATE_NAMES:
                cursor.execute("INSERT INTO player.web_admin_rates (name, value) VALUES (%s, %s) "
                               "ON DUPLICATE KEY UPDATE value=VALUES(value)", (name, int(values[name])))
        except pymysql.MySQLError:
            pass
        connection.commit()


def read_spawn_plan():
    values = read_spool_values(UPDATE_SPOOL / "spawn-plan.status")
    def number(key, default):
        try:
            return int(values.get(key, default))
        except (TypeError, ValueError):
            return default
    return {"window": max(1, min(180, number("window", 1))), "late_joiners": max(0, min(2500, number("late_joiners", 0))), "late_hours": max(1, min(168, number("late_hours", 24))), "state": values.get("state", "gotowy"), "message": values.get("message", "")}


def queue_spawn_plan(window, late_joiners, late_hours):
    stamp = int(time.time() * 1000)
    UPDATE_SPOOL.mkdir(parents=True, exist_ok=True)
    body = f"id=seban-spawn-{stamp}\nwindow={window}\nlate_joiners={late_joiners}\nlate_hours={late_hours}\ntime={int(time.time())}\n"
    temporary = UPDATE_SPOOL / "spawn-plan.request.new"
    temporary.write_text(body, encoding="utf-8")
    os.replace(temporary, UPDATE_SPOOL / "spawn-plan.request")
    (UPDATE_SPOOL / "spawn-plan.status").write_text(f"state=oczekuje\ntime={int(time.time())}\nwindow={window}\nlate_joiners={late_joiners}\nlate_hours={late_hours}\nmessage=Plan wejścia zapisany; oczekiwanie na restart gry.\n", encoding="utf-8")


def read_bot_count():
    """The bot-count target the game side will use on its next start.

    PLAYERBOT_AUTOSPAWN_COUNT is read once, at core boot, only when
    CPlayerBotManager::GetCount()==0 (game/src/input_db.cpp) -- there is no
    live/hot-reload path for it, matching Tieru's own launcher slider
    ("Zmiana suwaka działa dopiero po restarcie serwera", panel CHANGELOG
    1.33.2). A change therefore needs a real container recreate of `game`,
    exactly like the spawn-plan feature already does -- so this reads/writes
    through the SAME update-spool volume and watcher as queue_spawn_plan(),
    not RATES_SPOOL (that one is polled live, in-process, from inside the
    game container by m2-rates; there is no equivalent poller for bot count,
    confirmed missing from the image, 2026-09-26). Falls back to counting
    who is actually alive right now (never zero on a running world) only
    when the spool has nothing at all.
    """
    status = read_spool_values(UPDATE_SPOOL / "botcount.status")
    value = status.get("count", "")
    if value.isdigit():
        return int(value)
    return len(live_bots()) or 350


def queue_botcount_change(count):
    """Ask for a new playerbot target -- writes PLAYERBOT_AUTOSPAWN_COUNT
    into .env and force-recreates the `game` container, via the same
    isolated host-side watcher (seban-updater-watch.sh) that already
    handles the spawn-plan feature. See read_bot_count()'s docstring for
    why this can't be a live in-process reload."""
    stamp = int(time.time() * 1000)
    request_data = "\n".join((f"id=seban-botcount-{stamp}", f"count={count}", f"time={int(time.time())}", ""))
    UPDATE_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = UPDATE_SPOOL / "botcount.request.new"
    temporary.write_text(request_data, encoding="utf-8")
    os.replace(temporary, UPDATE_SPOOL / "botcount.request")
    (UPDATE_SPOOL / "botcount.status").write_text(
        "state=oczekuje\ntime=%s\ncount=%s\nmessage=Żądanie zapisane; oczekiwanie na restart gry.\n" %
        (int(time.time()), count), encoding="utf-8")


def read_student_chest_disabled():
    """Whether a new character (bot or player), of any class, is denied its
    starter chest (50187 warrior/sura, 50212 assassin, 50213 shaman).

    common.m2_switches is the same durable row apply.sh writes from
    M2_PLAYERBOT_DISABLE_STUDENT_CHEST at every playerbot-migrate start, and
    that starter_chest.quest reads live on a real player's first login --
    see that quest's own header for why a live read beats a cached one here.
    No row yet (a fresh install, or an image predating this switch) reads as
    "not disabled", matching the chest's original always-on behaviour.
    """
    row = one("SELECT value FROM common.m2_switches WHERE name='disable_student_chest'")
    return str(row.get("value", "0")) == "1"


def write_student_chest_disabled(disabled):
    """Flip the switch immediately, for real players' next login.

    This only ever touches the DB row a running quest reads live, so it
    needs no restart of anything -- unlike the rest of this page. It is
    still only half the story: a bot's own copy comes from a session
    variable apply.sh sets once at container start from
    M2_PLAYERBOT_DISABLE_STUDENT_CHEST, so this panel toggle covers real
    players' characters right away but leaves already-seeded bots and the
    .env default untouched, and a future playerbot-migrate run (a deploy, a
    host reboot) will reset this row back to whatever .env still says. Keep
    both in sync there if the choice should survive that.
    """
    rows(
        "INSERT INTO common.m2_switches (name, value) VALUES ('disable_student_chest', %s) "
        "ON DUPLICATE KEY UPDATE value = VALUES(value)",
        ("1" if disabled else "0",),
    )


def queue_rate_restart(values):
    if ENGINE_MT2009:
        persist_rates_mt2009(values)
    stamp = int(time.time() * 1000)
    request_data = "\n".join((
        f"id=seban-{stamp}",
        f"exp={values['exp']}",
        f"drop={values['drop']}",
        f"yang={values['yang']}",
        f"time={int(time.time())}",
        "",
    ))
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = RATES_SPOOL / "request.new"
    temporary.write_text(request_data, encoding="utf-8")
    os.replace(temporary, RATES_SPOOL / "request")
    (RATES_SPOOL / "rates.status").write_text(
        "state=running\ntime=%s\nexp=%s\ndrop=%s\nyang=%s\nmessage=restart requested by Seban Panel\n" %
        (int(time.time()), values["exp"], values["drop"], values["yang"]), encoding="utf-8")


def server_settings_status():
    """Report whether the game-side restart helper is alive, not just queued."""
    ready = read_spool_values(RATES_SPOOL / "server-settings.ready")
    request = RATES_SPOOL / "server-settings.request"
    status = read_spool_values(RATES_SPOOL / "server-settings.status")
    try:
        ready_age = max(0, int(time.time() - (RATES_SPOOL / "server-settings.ready").stat().st_mtime))
    except OSError:
        ready_age = None
    try:
        request_age = max(0, int(time.time() - request.stat().st_mtime))
    except OSError:
        request_age = None
    worker_ready = ready.get("capability") == "server-settings" and ready_age is not None and ready_age <= SERVER_SETTINGS_READY_MAX_AGE_SECONDS
    result = {"ready": worker_ready, "ready_age": ready_age, "pending": request.exists(), "request_age": request_age,
              "can_clear": bool(request_age is not None and request_age >= SERVER_SETTINGS_STALE_SECONDS and not worker_ready),
              # mt2009 never needed the unified helper for any of this: rates,
              # bot count and map respawns are each their own small
              # restart-on-poll script (m2-rates / m2-botcount / m2-map-regens)
              # that m2-supervise already watches. queue_server_settings()
              # routes respawn changes through m2-map-regens directly on this
              # engine, so the banner below would be describing a gap that
              # does not exist here.
              "engine_handles_directly": ENGINE_MT2009}
    if worker_ready:
        result["message"] = "Helper ustawień serwera jest gotowy."
    elif result["pending"]:
        result["message"] = "Zlecenie nie jest odbierane przez helper gry. Sprawdź instalację integracji; po 10 minutach można usunąć wyłącznie zaległe zlecenie."
    elif ENGINE_MT2009:
        result["message"] = ("Ten silnik (mt2009) nie korzysta ze wspólnego helpera ustawień: "
                             "raty, docelowa liczba botów i respawny na mapach są obsługiwane "
                             "bezpośrednio przez m2-rates / m2-botcount / m2-map-regens w "
                             "kontenerze gry, każdy własnym restartem rdzeni.")
    else:
        # Telling the operator to install something this build never ships is
        # not help, and the warning fired on every visit to the console even
        # though both buttons that matter work without the helper.
        result["message"] = ("Ta wersja serwera nie zawiera silnikowej integracji Sebana, "
                             "więc zmiana respawnów map jest niedostępna. Restart serwera "
                             "i zmiana rat działają normalnie i niczego nie wymagają.")
    return result


RESTART_STALE_SECONDS = 600


def restart_in_flight():
    status = read_rate_status()
    if status.get("state") != "running":
        return False
    try:
        started = int(status.get("time", "0"))
    except (TypeError, ValueError):
        return False
    return 0 < time.time() - started < RESTART_STALE_SECONDS


def queue_server_settings(action, values=None, changes=None):
    """Publish a complete request only while the game-side helper is present."""
    support = server_settings_status()
    if not support["ready"]:
        # The settings helper (integration/m2-server-settings) is not part of
        # this image, so the map respawn half of the console has nothing to
        # carry it out and is refused with the message above. A plain restart,
        # and a rates-only apply, never needed it: the game container has
        # always watched the rates spool, and that is the path both buttons
        # took before 1.38 - refusing them here would put the dead restart
        # button of 1.30.19 back on every install without the helper.
        # An empty respawn field arrives as "reset", for every map, from a
        # form nobody touched - so "no respawn change" is "nothing but resets".
        respawn_changes = {key: value for key, value in (changes or {}).items() if value != "reset"}
        # This used to refuse the whole bundled save the moment ANY map field
        # held a non-empty, non-"reset" value -- including a leftover value
        # from earlier testing that the operator never touched this time
        # around. A rates/bot-count save has nothing to do with respawn and
        # must not be blocked by it; only the respawn half is unavailable
        # without the helper, so that half alone is skipped, with a
        # non-blocking flash instead of refusing the whole restart.
        if restart_in_flight():
            raise FileExistsError("a restart is already under way")
        queue_rate_restart(values if action == "apply" and values else read_rates())
        if changes and ENGINE_MT2009:
            # mt2009 needs no unified helper for this half either: m2-map-regens
            # (docker/game/bin) already rewrites every named map's regen.txt from
            # its own .m2orig snapshot and restarts the cores itself, the same
            # restart-on-poll spool as m2-rates and m2-botcount -- see that
            # script's own header for the whole shape of it. The full `changes`
            # dict is forwarded, resets included: a "reset" is the operator
            # asking for the map's shipped timing back, not a no-op to swallow.
            queue_map_regen_changes(changes)
        elif respawn_changes:
            flash("Zmiana respawnu na mapach wymaga integracji silnikowej Sebana, więc ją pominięto — "
                  "restart z pozostałymi ustawieniami został zlecony.", "warning")
        return
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    request_id = "seban-" + uuid.uuid4().hex
    lines = [f"id={request_id}", f"action={action}", "source=panel"]
    if action == "apply":
        lines.extend(f"{key}={values[key]}" for key in RATE_NAMES)
        lines.extend(f"map_{key}={value}" for key, value in (changes or {}).items())
    temporary = RATES_SPOOL / (request_id + ".new")
    try:
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temporary.chmod(0o660)
        # A hard link is an atomic, exclusive publication on the shared volume.
        os.link(temporary, RATES_SPOOL / "server-settings.request")
    finally:
        temporary.unlink(missing_ok=True)


def queue_map_regen_changes(changes):
    stamp = int(time.time() * 1000)
    request_data = [f"id=seban-map-{stamp}", f"time={int(time.time())}"]
    request_data.extend(f"map_{map_index}={value}" for map_index, value in changes.items())
    RATES_SPOOL.mkdir(parents=True, exist_ok=True)
    temporary = RATES_SPOOL / "map-regens.request.new"
    temporary.write_text("\n".join(request_data) + "\n", encoding="utf-8")
    os.replace(temporary, RATES_SPOOL / "map-regens.request")
    (RATES_SPOOL / "map-regens.status").write_text(
        "state=running\ntime=%s\nmessage=Zapisano zestaw zmian respawnu; rdzenie zostaną ponownie uruchomione.\n" % int(time.time()),
        encoding="utf-8",
    )


def queue_map_regen_change(map_index, action, seconds=None):
    """Backward-compatible single-map queue entry."""
    queue_map_regen_changes({int(map_index): "reset" if action == "reset" else int(seconds)})


def biologist_missions():
    """Known Biologist missions plus names already emitted by the game."""
    names = set(BIOLOGIST_FALLBACK_MISSIONS)
    try:
        discovered = rows("""SELECT DISTINCT szName FROM player.quest
                           WHERE szName REGEXP '^(make_herb_lv[0-9]+|collect_quest_lv[0-9]+)$'""")
        names.update(row["szName"] for row in discovered if row.get("szName"))
    except pymysql.MySQLError:
        pass

    def mission_order(name):
        match = re.search(r"([0-9]+)$", name)
        return (int(match.group(1)) if match else 0, name)

    return tuple(sorted(names, key=mission_order))


# ---------------------------------------------------------------------------
# What makes a character a bot, in one place instead of eight.
#
# The name used to be the test: everything this project creates is called
# bot<something>, so `name LIKE 'bot%'` found them all. Rename them - which is
# exactly what the Discord keeps asking for, human nicknames instead of
# botarek7 - and every ranking, the live map, the world statistics and the
# season page quietly stop counting them.
#
# The core never asks the name. CPlayerBotManager::LoadRegisteredBots accepts a
# character only when its account login is exactly playerbot_NNN, and renaming a
# character does not touch an account login. So that is what is asked here too,
# with the old name test kept beside it, so a hand-made bot on an ordinary
# account stays visible exactly as before.
#
# The classic panel has had this since it was bitten by the same thing; this is
# the same predicate, spelled for the aliases these queries use.
def bot_identity(alias="p"):
    ref = (alias + ".") if alias else ""
    return ("(EXISTS (SELECT 1 FROM account.account ba"
            " WHERE ba.id = " + ref + "account_id"
            " AND LEFT(ba.login, 10) = 'playerbot_')"
            " OR " + ref + "name LIKE 'bot%%')")


BOT_IS = bot_identity("p")
BOT_IS_BARE = bot_identity("")


def include_real_players_in_rankings():
    """/manage toggle: rankingi/leaderboardy licza tylko playerboty domyslnie,
    albo kazda postac (w tym prawdziwych graczy) gdy operator to wlaczy --
    zgloszone przez gracza NerrVoVy na Discordzie, 2026-09-15, zeby granie
    obok botow bylo bardziej immersyjne."""
    row = one("SELECT value FROM common.m2_switches WHERE name='include_real_players_in_rankings'")
    return str(row.get("value", "0")) == "1"


def write_include_real_players_in_rankings(enabled):
    rows(
        "INSERT INTO common.m2_switches (name, value) VALUES ('include_real_players_in_rankings', %s) "
        "ON DUPLICATE KEY UPDATE value = VALUES(value)",
        ("1" if enabled else "0",),
    )


def read_announce_plus9_refines():
    """/manage toggle: server-wide gold announcement (same notice_all() /b
    uses) when a real player upgrades something to +9. Never for bots --
    they refine to +9 constantly, that would be pure spam. The collector
    polls for this switch and queues the actual notice_all() call through
    web_admin.quest; see collector.py's check_plus9_refines()."""
    row = one("SELECT value FROM common.m2_switches WHERE name='announce_plus9_refines'")
    return str(row.get("value", "0")) == "1"


def write_announce_plus9_refines(enabled):
    rows(
        "INSERT INTO common.m2_switches (name, value) VALUES ('announce_plus9_refines', %s) "
        "ON DUPLICATE KEY UPDATE value = VALUES(value)",
        ("1" if enabled else "0",),
    )


def ranking_scope_sql(alias="p"):
    """The WHERE-clause predicate for 'who counts' in rankings/leaderboards
    (NOT the same question as economy stats, which already count everyone,
    or the teleport-me human lookup, which always means real characters).
    With real players included, the installer's seeded admin/test account
    (Admin/AdminNinja/AdminSura/AdminSzaman, 500M gold each -- see the same
    exclusion for "yang w obiegu") would otherwise top every single
    category and bury any actual player under it."""
    if include_real_players_in_rankings():
        ref = (alias + ".") if alias else ""
        return ref + "name NOT IN ('[SA]Admin','Test','Admin','AdminNinja','AdminSura','AdminSzaman')"
    return bot_identity(alias)


def cached_dashboard_ranking(kind, limit=10, ttl=300):
    """Throttled cache for the three bot_ranking() kinds the dashboard
    carousel calls that turned out to be genuinely expensive: full
    all-time aggregates over 200-300K log rows with no useful index for
    the GROUP BY (refine: ~1.3s, fish: ~1.0s, refine_rate: ~1.8s --
    measured live, 2026-09-25, confirmed via EXPLAIN as "Using temporary;
    Using filesort" over the whole matching set every time). Together
    these were most of the dashboard's ~5-6s load time.

    Same throttle-and-serve-stale pattern as sync_news_events(), just
    simpler (a pure read-through cache, not an incremental scan) since
    recomputing from scratch is cheap to express even if slow to run --
    stored as JSON in web_seban_settings, refreshed by whichever request
    is first past the ttl window. /rankings itself still calls
    bot_ranking() directly and stays live; only the dashboard's top-10
    carousel reads through this cache.
    """
    name = f"dash_rank_cache_{kind}"
    try:
        row = one("SELECT value FROM player.web_seban_query_cache WHERE name=%s", (name,))
        if row and row.get("value"):
            payload = json.loads(row["value"])
            if time.time() - payload.get("at", 0) < ttl:
                return payload["rows"]
    except (pymysql.MySQLError, ValueError, KeyError):
        pass
    data = bot_ranking(kind)[:limit]
    try:
        rows("REPLACE INTO player.web_seban_query_cache (name,value) VALUES (%s,%s)",
             (name, json.dumps({"at": time.time(), "rows": data}, default=str)))
    except pymysql.MySQLError:
        pass
    return data


def bot_ranking(kind, sort_by="avg"):
    base = ranking_scope_sql("p")
    if kind == "gold":
        return rows(f"SELECT p.id,p.name,p.level,p.gold,CONCAT(FORMAT(p.gold,0),' Yang') AS detail FROM player.player p WHERE {base} ORDER BY p.gold DESC,p.level DESC LIMIT 100")
    if kind in ("weapon", "armor"):
        # Ranking a weapon/armor purely by its "+N" step (old: MOD(vnum,10))
        # let a +9 starter-tier item outrank a +7 endgame-tier one, because
        # refine level and item tier live in the same vnum without any
        # weighting between them. item_proto's own attack/defense value
        # columns turned out to be inconsistently authored across families
        # (checked live: some armor lines scale value1 with the refine step
        # baked in, most don't -- e.g. Zbr. Płyt. Tygrysa is flat 29 from +0
        # to +9), so they can't be trusted as a power proxy either.
        # limitvalue0 (the item's required character level, limittype0=1)
        # turned out to be reliable and monotonic with real tier across
        # every family checked -- score = tier*10 + refine step puts a
        # level-34 +7 armor above an level-18 +9 one, matching what the
        # operator asked for, 2026-09-26.
        pos = 4 if kind == "weapon" else 0
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,
            CONCAT(COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)),' (wymagany poziom ',COALESCE(CASE WHEN ip.limittype0=1 THEN ip.limitvalue0 WHEN ip.limittype1=1 THEN ip.limitvalue1 END,0),')') AS detail,
            COALESCE(CASE WHEN ip.limittype0=1 THEN ip.limitvalue0 WHEN ip.limittype1=1 THEN ip.limitvalue1 END,0)*10+MOD(COALESCE(i.vnum,0),10) AS power_score
            FROM player.player p LEFT JOIN player.item i ON i.owner_id=p.id AND i.window='EQUIPMENT' AND i.pos={pos}
            LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum WHERE {base}
            ORDER BY power_score DESC,i.vnum DESC,p.level DESC LIMIT 100""")
    if kind == "weapon30":
        weapon30_order = {
            "avg": "avg_damage DESC, skill_damage DESC, p.level DESC",
            "skill": "skill_damage DESC, avg_damage DESC, p.level DESC",
            "upgrade": "MOD(i.vnum,10) DESC, avg_damage DESC, skill_damage DESC, p.level DESC",
        }.get(sort_by, "avg_damage DESC, skill_damage DESC, p.level DESC")
        # avg_damage czyta APPLY_NORMAL_HIT_DAMAGE_BONUS (72), a
        # skill_damage APPLY_SKILL_DAMAGE_BONUS (71) - tak, jak nazywa je
        # common/length.h. Do 1.33.0 aliasy byly odwrotne, wiec ORDER BY
        # wybieral pierwsza setke po niewlasciwej kolumnie i poprawianie
        # samego sortowania w Pythonie nic by nie dalo.
        result = rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS item_name,
            IF(GREATEST(CASE WHEN i.attrtype0={ATTR_SKILL_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_SKILL_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_SKILL_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_SKILL_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_SKILL_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_SKILL_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_SKILL_DAMAGE} THEN i.attrvalue6 ELSE -999 END)=-999,0,GREATEST(CASE WHEN i.attrtype0={ATTR_SKILL_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_SKILL_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_SKILL_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_SKILL_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_SKILL_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_SKILL_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_SKILL_DAMAGE} THEN i.attrvalue6 ELSE -999 END)) AS skill_damage,
            IF(GREATEST(CASE WHEN i.attrtype0={ATTR_AVG_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_AVG_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_AVG_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_AVG_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_AVG_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_AVG_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_AVG_DAMAGE} THEN i.attrvalue6 ELSE -999 END)=-999,0,GREATEST(CASE WHEN i.attrtype0={ATTR_AVG_DAMAGE} THEN i.attrvalue0 ELSE -999 END,CASE WHEN i.attrtype1={ATTR_AVG_DAMAGE} THEN i.attrvalue1 ELSE -999 END,CASE WHEN i.attrtype2={ATTR_AVG_DAMAGE} THEN i.attrvalue2 ELSE -999 END,CASE WHEN i.attrtype3={ATTR_AVG_DAMAGE} THEN i.attrvalue3 ELSE -999 END,CASE WHEN i.attrtype4={ATTR_AVG_DAMAGE} THEN i.attrvalue4 ELSE -999 END,CASE WHEN i.attrtype5={ATTR_AVG_DAMAGE} THEN i.attrvalue5 ELSE -999 END,CASE WHEN i.attrtype6={ATTR_AVG_DAMAGE} THEN i.attrvalue6 ELSE -999 END)) AS avg_damage
            FROM player.item i JOIN player.player p ON p.id=i.owner_id LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum
            WHERE {base} AND ((i.vnum BETWEEN 290 AND 299) OR (i.vnum BETWEEN 1170 AND 1179) OR (i.vnum BETWEEN 2150 AND 2159) OR (i.vnum BETWEEN 3210 AND 3219) OR (i.vnum BETWEEN 5110 AND 5119) OR (i.vnum BETWEEN 7160 AND 7169))
            ORDER BY {weapon30_order} LIMIT 100""")
        # 71 is APPLY_SKILL_DAMAGE_BONUS and 72 is APPLY_NORMAL_HIT_DAMAGE_BONUS in
        # common/length.h, and the query names them so. A swap used to live
        # here, justified by "this build stores them the other way round" -
        # it does not, and the ranking showed the two columns exchanged.
        return sorted(
            result,
            key=lambda row: (
                (int(row.get("avg_damage") or 0), int(row.get("skill_damage") or 0), int(row.get("level") or 0)) if sort_by == "avg" else
                (int(row.get("skill_damage") or 0), int(row.get("avg_damage") or 0), int(row.get("level") or 0)) if sort_by == "skill" else
                (int(row.get("vnum") or 0) % 10, int(row.get("avg_damage") or 0), int(row.get("skill_damage") or 0), int(row.get("level") or 0))
            ),
            reverse=True,
        )
    if kind == "playtime":
        return rows(f"SELECT p.id,p.name,p.level,p.gold,p.playtime AS score,CONCAT(FLOOR(p.playtime/60),' h') AS detail FROM player.player p WHERE {base} ORDER BY p.playtime DESC,p.level DESC LIMIT 100")
    if kind == "bosses":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(*) AS score,
            CONCAT(COUNT(*),' zabitych bossów · 7 dni') AS detail
            FROM log.log l JOIN player.player p ON p.id=l.who
            WHERE {base} AND l.how='BOSS_KILL' AND l.time >= NOW() - INTERVAL 7 DAY
            GROUP BY p.id,p.name ORDER BY score DESC,p.level DESC,p.name LIMIT 100""")
    if kind == "refine":
        # Same REFINE SUCCESS count character_stat_summary() already shows
        # on /player/ as "Pomyślne ulepszenia" -- all-time, not windowed,
        # so this ranking's numbers line up with that page's.
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(*) AS score,
            CONCAT(COUNT(*),' pomyślnych ulepszeń') AS detail
            FROM log.log l JOIN player.player p ON p.id=l.who
            WHERE {base} AND l.how='REFINE SUCCESS'
            GROUP BY p.id,p.name ORDER BY score DESC,p.level DESC,p.name LIMIT 100""")
    if kind in SPECIAL_FLAG_RANKINGS:
        # player.player_special_flag -- the same table character_stat_summary()
        # reads for /player/'s "Statystyki (panel Y)" section (found 2026-09-23,
        # see that function's docstring for the full trace to CHARACTER::
        # AddPlayerStat). All-time, exact -- not a 7-day log.log window like
        # "bosses"/"refine" above, so these numbers match /player/ 1:1.
        flag, unit = SPECIAL_FLAG_RANKINGS[kind]
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,f.value AS score,
            CONCAT(FORMAT(f.value,0),' {unit}') AS detail
            FROM player.player_special_flag f JOIN player.player p ON p.id=f.pid
            WHERE {base} AND f.flag=%s AND f.value>0
            GROUP BY p.id,p.name,f.value ORDER BY f.value DESC,p.level DESC,p.name LIMIT 100""", (flag,))
    if kind == "fish":
        # log.fish_log -- a dedicated table the engine writes to on every
        # catch (LogManager::FishLog, called from pc_fishing_log() in
        # questlua_pc.cpp, itself called from fishing.lua's pc.fishing_log()
        # right after a successful catch). Missed in the original "does this
        # engine track fishing at all" audit because that only checked
        # log.log's `how` column, which genuinely has no fishing entry --
        # this is a separate table entirely. Confirmed live 2026-09-22: 5557
        # real rows, player_id joins cleanly to player.player.id.
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,SUM(fl.count) AS score,
            CONCAT(SUM(fl.count),' złowionych ryb') AS detail
            FROM log.fish_log fl JOIN player.player p ON p.id=fl.player_id
            WHERE {base}
            GROUP BY p.id,p.name ORDER BY score DESC,p.level DESC,p.name LIMIT 100""")
    if kind == "refine_rate":
        # Ciekawostka, per operator's ask: % success needs a minimum sample
        # size, or a bot's very first-ever refine lands it at #1 forever
        # having never tried again. 20 attempts is comfortably above that.
        # Failure here is REMOVE (REFINE FAIL), not 'REFINE FAIL' -- checked
        # live for pid 84 (314 SUCCESS / 62 REMOVE (REFINE FAIL), matching
        # the 83.x% the operator saw on /player/): this engine has zero
        # 'REFINE FAIL' rows at all, every failed refine burns the item and
        # is logged only as the burn event.
        min_attempts = 20
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,
            ROUND(100*SUM(l.how='REFINE SUCCESS')/COUNT(*),1) AS score,
            CONCAT(ROUND(100*SUM(l.how='REFINE SUCCESS')/COUNT(*),1),'%% (',SUM(l.how='REFINE SUCCESS'),'/',COUNT(*),' ulepszeń)') AS detail
            FROM log.log l JOIN player.player p ON p.id=l.who
            WHERE {base} AND l.how IN ('REFINE SUCCESS','REMOVE (REFINE FAIL)')
            GROUP BY p.id,p.name HAVING COUNT(*) >= {min_attempts}
            ORDER BY score DESC,COUNT(*) DESC,p.level DESC LIMIT 100""")
    if kind == "items":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(i.id) AS score,CONCAT(COUNT(i.id),' przedmiotów') AS detail
            FROM player.player p LEFT JOIN player.item i ON i.owner_id=p.id AND i.window='INVENTORY'
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""")
    if kind == "horse":
        return rows(f"SELECT p.id,p.name,p.level,p.gold,p.horse_level AS score,CONCAT('Koń Lv ',p.horse_level) AS detail FROM player.player p WHERE {base} ORDER BY p.horse_level DESC,p.level DESC LIMIT 100")
    if kind == "biologist":
        missions = biologist_missions()
        marks = ",".join(["%s"] * len(missions))
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,COUNT(DISTINCT q.szName) AS score,CONCAT(COUNT(DISTINCT q.szName),' / {len(missions)} misji') AS detail
            FROM player.player p LEFT JOIN player.quest q ON q.dwPID=p.id AND q.szName IN ({marks}) AND q.szState='__status' AND q.lValue=%s
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""", (*missions, BIOLOGIST_COMPLETE_STATE))
    if kind == "hunting":
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,MAX(CASE WHEN q.szState='complete' THEN q.lValue ELSE 0 END) AS score,
            CONCAT('Ukończone do Lv ',MAX(CASE WHEN q.szState='complete' THEN q.lValue ELSE 0 END)) AS detail
            FROM player.player p LEFT JOIN player.quest q ON q.dwPID=p.id AND q.szName='levelup'
            WHERE {base} GROUP BY p.id ORDER BY score DESC,p.level DESC LIMIT 100""")
    if kind == "shops":
        keeper_ids = [pid for pid, state in live_statuses().items() if int(state.get("action") or 0) == 13]
        if not keeper_ids:
            return []
        placeholders = ",".join(["%s"] * len(keeper_ids))
        return rows(f"SELECT p.id,p.name,p.level,p.gold,'Stragan otwarty' AS detail FROM player.player p WHERE p.id IN ({placeholders}) ORDER BY p.level DESC LIMIT 100", keeper_ids)
    if kind == "skills":
        # Kazdy bot z profesja, a nie czterysta najwyzszych poziomem.
        # Ranking umiejetnosci posortowany najpierw po poziomie odpowiada
        # na inne pytanie: bot z trzydziestki z mistrzowska umiejetnoscia
        # stal pod czterystoma piecdziesiatkami bez zadnej i nie pokazywal
        # sie wcale. Punktowanie i tak jest w Pythonie, bo skill_level to
        # blob, wiec caly zbior musi wrocic.
        roster = rows(f"SELECT p.id,p.name,p.level,p.gold,p.job,p.skill_group,p.skill_level FROM player.player p WHERE {base} AND p.skill_group>0 ")
        for bot in roster:
            best = max(parse_skills(bot.get("skill_level"), bot.get("job"), bot.get("skill_group")), key=lambda skill: (3 if skill["rank"] == "P" else 2 if skill["rank"].startswith("G") else 1 if skill["rank"].startswith("M") else 0, skill["level"]), default=None)
            bot["score"] = (3 if best and best["rank"] == "P" else 2 if best and best["rank"].startswith("G") else 1 if best and best["rank"].startswith("M") else 0, best["level"] if best else 0)
            bot["detail"] = f"{best['name']} · {best['rank']}" if best else "Brak rozwiniętych umiejętności"
        return sorted(roster, key=lambda bot: (bot["score"], bot["level"]), reverse=True)[:100]
    if kind == "plus9":
        # Ktore vnumy sa sprzetem, rozstrzyga item_proto, a nie liczba:
        # "ponizej 12000" mialo odsiac materialy, a odsiewalo kazda tarcze
        # (13xxx) i cala bizuterie razem z nimi. type 1 to ITEM_WEAPON,
        # 2 to ITEM_ARMOR - dokladnie ten zbior, ktorego lancuch ulepszen
        # biegnie base+0..9.
        # window musi byc ograniczone do EQUIPMENT/INVENTORY: w SAFEBOX
        # owner_id to id KONTA, nie postaci (magazyn dzielony miedzy
        # postaciami), wiec bez tego warunku przedmiot ze skrytki trafial
        # do rankingu tej postaci, ktorej id przypadkiem zbieglo sie z
        # id konta wlasciciela skrytki.
        return rows(f"""SELECT p.id,p.name,p.level,p.gold,i.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',i.vnum)) AS detail
            FROM player.item i JOIN player.player p ON p.id=i.owner_id LEFT JOIN player.item_proto ip ON ip.vnum=i.vnum
            WHERE {base} AND i.window IN ('EQUIPMENT','INVENTORY') AND ip.type IN (1,2) AND MOD(i.vnum,10)=9 ORDER BY i.vnum DESC,p.level DESC LIMIT 100""")
    return rows(f"SELECT p.id,p.name,p.level,p.gold,p.level AS score,'Poziom' AS detail FROM player.player p WHERE {base} ORDER BY p.level DESC,p.exp DESC LIMIT 100")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        current = settings()
        if current.get("setup_complete") != "1":
            return redirect(url_for("setup"))
        if current.get("auth_enabled") != "1":
            return view(*args, **kwargs)
        if not session.get("seban_admin"):
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


def item_icon_url(vnum):
    try:
        value = int(vnum)
    except (TypeError, ValueError):
        return None
    # Most upgrade series use the same client icon for +0 through +9.
    # Prefer an explicit mapping, then fall back to the base VNUM safely.
    icon = ITEM_ICONS.get(str(value)) or ITEM_ICONS.get(str(value - value % 10))
    return url_for("static", filename=f"icons/{quote(icon)}") if icon else None


@app.context_processor
def globals_for_templates():
    tieru_url = os.environ.get("TIERU_PANEL_URL", "http://127.0.0.1:7788")
    item_icon = item_icon_url
    current_settings = settings()
    def job_name(job):
        return class_profile(job)["name"]
    def class_portrait(job):
        return url_for("static", filename=f"class-portraits/{class_profile(job)['portrait']}")
    def empire_flag(empire):
        flag = empire_flag_path(empire)
        return url_for("static", filename=f"empires/{flag}") if flag else ""
    def static_asset_url(filename):
        # Docker deployments replace static files while browsers may retain an
        # older same-named stylesheet or script. Git preserves file mtimes,
        # therefore use a content digest rather than the timestamp.
        try:
            revision = hashlib.sha256((Path(app.static_folder) / filename).read_bytes()).hexdigest()[:12]
        except OSError:
            revision = 0
        return url_for("static", filename=filename, v=revision)
    return {"tieru_url": tieru_url, "panel_brand": current_settings.get("panel_name", "Metin2 Singleplayer"), "settings": current_settings, "map_name": map_name, "item_icon": item_icon, "job_name": job_name, "class_profile": class_profile, "class_portrait": class_portrait, "empire_info": empire_info, "empire_flag": empire_flag, "static_asset_url": static_asset_url}
@app.route("/login", methods=["GET", "POST"])
def login():
    current = settings()
    if current.get("auth_enabled") != "1":
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        password_hash = current.get("auth_password_hash", "")
        if password_hash and check_password_hash(password_hash, request.form.get("password", "")):
            session.clear()
            session["seban_admin"] = True
            session.permanent = True
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Nieprawidłowe hasło.", "error")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    current = settings()
    if current.get("setup_complete") == "1":
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        values, error = validate_display_settings(request.form)
        password = request.form.get("panel_password", "")
        enable_auth = request.form.get("auth_enabled") == "1"
        if enable_auth and len(password) < 8:
            error = "Hasło panelu musi mieć co najmniej 8 znaków."
        if error:
            flash(error, "error")
        else:
            values.update({"setup_complete": "1", "auth_enabled": "1" if enable_auth else "0", "auth_password_hash": generate_password_hash(password) if enable_auth else ""})
            write_settings(values)
            if enable_auth:
                session["seban_admin"] = True
            flash("Konfiguracja została zapisana.")
            return redirect(url_for("dashboard"))
    return render_template("setup.html", current=current)


@app.route("/")
@login_required
def dashboard():
    totals = one("""
        SELECT
          (SELECT COUNT(*) FROM player.player) AS characters,
          (SELECT COUNT(*) FROM account.account) AS accounts,
          (SELECT COUNT(*) FROM player.item) AS item_stacks,
          (SELECT COALESCE(SUM(gold),0) FROM player.player WHERE name NOT IN ('[SA]Admin','Test','Admin','AdminNinja','AdminSura','AdminSzaman')) AS yang
    """)
    bots = one("SELECT COUNT(*) AS count FROM player.player WHERE account_id BETWEEN 4 AND 1003")
    # The collector creates this table with its first snapshot; before that -
    # the first minutes of a fresh installation - the dashboard has no host
    # metrics to show, not an error to raise.
    try:
        system = one("SELECT * FROM player.web_seban_system_snapshot ORDER BY captured_at DESC LIMIT 1")
    except pymysql.MySQLError:
        system = {}
    map_rows = live_map_counts()
    for row in map_rows:
        row["name"] = map_name(row["map_index"])
    dashboard_channels = discovered_channels()
    # Only built once CH2 (or a future CH3+) is actually running -- on a
    # single-channel server this stays empty and the tile below simply
    # doesn't grow a rotation frame for it.
    channel_map_rows = []
    if len(dashboard_channels) > 1:
        per_channel = {channel: {row["map_index"]: row["character_count"] for row in live_map_counts(channel)} for channel in dashboard_channels}
        top_indexes = sorted(
            {index for counts in per_channel.values() for index in counts},
            key=lambda index: -sum(counts.get(index, 0) for counts in per_channel.values()),
        )[:10]
        for index in top_indexes:
            icon_vnum = MAP_ICON_VNUM.get(index)
            kingdom = MAP_KINGDOM.get(index)
            entry = {"map_index": index, "map_short": map_short_code(index),
                     "icon": item_icon_url(icon_vnum) if icon_vnum else None,
                     "flag": (url_for("static", filename=f"empires/{empire_flag_path(kingdom)}") if kingdom else None)}
            for channel in dashboard_channels:
                entry[f"ch{channel}"] = per_channel[channel].get(index, 0)
            channel_map_rows.append(entry)
    # "Boty według map" tile alternates with this second dataset (JS-driven,
    # see dashboard-charts.js) instead of a 4th tile -- three donut/carousel
    # tiles already fill the row edge-to-edge; a 4th would cramp all of them.
    # Same per-(map,empire) shape as economy_shops()'s by_map, so the exact
    # same flag+map-code bar chart plugin can be reused here, just smaller.
    shop_map_rows = []
    shop_snapshot_latest = one("SELECT MAX(captured_at) AS captured_at FROM player.web_seban_shop_snapshot").get("captured_at")
    if shop_snapshot_latest:
        raw_shop_map = rows("""SELECT map_index, empire, shop_count FROM player.web_seban_shop_snapshot
          WHERE captured_at=%s ORDER BY empire, shop_count DESC""", (shop_snapshot_latest,))
        shop_map_rows = [{"map_index": r["map_index"], "empire": int(r["empire"]), "map_short": map_short_code(r["map_index"]), "shop_count": int(r["shop_count"])} for r in raw_shop_map if int(r["shop_count"]) > 0]
    top = rows("SELECT id, name, level, exp, job, map_index, playtime FROM player.player WHERE " + ranking_scope_sql("") + " ORDER BY level DESC, exp DESC LIMIT 10")
    global_top_id = top[0]["id"] if top else None
    live = live_statuses()
    live_roster = live_bots()
    try:
        bot_guilds = one("""SELECT COUNT(*) AS count FROM player.guild g
                           JOIN player.player p ON p.id=g.master WHERE """ + BOT_IS).get("count", 0)
    except pymysql.MySQLError:
        bot_guilds = 0
    restart_status = read_rate_status()
    restart_time = restart_status.get("time")
    try:
        restart_label = datetime.fromtimestamp(int(restart_time)).strftime("%d.%m.%Y, %H:%M:%S")
    except (TypeError, ValueError, OSError):
        restart_label = "Brak danych"
    release_status = playerbots_release_status()
    world_summary = {
        "bots": len(live_roster),
        "average_level": round(sum(int(bot.get("level") or 0) for bot in live_roster) / len(live_roster), 1) if live_roster else 0,
        "party_bots": sum(1 for bot in live_roster if bot.get("in_party")),
        "max_level": max((int(bot.get("level") or 0) for bot in live_roster), default=0),
        "empire_counts": [{"empire": empire, "name": empire_info(empire)["name"], "flag": empire_flag_path(empire),
                            "count": sum(1 for bot in live_roster if int(bot.get("empire") or 0) == empire)}
                           for empire in (1, 2, 3)],
        "guilds": bot_guilds,
        "last_restart": restart_label,
        "version": release_status["installed"],
        "release": release_status,
        "rates": read_rates(),
        "events": read_events_status(),
    }
    for bot in top:
        if bot["id"] in live:
            bot["map_index"] = live[bot["id"]]["map_index"]
    quick_rankings = []
    quick_rankings.append({"title": "Poziom", "subtitle": "najwyższe poziomy", "items": [{"id": row["id"], "name": row["name"], "value": f"Lv {row['level']}"} for row in top]})
    playtime = bot_ranking("playtime")[:10]
    quick_rankings.append({"title": "Czas gry", "subtitle": "najdłużej online", "items": [{"id": row["id"], "name": row["name"], "value": row["detail"]} for row in playtime]})
    gold = bot_ranking("gold")[:10]
    quick_rankings.append({"title": "Yang", "subtitle": "najwięcej przy postaci", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row.get('gold') or 0):,}".replace(",", " ")} for row in gold]})
    weapon30 = bot_ranking("weapon30")[:10]
    quick_rankings.append({"title": "Broń 30 Lv", "subtitle": "średnie / umiejętności", "items": [{"id": row["id"], "name": row["name"], "value": f"Śr. {int(row.get('avg_damage') or 0)}% · Um. {int(row.get('skill_damage') or 0)}%"} for row in weapon30]})
    metins = rows("""SELECT p.id,p.name,COUNT(*) AS score FROM log.log l JOIN player.player p ON p.id=l.who
                     WHERE """ + ranking_scope_sql("p") + """ AND l.how='STONE_KILL' AND l.time >= NOW() - INTERVAL 7 DAY
                     GROUP BY p.id,p.name ORDER BY score DESC,p.name LIMIT 10""")
    quick_rankings.append({"title": "Metiny", "subtitle": "rozbite · ostatnie 7 dni", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} szt."} for row in metins]})
    bosses = bot_ranking("bosses")[:10]
    quick_rankings.append({"title": "Bossy", "subtitle": "zabite · ostatnie 7 dni", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} szt."} for row in bosses]})
    refine = cached_dashboard_ranking("refine")
    quick_rankings.append({"title": "Pomyślne ulepszenia", "subtitle": "łącznie, całościowo", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} szt."} for row in refine]})
    # "Ryby" used to sit here (LIKE '%ryb%' on log.log.what) and was pulled --
    # that specific check was right (log.log has no fishing `how` at all),
    # but the conclusion drawn from it ("the engine never logs a catch
    # anywhere") was wrong: log.fish_log is a *separate* table the engine
    # writes to on every catch (LogManager::FishLog, log.cpp), missed
    # entirely because nothing was looking for it. Restored once actually
    # found, per operator's ask 2026-09-23.
    fish = cached_dashboard_ranking("fish")
    quick_rankings.append({"title": "Ryby", "subtitle": "wyłowione · łącznie", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score'])} szt."} for row in fish]})
    # player_special_flag-backed rankings (2026-09-23) -- all-time exact
    # totals, matching /player/'s Statystyki (panel Y) section 1:1, unlike
    # the 7-day log.log windows above (Metiny/Bossy).
    damage_max = bot_ranking("damage_max")[:10]
    quick_rankings.append({"title": "Rekord obrażeń", "subtitle": "zwykły atak · najwyższy", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score']):,}".replace(',', ' ')} for row in damage_max]})
    yang_earned = bot_ranking("yang_earned")[:10]
    quick_rankings.append({"title": "Yang zdobyty", "subtitle": "łącznie · nie stan konta", "items": [{"id": row["id"], "name": row["name"], "value": f"{int(row['score']):,}".replace(',', ' ')} for row in yang_earned]})
    refine_rate = cached_dashboard_ranking("refine_rate")
    quick_rankings.append({"title": "Skuteczność ulepszeń", "subtitle": "% sukcesu · min. 20 prób", "items": [{"id": row["id"], "name": row["name"], "value": f"{row['score']}%"} for row in refine_rate]})
    ranking_ids = {item["id"] for ranking in quick_rankings for item in ranking["items"]}
    if ranking_ids:
        placeholders = ",".join(["%s"] * len(ranking_ids))
        jobs_by_id = {row["id"]: row["job"] for row in rows("SELECT id,job FROM player.player WHERE id IN (" + placeholders + ")", list(ranking_ids))}
        for quick_ranking in quick_rankings:
            for item in quick_ranking["items"]:
                item["job"] = jobs_by_id.get(item["id"], 0)
    return render_template("dashboard.html", totals=totals, bots=bots.get("count", 0), system=system, map_rows=map_rows,
                            channel_map_rows=channel_map_rows, dashboard_channels=dashboard_channels, shop_map_rows=shop_map_rows,
                            top=top, global_top_id=global_top_id, quick_rankings=quick_rankings, world_summary=world_summary,
                            panel_version=PANEL_VERSION, latest_changelog=changelog_entries()[:1], live_regen=read_regen_settings(), live_map_regens=read_map_regen_status())
@app.route("/players")
@login_required
def players():
    query = request.args.get("q", "").strip()
    sql = ("SELECT p.id, p.name, p.level, p.job, p.map_index, p.gold, p.playtime, p.last_play, " + EMPIRE_EXPR + " AS empire"
           " FROM player.player p LEFT JOIN player.player_index pi ON pi.id=p.account_id LEFT JOIN account.account a ON a.id=p.account_id")
    args = []
    if query:
        sql += " WHERE p.name LIKE %s OR p.id=%s"
        args = [f"%{query}%", query if query.isdigit() else -1]
    sql += " ORDER BY p.level DESC, p.exp DESC LIMIT 250"
    roster, live = rows(sql, args), live_statuses()
    for character in roster:
        state = live.get(character["id"])
        character["map_live"] = bool(state)
        if state:
            character["map_index"] = state["map_index"]
    return render_template("players.html", players=roster, query=query)


@app.route("/players/personalities")
@login_required
def bot_personalities():
    """Live playerbot roster grouped/filterable by personality
    (BOT_PERSONALITIES -- the base "system osobowości", distinct from the
    newer Iwakura persona/mood layer). Only ever shows bots that are
    currently online: personality, current action and map are all read
    from the live status file, never persisted to the database, so an
    offline bot has none of these to show. Operator's ask, 2026-09-26."""
    query = request.args.get("q", "").strip().lower()
    selected = request.args.get("personality", "").strip()
    roster = live_bots()
    counts = {}
    for bot in roster:
        key = int(bot.get("personality") or 0)
        counts[key] = counts.get(key, 0) + 1
    if query:
        roster = [bot for bot in roster if query in bot["name"].lower()]
    if selected.isdigit() and int(selected) in BOT_PERSONALITIES:
        roster = [bot for bot in roster if int(bot.get("personality") or 0) == int(selected)]
    roster.sort(key=lambda bot: (-(int(bot.get("level") or 0)), -(int(bot.get("exp") or 0))))
    total = len(roster)
    roster = roster[:200]
    for bot in roster:
        bot["experience"] = experience_progress(bot.get("level"), bot.get("exp"))
        bot["map_display"] = map_name(bot.get("map_index"))
        bot["personality_color"] = BOT_PERSONALITY_COLORS.get(int(bot.get("personality") or 0), "#cfe1fb")
    personalities = [{"id": pid, "label": label, "color": BOT_PERSONALITY_COLORS.get(pid, "#cfe1fb"), "count": counts.get(pid, 0)}
                      for pid, label in sorted(BOT_PERSONALITIES.items())]
    return render_template("bot_personalities.html", roster=roster, total=total, query=query, selected=selected, personalities=personalities)


@app.route("/guilds")
@login_required
def guilds():
    query = request.args.get("q", "").strip()
    roster, written_at = guild_statuses()
    if query:
        needle = query.casefold()
        roster = [g for g in roster if needle in g["name"].casefold() or needle in g["master"].casefold()]
    next_wars = {}
    for guild in roster:
        empire, seconds = guild.get("empire", 0), guild.get("next_war_in_s")
        if empire not in EMPIRES or seconds is None:
            continue
        old = next_wars.get(empire)
        if old is None or (seconds >= 0 and (old < 0 or seconds < old)):
            next_wars[empire] = seconds
    summary = {"guilds": len(roster), "online": sum(g["online"] for g in roster),
               "wars": sum(1 for g in roster if g["war_with"]),
               "exp": sum(g["exp_offered"] for g in roster)}
    return render_template("guilds.html", guilds=roster, query=query, summary=summary,
                           next_wars=[{"empire": empire, "text": guild_war_text(seconds)} for empire, seconds in sorted(next_wars.items())],
                           status_written_at=datetime.fromtimestamp(written_at).strftime("%H:%M") if written_at else None)


@app.route("/guild/<int:guild_id>")
@login_required
def guild(guild_id):
    details = one("""SELECT g.id,g.name,g.level,g.exp,g.sp,g.win,g.draw,g.loss,g.ladder_point,g.gold,
                     leader.id AS leader_id,leader.name AS leader_name,leader.level AS leader_level,
                     COUNT(gm.pid) AS member_count
                     FROM player.guild g
                     LEFT JOIN player.player leader ON leader.id=g.master
                     LEFT JOIN player.guild_member gm ON gm.guild_id=g.id
                     WHERE g.id=%s
                     GROUP BY g.id,g.name,g.level,g.exp,g.sp,g.win,g.draw,g.loss,g.ladder_point,g.gold,leader.id,leader.name,leader.level""", (guild_id,))
    if not details:
        abort(404)
    members = rows("""SELECT gm.pid,gm.grade,gm.is_general,gm.offer,p.name,p.level,p.job,p.map_index,p.playtime
                    FROM player.guild_member gm LEFT JOIN player.player p ON p.id=gm.pid
                    WHERE gm.guild_id=%s
                    ORDER BY (gm.pid=%s) DESC,gm.grade ASC,p.level DESC,p.name ASC""", (guild_id, details["leader_id"] or 0))
    return render_template("guild.html", guild=details, members=members)


# kind -> (player_special_flag.flag, unit label for the ranking's "detail"
# column). Shared between bot_ranking()'s SPECIAL_FLAG_RANKINGS branch and
# the /rankings kinds dict -- add a ranking here and it appears both places.
SPECIAL_FLAG_RANKINGS = {
    "damage_max": ("stat_damage", "obrażeń (zwykłe, rekord)"),
    "damage_max_horse": ("stat_damage_horse", "obrażeń (konno, rekord)"),
    "damage_max_skill": ("stat_damage_skill", "obrażeń (umiejętność, rekord)"),
    "yang_earned": ("stat_gold", "Yang zdobytych łącznie"),
    "yang_npc_sale": ("stat_sell_shop", "Yang ze sprzedaży u NPC"),
    "monsters_killed": ("stat_monster", "zabitych potworów łącznie"),
    "minibosses": ("stat_miniboss", "pokonanych minibossów"),
    "pvp_kills_total": ("stat_empire", "pokonanych graczy (wrogie królestwo)"),
    "duel_wins": ("stat_duel", "wygranych pojedynków"),
    "mining": ("stat_mining", "wykopanych rud"),
}


def character_stat_summary(pid):
    """The client's Y-panel ("Statystyki") window, traced to its real
    server-side source -- not log.log, which never held this data (the
    engine's log.log-based guess this function used before 2026-09-23 was
    wrong about several fields being untrackable; it simply hadn't found
    the right table yet).

    Ground truth: the engine has a whole "special flag" persistence system
    (`CHARACTER::AddPlayerStat`/`SetPlayerStat`, game/src/char.cpp) that
    every PLAYER_STATS_* counter goes through on every change
    (char_battle.cpp for kills/deaths/damage records, char_item.cpp for
    refine, mining.cpp for ore, shop_manager.cpp for NPC-shop sales). Each
    call lands in `CHARACTER::SetSpecialFlag` -> `SetSpecialFlagSave` ->
    a `REPLACE INTO player_special_flag (pid, aid, flag, value) ...` in
    db/src/ClientManager.cpp -- i.e. exactly the account/character-scoped,
    login-location-independent server table the operator insisted must
    exist (2026-09-23), found by following AddPlayerStat(...) call sites
    instead of log.log's `how` column.

    Four PLAYER_STATS_* flags are defined in common/length.h and named in
    constants.cpp's GET_SPECIAL_FLAG_KEY, but no file under game/src ever
    calls AddPlayerStat/SetPlayerStat with them -- confirmed dead code on
    this engine build, not a query gap: stat_dungeon (ukończone lochy),
    stat_herbalism (zebrane kwiaty), stat_chest (otwarte skrzynie),
    stat_questbook (ukończone księgi misji). They're simply not returned
    here; character_stats.html explains the gap once, for all four.
    """
    flag_rows = rows("SELECT flag,value FROM player.player_special_flag WHERE pid=%s", (pid,))
    flags = {r["flag"]: int(r["value"] or 0) for r in flag_rows}
    return {
        "monsters": flags.get("stat_monster", 0),
        "bosses": flags.get("stat_boss", 0),
        "minibosses": flags.get("stat_miniboss", 0),
        "metins": flags.get("stat_stone", 0),
        "pvp_kills": flags.get("stat_empire", 0),
        "duel_wins": flags.get("stat_duel", 0),
        "mining": flags.get("stat_mining", 0),
        "fishing": flags.get("stat_fishing", 0),
        "deaths_total": flags.get("stat_death", 0),
        "deaths_by_mob": flags.get("stat_death_mob", 0),
        "pvp_deaths": flags.get("stat_death_player", 0),
        "damage_max": flags.get("stat_damage", 0),
        "damage_max_horse": flags.get("stat_damage_horse", 0),
        "damage_max_skill": flags.get("stat_damage_skill", 0),
        "gold_earned": flags.get("stat_gold", 0),
        "gold_from_shop_sale": flags.get("stat_sell_shop", 0),
        "refine_success": flags.get("stat_refine_success", 0),
        "refine_burned": flags.get("stat_refine_fail_smith", 0),
    }


# Curated subset of log.log's `how` values that make an "equipment history"
# instead of noise: log.log holds thousands of GET/SET_SOCKET/GET_GOLD rows
# per bot, which drowned out the handful of equipment/trade events an
# operator actually wants -- matches Tieru's own /api/bot_gear_history on
# 7788 (audit, 2026-09-14), translated to Polish only (this panel has no
# language switcher).
GEAR_HISTORY_HOWS = {
    "REFINE SUCCESS": ("refine-ok", "Ulepszenie udane"),
    "REFINE FAIL": ("refine-fail", "Ulepszenie nieudane"),
    "REMOVE (REFINE FAIL)": ("burned", "Spalone przy ulepszaniu"),
    "REFINE FISH_ROD SUCCESS": ("refine-ok", "Wędka ulepszona"),
    "REFINE FISH_ROD FAIL": ("refine-fail", "Wędka nieulepszona"),
    "PLAYERBOT_EQUIP": ("equip", "Założone"),
    "PLAYERBOT_GIFT_OUT": ("gift-out", "Podarowane"),
    "PLAYERBOT_GIFT_IN": ("gift-in", "Dostane w prezencie"),
    "PLAYERBOT_STALL_SOLD": ("stall-sold", "Sprzedane na straganie"),
    "SHOP_BUY": ("bought", "Kupione na straganie"),
    "PLAYERBOT_SHOP_SELL": ("vendor", "Sprzedane handlarzowi"),
    "PLAYERBOT_BONUS": ("bonus", "Zużyte na przemianę bonusów"),
    "PLAYERBOT_BONUS_ADD": ("bonus", "Dodano bonus (Wzmocnienie)"),
    "PLAYERBOT_BONUS_CHANGE": ("bonus", "Zmieniono bonusy (Zmiana)"),
    "PLAYERBOT_BONUS_MARBLE": ("bonus", "Dodano 5. bonus (Marmur)"),
    "SAFEBOX PUT": ("safebox", "Do magazynu"),
    "SAFEBOX GET": ("safebox", "Z magazynu"),
    "MOONLIGHT_GET": ("get", "Ze Szkatułki Blasku"),
    "EXCHANGE_TAKE": ("gift-in", "Z wymiany"),
    "EXCHANGE_GIVE": ("gift-out", "Oddane w wymianie"),
}


# Word-boundary match: a name is bounded by space, "=", ":", "[", a bracket
# or line end, never by a letter/digit of its own -- bot names are numbered
# suffixes of a shared stem ("botgrom" must not match "botgrom2"). Ported
# from Tieru's classic panel (admin_panel.py's api_bot_logs), which the
# operator asked to compare our panel against, 2026-09-26.
def bot_debug_logs(name, limit=60, scan_lines=800):
    """Recent syslog lines mentioning this bot's name, across every core.
    Read-only, bounded (scan_lines per file so this never reads full,
    multi-GB syslogs -- same reasoning as scan_bot_chat_logs())."""
    name = (name or "").strip()
    if not name:
        return []
    name_re = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", re.IGNORECASE)
    matched = []
    for channel, path in channel_paths("syslog"):
        try:
            with path.open("rb") as handle:
                handle.seek(0, 2)
                size = handle.tell()
                handle.seek(max(0, size - 4_000_000))
                data = handle.read()
        except OSError:
            continue
        lines = data.decode("cp1250", "replace").splitlines()
        recent = lines[-scan_lines:] if len(lines) > scan_lines else lines
        for line in recent:
            if name_re.search(line):
                matched.append(line.strip())
    return matched[-limit:]


def bot_gear_history(pid, limit=60):
    hows = list(GEAR_HISTORY_HOWS.keys())
    marks = ",".join(["%s"] * len(hows))
    raw = rows(f"""SELECT l.time, l.how, l.hint, l.vnum, i.socket0 FROM log.log l
      LEFT JOIN player.item i ON i.id = l.what
      WHERE l.who=%s AND l.how IN ({marks}) ORDER BY l.time DESC LIMIT %s""", [pid] + hows + [limit])
    result = []
    for r in raw:
        how = game_text(r["how"])
        kind, label = GEAR_HISTORY_HOWS.get(how, ("other", how))
        vnum = int(r["vnum"] or 0)
        socket0 = int(r["socket0"] or 0) if vnum in SKILLBOOK_VNUMS else 0
        hint = game_text(r["hint"]).strip()
        detail = ""
        if how == "PLAYERBOT_GIFT_OUT":
            detail = "→ " + hint
        elif how == "PLAYERBOT_GIFT_IN":
            detail = "← " + hint
        elif how == "PLAYERBOT_STALL_SOLD":
            match = SALE_HINT_RE.match(hint)
            if match:
                detail = f"x{match.group(2)} za " + "{:,}".format(int(match.group(3))).replace(",", " ") + " yang"
        elif how == "PLAYERBOT_EQUIP":
            parts = hint.split()
            if len(parts) >= 4 and parts[3].isdigit() and int(parts[3]) > 0:
                detail = "zamiast " + _item_display_name(int(parts[3]))
        elif how in ("SAFEBOX PUT", "SAFEBOX GET"):
            parts = hint.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) > 1:
                detail = "x" + parts[1]
        result.append({
            "time": r["time"].strftime("%d.%m %H:%M") if hasattr(r["time"], "strftime") else str(r["time"]),
            "kind": kind, "label": label,
            "item": _item_display_name(vnum, socket0) if vnum else "",
            "detail": detail,
        })
    return result


def bot_offline_shop(pid):
    """Data straight from IkarusShop's own tables -- there is no separate
    price/listing table for offline shops on this engine (confirmed against
    a live shop while building the /economy/shops feed): ikashop_offlineshop
    is the stall itself (map, x, y, banner name), player.item WHERE
    window='IKASHOP_OFFLINESHOP' is the listing, and each offer's yang price
    lives in that item's own ikashop_data JSON column. Offers get the exact
    same tooltip enrichment (_enrich_items) as the /player/ equipment and
    inventory grids, so the shop window shows the same icon/name/base
    stats/bonuses/socketed stones -- just with a price line added on top.
    pos is laid out by the engine as a 10-wide grid (confirmed against live
    stalls: positions jump 4->10, 14->21 etc, i.e. row breaks every 10), which
    is also what the in-game offline shop window itself displays as."""
    shop = one("SELECT map, x, y, name, is_premium FROM player.ikashop_offlineshop WHERE owner=%s", (pid,))
    if not shop:
        return None
    offers = rows("""SELECT i.id, i.vnum, i.count, i.pos, i.socket0,i.socket1,i.socket2,
        i.attrtype0,i.attrvalue0,i.attrtype1,i.attrvalue1,i.attrtype2,i.attrvalue2,i.attrtype3,i.attrvalue3,i.attrtype4,i.attrvalue4,i.attrtype5,i.attrvalue5,i.attrtype6,i.attrvalue6,
        p.applytype0,p.applyvalue0,p.applytype1,p.applyvalue1,p.applytype2,p.applyvalue2,p.size AS item_size,
        COALESCE(p.locale_name, CONCAT('VNUM ', i.vnum)) AS item_name,
        CAST(JSON_UNQUOTE(JSON_EXTRACT(i.ikashop_data,'$.yang')) AS UNSIGNED) AS price
      FROM player.item i LEFT JOIN player.item_proto p ON p.vnum=i.vnum
      WHERE i.owner_id=%s AND i.window='IKASHOP_OFFLINESHOP' ORDER BY i.pos""", (pid,))
    _enrich_items(offers)
    for offer in offers:
        offer["icon_url"] = item_icon_url(offer["vnum"])
        offer["price"] = int(offer.get("price") or 0)
        offer["col"] = int(offer["pos"] or 0) % 10
        offer["row"] = (int(offer["pos"] or 0) // 10) % 8
    return {
        "name": game_text(shop["name"]) or "Bez nazwy", "map_index": int(shop["map"]), "map_name": map_name(shop["map"]),
        "x": int(shop["x"]), "y": int(shop["y"]), "is_premium": bool(shop["is_premium"]), "offers": offers,
        "total_value": sum(o["price"] * max(1, int(o.get("count") or 1)) for o in offers),
    }


def bot_live_logs(name, limit=80):
    """Tail of the live game core's own syslogs, filtered to lines naming
    this bot -- same source (channelN/*/syslog, across every known channel)
    and word-boundary matching as Tieru's own /api/bot_logs on 7788, so a
    short name doesn't also match a longer sibling's (botgrom vs botgrom2)."""
    if not name:
        return []
    name_re = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", re.IGNORECASE)
    matched = []
    for _channel, path in channel_paths("syslog"):
        try:
            with open(path, "r", encoding="latin-1", errors="ignore") as f:
                lines = f.readlines()
            recent = lines[-800:] if len(lines) > 800 else lines
            matched.extend(line.strip() for line in recent if name_re.search(line))
        except OSError:
            continue
    return matched[-limit:]


@app.route("/api/bot-logs/<int:pid>")
@login_required
def api_bot_logs(pid):
    character = one("SELECT name FROM player.player WHERE id=%s", (pid,))
    if not character:
        return {"ok": False, "logs": []}, 404
    return {"ok": True, "logs": bot_live_logs(character["name"])}


@app.route("/api/admin/teleport-me", methods=["POST"])
@login_required
def api_admin_teleport_me():
    """Moves whichever GM/human character is actually online right now to a
    bot's current position -- same one-click 'teleport me' the operator uses
    on Tieru's panel (7788), reusing the exact queue our own web_admin.quest
    already polls for item/gold grants (see item_grants.py). The panel
    cannot ask the database who is online (last_play only updates on save,
    minutes later), so every recently-active human character gets a queued
    WARP and whichever one is truly in the game answers first; the rest are
    withdrawn immediately so nobody is moved later for a click made now."""
    data = request.get_json(silent=True) or {}
    pid = int(data.get("pid") or 0)
    if data.get("x") and data.get("y"):
        # Explicit coordinates -- e.g. a shop's own stall position, which can
        # outlive the bot going offline (IkarusShop keeps the stall open).
        target_x, target_y = int(data["x"]), int(data["y"])
    else:
        live = live_statuses().get(pid)
        if not live:
            return {"ok": False, "error": "bot_offline"}
        target_x, target_y = int(live["x"]), int(live["y"])
    names = [r["name"] for r in rows(
        "SELECT name FROM player.player WHERE NOT (" + BOT_IS_BARE + ")"
        " AND last_play >= NOW() - INTERVAL 7 DAY ORDER BY last_play DESC LIMIT 8")]
    if not names:
        return {"ok": False, "error": "no_human_player"}
    for name in names:
        rows("INSERT INTO player.web_admin_queue (player_name,cmd,arg1,arg2) VALUES (%s,'WARP',%s,%s)",
             (name, str(target_x), str(target_y)))
    ids = {r["id"]: r["player_name"] for r in rows(
        "SELECT id, player_name FROM player.web_admin_queue WHERE cmd='WARP' AND status='pending'"
        " AND arg1=%s AND arg2=%s AND player_name IN (" + ",".join(["%s"] * len(names)) + ")",
        [str(target_x), str(target_y)] + names)}
    moved, status = None, "timeout"
    deadline = time.time() + 6.0
    while time.time() < deadline and moved is None:
        time.sleep(0.6)
        for r in rows("SELECT id, player_name, status FROM player.web_admin_queue WHERE id IN (" +
                       ",".join(["%s"] * len(ids)) + ")", list(ids.keys())):
            if r["status"] not in ("pending", None):
                moved, status = r["player_name"], r["status"]
                break
    rows("DELETE FROM player.web_admin_queue WHERE status='pending' AND id IN (" +
         ",".join(["%s"] * len(ids)) + ")", list(ids.keys()))
    if moved is None:
        return {"ok": False, "error": "player_offline", "tried": names}
    return {"ok": status == "done", "status": status, "name": moved, "x": target_x, "y": target_y}


def _enrich_items(items):
    """Adds item_name/item_size/base_stats/bonuses/stones to each item dict
    (mutated in place) -- shared by load_character_items() and
    bot_offline_shop() so the equipment/inventory tooltip and the offline
    shop window read the exact same tooltip data from the exact same logic."""
    for item in items:
        item["item_name"] = resolve_item_display_name(item["vnum"], item.get("socket0"), game_text(item["item_name"]))
        item["item_size"] = max(1, min(3, int(item.get("item_size") or 1)))
        item["base_stats"] = item_base_stats(item["vnum"]) + fishing_rod_stats(item["vnum"], item.get("socket0"))
        item["bonuses"] = [apply_text(item.get(f"applytype{i}"), item.get(f"applyvalue{i}")) for i in range(3) if item.get(f"applytype{i}") and item.get(f"applyvalue{i}")]
        item["bonuses"] += [apply_text(item.get(f"attrtype{i}"), item.get(f"attrvalue{i}")) for i in range(7) if item.get(f"attrtype{i}") and item.get(f"attrvalue{i}")]
    # Only weapons (type 1) and armor (type 2) actually use sockets for gems
    # ("kamienie duszy") -- other item types reuse those same DB columns for
    # completely unrelated, type-specific data (a Skill Book's socket0 is the
    # taught skill's vnum, already excluded below by vnum; a fishing rod's
    # socket0/1 held small numbers like 14/35 that happened to collide with
    # real weapon vnums -- 14 is "Miecz+4", 35 is "Sejmitar+5" -- and were
    # shown as if they were socketed gems; a Polymorph Stone's socket0 is the
    # target mob's vnum, handled below via mob_proto instead). Reported
    # ([GA]Seban, 2026-09-22): a Wędka+2's tooltip showing an unrelated
    # "Sejmitar+5" as a gem, same for a Rękawica Króla Przepow.
    stone_eligible_vnums = {int(item["vnum"]) for item in items
                             if int((ITEM_DEFS.get(str(int(item["vnum"] or 0))) or {}).get("type") or 0) in (1, 2)}
    socket_vnums = sorted({int(item.get(f"socket{i}") or 0) for item in items if int(item["vnum"]) in stone_eligible_vnums
                            for i in range(3) if int(item.get(f"socket{i}") or 0) > 0})
    stone_defs = {}
    if socket_vnums:
        marks = ",".join(["%s"] * len(socket_vnums))
        for stone in rows("SELECT vnum,COALESCE(locale_name,CONCAT('VNUM ',vnum)) AS item_name,applytype0,applyvalue0,applytype1,applyvalue1,applytype2,applyvalue2 FROM player.item_proto WHERE vnum IN (" + marks + ")", socket_vnums):
            stone_defs[int(stone["vnum"])] = {"name": game_text(stone["item_name"]), "bonuses": [apply_text(stone.get(f"applytype{i}"), stone.get(f"applyvalue{i}")) for i in range(3) if stone.get(f"applytype{i}") and stone.get(f"applyvalue{i}")]}
    # Polymorph items (type 19, "Marmur Polimorfii" and friends) store the
    # target monster's vnum in socket0 -- show what it actually turns you
    # into instead of silently nothing. Reported alongside the sockets bug
    # above, same day.
    polymorph_vnums = {int(item.get("socket0") or 0) for item in items
                        if int((ITEM_DEFS.get(str(int(item["vnum"] or 0))) or {}).get("type") or 0) == 19
                        and int(item.get("socket0") or 0) > 0}
    mob_names = {}
    if polymorph_vnums:
        marks = ",".join(["%s"] * len(polymorph_vnums))
        for mob in rows("SELECT vnum,COALESCE(locale_name,name) AS mob_name FROM player.mob_proto WHERE vnum IN (" + marks + ")", sorted(polymorph_vnums)):
            mob_names[int(mob["vnum"])] = game_text(mob["mob_name"])
    for item in items:
        vnum = int(item["vnum"] or 0)
        item_type = int((ITEM_DEFS.get(str(vnum)) or {}).get("type") or 0)
        # A Skill Book's socket0 is the taught skill's vnum, not a gem --
        # looking it up in item_proto as a "stone" was matching unrelated
        # items by coincidence (e.g. a sword showing up in a book's tooltip).
        if vnum in SKILLBOOK_VNUMS or item_type not in (1, 2):
            item["stones"] = []
        else:
            item["stones"] = [stone_defs[v] for v in (int(item.get(f"socket{i}") or 0) for i in range(3)) if v in stone_defs]
        item["polymorph_target"] = mob_names.get(int(item.get("socket0") or 0)) if item_type == 19 else None
    return items


def load_character_items(pid, account_id):
    """Equipment + inventory (owner_id=pid) and safebox (owner_id=account_id,
    shared across the account's characters) with names/stats/bonuses/stones
    resolved -- shared by the full /player/ page and the live-refresh
    fragment endpoint so both read the exact same, always-live SQL."""
    items = rows("""
      SELECT i.id, i.vnum, i.count, i.window, i.pos, i.socket0,i.socket1,i.socket2,
      i.attrtype0,i.attrvalue0,i.attrtype1,i.attrvalue1,i.attrtype2,i.attrvalue2,i.attrtype3,i.attrvalue3,i.attrtype4,i.attrvalue4,i.attrtype5,i.attrvalue5,i.attrtype6,i.attrvalue6,
      p.applytype0,p.applyvalue0,p.applytype1,p.applyvalue1,p.applytype2,p.applyvalue2,p.size AS item_size,COALESCE(p.locale_name, CONCAT('VNUM ', i.vnum)) AS item_name
      FROM player.item i LEFT JOIN player.item_proto p ON p.vnum=i.vnum WHERE i.owner_id=%s
      ORDER BY i.window, i.pos LIMIT 250
    """, (pid,))
    safebox = rows("""
      SELECT i.id,i.vnum,i.count,i.window,i.pos,i.socket0,i.socket1,i.socket2,
      i.attrtype0,i.attrvalue0,i.attrtype1,i.attrvalue1,i.attrtype2,i.attrvalue2,i.attrtype3,i.attrvalue3,i.attrtype4,i.attrvalue4,i.attrtype5,i.attrvalue5,i.attrtype6,i.attrvalue6,
      p.applytype0,p.applyvalue0,p.applytype1,p.applyvalue1,p.applytype2,p.applyvalue2,p.size AS item_size,COALESCE(p.locale_name,CONCAT('VNUM ',i.vnum)) AS item_name
      FROM player.item i LEFT JOIN player.item_proto p ON p.vnum=i.vnum WHERE i.owner_id=%s AND i.window='SAFEBOX' ORDER BY i.pos LIMIT 180
    """, (account_id,))
    _enrich_items([*items, *safebox])
    equipment, inventory = {}, []
    # EWearPositions from Server/common/length.h. The database stores these
    # offsets directly in EQUIPMENT (rather than their client offset +90).
    equipment_slots = {
        0: "body", 1: "head", 2: "foots", 3: "wrist", 4: "weapon",
        5: "neck", 6: "ear", 7: "unique1", 8: "unique2", 9: "arrow",
        10: "shield", 23: "belt",
    }
    for item in [*items, *safebox]:
        if item["window"] == "EQUIPMENT" and item["pos"] in equipment_slots:
            equipment[equipment_slots[item["pos"]]] = item
        elif item["window"] == "INVENTORY":
            inventory.append(item)
    # The horse saddlebag ("juki konne") isn't a separate window -- it's the
    # same INVENTORY array, one page further out (pos >= 180, i.e. page index
    # 4 in the pos//45 scheme the regular 4 pages already use). Confirmed
    # against [GA]Seban's own fully-stacked bag: swords (vnum 299, 2 slots
    # tall) and horse medals (vnum 50050) land exactly on the same --col/--row
    # grid math as every other page, including the "gap" row every tall item
    # visually consumes below it -- no separate layout logic needed, just a
    # separate page kept out of the regular Ekwipunek tabs and only shown
    # once a bot/character actually has something in it.
    horse_bag = [item for item in inventory if int(item["pos"] or 0) >= 180]
    inventory = [item for item in inventory if int(item["pos"] or 0) < 180]
    return equipment, inventory, safebox, horse_bag


@app.route("/player/<int:pid>")
@login_required
def player(pid):
    character = one("SELECT p.id,p.account_id,p.name,p.level,p.job,p.exp,p.gold,p.hp,p.mp,p.x,p.y,p.horse_level,p.alignment,p.st,p.ht,p.dx,p.iq,p.stat_point,p.skill_point,p.skill_group,p.skill_level,p.map_index,p.playtime,p.last_play,"
      "a.cash,a.silver_expire,a.gold_expire,a.safebox_expire,a.autoloot_expire,a.fish_mind_expire,a.marriage_fast_expire,a.money_drop_rate_expire,a.shop_expire,a.premium_expire,"
      + EMPIRE_EXPR + " AS empire FROM player.player p LEFT JOIN account.account a ON a.id=p.account_id LEFT JOIN player.player_index pi ON pi.id=p.account_id WHERE p.id=%s", (pid,))
    if not character:
        abort(404)
    live = live_statuses().get(pid)
    if live:
        character.update(live)
        character["personality"] = live_label("personality", live.get("personality"))
        character["ambition"] = live_label("ambition", live.get("ambition"))
        character["goal"] = live_label("goal", live.get("goal"))
        character["action"] = live.get("status") or live_label("action", live.get("action"))
        character["channel_live"] = True
        character["persona"] = BOT_PERSONAS.get(live.get("persona")) if live.get("persona") is not None else None
        character["mood"] = BOT_MOODS.get(live.get("mood")) if live.get("mood") is not None else None
        character["mood_lock"] = BOT_MOOD_LOCKS.get(live.get("mood_lock") or 0)
    else:
        character.update({"personality": "Bot offline", "ambition": "—", "goal": "—", "action": "—"})
        character["channel_live"] = False
        character["persona"] = character["mood"] = character["mood_lock"] = None
        try:
            last_channel = one("SELECT channel FROM player.web_seban_bot_position_snapshot WHERE pid=%s ORDER BY captured_at DESC LIMIT 1", (pid,))
            character["channel"] = int(last_channel["channel"]) if last_channel else None
        except pymysql.MySQLError:
            character["channel"] = None
    character["job_name"] = class_profile(character.get("job"))["name"]
    character["class_profile"] = class_profile(character.get("job"))
    character["experience"] = experience_progress(character.get("level"), character.get("exp"))
    character["honor"] = honor_rank(character.get("alignment"))
    character["honor"]["css"] = {"Rycerski": "knightly", "Szlachetny": "noble", "Dobry": "good", "Przyjazny": "friendly", "Neutralny": "neutral", "Agresywny": "aggressive", "Nieuczciwy": "dishonest", "Złośliwy": "malicious", "Okrutny": "cruel"}[character["honor"]["title"]]
    character["cash"] = int(character.get("cash") or 0)
    # One row per active *_expire column, human label first (see PREMIUM_TYPES)
    # so this always matches what "Nadaj VIP" itself offers -- no separate list
    # of names to keep in sync.
    now = datetime.now()
    character["premiums"] = [
        {"label": label, "expires": character.get(column)}
        for _type, label in PREMIUM_TYPES
        for column in [PREMIUM_COLUMNS[_type]]
        # shop_expire's schema default is the invalid zero-date
        # '0000-00-00 00:00:00', which the driver cannot represent as a
        # datetime and hands back as that literal string instead -- never an
        # active grant, but not directly comparable to `now` either.
        if isinstance(character.get(column), datetime) and character[column] > now
    ]
    character["playtime_hours"] = int(character.get("playtime") or 0) // 60
    character["playtime_minutes"] = int(character.get("playtime") or 0) % 60
    marriage = one("""SELECT p2.name AS partner_name FROM player.marriage m
      JOIN player.player p2 ON p2.id = IF(m.pid1=%s, m.pid2, m.pid1)
      WHERE (m.pid1=%s OR m.pid2=%s) AND m.is_married=1""", (pid, pid, pid))
    character["marriage_partner"] = marriage.get("partner_name") if marriage else None
    guild = one("""SELECT g.name AS guild_name, COALESCE(gg.name, '') AS grade_name FROM player.guild_member gm
      JOIN player.guild g ON g.id=gm.guild_id
      LEFT JOIN player.guild_grade gg ON gg.guild_id=gm.guild_id AND gg.grade=gm.grade
      WHERE gm.pid=%s""", (pid,))
    character["guild_name"] = guild.get("guild_name") if guild else None
    character["guild_grade"] = game_text(guild.get("grade_name")) if guild else None
    character["max_hp"] = max(int(character.get("max_hp") or 0), int(character.get("hp") or 0), 1)
    # The live Playerbots feed exposes exact max HP.  The original server
    # schema does not persist max MP, so an offline character is shown as a
    # current-value bar until it is next observed live.
    character["max_mp"] = max(int(character.get("max_mp") or 0), int(character.get("mp") or 0), 1)
    character["hp_percent"] = min(100, round(int(character.get("hp") or 0) * 100 / character["max_hp"], 1))
    character["mp_percent"] = min(100, round(int(character.get("mp") or 0) * 100 / character["max_mp"], 1))
    skill_raw = character.pop("skill_level", b"")
    character["skills"] = parse_skills(skill_raw, character.get("job"), character.get("skill_group"))
    character["passive_skills"] = parse_passive_skills(skill_raw)
    equipment, inventory, safebox, horse_bag = load_character_items(pid, character["account_id"])
    gear_history = bot_gear_history(pid)
    offline_shop = bot_offline_shop(pid)
    character_stats = character_stat_summary(pid)
    gm_row = one("SELECT mAuthority FROM common.gmlist WHERE mName=%s LIMIT 1", (character["name"],))
    character["gm_rank"] = gm_row["mAuthority"] if gm_row else ""
    return render_template("player.html", character=character, equipment=equipment, inventory=inventory, safebox=safebox,
                            has_safebox=bool(safebox), horse_bag=horse_bag, has_horse_bag=bool(horse_bag),
                            gear_history=gear_history, offline_shop=offline_shop, character_stats=character_stats,
                            gm_ranks=GM_RANK_OPTIONS)


@app.route("/api/player/<int:pid>/inventory-fragment")
@login_required
def api_player_inventory_fragment(pid):
    """Re-renders just the equipment/inventory/safebox/horse-bag markup from
    a fresh SQL read -- polled by player.html so gear changes show up without
    a page reload, the same 'always live, never stale' read the full page uses."""
    account_id = one("SELECT account_id FROM player.player WHERE id=%s", (pid,))
    if not account_id:
        abort(404)
    gold = one("SELECT gold FROM player.player WHERE id=%s", (pid,)).get("gold") or 0
    equipment, inventory, safebox, horse_bag = load_character_items(pid, account_id["account_id"])
    return render_template("_inventory_fragment.html", gold=gold, equipment=equipment, inventory=inventory, safebox=safebox,
                            has_safebox=bool(safebox), horse_bag=horse_bag, has_horse_bag=bool(horse_bag))


# VIP and "Dragon Coins" both turned out to be real, already-working engine
# features, not something this panel needs to invent: CItemShopManager::
# AddVIP (server/game/src/itemshop_manager.cpp) extends one of nine
# account.account "*_expire" columns, and account.cash is the exact balance
# the already-running ItemShop (docker-compose.yml's own comment: "Dragon
# Coins (account.cash) and Dragon Marks (account.mileage)") already spends
# in-game. Granting through the panel writes the same columns the same way
# the game itself does, instead of a parallel panel-only ledger nothing else
# would ever honor.
PREMIUM_TYPES = [
    (8, "Premium (ogólne, VIP)"), (1, "VIP Gold"), (0, "VIP Silver"),
    (2, "Magazyn Premium (Safebox)"), (3, "Auto-loot"), (4, "Umysł Rybaka (Fish Mind)"),
    (5, "Szybkie zaręczyny"), (6, "Bonus dropu Yang"), (7, "Rozszerzony sklep"),
]
PREMIUM_COLUMNS = {
    0: "silver_expire", 1: "gold_expire", 2: "safebox_expire", 3: "autoloot_expire",
    4: "fish_mind_expire", 5: "marriage_fast_expire", 6: "money_drop_rate_expire",
    7: "shop_expire", 8: "premium_expire",
}


def ensure_admin_tables():
    """Lazy-created, admin-only bookkeeping. Not something collected on a
    cycle, so it does not belong in collector.py::init() -- created here on
    first use instead, same CREATE TABLE IF NOT EXISTS idiom."""
    rows("""CREATE TABLE IF NOT EXISTS player.web_seban_deleted_players (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      player_id INT UNSIGNED NOT NULL, player_name VARCHAR(32) NOT NULL,
      snapshot_json LONGTEXT NOT NULL, deleted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      KEY(player_id)) ENGINE=InnoDB""")


@app.route("/player/<int:pid>/action/vip", methods=["POST"])
@login_required
def player_action_vip(pid):
    character = one("SELECT id,name,account_id FROM player.player WHERE id=%s", (pid,))
    if not character:
        abort(404)
    try:
        premium_type = int(request.form.get("premium_type", 8))
        days = int(request.form.get("days", 0))
    except ValueError:
        flash("Nieprawidłowe dane formularza.", "error")
        return redirect(url_for("player", pid=pid))
    if premium_type not in PREMIUM_COLUMNS or not 1 <= days <= 3650:
        flash("Liczba dni musi być w zakresie 1-3650.", "error")
        return redirect(url_for("player", pid=pid))
    column = PREMIUM_COLUMNS[premium_type]
    hours = days * 24
    # Same additive-extend logic as CItemShopManager::AddVIP: a still-active
    # grant is extended from its current expiry, not from now, so this
    # behaves exactly like the character buying it again in-game.
    rows(f"""UPDATE account.account SET {column} = CASE
        WHEN {column} <= NOW() THEN DATE_ADD(NOW(), INTERVAL %s HOUR)
        ELSE DATE_ADD({column}, INTERVAL %s HOUR) END WHERE id=%s""",
        (hours, hours, character["account_id"]))
    label = dict(PREMIUM_TYPES).get(premium_type, column)
    rows("INSERT INTO log.log (type,time,who,how,hint) VALUES ('CHARACTER',NOW(),%s,'PANEL_VIP_GRANT',%s)",
         (pid, f"{label} +{days}d"))
    flash(f"Nadano {label} (+{days} dni) dla {character['name']}.")
    return redirect(url_for("player", pid=pid))


@app.route("/manage/bulk-vip", methods=["POST"])
@login_required
def manage_bulk_vip():
    """Same additive-extend grant as player_action_vip, applied in one UPDATE
    to every playerbot_* account instead of one at a time through the UI --
    asked for after a fresh reseed left ~2500 bots with no VIP at all."""
    try:
        premium_type = int(request.form.get("premium_type", 8))
        days = int(request.form.get("days", 0))
    except ValueError:
        flash("Nieprawidłowe dane formularza.", "error")
        return redirect(url_for("manage"))
    if premium_type not in PREMIUM_COLUMNS or not 1 <= days <= 3650:
        flash("Liczba dni musi być w zakresie 1-3650.", "error")
        return redirect(url_for("manage"))
    column = PREMIUM_COLUMNS[premium_type]
    hours = days * 24
    # rows()/fetchall() would come back empty for an UPDATE -- cur.rowcount
    # is the only way to report how many accounts this actually touched.
    with db() as con:
        with con.cursor() as cur:
            cur.execute(f"""UPDATE account.account SET {column} = CASE
                WHEN {column} <= NOW() THEN DATE_ADD(NOW(), INTERVAL %s HOUR)
                ELSE DATE_ADD({column}, INTERVAL %s HOUR) END
                WHERE login LIKE 'playerbot\\_%%'""", (hours, hours))
            affected = cur.rowcount
    label = dict(PREMIUM_TYPES).get(premium_type, column)
    rows("INSERT INTO log.log (type,time,who,how,hint) VALUES ('SYSTEM',NOW(),0,'PANEL_VIP_GRANT_BULK',%s)",
         (f"{label} +{days}d, all playerbot accounts",))
    flash(f"Nadano {label} (+{days} dni) wszystkim botom ({affected} kont).")
    return redirect(url_for("manage"))


@app.route("/player/<int:pid>/action/coins", methods=["POST"])
@login_required
def player_action_coins(pid):
    character = one("SELECT id,name,account_id FROM player.player WHERE id=%s", (pid,))
    if not character:
        abort(404)
    try:
        amount = int(request.form.get("amount", 0))
    except ValueError:
        flash("Nieprawidłowa liczba.", "error")
        return redirect(url_for("player", pid=pid))
    if not 1 <= amount <= 1_000_000:
        flash("Liczba Smoczych Monet musi być w zakresie 1-1 000 000.", "error")
        return redirect(url_for("player", pid=pid))
    rows("UPDATE account.account SET cash = cash + %s WHERE id=%s", (amount, character["account_id"]))
    rows("INSERT INTO log.log (type,time,who,how,hint) VALUES ('CHARACTER',NOW(),%s,'PANEL_DRAGON_COINS',%s)",
         (pid, f"+{amount}"))
    flash(f"Dodano {amount} Smoczych Monet (account.cash) dla {character['name']}.")
    return redirect(url_for("player", pid=pid))


@app.route("/player/<int:pid>/action/rename", methods=["POST"])
@login_required
def player_action_rename(pid):
    character = one("SELECT id,name FROM player.player WHERE id=%s", (pid,))
    if not character:
        abort(404)
    new_name = request.form.get("new_name", "").strip()
    if not (2 <= len(new_name) <= 24) or not new_name.isalnum():
        flash("Nick musi mieć 2-24 znaki alfanumeryczne.", "error")
        return redirect(url_for("player", pid=pid))
    if one("SELECT id FROM player.player WHERE name=%s LIMIT 1", (new_name,)):
        flash(f"Nick '{new_name}' jest już zajęty.", "error")
        return redirect(url_for("player", pid=pid))
    rows("UPDATE player.player SET name=%s WHERE id=%s", (new_name, pid))
    # No PAUSE/STOP command exists in web_admin_queue's live command set
    # (checked web_admin.quest's cmd branches: ITEM/GOLD/LEVEL/WARP/SPEED/
    # RIDER_*/BULK_* only) to safely quiesce a live bot first, so this is a
    # plain write with an honest warning rather than a half-built pause hook.
    flash(f"Zmieniono nick '{character['name']}' → '{new_name}'. Silnik nie zapisuje nazwy z pamięci "
          f"przy CHARACTER::Save, więc żywa postać/bot NIE powinien cofnąć tej zmiany -- ale jeśli mimo "
          f"to wróci stara nazwa, krótko zrestartuj kanał gry, na którym stoi ta postać.")
    return redirect(url_for("player", pid=pid))


def queue_gm_reload():
    """Ask an online IMPLEMENTOR to run /reload a for us, so a GM grant/removal
    takes effect immediately instead of waiting for the character's next
    login. Same trick Tieru's own classic panel (7788) uses: this engine has
    no admin socket, so nothing can push HEADER_GD_RELOAD_ADMIN to the db
    core directly -- only an in-game /reload a can, and interpret_command()
    runs a queued command as the player who owns it, so only a character
    that already holds IMPLEMENTOR (gm_level 5) can carry it (see the
    GM_RELOAD branch in game/quest/web_admin.quest, already shipped and
    already running -- this just starts using it from this panel too).
    One row per current IMPLEMENTOR; whichever is actually online picks it
    up first, the rest are withdrawn. Returns True only if one actually did
    -- False means "wrote the gmlist row, but nobody was online to push the
    live reload; takes effect at that character's next login instead."""
    names = [r["mName"] for r in rows(
        "SELECT mName FROM common.gmlist WHERE mAuthority='IMPLEMENTOR' LIMIT 8") if r["mName"]]
    if not names:
        return False
    for name in names:
        rows("INSERT INTO player.web_admin_queue (player_name,cmd,arg1,arg2) VALUES (%s,'GM_RELOAD','','')", (name,))
    ids = {r["id"]: r["player_name"] for r in rows(
        "SELECT id, player_name FROM player.web_admin_queue WHERE cmd='GM_RELOAD' AND status='pending'"
        " AND player_name IN (" + ",".join(["%s"] * len(names)) + ")", names)}
    if not ids:
        return False
    done, deadline = False, time.time() + 8.0  # a player timer ticks every 3s
    while time.time() < deadline and not done:
        time.sleep(0.6)
        done = any(r["status"] == "done" for r in rows(
            "SELECT status FROM player.web_admin_queue WHERE id IN (" +
            ",".join(["%s"] * len(ids)) + ")", list(ids.keys())))
    rows("DELETE FROM player.web_admin_queue WHERE status='pending' AND id IN (" +
         ",".join(["%s"] * len(ids)) + ")", list(ids.keys()))
    return done


@app.route("/player/<int:pid>/action/gm-rank", methods=["POST"])
@login_required
def player_action_gm_rank(pid):
    """Nadaje albo odbiera rangę GM istniejącej postaci -- dotąd panel dawał
    to zrobić tylko przy zakładaniu nowego konta (audyt vs /gm na 7788).

    common.gmlist to jedyne źródło prawdy: silnik czyta stamtąd listę GM-ów,
    więc ten wiersz JEST nadaniem rangi. Rdzeń re-czyta listę przy starcie
    oraz przy /reload a -- queue_gm_reload() poniżej prosi o to online
    IMPLEMENTORA automatycznie (ten sam trik co panel Tieru na 7788), więc
    zwykle działa od razu; jeśli akurat nikt z tą rangą nie jest zalogowany,
    zmiana i tak zacznie działać przy najbliższym logowaniu tej postaci.
    """
    rank = (request.form.get("rank", "") or "").strip()
    if rank and rank not in GM_RANK_SET:
        flash("Nieprawidłowa ranga GM.", "error")
        return redirect(url_for("player", pid=pid))
    character = one("SELECT p.name AS name, a.login AS login FROM player.player p "
                     "LEFT JOIN account.account a ON a.id=p.account_id WHERE p.id=%s", (pid,))
    if not character:
        abort(404)
    name, login = character["name"], character["login"] or ""
    with db() as con:
        with con.cursor() as cur:
            # Replace, nie update: mName nie ma unikalnego klucza, więc wiersz
            # z dwoma wpisami dla tej samej postaci trzymałby starą rangę pod spodem.
            cur.execute("DELETE FROM common.gmlist WHERE mName=%s", (name,))
            if rank:
                cur.execute("INSERT INTO common.gmlist (mAccount,mName,mContactIP,mServerIP,mAuthority) "
                            "VALUES (%s,%s,'','ALL',%s)", (login, name, rank))
    label = dict(GM_RANK_OPTIONS).get(rank, rank)
    reloaded = queue_gm_reload()
    verb = "nadana" if rank else "odebrana"
    if reloaded:
        flash(f"Ranga GM „{label}” {verb} postaci {name}. Zadziałało od razu (online IMPLEMENTOR wykonał /reload a)."
              if rank else f"Ranga GM odebrana postaci {name}. Zadziałało od razu (online IMPLEMENTOR wykonał /reload a).")
    elif rank:
        flash(f"Ranga GM „{label}” nadana postaci {name}. Zacznie działać przy najbliższym zalogowaniu tej postaci "
              f"-- żaden IMPLEMENTOR nie był akurat online, żeby wykonać /reload a za nas.")
    else:
        flash(f"Ranga GM odebrana postaci {name}. Postać online zachowa komendy do wylogowania "
              f"-- żaden IMPLEMENTOR nie był akurat online, żeby wykonać /reload a za nas.")
    return redirect(url_for("player", pid=pid))


@app.route("/player/<int:pid>/action/reset-position", methods=["POST"])
@login_required
def player_action_reset_position(pid):
    character = one("SELECT p.id,p.name," + EMPIRE_EXPR + " AS empire FROM player.player p "
                     "LEFT JOIN account.account a ON a.id=p.account_id "
                     "LEFT JOIN player.player_index pi ON pi.id=p.account_id WHERE p.id=%s", (pid,))
    if not character:
        abort(404)
    empire = int(character.get("empire") or 0)
    if empire not in GM_EMPIRE_STARTS:
        flash("Nie udało się ustalić królestwa tej postaci -- pozycja nie została zmieniona.", "error")
        return redirect(url_for("player", pid=pid))
    x, y, map_index = GM_EMPIRE_STARTS[empire]
    rows("UPDATE player.player SET x=%s,y=%s,map_index=%s WHERE id=%s", (x, y, map_index, pid))
    flash(f"Pozycja postaci {character['name']} zresetowana do stolicy {empire_info(empire)['name']}. "
          f"Jeśli to aktywna postać/bot, silnik może to nadpisać przy najbliższym zapisie z pamięci.")
    return redirect(url_for("player", pid=pid))


@app.route("/player/<int:pid>/action/delete", methods=["POST"])
@login_required
def player_action_delete(pid):
    character = one("SELECT * FROM player.player WHERE id=%s", (pid,))
    if not character:
        abort(404)
    confirm_name = request.form.get("confirm_name", "").strip()
    if confirm_name != character["name"]:
        flash("Wpisana nazwa nie zgadza się z nazwą postaci -- nic nie usunięto.", "error")
        return redirect(url_for("player", pid=pid))
    ensure_admin_tables()
    rows("INSERT INTO player.web_seban_deleted_players (player_id,player_name,snapshot_json) VALUES (%s,%s,%s)",
         (pid, character["name"], json.dumps(character, default=str)))
    rows("DELETE FROM player.item WHERE owner_id=%s", (pid,))
    rows("DELETE FROM player.ikashop_offlineshop WHERE owner=%s", (pid,))
    rows("DELETE FROM player.myshop_pricelist WHERE owner_id=%s", (pid,))
    rows("UPDATE player.player_index SET pid1=IF(pid1=%s,0,pid1), pid2=IF(pid2=%s,0,pid2), "
         "pid3=IF(pid3=%s,0,pid3), pid4=IF(pid4=%s,0,pid4), pid5=IF(pid5=%s,0,pid5) WHERE id=%s",
         (pid, pid, pid, pid, pid, character["account_id"]))
    rows("DELETE FROM player.player WHERE id=%s", (pid,))
    flash(f"Postać '{character['name']}' usunięta. Kopia wiersza w web_seban_deleted_players (id postaci {pid}).")
    return redirect(url_for("players"))


@app.route("/economy")
@login_required
def economy():
    query = request.args.get("q", "").strip().lower()
    latest = one("SELECT MAX(captured_at) AS captured_at FROM player.web_seban_item_snapshot").get("captured_at")
    items = []
    if latest:
        items = rows("""
          SELECT s.vnum, s.socket0, s.amount, COALESCE(p.locale_name, CONCAT('VNUM ', s.vnum)) AS item_name
          FROM player.web_seban_item_snapshot s LEFT JOIN player.item_proto p ON p.vnum=s.vnum
          WHERE s.captured_at=%s ORDER BY s.amount DESC
        """, (latest,))
        for item in items:
            item["item_name"] = resolve_item_display_name(item["vnum"], item["socket0"], game_text(item["item_name"]))
        if query:
            items = [item for item in items if query in item["item_name"].lower() or query == str(item["vnum"])]
    trend = rows("""
      SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS captured_at, value FROM player.web_seban_metric_snapshot
      WHERE metric='total_yang' AND captured_at >= NOW() - INTERVAL 7 DAY ORDER BY captured_at
    """)
    return render_template("economy.html", latest=latest, items=items[:500], query=query, trend=trend)


@app.route("/economy/item/<int:vnum>")
@login_required
def economy_item(vnum):
    item = one("SELECT vnum,COALESCE(locale_name,CONCAT('VNUM ',vnum)) AS item_name FROM player.item_proto WHERE vnum=%s", (vnum,)) or {"vnum": vnum, "item_name": f"VNUM {vnum}"}
    item["item_name"] = game_text(item["item_name"])
    history = rows("""SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS captured_at,amount
      FROM player.web_seban_item_snapshot WHERE vnum=%s AND captured_at >= NOW() - INTERVAL 14 DAY ORDER BY captured_at""", (vnum,))
    return render_template("economy_item.html", item=item, history=history)


def _shop_trend(current, previous):
    if previous is None or current == previous:
        return "flat"
    return "up" if current > previous else "down"


def shop_item_market_row(vnum, socket0, shop_latest):
    """Current (or last-known) shop stats for one (vnum, socket0) pair, with a
    trend against the earliest snapshot within the last 24h -- degrades to
    'flat'/no baseline while history is still short, rather than guessing.
    Resolves its own display name (instead of taking one from the caller) so
    that the same vnum -- e.g. 50300, the generic Skill Book -- can come back
    with a different name per socket0."""
    proto = one("SELECT COALESCE(locale_name, CONCAT('VNUM ', vnum)) AS item_name FROM player.item_proto WHERE vnum=%s", (vnum,))
    base_name = game_text(proto["item_name"]) if proto else f"VNUM {vnum}"
    item_name = resolve_item_display_name(vnum, socket0, base_name)
    now_row = one("""SELECT captured_at, offers, total_units, total_value
      FROM player.web_seban_shop_item_snapshot WHERE vnum=%s AND socket0=%s ORDER BY captured_at DESC LIMIT 1""", (vnum, socket0))
    if not now_row:
        return {"vnum": vnum, "socket0": socket0, "item_name": item_name, "on_market": False, "offers": 0,
                "total_units": 0, "avg_price": 0, "last_seen": None,
                "units_trend": "flat", "price_trend": "flat"}
    baseline = one("""SELECT total_units, total_value FROM player.web_seban_shop_item_snapshot
      WHERE vnum=%s AND socket0=%s AND captured_at >= NOW() - INTERVAL 24 HOUR ORDER BY captured_at ASC LIMIT 1""", (vnum, socket0))
    units = int(now_row["total_units"])
    value = int(now_row["total_value"])
    prev_units = int(baseline["total_units"]) if baseline else None
    prev_value = int(baseline["total_value"]) if baseline else None
    prev_avg = round(prev_value / prev_units) if baseline and prev_units else None
    return {
        "vnum": vnum, "socket0": socket0, "item_name": item_name, "offers": int(now_row["offers"]),
        "total_units": units, "avg_price": round(value / units) if units else 0,
        "on_market": now_row["captured_at"] == shop_latest, "last_seen": now_row["captured_at"],
        "units_trend": _shop_trend(units, prev_units),
        "price_trend": _shop_trend(round(value / units) if units else 0, prev_avg),
    }


SALE_HINT_RE = re.compile(r"^(\d+)\s+x(\d+)\s+za\s+(\d+)$")


def map_short_code(index):
    """'Shinsoo M1 - Yongan' -> 'M1'. Every map that ever hosts an offline
    shop follows this naming; falls back to the full name for one that does
    not (a dungeon, say), rather than showing nothing."""
    match = re.search(r"M\d+", MAP_NAMES.get(int(index or 0), ""))
    return match.group(0) if match else map_name(index)


def _item_display_name(vnum, socket0=0):
    proto = one("SELECT COALESCE(locale_name, CONCAT('VNUM ', vnum)) AS item_name FROM player.item_proto WHERE vnum=%s", (vnum,))
    base_name = game_text(proto["item_name"]) if proto else f"VNUM {vnum}"
    return resolve_item_display_name(vnum, socket0, base_name)


def shop_sales_velocity(hours=24, limit=15, only_skillbooks=False):
    """Ranks items by how many times bots actually bought them off a stall in
    the last `hours` (log.log how='PLAYERBOT_STALL_SOLD'), not by what is
    merely listed -- that is what shop_item_market_row() already covers.
    Demand signal for 'which price should go up', per operator's ask.
    log.log itself has no socket0 column, but log.what is the sold item's
    own id, and that row often still exists in player.item (confirmed on
    live data: ~79% over 24h, ~90% within the last hour -- it only
    disappears once a bot actually consumes the book). Joining it back lets
    Skill Book sales split by the taught skill; a sale whose item is
    already gone can't be attributed to any specific skill, so it is
    dropped rather than shown as a 'which price should I raise' row for an
    unknown skill -- that gave no real signal (confirmed with operator: the
    lumped generic row was topping the ranking and telling them nothing
    actionable). only_skillbooks=True narrows the whole query to Skill Book
    vnums, for a dedicated 'top skill books' panel."""
    vnum_filter = " AND l.vnum IN ({})".format(",".join(str(v) for v in SKILLBOOK_VNUMS)) if only_skillbooks else ""
    raw = rows(f"""SELECT l.vnum, l.hint, l.time, i.socket0 FROM log.log l
      LEFT JOIN player.item i ON i.id=l.what
      WHERE l.how='PLAYERBOT_STALL_SOLD' AND l.time >= NOW() - INTERVAL %s HOUR{vnum_filter}""", (hours,))
    cutoff = datetime.now() - timedelta(hours=hours / 2)
    agg = {}
    for r in raw:
        match = SALE_HINT_RE.match(game_text(r["hint"]))
        if not match:
            continue
        vnum, qty, price = int(match.group(1)), int(match.group(2)), int(match.group(3))
        is_skillbook = vnum in SKILLBOOK_VNUMS
        socket0 = int(r["socket0"] or 0) if is_skillbook else 0
        if is_skillbook and socket0 == 0:
            continue
        key = (vnum, socket0)
        a = agg.setdefault(key, {"sales": 0, "units": 0, "revenue": 0,
                                   "recent_units": 0, "recent_revenue": 0, "older_units": 0, "older_revenue": 0})
        a["sales"] += 1
        a["units"] += qty
        a["revenue"] += price
        bucket = "recent" if r["time"] >= cutoff else "older"
        a[f"{bucket}_units"] += qty
        a[f"{bucket}_revenue"] += price
    ranked = sorted(agg.items(), key=lambda kv: kv[1]["sales"], reverse=True)[:limit]
    result = []
    for (vnum, socket0), a in ranked:
        recent_avg = round(a["recent_revenue"] / a["recent_units"]) if a["recent_units"] else None
        older_avg = round(a["older_revenue"] / a["older_units"]) if a["older_units"] else None
        result.append({
            "vnum": vnum, "item_name": _item_display_name(vnum, socket0),
            "sales": a["sales"], "units": a["units"],
            "avg_price": round(a["revenue"] / a["units"]) if a["units"] else 0,
            "per_hour": round(a["sales"] / hours, 1),
            "price_trend": _shop_trend(recent_avg, older_avg) if recent_avg is not None else "flat",
        })
    return result


def recent_shop_sales(limit=10):
    """Last N completed stall sales, newest first. The engine's sale log
    (log.log how='PLAYERBOT_STALL_SOLD') only ever records the seller -- no
    buyer identity exists anywhere for an offline-shop purchase, confirmed
    against a live sample -- so this is honestly a 'who sold what' feed, not
    a two-sided trade feed. Joined to player.item on log.what (the sold
    item's own id) to recover socket0 for Skill Books -- see
    shop_sales_velocity() for the match-rate note."""
    raw = rows("""SELECT l.time, l.who, l.x, l.y, l.vnum, l.hint, i.socket0 FROM log.log l
      LEFT JOIN player.item i ON i.id=l.what
      WHERE l.how='PLAYERBOT_STALL_SOLD' ORDER BY l.time DESC LIMIT %s""", (limit,))
    sales = []
    for r in raw:
        match = SALE_HINT_RE.match(game_text(r["hint"]))
        qty = int(match.group(2)) if match else 1
        price = int(match.group(3)) if match else 0
        socket0 = int(r["socket0"] or 0) if int(r["vnum"]) in SKILLBOOK_VNUMS else 0
        seller = one("""SELECT p.name, pi.empire FROM player.player p
          JOIN player.player_index pi ON pi.id=p.account_id WHERE p.id=%s""", (r["who"],))
        map_index = next((idx for idx, b in MAP_BOUNDS.items()
                           if b[0] <= r["x"] < b[0] + b[2] and b[1] <= r["y"] < b[1] + b[3]), None)
        sales.append({
            "time": r["time"].strftime("%H:%M:%S"), "vnum": r["vnum"], "item_name": _item_display_name(r["vnum"], socket0),
            "icon_url": item_icon_url(r["vnum"]),
            "qty": qty, "price": price,
            "seller": (seller or {}).get("name") or f"pid {r['who']}",
            "seller_id": int(r["who"]),
            "empire": int((seller or {}).get("empire") or 0),
            "map_name": map_name(map_index) if map_index is not None else "—",
        })
    return sales


@app.route("/economy/shops")
@login_required
def economy_shops():
    latest = one("SELECT MAX(captured_at) AS captured_at FROM player.web_seban_shop_snapshot").get("captured_at")
    by_map = []
    empire_totals = {empire: {"shops": 0, "offers": 0, "items": 0, "value": 0} for empire in EMPIRES}
    if latest:
        by_map = rows("""SELECT map_index, empire, shop_count, offer_count, item_count, total_value
          FROM player.web_seban_shop_snapshot WHERE captured_at=%s ORDER BY empire, shop_count DESC""", (latest,))
        for m in by_map:
            m["map_name"] = map_name(m["map_index"])
            m["map_short"] = map_short_code(m["map_index"])
            totals = empire_totals.setdefault(int(m["empire"]), {"shops": 0, "offers": 0, "items": 0, "value": 0})
            totals["shops"] += int(m["shop_count"])
            totals["offers"] += int(m["offer_count"])
            totals["items"] += int(m["item_count"])
            totals["value"] += int(m["total_value"])
    kpi = {
        "shops": sum(t["shops"] for t in empire_totals.values()),
        "offers": sum(t["offers"] for t in empire_totals.values()),
        "items": sum(t["items"] for t in empire_totals.values()),
        "value": sum(t["value"] for t in empire_totals.values()),
        "transactions_total": int(one("SELECT COUNT(*) AS n FROM log.log WHERE how='PLAYERBOT_STALL_SOLD'").get("n") or 0),
        "transactions_24h": int(one("SELECT COUNT(*) AS n FROM log.log WHERE how='PLAYERBOT_STALL_SOLD' AND time >= NOW() - INTERVAL 24 HOUR").get("n") or 0),
    }

    # Same label/series pivot as maps(): one line per empire, values aligned
    # to a shared, appearance-ordered label list, missing points left as gaps
    # (null) rather than false zeros the market never actually hit.
    raw_trend = rows("""SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS label, empire, SUM(total_value) AS total_value
      FROM player.web_seban_shop_snapshot WHERE captured_at >= NOW() - INTERVAL 7 DAY
      GROUP BY captured_at, empire ORDER BY captured_at ASC""")
    trend_labels, trend_values = [], {empire: {} for empire in EMPIRES}
    for row in raw_trend:
        empire = int(row["empire"] or 0)
        if empire not in trend_values:
            continue
        if row["label"] not in trend_labels:
            trend_labels.append(row["label"])
        trend_values[empire][row["label"]] = int(row["total_value"] or 0)
    value_trend = {"labels": trend_labels, "series": [
        {"id": empire, "name": empire_info(empire)["name"],
         "data": [trend_values[empire].get(label) for label in trend_labels]}
        for empire in EMPIRES
    ]}

    shop_latest = one("SELECT MAX(captured_at) AS captured_at FROM player.web_seban_shop_item_snapshot").get("captured_at")
    query = request.args.get("q", "").strip()
    market_items = []
    if query:
        # A search can name an item with zero active offers right now -- look
        # it up regardless of whether it is in today's top ranking, and
        # shop_item_market_row() reports whether it is on the market or was
        # last seen there, rather than silently returning nothing.
        # A generic term can match dozens/hundreds of item_proto rows (e.g.
        # a common Polish word); items that have ever actually shown up in a
        # shop are what the operator is asking about, so they are ranked
        # first instead of getting cut off by LIMIT in plain vnum order.
        candidates = rows("""SELECT ip.vnum, COALESCE(ip.locale_name, CONCAT('VNUM ', ip.vnum)) AS item_name
          FROM player.item_proto ip
          LEFT JOIN (SELECT vnum, MAX(captured_at) AS seen FROM player.web_seban_shop_item_snapshot GROUP BY vnum) h
            ON h.vnum = ip.vnum
          WHERE ip.vnum=%s OR ip.locale_name LIKE %s
          ORDER BY (h.seen IS NOT NULL) DESC, ip.vnum LIMIT 20""",
          (int(query) if query.isdigit() else -1, f"%{query}%"))
        # (vnum, socket0) pairs to look up. A plain item_proto match on the
        # generic Skill Book (50300) is expanded into every specific skill
        # variant this shop history has ever seen; a query is also matched
        # against skill names directly, since item_proto's own locale_name
        # for 50300 is always "Ksiega Umiejetnosci" and can never mention
        # e.g. "Berserk" the way resolve_item_display_name()'s output does.
        keys = []
        for c in candidates:
            if int(c["vnum"]) in SKILLBOOK_VNUMS:
                variants = rows("SELECT DISTINCT socket0 FROM player.web_seban_shop_item_snapshot WHERE vnum=%s", (c["vnum"],))
                keys += [(int(c["vnum"]), int(v["socket0"])) for v in variants]
            else:
                keys.append((int(c["vnum"]), 0))
        query_lower = query.lower()
        for skill_vnum, skill_name in SKILL_NAMES.items():
            if query_lower in skill_name.lower():
                for book_vnum in SKILLBOOK_VNUMS:
                    keys.append((book_vnum, skill_vnum))
        seen_keys = set()
        keys = [k for k in keys if not (k in seen_keys or seen_keys.add(k))][:20]
        market_items = [shop_item_market_row(vnum, socket0, shop_latest) for vnum, socket0 in keys]
    elif shop_latest:
        top_rows = rows("""SELECT s.vnum, s.socket0
          FROM player.web_seban_shop_item_snapshot s
          WHERE s.captured_at=%s ORDER BY s.total_units DESC LIMIT 15""", (shop_latest,))
        market_items = [shop_item_market_row(r["vnum"], r["socket0"], shop_latest) for r in top_rows]

    return render_template("economy_shops.html", latest=latest, by_map=by_map, query=query,
                            empire_totals=empire_totals, kpi=kpi, value_trend=value_trend, market_items=market_items,
                            sales_velocity=shop_sales_velocity(), skillbook_velocity=shop_sales_velocity(limit=5, only_skillbooks=True),
                            recent_sales=recent_shop_sales(10))


@app.route("/api/shop-feed")
@login_required
def api_shop_feed():
    return {"ok": True, "sales": recent_shop_sales(10)}


@app.route("/items")
@login_required
def items_database():
    query = request.args.get("q", "").strip()
    item_type = request.args.get("type", "").strip()
    where, params = [], []
    if query:
        where.append("(p.vnum=%s OR p.locale_name LIKE %s OR p.name LIKE %s)")
        params += [int(query) if query.isdigit() else -1, f"%{query}%", f"%{query}%"]
    if item_type.isdigit():
        where.append("p.type=%s")
        params.append(int(item_type))
    predicate = " WHERE " + " AND ".join(where) if where else ""
    total = one("SELECT COUNT(*) AS count FROM player.item_proto p" + predicate, params).get("count", 0)
    records = rows("SELECT p.vnum,p.name,p.locale_name,p.type,p.subtype,p.size,p.gold,p.shop_buy_price FROM player.item_proto p" + predicate + " ORDER BY p.vnum", params)
    for item in records:
        item["name"] = game_text(item.get("locale_name") or item.get("name"))
    types = rows("SELECT type,COUNT(*) AS count,MIN(vnum) AS icon_vnum FROM player.item_proto GROUP BY type ORDER BY type")
    for category in types:
        index = int(category["type"])
        category["label"] = ITEM_TYPE_NAMES[index] if 0 <= index < len(ITEM_TYPE_NAMES) else f"ITEM_TYPE_{index}"
    return render_template("items.html", items=records, types=types, selected_type=item_type, query=query, total=total)


@app.get("/api/items")
@login_required
def api_items():
    """Debounced AJAX search backing /items -- see items.html's JS.

    The old client-side filter rendered all 6001 item_proto rows (every
    category combined) into the DOM up front, each with its own <img>, and
    re-scanned every single one of those 6001 nodes on every keystroke with
    no debounce -- fine typed fast (the browser drops/coalesces rapid
    `input` events), but typing slowly meant paying that full 6001-node
    scan-and-reflow *and* nothing had lazy-loaded the images either, so the
    browser also kept re-triggering layout for thousands of <img> tags.
    Operator's report, 2026-09-26: browser and PC fans struggling on a
    high-end machine. This now asks the server (which already had the
    fast, indexed vnum/locale_name query the "Szukaj" button used) instead
    of ever touching thousands of DOM nodes client-side.
    """
    query = request.args.get("q", "").strip()
    item_type = request.args.get("type", "").strip()
    where, params = [], []
    if query:
        where.append("(p.vnum=%s OR p.locale_name LIKE %s OR p.name LIKE %s)")
        params += [int(query) if query.isdigit() else -1, f"%{query}%", f"%{query}%"]
    if item_type.isdigit():
        where.append("p.type=%s")
        params.append(int(item_type))
    predicate = " WHERE " + " AND ".join(where) if where else ""
    total = one("SELECT COUNT(*) AS count FROM player.item_proto p" + predicate, params).get("count", 0)
    records = rows("SELECT p.vnum,p.name,p.locale_name,p.type,p.subtype,p.size,p.gold,p.shop_buy_price FROM player.item_proto p" + predicate + " ORDER BY p.vnum LIMIT 500", params)
    for item in records:
        item["name"] = game_text(item.get("locale_name") or item.get("name"))
    count_label = f"{total} przedmiotów" + (" pasuje do wyszukiwania" if query else (" w wybranej kategorii" if item_type else " · pełna lista bez stron"))
    if total > 500:
        count_label += " (pokazano pierwsze 500 — zawęź wyszukiwanie)"
    return {"ok": True, "html": render_template("partials/items_catalog.html", items=records), "count_label": count_label}


CHAT_FEED_TYPES = ("SHOUT", "TRADE")
# Player-originated public messages reach log.chat_log directly.  Playerbots
# broadcast without a client descriptor, so their own public output is
# deliberately written by the engine into each core's syslog instead.
BOT_PUBLIC_CHAT_RE = re.compile(
    r"^(?P<stamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d) :: "
    r"(?:PLAYERBOT_TRADE: shout pid=(?P<trade_pid>\d+) name=(?P<trade_name>\S+) text=\"(?P<trade_text>.*)\""
    r"|PLAYERBOT_SHOUT: pid=(?P<refine_pid>\d+) plus=\d+ text=(?P<refine_text>.*))$"
)


def chat_message_text(value, author=""):
    """Turn the client-decorated ChatLog payload into the message itself.

    The core stores the same formatted string it sends to the client, including
    Metin hyperlink and colour tokens.  The panel already knows the author from
    its own ChatLog column, so retaining that prefix would duplicate the nick.
    """
    text = game_text(value).replace("\x00", "").strip()
    text = re.sub(r"\|c[0-9A-Fa-f]{8}", "", text)
    text = text.replace("|r", "")
    text = re.sub(r"\|H[^|]*\|h([^|]*)\|h", r"\1", text)
    text = re.sub(r"\|[hH]", "", text)
    if author:
        for prefix in (f"[{author}] : ", f"[{author}]: ", f"{author} : ", f"{author}: "):
            if text.startswith(prefix):
                return text[len(prefix):].strip()
    return re.sub(r"^\s*(?:\[[^\]]+\]|[^:]{1,48})\s*:\s*", "", text, count=1).strip() or text


def player_chat_identities(pids):
    if not pids:
        return {}
    marks = ",".join(["%s"] * len(pids))
    query = "SELECT p.id,p.name,p.job," + EMPIRE_EXPR + " AS empire FROM player.player p " \
            "LEFT JOIN player.player_index pi ON pi.id=p.account_id " \
            "LEFT JOIN account.account a ON a.id=p.account_id WHERE p.id IN (" + marks + ")"
    try:
        return {int(row["id"]): row for row in rows(query, list(pids))}
    except Exception:
        app.logger.exception("Nie można odczytać tożsamości autorów czatu botów")
        return {}


CHAT_SCAN_BACKFILL_BYTES = 384_000
CHAT_SCAN_MAX_READ_BYTES = 4_000_000


def scan_bot_chat_logs():
    """Incrementally append new PLAYERBOT_TRADE/PLAYERBOT_SHOUT lines from
    every core's syslog into a persistent table, so a message stays visible
    on /live-chat for as long as the feed wants it to -- not just for as
    long as it happens to still sit inside the syslog's last few hundred KB.

    Root cause of "wiadomości pojawiają się i zaraz znikają" (operator
    report, 2026-09-25): the previous approach re-read a fixed 384 KB tail
    of the *live* syslog on every poll. With ~1200 bots online these files
    grow at roughly 45 KB/s per core (measured live: +223 956 bytes in 5s
    on channel1/game1) -- so a message scrolled out of that 384 KB window
    within about 8 seconds, well inside two 4s poll cycles. There is no
    log rotation to rely on either (checked: no syslog.1/syslog-DATE files
    exist, cores just keep appending to one growing file).

    Fix: track a byte offset per syslog path (web_seban_chat_offset) and on
    each call read only what's been appended since the last read, capped at
    CHAT_SCAN_MAX_READ_BYTES so a long gap (panel restart, etc.) can't turn
    one poll into a multi-hundred-MB read. Matches are stored permanently
    in web_seban_bot_chat_log (pruned to the newest 2000), decoupling what
    /live-chat shows from what still happens to be in the log's tail. First
    scan of a path only backfills the last CHAT_SCAN_BACKFILL_BYTES (same
    window the old code used), not the entire multi-GB history.

    Called from playerbot_public_messages() on every /api/live-chat poll
    (4s cadence) -- no separate background thread/process needed.
    """
    try:
        con = db()
    except pymysql.MySQLError:
        return
    try:
        with con.cursor() as cur:
            offsets = {row["path"]: row["byte_offset"] for row in rows("SELECT path,byte_offset FROM player.web_seban_chat_offset")}
            year = datetime.now().year
            new_rows, updates = [], []
            for channel, path in channel_paths("syslog"):
                key = str(path)
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                start = offsets.get(key, 0)
                if size < start:
                    start = 0  # rotated or truncated since the last scan
                if start == 0 and size > CHAT_SCAN_BACKFILL_BYTES:
                    start = size - CHAT_SCAN_BACKFILL_BYTES
                if size <= start:
                    continue
                read_to = min(size, start + CHAT_SCAN_MAX_READ_BYTES)
                try:
                    with path.open("rb") as handle:
                        handle.seek(start)
                        data = handle.read(read_to - start)
                except OSError:
                    continue
                text = data.decode("cp1250", "replace")
                # Only advance past complete lines -- an in-progress final
                # line (still being written) is picked up on the next poll.
                usable_len = text.rfind("\n") + 1
                if usable_len == 0:
                    continue
                for line in text[:usable_len].splitlines():
                    match = BOT_PUBLIC_CHAT_RE.match(line)
                    if not match:
                        continue
                    groups = match.groupdict()
                    pid = int(groups.get("trade_pid") or groups.get("refine_pid") or 0)
                    if pid <= 0:
                        continue
                    name = groups.get("trade_name") or ""
                    body = groups.get("trade_text") if groups.get("trade_pid") else groups.get("refine_text")
                    body = (body or "").strip()
                    if not body:
                        continue
                    try:
                        when = datetime.strptime(f"{year} {groups['stamp']}", "%Y %b %d %H:%M:%S")
                    except ValueError:
                        continue
                    new_rows.append((channel, pid, name[:64], body[:255], when))
                updates.append((key, start + usable_len))
            if new_rows:
                cur.executemany(
                    "INSERT IGNORE INTO player.web_seban_bot_chat_log (channel,pid,name,message,captured_at) VALUES (%s,%s,%s,%s,%s)",
                    new_rows)
                # /live-chat only ever shows the newest 100 -- keep the table from growing forever
                # (operator's ask 2026-09-25: bounded history, not unlimited retention).
                cur.execute("""DELETE FROM player.web_seban_bot_chat_log WHERE id < (
                    SELECT id FROM (SELECT id FROM player.web_seban_bot_chat_log ORDER BY id DESC LIMIT 1 OFFSET 100) t)""")
            for key, new_offset in updates:
                cur.execute("REPLACE INTO player.web_seban_chat_offset (path,byte_offset) VALUES (%s,%s)", (key, new_offset))
    except pymysql.MySQLError:
        app.logger.exception("Nie można zaktualizować dziennika czatu botów")
    finally:
        con.close()


def playerbot_public_messages(limit=100):
    """Newest public Playerbot broadcasts (Wołaj / refine announcements),
    read from the persistent capture table scan_bot_chat_logs() fills
    incrementally -- see that function's docstring for why this isn't a
    live syslog tail anymore."""
    scan_bot_chat_logs()
    try:
        records = rows("""SELECT channel,pid,name,message,captured_at FROM player.web_seban_bot_chat_log
          ORDER BY captured_at DESC LIMIT %s""", (limit,))
    except pymysql.MySQLError:
        app.logger.exception("Nie można odczytać dziennika czatu botów")
        records = []
    identities = player_chat_identities({r["pid"] for r in records})
    result = []
    for r in records:
        identity = identities.get(r["pid"], {})
        author = game_text(identity.get("name") or r["name"]).strip() or "Nieznany"
        when = r["captured_at"]
        result.append({
            "id": f"bot:{r['pid']}:{when}:{r['message']}",
            "sort_at": when, "time": when.strftime("%H:%M:%S"),
            "type": "SHOUT", "author": author, "message": chat_message_text(r["message"], author),
            "player_id": int(identity.get("id") or r["pid"]), "job": int(identity.get("job") or 0),
            "empire": int(identity.get("empire") or 0),
        })
    return result[-limit:]


def live_chat_messages(limit=100):
    """Newest public player and bot messages from all active MT2009 cores.
    Capped at 100 (operator's ask, 2026-09-25): a bounded, persistent
    history so opening the page at any random moment shows what bots were
    just chatting about, not just whatever shows up from that point on."""
    limit = max(1, min(int(limit or 100), 100))
    query = """
        SELECT c.`where` AS map_index,c.who_id,c.who_name,c.type,
               c.msg,c.`when`,p.id,p.job,""" + EMPIRE_EXPR + """ AS empire
          FROM log.chat_log c
          LEFT JOIN player.player p ON p.id=c.who_id
          LEFT JOIN player.player_index pi ON pi.id=p.account_id
          LEFT JOIN account.account a ON a.id=p.account_id
         WHERE c.type IN ('SHOUT','TRADE')
         ORDER BY c.`when` DESC
         LIMIT %s
    """
    try:
        records = rows(query, [limit])
    except Exception:
        app.logger.exception("Nie można odczytać log.chat_log")
        records = []
    result = []
    for row in records:
        author = game_text(row.get("who_name")).strip() or "Nieznany"
        when = row.get("when")
        result.append({
            "id": f"player:{row.get('who_id', 0)}:{when}:{game_text(row.get('msg'))}",
            "sort_at": when, "time": when.strftime("%H:%M:%S") if hasattr(when, "strftime") else str(when)[11:19],
            "type": row.get("type") if row.get("type") in CHAT_FEED_TYPES else "SHOUT",
            "author": author, "message": chat_message_text(row.get("msg"), author),
            "player_id": int(row.get("id") or row.get("who_id") or 0), "job": int(row.get("job") or 0),
            "empire": int(row.get("empire") or 0),
        })
    # A future source may log the same line by both paths.  The durable id
    # keeps it visible once while preserving chronological ordering.
    unique = {entry["id"]: entry for entry in result + playerbot_public_messages(limit)}
    return sorted(unique.values(), key=lambda entry: entry.get("sort_at") or datetime.min)[-limit:]


@app.get("/live-chat")
@login_required
def live_chat():
    return render_template("live_chat.html", messages=live_chat_messages())


@app.get("/api/live-chat")
@login_required
def api_live_chat():
    return {"ok": True, "html": render_template("partials/live_chat_messages.html", messages=live_chat_messages())}


@app.get("/world-feed")
@login_required
def world_feed():
    return render_template("world_feed.html", events=news_feed_history())


@app.get("/api/world-feed")
@login_required
def api_world_feed():
    before = request.args.get("before") or None
    events = news_feed_history(before=before)
    return {"ok": True, "html": render_template("partials/world_feed_events.html", events=events),
            "next_before": events[-1]["cursor"] if events else None, "has_more": len(events) >= 40}


@app.route("/gm-commands")
@login_required
def gm_commands():
    return render_template("gm_commands.html", commands=GM_COMMANDS)


@app.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    authorities = ("PLAYER", "LOW_WIZARD", "GOD", "HIGH_WIZARD", "IMPLEMENTOR")
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()[:120]
        empire = max(1, min(3, int(request.form.get("empire", 1) or 1)))
        authority = request.form.get("authority", "PLAYER")
        gm_name = request.form.get("gm_name", "").strip()
        deletion_code = request.form.get("deletion_code", "").strip()
        try:
            gm_job = int(request.form.get("gm_job", 0) or 0)
        except ValueError:
            gm_job = -1
        gm_gender = request.form.get("gm_gender", "classic")
        # account.login is varchar(16) on mt2009 and varchar(30) on r40250; a
        # longer one is "Data too long" from the database, not a form error.
        login_max = 16 if ENGINE_MT2009 else 30
        if not (3 <= len(login) <= login_max and login.replace("_", "").isalnum() and len(password) >= 6 and authority in authorities):
            flash(f"Login ma mieć 3–{login_max} znaków (litery, cyfry, _), a hasło minimum 6 znaków.", "error")
        elif not (deletion_code.isdigit() and len(deletion_code) == 7):
            flash("Kod usunięcia postaci ma zawierać dokładnie 7 cyfr.", "error")
        elif authority != "PLAYER" and not re.fullmatch(GM_NAME_PATTERN, gm_name):
            flash("Nick postaci GM ma mieć 2–24 znaki. Dozwolony jest też jeden prefiks, np. [GM]Seban lub [GA]Seban.", "error")
        elif authority != "PLAYER" and gm_job not in dict(GM_JOB_OPTIONS):
            flash("Wybierz poprawną klasę postaci GM.", "error")
        elif authority != "PLAYER" and gm_gender not in dict(GM_GENDER_OPTIONS):
            flash("Wybierz prawidłową płeć postaci GM.", "error")
        else:
            account_id = None
            player_id = None
            try:
                with db() as con:
                    with con.cursor() as cur:
                        if authority != "PLAYER":
                            cur.execute("SELECT id FROM player.player WHERE name=%s LIMIT 1", (gm_name,))
                            if cur.fetchone():
                                raise ValueError("Taki nick postaci już istnieje.")
                        con.begin()
                        # The mt2009 account table has no empire column (the kingdom
                        # lives in player_index, written below for a GM character and
                        # by the game itself for a player's first character); naming
                        # it refused every account on the 2.x line ("Unknown column
                        # 'empire' in 'INSERT INTO'", NieBijOddam, 11 September).
                        if ENGINE_MT2009:
                            cur.execute("INSERT INTO account.account (login,password,social_id,email,status) VALUES (%s,PASSWORD(%s),%s,%s,'OK')", (login, password, deletion_code, email))
                        else:
                            cur.execute("INSERT INTO account.account (login,password,social_id,email,status,empire) VALUES (%s,PASSWORD(%s),%s,%s,'OK',%s)", (login, password, deletion_code, email, empire if authority != "PLAYER" else 0))
                        if authority != "PLAYER":
                            account_id = cur.lastrowid
                            x, y, map_index = GM_EMPIRE_STARTS[empire]
                            st, ht, dx, iq, hp, mp = GM_JOB_STARTS[gm_job]
                            character_race = GM_RACE_BY_CLASS_GENDER[(gm_job, gm_gender)]
                            cur.execute("""INSERT INTO player.player
                              (account_id,name,job,dir,x,y,map_index,exit_x,exit_y,exit_map_index,hp,mp,stamina,random_hp,random_sp,level,st,ht,dx,iq,stat_point,skill_point,sub_skill_point,part_main,part_base,part_hair,skill_group,horse_hp,horse_stamina,horse_level,horse_hp_droptime,horse_riding,horse_skill_point""" + ("" if ENGINE_MT2009 else ",bank_value") + """)
                              VALUES (%s,%s,%s,0,%s,%s,%s,%s,%s,%s,%s,%s,1000,0,0,1,%s,%s,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0""" + ("" if ENGINE_MT2009 else ",0") + """)""",
                              (account_id, gm_name, character_race, x, y, map_index, x, y, map_index, hp, mp, st, ht, dx, iq))
                            player_id = cur.lastrowid
                            # Metin reads character slots from player_index.  A player row
                            # without this entry exists in SQL but is invisible at login.
                            cur.execute("""INSERT INTO player.player_index (id,pid1,pid2,pid3,pid4,empire)
                              VALUES (%s,%s,0,0,0,%s)
                              ON DUPLICATE KEY UPDATE pid1=VALUES(pid1),pid2=0,pid3=0,pid4=0,empire=VALUES(empire)""",
                              (account_id, player_id, empire))
                            cur.execute("INSERT INTO common.gmlist (mAccount,mName,mContactIP,mServerIP,mAuthority) VALUES (%s,%s,'','ALL',%s)", (login, gm_name, authority))
                        con.commit()
                if authority != "PLAYER":
                    flash(f"Utworzono konto i postać GM „{gm_name}”. Postać jest dostępna od razu; uprawnienia GM staną się aktywne po restarcie usług gry.")
                else:
                    flash("Konto utworzone.")
                return redirect(url_for("accounts"))
            except (pymysql.MySQLError, ValueError) as exc:
                try: con.rollback()
                except Exception: pass
                # The original Metin tables use MyISAM, so a failed multi-table
                # creation is not rolled back by MariaDB.  Remove only records
                # made by this request so an empty account is never left behind.
                if account_id:
                    try:
                        with db() as cleanup_con:
                            with cleanup_con.cursor() as cleanup:
                                cleanup.execute("DELETE FROM common.gmlist WHERE mAccount=%s AND mName=%s", (login, gm_name))
                                if player_id:
                                    cleanup.execute("DELETE FROM player.player WHERE id=%s AND account_id=%s", (player_id, account_id))
                                cleanup.execute("DELETE FROM player.player_index WHERE id=%s", (account_id,))
                                cleanup.execute("DELETE FROM account.account WHERE id=%s AND login=%s", (account_id, login))
                    except pymysql.MySQLError:
                        pass
                flash(f"Nie utworzono konta: {exc.args[1] if isinstance(exc, pymysql.MySQLError) and len(exc.args)>1 else exc}", "error")
    account_query = request.args.get("q", "").strip()[:60]
    display = request.args.get("display", "100")
    if display not in ("100", "1000", "all"):
        display = "100"
    where, params = [], []
    if account_query:
        where.append("(a.login LIKE %s OR EXISTS (SELECT 1 FROM player.player p WHERE p.account_id=a.id AND p.name LIKE %s))")
        params.extend([f"%{account_query}%", f"%{account_query}%"])
    query_sql = "SELECT a.id,a.login,a.email," + EMPIRE_EXPR + " AS empire,a.create_time,a.last_play FROM account.account a LEFT JOIN player.player_index pi ON pi.id=a.id"
    if where:
        query_sql += " WHERE " + " AND ".join(where)
    query_sql += " ORDER BY a.id DESC"
    if display != "all":
        query_sql += " LIMIT %s"
        params.append(int(display))
    recent = rows(query_sql, params)
    return render_template("accounts.html", accounts=recent, authorities=authorities, jobs=GM_JOB_OPTIONS, genders=GM_GENDER_OPTIONS, account_query=account_query, display=display)


BOT_NAME_STATUSES = ("all", "free", "used", "blocked")


def reconcile_bot_names():
    """Deals a name to any playerbot account that exists in the DB but has
    never had one (no common.playerbot_name_history row) -- the only moment
    web_seban_bot_name_pool's priority/blocked settings actually change
    anything, since every currently-existing bot was already named the
    moment its account was seeded (confirmed live 2026-09-22: all 2500
    accounts already have a history row, regardless of whether they are
    actively spawned). This only has real work to do right after a genuine
    wipe/reseed grows the cohort past what the last pass already named.
    Mirrors playerbot_names.sql's own per-kingdom, PID-ordered matching (see
    that file's header), but draws from the panel's own pool table --
    priority DESC, pool_order ASC -- and skips blocked names. Runs in one
    connection/cursor since the TEMPORARY TABLE it uses is connection-scoped
    and rows()/one() each open a fresh one."""
    with db() as con, con.cursor() as cur:
        cur.execute("DROP TEMPORARY TABLE IF EXISTS seban_name_plan")
        cur.execute("""CREATE TEMPORARY TABLE seban_name_plan (
          pid INT UNSIGNED NOT NULL PRIMARY KEY, seed_name VARCHAR(24) NOT NULL,
          human_name VARCHAR(24) NOT NULL, UNIQUE KEY human_name (human_name)) ENGINE=MEMORY""")
        cur.execute("""INSERT INTO seban_name_plan (pid, seed_name, human_name)
          SELECT waiting.pid, waiting.name, free.name
            FROM (SELECT p.id AS pid, p.name,
                    CASE WHEN pi.empire IN (1,2,3) THEN pi.empire ELSE 2 END AS empire,
                    ROW_NUMBER() OVER (PARTITION BY CASE WHEN pi.empire IN (1,2,3) THEN pi.empire ELSE 2 END ORDER BY p.id) AS rn
                    FROM player.player p
                    JOIN account.account a ON a.id=p.account_id
                    LEFT JOIN player.player_index pi ON pi.id=p.account_id
                    LEFT JOIN common.playerbot_name_history h ON h.pid=p.id
                   WHERE LEFT(a.login,10)='playerbot_' AND h.pid IS NULL) AS waiting
            JOIN (SELECT name, empire,
                    ROW_NUMBER() OVER (PARTITION BY empire ORDER BY priority DESC, pool_order ASC) AS rn
                    FROM player.web_seban_bot_name_pool np
                   WHERE blocked=0
                     AND NOT EXISTS (SELECT 1 FROM player.player px JOIN account.account ax ON ax.id=px.account_id
                                      LEFT JOIN common.playerbot_name_history hx ON hx.pid=px.id
                                     WHERE px.name=np.name AND NOT (LEFT(ax.login,10)='playerbot_' AND hx.pid IS NULL))
                  ) AS free ON free.empire=waiting.empire AND free.rn=waiting.rn""")
        cur.execute("SELECT COUNT(*) AS n FROM seban_name_plan")
        planned = cur.fetchone()["n"]
        if planned:
            cur.execute("""INSERT INTO common.playerbot_name_history (pid, seed_name, human_name, pool_version, renamed_at)
              SELECT pid, seed_name, human_name, 'seban-panel', NOW() FROM seban_name_plan
              ON DUPLICATE KEY UPDATE human_name=VALUES(human_name), pool_version=VALUES(pool_version), renamed_at=VALUES(renamed_at)""")
            cur.execute("UPDATE player.player p JOIN seban_name_plan pl ON pl.pid=p.id SET p.name=pl.human_name")
        cur.execute("DROP TEMPORARY TABLE IF EXISTS seban_name_plan")
        return planned


@app.route("/accounts/bot-names")
@login_required
def bot_names():
    search = request.args.get("q", "").strip()[:24]
    try:
        empire = int(request.args.get("empire", 0) or 0)
    except ValueError:
        empire = 0
    if empire not in (0, 1, 2, 3):
        empire = 0
    status = request.args.get("status", "all")
    if status not in BOT_NAME_STATUSES:
        status = "all"
    try:
        page = max(1, int(request.args.get("page", 1) or 1))
    except ValueError:
        page = 1
    per_page = 100
    where, params = ["1=1"], []
    if search:
        where.append("np.name LIKE %s")
        params.append(f"%{search}%")
    if empire:
        where.append("np.empire=%s")
        params.append(empire)
    if status == "free":
        where.append("np.blocked=0 AND h.pid IS NULL")
    elif status == "used":
        where.append("h.pid IS NOT NULL")
    elif status == "blocked":
        where.append("np.blocked=1")
    where_sql = " AND ".join(where)
    join_sql = """FROM player.web_seban_bot_name_pool np
      LEFT JOIN common.playerbot_name_history h ON h.human_name=np.name
      LEFT JOIN player.player p ON p.id=h.pid
      WHERE """ + where_sql
    total = one("SELECT COUNT(*) AS n " + join_sql, params).get("n", 0)
    entries = rows("""SELECT np.name, np.empire, np.pool_order, np.source, np.priority, np.blocked, np.note,
        h.pid, p.name AS current_name, p.level """ + join_sql +
        " ORDER BY np.priority DESC, np.pool_order ASC LIMIT %s OFFSET %s",
        params + [per_page, (page - 1) * per_page])
    stats = one("""SELECT COUNT(*) AS total, SUM(np.blocked) AS blocked_count,
        SUM(CASE WHEN h.pid IS NOT NULL THEN 1 ELSE 0 END) AS used_count,
        SUM(CASE WHEN np.source='custom' THEN 1 ELSE 0 END) AS custom_count
      FROM player.web_seban_bot_name_pool np LEFT JOIN common.playerbot_name_history h ON h.human_name=np.name""")
    pending = one("""SELECT COUNT(*) AS n FROM player.player p JOIN account.account a ON a.id=p.account_id
      LEFT JOIN common.playerbot_name_history h ON h.pid=p.id
      WHERE LEFT(a.login,10)='playerbot_' AND h.pid IS NULL""").get("n", 0)
    pages = max(1, (total + per_page - 1) // per_page)
    return render_template("bot_names.html", entries=entries, search=search, empire=empire, status=status,
        page=page, pages=pages, total=total, stats=stats, pending=pending, empires=EMPIRES)


@app.post("/accounts/bot-names/add")
@login_required
def bot_names_add():
    raw = request.form.get("names", "")
    try:
        empire = max(1, min(3, int(request.form.get("empire", 2) or 2)))
        priority = max(0, min(1000, int(request.form.get("priority", 0) or 0)))
    except ValueError:
        flash("Królestwo i priorytet muszą być liczbami.", "error")
        return redirect(url_for("bot_names"))
    names = [n.strip() for n in raw.splitlines() if n.strip()]
    added, skipped = 0, 0
    for name in names:
        if not re.fullmatch(r"[A-Za-z0-9]{2,24}", name):
            skipped += 1
            continue
        try:
            rows("INSERT INTO player.web_seban_bot_name_pool (name,empire,pool_order,source,priority) VALUES (%s,%s,0,'custom',%s)",
                 (name, empire, priority))
            added += 1
        except pymysql.MySQLError:
            skipped += 1
    flash(f"Dodano {added} nick(ów) do kolejki." + (f" Pominięto {skipped} (zły format albo nick już istnieje w puli)." if skipped else ""))
    return redirect(url_for("bot_names"))


@app.post("/accounts/bot-names/<name>/block")
@login_required
def bot_names_block(name):
    rows("UPDATE player.web_seban_bot_name_pool SET blocked=1 WHERE name=%s", (name,))
    flash(f"Nick „{name}” zablokowany — nie zostanie przydzielony żadnemu przyszłemu botowi.")
    return redirect(request.referrer or url_for("bot_names"))


@app.post("/accounts/bot-names/<name>/unblock")
@login_required
def bot_names_unblock(name):
    rows("UPDATE player.web_seban_bot_name_pool SET blocked=0 WHERE name=%s", (name,))
    flash(f"Nick „{name}” odblokowany.")
    return redirect(request.referrer or url_for("bot_names"))


@app.post("/accounts/bot-names/<name>/delete")
@login_required
def bot_names_delete(name):
    row = one("SELECT source FROM player.web_seban_bot_name_pool WHERE name=%s", (name,))
    used = one("SELECT pid FROM common.playerbot_name_history WHERE human_name=%s", (name,))
    if not row:
        flash("Nie znaleziono tego nicku w puli.", "error")
    elif used:
        flash("Ten nick jest już przypisany do bota — nie można go usunąć z kolejki.", "error")
    elif row["source"] != "custom":
        flash("Nicki z bazowej puli silnika można tylko zablokować, nie usunąć całkowicie (silnik i tak je zna z własnego pliku).", "error")
    else:
        rows("DELETE FROM player.web_seban_bot_name_pool WHERE name=%s", (name,))
        flash(f"Usunięto nick „{name}” z kolejki.")
    return redirect(request.referrer or url_for("bot_names"))


@app.post("/accounts/bot-names/<name>/priority")
@login_required
def bot_names_priority(name):
    try:
        priority = max(0, min(1000, int(request.form.get("priority", 0))))
    except ValueError:
        priority = 0
    rows("UPDATE player.web_seban_bot_name_pool SET priority=%s WHERE name=%s", (priority, name))
    return redirect(request.referrer or url_for("bot_names"))


@app.post("/accounts/bot-names/reconcile")
@login_required
def bot_names_reconcile():
    assigned = reconcile_bot_names()
    if assigned:
        flash(f"Nadano nick {assigned} botom, które go jeszcze nie miały.")
    else:
        flash("Wszystkie istniejące boty mają już nick — nie ma czego przydzielać. To coś zmieni dopiero po realnym poszerzeniu puli botów (pełny wipe/reseed).")
    return redirect(url_for("bot_names"))


@app.route("/api/character-creator/name-status")
@login_required
def api_character_creator_name_status():
    name = request.args.get("name", "").strip()
    if not re.fullmatch(GM_NAME_PATTERN, name):
        return jsonify(ok=False, valid=False, available=False, reason="Nazwa może zawierać litery A-Z, cyfry i nawiasy [ ], 2-24 znaki.")
    taken = bool(one("SELECT id FROM player.player WHERE name=%s LIMIT 1", (name,)))
    return jsonify(ok=True, valid=True, available=not taken)


@app.route("/api/character-creator/accounts")
@login_required
def api_character_creator_accounts():
    q = request.args.get("q", "").strip()[:60]
    where, params = "", ()
    if q:
        where, params = " WHERE a.login LIKE %s", (f"%{q}%",)
    accounts = rows(
        "SELECT a.id,a.login,pi.empire,"
        "(pi.pid1<>0)+(pi.pid2<>0)+(pi.pid3<>0)+(pi.pid4<>0) AS used_slots "
        "FROM account.account a LEFT JOIN player.player_index pi ON pi.id=a.id" + where +
        " ORDER BY a.id DESC LIMIT 200", params)
    out = []
    for a in accounts:
        empire = int(a["empire"] or 0)
        out.append({
            "id": a["id"], "login": a["login"],
            "empire": empire, "empire_name": EMPIRES.get(empire, {}).get("name") if empire else None,
            "used_slots": int(a["used_slots"] or 0), "free_slots": 4 - int(a["used_slots"] or 0),
        })
    return jsonify(ok=True, accounts=out)


@app.route("/character-creator", methods=["GET", "POST"])
@login_required
def character_creator():
    authorities = ("PLAYER", "LOW_WIZARD", "GOD", "HIGH_WIZARD", "IMPLEMENTOR")
    if request.method == "POST":
        gm_name = request.form.get("gm_name", "").strip()
        gm_gender = request.form.get("gm_gender", "male")
        authority = request.form.get("authority", "PLAYER")
        account_mode = request.form.get("account_mode", "existing")
        existing_account_id = request.form.get("existing_account_id", "").strip()
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()[:120]
        deletion_code = request.form.get("deletion_code", "").strip()
        try:
            gm_job = int(request.form.get("gm_job", 0) or 0)
        except ValueError:
            gm_job = -1
        try:
            empire = int(request.form.get("empire", 0) or 0)
        except ValueError:
            empire = 0
        account_id = None
        player_id = None
        slot_col = None
        created_account_id = None
        account_login = None
        login_max = 16 if ENGINE_MT2009 else 30
        if not re.fullmatch(GM_NAME_PATTERN, gm_name):
            flash("Nazwa może zawierać litery A-Z, cyfry i nawiasy [ ], 2-24 znaki.", "error")
        elif gm_job not in dict(GM_JOB_OPTIONS):
            flash("Wybierz poprawną klasę postaci.", "error")
        elif gm_gender not in ("male", "female"):
            flash("Wybierz prawidłową płeć postaci.", "error")
        elif authority not in authorities:
            flash("Wybierz poprawny rodzaj konta.", "error")
        elif empire not in (1, 2, 3):
            flash("Wybierz królestwo.", "error")
        elif account_mode == "existing" and not existing_account_id.isdigit():
            flash("Wybierz konto z listy.", "error")
        elif account_mode == "new" and not (3 <= len(login) <= login_max and login.replace("_", "").isalnum() and len(password) >= 6):
            flash(f"Login ma mieć 3–{login_max} znaków (litery, cyfry, _), a hasło minimum 6 znaków.", "error")
        elif account_mode == "new" and not (deletion_code.isdigit() and len(deletion_code) == 7):
            flash("Kod usunięcia postaci ma zawierać dokładnie 7 cyfr.", "error")
        else:
            try:
                with db() as con:
                    with con.cursor() as cur:
                        cur.execute("SELECT id FROM player.player WHERE name=%s LIMIT 1", (gm_name,))
                        if cur.fetchone():
                            raise ValueError("Taki nick postaci już istnieje.")
                        if account_mode == "existing":
                            account_id = int(existing_account_id)
                            cur.execute("SELECT login FROM account.account WHERE id=%s", (account_id,))
                            acc_row = cur.fetchone()
                            if not acc_row:
                                raise ValueError("Wybrane konto nie istnieje.")
                            account_login = acc_row["login"]
                            cur.execute("SELECT pid1,pid2,pid3,pid4,empire FROM player.player_index WHERE id=%s", (account_id,))
                            slot_row = cur.fetchone()
                            if slot_row:
                                slot_col = next((c for c in ("pid1", "pid2", "pid3", "pid4") if not slot_row[c]), None)
                                if not slot_col:
                                    raise ValueError("To konto ma już 4 postacie - brak wolnego slotu.")
                                # An account's characters always share one kingdom -- lock
                                # onto whichever it already has instead of trusting the
                                # empire the admin had selected before picking this account.
                                if any(slot_row[c] for c in ("pid1", "pid2", "pid3", "pid4")) and slot_row["empire"]:
                                    empire = int(slot_row["empire"])
                            else:
                                slot_col = "pid1"
                        con.begin()
                        if account_mode == "new":
                            # The mt2009 account table has no empire column (the kingdom
                            # lives in player_index, written below); naming it refused
                            # every account on the 2.x line ("Unknown column 'empire' in
                            # 'INSERT INTO'", NieBijOddam, 11 September).
                            if ENGINE_MT2009:
                                cur.execute("INSERT INTO account.account (login,password,social_id,email,status) VALUES (%s,PASSWORD(%s),%s,%s,'OK')", (login, password, deletion_code, email))
                            else:
                                cur.execute("INSERT INTO account.account (login,password,social_id,email,status,empire) VALUES (%s,PASSWORD(%s),%s,%s,'OK',%s)", (login, password, deletion_code, email, empire))
                            account_id = cur.lastrowid
                            created_account_id = account_id
                            account_login = login
                            slot_col = "pid1"
                        x, y, map_index = GM_EMPIRE_STARTS[empire]
                        st, ht, dx, iq, hp, mp = GM_JOB_STARTS[gm_job]
                        character_race = GM_RACE_BY_CLASS_GENDER[(gm_job, gm_gender)]
                        cur.execute("""INSERT INTO player.player
                          (account_id,name,job,dir,x,y,map_index,exit_x,exit_y,exit_map_index,hp,mp,stamina,random_hp,random_sp,level,st,ht,dx,iq,stat_point,skill_point,sub_skill_point,part_main,part_base,part_hair,skill_group,horse_hp,horse_stamina,horse_level,horse_hp_droptime,horse_riding,horse_skill_point""" + ("" if ENGINE_MT2009 else ",bank_value") + """)
                          VALUES (%s,%s,%s,0,%s,%s,%s,%s,%s,%s,%s,%s,1000,0,0,1,%s,%s,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0""" + ("" if ENGINE_MT2009 else ",0") + """)""",
                          (account_id, gm_name, character_race, x, y, map_index, x, y, map_index, hp, mp, st, ht, dx, iq))
                        player_id = cur.lastrowid
                        # Metin reads character slots from player_index.  A player row
                        # without this entry exists in SQL but is invisible at login.
                        # Only the one resolved slot column is ever touched here -- never
                        # a blanket pid2=0,pid3=0,pid4=0 that would wipe an existing
                        # account's other characters.
                        cur.execute(
                            f"INSERT INTO player.player_index (id,{slot_col},empire) VALUES (%s,%s,%s) "
                            f"ON DUPLICATE KEY UPDATE {slot_col}=VALUES({slot_col}), empire=VALUES(empire)",
                            (account_id, player_id, empire))
                        if authority != "PLAYER":
                            cur.execute("INSERT INTO common.gmlist (mAccount,mName,mContactIP,mServerIP,mAuthority) VALUES (%s,%s,'','ALL',%s)", (account_login, gm_name, authority))
                        con.commit()
                if account_mode == "new":
                    flash(f"Utworzono postać „{gm_name}” na nowym koncie „{account_login}”.")
                else:
                    flash(f"Utworzono postać „{gm_name}” na koncie „{account_login}”.")
                if authority != "PLAYER":
                    flash("Uprawnienia GM staną się aktywne po restarcie usług gry.")
                return redirect(url_for("character_creator"))
            except (pymysql.MySQLError, ValueError) as exc:
                try: con.rollback()
                except Exception: pass
                # MyISAM tables (the original Metin ones) don't roll back a
                # failed multi-table write, so undo by hand what this
                # request itself added - never anything that pre-existed.
                try:
                    with db() as cleanup_con:
                        with cleanup_con.cursor() as cleanup:
                            if authority != "PLAYER":
                                cleanup.execute("DELETE FROM common.gmlist WHERE mName=%s", (gm_name,))
                            if player_id:
                                cleanup.execute("DELETE FROM player.player WHERE id=%s AND account_id=%s", (player_id, account_id))
                            if slot_col and not created_account_id:
                                cleanup.execute(f"UPDATE player.player_index SET {slot_col}=0 WHERE id=%s AND {slot_col}=%s", (account_id, player_id or 0))
                            if created_account_id:
                                cleanup.execute("DELETE FROM player.player_index WHERE id=%s", (created_account_id,))
                                cleanup.execute("DELETE FROM account.account WHERE id=%s", (created_account_id,))
                except pymysql.MySQLError:
                    pass
                flash(f"Nie utworzono postaci: {exc.args[1] if isinstance(exc, pymysql.MySQLError) and len(exc.args)>1 else exc}", "error")
    return render_template("character_creator.html", authorities=authorities, jobs=GM_JOB_OPTIONS, genders=GM_GENDER_OPTIONS, preselect_account_id=request.args.get("account_id", "").strip())


@app.route("/account/<int:aid>")
@login_required
def account_detail(aid):
    account = one(
        "SELECT a.id,a.login,a.email,a.cash,a.create_time,a.last_play,"
        "a.silver_expire,a.gold_expire,a.safebox_expire,a.autoloot_expire,a.fish_mind_expire,"
        "a.marriage_fast_expire,a.money_drop_rate_expire,a.shop_expire,a.premium_expire," +
        EMPIRE_EXPR + " AS empire "
        "FROM account.account a LEFT JOIN player.player_index pi ON pi.id=a.id WHERE a.id=%s", (aid,))
    if not account:
        abort(404)
    account["cash"] = int(account.get("cash") or 0)
    empire = int(account.get("empire") or 0)
    account["empire_name"] = EMPIRES.get(empire, {}).get("name") if empire else None
    now = datetime.now()
    # Same "one row per currently-active *_expire column" pattern player()
    # uses -- keeps this page's VIP list in sync with "Nadaj VIP" for free.
    account["premiums"] = [
        {"label": label, "expires": account.get(column)}
        for _type, label in PREMIUM_TYPES
        for column in [PREMIUM_COLUMNS[_type]]
        if isinstance(account.get(column), datetime) and account[column] > now
    ]
    characters = rows(
        "SELECT id,name,level,job,playtime,last_play,gold FROM player.player "
        "WHERE account_id=%s ORDER BY level DESC", (aid,))
    for character in characters:
        character["class_profile"] = class_profile(character["job"])
        character["playtime_hours"] = int(character.get("playtime") or 0) // 60
        character["playtime_minutes"] = int(character.get("playtime") or 0) % 60
    # common.gmlist is keyed by login (mAccount), the same table the
    # character-creator writes to for a GM character -- no separate
    # permissions table to invent.
    gm_row = one("SELECT mAuthority FROM common.gmlist WHERE mAccount=%s LIMIT 1", (account["login"],))
    account["authority"] = gm_row["mAuthority"] if gm_row else "PLAYER"
    return render_template("account_detail.html", account=account, characters=characters)


@app.route("/maps")
@login_required
def maps():
    """One chart+current-table per channel plus an 'all' (summed) view, so the
    page can switch CH1/CH2/... client-side without a reload -- scales to
    however many channelN dirs discovered_channels() finds, not just two."""
    channels = discovered_channels()
    raw = rows("""
      SELECT DATE_FORMAT(captured_at, '%%m-%%d %%H:%%i') AS label, channel, map_index, character_count
      FROM player.web_seban_map_snapshot
      WHERE captured_at >= NOW() - INTERVAL 24 HOUR ORDER BY captured_at ASC
    """)

    def build_chart(scoped_rows):
        labels, series = [], {index: {} for index, _name in TRACKED_MAP_OPTIONS}
        for row in scoped_rows:
            index = int(row["map_index"] or 0)
            if index not in series:
                continue
            if row["label"] not in labels:
                labels.append(row["label"])
            series[index][row["label"]] = series[index].get(row["label"], 0) + int(row["character_count"] or 0)
        return {"labels": labels, "series": [
            {"id": index, "name": name, "data": [values.get(label, 0) for label in labels]}
            for index, name in TRACKED_MAP_OPTIONS for values in (series[index],)
        ]}

    charts = {"all": build_chart(raw)}
    for channel in channels:
        charts[str(channel)] = build_chart([row for row in raw if int(row.get("channel") or 1) == channel])

    def build_latest(channel):
        current = {int(row["map_index"]): row["character_count"] for row in live_map_counts(channel)}
        return [{"map_index": index, "map_name": name, "character_count": current.get(index, 0)} for index, name in TRACKED_MAP_OPTIONS]

    latest = {"all": build_latest(None)}
    for channel in channels:
        latest[str(channel)] = build_latest(channel)
    return render_template("maps.html", charts=charts, latest=latest, channels=channels)


@app.route("/changelog")
@login_required
def changelog():
    return render_template("changelog.html", entries=changelog_entries(), panel_version=PANEL_VERSION)


@app.route("/accounts/<int:aid>/characters")
@login_required
def account_characters(aid):
    characters = rows("""SELECT id,name,level,job,map_index FROM player.player
      WHERE account_id=%s ORDER BY level DESC""", (aid,))
    for character in characters:
        character["job_name"] = class_profile(character["job"])["name"]
        character["map_name"] = map_name(character["map_index"])
    return {"ok": True, "characters": characters}


@app.route("/api/live-bots")
@login_required
def api_live_bots():
    global_top = one("SELECT id FROM player.player WHERE " + BOT_IS_BARE + " ORDER BY level DESC,exp DESC LIMIT 1")
    return {"ok": True, "updated_at": int(datetime.now().timestamp() * 1000), "maps": MAP_NAMES, "bounds": MAP_BOUNDS,
            "global_top_id": global_top.get("id"), "bots": live_bots(), "channels": discovered_channels()}


@app.route("/api/news-feed")
@login_required
def api_news_feed():
    return {"ok": True, "events": news_feed_events()}


@app.route("/system")
@login_required
def system():
    samples = rows("""
      SELECT DATE_FORMAT(captured_at, '%%H:%%i') AS label, cpu_percent, ram_percent, ram_used_mb, ram_total_mb,
             disk_percent, disk_used_mb, disk_total_mb
      FROM player.web_seban_system_snapshot WHERE captured_at >= NOW() - INTERVAL 24 HOUR ORDER BY captured_at
    """)
    current = samples[-1] if samples else {}
    return render_template("system.html", samples=samples, current=current)


@app.route("/api/system-current")
@login_required
def api_system_current():
    return {"ok": True, "system": one("SELECT * FROM player.web_seban_system_snapshot ORDER BY captured_at DESC LIMIT 1")}


@app.route("/rankings")
@login_required
def rankings():
    kinds = {
        "level": "Poziom", "armor": "Zbroja", "weapon": "Broń", "weapon30": "Broń 30 Lv",
        "gold": "Yang", "items": "Przedmioty", "horse": "Koń", "hunting": "Polowanie", "biologist": "Biolog",
        "shops": "Otwarte stragany", "skills": "Umiejętności", "plus9": "Przedmiot +9", "playtime": "Czas gry", "bosses": "Bossy", "refine": "Pomyślne ulepszenia", "refine_rate": "Skuteczność ulepszeń", "fish": "Wyłowione ryby",
        "damage_max": "Rekord obrażeń (zwykłe)", "damage_max_horse": "Rekord obrażeń (konno)", "damage_max_skill": "Rekord obrażeń (umiejętność)",
        "yang_earned": "Zdobyty Yang (łącznie)", "yang_npc_sale": "Yang ze sprzedaży u NPC",
        "monsters_killed": "Zabite potwory (łącznie)", "minibosses": "Pokonane minibossy", "pvp_kills_total": "Pokonani gracze (PVP)", "duel_wins": "Wygrane pojedynki", "mining": "Wykopane rudy",
    }
    kind = request.args.get("type", "level")
    if kind not in kinds:
        kind = "level"
    weapon30_sort = request.args.get("sort", "avg") if kind == "weapon30" else "avg"
    if weapon30_sort not in ("avg", "skill", "upgrade"):
        weapon30_sort = "avg"
    ranking = bot_ranking(kind, weapon30_sort)
    ids = [row["id"] for row in ranking]
    if ids:
        # Which kingdom each of them belongs to. player_index.empire, because
        # that is the column the core reads when it decides where a bot lives;
        # the account's own copy was left at Chunjo for the whole cohort.
        marks = ",".join(["%s"] * len(ids))
        empire_rows = rows(
            "SELECT p.id, " + EMPIRE_EXPR + " AS empire"
            " FROM player.player p"
            " LEFT JOIN player.player_index pi ON pi.id=p.account_id"
            " LEFT JOIN account.account a ON a.id=p.account_id"
            " WHERE p.id IN (" + marks + ")", ids)
        empires = {row["id"]: row["empire"] for row in empire_rows}
        for row in ranking:
            row["empire"] = empires.get(row["id"], 0)
        progress_rows = rows("SELECT id,level,exp,job FROM player.player WHERE id IN (" + ",".join(["%s"] * len(ids)) + ")", ids)
        progress = {row["id"]: experience_progress(row["level"], row["exp"]) for row in progress_rows}
        jobs = {row["id"]: row["job"] for row in progress_rows}
        for row in ranking:
            row["job"] = jobs.get(row["id"], 0)
            row["experience"] = progress.get(row["id"], {"percent": 0})
    for row in ranking:
        if kind == "weapon30":
            row["detail"] = "Średnie obrażenia: %s%% · Obrażenia umiejętności: %s%% · %s" % (
                int(row.get("avg_damage") or 0), int(row.get("skill_damage") or 0), game_text(row.get("item_name")))
        else:
            row["detail"] = game_text(row.get("detail"))
    return render_template("rankings.html", kinds=kinds, kind=kind, ranking=ranking, weapon30_sort=weapon30_sort)


@app.route("/season")
def season():
    """Weekly season from the three indexed event types only."""
    if time.time() - _season_cache["at"] < 600:
        return render_template("season.html", weekly=_season_cache["weekly"], records=_season_cache["records"])
    weekly = rows("""SELECT p.id,p.name,p.level,
        SUM(l.how='STONE_KILL') AS metins,
        SUM(l.how='BOSS_KILL') AS bosses,
        SUM(l.how='REFINE SUCCESS' AND (l.hint LIKE '%%+7' OR l.hint LIKE '%%+8' OR l.hint LIKE '%%+9')) AS refine7
        FROM log.log l JOIN player.player p ON p.id=l.who
        WHERE l.time>=NOW()-INTERVAL 7 DAY AND """ + ranking_scope_sql("p") + """
          AND l.how IN ('STONE_KILL','BOSS_KILL','REFINE SUCCESS')
        GROUP BY p.id ORDER BY (SUM(l.how='STONE_KILL')*150+SUM(l.how='BOSS_KILL')*500+SUM(l.how='REFINE SUCCESS' AND (l.hint LIKE '%%+7' OR l.hint LIKE '%%+8' OR l.hint LIKE '%%+9'))*200) DESC,p.level DESC LIMIT 30""")
    for row in weekly:
        row["points"] = int(row.get("metins") or 0)*150 + int(row.get("bosses") or 0)*500 + int(row.get("refine7") or 0)*200
    records = one("""SELECT
        SUM(l.how='STONE_KILL') AS metins,
        SUM(l.how='BOSS_KILL') AS bosses,
        SUM(l.how='REFINE SUCCESS' AND (l.hint LIKE '%%+7' OR l.hint LIKE '%%+8' OR l.hint LIKE '%%+9')) AS refine7,
        (SELECT MAX(level) FROM player.player) AS level
        FROM log.log l
        WHERE l.time>=NOW()-INTERVAL 7 DAY
          AND l.how IN ('STONE_KILL','BOSS_KILL','REFINE SUCCESS')""")
    _season_cache.update(at=time.time(), weekly=weekly, records=records)
    return render_template("season.html", weekly=weekly, records=records)





@app.route("/economy/itemshop")
@login_required
def economy_itemshop():
    totals = one("""SELECT COALESCE(SUM(cash),0) cash,COALESCE(SUM(cash_mark),0) mileage,
                       SUM(cash>0) cash_accounts,SUM(cash_mark>0) mileage_accounts
                    FROM account.account WHERE status IN ('OK','BLOCK')""") or {}
    top_cash = rows("""SELECT id,login,cash,cash_mark AS mileage FROM account.account
                       WHERE status IN ('OK','BLOCK') AND cash>0 ORDER BY cash DESC,id ASC LIMIT 15""")
    top_mileage = rows("""SELECT id,login,cash,cash_mark AS mileage FROM account.account
                          WHERE status IN ('OK','BLOCK') AND cash_mark>0 ORDER BY cash_mark DESC,id ASC LIMIT 10""")
    purchases = rows("""SELECT COALESCE(p.name,CONCAT('PID ',l.pid)) buyer_name,
                        COALESCE(ip.locale_name,CONCAT('VNUM ',l.vnum)) item_name,
                        l.time date_of_buy,l.vnum vnum_icon
                        FROM log.itemshop l
                        LEFT JOIN player.player p ON p.id=l.pid
                        LEFT JOIN player.item_proto ip ON ip.vnum=l.vnum
                        ORDER BY l.time DESC LIMIT 80""")
    popular = rows("""SELECT l.vnum,COALESCE(ip.locale_name,CONCAT('VNUM ',l.vnum)) item_name,
                      COUNT(*) total FROM log.itemshop l
                      LEFT JOIN player.item_proto ip ON ip.vnum=l.vnum
                      GROUP BY l.vnum,ip.locale_name ORDER BY total DESC,item_name LIMIT 10""")
    daily = rows("""SELECT DATE_FORMAT(time,'%%d.%%m') label,COUNT(*) total
                    FROM log.itemshop WHERE time>=NOW()-INTERVAL 14 DAY
                    GROUP BY DATE(time) ORDER BY DATE(time)""")
    for row in purchases + popular:
        row["item_name"] = game_text(row.get("item_name"))
    return render_template("economy_itemshop.html", totals=totals, top_cash=top_cash,
                           top_mileage=top_mileage, purchases=purchases, popular=popular,
                           daily=daily)

def read_panel_log_files(max_lines=500):
    """Newest lines first across the active log plus any rotated backups
    (panel.log.1, .2, ...), oldest rotated file read last -- so "last N
    lines" reads back in true chronological order regardless of where a
    rotation boundary happens to fall."""
    chunks = []
    for suffix in ("", ".1", ".2", ".3", ".4", ".5"):
        path = Path(str(PANEL_LOG_FILE) + suffix)
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    text = "".join(reversed(chunks))
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


@app.route("/diagnostics/panel-logs")
@login_required
def panel_logs():
    tail = read_panel_log_files(500)
    try:
        size = PANEL_LOG_FILE.stat().st_size
    except OSError:
        size = 0
    return render_template("panel_logs.html", log_tail=tail, log_size=size)


@app.route("/diagnostics/panel-logs/download")
@login_required
def panel_logs_download():
    if not PANEL_LOG_FILE.exists():
        abort(404)
    return send_file(PANEL_LOG_FILE, as_attachment=True,
                      download_name=f"seban-panel-log-{datetime.now().strftime('%Y%m%d-%H%M')}.txt",
                      mimetype="text/plain")


@app.route("/diagnostics")
@login_required
def diagnostics():
    return render_template("diagnostics.html", diagnostic=fishing_diagnostics())

@app.route("/daily-summary/<int:summary_id>")
@login_required
def daily_summary(summary_id):
    """Nie ma linku w nawigacji celowo -- dociera się tu tylko z powiadomienia
    albo bezpośredniego linku (tak jak poprosił operator)."""
    summary = one("SELECT * FROM player.web_seban_daily_summary WHERE id=%s", (summary_id,))
    if not summary:
        abort(404)
    return render_template("daily_summary.html", s=summary)


@app.get("/respawns")
@login_required
def respawns():
    return render_template("respawns.html", regen=read_regen_settings(),
                           count_choices=REGEN_COUNT_CHOICES,
                           map_options=MAP_RESPAWN_OPTIONS,
                           stone_maps=MAP_STONE_RESPAWN_IDS,
                           map_status=read_map_regen_status())


@app.post("/respawns/delay")
@login_required
def respawns_delay():
    try:
        values = {key: int(request.form.get(f"delay_{key}", "")) for key in REGEN_DELAY_FLAGS}
        if any(not REGEN_DELAY_MIN <= value <= 100 for value in values.values()):
            raise ValueError(f"Szybkość odrodzenia musi mieścić się w zakresie {REGEN_DELAY_MIN}–100%.")
        persist_regen_settings("delay", values)
        status, queue_id = queue_game_admin_command("REGEN", f"{0 if values['boss'] == 100 else values['boss']},{0 if values['mob'] == 100 else values['mob']}")
        if status != "done":
            if status == "timeout": cancel_pending_admin_command(queue_id)
            raise RuntimeError("Ustawienie zapisano na następny start, ale rdzeń nie potwierdził zmiany na żywo.")
    except (TypeError, ValueError) as exc:
        flash(str(exc) or "Wprowadź prawidłowe wartości.", "error")
    except (RuntimeError, pymysql.MySQLError) as exc:
        flash(str(exc) or "Nie udało się połączyć z kolejką gry.", "error")
    else:
        flash("Czasy odrodzenia zmienione na żywo. Kolejny cykl użyje nowych wartości.")
    return redirect(url_for("respawns"))


@app.post("/respawns/count")
@login_required
def respawns_count():
    try:
        values = {key: int(request.form.get(f"count_{key}", "")) for key in REGEN_COUNT_FLAGS}
        if any(value not in REGEN_COUNT_CHOICES for value in values.values()):
            raise ValueError("Wybierz jeden z dostępnych mnożników liczby potworów.")
        persist_regen_settings("count", values)
        status, queue_id = queue_game_admin_command("REGEN_COUNT", f"{values['boss']},{values['mob']}")
        if status != "done":
            if status == "timeout": cancel_pending_admin_command(queue_id)
            raise RuntimeError("Ustawienie zapisano na następny start, ale rdzeń nie potwierdził zmiany na żywo.")
    except (TypeError, ValueError) as exc:
        flash(str(exc) or "Wybierz prawidłowe wartości.", "error")
    except (RuntimeError, pymysql.MySQLError) as exc:
        flash(str(exc) or "Nie udało się połączyć z kolejką gry.", "error")
    else:
        flash("Liczebność respawnów zmieniona na żywo. Brakujące jednostki pojawią się przy kolejnym odrodzeniu.")
    return redirect(url_for("respawns"))


@app.post("/respawns/map")
@login_required
def respawns_map():
    known = {str(index) for index, _label in MAP_RESPAWN_OPTIONS}
    map_index, target = request.form.get("map_index", ""), request.form.get("target", "mob")
    try:
        if map_index not in known or target not in ("mob", "stone"):
            raise ValueError("Wybierz prawidłową mapę i rodzaj respawnu.")
        if target == "stone" and int(map_index) not in MAP_STONE_RESPAWN_IDS:
            raise ValueError("Ta mapa nie ma osobnego pliku respawnu Metinów.")
        raw = request.form.get("seconds", "").strip()
        value = "reset" if not raw else int(raw)
        if value != "reset" and not 1 <= value <= 3600:
            raise ValueError("Czas respawnu musi mieścić się w zakresie 1–3600 sekund.")
        key = f"stone_{map_index}" if target == "stone" else map_index
        queue_map_regen_changes({key: value})
    except (TypeError, ValueError) as exc:
        flash(str(exc) or "Wprowadź prawidłową wartość.", "error")
    except OSError:
        flash("Nie udało się zlecić zmiany dla mapy.", "error")
    else:
        flash("Zlecono dokładny czas dla mapy. Ta operacja odtwarza rdzenie, aby wczytać pliki respawnu.")
    return redirect(url_for("respawns"))


@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    check_all_notifications()
    event_history = globals()["rows"]("""SELECT id,kind,value,started_at,ended_at,chest_count,yang_extra
      FROM player.web_seban_event_runs WHERE ended_at IS NOT NULL ORDER BY ended_at DESC LIMIT 20""")
    for item in event_history:
        item["label"] = EVENT_LABELS.get(item["kind"], item["kind"])
        if item.get("chest_count") is not None:
            item["summary"] = f"{item['chest_count']} szkatułek"
        elif item.get("yang_extra") is not None:
            item["summary"] = f"+{item['yang_extra']:,} yang".replace(",", " ")
        else:
            item["summary"] = "brak statystyk"
    rows, nows = read_events()
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "save":
            new_rows = []
            for index in range(16):
                kind = request.form.get(f"r{index}_kind")
                if kind is None:
                    break
                if kind not in EVENT_KINDS or request.form.get(f"r{index}_delete"):
                    continue
                start = event_hhmm(request.form.get(f"r{index}_start"))
                end = event_hhmm(request.form.get(f"r{index}_end"))
                try:
                    value = max(0, min(1000, int(request.form.get(f"r{index}_value") or 0)))
                except ValueError:
                    value = -1
                if not start or not end or start == "24:00" or value < 0:
                    flash(f"Wiersz {index + 1}: podaj poprawne godziny i wartość 0–1000%.", "error")
                    return redirect(url_for("events"))
                days = [day for day in range(1, 8) if request.form.get(f"r{index}_d{day}")]
                new_rows.append({"kind": kind, "days": days, "start": start, "end": end,
                                 "value": 0 if kind == "chest" else value,
                                 "on": bool(request.form.get(f"r{index}_on"))})
            try:
                write_events(new_rows, nows)
            except OSError:
                flash("Nie udało się zapisać harmonogramu eventów.", "error")
            else:
                flash("Harmonogram zapisany. Rdzeń zastosuje go w ciągu pięciu sekund.", "success")
            return redirect(url_for("events"))
        kind = request.form.get("kind", "")
        if kind not in EVENT_KINDS:
            return redirect(url_for("events"))
        if action == "now":
            try:
                minutes = max(5, min(1440, int(request.form.get("minutes") or 60)))
                value = max(1, min(1000, int(request.form.get("value") or 50)))
            except ValueError:
                minutes, value = 60, 50
            nows[kind] = {"until": int(time.time()) + minutes * 60, "value": 0 if kind == "chest" else value}
            write_events(rows, nows)
            flash(f"Event aktywowany na {minutes} min. Rdzeń odczyta go w ciągu pięciu sekund.", "success")
        elif action == "stop":
            nows.pop(kind, None)
            write_events(rows, nows)
            flash("Natychmiastowy event został zatrzymany.", "success")
        return redirect(url_for("events"))
    shown = list(rows) + [{"kind": "", "days": list(range(1, 8)), "start": "20:00", "end": "21:00", "value": 50, "on": True} for _ in range(max(0, 4 - len(rows)))]
    return render_template("events.html", rows=shown, nows=nows, status=read_events_status(),
                           event_kinds=EVENT_KINDS, event_labels=EVENT_LABELS,
                           day_names=EVENT_DAY_NAMES, now_minutes=EVENT_NOW_MINUTES,
                           now_epoch=int(time.time()), event_history=event_history)

@app.route("/manage")
@login_required
def manage():
    map_counts = live_map_counts()
    current_settings = settings()
    updater = update_status()
    updater["protected"] = current_settings.get("auth_enabled") == "1" and bool(session.get("seban_admin"))
    return render_template("manage.html", rates=read_rates(), ai_weights=read_ai_weights(), ai_weight_keys=AI_WEIGHT_KEYS, restart=restart_progress(), settings=current_settings, map_counts=map_counts, bot_count=len(live_bots()), map_respawn_options=MAP_RESPAWN_OPTIONS, map_stone_respawn_ids=MAP_STONE_RESPAWN_IDS, map_respawn_status=read_map_regen_status(), server_settings=server_settings_status(), updater=updater, playerbots_release=playerbots_release_status(), update_csrf=update_csrf_token(), bot_count_wanted=read_bot_count(), spawn_plan=read_spawn_plan(), student_chest_disabled=read_student_chest_disabled(), custom_patches_enabled=CUSTOM_PATCHES_ENABLED, include_real_players=include_real_players_in_rankings(), announce_plus9=read_announce_plus9_refines(), bots_held=read_bot_hold(), item_policy=read_ai_item_policy())


@app.post("/manage/update")
@login_required
def manage_update():
    current = settings()
    if current.get("auth_enabled") != "1" or not session.get("seban_admin"):
        flash("Aktualizacje z panelu wymagają włączonej ochrony hasłem.", "error")
        return redirect(url_for("manage"))
    supplied = request.form.get("update_csrf", "")
    expected = session.get("seban_update_csrf", "")
    if not expected or not hmac.compare_digest(supplied, expected):
        abort(403)
    try:
        queue_tieru_update(current.get("update_seban_panel") == "1")
    except (OSError, RuntimeError) as exc:
        flash(str(exc), "error")
    else:
        panel_note = " Razem z Playerbots zostanie zaktualizowany Seban Panel." if current.get("update_seban_panel") == "1" else " Seban Panel pozostanie w obecnej wersji."
        flash("Pobrano zlecenie aktualizacji. Serwer zostanie przebudowany przez odizolowany updater; postęp jest widoczny poniżej." + panel_note)
    return redirect(url_for("manage"))


@app.post("/manage/settings")
@login_required
def manage_settings():
    values, error = validate_display_settings(request.form)
    if error:
        flash(error, "error")
        return redirect(url_for("manage"))
    current = settings()
    enable_auth = request.form.get("auth_enabled") == "1"
    password = request.form.get("panel_password", "")
    if enable_auth:
        if password and len(password) < 8:
            flash("Nowe hasło musi mieć co najmniej 8 znaków.", "error")
            return redirect(url_for("manage"))
        password_hash = generate_password_hash(password) if password else current.get("auth_password_hash", "")
        if not password_hash:
            flash("Aby włączyć ochronę, ustaw hasło panelu.", "error")
            return redirect(url_for("manage"))
    else:
        password_hash = ""
        session.clear()
    values.update({"auth_enabled": "1" if enable_auth else "0", "auth_password_hash": password_hash, "setup_complete": "1"})
    write_settings(values)
    flash("Ustawienia panelu zapisane.")
    return redirect(url_for("manage"))


@app.post("/manage/overrides")
@login_required
def manage_overrides():
    values = {key: "1" if request.form.get(key) == "1" else "0" for key in ("allow_student_chest", "allow_moonlight_chest", "keep_demo_characters", "update_seban_panel")}
    write_settings(values)
    flash("Override'y zapisane. Zostaną zastosowane przy następnej aktualizacji Playerbots.")
    return redirect(url_for("manage"))


@app.post("/manage/restart-config")
@login_required
def manage_restart_config():
    action = request.form.get("submit_action", "apply")
    values, changes = {}, {}
    bot_count = None
    try:
        if action not in ("apply", "restart"):
            raise ValueError("Nieprawidłowa akcja.")
        if action == "apply":
            values = {name: int(request.form.get(name, "")) for name in RATE_NAMES}
            if any(not 1 <= value <= 10000 for value in values.values()):
                raise ValueError("Mnożniki muszą mieścić się w zakresie 1–10 000%.")
            # Older browser tabs opened before this field existed do not send
            # it -- leave the game side's current target alone rather than
            # snapping it to some default.
            if "playerbot_count" in request.form:
                bot_count = int(request.form["playerbot_count"])
                if not 1 <= bot_count <= 2500:
                    raise ValueError("Liczba botów musi mieścić się w zakresie 1–2500.")
            for index, name in MAP_RESPAWN_OPTIONS:
                for prefix in ("", "stone_"):
                    if prefix and index not in MAP_STONE_RESPAWN_IDS:
                        continue
                    key = f"{prefix}{index}"
                    # Older browser tabs do not contain the Metin fields.
                    if f"map_{key}" not in request.form:
                        continue
                    raw = request.form[f"map_{key}"].strip()
                    if not raw:
                        changes[key] = "reset"
                    else:
                        seconds = int(raw)
                        if not 1 <= seconds <= 3600:
                            raise ValueError(f"{name}: respawn musi mieścić się w zakresie 1–3600 sekund.")
                        changes[key] = seconds
        queue_server_settings(action, values, changes)
        if action == "apply" and bot_count is not None:
            queue_botcount_change(bot_count)
    except ValueError as exc:
        flash(str(exc) if "invalid literal" not in str(exc) else "Wpisz całkowite wartości liczbowe.", "error")
    except RuntimeError as exc:
        flash(str(exc), "error")
    except FileExistsError:
        flash("Poprzednie zlecenie nadal trwa. Poczekaj na zakończenie restartu.", "error")
    except OSError:
        flash("Nie udało się zapisać zlecenia do kolejki gry.", "error")
    else:
        flash("Zestaw zapisany do kolejki: jeden restart zastosuje raty i respawn." if action == "apply"
              else "Zlecono restart bez zapisywania zmian w formularzu.")
    return redirect(url_for("manage"))


@app.post("/manage/spawn-plan")
@login_required
def manage_spawn_plan():
    try:
        window = int(request.form.get("spawn_window_minutes", ""))
        late_joiners = int(request.form.get("late_joiners", ""))
        late_hours = int(request.form.get("late_join_hours", ""))
        if not 1 <= window <= 180:
            raise ValueError("Okno wejścia musi mieścić się w zakresie 1–180 minut.")
        if not 0 <= late_joiners <= 2500:
            raise ValueError("Liczba dodatkowych botów musi mieścić się w zakresie 0–2500.")
        if not 1 <= late_hours <= 168:
            raise ValueError("Okres późnego wejścia musi mieścić się w zakresie 1–168 godzin.")
        queue_spawn_plan(window, late_joiners, late_hours)
    except (TypeError, ValueError, OSError) as exc:
        flash(str(exc) or "Nie udało się zapisać planu wejścia.", "error")
    else:
        flash("Plan wejścia zapisany. Kontener gry zostanie odtworzony z nowymi ustawieniami.")
    return redirect(url_for("manage"))


@app.post("/manage/student-chest")
@login_required
def manage_student_chest():
    disabled = "1" in request.form.getlist("disable_student_chest")
    write_student_chest_disabled(disabled)
    if disabled:
        flash("Skrzynia startowa jest teraz wyłączona dla nowych postaci graczy, każdej klasy — działa od razu, bez restartu.")
    else:
        flash("Skrzynia startowa jest teraz włączona dla nowych postaci graczy, każdej klasy — działa od razu, bez restartu.")
    return redirect(url_for("manage"))


@app.post("/manage/ranking-scope")
@login_required
def manage_ranking_scope():
    enabled = "1" in request.form.getlist("include_real_players")
    write_include_real_players_in_rankings(enabled)
    if enabled:
        flash("Rankingi i karuzela na dashboardzie liczą teraz każdą postać, nie tylko boty — działa od razu.")
    else:
        flash("Rankingi liczą teraz znowu wyłącznie boty.")
    return redirect(url_for("manage"))


@app.post("/manage/plus9-announce")
@login_required
def manage_plus9_announce():
    enabled = "1" in request.form.getlist("announce_plus9_refines")
    write_announce_plus9_refines(enabled)
    if enabled:
        flash("Ulepszenia graczy na +9 będą teraz ogłaszane na złoto na całym świecie — kolektor sprawdza co kilka sekund/minut, nie natychmiast.")
    else:
        flash("Ogłoszenia +9 wyłączone.")
    return redirect(url_for("manage"))


@app.post("/manage/restart-clear-stale")
@login_required
def manage_restart_clear_stale():
    support = server_settings_status()
    if not support["can_clear"]:
        flash("Nie można usunąć zlecenia: helper może jeszcze je przetwarzać albo zlecenie nie jest wystarczająco stare.", "error")
        return redirect(url_for("manage"))
    try:
        (RATES_SPOOL / "server-settings.request").unlink()
        (RATES_SPOOL / "server-settings.status").write_text(
            "state=failed\npercent=0\nmessage=Usunięto zaległe zlecenie bez aktywnego helpera gry.\ntime=%s\n" % int(time.time()), encoding="utf-8")
    except OSError:
        flash("Nie udało się usunąć zaległego zlecenia z kolejki.", "error")
    else:
        flash("Usunięto zaległe zlecenie. Zainstaluj integrację gry, zanim zlecisz kolejną zmianę.")
    return redirect(url_for("manage"))


@app.post("/manage/map-respawns")
@login_required
def manage_map_respawns():
    known_maps = {str(index) for index, _name in MAP_RESPAWN_OPTIONS}
    map_index = request.form.get("map_index", "")
    action = request.form.get("action", "")
    if map_index not in known_maps or action not in ("set", "reset"):
        flash("Nieprawidłowa mapa lub akcja.", "error")
        return redirect(url_for("manage"))
    seconds = None
    if action == "set":
        try:
            seconds = int(request.form.get("seconds", ""))
        except ValueError:
            seconds = 0
        if not 1 <= seconds <= 3600:
            flash("Czas respawnu musi mieścić się w zakresie 1–3600 sekund.", "error")
            return redirect(url_for("manage"))
    try:
        queue_map_regen_change(map_index, action, seconds)
    except OSError:
        flash("Nie udało się zapisać zmiany mapy do kolejki gry.", "error")
        return redirect(url_for("manage"))
    flash("Zmiana respawnu została zlecona. Gra zastosuje ją i uruchomi rdzenie ponownie.")
    return redirect(url_for("manage"))


@app.post("/manage/behavior")
@login_required
def manage_behavior():
    # Keep live-only switches even if this request came from an older browser
    # tab that does not render them yet.
    values = read_ai_weights()
    for key, _, _ in AI_WEIGHT_KEYS:
        try:
            value = int(request.form.get(key, AI_WEIGHT_NEUTRAL))
        except (TypeError, ValueError):
            value = AI_WEIGHT_NEUTRAL
        values[key] = max(AI_WEIGHT_MIN, min(AI_WEIGHT_MAX, value))
    values["CHAT"] = 1 if "1" in request.form.getlist("CHAT") else 0
    # Preserve the existing switch for a form opened before this field existed.
    values["BOOKS"] = 1 if "BOOKS" not in request.form else (1 if "1" in request.form.getlist("BOOKS") else 0)
    for key, default in (("NIGHT", 1), ("LIFE", 0), ("WARS", 1), ("TOWER", 1), ("ISHOP", 1), ("PERSONA", 1)):
        values[key] = default if key not in request.form else (1 if "1" in request.form.getlist(key) else 0)
    try:
        values["SCRAP"] = max(0, min(100, int(request.form.get("SCRAP", values.get("SCRAP", 0)))))
    except (TypeError, ValueError):
        values["SCRAP"] = 0
    try:
        values["REST"] = max(0, min(100, int(request.form.get("REST", values.get("REST", 100)))))
    except (TypeError, ValueError):
        values["REST"] = 100
    try:
        values["KINGDOMPVP"] = max(0, min(100, int(request.form.get("KINGDOMPVP", values.get("KINGDOMPVP", 0)))))
    except (TypeError, ValueError):
        values["KINGDOMPVP"] = 0
    try:
        values["SCROLL_FROM"] = max(1, min(9, int(request.form.get("SCROLL_FROM", values.get("SCROLL_FROM", 1)))))
    except (TypeError, ValueError):
        values["SCROLL_FROM"] = 1
    for key in ("CHEST", "CHEST_STONE"):
        if key not in request.form:
            continue
        try:
            values[key] = max(0, min(1000, int(request.form[key])))
        except (TypeError, ValueError):
            # A malformed chest control must not turn an existing server value
            # into a guessed default.
            continue
    try:
        write_ai_weights(values)
    except OSError:
        flash("Nie udało się zapisać wag Playerbots.", "error")
    else:
        flash("Zachowanie botów zapisane — nowy plan działania wejdzie w życie do 5 sekund, bez restartu.")
    return redirect(url_for("manage"))


@app.post("/manage/item-policy")
@login_required
def manage_item_policy():
    """Per-item keep/stall/merchant/drop rules -- ported from Tieru's classic
    panel (2026-09-26 audit), confirmed the engine reads this exact file
    live (playerbot_config.h), same as the behaviour weights above."""
    text = request.form.get("policy", "")
    bad_lines = check_ai_item_policy(text)
    if bad_lines:
        flash("Odrzucono -- błędne linie: " + ", ".join(str(n) for n in bad_lines) + ". Format: <vnum lub type:N> <keep|stall|merchant|drop>.", "error")
        return redirect(url_for("manage"))
    try:
        write_ai_item_policy(text)
    except OSError:
        flash("Nie udało się zapisać polityki przedmiotów.", "error")
    else:
        flash("Polityka przedmiotów zapisana — rdzeń odczytuje ją na żywo, bez restartu.")
    return redirect(url_for("manage"))


@app.post("/manage/release-bots")
@login_required
def manage_release_bots():
    """Wpuszcza boty trzymane 'przy drzwiach' (M2_PLAYERBOT_START_HELD przy
    świeżym siewie świata) -- bez restartu, świat wypełnia się zwykłym oknem
    spawnu w ciągu kilku sekund."""
    try:
        write_bot_hold(False)
        flash("Boty wpuszczone do świata — wejdą przez zwykłe okno spawnu, bez restartu.")
    except OSError:
        flash("Nie udało się wpuścić botów (spool nie do zapisu).", "error")
    return redirect(url_for("manage"))


@app.post("/manage/hold-bots")
@login_required
def manage_hold_bots():
    """Odwrotność powyższego -- z powrotem trzyma boty przy drzwiach, gdyby
    trzeba było jeszcze coś domknąć zanim wejdą do świata."""
    try:
        write_bot_hold(True)
        flash("Boty zatrzymane przy drzwiach.")
    except OSError:
        flash("Nie udało się zatrzymać botów (spool nie do zapisu).", "error")
    return redirect(url_for("manage"))


@app.post("/manage/tower-now")
@login_required
def manage_tower_now():
    """Każe rdzeniowi wywołać teraz najazd na Wieżę Demonów gildii botów,
    zamiast czekać na losowy termin."""
    try:
        queue_tower_now()
        flash("Zlecono najazd na Wieżę Demonów — rdzeń wywoła go przy najbliższym sprawdzeniu, jeśli żaden akurat nie trwa.")
    except OSError:
        flash("Nie udało się zlecić najazdu (spool nie do zapisu).", "error")
    return redirect(url_for("manage"))


@app.post("/manage/restart")
@login_required
def manage_restart():
    if request.form.get("confirmation", "").strip().upper() != "RESTART":
        flash("Aby potwierdzić restart, wpisz RESTART.", "error")
        return redirect(url_for("manage"))
    queue_rate_restart(read_rates())
    flash("Restart został zlecony. Pasek postępu pokaże kolejne etapy.")
    return redirect(url_for("manage"))


@app.route("/api/manage-status")
@login_required
def api_manage_status():
    status = read_rate_status()
    updater = update_status()
    updater["protected"] = settings().get("auth_enabled") == "1" and bool(session.get("seban_admin"))
    check_finished_events()
    return {"ok": True, "restart": restart_progress(), "server_settings": server_settings_status(), "updater": updater, "rates": read_rates(), "events": read_events_status(), "bots": len(live_bots()), "maps": live_map_counts()}


@app.route("/api/notifications")
@login_required
def api_notifications():
    """Dzwoneczek w base.html -- wspólny dla całego panelu, karmiony przez
    trzy źródła (koniec eventu / nowa wersja / podsumowanie dnia). Wywołuje
    detekcję przy okazji (jak reszta panelu: żaden osobny proces w tle)."""
    check_all_notifications()
    items = rows("""SELECT id,kind,title,body,link_url,ref_id,created_at,read_at,popped_at
      FROM player.web_seban_notifications ORDER BY created_at DESC LIMIT 30""")
    for item in items:
        item["created_at"] = item["created_at"].strftime("%d.%m %H:%M")
        item["read"] = item["read_at"] is not None
        item["popped"] = item["popped_at"] is not None
        del item["read_at"], item["popped_at"]
    unread = one("SELECT COUNT(*) AS n FROM player.web_seban_notifications WHERE read_at IS NULL")
    return {"ok": True, "unread_count": int(unread.get("n") or 0), "items": items}


def _notification_ids_from_request():
    try:
        return [int(value) for value in request.get_json(silent=True, force=True).get("ids", [])]
    except (AttributeError, TypeError, ValueError):
        return []


@app.post("/api/notifications/read")
@login_required
def api_notifications_read():
    ids = _notification_ids_from_request()
    if ids:
        placeholders = ",".join(["%s"] * len(ids))
        rows(f"UPDATE player.web_seban_notifications SET read_at=NOW() WHERE id IN ({placeholders}) AND read_at IS NULL", ids)
    return {"ok": True}


@app.post("/api/notifications/read-all")
@login_required
def api_notifications_read_all():
    rows("UPDATE player.web_seban_notifications SET read_at=NOW() WHERE read_at IS NULL")
    return {"ok": True}


@app.post("/api/notifications/pop")
@login_required
def api_notifications_pop():
    """Oznacza że dany wpis pokazał się już jako toast na żywo -- osobno od
    'read', żeby dzwoneczek dalej liczył go jako nieprzeczytany dopóki
    ktoś faktycznie nie otworzy listy/nie kliknie."""
    ids = _notification_ids_from_request()
    if ids:
        placeholders = ",".join(["%s"] * len(ids))
        rows(f"UPDATE player.web_seban_notifications SET popped_at=NOW() WHERE id IN ({placeholders}) AND popped_at IS NULL", ids)
    return {"ok": True}


@app.route("/api/heat-events")
@login_required
def api_heat_events():
    event_type = request.args.get("type", "deaths").strip().lower()
    event_types = {"deaths": "DEAD_BY_NPC", "metins": "STONE_KILL", "bosses": "BOSS_KILL"}
    how = event_types.get(event_type)
    if not how:
        abort(400)
    raw = rows("""SELECT l.x,l.y,l.time,p.name FROM log.log l LEFT JOIN player.player p ON p.id=l.who
        WHERE l.type='CHARACTER' AND l.how=%s AND l.time >= NOW() - INTERVAL 24 HOUR ORDER BY l.time DESC LIMIT 4000""", (how,))
    events = []
    for event in raw:
        for index, bound in MAP_BOUNDS.items():
            if bound[0] <= event["x"] < bound[0] + bound[2] and bound[1] <= event["y"] < bound[1] + bound[3]:
                events.append({"map_index": index, "x": event["x"], "y": event["y"], "time": event["time"].isoformat(), "name": event.get("name")})
                break
    return {"ok": True, "type": event_type, "events": events, "bounds": MAP_BOUNDS}


from item_grants import install as install_item_grants
install_item_grants(app, db, login_required, game_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7789)
