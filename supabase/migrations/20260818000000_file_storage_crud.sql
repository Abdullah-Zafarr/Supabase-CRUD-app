-- Supabase File Storage + CRUD App
-- Apply with: supabase db push

create extension if not exists pgcrypto;

create table if not exists public.file_records (
  id uuid primary key default gen_random_uuid(),
  bucket_name text not null default 'documents',
  storage_path text not null unique,
  original_name text not null,
  uploaded_by text not null default 'terminal-user',
  owner_id uuid references auth.users(id) on delete set null,
  content_type text,
  size_bytes bigint,
  checksum_sha256 text,
  description text,
  status text not null default 'pending'
    check (status in ('pending', 'active', 'rejected')),
  validation_error text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists file_records_created_at_idx
  on public.file_records (created_at desc);
create index if not exists file_records_status_idx
  on public.file_records (status);

create or replace function public.set_file_records_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists set_file_records_updated_at on public.file_records;
create trigger set_file_records_updated_at
before update on public.file_records
for each row execute function public.set_file_records_updated_at();

-- Private bucket: files are only accessible through authenticated/service-side
-- Storage calls. The application uses the server-side service key.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'documents',
  'documents',
  false,
  10485760,
  array[
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'text/plain',
    'text/csv',
    'application/json'
  ]::text[]
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

alter table public.file_records enable row level security;

drop policy if exists "Users can read their own file records" on public.file_records;
create policy "Users can read their own file records"
on public.file_records for select to authenticated
using (owner_id = (select auth.uid()));

drop policy if exists "Users can insert their own file records" on public.file_records;
create policy "Users can insert their own file records"
on public.file_records for insert to authenticated
with check (owner_id = (select auth.uid()));

drop policy if exists "Users can update their own file records" on public.file_records;
create policy "Users can update their own file records"
on public.file_records for update to authenticated
using (owner_id = (select auth.uid()))
with check (owner_id = (select auth.uid()));

drop policy if exists "Users can delete their own file records" on public.file_records;
create policy "Users can delete their own file records"
on public.file_records for delete to authenticated
using (owner_id = (select auth.uid()));

grant select, insert, update, delete on public.file_records to authenticated;
grant all on public.file_records to service_role;

-- Storage policies for authenticated clients. The terminal app's service key
-- bypasses RLS; these policies keep the bucket safe if a user-facing client is
-- added later.
drop policy if exists "Users can read their own document objects" on storage.objects;
create policy "Users can read their own document objects"
on storage.objects for select to authenticated
using (
  bucket_id = 'documents'
  and owner_id = (select auth.uid()::text)
);

drop policy if exists "Users can upload document objects" on storage.objects;
create policy "Users can upload document objects"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'documents'
  and owner_id = (select auth.uid()::text)
);

drop policy if exists "Users can update their own document objects" on storage.objects;
create policy "Users can update their own document objects"
on storage.objects for update to authenticated
using (
  bucket_id = 'documents'
  and owner_id = (select auth.uid()::text)
)
with check (
  bucket_id = 'documents'
  and owner_id = (select auth.uid()::text)
);

drop policy if exists "Users can delete their own document objects" on storage.objects;
create policy "Users can delete their own document objects"
on storage.objects for delete to authenticated
using (
  bucket_id = 'documents'
  and owner_id = (select auth.uid()::text)
);

