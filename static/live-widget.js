(() => {
  let snapshot = [], globalTopId = null, topLevelRanks = {}, currentLevel = 'all', currentChannel = 'all', knownChannels = [1], worldEmpireFilter = 'all';
  const $ = id => document.getElementById(id);
  const map = $('world-map'), select = $('map-select'), search = $('bot-search');
  const filters = document.querySelector('.live-filters');
  // Panel boczny (ranking + aktywności) dopasowuje wysokość один do один do
  // faktycznie wyrenderowanej mapy, zamiast rosnąć/kurczyć się razem z
  // ilością botów/aktywności -- mapa sama w sobie pozostaje nietknięta.
  const liveSidebar = document.querySelector('.live-sidebar');
  if (map && liveSidebar && 'ResizeObserver' in window) {
    // Tylko gdy mapa i panel faktycznie stoją obok siebie (desktop) -- poniżej
    // 1001px .live-grid układa się w jedną kolumnę (mapa nad panelem), więc
    // dopasowanie wysokości do mapy nie ma sensu i tylko ściska ranking do
    // zera (potwierdzone na telefonie w pionie, 20.09).
    const sideBySide = () => window.matchMedia('(min-width: 1001px)').matches;
    const syncSidebarHeight = () => {
      if (sideBySide()) liveSidebar.style.height = map.offsetHeight + 'px';
      else liveSidebar.style.height = '';
    };
    new ResizeObserver(syncSidebarHeight).observe(map);
    window.addEventListener('resize', syncSidebarHeight);
    syncSidebarHeight();
  }
  // Powyżej 1700px .live-insights (Rozkład kanałów / Respawny / Królestwa /
  // nowa karta Aktywności-w-świecie) pływa jako osobna kolumna obok
  // .live-sidebar zamiast pod mapą -- bez tego miała wysokość "naturalną"
  // (sumę kart), więc jej dół nie trafiał w dół .live-sidebar (który JEST
  // dopasowany do mapy, patrz wyżej) i robiły się schodki (zgłoszenie,
  // 2026-10-02). Ostatnia karta (#world-insights-card) ma flex:1 w CSS, więc
  // rozciąga się i wypełnia dokładnie tyle, ile trzeba, żeby oba dolne
  // krawędzie się zrównały.
  const liveInsights = document.querySelector('.live-insights');
  if (map && liveInsights && 'ResizeObserver' in window) {
    const insightsFloat = () => window.matchMedia('(min-width: 1700px)').matches;
    const syncInsightsHeight = () => {
      if (insightsFloat()) liveInsights.style.height = map.offsetHeight + 'px';
      else liveInsights.style.height = '';
    };
    new ResizeObserver(syncInsightsHeight).observe(map);
    window.addEventListener('resize', syncInsightsHeight);
    syncInsightsHeight();
  }
  const channelSelect = document.createElement('select');
  channelSelect.id = 'channel-select';
  channelSelect.style.display = 'none';
  filters.insertBefore(channelSelect, search);
  function ensureChannelUI(channels) {
    if (JSON.stringify(channels) === JSON.stringify(knownChannels) && channelSelect.options.length) return;
    knownChannels = channels;
    if (channels.length < 2) { channelSelect.style.display = 'none'; return; }
    channelSelect.style.display = '';
    channelSelect.innerHTML = '<option value="all">Wszystkie kanały</option>' + channels.map(ch => `<option value="${ch}">Kanał ${ch}</option>`).join('');
    channelSelect.value = currentChannel;
  }
  channelSelect.addEventListener('input', () => { currentChannel = channelSelect.value; markInteraction(); render(); });
  const mode = document.createElement('select');
  mode.id = 'live-mode';
  mode.innerHTML = '<option value="live">Pozycje botów na żywo</option><option value="deaths">Mapa cieplna: zgony botów</option><option value="metins">Mapa cieplna: rozbite Metiny</option><option value="bosses">Mapa cieplna: zabite bossy</option>';
  filters.insertBefore(mode, search);
  const autoplay = document.createElement('label');
  autoplay.className = 'map-autoplay';
  autoplay.innerHTML = '<input id="map-autoplay" type="checkbox"> Automatycznie zmieniaj mapy po bezczynności';
  filters.insertBefore(autoplay, search);
  const restartInfo = document.createElement('small');
  restartInfo.id = 'last-restart';
  document.querySelector('.live-shell header > div').appendChild(restartInfo);
  [...document.querySelectorAll('.live-shell footer span')].filter(node => node.textContent.includes('Podkład graficzny')).forEach(node => node.remove());
  const mapLabels = {21:'Chunjo M1 — Joan',23:'Chunjo M2 — Bokjung',24:'Chunjo M3 — Waryong',25:'Loch Małp Chunjo',61:'Góra Sohan',64:'Dolina Orków',63:'Pustynia Yongbi',104:'Loch Pająków V1',108:'Loch Małp Normalny',109:'Loch Małp Trudny',65:'Świątynia Hwang',4:'Shinsoo M3 — Jungrang',44:'Jinno M3 — Imha',5:'Loch Małp Shinsoo',45:'Loch Małp Jinno',1:'Shinsoo M1 — Yongan',3:'Shinsoo M2 — Jayang',41:'Jinno M1 — Pyongmoo',43:'Jinno M2 — Bakra',67:'Las',68:'Czerwony Las',66:'Wieża Demonów'};
  Object.entries(mapLabels).forEach(([id,label]) => {
    const option = select.querySelector(`option[value="${id}"]`);
    if (option) option.textContent = label;
  });
  const overview = document.querySelector('.world-overview');
  let overviewMaps = null;
  if (overview) {
    overviewMaps = document.createElement('section');
    overviewMaps.className = 'overview-maps';
    overviewMaps.innerHTML = '<div class="overview-maps-list"><div class="muted">Ładowanie…</div></div>';
    (overview.querySelector('[data-page="2"]') || overview).appendChild(overviewMaps);
  }
  function renderOverviewMaps() {
    if (!overviewMaps) return;
    const counts = snapshot.reduce((all, bot) => { all[bot.map_index] = (all[bot.map_index] || 0) + 1; return all; }, Object.fromEntries(Object.keys(mapLabels).map(id => [id, 0])));
    const entries = Object.entries(counts).sort((a,b)=>b[1]-a[1]);
    // Scrollable inner list -- with 20+ maps now tracked, the plain list
    // used to spill past the fixed-height world-overview sidebar box.
    // Audyt 2026-09-19: liczby zmieniają się co ~1,5s, więc resortowanie
    // listy na każdym odświeżeniu potrafiło zmienić kolejność wierszy i
    // wywalić użytkownika z powrotem na górę w trakcie przewijania -- zapisz
    // scrollTop przed podmianą innerHTML i przywróć go zaraz po.
    const prevList = overviewMaps.querySelector('.overview-maps-list');
    const scrollTop = prevList ? prevList.scrollTop : 0;
    overviewMaps.innerHTML = '<div class="overview-maps-list">' + (entries.map(([id,count]) => `<div><span>${escape(mapLabels[id] || `Mapa #${id}`)}</span><b>${count}</b></div>`).join('') || '<div class="muted">Brak botów online.</div>') + '</div>';
    const newList = overviewMaps.querySelector('.overview-maps-list');
    if (newList) newList.scrollTop = scrollTop;
  }
  (function initOverviewPager() {
    // "Stan serwera" jako 3 przełączalne strony w stylu iOS springboard --
    // kropki pod widgetem lub swipe palcem (dotyk) przełączają sekcję,
    // zamiast trzymać wszystko jedno pod drugim w jednej rosnącej kolumnie.
    if (!overview) return;
    const pages = [...overview.querySelectorAll('.overview-page')];
    const dots = [...overview.querySelectorAll('.overview-dots button')];
    if (!pages.length) return;
    let active = 0;
    function show(index) {
      active = (index + pages.length) % pages.length;
      pages.forEach((page, i) => page.classList.toggle('active', i === active));
      dots.forEach((dot, i) => dot.classList.toggle('active', i === active));
    }
    dots.forEach((dot, i) => dot.addEventListener('click', () => show(i)));
    const track = overview.querySelector('.overview-pages');
    let touchStartX = null;
    track.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, {passive: true});
    track.addEventListener('touchend', e => {
      if (touchStartX === null) return;
      const dx = e.changedTouches[0].clientX - touchStartX;
      if (Math.abs(dx) > 40) show(active + (dx < 0 ? 1 : -1));
      touchStartX = null;
    });
    show(0);
  })();
  const levelOK = (level) => { if (currentLevel === 'all') return true; if (currentLevel.endsWith('+')) return level >= Number.parseInt(currentLevel, 10); const [from, to] = currentLevel.split('-').map(Number); return level >= from && level <= to; };
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const portrait = job => { const files = ["warrior_m.bmp","assassin_w.bmp","sura_m.bmp","shaman_w.bmp","warrior_w.bmp","assassin_m.bmp","sura_w.bmp","shaman_m.bmp"]; const index = Number.isInteger(Number(job)) && Number(job) >= 0 && Number(job) < files.length ? Number(job) : 0; return `/static/class-portraits/${files[index]}`; };
  const empireFlag = empire => ({ 1: 'shinsoo.png', 2: 'chunjo.png', 3: 'jinno.png' })[Number(empire)] || 'chunjo.png';
  const levelMarkup = bot => topLevelRanks[bot.id] ? `<span class="top-level-badge top-level-badge--compact" title="Top 10 poziomu · #${topLevelRanks[bot.id]}">Lv ${bot.level}</span>` : `Lv ${bot.level}`;
  // Audyt 2026-09-19: goal 0 (`BOT_GOALS[0]`) to bazowe "Zdobywanie poziomu",
  // czyli domyślny cel niemal każdego bota, który akurat nie robi nic
  // szczególnego -- celowo pominięty tutaj, żeby w tym najczęstszym stanie
  // liczyła się bardziej konkretna akcja (walczy/zbiera łup/podróżuje) niż
  // jeden wspólny, bezużyteczny worek. Goal 1 (Przetrwanie) pominięty z tego
  // samego powodu. Reszta kodów 0-18 zsynchronizowana z kanonicznym
  // app.py:BOT_GOALS/BOT_ACTIONS -- wcześniej brakowało action 0 (spadało do
  // mylącego domyślnego "Expi / walczy"), a action 9 dublował etykietę
  // action 7, więc dwie różne akcje znikały pod jedną nazwą.
  function activityGroup(bot) {
    const status = String(bot.action_label || '').toLowerCase();
    if (/łow|low|ryb|fishing|branie/.test(status)) return 'Łowi ryby';
    const goals = {2:'Wybiera profesję',3:'Zdobywa ekwipunek',4:'Uzupełnia zapasy',5:'Ulepsza ekwipunek',6:'Rozwija umiejętności',7:'Poluje na Metiny',8:'Gra w grupie',9:'Robi Biologa',10:'Misje polowania',11:'Rozwija konia'};
    if (goals[bot.goal] !== undefined) return goals[bot.goal];
    const actions = {0:'Planuje ruch',1:'Przemieszcza się',2:'Expi / walczy',3:'Zbiera łup',4:'Regeneruje się',5:'Wybiera profesję',6:'Handluje',7:'Ulepsza ekwipunek',8:'Rozwija umiejętności',9:'Zakłada kostium',10:'Gra w grupie',11:'Robi Biologa',12:'Odwiedza stajennego',13:'Prowadzi stragan',14:'Łowi ryby',15:'Przegląda stragany',16:'Wabi potwory',17:'Odpoczywa w mieście',18:'Kopie rudę'};
    return actions[bot.action] || 'Inna aktywność';
  }
  function renderActivities(bots) {
    const box = $('live-activity');
    if (!box) return;
    const grouped = bots.reduce((all, bot) => { const label = activityGroup(bot); all[label] = (all[label] || 0) + 1; return all; }, {});
    // Audyt 2026-09-19: lista jest teraz przewijalna (#live-activity ma
    // overflow-y:auto), więc nie ma już powodu ucinać po 5 pozycjach i
    // chować resztę pod zbiorczym "Pozostałe aktywności" -- to właśnie ten
    // sztywny limit, nie brakujące etykiety, wrzucał większość botów do
    // jednego wspólnego worka. Pokazujemy teraz wszystkie realne kategorie.
    let entries = Object.entries(grouped).sort((a,b)=>b[1]-a[1]);
    const total = bots.length || 1;
    box.innerHTML = entries.map(([label,count]) => `<div class="activity-line"><span title="${escape(label)}">${escape(label)}</span><b>${count}</b><i style="--share:${Math.max(4,Math.round(count/total*100))}%"></i></div>`).join('') || '<p class="muted">Brak aktywnych botów na tej mapie.</p>';
  }
  function barLines(entries, total) {
    return entries.map(([label,count]) => `<div class="activity-line"><span title="${escape(label)}">${escape(label)}</span><b>${count}</b><i style="--share:${Math.max(4,Math.round(count/total*100))}%"></i></div>`).join('');
  }
  // World-wide (every map, every channel) counterpart to renderActivities()
  // above, which only sees the currently selected map -- requested by
  // players ("szerszy pogląd na to co dzieje się na wszystkich mapach",
  // Kordyl13, 2026-10-01). Re-derived from the same `snapshot` the live map
  // already polls every 1.5s, so no extra request.
  function renderWorldInsights() {
    const activityBox = $('world-activity-chart'), levelBox = $('world-level-chart');
    if (!activityBox && !levelBox) return;
    const bots = worldEmpireFilter === 'all' ? snapshot : snapshot.filter(b => String(b.empire) === worldEmpireFilter);
    const total = bots.length || 1;
    if (activityBox) {
      const grouped = bots.reduce((all, bot) => { const label = activityGroup(bot); all[label] = (all[label] || 0) + 1; return all; }, {});
      const entries = Object.entries(grouped).sort((a,b) => b[1]-a[1]);
      activityBox.innerHTML = barLines(entries, total) || '<p class="muted">Brak botów w tym królestwie.</p>';
    }
    if (levelBox) {
      const buckets = {};
      bots.forEach(bot => { const start = Math.max(1, Math.floor((Number(bot.level) - 1) / 10) * 10 + 1); const key = `${start}-${start + 9}`; buckets[key] = (buckets[key] || 0) + 1; });
      const entries = Object.entries(buckets).sort((a,b) => Number(a[0].split('-')[0]) - Number(b[0].split('-')[0])).map(([key,count]) => [`Lv ${key}`, count]);
      levelBox.innerHTML = barLines(entries, total) || '<p class="muted">Brak botów w tym królestwie.</p>';
    }
  }
  document.querySelectorAll('#world-activity-filter button').forEach(btn => btn.onclick = () => {
    document.querySelectorAll('#world-activity-filter button').forEach(x => x.classList.toggle('active', x === btn));
    worldEmpireFilter = btn.dataset.empire;
    renderWorldInsights();
  });
  const worldTabs = $('world-insights-tabs');
  if (worldTabs) worldTabs.addEventListener('click', event => {
    const btn = event.target.closest('button[data-tab]');
    if (!btn) return;
    worldTabs.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === btn));
    $('world-insights-card').dataset.worldTab = btn.dataset.tab;
  });
  // Read fresh each call, not once at module load: dashboard-deferred.js
  // replaces this script tag's JSON once the real data finishes loading in
  // the background (fast dashboard shell, 1.94.0) -- a one-time read here
  // would keep showing the placeholder forever. Defensively falls back to
  // the same 100%/100% defaults if a shape mismatch slips through again
  // (was previously an uncaught TypeError on "global.delay.mob", which
  // aborted the whole render() and left the live badge stuck on "Brak
  // danych live" permanently, not just on real fetch failures -- reported
  // [GA]Seban 2026-09-27).
  function regenInfo() {
    const fallback = {delay:{mob:100,boss:100},count:{mob:100,boss:100}};
    const rN = document.getElementById('live-regen-data');
    try {
      const parsed = rN ? JSON.parse(rN.textContent || '{}') : {};
      return {global: (parsed.global && parsed.global.delay && parsed.global.count) ? parsed.global : fallback, maps: parsed.maps || {values:{},stones:{}}};
    } catch (_) { return {global: fallback, maps: {values:{},stones:{}}}; }
  }
  function donut(id,rows,colors){const n=$(id),total=rows.reduce((a,x)=>a+x[1],0),t=total||1;if(!n)return;let at=0;const slices=rows.map(([l,v],i)=>{const from=at/t*360;at+=v;return `${colors[i]} ${from}deg ${at/t*360}deg`}).join(',');
    // An empty map (total 0) has no leader -- reduce() defaulting to rows[0]
    // named the first kingdom (Shinsoo) "dominant" at 0%, which read as a
    // real claim rather than "nobody's here".
    const lead=total?rows.reduce((a,x)=>x[1]>a[1]?x:a,rows[0]||['—',0]):['—',0],pct=total?Math.round(lead[1]/t*100):0;n.innerHTML=`<div class="map-donut" style="--map-donut:conic-gradient(${slices})"><b>${escape(lead[0])}</b><small>${pct}%</small></div><div class="map-donut-legend">${rows.map(([l,v],i)=>`<span><i style="--dot:${colors[i]}"></i>${escape(l)} <b>${v}</b></span>`).join('')}</div>`}
  function insights(mapId,bots){donut('map-channel-chart',[...new Set(snapshot.map(x=>+x.channel||1))].sort().map(c=>[`CH${c}`,bots.filter(x=>(+x.channel||1)===c).length]),['#43df91','#ef5ac9','#f5f5f5','#8a8a94']);donut('map-empire-chart',[[1,'Shinsoo'],[2,'Chunjo'],[3,'Jinno']].map(([e,l])=>[l,bots.filter(x=>+x.empire===e).length]),['#d95a54','#e8b93f','#4f86d9']);const rI=regenInfo(),m=rI.maps,g=rI.global,n=$('map-respawn-summary'),v=(m.values||{}),st=(m.stones||{}),mapSeconds=value=>value === 'reset' || value === undefined || value === null || value === '' ? null : Number(value);const mobSeconds=mapSeconds(v[mapId]),stoneSeconds=mapSeconds(st[mapId]);if(n)n.innerHTML=`<div><b>⚔ Potwory</b><small>${mobSeconds?`Własny czas mapy · ${mobSeconds} s`:`Globalnie · ${g.delay.mob}% czasu podstawowego`}</small></div><div><b>🗿 Metiny i bossy</b><small>${stoneSeconds?`Własny czas mapy · ${stoneSeconds} s`:`Globalnie · ${g.delay.boss}% czasu podstawowego`}</small></div><div><b>✦ Liczebność</b><small>Potwory ${g.count.mob}% · Metiny/bossy ${g.count.boss}%</small></div>`}
  document.querySelectorAll('[data-insight]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-insight]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('[data-insight-page]').forEach(x=>x.classList.toggle('active',x.dataset.insightPage===b.dataset.insight))});
  function render() {
    if (mode.value !== 'live') return;
    if (window.SebanHeatmap) window.SebanHeatmap.clear(map);
    const mapId = Number(select.value), needle = search.value.trim().toLowerCase();
    map.dataset.mapIndex = String(mapId);
    const bots = snapshot.filter(b => b.map_index === mapId && levelOK(b.level) && (!$('party-only').checked || b.in_party) && (!needle || b.name.toLowerCase().includes(needle)) && (currentChannel === 'all' || Number(b.channel) === Number(currentChannel)));
    // Aktualizacja in-place: nie usuwaj wszystkich ikonek przed ich
    // ponownym dodaniem, bo na telefonie tworzy to pustą klatkę co 1,5 s.
    const visibleIds = new Set();
    bots.forEach(bot => {
      const id = String(bot.id); visibleIds.add(id);
      let point = map.querySelector(`.bot-point[data-bot-id="${CSS.escape(id)}"]`);
      if (!point) { point = document.createElement('a'); point.dataset.botId = id; map.appendChild(point); }
      const dotStatus = bot.stuck ? 'red' : bot.fighting_metin ? 'yellow' : bot.in_party ? 'purple' : 'green';
      point.className = `bot-point dot-${dotStatus} ch-${bot.channel || 1} ${bot.in_party ? 'is-pt' : ''}${bot.stuck ? ' is-stuck' : ''}${bot.fighting_metin ? ' is-metin' : ''}`;
      point.href = `/player/${bot.id}`;
      point.style.left = `${Math.max(1,Math.min(99,bot.px))}%`; point.style.top = `${Math.max(1,Math.min(99,bot.py))}%`;
      point.title = `${bot.name} · poziom ${bot.level}${knownChannels.length > 1 ? ' · CH' + (bot.channel || 1) : ''}${bot.in_party ? ' · PT' : ''}${bot.stuck ? ' · możliwie zablokowany' : ''}${bot.fighting_metin ? ' · walczy z Metinem' : ''}`;
      const html = `${$('show-names').checked ? `<em class="kd-${Number(bot.empire) || 0}">${escape(bot.name)} ${levelMarkup(bot)} (CH ${bot.channel || 1})</em>` : ''}`;
      if (point.innerHTML !== html) point.innerHTML = html;
    });
    map.querySelectorAll('.bot-point').forEach(point => { if (!visibleIds.has(point.dataset.botId)) point.remove(); });
    const average = bots.length ? (bots.reduce((sum,b)=>sum+b.level,0)/bots.length).toFixed(1) : '—';
    $('stat-visible').textContent = bots.length; $('stat-pt').textContent = bots.filter(b=>b.in_party).length; $('stat-avg').textContent = average; $('stat-max').textContent = bots.length ? Math.max(...bots.map(b=>b.level)) : '—';
    $('live-count').textContent = `Zaktualizowano ${new Date().toLocaleTimeString('pl-PL', {hour:'2-digit', minute:'2-digit', second:'2-digit'})}`;
    $('map-caption').textContent = select.options[select.selectedIndex].text;
    const ranking = bots.slice().sort((a,b)=>b.level-a.level||a.name.localeCompare(b.name)).slice(0,10);
    const rankingBox = $('live-ranking'), rankingIds = new Set();
    ranking.forEach((b,i) => {
      const id = String(b.id); rankingIds.add(id);
      let row = rankingBox.querySelector(`a[data-bot-id="${CSS.escape(id)}"]`);
      if (!row) { row = document.createElement('a'); row.dataset.botId = id; }
      row.className = b.id === globalTopId ? 'is-global-leader' : '';
      row.href = `/player/${b.id}`;
      const html = `<b>#${i+1}</b><img class="class-portrait class-portrait--live" src="${portrait(b.job)}" alt=""> ${escape(b.name)}${b.in_party?'<mark class="pt-mark">PT</mark>':''}${b.stuck?'<mark class="stuck-mark">⚠</mark>':''} <span>${levelMarkup(b)}</span>`;
      if (row.innerHTML !== html) row.innerHTML = html;
      rankingBox.appendChild(row);
    });
    rankingBox.querySelectorAll('a[data-bot-id]').forEach(row => { if (!rankingIds.has(row.dataset.botId)) row.remove(); });
    if (!ranking.length) rankingBox.innerHTML = '<p class="muted">Brak botów spełniających filtr.</p>';
    else rankingBox.querySelector('.muted')?.remove();
    renderActivities(bots);
    insights(mapId,bots);
  }
  async function load() {
    try {
      const response = await fetch('/api/live-bots', {cache:'no-store'}), data = await response.json();
      if (!data.ok) return;
      globalTopId = data.global_top_id; topLevelRanks = data.top_level_ranks || {}; snapshot = data.bots.map(bot => { const b = data.bounds[String(bot.map_index)] || data.bounds[bot.map_index]; return b ? {...bot, px:(bot.x-b[0])/b[2]*100, py:(bot.y-b[1])/b[3]*100} : bot; });
      ensureChannelUI(data.channels || [1]);
      const globalAverage = snapshot.length ? (snapshot.reduce((sum,bot)=>sum+bot.level,0)/snapshot.length).toFixed(1) : '0';
      if ($('overview-bots')) $('overview-bots').textContent = snapshot.length;
      if ($('overview-avg')) $('overview-avg').textContent = globalAverage;
      if ($('overview-party')) $('overview-party').textContent = snapshot.filter(bot=>bot.in_party).length;
      if ($('overview-max')) $('overview-max').textContent = snapshot.length ? Math.max(...snapshot.map(bot=>bot.level)) : '0';
      renderOverviewMaps();
      renderWorldInsights();
      if (mode.value === 'live') render();
    } catch (err) { console.error('live-widget load()', err); $('live-count').textContent = 'Brak danych live'; }
  }
  async function loadHeat() {
    try {
      const mapId = Number(select.value);
      const response = await fetch(`/api/heat-events?type=${encodeURIComponent(mode.value)}&map=${mapId}`, {cache:'no-store'}), data = await response.json();
      if (!data.ok) return;
      const events = data.events || [];
      map.dataset.mapIndex = String(mapId);
      map.querySelectorAll('.bot-point,.heat-point').forEach(node => node.remove());
      window.SebanHeatmap.render(map,data.cells||[],data.max||0,mode.value);
    const label = ({deaths:'zgonów botów',metins:'rozbitych Metinów',bosses:'zabitych bossów'})[mode.value] || 'zdarzeń';
      $('live-count').textContent = `${data.total||0} ${label}`;
      $('map-caption').textContent = `${select.options[select.selectedIndex].text} · ${label}`;
      $('stat-visible').textContent = data.total||0; $('stat-pt').textContent = '—'; $('stat-avg').textContent = 'historia'; $('stat-max').textContent = '●';
      $('live-ranking').innerHTML = events.slice(0,15).map((event,i)=>`<a href="#"><b>#${i+1}</b> ${escape(event.name||'Zdarzenie')} <span>${String(event.time).slice(11,16)}</span></a>`).join('') || '<p class="muted">Brak zdarzeń na tej mapie.</p>';
      const activity = $('live-activity'); if (activity) activity.innerHTML = '<p class="muted">W trybie mapy cieplnej aktywności nie są wyświetlane.</p>';
    } catch (_) { $('live-count').textContent = 'Brak danych heatmapy'; }
  }
  async function refreshRestartInfo() {
    try {
      const data = await fetch('/api/manage-status',{cache:'no-store'}).then(r=>r.json());
      const time = Number(data.last_restart_time || 0); const label=time ? new Date(time * 1000).toLocaleString('pl-PL') : 'Brak danych';
      restartInfo.textContent = time ? `Ostatni restart: ${label}` : ''; if ($('overview-restart')) $('overview-restart').textContent=label;
      Object.entries(data.rates || {}).forEach(([name,value]) => { const node=$(`overview-rate-${name}`); if (node) node.textContent=`${value}%`; });
      // Event tymczasowy (np. "podwójny drop na godzinę") na tę ratę -- kolor
      // wiersza + licznik do końca, żeby było widać na pierwszy rzut oka że
      // to nie jest stała rata serwera tylko coś co zaraz się skończy.
      ['exp','drop','yang'].forEach(name => {
        const row = $(`rate-row-${name}`), badge = $(`rate-bonus-${name}`);
        if (!row || !badge) return;
        const ev = (data.events || {})[name];
        if (ev && ev.active) {
          row.classList.add('rate-event-active');
          badge.hidden = false;
          badge.dataset.until = ev.until || '';
          badge.innerHTML = `⚡ +${ev.value}% · <span class="rate-bonus-countdown"></span>`;
        } else {
          row.classList.remove('rate-event-active');
          badge.hidden = true;
          badge.dataset.until = '';
        }
      });
    } catch (_) {}
  }
  function tickRateBonusCountdowns() {
    document.querySelectorAll('.rate-bonus[data-until]').forEach(badge => {
      const until = Number(badge.dataset.until || 0);
      const span = badge.querySelector('.rate-bonus-countdown');
      if (!until || !span) return;
      const left = until - Math.floor(Date.now() / 1000);
      if (left <= 0) { badge.hidden = true; const row = badge.closest('.rate-row'); if (row) row.classList.remove('rate-event-active'); return; }
      // >=1h: "1h48min" -- >=1min: "48 min" -- poniżej minuty: sekundy, żeby
      // ostatnia chwila eventu była czytelna, a nie np. "108 minut" zbiorczo.
      const h = Math.floor(left / 3600), m = Math.floor((left % 3600) / 60), s = left % 60;
      span.textContent = h > 0 ? `${h}h${String(m).padStart(2,'0')}min` : m > 0 ? `${m} min` : `${s} s`;
    });
  }
  let lastInteraction = Date.now();
  const markInteraction = () => { lastInteraction = Date.now(); };
  document.querySelectorAll('[data-level]').forEach(button => button.addEventListener('click', () => { markInteraction(); currentLevel = button.dataset.level; document.querySelectorAll('[data-level]').forEach(x=>x.classList.toggle('active',x===button)); render(); }));
  [select, search, $('show-names'), $('party-only')].forEach(node => node.addEventListener('input', () => mode.value === 'live' ? render() : loadHeat()));
  mode.addEventListener('input', () => mode.value === 'live' ? render() : loadHeat());
  [select, search, $('show-names'), $('party-only'), mode, $('map-autoplay')].forEach(node => node.addEventListener('input', markInteraction));
  window.addEventListener('pointerdown', markInteraction, {passive:true});
  setInterval(() => { if (!$('map-autoplay').checked || Date.now() - lastInteraction < 15000) return; const next=(select.selectedIndex+1)%select.options.length; select.selectedIndex=next; mode.value === 'live' ? render() : loadHeat(); }, 8000);
  const insightToggle=$('live-insights-toggle');
  if(insightToggle)insightToggle.addEventListener('click',()=>{const shell=document.querySelector('.live-shell'),visible=shell.classList.toggle('show-map-insights');insightToggle.setAttribute('aria-expanded',String(visible));insightToggle.textContent=visible?'← Ranking i aktywności':'▦ Diagramy mapy'});
  const sidebarTabs=$('live-sidebar-tabs');
  if(sidebarTabs)sidebarTabs.addEventListener('click',event=>{const btn=event.target.closest('button[data-tab]');if(!btn)return;sidebarTabs.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b===btn));document.querySelector('.live-sidebar').dataset.sidebarTab=btn.dataset.tab});
  load(); refreshRestartInfo(); tickRateBonusCountdowns(); setInterval(load, 1500); setInterval(refreshRestartInfo, 30000); setInterval(tickRateBonusCountdowns, 1000);
})();
