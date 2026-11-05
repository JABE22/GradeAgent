import json
import os

os.environ["GRADEAGENT_DB"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app import database
from app.extraction import extract, normalise_name

NB = {"cells": [
    {"cell_type": "markdown", "source": ["# Lab\n", "Student: Jane Doe\n", "Group: G1\n", "Course: ML101\n", "Workshop: W1\n"]},
    {"cell_type": "code", "source": ["def f(x):\n", "    '''Square.'''\n", "    return x * x\n", "print(f(2))"]},
]}


@pytest.fixture()
def client(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from app.main import app
    database.Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng, autoflush=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[database.get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_extract_notebook_metadata():
    ex = extract("x.ipynb", json.dumps(NB).encode())
    assert (ex.student, ex.group, ex.course, ex.workshop) == ("Jane Doe", "G1", "ML101", "W1")


def test_extract_from_filename():
    ex = extract("ML101_W2_G1_John_Smith.py", b"x = 1")
    assert (ex.course, ex.workshop, ex.group, ex.student) == ("ML101", "W2", "G1", "John Smith")


def test_name_matching():
    assert normalise_name("Doe, Jane") == normalise_name("jane  DOE")


def test_upload_associates_student_and_stats(client):
    for ws in ("W1", "W2"):
        r = client.post("/api/submissions", files={"file": ("a.ipynb", json.dumps(NB).encode())}, data={"workshop": ws})
        assert r.status_code == 200, r.text
    client.post("/api/submissions", files={"file": ("b.py", b"# Student: doe jane\nx=1")}, data={"course": "ML101", "workshop": "W1"})
    data = client.get("/api/students").json()
    assert data["totals"]["students"] == 1
    st = data["students"][0]
    assert st["submissions"] == 3 and st["proposed_score"] is not None
    assert client.get(f"/api/students/{st['id']}").status_code == 200


def test_errors(client):
    assert client.post("/api/submissions", files={"file": ("a.txt", b"x")}).status_code == 400
    assert client.post("/api/submissions", files={"file": ("a.py", b"x=1")}).status_code == 422
