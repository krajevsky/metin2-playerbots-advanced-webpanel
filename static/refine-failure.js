(() => {
  const LINES = [
    'Ulepszanie nie powiodło się.',
    'Co za debil ten panel zrobił..',
    'Znowu coś nie działa.',
    'Niestety ten panel jest bardzo złej jakości...',
    'KUR@!#!@#AAA',
  ];

  window.showRefineFailure = function showRefineFailure(notification) {
    const line = LINES[Math.floor(Math.random() * LINES.length)];
    const dialog = document.createElement('dialog');
    dialog.className = 'refine-failure-modal';
    dialog.innerHTML = `<div class="refine-failure-frame" role="document">
      <p class="refine-failure-line"></p>
      <small class="refine-failure-detail"></small>
      <button type="button">OK</button>
    </div>`;
    dialog.querySelector('.refine-failure-line').textContent = line;
    dialog.querySelector('.refine-failure-detail').textContent = notification.body || '';
    const close = () => { dialog.close(); dialog.remove(); };
    dialog.querySelector('button').addEventListener('click', close);
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
    document.body.appendChild(dialog);
    dialog.showModal();
    const sound = new Audio('/static/sounds/refine-failed.mp3');
    sound.volume = 0.72;
    sound.play().catch(() => {});
  };
})();
