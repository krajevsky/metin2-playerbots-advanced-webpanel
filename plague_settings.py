"""NerrVoVy's Plague Dungeon (#575) for this panel: the classic panel's /plague
page, ported (Tieru, 3 November: both add-ons manageable in both panels, the
classic one the main). The same world flag (m2_plague_enabled in player.quest,
made live through web_admin.quest's PLAGUE), the same settings row
(player.local_plague_config, which the quest reads at the guard and freezes into
a run at its first login) and the same limits; a revision refuses a form opened
before another save, and every write first copies what it replaces into the
spool (plague-backups/). Players only: bots and companions never enter."""
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
import hmac, json, re, secrets
from flask import abort, flash, redirect, render_template, request, session, url_for
from plague_settings_text import text

FLAG = 'm2_plague_enabled'
MOBS = tuple(range(1200, 1207)) + (8437, 8438) + tuple(range(9251, 9257))
ITEMS = tuple(range(30734, 30740))
# (column, lowest, highest): the quest's own limits - a reward is paid only
# while the purse stays under 2 000 000 000.
FIELDS = (('entry_yang', 0, 1000000000), ('pass_count', 0, 200), ('pass_price', 0, 1000000000),
          ('reward_yang', 0, 1000000000), ('reward_exp', 0, 2000000000))
MAX_COUNT = 200
DEFAULTS = dict(entry_yang=0, pass_count=1, pass_price=100000, reward_yang=250000, reward_exp=500000,
                reward_item1=0, reward_count1=0, reward_item2=0, reward_count2=0, reward_item3=0, reward_count3=0)
CONFIG_SQL = 'SELECT * FROM player.local_plague_config WHERE id=1'
FLAG_SQL = 'SELECT lValue FROM player.quest WHERE dwPID=0 AND szName=%s LIMIT 1'


@lru_cache(maxsize=2)
def names(language):
    """The official English and Turkish item names the panel ships (static/)."""
    path = Path(__file__).parent / 'static' / ('item_names_' + language + '.json')
    return json.loads(path.read_text(encoding='utf8')) if path.is_file() else {}


def parse(form, language, item_exists=None):
    """The settings out of the page's form, or ValueError naming the field."""
    t = lambda key: text(key, language)
    values = {}
    for key, low, high in FIELDS:
        raw = (form.get(key, '') or '').strip().replace(' ', '').replace(' ', '')
        if not re.fullmatch(r'\d{1,10}', raw) or not low <= int(raw) <= high:
            raise ValueError(t('bad_number') % (t(key), low, high))
        values[key] = int(raw)
    vnums = []
    for i in (1, 2, 3):
        vnum = (form.get('reward_item%d' % i, '0') or '0').strip()
        count = (form.get('reward_count%d' % i, '0') or '0').strip()
        if not re.fullmatch(r'\d{1,10}', vnum) or not re.fullmatch(r'\d{1,4}', count):
            raise ValueError(t('bad_item') % i)
        vnum, count = int(vnum), int(count)
        if vnum == 0:
            count = 0
        elif not 1 <= count <= MAX_COUNT:
            raise ValueError(t('bad_count') % (i, MAX_COUNT))
        elif vnum in vnums:
            raise ValueError(t('repeat') % i)
        if vnum:
            vnums.append(vnum)
        values['reward_item%d' % i] = vnum
        values['reward_count%d' % i] = count
    if item_exists is not None:
        missing = sorted(set(vnums) - set(item_exists(vnums)))
        if missing:
            raise ValueError(t('no_item') % ', '.join(str(v) for v in missing))
    return values


def read_config(row):
    cfg = dict(DEFAULTS)
    for key in cfg:
        if row and row.get(key) is not None:
            cfg[key] = int(row[key])
    cfg['revision'] = int((row or {}).get('revision') or 0)
    return cfg


def register(app, api):
    def language(): return api['settings']().get('ui_language', 'pl')
    def t(key): return text(key, language())
    def supported(): return bool(api.get('ENGINE_MT2009', False))
    def authorized():
        if not supported(): abort(404)
        if api['settings']().get('auth_enabled') == '1' and not session.get('seban_admin'): abort(403)

    def item_names(vnums):
        vnums = sorted({int(v) for v in vnums if int(v) > 0})
        if not vnums: return {}
        found = api['rows']('SELECT vnum,HEX(locale_name) name_hex FROM world.item_proto WHERE vnum IN ('
                            + ','.join(['%s'] * len(vnums)) + ')', tuple(vnums))
        lang = language(); out = {}
        for row in found:
            vnum = int(row['vnum'])
            translated = names(lang).get(str(vnum)) if lang in ('en', 'tr') else None
            if translated:
                out[vnum] = translated[-1] if isinstance(translated, list) else translated
            elif row.get('name_hex'):
                out[vnum] = bytes.fromhex(row['name_hex']).decode('cp1250', 'replace')
            else:
                out[vnum] = str(vnum)
        return out

    def backup(payload):
        folder = Path(api['RATES_SPOOL']) / 'plague-backups'; folder.mkdir(parents=True, exist_ok=True)
        path = folder / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + secrets.token_hex(4) + '.json')
        path.write_text(json.dumps(dict(panel='seban', **payload), default=str), encoding='utf8')

    def switch(value):
        """The flag in one transaction after its backup; then made live."""
        connection = api['db']()
        try:
            connection.begin()
            with connection.cursor() as cur:
                cur.execute(FLAG_SQL + ' FOR UPDATE', (FLAG,))
                before = cur.fetchall()
                backup(dict(flag=FLAG, before=before))
                cur.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', %s)",
                            (FLAG, int(value)))
            connection.commit()
        except BaseException:
            connection.rollback(); raise
        finally:
            connection.close()
        try:
            status, queue_id = api['queue_game_admin_command']('PLAGUE', str(int(value)))
        except Exception:
            status, queue_id = 'failed', 0
        if status == 'done':
            return t('live_open' if value else 'live_closed')
        if status == 'timeout' and queue_id:
            api['cancel_pending_admin_command'](queue_id)
        return t('next_start')

    def save(form):
        exists = lambda vnums: set(item_names(vnums))
        values = parse(form, language(), exists)
        try: revision = int(form.get('revision', '-1'))
        except (TypeError, ValueError): revision = -1
        connection = api['db']()
        try:
            connection.begin()
            with connection.cursor() as cur:
                cur.execute(CONFIG_SQL + ' FOR UPDATE')
                locked = cur.fetchall()
                if len(locked) != 1: raise LookupError('missing')
                if int(locked[0].get('revision') or 0) != revision: raise ValueError(t('stale'))
                backup(dict(config=locked))
                cols = list(values)
                cur.execute('UPDATE player.local_plague_config SET ' + ', '.join('%s=%%s' % c for c in cols)
                            + ', revision=revision+1 WHERE id=1 AND revision=%s',
                            [values[c] for c in cols] + [revision])
            connection.commit()
        except BaseException:
            connection.rollback(); raise
        finally:
            connection.close()

    @app.context_processor
    def context(): return dict(plague_supported=supported(), plague_t=t)

    @app.route('/manage/plague', methods=['GET', 'POST'])
    @api['login_required']
    def plague_settings_page():
        authorized()
        token = session.setdefault('plague_csrf', secrets.token_hex(32))
        if request.method == 'POST':
            if not hmac.compare_digest(token, request.form.get('csrf', '')): abort(403)
            action = request.form.get('action', '')
            try:
                if action in ('open', 'close'):
                    flash(switch(1 if action == 'open' else 0), 'success')
                elif action == 'save':
                    save(request.form); flash(t('saved'), 'success')
            except ValueError as exc:
                flash(str(exc), 'error')
            except LookupError:
                flash(t('missing'), 'error')
            except Exception:
                app.logger.exception('Plague Dungeon save failed'); flash(t('failed'), 'error')
            return redirect(url_for('plague_settings_page'))
        cfg = None; is_open = False; ready = dict(mobs=0, items=0, ok=False)
        try:
            found = api['rows'](CONFIG_SQL)
            if found: cfg = read_config(found[0])
            flag = api['rows'](FLAG_SQL, (FLAG,))
            is_open = bool(flag) and int(flag[0]['lValue'] or 0) == 1
            count = lambda table, vnums: int((api['rows']('SELECT COUNT(*) AS n FROM ' + table + ' WHERE vnum IN ('
                                                         + ','.join(['%s'] * len(vnums)) + ')', vnums)
                                              or [dict(n=0)])[0]['n'])
            mobs, items = count('world.mob_proto', MOBS), count('world.item_proto', ITEMS)
            ready = dict(mobs=mobs, items=items, ok=mobs == len(MOBS) and items == len(ITEMS))
        except Exception:
            app.logger.exception('Plague Dungeon read failed')
        reward_names = item_names([cfg['reward_item%d' % i] for i in (1, 2, 3)]) if cfg else {}
        return render_template('plague_settings.html', cfg=cfg, fields=FIELDS, names=reward_names,
                               is_open=is_open, ready=ready, csrf=token, mob_total=len(MOBS), item_total=len(ITEMS))
