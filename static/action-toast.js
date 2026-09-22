(() => {
  const stack = document.getElementById('action-toast-stack');
  if (!stack) return;
  const ICONS = {
    error: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm4.3 13.3-1.4 1.4L12 13.4l-2.9 2.9-1.4-1.4L10.6 12 7.7 9.1l1.4-1.4L12 10.6l2.9-2.9 1.4 1.4L13.4 12l2.9 2.9z"/></svg>',
    success: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-1.6 14.6-4-4 1.4-1.4 2.6 2.6 5.6-5.6 1.4 1.4-7 7z"/></svg>',
  };
  // Global, so plain (non-AJAX) pages can call this too if they ever want to.
  window.showActionToast = function showActionToast(message, category) {
    category = category === 'error' ? 'error' : 'success';
    const el = document.createElement('div');
    el.className = 'action-toast ' + category;
    el.innerHTML = `<span class="action-toast-icon">${ICONS[category]}</span><span class="action-toast-body"></span><button type="button" class="action-toast-close" aria-label="Zamknij">✕</button>`;
    el.querySelector('.action-toast-body').textContent = message;
    const close = () => { el.classList.add('is-leaving'); setTimeout(() => el.remove(), 250); };
    el.querySelector('.action-toast-close').addEventListener('click', close);
    stack.appendChild(el);
    return close;
  };
})();
