// Yönetici panellerinin girişi (Supabase Auth).
// Proje adresi bilerek koda sabitlendi: localStorage'dan okunsaydı başka bir
// projedeki hesapla bu kapıdan geçilebilirdi. Publishable key gizli değildir;
// verileri veritabanındaki RLS kuralları korur. Buraya asla service_role
// anahtarı koymayın.
// Not: bu statik bir sayfadır. Bu kapı arayüze girişi denetler; sunucudaki
// verilerin güvenliği yine RLS'e dayanır. Yetki kurulumu: supabase/ADMIN_SETUP.md
(function () {
  'use strict';
  const URL_ = 'https://mkimvsmlxassitajminz.supabase.co';
  const KEY = 'sb_publishable_duEqBEFX7FsPnbEq0uo9rg_osJiJp5D';
  const storeKey = (kind) => 'adimplan_auth_' + kind;

  async function call(path, options, token) {
    const headers = { apikey: KEY, 'Content-Type': 'application/json' };
    if (token) headers.Authorization = 'Bearer ' + token;
    try {
      return await fetch(URL_ + path, Object.assign({ headers }, options));
    } catch (e) {
      throw new Error('Sunucuya ulaşılamadı. Bağlantınızı kontrol edin.');
    }
  }

  // Kullanıcı ve rol her seferinde sunucudan okunur; tarayıcıdaki bilgiye güvenilmez.
  async function authorize(kind, token) {
    const userRes = await call('/auth/v1/user', {}, token);
    if (!userRes.ok) throw new Error('Oturum süresi doldu. Tekrar giriş yapın.');
    const user = await userRes.json();
    let allowed = false;
    if (kind === 'platform') {
      allowed = !!(user.app_metadata && user.app_metadata.platform_admin === true);
    } else if (kind === 'owner' && user.id) {
      const res = await call(
        '/rest/v1/memberships?select=id&role=eq.owner&limit=1&user_id=eq.' + encodeURIComponent(user.id),
        {}, token);
      if (!res.ok) throw new Error('Yetki kontrol edilemedi. Daha sonra tekrar deneyin.');
      const rows = await res.json();
      allowed = Array.isArray(rows) && rows.length > 0;
    }
    if (!allowed) throw new Error('Bu hesabın bu panele erişim yetkisi yok.');
    return { email: user.email || '' };
  }

  async function login(kind, email, password) {
    if (!email || !password) throw new Error('E-posta ve şifre girin.');
    const res = await call('/auth/v1/token?grant_type=password', {
      method: 'POST', body: JSON.stringify({ email, password })
    });
    if (res.status === 429) throw new Error('Çok fazla deneme. Biraz bekleyin.');
    if (!res.ok) throw new Error('E-posta veya şifre hatalı.');
    const token = (await res.json()).access_token;
    const user = await authorize(kind, token);
    sessionStorage.setItem(storeKey(kind), token);
    return user;
  }

  // Sayfa yenilendiğinde: geçerli ve yetkili bir oturum yoksa null döner.
  async function restore(kind) {
    const token = sessionStorage.getItem(storeKey(kind));
    if (!token) return null;
    try {
      return await authorize(kind, token);
    } catch (e) {
      sessionStorage.removeItem(storeKey(kind));
      return null;
    }
  }

  function logout(kind) {
    const token = sessionStorage.getItem(storeKey(kind));
    sessionStorage.removeItem(storeKey(kind));
    if (token) call('/auth/v1/logout?scope=local', { method: 'POST' }, token).catch(() => {});
  }

  // Yetki her çağrıda veritabanında yeniden denetlenir; burada yalnızca oturum eklenir.
  async function rpc(kind, name, args) {
    const token = sessionStorage.getItem(storeKey(kind));
    if (!token) throw new Error('Oturum süresi doldu. Tekrar giriş yapın.');
    const res = await call('/rest/v1/rpc/' + name, { method: 'POST', body: JSON.stringify(args || {}) }, token);
    if (res.status === 401) throw new Error('Oturum süresi doldu. Tekrar giriş yapın.');
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;
    if (!res.ok) throw new Error((data && data.message) || 'İşlem tamamlanamadı.');
    return data;
  }

  // Eski sürümün düz metin yönetici şifresini tarayıcıdan sil.
  localStorage.removeItem('ivme_admin_pass');

  window.AdminAuth = { login, restore, logout, rpc };
})();
