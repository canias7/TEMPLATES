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
