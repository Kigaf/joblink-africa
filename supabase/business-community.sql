-- JobLink Africa Business Community
-- Run this migration in Supabase SQL Editor after the member accounts migration.
create table if not exists public.joblink_business_profiles (
 user_id uuid primary key references auth.users(id) on delete cascade,
 display_name text not null,
 category text not null,
 location text not null default '',
 business_name text not null default '',
 bio text not null default '',
 looking_for text not null default '',
 is_public boolean not null default true,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
alter table public.joblink_business_profiles enable row level security;
drop policy if exists "Members view public business profiles" on public.joblink_business_profiles;
create policy "Members view public business profiles" on public.joblink_business_profiles for select to authenticated using(is_public or auth.uid()=user_id);
drop policy if exists "Members create own business profile" on public.joblink_business_profiles;
create policy "Members create own business profile" on public.joblink_business_profiles for insert to authenticated with check(auth.uid()=user_id);
drop policy if exists "Members update own business profile" on public.joblink_business_profiles;
create policy "Members update own business profile" on public.joblink_business_profiles for update to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
grant select,insert,update on public.joblink_business_profiles to authenticated;

create table if not exists public.joblink_business_posts (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 post_type text not null check(post_type in ('Business idea','Looking for a partner','Seeking advice','Offering a service','Looking for a supplier')),
 category text not null,
 title text not null check(char_length(title) between 5 and 120),
 body text not null check(char_length(body) between 10 and 1800),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists joblink_business_posts_created_idx on public.joblink_business_posts(created_at desc);
alter table public.joblink_business_posts enable row level security;
drop policy if exists "Members read business posts" on public.joblink_business_posts;
create policy "Members read business posts" on public.joblink_business_posts for select to authenticated using(true);
drop policy if exists "Members publish own business posts" on public.joblink_business_posts;
create policy "Members publish own business posts" on public.joblink_business_posts for insert to authenticated with check(auth.uid()=user_id);
drop policy if exists "Members edit own business posts" on public.joblink_business_posts;
create policy "Members edit own business posts" on public.joblink_business_posts for update to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists "Members delete own business posts" on public.joblink_business_posts;
create policy "Members delete own business posts" on public.joblink_business_posts for delete to authenticated using(auth.uid()=user_id);
grant select,insert,update,delete on public.joblink_business_posts to authenticated;

create table if not exists public.joblink_business_connections (
 id uuid primary key default gen_random_uuid(),
 sender_id uuid not null references auth.users(id) on delete cascade,
 recipient_id uuid not null references auth.users(id) on delete cascade,
 post_id uuid references public.joblink_business_posts(id) on delete set null,
 message text not null check(char_length(message) between 5 and 700),
 status text not null default 'pending' check(status in ('pending','accepted','declined')),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 check(sender_id<>recipient_id)
);
create index if not exists joblink_business_connections_recipient_idx on public.joblink_business_connections(recipient_id,created_at desc);
create index if not exists joblink_business_connections_sender_idx on public.joblink_business_connections(sender_id,created_at desc);
alter table public.joblink_business_connections enable row level security;
drop policy if exists "Members view their business connection requests" on public.joblink_business_connections;
create policy "Members view their business connection requests" on public.joblink_business_connections for select to authenticated using(auth.uid()=sender_id or auth.uid()=recipient_id);
drop policy if exists "Members send business connection requests" on public.joblink_business_connections;
create policy "Members send business connection requests" on public.joblink_business_connections for insert to authenticated with check(auth.uid()=sender_id and exists(select 1 from public.joblink_business_profiles p where p.user_id=recipient_id and p.is_public));
drop policy if exists "Recipients respond to business connection requests" on public.joblink_business_connections;
create policy "Recipients respond to business connection requests" on public.joblink_business_connections for update to authenticated using(auth.uid()=recipient_id) with check(auth.uid()=recipient_id and status in ('accepted','declined'));
grant select,insert,update on public.joblink_business_connections to authenticated;