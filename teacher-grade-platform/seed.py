"""Create a demo teacher, course, students, assignments and grades.

    python seed.py        # then log in as demo@school.edu / demo1234
"""

import os
import sqlite3

from werkzeug.security import generate_password_hash

import app as tgp

STUDENTS = ["Ada Lovelace", "Alan Turing", "Grace Hopper", "Katherine Johnson"]
ASSIGNMENTS = [("Homework 1", 20, "2026-09-10"),
               ("Quiz 1", 50, "2026-09-17"),
               ("Midterm", 100, "2026-10-01")]
SCORES = [[18, 44, 91], [20, 50, 96], [15, 38, 82], [12, None, 71]]


def main():
    tgp.init_db()
    db = sqlite3.connect(tgp.DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")

    db.execute("DELETE FROM teachers WHERE email = ?", ("demo@school.edu",))
    teacher_id = db.execute(
        "INSERT INTO teachers (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo Teacher", "demo@school.edu",
         generate_password_hash("demo1234"))).lastrowid
    course_id = db.execute(
        "INSERT INTO courses (teacher_id, name, term) VALUES (?, ?, ?)",
        (teacher_id, "Algebra I", "Fall 2026")).lastrowid

    student_ids = [db.execute(
        "INSERT INTO students (course_id, name, email) VALUES (?, ?, ?)",
        (course_id, name, name.split()[0].lower() + "@school.edu")).lastrowid
        for name in STUDENTS]
    assignment_ids = [db.execute(
        "INSERT INTO assignments (course_id, title, max_points, due_date) "
        "VALUES (?, ?, ?, ?)", (course_id, title, points, due)).lastrowid
        for title, points, due in ASSIGNMENTS]

    for student_id, row in zip(student_ids, SCORES):
        for assignment_id, points in zip(assignment_ids, row):
            if points is not None:
                db.execute("INSERT INTO grades (student_id, assignment_id, points) "
                           "VALUES (?, ?, ?)", (student_id, assignment_id, points))
    db.commit()
    db.close()
    print("Seeded {} -> log in as demo@school.edu / demo1234".format(tgp.DB_PATH))


if __name__ == "__main__":
    main()
