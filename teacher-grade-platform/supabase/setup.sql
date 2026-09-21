-- ============================================================
-- Teacher Grade Platform - COMPLETE SETUP
-- Paste this whole file into the Supabase SQL Editor and click Run.
-- It creates the tables, the security rules, the two test teachers,
-- and their fake students and grades. Safe to run more than once.
-- ============================================================

-- Teacher Grade Platform schema.
-- Teachers are Supabase Auth users; row level security is what stops one
-- teacher from seeing another teacher's students.

create table if not exists public.students (
  id         uuid primary key default gen_random_uuid(),
  teacher_id uuid not null references auth.users (id) on delete cascade,
  full_name  text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.grades (
  id         uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students (id) on delete cascade,
  subject    text not null,
  score      numeric(5,2) not null check (score >= 0 and score <= 100),
  updated_at timestamptz not null default now(),
  unique (student_id, subject)
);

create index if not exists students_teacher_id_idx on public.students (teacher_id);
create index if not exists grades_student_id_idx on public.grades (student_id);

alter table public.students enable row level security;
alter table public.grades   enable row level security;

-- A teacher can read only their own students.
drop policy if exists "teachers read their own students" on public.students;
create policy "teachers read their own students"
  on public.students for select to authenticated
  using (teacher_id = (select auth.uid()));

-- A teacher can read only grades belonging to their own students.
drop policy if exists "teachers read their own students grades" on public.grades;
create policy "teachers read their own students grades"
  on public.grades for select to authenticated
  using (exists (select 1 from public.students s
                 where s.id = grades.student_id
                   and s.teacher_id = (select auth.uid())));

-- A teacher can change only grades belonging to their own students.
drop policy if exists "teachers update their own students grades" on public.grades;
create policy "teachers update their own students grades"
  on public.grades for update to authenticated
  using (exists (select 1 from public.students s
                 where s.id = grades.student_id
                   and s.teacher_id = (select auth.uid())))
  with check (exists (select 1 from public.students s
                      where s.id = grades.student_id
                        and s.teacher_id = (select auth.uid())));

-- No insert or delete policies: the app only reads and edits grades, so
-- nothing else is permitted through the public API.
-- Two test teachers with completely separate fake students and fake grades.
-- Re-running this resets the seeded students and grades to these values.
--
--   teacher.allen@example.com  / Teach1234!
--   teacher.brooks@example.com / Teach1234!

do $$
declare
  allen_id  uuid;
  brooks_id uuid;
  sid       uuid;
begin
  -- ---------------------------------------------------------------- users --
  select id into allen_id from auth.users where email = 'teacher.allen@example.com';
  if allen_id is null then
    allen_id := gen_random_uuid();
    insert into auth.users (
      instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      created_at, updated_at, raw_app_meta_data, raw_user_meta_data,
      confirmation_token, recovery_token, email_change_token_new, email_change)
    values (
      '00000000-0000-0000-0000-000000000000', allen_id, 'authenticated',
      'authenticated', 'teacher.allen@example.com',
      crypt('Teach1234!', gen_salt('bf')), now(), now(), now(),
      '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb,
      '', '', '', '');
    insert into auth.identities (
      provider_id, user_id, identity_data, provider,
      last_sign_in_at, created_at, updated_at)
    values (
      allen_id::text, allen_id,
      json_build_object('sub', allen_id::text,
                        'email', 'teacher.allen@example.com',
                        'email_verified', true)::jsonb,
      'email', now(), now(), now());
  end if;

  select id into brooks_id from auth.users where email = 'teacher.brooks@example.com';
  if brooks_id is null then
    brooks_id := gen_random_uuid();
    insert into auth.users (
      instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      created_at, updated_at, raw_app_meta_data, raw_user_meta_data,
      confirmation_token, recovery_token, email_change_token_new, email_change)
    values (
      '00000000-0000-0000-0000-000000000000', brooks_id, 'authenticated',
      'authenticated', 'teacher.brooks@example.com',
      crypt('Teach1234!', gen_salt('bf')), now(), now(), now(),
      '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb,
      '', '', '', '');
    insert into auth.identities (
      provider_id, user_id, identity_data, provider,
      last_sign_in_at, created_at, updated_at)
    values (
      brooks_id::text, brooks_id,
      json_build_object('sub', brooks_id::text,
                        'email', 'teacher.brooks@example.com',
                        'email_verified', true)::jsonb,
      'email', now(), now(), now());
  end if;

  -- ------------------------------------------------------ fake class data --
  delete from public.students where teacher_id in (allen_id, brooks_id);

  -- Ms. Allen's students (all fake)
  insert into public.students (teacher_id, full_name) values (allen_id, 'Ada Nguyen') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'Math', 88), (sid, 'Science', 92), (sid, 'English', 79);

  insert into public.students (teacher_id, full_name) values (allen_id, 'Marcus Webb') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'Math', 71), (sid, 'Science', 65), (sid, 'English', 83);

  insert into public.students (teacher_id, full_name) values (allen_id, 'Priya Raman') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'Math', 95), (sid, 'Science', 90), (sid, 'English', 97);

  -- Mr. Brooks's students (all fake, completely different people)
  insert into public.students (teacher_id, full_name) values (brooks_id, 'Diego Santos') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'History', 84), (sid, 'Art', 91);

  insert into public.students (teacher_id, full_name) values (brooks_id, 'Hana Kimura') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'History', 76), (sid, 'Art', 88);

  insert into public.students (teacher_id, full_name) values (brooks_id, 'Leo Fitzgerald') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'History', 69), (sid, 'Art', 73);
end $$;
