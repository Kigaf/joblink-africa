-- JobLink Africa learning resources: run once in Supabase SQL Editor.
create table if not exists public.learning_resources (
 id uuid primary key default gen_random_uuid(),
 title text not null check (char_length(title) between 2 and 180),
 level text not null,
 subject text not null,
 resource_type text not null default 'notes' check (resource_type in ('exam','assignment','notes','scheme','lesson_plan')),\n class_name text not null default '',\n term text check (term is null or term in ('Term 1','Term 2','Term 3')),\n academic_year integer check (academic_year is null or academic_year between 2000 and 2100),\n description text not null default '',
 price numeric(10,2) not null default 0 check (price >= 0),
 file_path text not null unique,
 status text not null default 'draft' check (status in ('draft','published','archived')),
 created_by uuid references auth.users(id) on delete set null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists learning_resources_public_idx on public.learning_resources(status,created_at desc);
alter table public.learning_resources enable row level security;
drop policy if exists "Public read published learning resources" on public.learning_resources;
create policy "Public read published learning resources" on public.learning_resources for select to anon,authenticated using(status='published');
drop policy if exists "Admins manage learning resources" on public.learning_resources;
create policy "Admins manage learning resources" on public.learning_resources for all to authenticated using(public.joblink_is_admin()) with check(public.joblink_is_admin());
grant select on public.learning_resources to anon,authenticated;
grant insert,update,delete on public.learning_resources to authenticated;
drop trigger if exists learning_resources_set_updated_at on public.learning_resources;
create trigger learning_resources_set_updated_at before update on public.learning_resources for each row execute function public.joblink_set_updated_at();

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('learning-pdfs','learning-pdfs',false,26214400,array['application/pdf'])
on conflict(id) do update set public=false,file_size_limit=26214400,allowed_mime_types=array['application/pdf'];
drop policy if exists "Admins upload learning PDFs" on storage.objects;
create policy "Admins upload learning PDFs" on storage.objects for insert to authenticated with check(bucket_id='learning-pdfs' and public.joblink_is_admin());
drop policy if exists "Admins update learning PDFs" on storage.objects;
create policy "Admins update learning PDFs" on storage.objects for update to authenticated using(bucket_id='learning-pdfs' and public.joblink_is_admin()) with check(bucket_id='learning-pdfs' and public.joblink_is_admin());
drop policy if exists "Admins delete learning PDFs" on storage.objects;
create policy "Admins delete learning PDFs" on storage.objects for delete to authenticated using(bucket_id='learning-pdfs' and public.joblink_is_admin());
drop policy if exists "Read published free learning PDFs" on storage.objects;
create policy "Read published free learning PDFs" on storage.objects for select to anon,authenticated using(bucket_id='learning-pdfs' and exists(select 1 from public.learning_resources r where r.file_path=name and r.status='published' and r.price=0));
\n-- Safe migration for installations created before structured categories were added.\nalter table public.learning_resources add column if not exists resource_type text not null default 'notes';\nalter table public.learning_resources add column if not exists class_name text not null default '';\nalter table public.learning_resources add column if not exists term text;\nalter table public.learning_resources add column if not exists academic_year integer;\ncreate index if not exists learning_resources_category_idx on public.learning_resources(resource_type,level,subject,term,academic_year,status);\n