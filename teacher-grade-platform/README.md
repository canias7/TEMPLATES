# Teacher Grade Platform

A minimal gradebook web app for teachers: create courses, add students and
assignments, enter scores in one grid, and get per-student and class averages
with letter grades. Flask + SQLite, server-rendered HTML, no build step.

## Run it

```bash
cd teacher-grade-platform
pip install -r requirements.txt
python seed.py          # optional: demo course with data
python app.py           # http://127.0.0.1:5000
```

Register your own account at `/register`, or log in with the seeded demo
account: **demo@school.edu / demo1234**.

## Tests

```bash
python -m unittest test_app -v     # 11 tests, uses a temporary database
```

## What it does

| Feature | Where |
| --- | --- |
| Teacher register / log in / log out | `/register`, `/login` |
| Create and delete courses | `/` |
| Add and remove students | course page |
| Add and delete assignments (title, max points, due date) | course page |
| Enter or edit every score in one grid, saved in a single submit | course page |
| Per-student total, percentage and letter grade | course page + `/courses/<id>/students/<id>` |
| Class average | course page |
| CSV export of the gradebook | `/courses/<id>/export.csv` |

## Design notes

- **Percentages only count graded work.** A student's percent is their earned
  points over the points of the assignments they actually have a score for, so
  an assignment nobody has been graded on yet never drags an average down.
- **Blank means "not graded yet."** Clearing a box in the grid deletes the
  stored score rather than recording a zero. A submit that omits a field
  entirely leaves that score untouched.
- **Scores are validated** against the assignment's max points; anything
  out of range or non-numeric is skipped and reported back to the teacher.
- **Each teacher only sees their own courses** — every course, student,
  assignment and grade route checks ownership and returns 404 otherwise.
- **Deletes cascade** (SQLite foreign keys are on), so removing a course,
  student or assignment cleans up its grades.
- Letter scale is the standard 90/80/70/60 cut-off.

## Layout

```
app.py          all routes and grade logic (~400 lines)
schema.sql      teachers, courses, students, assignments, grades
seed.py         demo data
test_app.py     smoke tests
templates/      base, login, register, courses, course (gradebook), student
static/style.css
```

## Not included

Kept out deliberately to stay small: student logins, weighted grading
categories, attendance, and password reset. `app.secret_key` and the dev server
are development defaults — set `TGP_SECRET` and run behind a real WSGI server
before using this anywhere real.
