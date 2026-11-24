"""Opt-in real model integration check. It never pulls a model."""

import argparse
import asyncio
import sys
from pathlib import Path

if __package__ in ("", None):
    project = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project), str(project / "backend")]

from app.core.config import Settings
from app.core.db import open_engine
from app.providers.contracts import ProviderUnavailable, Turn, TutorContext
from app.providers.ollama import OllamaProvider
from app.schemas.tutor import TutorInput
from app.services.retrieval import Citation, PassageHit, Retriever
from app.services.tutor import TutorService


def isolated_passage() -> PassageHit:
    """Original test evidence used only for the provider smoke check."""
    return PassageHit(
        citation=Citation(
            id="ollama_smoke_left_join",
            kind="lesson",
            title="LEFT JOIN test explanation",
            url="https://www.sqlite.org/lang_select.html",
            attribution="Test-only explanation based on SQLite SELECT documentation",
            license_url=None,
            lesson_ref=None,
        ),
        topic_id="sql.joins",
        text="A LEFT JOIN keeps each left-side row even when there is no matching row on the right. For unmatched rows, SQLite returns NULL in the columns from the right side. INNER JOIN emits only the matching pairs.",
        rank=1,
    )


async def run(provider_only: bool, book: bool) -> None:
    settings = Settings()
    provider = OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    request = TutorInput(
        query="Why would a report use LEFT JOIN?", topic_id="sql.joins", mode="explain"
    )
    if book:
        request = TutorInput(
            query="What happens to the two maintenance jobs if their machine is deleted "
            "and the foreign key uses ON DELETE CASCADE?",
            topic_id="relational.keys",
            mode="explain",
        )
    if provider_only:
        source = isolated_passage()
        reply = await provider.respond(TutorContext(request, (source,)))
        if source.citation.id not in reply.passage_ids:
            raise ProviderUnavailable("the model did not cite the supplied smoke passage")
        print(f"{settings.ollama_model} returned a grounded reply using test-only evidence.")
        print(reply.text)
        followup = TutorInput(
            query="Why does a customer with no matching order still appear in the report, and what values appear in the order columns?",
            topic_id="sql.joins",
            mode="ask",
        )
        next_answer = await provider.respond(
            TutorContext(
                followup,
                (source,),
                history=(Turn("user", request.query), Turn("assistant", reply.text)),
            )
        )
        if (
            source.citation.id not in next_answer.passage_ids
            or "null" not in next_answer.text.lower()
        ):
            raise ProviderUnavailable(
                "the follow-up did not cite the test evidence and explain NULL"
            )
        print("Follow-up:")
        print(next_answer.text)
        return

    engine = open_engine(settings.app_db)
    try:
        reply_ = await TutorService(Retriever(engine), provider).answer(request)
    finally:
        engine.dispose()
    if reply_.degraded or reply_.provider != "ollama" or not reply_.citations:
        raise ProviderUnavailable(f"reviewed-corpus integration did not pass ({reply_.status})")
    if book and (
        not any(
            citation.kind == "book"
            and citation.id.startswith("runestone_practical_db:runestone_foreign_key_actions:")
            for citation in reply_.citations
        )
        or "delet" not in reply_.answer.casefold()
        or "job" not in reply_.answer.casefold()
    ):
        raise ProviderUnavailable(
            "the model did not explain the cascade using the Runestone excerpt"
        )
    print(f"{settings.ollama_model} answered from the approved local corpus:")
    print(reply_.answer)
    for citation in reply_.citations:
        print(f"Source: {citation.title} — {citation.url}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    checks = parser.add_mutually_exclusive_group()
    checks.add_argument(
        "--provider-only",
        action="store_true",
        help="verify the transport/model with one test passage",
    )
    checks.add_argument("--book", action="store_true", help="verify a real textbook citation")
    args = parser.parse_args()
    try:
        asyncio.run(run(args.provider_only, args.book))
    except (ProviderUnavailable, ValueError) as error:
        print(f"Ollama check blocked: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
