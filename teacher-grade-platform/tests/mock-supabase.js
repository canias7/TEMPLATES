/* Stand-in for supabase-js: same call shapes app.js uses, backed by memory.
   It mimics the server's teacher filtering so the UI can be tested offline. */
(function () {
  var TEACHERS = {
    "teacher.allen@example.com": { id: "allen", password: "Teach1234!" },
    "teacher.brooks@example.com": { id: "brooks", password: "Teach1234!" },
    "teacher.carter@example.com": { id: "carter", password: "Teach1234!" }
  };
  var STUDENTS = [
    { id: "s1", teacher: "allen", full_name: "Ada Nguyen" },
    { id: "s2", teacher: "allen", full_name: "Marcus Webb" },
    { id: "s3", teacher: "allen", full_name: "Priya Raman" },
    { id: "s4", teacher: "brooks", full_name: "Diego Santos" },
    { id: "s5", teacher: "brooks", full_name: "Hana Kimura" },
    { id: "s6", teacher: "brooks", full_name: "Leo Fitzgerald" },
    { id: "s7", teacher: "carter", full_name: "Nia Osei" },
    { id: "s8", teacher: "carter", full_name: "Tomas Reyes" }
  ];
  var GRADES = [
    { id: "g1", student: "s1", subject: "Math", score: 88 },
    { id: "g2", student: "s1", subject: "Science", score: 92 },
    { id: "g3", student: "s1", subject: "English", score: 79 },
    { id: "g4", student: "s2", subject: "Math", score: 71 },
    { id: "g5", student: "s2", subject: "Science", score: 65 },
    { id: "g6", student: "s2", subject: "English", score: 83 },
    { id: "g7", student: "s3", subject: "Math", score: 95 },
    { id: "g8", student: "s3", subject: "Science", score: 90 },
    { id: "g9", student: "s3", subject: "English", score: 97 },
    { id: "g10", student: "s4", subject: "History", score: 84 },
    { id: "g11", student: "s4", subject: "Art", score: 91 },
    { id: "g12", student: "s5", subject: "History", score: 76 },
    { id: "g13", student: "s5", subject: "Art", score: 88 },
    { id: "g14", student: "s6", subject: "History", score: 69 },
    { id: "g15", student: "s6", subject: "Art", score: 73 },
    { id: "g16", student: "s7", subject: "Biology", score: 87 },
    { id: "g17", student: "s7", subject: "Chemistry", score: 91 },
    { id: "g18", student: "s8", subject: "Biology", score: 74 },
    { id: "g19", student: "s8", subject: "Chemistry", score: 68 }
  ];

  var session = null;
  window.__mockState = { grades: GRADES };

  function makeClient() {
    return {
      auth: {
        getSession: function () {
          return Promise.resolve({ data: { session: session } });
        },
        signInWithPassword: function (creds) {
          var teacher = TEACHERS[creds.email];
          if (!teacher || teacher.password !== creds.password) {
            return Promise.resolve({ error: { message: "Invalid login credentials" } });
          }
          session = { user: { email: creds.email, id: teacher.id } };
          return Promise.resolve({ error: null });
        },
        signOut: function () { session = null; return Promise.resolve({}); }
      },
      from: function (table) {
        return {
          select: function () {
            return {
              order: function () {
                if (!session) return Promise.resolve({ data: [], error: null });
                var mine = STUDENTS.filter(function (s) { return s.teacher === session.user.id; });
                var rows = mine.map(function (s) {
                  return {
                    id: s.id,
                    full_name: s.full_name,
                    grades: GRADES.filter(function (g) { return g.student === s.id; })
                      .map(function (g) { return { id: g.id, subject: g.subject, score: g.score }; })
                  };
                }).sort(function (a, b) { return a.full_name.localeCompare(b.full_name); });
                return Promise.resolve({ data: rows, error: null });
              }
            };
          },
          update: function (patch) {
            return {
              eq: function (_column, value) {
                var grade = GRADES.filter(function (g) { return g.id === value; })[0];
                // server-side ownership check, same as the row level security policy
                var owner = grade && STUDENTS.filter(function (s) { return s.id === grade.student; })[0];
                if (!session || !owner || owner.teacher !== session.user.id) {
                  return Promise.resolve({ error: { message: "row level security blocked this" } });
                }
                grade.score = patch.score;
                return Promise.resolve({ error: null });
              }
            };
          }
        };
      }
    };
  }

  window.supabase = { createClient: makeClient };
})();
