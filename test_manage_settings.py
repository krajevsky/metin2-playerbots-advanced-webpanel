"""Run against staged app.py; every POST uses an isolated spool and mocked DB."""
import tempfile
from pathlib import Path
from unittest.mock import patch
import app as panel

panel.app.config['TESTING'] = True
with tempfile.TemporaryDirectory() as tmp, patch.object(panel,'RATES_SPOOL',Path(tmp)), \
     patch.object(panel,'AI_WEIGHTS_FILE',Path(tmp) / 'playerbot_weights.tsv'), \
     patch.object(panel,'UPDATE_SPOOL',Path(tmp) / 'update-spool'), \
     patch.object(panel,'settings',return_value={'setup_complete':'1','auth_enabled':'0'}), \
     patch.object(panel,'db',side_effect=AssertionError('POST must not write the DB')):
    client=panel.app.test_client()
    panel._playerbots_release_cache.update({'checked_at': panel.time.time(), 'latest': '1.30.22', 'error': None})
    Path(tmp, 'server-settings.ready').write_text('capability=server-settings\ntime=1\n')
    class FakeCursor:
        def __init__(self): self.calls=[]; self.lastrowid=4242
        def __enter__(self): return self
        def __exit__(self,*_args): return False
        def execute(self, query, params=()): self.calls.append((query,params))
        def fetchone(self): return None
    class FakeConnection:
        def __init__(self): self.cursor_instance=FakeCursor(); self.started=False; self.committed=False
        def __enter__(self): return self
        def __exit__(self,*_args): return False
        def cursor(self): return self.cursor_instance
        def begin(self): self.started=True
        def commit(self): self.committed=True
        def rollback(self): pass
    fake_connection=FakeConnection()
    with patch.object(panel, 'db', return_value=fake_connection):
        gm_response=client.post('/accounts', data={'login':'gm_test','password':'secret12','email':'','deletion_code':'1234567','empire':'2','authority':'GOD','gm_name':'TestGM','gm_job':'2'})
    assert gm_response.status_code == 302 and fake_connection.started and fake_connection.committed
    queries=[query for query,_params in fake_connection.cursor_instance.calls]
    assert any('INSERT INTO player.player' in query for query in queries)
    assert any('INSERT INTO player.player_index' in query for query in queries)
    player_insert=next(params for query,params in fake_connection.cursor_instance.calls if 'INSERT INTO player.player' in query)
    assert player_insert[:6] == (4242, 'TestGM', 2, 55700, 157900, 21)
    with patch.object(panel, 'db', return_value=FakeConnection()):
        tagged_response=client.post('/accounts', data={'login':'ga_test','password':'secret12','email':'','deletion_code':'1234567','empire':'1','authority':'GOD','gm_name':'[GA]Test','gm_job':'0'})
    assert tagged_response.status_code == 302
    form={'submit_action':'apply','exp':'150','drop':'170','yang':'190','map_21':'1','map_stone_21':'350','map_1':''}
    assert client.post('/manage/restart-config',data=form).status_code==302
    request=Path(tmp)/'server-settings.request'; original=request.read_text()
    assert 'map_stone_21=350' in original and 'map_21=1' in original and 'map_1=reset' in original
    assert not (Path(tmp)/'request').exists() and not (Path(tmp)/'map-regens.request').exists()
    assert client.post('/manage/restart-config',data=form).status_code==302
    assert request.read_text()==original
    request.unlink()
    for key,value in [('map_stone_21','0'),('map_21','3601'),('exp','not-a-number')]:
        invalid=dict(form);invalid[key]=value
        assert client.post('/manage/restart-config',data=invalid).status_code==302
        assert not request.exists()
    assert client.post('/manage/restart-config',data={'submit_action':'restart','exp':'bad','map_21':'-1'}).status_code==302
    assert 'action=restart' in request.read_text() and 'map_21=' not in request.read_text()
    request.unlink()
    (Path(tmp)/'map-regens.status').write_text('state=ok\nmap_21=1\nmap_stone_21=350\n')
    status=panel.read_map_regen_status()
    assert status['values']=={21:'1'} and status['stones']=={21:'350'}
    assert panel.server_settings_status()['ready']
    request.write_text('id=orphan\naction=restart\n')
    stale = Path(tmp) / 'server-settings.ready'; stale.unlink()
    with patch.object(panel.time, 'time', return_value=request.stat().st_mtime + 601):
        assert panel.server_settings_status()['can_clear']
    request.unlink()
    Path(tmp, 'server-settings.ready').write_text('capability=server-settings\ntime=1\n')
    class FakeCursor:
        def __init__(self): self.calls=[]; self.lastrowid=4242
        def __enter__(self): return self
        def __exit__(self,*_args): return False
        def execute(self, query, params=()): self.calls.append((query,params))
        def fetchone(self): return None
    class FakeConnection:
        def __init__(self): self.cursor_instance=FakeCursor(); self.started=False; self.committed=False
        def __enter__(self): return self
        def __exit__(self,*_args): return False
        def cursor(self): return self.cursor_instance
        def begin(self): self.started=True
        def commit(self): self.committed=True
        def rollback(self): pass
    fake_connection=FakeConnection()
    with patch.object(panel, 'db', return_value=fake_connection):
        gm_response=client.post('/accounts', data={'login':'gm_test','password':'secret12','email':'','deletion_code':'1234567','empire':'2','authority':'GOD','gm_name':'TestGM','gm_job':'2'})
    assert gm_response.status_code == 302 and fake_connection.started and fake_connection.committed
    queries=[query for query,_params in fake_connection.cursor_instance.calls]
    assert any('INSERT INTO player.player' in query for query in queries)
    player_insert=next(params for query,params in fake_connection.cursor_instance.calls if 'INSERT INTO player.player' in query)
    assert player_insert[:6] == (4242, 'TestGM', 2, 55700, 157900, 21)
    weights_file=Path(tmp)/'playerbot_weights.tsv'
    weights_file.write_text('BOOKS\t0\nCHEST\t10\nCHEST_STONE\t300\nFUTURE_KEY\t77\n')
    weights=panel.read_ai_weights()
    assert weights['BOOKS']==0 and weights['CHEST']==10 and weights['CHEST_STONE']==300
    weights['BOOKS']=1; weights['CHEST']=11; weights['CHEST_STONE']=301
    panel.write_ai_weights(weights)
    saved=weights_file.read_text()
    assert 'BOOKS\t1' in saved and 'CHEST\t11' in saved and 'CHEST_STONE\t301' in saved and 'FUTURE_KEY\t77' in saved
    assert panel.SKILLS[(0,1)][3] == (4, 'Aura Miecza') and len(panel.SKILLS[(0,1)]) == 5
    # Tieru ships master icons as *_m.png for M/G/P; *_p.png does not exist.
    skill_bytes=bytes(24) + bytes([3, 35])
    assert panel.parse_skills(skill_bytes, 0, 1)[0]['icon_suffix'] == '_m'
    assert panel.MAP_NAMES[61] == 'Góra Sohan' and panel.MAP_NAMES[104] == 'Loch Pająków V1'
    assert panel.MAP_NAMES[108] == 'Loch Małp Normalny' and panel.MAP_NAMES[109] == 'Loch Małp Trudny'
    assert panel.playerbots_release_status()['tone'] in ('current', 'outdated')
    assert panel.MAP_BOUNDS[61] == (358400, 153600, 153600, 153600)
    assert 61 in panel.MAP_STONE_RESPAWN_IDS and not {25, 104, 108, 109} & panel.MAP_STONE_RESPAWN_IDS
    assert [index for index, _name in panel.TRACKED_MAP_OPTIONS] == [21, 23, 24, 25, 61, 63, 64, 104, 108, 109]
    assert panel.changelog_entries()[0]['version'] == '1.40.0'
    assert (Path(panel.__file__).parent / 'static' / 'inventory-background.svg').is_file()
    assert panel.class_profile(5)['portrait'] == 'assassin_m.bmp' and panel.class_profile(6)['gender'] == 'Kobieta'
    assert panel.empire_info(2)['name'] == 'Chunjo' and panel.empire_info(999)['flag'] == ''
    assert (Path(panel.__file__).parent / 'static' / 'empires' / 'chunjo.png').is_file()
    with patch.object(panel, 'rows', return_value=[]) as ranking_rows:
        assert panel.bot_ranking('bosses') == []
        assert "BOSS_KILL" in ranking_rows.call_args.args[0]
    with patch.object(panel,'live_map_counts',return_value=[]), patch.object(panel,'live_bots',return_value=[]), \
         patch.object(panel,'read_rates',return_value={'exp':150,'drop':170,'yang':190}), \
         patch.object(panel,'restart_progress',return_value={'state':'ok','percent':100,'stage':'Serwer działa'}), \
         patch.object(panel,'globals_for_templates'):
        # Use real Jinja rendering with context processors disabled (all DB mocked).
        processors=panel.app.template_context_processors[None]
        panel.app.template_context_processors[None]=[]
        try:
            response=client.get('/manage')
            assert response.status_code==200
            html=response.get_data(as_text=True)
            assert 'id="map_stone_21"' in html and 'formnovalidate' in html
            assert html.count('id="restart-fill"')==1 and 'Chunjo M1 — Joan' in html
            assert html.index('restart-console') < html.index('id="restart-fill"')
        finally:panel.app.template_context_processors[None]=processors
    update_spool=Path(tmp)/'update-spool'; update_spool.mkdir(); (update_spool/'watcher').touch()
    with patch.dict(panel.os.environ, {'PLAYERBOTS_VERSION':'1.30.12'}, clear=False):
        panel.queue_tieru_update()
    update_request=(update_spool/'request').read_text()
    assert 'id=seban-' in update_request and 'version=1.30.12' in update_request
    update_state=panel.update_status()
    assert update_state['watcher_ready'] and update_state['state']=='idle'
    # The updater route stays unavailable until protection is explicitly enabled.
    assert client.post('/manage/update',data={'update_csrf':'anything'}).status_code == 302
    assert client.get('/changelog').status_code == 200

with patch.object(panel, 'settings', return_value={'setup_complete':'1','auth_enabled':'1','auth_password_hash':'hash'}), \
     patch.object(panel, 'check_password_hash', return_value=True):
    auth_client = panel.app.test_client()
    response = auth_client.post('/login', data={'password':'correct'})
    assert response.status_code == 302
    assert any('seban_panel_session=' in header for header in response.headers.getlist('Set-Cookie'))
    with auth_client.session_transaction() as saved_session:
        assert saved_session['seban_admin'] is True and saved_session.permanent
assert panel.app.config['SESSION_COOKIE_NAME'] == 'seban_panel_session'
print('PASS: Flask batch validation, weights incl. BOOKS/CHEST, isolated updater queue, skills, and manage rendering')
