"""Versioned content and durable learner evidence."""

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(unique=True)
    password_hash: Mapped[str | None]
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[int]
    disabled_at: Mapped[int | None]


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(primary_key=True)
    domain_slug: Mapped[str]
    title: Mapped[str]
    position: Mapped[int]


class TopicPrerequisite(Base):
    __tablename__ = "topic_prerequisites"

    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    prerequisite_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(primary_key=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"))


class LessonVersion(Base):
    __tablename__ = "lesson_versions"
    __table_args__ = (
        UniqueConstraint("lesson_id", "version", name="lesson_logical_version"),
        CheckConstraint("version > 0"),
        CheckConstraint("id = lesson_id || '@' || version"),
        CheckConstraint("review_status IN ('author_verified', 'independent_verified')"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"))
    version: Mapped[int]
    title: Mapped[str]
    body_markdown: Mapped[str]
    review_status: Mapped[str]
    source_ref: Mapped[str]
    reviewed_by: Mapped[str]
    reviewed_at: Mapped[str]
    content_hash: Mapped[str]


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (CheckConstraint("type IN ('mcq', 'sql')"),)

    id: Mapped[str] = mapped_column(primary_key=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"))
    type: Mapped[str]


class QuestionVersion(Base):
    __tablename__ = "question_versions"
    __table_args__ = (
        UniqueConstraint("question_id", "version", name="question_logical_version"),
        CheckConstraint("version > 0"),
        CheckConstraint("id = question_id || '@' || version"),
        CheckConstraint("pool IN ('diagnostic', 'practice', 'checkpoint', 'pre_test_a', 'post_test_b')"),
        CheckConstraint("review_status IN ('author_verified', 'independent_verified')"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    version: Mapped[int]
    pool: Mapped[str]
    stem: Mapped[str]
    difficulty: Mapped[str]
    explanation: Mapped[str | None]
    review_status: Mapped[str]
    source_ref: Mapped[str]
    reviewed_by: Mapped[str]
    reviewed_at: Mapped[str]
    content_hash: Mapped[str]


class QuestionOption(Base):
    __tablename__ = "question_options"
    __table_args__ = (CheckConstraint("option_index BETWEEN 0 AND 3"),)

    question_version_id: Mapped[str] = mapped_column(
        ForeignKey("question_versions.id", deferrable=True, initially="DEFERRED"), primary_key=True
    )
    option_index: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str]
    is_correct: Mapped[bool]
    misconception_code: Mapped[str | None]


class SQLExerciseVersion(Base):
    __tablename__ = "sql_exercise_versions"

    question_version_id: Mapped[str] = mapped_column(
        ForeignKey("question_versions.id", deferrable=True, initially="DEFERRED"), primary_key=True
    )
    dialect: Mapped[str]
    fixture_spec: Mapped[str]
    expected_result_spec: Mapped[str]
    reference_query: Mapped[str]
    comparison_spec: Mapped[str]


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[int]
    completed_at: Mapped[int | None]


class SessionItem(Base):
    __tablename__ = "assessment_session_items"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="unique_session_position"),
        UniqueConstraint("id", "question_version_id", name="unique_item_version"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id", ondelete="CASCADE"))
    question_version_id: Mapped[str] = mapped_column(ForeignKey("question_versions.id"))
    position: Mapped[int]
    status: Mapped[str]
    revealing_hint_used: Mapped[bool] = mapped_column(default=False)
    remediation_code: Mapped[str | None] = mapped_column(ForeignKey("misconceptions.code"))


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="idempotency_by_user"),
        ForeignKeyConstraint(
            ("session_item_id", "question_version_id"),
            ("assessment_session_items.id", "assessment_session_items.question_version_id"),
            ondelete="CASCADE",
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    session_item_id: Mapped[str] = mapped_column(unique=True)
    question_version_id: Mapped[str]
    idempotency_key: Mapped[str]
    request_fingerprint: Mapped[str]
    result_json: Mapped[str]
    selected_option_index: Mapped[int | None]
    submitted_sql: Mapped[str | None]
    correct: Mapped[bool]
    hint_used: Mapped[bool]
    context: Mapped[str]
    created_at: Mapped[int]


class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (CheckConstraint("score BETWEEN 0 AND 1"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    model_name: Mapped[str] = mapped_column(primary_key=True)
    score: Mapped[float]
    confidence_level: Mapped[str]
    attempts_count: Mapped[int]
    distinct_question_count: Mapped[int]
    review_due_at: Mapped[int | None]
    review_interval_step: Mapped[int]
    updated_at: Mapped[int]


class MasteryHistory(Base):
    __tablename__ = "mastery_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"))
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), unique=True)
    old_score: Mapped[float]
    new_score: Mapped[float]
    model_version: Mapped[str]
    created_at: Mapped[int]


class Misconception(Base):
    __tablename__ = "misconceptions"

    code: Mapped[str] = mapped_column(primary_key=True)
    subtopic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"))
    title: Mapped[str]
    rule_version: Mapped[str]
    review_status: Mapped[str]
    enabled: Mapped[bool]
    remediation_lesson_version_id: Mapped[str] = mapped_column(ForeignKey("lesson_versions.id"))
    definition_json: Mapped[str]


class MisconceptionEvidence(Base):
    __tablename__ = "misconception_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(ForeignKey("misconceptions.code"))
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), unique=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    question_version_id: Mapped[str] = mapped_column(ForeignKey("question_versions.id"))
    evidence_type: Mapped[str]
    reason: Mapped[str]
    created_at: Mapped[int]


class UserMisconception(Base):
    __tablename__ = "user_misconceptions"
    __table_args__ = (CheckConstraint("state IN ('possible', 'active', 'improving', 'resolved')"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    code: Mapped[str] = mapped_column(ForeignKey("misconceptions.code"), primary_key=True)
    state: Mapped[str]
    evidence_count: Mapped[int]
    last_seen_at: Mapped[int]
    resolved_at: Mapped[int | None]


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    trigger_attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), unique=True)
    policy_version: Mapped[str]
    model_version: Mapped[str]
    input_snapshot_json: Mapped[str]
    selected_action: Mapped[str]
    reason_code: Mapped[str]
    created_at: Mapped[int]


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    policy_decision_id: Mapped[int] = mapped_column(
        ForeignKey("policy_decisions.id", ondelete="CASCADE"), unique=True
    )
    action_type: Mapped[str]
    subtopic_id: Mapped[str | None] = mapped_column(ForeignKey("topics.id"))
    reason: Mapped[str]
    created_at: Mapped[int]
    followed_at: Mapped[int | None]
    skipped_at: Mapped[int | None]
