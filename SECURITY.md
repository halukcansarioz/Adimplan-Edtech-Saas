# Güvenlik Politikası (Security Policy)

**İvme Akademi — Adımplan EdTech SaaS**, öğrenci verilerinin gizliliğini, KVKK uyumunu ve çok-kiracılı (multi-tenant) veri izolasyonunu en üst düzeyde tutmayı hedefler.

## 1. Güvenlik Açığı Bildirimi

Bir güvenlik açığı veya veri gizliliği ihlali tespit ederseniz, lütfen herkese açık bir GitHub Issue açmadan önce doğrudan güvenlik ekibimizle iletişime geçin:

- **E-posta:** `kvkk@ivmeakademi.com`
- **Yanıt Süresi:** Bildirimler en geç **48 saat** içinde değerlendirilir ve geri dönüş sağlanır.
- **Kapsam:** Kimlik doğrulama, yetkilendirme (RLS), veri sızıntısı, XSS/CSRF, API hız sınırı aşımı ve altyapı yapılandırmaları.

## 2. Mimari Güvenlik Katmanları

### Çok-Kiracılı İzolasyon (PostgreSQL RLS)
- Tüm kiracı (kurum/koç/öğrenci) tablolarında **PostgreSQL Row-Level Security (RLS)** aktif olarak uygulanır.
- Her istek, oturum bağlamındaki (`auth.uid()` / `tenant_id`) kimlik ve kiracı politikalarına göre veritabanı seviyesinde filtrelenir; bir kurum veya kullanıcı başka bir kiracının verisine erişemez.

### Hız Sınırlama (Rate Limiting)
- Kimlik doğrulama, davet/link üretimi, bildirim (`/api/notify/*`) ve faturalandırma (`/api/billing/*`) uç noktaları kötüye kullanım ve kaba kuvvet (brute-force) saldırılarına karşı **rate limiting** politikalarıyla korunur.

### Oturum Yönetimi ve 30 Dakika Oturum Kilidi
- Kullanıcı güvenliği için hareketsizlik durumunda **30 dakikalık otomatik oturum kilidi** uygulanır.
- Süre dolduğunda aktif oturum kilitlenir/sonlandırılır ve hassas işlemlere devam etmeden önce yeniden kimlik doğrulama istenir.

### HTTP Güvenlik Başlıkları (Security Headers)
- Statik barındırma (`vercel.json`) ve API katmanında modern tarayıcı güvenlik başlıkları uygulanır:
  - `X-Content-Type-Options: nosniff` (MIME type sniffing koruması)
  - `X-Frame-Options: DENY` / `SAMEORIGIN` (Clickjacking koruması)
  - `Referrer-Policy: strict-origin-when-cross-origin` (Yönlendiren bilgisi sınırlandırması)
  - `Strict-Transport-Security` (HTTPS zorunluluğu)
  - `Permissions-Policy` (Gereksiz tarayıcı API erişimlerinin kısıtlanması)

## 3. Desteklenen Sürümler

| Sürüm | Güvenlik Desteği |
| --- | --- |
| `v1.2.x` | Aktif |
| `v1.1.x` | Güvenlik yamaları |
| `< v1.1.0` | Desteklenmiyor |
