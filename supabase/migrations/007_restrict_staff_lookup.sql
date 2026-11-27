-- 007_restrict_staff_lookup.sql
-- is_user_staff_of yalnızca çağıran kişinin üyesi olduğu kurum için yanıt verir;
-- böylece kimlikleri bilen biri başka kurumların personelini sorgulayamaz.
create or replace function public.is_user_staff_of(target_tenant_id uuid, target_user_id uuid)
returns boolean
language sql
security definer
stable
set search_path = ''
as $$
    select public.is_tenant_member(target_tenant_id) and exists (
        select 1 from public.memberships m
        where m.tenant_id = target_tenant_id
          and m.user_id = target_user_id
          and m.role in ('owner', 'coach')
    );
$$;
