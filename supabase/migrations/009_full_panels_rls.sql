-- v1.7.0 Full Panels Tables and Tenant-Based PostgreSQL RLS Policies

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.weekly_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  student_id UUID NOT NULL,
  title TEXT NOT NULL,
  subject TEXT,
  due_date DATE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.pomodoro_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  student_id UUID NOT NULL,
  subject TEXT,
  duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.question_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  student_id UUID NOT NULL,
  subject TEXT NOT NULL,
  topic TEXT,
  correct_count INTEGER NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
  wrong_count INTEGER NOT NULL DEFAULT 0 CHECK (wrong_count >= 0),
  blank_count INTEGER NOT NULL DEFAULT 0 CHECK (blank_count >= 0),
  logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.exam_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  student_id UUID NOT NULL,
  exam_name TEXT NOT NULL,
  exam_type TEXT NOT NULL DEFAULT 'TYT',
  total_net NUMERIC(6,2) NOT NULL DEFAULT 0,
  taken_at DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.student_mistakes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  student_id UUID NOT NULL,
  subject TEXT NOT NULL,
  topic TEXT NOT NULL,
  note TEXT,
  resolved BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.session_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  coach_id UUID NOT NULL,
  student_id UUID NOT NULL,
  delta_sessions INTEGER NOT NULL,
  reason TEXT NOT NULL,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.weekly_parent_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  student_id UUID NOT NULL,
  week_start DATE NOT NULL,
  summary TEXT NOT NULL,
  total_questions INTEGER NOT NULL DEFAULT 0,
  total_pomodoro_minutes INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE public.weekly_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pomodoro_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_mistakes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weekly_parent_reports ENABLE ROW LEVEL SECURITY;

-- Tenant-based RLS policies
DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'weekly_tasks',
    'pomodoro_sessions',
    'question_logs',
    'exam_results',
    'student_mistakes',
    'session_ledger',
    'weekly_parent_reports'
  ]
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', tbl || '_tenant_isolation_select', tbl);
    EXECUTE format(
      'CREATE POLICY %I ON public.%I FOR SELECT USING (tenant_id::text = COALESCE(NULLIF(current_setting(''app.current_tenant_id'', true), ''''), auth.jwt() ->> ''tenant_id''));',
      tbl || '_tenant_isolation_select', tbl
    );

    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', tbl || '_tenant_isolation_insert', tbl);
    EXECUTE format(
      'CREATE POLICY %I ON public.%I FOR INSERT WITH CHECK (tenant_id::text = COALESCE(NULLIF(current_setting(''app.current_tenant_id'', true), ''''), auth.jwt() ->> ''tenant_id''));',
      tbl || '_tenant_isolation_insert', tbl
    );

    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', tbl || '_tenant_isolation_update', tbl);
    EXECUTE format(
      'CREATE POLICY %I ON public.%I FOR UPDATE USING (tenant_id::text = COALESCE(NULLIF(current_setting(''app.current_tenant_id'', true), ''''), auth.jwt() ->> ''tenant_id'')) WITH CHECK (tenant_id::text = COALESCE(NULLIF(current_setting(''app.current_tenant_id'', true), ''''), auth.jwt() ->> ''tenant_id''));',
      tbl || '_tenant_isolation_update', tbl
    );

    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', tbl || '_tenant_isolation_delete', tbl);
    EXECUTE format(
      'CREATE POLICY %I ON public.%I FOR DELETE USING (tenant_id::text = COALESCE(NULLIF(current_setting(''app.current_tenant_id'', true), ''''), auth.jwt() ->> ''tenant_id''));',
      tbl || '_tenant_isolation_delete', tbl
    );
  END LOOP;
END $$;
