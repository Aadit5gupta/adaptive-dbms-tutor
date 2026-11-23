"""Coverage-aware learner progress without answer keys or raw SQL."""

from collections import defaultdict

from pydantic import BaseModel
from sqlalchemy import Integer, and_, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Attempt,
    Mastery,
    MasteryHistory,
    PolicyDecision,
    Question,
    QuestionVersion,
    Topic,
)
from app.services.adaptive import NextAction
from app.services.mastery import MODEL_NAME


class TopicProgress(BaseModel):
    topic: str
    title: str
    domain: str
    score: float | None = None
    confidence: str = "unassessed"
    attempts: int = 0
    distinct: int = 0
    recent_accuracy: float | None = None
    review_due_at: int | None = None
    review_due: bool = False


class DomainProgress(BaseModel):
    domain: str
    assessed_topics: int
    listed_topics: int
    score: float | None


class AttemptSummary(BaseModel):
    topic: str
    context: str
    correct: bool
    created_at: int
    mastery_after: float | None


class Progress(BaseModel):
    topics: list[TopicProgress]
    domains: list[DomainProgress]
    recent: list[AttemptSummary]
    recommendation: NextAction | None


def latest_recommendation(db: Session, user_id: str) -> NextAction | None:
    action = db.scalar(
        select(PolicyDecision.selected_action)
        .where(PolicyDecision.user_id == user_id)
        .order_by(PolicyDecision.id.desc())
        .limit(1)
    )
    return NextAction.model_validate_json(action) if action is not None else None


def read_progress(db: Session, user_id: str, now: int) -> Progress:
    ranked_attempts = (
        select(
            Question.subtopic_id.label("topic"),
            Attempt.correct,
            func.row_number()
            .over(
                partition_by=Question.subtopic_id,
                order_by=(Attempt.created_at.desc(), Attempt.id.desc()),
            )
            .label("rank"),
        )
        .join(QuestionVersion, QuestionVersion.id == Attempt.question_version_id)
        .join(Question, Question.id == QuestionVersion.question_id)
        .where(Attempt.user_id == user_id, Attempt.context.not_in(("pre_test_a", "post_test_b")))
        .subquery()
    )
    accuracy = {
        topic: correct / count
        for topic, correct, count in db.execute(
            select(
                ranked_attempts.c.topic,
                func.sum(ranked_attempts.c.correct.cast(Integer)),
                func.count(),
            )
            .where(ranked_attempts.c.rank <= 5)
            .group_by(ranked_attempts.c.topic)
        )
    }
    topics: list[TopicProgress] = []
    grouped: dict[str, list[TopicProgress]] = defaultdict(list)
    for topic, row in db.execute(
        select(Topic, Mastery)
        .outerjoin(
            Mastery,
            and_(
                Mastery.subtopic_id == Topic.id,
                Mastery.user_id == user_id,
                Mastery.model_name == MODEL_NAME,
            ),
        )
        .order_by(Topic.domain_slug, Topic.position)
    ):
        item = TopicProgress(topic=topic.id, title=topic.title, domain=topic.domain_slug)
        if row is not None:
            item.score = row.score
            item.confidence = row.confidence_level
            item.attempts = row.attempts_count
            item.distinct = row.distinct_question_count
            item.review_due_at = row.review_due_at
            item.review_due = row.review_due_at is not None and row.review_due_at <= now
            item.recent_accuracy = accuracy.get(topic.id)
        grouped[topic.domain_slug].append(item)
        topics.append(item)

    domains = []
    for domain, items in grouped.items():
        scores = [item.score for item in items if item.score is not None]
        domains.append(
            DomainProgress(
                domain=domain,
                assessed_topics=len(scores),
                listed_topics=len(items),
                score=sum(scores) / len(scores) if scores else None,
            )
        )

    recent = [
        AttemptSummary(
            topic=topic, context=context, correct=correct, created_at=created, mastery_after=score
        )
        for topic, context, correct, created, score in db.execute(
            select(
                Question.subtopic_id,
                Attempt.context,
                Attempt.correct,
                Attempt.created_at,
                MasteryHistory.new_score,
            )
            .join(QuestionVersion, QuestionVersion.id == Attempt.question_version_id)
            .join(Question, Question.id == QuestionVersion.question_id)
            .outerjoin(MasteryHistory, MasteryHistory.attempt_id == Attempt.id)
            .where(Attempt.user_id == user_id)
            .order_by(Attempt.created_at.desc(), Attempt.id.desc())
            .limit(20)
        )
    ]
    return Progress(
        topics=topics,
        domains=domains,
        recent=recent,
        recommendation=latest_recommendation(db, user_id),
    )
