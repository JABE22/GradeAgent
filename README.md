# GradeAgent
GradeAgent is a local-first prototype for collecting and evaluating Python course submissions.

## First-draft website
The standalone interface in `frontend/` accepts one or more Jupyter notebooks (`.ipynb`), lists them for the current browser session, counts submissions, and displays a placeholder score of 100/100 for each. It does not send files to a server or use a database; refreshing the page clears the list. This score is a UI placeholder, not an evaluation result.

Run the no-database website locally from the repository root:
```
python -m http.server 8000 --directory frontend
```
Then open http://localhost:8000.

## Existing grading API
The optional FastAPI backend supports notebook and Python file uploads, rubric-based heuristic or LLM grading, and a teacher-oriented student/submission API backed by SQLite (configurable via `GRADEAGENT_DB`). Starting this backend creates/uses the database; it is separate from the no-database first-draft website.

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
frontend/                  standalone first-draft upload UI
```

To run the optional API-backed version:
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload     # open http://localhost:8000
python -m pytest
```

## Product direction
The smallest useful evaluator should accept a notebook, associate it with a course/workshop and student, run transparent rubric checks, and return criterion-level feedback that a teacher can review. Nice next steps are manual score overrides, submission history, progress/feedback states, exports, and secure sandboxed code execution.

Keep courses configurable around shared course → lecture/workshop → activity structures, with course-specific rubrics and materials rather than course-specific application code. A materials library could index course-owned documents and link to reviewed external sources; an interactive practice area could embed small visualizations (for example, adjusting a decision tree’s depth and observing its splits). Theoretical learning can combine low-stakes retrieval quizzes, debugging/model-interpretation questions, and higher-stakes exams, with immediate explanations for practice and teacher review for consequential grading.

Useful reference projects (not drop-in equivalents):
- [JupyterLite](https://github.com/jupyterlite/jupyterlite) provides Jupyter interfaces in the browser with Web Worker/Pyodide kernels and browser storage; it is distributed as a static site. It is a reference for local practice and notebook access.
- [nbgrader](https://github.com/jupyter/nbgrader) provides Jupyter extensions and Python command-line tools for creating, releasing, collecting, autograding, and manually grading assignments. It is a reference for the assignment lifecycle.
- [Otter-Grader](https://github.com/ucbds-infra/otter-grader) is a Python autograding package for scripts and notebooks, including Docker-based grading and student-facing checks. It is a reference for separating practice checks from instructor grading.
- [PrairieLearn](https://github.com/PrairieLearn/PrairieLearn) is a TypeScript/Node assessment platform whose questions can combine HTML, JavaScript, and Python for interactive and autograded activities. It is a reference for quizzes and interactive assessments.

For GradeAgent, combine the relevant workflows instead of adopting one platform wholesale: keep AI rubric feedback advisory and evidence-based, distinguish public practice from private grading, and make local-save, submit, and sync states explicit.

## Grading engines
Select with `GRADEAGENT_ENGINE` (default `heuristic`) or the `engine` form field.
- `heuristic` – no dependencies; rough static checks, for demos/tests.
- `ollama` – any open-source model served by [Ollama](https://ollama.com): `ollama pull qwen2.5-coder:7b`, then `GRADEAGENT_ENGINE=ollama` (optional `OLLAMA_URL`, `OLLAMA_MODEL`).

To add your own model (vLLM, llama.cpp, Hugging Face...), subclass `GradingEngine` in `backend/app/engines/base.py`, implement `grade(code, text, rubric)` returning one `CriterionResult` per criterion, and register it in `backend/app/engines/__init__.py`.

## API
`POST /api/submissions`, `GET /api/submissions[/{id}]`, `GET /api/students[/{id}]`, `GET /api/rubric`.

## Status / TODO
Draft: no authentication, a single global rubric, no code execution sandbox. Next: per-course rubrics, teacher login, manual score overrides, exports, sandboxed notebook execution.
