# Backup demo build

A no-accounts version of the same app, published as a Claude-hosted page while
the Supabase account was unavailable. Same two teachers, same fake students,
same editable grades, and edits persist in the page's own shared store.

Difference that matters: here the "only your own students" rule is enforced by
the page's query. In the real build (`../index.html` + `../supabase/setup.sql`)
it is enforced by the database itself through row level security, so it holds
even against someone editing the JavaScript in their browser.

Use the real build for submission; this exists so there is something working
and shareable if the Supabase step runs late.
