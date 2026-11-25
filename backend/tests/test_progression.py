"""Assessment and progression checks against the authored learner bank."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.db import open_engine
from app.db.models import User
from app.main import ALEMBIC_INI
from app.schemas.assessment import AnswerInput
from app.services.assessment import AssessmentError, submit_mcq
from app.services.curriculum import publish_from_disk
from app.services.study import start_study, study_session
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
