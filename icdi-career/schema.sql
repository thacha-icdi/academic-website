-- ICDI Career Hub: run once in Supabase SQL Editor. No service key in frontend.
begin;
create table public.career_profiles(user_id uuid primary key references auth.users(id) on delete cascade,full_name text not null check(length(full_name)<=150),active boolean not null default true,created_at timestamptz not null default now());
create table public.career_staff(user_id uuid primary key references auth.users(id) on delete cascade,role text not null check(role in ('manager','admin')));
create table public.career_memberships(user_id uuid primary key references auth.users(id) on delete cascade,member_type text not null check(member_type in ('student','alumni')),student_id text not null check(length(student_id) between 1 and 30),graduation_year int check(graduation_year between 1900 and 2700),file_path text not null,status text not null default 'pending' check(status in ('pending','approved','rejected')),submitted_at timestamptz not null default now(),reviewed_at timestamptz,reviewed_by uuid references auth.users(id) on delete set null,review_note text check(length(review_note)<=1000),check(member_type<>'alumni' or graduation_year is not null));
create table public.career_resumes(user_id uuid primary key references auth.users(id) on delete cascade,content jsonb not null default '{}'::jsonb check(jsonb_typeof(content)='object' and octet_length(content::text)<=65000),updated_at timestamptz not null default now());
create table public.career_portfolios(id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id) on delete cascade,title text not null check(length(title) between 1 and 150),description text check(length(description)<=3000),url text check(url is null or (url ~ '^https?://' and length(url)<=1000)),file_path text,file_name text,created_at timestamptz not null default now(),check(url is not null or file_path is not null));
create table public.career_saved_jobs(user_id uuid not null references auth.users(id) on delete cascade,job_id text not null check(length(job_id)<=200),snapshot jsonb not null check(jsonb_typeof(snapshot)='object' and octet_length(snapshot::text)<=20000),created_at timestamptz not null default now(),primary key(user_id,job_id));
create table public.career_audit(id bigint generated always as identity primary key,actor_id uuid references auth.users(id) on delete set null,target_id uuid references auth.users(id) on delete set null,action text not null,details jsonb,created_at timestamptz not null default now());
create table public.career_jobs(id uuid primary key default gen_random_uuid(),title text not null check(length(title) between 1 and 200),company text not null check(length(company) between 1 and 200),location text not null check(length(location)<=200),url text not null check(url ~ '^https://'),role_ids integer[] not null check(cardinality(role_ids)>0 and role_ids <@ array[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29]),level text not null default 'unspecified' check(level in ('entry','experienced','unspecified')),is_active boolean not null default true,created_at timestamptz not null default now());
create function public.career_is_staff() returns boolean language sql stable security definer set search_path='' as $$ select exists(select 1 from public.career_staff s join public.career_profiles p using(user_id) where s.user_id=auth.uid() and p.active); $$;
create function public.career_is_admin() returns boolean language sql stable security definer set search_path='' as $$ select exists(select 1 from public.career_staff s join public.career_profiles p using(user_id) where s.user_id=auth.uid() and s.role='admin' and p.active); $$;
create function public.career_verified() returns boolean language sql stable security definer set search_path='' as $$ select exists(select 1 from public.career_profiles p where p.user_id=auth.uid() and p.active and (public.career_is_staff() or exists(select 1 from public.career_memberships m where m.user_id=p.user_id and m.status='approved'))); $$;
create function public.career_new_user() returns trigger language plpgsql security definer set search_path='' as $$ begin insert into public.career_profiles(user_id,full_name) values(new.id,left(coalesce(new.raw_user_meta_data->>'full_name','ICDI member'),150)); return new; end; $$;
create trigger career_on_signup after insert on auth.users for each row execute function public.career_new_user();
-- Existing auth accounts can also use this application.
insert into public.career_profiles(user_id,full_name) select id,left(coalesce(raw_user_meta_data->>'full_name','ICDI member'),150) from auth.users on conflict do nothing;
create function public.career_touch_resume() returns trigger language plpgsql set search_path='' as $$ begin new.updated_at=now(); return new; end; $$;
create trigger career_resume_updated before insert or update on public.career_resumes for each row execute function public.career_touch_resume();
create function public.career_submit_membership(p_member_type text,p_student_id text,p_graduation_year int,p_file_path text) returns void language plpgsql security definer set search_path='' as $$
begin
 if auth.uid() is null or not exists(select 1 from public.career_profiles where user_id=auth.uid() and active) then raise exception 'Account unavailable'; end if;
 if exists(select 1 from public.career_memberships where user_id=auth.uid() and status in ('pending','approved')) then raise exception 'A pending or approved membership already exists'; end if;
 if split_part(p_file_path,'/',1)<>auth.uid()::text or not exists(select 1 from storage.objects where bucket_id='career-evidence' and name=p_file_path) then raise exception 'Evidence not found'; end if;
 insert into public.career_memberships(user_id,member_type,student_id,graduation_year,file_path) values(auth.uid(),p_member_type,p_student_id,p_graduation_year,p_file_path)
 on conflict(user_id) do update set member_type=excluded.member_type,student_id=excluded.student_id,graduation_year=excluded.graduation_year,file_path=excluded.file_path,status='pending',submitted_at=now(),reviewed_at=null,reviewed_by=null,review_note=null;
 insert into public.career_audit(actor_id,target_id,action) values(auth.uid(),auth.uid(),'membership_submitted');
end; $$;
create function public.career_review_membership(p_user_id uuid,p_status text,p_note text) returns void language plpgsql security definer set search_path='' as $$
begin
 if not public.career_is_staff() or p_user_id=auth.uid() then raise exception 'Not allowed'; end if;
 if p_status not in ('approved','rejected') or (p_status='rejected' and length(trim(coalesce(p_note,'')))=0) then raise exception 'Review status and note required'; end if;
 update public.career_memberships set status=p_status,reviewed_by=auth.uid(),reviewed_at=now(),review_note=p_note where user_id=p_user_id and status='pending';
 if not found then raise exception 'No pending membership'; end if;
 insert into public.career_audit(actor_id,target_id,action,details) values(auth.uid(),p_user_id,'membership_'||p_status,jsonb_build_object('note',p_note));
end; $$;
create function public.career_set_staff(p_user_id uuid,p_role text) returns void language plpgsql security definer set search_path='' as $$
begin
 if not public.career_is_admin() or p_user_id=auth.uid() then raise exception 'Only an admin may change another user role'; end if;
 if p_role='member' then delete from public.career_staff where user_id=p_user_id;
 elsif p_role in ('admin','manager') then insert into public.career_staff(user_id,role) values(p_user_id,p_role) on conflict(user_id) do update set role=excluded.role;
 else raise exception 'Invalid role'; end if;
 insert into public.career_audit(actor_id,target_id,action,details) values(auth.uid(),p_user_id,'staff_role_changed',jsonb_build_object('role',p_role));
end; $$;
create function public.career_set_active(p_user_id uuid,p_active boolean) returns void language plpgsql security definer set search_path='' as $$
begin
 if not public.career_is_admin() or p_user_id=auth.uid() then raise exception 'Only an admin may change another account'; end if;
 update public.career_profiles set active=p_active where user_id=p_user_id;
 insert into public.career_audit(actor_id,target_id,action,details) values(auth.uid(),p_user_id,'account_status_changed',jsonb_build_object('active',p_active));
end; $$;
-- Every table is deny-by-default; clients cannot edit staff, active status or approvals.
alter table public.career_profiles enable row level security;
alter table public.career_staff enable row level security;
alter table public.career_memberships enable row level security;
alter table public.career_resumes enable row level security;
alter table public.career_portfolios enable row level security;
alter table public.career_saved_jobs enable row level security;
alter table public.career_audit enable row level security;
alter table public.career_jobs enable row level security;
revoke all on public.career_profiles,public.career_staff,public.career_memberships,public.career_resumes,public.career_portfolios,public.career_saved_jobs,public.career_audit,public.career_jobs from anon,authenticated;
grant select on public.career_profiles,public.career_staff,public.career_memberships to authenticated;
grant select,insert,update,delete on public.career_resumes,public.career_portfolios,public.career_saved_jobs to authenticated;
grant select on public.career_audit to authenticated;
grant select on public.career_jobs to anon,authenticated;
grant insert,update,delete on public.career_jobs to authenticated;
create policy career_profile_read on public.career_profiles for select to authenticated using(user_id=auth.uid() or public.career_is_staff());
create policy career_staff_read on public.career_staff for select to authenticated using(user_id=auth.uid() or public.career_is_staff());
create policy career_membership_read on public.career_memberships for select to authenticated using(user_id=auth.uid() or public.career_is_staff());
create policy career_resume_read on public.career_resumes for select to authenticated using(user_id=auth.uid());
create policy career_resume_insert on public.career_resumes for insert to authenticated with check(user_id=auth.uid() and public.career_verified());
create policy career_resume_update on public.career_resumes for update to authenticated using(user_id=auth.uid() and public.career_verified()) with check(user_id=auth.uid() and public.career_verified());
create policy career_resume_delete on public.career_resumes for delete to authenticated using(user_id=auth.uid());
create policy career_portfolio_read on public.career_portfolios for select to authenticated using(user_id=auth.uid());
create policy career_portfolio_insert on public.career_portfolios for insert to authenticated with check(user_id=auth.uid() and public.career_verified() and (file_path is null or split_part(file_path,'/',1)=auth.uid()::text));
create policy career_portfolio_update on public.career_portfolios for update to authenticated using(user_id=auth.uid() and public.career_verified()) with check(user_id=auth.uid() and public.career_verified() and (file_path is null or split_part(file_path,'/',1)=auth.uid()::text));
create policy career_portfolio_delete on public.career_portfolios for delete to authenticated using(user_id=auth.uid());
create policy career_saved_owner on public.career_saved_jobs for all to authenticated using(user_id=auth.uid()) with check(user_id=auth.uid() and public.career_verified());
create policy career_audit_admin on public.career_audit for select to authenticated using(public.career_is_admin());
create policy career_jobs_read on public.career_jobs for select using(is_active or public.career_is_staff());
create policy career_jobs_manage on public.career_jobs for all to authenticated using(public.career_is_staff()) with check(public.career_is_staff());
-- Narrow RPC permissions; Supabase defaults function execution to PUBLIC.
revoke all on function public.career_new_user(),public.career_touch_resume() from public,anon,authenticated;
revoke all on function public.career_is_staff(),public.career_is_admin(),public.career_verified(),public.career_submit_membership(text,text,int,text),public.career_review_membership(uuid,text,text),public.career_set_staff(uuid,text),public.career_set_active(uuid,boolean) from public,anon;
grant execute on function public.career_is_staff(),public.career_is_admin(),public.career_verified(),public.career_submit_membership(text,text,int,text),public.career_review_membership(uuid,text,text),public.career_set_staff(uuid,text),public.career_set_active(uuid,boolean) to authenticated;
-- Public job SELECT policy calls career_is_staff even for anonymous visitors.
grant execute on function public.career_is_staff() to anon;
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values
 ('career-evidence','career-evidence',false,10485760,array['application/pdf','image/png','image/jpeg']),
 ('career-portfolios','career-portfolios',false,10485760,array['application/pdf','image/png','image/jpeg']) on conflict(id) do nothing;
create policy career_evidence_insert on storage.objects for insert to authenticated with check(bucket_id='career-evidence' and (storage.foldername(name))[1]=auth.uid()::text and exists(select 1 from public.career_profiles where user_id=auth.uid() and active));
create policy career_evidence_read on storage.objects for select to authenticated using(bucket_id='career-evidence' and ((storage.foldername(name))[1]=auth.uid()::text or public.career_is_staff()));
create policy career_evidence_delete on storage.objects for delete to authenticated using(bucket_id='career-evidence' and (storage.foldername(name))[1]=auth.uid()::text and not exists(select 1 from public.career_memberships m where m.file_path=name));
create policy career_portfolio_file_insert on storage.objects for insert to authenticated with check(bucket_id='career-portfolios' and (storage.foldername(name))[1]=auth.uid()::text and public.career_verified());
create policy career_portfolio_file_read on storage.objects for select to authenticated using(bucket_id='career-portfolios' and (storage.foldername(name))[1]=auth.uid()::text);
create policy career_portfolio_file_delete on storage.objects for delete to authenticated using(bucket_id='career-portfolios' and (storage.foldername(name))[1]=auth.uid()::text);
commit;
-- AFTER signing up and confirming your own email, bootstrap the first admin:
-- insert into public.career_staff(user_id,role)
-- select id,'admin' from auth.users where email='YOUR_CONFIRMED_ADMIN_EMAIL'
-- on conflict(user_id) do update set role='admin';
