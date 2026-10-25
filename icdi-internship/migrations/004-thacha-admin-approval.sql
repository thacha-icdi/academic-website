-- Run once in Supabase SQL Editor. Only Thacha's registered accounts may approve Admin requests.
begin;
create table if not exists public.admin_approvers(user_id uuid primary key references auth.users(id) on delete cascade);
alter table public.admin_approvers enable row level security;
revoke all on public.admin_approvers from anon, authenticated;
insert into public.admin_approvers(user_id)
select id from auth.users where lower(email) in ('thacha.l@cmu.ac.th','thacha.l@icdi.cmu.ac.th','adthalwn@gmail.com')
on conflict do nothing;
create or replace function public.can_approve_admin() returns boolean
language sql stable security definer set search_path='' as $$
select exists(select 1 from public.admin_approvers where user_id=auth.uid())
and exists(select 1 from auth.users where id=auth.uid() and email_confirmed_at is not null);
$$;
revoke all on function public.can_approve_admin() from public;
grant execute on function public.can_approve_admin() to authenticated;
create table if not exists public.admin_approval_history(
id uuid primary key default gen_random_uuid(),target_user uuid not null references auth.users(id),
reviewed_by uuid not null references auth.users(id), decision text not null check(decision in ('approved','rejected')),
reviewed_at timestamptz not null default now());
alter table public.admin_approval_history enable row level security;
revoke all on public.admin_approval_history from anon,authenticated;
create or replace function public.list_admin_requests()
returns table(user_id uuid,email text,full_name text,"position" text,department text,phone text,email_verified boolean,request_status text)
language plpgsql security definer set search_path='' as $$
begin
if not public.can_approve_admin() then raise exception 'Only Thacha Lawanna may approve Admin requests'; end if;
return query select u.id,u.email::text,u.raw_user_meta_data->>'full_name',u.raw_user_meta_data->>'position',
u.raw_user_meta_data->>'department',u.raw_user_meta_data->>'phone',u.email_confirmed_at is not null,
coalesce((select a.decision from public.admin_approval_history a where a.target_user=u.id order by a.reviewed_at desc limit 1),'pending')
from auth.users u where u.raw_user_meta_data->>'registration_type'='admin_request' order by u.created_at;
end $$;
create or replace function public.review_admin_request(target_id uuid,approve boolean)
returns void language plpgsql security definer set search_path='' as $$
declare target auth.users%rowtype;
begin
if not public.can_approve_admin() then raise exception 'Only Thacha Lawanna may approve Admin requests'; end if;
select * into target from auth.users where id=target_id for update;
if not found or target.raw_user_meta_data->>'registration_type' is distinct from 'admin_request' then raise exception 'Admin request not found'; end if;
if approve and target.email_confirmed_at is null then raise exception 'Applicant must verify email first'; end if;
if approve then
insert into public.staff(user_id) values(target_id) on conflict do nothing;
else
if exists(select 1 from public.admin_approvers where user_id=target_id) then raise exception 'Cannot revoke approver through this action'; end if;
delete from public.staff where user_id=target_id;
end if;
insert into public.admin_approval_history(target_user,reviewed_by,decision)
values(target_id,auth.uid(),case when approve then 'approved' else 'rejected' end);
end $$;
revoke all on function public.list_admin_requests() from public;
revoke all on function public.review_admin_request(uuid,boolean) from public;
grant execute on function public.list_admin_requests() to authenticated;
grant execute on function public.review_admin_request(uuid,boolean) to authenticated;
commit;
