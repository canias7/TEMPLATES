-- Proof that teachers cannot reach each other's data.
-- Run in the Supabase SQL editor AFTER setup.sql. Every answer below should
-- match the comment next to it.

\set QUIET on
select id as allen  from auth.users where email = 'teacher.allen@example.com'  \gset
select id as brooks from auth.users where email = 'teacher.brooks@example.com' \gset
select g.id as brooks_grade from public.grades g
  join public.students s on s.id = g.student_id
  where s.full_name = 'Diego Santos' and g.subject = 'Art' \gset
\set QUIET off

set role authenticated;

-- Acting as Ms. Allen
select set_config('request.jwt.claim.sub', :'allen', false);
select count(*) as allen_students from public.students;   -- 3
select count(*) as allen_grades   from public.grades;     -- 9

-- Allen tries to read and edit one of Mr. Brooks's grades by its real id
select count(*) as brooks_row_visible_to_allen
  from public.grades where id = :'brooks_grade';          -- 0
with attempt as (
  update public.grades set score = 0 where id = :'brooks_grade' returning 1)
select count(*) as brooks_row_updated_by_allen from attempt;  -- 0

-- Acting as Mr. Brooks
select set_config('request.jwt.claim.sub', :'brooks', false);
select count(*) as brooks_students from public.students;  -- 3
select score as diego_art_untouched from public.grades g
  join public.students s on s.id = g.student_id
  where s.full_name = 'Diego Santos' and g.subject = 'Art';   -- 91

-- Signed out entirely
select set_config('request.jwt.claim.sub', '', false);
select count(*) as visible_when_signed_out from public.students;  -- 0

reset role;
