# Tests

## `isolation_test.sql`
Run in the Supabase SQL editor after `../supabase/setup.sql`. It signs in as
each teacher in turn and tries to read and overwrite the other teacher's data
by its real row id, bypassing the UI entirely. Expected answers are in the
comments: 8 students each, 0 rows visible, 0 rows updated across teachers.

Result when run against a local PostgreSQL 16 with the Supabase `auth` schema
stubbed in:

| Check | Result |
| --- | --- |
| Password `Teach1234!` verifies, a wrong one does not | pass |
| Test Teacher One sees 8 students / 24 grades, none of Teacher Two's | pass |
| Test Teacher One updates her own student's grade | 1 row |
| Test Teacher One reads Teacher Two's grade row by id | 0 rows |
| Test Teacher One updates Teacher Two's grade row by id | 0 rows |
| Test Teacher Two sees their own 8 students, data intact | pass |
| Signed out, no JWT | 0 rows visible |

## `ui_test.py`
Drives the real `index.html` and `app.js` in Chromium with `mock-supabase.js`
standing in for the Supabase client, so the interface can be checked without a
live project. Covers: login screen first, wrong password rejected, each teacher
seeing only their own students, saving a grade, rejecting a grade outside
0-100, and logout clearing the screen.

```bash
pip install playwright
python tests/ui_test.py
```
