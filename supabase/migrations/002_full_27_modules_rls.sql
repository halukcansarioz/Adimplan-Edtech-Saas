-- Adimplo / Adimplan EdTech SaaS: Full 27 Modules Migration & RLS Policies
-- Supports YKS, LGS, KPSS, MEBAGS, ALES, DGS, TUS, YDS

create table if not exists public.exam_catalog (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  category text not null,
  description text,
  default_duration_minutes int not null default 120,
  total_questions int not null default 120,
  wrong_penalty_ratio numeric(4,2) not null default 0.25,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.exam_catalog (code, name, category, description, default_duration_minutes, total_questions, wrong_penalty_ratio)
values
  ('YKS', 'Yuksekogretim Kurumlari Sinavi (TYT/AYT)', 'Universite Giris', 'TYT ve AYT oturumlari icin konu, deneme ve net takibi', 165, 120, 0.25),
  ('LGS', 'Liselere Gecis Sistemi', 'Lise Giris', '8. sinif sozel ve sayisal oturum hazirlik modulu', 155, 90, 0.33),
  ('KPSS', 'Kamu Personeli Secme Sinavi', 'Kamu Kariyer', 'Genel Yetenek, Genel Kultur ve Egitim Bilimleri/Alan', 130, 120, 0.25),
  ('MEBAGS', 'Milli Egitim Bakanligi Akademi Giris Sinavi', 'Ogretmenlik', 'MEB Akademi Giris Sinavi ve OABT hazirlik sureci', 110, 80, 0.25),
  ('ALES', 'Akademik Personel ve Lisansustu Egitimi Giris Sinavi', 'Akademik', 'Sayisal ve Sozel akil yurutme soru takibi', 150, 100, 0.25),
  ('DGS', 'Dikey Gecis Sinavi', 'Onlisans -> Lisans', 'Sayisal ve Sozel yetenek testleri ve net analizi', 135, 100, 0.25),
  ('TUS', 'Tipta Uzmanlik Egitimi Giris Sinavi', 'Saglik Uzmanlik', 'Temel Tip Bilimleri ve Klinik Tip Bilimleri takibi', 150, 120, 0.25),
  ('YDS', 'Yabanci Dil Bilgisi Seviye Tespit Sinavi', 'Yabanci Dil', 'Okuma, kelime, gramer ve ceviri deneme analizi', 180, 80, 0.00)
on conflict (code) do nothing;

create table if not exists public.class_groups (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  name text not null,
  exam_code text not null default 'YKS',
  grade_level text,
  advisor_coach_id uuid references public.profiles(id) on delete set null,
  capacity int not null default 30,
  academic_year text not null default '2026-2027',
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.task_templates (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  created_by uuid references public.profiles(id) on delete set null,
  title text not null,
  description text,
  exam_code text not null default 'YKS',
  subject text not null,
  topic text,
  default_duration_min int not null default 45,
  target_questions int not null default 30,
  recurrence_rule text default 'weekly',
  assigned_class_group_id uuid references public.class_groups(id) on delete set null,
  is_bulk_assignable boolean not null default true,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.daily_question_logs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  log_date date not null default current_date,
  exam_code text not null default 'YKS',
  subject text not null,
  topic text,
  correct_count int not null default 0 check (correct_count >= 0),
  wrong_count int not null default 0 check (wrong_count >= 0),
  blank_count int not null default 0 check (blank_count >= 0),
  net_score numeric(6,2) not null default 0,
  duration_minutes int not null default 0 check (duration_minutes >= 0),
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.daily_mood_logs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  log_date date not null default current_date,
  mood_score int not null check (mood_score between 1 and 5),
  anxiety_level int not null default 3 check (anxiety_level between 1 and 5),
  energy_level int not null default 3 check (energy_level between 1 and 5),
  study_streak_days int not null default 0 check (study_streak_days >= 0),
  focus_minutes int not null default 0 check (focus_minutes >= 0),
  notes text,
  created_at timestamptz not null default now(),
  unique (tenant_id, student_id, log_date)
);

create table if not exists public.book_progress (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  book_title text not null,
  publisher text,
  exam_code text not null default 'YKS',
  subject text not null,
  total_tests int not null default 0 check (total_tests >= 0),
  completed_tests int not null default 0 check (completed_tests >= 0),
  remaining_tests int generated always as (greatest(total_tests - completed_tests, 0)) stored,
  total_questions int not null default 0 check (total_questions >= 0),
  solved_questions int not null default 0 check (solved_questions >= 0),
  status text not null default 'active' check (status in ('active', 'completed', 'paused')),
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create table if not exists public.student_curriculum_progress (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  exam_code text not null default 'YKS',
  subject text not null,
  topic text not null,
  status text not null default 'pending' check (status in ('pending', 'in_progress', 'completed', 'review_needed')),
  mastery_percent int not null default 0 check (mastery_percent between 0 and 100),
  completed_at timestamptz,
  coach_note text,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (tenant_id, student_id, exam_code, subject, topic)
);

create table if not exists public.coaching_sessions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  coach_id uuid not null references public.profiles(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  title text not null default 'Haftalik Kocluk Gorusmesi',
  scheduled_at timestamptz not null,
  duration_minutes int not null default 45 check (duration_minutes > 0),
  meeting_url text,
  status text not null default 'scheduled' check (status in ('scheduled', 'completed', 'cancelled', 'no_show')),
  reminder_30m_sent boolean not null default false,
  reminder_30m_sent_at timestamptz,
  summary_notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  sender_id uuid not null references public.profiles(id) on delete cascade,
  recipient_id uuid references public.profiles(id) on delete cascade,
  class_group_id uuid references public.class_groups(id) on delete set null,
  is_broadcast boolean not null default false,
  subject text,
  body text not null,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.announcements (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  author_id uuid references public.profiles(id) on delete set null,
  title text not null,
  content text not null,
  is_ticker boolean not null default false,
  priority text not null default 'normal' check (priority in ('low', 'normal', 'high', 'urgent')),
  target_role text not null default 'all' check (target_role in ('all', 'student', 'coach', 'parent')),
  starts_at timestamptz not null default now(),
  expires_at timestamptz,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.attendance_records (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  class_group_id uuid references public.class_groups(id) on delete set null,
  student_id uuid not null references public.profiles(id) on delete cascade,
  session_date date not null default current_date,
  status text not null default 'present' check (status in ('present', 'absent', 'late', 'excused')),
  note text,
  recorded_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.payment_records (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  payment_type text not null default 'tuition' check (payment_type in ('tuition', 'coaching_session', 'material', 'other')),
  amount numeric(10,2) not null check (amount >= 0),
  currency text not null default 'TRY',
  due_date date not null,
  paid_at timestamptz,
  status text not null default 'pending' check (status in ('pending', 'paid', 'overdue', 'cancelled', 'refunded')),
  reference_code text,
  notes text,
  created_at timestamptz not null default now()
);

-- Indexes for tenant and student queries
create index if not exists idx_class_groups_tenant on public.class_groups(tenant_id);
create index if not exists idx_task_templates_tenant on public.task_templates(tenant_id);
create index if not exists idx_daily_question_logs_tenant_student on public.daily_question_logs(tenant_id, student_id, log_date);
create index if not exists idx_daily_mood_logs_tenant_student on public.daily_mood_logs(tenant_id, student_id, log_date);
create index if not exists idx_book_progress_tenant_student on public.book_progress(tenant_id, student_id);
create index if not exists idx_student_curriculum_tenant_student on public.student_curriculum_progress(tenant_id, student_id);
create index if not exists idx_coaching_sessions_tenant_sched on public.coaching_sessions(tenant_id, scheduled_at);
create index if not exists idx_messages_tenant_recipient on public.messages(tenant_id, recipient_id, created_at);
create index if not exists idx_announcements_tenant_active on public.announcements(tenant_id, is_active, starts_at);
create index if not exists idx_attendance_records_tenant_date on public.attendance_records(tenant_id, session_date);
create index if not exists idx_payment_records_tenant_status on public.payment_records(tenant_id, status, due_date);

-- Row Level Security (RLS)
alter table public.exam_catalog enable row level security;
alter table public.class_groups enable row level security;
alter table public.task_templates enable row level security;
alter table public.daily_question_logs enable row level security;
alter table public.daily_mood_logs enable row level security;
alter table public.book_progress enable row level security;
alter table public.student_curriculum_progress enable row level security;
alter table public.coaching_sessions enable row level security;
alter table public.messages enable row level security;
alter table public.announcements enable row level security;
alter table public.attendance_records enable row level security;
alter table public.payment_records enable row level security;

create policy "Exam catalog readable by authenticated"
  on public.exam_catalog for select
  using (auth.role() = 'authenticated');

create policy "Class groups isolated by tenant_id"
  on public.class_groups for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Task templates isolated by tenant_id"
  on public.task_templates for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Daily question logs isolated by tenant_id"
  on public.daily_question_logs for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Daily mood logs isolated by tenant_id"
  on public.daily_mood_logs for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Book progress isolated by tenant_id"
  on public.book_progress for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Student curriculum progress isolated by tenant_id"
  on public.student_curriculum_progress for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Coaching sessions isolated by tenant_id"
  on public.coaching_sessions for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Messages isolated by tenant_id"
  on public.messages for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Announcements isolated by tenant_id"
  on public.announcements for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Attendance records isolated by tenant_id"
  on public.attendance_records for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy "Payment records isolated by tenant_id"
  on public.payment_records for all
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));
);
