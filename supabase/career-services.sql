-- JobLink Africa career-service requests.
-- Run this migration in Supabase SQL Editor after supabase/schema.sql.
create table if not exists public.service_orders (
  id uuid primary key default gen_random_uuid(),
  customer_name text not null check (char_length(customer_name) between 2 and 120),
  customer_email text not null check (char_length(customer_email) between 5 and 254),
  customer_phone text not null check (char_length(customer_phone) between 7 and 30),
  service_type text not null check (service_type in (
    'CV Revamp',
    'Tailor-made CV + Cover Letter',
    'LinkedIn Profile Optimisation',
    'Interview Preparation',
    'International Application Package'
  )),
  target_role text not null check (char_length(target_role) between 2 and 180),
  target_country text not null default 'Not specified',
  job_ad_url text not null default '',
  instructions text not null default '',
  delivery_method text not null default 'Email',
  cv_storage_path text,
  payment_status text not null default 'pending' check (payment_status in ('pending','submitted','confirmed','rejected')),
  mpesa_reference text not null default '',
  order_status text not null default 'awaiting_payment' check (order_status in ('awaiting_payment','queued','in_progress','review','completed','cancelled')),
  admin_notes text not null default '',
  delivery_link text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists service_orders_created_idx on public.service_orders(created_at desc);
create index if not exists service_orders_status_idx on public.service_orders(order_status,payment_status);

alter table public.service_orders enable row level security;

drop policy if exists "Public can submit service requests" on public.service_orders;
create policy "Public can submit service requests" on public.service_orders
for insert to anon, authenticated
with check (
  char_length(customer_name) between 2 and 120
  and char_length(customer_email) between 5 and 254
  and char_length(customer_phone) between 7 and 30
  and service_type in ('CV Revamp','Tailor-made CV + Cover Letter','LinkedIn Profile Optimisation','Interview Preparation','International Application Package')
  and order_status = 'awaiting_payment'
  and payment_status = 'pending'
  and coalesce(mpesa_reference,'') = ''
  and coalesce(admin_notes,'') = ''
  and coalesce(delivery_link,'') = ''
  and (cv_storage_path is null or cv_storage_path ~ '^[0-9a-f-]{36}/cv[.](pdf|doc|docx)$')
);

drop policy if exists "Admins manage service requests" on public.service_orders;
create policy "Admins manage service requests" on public.service_orders
for all to authenticated
using (public.joblink_is_admin())
with check (public.joblink_is_admin());

grant insert on public.service_orders to anon, authenticated;
grant select, update on public.service_orders to authenticated;

drop trigger if exists service_orders_set_updated_at on public.service_orders;
create trigger service_orders_set_updated_at before update on public.service_orders
for each row execute function public.joblink_set_updated_at();

-- Private bucket: visitors can upload only their generated CV filename; only admins can read/delete.
insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types)
values (
  'career-service-cvs',
  'career-service-cvs',
  false,
  5242880,
  array['application/pdf','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document']
)
on conflict (id) do update set
  public = false,
  file_size_limit = 5242880,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Visitors can upload career service CVs" on storage.objects;
create policy "Visitors can upload career service CVs" on storage.objects
for insert to anon, authenticated
with check (
  bucket_id = 'career-service-cvs'
  and name ~ '^[0-9a-f-]{36}/cv[.](pdf|doc|docx)$'
);

drop policy if exists "Admins can read career service CVs" on storage.objects;
create policy "Admins can read career service CVs" on storage.objects
for select to authenticated
using (bucket_id = 'career-service-cvs' and public.joblink_is_admin());

drop policy if exists "Admins can delete career service CVs" on storage.objects;
create policy "Admins can delete career service CVs" on storage.objects
for delete to authenticated
using (bucket_id = 'career-service-cvs' and public.joblink_is_admin());
