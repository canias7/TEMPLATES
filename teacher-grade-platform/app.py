"""Teacher Grade Platform - a minimal gradebook for teachers.

Stack: Flask + SQLite (stdlib), server-rendered HTML. No build step.
Run with:  python app.py
"""

import csv
import io
import os
import sqlite3
from functools import wraps

from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("TGP_DB", os.path.join(BASE_DIR, "grades.db"))

app = Flask(__name__)
app.secret_key = os.environ.get("TGP_SECRET", "dev-secret-change-me")


# ---------------------------------------------------------------- database --

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tables if they do not exist yet."""
    with open(os.path.join(BASE_DIR, "schema.sql")) as fh:
        script = fh.read()
    db = sqlite3.connect(DB_PATH)
    try:
        db.executescript(script)
        db.commit()
    finally:
        db.close()


# ------------------------------------------------------------------- auth --

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "teacher_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_teacher():
    return {"teacher_name": session.get("teacher_name")}


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not (name and email and password):
            flash("Name, email and password are all required.")
        else:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO teachers (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                flash("That email is already registered.")
            else:
                session.clear()
                session["teacher_id"] = cur.lastrowid
                session["teacher_name"] = name
                return redirect(url_for("courses"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT * FROM teachers WHERE email = ?", (email,)
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["teacher_id"] = row["id"]
            session["teacher_name"] = row["name"]
            return redirect(url_for("courses"))
        flash("Wrong email or password.")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------------------- gradebook --

def letter_grade(percent):
    """Standard US letter scale."""
    if percent is None:
        return "-"
    if percent >= 90:
        return "A"
    if percent >= 80:
        return "B"
    if percent >= 70:
        return "C"
    if percent >= 60:
        return "D"
    return "F"


def owned_course(course_id):
    """Fetch a course, 404 unless it belongs to the logged-in teacher."""
    row = get_db().execute(
        "SELECT * FROM courses WHERE id = ? AND teacher_id = ?",
        (course_id, session["teacher_id"]),
    ).fetchone()
    if row is None:
        abort(404)
    return row


def build_gradebook(course_id):
    """Return (students, assignments, rows, class_average).

    A student's percentage only counts assignments they have a score for,
    so an ungraded assignment never drags an average down.
    """
    db = get_db()
    students = db.execute(
        "SELECT * FROM students WHERE course_id = ? ORDER BY name", (course_id,)
    ).fetchall()
    assignments = db.execute(
        "SELECT * FROM assignments WHERE course_id = ? ORDER BY id", (course_id,)
    ).fetchall()
    scored = db.execute(
        "SELECT g.student_id, g.assignment_id, g.points FROM grades g "
        "JOIN students s ON s.id = g.student_id WHERE s.course_id = ?",
        (course_id,),
    ).fetchall()
    scores = {(r["student_id"], r["assignment_id"]): r["points"] for r in scored}

    rows = []
    for student in students:
        cells, earned, possible = [], 0.0, 0.0
        for assignment in assignments:
            points = scores.get((student["id"], assignment["id"]))
            percent = None
            if points is not None and assignment["max_points"]:
                percent = round(points / assignment["max_points"] * 100, 1)
            cells.append({"assignment": assignment, "points": points,
                          "percent": percent})
            if points is not None:
                earned += points
                possible += assignment["max_points"]
        percent = round(earned / possible * 100, 1) if possible else None
        rows.append({"student": student, "cells": cells, "earned": earned,
                     "possible": possible, "percent": percent,
                     "letter": letter_grade(percent)})

    graded = [r["percent"] for r in rows if r["percent"] is not None]
    class_average = round(sum(graded) / len(graded), 1) if graded else None
    return students, assignments, rows, class_average


# ----------------------------------------------------------------- courses --

@app.route("/")
@login_required
def courses():
    rows = get_db().execute(
        "SELECT c.*, "
        "  (SELECT COUNT(*) FROM students s WHERE s.course_id = c.id) AS student_count, "
        "  (SELECT COUNT(*) FROM assignments a WHERE a.course_id = c.id) AS assignment_count "
        "FROM courses c WHERE c.teacher_id = ? ORDER BY c.name",
        (session["teacher_id"],),
    ).fetchall()
    return render_template("courses.html", courses=rows)


@app.route("/courses", methods=["POST"])
@login_required
def create_course():
    name = request.form.get("name", "").strip()
    term = request.form.get("term", "").strip()
    if not name:
        flash("Course name is required.")
    else:
        db = get_db()
        db.execute("INSERT INTO courses (teacher_id, name, term) VALUES (?, ?, ?)",
                   (session["teacher_id"], name, term))
        db.commit()
    return redirect(url_for("courses"))


@app.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def delete_course(course_id):
    owned_course(course_id)
    db = get_db()
    db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    db.commit()
    return redirect(url_for("courses"))


@app.route("/courses/<int:course_id>")
@login_required
def course_detail(course_id):
    course = owned_course(course_id)
    students, assignments, rows, class_average = build_gradebook(course_id)
    return render_template("course.html", course=course, students=students,
                           assignments=assignments, rows=rows,
                           class_average=class_average,
                           class_letter=letter_grade(class_average))


# ---------------------------------------------------------------- students --

@app.route("/courses/<int:course_id>/students", methods=["POST"])
@login_required
def add_student(course_id):
    owned_course(course_id)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name:
        flash("Student name is required.")
    else:
        db = get_db()
        db.execute("INSERT INTO students (course_id, name, email) VALUES (?, ?, ?)",
                   (course_id, name, email))
        db.commit()
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/courses/<int:course_id>/students/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(course_id, student_id):
    owned_course(course_id)
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ? AND course_id = ?",
               (student_id, course_id))
    db.commit()
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/courses/<int:course_id>/students/<int:student_id>")
@login_required
def student_report(course_id, student_id):
    course = owned_course(course_id)
    _students, _assignments, rows, class_average = build_gradebook(course_id)
    row = next((r for r in rows if r["student"]["id"] == student_id), None)
    if row is None:
        abort(404)
    return render_template("student.html", course=course, row=row,
                           class_average=class_average)


# ------------------------------------------------------------- assignments --

@app.route("/courses/<int:course_id>/assignments", methods=["POST"])
@login_required
def add_assignment(course_id):
    owned_course(course_id)
    title = request.form.get("title", "").strip()
    due_date = request.form.get("due_date", "").strip()
    try:
        max_points = float(request.form.get("max_points", "100"))
    except ValueError:
        max_points = 0.0
    if not title:
        flash("Assignment title is required.")
    elif max_points <= 0:
        flash("Max points must be a number greater than zero.")
    else:
        db = get_db()
        db.execute(
            "INSERT INTO assignments (course_id, title, max_points, due_date) "
            "VALUES (?, ?, ?, ?)", (course_id, title, max_points, due_date))
        db.commit()
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/courses/<int:course_id>/assignments/<int:assignment_id>/delete",
           methods=["POST"])
@login_required
def delete_assignment(course_id, assignment_id):
    owned_course(course_id)
    db = get_db()
    db.execute("DELETE FROM assignments WHERE id = ? AND course_id = ?",
               (assignment_id, course_id))
    db.commit()
    return redirect(url_for("course_detail", course_id=course_id))


# ------------------------------------------------------------------ grades --

@app.route("/courses/<int:course_id>/grades", methods=["POST"])
@login_required
def save_grades(course_id):
    """Save the whole gradebook grid in one submit.

    A blank box means "not graded yet" and removes any stored score.
    """
    owned_course(course_id)
    db = get_db()
    students, assignments, _rows, _avg = build_gradebook(course_id)
    saved, cleared, rejected = 0, 0, 0

    for student in students:
        for assignment in assignments:
            field = "g-{}-{}".format(student["id"], assignment["id"])
            if field not in request.form:
                continue  # not part of this submit; leave the stored score alone
            raw = request.form[field].strip()
            if raw == "":
                cur = db.execute(
                    "DELETE FROM grades WHERE student_id = ? AND assignment_id = ?",
                    (student["id"], assignment["id"]))
                cleared += cur.rowcount
                continue
            try:
                points = float(raw)
            except ValueError:
                rejected += 1
                continue
            if points < 0 or points > assignment["max_points"]:
                rejected += 1
                continue
            db.execute(
                "INSERT INTO grades (student_id, assignment_id, points) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT (student_id, assignment_id) "
                "DO UPDATE SET points = excluded.points",
                (student["id"], assignment["id"], points))
            saved += 1
    db.commit()

    flash("Saved {} score(s), cleared {}.".format(saved, cleared))
    if rejected:
        flash("Skipped {} entr(y/ies): must be a number between 0 and the "
              "assignment's max points.".format(rejected))
    return redirect(url_for("course_detail", course_id=course_id))


@app.route("/courses/<int:course_id>/export.csv")
@login_required
def export_csv(course_id):
    course = owned_course(course_id)
    _students, assignments, rows, _avg = build_gradebook(course_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Student", "Email"]
                    + ["{} (/{:g})".format(a["title"], a["max_points"])
                       for a in assignments]
                    + ["Total", "Percent", "Letter"])
    for row in rows:
        writer.writerow(
            [row["student"]["name"], row["student"]["email"]]
            + ["" if c["points"] is None else "{:g}".format(c["points"])
               for c in row["cells"]]
            + ["{:g}/{:g}".format(row["earned"], row["possible"]),
               "" if row["percent"] is None else row["percent"],
               row["letter"]])

    filename = "".join(ch if ch.isalnum() else "-" for ch in course["name"])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition":
                 'attachment; filename="{}-grades.csv"'.format(filename)})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
