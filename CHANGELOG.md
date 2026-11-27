# Değişiklik Günlüğü (Changelog)

Bu dosya **İvme Akademi — Adımplan EdTech SaaS** projesindeki önemli sürüm değişikliklerini içerir.
## [v1.6.0]
### Eklenenler ve İyileştirmeler
- **Yeni Sayfalar ve PWA Önbellekleme:** `program.html`, `student.html`, `coach-panel.html` ve `pricing.html` sayfaları eklendi; `index.html` navigasyon bağlantıları güncellendi ve `frontend/sw.js` önbellek listesine eklendi.
- **Playwright E2E Testleri:** Yeni sayfalar ve kullanıcı akışları için yeni Playwright E2E testi eklendi.
- **Kimlik Doğrulama ve Güvenlik İyileştirmeleri:** Kimlik doğrulama akışları geliştirildi; CodeQL statik analiz ve Dependabot bağımlılık güvenliği iyileştirmeleri uygulandı.
## [v1.5.0]

### Eklenenler ve İyileştirmeler
- **Kimlik Doğrulama ve Rol Bazlı Yetkilendirme (PR #2):** Gerçek giriş doğrulaması, rol bazlı yetki kontrolleri ve `005_role_based_access.sql` veritabanı migrasyonu eklendi.
- **Bağımlılık Sabitleme, Redis ve CI/E2E Güncellemeleri (PR #3):** Üretim bağımlılıkları sabitlendi ve geliştirme bağımlılıkları `requirements-dev.txt` dosyasına ayrıldı; opsiyonel Redis tabanlı rate-limit ve önbellek desteği eklendi; Playwright E2E testleri, CI Node 24 güncellemesi ve `README.md` dokümantasyon güncellemesi yapıldı.
- **Docker Güvenlik Sertleştirmesi:** `backend/Dockerfile` dosyasına non-root `appuser` kullanıcısı (`USER appuser`) ve `/health` uç noktasını doğrulayan Python tabanlı `HEALTHCHECK` yönergesi eklendi.

## [v1.4.0]

### Eklenenler
- **Günler Arası Sürükle-Bırak Haftalık Takvim:** `frontend/app.html` (`#tab-0`) üzerindeki 7 günlük `.week-grid` tablosunda her gün sütunu sürükle-bırak hedefi (`ondragover`, `ondrop`) haline getirildi; görev kartları sürüklenebilir (`draggable="true"`) ve karta tıklanarak tamamlandı işaretlenebilir yapıldı, gün değişiklikleri anında `localStorage`'a kaydedilir.
- **Playwright E2E Kapsamı:** `tests/test_frontend_e2e.py` dosyasına `test_weekly_grid_view_toggle` testi eklenerek `#btnViewGrid` ile 7 sütunlu tablonun görünürlüğü ve `390px` mobil ekranda yatay taşma olmadığı doğrulandı (17/17 E2E).

## [v1.3.0]

### Eklenenler
- **7 Günlük Haftalık Tablo Görünümü:** `frontend/app.html` içinde `#btnViewGrid` / `#btnViewList` geçişiyle Pazartesi'den Pazar'a 7 sütunlu `.week-grid` haftalık program tablosu eklendi.
- **Web Audio Pomodoro Zil Sesi:** Pomodoro zamanlayıcısı tamamlandığında Web Audio API tabanlı bildirim zil sesi eklendi.

## [v1.2.0]

### Eklenenler
- **Kurumsal Marka & Favicon:** `frontend/favicon.svg` (İvme Akademi indigo `#4f46e5` → `#6366f1` rozet ve beyaz `İA` logosu) oluşturuldu; `index.html`, `login.html`, `app.html` ve `admin.html` sayfalarına eklendi.
- **Güvenlik ve Şeffaflık Dokümantasyonu:** `SECURITY.md` (KVKK bildirim e-postası, PostgreSQL RLS izolasyonu, rate limiting, 30 dk oturum kilidi, güvenlik başlıkları) ve `CHANGELOG.md` eklendi.
- **Vercel & Güvenlik Başlıkları:** `vercel.json` üzerinde `cleanUrls` ve HTTP güvenlik başlıkları yapılandırıldı.
- **Uçtan Uca Testler (E2E):** GitHub Actions CI iş akışına 16/16 Playwright senaryosunu çalıştıran `frontend-e2e` işi eklendi.

## [v1.1.0]

### Eklenenler
- **Çok-Kiracılı (Multi-Tenant) & RLS Altyapısı:** Supabase/PostgreSQL üzerinde kiracı izolasyonu ve veritabanı migrasyonları (`daily_mood_logs` dahil) tamamlandı.
- **Faturalandırma ve Veli Bildirimleri:** `/api/billing/quote` ve `/api/notify/parent-email` uç noktaları ile kapsamlı backend testleri eklendi.
- **Arayüz İyileştirmeleri:** `login.html`, `app.html` ve `admin.html` için tipografi ve yönetim paneli modernizasyonu yapıldı.

## [v1.0.0]

### Eklenenler
- **İlk Sürüm (MVP):** FastAPI tabanlı analitik ve koçluk backend servisi, öğrenci takip arayüzü, davet/kayıt akışı ve temel CI (`test`) iş akışı yayına alındı.
