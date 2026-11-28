-- 010_organization_requests.sql
-- Onaylı kurum açma: koç başvurur, platform yöneticisi onaylar.
-- 001-008'den sonra çalıştırın (009'a bağlı değildir). Tekrar çalıştırmak güvenlidir.
-- Başvuru tablosuna doğrudan erişim yoktur; her işlem aşağıdaki işlevlerle yapılır.

create table if not exists public.organization_requests (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    org_name text not null check (char_length(org_name) between 2 and 80),
    status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
    tenant_id uuid references public.tenants(id) on delete set null,
    created_at timestamptz not null default now(),
    reviewed_at timestamptz,
    reviewed_by uuid references auth.users(id) on delete set null
);

-- Bir kullanıcının aynı anda tek bekleyen başvurusu olabilir.
create unique index if not exists organization_requests_one_pending
    on public.organization_requests (user_id) where status = 'pending';

alter table public.organization_requests enable row level security;
revoke all on public.organization_requests from anon, authenticated;

-- platform_admin yalnızca sunucu tarafında değiştirilebilen app_metadata'dan okunur.
create or replace function public.is_platform_admin()
returns boolean
language sql
stable
set search_path = ''
as $$
    select coalesce(auth.jwt() -> 'app_metadata' ->> 'platform_admin', '') = 'true';
$$;

create or replace function public.request_organization(p_name text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_name text := btrim(coalesce(p_name, ''));
begin
    if auth.uid() is null then
        raise exception 'not_signed_in';
    end if;
    if not exists (select 1 from auth.users u where u.id = auth.uid() and u.email_confirmed_at is not null) then
        raise exception 'email_not_confirmed';
    end if;
    if char_length(v_name) not between 2 and 80 then
        raise exception 'invalid_name';
    end if;
    if exists (select 1 from public.memberships m where m.user_id = auth.uid()) then
        raise exception 'already_member';
    end if;
    insert into public.organization_requests (user_id, org_name) values (auth.uid(), v_name);
exception
    when unique_violation then
        raise exception 'already_pending';
end;
$$;

create or replace function public.my_organization_request()
returns table (org_name text, status text, created_at timestamptz)
language sql
security definer
stable
set search_path = ''
as $$
    select r.org_name, r.status, r.created_at
    from public.organization_requests r
    where r.user_id = auth.uid()
    order by r.created_at desc
    limit 1;
$$;

create or replace function public.list_organization_requests()
returns table (id uuid, email text, org_name text, created_at timestamptz)
language plpgsql
security definer
stable
set search_path = ''
as $$
begin
    if not public.is_platform_admin() then
        raise exception 'not_allowed';
    end if;
    return query
        select r.id, u.email::text, r.org_name, r.created_at
        from public.organization_requests r
        join auth.users u on u.id = r.user_id
        where r.status = 'pending'
        order by r.created_at;
end;
$$;

create or replace function public.review_organization_request(p_request_id uuid, p_approve boolean)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_request public.organization_requests%rowtype;
    v_tenant_id uuid;
begin
    if not public.is_platform_admin() then
        raise exception 'not_allowed';
    end if;
    if p_approve is null then
        raise exception 'invalid_decision';
    end if;
    select * into v_request from public.organization_requests r where r.id = p_request_id for update;
    if not found or v_request.status <> 'pending' then
        raise exception 'request_not_pending';
    end if;
    if p_approve then
        if exists (select 1 from public.memberships m where m.user_id = v_request.user_id) then
            raise exception 'already_member';
        end if;
        insert into public.profiles (id, full_name)
            select u.id, coalesce(nullif(u.raw_user_meta_data ->> 'full_name', ''), u.email)
            from auth.users u where u.id = v_request.user_id
            on conflict (id) do nothing;
        insert into public.tenants (name, slug)
            values (v_request.org_name, 'org-' || replace(v_request.id::text, '-', ''))
            returning public.tenants.id into v_tenant_id;
        insert into public.memberships (tenant_id, user_id, role)
            values (v_tenant_id, v_request.user_id, 'owner');
    end if;
    update public.organization_requests r
        set status = case when p_approve then 'approved' else 'rejected' end,
            tenant_id = v_tenant_id, reviewed_at = now(), reviewed_by = auth.uid()
        where r.id = p_request_id;
end;
$$;

revoke all on function public.is_platform_admin() from public, anon;
revoke all on function public.request_organization(text) from public, anon;
revoke all on function public.my_organization_request() from public, anon;
revoke all on function public.list_organization_requests() from public, anon;
revoke all on function public.review_organization_request(uuid, boolean) from public, anon;
grant execute on function public.is_platform_admin() to authenticated;
grant execute on function public.request_organization(text) to authenticated;
grant execute on function public.my_organization_request() to authenticated;
grant execute on function public.list_organization_requests() to authenticated;
grant execute on function public.review_organization_request(uuid, boolean) to authenticated;
