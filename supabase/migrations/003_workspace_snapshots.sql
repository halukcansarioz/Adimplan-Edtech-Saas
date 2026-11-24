-- 003_workspace_snapshots.sql
-- Tek tikla bulut senkronizasyonu (Push / Pull) icin workspace_snapshots tablosu ve RLS politikalari

create table if not exists public.workspace_snapshots (
  id uuid primary key default gen_random_uuid(),
  workspace_key text unique not null,
  payload jsonb not null,
  updated_at timestamptz default now()
);

create index if not exists idx_workspace_snapshots_key on public.workspace_snapshots (workspace_key);

alter table public.workspace_snapshots enable row level security;

drop policy if exists "workspace_snapshots_select" on public.workspace_snapshots;
create policy "workspace_snapshots_select"
  on public.workspace_snapshots
  for select
  to anon, authenticated
  using (true);

drop policy if exists "workspace_snapshots_insert" on public.workspace_snapshots;
create policy "workspace_snapshots_insert"
  on public.workspace_snapshots
  for insert
  to anon, authenticated
  with check (true);

drop policy if exists "workspace_snapshots_update" on public.workspace_snapshots;
create policy "workspace_snapshots_update"
  on public.workspace_snapshots
  for update
  to anon, authenticated
  using (true)
  with check (true);
