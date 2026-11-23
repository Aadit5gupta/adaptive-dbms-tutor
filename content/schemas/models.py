"""Versioned curriculum and review contracts shared by tooling and the app."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
LogicalId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$")]
VersionRef = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*@[1-9][0-9]*$")]
TopicId = Annotated[str, StringConstraints(pattern=r"^[a-z_]+\.[a-z][a-z0-9_]*$")]
Code = Annotated[str, StringConstraints(pattern=r"^[A-Z]+(?:-[A-Z]+)*-[0-9]+$")]
Pool = Literal["practice", "diagnostic", "checkpoint", "pre_test_a", "post_test_b"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Source(Record):
    kind: Literal["authored", "section"]
    factual_reference_url: HttpUrl
    reproduced_book_text: bool = False
    source_section_clearance_id: LogicalId | None = None

    @model_validator(mode="after")
    def require_clearance(self) -> "Source":
        if (self.kind == "section" or self.reproduced_book_text) and (
            self.source_section_clearance_id is None
        ):
            raise ValueError("reproduced material requires source_section_clearance_id")
        return self


class Reviewed(Record):
    subtopic_id: TopicId
    review_status: Literal["draft", "author_verified", "independent_verified"]
    source: Source
    author: Text | None = None
    verified_by: Text | None = None
    verified_on: date | None = None
    second_review: bool = False
    ai_assisted: bool

    @property
    def reviewed(self) -> bool:
        return self.review_status != "draft"

    @model_validator(mode="after")
    def require_review(self) -> "Reviewed":
        if self.reviewed:
            if not all((self.author, self.verified_by, self.verified_on)):
                raise ValueError("reviewed records require author, verified_by and verified_on")
            if "second_review" not in self.model_fields_set:
                raise ValueError("reviewed records require explicit second_review")
            if self.second_review != (self.review_status == "independent_verified"):
                raise ValueError("second_review disagrees with review_status")
            if self.second_review and self.author == self.verified_by:
                raise ValueError("independent reviewer must differ from the author")
        elif self.verified_by or self.verified_on or self.second_review:
            raise ValueError("draft cannot have verification metadata")
        return self


class Versioned(Reviewed):
    id: LogicalId
    version: Annotated[int, Field(strict=True, gt=0)]

    @property
    def ref(self) -> str:
        return f"{self.id}@{self.version}"


class Lesson(Versioned):
    title: Text
    body_markdown: Text


class Question(Versioned):
    pool: Pool
    difficulty: Literal["easy", "medium", "hard"]


class Option(Record):
    text: Text
    correct: bool
    misconception_code: Code | None = None


class MCQ(Question):
    type: Literal["mcq"]
    stem: Text
    options: Annotated[tuple[Option, ...], Field(min_length=4, max_length=4)]
    explanation: Text

    @model_validator(mode="after")
    def validate_options(self) -> "MCQ":
        if sum(option.correct for option in self.options) != 1:
            raise ValueError("exactly one option must be correct")
        if len({option.text.casefold() for option in self.options}) != 4:
            raise ValueError("duplicate option text")
        for option in self.options:
            if option.misconception_code and (
                option.correct or self.pool not in ("diagnostic", "practice")
            ):
                raise ValueError(
                    "misconception mappings require a wrong practice/diagnostic option"
                )
        return self


class Comparison(Record):
    order_sensitive: bool
    duplicate_sensitive: bool
    column_names_matter: bool


class ExpectedResult(Record):
    fixture: Text
    expected_result_file: Text


class SQLQuestion(Question):
    type: Literal["sql"]
    dialect: Literal["sqlite"]
    min_sqlite_version: Annotated[str, StringConstraints(pattern=r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$")]
    prompt: Text
    visible_fixture: Text
    hidden_fixtures: Annotated[tuple[Text, ...], Field(min_length=1)]
    reference_query: Text
    compare: Comparison
    expected_results: tuple[ExpectedResult, ...]

    @property
    def fixtures(self) -> tuple[str, ...]:
        return (self.visible_fixture, *self.hidden_fixtures)

    @model_validator(mode="after")
    def require_fixture_coverage(self) -> "SQLQuestion":
        expected = [entry.fixture for entry in self.expected_results]
        if len(set(self.fixtures)) != len(self.fixtures):
            raise ValueError("visible and hidden fixtures must be distinct")
        if sorted(expected) != sorted(self.fixtures):
            raise ValueError("provide one expected result for every fixture")
        if len({entry.expected_result_file for entry in self.expected_results}) != len(expected):
            raise ValueError("each fixture needs a separate expected result file")
        return self


class EvidenceRule(Record):
    min_distinct_logical_questions: Annotated[int, Field(strict=True, ge=2)]
    ignore_after_revealing_hint: Literal[True]


class Misconception(Reviewed):
    code: Code
    name: Text
    explanation: Text
    enabled: bool
    evidence_rule: EvidenceRule
    detector_question_refs: tuple[VersionRef, ...]
    remediation_lesson_ref: VersionRef
    checkpoint_question_refs: tuple[VersionRef, ...]
    retrieval_query: Text


class Domain(Record):
    id: LogicalId
    title: Text
    subtopics: Annotated[dict[TopicId, Text], Field(min_length=1)]


class Prerequisite(Record):
    subtopic_id: TopicId
    prerequisite_id: TopicId
