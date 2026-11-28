-- 011_invitations.sql
-- Koç ve öğrenci daveti. 010'dan sonra çalıştırın. Tekrar çalıştırmak güvenlidir.
-- Davet kodunun yalnızca özeti saklanır. Tabloya doğrudan erişim yoktur.

create table if not exists public.invitations (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    email text not null,
    role text not null check (role in ('coach', 'student')),
    student_id uuid references public.students(id) on delete cascade,
    token_hash bytea not null unique,
    invited_by uuid not null references auth.users(id) on delete cascade,
    created_at timestamptz not null default now(),
    expires_at timestamptz not null default now() + interval '7 days',
    accepted_at timestamptz,
    revoked_at timestamptz
);

alter table public.invitations enable row level security;
revoke all on public.invitations from anon, authenticated;

-- Sahip koç ve öğrenci, koç yalnızca öğrenci davet edebilir. 'owner' davetle verilmez.
create or replace function public.can_invite(p_user_id uuid, p_tenant_id uuid, p_role text)
returns boolean
language sql
security definer
stable
set search_path = ''
as $$
    select exists (
        select 1 from public.memberships m
        where m.user_id = p_user_id and m.tenant_id = p_tenant_id
          and (m.role = 'owner' or (m.role = 'coach' and p_role = 'student'))
    );
$$;

create or replace function public.create_invitation(
    p_tenant_id uuid, p_email text, p_role text, p_student_id uuid default null)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_email text := lower(btrim(coalesce(p_email, '')));
    v_token text := replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '');
begin
    if p_role is null or p_role not in ('coach', 'student') then
        raise exception 'invalid_role';
    end if;
    if not public.can_invite(auth.uid(), p_tenant_id, p_role) then
        raise exception 'not_allowed';
    end if;
    if v_email !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' or char_length(v_email) > 254 then
        raise exception 'invalid_email';
    end if;
    if p_student_id is not null and (p_role <> 'student' or not exists (
        select 1 from public.students s
        where s.id = p_student_id and s.tenant_id = p_tenant_id and s.user_id is null)) then
        raise exception 'invalid_student';
    end if;
    -- Aynı adrese verilmiş eski davet geçersiz olur (koç, sahibin koç davetini iptal edemez).
    update public.invitations i set revoked_at = now()
        where i.tenant_id = p_tenant_id and i.email = v_email
          and i.accepted_at is null and i.revoked_at is null
          and public.can_invite(auth.uid(), i.tenant_id, i.role);
    if (select count(*) from public.invitations i
        where i.tenant_id = p_tenant_id and i.accepted_at is null
          and i.revoked_at is null and i.expires_at > now()) >= 50 then
        raise exception 'too_many_pending';
    end if;
    insert into public.invitations (tenant_id, email, role, student_id, token_hash, invited_by)
        values (p_tenant_id, v_email, p_role, p_student_id,
                sha256(convert_to(v_token, 'UTF8')), auth.uid());
    return v_token;
end;
$$;

create or replace function public.list_invitations(p_tenant_id uuid)
returns table (id uuid, email text, role text, expires_at timestamptz)
language sql
security definer
stable
set search_path = ''
as $$
    select i.id, i.email, i.role, i.expires_at
    from public.invitations i
    where i.tenant_id = p_tenant_id
      and i.accepted_at is null and i.revoked_at is null and i.expires_at > now()
      and public.can_invite(auth.uid(), i.tenant_id, i.role)
    order by i.created_at desc;
$$;

create or replace function public.revoke_invitation(p_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
    update public.invitations i set revoked_at = now()
        where i.id = p_id and i.accepted_at is null and i.revoked_at is null
          and public.can_invite(auth.uid(), i.tenant_id, i.role);
    if not found then
        raise exception 'not_allowed';
    end if;
end;
$$;

create or replace function public.accept_invitation(p_token text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_invite public.invitations%rowtype;
    v_email text;
    v_name text;
begin
    if auth.uid() is null then
        raise exception 'not_signed_in';
    end if;
    -- Aynı kullanıcı iki daveti aynı anda kabul edemez.
    perform pg_advisory_xact_lock(hashtext(auth.uid()::text));
    select lower(u.email), coalesce(nullif(btrim(u.raw_user_meta_data ->> 'full_name'), ''), u.email)
        into v_email, v_name
        from auth.users u where u.id = auth.uid() and u.email_confirmed_at is not null;
    if not found then
        raise exception 'email_not_confirmed';
    end if;
    select * into v_invite from public.invitations i
        where i.token_hash = sha256(convert_to(coalesce(p_token, ''), 'UTF8')) for update;
    if not found or v_invite.accepted_at is not null or v_invite.revoked_at is not null
       or v_invite.expires_at <= now()
       -- Davet eden yetkisini kaybettiyse davet de geçersizdir.
       or not public.can_invite(v_invite.invited_by, v_invite.tenant_id, v_invite.role) then
        raise exception 'invalid_invitation';
    end if;
    if v_invite.email <> v_email then
        raise exception 'email_mismatch';
    end if;
    if exists (select 1 from public.memberships m where m.user_id = auth.uid()) then
        raise exception 'already_member';
    end if;
    insert into public.profiles (id, full_name) values (auth.uid(), v_name)
        on conflict (id) do nothing;
    insert into public.memberships (tenant_id, user_id, role)
        values (v_invite.tenant_id, auth.uid(), v_invite.role);
    if v_invite.role = 'student' then
        if v_invite.student_id is null then
            insert into public.students (tenant_id, user_id, full_name)
                values (v_invite.tenant_id, auth.uid(), v_name);
        else
            update public.students s set user_id = auth.uid(), updated_at = now()
                where s.id = v_invite.student_id and s.tenant_id = v_invite.tenant_id
                  and s.user_id is null;
            if not found then
                raise exception 'invalid_invitation';
            end if;
        end if;
    end if;
    update public.invitations i set accepted_at = now() where i.id = v_invite.id;
    return v_invite.role;
end;
$$;

revoke all on function public.can_invite(uuid, uuid, text) from public, anon, authenticated;
revoke all on function public.create_invitation(uuid, text, text, uuid) from public, anon;
revoke all on function public.list_invitations(uuid) from public, anon;
revoke all on function public.revoke_invitation(uuid) from public, anon;
revoke all on function public.accept_invitation(text) from public, anon;
grant execute on function public.create_invitation(uuid, text, text, uuid) to authenticated;
grant execute on function public.list_invitations(uuid) to authenticated;
grant execute on function public.revoke_invitation(uuid) to authenticated;
grant execute on function public.accept_invitation(text) to authenticated;
