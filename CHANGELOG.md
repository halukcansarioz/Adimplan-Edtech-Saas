# Değişiklik Günlüğü (Changelog)

Bu dosya **İvme Akademi — Adımplan EdTech SaaS** projesindeki önemli sürüm değişikliklerini içerir.

## [v2.2.1]

### Düzeltmeler
- **Öğrenci Paneli Yerleşimi:** Dosyanın sonuna kaymış `<main>` etiketi yerine alındı; içerik artık ana alanda. Hızlı araç çubuğu küçültülebiliyor ve sayfa sonunda içeriği kapatmıyor. Service worker önbelleği `adimplan-pwa-v26` oldu.

## [v2.2.0]

### Eklenenler
- **Google ile Giriş:** Giriş sayfasına "Google ile devam et" düğmesi eklendi. İlk girişte rol seçimi ve KVKK onayı zorunludur. Düğme yalnızca Supabase'de Google sağlayıcısı açıkken görünür. Kurulum: `supabase/GOOGLE_LOGIN_SETUP.md`. Service worker önbelleği `adimplan-pwa-v25` oldu.

## [v2.1.1]

### Düzeltmeler
- **Veli E-postası:** Resend isteğine `User-Agent` başlığı eklendi (başlıksız istekler 403 / 1010 ile reddediliyor). Boş `RESEND_FROM_EMAIL` artık varsayılan göndericiye düşüyor.
- **Şifre Sıfırlama:** Giriş sayfasındaki ikinci (`prompt`) sıfırlama akışı kaldırıldı; `login.html` ve `auth-callback.js` tek Supabase istemcisi kullanıyor.
- **E-posta Kurulumu:** `supabase/EMAIL_SETUP.md` eklendi (yönlendirme adresleri ve özel SMTP). Service worker önbelleği `adimplan-pwa-v24` oldu.

## [v2.1.0]

### Eklenenler ve İyileştirmeler
- **Animasyonlar ve SVG İllüstrasyonlar (PR #45):** Ana sayfa ve ürün bölümleri için akıcı animasyonlar ve özel SVG illüstrasyonları eklendi.
- **SSS Bölümü (PR #46):** Sıkça Sorulan Sorular bölümü 12 kapsamlı soru-cevap ile güncellendi.
- **3B Perspektifli Katmanlı Görsel Vitrinler (PR #47):** Ürün arayüzlerini öne çıkaran 3B perspektifli katmanlı görsel vitrinler eklendi.
- **SEO, Open Graph ve Site Haritası:** `frontend/index.html` için Türkçe SEO meta açıklaması, canonical bağlantı, Open Graph / Twitter Card etiketleri eklendi; `frontend/sitemap.xml` tüm v2 sayfaları ve `2026-11-27` tarihiyle güncellendi.

## [v2.0.0]

### Eklenenler ve İyileştirmeler
- **Etkileşimli Optik Okuyucu:** `frontend/optical-reader.html` ile etkileşimli optik baloncuk ızgarası, CSV toplu içe/dışa aktarım, otomatik D/Y/B + net analizi ve veli raporu kısayolu eklendi.
- **PWA Güncellemesi:** Service worker önbellek sürümü `adimplan-pwa-v23` olarak güncellendi.
- **Playwright E2E Testleri:** `test_optical_reader_loads_and_scores` E2E testi eklendi.
## [v1.9.0]

### Eklenenler ve İyileştirmeler
- **Paylaşılabilir Haftalık Veli Raporu:** `parent-report.html` ile URL parametreleri üzerinden paylaşılabilir haftalık veli raporu sayfası eklendi.
- **Koç Paneli Tek Tıkla Rapor Bağlantısı:** `frontend/coach-live-hooks.js` içindeki **Veli Raporu Üret** modalına `URLSearchParams` ile oluşturulan **Paylaşılabilir Raporu Aç** bağlantısı eklendi.
- **PWA Güncellemesi:** Service worker önbellek sürümü `adimplan-pwa-v22` olarak güncellendi.
- **Playwright E2E Testleri:** `parent-report.html` ve koç modalı rapor bağlantısı için yeni E2E testleri eklendi.
## [v1.8.1]

### Eklenenler ve İyileştirmeler
- **E-posta Doğrulama ve Auth Yönlendirme:** `emailRedirectTo`, PKCE (`code`) ve OTP (`token_hash`) doğrulama akışları eklendi.
- **Şifre Sıfırlama Modalı:** `auth-callback.js` ile sayfa içi şifre sıfırlama modalı ve hata/bilgi uyarı banner'ı desteği eklendi.
- **Vercel Auth Rewrite Kuralları:** `vercel.json` yapılandırmasına auth callback yönlendirme/rewrite kuralları eklendi.
- **PWA Güncellemesi:** Service worker önbellek sürümü `adimplan-pwa-v21` olarak güncellendi.
- **Playwright E2E Testleri:** `tests/test_frontend_e2e.py` dosyasına `auth-callback` PKCE yönlendirme ve hata uyarısı E2E testleri eklendi.

## [v1.8.0]

### Eklenenler ve İyileştirmeler
- **Canlı Senkronizasyon ve Hook'lar:** `supabase-sync.js`, `coach-live-hooks.js` ve `student-live-hooks.js` entegrasyonları eklendi.
- **PWA Güncellemesi:** Service worker önbellek sürümü `adimplan-pwa-v20` olarak güncellendi.
- **Yeni Okuma ve Yetenek Uç Noktaları:** Yeni okuma (API reads) ve capabilities uç noktaları eklendi.

## [v1.7.0]

### Eklenenler ve İyileştirmeler
- **Yeni Ön Panel ve Rotalar:** Yeni ön panel arayüzü ve `v17_routes.py` API rotaları eklendi.
- **Veritabanı Migrasyonu:** `006_full_panels_rls.sql` tam panel RLS veritabanı migrasyonu eklendi.
- **Docker Compose Kurulumu:** Yerel geliştirme ve çalıştırma için `docker-compose.yml` yapılandırması eklendi.

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
