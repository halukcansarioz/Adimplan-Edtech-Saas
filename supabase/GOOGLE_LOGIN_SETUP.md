# Google ile Giriş Kurulumu

Giriş sayfasındaki düğme, aşağıdaki ayar tamamlanana kadar görünmez.

## 1. Google Cloud Console
1. Bir proje seçin veya oluşturun, **Google Auth Platform** bölümünü açın.
2. Uygulama adı, destek e-postası ve hedef kitleyi (External) girin. Uygulama
   "Testing" durumundayken yalnızca eklediğiniz test kullanıcıları giriş yapabilir.
3. **Clients > Create client > Web application**:
   - Authorized JavaScript origins: `https://adimplan.vercel.app`
   - Authorized redirect URIs:
     `https://mkimvsmlxassitajminz.supabase.co/auth/v1/callback`
4. Client ID ve Client Secret değerlerini not edin.

## 2. Supabase paneli
1. **Authentication > Sign In / Providers > Google**: sağlayıcıyı açın, Client ID
   ve Client Secret girip kaydedin. Secret değerini depoya yazmayın.
2. **Authentication > URL Configuration**: Redirect URLs listesinde
   `https://adimplan.vercel.app/**` bulunmalı (`EMAIL_SETUP.md`).

## 3. Kontrol
Giriş sayfasını yenileyin, "Google ile devam et" ile giriş yapın.
İlk kez Google ile gelen kullanıcı "Bireysel Koç" arayüzüyle açılır.
