// Opt-in per page: <body data-ajax-forms> (set by that page's own inline
// script, since base.html owns the <body> tag). Submits every <form> inside
// <main> over fetch instead of a normal navigation, swaps <main> with the
// freshly-rendered response (so every dynamic value on the page -- restart
// progress, updater state, checkboxes -- reflects the real new state exactly
// like a full reload would, just without the visible reload/flash-modal),
// and shows the same flash message(s) as a dismiss-on-click toast instead of
// the blocking <dialog> modal. Operator's ask, 2026-09-22: buttons that
// change something shouldn't refresh the whole page.
(() => {
  if (!('ajaxForms' in document.body.dataset)) return;

  function extractFlashes(doc) {
    const modal = doc.getElementById('flash-modal');
    if (!modal) return [];
    return [...modal.querySelectorAll('.flash-card')].map(card => ({
      message: (card.querySelector('span') || card).textContent.trim(),
      category: card.classList.contains('error') ? 'error' : 'success',
    }));
  }

  // innerHTML doesn't execute <script> tags -- swap each for a fresh node
  // (with the same attributes/text) so page-specific behavior (e.g.
  // manage.html's status polling) keeps working after a swap.
  function runScripts(container) {
    container.querySelectorAll('script').forEach(old => {
      const fresh = document.createElement('script');
      [...old.attributes].forEach(a => fresh.setAttribute(a.name, a.value));
      fresh.textContent = old.textContent;
      old.replaceWith(fresh);
    });
  }

  async function submitAjax(form, submitter) {
    const buttons = [...form.querySelectorAll('button')];
    buttons.forEach(b => b.disabled = true);
    try {
      const res = await fetch(form.getAttribute('action') || window.location.href, {
        method: (form.getAttribute('method') || 'GET').toUpperCase(),
        body: new FormData(form, submitter),
        credentials: 'same-origin',
      });
      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const flashes = extractFlashes(doc);
      const newMain = doc.querySelector('main');
      const main = document.querySelector('main');
      if (newMain && main) {
        const dialog = newMain.querySelector('#flash-modal');
        if (dialog) dialog.remove();
        main.innerHTML = newMain.innerHTML;
        runScripts(main);
        bindForms();
      }
      if (flashes.length) {
        flashes.forEach(f => window.showActionToast(f.message, f.category));
      } else if (res.ok) {
        window.showActionToast('Zmiana zapisana.', 'success');
      } else {
        window.showActionToast('Coś poszło nie tak (' + res.status + ').', 'error');
      }
    } catch (err) {
      window.showActionToast('Błąd sieci — spróbuj ponownie.', 'error');
    }
    // Buttons may no longer exist post-swap; re-enabling stale ones is harmless.
    buttons.forEach(b => { try { b.disabled = false; } catch (_) {} });
  }

  function bindForms() {
    document.querySelectorAll('main form').forEach(form => {
      if (form.dataset.ajaxBound) return;
      form.dataset.ajaxBound = '1';
      let clickedSubmitter = null;
      form.addEventListener('click', e => {
        const btn = e.target.closest('button, input[type=submit]');
        if (btn && form.contains(btn)) clickedSubmitter = btn;
      });
      form.addEventListener('submit', e => {
        // An inline onsubmit="return confirm(...)" attribute runs before this
        // listener (registered at parse time); if the operator cancelled it,
        // the event is already marked prevented -- respect that and bail.
        if (e.defaultPrevented) return;
        e.preventDefault();
        const submitter = clickedSubmitter;
        clickedSubmitter = null;
        submitAjax(form, submitter);
      });
    });
  }
  bindForms();
})();
