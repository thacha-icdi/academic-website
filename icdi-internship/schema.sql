-- Run once in Supabase SQL Editor. No passwords or private keys belong in GitHub.
create table public.staff(user_id uuid primary key references auth.users(id) on delete cascade);
alter table public.staff enable row level security;
create policy staff_self on public.staff for select to authenticated using(user_id=auth.uid());
create function public.is_staff() returns boolean language sql stable security definer set search_path=public as $$ select exists(select 1 from public.staff where user_id=auth.uid()) $$;
revoke all on function public.is_staff() from public;
grant execute on function public.is_staff() to authenticated;
create table public.profiles(
 id uuid primary key references auth.users(id) on delete cascade,
 student_id text unique not null, full_name text not null, english_name text not null,
 phone text not null, program text not null, year integer check(year between 1 and 8),
 gpa numeric check(gpa between 0 and 4), advisor text, address text,
 emergency_name text, emergency_phone text, emergency_relation text,
 skills text, languages text, interests text, preferred_location text,
 start_date date, end_date date, required_hours integer check(required_hours>0),
 resume_url text, portfolio_url text, consent_at timestamptz not null,
 check(end_date>=start_date)
);
create table public.opportunities(
 id uuid primary key default gen_random_uuid(),title text not null,company text not null,
 location text not null,deadline date not null,skills text not null,
 allowance text,description text not null, active boolean not null default true
);
create table public.applications(
 id uuid primary key default gen_random_uuid(),
 student_id uuid not null references public.profiles(id) on delete cascade,
 opportunity_id uuid not null references public.opportunities(id),
 status text not null default 'submitted' check(status in ('submitted','reviewing','approved','rejected','completed')),
 feedback text,created_at timestamptz not null default now(),
 unique(student_id,opportunity_id)
);
create table public.work_logs(
 id uuid primary key default gen_random_uuid(),
 application_id uuid not null references public.applications(id),
 student_id uuid not null references public.profiles(id) on delete cascade,
 work_date date not null,hours numeric not null check(hours between .5 and 24),
 summary text not null check(length(summary) between 1 and 5000),report_url text,
 created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
alter table public.opportunities enable row level security;
alter table public.applications enable row level security;
alter table public.work_logs enable row level security;
create policy profile_read on public.profiles for select to authenticated using(id=auth.uid() or public.is_staff());
create policy profile_create on public.profiles for insert to authenticated with check(id=auth.uid());
create policy profile_edit on public.profiles for update to authenticated using(id=auth.uid()) with check(id=auth.uid());
create policy jobs_read on public.opportunities for select to anon,authenticated using(active=true);
create policy jobs_staff on public.opportunities for all to authenticated using(public.is_staff()) with check(public.is_staff());
create policy application_read on public.applications for select to authenticated using(student_id=auth.uid() or public.is_staff());
create policy application_create on public.applications for insert to authenticated with check(
 student_id=auth.uid() and status='submitted' and feedback is null
 and exists(select 1 from public.opportunities o where o.id=opportunity_id and o.active and o.deadline>=current_date)
);
create policy application_review on public.applications for update to authenticated using(public.is_staff()) with check(public.is_staff());
create policy logs_read on public.work_logs for select to authenticated using(student_id=auth.uid() or public.is_staff());
create policy logs_create on public.work_logs for insert to authenticated with check(
 student_id=auth.uid() and exists(select 1 from public.applications a
 where a.id=application_id and a.student_id=auth.uid() and a.status='approved')
);
grant select on public.opportunities to anon;
grant select,insert,update,delete on public.opportunities to authenticated;
grant select on public.staff to authenticated;
grant select,insert,update on public.profiles,public.applications to authenticated;
grant select,insert on public.work_logs to authenticated;
create index application_student_idx on public.applications(student_id);
create index logs_student_idx on public.work_logs(student_id);
-- Add coordinator AFTER they register and verify their email:
-- insert into public.staff(user_id) values ('USER_UUID_FROM_AUTH_USERS');
