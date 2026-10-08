// Motyw "Laka i Złoto": zachowanie otoczki (base.html + _laka_nav.html).
// Ctrl+K (strony + szukanie gracza), arkusz "Więcej" na telefonie, animacje
// przejść między stronami i licznik botów online w górnej belce.
(() => {
  const body = document.body;
  if (body.dataset.skin !== 'laka') return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const main = document.querySelector('main');
  const tpl = document.getElementById('laka-sheet-tpl');

  // Wejście strony: bloki pojawiają się po kolei.
  if (main) [...main.children].forEach((el, i) => el.style.setProperty('--laka-i', Math.min(i, 8)));

  // Wyjście strony: krótkie "odpłynięcie" treści przed przejściem pod zwykły link.
  document.addEventListener('click', e => {
    if (reduced || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest('a[href]');
    if (!a || a.target || a.hasAttribute('download')) return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin || (url.pathname === location.pathname && url.search === location.search)) return;
    e.preventDefault();
    body.classList.add('laka-leaving');
    setTimeout(() => { location.href = url.href; }, 150);
  });
  // Powrót przyciskiem "wstecz" z bfcache nie może zostawić pustej strony.
  addEventListener('pageshow', () => body.classList.remove('laka-leaving'));

  function pages() {
    if (!tpl) return [];
    return [...tpl.content.querySelectorAll('.laka-sheet-links a')].map(a => ({
      label: a.textContent.trim(), section: a.dataset.lakaSection, icon: a.dataset.lakaIcon, href: a.getAttribute('href'),
    }));
  }
  const layer = document.createElement('div');
  body.appendChild(layer);
  const close = () => { layer.innerHTML = ''; };
  layer.addEventListener('click', e => { if (e.target.matches('[data-laka-close]')) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });

  function openPalette() {
    const all = pages(), playersUrl = tpl ? tpl.dataset.playersUrl : '/players';
    layer.innerHTML = '<div class="laka-overlay" data-laka-close><div class="laka-palette" role="dialog" aria-label="Szukaj"><input id="laka-q" placeholder="Strona albo nick gracza…" autocomplete="off"><ul id="laka-list"></ul></div></div>';
    const q = layer.querySelector('#laka-q'), list = layer.querySelector('#laka-list');
    let sel = 0, cur = [];
    const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const draw = () => {
      const v = q.value.trim().toLowerCase();
      cur = all.filter(p => !v || (p.label + ' ' + p.section).toLowerCase().includes(v)).slice(0, 10);
      if (v) cur.push({ label: `Szukaj gracza „${q.value.trim()}”`, section: 'Gracze i boty', icon: all.find(p => p.section === 'Postacie')?.icon || '', href: `${playersUrl}?q=${encodeURIComponent(q.value.trim())}` });
      sel = Math.min(sel, Math.max(cur.length - 1, 0));
      list.innerHTML = cur.length ? cur.map((p, k) => `<li><a href="${esc(p.href)}" class="${k === sel ? 'sel' : ''}"><img src="${esc(p.icon)}" alt=""><span>${esc(p.label)}</span><small>${esc(p.section)}</small></a></li>`).join('')
        : '<li class="laka-empty">Wpisz nazwę strony albo nick.</li>';
    };
    q.addEventListener('input', () => { sel = 0; draw(); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { sel = Math.min(sel + 1, cur.length - 1); draw(); e.preventDefault(); }
      if (e.key === 'ArrowUp') { sel = Math.max(sel - 1, 0); draw(); e.preventDefault(); }
      if (e.key === 'Enter' && cur[sel]) { location.href = cur[sel].href; }
    });
    draw(); q.focus();
  }
  document.getElementById('laka-open-palette')?.addEventListener('click', openPalette);
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPalette(); }
  });
  document.getElementById('laka-more')?.addEventListener('click', () => {
    if (!tpl) return;
    layer.innerHTML = '';
    layer.appendChild(tpl.content.cloneNode(true));
  });

  // Licznik botów online: /api/manage-status zwraca "bots": len(live_bots()).
  const count = document.getElementById('laka-live-count');
  async function refresh() {
    if (!count || document.hidden) return;
    try {
      const data = await fetch('/api/manage-status', { cache: 'no-store' }).then(r => r.json());
      if (!data.ok) return;
      const next = String(data.bots ?? '—');
      if (count.textContent !== next) {
        count.textContent = next;
        count.classList.remove('laka-flash'); void count.offsetWidth; count.classList.add('laka-flash');
      }
    } catch (_) { /* belka zostaje z ostatnią wartością */ }
  }
  refresh();
  setInterval(refresh, 30000);
  document.addEventListener('visibilitychange', refresh);
})();
