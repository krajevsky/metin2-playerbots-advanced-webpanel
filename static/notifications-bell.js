(() => {
  const bell = document.getElementById('notif-bell');
  if (!bell) return;
  const badge = document.getElementById('notif-badge');
  const dropdown = document.getElementById('notif-dropdown');
  const list = document.getElementById('notif-list');
  const markAllBtn = document.getElementById('notif-mark-all');
  const toastStack = document.getElementById('notif-toast-stack');
  const escapeHtml = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let open = false;

  function closeDropdown() { open = false; dropdown.hidden = true; bell.setAttribute('aria-expanded', 'false'); }
  function toggleDropdown() {
    open = !open;
    dropdown.hidden = !open;
    bell.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) markVisibleAsRead();
  }
  bell.addEventListener('click', e => { e.stopPropagation(); toggleDropdown(); });
  document.addEventListener('click', e => { if (open && !dropdown.contains(e.target) && e.target !== bell) closeDropdown(); });
  if (markAllBtn) markAllBtn.addEventListener('click', e => {
    e.stopPropagation();
    fetch('/api/notifications/read-all', {method: 'POST'}).then(refresh).catch(() => {});
  });

  function markVisibleAsRead() {
    const unreadEls = [...list.querySelectorAll('.notif-item.is-unread')];
    if (!unreadEls.length) return;
    const ids = unreadEls.map(el => el.dataset.id);
    fetch('/api/notifications/read', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ids}),
    }).then(() => {
      unreadEls.forEach(el => el.classList.remove('is-unread'));
      updateBadge(Math.max(0, (parseInt(badge.textContent, 10) || 0) - ids.length));
    }).catch(() => {});
  }

  function updateBadge(n) {
    if (n > 0) { badge.hidden = false; badge.textContent = n > 99 ? '99+' : n; }
    else badge.hidden = true;
  }

  function renderList(items) {
    if (!items.length) { list.innerHTML = '<p class="notif-empty">Brak powiadomień.</p>'; return; }
    list.innerHTML = items.map(n => {
      const external = n.link_url && n.link_url.startsWith('http');
      return `<a class="notif-item ${n.read ? '' : 'is-unread'}" data-id="${n.id}" href="${n.link_url || '#'}" ${external ? 'target="_blank" rel="noopener"' : ''}>
        <p class="notif-item-title">${escapeHtml(n.title)}</p>
        ${n.body ? `<p class="notif-item-body">${escapeHtml(n.body)}</p>` : ''}
        <p class="notif-item-time">${n.created_at}</p>
      </a>`;
    }).join('');
  }

  function showToast(n) {
    const el = document.createElement('div');
    el.className = 'notif-toast';
    el.innerHTML = `<b>${escapeHtml(n.title)}</b><span>${n.body ? escapeHtml(n.body) : 'Kliknij, żeby zobaczyć.'}</span>`;
    el.addEventListener('click', () => {
      fetch('/api/notifications/read', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ids: [n.id]}),
      }).catch(() => {});
      if (n.link_url) window.location.href = n.link_url;
    });
    toastStack.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .4s'; setTimeout(() => el.remove(), 400); }, 9000);
  }

  async function refresh() {
    try {
      const data = await fetch('/api/notifications', {cache: 'no-store'}).then(r => r.json());
      if (!data.ok) return;
      updateBadge(data.unread_count);
      renderList(data.items);
      const toPop = data.items.filter(n => !n.popped);
      toPop.forEach(showToast);
      if (toPop.length) {
        fetch('/api/notifications/pop', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ids: toPop.map(n => n.id)}),
        }).catch(() => {});
      }
    } catch (_) {}
  }
  refresh();
  setInterval(refresh, 30000);
})();
