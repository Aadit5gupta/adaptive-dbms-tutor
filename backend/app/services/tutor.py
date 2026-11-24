"""Grounded tutoring; returned references come from retrieval metadata."""

import re

from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from app.providers.contracts import ProviderUnavailable, Turn, TutorContext, TutorProvider
from app.providers.curated import CuratedProvider
from app.schemas.tutor import TutorInput, TutorReply
from app.services.retrieval import PassageHit, Retriever
from scripts.validate_content import ContentError

MODEL_CITATION = re.compile(r"https?://|\bwww\.|\[\s*\d+\s*\]", re.IGNORECASE)


# Assessment guidance is deliberately independent of generated text and stored answer keys.
ASSESSMENT_HINTS = (
    "Restate what the result needs to include. Which property or rule should you check first?",
    "List the conditions in the question. Check each option against every condition and set aside any option that breaks one.",
    "Make a tiny example with your own values. Trace the remaining choices against it, including a boundary case.",
)


# Each clue suggests a reasoning step using only the approved topic and learner's words.
ASSESSMENT_CLUES: dict[str, tuple[tuple[set[str], str], ...]] = {
    "relational.keys": (
        (
            {"duplicate", "duplicates", "repeated", "repeat", "repeats", "twice", "unique"},
            (
                "Compare the column that stores the reference with the column it points to. "
                "Which column does each constraint describe?"
            ),
        ),
        (
            {"foreign", "reference", "references", "club", "matching", "missing", "parent", "null"},
            (
                "Pick one row with a reference. Identify the column that stores the value "
                "and the table where you would look for a match."
            ),
        ),
        (
            {"candidate", "composite", "superkey", "primary", "minimal"},
            (
                "Try removing one column from the proposed key. Can you construct two "
                "allowed rows that would then be indistinguishable?"
            ),
        ),
    ),
    "sql.joins": (
        (
            {"inner", "left", "join", "joins", "matching", "unmatched", "null"},
            (
                "Draw one row from the left table that has no match. Trace what each "
                "proposed join would do with that row."
            ),
        ),
    ),
    "sql.aggregation": (
        (
            {"count", "aggregate", "group", "grouping", "having", "null"},
            (
                "Make a tiny group with a missing value. Trace which rows or values "
                "each expression checks before comparing the results."
            ),
        ),
    ),
    "sql.null": (
        (
            {"null", "unknown", "missing", "equal", "comparison"},
            (
                "Evaluate the condition for one known value and one missing value. "
                "Write the result of each comparison before deciding which rows pass."
            ),
        ),
    ),
    "sql.subqueries": (
        (
            {"exists", "subquery", "correlated", "matching"},
            (
                "Pick one outer row and trace the inner query with that row's values. "
                "What does the outer condition look for in the result?"
            ),
        ),
    ),
    "normalization.normal_forms": (
        (
            {"partial", "transitive", "dependency", "normalize", "normalization", "key"},
            (
                "Draw an arrow from each determinant to what it determines. Follow the "
                "arrows from the key and check whether you need every column or an intermediate step."
            ),
        ),
    ),
    "transactions.acid": (
        (
            {"atomicity", "rollback", "commit", "durability", "isolation", "transaction"},
            (
                "Trace what would happen if execution stopped at the point described. "
                "Which changes should be visible to the people in the example?"
            ),
        ),
    ),
    "indexing.plans": (
        (
            {"scan", "search", "plan", "index", "sqlite"},
            (
                "Look at the operation reported for the table. Compare how much of the "
                "table each proposed access path would have to examine."
            ),
        ),
    ),
}


def assessment_hint(request: TutorInput) -> str:
    prepared = ASSESSMENT_HINTS[request.hint_level - 1]
    if not request.query:
        return prepared
    words = set(re.findall(r"[a-z]+", request.query.casefold()))
    for triggers, clue in ASSESSMENT_CLUES.get(request.topic_id or "", ()):
        if words & triggers:
            return clue
    return f"I don’t have a specific clue for that wording. {prepared}"


class TutorService:
    def __init__(self, retriever: Retriever, provider: TutorProvider | None = None):
        self.retriever = retriever
        self.provider = provider
        self.curated = CuratedProvider()

    async def evidence(self, request: TutorInput) -> list[PassageHit]:
        topics = (request.topic_id,) if request.topic_id else ()
        try:
            hits = await run_in_threadpool(self.retriever.search, request.query, topics, 4)
        except (SQLAlchemyError, ContentError):
            hits = []
        if topics:
            selected = [hit for hit in hits if hit.topic_id == request.topic_id]
            if selected:
                return selected
            try:
                fallback = await run_in_threadpool(self.retriever.topic_passages, topics[0])
            except SQLAlchemyError:
                fallback = []
            if fallback:
                return fallback
        return hits

    async def answer(
        self,
        request: TutorInput,
        *,
        history: tuple[Turn, ...] = (),
        learner_context: str = "",
        explain_join_count: bool = False,
    ) -> TutorReply:
        if request.mode == "hint" and request.item_id is not None:
            return TutorReply(
                answer=assessment_hint(request),
                citations=[],
                mode="hint",
                provider="curated",
                degraded=False,
                status="ok",
                topic_id=request.topic_id,
            )
        hits = await self.evidence(request)
        if explain_join_count:
            hits = [hit for hit in hits if hit.citation.lesson_ref == "lesson_join_unmatched@1"]
            if hits:
                return TutorReply(
                    answer=(
                        "Group by the customer ID so customers with the same name stay separate. "
                        "A LEFT JOIN keeps the customer with no orders, so COUNT(*) counts that "
                        "preserved row. Count the order ID instead. It is NULL on the unmatched "
                        "row, so it contributes zero."
                    ),
                    citations=[hits[0].citation],
                    mode=request.mode,
                    provider="curated",
                    degraded=False,
                    status="ok",
                    topic_id=request.topic_id,
                )
        if not hits:
            return TutorReply(
                topic_id=request.topic_id,
                answer="I could not find reviewed material for this question. Try naming a specific DBMS topic or check the Library.",
                citations=[],
                mode=request.mode,
                provider="curated",
                degraded=True,
                status="no_evidence",
            )

        context = TutorContext(
            request=request,
            passages=tuple(hits[:4]),
            history=tuple(Turn(turn.role, turn.text[:450]) for turn in history[-6:]),
            learner_context=learner_context[:400],
        )
        citations = {hit.citation.id: hit.citation for hit in context.passages}
        use_model = self.provider is not None
        if self.provider is not None:
            try:
                candidate = await self.provider.respond(context)
                ids = tuple(dict.fromkeys(candidate.passage_ids))
                answer = candidate.text.strip()
                if (
                    answer
                    and len(answer) <= 2_400
                    and ids
                    and all(ref in citations for ref in ids)
                    and not MODEL_CITATION.search(answer)
                ):
                    return TutorReply(
                        topic_id=request.topic_id or context.passages[0].topic_id,
                        answer=answer,
                        citations=[citations[ref] for ref in ids],
                        mode=request.mode,
                        provider="ollama",
                        degraded=False,
                        status="ok",
                    )
            except ProviderUnavailable:
                pass

        curated = await self.curated.respond(context)
        return TutorReply(
            topic_id=request.topic_id or context.passages[0].topic_id,
            answer=curated.text,
            citations=[citations[ref] for ref in curated.passage_ids],
            mode=request.mode,
            provider="curated",
            degraded=use_model,
            status="ai_unavailable" if use_model else "ok",
        )
