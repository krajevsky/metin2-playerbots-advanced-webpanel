// Opt-in per page: <body data-ajax-forms> (set by that page's own inline
// script, since base.html owns the <body> tag). Submits every <form> inside
// <main> over fetch instead of a normal navigation, swaps <main> with the
// freshly-rendered response (so every dynamic value on the page -- restart
// progress, updater state, checkboxes -- reflects the real new state exactly
// like a full reload would, just without the visible reload/flash-modal),
// and shows the same flash message(s) as a dismiss-on-click toast instead of
// the blocking <dialog> modal. Operator's ask, 2026-09-22: buttons that
// change something shouldn't refresh the whole page.
//
// IMPORTANT for any page's own inline <script data-page-script> inside
// <main>: wrap its body in an IIFE, e.g. `(() => { ... })();` -- innerHTML
// swaps don't execute scripts, so runScripts() below re-creates and
// re-executes them, but a plain top-level `const`/`let` collides with the
// still-alive binding from the *previous* execution ("Identifier has
// already been declared") the moment a form is submitted a second time.
// An IIFE gives every re-run its own throwaway scope. Confirmed live this
// crashes silently (pageerror, not a console.error) if skipped.
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

  // The flash dialog's own inline "showModal()" script (base.html) has to go
  // together with the dialog element -- left behind alone it throws (calls
  // .showModal() on a now-missing #flash-modal) the moment it re-executes.
  function stripFlashModal(main) {
    const dialog = main.querySelector('#flash-modal');
    if (dialog) dialog.remove();
    main.querySelectorAll('script').forEach(s => {
      if (s.textContent.includes('flash-modal')) s.remove();
    });
  }

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
    const method = (form.getAttribute('method') || 'GET').toUpperCase();
    let url = form.getAttribute('action') || (window.location.pathname + window.location.search);
    const formData = new FormData(form, submitter);
    const opts = { method, credentials: 'same-origin' };
    if (method === 'GET' || method === 'HEAD') {
      // fetch() forbids a body on GET/HEAD -- fold the fields into the query
      // string instead, same as a plain <form method=get> submission would.
      const params = new URLSearchParams();
      for (const [k, v] of formData.entries()) params.append(k, v);
      const qs = params.toString();
      url = url.split('?')[0] + (qs ? '?' + qs : '');
    } else {
      opts.body = formData;
    }
    try {
      const res = await fetch(url, opts);
      const resUrl = new URL(res.url, window.location.origin);
      if (resUrl.pathname !== window.location.pathname) {
        // The server sent us somewhere genuinely different (e.g. deleting a
        // character redirects to the player list, not back to the now-gone
        // profile) -- an in-place swap would leave the address bar lying
        // about what's on screen. A real navigation is the only honest move.
        window.location.href = res.url;
        return;
      }
      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const flashes = extractFlashes(doc);
      const newMain = doc.querySelector('main');
      const main = document.querySelector('main');
      if (newMain && main) {
        stripFlashModal(newMain);
        main.innerHTML = newMain.innerHTML;
        runScripts(main);
        bindForms();
      }
      if (resUrl.search !== window.location.search) {
        // Same page, new query string (a filter/search form) -- keep the
        // address bar accurate without a real reload, and let Back undo it.
        history.pushState(null, '', res.url);
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
