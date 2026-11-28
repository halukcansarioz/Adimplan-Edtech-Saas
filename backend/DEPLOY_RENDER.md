# API'yi Render'a kurma

1. Render panelinde **New > Blueprint** ile bu depoyu seçin. `render.yaml` iki servis
   tanımlar: `adimplan-api` (API) ve `adimplan-web` (statik site). Ön yüz Vercel'de
   yayınlanıyorsa `adimplan-web` gerekmez; yalnızca API istiyorsanız Blueprint yerine
   **New > Web Service** (Docker, Dockerfile yolu `./backend/Dockerfile`, sağlık yolu
   `/health`) kullanın ve aşağıdaki değişkenleri elle girin.
2. Değişkenler:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`: değerleri `render.yaml` içindedir.
   - `RESEND_API_KEY`: yalnızca gerçek e-posta gönderilecekse, panelden girin.
   - `RESEND_FROM_EMAIL`: Resend'de doğrulanmış alan adınıza ait gönderen adresi.
     Doğrulanmamış bir alan adından gönderim reddedilir.
   - `ALLOWED_ORIGINS`: ön yüz farklı bir alan adındaysa o adresleri virgülle yazın
     (varsayılan listenin yerine geçer).
3. Kontrol: `https://<servis-adresi>/health` yanıt vermelidir.
4. Ön yüz API adresini şu an yalnızca tarayıcı ayarından okur: yönetici panelindeki
   API adresi alanına girilen değer sadece o tarayıcıda geçerlidir.

Ücretsiz planda servis boşta kalınca uyuyabilir; ilk istek gecikebilir.
