-- 005_role_based_access.sql
-- 001/002 let every member of a tenant, students included, read and change all of
-- the tenant's data. Run after 001-004. Safe to run more than once.
--
-- owner, coach : full access inside their own tenant
-- student      : reads only their own records; writes only
--                  pomodoro_sessions, mistake_vault, daily_question_logs,
--                  daily_mood_logs, book_progress  (own rows)
--                  study_tasks.status              (own tasks)
--                  messages                        (sends to staff, marks own as read)
--                reads class_groups and announcements addressed to students

create or replace function public.is_tenant_staff(target_tenant_id uuid)
returns boolean
language sql
security definer
stable
set search_path = ''
as $$
    select exists (
        select 1 from public.memberships m
        where m.tenant_id = target_tenant_id
          and m.user_id = auth.uid()
          and m.role in ('owner', 'coach')
    );
$$;

-- Remove the "any member may do anything" policies.
drop policy if exists "Study tasks isolated by tenant_id" on public.study_tasks;
drop policy if exists "Exam attempts isolated by tenant_id" on public.exam_attempts;
drop policy if exists "Exam topic stats isolated by tenant_id" on public.exam_topic_stats;
drop policy if exists "Pomodoro sessions isolated by tenant_id" on public.pomodoro_sessions;
drop policy if exists "Mistake vault isolated by tenant_id" on public.mistake_vault;
drop policy if exists "Class groups isolated by tenant_id" on public.class_groups;
drop policy if exists "Task templates isolated by tenant_id" on public.task_templates;
drop policy if exists "Daily question logs isolated by tenant_id" on public.daily_question_logs;
drop policy if exists "Daily mood logs isolated by tenant_id" on public.daily_mood_logs;
drop policy if exists "Book progress isolated by tenant_id" on public.book_progress;
drop policy if exists "Student curriculum progress isolated by tenant_id" on public.student_curriculum_progress;
drop policy if exists "Coaching sessions isolated by tenant_id" on public.coaching_sessions;
drop policy if exists "Messages isolated by tenant_id" on public.messages;
drop policy if exists "Announcements isolated by tenant_id" on public.announcements;
drop policy if exists "Attendance records isolated by tenant_id" on public.attendance_records;
drop policy if exists "Payment records isolated by tenant_id" on public.payment_records;

-- Staff: full access within the tenant.
do $$
declare t text;
begin
    foreach t in array array[
        'study_tasks', 'exam_attempts', 'exam_topic_stats', 'pomodoro_sessions',
        'mistake_vault', 'class_groups', 'task_templates', 'daily_question_logs',
        'daily_mood_logs', 'book_progress', 'student_curriculum_progress',
        'coaching_sessions', 'messages', 'announcements', 'attendance_records',
        'payment_records'
    ] loop
        execute format('drop policy if exists staff_all on public.%I', t);
        execute format(
            'create policy staff_all on public.%I for all '
            'using (public.is_tenant_staff(tenant_id)) '
            'with check (public.is_tenant_staff(tenant_id))', t);
    end loop;

    -- Students: read their own records.
    foreach t in array array[
        'study_tasks', 'exam_attempts', 'exam_topic_stats', 'pomodoro_sessions',
        'mistake_vault', 'daily_question_logs', 'daily_mood_logs', 'book_progress',
        'student_curriculum_progress', 'coaching_sessions', 'attendance_records',
        'payment_records'
    ] loop
        execute format('drop policy if exists student_read_own on public.%I', t);
        execute format(
            'create policy student_read_own on public.%I for select '
            'using (student_id = auth.uid() and public.is_tenant_member(tenant_id))', t);
    end loop;

    -- Students: manage the records they produce themselves.
    foreach t in array array[
        'pomodoro_sessions', 'mistake_vault', 'daily_question_logs',
        'daily_mood_logs', 'book_progress'
    ] loop
        execute format('drop policy if exists student_write_own on public.%I', t);
        execute format(
            'create policy student_write_own on public.%I for all '
            'using (student_id = auth.uid() and public.is_tenant_member(tenant_id)) '
            'with check (student_id = auth.uid() and public.is_tenant_member(tenant_id))', t);
    end loop;
end $$;

drop policy if exists member_read on public.class_groups;
create policy member_read on public.class_groups
    for select using (public.is_tenant_member(tenant_id));

drop policy if exists member_read_addressed on public.announcements;
create policy member_read_addressed on public.announcements
    for select using (
        public.is_tenant_member(tenant_id)
        and is_active
        and starts_at <= now()
        and (expires_at is null or expires_at > now())
        and target_role in ('all', 'student')
    );

drop policy if exists student_update_own_task on public.study_tasks;
create policy student_update_own_task on public.study_tasks
    for update
    using (student_id = auth.uid() and public.is_tenant_member(tenant_id))
    with check (student_id = auth.uid() and public.is_tenant_member(tenant_id));

-- Messages. Class-group broadcasts stay staff-only because the schema does not
-- record which students belong to a class group.
drop policy if exists member_read_messages on public.messages;
create policy member_read_messages on public.messages
    for select using (
        public.is_tenant_member(tenant_id)
        and (sender_id = auth.uid()
             or recipient_id = auth.uid()
             or (is_broadcast and class_group_id is null))
    );

create or replace function public.is_user_staff_of(target_tenant_id uuid, target_user_id uuid)
returns boolean
language sql
security definer
stable
set search_path = ''
as $$
    select exists (
        select 1 from public.memberships m
        where m.tenant_id = target_tenant_id
          and m.user_id = target_user_id
          and m.role in ('owner', 'coach')
    );
$$;

drop policy if exists student_send_to_staff on public.messages;
create policy student_send_to_staff on public.messages
    for insert with check (
        sender_id = auth.uid()
        and public.is_tenant_member(tenant_id)
        and not is_broadcast
        and class_group_id is null
        and public.is_user_staff_of(tenant_id, recipient_id)
    );

drop policy if exists recipient_mark_read on public.messages;
create policy recipient_mark_read on public.messages
    for update
    using (recipient_id = auth.uid() and public.is_tenant_member(tenant_id))
    with check (recipient_id = auth.uid() and public.is_tenant_member(tenant_id));

-- RLS cannot limit columns, so a trigger does: a non-staff user may change only
-- the column named in the trigger argument. The SQL editor and service role
-- (auth.uid() is null) are not affected.
create or replace function public.limit_non_staff_update()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    if auth.uid() is not null
       and not public.is_tenant_staff(old.tenant_id)
       and (to_jsonb(new) - tg_argv[0]) is distinct from (to_jsonb(old) - tg_argv[0]) then
        raise exception 'only the % column may be changed', tg_argv[0]
            using errcode = 'insufficient_privilege';
    end if;
    return new;
end;
$$;

drop trigger if exists limit_non_staff_update on public.study_tasks;
create trigger limit_non_staff_update before update on public.study_tasks
    for each row execute function public.limit_non_staff_update('status');

drop trigger if exists limit_non_staff_update on public.messages;
create trigger limit_non_staff_update before update on public.messages
    for each row execute function public.limit_non_staff_update('read_at');
