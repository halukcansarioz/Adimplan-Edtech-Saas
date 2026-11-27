# Yönetici hesapları

Yönetici panellerinde varsayılan şifre veya demo girişi yoktur.

## 1. Kullanıcı oluştur
Supabase panelinde **Authentication > Users > Add user** ile e-posta ve güçlü bir
şifre girin ("Auto Confirm User" işaretli). Şifreyi kimseyle paylaşmayın.

## 2. Yetki ver (SQL Editor)
Aşağıdaki iki yerde `EPOSTA` yerine kendi adresinizi yazın.

Süper admin paneli (`/super-admin.html`):

```sql
update auth.users
set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb) || '{"platform_admin": true}'
where email = 'EPOSTA';
```

Kurum paneli (`/admin.html`) için kullanıcı bir kurumun sahibi (`owner`) olmalı:

```sql
with u as (
  select id, email from auth.users where email = 'EPOSTA'
), p as (
  insert into public.profiles (id, full_name)
  select id, email from u
  on conflict (id) do update set full_name = public.profiles.full_name
  returning id
), t as (
  insert into public.tenants (name, slug)
  values ('Adimplan', 'adimplan')
  on conflict (slug) do update set name = public.tenants.name
  returning id
)
insert into public.memberships (tenant_id, user_id, role)
select t.id, p.id, 'owner' from t, p;
```

Yetkiyi geri almak için ilgili `memberships` satırını silin veya
`platform_admin` alanını kaldırın.
