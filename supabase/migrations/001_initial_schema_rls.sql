-- Multi-tenant EdTech Coaching & Student Tracking Schema (PostgreSQL / Supabase RLS)
create extension if not exists "pgcrypto";

-- 1. Tenants
create table if not exists public.tenants (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text unique not null,
    created_at timestamptz not null default now()
);

-- 2. Profiles (linked to auth.users)
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text not null,
    avatar_url text,
    created_at timestamptz not null default now()
);

-- 3. Memberships (tenant_id + user_id + role)
create table if not exists public.memberships (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    role text not null check (role in ('owner', 'coach', 'student')),
    created_at timestamptz not null default now(),
    unique (tenant_id, user_id)
);

-- 4. Exam Subjects
create table if not exists public.exam_subjects (
    id uuid primary key default gen_random_uuid(),
    exam_type text not null default 'TYT',
    name text not null,
    code text unique not null,
    created_at timestamptz not null default now()
);

-- 5. Exam Topics
create table if not exists public.exam_topics (
    id uuid primary key default gen_random_uuid(),
    subject_id uuid not null references public.exam_subjects(id) on delete cascade,
    name text not null,
    order_index int not null default 0,
    unique (subject_id, name)
);

-- 6. Study Tasks
create table if not exists public.study_tasks (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    student_id uuid not null references public.profiles(id) on delete cascade,
    coach_id uuid references public.profiles(id) on delete set null,
    topic_id uuid references public.exam_topics(id) on delete set null,
    title text not null,
    due_date date,
    status text not null default 'pending' check (status in ('pending', 'in_progress', 'completed')),
    created_at timestamptz not null default now()
);

-- 7. Exam Attempts
create table if not exists public.exam_attempts (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    student_id uuid not null references public.profiles(id) on delete cascade,
    exam_name text not null,
    exam_date date not null default current_date,
    total_net numeric(5,2) not null default 0,
    created_at timestamptz not null default now()
);

-- 8. Exam Topic Stats
create table if not exists public.exam_topic_stats (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    attempt_id uuid not null references public.exam_attempts(id) on delete cascade,
    student_id uuid not null references public.profiles(id) on delete cascade,
    topic_id uuid not null references public.exam_topics(id) on delete cascade,
    correct_count int not null default 0 check (correct_count >= 0),
    wrong_count int not null default 0 check (wrong_count >= 0),
    empty_count int not null default 0 check (empty_count >= 0),
    net numeric(5,2) generated always as (correct_count - (wrong_count::numeric / 4.0)) stored
);

-- 9. Pomodoro Sessions
create table if not exists public.pomodoro_sessions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    student_id uuid not null references public.profiles(id) on delete cascade,
    topic_id uuid references public.exam_topics(id) on delete set null,
    duration_minutes int not null check (duration_minutes > 0),
    started_at timestamptz not null default now(),
    ended_at timestamptz
);

-- 10. Mistake Vault
create table if not exists public.mistake_vault (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    student_id uuid not null references public.profiles(id) on delete cascade,
    topic_id uuid references public.exam_topics(id) on delete set null,
    question_note text not null,
    image_url text,
    is_resolved boolean not null default false,
    created_at timestamptz not null default now()
);

-- View: Student Topic Heatmap
create or replace view public.student_topic_heatmap as
select
    ets.tenant_id,
    ets.student_id,
    es.name as subject_name,
    et.id as topic_id,
    et.name as topic_name,
    sum(ets.correct_count) as total_correct,
    sum(ets.wrong_count) as total_wrong,
    sum(ets.empty_count) as total_empty,
    round(sum(ets.net), 2) as total_net,
    case
        when sum(ets.correct_count + ets.wrong_count + ets.empty_count) = 0 then 0
        else round(
            greatest(0, sum(ets.net)) /
            sum(ets.correct_count + ets.wrong_count + ets.empty_count)::numeric * 100,
            2
        )
    end as mastery_percentage
from public.exam_topic_stats ets
join public.exam_topics et on et.id = ets.topic_id
join public.exam_subjects es on es.id = et.subject_id
group by ets.tenant_id, ets.student_id, es.name, et.id, et.name;

-- Helper function for tenant_id membership check
create or replace function public.is_tenant_member(target_tenant_id uuid)
returns boolean
language sql
security definer
stable
as $$
    select exists (
        select 1
        from public.memberships m
        where m.tenant_id = target_tenant_id
          and m.user_id = auth.uid()
    );
$$;

-- Enable Row Level Security (RLS)
alter table public.tenants enable row level security;
alter table public.profiles enable row level security;
alter table public.memberships enable row level security;
alter table public.exam_subjects enable row level security;
alter table public.exam_topics enable row level security;
alter table public.study_tasks enable row level security;
alter table public.exam_attempts enable row level security;
alter table public.exam_topic_stats enable row level security;
alter table public.pomodoro_sessions enable row level security;
alter table public.mistake_vault enable row level security;

-- RLS Policies
create policy "Tenants visible to members"
    on public.tenants for select
    using (public.is_tenant_member(id));

create policy "Profiles readable by authenticated users"
    on public.profiles for select
    using (auth.uid() = id or exists (
        select 1 from public.memberships m1
        join public.memberships m2 on m1.tenant_id = m2.tenant_id
        where m1.user_id = auth.uid() and m2.user_id = profiles.id
    ));

create policy "Users can update own profile"
    on public.profiles for update
    using (auth.uid() = id);

create policy "Memberships isolated by tenant_id"
    on public.memberships for all
    using (public.is_tenant_member(tenant_id))
    with check (public.is_tenant_member(tenant_id));

create policy "Exam subjects readable by authenticated"
    on public.exam_subjects for select
    using (auth.role() = 'authenticated');

create policy "Exam topics readable by authenticated"
    on public.exam_topics for select
    using (auth.role() = 'authenticated');

create policy "Study tasks isolated by tenant_id"
    on public.study_tasks for all
    using (public.is_tenant_member(tenant_id))
    with check (public.is_tenant_member(tenant_id));

create policy "Exam attempts isolated by tenant_id"
    on public.exam_attempts for all
    using (public.is_tenant_member(tenant_id))
    with check (public.is_tenant_member(tenant_id));

create policy "Exam topic stats isolated by tenant_id"
    on public.exam_topic_stats for all
    using (public.is_tenant_member(tenant_id))
    with check (public.is_tenant_member(tenant_id));

create policy "Pomodoro sessions isolated by tenant_id"
    on public.pomodoro_sessions for all
    using (public.is_tenant_member(tenant_id))
    with check (public.is_tenant_member(tenant_id));

create policy "Mistake vault isolated by tenant_id"
    on public.mistake_vault for all
    using (public.is_tenant_member(tenant_id))
    with check (public.is_tenant_member(tenant_id));

-- Initial Seed Data: TYT Matematik & TYT Turkce
insert into public.exam_subjects (exam_type, name, code) values
    ('TYT', 'Matematik', 'TYT_MAT'),
    ('TYT', 'Türkçe', 'TYT_TUR')
on conflict (code) do nothing;

insert into public.exam_topics (subject_id, name, order_index)
select s.id, t.topic_name, t.ord
from public.exam_subjects s
cross join (values
    ('TYT_MAT', 'Temel Kavramlar', 1),
    ('TYT_MAT', 'Sayı Basamakları ve Bölünebilme', 2),
    ('TYT_MAT', 'Rasyonel Sayılar ve Basit Eşitsizlikler', 3),
    ('TYT_MAT', 'Üslü ve Köklü Sayılar', 4),
    ('TYT_MAT', 'Problemler', 5),
    ('TYT_MAT', 'Fonksiyonlar', 6),
    ('TYT_TUR', 'Sözcükte Anlam', 1),
    ('TYT_TUR', 'Cümlede Anlam', 2),
    ('TYT_TUR', 'Paragrafta Anlam', 3),
    ('TYT_TUR', 'Ses Bilgisi ve Yazım Kuralları', 4),
    ('TYT_TUR', 'Noktalama İşaretleri', 5),
    ('TYT_TUR', 'Cümlenin Ögeleri', 6)
) as t(subj_code, topic_name, ord)
where s.code = t.subj_code
on conflict (subject_id, name) do nothing;
