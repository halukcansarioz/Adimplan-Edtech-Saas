(function () {
  "use strict";

  function initCoachLiveHooks() {
    if (!document.body || document.getElementById("adimplan-live-api-bar")) {
      return;
    }

    var bar = document.createElement("aside");
    bar.id = "adimplan-live-api-bar";
    bar.setAttribute("aria-label", "Canlı API Araçları");
    bar.style.position = "fixed";
    bar.style.right = "16px";
    bar.style.bottom = "16px";
    bar.style.zIndex = "9990";
    bar.style.display = "flex";
    bar.style.flexDirection = "column";
    bar.style.gap = "8px";
    bar.style.padding = "12px";
    bar.style.borderRadius = "12px";
    bar.style.background = "#0f172a";
    bar.style.color = "#f8fafc";
    bar.style.boxShadow = "0 10px 25px rgba(15, 23, 42, 0.25)";
    bar.style.fontFamily = "system-ui, -apple-system, sans-serif";
    bar.style.fontSize = "13px";
    bar.style.maxWidth = "280px";

    var title = document.createElement("div");
    title.textContent = "Canlı API Araçları";
    title.style.fontWeight = "600";
    title.style.fontSize = "12px";
    title.style.letterSpacing = "0.02em";
    title.style.color = "#94a3b8";
    bar.appendChild(title);

    var btnRow = document.createElement("div");
    btnRow.style.display = "flex";
    btnRow.style.flexWrap = "wrap";
    btnRow.style.gap = "6px";
    bar.appendChild(btnRow);

    var statusEl = document.createElement("div");
    statusEl.setAttribute("role", "status");
    statusEl.style.fontSize = "12px";
    statusEl.style.color = "#cbd5e1";
    statusEl.style.display = "none";
    bar.appendChild(statusEl);

    function setStatus(msg, isError) {
      statusEl.textContent = msg;
      statusEl.style.color = isError ? "#fca5a5" : "#86efac";
      statusEl.style.display = msg ? "block" : "none";
    }

    function createButton(label, bg) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = label;
      btn.style.border = "none";
      btn.style.borderRadius = "8px";
      btn.style.padding = "6px 10px";
      btn.style.fontSize = "12px";
      btn.style.fontWeight = "600";
      btn.style.cursor = "pointer";
      btn.style.background = bg;
      btn.style.color = "#ffffff";
      return btn;
    }

    function openModal(headingText, bodyBuilder) {
      var existing = document.getElementById("adimplan-live-api-modal");
      if (existing && existing.parentNode) {
        existing.parentNode.removeChild(existing);
      }

      var overlay = document.createElement("div");
      overlay.id = "adimplan-live-api-modal";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");
      overlay.style.position = "fixed";
      overlay.style.inset = "0";
      overlay.style.zIndex = "10000";
      overlay.style.background = "rgba(15, 23, 42, 0.6)";
      overlay.style.display = "flex";
      overlay.style.alignItems = "center";
      overlay.style.justifyContent = "center";
      overlay.style.padding = "16px";

      var card = document.createElement("div");
      card.style.background = "#ffffff";
      card.style.color = "#0f172a";
      card.style.borderRadius = "14px";
      card.style.maxWidth = "520px";
      card.style.width = "100%";
      card.style.maxHeight = "80vh";
      card.style.overflowY = "auto";
      card.style.padding = "20px";
      card.style.boxShadow = "0 20px 40px rgba(15, 23, 42, 0.3)";
      card.style.fontFamily = "system-ui, -apple-system, sans-serif";

      var header = document.createElement("div");
      header.style.display = "flex";
      header.style.alignItems = "center";
      header.style.justifyContent = "space-between";
      header.style.marginBottom = "12px";

      var h3 = document.createElement("h3");
      h3.textContent = headingText;
      h3.style.margin = "0";
      h3.style.fontSize = "16px";
      h3.style.fontWeight = "700";

      var closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.textContent = "Kapat";
      closeBtn.style.border = "1px solid #cbd5e1";
      closeBtn.style.borderRadius = "8px";
      closeBtn.style.background = "#f8fafc";
      closeBtn.style.color = "#0f172a";
      closeBtn.style.padding = "4px 10px";
      closeBtn.style.cursor = "pointer";
      closeBtn.addEventListener("click", function () {
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      });

      header.appendChild(h3);
      header.appendChild(closeBtn);
      card.appendChild(header);

      var content = document.createElement("div");
      content.style.fontSize = "14px";
      content.style.lineHeight = "1.5";
      bodyBuilder(content);
      card.appendChild(content);

      overlay.addEventListener("click", function (e) {
        if (e.target === overlay && overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      });

      overlay.appendChild(card);
      document.body.appendChild(overlay);
    }

    var aiBtn = createButton("AI Plan Öner", "#2563eb");
    aiBtn.addEventListener("click", function () {
      var api = window.AdimplanAPI;
      if (!api || typeof api.suggestPlan !== "function") {
        setStatus("AdimplanAPI.suggestPlan kullanılamıyor.", true);
        return;
      }
      setStatus("AI plan önerisi alınıyor...", false);
      Promise.resolve(api.suggestPlan({ subject: "Matematik", daily_minutes: 60 }))
        .then(function (res) {
          setStatus("AI plan önerisi hazır.", false);
          openModal("AI Plan Önerisi", function (container) {
            var meta = document.createElement("p");
            meta.style.margin = "0 0 10px 0";
            meta.style.color = "#475569";
            meta.textContent = res && res.fallback
              ? "Kaynak: Yerel yedek öneri"
              : "Kaynak: Canlı AI API";
            container.appendChild(meta);

            var list = document.createElement("ul");
            list.style.margin = "0";
            list.style.paddingLeft = "18px";
            var items = (res && Array.isArray(res.plan)) ? res.plan : [];
            if (items.length === 0) {
              var empty = document.createElement("li");
              empty.textContent = "Plan öğesi bulunamadı.";
              list.appendChild(empty);
            } else {
              items.forEach(function (item) {
                var li = document.createElement("li");
                li.style.marginBottom = "6px";
                var day = item.day ? String(item.day) : "Gün";
                var subj = item.subject ? String(item.subject) : "";
                var task = item.task ? String(item.task) : "";
                var mins = item.minutes ? String(item.minutes) + " dk" : "";
                li.textContent = day + " — " + subj + ": " + task + (mins ? " (" + mins + ")" : "");
                list.appendChild(li);
              });
            }
            container.appendChild(list);
          });
        })
        .catch(function (err) {
          setStatus("AI plan hatası: " + (err && err.message ? err.message : "Bilinmeyen hata"), true);
        });
    });

    var reportBtn = createButton("Veli Raporu Üret", "#7c3aed");
    reportBtn.addEventListener("click", function () {
      var api = window.AdimplanAPI;
      if (!api || typeof api.getWeeklyParentReport !== "function") {
        setStatus("AdimplanAPI.getWeeklyParentReport kullanılamıyor.", true);
        return;
      }
      setStatus("Pazar 15:00 veli raporu hazırlanıyor...", false);
      Promise.resolve(api.getWeeklyParentReport({ total_questions: 120, total_pomodoro_minutes: 300 }))
        .then(function (res) {
          setStatus("Veli raporu hazır.", false);
          openModal("Pazar 15:00 Veli Raporu Özeti", function (container) {
            var scheduleNote = document.createElement("p");
            scheduleNote.style.margin = "0 0 8px 0";
            scheduleNote.style.fontWeight = "600";
            scheduleNote.textContent = "Gönderim Zamanı: Pazar 15:00";
            container.appendChild(scheduleNote);

            var stats = document.createElement("p");
            stats.style.margin = "0 0 8px 0";
            stats.style.color = "#475569";
            var week = res && res.week_start ? String(res.week_start) : "-";
            var qCount = res && res.total_questions !== undefined ? String(res.total_questions) : "0";
            var pMins = res && res.total_pomodoro_minutes !== undefined ? String(res.total_pomodoro_minutes) : "0";
            stats.textContent = "Hafta: " + week + " | Soru: " + qCount + " | Pomodoro: " + pMins + " dk";
            container.appendChild(stats);

            var summary = document.createElement("p");
            summary.style.margin = "0";
            summary.textContent = res && res.summary ? String(res.summary) : "Özet bilgisi mevcut değil.";
            container.appendChild(summary);

          var params = new URLSearchParams();
          params.set("student", res && res.student_name ? String(res.student_name) : "Öğrenci");
          params.set("week", week);
          params.set("done", qCount);
          params.set("total", qCount);
          params.set("pomodoro", pMins);
          params.set("net", res && res.net_score !== undefined ? String(res.net_score) : "0");
          params.set("note", summary.textContent);

          var reportLink = document.createElement("a");
          reportLink.href = "./parent-report.html?" + params.toString();
          reportLink.target = "_blank";
          reportLink.rel = "noopener noreferrer";
          reportLink.textContent = "Paylaşılabilir Raporu Aç";
          reportLink.style.display = "inline-block";
          reportLink.style.marginTop = "12px";
          reportLink.style.padding = "8px 12px";
          reportLink.style.borderRadius = "8px";
          reportLink.style.background = "#7c3aed";
          reportLink.style.color = "#ffffff";
          reportLink.style.textDecoration = "none";
          reportLink.style.fontWeight = "600";
          container.appendChild(reportLink);
          });
        })
        .catch(function (err) {
          setStatus("Veli raporu hatası: " + (err && err.message ? err.message : "Bilinmeyen hata"), true);
        });
    });

    var syncBtn = createButton("Senkronize Et", "#059669");
    syncBtn.addEventListener("click", function () {
      var sync = window.AdimplanSync;
      if (!sync || typeof sync.flushQueue !== "function") {
        setStatus("AdimplanSync.flushQueue kullanılamıyor.", true);
        return;
      }
      setStatus("Senkronizasyon başlatılıyor...", false);
      Promise.resolve(sync.flushQueue())
        .then(function (res) {
          var flushed = res && typeof res.flushed === "number" ? res.flushed : 0;
          var remaining = res && typeof res.remaining === "number" ? res.remaining : 0;
          setStatus("Senkronize edildi: " + flushed + " gönderildi, " + remaining + " bekliyor.", false);
        })
        .catch(function (err) {
          setStatus("Senkronizasyon hatası: " + (err && err.message ? err.message : "Bilinmeyen hata"), true);
        });
    });

    btnRow.appendChild(aiBtn);
    btnRow.appendChild(reportBtn);
    btnRow.appendChild(syncBtn);
    document.body.appendChild(bar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCoachLiveHooks);
  } else {
    initCoachLiveHooks();
  }
})();
