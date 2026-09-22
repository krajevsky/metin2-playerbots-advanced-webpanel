(function(){
  var stage = document.getElementById('cc-scene');
  if (!stage) return;
  var classes = [
    {job:0, slug:'warrior',  label:'Wojownik'},
    {job:1, slug:'assassin', label:'Ninja'},
    {job:2, slug:'sura',     label:'Sura'},
    {job:3, slug:'shaman',   label:'Szaman'}
  ];
  var base = stage.dataset.base;
  var jobField = document.getElementById('cc-gm-job');
  var genderField = document.getElementById('cc-gm-gender');
  var empireField = document.getElementById('cc-empire');
  var classNameEl = document.getElementById('cc-class-name');
  var orbit = stage.querySelector('.cc-orbit');
  var nickInput = document.getElementById('cc-nick-input');
  var nickStatus = document.getElementById('cc-nick-status');
  var nextBtn = document.getElementById('cc-next-btn');
  var backBtn = document.getElementById('cc-back-btn');
  var step1Actions = document.getElementById('cc-step1-actions');
  var step2 = document.getElementById('cc-step2');
  var submitBtn = document.getElementById('cc-submit-btn');
  var accountModeField = document.getElementById('cc-account-mode');
  var accountSelect = document.getElementById('cc-account-select');
  var accountSearch = document.getElementById('cc-account-search');
  var existingBox = document.getElementById('cc-existing-account');
  var newBox = document.getElementById('cc-new-account');
  var empireWarning = document.getElementById('cc-empire-warning');
  var preselectAccountId = stage.dataset.preselectAccount || '';

  var selected = 0;
  var gender = 'male';
  var accountMode = 'existing';
  var lockedInStep2 = false;

  var slots = classes.map(function(c){
    var el = document.createElement('div');
    el.className = 'cc-slot';
    el.innerHTML = '<img alt="' + c.label + '"><div class="cc-slot-label">' + c.label + '</div>';
    orbit.appendChild(el);
    return el;
  });
  slots.forEach(function(el, i){
    el.addEventListener('click', function(){ if (!lockedInStep2) select(i); });
  });

  function genderSuffix(){ return gender === 'female' ? 'w' : 'm'; }
  function roleFor(i){
    var rel = (i - selected + classes.length) % classes.length;
    return ['front', 'right', 'back', 'left'][rel];
  }

  function render(){
    classes.forEach(function(c, i){
      var img = slots[i].querySelector('img');
      var state = !lockedInStep2 ? 'wait' : (i === selected ? 'selected' : 'not_selected');
      var src = base + c.slug + '_' + genderSuffix() + '/' + state + '.gif';
      if (img.getAttribute('src') !== src) img.src = src;
      slots[i].dataset.role = roleFor(i);
    });
    if (jobField) jobField.value = classes[selected].job;
    if (genderField) genderField.value = gender;
    if (classNameEl) classNameEl.textContent = classes[selected].label;
  }

  function select(i){
    selected = (i + classes.length) % classes.length;
    render();
  }

  var left = stage.querySelector('.cc-arrow.left');
  var right = stage.querySelector('.cc-arrow.right');
  if (left) left.addEventListener('click', function(){ if (!lockedInStep2) select(selected - 1); });
  if (right) right.addEventListener('click', function(){ if (!lockedInStep2) select(selected + 1); });

  document.querySelectorAll('.cc-gender-toggle .gender-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      if (lockedInStep2) return;
      gender = btn.dataset.gender;
      document.querySelectorAll('.cc-gender-toggle .gender-btn').forEach(function(b){ b.classList.toggle('active', b === btn); });
      render();
    });
  });

  document.querySelectorAll('.empire-flag-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      if (lockedInStep2) return;
      document.querySelectorAll('.empire-flag-btn').forEach(function(b){ b.classList.toggle('active', b === btn); });
      if (empireField) empireField.value = btn.dataset.empire;
    });
  });

  function setLocked(state){
    lockedInStep2 = state;
    stage.classList.toggle('locked', state);
    document.querySelectorAll('.cc-sidebar .empire-flag-btn, .cc-sidebar .cc-gender-toggle button').forEach(function(el){
      el.disabled = state;
    });
    nickInput.readOnly = state;
    render();
  }

  // -- step 1: name availability check, then move to step 2 --
  var nameCheckTimer = null;
  function checkName(cb){
    var name = nickInput.value.trim();
    if (!name) { nickStatus.textContent = ''; if (cb) cb(false); return; }
    fetch('/api/character-creator/name-status?name=' + encodeURIComponent(name))
      .then(function(r){ return r.json(); })
      .then(function(data){
        if (!data.ok || !data.valid) {
          nickStatus.textContent = data.reason || 'Nieprawidłowa nazwa.';
          nickStatus.style.color = '#ff8080';
          if (cb) cb(false);
        } else if (!data.available) {
          nickStatus.textContent = 'Ta nazwa jest już zajęta.';
          nickStatus.style.color = '#ff8080';
          if (cb) cb(false);
        } else {
          nickStatus.textContent = 'Nazwa wolna.';
          nickStatus.style.color = '#7be08a';
          if (cb) cb(true);
        }
      })
      .catch(function(){ nickStatus.textContent = ''; if (cb) cb(false); });
  }
  nickInput.addEventListener('input', function(){
    clearTimeout(nameCheckTimer);
    nameCheckTimer = setTimeout(function(){ checkName(); }, 400);
  });

  nextBtn.addEventListener('click', function(){
    checkName(function(available){
      if (!available) return;
      step1Actions.hidden = true;
      step2.hidden = false;
      setLocked(true);
      loadAccounts('');
    });
  });

  backBtn.addEventListener('click', function(){
    step2.hidden = true;
    step1Actions.hidden = false;
    setLocked(false);
  });

  // -- step 2: account mode + list --
  document.querySelectorAll('.cc-account-mode .mode-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      accountMode = btn.dataset.mode;
      accountModeField.value = accountMode;
      document.querySelectorAll('.cc-account-mode .mode-btn').forEach(function(b){ b.classList.toggle('active', b === btn); });
      existingBox.hidden = accountMode !== 'existing';
      newBox.hidden = accountMode !== 'new';
      empireWarning.hidden = true;
      submitBtn.disabled = false;
    });
  });

  var searchTimer = null;
  accountSearch.addEventListener('input', function(){
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function(){ loadAccounts(accountSearch.value.trim()); }, 300);
  });

  function loadAccounts(q){
    fetch('/api/character-creator/accounts?q=' + encodeURIComponent(q))
      .then(function(r){ return r.json(); })
      .then(function(data){
        if (!data.ok) return;
        accountSelect.innerHTML = '';
        data.accounts.forEach(function(a){
          var opt = document.createElement('option');
          opt.value = a.id;
          var status = a.empire_name ? (a.empire_name + ', ' + a.used_slots + '/4 postaci') : 'brak postaci jeszcze';
          opt.textContent = a.login + ' — ' + status;
          opt.dataset.empire = a.empire || '';
          opt.dataset.freeSlots = a.free_slots;
          accountSelect.appendChild(opt);
        });
        // Came here from an account's own page ("Stwórz nową postać") --
        // have that account already highlighted once, not on every re-search.
        if (preselectAccountId) {
          var match = Array.prototype.find.call(accountSelect.options, function(o){ return o.value === preselectAccountId; });
          if (match) accountSelect.value = preselectAccountId;
          preselectAccountId = '';
        }
        checkEmpireMatch();
      });
  }

  accountSelect.addEventListener('change', checkEmpireMatch);

  var empireNames = {'1':'Shinsoo','2':'Chunjo','3':'Jinno'};

  function checkEmpireMatch(){
    var opt = accountSelect.selectedOptions[0];
    if (!opt) { empireWarning.hidden = true; submitBtn.disabled = false; return; }
    var accEmpire = opt.dataset.empire;
    var freeSlots = parseInt(opt.dataset.freeSlots, 10);
    if (freeSlots <= 0) {
      empireWarning.hidden = false;
      empireWarning.className = 'flash error';
      empireWarning.textContent = 'To konto ma już 4 postacie — brak wolnego slotu.';
      submitBtn.disabled = true;
      return;
    }
    if (accEmpire) {
      // This account is already locked to a kingdom by an earlier character --
      // follow it automatically instead of forcing the admin to go back.
      if (String(accEmpire) !== String(empireField.value)) empireField.value = accEmpire;
      document.querySelectorAll('.empire-flag-btn').forEach(function(b){
        b.classList.toggle('active', b.dataset.empire === String(accEmpire));
      });
      empireWarning.hidden = false;
      empireWarning.className = 'flash';
      empireWarning.textContent = 'To konto ma już postać w królestwie ' + (empireNames[accEmpire] || '?') + ' — ustawiono automatycznie.';
      submitBtn.disabled = false;
    } else {
      empireWarning.hidden = true;
      submitBtn.disabled = false;
    }
  }

  render();
})();
