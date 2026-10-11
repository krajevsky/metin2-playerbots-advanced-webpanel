(() => {
  const list = document.getElementById('shop-transactions-list');
  if (!list) return;
  const labels = JSON.parse(document.getElementById('shop-transactions-labels').textContent);
  const status = document.getElementById('shop-transactions-status');
  const pause = document.getElementById('shop-transactions-pause');
  const more = document.getElementById('shop-transactions-more');
  const locale = document.documentElement.lang === 'en' ? 'en-US' : 'pl-PL';
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let newest = 0, oldest = 0, paused = false, loading = false;

  function actor(id, name, isBot) {
    const badge = `<small class="shop-actor-type">${isBot ? labels.bot : labels.player}</small>`;
    return `<a href="/player/${Number(id)}">${escape(name)}</a>${badge}`;
  }
  function card(row) {
    const icon = row.icon_url ? `<img src="${escape(row.icon_url)}" alt="" loading="lazy">` : '';
    const price = `${Number(row.yang).toLocaleString(locale)} Yang${row.cheque ? ` · ${Number(row.cheque).toLocaleString(locale)} ${labels.cheque}` : ''}`;
    return `<article class="shop-transaction" data-id="${Number(row.id)}">
      <time>${escape(row.time)}</time>
      <div class="shop-transaction-main"><div class="shop-transaction-actors"><span><small>${labels.buyer}</small>${actor(row.buyer_id,row.buyer,row.buyer_is_bot)}</span><span class="shop-transaction-arrow" aria-hidden="true">←</span><span><small>${labels.seller}</small>${actor(row.seller_id,row.seller,row.seller_is_bot)}</span></div>
      <div class="shop-transaction-item">${icon}<a href="/economy/item/${Number(row.vnum)}">${escape(row.item_name)}</a><small>×${Number(row.quantity)}</small></div></div>
      <strong class="shop-transaction-price">${price}</strong>
    </article>`;
  }
  function paintStatus() {
    status.textContent = paused ? labels.paused : labels.live;
    status.classList.toggle('is-paused', paused);
    pause.textContent = paused ? labels.resume : labels.pause;
  }
  async function read(query = '') {
    const response = await fetch(`/api/shop-transactions${query}`, {cache:'no-store'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
  async function initial() {
    try {
      const data = await read();
      const rows = data.transactions || [];
      list.innerHTML = rows.length ? rows.map(card).join('') : `<p class="muted">${labels.empty}</p>`;
      list.setAttribute('aria-busy','false');
      newest = rows[0]?.id || 0; oldest = rows[rows.length - 1]?.id || 0;
      more.hidden = !data.has_more;
      paintStatus();
    } catch (_) {
      list.innerHTML = `<p class="muted">${labels.error}</p>`;
      list.setAttribute('aria-busy','false');
      setTimeout(initial, 5000);
    }
  }
  async function refresh() {
    if (paused || loading || document.hidden) return;
    if (!newest) { await initial(); return; }
    loading = true;
    try {
      for (let page = 0; page < 5; page++) {
        const data = await read(`?after=${newest}`);
        const rows = data.transactions || [];
        if (!rows.length) break;
        list.querySelector('.muted')?.remove();
        for (const row of [...rows].reverse()) if (!list.querySelector(`[data-id="${Number(row.id)}"]`)) list.insertAdjacentHTML('afterbegin', card(row));
        newest = rows[rows.length - 1].id;
        if (!oldest) oldest = rows[0].id;
        if (!data.has_more) break;
      }
      while (list.querySelectorAll('.shop-transaction').length > 240) list.lastElementChild.remove();
      oldest = Number(list.lastElementChild?.dataset.id) || oldest;
    } catch (_) { status.textContent = labels.error; }
    loading = false;
  }
  pause.addEventListener('click', () => { paused = !paused; paintStatus(); if (!paused) refresh(); });
  more.addEventListener('click', async () => {
    if (loading || !oldest) return;
    loading = true; more.disabled = true;
    try {
      const data = await read(`?before=${oldest}`);
      const rows = data.transactions || [];
      list.insertAdjacentHTML('beforeend', rows.map(card).join(''));
      if (rows.length) oldest = rows[rows.length - 1].id;
      more.hidden = !data.has_more;
    } catch (_) { status.textContent = labels.error; }
    more.disabled = false; loading = false;
  });
  paintStatus(); initial();
  setInterval(refresh, 8000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
})();
