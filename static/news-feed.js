(() => {
  const list = document.getElementById('news-feed');
  if (!list) return;
  const storageKey = 'seban-panel-news-cache-v2';
  const visibilityKey = 'seban-panel-news-hidden';
  const ticker = list.closest('.news-ticker');
  const toggle = document.getElementById('news-toggle');
  function setHidden(hidden) {
    ticker.classList.toggle('is-hidden', hidden);
    toggle.textContent = hidden ? 'Wiadomości' : 'Ukryj';
    toggle.setAttribute('aria-expanded', String(!hidden));
    localStorage.setItem(visibilityKey, hidden ? '1' : '0');
  }
  if (toggle) {
    setHidden(localStorage.getItem(visibilityKey) === '1');
    toggle.addEventListener('click', () => setHidden(!ticker.classList.contains('is-hidden')));
  }
  let cached = [];
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) || '[]');
    cached = Array.isArray(stored) ? stored.filter(event => event && event.key && event.message) : [];
  } catch (_) { cached = []; }
  const seen = new Set(cached.map(event => event.key));
  const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  function render(events) {
    if (!events.length) {
      list.innerHTML = '<li class="muted">Oczekiwanie na nowe ważne wydarzenia ze świata…</li>';
      return;
    }
    list.innerHTML = events.slice(-8).map(event => `<li${Number(event.refine_tier) >= 8 ? ' class="refine-rare"' : ''}><time>${escape(event.time)}</time><span>${escape(event.message)}</span></li>`).join('');
    list.dataset.loaded = '1';
  }
  render(cached);
  async function refresh() {
    try {
      const response = await fetch('/api/news-feed', {cache: 'no-store'});
      if (!response.ok) throw new Error('Nie udało się pobrać wiadomości.');
      const data = await response.json();
      if (!data.ok) throw new Error('Nieprawidłowa odpowiedź feedu.');
      const fresh = data.events.filter(event => !seen.has(event.key));
      if (fresh.length) {
        fresh.forEach(event => seen.add(event.key));
        cached = [...cached, ...fresh].slice(-40);
        localStorage.setItem(storageKey, JSON.stringify(cached));
      }
      // A reload must keep showing the last received events. The API may have
      // no new rare event in its current window, but that is not an empty feed.
      render(cached);
    } catch (_) {
      if (!cached.length) list.innerHTML = '<li class="muted">Feed wydarzeń jest chwilowo niedostępny.</li>';
    }
  }
  refresh();
  setInterval(refresh, 30000);
})();
