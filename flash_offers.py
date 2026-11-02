"""Operator-created offers in MT2009's native ItemShop, never a purchase path."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import hmac
import re
import secrets
import time
import pymysql

from flask import abort, flash, g, jsonify, redirect, render_template, request, session, url_for

ZONE = ZoneInfo("Europe/Warsaw")
MAX_INT = 2147483647
# BuyItem accepts at most ten bundles and multiplies the price in a 32-bit
# signed long. The progress display multiplies remaining stock by 100.
MAX_PRICE = MAX_INT // 10
MAX_STOCK = MAX_INT // 100
LOCK_NAME = "web_flash_offer_create"
# The native tables can be MyISAM. A Python transaction alone cannot roll them
# back or stop two workers allocating the same id. Keep their table locks short;
# never wait for an online GM while holding them.
TABLE_LOCKS = ("common.web_flash_config READ, common.web_flash_offers WRITE, "
               "common.itemshop_items WRITE, common.itemshop_time_auctions WRITE, "
               "player.itemshop_time_auction WRITE, common.itemshop_promotions READ, "
               "common.m2_itemshop_price_base WRITE")


class InvalidOffer(ValueError):
    pass


def validate(form, now=None):
    """Return UTC-naive DB values, refusing ambiguous/nonexistent Warsaw time."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(tzinfo=None)
    result = {}
    for field, low, high in (("vnum", 1, MAX_INT), ("count", 1, 200),
                             ("price", 1, MAX_PRICE), ("minLevel", 0, 255),
                             ("max_amount", 1, MAX_STOCK), ("account_limit", 0, MAX_STOCK)):
        text = str(form.get(field, ""))
        if not re.fullmatch(r"[0-9]{1,10}", text):
            raise InvalidOffer("numbers")
        value = int(text)
        if not low <= value <= high:
            raise InvalidOffer("numbers")
        result[field] = value
    if result["max_amount"] % result["count"] or result["account_limit"] % result["count"]:
        raise InvalidOffer("multiples")
    if form.get("currency") not in ("DRAGON_COIN", "DRAGON_MARK"):
        raise InvalidOffer("currency")
    result["currency"] = form["currency"]
    for field in ("start_time", "end_time"):
        try:
            local = datetime.strptime(form.get(field, ""), "%Y-%m-%dT%H:%M")
        except (ValueError, TypeError):
            raise InvalidOffer("date") from None
        first, second = (local.replace(tzinfo=ZONE, fold=fold) for fold in (0, 1))
        if first.utcoffset() != second.utcoffset():
            raise InvalidOffer("dst")
        if first.astimezone(timezone.utc).astimezone(ZONE).replace(tzinfo=None) != local:
            raise InvalidOffer("dst")
        result[field] = first.astimezone(timezone.utc).replace(tzinfo=None)
    if result["end_time"] <= result["start_time"] or result["end_time"] <= now:
        raise InvalidOffer("order")
    if result["start_time"] < now - timedelta(minutes=5):
        raise InvalidOffer("past")
    if result["end_time"].year >= 2038:
        raise InvalidOffer("range")
    return result


@contextmanager
def locked(db):
    with db() as con, con.cursor() as cur:
        cur.execute("SELECT GET_LOCK(%s,5) acquired", (LOCK_NAME,))
        if cur.fetchone()["acquired"] != 1:
            raise InvalidOffer("busy")
        tables_locked = False
        try:
            # GET_LOCK does not bound metadata/table-lock waits. A pending
            # writer can also hold up the core's synchronous purchase reads.
            cur.execute("SET SESSION lock_wait_timeout=3")
            try:
                cur.execute("LOCK TABLES " + TABLE_LOCKS)
            except pymysql.OperationalError as exc:
                if exc.args[0] == 1205:
                    raise InvalidOffer("busy") from None
                raise
            tables_locked = True
            yield cur
        finally:
            try:
                if tables_locked:
                    cur.execute("UNLOCK TABLES")
            finally:
                cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))


ITEM_FIELDS = ("vnum", "count", "price", "currency", "minLevel")
AUCTION_FIELDS = ("max_amount", "account_limit", "start_time", "end_time")


def update_item(cur, index, values):
    cur.execute("UPDATE common.itemshop_items SET vnum=%s,`count`=%s,price=%s,"
                "currency=%s,minLevel=%s WHERE `index`=%s",
                tuple(values[key] for key in ITEM_FIELDS) + (index,))


def update_window(cur, index, values):
    # TIMESTAMP columns and a non-UTC DB session both need a numeric epoch.
    times = tuple(int(values[key].replace(tzinfo=timezone.utc).timestamp())
                  for key in ("start_time", "end_time"))
    cur.execute("UPDATE common.itemshop_time_auctions SET max_amount=%s,account_limit=%s,"
                "start_time=FROM_UNIXTIME(%s),end_time=FROM_UNIXTIME(%s) WHERE item_index=%s",
                (values["max_amount"], values["account_limit"]) + times + (index,))


def save_offer(db, values, edit=0):
    """Only managed, unstarted, unbought rows are editable; never reset a counter."""
    with locked(db) as cur:
        cur.execute("SELECT enabled FROM common.web_flash_config WHERE id=1")
        if not (cur.fetchone() or {}).get("enabled"):
            raise InvalidOffer("disabled")
        cur.execute("SELECT UNIX_TIMESTAMP() server_now")
        now = cur.fetchone()["server_now"]
        if int(values["end_time"].replace(tzinfo=timezone.utc).timestamp()) <= now:
            raise InvalidOffer("order")
        if int(values["start_time"].replace(tzinfo=timezone.utc).timestamp()) < now - 300:
            raise InvalidOffer("past")
        if edit:
            cur.execute("SELECT cancelled FROM common.web_flash_offers WHERE item_index=%s", (edit,))
            managed = cur.fetchone()
            cur.execute("SELECT *,UNIX_TIMESTAMP(start_time) start_epoch,"
                        "UNIX_TIMESTAMP(end_time) end_epoch,UNIX_TIMESTAMP() server_now "
                        "FROM common.itemshop_time_auctions WHERE item_index=%s", (edit,))
            old_window = cur.fetchone()
            cur.execute("SELECT buy_count FROM player.itemshop_time_auction WHERE item_index=%s", (edit,))
            counter = cur.fetchone()
            if (not managed or managed["cancelled"] or not old_window or not counter
                    or counter["buy_count"] or old_window["start_epoch"] <= old_window["server_now"]):
                raise InvalidOffer("not_editable")
            cur.execute("SELECT * FROM common.itemshop_items WHERE `index`=%s", (edit,))
            old_item = cur.fetchone()
            if not old_item:
                raise InvalidOffer("not_editable")
            # Preserve MyISAM rows too if the second statement fails.
            for key in ("start_time", "end_time"):
                old_window[key] = datetime.fromtimestamp(old_window[key.replace("time", "epoch")], timezone.utc).replace(tzinfo=None)
            try:
                update_item(cur, edit, values)
                update_window(cur, edit, values)
            except Exception:
                update_item(cur, edit, old_item)
                update_window(cur, edit, old_window)
                raise
            return edit
        cur.execute("SELECT GREATEST(COALESCE((SELECT MAX(`index`) FROM common.itemshop_items),0),"
                    "COALESCE((SELECT MAX(item_index) FROM common.itemshop_time_auctions),0),"
                    "COALESCE((SELECT MAX(item_index) FROM player.itemshop_time_auction),0),"
                    "COALESCE((SELECT MAX(item_index) FROM common.itemshop_promotions),0),"
                    "COALESCE((SELECT MAX(`index`) FROM common.m2_itemshop_price_base),0),"
                    "COALESCE((SELECT MAX(item_index) FROM common.web_flash_offers),0))+1 next_id")
        index = int(cur.fetchone()["next_id"])
        if index > MAX_INT:
            raise InvalidOffer("ids")
        added = []
        try:
            cur.execute("INSERT INTO player.itemshop_time_auction (item_index,buy_count) VALUES (%s,0)", (index,))
            added.append(("player.itemshop_time_auction", "item_index"))
            cur.execute("INSERT INTO common.itemshop_time_auctions "
                        "(item_index,max_amount,account_limit,start_time,end_time) "
                        "VALUES (%s,%s,%s,FROM_UNIXTIME(%s),FROM_UNIXTIME(%s))",
                        (index, values["max_amount"], values["account_limit"],
                         *(int(values[key].replace(tzinfo=timezone.utc).timestamp()) for key in ("start_time", "end_time"))))
            added.append(("common.itemshop_time_auctions", "item_index"))
            cur.execute("INSERT INTO common.web_flash_offers (item_index,created_at) VALUES (%s,UTC_TIMESTAMP())", (index,))
            added.append(("common.web_flash_offers", "item_index"))
            cur.execute("INSERT INTO common.m2_itemshop_price_base (`index`,base,applied,own) VALUES (%s,%s,%s,1)",
                        (index, values["price"], values["price"]))
            added.append(("common.m2_itemshop_price_base", "`index`"))
            # InitializeItemShop starts from items: an item without its window
            # is an unlimited regular sale. Publish the item last, so even a
            # lost connection that prevents compensation cannot create one.
            # Register cleanup first too: an executed INSERT may lose its ACK.
            added.append(("common.itemshop_items", "`index`"))
            cur.execute("INSERT INTO common.itemshop_items (`index`,vnum,`count`,price,currency,minLevel) "
                        "VALUES (%s,%s,%s,%s,%s,%s)", (index,) + tuple(values[key] for key in ITEM_FIELDS))
        except Exception:
            for table, column in reversed(added):
                cur.execute("DELETE FROM " + table + " WHERE " + column + "=%s", (index,))
            raise
        return index


def cancel_offer(db, index):
    with locked(db) as cur:
        cur.execute("SELECT item_index FROM common.web_flash_offers WHERE item_index=%s", (index,))
        if not cur.fetchone():
            raise InvalidOffer("missing")
        cur.execute("SELECT end_time FROM common.itemshop_time_auctions WHERE item_index=%s", (index,))
        previous = cur.fetchone()
        if not previous:
            raise InvalidOffer("missing")
        try:
            cur.execute("UPDATE common.itemshop_time_auctions SET end_time=LEAST(end_time,NOW()) WHERE item_index=%s", (index,))
            cur.execute("UPDATE common.web_flash_offers SET cancelled=1 WHERE item_index=%s", (index,))
        except Exception:
            cur.execute("UPDATE common.itemshop_time_auctions SET end_time=%s WHERE item_index=%s", (previous["end_time"], index))
            raise


def request_reload(api, wait=5, clock=time.monotonic, sleep=time.sleep):
    """Only a live IMPLEMENTOR can acknowledge the reload; last_play is not online.

    Probe all matching GM characters concurrently through the existing queue,
    then withdraw pending probes so an offline GM cannot serve them on login.
    Multiple already-claimed reloads are harmless, unlike player actions.
    """
    gms = api["rows"]("""SELECT DISTINCT p.name AS mName FROM common.gmlist g
        JOIN player.player p ON p.name=g.mName JOIN account.account a ON a.id=p.account_id AND a.login=g.mAccount
        WHERE g.mAuthority='IMPLEMENTOR' ORDER BY p.name""")
    if not gms:
        return False
    ids = []
    try:
        with api["db"]() as con, con.cursor() as cur:
            for gm in gms:
                cur.execute("INSERT INTO player.web_admin_queue (player_name,cmd,arg1,arg2) VALUES (%s,%s,%s,%s)",
                            (gm["mName"], "GM_RELOAD", "itemshop", ""))
                ids.append(cur.lastrowid)
        marks = ",".join(["%s"] * len(ids))
        deadline = clock() + wait
        while clock() < deadline:
            sleep(0.25)
            replies = api["rows"]("SELECT id,status FROM player.web_admin_queue WHERE id IN (" + marks + ")", tuple(ids))
            if any(row["status"] == "done" for row in replies):
                return True
            if len(replies) == len(ids) and all(row["status"] in api["QUEUE_FINAL_STATUSES"] for row in replies):
                return False
        return False
    finally:
        if ids:
            api["rows"]("UPDATE player.web_admin_queue SET status='cancelled' WHERE status='pending' AND id IN (" +
                        ",".join(["%s"] * len(ids)) + ")", tuple(ids))


def register(app, api):
    from flash_offers_text import text

    def t(key):
        if not hasattr(g, "flash_language"):
            g.flash_language = api["settings"]().get("ui_language", "pl")
        return text(key, g.flash_language)

    app.jinja_env.globals["flash_t"] = t
    app.jinja_env.globals["flash_supported"] = api["ENGINE_MT2009"]

    def available():
        if not api["ENGINE_MT2009"]:
            return False
        if not hasattr(g, "flash_schema_ready"):
            try:
                row = api["one"]("SELECT COUNT(*) AS present FROM information_schema.TABLES WHERE TABLE_SCHEMA='common' "
                                 "AND TABLE_NAME IN ('web_flash_config','web_flash_offers','m2_itemshop_price_base')")
                g.flash_schema_ready = row.get("present") == 3
            except pymysql.MySQLError:
                g.flash_schema_ready = False
        return g.flash_schema_ready

    app.jinja_env.globals["flash_available"] = available

    def csrf():
        expected = session.get("flash_csrf")
        supplied = request.form.get("csrf", "")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", supplied) or not hmac.compare_digest(expected, supplied):
            abort(403)

    def enabled():
        return bool(api["one"]("SELECT enabled FROM common.web_flash_config WHERE id=1").get("enabled"))

    def check_engine():
        if not api["ENGINE_MT2009"]:
            abort(404)

    def reload_shop():
        try:
            if request_reload(api):
                flash(t("saved_reload"), "success")
                return
        except Exception:
            app.logger.warning("PLAYERBOT_FLASH: saved offer; ItemShop reload queue unavailable")
        flash(t("saved_manual"), "warning")

    def offers():
        result = api["rows"]("""SELECT i.*,a.max_amount,a.account_limit,a.start_time,a.end_time,
            COALESCE(c.buy_count,0) buy_count,w.cancelled,p.locale_name item_name,
            UNIX_TIMESTAMP() server_now,UNIX_TIMESTAMP(a.start_time) start_epoch,UNIX_TIMESTAMP(a.end_time) end_epoch
            FROM common.web_flash_offers w JOIN common.itemshop_items i ON i.`index`=w.item_index
            JOIN common.itemshop_time_auctions a ON a.item_index=i.`index`
            LEFT JOIN player.itemshop_time_auction c ON c.item_index=i.`index`
            LEFT JOIN world.item_proto p ON p.vnum=i.vnum ORDER BY i.`index` DESC LIMIT 200""")
        for row in result:
            row["item_name"] = api["game_text"](row.get("item_name"))
            row["state"] = ("cancelled" if row["cancelled"] else "ended" if row["end_epoch"] <= row["server_now"] else
                            "planned" if row["start_epoch"] > row["server_now"] else
                            "sold_out" if row["buy_count"] >= row["max_amount"] else "active")
            row["editable"] = row["state"] == "planned" and row["buy_count"] == 0
            for key in ("start_time", "end_time"):
                row[key + "_local"] = datetime.fromtimestamp(row[key.replace("time", "epoch")], ZONE).strftime("%Y-%m-%dT%H:%M")
        return result

    @app.route("/economy/flash-offers", methods=["GET", "POST"])
    @api["login_required"]
    def flash_offers():
        check_engine()
        if not available():
            return render_template("flash_offers_unavailable.html"), 503
        error, form = None, None
        if request.method == "POST":
            csrf()
            form = request.form.to_dict()
            try:
                values = validate(form)
                if not api["one"]("SELECT vnum FROM world.item_proto WHERE vnum=%s", (values["vnum"],)):
                    raise InvalidOffer("item_missing")
                edit_text = form.get("edit_id", "") or "0"
                if not re.fullmatch(r"[0-9]{1,10}", edit_text) or int(edit_text) > MAX_INT:
                    raise InvalidOffer("not_editable")
                save_offer(api["db"], values, int(edit_text))
                reload_shop()
                return redirect(url_for("flash_offers"))
            except InvalidOffer as exc:
                error = t(str(exc))
        current = offers()
        if form is None:
            selected = request.args.get("edit", type=int)
            form = next((dict(r, edit_id=selected, start_time=r["start_time_local"], end_time=r["end_time_local"])
                         for r in current if r["index"] == selected and r["editable"]), {})
            if not form:
                now = datetime.now(ZONE)
                form = dict(count=1, price="", minLevel=0, max_amount="", account_limit="", currency="DRAGON_COIN",
                            start_time=now.strftime("%Y-%m-%dT%H:%M"), end_time=(now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"))
        session.setdefault("flash_csrf", secrets.token_hex(32))
        return render_template("flash_offers.html", offers=current, form=form, error=error,
                               csrf=session["flash_csrf"], flash_enabled=enabled(),
                               flash_max_price=MAX_PRICE, flash_max_stock=MAX_STOCK)

    @app.post("/economy/flash-offers/enabled")
    @api["login_required"]
    def flash_offer_enabled():
        check_engine()
        csrf()
        if not available():
            abort(503)
        value = request.form.get("enabled")
        if value not in ("0", "1"):
            abort(400)
        api["rows"]("UPDATE common.web_flash_config SET enabled=%s WHERE id=1", (int(value),))
        return redirect(url_for("flash_offers"))

    @app.post("/economy/flash-offers/<int:index>/cancel")
    @api["login_required"]
    def flash_offer_cancel(index):
        check_engine()
        csrf()
        if not available():
            abort(503)
        try:
            cancel_offer(api["db"], index)
        except InvalidOffer:
            abort(404)
        reload_shop()
        return redirect(url_for("flash_offers"))

    @app.get("/economy/flash-offers/items")
    @api["login_required"]
    def flash_offer_items():
        check_engine()
        if not available():
            abort(503)
        if not enabled():
            abort(409)
        q = request.args.get("q", "").strip()[:64]
        if not q:
            return jsonify([])
        language = api["settings"]().get("ui_language", "pl")
        predicate, params = api["item_name_search"](q, language, internal=False)
        found = api["rows"]("SELECT vnum,locale_name FROM world.item_proto WHERE " + predicate + " ORDER BY vnum LIMIT 30", tuple(params))
        return jsonify([dict(vnum=r["vnum"], name=api["translations"].item_display_name(
            r["vnum"], api["game_text"](r["locale_name"]), language)) for r in found])
