// Motyw "Laka i Złoto": tabela liczb, widżety i Kronika świata na Przeglądzie świata.
// Nie wysyła własnych zapytań (poza odczytem VPS co 15 s): czyta odpowiedzi, które dashboard
// i tak pobiera, przez window.lakaBus z base.html.
(() => {
  const bus = window.lakaBus;
  if (!bus || !document.querySelector('.laka-ledger')) return;
  const $ = id => document.getElementById(id);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const num = n => Number(n || 0).toLocaleString('pl-PL').replace(/ |,/g, ' ');
  const set = (id, html) => {
    const el = $(id);
    if (!el || el.innerHTML === String(html)) return;
    el.innerHTML = html;
    el.classList.remove('laka-flash'); void el.offsetWidth; el.classList.add('laka-flash');
  };
  // bus.on() może wywołać handler od razu (dane przyszły przed tym skryptem), więc stałe muszą być na górze
  const monitorDocker = /Docker/.test(document.querySelector('.laka-widget h2')?.textContent || '');
  const PORTRAITS = ['warrior_m', 'assassin_w', 'sura_m', 'shaman_w', 'warrior_w', 'assassin_m', 'sura_w', 'shaman_m'];
  const portrait = job => `/static/class-portraits/${PORTRAITS[Math.max(0, Math.min(7, Number(job) || 0))]}.bmp`;

  // ── boty na żywo: liczby w tabeli i "Boty według map" z podziałem na królestwa
  bus.on('/api/live-bots', data => {
    const bots = data.bots || [];
    if (!bots.length) return;
    set('lg-bots', num(bots.length));
    set('lg-party', num(bots.filter(b => b.in_party).length));
    const avg = bots.reduce((s, b) => s + Number(b.level || 0), 0) / bots.length;
    set('lg-levels', `${avg.toFixed(1).replace('.', ',')} / ${Math.max(...bots.map(b => Number(b.level || 0)))}`);
    const byMap = {};
    bots.forEach(b => {
      const m = b.map_index >= 10000 ? Math.floor(b.map_index / 10000) : b.map_index;
      const row = byMap[m] = byMap[m] || [0, 0, 0, 0];
      row[0]++; row[Number(b.empire) || 0]++;
    });
    // wszystkie mapy z botami; lista wypełnia pudełko i przewija się
    const top = Object.entries(byMap).sort((a, b) => b[1][0] - a[1][0]);
    const max = top.length ? top[0][1][0] : 1;
    const names = data.maps || {};
    $('lw-maps').innerHTML = top.map(([m, r]) => `<div class="laka-hbar"><span title="${esc(names[m] || 'Mapa ' + m)}">${esc(names[m] || 'Mapa ' + m)}</span><div class="laka-track"><i style="width:${r[0] / max * 100}%">${[1, 2, 3].map(e => `<b class="e${e}" style="width:${r[e] / r[0] * 100}%" title="${['', 'Shinsoo', 'Chunjo', 'Jinno'][e]}: ${r[e]}"></b>`).join('')}</i></div><em>${r[0]}</em></div>`).join('');
  });

  // ── raty, eventy i wersja Playerbots
  bus.on('/api/manage-status', data => {
    const r = data.rates || {};
    if ('exp' in r) set('lg-rates', `${r.exp} · ${r.drop} · ${r.yang}%`);
    const names = { exp: 'EXP', drop: 'Drop', yang: 'Yang' };
    const events = Object.entries(data.events || {}).filter(([k, ev]) => names[k] && ev);
    const active = events.filter(([, ev]) => ev.active && Number(ev.value) > 0);
    if (active.length) {
      set('lg-event', active.map(([k, ev]) => `<span class="laka-event">${names[k]} +${ev.value}% do ${esc(ev.until_text || '—')}</span>`).join(' '));
    } else {
      // nic nie trwa: najbliższy zaplanowany event z rdzenia (next_start / next_value)
      const next = events.filter(([, ev]) => ev.scheduled && Number(ev.next_start) > 0 && Number(ev.next_value) > 0)
        .sort((a, b) => a[1].next_start - b[1].next_start);
      if (next.length) {
        const at = next[0][1].next_start;
        set('lg-event', 'następny: ' + next.filter(([, ev]) => ev.next_start === at).map(([k, ev]) => `${names[k]} +${ev.next_value}%`).join(', ') + ` · ${esc(next[0][1].next_start_text || '')}`);
      } else set('lg-event', 'bez eventu');
    }
  });

  // ── dane historyczne: wersja panelu i rankingi (te same, co stara karuzela)
  let ranks = [], rankI = 0, topId = null;
  const drawRank = () => {
    const r = ranks[rankI];
    if (!r) return;
    $('lw-rank-title').textContent = r.title || 'Ranking';
    $('lw-rank-sub').textContent = r.subtitle || '';
    const items = (r.items || []).slice(0, 10);
    $('lw-rank').innerHTML = items.length ? items.map(row => `<li class="${row.id === topId ? 'is-leader' : ''}"><img src="${portrait(row.job)}" alt=""><a href="/player/${Number(row.id)}">${row.is_person ? '<span class="laka-person" title="Postać gracza">●</span> ' : ''}${esc(row.name)}</a><b>${esc(row.value)}</b></li>`).join('')
      : '<li class="muted">Brak danych — jeszcze nikt tego nie zrobił.</li>';
  };
  $('lw-rank-prev')?.addEventListener('click', () => { if (ranks.length) { rankI = (rankI + ranks.length - 1) % ranks.length; drawRank(); } });
  $('lw-rank-next')?.addEventListener('click', () => { if (ranks.length) { rankI = (rankI + 1) % ranks.length; drawRank(); } });
  bus.on('/api/dashboard-deferred', data => {
    const w = data.world_summary || {};
    if (w.panel_release && w.panel_release.installed) set('lg-panel', esc(w.panel_release.installed));
    const rel = w.release || {};
    const pb = rel.installed || w.version;
    if (pb) set('lg-playerbots', rel.behind && rel.latest ? `Playerbots ${esc(pb)} · <span class="laka-warn">dostępna ${esc(rel.latest)}</span>` : `Playerbots ${esc(pb)}`);
    if (w.rates && !$('lg-rates').textContent.includes('%')) set('lg-rates', `${w.rates.exp} · ${w.rates.drop} · ${w.rates.yang}%`);
    ranks = data.quick_rankings || []; topId = data.global_top_id; rankI = 0; drawRank();
    if (data.system) drawSystem(data.system);
  });

  // ── obciążenie VPS
  function drawSystem(s) {
    if (!s || s.cpu_percent === undefined) return;
    const row = (label, pct, detail) => `<div class="laka-meter"><div><span>${label}</span><b>${Math.round(pct)}%</b></div><div class="laka-bar${pct >= 85 ? ' is-hot' : pct >= 70 ? ' is-warm' : ''}"><i style="width:${Math.min(100, pct)}%"></i></div>${detail ? `<small>${detail}</small>` : ''}</div>`;
    let html = row('CPU', Number(s.cpu_percent)) + row('RAM', Number(s.ram_percent), `${num(s.ram_used_mb)} / ${num(s.ram_total_mb)} MB`);
    if (!monitorDocker && s.disk_percent !== undefined && s.disk_percent !== null) html += row('Dysk', Number(s.disk_percent), `${(s.disk_used_mb / 1024).toFixed(1).replace('.', ',')} / ${(s.disk_total_mb / 1024).toFixed(1).replace('.', ',')} GB`);
    $('lw-system').innerHTML = html;
  }
  bus.on('/api/system-current', data => drawSystem(data.system));
  const pollSystem = () => { if (!document.hidden) fetch('/api/system-current', { cache: 'no-store' }).catch(() => {}); };
  setInterval(pollSystem, 15000);

  // ── wykres VPS z ostatnich 24 h (/api/system-history: te same próbki co strona Wydajność)
  async function loadHistory() {
    try {
      const data = await fetch('/api/system-history', { cache: 'no-store' }).then(r => r.json());
      const s = (data.samples || []).filter(p => p.cpu_percent !== null);
      const box = $('lw-history');
      if (!box) return;
      if (s.length < 2) { box.innerHTML = '<p class="muted">Za mało próbek z ostatniej doby.</p>'; return; }
      const W = 300, H = 92, pad = 4, x = i => pad + i / (s.length - 1) * (W - 2 * pad), y = v => H - 14 - Math.min(100, Math.max(0, Number(v) || 0)) / 100 * (H - 22);
      const line = key => s.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(p[key]).toFixed(1)}`).join(' ');
      const cpu = line('cpu_percent'), ram = line('ram_percent');
      const mid = Math.floor(s.length / 2);
      box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="CPU i RAM w ostatnich 24 godzinach">
        <defs><linearGradient id="lw-cpu-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8b93f" stop-opacity=".35"/><stop offset="1" stop-color="#e8b93f" stop-opacity="0"/></linearGradient></defs>
        ${[0, 50, 100].map(v => `<line x1="${pad}" x2="${W - pad}" y1="${y(v)}" y2="${y(v)}" class="grid"/>`).join('')}
        <path d="${cpu} L${x(s.length - 1)} ${y(0)} L${x(0)} ${y(0)} Z" fill="url(#lw-cpu-fill)"/>
        <path d="${ram}" class="ram"/><path d="${cpu}" class="cpu"/>
        <circle cx="${x(s.length - 1)}" cy="${y(s[s.length - 1].cpu_percent)}" r="2.6" class="dot"/>
      </svg><div class="laka-spark-axis"><span>${esc(s[0].label)}</span><span>${esc(s[mid].label)}</span><span>${esc(s[s.length - 1].label)}</span></div>`;
      const peak = s.reduce((a, b) => (Number(b.cpu_percent) > Number(a.cpu_percent) ? b : a));
      const avgRam = s.reduce((t, p) => t + Number(p.ram_percent || 0), 0) / s.length;
      const sys = bus.last['/api/system-current']?.system || bus.last['/api/dashboard-deferred']?.system || {};
      const freeDisk = sys.disk_total_mb ? `${((sys.disk_total_mb - sys.disk_used_mb) / 1024).toFixed(1).replace('.', ',')} GB` : '—';
      $('lw-history-stats').innerHTML = `<div><span>Szczyt CPU</span><b>${Math.round(peak.cpu_percent)}%</b><small>o ${esc(peak.label)}</small></div><div><span>Średni RAM</span><b>${Math.round(avgRam)}%</b><small>z ${s.length} próbek</small></div><div><span>Wolny dysk</span><b>${freeDisk}</b><small>teraz</small></div>`;
    } catch (_) { /* wykres zostaje z poprzednim stanem */ }
  }
  loadHistory();
  setInterval(() => { if (!document.hidden) loadHistory(); }, 300000);

  // ── Kronika świata (te same wydarzenia, co pasek wiadomości)
  const KIND = { refine: 'icons/71085.png', hammer: 'icons/25040.png', bought: 'icons/money.png', weapon: 'icons/00010.png', armor: 'icons/11290.png', announcement: 'icons/71027.png' };
  bus.on('/api/news-feed', data => {
    const events = (data.events || []).slice(-10).reverse();
    $('lw-chronicle').innerHTML = events.length ? events.map(e => `<li class="${Number(e.refine_tier) >= 8 ? 'is-rare' : ''}"><img src="/static/${KIND[e.kind] || 'icons/25040.png'}" alt=""><span>${esc(e.message)}</span><time>${esc(e.time)}</time></li>`).join('')
      : '<li class="muted">Oczekiwanie na nowe ważne wydarzenia ze świata…</li>';
  });
})();
