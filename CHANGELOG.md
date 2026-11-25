# Değişiklik Günlüğü (Changelog)

Bu dosya **İvme Akademi — Adımplan EdTech SaaS** projesindeki önemli sürüm değişikliklerini içerir.

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
