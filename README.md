# GradeAgent
Autonomous agent for evaluating Machine Learning assignments: students' Jupyter notebooks (`.ipynb`) or Python files (`.py`) are uploaded, graded against a rubric by a pluggable engine (open-source LLM or baseline heuristic), stored in a database and presented to the teacher in a dashboard.

## Features (draft)
- Upload UI (`frontend/`) with a teacher dashboard: totals, per-student rubric averages, submission list, proposed course score.
- Automatic extraction of **student, group, course, workshop** from the file, e.g. header lines (first markdown cell or leading comments):
  ```
  Student: Jane Doe
  Group: G1
  Course: ML101
  Workshop: W1
  ```
  or the file name `COURSE_WORKSHOP_GROUP_First_Last.ipynb`. Form fields override extracted values.
- New files are matched to existing students (case/order/punctuation-insensitive name: "Doe, Jane" = "jane doe").
- SQLite database via SQLAlchemy (`GRADEAGENT_DB` to change, e.g. PostgreSQL URL).
- Proposed course score = mean of the latest submission percentage per workshop; overall = mean over courses.

## Layout
```
backend/app/main.py        FastAPI app and REST API
backend/app/extraction.py  notebook/.py parsing + metadata extraction
backend/app/models.py      Student, Submission, CriterionScore
backend/app/rubric.py      default rubric
backend/app/stats.py       per-student statistics and course score
backend/app/engines/       grading engines (base, heuristic, ollama)
backend/tests/             pytest tests
frontend/                  static dashboard (served by the backend)
```

## Run
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload     # open http://localhost:8000
python -m pytest
```

## Grading engines
Select with `GRADEAGENT_ENGINE` (default `heuristic`) or the `engine` form field.
- `heuristic` – no dependencies; rough static checks, for demos/tests.
- `ollama` – any open-source model served by [Ollama](https://ollama.com): `ollama pull qwen2.5-coder:7b`, then `GRADEAGENT_ENGINE=ollama` (optional `OLLAMA_URL`, `OLLAMA_MODEL`).

To add your own model (vLLM, llama.cpp, Hugging Face...), subclass `GradingEngine` in `backend/app/engines/base.py`, implement `grade(code, text, rubric)` returning one `CriterionResult` per criterion, and register it in `backend/app/engines/__init__.py`.

## API
`POST /api/submissions`, `GET /api/submissions[/{id}]`, `GET /api/students[/{id}]`, `GET /api/rubric`.

## Status / TODO
Draft: no authentication, a single global rubric, no code execution sandbox. Next: per-course rubrics, teacher login, manual score overrides, exports, sandboxed notebook execution.
