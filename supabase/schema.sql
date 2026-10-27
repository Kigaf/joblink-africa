-- JobLink Africa Supabase schema. Run the entire file in Supabase SQL Editor.
-- Public visitors can only read published, non-expired listings. Only user IDs explicitly
-- inserted into public.admin_users can create/update/delete jobs.
create extension if not exists pgcrypto;

create table if not exists public.admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table if not exists public.jobs (
  id uuid primary key default gen_random_uuid(),
  title text not null check (char_length(title) between 2 and 180),
  company text not null check (char_length(company) between 2 and 180),
  country text not null,
  location text not null,
  category text not null,
  type text not null,
  mode text not null,
  experience text not null default '',
  salary text not null default 'Not provided',
  sponsor boolean not null default false,
  featured boolean not null default false,
  posted date not null default current_date,
  deadline date,
  source text not null,
  url text not null check (url ~ '^https://'),
  description text not null,
  requirements text not null default '',
  status text not null default 'draft' check (status in ('draft','published','expired')),
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists jobs_public_order_idx on public.jobs(status, featured desc, posted desc);
create index if not exists jobs_deadline_idx on public.jobs(deadline);

create or replace function public.joblink_is_admin()
returns boolean
language sql stable security definer
set search_path = public
as $$ select exists (select 1 from public.admin_users where user_id = auth.uid()); $$;
revoke all on function public.joblink_is_admin() from public;
grant execute on function public.joblink_is_admin() to anon, authenticated;

create or replace function public.joblink_set_updated_at()
returns trigger language plpgsql set search_path = public
as $$ begin new.updated_at = now(); return new; end; $$;
drop trigger if exists jobs_set_updated_at on public.jobs;
create trigger jobs_set_updated_at before update on public.jobs for each row execute function public.joblink_set_updated_at();

alter table public.jobs enable row level security;
alter table public.admin_users enable row level security;

drop policy if exists "Public reads published active jobs" on public.jobs;
create policy "Public reads published active jobs" on public.jobs for select to anon, authenticated
using (status = 'published' and (deadline is null or deadline >= current_date));
drop policy if exists "Admins read all jobs" on public.jobs;
create policy "Admins read all jobs" on public.jobs for select to authenticated using (public.joblink_is_admin());
drop policy if exists "Admins insert jobs" on public.jobs;
create policy "Admins insert jobs" on public.jobs for insert to authenticated with check (public.joblink_is_admin());
drop policy if exists "Admins update jobs" on public.jobs;
create policy "Admins update jobs" on public.jobs for update to authenticated using (public.joblink_is_admin()) with check (public.joblink_is_admin());
drop policy if exists "Admins delete jobs" on public.jobs;
create policy "Admins delete jobs" on public.jobs for delete to authenticated using (public.joblink_is_admin());
-- No direct policies are granted on admin_users; membership is managed only in SQL Editor.
revoke all on public.admin_users from anon, authenticated;
grant select on public.jobs to anon, authenticated;
grant insert, update, delete on public.jobs to authenticated;
