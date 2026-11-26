-- 004_security_hardening.sql
-- Fixes access-control holes left by 001 and 003. Safe to run more than once.

-- 1) The heatmap view ran with its owner's rights and bypassed RLS, exposing
--    every tenant's results. security_invoker applies the caller's RLS (PostgreSQL 15+).
alter view public.student_topic_heatmap set (security_invoker = true);
revoke all on public.student_topic_heatmap from anon;

-- 2) Pin the search_path of the SECURITY DEFINER helper.
alter function public.is_tenant_member(uuid) set search_path = '';

create or replace function public.is_tenant_owner(target_tenant_id uuid)
returns boolean
language sql
security definer
stable
set search_path = ''
as $$
    select exists (
        select 1
        from public.memberships m
        where m.tenant_id = target_tenant_id
          and m.user_id = auth.uid()
          and m.role = 'owner'
    );
$$;

-- 3) Any member (including students) could make themselves owner, remove the
--    owner or add outsiders. Members may now read; only owners may change.
drop policy if exists "Memberships isolated by tenant_id" on public.memberships;
drop policy if exists "memberships_select_member" on public.memberships;
drop policy if exists "memberships_insert_owner" on public.memberships;
drop policy if exists "memberships_update_owner" on public.memberships;
drop policy if exists "memberships_delete_owner" on public.memberships;

create policy "memberships_select_member" on public.memberships
    for select using (public.is_tenant_member(tenant_id));
create policy "memberships_insert_owner" on public.memberships
    for insert with check (public.is_tenant_owner(tenant_id));
create policy "memberships_update_owner" on public.memberships
    for update using (public.is_tenant_owner(tenant_id))
    with check (public.is_tenant_owner(tenant_id));
create policy "memberships_delete_owner" on public.memberships
    for delete using (public.is_tenant_owner(tenant_id));

-- 4) Anyone holding the public anon key could list, read and overwrite EVERY
--    workspace snapshot. Direct table access is removed; a caller must now know
--    the exact workspace key, which the app generates randomly. Treat that key
--    like a password. (Per-user ownership via Supabase Auth would be stronger.)
drop policy if exists "workspace_snapshots_select" on public.workspace_snapshots;
drop policy if exists "workspace_snapshots_insert" on public.workspace_snapshots;
drop policy if exists "workspace_snapshots_update" on public.workspace_snapshots;
revoke all on public.workspace_snapshots from anon, authenticated;

create or replace function public.push_workspace_snapshot(p_workspace_key text, p_payload jsonb)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
    if p_workspace_key is null or length(p_workspace_key) < 24 then
        raise exception 'workspace key must be at least 24 characters';
    end if;
    if p_payload is null or pg_column_size(p_payload) > 5 * 1024 * 1024 then
        raise exception 'payload is missing or too large';
    end if;
    insert into public.workspace_snapshots (workspace_key, payload, updated_at)
    values (p_workspace_key, p_payload, now())
    on conflict (workspace_key)
    do update set payload = excluded.payload, updated_at = excluded.updated_at;
end;
$$;

create or replace function public.pull_workspace_snapshot(p_workspace_key text)
returns table (payload jsonb, updated_at timestamptz)
language sql
security definer
stable
set search_path = ''
as $$
    select s.payload, s.updated_at
    from public.workspace_snapshots s
    where s.workspace_key = p_workspace_key
      and length(p_workspace_key) >= 24;
$$;

revoke all on function public.push_workspace_snapshot(text, jsonb) from public;
revoke all on function public.pull_workspace_snapshot(text) from public;
grant execute on function public.push_workspace_snapshot(text, jsonb) to anon, authenticated;
grant execute on function public.pull_workspace_snapshot(text) to anon, authenticated;

-- Snapshots saved earlier under a short key (e.g. 'adimplan-default') were
-- publicly readable. They stay in the table but can no longer be pulled by the
-- app. Push again from a device that has the data, then delete the old rows:
--   delete from public.workspace_snapshots where length(workspace_key) < 24;
