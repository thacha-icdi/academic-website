begin;
create table if not exists public.letter_requests(
id uuid primary key default gen_random_uuid(),
student_id uuid not null references auth.users(id),
student_name text not null,student_number text not null,program text not null,phone text not null,
company text not null,position text not null,province text not null,address text not null,
recipient_name text not null,recipient_position text not null,contact_name text not null,contact_email text not null,contact_phone text not null,
start_date date not null,end_date date not null check(end_date>=start_date),
source_url text,notes text,status text not null default 'submitted' check(status in ('submitted','reviewing','issued','needs_revision')),
admin_notes text,created_at timestamptz not null default now()
);
alter table public.letter_requests enable row level security;
create policy letter_read on public.letter_requests for select to authenticated using(student_id=auth.uid() or public.is_staff());
create policy letter_submit on public.letter_requests for insert to authenticated with check(student_id=auth.uid() and status='submitted' and admin_notes is null);
create policy letter_review on public.letter_requests for update to authenticated using(public.is_staff()) with check(public.is_staff());
revoke all on public.letter_requests from anon,authenticated;
grant select,insert on public.letter_requests to authenticated;
grant update(status,admin_notes) on public.letter_requests to authenticated;
create index if not exists letter_student_idx on public.letter_requests(student_id);
commit;