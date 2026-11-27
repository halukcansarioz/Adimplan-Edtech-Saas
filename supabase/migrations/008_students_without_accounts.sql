-- 008_students_without_accounts.sql
-- Öğrenci artık giriş hesabı olmadan eklenebilir. Hesap sonradan user_id ile
-- bağlanır. Bu aşamada yalnızca students ve study_tasks değişir; diğer öğrenci
-- tabloları hâlâ profiles(id) kullanır. 007'den sonra çalıştırın.

create table if not exists public.students (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    user_id uuid,
    full_name text not null check (length(btrim(full_name)) > 0),
    goal text not null default '',
    risk text not null default 'Normal',
    client_id text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (id, tenant_id),
    unique (tenant_id, user_id),
    unique (tenant_id, client_id),
    -- Yalnızca aynı kurumun üyesi bağlanabilir; üyelik silinirse bağ kopar, kayıt kalır.
    foreign key (tenant_id, user_id) references public.memberships (tenant_id, user_id)
        on delete set null (user_id)
);

alter table public.students enable row level security;
revoke all on public.students from anon;
grant select, insert, update, delete on public.students to authenticated;

drop policy if exists staff_all on public.students;
create policy staff_all on public.students for all
    using (public.is_tenant_staff(tenant_id))
    with check (public.is_tenant_staff(tenant_id));

drop policy if exists student_read_own on public.students;
create policy student_read_own on public.students for select
    using (user_id = auth.uid() and public.is_tenant_member(tenant_id));

create or replace function public.is_own_student(target_tenant_id uuid, target_student_id uuid)
returns boolean
language sql
security definer
stable
set search_path = ''
as $$
    select public.is_tenant_member(target_tenant_id) and exists (
        select 1 from public.students s
        where s.id = target_student_id
          and s.tenant_id = target_tenant_id
          and s.user_id = auth.uid()
    );
$$;

-- Var olan görevleri yeni öğrenci kayıtlarına taşı (yalnızca ilk çalıştırmada).
do $$
begin
    if exists (select 1 from pg_constraint where conname = 'study_tasks_student_tenant_fkey') then
        return;
    end if;

    drop policy if exists student_read_own on public.study_tasks;
    drop policy if exists student_update_own_task on public.study_tasks;
    alter table public.study_tasks add column new_student_id uuid;

    -- Üyeliği olan her (kurum, kullanıcı) için hesaba bağlı öğrenci kaydı.
    insert into public.students (tenant_id, user_id, full_name)
    select distinct t.tenant_id, t.student_id, p.full_name
    from public.study_tasks t
    join public.profiles p on p.id = t.student_id
    join public.memberships m on m.tenant_id = t.tenant_id and m.user_id = t.student_id
    on conflict (tenant_id, user_id) do nothing;

    -- Üyeliği kalmamış öğrencilerin görevleri de korunur (hesapsız kayıt).
    insert into public.students (tenant_id, full_name, client_id)
    select distinct t.tenant_id, p.full_name, 'profile:' || p.id
    from public.study_tasks t
    join public.profiles p on p.id = t.student_id
    where not exists (select 1 from public.memberships m
                      where m.tenant_id = t.tenant_id and m.user_id = t.student_id)
    on conflict (tenant_id, client_id) do nothing;

    update public.study_tasks t set new_student_id = s.id
    from public.students s
    where s.tenant_id = t.tenant_id
      and (s.user_id = t.student_id or s.client_id = 'profile:' || t.student_id);

    alter table public.study_tasks drop column student_id;
    alter table public.study_tasks rename column new_student_id to student_id;
    alter table public.study_tasks alter column student_id set not null;
    alter table public.study_tasks add constraint study_tasks_student_tenant_fkey
        foreign key (student_id, tenant_id) references public.students (id, tenant_id) on delete cascade;
    create index if not exists study_tasks_student_idx on public.study_tasks (student_id);
end $$;

-- Uygulamadaki görev alanları.
alter table public.study_tasks
    add column if not exists day text check (day in ('Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz')),
    add column if not exists task_type text not null default 'Konu',
    add column if not exists meta text not null default '',
    add column if not exists position integer not null default 0,
    add column if not exists client_id text;

create unique index if not exists study_tasks_tenant_client_key
    on public.study_tasks (tenant_id, client_id);

drop policy if exists student_read_own on public.study_tasks;
create policy student_read_own on public.study_tasks for select
    using (public.is_own_student(tenant_id, student_id));

drop policy if exists student_update_own_task on public.study_tasks;
create policy student_update_own_task on public.study_tasks for update
    using (public.is_own_student(tenant_id, student_id))
    with check (public.is_own_student(tenant_id, student_id));
