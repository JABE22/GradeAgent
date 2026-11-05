from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import stats
from .database import Base, engine as db_engine, get_db
from .engines import ENGINES, get_engine
from .extraction import extract, normalise_name
from .models import CriterionScore, Student, Submission
from .rubric import DEFAULT_RUBRIC

Base.metadata.create_all(db_engine)

app = FastAPI(title="GradeAgent")
MAX_UPLOAD = 5 * 1024 * 1024


def _submission_json(s: Submission, with_content=False) -> dict:
    d = {
        "id": s.id, "student": s.student.name, "student_id": s.student_id, "group": s.student.group,
        "course": s.course, "workshop": s.workshop, "filename": s.filename, "engine": s.engine,
        "score": s.score, "max_score": s.max_score, "summary": s.summary, "created_at": s.created_at.isoformat(),
        "criteria": [{"name": c.name, "score": c.score, "max_score": c.max_score, "feedback": c.feedback} for c in s.criteria],
    }
    if with_content:
        d["content"] = s.content
    return d


@app.get("/api/rubric")
def rubric():
    return {"criteria": [c.__dict__ for c in DEFAULT_RUBRIC], "engines": list(ENGINES)}


@app.post("/api/submissions")
async def upload(
    file: UploadFile = File(...),
    student: str = Form(""), group: str = Form(""), course: str = Form(""), workshop: str = Form(""),
    engine: str = Form(""),
    db: Session = Depends(get_db),
):
    raw = await file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "File too large")
    try:
        ex = extract(file.filename or "", raw)
        grader = get_engine(engine or None)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    # explicit form values override extracted ones
    name = student.strip() or ex.student
    if not name:
        raise HTTPException(422, "Student name could not be extracted; please provide it")
    course_name = course.strip() or ex.course or "Unknown course"
    workshop_name = workshop.strip() or ex.workshop or "Unknown workshop"
    group_name = group.strip() or ex.group

    key = normalise_name(name)
    st = db.scalar(select(Student).where(Student.key == key))
    if st is None:
        st = Student(key=key, name=name, group=group_name)
        db.add(st)
    elif group_name and not st.group:
        st.group = group_name

    try:
        results = grader.grade(ex.code, ex.text, DEFAULT_RUBRIC)
    except Exception as exc:  # model backend unavailable, bad output, ...
        raise HTTPException(502, f"Grading engine '{grader.name}' failed: {exc}")
    sub = Submission(
        student=st, course=course_name, workshop=workshop_name, filename=file.filename, content=raw.decode("utf-8", "replace"),
        engine=grader.name, score=sum(r.score for r in results), max_score=sum(r.max_score for r in results),
        summary="; ".join(f"{r.name}: {r.score:g}/{r.max_score:g}" for r in results),
        criteria=[CriterionScore(name=r.name, score=r.score, max_score=r.max_score, feedback=r.feedback) for r in results],
    )
    db.add(sub)
    db.commit()
    return _submission_json(sub)


@app.get("/api/submissions")
def list_submissions(db: Session = Depends(get_db)):
    return [_submission_json(s) for s in db.scalars(select(Submission).order_by(Submission.created_at.desc()))]


@app.get("/api/submissions/{sid}")
def get_submission(sid: int, db: Session = Depends(get_db)):
    s = db.get(Submission, sid)
    if not s:
        raise HTTPException(404, "Not found")
    return _submission_json(s, with_content=True)


@app.get("/api/students")
def students(db: Session = Depends(get_db)):
    return stats.overview(db)


@app.get("/api/students/{stid}")
def student(stid: int, db: Session = Depends(get_db)):
    st = db.get(Student, stid)
    if not st:
        raise HTTPException(404, "Not found")
    return stats.student_stats(st)


_frontend = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=_frontend, html=True), name="frontend")
