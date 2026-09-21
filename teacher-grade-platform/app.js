/* Teacher Grade Platform - log in, see your own students, edit their grades. */

const client = window.supabase.createClient(
  window.APP_CONFIG.SUPABASE_URL,
  window.APP_CONFIG.SUPABASE_ANON_KEY
);

const el = (id) => document.getElementById(id);
const setStatus = (message) => { el("status").textContent = message || ""; };

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function showView(name) {
  el("login-view").classList.toggle("hidden", name !== "login");
  el("dashboard-view").classList.toggle("hidden", name !== "dashboard");
}

/* ---------------------------------------------------------------- data -- */

async function loadStudents() {
  // Row level security means this only ever returns the logged-in
  // teacher's own students, no matter what the browser asks for.
  const { data, error } = await client
    .from("students")
    .select("id, full_name, grades ( id, subject, score )")
    .order("full_name");

  if (error) {
    setStatus("Could not load students: " + error.message);
    return;
  }

  const rows = [];
  for (const student of data) {
    const grades = (student.grades || [])
      .sort((a, b) => a.subject.localeCompare(b.subject));

    if (grades.length === 0) {
      rows.push(
        "<tr><td>" + escapeHtml(student.full_name) +
        "</td><td colspan='3'>No grades yet</td></tr>"
      );
      continue;
    }
    for (const grade of grades) {
      rows.push(
        "<tr><td>" + escapeHtml(student.full_name) + "</td>" +
        "<td>" + escapeHtml(grade.subject) + "</td>" +
        "<td><input type='number' min='0' max='100' step='0.1' value='" +
        escapeHtml(grade.score) + "' data-grade-input='" + grade.id + "'></td>" +
        "<td><button data-save='" + grade.id + "'>Save</button></td></tr>"
      );
    }
  }
  el("rows").innerHTML = rows.join("") ||
    "<tr><td colspan='4'>No students assigned to you.</td></tr>";
}

async function saveGrade(gradeId) {
  const input = document.querySelector("[data-grade-input='" + gradeId + "']");
  const score = Number(input.value);

  if (input.value.trim() === "" || Number.isNaN(score) || score < 0 || score > 100) {
    setStatus("Grade must be a number between 0 and 100.");
    return;
  }

  const { error } = await client
    .from("grades")
    .update({ score: score, updated_at: new Date().toISOString() })
    .eq("id", gradeId);

  setStatus(error
    ? "Save failed: " + error.message
    : "Saved. It stays saved after you refresh the page.");
}

/* ---------------------------------------------------------------- auth -- */

async function showCurrentView() {
  const { data: { session } } = await client.auth.getSession();
  if (!session) {
    showView("login");
    return;
  }
  el("who").textContent = session.user.email;
  showView("dashboard");
  await loadStudents();
}

el("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Logging in...");
  const { error } = await client.auth.signInWithPassword({
    email: el("email").value.trim(),
    password: el("password").value
  });
  if (error) {
    setStatus("Login failed: " + error.message);
    return;
  }
  setStatus("");
  el("password").value = "";
  await showCurrentView();
});

el("logout").addEventListener("click", async () => {
  await client.auth.signOut();
  setStatus("");
  el("rows").innerHTML = "";
  showView("login");
});

el("rows").addEventListener("click", (event) => {
  const button = event.target.closest("[data-save]");
  if (button) saveGrade(button.dataset.save);
});

showCurrentView();
