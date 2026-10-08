// Motyw "Laka i Złoto": zachowanie otoczki (base.html + _laka_nav.html).
// Ctrl+K (strony + szukanie gracza), arkusz "Więcej" na telefonie, animacje
// przejść między stronami i licznik botów online w górnej belce.
(() => {
  const body = document.body;
  if (body.dataset.skin !== 'laka') return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const main = document.querySelector('main');
  const tpl = document.getElementById('laka-sheet-tpl');

  // Nagłówek strony a tytuł w górnej belce: na stronach szczegółów (gildia, konto, przedmiot…)
  // nazwa z <h1> trafia do belki; gdzie indziej <h1> znika tylko, jeśli powtarza tytuł belki.
  const topTitle = document.querySelector('.laka-crumbs h1');
  const detail = document.querySelector('.laka-top')?.dataset.lakaDetail === '1';
  const pageH1 = main && main.querySelector(detail ? 'h1' : ':scope > h1');
  if (topTitle && pageH1) {
    const norm = s => s.toLowerCase().replace(/[^a-ząćęłńóśźż0-9]+/g, '');
    const a = norm(pageH1.textContent), b = norm(topTitle.textContent);
    if (detail) topTitle.textContent = pageH1.textContent.replace(/\s+/g, ' ').trim();
    // Nagłówek zagnieżdżony we własnym bloku strony (np. karta postaci) zostaje na miejscu.
    if (pageH1.parentElement === main && (detail || (a && b && (a.includes(b) || b.includes(a))))) {
      pageH1.hidden = true;
      const prev = pageH1.previousElementSibling;
      if (prev && prev.classList.contains('eyebrow')) prev.hidden = true;
    }
  }

  // Karty akcji na karcie postaci mają w motywie własne ikony, więc emoji z początku nagłówka znika.
  // Robione w JS, bo tekst nagłówka jest kluczem tłumaczenia EN (i18n-watch.js) i testów.
  const stripEmoji = () => document.querySelectorAll('.admin-card h3, .admin-card > button').forEach(h => {
    const t = h.firstChild;
    if (!t || t.nodeType !== 3) return;
    const clean = t.textContent.replace(/^[\p{Extended_Pictographic}☀-➿️‍\s]+/u, '');
    if (clean !== t.textContent) t.textContent = clean; // tylko przy zmianie, inaczej obserwator kręciłby się w kółko
  });
  stripEmoji();
  // Nagłówki paneli w całym panelu: emoji z początku zastępuje złoty romb z CSS.
  // Tylko na panelu po polsku, bo w EN tekst z emoji jest kluczem tłumaczenia (i18n-watch.js).
  if (document.documentElement.lang !== 'en') {
    document.querySelectorAll('main h1, main h2, main h3, main summary').forEach(h => {
      const t = [...h.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
      if (!t) return;
      const clean = t.textContent.replace(/^\s*[\p{Extended_Pictographic}☀-➿←-⇿⌀-⏿⬀-⯿️‍]+\s*/u, '');
      if (clean !== t.textContent) t.textContent = clean;
    });
  }
  if (document.querySelector('.admin-card h3') && 'MutationObserver' in window)
    new MutationObserver(stripEmoji).observe(document.querySelector('.admin-actions') || document.body, { childList: true, subtree: true, characterData: true });

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
      if (v) cur.push({ label: `Szukaj gracza „${q.value.trim()}”`, section: 'Gracze i boty', icon: 'chars', href: `${playersUrl}?q=${encodeURIComponent(q.value.trim())}` });
      sel = Math.min(sel, Math.max(cur.length - 1, 0));
      list.innerHTML = cur.length ? cur.map((p, k) => `<li><a href="${esc(p.href)}" class="${k === sel ? 'sel' : ''}"><svg aria-hidden="true"><use href="#li-${esc(p.icon)}"/></svg><span>${esc(p.label)}</span><small>${esc(p.section)}</small></a></li>`).join('')
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

  // Pasek "Źródła danych": każdy endpoint /api/*, z którego strona korzysta, z czasem ostatniej odpowiedzi
  // (mierzy go podsłuch fetch w base.html). Kropka mignie przy każdej nowej odpowiedzi.
  const bus = window.lakaBus;
  if (bus && main) {
    const bar = document.createElement('footer');
    bar.className = 'laka-telemetry';
    bar.setAttribute('aria-label', 'Źródła danych');
    main.after(bar);
    const ago = t => { const s = Math.round((Date.now() - t) / 1000); return s < 60 ? `${s} s temu` : `${Math.round(s / 60)} min temu`; };
    const draw = hit => {
      const rows = Object.entries(bus.stats).sort((a, b) => b[1].n - a[1].n);
      bar.hidden = !rows.length;
      bar.innerHTML = '<b>Źródła danych</b>' + rows.map(([path, s]) => `<span class="laka-ep${path === hit ? ' is-hit' : ''}${s.status >= 400 ? ' is-bad' : ''}" title="${s.n}× · ostatnio ${ago(s.at)} · HTTP ${s.status}"><i></i>${path} · ${s.ms} ms</span>`).join('');
    };
    document.addEventListener('laka:api', e => draw(e.detail.path));
    draw();
  }

  // Licznik botów online: /api/manage-status zwraca "bots": len(live_bots()).
  const count = document.getElementById('laka-live-count');
  async function refresh(force) {
    // Pierwszy odczyt zawsze; potem tylko gdy karta jest widoczna (karta otwarta w tle też ma dostać liczbę).
    if (!count || (document.hidden && force !== true)) return;
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
  refresh(true);
  setInterval(refresh, 30000);
  document.addEventListener('visibilitychange', refresh);
})();
