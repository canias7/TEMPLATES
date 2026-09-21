# Teacher Grade Platform

A minimal web app where a teacher logs in with email and password, sees only
the students assigned to them, and edits those students' grades. Changes save
to the database and survive a page refresh.

- **Live URL:** _(filled in after deployment)_
- **Auth + database:** Supabase
- **Hosting:** Vercel (static site, free tier)
- **Frontend:** plain HTML + JavaScript, no build step

## Test accounts

| Email | Password | Their students |
| --- | --- | --- |
| teacher.allen@example.com | Teach1234! | Ada Nguyen, Marcus Webb, Priya Raman |
| teacher.brooks@example.com | Teach1234! | Diego Santos, Hana Kimura, Leo Fitzgerald |

All student names and grades are fake. Log in as one teacher, then the other:
each sees only their own students, which is enforced by the database itself.

## How the separation works

Each row in `students` carries a `teacher_id` pointing at a Supabase Auth user.
Row level security policies in `supabase/01_schema.sql` restrict every query to
`teacher_id = auth.uid()`, so a teacher cannot read or edit another teacher's
students or grades even by editing the JavaScript in their browser. The
publishable key in `config.js` is public by design; the policies are what
protect the data.

There are only three policies — read students, read grades, update grades.
No insert or delete is permitted through the app.

## Files

```
index.html            login screen and grade table
app.js                login, logout, load students, save a grade
config.js             Supabase URL and publishable key
supabase/01_schema.sql  tables, indexes, row level security policies
supabase/02_seed.sql    the two test teachers and their fake class data
```

## Redeploying

The site is static, so deployment is just uploading these files to Vercel.
If you connect this GitHub repository to Vercel instead, set the project's
**Root Directory** to `teacher-grade-platform`, framework preset **Other**,
and leave the build and output settings empty.
