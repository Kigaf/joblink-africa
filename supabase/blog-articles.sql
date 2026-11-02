-- JobLink Africa blog articles. Run in Supabase SQL Editor.
create table if not exists public.blog_articles (
 id uuid primary key default gen_random_uuid(),
 title text not null check(char_length(title) between 5 and 180),
 slug text not null unique check(slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
 category text not null default 'Other',
 excerpt text not null check(char_length(excerpt) between 10 and 320),
 content text not null,
 author text not null default 'JobLink Africa Editorial Team',
 cover_image text not null default '',
 status text not null default 'draft' check(status in ('draft','published')),
 published_at timestamptz,
 created_by uuid references auth.users(id) on delete set null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists blog_articles_public_idx on public.blog_articles(status,published_at desc);
create or replace function public.blog_articles_set_updated_at()
returns trigger language plpgsql set search_path=public
as $$ begin new.updated_at=now(); if new.status='published' and (old.status is distinct from 'published' or new.published_at is null) then new.published_at=now(); end if; return new; end; $$;
drop trigger if exists blog_articles_updated_at on public.blog_articles;
create trigger blog_articles_updated_at before update on public.blog_articles for each row execute function public.blog_articles_set_updated_at();
alter table public.blog_articles enable row level security;
drop policy if exists "Anyone reads published blog articles" on public.blog_articles;
create policy "Anyone reads published blog articles" on public.blog_articles for select to anon,authenticated using(status='published');
drop policy if exists "Admins read all blog articles" on public.blog_articles;
create policy "Admins read all blog articles" on public.blog_articles for select to authenticated using(public.joblink_is_admin());
drop policy if exists "Admins insert blog articles" on public.blog_articles;
create policy "Admins insert blog articles" on public.blog_articles for insert to authenticated with check(public.joblink_is_admin());
drop policy if exists "Admins update blog articles" on public.blog_articles;
create policy "Admins update blog articles" on public.blog_articles for update to authenticated using(public.joblink_is_admin()) with check(public.joblink_is_admin());
drop policy if exists "Admins delete blog articles" on public.blog_articles;
create policy "Admins delete blog articles" on public.blog_articles for delete to authenticated using(public.joblink_is_admin());
grant select on public.blog_articles to anon,authenticated;
grant insert,update,delete on public.blog_articles to authenticated;