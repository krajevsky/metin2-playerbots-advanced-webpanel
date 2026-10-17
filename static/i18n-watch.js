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
  // An element marked translate="no" holds what players and bots wrote (the
  // live chat's lines and nicks): translations.py leaves it alone, and so
  // does this, whether it was in the page or is added inside one later.
  const KEEP = '[translate="no"]';
  function kept(node) {
    const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    return !!(element && element.closest(KEEP));
  }

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
    if (node.nodeType !== Node.ELEMENT_NODE || node.getAttribute('translate') === 'no') return;
    for (const attr of ATTRS) {
      const value = node.getAttribute && node.getAttribute(attr);
      if (value) {
        const translated = translate(value);
        if (translated !== value) node.setAttribute(attr, translated);
      }
    }
    // a textarea's placeholder is translated (above), never its content (Turkish patch)
    if (SKIP_TAGS.has(node.tagName)) return;
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
        mutation.addedNodes.forEach(node => { if (!kept(node)) walk(node); });
      } else if (mutation.type === 'characterData') {
        if (kept(mutation.target)) continue;
        const translated = translate(mutation.target.nodeValue);
        if (translated !== mutation.target.nodeValue) mutation.target.nodeValue = translated;
      } else if (mutation.type === 'attributes') {
        // Turkish patch: a script that rewrites a title/placeholder in place
        // (the live map's markers, a refreshed tooltip) is translated too.
        const element = mutation.target, attr = mutation.attributeName;
        if (kept(element)) continue;
        const value = element.getAttribute(attr);
        if (!value) continue;
        const translated = translate(value);
        if (translated !== value) element.setAttribute(attr, translated);
      }
    }
  }).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });

  // Turkish patch: a chart's own words (dataset names, category labels in
  // the legend, tooltips and axes) are drawn on its canvas, out of the
  // DOM's reach -- they are translated inside Chart.js, for the charts the
  // page drew already and, by a plugin, at every later update.
  function translateChart(chart) {
    const data = chart && chart.data;
    if (!data) return false;
    let changed = false;
    if (Array.isArray(data.labels)) {
      data.labels = data.labels.map(label => {
        if (typeof label !== 'string') return label;
        const translated = translate(label);
        if (translated !== label) changed = true;
        return translated;
      });
    }
    (data.datasets || []).forEach(dataset => {
      if (typeof dataset.label !== 'string') return;
      const translated = translate(dataset.label);
      if (translated !== dataset.label) { dataset.label = translated; changed = true; }
    });
    return changed;
  }
  if (window.Chart) {
    try { window.Chart.register({ id: 'm2-i18n', beforeUpdate: chart => { translateChart(chart); } }); } catch (_) {}
    try {
      Object.values(window.Chart.instances || {}).forEach(chart => { if (translateChart(chart)) chart.update('none'); });
    } catch (_) {}
  }

  // Turkish patch: the dialogs a script opens itself (a deletion's
  // confirmation, an error alert) never enter the DOM, so their message is
  // translated here with the same table.
  for (const name of ['alert', 'confirm', 'prompt']) {
    const original = window[name];
    if (typeof original !== 'function') continue;
    window[name] = function (message, ...rest) {
      return original.call(window, typeof message === 'string' ? translate(message) : message, ...rest);
    };
  }
})();
