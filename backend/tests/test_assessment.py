from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.db import open_engine
from app.db.models import Attempt, QuestionVersion, SQLExerciseVersion, User
from app.main import ALEMBIC_INI
from app.schemas.assessment import AnswerInput
from app.services.assessment import AssessmentError, allocate_mcqs, submit_mcq
from app.services.curriculum import publish_from_disk
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from content.schemas.models import Pool
from scripts.validate_content import ContentError

from .content_fixtures import save


@pytest.fixture
def assessment_db(tmp_path: Path, s1: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    monkeypatch.setenv("DBMS_APP_DB", str(tmp_path / "app.sqlite"))
    monkeypatch.setenv("DBMS_DEMO_DB", str(tmp_path / "demo.sqlite"))
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    engine = open_engine(Settings().app_db)
    try:
        with Session(engine) as db, db.begin():
            db.add_all(User(id=id_, is_demo=False, created_at=0) for id_ in ("learner", "other"))
            publish_from_disk(db, s1)
        yield engine
    finally:
        engine.dispose()


def test_allocation_withholds_key_and_sql_specs(assessment_db: Engine) -> None:
    with Session(assessment_db) as db, db.begin():
        view = allocate_mcqs(db, "learner", "practice", limit=20)
        assert len(view.items) == 6
        for item in view.items:
            assert set(item.model_dump()) == {
                "item_id",
                "question_ref",
                "subtopic_id",
                "stem",
                "options",
            }
            assert len(item.options) == 4
            assert "checkpoint" not in item.question_ref
            assert item.question_ref != "sql_fixture@1"
        assert db.get(SQLExerciseVersion, "sql_fixture@1") is not None


def test_grading_uses_stored_answer_and_blocks_cross_learner_access(assessment_db: Engine) -> None:
    with Session(assessment_db) as db, db.begin():
        practice = allocate_mcqs(db, "learner", "practice", limit=2)
    answer = AnswerInput(item_id=practice.items[0].item_id, option_index=1)
    with pytest.raises(AssessmentError, match="not found"):
        submit_mcq(assessment_db, "other", practice.session_id, "key", answer)
    result = submit_mcq(assessment_db, "learner", practice.session_id, "key", answer)
    assert not result.correct
    assert result.explanation == "Synthetic explanation"
    assert submit_mcq(assessment_db, "learner", practice.session_id, "key", answer) == result
    changed = answer.model_copy(update={"option_index": 0})
    with pytest.raises(AssessmentError, match="key was already used"):
        submit_mcq(assessment_db, "learner", practice.session_id, "key", changed)
    with pytest.raises(AssessmentError, match="already has a submission"):
        submit_mcq(assessment_db, "learner", practice.session_id, "new-key", changed)
    next_item = AnswerInput(item_id=practice.items[1].item_id, option_index=0)
    assert submit_mcq(assessment_db, "learner", practice.session_id, "next", next_item).correct
    with Session(assessment_db) as db:
        assert db.scalar(select(func.count()).select_from(Attempt)) == 2


def test_checkpoint_exposure_and_held_out_pool_are_reserved(assessment_db: Engine) -> None:
    with Session(assessment_db) as db, db.begin():
        with pytest.raises(AssessmentError, match="reserved"):
            allocate_mcqs(db, "learner", "pre_test_a")
        with pytest.raises(AssessmentError, match="No verified checkpoint"):
            allocate_mcqs(db, "learner", "checkpoint")
        keys = ("keys_checkpoint_0@1", "keys_checkpoint_1@1")
        first = allocate_mcqs(
            db, "learner", "checkpoint", reserved_refs=keys, misconception_code="KEYS-02"
        )
        second = allocate_mcqs(
            db, "learner", "checkpoint", reserved_refs=keys, misconception_code="KEYS-02"
        )
        assert first.items[0].question_ref != second.items[0].question_ref
        with pytest.raises(AssessmentError, match="no eligible questions"):
            allocate_mcqs(
                db, "learner", "checkpoint", reserved_refs=keys, misconception_code="KEYS-02"
            )


def test_new_version_preserves_existing_allocation(assessment_db: Engine, s1: Path) -> None:
    with Session(assessment_db) as db, db.begin():
        existing = allocate_mcqs(db, "learner", "practice", subtopic="relational.keys")
        selected = existing.items[0]
    path = s1 / "content/questions/test.yaml"
    questions = yaml.safe_load(path.read_text())
    logical_id = selected.question_ref.split("@")[0]
    original = next(question for question in questions if question["id"] == logical_id)
    save(
        s1,
        "content/questions/test.yaml",
        [*questions, {**original, "version": 2, "stem": "New stem"}],
    )
    with Session(assessment_db) as db, db.begin():
        publish_from_disk(db, s1)
        publish_from_disk(db, s1)
        current = allocate_mcqs(db, "learner", "practice", subtopic="relational.keys").items[0]
        assert current.question_ref == f"{logical_id}@2"
        assert current.stem == "New stem"
    submit_mcq(
        assessment_db,
        "learner",
        existing.session_id,
        "original",
        AnswerInput(item_id=selected.item_id, option_index=0),
    )
    with Session(assessment_db) as db:
        assert db.scalar(select(Attempt.question_version_id)) == selected.question_ref

    original["stem"] = "Edit in place"
    save(s1, "content/questions/test.yaml", questions)
    with (
        pytest.raises(ContentError, match="publish edits as a new question version"),
        Session(assessment_db) as db,
        db.begin(),
    ):
        publish_from_disk(db, s1)


def test_draft_content_stays_out_of_published_pool(assessment_db: Engine, s1: Path) -> None:
    path = s1 / "content/questions/test.yaml"
    questions = yaml.safe_load(path.read_text())
    draft = {
        **questions[0],
        "id": "unverified_question",
        "review_status": "draft",
        "verified_by": None,
        "verified_on": None,
    }
    save(s1, "content/questions/test.yaml", [*questions, draft])
    with Session(assessment_db) as db, db.begin():
        publish_from_disk(db, s1)
        assert db.get(QuestionVersion, "unverified_question@1") is None


def test_independent_evidence_stays_with_the_correct_learner(assessment_db: Engine) -> None:
    from app.db.models import UserMisconception

    answers: list[tuple[str, Pool]] = [
        ("learner", "diagnostic"),
        ("other", "practice"),
        ("learner", "practice"),
    ]
    for user, pool in answers:
        with Session(assessment_db) as db, db.begin():
            view = allocate_mcqs(db, user, pool, subtopic="relational.keys")
        submit_mcq(
            assessment_db,
            user,
            view.session_id,
            f"answer-{pool}",
            AnswerInput(item_id=view.items[0].item_id, option_index=1),
        )
    with Session(assessment_db) as db:
        a = db.get(UserMisconception, ("learner", "KEYS-02"))
        b = db.get(UserMisconception, ("other", "KEYS-02"))
        assert a is not None and a.state == "active"
        assert b is not None and b.state == "possible"

    with Session(assessment_db) as db, db.begin():
        checkpoint = allocate_mcqs(
            db,
            "learner",
            "checkpoint",
            limit=2,
            misconception_code="KEYS-02",
            reserved_refs=("keys_checkpoint_0@1", "keys_checkpoint_1@1"),
        )
    for item in checkpoint.items:
        submit_mcq(
            assessment_db,
            "learner",
            checkpoint.session_id,
            item.item_id,
            AnswerInput(item_id=item.item_id, option_index=0),
        )
    with Session(assessment_db) as db:
        resolved = db.get(UserMisconception, ("learner", "KEYS-02"))
        assert resolved is not None and resolved.state == "resolved"


def test_concurrent_retry_commits_learning_state_once(assessment_db: Engine) -> None:
    from concurrent.futures import ThreadPoolExecutor

    from app.db.models import Mastery, MasteryHistory, PolicyDecision, Recommendation

    with Session(assessment_db) as db, db.begin():
        practice = allocate_mcqs(db, "learner", "practice", subtopic="relational.keys")
    answer = AnswerInput(item_id=practice.items[0].item_id, option_index=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(submit_mcq, assessment_db, "learner", practice.session_id, "retry", answer)
        b = pool.submit(submit_mcq, assessment_db, "learner", practice.session_id, "retry", answer)
        assert a.result() == b.result()
    with Session(assessment_db) as db:
        for table in (Attempt, Mastery, MasteryHistory, PolicyDecision, Recommendation):
            assert db.scalar(select(func.count()).select_from(table)) == 1


def test_policy_failure_rolls_back_answer_and_mastery(
    assessment_db: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.db.models import Mastery, SessionItem

    with Session(assessment_db) as db, db.begin():
        practice = allocate_mcqs(db, "learner", "practice")
    item_id = practice.items[0].item_id

    def fail(*_: object) -> None:
        raise RuntimeError("Synthetic policy failure")

    monkeypatch.setattr("app.services.learning_state.choose_next", fail)
    with pytest.raises(RuntimeError, match="Synthetic policy failure"):
        submit_mcq(
            assessment_db,
            "learner",
            practice.session_id,
            "key",
            AnswerInput(item_id=item_id, option_index=0),
        )
    with Session(assessment_db) as db:
        assert db.scalar(select(func.count()).select_from(Attempt)) == 0
        assert db.scalar(select(func.count()).select_from(Mastery)) == 0
        item = db.get(SessionItem, item_id)
        assert item is not None and item.status == "open"


def test_sql_grade_runs_before_transaction(
    assessment_db: Engine, s1: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.schemas.assessment import SQLAnswerInput
    from app.services.assessment import allocate_sql, submit_sql
    from app.services.sql_grading import Grade

    with Session(assessment_db) as db, db.begin():
        practice = allocate_sql(db, "learner", "sql_fixture")
    calls = 0

    def mock_grade(*_: object) -> Grade:
        nonlocal calls
        calls += 1
        with assessment_db.connect() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            connection.rollback()
        return Grade(correct=True, feedback_code="correct", checked_fixtures=2)

    monkeypatch.setattr("app.services.assessment.grade_sql", mock_grade)
    answer = SQLAnswerInput(item_id=practice.items[0].item_id, query="SELECT n FROM t")
    result = submit_sql(assessment_db, s1, "learner", practice.session_id, "sql-key", answer)
    assert result.correct and result.mastery and result.mastery.after == 0.6
    assert (
        submit_sql(assessment_db, s1, "learner", practice.session_id, "sql-key", answer) == result
    )
    assert calls == 1


def test_five_question_practice_resumes_and_prefers_fresh_questions(assessment_db: Engine) -> None:
    from app.services.study import start_study, study_session

    with Session(assessment_db) as db, db.begin():
        first = start_study(db, "learner", "practice")
        assert len(first.items) == 5
        assert start_study(db, "learner", "practice") == first
        with pytest.raises(AssessmentError, match="not found"):
            study_session(db, "other", first.session_id)
    for item in first.items:
        submit_mcq(
            assessment_db,
            "learner",
            first.session_id,
            item.item_id,
            AnswerInput(item_id=item.item_id, option_index=0),
        )
    with Session(assessment_db) as db, db.begin():
        second = start_study(db, "learner", "practice")
        assert second.session_id != first.session_id
        assert second.items[0].question_ref not in {item.question_ref for item in first.items}


def test_diagnostic_allocates_only_fresh_reviewed_domains(assessment_db: Engine) -> None:
    from app.services.study import start_study

    with Session(assessment_db) as db, db.begin():
        diagnostic = start_study(db, "learner", "diagnostic")
        assert {row.subtopic_id for row in diagnostic.items} == {"relational.keys", "sql.joins"}
    for item in diagnostic.items:
        submit_mcq(
            assessment_db,
            "learner",
            diagnostic.session_id,
            item.item_id,
            AnswerInput(item_id=item.item_id, option_index=0),
        )
    with (
        Session(assessment_db) as db,
        db.begin(),
        pytest.raises(AssessmentError, match="no eligible questions"),
    ):
        start_study(db, "learner", "diagnostic", topic="relational.keys")


def test_progress_coverage_review_and_persisted_recommendation(assessment_db: Engine) -> None:
    from app.services.progress import read_progress

    with Session(assessment_db) as db, db.begin():
        view = allocate_mcqs(db, "learner", "practice", subtopic="relational.keys")
    answer = submit_mcq(
        assessment_db,
        "learner",
        view.session_id,
        "progress",
        AnswerInput(item_id=view.items[0].item_id, option_index=0),
    )
    with Session(assessment_db) as db:
        owner = read_progress(db, "learner", now=100_000_000_000)
        other = read_progress(db, "other", now=100_000_000_000)
    assert len(owner.domains) == 7 and owner.recommendation == answer.next_action
    keys = next(row for row in owner.topics if row.topic == "relational.keys")
    assert keys.score == 0.6 and keys.recent_accuracy == 1.0 and keys.review_due
    relational = next(row for row in owner.domains if row.domain == "relational")
    assert relational.assessed_topics == 1 and relational.listed_topics > 1
    assert all(row.score is None for row in other.topics)
    assert other.recent == []
    assert set(owner.recent[0].model_dump()) == {
        "topic",
        "context",
        "correct",
        "created_at",
        "mastery_after",
    }


def test_publishing_preserves_reserved_pool_and_disables_removed_rules(
    assessment_db: Engine, s1: Path
) -> None:
    from app.db.models import Misconception

    rules_file = s1 / "content/misconceptions.yaml"
    rules = yaml.safe_load(rules_file.read_text())
    for rule in rules:
        rule["enabled"] = False
    save(s1, "content/misconceptions.yaml", rules)
    with Session(assessment_db) as db, db.begin():
        publish_from_disk(db, s1)
        assert all(not rule.enabled for rule in db.scalars(select(Misconception)))

    questions_file = s1 / "content/questions/test.yaml"
    questions = yaml.safe_load(questions_file.read_text())
    questions[0]["pool"] = "diagnostic"
    questions[0]["version"] = 2
    save(s1, "content/questions/test.yaml", questions)
    with (
        Session(assessment_db) as db,
        db.begin(),
        pytest.raises(ContentError, match="pool of a published"),
    ):
        publish_from_disk(db, s1)
