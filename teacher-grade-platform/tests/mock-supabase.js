/* Stand-in for supabase-js: same call shapes app.js uses, backed by memory.
   It mimics the server's teacher filtering so the UI can be tested offline. */
(function () {
  var TEACHERS = {
    "test.teacher1@example.com": { id: "t1", password: "Teach1234!" },
    "test.teacher2@example.com": { id: "t2", password: "Teach1234!" }
  };
  var STUDENTS = [
    { id: "s1", teacher: "t1", full_name: "Ada Nguyen" },
    { id: "s2", teacher: "t1", full_name: "Marcus Webb" },
    { id: "s3", teacher: "t1", full_name: "Priya Raman" },
    { id: "s4", teacher: "t1", full_name: "Jonah Feldman" },
    { id: "s5", teacher: "t1", full_name: "Sofia Castillo" },
    { id: "s6", teacher: "t1", full_name: "Emmett Boyle" },
    { id: "s7", teacher: "t1", full_name: "Leila Haddad" },
    { id: "s8", teacher: "t1", full_name: "Owen Pritchard" },
    { id: "s9", teacher: "t2", full_name: "Diego Santos" },
    { id: "s10", teacher: "t2", full_name: "Hana Kimura" },
    { id: "s11", teacher: "t2", full_name: "Leo Fitzgerald" },
    { id: "s12", teacher: "t2", full_name: "Maya Thornton" },
    { id: "s13", teacher: "t2", full_name: "Rashid Karim" },
    { id: "s14", teacher: "t2", full_name: "Ingrid Solberg" },
    { id: "s15", teacher: "t2", full_name: "Caleb Mwangi" },
    { id: "s16", teacher: "t2", full_name: "Yuki Tanaka" }
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
    { id: "g10", student: "s4", subject: "Math", score: 64 },
    { id: "g11", student: "s4", subject: "Science", score: 72 },
    { id: "g12", student: "s4", subject: "English", score: 70 },
    { id: "g13", student: "s5", subject: "Math", score: 82 },
    { id: "g14", student: "s5", subject: "Science", score: 88 },
    { id: "g15", student: "s5", subject: "English", score: 91 },
    { id: "g16", student: "s6", subject: "Math", score: 77 },
    { id: "g17", student: "s6", subject: "Science", score: 59 },
    { id: "g18", student: "s6", subject: "English", score: 68 },
    { id: "g19", student: "s7", subject: "Math", score: 93 },
    { id: "g20", student: "s7", subject: "Science", score: 96 },
    { id: "g21", student: "s7", subject: "English", score: 89 },
    { id: "g22", student: "s8", subject: "Math", score: 58 },
    { id: "g23", student: "s8", subject: "Science", score: 63 },
    { id: "g24", student: "s8", subject: "English", score: 74 },
    { id: "g25", student: "s9", subject: "History", score: 84 },
    { id: "g26", student: "s9", subject: "Art", score: 91 },
    { id: "g27", student: "s10", subject: "History", score: 76 },
    { id: "g28", student: "s10", subject: "Art", score: 88 },
    { id: "g29", student: "s11", subject: "History", score: 69 },
    { id: "g30", student: "s11", subject: "Art", score: 73 },
    { id: "g31", student: "s12", subject: "History", score: 90 },
    { id: "g32", student: "s12", subject: "Art", score: 85 },
    { id: "g33", student: "s13", subject: "History", score: 62 },
    { id: "g34", student: "s13", subject: "Art", score: 78 },
    { id: "g35", student: "s14", subject: "History", score: 88 },
    { id: "g36", student: "s14", subject: "Art", score: 94 },
    { id: "g37", student: "s15", subject: "History", score: 73 },
    { id: "g38", student: "s15", subject: "Art", score: 67 },
    { id: "g39", student: "s16", subject: "History", score: 81 },
    { id: "g40", student: "s16", subject: "Art", score: 92 }
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
