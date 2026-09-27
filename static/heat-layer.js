(() => {
  // Port of Tieru's 7788 heatmap. The backend groups real game-log
  // coordinates into a 72x72 grid; the frontend only visualises those cells.
  function render(container, cells, peak, kind) {
    clear(container);
    if (!cells.length || !peak) return;
    const layer = document.createElement('div');
    layer.className = 'density-heat-layer';
    const rgb = kind === 'metins' ? '255,105,205' : kind === 'bosses' ? '255,166,58' : '255,72,58';
    layer.innerHTML = cells.map(cell => {
      const weight = Math.sqrt(cell.n / peak);
      const size = (11 + weight * 62).toFixed(0);
      const alpha = (.20 + weight * .55).toFixed(2);
      return `<i class="density-heat-dot" style="left:${cell.px}%;top:${cell.py}%;width:${size}px;height:${size}px;background:radial-gradient(circle,rgba(${rgb},${alpha}) 0%,rgba(${rgb},0) 70%)"></i>`;
    }).join('');
    container.appendChild(layer);
  }
  function clear(container) {
    container.querySelector(':scope > .density-heat-layer')?.remove();
  }
  window.SebanHeatmap = {render, clear};
})();
