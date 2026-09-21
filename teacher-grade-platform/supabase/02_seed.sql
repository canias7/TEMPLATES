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
