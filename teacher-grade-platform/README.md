# Teacher Grade Platform

A minimal web app where a teacher logs in with email and password, sees only
the students assigned to them, and edits those students' grades. Changes save
to the database and survive a refresh.

- **Auth + database:** Supabase (free tier)
- **Hosting:** any static host — Vercel or GitHub Pages
- **Frontend:** plain HTML + JavaScript, no build step, no dependencies
- **Live URL:** _(filled in at deployment)_

## Test accounts

| Email | Password | Their students |
| --- | --- | --- |
| teacher.allen@example.com | Teach1234! | Ada Nguyen, Marcus Webb, Priya Raman |
| teacher.brooks@example.com | Teach1234! | Diego Santos, Hana Kimura, Leo Fitzgerald |

Both logins are **created automatically** by `supabase/setup.sql` — there is no
sign-up screen to click through and no account to make by hand. All student
names and grades are fictional.

## Setup

1. Create a free Supabase project.
2. Open the **SQL Editor**, paste all of `supabase/setup.sql`, press **Run**.
   That creates the tables, the security rules, both teacher logins, and the
   fake class data. It is safe to run more than once.
3. In **Project Settings → API**, copy the **Project URL** and the **anon /
   publishable key** into `config.js`.
4. Publish the folder to any static host.

### If step 2 reports a problem creating the logins

Some Supabase versions restrict writing to `auth.users` from SQL. Fallback:

1. Go to **Authentication → Users → Add user**.
2. Add `teacher.allen@example.com` with password `Teach1234!`, and tick
   **Auto Confirm User**. Repeat for `teacher.brooks@example.com`.
3. Run `supabase/setup.sql` again. It looks the teachers up by email, finds the
   ones you just made, and only adds the students and grades.

## How the teacher separation works

Each row in `students` carries a `teacher_id` pointing at a Supabase Auth user.
Row level security policies restrict every query to `teacher_id = auth.uid()`,
so a teacher cannot read or edit another teacher's data **even by editing the
JavaScript in their browser or calling the API directly**. The key in
`config.js` is public by design; the policies are what protect the data.

Only three policies exist — read students, read grades, update grades. Insert
and delete are not exposed through the app at all.

## Verified

Run against a local PostgreSQL 16 with Supabase's `auth` schema stubbed in, and
in Chromium against a stubbed client. Details and the exact commands are in
`tests/README.md`.

| Check | Result |
| --- | --- |
| `setup.sql` runs clean; creates 2 teachers, 6 students, 15 grades | pass |
| Password `Teach1234!` verifies; a wrong password does not | pass |
| Each teacher sees exactly their own 3 students | pass |
| Teacher A reads teacher B's grade row by its real id | 0 rows |
| Teacher A updates teacher B's grade row by its real id | 0 rows |
| Signed out with no session | 0 rows visible |
| A teacher edits their own student's grade | saved |
| Grade outside 0–100 is rejected | pass |
| Login screen first, wrong password refused, logout clears the screen | pass |

## Files

```
index.html              login screen and grade table
app.js                  login, logout, load students, save a grade
config.js               Supabase URL and publishable key
supabase/setup.sql      tables, security rules, teachers, fake class data
tests/isolation_test.sql  cross-teacher access proof, for the SQL editor
tests/ui_test.py          browser test of the interface
tests/mock-supabase.js    stubbed client so the UI runs without a project
backup-demo/            a no-accounts version of the same app (see its README)
```

## Deploying

The site is three static files, so any host works.

- **GitHub Pages:** publish a branch whose root holds `index.html`, `app.js`
  and `config.js`. No account needed beyond GitHub.
- **Vercel:** import the repository, set **Root Directory** to
  `teacher-grade-platform`, framework preset **Other**, leave build and output
  settings empty.
