from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Student, Submission


def _pct(s: Submission) -> float:
    return 100 * s.score / s.max_score if s.max_score else 0.0


def student_stats(student: Student) -> dict:
    """Per-course score: latest submission per workshop, averaged over workshops."""
    latest: dict[tuple[str, str], Submission] = {}
    for s in sorted(student.submissions, key=lambda s: (s.created_at, s.id)):
        latest[(s.course, s.workshop)] = s
    courses: dict[str, list[float]] = {}
    for (course, _), s in latest.items():
        courses.setdefault(course, []).append(_pct(s))
    criteria: dict[str, list[float]] = {}
    for s in latest.values():
        for c in s.criteria:
            criteria.setdefault(c.name, []).append(100 * c.score / c.max_score if c.max_score else 0)
    return {
        "id": student.id,
        "name": student.name,
        "group": student.group,
        "submissions": len(student.submissions),
        "courses": {c: round(mean(v), 1) for c, v in courses.items()},
        "proposed_score": round(mean(mean(v) for v in courses.values()), 1) if courses else None,
        "criteria_avg": {k: round(mean(v), 1) for k, v in criteria.items()},
        "history": [
            {"id": s.id, "course": s.course, "workshop": s.workshop, "percent": round(_pct(s), 1), "created_at": s.created_at.isoformat()}
            for s in sorted(student.submissions, key=lambda s: s.created_at)
        ],
    }


def overview(db: Session) -> dict:
    students = [student_stats(s) for s in db.scalars(select(Student).order_by(Student.name))]
    scores = [s["proposed_score"] for s in students if s["proposed_score"] is not None]
    return {
        "students": students,
        "totals": {
            "students": len(students),
            "submissions": sum(s["submissions"] for s in students),
            "mean_score": round(mean(scores), 1) if scores else None,
            "max_score": max(scores) if scores else None,
            "min_score": min(scores) if scores else None,
        },
    }
