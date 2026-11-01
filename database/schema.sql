-- Applied through Supabase migration ai_signal_private_bookmarks.
-- Auth is shared with the existing project; application data is isolated by table and user.
create table public.ai_signal_bookmarks (
  user_id uuid not null references auth.users(id) on delete cascade,
  article_id text not null check (char_length(article_id) between 1 and 160),
  created_at timestamptz not null default now(),
  primary key (user_id, article_id)
);
alter table public.ai_signal_bookmarks enable row level security;
revoke all on public.ai_signal_bookmarks from anon;
grant select, insert, delete on public.ai_signal_bookmarks to authenticated;
create policy ai_signal_bookmarks_select on public.ai_signal_bookmarks
for select to authenticated using ((select auth.uid()) = user_id);
create policy ai_signal_bookmarks_insert on public.ai_signal_bookmarks
for insert to authenticated with check ((select auth.uid()) = user_id);
create policy ai_signal_bookmarks_delete on public.ai_signal_bookmarks
for delete to authenticated using ((select auth.uid()) = user_id);
