-- ============================================================
-- Teacher Grade Platform - COMPLETE SETUP
-- Paste this whole file into the Supabase SQL Editor and click Run.
-- Creates the tables, the security rules, two TEST teacher logins, and
-- their fictional students and grades. Safe to run more than once.
--
--   TEST ACCOUNT 1: test.teacher1@example.com  /  Teach1234!   (8 students)
--   TEST ACCOUNT 2: test.teacher2@example.com  /  Teach1234!   (8 students)
--
-- Every teacher, student and grade below is invented test data.
-- ============================================================

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

-- ------------------------------------------------------------
-- TEST DATA: two test teachers, 8 fictional students each.
-- ------------------------------------------------------------

do $$
declare
  t1 uuid;
  t2 uuid;
begin
  select id into t1 from auth.users where email = 'test.teacher1@example.com';
  if t1 is null then
    t1 := gen_random_uuid();
    insert into auth.users (
      instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      created_at, updated_at, raw_app_meta_data, raw_user_meta_data,
      confirmation_token, recovery_token, email_change_token_new, email_change)
    values (
      '00000000-0000-0000-0000-000000000000', t1, 'authenticated',
      'authenticated', 'test.teacher1@example.com', crypt('Teach1234!', gen_salt('bf')),
      now(), now(), now(),
      '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb,
      '', '', '', '');
    insert into auth.identities (
      provider_id, user_id, identity_data, provider,
      last_sign_in_at, created_at, updated_at)
    values (
      t1::text, t1,
      json_build_object('sub', t1::text, 'email', 'test.teacher1@example.com',
                        'email_verified', true)::jsonb,
      'email', now(), now(), now());
  end if;

  select id into t2 from auth.users where email = 'test.teacher2@example.com';
  if t2 is null then
    t2 := gen_random_uuid();
    insert into auth.users (
      instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      created_at, updated_at, raw_app_meta_data, raw_user_meta_data,
      confirmation_token, recovery_token, email_change_token_new, email_change)
    values (
      '00000000-0000-0000-0000-000000000000', t2, 'authenticated',
      'authenticated', 'test.teacher2@example.com', crypt('Teach1234!', gen_salt('bf')),
      now(), now(), now(),
      '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb,
      '', '', '', '');
    insert into auth.identities (
      provider_id, user_id, identity_data, provider,
      last_sign_in_at, created_at, updated_at)
    values (
      t2::text, t2,
      json_build_object('sub', t2::text, 'email', 'test.teacher2@example.com',
                        'email_verified', true)::jsonb,
      'email', now(), now(), now());
  end if;

  -- reset the seeded class lists so re-running gives the same result
  delete from public.students where teacher_id in (t1, t2);

  insert into public.students (teacher_id, full_name)
  select t1, name from unnest(array[
    'Ada Nguyen',
    'Marcus Webb',
    'Priya Raman',
    'Jonah Feldman',
    'Sofia Castillo',
    'Emmett Boyle',
    'Leila Haddad',
    'Owen Pritchard'
  ]) as name;

  insert into public.students (teacher_id, full_name)
  select t2, name from unnest(array[
    'Diego Santos',
    'Hana Kimura',
    'Leo Fitzgerald',
    'Maya Thornton',
    'Rashid Karim',
    'Ingrid Solberg',
    'Caleb Mwangi',
    'Yuki Tanaka'
  ]) as name;

  insert into public.grades (student_id, subject, score)
  select s.id, v.subject, v.score
  from (values
    ('Ada Nguyen', 'Math', 88),
    ('Ada Nguyen', 'Science', 92),
    ('Ada Nguyen', 'English', 79),
    ('Marcus Webb', 'Math', 71),
    ('Marcus Webb', 'Science', 65),
    ('Marcus Webb', 'English', 83),
    ('Priya Raman', 'Math', 95),
    ('Priya Raman', 'Science', 90),
    ('Priya Raman', 'English', 97),
    ('Jonah Feldman', 'Math', 64),
    ('Jonah Feldman', 'Science', 72),
    ('Jonah Feldman', 'English', 70),
    ('Sofia Castillo', 'Math', 82),
    ('Sofia Castillo', 'Science', 88),
    ('Sofia Castillo', 'English', 91),
    ('Emmett Boyle', 'Math', 77),
    ('Emmett Boyle', 'Science', 59),
    ('Emmett Boyle', 'English', 68),
    ('Leila Haddad', 'Math', 93),
    ('Leila Haddad', 'Science', 96),
    ('Leila Haddad', 'English', 89),
    ('Owen Pritchard', 'Math', 58),
    ('Owen Pritchard', 'Science', 63),
    ('Owen Pritchard', 'English', 74),
    ('Diego Santos', 'History', 84),
    ('Diego Santos', 'Art', 91),
    ('Hana Kimura', 'History', 76),
    ('Hana Kimura', 'Art', 88),
    ('Leo Fitzgerald', 'History', 69),
    ('Leo Fitzgerald', 'Art', 73),
    ('Maya Thornton', 'History', 90),
    ('Maya Thornton', 'Art', 85),
    ('Rashid Karim', 'History', 62),
    ('Rashid Karim', 'Art', 78),
    ('Ingrid Solberg', 'History', 88),
    ('Ingrid Solberg', 'Art', 94),
    ('Caleb Mwangi', 'History', 73),
    ('Caleb Mwangi', 'Art', 67),
    ('Yuki Tanaka', 'History', 81),
    ('Yuki Tanaka', 'Art', 92)
  ) as v(student, subject, score)
  join public.students s
    on s.full_name = v.student and s.teacher_id in (t1, t2);
end $$;
