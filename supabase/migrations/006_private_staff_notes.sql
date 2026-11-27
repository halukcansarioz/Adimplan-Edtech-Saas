-- 006_private_staff_notes.sql
-- Koç/kurum notlarını öğrencinin okuyamayacağı tablolara taşır.
-- RLS sütun gizleyemediği (öğrenci ve koç aynı "authenticated" rolünü kullandığı)
-- için notlar ayrı tablolarda tutulur. Var olan notlar önce kopyalanır, sonra
-- eski sütunlar kaldırılır. 005'ten sonra çalıştırın.

do $$
declare
    r record;
begin
    for r in
        select * from (values
            ('coaching_sessions', 'summary_notes', 'coaching_session_notes', 'session_id'),
            ('student_curriculum_progress', 'coach_note', 'curriculum_progress_notes', 'progress_id'),
            ('payment_records', 'notes', 'payment_record_notes', 'payment_id')
        ) as v(parent, old_column, note_table, ref_column)
    loop
        -- (id, tenant_id) anahtarı: not, ait olduğu kayıtla aynı kurumda olmak zorunda.
        if not exists (select 1 from pg_constraint where conname = r.parent || '_id_tenant_key') then
            execute format('alter table public.%I add constraint %I unique (id, tenant_id)',
                r.parent, r.parent || '_id_tenant_key');
        end if;

        execute format(
            'create table if not exists public.%I ('
            ' %I uuid primary key,'
            ' tenant_id uuid not null,'
            ' note text not null,'
            ' updated_at timestamptz not null default now(),'
            ' foreign key (%I, tenant_id) references public.%I (id, tenant_id) on delete cascade)',
            r.note_table, r.ref_column, r.ref_column, r.parent);

        execute format('alter table public.%I enable row level security', r.note_table);
        execute format('revoke all on public.%I from anon', r.note_table);
        execute format('grant select, insert, update, delete on public.%I to authenticated', r.note_table);
        execute format('drop policy if exists staff_all on public.%I', r.note_table);
        execute format(
            'create policy staff_all on public.%I for all '
            'using (public.is_tenant_staff(tenant_id)) '
            'with check (public.is_tenant_staff(tenant_id))', r.note_table);

        if exists (select 1 from information_schema.columns
                   where table_schema = 'public' and table_name = r.parent
                     and column_name = r.old_column) then
            execute format(
                'insert into public.%I (%I, tenant_id, note) '
                'select id, tenant_id, %I from public.%I where %I is not null '
                'on conflict (%I) do nothing',
                r.note_table, r.ref_column, r.old_column, r.parent, r.old_column, r.ref_column);
            execute format('alter table public.%I drop column %I', r.parent, r.old_column);
        end if;
    end loop;
end $$;
