"""Durable mass item grants. Items are created only by the in-game quest."""
import json
import secrets
import time

from flask import abort, flash, redirect, render_template, request, session, url_for

# 200, bo tyle wynosi pelny stos i tyle jest w stanie wydac silnik za jednym
# razem. pc.give_item2 czyta ilosc jako int i podaje ja do
# CHARACTER::AutoGiveItem(DWORD, BYTE, ...) - jeden bajt: 256 staje sie zerem,
# 300 czterdziestoma czterema, 65535 dwiescia piecdziesiecioma pieciema. Nic
# tego nie zglaszalo, bo niezerowe item_id wygladalo na sukces, wiec paczka
# konczyla sie statusem "Nadano" i mniejsza liczba sztuk, niz proszono.
# Quest odrzuca teraz wszystko powyzej 200 statusem qty_too_big; panel nie
# powinien takiej liczby w ogole proponowac.
MAX_ITEM_COUNT, MAX_PENDING = 200, 10
JOBS = (("", "Każda klasa"), ("0", "Wojownik"), ("1", "Ninja"), ("2", "Sura"), ("3", "Szaman"))
TERMINAL = {"done": "Nadano", "has_item": "Już posiada", "full": "Brak miejsca w ekwipunku",
    "failed": "Gra nie mogła utworzyć przedmiotu", "bad_args": "Nieprawidłowy VNUM lub ilość",
    "no_skill": "Warunek nie jest już spełniony", "gone": "Postać nie istnieje",
    "qty_too_big": "Ilość ponad 200 — gra nie wyda tego za jednym razem",
    "partial": "Wydano mniej, niż proszono (sprawdź plecak)",
    "cancelled": "Anulowano", "review": "Wymaga sprawdzenia", "unknown_cmd": "Quest wymaga aktualizacji"}
LABELS = {"waiting": "Czeka na wysłanie", "queued": "Przekazano aktywnej postaci", **TERMINAL}

# The worker is a separate container (seban-item-grants) and the page could
# not tell whether it was running: a batch that stopped at 333 recipients
# looked exactly like a worker that had died, a queue nobody in game was
# reading, and three hundred bots that were simply offline (audit D02). The
# worker stamps every tick into web_seban_settings; the page reads the stamp,
# the last error, and the age of the oldest task in each state, so the next
# report can say which of those it is.
HEARTBEAT_KEY, LAST_ERROR_KEY = "item_grants_heartbeat", "item_grants_last_error"
HEARTBEAT_STALE = 15          # three ticks of three seconds, with room to spare
QUEUE_STALE = 45              # a queue row older than this has nobody in game reading it

# Measured on 11 September with 1500 registered bots of which 349 were in the
# world: a batch for all of them reached done=350 in two minutes and then sat
# at queued=10 for good - the ten places of MAX_PENDING were all offline
# recipients, each of which takes 30 s for the quest's sweep to call
# player_offline, another 60 s for this worker to withdraw it, and comes back
# two minutes later, so ten offline names blocked every online one behind
# them. That is the "stops at 333" of the audit: not a terminal state, a queue
# whose head is offline. The collector's five-minute snapshot says who is in
# the world; the online recipients go first and the offline ones get at most
# OFFLINE_PROBES_PER_TICK of the places, so the queue always has room to move.
SNAPSHOT_MAX_AGE = 15 * 60
OFFLINE_PROBES_PER_TICK = 2
OFFLINE_MAX_PENDING = 4       # offline probes may hold this many of MAX_PENDING's places at once


def init(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_grants (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, batch CHAR(32) NOT NULL,
      player_id INT UNSIGNED NOT NULL, player_name VARCHAR(24) NOT NULL, vnum INT UNSIGNED NOT NULL,
      quantity INT UNSIGNED NOT NULL DEFAULT 1, criteria VARCHAR(1000) NOT NULL DEFAULT '{}',
      only_missing TINYINT(1) NOT NULL DEFAULT 1, status VARCHAR(24) NOT NULL DEFAULT 'waiting',
      queue_id INT NULL, created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, next_try DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY batch_player(batch,player_id), KEY pending(status,next_try), KEY recipient(player_id,vnum,status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_settings (
      name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(255) NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
    cur.execute("SHOW COLUMNS FROM player.web_seban_grants")
    columns = {row["Field"] for row in cur.fetchall()}
    for name, sql in (
        ("quantity", "ADD COLUMN quantity INT UNSIGNED NOT NULL DEFAULT 1 AFTER vnum"),
        ("criteria", "ADD COLUMN criteria VARCHAR(1000) NOT NULL DEFAULT '{}' AFTER quantity"),
        ("only_missing", "ADD COLUMN only_missing TINYINT(1) NOT NULL DEFAULT 1 AFTER criteria"),
    ):
        if name not in columns:
            cur.execute("ALTER TABLE player.web_seban_grants " + sql)


def number(raw, label, maximum, empty=True):
    raw = (raw or "").strip()
    if empty and not raw:
        return None
    try: value = int(raw)
    except ValueError: abort(400, f"{label}: wpisz liczbę całkowitą.")
    if not 0 <= value <= maximum: abort(400, f"{label}: dozwolony zakres to 0–{maximum}.")
    return value


def criteria_from(values):
    job = values.get("job", "")
    if job not in dict(JOBS): abort(400, "Nieprawidłowa klasa postaci.")
    criteria = {
        "min_level": number(values.get("min_level"), "Minimalny poziom", 120),
        "max_level": number(values.get("max_level"), "Maksymalny poziom", 120),
        "min_horse": number(values.get("min_horse"), "Minimalny poziom konia", 30),
        "min_playtime": number(values.get("min_playtime"), "Minimalny czas gry", 100000),
        "min_riding": number(values.get("min_riding"), "Minimalne jeździectwo", 30),
        "job": int(job) if job else None,
    }
    if criteria["min_level"] is not None and criteria["max_level"] is not None and criteria["min_level"] > criteria["max_level"]:
        abort(400, "Minimalny poziom nie może być wyższy od maksymalnego.")
    return {key: value for key, value in criteria.items() if value is not None}


def criteria_text(criteria):
    labels = []
    for key, text in (("min_level", "Lv ≥ {}"), ("max_level", "Lv ≤ {}"), ("min_horse", "Koń ≥ {}"),
                      ("min_playtime", "Czas ≥ {} h"), ("min_riding", "Jeździectwo ≥ {}")):
        if key in criteria: labels.append(text.format(criteria[key]))
    if "job" in criteria: labels.append(dict(JOBS)[str(criteria["job"])])
    return " · ".join(labels) or "Bez warunków"


def where_for(criteria, alias="p"):
    conditions, params = [], []
    for key, sql, multiplier in (
        ("min_level", f"{alias}.level >= %s", 1), ("max_level", f"{alias}.level <= %s", 1),
        ("min_horse", f"{alias}.horse_level >= %s", 1), ("min_playtime", f"{alias}.playtime >= %s", 60),
        ("job", f"MOD({alias}.job,4) = %s", 1), ("min_riding", f"ORD(SUBSTRING({alias}.skill_level,782,1)) >= %s", 1),
    ):
        if key in criteria:
            conditions.append(sql); params.append(criteria[key] * multiplier)
    return conditions, params


def has_item_sql(vnum, alias="p"):
    return f"""EXISTS(SELECT 1 FROM player.item i WHERE i.vnum=%s AND i.count>0 AND
      ((i.owner_id={alias}.id AND i.window IN ('INVENTORY','EQUIPMENT')) OR
       (i.owner_id={alias}.account_id AND i.window IN ('SAFEBOX','MALL'))))""", [vnum]


def candidates(cur, vnum, criteria, only_missing, player_id=None):
    conditions, params = where_for(criteria)
    # The tool is explicitly for Playerbots.  A level/horse filter alone can
    # also match an administrator or an ordinary player's character.
    conditions.append("(LEFT(a.login,10)='playerbot_' OR p.name LIKE 'bot%%')")
    if only_missing:
        sql, item_params = has_item_sql(vnum); conditions.append("NOT " + sql); params += item_params
    if player_id is not None: conditions.append("p.id=%s"); params.append(player_id)
    query = """SELECT p.id,p.name,p.level,p.horse_level,p.playtime,MOD(p.job,4) AS job,
      ORD(SUBSTRING(p.skill_level,782,1)) AS riding FROM player.player p
      LEFT JOIN account.account a ON a.id=p.account_id"""
    if conditions: query += " WHERE " + " AND ".join(conditions)
    cur.execute(query + " ORDER BY p.id", params)
    return cur.fetchall()


def stamp(cur, key, value):
    cur.execute("INSERT INTO player.web_seban_settings (name,value) VALUES (%s,%s) "
                "ON DUPLICATE KEY UPDATE value=VALUES(value)", (key, str(value)[:255]))


def worker_stats(cur):
    """What the page shows above the history: is the worker alive, what is
    waiting, and for how long. Every age is in seconds, None when there is
    nothing in that state."""
    stats = {"alive": False, "heartbeat_age": None, "last_error": "", "counts": {},
             "oldest_waiting": None, "oldest_queued": None, "pending": 0, "oldest_pending": None,
             "queue_stale": False}
    cur.execute("SELECT name,value,UNIX_TIMESTAMP(updated_at) AS at FROM player.web_seban_settings WHERE name IN (%s,%s)",
                (HEARTBEAT_KEY, LAST_ERROR_KEY))
    for row in cur.fetchall():
        if row["name"] == HEARTBEAT_KEY:
            try: age = max(0, int(time.time()) - int(row["value"]))
            except (TypeError, ValueError): age = None
            stats["heartbeat_age"] = age
            stats["alive"] = age is not None and age <= HEARTBEAT_STALE
        else:
            stats["last_error"] = row["value"] or ""
    cur.execute("""SELECT status,COUNT(*) AS n,MAX(TIMESTAMPDIFF(SECOND,updated,NOW())) AS oldest
                   FROM player.web_seban_grants GROUP BY status""")
    for row in cur.fetchall():
        stats["counts"][row["status"]] = int(row["n"])
        if row["status"] == "waiting": stats["oldest_waiting"] = int(row["oldest"] or 0)
        if row["status"] == "queued": stats["oldest_queued"] = int(row["oldest"] or 0)
    # The in-game side: rows the helper quest has not taken yet. A pending row
    # older than QUEUE_STALE means nothing in game is reading the queue at all
    # (no player logged in since the start, or a quest the core did not compile).
    cur.execute("SELECT COUNT(*) AS n,MAX(TIMESTAMPDIFF(SECOND,created,NOW())) AS oldest "
                "FROM player.web_admin_queue WHERE status='pending'")
    row = cur.fetchone() or {}
    stats["pending"] = int(row.get("n") or 0)
    stats["oldest_pending"] = int(row["oldest"]) if row.get("oldest") is not None else None
    stats["queue_stale"] = stats["oldest_pending"] is not None and stats["oldest_pending"] > QUEUE_STALE
    return stats


def online_pids(cur):
    """The bots the collector last saw in the world, or None when it has not
    looked recently (then nobody is preferred and the old order applies)."""
    try:
        cur.execute("SELECT MAX(captured_at) AS at, TIMESTAMPDIFF(SECOND,MAX(captured_at),NOW()) AS age "
                    "FROM player.web_seban_bot_position_snapshot")
        row = cur.fetchone() or {}
        if row.get("at") is None or int(row.get("age") or 0) > SNAPSHOT_MAX_AGE:
            return None
        cur.execute("SELECT pid FROM player.web_seban_bot_position_snapshot WHERE captured_at=%s", (row["at"],))
        return {int(r["pid"]) for r in cur.fetchall()}
    except Exception:
        return None


def pick_waiting(cur, capacity, pending=0):
    """The waiting rows this tick may hand to the game, online recipients first."""
    if capacity <= 0:
        return []
    online = online_pids(cur)
    if online is None:
        cur.execute("SELECT * FROM player.web_seban_grants WHERE status='waiting' AND next_try<=NOW() "
                    "ORDER BY next_try,id LIMIT %s FOR UPDATE", (capacity,))
        return cur.fetchall()
    # A human's character is never in the bot snapshot; it counts as "maybe
    # online" and takes the fast lane, because the quest answers for it within
    # three seconds when it is in game and the sweep retires it when it is not.
    bots_sql = ("SELECT p.id FROM player.player p JOIN account.account a ON a.id=p.account_id "
                "WHERE a.login LIKE 'playerbot_%%'")
    marks = ",".join(["%s"] * len(online)) if online else "NULL"
    cur.execute("SELECT * FROM player.web_seban_grants WHERE status='waiting' AND next_try<=NOW() "
                "AND (player_id IN (" + marks + ") OR player_id NOT IN (" + bots_sql + ")) "
                "ORDER BY next_try,id LIMIT %s FOR UPDATE", tuple(sorted(online)) + (capacity,))
    picked = list(cur.fetchall())
    # A probe sits in the queue for up to 60 s before it is withdrawn, so two
    # a tick would still fill every place in five ticks; the cap is on how many
    # can be out at once, and it always leaves the fast lane room.
    left = min(capacity - len(picked), OFFLINE_PROBES_PER_TICK, OFFLINE_MAX_PENDING - pending)
    if left > 0:
        taken = [g["id"] for g in picked]
        cur.execute("SELECT * FROM player.web_seban_grants WHERE status='waiting' AND next_try<=NOW() "
                    + ("AND id NOT IN (" + ",".join(["%s"] * len(taken)) + ") " if taken else "")
                    + "ORDER BY next_try,id LIMIT %s FOR UPDATE", tuple(taken) + (left,))
        picked.extend(cur.fetchall())
    return picked


def grant_criteria(grant):
    try:
        value = json.loads(grant["criteria"] or "{}")
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        return None


def install(app, db, login_required, game_text):
    @app.route("/manage/items", methods=["GET", "POST"])
    @login_required
    def manage_items():
        token = session.setdefault("grant_csrf", secrets.token_hex(32))
        try: vnum = int(request.values.get("vnum", "50051"))
        except (TypeError, ValueError): abort(400, "Nieprawidłowy VNUM.")
        if not 1 <= vnum <= 2147483647: abort(400, "Nieprawidłowy VNUM.")
        quantity = number(request.values.get("quantity", "1"), "Ilość", MAX_ITEM_COUNT, False)
        criteria = criteria_from(request.values)
        only_missing = (request.values.getlist("only_missing") or ["1"])[-1] == "1"
        with db() as con, con.cursor() as cur:
            init(cur)
            if request.method == "POST" and not secrets.compare_digest(request.form.get("csrf", ""), token):
                abort(400, "Odśwież formularz i spróbuj ponownie.")
            if request.method == "POST" and request.form.get("action") == "cancel":
                cur.execute("UPDATE player.web_seban_grants SET status='cancelled',updated=NOW() WHERE status='waiting' AND batch=%s", (request.form.get("batch", ""),))
                flash(f"Anulowano oczekujące nadania: {cur.rowcount}.")
                return redirect(url_for("manage_items", vnum=vnum))
            cur.execute("SELECT vnum,locale_name,type,size FROM player.item_proto WHERE vnum=%s", (vnum,))
            item = cur.fetchone()
            if not item: abort(404, "Nie ma przedmiotu o tym VNUM.")
            if not 1 <= int(item["size"] or 0) <= 3 or int(item["type"] or 0) in (0, 10, 29, 30):
                abort(400, "Ten przedmiot nie jest obsługiwany przez zwykły ekwipunek.")
            recipients = candidates(cur, vnum, criteria, only_missing)
            fingerprint = json.dumps((vnum, quantity, criteria, only_missing), sort_keys=True)
            if request.method == "POST":
                preview = session.get("grant_preview")
                if not preview or preview.get("fingerprint") != fingerprint or time.time() - preview["time"] > 900:
                    abort(400, "Najpierw odśwież podgląd odbiorców.")
                cur.execute("SELECT GET_LOCK('seban_item_grants',10) AS acquired")
                if cur.fetchone()["acquired"] != 1: abort(409, "Inne nadanie jest właśnie zapisywane.")
                try:
                    con.begin()
                    recipients = candidates(cur, vnum, criteria, only_missing)
                    criteria_json = json.dumps(criteria, separators=(",", ":"))
                    for row in recipients:
                        cur.execute("""INSERT INTO player.web_seban_grants
                          (batch,player_id,player_name,vnum,quantity,criteria,only_missing)
                          VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                          (preview["batch"], row["id"], row["name"], vnum, quantity, criteria_json, only_missing))
                    con.commit()
                except Exception:
                    con.rollback(); raise
                finally:
                    cur.execute("SELECT RELEASE_LOCK('seban_item_grants')")
                session.pop("grant_preview", None)
                flash(f"Zlecono {quantity}× VNUM {vnum} dla {len(recipients)} postaci.")
                return redirect(url_for("manage_items", vnum=vnum))
            session["grant_preview"] = {"fingerprint": fingerprint, "batch": secrets.token_hex(16), "time": time.time()}
            stats = worker_stats(cur)
            cur.execute("SELECT * FROM player.web_seban_grants ORDER BY id DESC LIMIT 1000")
            history = cur.fetchall()
            for grant in history:
                grant["criteria_text"] = criteria_text(grant_criteria(grant) or {})
            item["name"] = game_text(item["locale_name"])
            return render_template("item_grants.html", item=item, vnum=vnum, quantity=quantity, criteria=criteria,
                recipients=recipients, only_missing=only_missing, history=history, labels=LABELS, csrf=token, jobs=JOBS,
                criteria_text=criteria_text, stats=stats)


def tick(con):
    with con.cursor() as cur:
        cur.execute("SELECT GET_LOCK('seban_item_grants',0) AS acquired")
        if cur.fetchone()["acquired"] != 1: return
        try:
            con.begin()
            cur.execute("""SELECT g.*,q.status AS queue_status,TIMESTAMPDIFF(SECOND,q.created,NOW()) AS age
              FROM player.web_seban_grants g LEFT JOIN player.web_admin_queue q ON q.id=g.queue_id
              WHERE g.status='queued' FOR UPDATE""")
            for grant in cur.fetchall():
                status = grant["queue_status"]
                if status == "pending" and (grant["age"] or 0) > 60:
                    cur.execute("UPDATE player.web_admin_queue SET status='cancelled' WHERE id=%s AND status='pending'", (grant["queue_id"],))
                    if cur.rowcount: status = "player_offline"
                if status == "pending": continue
                if status and status.startswith("w"):
                    if (grant["age"] or 0) < 120: continue
                    status = "review"
                if status == "player_offline":
                    cur.execute("UPDATE player.web_seban_grants SET status='waiting',queue_id=NULL,next_try=NOW()+INTERVAL 2 MINUTE,updated=NOW() WHERE id=%s", (grant["id"],))
                else:
                    cur.execute("UPDATE player.web_seban_grants SET status=%s,updated=NOW() WHERE id=%s", (status if status in TERMINAL else "review", grant["id"]))
            cur.execute("SELECT COUNT(*) AS n FROM player.web_admin_queue WHERE status='pending'")
            pending = int(cur.fetchone()["n"])
            capacity = max(0, MAX_PENDING - pending)
            for grant in pick_waiting(cur, capacity, pending):
                criteria = grant_criteria(grant)
                player = candidates(cur, grant["vnum"], criteria, bool(grant["only_missing"]), grant["player_id"]) if criteria is not None else []
                if not player:
                    cur.execute("SELECT id FROM player.player WHERE id=%s", (grant["player_id"],))
                    status = "gone" if not cur.fetchone() else ("has_item" if grant["only_missing"] else "no_skill")
                    cur.execute("UPDATE player.web_seban_grants SET status=%s,updated=NOW() WHERE id=%s", (status, grant["id"]))
                    continue
                command = "BULK_MISSING" if grant["only_missing"] else "BULK_ITEM"
                cur.execute("INSERT INTO player.web_admin_queue(player_name,cmd,arg1,arg2) VALUES(%s,%s,%s,%s)",
                    (player[0]["name"], command, str(grant["vnum"]), str(grant["quantity"])))
                cur.execute("UPDATE player.web_seban_grants SET status='queued',queue_id=%s,updated=NOW() WHERE id=%s", (cur.lastrowid, grant["id"]))
            con.commit()
        except Exception:
            con.rollback(); raise
        finally:
            cur.execute("SELECT RELEASE_LOCK('seban_item_grants')")


def beat(error=""):
    """One row per tick, whatever the tick did. Its own connection, so a tick
    that failed halfway (and rolled back) still leaves a fresh stamp - a dead
    worker and a failing one are different problems, and the page says which."""
    from app import db
    with db() as con, con.cursor() as cur:
        stamp(cur, HEARTBEAT_KEY, int(time.time()))
        stamp(cur, LAST_ERROR_KEY, error)


if __name__ == "__main__":
    from app import db
    while True:
        error = ""
        try:
            with db() as con:
                with con.cursor() as cur: init(cur)
                tick(con)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            print(f"[item-grants] {error}", flush=True)
        try:
            beat(error)
        except Exception as exc:
            print(f"[item-grants] heartbeat: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(3)
