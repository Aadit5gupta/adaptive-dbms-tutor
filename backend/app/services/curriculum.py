"""Publish approved content as immutable database snapshots."""

import json
from hashlib import sha256
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import (
    Lesson,
    LessonVersion,
    Misconception,
    Question,
    QuestionOption,
    QuestionVersion,
    SQLExerciseVersion,
    Topic,
    TopicPrerequisite,
)
from content.schemas.models import MCQ, SQLQuestion, Versioned
from scripts.validate_content import ROOT, Content, ContentError, load_content


def version_fields(item: Versioned, content_hash: str) -> dict[str, str | int]:
    assert item.verified_by is not None and item.verified_on is not None
    return {
        "id": item.ref,
        "version": item.version,
        "source_ref": item.source.model_dump_json(),
        "review_status": item.review_status,
        "reviewed_by": item.verified_by,
        "reviewed_at": item.verified_on.isoformat(),
        "content_hash": content_hash,
    }


def sql_snapshot(root: Path, question: SQLQuestion) -> tuple[str, str]:
    fixtures = [
        {"path": fixture, "sha256": sha256((root / fixture).read_bytes()).hexdigest()}
        for fixture in question.fixtures
    ]
    results = {
        result.fixture: json.loads((root / result.expected_result_file).read_text(encoding="utf-8"))
        for result in question.expected_results
    }
    return json.dumps(fixtures, sort_keys=True), json.dumps(results, sort_keys=True)


def publish_question(db: Session, item: MCQ | SQLQuestion, root: Path) -> None:
    snapshot = sql_snapshot(root, item) if isinstance(item, SQLQuestion) else ("", "")
    digest = sha256(json.dumps([item.model_dump(mode="json"), *snapshot], sort_keys=True).encode())
    existing = db.get(QuestionVersion, item.ref)
    if existing is not None:
        if existing.content_hash != digest.hexdigest():
            raise ContentError(f"{item.ref}: publish edits as a new question version")
        return

    question = db.get(Question, item.id)
    if question is None:
        db.add(Question(id=item.id, subtopic_id=item.subtopic_id, type=item.type))
        db.flush()
    elif (question.subtopic_id, question.type) != (item.subtopic_id, item.type):
        raise ContentError(f"{item.id}: type and topic of a published question are immutable")

    if isinstance(item, MCQ):
        db.add_all(
            QuestionOption(
                question_version_id=item.ref,
                option_index=ordinal,
                body=option.text,
                is_correct=option.correct,
                misconception_code=option.misconception_code,
            )
            for ordinal, option in enumerate(item.options)
        )
        stem, explanation = item.stem, item.explanation
    else:
        db.add(
            SQLExerciseVersion(
                question_version_id=item.ref,
                dialect=item.dialect,
                fixture_spec=snapshot[0],
                expected_result_spec=snapshot[1],
                reference_query=item.reference_query,
                comparison_spec=item.compare.model_dump_json(),
            )
        )
        stem, explanation = item.prompt, None
    db.flush()
    db.add(
        QuestionVersion(
            **version_fields(item, digest.hexdigest()),
            question_id=item.id,
            pool=item.pool,
            difficulty=item.difficulty,
            stem=stem,
            explanation=explanation,
        )
    )
    db.flush()


def publish_content(db: Session, content: Content, root: Path = ROOT) -> None:
    for domain in content.domains:
        for position, (topic, title) in enumerate(domain.subtopics.items()):
            db.merge(Topic(id=topic, domain_slug=domain.id, title=title, position=position))
    db.flush()
    for edge in content.prerequisites:
        db.merge(TopicPrerequisite(topic_id=edge.subtopic_id, prerequisite_id=edge.prerequisite_id))

    for item in content.lessons.values():
        if not item.reviewed:
            continue
        digest = sha256(item.model_dump_json().encode()).hexdigest()
        existing = db.get(LessonVersion, item.ref)
        if existing is not None:
            if existing.content_hash != digest:
                raise ContentError(f"{item.ref}: publish edits as a new lesson version")
            continue
        lesson = db.get(Lesson, item.id)
        if lesson is None:
            db.add(Lesson(id=item.id, subtopic_id=item.subtopic_id))
            db.flush()
        elif lesson.subtopic_id != item.subtopic_id:
            raise ContentError(f"{item.id}: topic of a published lesson is immutable")
        db.add(
            LessonVersion(
                **version_fields(item, digest),
                lesson_id=item.id,
                title=item.title,
                body_markdown=item.body_markdown,
            )
        )
        db.flush()

    for question in content.questions.values():
        if question.reviewed:
            publish_question(db, question, root)

    for rule in content.rules.values():
        if rule.enabled:
            snapshot = rule.model_dump_json()
            db.merge(
                Misconception(
                    code=rule.code,
                    title=rule.name,
                    subtopic_id=rule.subtopic_id,
                    review_status=rule.review_status,
                    enabled=True,
                    rule_version=sha256(snapshot.encode()).hexdigest(),
                    remediation_lesson_version_id=rule.remediation_lesson_ref,
                    definition_json=snapshot,
                )
            )


def publish_from_disk(db: Session, root: Path = ROOT) -> None:
    publish_content(db, load_content(root), root)
