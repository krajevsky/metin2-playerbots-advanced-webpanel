(() => {
  const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = '/static/live-overrides.css'; document.head.appendChild(css);
  let snapshot = [], globalTopId = null, currentLevel = 'all', currentChannel = 'all', knownChannels = [1];
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
  const regenNode=document.getElementById('live-regen-data'),regenInfo=regenNode?JSON.parse(regenNode.textContent||'{}'):{global:{delay:{mob:100,boss:100},count:{mob:100,boss:100}},maps:{values:{},stones:{}}};
  function insightRows(id, rows, colors){const total=rows.reduce((n,x)=>n+x[1],0)||1,node=$(id);if(!node)return;node.innerHTML=rows.map(([label,count],i)=>`<div class="map-insight-row"><span>${escape(label)}</span><i style="--share:${Math.round(count/total*100)}%;--chart-color:${colors[i]}"></i><b>${count}</b></div>`).join('')}
  function renderInsights(mapId,bots){insightRows('map-channel-chart',[...new Set(snapshot.map(b=>Number(b.channel||1)))].sort((a,b)=>a-b).map(ch=>[`CH${ch}`,bots.filter(b=>Number(b.channel||1)===ch).length]),['#ff8c00','#800080','#30b6ff']);insightRows('map-empire-chart',[[1,'Shinsoo'],[2,'Chunjo'],[3,'Jinno']].map(([e,n])=>[n,bots.filter(b=>Number(b.empire||0)===e).length]),['#d95a54','#e8b93f','#4f86d9']);const m=regenInfo.maps||{},g=regenInfo.global||{delay:{mob:100,boss:100},count:{mob:100,boss:100}},v=m.values||{},st=m.stones||{},n=$('map-respawn-summary');if(n)n.innerHTML=`<div><b>⚔ Potwory</b><small>${v[mapId]?`Nadpisanie mapy · ${v[mapId]} s`:`Globalnie · ${g.delay.mob}% czasu podstawowego`}</small></div><div><b>🗿 Metiny i bossy</b><small>${st[mapId]?`Nadpisanie mapy · ${st[mapId]} s`:`Globalnie · ${g.delay.boss}% czasu podstawowego`}</small></div><div><b>✦ Liczebność</b><small>Potwory ${g.count.mob}% · Metiny/bossy ${g.count.boss}%</small></div>`}
  document.querySelectorAll('[data-insight]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-insight]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('[data-insight-page]').forEach(x=>x.classList.toggle('active',x.dataset.insightPage===b.dataset.insight))}));
  function render() {
    if (mode.value !== 'live') return;
    const mapId = Number(select.value), needle = search.value.trim().toLowerCase();
    map.dataset.mapIndex = String(mapId);
    const bots = snapshot.filter(b => b.map_index === mapId && levelOK(b.level) && (!$('party-only').checked || b.in_party) && (!needle || b.name.toLowerCase().includes(needle)) && (currentChannel === 'all' || Number(b.channel) === Number(currentChannel)));
    map.querySelectorAll('.bot-point,.heat-point').forEach(node => node.remove());
    bots.forEach(bot => {
      const point = document.createElement('a'); point.className = `bot-point ch-${bot.channel || 1} ${bot.in_party ? 'is-pt' : ''}${bot.stuck ? ' is-stuck' : ''}${bot.fighting_metin ? ' is-metin' : ''}`;
      point.href = `/player/${bot.id}`; point.style.left = `${Math.max(1,Math.min(99,bot.px))}%`; point.style.top = `${Math.max(1,Math.min(99,bot.py))}%`;
      point.title = `${bot.name} · poziom ${bot.level}${knownChannels.length > 1 ? ' · CH' + (bot.channel || 1) : ''}${bot.in_party ? ' · PT' : ''}${bot.stuck ? ' · możliwie zablokowany' : ''}${bot.fighting_metin ? ' · walczy z Metinem' : ''}`;
      if ($('show-names').checked) point.innerHTML = `<em>${escape(bot.name)} (${bot.level})</em>`;
      map.appendChild(point);
    });
    const average = bots.length ? (bots.reduce((sum,b)=>sum+b.level,0)/bots.length).toFixed(1) : '—';
    $('stat-visible').textContent = bots.length; $('stat-pt').textContent = bots.filter(b=>b.in_party).length; $('stat-avg').textContent = average; $('stat-max').textContent = bots.length ? Math.max(...bots.map(b=>b.level)) : '—';
    $('live-count').textContent = `${bots.length} botów na mapie`;
    $('map-caption').textContent = select.options[select.selectedIndex].text;
$('live-ranking').innerHTML = bots.sort((a,b)=>b.level-a.level||a.name.localeCompare(b.name)).slice(0,10).map((b,i)=>`<a class="${b.id === globalTopId ? 'is-global-leader' : ''}" href="/player/${b.id}"><b>#${i+1}</b><img class="class-portrait class-portrait--live" src="${portrait(b.job)}" alt=""> ${escape(b.name)}${b.in_party?'<mark class="pt-mark">PT</mark>':''}${b.stuck?'<mark class="stuck-mark">⚠</mark>':''} <span>Lv ${b.level}</span></a>`).join('') || '<p class="muted">Brak botów spełniających filtr.</p>';
    renderActivities(bots);
    renderInsights(mapId,bots);
  }
  async function load() {
    try {
      const response = await fetch('/api/live-bots', {cache:'no-store'}), data = await response.json();
      if (!data.ok) return;
      globalTopId = data.global_top_id; snapshot = data.bots.map(bot => { const b = data.bounds[String(bot.map_index)] || data.bounds[bot.map_index]; return b ? {...bot, px:(bot.x-b[0])/b[2]*100, py:(bot.y-b[1])/b[3]*100} : bot; });
      ensureChannelUI(data.channels || [1]);
      const globalAverage = snapshot.length ? (snapshot.reduce((sum,bot)=>sum+bot.level,0)/snapshot.length).toFixed(1) : '0';
      if ($('overview-bots')) $('overview-bots').textContent = snapshot.length;
      if ($('overview-avg')) $('overview-avg').textContent = globalAverage;
      if ($('overview-party')) $('overview-party').textContent = snapshot.filter(bot=>bot.in_party).length;
      if ($('overview-max')) $('overview-max').textContent = snapshot.length ? Math.max(...snapshot.map(bot=>bot.level)) : '0';
      renderOverviewMaps();
      if (mode.value === 'live') render();
    } catch (_) { $('live-count').textContent = 'Brak danych live'; }
  }
  async function loadHeat() {
    try {
      const response = await fetch(`/api/heat-events?type=${encodeURIComponent(mode.value)}`, {cache:'no-store'}), data = await response.json();
      if (!data.ok) return;
      const mapId = Number(select.value), bound = data.bounds[String(mapId)] || data.bounds[mapId];
      const events = data.events.filter(event => event.map_index === mapId);
      map.dataset.mapIndex = String(mapId);
      map.querySelectorAll('.bot-point,.heat-point').forEach(node => node.remove());
      events.forEach(event => { const dot=document.createElement('i'); dot.className='heat-point'; dot.style.left=`${Math.max(1,Math.min(99,(event.x-bound[0])/bound[2]*100))}%`; dot.style.top=`${Math.max(1,Math.min(99,(event.y-bound[1])/bound[3]*100))}%`; dot.title=`${event.name||'Zdarzenie'} · ${event.time}`; map.appendChild(dot); });
    const label = ({deaths:'zgonów botów',metins:'rozbitych Metinów',bosses:'zabitych bossów'})[mode.value] || 'zdarzeń';
      $('live-count').textContent = `${events.length} ${label} / 24 h`;
      $('map-caption').textContent = `${select.options[select.selectedIndex].text} · ${label}`;
      $('stat-visible').textContent = events.length; $('stat-pt').textContent = '—'; $('stat-avg').textContent = '24 h'; $('stat-max').textContent = '●';
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
  load(); refreshRestartInfo(); tickRateBonusCountdowns(); setInterval(load, 1500); setInterval(refreshRestartInfo, 30000); setInterval(tickRateBonusCountdowns, 1000);
})();
