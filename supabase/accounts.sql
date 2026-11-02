-- JobLink Africa member accounts, profiles and cloud-saved jobs.
-- Run once in Supabase SQL Editor.
create table if not exists public.joblink_profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 full_name text not null default '',
 phone text not null default '',
 career_interests text not null default '',
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
alter table public.joblink_profiles enable row level security;
drop policy if exists "Members read own profile" on public.joblink_profiles;
create policy "Members read own profile" on public.joblink_profiles for select to authenticated using (auth.uid()=id);
drop policy if exists "Members insert own profile" on public.joblink_profiles;
create policy "Members insert own profile" on public.joblink_profiles for insert to authenticated with check (auth.uid()=id);
drop policy if exists "Members update own profile" on public.joblink_profiles;
create policy "Members update own profile" on public.joblink_profiles for update to authenticated using (auth.uid()=id) with check (auth.uid()=id);
grant select,insert,update on public.joblink_profiles to authenticated;

create or replace function public.joblink_create_member_profile()
returns trigger language plpgsql security definer set search_path=public
as $$
begin
 insert into public.joblink_profiles(id,full_name)
 values(new.id,coalesce(new.raw_user_meta_data->>'full_name',''))
 on conflict(id) do nothing;
 return new;
end;
$$;
drop trigger if exists joblink_auth_user_profile on auth.users;
create trigger joblink_auth_user_profile after insert on auth.users
for each row execute function public.joblink_create_member_profile();

create table if not exists public.joblink_saved_jobs (
 user_id uuid not null references auth.users(id) on delete cascade,
 job_id uuid not null references public.jobs(id) on delete cascade,
 created_at timestamptz not null default now(),
 primary key(user_id,job_id)
);
create index if not exists joblink_saved_jobs_user_idx on public.joblink_saved_jobs(user_id,created_at desc);
alter table public.joblink_saved_jobs enable row level security;
drop policy if exists "Members read own saved jobs" on public.joblink_saved_jobs;
create policy "Members read own saved jobs" on public.joblink_saved_jobs for select to authenticated using(auth.uid()=user_id);
drop policy if exists "Members save own jobs" on public.joblink_saved_jobs;
create policy "Members save own jobs" on public.joblink_saved_jobs for insert to authenticated with check(auth.uid()=user_id and exists(select 1 from public.jobs j where j.id=job_id and j.status='published'));
drop policy if exists "Members remove own saved jobs" on public.joblink_saved_jobs;
create policy "Members remove own saved jobs" on public.joblink_saved_jobs for delete to authenticated using(auth.uid()=user_id);
grant select,insert,delete on public.joblink_saved_jobs to authenticated;
