create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null,
  hostel text not null,
  room_number text not null,
  enrollment_no text not null unique,
  contact_number text not null unique,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'suspended')),
  created_at timestamptz not null default timezone('utc'::text, now()),
  updated_at timestamptz not null default timezone('utc'::text, now())
);

-- Link grievances to the student profile who submitted it
alter table public.grievance
add column if not exists student_id uuid references public.profiles(id) on delete set null;

-- Make lookup_token_hash optional so new grievances no longer require a lookup code
alter table public.grievance
alter column lookup_token_hash drop not null;


-- Link grievances to the student profile who submitted it
alter table public.grievance
add column if not exists student_id uuid references public.profiles(id) on delete set null;

-- Make lookup_token_hash optional so new grievances no longer require a lookup code
alter table public.grievance
alter column lookup_token_hash drop not null;