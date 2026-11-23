"""Learner-facing curriculum and approved exercise availability."""

from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Lesson, LessonVersion, Question, QuestionVersion, SQLExerciseVersion
from app.services.assessment import AssessmentError
from app.services.sql_grading import worker_supported
from content.schemas.models import Source
from scripts.validate_content import DOMAINS, PREREQUISITES, read_records


class LessonLink(BaseModel):
    ref: str
    title: str


class LessonDetail(LessonLink):
    topic_id: str
    body: str
    source_url: str


class TopicView(BaseModel):
    id: str
    title: str
    prerequisites: list[str]
    lessons: list[LessonLink]
    practice: bool
    diagnostic: bool


class DomainView(BaseModel):
    id: str
    title: str
    topics: list[TopicView]


class ExerciseView(BaseModel):
    id: str
    ref: str
    topic_id: str
    prompt: str
    difficulty: str
    dialect: str
    minimum_sqlite_version: str
    enabled: bool


def course(db: Session, root: Path) -> list[DomainView]:
    domains = read_records(root / "content/curriculum/topics.yaml", DOMAINS)
    prerequisites = read_records(root / "content/curriculum/prerequisites.yaml", PREREQUISITES)
    all_lessons = list(
        db.execute(
            select(Lesson.subtopic_id, LessonVersion)
            .join(Lesson, Lesson.id == LessonVersion.lesson_id)
            .order_by(Lesson.id, LessonVersion.version.desc())
        )
    )
    lesson_ids: set[str] = set()
    subtopic_lessons: dict[str, list[LessonLink]] = {}
    for topic_id, version in all_lessons:
        if version.lesson_id not in lesson_ids:
            lesson_ids.add(version.lesson_id)
            subtopic_lessons.setdefault(topic_id, []).append(
                LessonLink(ref=version.id, title=version.title)
            )
    available = set(
        db.execute(
            select(Question.subtopic_id, QuestionVersion.pool)
            .join(QuestionVersion, QuestionVersion.question_id == Question.id)
            .where(Question.type == "mcq")
            .distinct()
        )
    )
    return [
        DomainView(
            id=domain.id,
            title=domain.title,
            topics=[
                TopicView(
                    id=topic,
                    title=title,
                    lessons=subtopic_lessons.get(topic, []),
                    prerequisites=[
                        edge.prerequisite_id for edge in prerequisites if edge.subtopic_id == topic
                    ],
                    practice=(topic, "practice") in available,
                    diagnostic=(topic, "diagnostic") in available,
                )
                for topic, title in domain.subtopics.items()
            ],
        )
        for domain in domains
    ]


def lesson_detail(db: Session, ref: str) -> LessonDetail:
    row = db.execute(
        select(Lesson.subtopic_id, LessonVersion)
        .join(Lesson, Lesson.id == LessonVersion.lesson_id)
        .where(LessonVersion.id == ref)
    ).first()
    if row is None:
        raise AssessmentError("No reviewed lesson matches this reference.", "lesson_not_found", 404)
    topic, version = row
    source = Source.model_validate_json(version.source_ref)
    return LessonDetail(
        ref=version.id,
        topic_id=topic,
        title=version.title,
        body=version.body_markdown,
        source_url=str(source.factual_reference_url),
    )


def reviewed_exercises(db: Session) -> list[ExerciseView]:
    from app.services.sql_grading import FixtureSpec

    rows = db.execute(
        select(Question, QuestionVersion, SQLExerciseVersion)
        .join(QuestionVersion, QuestionVersion.question_id == Question.id)
        .join(SQLExerciseVersion, SQLExerciseVersion.question_version_id == QuestionVersion.id)
        .where(QuestionVersion.pool == "practice")
        .order_by(Question.id, QuestionVersion.version.desc())
    )
    exercises: dict[str, ExerciseView] = {}
    enabled = worker_supported()
    for question, version, sql in rows:
        if question.id not in exercises:
            spec = FixtureSpec.model_validate_json(sql.fixture_spec)
            exercises[question.id] = ExerciseView(
                id=question.id,
                ref=version.id,
                topic_id=question.subtopic_id,
                prompt=version.stem,
                difficulty=version.difficulty,
                dialect=sql.dialect,
                minimum_sqlite_version=spec.minimum_sqlite_version,
                enabled=enabled,
            )
    return list(exercises.values())
