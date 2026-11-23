"""Private tutor history and narrowly scoped learning context."""

from dataclasses import dataclass
from time import time
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.db.models import (
    AssessmentSession,
    Attempt,
    Misconception,
    Profile,
    Question,
    QuestionVersion,
    SessionItem,
    TutorConversation,
    TutorMessage,
    User,
    UserMisconception,
)
from app.providers.contracts import Turn
from app.schemas.assessment import AnswerResult
from app.schemas.tutor import TutorInput, TutorReply, TutorTurnView
from app.services.assessment import AssessmentError
from app.services.tutor import TutorService

SQL_CONTEXT = {
    "result_mismatch": "The submitted query returned a different result; discuss row selection, joins, or grouping.",
    "invalid_query": "The SQL processor reported a syntax or name error; discuss how to check columns and syntax.",
    "query_denied": "The lab accepts a bounded read-only SELECT over the exercise tables.",
    "execution_limit": "The submitted query exceeded the runtime limit; explain how to reduce row combinations.",
    "output_limit": "The submitted query exceeded the result limit; explain how to narrow its output.",
}


@dataclass(frozen=True)
class Snapshot:
    id: str
    revision: int | None
    request: TutorInput
    history: tuple[Turn, ...]
    learner_context: str
    explain_join_count: bool


def owned_conversation(db: Session, user_id: str, reference: str) -> TutorConversation:
    row = db.get(TutorConversation, reference)
    if row is None or row.user_id != user_id:
        raise AssessmentError("Tutor conversation not found.", "conversation_not_found", 404)
    return row


def recent_messages(db: Session, reference: str) -> list[TutorMessage]:
    rows = list(
        db.scalars(
            select(TutorMessage)
            .where(TutorMessage.conversation_id == reference)
            .order_by(TutorMessage.id.desc())
            .limit(6)
        )
    )
    return list(reversed(rows))


def learner_snapshot(engine: Engine, user_id: str, body: TutorInput) -> Snapshot:
    with Session(engine) as db, db.begin():
        # Hint exposure must be stored before a concurrent assessment submission.
        if body.item_id is not None:
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        conversation = (
            owned_conversation(db, user_id, body.conversation_id) if body.conversation_id else None
        )
        topic = body.topic_id or (conversation.topic_id if conversation else None)
        facts: list[str] = []
        explain_join_count = False
        if body.item_id is not None:
            item = db.get(SessionItem, body.item_id)
            session = db.get(AssessmentSession, item.session_id) if item else None
            if (
                body.mode != "hint"
                or item is None
                or session is None
                or session.user_id != user_id
                or session.kind not in ("practice", "review")
                or item.status != "open"
            ):
                raise AssessmentError("Open assessment item not found.", "item_not_found", 404)
            question = db.scalar(
                select(Question)
                .join(QuestionVersion, QuestionVersion.question_id == Question.id)
                .where(QuestionVersion.id == item.question_version_id)
            )
            if question is None:
                raise AssessmentError("Open assessment item not found.", "item_not_found", 404)
            topic = question.subtopic_id
            if body.hint_level > item.highest_hint_level + 1:
                raise AssessmentError("Open the preceding hint first.", "hint_order", 409)
            item.highest_hint_level = max(item.highest_hint_level, body.hint_level)
            if body.hint_level >= 2:
                item.revealing_hint_used = True

        if body.attempt_id is not None:
            attempt = db.get(Attempt, body.attempt_id)
            if (
                body.mode != "sql_feedback"
                or attempt is None
                or attempt.user_id != user_id
                or attempt.context != "sql"
            ):
                raise AssessmentError("SQL attempt not found.", "attempt_not_found", 404)
            version = db.get(QuestionVersion, attempt.question_version_id)
            if version is not None:
                goal = version.stem.splitlines()[0][:200]
                facts.append(f"Exercise goal: {goal}")
            result = AnswerResult.model_validate_json(attempt.result_json)
            explain_join_count = (
                version is not None
                and version.question_id == "sql_join_001"
                and result.feedback_code == "result_mismatch"
            )
            facts.append(
                SQL_CONTEXT.get(
                    result.feedback_code or "",
                    "Explain the query feedback using the supplied topic.",
                )
            )
            question = db.get(Question, version.question_id) if version else None
            topic = question.subtopic_id if question else topic

        profile = db.get(Profile, user_id)
        if profile is not None:
            if profile.goal:
                facts.append(f"Goal: {profile.goal}.")
            if profile.level:
                facts.append(f"Experience: {profile.level}.")
        if topic is not None:
            hypothesis = db.execute(
                select(Misconception.title, UserMisconception.state)
                .join(Misconception, Misconception.code == UserMisconception.code)
                .where(
                    UserMisconception.user_id == user_id,
                    Misconception.subtopic_id == topic,
                    UserMisconception.state.in_(("active", "improving")),
                    Misconception.enabled.is_(True),
                )
                .order_by(Misconception.code)
                .limit(1)
            ).first()
            if hypothesis:
                facts.append(f"Learning hypothesis ({hypothesis.state}): {hypothesis.title}.")

        history = (
            ()
            if conversation is None
            else tuple(
                Turn("user" if row.role == "user" else "assistant", row.content)
                for row in recent_messages(db, conversation.id)
            )
        )
        return Snapshot(
            id=conversation.id if conversation else uuid4().hex,
            revision=conversation.revision if conversation else None,
            request=body.model_copy(update={"topic_id": topic}),
            history=history,
            learner_context=" ".join(facts),
            explain_join_count=explain_join_count,
        )


def store_reply(engine: Engine, user_id: str, snapshot: Snapshot, reply: TutorReply) -> None:
    now = int(time())
    with Session(engine) as db, db.begin():
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        if db.get(User, user_id) is None:
            raise AssessmentError("Sign in to continue.", "sign_in_required", 401)
        if snapshot.revision is None:
            conversation = TutorConversation(
                id=snapshot.id,
                user_id=user_id,
                topic_id=reply.topic_id,
                created_at=now,
                revision=1,
            )
            db.add(conversation)
            db.flush()
        else:
            conversation = owned_conversation(db, user_id, snapshot.id)
            if conversation.revision != snapshot.revision:
                raise AssessmentError(
                    "This conversation changed. Retry your question.", "conversation_conflict"
                )
            conversation.revision += 1
            conversation.topic_id = reply.topic_id or conversation.topic_id
        db.add_all(
            (
                TutorMessage(
                    conversation_id=snapshot.id,
                    role="user",
                    content=snapshot.request.query,
                    created_at=now,
                ),
                TutorMessage(
                    conversation_id=snapshot.id,
                    role="assistant",
                    content=reply.answer,
                    reply_json=reply.model_dump_json(),
                    created_at=now,
                ),
            )
        )


async def teach(
    engine: Engine, service: TutorService, user_id: str, body: TutorInput
) -> TutorReply:
    snapshot = await run_in_threadpool(learner_snapshot, engine, user_id, body)
    reply = await service.answer(
        snapshot.request,
        history=snapshot.history,
        learner_context=snapshot.learner_context,
        explain_join_count=snapshot.explain_join_count,
    )
    reply.conversation_id = snapshot.id
    await run_in_threadpool(store_reply, engine, user_id, snapshot, reply)
    return reply


def conversation_history(engine: Engine, user_id: str, reference: str) -> list[TutorTurnView]:
    with Session(engine) as db:
        owned_conversation(db, user_id, reference)
        return [
            TutorTurnView(
                role="user" if row.role == "user" else "assistant",
                text=row.content,
                reply=TutorReply.model_validate_json(row.reply_json) if row.reply_json else None,
            )
            for row in recent_messages(db, reference)
        ]
