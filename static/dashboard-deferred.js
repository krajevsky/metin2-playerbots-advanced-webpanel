(() => {
  const widgets = document.getElementById('dashboard-widgets') || document.querySelector('.dashboard-widgets');
  if (!widgets) return;

  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const portrait = job => {
    const files = ['warrior_m.bmp','assassin_w.bmp','sura_m.bmp','shaman_w.bmp','warrior_w.bmp','assassin_m.bmp','sura_w.bmp','shaman_m.bmp'];
    return `/static/class-portraits/${files[Math.max(0, Math.min(files.length - 1, Number(job) || 0))]}`;
  };
  const shimmer = label => `<div class="dashboard-widget-loader ld-shimmer" aria-label="${escape(label)}"><i></i><i></i><i></i></div>`;
  widgets.querySelectorAll('.panel').forEach(panel => {
    panel.classList.add('is-loading');
    if (!panel.querySelector('.dashboard-widget-loader')) panel.insertAdjacentHTML('beforeend', shimmer('Ładowanie danych'));
  });

  function updateWorld(summary) {
    const values = {
      'overview-bots': summary.bots,
      'overview-avg': summary.average_level,
      'overview-party': summary.party_bots,
      'overview-max': summary.max_level,
    };
    Object.entries(values).forEach(([id, value]) => { const node = document.getElementById(id); if (node) node.textContent = value; });
    const guild = document.querySelector('.world-summary-grid > div:nth-child(6) b');
    if (guild) guild.textContent = summary.guilds ?? 0;
    ['exp','drop','yang'].forEach(key => {
      const node = document.getElementById(`overview-rate-${key}`);
      if (node && summary.rates) node.textContent = `${summary.rates[key] ?? 0}%`;
    });
  }

  function renderSystem(system) {
    const panel = widgets.querySelector('[data-dashboard-widget="system"]') || widgets.querySelector('.system-dashboard');
    if (!panel) return;
    const title = panel.querySelector('h2')?.textContent || 'Obciążenie VPS';
    if (!system || !Object.keys(system).length) {
      panel.innerHTML = `<h2>${escape(title)}</h2><p class="muted">Brak jeszcze danych monitoringu.</p>`;
      panel.classList.remove('is-loading');
      return;
    }
    const disk = system.disk_percent !== undefined;
    panel.innerHTML = `<h2>${escape(title)}</h2><div class="dashboard-donuts">${[['cpu-donut','cpu_percent','CPU'],['ram-donut','ram_percent','RAM'],...(disk ? [['disk-donut','disk_percent','Dysk']] : [])].map(([id,key,label]) => `<div class="donut-wrap"><canvas id="${id}"></canvas><b>${escape(system[key])}%<small>${label}</small></b></div>`).join('')}</div><div class="monitor-details"><span><b>Pamięć RAM</b><strong>${escape(system.ram_used_mb)} / ${escape(system.ram_total_mb)} MB</strong></span>${disk ? `<span><b>Dysk</b><strong>${(Number(system.disk_used_mb || 0) / 1024).toFixed(1)} / ${(Number(system.disk_total_mb || 0) / 1024).toFixed(1)} GB</strong></span>` : ''}</div>`;
    panel.classList.remove('is-loading');
  }

  function renderRanking(rankings, globalTopId) {
    const panel = widgets.querySelector('.ranking-carousel');
    if (!panel) return;
    const title = panel.querySelector('#quick-rank-title');
    const subtitle = panel.querySelector('#quick-rank-subtitle');
    const slides = rankings.map((ranking, index) => `<ol class="quick-rank-slide" data-title="${escape(ranking.title)}" data-subtitle="${escape(ranking.subtitle)}" ${index ? 'hidden' : ''}>${(ranking.items || []).map(row => `<li class="${row.id === globalTopId ? 'quick-leader' : ''}"><a href="/player/${Number(row.id)}"><img class="class-portrait class-portrait--carousel" src="${portrait(row.job)}" alt="" aria-hidden="true">${escape(row.name)}</a><b>${escape(row.value)}</b></li>`).join('') || '<li class="quick-rank-empty muted">Brak danych — jeszcze nikt tego nie zrobił.</li>'}</ol>`).join('');
    const dots = rankings.map((_, index) => `<button class="${index ? '' : 'active'}" data-slide="${index}"></button>`).join('');
    panel.querySelector('#quick-rank-slides').innerHTML = slides;
    panel.querySelector('.carousel-dots').innerHTML = dots;
    if (title) title.textContent = rankings[0]?.title || 'Rankingi';
    if (subtitle) subtitle.textContent = rankings[0]?.subtitle || '';
    panel.classList.remove('is-loading');
  }

  function renderDeferred(data) {
    renderSystem(data.system);
    const mapData = {
      'map-data': data.map_rows || [],
      'channel-map-data': data.channel_map_rows || [],
      'channels-data': data.dashboard_channels || [],
      'shop-map-data': data.shop_map_rows || [],
      'live-regen-data': {global: data.live_regen || {}, maps: data.live_map_regens || {}}
    };
    Object.entries(mapData).forEach(([id, value]) => { const node = document.getElementById(id); if (node) node.textContent = JSON.stringify(value); });
    renderRanking(data.quick_rankings || [], data.global_top_id);
    updateWorld(data.world_summary || {});
    widgets.classList.remove('dashboard-widgets--loading');
    // dashboard-charts.js was already loaded against empty placeholders. Run
    // it once more after the data and canvases exist; its own code remains the
    // single source of truth for Chart.js rendering.
    const mapCanvas = document.getElementById('map-donut');
    if (window.Chart && mapCanvas) {
      const existingChart = Chart.getChart(mapCanvas);
      if (existingChart) existingChart.destroy();
    }
    const script = document.createElement('script');
    script.src = '/static/dashboard-charts.js?v=deferred';
    script.onload = () => widgets.querySelectorAll('.panel').forEach(panel => panel.classList.remove('is-loading'));
    document.body.appendChild(script);
  }

  fetch('/api/dashboard-deferred', {cache: 'no-store'})
    .then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
    .then(renderDeferred)
    .catch(() => widgets.querySelectorAll('.panel').forEach(panel => {
      panel.classList.remove('is-loading');
      const loader = panel.querySelector('.dashboard-widget-loader');
      if (loader) loader.outerHTML = '<p class="muted dashboard-widget-error">Nie udało się doładować danych.</p>';
    }));
})();
