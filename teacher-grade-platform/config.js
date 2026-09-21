// Public Supabase settings. The publishable (anon) key is meant to be public:
// row level security in the database is what keeps each teacher's data private.
window.APP_CONFIG = {
  SUPABASE_URL: "__SUPABASE_URL__",
  SUPABASE_ANON_KEY: "__SUPABASE_ANON_KEY__"
};
