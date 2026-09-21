"""Smoke tests: python -m unittest test_app -v"""

import os
import tempfile
import unittest

DB_FD, DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(DB_FD)
os.environ["TGP_DB"] = DB_PATH

import app as tgp  # noqa: E402  (must follow the TGP_DB assignment)


class PlatformTest(unittest.TestCase):

    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        tgp.init_db()
        tgp.app.config["TESTING"] = True
        self.client = tgp.app.test_client()

    # helpers ------------------------------------------------------------
    def register(self, email="t@school.edu", client=None):
        client = client or self.client
        return client.post("/register", data={
            "name": "Teacher", "email": email, "password": "pw123456"},
            follow_redirects=True)

    def make_course(self, name="Algebra I"):
        self.client.post("/courses", data={"name": name, "term": "Fall 2026"})
        with tgp.app.app_context():
            return tgp.sqlite3.connect(DB_PATH).execute(
                "SELECT id FROM courses WHERE name = ?", (name,)).fetchone()[0]

    def add_student(self, course_id, name="Ada Lovelace"):
        self.client.post("/courses/{}/students".format(course_id),
                         data={"name": name, "email": "ada@school.edu"})
        return tgp.sqlite3.connect(DB_PATH).execute(
            "SELECT id FROM students WHERE name = ?", (name,)).fetchone()[0]

    def add_assignment(self, course_id, title="Quiz 1", max_points=50):
        self.client.post("/courses/{}/assignments".format(course_id),
                         data={"title": title, "max_points": max_points,
                               "due_date": "2026-09-17"})
        return tgp.sqlite3.connect(DB_PATH).execute(
            "SELECT id FROM assignments WHERE title = ?", (title,)).fetchone()[0]

    # tests --------------------------------------------------------------
    def test_letter_grade_scale(self):
        self.assertEqual(
            [tgp.letter_grade(p) for p in (95, 85, 75, 65, 30, None)],
            ["A", "B", "C", "D", "F", "-"])

    def test_login_required(self):
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_register_then_see_courses(self):
        response = self.register()
        self.assertIn(b"My courses", response.data)

    def test_login_with_wrong_password_fails(self):
        self.register()
        self.client.post("/logout")
        response = self.client.post("/login", data={
            "email": "t@school.edu", "password": "nope"}, follow_redirects=True)
        self.assertIn(b"Wrong email or password", response.data)

    def test_grade_entry_computes_percent_and_letter(self):
        self.register()
        course_id = self.make_course()
        student_id = self.add_student(course_id)
        quiz_id = self.add_assignment(course_id, "Quiz 1", 50)
        homework_id = self.add_assignment(course_id, "Homework 1", 20)

        self.client.post("/courses/{}/grades".format(course_id), data={
            "g-{}-{}".format(student_id, quiz_id): "45",
            "g-{}-{}".format(student_id, homework_id): "18"})

        page = self.client.get("/courses/{}".format(course_id)).data
        self.assertIn(b"63/70", page)   # 45 + 18 out of 50 + 20
        self.assertIn(b"90.0%", page)   # 63/70
        self.assertIn(b"<td>A</td>", page)  # letter grade for 90%

    def test_blank_score_clears_the_grade(self):
        self.register()
        course_id = self.make_course()
        student_id = self.add_student(course_id)
        quiz_id = self.add_assignment(course_id)
        field = "g-{}-{}".format(student_id, quiz_id)

        self.client.post("/courses/{}/grades".format(course_id), data={field: "45"})
        self.client.post("/courses/{}/grades".format(course_id), data={field: ""})

        remaining = tgp.sqlite3.connect(DB_PATH).execute(
            "SELECT COUNT(*) FROM grades").fetchone()[0]
        self.assertEqual(remaining, 0)

    def test_score_above_max_points_is_rejected(self):
        self.register()
        course_id = self.make_course()
        student_id = self.add_student(course_id)
        quiz_id = self.add_assignment(course_id, "Quiz 1", 50)

        response = self.client.post(
            "/courses/{}/grades".format(course_id),
            data={"g-{}-{}".format(student_id, quiz_id): "500"},
            follow_redirects=True)

        self.assertIn(b"Skipped 1", response.data)
        self.assertEqual(tgp.sqlite3.connect(DB_PATH).execute(
            "SELECT COUNT(*) FROM grades").fetchone()[0], 0)

    def test_teacher_cannot_open_another_teachers_course(self):
        self.register("first@school.edu")
        course_id = self.make_course()
        self.client.post("/logout")
        self.register("second@school.edu")
        self.assertEqual(
            self.client.get("/courses/{}".format(course_id)).status_code, 404)

    def test_csv_export(self):
        self.register()
        course_id = self.make_course()
        student_id = self.add_student(course_id)
        quiz_id = self.add_assignment(course_id, "Quiz 1", 50)
        self.client.post("/courses/{}/grades".format(course_id),
                         data={"g-{}-{}".format(student_id, quiz_id): "45"})

        response = self.client.get("/courses/{}/export.csv".format(course_id))
        self.assertEqual(response.mimetype, "text/csv")
        body = response.data.decode()
        self.assertIn("Ada Lovelace", body)
        self.assertIn("Quiz 1 (/50)", body)
        self.assertIn("90.0", body)

    def test_deleting_assignment_removes_its_grades(self):
        self.register()
        course_id = self.make_course()
        student_id = self.add_student(course_id)
        quiz_id = self.add_assignment(course_id)
        self.client.post("/courses/{}/grades".format(course_id),
                         data={"g-{}-{}".format(student_id, quiz_id): "45"})
        self.client.post("/courses/{}/assignments/{}/delete".format(
            course_id, quiz_id))
        self.assertEqual(tgp.sqlite3.connect(DB_PATH).execute(
            "SELECT COUNT(*) FROM grades").fetchone()[0], 0)

    def test_partial_submit_leaves_other_scores_alone(self):
        self.register()
        course_id = self.make_course()
        student_id = self.add_student(course_id)
        quiz_id = self.add_assignment(course_id, "Quiz 1", 50)
        homework_id = self.add_assignment(course_id, "Homework 1", 20)
        self.client.post("/courses/{}/grades".format(course_id), data={
            "g-{}-{}".format(student_id, quiz_id): "45",
            "g-{}-{}".format(student_id, homework_id): "18"})

        # a submit that does not include the homework field must not clear it
        self.client.post("/courses/{}/grades".format(course_id), data={
            "g-{}-{}".format(student_id, quiz_id): "50"})

        stored = dict(tgp.sqlite3.connect(DB_PATH).execute(
            "SELECT assignment_id, points FROM grades").fetchall())
        self.assertEqual(stored, {quiz_id: 50.0, homework_id: 18.0})


if __name__ == "__main__":
    unittest.main()
