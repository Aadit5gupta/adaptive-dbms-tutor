"""Measure hit@k and reciprocal rank against a labeled local lesson index."""

import argparse
import json
import sys
from pathlib import Path
from typing import Annotated, Literal

if __package__ in ("", None):
    project = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project), str(project / "backend")]

from app.core.config import Settings
from app.core.db import open_engine
from app.db.models import Passage
from app.services.retrieval import VOCAB, Retriever
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from content.schemas.models import TopicId, VersionRef
from scripts.validate_content import ROOT, ContentError, read_yaml


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    query: str
    topic_id: TopicId
    expected_lessons: Annotated[list[VersionRef], Field(min_length=1)]


class QuerySet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: Literal["draft", "author_verified", "independent_verified"]
    cases: Annotated[list[Case], Field(min_length=1)]


def evaluate(engine: Engine, retriever: Retriever, queries: QuerySet, k: int) -> dict[str, object]:
    with Session(engine) as db:
        installed = set(
            db.scalars(
                select(Passage.lesson_ref)
                .join(VOCAB, VOCAB.c.doc == Passage.id)
                .where(Passage.kind == "lesson")
                .distinct()
            )
        )

    missing = sorted(
        {ref for case in queries.cases for ref in case.expected_lessons if ref not in installed}
    )
    if missing:
        raise ContentError("Expected reviewed passages are missing from FTS: " + ", ".join(missing))
    if len({case.id for case in queries.cases}) != len(queries.cases):
        raise ContentError("Query cases must have unique IDs")

    rank_by_case: dict[str, int | None] = {}
    for case in queries.cases:
        hits = retriever.search(case.query, (case.topic_id,), k=k)
        rank_by_case[case.id] = next(
            (
                rank
                for rank, hit in enumerate(hits, 1)
                if hit.citation.lesson_ref in case.expected_lessons
            ),
            None,
        )

    ranks = [rank for rank in rank_by_case.values() if rank is not None]
    return {
        "label_review_status": queries.review_status,
        "queries": len(queries.cases),
        "k": k,
        "hit_rate": len(ranks) / len(queries.cases),
        "mean_reciprocal_rank": sum(1 / rank for rank in ranks) / len(queries.cases),
        "ranks": rank_by_case,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, choices=range(1, 7), default=4)
    parser.add_argument("--queries", type=Path, default=ROOT / "experiments/retrieval_queries.yaml")
    args = parser.parse_args()
    engine = open_engine(Settings().app_db)
    try:
        queries = QuerySet.model_validate(read_yaml(args.queries))
        result = evaluate(engine, Retriever(engine), queries, args.k)
    except (ContentError, ValidationError, SQLAlchemyError) as error:
        reason = (
            "The application database must be migrated and indexed."
            if isinstance(error, SQLAlchemyError)
            else str(error)
        )
        print(f"Retrieval evaluation blocked: {reason}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
