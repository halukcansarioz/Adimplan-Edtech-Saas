(function () {
  'use strict';

  function showToast(msg, isError) {
    var existing = document.getElementById('adimplan-student-toast');
    if (existing) {
      existing.remove();
    }
    var toast = document.createElement('div');
    toast.id = 'adimplan-student-toast';
    toast.setAttribute('role', 'status');
    toast.style.cssText =
      'position:fixed;bottom:84px;right:18px;z-index:10001;padding:10px 14px;border-radius:10px;font-size:13px;font-weight:600;color:#fff;box-shadow:0 8px 24px rgba(0,0,0,0.22);background:' +
      (isError ? '#b91c1c' : '#0f766e') +
      ';max-width:320px;';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(function () {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 3600);
  }

  function makeBtn(label, bg) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = label;
    btn.style.cssText =
      'border:0;border-radius:8px;padding:7px 11px;font-size:12px;font-weight:600;cursor:pointer;color:#fff;background:' +
      bg +
      ';white-space:nowrap;';
    return btn;
  }

  function makeField(labelText, inputEl) {
    var wrap = document.createElement('label');
    wrap.style.cssText =
      'display:flex;flex-direction:column;gap:4px;font-size:12px;font-weight:600;color:#334155;';
    var span = document.createElement('span');
    span.textContent = labelText;
    wrap.appendChild(span);
    inputEl.style.cssText =
      'padding:8px 10px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;color:#0f172a;background:#fff;';
    wrap.appendChild(inputEl);
    return wrap;
  }

  function openQuestionModal() {
    var prev = document.getElementById('adimplan-question-modal');
    if (prev) {
      prev.remove();
    }

    var overlay = document.createElement('div');
    overlay.id = 'adimplan-question-modal';
    overlay.style.cssText =
      'position:fixed;inset:0;z-index:10002;background:rgba(15,23,42,0.55);display:flex;align-items:center;justify-content:center;padding:16px;';

    var card = document.createElement('div');
    card.style.cssText =
      'width:100%;max-width:380px;background:#fff;border-radius:14px;padding:18px;box-shadow:0 20px 45px rgba(0,0,0,0.28);display:flex;flex-direction:column;gap:12px;';

    var title = document.createElement('h3');
    title.textContent = 'Soru Kaydı (D/Y/B)';
    title.style.cssText = 'margin:0;font-size:16px;font-weight:700;color:#0f172a;';
    card.appendChild(title);

    var subjectInput = document.createElement('input');
    subjectInput.type = 'text';
    subjectInput.value = 'Matematik';
    subjectInput.placeholder = 'Örn: Matematik';
    card.appendChild(makeField('Ders', subjectInput));

    var grid = document.createElement('div');
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(3,1fr);gap:8px;';

    var correctInput = document.createElement('input');
    correctInput.type = 'number';
    correctInput.min = '0';
    correctInput.value = '0';

    var wrongInput = document.createElement('input');
    wrongInput.type = 'number';
    wrongInput.min = '0';
    wrongInput.value = '0';

    var blankInput = document.createElement('input');
    blankInput.type = 'number';
    blankInput.min = '0';
    blankInput.value = '0';

    grid.appendChild(makeField('Doğru (D)', correctInput));
    grid.appendChild(makeField('Yanlış (Y)', wrongInput));
    grid.appendChild(makeField('Boş (B)', blankInput));
    card.appendChild(grid);

    var netDisplay = document.createElement('div');
    netDisplay.style.cssText =
      'padding:8px 12px;border-radius:8px;background:#f1f5f9;color:#0f172a;font-size:13px;font-weight:700;';
    netDisplay.textContent = 'Net: 0.00';
    card.appendChild(netDisplay);

    function updateNet() {
      var d = Math.max(0, Number(correctInput.value) || 0);
      var y = Math.max(0, Number(wrongInput.value) || 0);
      var net = d - y * 0.25;
      netDisplay.textContent = 'Net: ' + net.toFixed(2);
    }

    correctInput.addEventListener('input', updateNet);
    wrongInput.addEventListener('input', updateNet);

    var actions = document.createElement('div');
    actions.style.cssText = 'display:flex;justify-content:flex-end;gap:8px;margin-top:4px;';

    var cancelBtn = makeBtn('Vazgeç', '#64748b');
    cancelBtn.addEventListener('click', function () {
      overlay.remove();
    });

    var saveBtn = makeBtn('Kaydet', '#2563eb');
    saveBtn.addEventListener('click', function () {
      var sync = window.AdimplanSync;
      if (!sync || typeof sync.logQuestions !== 'function') {
        showToast('Senkronizasyon modülü hazır değil.', true);
        return;
      }
      var subject = (subjectInput.value || '').trim() || 'Genel';
      var correctCount = Math.max(0, Math.floor(Number(correctInput.value) || 0));
      var wrongCount = Math.max(0, Math.floor(Number(wrongInput.value) || 0));
      var blankCount = Math.max(0, Math.floor(Number(blankInput.value) || 0));
      var net = correctCount - wrongCount * 0.25;

      saveBtn.disabled = true;
      Promise.resolve(
        sync.logQuestions({
          subject: subject,
          correct_count: correctCount,
          wrong_count: wrongCount,
          blank_count: blankCount,
          logged_at: new Date().toISOString(),
        })
      )
        .then(function () {
          overlay.remove();
          showToast(subject + ' soru kaydı alındı (Net: ' + net.toFixed(2) + ').');
        })
        .catch(function (err) {
          saveBtn.disabled = false;
          showToast((err && err.message) || 'Soru kaydı başarısız.', true);
        });
    });

    actions.appendChild(cancelBtn);
    actions.appendChild(saveBtn);
    card.appendChild(actions);
    overlay.appendChild(card);

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) {
        overlay.remove();
      }
    });

    document.body.appendChild(overlay);
  }

  function mountStudentToolbar() {
    if (document.getElementById('adimplan-student-live-bar')) {
      return;
    }

    var bar = document.createElement('div');
    bar.id = 'adimplan-student-live-bar';
    bar.style.cssText =
      'position:fixed;bottom:16px;right:16px;z-index:9999;display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:10px 12px;border-radius:14px;background:rgba(15,23,42,0.92);backdrop-filter:blur(8px);box-shadow:0 12px 32px rgba(0,0,0,0.28);max-width:calc(100vw - 32px);';

    var label = document.createElement('span');
    label.textContent = 'Öğrenci Hızlı Araçları';
    label.style.cssText = 'color:#e2e8f0;font-size:12px;font-weight:700;margin-right:4px;';
    bar.appendChild(label);

    var btnPomodoro = makeBtn('+25 dk Pomodoro Kaydet', '#0d9488');
    btnPomodoro.addEventListener('click', function () {
      var sync = window.AdimplanSync;
      if (!sync || typeof sync.logPomodoro !== 'function') {
        showToast('Senkronizasyon modülü hazır değil.', true);
        return;
      }
      btnPomodoro.disabled = true;
      Promise.resolve(
        sync.logPomodoro({
          subject: 'Genel Çalışma',
          duration_minutes: 25,
          completed_at: new Date().toISOString(),
        })
      )
        .then(function () {
          showToast('25 dk Pomodoro oturumu kaydedildi.');
        })
        .catch(function (err) {
          showToast((err && err.message) || 'Pomodoro kaydedilemedi.', true);
        })
        .finally(function () {
          btnPomodoro.disabled = false;
        });
    });

    var btnQuestion = makeBtn('Soru Kaydı (D/Y/B)', '#2563eb');
    btnQuestion.addEventListener('click', openQuestionModal);

    var btnSync = makeBtn('Senkronize Et', '#475569');
    btnSync.addEventListener('click', function () {
      var sync = window.AdimplanSync;
      if (!sync || typeof sync.flushQueue !== 'function') {
        showToast('Senkronizasyon modülü hazır değil.', true);
        return;
      }
      btnSync.disabled = true;
      Promise.resolve(sync.flushQueue())
        .then(function (res) {
          var flushed = res && typeof res.flushed === 'number' ? res.flushed : 0;
          var remaining = res && typeof res.remaining === 'number' ? res.remaining : 0;
          showToast('Senkronizasyon tamam: ' + flushed + ' gönderildi, ' + remaining + ' bekliyor.');
        })
        .catch(function (err) {
          showToast((err && err.message) || 'Senkronizasyon başarısız.', true);
        })
        .finally(function () {
          btnSync.disabled = false;
        });
    });

    bar.appendChild(btnPomodoro);
    bar.appendChild(btnQuestion);
    bar.appendChild(btnSync);

    // Çubuk içeriğin üstünde durduğu için küçültülebilir.
    var btnToggle = makeBtn('Gizle', 'transparent');
    btnToggle.id = 'adimplan-student-live-toggle';
    btnToggle.setAttribute('aria-expanded', 'true');
    var tools = [label, btnPomodoro, btnQuestion, btnSync];
    var displays = tools.map(function (el) { return el.style.display; });
    btnToggle.addEventListener('click', function () {
      var open = btnToggle.getAttribute('aria-expanded') !== 'true';
      tools.forEach(function (el, i) { el.style.display = open ? displays[i] : 'none'; });
      btnToggle.setAttribute('aria-expanded', String(open));
      btnToggle.textContent = open ? 'Gizle' : 'Hızlı Araçlar';
    });
    bar.appendChild(btnToggle);
    document.body.appendChild(bar);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountStudentToolbar);
  } else {
    mountStudentToolbar();
  }
})();
