"""Validate curriculum, versioned content, and explicit release-stage minima."""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, TypeVar

import yaml
from pydantic import Field, TypeAdapter, ValidationError

ROOT = Path(__file__).resolve().parents[1]
if __package__ in ("", None):
    sys.path.insert(0, str(ROOT))

from content.schemas.models import (
    MCQ,
    Domain,
    Lesson,
    Misconception,
    Prerequisite,
    Reviewed,
    SQLQuestion,
)
from content.schemas.rights import Catalog, Clearance

Question = Annotated[MCQ | SQLQuestion, Field(discriminator="type")]
QUESTIONS = TypeAdapter(list[Question])
LESSONS = TypeAdapter(list[Lesson])
RULES = TypeAdapter(list[Misconception])
DOMAINS = TypeAdapter(list[Domain])
PREREQUISITES = TypeAdapter(list[Prerequisite])
REQUIRED_DOMAINS = {
    "er",
    "relational",
    "sql",
    "normalization",
    "transactions",
    "concurrency",
    "indexing",
}
Stage = Literal["S1", "S4"]
T = TypeVar("T")


class ContentError(ValueError):
    """Invalid content that must be corrected before distribution."""


@dataclass(frozen=True)
class Counts:
    reviewed_mcqs: int
    ordinary_practice_mcqs: int
    reviewed_lessons: int
    checked_sql_tasks: int
    enabled_patterns: int


@dataclass(frozen=True)
class Content:
    catalog: Catalog
    domains: list[Domain]
    prerequisites: list[Prerequisite]
    questions: dict[str, MCQ | SQLQuestion]
    lessons: dict[str, Lesson]
    rules: dict[str, Misconception]
    counts: Counts


def read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ContentError(f"{path}: {error}") from error


def read_records(path: Path, schema: TypeAdapter[list[T]]) -> list[T]:
    try:
        return schema.validate_python(read_yaml(path))
    except ValidationError as error:
        messages = [
            f"{'.'.join(map(str, issue['loc']))}: {issue['msg']}"
            for issue in error.errors(include_input=False)
        ]
        raise ContentError(f"{path}: {'; '.join(messages)}") from error


def check_graph(domains: list[Domain], edges: list[Prerequisite]) -> set[str]:
    ids = [domain.id for domain in domains]
    if set(ids) != REQUIRED_DOMAINS or len(ids) != len(REQUIRED_DOMAINS):
        raise ContentError("topics.yaml: expected exactly seven distinct canonical domains")

    topics = {topic for domain in domains for topic in domain.subtopics}
    for domain in domains:
        for topic in domain.subtopics:
            if topic.partition(".")[0] != domain.id:
                raise ContentError(f"topics.yaml: {topic} must belong to {domain.id}")

    graph: dict[str, set[str]] = {topic: set() for topic in topics}
    for edge in edges:
        node, parent = edge.subtopic_id, edge.prerequisite_id
        if node not in topics or parent not in topics or parent in graph[node]:
            raise ContentError(f"prerequisites.yaml: invalid or duplicate edge {node} -> {parent}")
        graph[node].add(parent)

    checked: set[str] = set()
    active: set[str] = set()

    def visit(topic: str) -> None:
        if topic in active:
            raise ContentError(f"prerequisites.yaml: cycle involving {topic}")
        if topic not in checked:
            active.add(topic)
            for parent in sorted(graph[topic]):
                visit(parent)
            active.remove(topic)
            checked.add(topic)

    for topic in sorted(topics):
        visit(topic)
    return topics


def require_topic_and_source(
    record: Reviewed, topics: set[str], clearances: dict[str, Clearance], label: str
) -> None:
    if record.subtopic_id not in topics:
        raise ContentError(f"{label}: unknown subtopic {record.subtopic_id}")
    source = record.source
    if source.source_section_clearance_id:
        clearance = clearances.get(source.source_section_clearance_id)
        if (
            clearance is None
            or clearance.approved_content_hash != source.source_section_content_hash
            or clearance.section_url != source.factual_reference_url
        ):
            raise ContentError(f"{label}: source URL and hash must match an approved clearance")


def safe_path(root: Path, value: str, directory: str, suffix: str) -> Path:
    parent = (root / directory).resolve()
    path = (root / value).resolve()
    if (
        not parent.is_relative_to(root.resolve())
        or not path.is_relative_to(parent)
        or path.suffix != suffix
        or not path.is_file()
    ):
        raise ContentError(f"{value}: expected existing {suffix} file under {directory}")
    return path


def check_sql_reference(root: Path, question: SQLQuestion) -> None:
    """Check trusted, authored reference files offline against independently listed rows."""
    minimum = tuple(map(int, question.min_sqlite_version.split(".")))
    if sqlite3.sqlite_version_info < minimum:
        raise ContentError(f"{question.ref}: requires SQLite {question.min_sqlite_version}")
    for expected in question.expected_results:
        fixture = safe_path(root, expected.fixture, "content/sql_fixtures", ".sql")
        result = safe_path(root, expected.expected_result_file, "tests/fixtures/expected", ".json")
        try:
            rows = json.loads(result.read_text(encoding="utf-8"))
            with closing(sqlite3.connect(":memory:")) as db:
                db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1_000_000)
                db.set_progress_handler(lambda: 1, 500_000)
                db.executescript(fixture.read_text(encoding="utf-8"))
                db.execute("PRAGMA query_only = ON")
                cursor = db.execute(question.reference_query)
                actual = cursor.fetchmany(1_001)
                columns = [column[0] for column in cursor.description or ()]
            if question.compare.column_names_matter:
                if not isinstance(rows, dict) or rows.get("columns") != columns:
                    raise ValueError("reference query does not match expected columns")
                rows = rows.get("rows")
            if not isinstance(rows, list) or len(rows) > 1_000:
                raise ValueError("expected results must be a list of at most 1000 rows")
            if not all(isinstance(row, list) for row in rows):
                raise ValueError("expected results must consist of row arrays")
            target = [tuple(row) for row in rows]
            comparable = actual
            if not question.compare.duplicate_sensitive:
                comparable = list(dict.fromkeys(comparable))
                target = list(dict.fromkeys(target))
            matches = (
                comparable == target
                if question.compare.order_sensitive
                else Counter(comparable) == Counter(target)
            )
            if len(actual) > 1_000 or not matches:
                raise ValueError("reference query does not match expected results")
        except (OSError, sqlite3.Error, ValueError, TypeError) as error:
            raise ContentError(f"{question.ref}: {expected.fixture}: {error}") from error


def check_rule(
    rule: Misconception,
    questions: dict[str, MCQ | SQLQuestion],
    lessons: dict[str, Lesson],
) -> set[str]:
    lesson = lessons.get(rule.remediation_lesson_ref)
    if lesson is None or lesson.subtopic_id != rule.subtopic_id:
        raise ContentError(f"{rule.code}: missing remediation lesson in the rule's subtopic")
    if rule.enabled and (not rule.reviewed or not lesson.reviewed):
        raise ContentError(f"{rule.code}: enabled rule and remediation lesson require human review")

    ids: set[str] = set()
    for ref in rule.detector_question_refs:
        question = questions.get(ref)
        if (
            not isinstance(question, MCQ)
            or question.pool not in ("diagnostic", "practice")
            or question.subtopic_id != rule.subtopic_id
            or (rule.enabled and not question.reviewed)
            or not any(option.misconception_code == rule.code for option in question.options)
        ):
            raise ContentError(f"{rule.code}: {ref} is not an eligible mapped detector")
        if question.id in ids:
            raise ContentError(f"{rule.code}: detector logical IDs must be distinct")
        ids.add(question.id)

    checkpoints: set[str] = set()
    for ref in rule.checkpoint_question_refs:
        question = questions.get(ref)
        if (
            not isinstance(question, MCQ)
            or question.pool != "checkpoint"
            or question.subtopic_id != rule.subtopic_id
            or question.id in ids | checkpoints
            or (rule.enabled and not question.reviewed)
        ):
            raise ContentError(
                f"{rule.code}: {ref} is not an eligible distinct reserved checkpoint"
            )
        checkpoints.add(question.id)

    if rule.enabled and (
        len(ids) < rule.evidence_rule.min_distinct_logical_questions or len(checkpoints) < 2
    ):
        raise ContentError(
            f"{rule.code}: enabled rule needs distinct detectors and two checkpoints"
        )
    return checkpoints


def load_content(root: Path = ROOT) -> Content:
    content = root / "content"
    manifest = content / "manifests/books.yaml"
    try:
        catalog = Catalog.model_validate(read_yaml(manifest))
    except ValidationError as error:
        raise ContentError(f"{manifest}: {error}") from error
    clearances = catalog.approved_clearances
    domains = read_records(content / "curriculum/topics.yaml", DOMAINS)
    prerequisites = read_records(content / "curriculum/prerequisites.yaml", PREREQUISITES)
    topics = check_graph(domains, prerequisites)

    questions: dict[str, MCQ | SQLQuestion] = {}
    identities: dict[str, tuple[str, str, str]] = {}
    for path in sorted((content / "questions").glob("*.yaml")):
        for question in read_records(path, QUESTIONS):
            require_topic_and_source(question, topics, clearances, f"{path}: {question.ref}")
            if question.ref in questions:
                raise ContentError(f"{path}: duplicate question version {question.ref}")
            identity = (question.type, question.subtopic_id, question.pool)
            if identities.setdefault(question.id, identity) != identity:
                raise ContentError(
                    f"{path}: {question.id} changes type, topic or pool across versions"
                )
            if isinstance(question, SQLQuestion):
                check_sql_reference(root, question)
            questions[question.ref] = question

    lessons: dict[str, Lesson] = {}
    lesson_topics: dict[str, str] = {}
    for path in sorted((content / "lessons").glob("*.yaml")):
        for lesson in read_records(path, LESSONS):
            require_topic_and_source(lesson, topics, clearances, f"{path}: {lesson.ref}")
            if lesson.ref in lessons:
                raise ContentError(f"{path}: duplicate lesson version {lesson.ref}")
            if lesson_topics.setdefault(lesson.id, lesson.subtopic_id) != lesson.subtopic_id:
                raise ContentError(f"{path}: {lesson.id} changes topic across versions")
            lessons[lesson.ref] = lesson

    rule_file = content / "misconceptions.yaml"
    rules: dict[str, Misconception] = {}
    reserved: set[str] = set()
    for rule in read_records(rule_file, RULES) if rule_file.exists() else ():
        require_topic_and_source(rule, topics, clearances, rule.code)
        if rule.code in rules:
            raise ContentError(f"{rule_file}: duplicate code {rule.code}")
        checkpoints = check_rule(rule, questions, lessons)
        if rule.enabled:
            if reserved & checkpoints:
                raise ContentError(f"{rule.code}: checkpoint logical ID already reserved")
            reserved.update(checkpoints)
        rules[rule.code] = rule

    detectors: set[str] = set()
    for question in questions.values():
        if isinstance(question, MCQ):
            for option in question.options:
                if option.misconception_code:
                    rule_for_option = rules.get(option.misconception_code)
                    if (
                        rule_for_option is None
                        or rule_for_option.subtopic_id != question.subtopic_id
                    ):
                        raise ContentError(
                            f"{question.ref}: unknown or incompatible misconception mapping"
                        )
                    detectors.add(question.id)

    counts = Counts(
        reviewed_mcqs=len({q.id for q in questions.values() if isinstance(q, MCQ) and q.reviewed}),
        ordinary_practice_mcqs=len(
            {
                q.id
                for q in questions.values()
                if isinstance(q, MCQ)
                and q.reviewed
                and q.pool == "practice"
                and q.id not in detectors
            }
        ),
        reviewed_lessons=len({lesson.id for lesson in lessons.values() if lesson.reviewed}),
        checked_sql_tasks=len(
            {q.id for q in questions.values() if isinstance(q, SQLQuestion) and q.reviewed}
        ),
        enabled_patterns=sum(rule.enabled for rule in rules.values()),
    )
    return Content(catalog, domains, prerequisites, questions, lessons, rules, counts)


def check_stage(counts: Counts, stage: Stage) -> None:
    minima = Counts(12, 4, 2, 1, 2) if stage == "S1" else Counts(30, 4, 6, 6, 3)
    actual = asdict(counts)
    missing = [
        f"{key}={actual[key]} (need {minimum})"
        for key, minimum in asdict(minima).items()
        if actual[key] < minimum
    ]
    if missing:
        raise ContentError(f"{stage} content gate: " + ", ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="check all structural contracts")
    parser.add_argument("--stage", choices=("S1", "S4"))
    args = parser.parse_args()
    try:
        content = load_content()
        print(
            f"catalog_books={len(content.catalog.books)}, cleared_sections={len(content.catalog.approved_clearances)}"
        )
        print(", ".join(f"{key}={value}" for key, value in asdict(content.counts).items()))
        if args.stage:
            check_stage(content.counts, args.stage)
    except ContentError as error:
        print(error, file=sys.stderr)
        return 1
    print("Content validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
