"""Class results page."""


def class_results(db, class_id):
    students = db.query("SELECT id, name FROM students WHERE class_id = ? ORDER BY id", (class_id,))
    marks = db.query("SELECT m.student_id, m.course, m.mark FROM marks m JOIN students s ON s.id = m.student_id "
                     "WHERE s.class_id = ? ORDER BY m.course", (class_id,))
    by_student = {}
    for m in marks:
        by_student.setdefault(m["student_id"], {})[m["course"]] = m["mark"]
    return [{"student": s["name"], "marks": by_student.get(s["id"], {})} for s in students]
