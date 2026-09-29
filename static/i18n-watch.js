(() => {
  // Client-side half of the ui_language="en" panel translation. Only loaded
  // by base.html when English is selected. The server (translations.py,
  // app.py's after_request hook) already translates the initial HTML;
  // this covers anything dashboard-deferred.js / live-widget.js /
  // dashboard-charts.js / news-feed.js render into the DOM afterwards,
  // using the exact same EXACT + PATTERNS_RAW table (embedded below by
  // base.html as JSON), so a phrase only needs one English translation to
  // cover both paths.
  const dataNode = document.getElementById('i18n-data');
  if (!dataNode) return;
  let table;
  try { table = JSON.parse(dataNode.textContent); } catch { return; }
  const exact = table.exact || {};
  // 'g' so a pattern can fire more than once per string, matching Python's
  // re.subn (no count limit) on the server side.
  const patterns = (table.patterns || []).map(([source, replacement]) => [new RegExp(source, 'g'), replacement]);
  const ATTRS = ['title', 'alt', 'placeholder', 'aria-label'];
  const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'PRE']);

  function translate(text) {
    const trimmed = text.trim();
    if (!trimmed) return text;
    const lead = text.slice(0, text.indexOf(trimmed));
    const trail = text.slice(text.indexOf(trimmed) + trimmed.length);
    if (Object.prototype.hasOwnProperty.call(exact, trimmed)) return lead + exact[trimmed] + trail;
    // Cascades every pattern (not just the first hit) -- see translate_string's
    // docstring in translations.py for why: many dynamic strings are
    // composed from more than one translatable fragment.
    let result = trimmed, changed = false;
    for (const [re, replacement] of patterns) {
      const next = result.replace(re, replacement);
      if (next !== result) { result = next; changed = true; }
    }
    return changed ? lead + result + trail : text;
  }

  function walk(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      const translated = translate(node.nodeValue);
      if (translated !== node.nodeValue) node.nodeValue = translated;
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE || SKIP_TAGS.has(node.tagName)) return;
    for (const attr of ATTRS) {
      const value = node.getAttribute && node.getAttribute(attr);
      if (value) {
        const translated = translate(value);
        if (translated !== value) node.setAttribute(attr, translated);
      }
    }
    if (node.tagName === 'INPUT' && (node.type === 'submit' || node.type === 'button') && node.value) {
      const translated = translate(node.value);
      if (translated !== node.value) node.value = translated;
    }
    for (const child of Array.from(node.childNodes)) walk(child);
  }

  walk(document.body);
  new MutationObserver(mutations => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(walk);
      } else if (mutation.type === 'characterData') {
        const translated = translate(mutation.target.nodeValue);
        if (translated !== mutation.target.nodeValue) mutation.target.nodeValue = translated;
      }
    }
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
})();
