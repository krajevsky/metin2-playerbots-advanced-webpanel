"""Seban's panel's Plague Dungeon page (the classic /plague, ported 3 November):
real Flask routes on an in-memory database; never connects to a game DB.

    python -m pytest test_plague_settings.py
"""
from pathlib import Path
import copy, glob, json, os, sys, tempfile, unittest
from functools import wraps
from flask import Flask, session
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

PANEL = Path(__file__).resolve().parent
sys.path.insert(0, str(PANEL))
import plague_settings  # noqa: E402
from plague_settings import register, parse, FIELDS, MOBS, ITEMS, FLAG  # noqa: E402

ITEM_ROWS = {27003: 'Czerwona Mikstura (D)', 30734: 'Przepustka Zarazy'}


class Database:
    def __init__(self):
        self.flag = None
        self.cfg = dict(id=1, revision=4, entry_yang=0, pass_count=1, pass_price=100000, reward_yang=250000,
                        reward_exp=500000, reward_item1=0, reward_count1=0, reward_item2=0, reward_count2=0,
                        reward_item3=0, reward_count3=0)
        self.statements = []; self.committed = False; self.rolled_back = False; self.snapshot = None
    def begin(self): self.snapshot = copy.deepcopy((self.flag, self.cfg))
    def cursor(self): return self
    def __enter__(self): return self
    def __exit__(self, *unused): pass
    def close(self): pass
    def commit(self): self.committed = True
    def rollback(self):
        self.rolled_back = True
        if self.snapshot: self.flag, self.cfg = self.snapshot
    def execute(self, sql, args=None):
        self.statements.append((sql, args)); self.query = sql
        if sql.startswith('REPLACE INTO player.quest'):
            assert args[0] == FLAG; self.flag = args[1]
        elif sql.startswith('UPDATE player.local_plague_config'):
            if getattr(self, 'fail', False): raise RuntimeError('test rollback')
            *values, revision = args
            if revision == self.cfg['revision']:
                cols = [part.split('=')[0].strip() for part in sql.split(' SET ', 1)[1].split(', revision')[0].split(',')]
                self.cfg.update(zip(cols, values)); self.cfg['revision'] += 1
    def fetchall(self):
        if 'local_plague_config' in self.query: return [dict(self.cfg)]
        if 'player.quest' in self.query: return [] if self.flag is None else [dict(lValue=self.flag)]
        return []


class PlaguePanel(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.db = Database(); self.lang = 'pl'
        self.queued = []; self.answer = 'done'; self.cancelled = []
        self.api = dict(ENGINE_MT2009=True, RATES_SPOOL=self.temp.name)
        self.app = Flask(__name__); self.app.secret_key = 'test-only'
        self.app.jinja_loader = ChoiceLoader([DictLoader({'base.html': '{% for c, m in get_flashed_messages(with_categories=true) %}<p class="flash {{c}}">{{m}}</p>{% endfor %}{% block content %}{% endblock %}'}),
                                              FileSystemLoader(str(PANEL / 'templates'))])
        self.app.jinja_env.globals.update(item_icon=lambda unused: None, panel_brand='Test')
        def login_required(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                return fn(*args, **kwargs) if session.get('test_login') else ('login', 401)
            return wrapped
        def rows(sql, args=None):
            if 'local_plague_config' in sql: return [dict(self.db.cfg)]
            if 'player.quest' in sql: return [] if self.db.flag is None else [dict(lValue=self.db.flag)]
            if 'mob_proto' in sql: return [dict(n=len(MOBS))]
            if 'COUNT(*)' in sql and 'item_proto' in sql: return [dict(n=len(ITEMS))]
            if 'item_proto' in sql:
                return [dict(vnum=v, name_hex=ITEM_ROWS[v].encode('cp1250').hex()) for v in (args or ()) if v in ITEM_ROWS]
            return []
        def queue(cmd, arg):
            self.queued.append((cmd, arg)); return self.answer, 77
        self.api.update(login_required=login_required, settings=lambda: dict(auth_enabled='1', ui_language=self.lang),
                        rows=rows, db=lambda: self.db, queue_game_admin_command=queue,
                        cancel_pending_admin_command=self.cancelled.append)
        register(self.app, self.api); self.client = self.app.test_client()

    def tearDown(self): self.temp.cleanup()

    def login(self, admin=True):
        with self.client.session_transaction() as value: value.update(test_login=True, seban_admin=admin)

    def token(self):
        self.login(); self.assertEqual(self.client.get('/manage/plague').status_code, 200)
        with self.client.session_transaction() as value: return value['plague_csrf']

    def form(self, **extra):
        form = dict(csrf=self.token(), action='save', revision=str(self.db.cfg['revision']),
                    entry_yang='0', pass_count='2', pass_price='100 000', reward_yang='250000', reward_exp='500000',
                    reward_item1='27003', reward_count1='5', reward_item2='0', reward_count2='9',
                    reward_item3='0', reward_count3='0')
        form.update(extra); return form

    def backups(self): return glob.glob(os.path.join(self.temp.name, 'plague-backups', '*.json'))

    def test_login_admin_and_engine_boundaries(self):
        self.assertEqual(self.client.get('/manage/plague').status_code, 401)
        self.login(False); self.assertEqual(self.client.get('/manage/plague').status_code, 403)
        self.login(); self.api['ENGINE_MT2009'] = False
        self.assertEqual(self.client.get('/manage/plague').status_code, 404)

    def test_closed_by_default_in_three_languages(self):
        self.login()
        for lang, title, closed in [('pl', 'Loch Zarazy', 'Zamknięty'), ('en', 'Plague Dungeon', 'Closed'),
                                    ('tr', 'Veba Zindanı', 'Kapalı'), ('de', 'Plague Dungeon', 'Closed')]:
            self.lang = lang; body = self.client.get('/manage/plague').get_data(as_text=True)
            self.assertIn(title, body, lang); self.assertIn(closed, body, lang)
            self.assertIn('value="open"', body); self.assertEqual(body.count('method="post"'), 2)
            self.assertEqual(body.count('name="csrf"'), 2)
        self.assertIsNone(self.db.flag)

    def test_open_writes_the_flag_backs_up_and_goes_live(self):
        token = self.token()
        response = self.client.post('/manage/plague', data=dict(csrf=token, action='open'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.db.flag, 1); self.assertTrue(self.db.committed)
        self.assertEqual(self.queued, [('PLAGUE', '1')])
        self.assertEqual(len(self.backups()), 1)
        body = self.client.get('/manage/plague').get_data(as_text=True)
        self.assertIn('value="close"', body); self.assertIn('Otwarty dla graczy', body)
        self.assertIn('gra już o tym wie', body)

    def test_close_timeout_cancels_and_says_next_start(self):
        self.db.flag = 1; self.answer = 'timeout'; token = self.token()
        self.client.post('/manage/plague', data=dict(csrf=token, action='close'))
        self.assertEqual(self.db.flag, 0); self.assertEqual(self.cancelled, [77])
        self.assertIn('następnym starcie', self.client.get('/manage/plague').get_data(as_text=True))

    def test_save_settings(self):
        self.assertEqual(self.client.post('/manage/plague', data=self.form()).status_code, 302)
        self.assertEqual(self.db.cfg['pass_count'], 2); self.assertEqual(self.db.cfg['pass_price'], 100000)
        self.assertEqual(self.db.cfg['reward_item1'], 27003); self.assertEqual(self.db.cfg['reward_count2'], 0)
        self.assertEqual(self.db.cfg['revision'], 5); self.assertIsNone(self.db.flag)
        files = self.backups(); self.assertEqual(len(files), 1)
        with open(files[0], encoding='utf8') as fh: saved = json.load(fh)
        self.assertEqual(saved['config'][0]['pass_count'], 1)
        self.assertIn('Czerwona Mikstura (D)', self.client.get('/manage/plague').get_data(as_text=True))

    def test_bad_csrf_never_writes(self):
        form = self.form(csrf='bad')
        self.assertEqual(self.client.post('/manage/plague', data=form).status_code, 403)
        self.assertEqual(self.db.statements, [])

    def test_stale_form_rolls_back(self):
        self.client.post('/manage/plague', data=self.form(revision='3'))
        self.assertTrue(self.db.rolled_back); self.assertFalse(self.db.committed)
        self.assertEqual(self.db.cfg['pass_count'], 1); self.assertEqual(self.backups(), [])

    def test_refusals_never_write(self):
        for extra in (dict(pass_count='201'), dict(reward_yang='-1'), dict(reward_exp='abc'),
                      dict(reward_count1='0'), dict(reward_count1='201'),
                      dict(reward_item2='27003', reward_count2='1'), dict(reward_item1='12345')):
            self.db = Database()
            self.client.post('/manage/plague', data=self.form(**extra))
            self.assertFalse([s for s, _ in self.db.statements if s.startswith('UPDATE')], extra)

    def test_update_failure_preserves_settings(self):
        self.db.fail = True
        self.client.post('/manage/plague', data=self.form())
        self.assertTrue(self.db.rolled_back); self.assertEqual(self.db.cfg['pass_count'], 1)

    def test_navigation_links(self):
        for name in ('base.html', '_laka_nav.html'):
            nav = (PANEL / 'templates' / name).read_text(encoding='utf-8')
            self.assertIn("plague_settings_page", nav, name)
        self.assertIn("plague_settings_page", (PANEL / 'templates/events.html').read_text(encoding='utf-8'))
        docker = (PANEL / 'Dockerfile').read_text(encoding='utf-8')
        self.assertIn('COPY plague_settings.py plague_settings_text.py ./', docker)


if __name__ == '__main__': unittest.main()
