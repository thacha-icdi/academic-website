-- Updates policies only. Does not assign Admin to any account.
begin;
alter table public.profiles enable row level security;
drop policy if exists profile_read on public.profiles;
create policy profile_read on public.profiles for select to authenticated using(id=auth.uid() or public.is_staff());
drop policy if exists profile_edit on public.profiles;
create policy profile_edit on public.profiles for update to authenticated using(id=auth.uid() or public.is_staff()) with check(id=auth.uid() or public.is_staff());
commit;
