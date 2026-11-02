-- JobLink Africa Phase 1: job alerts and privacy-conscious analytics.
-- Run this migration in Supabase SQL Editor after deploying the matching website update.

create table if not exists public.job_alert_subscriptions (
  id uuid primary key default gen_random_uuid(),
  email text not null check (char_length(email) between 5 and 254),
  country text not null default '',
  category text not null default '',
  active boolean not null default true,
  created_at timestamptz not null default now(),
  constraint job_alert_email_lowercase check (email = lower(email))
);
create unique index if not exists job_alert_email_preferences_idx
  on public.job_alert_subscriptions (email, country, category);
create index if not exists job_alert_active_idx
  on public.job_alert_subscriptions (active, created_at desc);
alter table public.job_alert_subscriptions enable row level security;
drop policy if exists "Public can register job alerts" on public.job_alert_subscriptions;
create policy "Public can register job alerts" on public.job_alert_subscriptions
  for insert to anon, authenticated with check (
    active = true and email = lower(email)
    and char_length(email) between 5 and 254
    and char_length(country) <= 100 and char_length(category) <= 120
  );
drop policy if exists "Admins manage job alert subscriptions" on public.job_alert_subscriptions;
create policy "Admins manage job alert subscriptions" on public.job_alert_subscriptions
  for all to authenticated using (public.joblink_is_admin())
  with check (public.joblink_is_admin());
grant insert on public.job_alert_subscriptions to anon, authenticated;
grant select, update, delete on public.job_alert_subscriptions to authenticated;

create table if not exists public.site_events (
  id bigint generated always as identity primary key,
  event_type text not null check (event_type in ('page_view','job_open')),
  job_id uuid references public.jobs(id) on delete set null,
  page_path text not null default '/',
  created_at timestamptz not null default now()
);
create index if not exists site_events_created_idx on public.site_events(created_at desc);
create index if not exists site_events_job_idx on public.site_events(job_id, created_at desc);
alter table public.site_events enable row level security;
drop policy if exists "Visitors can record basic site events" on public.site_events;
create policy "Visitors can record basic site events" on public.site_events
  for insert to anon, authenticated with check (
    event_type in ('page_view','job_open')
    and char_length(page_path) between 1 and 300
  );
drop policy if exists "Admins can read site events" on public.site_events;
create policy "Admins can read site events" on public.site_events
  for select to authenticated using (public.joblink_is_admin());
grant insert on public.site_events to anon, authenticated;
grant select on public.site_events to authenticated;
