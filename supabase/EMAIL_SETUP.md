# E-posta Kurulumu (Supabase panelinde bir kez yapılır)

Kayıt doğrulama ve şifre sıfırlama e-postalarını Supabase Auth gönderir.
Aşağıdaki ayarlar depodaki kodla yapılamaz.

## 1. Yönlendirme adresleri
**Authentication > URL Configuration**

- **Site URL:** `https://adimplan.vercel.app`
- **Redirect URLs:**
  - `https://adimplan.vercel.app/**`
  - `https://adimplan-edtech-saas.vercel.app/**` (bu adres de kullanılıyorsa)
  - `http://localhost:5500/**`, `http://127.0.0.1:5500/**` (yerel geliştirme)

Uygulamanın istediği adres bu listede yoksa Supabase, e-postadaki bağlantıyı
Site URL'ye yönlendirir. Site URL `http://localhost:3000` kalırsa bağlantı
kullanıcının cihazında açılmaz.

## 2. Özel SMTP
Supabase'in yerleşik e-posta servisi yalnızca organizasyon ekip üyelerinin
adreslerine gönderir ve saatlik sınırı çok düşüktür. Gerçek kullanıcılar için
**Authentication > Emails > SMTP Settings** bölümünde özel SMTP açın.

Resend ile (önce Resend'de bir alan adı doğrulanmalıdır):

| Alan | Değer |
|---|---|
| Host | `smtp.resend.com` |
| Port | `465` |
| Username | `resend` |
| Password | Resend API anahtarı (depoya yazmayın) |
| Sender email | doğrulanmış alan adınızdaki bir adres |

## 3. Kontrol
Canlı sitede "Şifremi Unuttum" ile ekip dışı bir adrese sıfırlama isteyin;
bağlantı `login.html` sayfasını açmalı ve yeni şifre penceresi görünmelidir.
Her bağlantı tek kullanımlıktır; en son gelen e-postadakini kullanın.

## Veli raporu e-postası
Bu ayrı bir akıştır: API servisinde `RESEND_API_KEY` ve `RESEND_FROM_EMAIL`
tanımlanmalı, yönetici panelinde API adresi girilmelidir. API adresi boşsa
uygulama cihazdaki e-posta programını açar (`backend/DEPLOY_RENDER.md`).
