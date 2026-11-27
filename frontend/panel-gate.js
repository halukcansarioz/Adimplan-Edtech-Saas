// Panel sayfaları için giriş kontrolü (arayüz düzeyinde). <head> içinde, diğer
// betiklerden önce yüklenmelidir. app.html aynı kuralları kendi içinde uygular.
(function () {
  'use strict';
  var TIMEOUT = 30 * 60 * 1000, ACTIVE = 'ivme_last_active', ls = window.localStorage;

  function lastActive() { return Number(ls.getItem(ACTIVE)) || 0; }
  function expired() {
    return !ls.getItem('ivme_user') || (lastActive() > 0 && Date.now() - lastActive() >= TIMEOUT);
  }
  function leave() {
    if (expired()) {
      Object.keys(ls).filter(function (k) { return /^sb-.+-auth-token/.test(k); })
        .forEach(function (k) { ls.removeItem(k); });
      ['ivme_user', 'ivme_demo', ACTIVE].forEach(function (k) { ls.removeItem(k); });
    }
    sessionStorage.setItem('adimplan_next', location.pathname.split('/').pop());
    document.documentElement.style.display = 'none';
    location.replace('./login.html');
  }

  window.addEventListener('pageshow', function (e) { if (e.persisted) location.reload(); });
  if (expired()) { leave(); return; }

  // Demo oturumu gerçek verileri görmez ve değiştirmez (app.html ile aynı 'demo:' alanı).
  if (ls.getItem('ivme_demo') === 'true') {
    var shared = ['ivme_user', 'ivme_demo', ACTIVE, 'ivme_invite_only', 'adimplan_theme'];
    ['getItem', 'setItem', 'removeItem'].forEach(function (name) {
      var original = Storage.prototype[name];
      Storage.prototype[name] = function (key) {
        var args = Array.prototype.slice.call(arguments);
        if (this === window.localStorage && /^(adimplan_|ivme_|supabase_)/.test(String(key)) &&
            shared.indexOf(String(key)) === -1) {
          args[0] = 'demo:' + key;
        }
        return original.apply(this, args);
      };
    });
  }

  var left = false;
  function check() { if (!left && expired()) { left = true; leave(); } }
  function touch() { check(); if (!left) ls.setItem(ACTIVE, String(Date.now())); }
  ls.setItem(ACTIVE, String(Date.now()));
  ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'].forEach(function (evt) {
    document.addEventListener(evt, touch, { passive: true });
  });
  document.addEventListener('visibilitychange', check);
  setInterval(check, 15000);
})();
