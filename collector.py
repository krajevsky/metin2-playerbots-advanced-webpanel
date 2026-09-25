import os
import re
import time
from datetime import datetime
from pathlib import Path

import pymysql

INTERVAL = int(os.environ.get("SEBAN_COLLECTOR_INTERVAL", "300"))
CHANNEL_VAR_ROOT = Path(os.environ.get("PLAYERBOTS_VAR_ROOT", "/opt/metin2/var"))


def discovered_channels():
    """Same discovery as app.py's -- kept duplicated since this runs in its
    own process, not imported. Sorted channel numbers with a live var dir."""
    found = []
    try:
        for path in CHANNEL_VAR_ROOT.glob("channel*"):
            match = re.fullmatch(r"channel(\d+)", path.name)
            if match and path.is_dir():
                found.append(int(match.group(1)))
    except OSError:
        pass
    return sorted(found) or [1]


def status_paths():
    for channel in discovered_channels():
        try:
            for path in CHANNEL_VAR_ROOT.glob(f"channel{channel}/*/playerbot_status.tsv"):
                yield channel, path
        except OSError:
            continue


def connect():
    return pymysql.connect(host=os.environ.get("DB_HOST", "mariadb"), port=int(os.environ.get("DB_PORT", "3306")), user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"], charset="utf8mb4", autocommit=True)


def decode_cp1250(value):
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("cp1250", "replace")
    return value or ""


def check_plus9_refines(cur):
    """Gold "/b"-style server announcement when a real player (not a bot --
    they refine to +9 constantly, that would be pure spam) upgrades
    something to +9. Off by default, toggled from /manage
    ('announce_plus9_refines' in common.m2_switches). Queues one NOTICE
    command (see web_admin.quest) for the player who just refined -- they
    are guaranteed online, they just acted -- and that quest's own poll
    loop calls notice_all(), the same Lua function /b uses, next tick.
    The watermark ('plus9_announce_watermark') is a unix timestamp, not a
    formatted datetime: common.m2_switches.value is only VARCHAR(16)."""
    cur.execute("SELECT value FROM common.m2_switches WHERE name='announce_plus9_refines'")
    row = cur.fetchone()
    if not row or str(row[0]) != "1":
        return
    cur.execute("SELECT value FROM common.m2_switches WHERE name='plus9_announce_watermark'")
    row = cur.fetchone()
    last_time = datetime.fromtimestamp(int(row[0])) if row else datetime(2000, 1, 1)
    cur.execute("""SELECT l.time, l.hint, p.name FROM log.log l
      JOIN player.player p ON p.id = l.who
      WHERE l.how='REFINE SUCCESS' AND l.hint LIKE '%%+9' AND l.time > %s
        AND NOT (EXISTS (SELECT 1 FROM account.account ba WHERE ba.id=p.account_id AND LEFT(ba.login,10)='playerbot_') OR p.name LIKE 'bot%%')
      ORDER BY l.time ASC LIMIT 20""", (last_time,))
    events = cur.fetchall()
    newest = last_time
    for time_val, hint, name in events:
        message = f"{decode_cp1250(name) if isinstance(name, (bytes, bytearray)) else name} ulepszył {decode_cp1250(hint)}"[:250]
        cur.execute("INSERT INTO player.web_admin_queue (player_name,cmd,arg1,arg2) VALUES (%s,'NOTICE',%s,'')", (name, message))
        newest = time_val
    if events:
        cur.execute(
            "INSERT INTO common.m2_switches (name, value) VALUES ('plus9_announce_watermark', %s) "
            "ON DUPLICATE KEY UPDATE value = VALUES(value)",
            (str(int(newest.timestamp())),))


def host_metrics(previous=None):
    try:
        with open("/host/proc/stat") as f:
            parts = f.readline().split()[1:]
        total = sum(map(int, parts)); idle = int(parts[3]) + int(parts[4])
        with open("/host/proc/meminfo") as f:
            mem = {line.split(":")[0]: int(line.split()[1]) for line in f if ":" in line}
        total_mb = mem["MemTotal"] // 1024; used_mb = (mem["MemTotal"] - mem.get("MemAvailable", mem.get("MemFree", 0))) // 1024
        disk = os.statvfs("/hostfs")
        disk_total_mb = (disk.f_blocks * disk.f_frsize) // (1024 * 1024)
        disk_used_mb = ((disk.f_blocks - disk.f_bavail) * disk.f_frsize) // (1024 * 1024)
        if previous:
            cpu = round(100 * (1 - (idle - previous[1]) / max(1, total - previous[0])), 1)
        else:
            with open("/host/proc/loadavg") as f:
                load_1m = float(f.read().split()[0])
            with open("/host/proc/cpuinfo") as f:
                cpu_count = max(1, sum(1 for line in f if line.startswith("processor")))
            cpu = round(min(100, 100 * load_1m / cpu_count), 1)
        return (total, idle), cpu, used_mb, total_mb, disk_used_mb, disk_total_mb
    except (OSError, KeyError, ValueError):
        return previous, 0, 0, 0, 0, 0


def table_exists(cur, table):
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='player' AND table_name=%s", (table,))
    return cur.fetchone() is not None


def init(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_admin_queue (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      player_name VARCHAR(24) NOT NULL, cmd VARCHAR(32) NOT NULL,
      arg1 VARCHAR(255) NOT NULL DEFAULT '', arg2 VARCHAR(255) NOT NULL DEFAULT '',
      status VARCHAR(24) NOT NULL DEFAULT 'pending',
      created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY pending (status, created), KEY player_status (player_name, status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_settings (
      name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(255) NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
    # Not created by apply.sh or any migration -- this table only ever existed
    # because it was added by hand on the previous server. Self-healing
    # CREATE here so a from-scratch install (no DB, no backups) doesn't 500
    # on every page that reads a switch (student chest, plus9 announcements,
    # real-players-in-rankings).
    cur.execute("""CREATE TABLE IF NOT EXISTS common.m2_switches (
      name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(16) NOT NULL DEFAULT '0',
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
    # Historia eventów czasowych (start/koniec + statystyki) -- popup "event
    # się skończył" i trwała lista na /events czytają stąd. Zdobycie szkatułki
    # (log.log how='GET') liczymy niezależnie od tego co bot z nią potem
    # zrobił (otworzył/sprzedał/zatrzymał), więc liczba jest dokładna mimo że
    # stan ekwipunku nie jest. Yang: "ekstra" to różnica wynikająca z bonusu,
    # policzona z sumy realnie zdobytego yangu (log.log how='GET_GOLD') w
    # oknie eventu, nie ze stanu konta.
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_event_runs (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      kind VARCHAR(16) NOT NULL, value INT NOT NULL,
      started_at DATETIME NOT NULL, ended_at DATETIME NULL,
      chest_count INT NULL, yang_extra BIGINT NULL,
      acknowledged TINYINT(1) NOT NULL DEFAULT 0,
      KEY kind_open (kind, ended_at)) ENGINE=InnoDB""")
    # Dzwoneczek powiadomień w base.html, wspólny dla całego panelu -- karmiony
    # z trzech źródeł (koniec eventu, nowa wersja Playerbots, podsumowanie
    # dnia). read_at osobno od popped_at: popped = pokazany raz jako toast na
    # żywo, read = użytkownik faktycznie otworzył dzwoneczek/kliknął.
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_notifications (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      kind VARCHAR(32) NOT NULL, title VARCHAR(255) NOT NULL, body VARCHAR(500) NULL,
      link_url VARCHAR(255) NULL, ref_id BIGINT UNSIGNED NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      read_at DATETIME NULL, popped_at DATETIME NULL,
      KEY(read_at), KEY(created_at)) ENGINE=InnoDB""")
    # Powiadomienia powstają przy okazji zwykłego ruchu na stronie (2 workery
    # gunicorn x 4 wątki), nie w jednym procesie w tle -- dwa równoległe
    # żądania mogły oba zobaczyć ten sam "otwarty" event/dzień/wersję przed
    # zapisem drugiego i wstawić dwa identyczne wpisy (duplikaty w dzwoneczku,
    # zgłoszone przez [GA]Seban 2026-09-21). Sprzątamy stare duplikaty (zostaje
    # najstarszy wpis) zanim dodamy unikalny indeks, inaczej ALTER by się
    # wywalił na już istniejących parach. Ten indeks + INSERT IGNORE w
    # create_notification() (app.py) czyni to bezpiecznym pod współbieżnością.
    # Single-table DELETE with a subquery, not the join-delete "DELETE n1
    # FROM ... n1 JOIN ... n2" form -- that form errors with "No database
    # selected" over a schema-qualified table when the connection has no
    # default database (this one doesn't -- pymysql.connect() below never
    # passes db=), even though every other query here works fine fully
    # qualified. Confirmed live 2026-09-21.
    cur.execute("""DELETE FROM player.web_seban_notifications
      WHERE ref_id IS NOT NULL AND id NOT IN (
        SELECT min_id FROM (SELECT MIN(id) AS min_id FROM player.web_seban_notifications
          WHERE ref_id IS NOT NULL GROUP BY kind, ref_id) AS keep)""")
    try:
        cur.execute("ALTER TABLE player.web_seban_notifications ADD UNIQUE INDEX IF NOT EXISTS uniq_kind_ref (kind, ref_id)")
    except pymysql.MySQLError:
        pass
    # Podsumowanie dnia: jeden wiersz na dzień świata, start/koniec dla
    # kilku metryk (migawki z web_seban_metric_snapshot) + liczniki zdarzeń
    # z log.log/event_runs w tym oknie czasowym.
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_daily_summary (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      summary_date DATE NOT NULL, day_number INT NOT NULL,
      bots_start INT, bots_end INT, yang_start BIGINT, yang_end BIGINT,
      refine9_count INT, metin_count INT, cash_start BIGINT, cash_end BIGINT,
      events_count INT, level_start INT, level_end INT, shops_start INT, shops_end INT,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY(summary_date)) ENGINE=InnoDB""")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS top_weapon_vnum INT UNSIGNED NULL")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS top_weapon_name VARCHAR(64) NULL")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS top_weapon_avg_damage INT NULL")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS top_weapon_owner_pid INT UNSIGNED NULL")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS top_weapon_owner_name VARCHAR(24) NULL")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS fish_count INT NULL")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS mining_count INT NULL")
    cur.execute("ALTER TABLE player.web_seban_daily_summary ADD COLUMN IF NOT EXISTS boss_count INT NULL")
    # /live-chat's persistent capture of PLAYERBOT_TRADE/PLAYERBOT_SHOUT
    # syslog lines -- app.py's scan_bot_chat_logs() reads/writes these
    # incrementally on every poll (see its docstring). message(191) in the
    # unique key keeps the index within InnoDB's byte limit for utf8mb4.
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_bot_chat_log (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      channel TINYINT UNSIGNED NOT NULL, pid INT UNSIGNED NOT NULL,
      name VARCHAR(64) NOT NULL, message VARCHAR(255) NOT NULL, captured_at DATETIME NOT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY uniq_msg (channel,pid,captured_at,message(191)), INDEX idx_captured (captured_at)
      ) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_chat_offset (
      path VARCHAR(255) NOT NULL PRIMARY KEY, byte_offset BIGINT UNSIGNED NOT NULL DEFAULT 0,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      ) ENGINE=InnoDB""")
    cur.execute("""INSERT IGNORE INTO player.web_seban_settings (name,value) VALUES
      ('panel_name','Metin2 Singleplayer'),('stuck_minutes','5'),('theme','empire'),('monitor_mode','vps'),
      ('setup_complete','1'),('auth_enabled','0'),('auth_password_hash','')""")
    # One-time branding migration for deployments created before the public-ready build.
    cur.execute("UPDATE player.web_seban_settings SET value='Metin2 Singleplayer' WHERE name='panel_name' AND value='Mt2009'")
    # Single-player suite: no setup wizard, no passphrase - one player at their
    # own machine (Tieru, 13 September). Skip the wizard for installs seeded
    # before this; an operator can still turn auth on from the panel.
    cur.execute("UPDATE player.web_seban_settings SET value='1' WHERE name='setup_complete' AND value='0'")
    # socket0 added 2026-09-13 so a generic Skill Book (vnum 50300 -- the
    # actual skill lives only in socket0, see resolve_item_display_name in
    # app.py) shows up as distinct rows instead of one lump sum. Disposable
    # monitoring history, not player data, so a schema change here drops and
    # recreates rather than an in-place ALTER of the primary key.
    if table_exists(cur, "web_seban_item_snapshot"):
        cur.execute("SHOW COLUMNS FROM player.web_seban_item_snapshot LIKE 'socket0'")
        if cur.fetchone() is None:
            cur.execute("DROP TABLE IF EXISTS player.web_seban_item_snapshot")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_item_snapshot (
      captured_at DATETIME NOT NULL, vnum INT UNSIGNED NOT NULL, socket0 INT NOT NULL DEFAULT 0,
      amount BIGINT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,vnum,socket0), KEY(vnum,captured_at)) ENGINE=InnoDB""")
    # channel added 2026-09-19 for CH2 support: the same map can now carry two
    # independent counts (one per channel) at the same captured_at, so the
    # primary key has to grow -- same drop/recreate approach as socket0 above,
    # disposable monitoring history rather than player data.
    if table_exists(cur, "web_seban_map_snapshot"):
        cur.execute("SHOW COLUMNS FROM player.web_seban_map_snapshot LIKE 'channel'")
        if cur.fetchone() is None:
            cur.execute("DROP TABLE IF EXISTS player.web_seban_map_snapshot")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_map_snapshot (
      captured_at DATETIME NOT NULL, channel TINYINT UNSIGNED NOT NULL DEFAULT 1, map_index INT UNSIGNED NOT NULL, character_count INT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,channel,map_index), KEY(map_index,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_system_snapshot (
      captured_at DATETIME NOT NULL PRIMARY KEY, cpu_percent DECIMAL(5,1) NOT NULL,
      ram_percent DECIMAL(5,1) NOT NULL, ram_used_mb INT UNSIGNED NOT NULL, ram_total_mb INT UNSIGNED NOT NULL,
      disk_percent DECIMAL(5,1) NOT NULL DEFAULT 0, disk_used_mb INT UNSIGNED NOT NULL DEFAULT 0,
      disk_total_mb INT UNSIGNED NOT NULL DEFAULT 0) ENGINE=InnoDB""")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_percent DECIMAL(5,1) NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_used_mb INT UNSIGNED NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_total_mb INT UNSIGNED NOT NULL DEFAULT 0")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_metric_snapshot (
      captured_at DATETIME NOT NULL, metric VARCHAR(64) NOT NULL, value BIGINT NOT NULL,
      PRIMARY KEY(captured_at,metric), KEY(metric,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_bot_position_snapshot (
      captured_at DATETIME NOT NULL, pid INT UNSIGNED NOT NULL, map_index INT UNSIGNED NOT NULL,
      x INT NOT NULL, y INT NOT NULL, PRIMARY KEY(captured_at,pid), KEY(pid,captured_at)) ENGINE=InnoDB""")
    # channel added 2026-09-19 (CH2 support) -- a bot only ever sits on one
    # channel at a time, so the primary key doesn't need to change, just a
    # plain additive column read by the player page's "last seen on" lookup.
    cur.execute("ALTER TABLE player.web_seban_bot_position_snapshot ADD COLUMN IF NOT EXISTS channel TINYINT UNSIGNED NOT NULL DEFAULT 1")
    # Offline shops (IkarusShop "stragany"): player.ikashop_offlineshop is one
    # row per open shop, player.item WHERE window='IKASHOP_OFFLINESHOP' is one
    # row per listed offer, and the offer's price for its whole stack (not
    # per unit) lives in that item's own ikashop_data JSON column
    # ({"yang":N,...}) -- there is no separate price/listing table for this
    # engine's offline shops, confirmed against a live test shop.
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_shop_snapshot (
      captured_at DATETIME NOT NULL, map_index INT UNSIGNED NOT NULL, empire TINYINT UNSIGNED NOT NULL,
      shop_count INT UNSIGNED NOT NULL, offer_count INT UNSIGNED NOT NULL,
      item_count BIGINT UNSIGNED NOT NULL, total_value BIGINT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,map_index), KEY(map_index,captured_at)) ENGINE=InnoDB""")
    # Per-vnum history of what is offered in shops, so the shop page can show
    # a price/quantity trend and answer "was this item ever on the market"
    # for items with zero active offers right now -- web_seban_shop_snapshot
    # above only keeps the per-map/empire rollup, not individual vnums.
    # socket0 added 2026-09-13, same reason and same drop/recreate approach
    # as web_seban_item_snapshot above.
    if table_exists(cur, "web_seban_shop_item_snapshot"):
        cur.execute("SHOW COLUMNS FROM player.web_seban_shop_item_snapshot LIKE 'socket0'")
        if cur.fetchone() is None:
            cur.execute("DROP TABLE IF EXISTS player.web_seban_shop_item_snapshot")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_shop_item_snapshot (
      captured_at DATETIME NOT NULL, vnum INT UNSIGNED NOT NULL, socket0 INT NOT NULL DEFAULT 0,
      offers INT UNSIGNED NOT NULL, total_units BIGINT UNSIGNED NOT NULL, total_value BIGINT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,vnum,socket0), KEY(vnum,captured_at)) ENGINE=InnoDB""")

    # "Konta i GM -> Nazwy postaci botów": a durable, queryable copy of the
    # 5400-name pool from playerbot_names.sql (the engine's own generated
    # rename list -- 1800 names/kingdom, applied once per bot the moment its
    # account exists, not when it's actively spawned; see
    # common.playerbot_name_history for who already has one). Parsed from the
    # file once (only when this table is still empty of 'base' rows) so the
    # panel can browse/search/filter 5400 rows without re-reading a 5600-line
    # SQL file on every request. 'custom' rows are names the operator adds
    # from the panel; 'blocked' marks a name (base or custom) as never to be
    # dealt out again. None of this touches a bot that already has a name --
    # see check_bot_name_reconcile() in app.py, which only ever assigns a name
    # to a bot with no common.playerbot_name_history row at all (i.e. freshly
    # seeded past the current 2500, after a real wipe/reseed).
    # name is explicitly latin1/latin1_swedish_ci -- the columns this table
    # gets JOINed against (common.playerbot_name_history.human_name,
    # player.player.name) are both that collation (the mt2009 schema's own
    # default), while this session's default is cp1250 (M2_DEFAULT_GAME_
    # LANGUAGE). A plain VARCHAR here inherited cp1250 and every query
    # joining on name/human_name/=%s failed with "Illegal mix of collations"
    # (1267) the moment the panel loaded -- caught immediately, 2026-09-22.
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_bot_name_pool (
      name VARCHAR(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL PRIMARY KEY,
      empire TINYINT UNSIGNED NOT NULL,
      pool_order INT UNSIGNED NOT NULL, source ENUM('base','custom') NOT NULL DEFAULT 'base',
      priority INT NOT NULL DEFAULT 0, blocked TINYINT(1) NOT NULL DEFAULT 0,
      note VARCHAR(255) NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      KEY empire_priority (empire, blocked, priority, pool_order)) ENGINE=InnoDB DEFAULT CHARSET=latin1""")
    # cur.fetchone() is not always a plain tuple here -- this init() also runs
    # through app.py's DictCursor at startup (_ensure_collector_tables), so
    # indexing by [0] crashed the panel with KeyError there. LIMIT 1 + "is
    # not None" (table_exists()'s own trick above) works under either cursor.
    cur.execute("SELECT 1 FROM player.web_seban_bot_name_pool WHERE source='base' LIMIT 1")
    if cur.fetchone() is None:
        names_sql = Path("/hostfs" + os.environ.get("SEBAN_M2_ROOT", "/opt/metin2-mt2009/mt2009-r41023-base")) \
            / "linux-port/docker/mariadb/playerbot/playerbot_names.sql"
        try:
            text = names_sql.read_text(encoding="latin-1", errors="replace")
        except OSError:
            text = ""
        rows = re.findall(r"\((\d+),(\d+),'([^']*)'\)", text)
        if rows:
            cur.executemany(
                "INSERT IGNORE INTO player.web_seban_bot_name_pool (pool_order,empire,name,source) VALUES (%s,%s,%s,'base')",
                [(int(n), int(empire), name) for n, empire, name in rows])
            print(f"[seban-collector] bot name pool: loaded {len(rows)} base name(s) from {names_sql}", flush=True)


def live_positions():
    result = {}
    for channel, path in status_paths():
        try:
            if time.time() - path.stat().st_mtime > 25:
                continue
            for line in path.read_text(encoding="cp1250", errors="replace").splitlines()[1:]:
                values = line.split("\t", 13)
                if len(values) == 14:
                    result[int(values[0])] = (int(values[8]), int(values[9]), int(values[10]), channel)
        except (OSError, ValueError):
            continue
    return result


def live_map_counts():
    counts = {}
    for index, _, _, channel in live_positions().values():
        counts[(channel, index)] = counts.get((channel, index), 0) + 1
    return counts


def collect(con, previous):
    now = datetime.now().replace(second=0, microsecond=0)
    previous, cpu, used, total, disk_used, disk_total = host_metrics(previous)
    ram = round(100 * used / total, 1) if total else 0
    disk_percent = round(100 * disk_used / disk_total, 1) if disk_total else 0
    with con.cursor() as cur:
        init(cur)
        cur.execute("""INSERT INTO player.web_seban_system_snapshot
          (captured_at,cpu_percent,ram_percent,ram_used_mb,ram_total_mb,disk_percent,disk_used_mb,disk_total_mb)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
          ON DUPLICATE KEY UPDATE cpu_percent=VALUES(cpu_percent), ram_percent=VALUES(ram_percent),
            ram_used_mb=VALUES(ram_used_mb), ram_total_mb=VALUES(ram_total_mb), disk_percent=VALUES(disk_percent),
            disk_used_mb=VALUES(disk_used_mb), disk_total_mb=VALUES(disk_total_mb)""",
            (now, cpu, ram, used, total, disk_percent, disk_used, disk_total))
        for (channel, map_index), count in live_map_counts().items():
            cur.execute("INSERT IGNORE INTO player.web_seban_map_snapshot (captured_at,channel,map_index,character_count) VALUES (%s,%s,%s,%s)", (now, channel, map_index, count))
        positions = live_positions()
        for pid, (map_index, x, y, channel) in positions.items():
            cur.execute("INSERT IGNORE INTO player.web_seban_bot_position_snapshot (captured_at,pid,channel,map_index,x,y) VALUES (%s,%s,%s,%s,%s,%s)", (now, pid, channel, map_index, x, y))
        # Split by socket0 only for vnum 50300 (the generic Skill Book -- see
        # resolve_item_display_name in app.py): splitting every socketed
        # item this way would fragment ordinary equipment into one row per
        # gem combination for no reason, since only 50300's socket0 changes
        # what the item actually *is*.
        cur.execute("""INSERT IGNORE INTO player.web_seban_item_snapshot (captured_at,vnum,socket0,amount)
          SELECT %s, vnum, IF(vnum=50300, socket0, 0), SUM(count)
          FROM player.item GROUP BY vnum, IF(vnum=50300, socket0, 0)""", (now,))
        cur.execute("""INSERT IGNORE INTO player.web_seban_shop_snapshot
          (captured_at, map_index, empire, shop_count, offer_count, item_count, total_value)
          SELECT %s, o.map, pi.empire, COUNT(DISTINCT o.owner), COUNT(i.id),
                 COALESCE(SUM(i.count),0),
                 COALESCE(SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(i.ikashop_data,'$.yang')) AS UNSIGNED)),0)
          FROM player.ikashop_offlineshop o
          JOIN player.player p ON p.id = o.owner
          JOIN player.player_index pi ON pi.id = p.account_id
          LEFT JOIN player.item i ON i.owner_id = o.owner AND i.window = 'IKASHOP_OFFLINESHOP'
          GROUP BY o.map, pi.empire""", (now,))
        cur.execute("""INSERT IGNORE INTO player.web_seban_shop_item_snapshot (captured_at, vnum, socket0, offers, total_units, total_value)
          SELECT %s, vnum, IF(vnum=50300, socket0, 0), COUNT(*), SUM(count),
                 COALESCE(SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(ikashop_data,'$.yang')) AS UNSIGNED)),0)
          FROM player.item WHERE window = 'IKASHOP_OFFLINESHOP' GROUP BY vnum, IF(vnum=50300, socket0, 0)""", (now,))
        cur.execute("SELECT COALESCE(SUM(gold),0) FROM player.player WHERE name NOT IN ('[SA]Admin','Test','Admin','AdminNinja','AdminSura','AdminSzaman')")
        yang = cur.fetchone()[0]
        cur.execute("INSERT IGNORE INTO player.web_seban_metric_snapshot VALUES (%s,'total_yang',%s)", (now, yang))
        # Dodatkowe migawki dla "Podsumowania dnia" (start/koniec dnia
        # porównuje dwie migawki z tej samej tabeli, jak total_yang powyżej).
        cur.execute("INSERT IGNORE INTO player.web_seban_metric_snapshot VALUES (%s,'bots_count',%s)", (now, len(positions)))
        # Tylko boty -- konto GM/admina z wysokim poziomem fałszowałoby to.
        cur.execute("""SELECT COALESCE(MAX(p.level),0) FROM player.player p
          LEFT JOIN account.account a ON a.id=p.account_id WHERE LEFT(a.login,10)='playerbot_'""")
        cur.execute("INSERT IGNORE INTO player.web_seban_metric_snapshot VALUES (%s,'max_level',%s)", (now, cur.fetchone()[0]))
        cur.execute("SELECT COALESCE(SUM(cash),0) FROM account.account")
        cur.execute("INSERT IGNORE INTO player.web_seban_metric_snapshot VALUES (%s,'dragon_coins',%s)", (now, cur.fetchone()[0]))
        cur.execute("SELECT COUNT(DISTINCT owner) FROM player.ikashop_offlineshop")
        cur.execute("INSERT IGNORE INTO player.web_seban_metric_snapshot VALUES (%s,'shops_count',%s)", (now, cur.fetchone()[0]))
        check_plus9_refines(cur)
    return previous


def main():
    previous = None
    while True:
        try:
            with connect() as con:
                previous = collect(con, previous)
                print("[seban-collector] snapshot complete", flush=True)
            time.sleep(INTERVAL)
        except Exception as exc:
            # A failed attempt (most often: MariaDB not accepting connections
            # yet, moments after a fresh `docker compose up`) used to fall
            # through to the same full-length sleep as a success, so the
            # panel's tables -- and every page that reads them -- could stay
            # missing for a whole INTERVAL (default 300s) after a restart.
            # Retry soon instead of waiting out the normal cadence.
            print(f"[seban-collector] {exc}", flush=True)
            time.sleep(10)


if __name__ == "__main__":
    main()
