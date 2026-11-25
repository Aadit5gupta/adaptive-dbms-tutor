"""Assessment and progression checks against the authored learner bank."""

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from app.core.db import open_engine
from app.db.models import Mastery, SessionItem, User
from app.main import ALEMBIC_INI
from app.schemas.assessment import AnswerInput, AnswerResult
from app.services.assessment import AssessmentError, options_for, submit_mcq
from app.services.curriculum import publish_from_disk
from app.services.learning_state import state_from_row
from app.services.mastery import MODEL_NAME, MasteryState
from app.services.progress import latest_recommendation
from app.services.study import StudyMode, start_checkpoints, start_study, study_session
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


@pytest.fixture
def authored_db(tmp_path: Path) -> Iterator[Engine]:
    engine = open_engine(tmp_path / "authored.sqlite", create=True)
    cfg = Config(str(ALEMBIC_INI))
    try:
        with engine.begin() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with Session(engine) as db, db.begin():
            db.add_all(User(id=name, is_demo=False, created_at=0) for name in ("a", "b"))
            publish_from_disk(db)
        yield engine
    finally:
        engine.dispose()


def test_global_diagnostic_can_resume_ticket_in_exact_scope(authored_db: Engine) -> None:
    with Session(authored_db) as db, db.begin():
        initial = start_study(db, "a", "diagnostic")
        assert initial.total == 4
        assert initial.items[0].subtopic_id == "sql.joins"
        targeted = start_study(db, "a", "diagnostic", topic="relational.keys")
        assert targeted.session_id == initial.session_id
        assert targeted.total == targeted.remaining == 1
        assert targeted.items[0].question_ref == "q_keys_detector_tickets@1"
        assert targeted == study_session(
            db, "a", initial.session_id, diagnostic_scope="relational.keys"
        )
        assert len(study_session(db, "a", initial.session_id).items) == 4
        with pytest.raises(AssessmentError, match="not found"):
            study_session(db, "b", initial.session_id, diagnostic_scope="relational.keys")

    result = submit_mcq(
        authored_db,
        "a",
        targeted.session_id,
        "tickets",
        AnswerInput(item_id=targeted.items[0].item_id, option_index=1),
    )
    assert result.misconception is not None and result.misconception.state == "possible"
    with Session(authored_db) as db, db.begin():
        assert (
            study_session(
                db, "a", targeted.session_id, diagnostic_scope="relational.keys"
            ).remaining
            == 0
        )
        assert study_session(db, "a", targeted.session_id).remaining == 3
        with pytest.raises(AssessmentError, match="no eligible"):
            start_study(db, "a", "diagnostic", topic="relational.keys")


@pytest.mark.parametrize(
    ("mode", "scope", "expected"),
    [
        ("diagnostic", "sql", {"sql.joins"}),
        ("diagnostic", "normalization", {"normalization.fds", "normalization.normal_forms"}),
        ("practice", "relational.keys", {"relational.keys"}),
        (
            "practice",
            "normalization",
            {"normalization.fds", "normalization.normal_forms", "normalization.decomposition"},
        ),
    ],
)
def test_domain_and_topic_selections_use_only_scoped_questions(
    authored_db: Engine, mode: str, scope: str, expected: set[str]
) -> None:
    from typing import cast

    from app.services.study import StudyMode

    with Session(authored_db) as db, db.begin():
        view = start_study(db, "b", cast(StudyMode, mode), topic=scope)
        assert {item.subtopic_id for item in view.items} == expected


def test_requested_difficulty_does_not_resume_easy_session_or_insert_easy_filler(
    authored_db: Engine,
) -> None:
    with Session(authored_db) as db, db.begin():
        easy = start_study(db, "b", "practice", topic="relational.keys", difficulty="easy")
        medium = start_study(
            db, "b", "practice", topic="relational.keys", difficulty="medium", fresh=True
        )
        assert easy.total == 5
        assert {item.difficulty for item in easy.items} == {"easy"}
        assert medium.session_id != easy.session_id and medium.total == 1
        assert {item.difficulty for item in medium.items} == {"medium"}
        assert medium == start_study(
            db, "b", "practice", topic="relational.keys", difficulty="medium"
        )
        with pytest.raises(AssessmentError, match="no eligible"):
            start_study(db, "b", "practice", topic="relational.keys", difficulty="hard")


def take(
    engine: Engine,
    learner: str,
    topic: str,
    mode: str,
    correct: bool,
    *,
    tier: str | None = None,
    hinted: bool = False,
) -> tuple[AnswerResult, MasteryState]:
    with Session(engine) as db, db.begin():
        view = (
            start_checkpoints(db, learner)
            if mode == "checkpoint"
            else start_study(db, learner, cast(StudyMode, mode), topic=topic, difficulty=tier)
        )
        item = view.items[0]
        before = state_from_row(db.get(Mastery, (learner, topic, MODEL_NAME)))
        options = options_for(db, item.question_ref)
        choice = next(
            (
                option
                for option in options
                if option.is_correct == correct and (correct or option.misconception_code)
            ),
            next(option for option in options if option.is_correct == correct),
        )
        if hinted:
            row = db.get(SessionItem, item.item_id)
            assert row is not None
            row.revealing_hint_used = True
        index = choice.option_index
    result = submit_mcq(
        engine,
        learner,
        view.session_id,
        item.item_id,
        AnswerInput(item_id=item.item_id, option_index=index),
    )
    with Session(engine) as db:
        after = state_from_row(db.get(Mastery, (learner, topic, MODEL_NAME)))
        assert result.next_action == latest_recommendation(db, learner)
    assert result.correct == correct and result.next_action is not None
    print(
        f"TRACE {mode}:{item.question_ref} option {index} {'right' if correct else 'wrong'} "
        f"{before.score:.3f}/{before.distinct} → {after.score:.3f}/{after.distinct} "
        f"{after.confidence} {result.misconception.state if result.misconception else '—'} "
        f"{result.next_action.action_type}:{result.next_action.subtopic_id} {result.next_action.reason_code}"
    )
    return result, after


def test_learner_a_needs_foundation_and_failed_checkpoints_remain_active(
    authored_db: Engine,
) -> None:
    topic = "relational.keys"
    first, _ = take(authored_db, "a", topic, "diagnostic", False)
    assert first.next_action and first.next_action.action_type == "RETEACH"
    assert first.next_action.lesson_ref == "lesson_fk_multiplicity@1"
    assert first.misconception and first.misconception.state == "possible"
    second, _ = take(authored_db, "a", topic, "practice", False, tier="easy")
    assert second.next_action and second.next_action.action_type == "MISCONCEPTION_REMEDIATION"
    assert second.misconception and second.misconception.state == "active"
    take(authored_db, "a", topic, "checkpoint", False)
    last, _ = take(authored_db, "a", topic, "checkpoint", True)
    assert last.misconception and last.misconception.state == "improving"
    assert last.next_action and last.next_action.reason_code == "CHECKPOINTS_EXHAUSTED"
    assert last.next_action.lesson_ref == "lesson_fk_multiplicity@1"
    with Session(authored_db) as db, pytest.raises(AssessmentError, match="No checkpoint"):
        start_checkpoints(db, "a")


def test_learner_b_progresses_and_recovers_from_a_hard_mistake(authored_db: Engine) -> None:
    from .content_fixtures import add_progression_questions

    with Session(authored_db) as db, db.begin():
        add_progression_questions(db)
    topic = "er.entities"
    for correct in (False, True, False, True):
        outcome, state = take(authored_db, "a", topic, "practice", correct, tier="easy")
    assert state.distinct == 4
    assert outcome.next_action and outcome.next_action.difficulty == "medium"
    for _ in range(2):
        outcome, state = take(authored_db, "a", topic, "practice", True, tier="medium")
    assert state.distinct == 6 and state.band == "high"
    assert outcome.next_action and outcome.next_action.difficulty == "hard"
    outcome, state = take(authored_db, "a", topic, "practice", False, tier="hard")
    assert state.band == "medium"
    assert outcome.next_action and outcome.next_action.difficulty == "medium"
    for _ in range(2):
        outcome, state = take(authored_db, "a", topic, "practice", True, tier="medium")
    assert outcome.next_action and outcome.next_action.difficulty == "hard"
    for _ in range(2):
        outcome, state = take(authored_db, "a", topic, "practice", True, tier="hard")
    assert outcome.next_action and outcome.next_action.reason_code == "ADVANCE_TOPIC"
    assert outcome.next_action.subtopic_id != topic


def test_learner_c_uses_authored_medium_and_explores_after_bank_exhaustion(
    authored_db: Engine,
) -> None:
    topic = "relational.keys"
    result, state = take(authored_db, "a", topic, "diagnostic", True)
    assert result.next_action and result.next_action.difficulty == "easy"
    for _ in range(5):
        result, state = take(authored_db, "a", topic, "practice", True, tier="easy")
        assert result.misconception is None
    assert result.next_action and result.next_action.difficulty == "medium"
    result, state = take(authored_db, "a", topic, "practice", True, tier="medium")
    assert state.distinct == 7 and state.band == "high"
    assert result.next_action and result.next_action.reason_code == "EXPLORE_NEXT_TOPIC"
    assert result.next_action.subtopic_id != topic and result.misconception is None


def test_learners_d_and_e_repeat_without_inflation_and_explore_an_available_topic(
    authored_db: Engine,
) -> None:
    topic = "er.entities"
    first, before = take(authored_db, "a", topic, "practice", True)
    for _ in range(4):
        last, after = take(authored_db, "a", topic, "practice", True)
        assert after.score == before.score == 0.6 and after.distinct == 1
    assert first.next_action == last.next_action
    assert last.next_action and last.next_action.reason_code == "EXPLORE_NEXT_TOPIC"
    assert last.next_action.subtopic_id != topic
    with (
        Session(authored_db) as db,
        db.begin(),
        pytest.raises(AssessmentError, match="no eligible"),
    ):
        start_study(db, "a", "practice", topic=topic, fresh=True)
    _, assisted = take(authored_db, "b", topic, "practice", True, hinted=True)
    _, replayed = take(authored_db, "b", topic, "practice", True)
    assert assisted.distinct == replayed.distinct == 0
    assert assisted.score == replayed.score == 0.5


def test_learner_f_resolves_using_two_distinct_checkpoints(authored_db: Engine) -> None:
    topic = "relational.keys"
    first, _ = take(authored_db, "a", topic, "practice", False, tier="easy")
    second, _ = take(authored_db, "a", topic, "diagnostic", False)
    assert first.misconception and first.misconception.state == "possible"
    assert second.misconception and second.misconception.state == "active"
    improved, _ = take(authored_db, "a", topic, "checkpoint", True)
    resolved, final = take(authored_db, "a", topic, "checkpoint", True)
    assert improved.misconception and improved.misconception.state == "improving"
    assert resolved.misconception and resolved.misconception.state == "resolved"
    assert final.score == 0.5648
    assert resolved.next_action and resolved.next_action.action_type != "MISCONCEPTION_REMEDIATION"


def test_mastery_migration_replays_legacy_retries_and_preserves_due_date(
    authored_db: Engine,
) -> None:
    from app.db.models import Attempt, MasteryHistory
    from sqlalchemy import select

    topic = "er.entities"
    for _ in range(4):
        _, projected = take(authored_db, "a", topic, "practice", True)
    cfg = Config(str(ALEMBIC_INI))
    with authored_db.begin() as connection:
        cfg.attributes["connection"] = connection
        command.downgrade(cfg, "0007_ai_review")
    with Session(authored_db) as db:
        old = state_from_row(db.get(Mastery, ("a", topic, MODEL_NAME)))
        assert old.score == 0.7952
    with authored_db.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
    with Session(authored_db) as db:
        restored = state_from_row(db.get(Mastery, ("a", topic, MODEL_NAME)))
        assert restored == projected and old.review_due_at == restored.review_due_at
        assert len(list(db.scalars(select(Attempt)))) == 4
        assert len(list(db.scalars(select(MasteryHistory)))) == 4


def test_review_due_recomputed_without_a_new_submission(authored_db: Engine) -> None:
    topic = "relational.keys"
    submitted, sampled = take(authored_db, "a", topic, "diagnostic", True)
    assert sampled.review_due_at is not None
    with Session(authored_db) as db, db.begin():
        future = latest_recommendation(db, "a", now=sampled.review_due_at)
        assert future and future.action_type == "MIXED_REVIEW" and future.fresh
        assert future.subtopic_id == topic
        selected = start_study(db, "a", "review", topic=topic, fresh=True)
        assert selected.items and selected.items[0].question_ref not in (
            "q_keys_detector_tickets@1",
        )
    assert submitted.next_action != future


def test_sql_recommendation_opens_exact_available_exercise(
    authored_db: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.assessment import allocate_sql

    # Exercise grading is checked independently on supported worker platforms.
    monkeypatch.setattr("app.services.learning_state.worker_supported", lambda: True)
    topic = "sql.joins"
    take(authored_db, "a", topic, "diagnostic", True)
    take(authored_db, "a", topic, "practice", True, tier="easy")
    take(authored_db, "a", topic, "practice", True, tier="easy")
    result, _ = take(authored_db, "a", topic, "practice", True, tier="medium")
    next_action = result.next_action
    assert next_action is not None and next_action.action_type == "SQL_PRACTICE"
    assert next_action.question_id == "sql_customers_without_orders"
    with Session(authored_db) as db, db.begin():
        other = allocate_sql(db, "a", "sql_join_001")
        selected = allocate_sql(db, "a", next_action.question_id)
        assert selected.session_id != other.session_id
        assert selected.items[0].question_ref == "sql_customers_without_orders@1"
        assert allocate_sql(db, "a", next_action.question_id) == selected
    monkeypatch.setattr("app.services.learning_state.worker_supported", lambda: False)
    with Session(authored_db) as db:
        supported_fallback = latest_recommendation(db, "a")
    assert supported_fallback is not None and supported_fallback.action_type != "SQL_PRACTICE"
