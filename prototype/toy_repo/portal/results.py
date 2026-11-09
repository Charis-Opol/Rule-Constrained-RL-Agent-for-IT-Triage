"""Class results page."""


def class_results(db, class_id):
    students = db.query("SELECT id, name FROM students WHERE class_id = ? ORDER BY id", (class_id,))
    results = []
    for student in students:
        marks = db.query("SELECT course, mark FROM marks WHERE student_id = ? ORDER BY course", (student["id"],))
        results.append({"student": student["name"], "marks": {m["course"]: m["mark"] for m in marks}})
    return results
