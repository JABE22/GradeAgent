from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now():
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True)  # normalised name
    name: Mapped[str] = mapped_column(String)
    group: Mapped[str] = mapped_column(String, default="")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course: Mapped[str] = mapped_column(String, index=True)
    workshop: Mapped[str] = mapped_column(String, index=True)
    filename: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String)
    score: Mapped[float] = mapped_column(Float, default=0)
    max_score: Mapped[float] = mapped_column(Float, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    student: Mapped[Student] = relationship(back_populates="submissions")
    criteria: Mapped[list["CriterionScore"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class CriterionScore(Base):
    __tablename__ = "criterion_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    name: Mapped[str] = mapped_column(String)
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float)
    feedback: Mapped[str] = mapped_column(Text, default="")
    submission: Mapped[Submission] = relationship(back_populates="criteria")
