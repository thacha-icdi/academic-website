-- For projects where schema.sql has already been installed; run once in SQL Editor.
alter table public.profiles add column if not exists earned_credits numeric check (earned_credits between 0 and 300);
alter table public.profiles add column if not exists nationality text;
