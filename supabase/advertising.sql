-- JobLink Africa advertising system. Run once in Supabase SQL Editor.
create table if not exists public.advertiser_requests (
 id uuid primary key default gen_random_uuid(),
 business_name text not null check (char_length(business_name) between 2 and 180),
 contact_name text not null check (char_length(contact_name) between 2 and 120),
 email text not null check (char_length(email) between 5 and 254),
 phone text not null default '',
 website text not null default '',
 ad_type text not null check (ad_type in ('Banner advert','Sponsored job listing','Recruitment campaign','Newsletter sponsorship')),
 placement text not null default 'Homepage, job pages and career advice',
 message text not null default '',
 status text not null default 'new' check (status in ('new','contacted','approved','declined')),
 created_at timestamptz not null default now()
);
create index if not exists advertiser_requests_created_idx on public.advertiser_requests(created_at desc);
alter table public.advertiser_requests enable row level security;
drop policy if exists "Public can submit advertiser requests" on public.advertiser_requests;
create policy "Public can submit advertiser requests" on public.advertiser_requests
 for insert to anon, authenticated with check (
 char_length(business_name) between 2 and 180 and char_length(contact_name) between 2 and 120
 and char_length(email) between 5 and 254 and ad_type in ('Banner advert','Sponsored job listing','Recruitment campaign','Newsletter sponsorship')
 and status='new'
);
drop policy if exists "Admins manage advertiser requests" on public.advertiser_requests;
create policy "Admins manage advertiser requests" on public.advertiser_requests
 for all to authenticated using (public.joblink_is_admin()) with check (public.joblink_is_admin());
grant insert on public.advertiser_requests to anon, authenticated;
grant select,update on public.advertiser_requests to authenticated;

create table if not exists public.advertisements (
 id uuid primary key default gen_random_uuid(),
 advertiser_name text not null check (char_length(advertiser_name) between 2 and 180),
 title text not null check (char_length(title) between 2 and 180),
 image_url text not null,
 destination_url text not null,
 placement text not null default 'all' check (placement in ('all','home','jobs','career')),
 status text not null default 'draft' check (status in ('draft','active','paused','expired')),
 starts_at date not null default current_date,
 ends_at date,
 alt_text text not null default '',
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 constraint ad_image_https check (image_url ~ '^https://'),
 constraint ad_destination_https check (destination_url ~ '^https://'),
 constraint ad_dates_valid check (ends_at is null or ends_at >= starts_at)
);
create index if not exists advertisements_active_idx on public.advertisements(status,starts_at,ends_at);
alter table public.advertisements enable row level security;
drop policy if exists "Public can view active advertisements" on public.advertisements;
create policy "Public can view active advertisements" on public.advertisements
 for select to anon, authenticated using (
 status='active' and starts_at <= current_date and (ends_at is null or ends_at >= current_date)
);
drop policy if exists "Admins manage advertisements" on public.advertisements;
create policy "Admins manage advertisements" on public.advertisements
 for all to authenticated using (public.joblink_is_admin()) with check (public.joblink_is_admin());
grant select on public.advertisements to anon, authenticated;
grant insert,update,delete,select on public.advertisements to authenticated;
drop trigger if exists advertisements_set_updated_at on public.advertisements;
create trigger advertisements_set_updated_at before update on public.advertisements
 for each row execute function public.joblink_set_updated_at();
