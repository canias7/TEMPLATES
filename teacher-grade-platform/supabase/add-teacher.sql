-- ============================================================
-- Add a new teacher.
--
-- 1. Change the two lines marked EDIT below.
-- 2. Change the student names and grades at the bottom (or delete that
--    section to create the teacher with no students yet).
-- 3. Paste the whole file into the Supabase SQL Editor and press Run.
--
-- The new teacher can log in immediately and will see only the students
-- created here. Running it twice with the same email does not duplicate
-- the teacher; it just adds the students again.
-- ============================================================

do $$
declare
  new_email    text := 'teacher.carter@example.com';   -- EDIT: their email
  new_password text := 'Teach1234!';                   -- EDIT: their password
  new_teacher  uuid;
  sid          uuid;
begin
  select id into new_teacher from auth.users where email = new_email;

  if new_teacher is null then
    new_teacher := gen_random_uuid();
    insert into auth.users (
      instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      created_at, updated_at, raw_app_meta_data, raw_user_meta_data,
      confirmation_token, recovery_token, email_change_token_new, email_change)
    values (
      '00000000-0000-0000-0000-000000000000', new_teacher, 'authenticated',
      'authenticated', new_email, crypt(new_password, gen_salt('bf')),
      now(), now(), now(),
      '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb,
      '', '', '', '');
    insert into auth.identities (
      provider_id, user_id, identity_data, provider,
      last_sign_in_at, created_at, updated_at)
    values (
      new_teacher::text, new_teacher,
      json_build_object('sub', new_teacher::text, 'email', new_email,
                        'email_verified', true)::jsonb,
      'email', now(), now(), now());
    raise notice 'Created teacher %', new_email;
  else
    raise notice 'Teacher % already existed, adding students to them', new_email;
  end if;

  -- ---- their students and grades (edit or delete this section) ----
  insert into public.students (teacher_id, full_name) values (new_teacher, 'Nia Osei') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'Biology', 87), (sid, 'Chemistry', 91);

  insert into public.students (teacher_id, full_name) values (new_teacher, 'Tomas Reyes') returning id into sid;
  insert into public.grades (student_id, subject, score) values (sid, 'Biology', 74), (sid, 'Chemistry', 68);
end $$;
