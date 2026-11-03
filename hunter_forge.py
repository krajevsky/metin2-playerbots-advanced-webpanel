"""Players-only crafting settings; no bot behavior or price overrides."""
from pathlib import Path
from datetime import datetime, timezone
from functools import lru_cache
import hmac, json, re, secrets
from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for
from hunter_forge_text import text

FAMILIES={98100:(299,98900,220),98101:(3219,98910,3180),98102:(1179,98920,1150),
          98103:(2159,98930,2190),98104:(5119,98940,5150),98105:(7169,98950,7170)}
SQL='SELECT vnum,item_vnum,count,price,chance,recipe,req_level FROM world.crafting_proto WHERE vnum BETWEEN 98100 AND 98105 ORDER BY vnum'
STATE='SELECT enabled,revision FROM player.hunter_forge_settings WHERE id=1'

def materials(recipe,source):
    if not re.fullmatch(r'[0-9]+(?:,[0-9]+)+',recipe): raise ValueError('invalid')
    parts=list(map(int,recipe.split(',')))
    if len(parts)>10 or len(parts)%2 or parts[:2]!=[source,1]: raise ValueError('invalid')
    return list(zip(parts[2::2],parts[3::2]))

def validate(form,items):
    try:
        rid=int(form['recipe_id']);fee=int(form['price'])
        if rid not in FAMILIES or not 0<=fee<=2000000000: raise ValueError()
        result=[];seen={FAMILIES[rid][0]}
        for i in range(4):
            raw_id=form.get('item_%d'%i,'').strip();raw_count=form.get('count_%d'%i,'').strip()
            if not raw_id and not raw_count: continue
            vnum,count=int(raw_id),int(raw_count)
            if vnum in seen or vnum not in items or 98900<=vnum<=98959 or not 1<=count<=1000 or int(items[vnum]['type']) in (1,2): raise ValueError()
            seen.add(vnum);result.append((vnum,count))
        return rid,fee,','.join(str(n) for pair in [(FAMILIES[rid][0],1),*result] for n in pair)
    except (KeyError,TypeError,ValueError): raise ValueError('invalid') from None

@lru_cache(maxsize=2)
def names(language):
    path=Path(__file__).parent/'static'/('item_names_'+language+'.json')
    return json.loads(path.read_text(encoding='utf8')) if path.is_file() else {}

def register(app,api):
    def language(): return api['settings']().get('ui_language','pl')
    def t(key): return text(key,language())
    def supported(): return bool(api.get('ENGINE_MT2009',False))
    def authorized():
        if not supported(): abort(404)
        if api['settings']().get('auth_enabled')=='1' and not session.get('seban_admin'): abort(403)
    def item_name(vnum,row=None):
        lang=language()
        translated=names(lang).get(str(vnum)) if lang in ('en','tr') else None
        if translated: return translated[-1] if isinstance(translated,list) else translated
        return bytes.fromhex(row['name_hex']).decode('cp1250','replace') if row and row.get('name_hex') else str(vnum)
    def catalog(ids):
        ids=sorted(set(ids))
        if not ids: return {}
        rows=api['rows']('SELECT vnum,type,HEX(locale_name) name_hex FROM world.item_proto WHERE vnum IN ('+','.join(['%s']*len(ids))+')',tuple(ids))
        return {int(row['vnum']):dict(row,label=item_name(int(row['vnum']),row)) for row in rows}
    icons=api.get('ITEM_ICONS',{})
    for source,target,model in FAMILIES.values():
        if str(model) in icons:
            for plus in range(10): icons[str(target+plus)]=icons[str(model)]
    @app.context_processor
    def context(): return dict(hunter_forge_supported=supported(),hunter_forge_t=t)

    @app.get('/manage/hunter-forge/items')
    @api['login_required']
    def hunter_forge_items():
        authorized();query=request.args.get('q','').strip()[:64]
        if len(query)<2: return jsonify([])
        rows=api['rows']('SELECT vnum,type,HEX(locale_name) name_hex FROM world.item_proto WHERE type NOT IN (1,2) AND (CAST(vnum AS CHAR) LIKE %s OR CONVERT(CAST(locale_name AS BINARY) USING cp1250) LIKE %s) ORDER BY vnum LIMIT 25',('%'+query+'%','%'+query+'%'))
        return jsonify([dict(vnum=row['vnum'],name=item_name(int(row['vnum']),row)) for row in rows])

    @app.route('/manage/hunter-forge',methods=['GET','POST'])
    @api['login_required']
    def hunter_forge_page():
        authorized()
        token=session.setdefault('hunter_forge_csrf',secrets.token_hex(32))
        connection=None;error=None
        try:
            settings=api['rows'](STATE)
            rows=api['rows'](SQL)
        except Exception:
            settings=[];rows=[]
        ready=len(settings)==1 and len(rows)==6
        state=settings[0] if settings else dict(enabled=0,revision=0)
        if request.method=='POST':
            if not hmac.compare_digest(token,request.form.get('csrf','')): abort(403)
            try:
                if not ready: raise ValueError('missing')
                rid=fee=recipe=None
                if request.form.get('action')!='toggle':
                    ids=[int(request.form.get('item_%d'%i) or 0) for i in range(4)]
                    rid,fee,recipe=validate(request.form,catalog(ids))
                connection=api['db']();connection.begin()
                with connection.cursor() as cur:
                    cur.execute(STATE+' FOR UPDATE');locked=cur.fetchall()
                    if len(locked)!=1 or int(locked[0]['revision'])!=int(request.form.get('revision','-1')): raise ValueError('stale')
                    cur.execute(SQL+' FOR UPDATE');before=cur.fetchall()
                    if len(before)!=6: raise ValueError('missing')
                    for row in before:
                        pair=FAMILIES.get(int(row['vnum']))
                        if pair is None or int(row['item_vnum'])!=pair[1] or int(row['chance'])!=100 or int(row['count'])!=1: raise ValueError('missing')
                        materials(row['recipe'],pair[0])
                    folder=Path(api['RATES_SPOOL'])/'hunter-forge-backups';folder.mkdir(parents=True,exist_ok=True)
                    path=folder/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+secrets.token_hex(4)+'.json')
                    path.write_text(json.dumps(dict(settings=locked,recipes=before),default=str),encoding='utf8')
                    if request.form.get('action')=='toggle':
                        cur.execute('UPDATE player.hunter_forge_settings SET enabled=%s,revision=revision+1 WHERE id=1',(1 if request.form.get('enabled')=='1' else 0,))
                    else:
                        cur.execute('UPDATE world.crafting_proto SET price=%s,recipe=%s,req_level=0,req_progress=0,count=1,chance=100 WHERE vnum=%s',(fee,recipe,rid))
                        cur.execute('UPDATE player.hunter_forge_settings SET revision=revision+1 WHERE id=1')
                connection.commit();flash(t('saved'),'success')
                return redirect(url_for('hunter_forge_page'))
            except (ValueError,TypeError) as exc:
                if connection: connection.rollback()
                error=t(str(exc) if str(exc) in ('invalid','missing','stale') else 'invalid')
            except Exception:
                if connection: connection.rollback()
                app.logger.exception('Hunter Forge save failed');error=t('failed')
            finally:
                if connection: connection.close()
        cards=[];ids=[]
        for row in rows:
            pair=FAMILIES.get(int(row['vnum']))
            if pair is None: continue
            try: mats=materials(row['recipe'],pair[0])
            except ValueError: ready=False;continue
            ids.extend(v for v,n in mats)
            cards.append(dict(id=int(row['vnum']),source=pair[0],target=pair[1],model=pair[2],price=int(row['price']),materials=mats))
        labels=catalog([card['model'] for card in cards])
        for card in cards: card['label']=labels.get(card['model'],{}).get('label',str(card['model']))
        return render_template('hunter_forge.html',cards=cards,items=catalog(ids),csrf=token,state=state,error=error,ready=ready)
