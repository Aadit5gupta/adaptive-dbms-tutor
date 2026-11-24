import asyncio
import json

import httpx
import pytest
from app.providers.contracts import ProviderUnavailable, Turn, TutorContext
from app.providers.ollama import OllamaProvider
from app.schemas.tutor import TutorInput
from app.services.retrieval import Citation, PassageHit

PASSAGE = PassageHit(
    citation=Citation(
        id="test_passage",
        kind="lesson",
        title="Synthetic test source",
        url="https://example.invalid/lesson",
        attribution="Synthetic",
        license_url=None,
        lesson_ref=None,
    ),
    topic_id="sql.joins",
    text="Preserve unmatched rows from the left relation.",
    rank=1,
)
CONTEXT = TutorContext(TutorInput(query="Why use LEFT JOIN?", topic_id="sql.joins"), (PASSAGE,))


def packet(ids: tuple[str, ...] = ("s1",)) -> dict[str, object]:
    return {
        "done": True,
        "done_reason": "stop",
        "message": {
            "content": json.dumps({"answer": "Keeps unmatched left rows.", "source_ids": ids})
        },
    }


def test_provider_sends_bounded_local_payload_and_maps_source_ids() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://127.0.0.1:11434/api/chat"
        assert request.method == "POST"
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3:1.7b"
        assert payload["stream"] is False and payload["think"] is False
        assert payload["options"]["num_ctx"] == 4096
        assert payload["options"]["num_predict"] == 384
        user_payload = payload["messages"][1]["content"]
        assert len(user_payload.encode("utf-8")) <= 3180
        data = json.loads(user_payload)
        assert len(data["recent_turns"]) <= 6 and len(data["evidence"]) <= 4
        assert data["evidence"][0]["id"] == "s1"
        return httpx.Response(200, json=packet())

    provider = OllamaProvider(
        "http://localhost:11434", "qwen3:1.7b", transport=httpx.MockTransport(handle)
    )
    large = TutorContext(
        TutorInput(query="\\n" * 300, topic_id="sql.joins"),
        tuple([PASSAGE] * 8),
        history=tuple(Turn("user", '"\\' * 360) for _ in range(12)),
        learner_context="X" * 1000,
    )
    result = asyncio.run(provider.respond(large))
    assert result.passage_ids == ("test_passage",)


@pytest.mark.parametrize(
    "mode",
    ["missing", "fabricated", "malformed", "unfinished", "too_long", "connection"],
)
def test_provider_failures_are_eligible_for_curated_fallback(mode: str) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if mode == "missing":
            return httpx.Response(404)
        if mode == "fabricated":
            return httpx.Response(200, json=packet(("unavailable-source",)))
        if mode == "unfinished":
            return httpx.Response(200, json={**packet(), "done_reason": "length"})
        if mode == "too_long":
            return httpx.Response(200, content=b"x" * 25_000)
        if mode == "connection":
            raise httpx.ConnectError("synthetic unavailable host", request=request)
        return httpx.Response(200, content=b"not json")

    provider = OllamaProvider(
        "http://127.0.0.1", "qwen3:1.7b", transport=httpx.MockTransport(handle)
    )
    with pytest.raises(ProviderUnavailable):
        asyncio.run(provider.respond(CONTEXT))


def test_provider_rejects_cloud_and_non_loopback_endpoints() -> None:
    with pytest.raises(ValueError, match="loopback"):
        OllamaProvider("https://example.com", "qwen3:1.7b")
    with pytest.raises(ValueError, match="local tagged model"):
        OllamaProvider("http://127.0.0.1", "qwen3:cloud")


def test_busy_inference_degrades_immediately_and_timeout_releases_slot() -> None:
    async def run() -> None:
        entered = asyncio.Event()

        async def slow(_: httpx.Request) -> httpx.Response:
            entered.set()
            await asyncio.sleep(1)
            return httpx.Response(200, json=packet())

        provider = OllamaProvider(
            "http://127.0.0.1", "qwen3:1.7b", transport=httpx.MockTransport(slow), timeout=0.04
        )
        first = asyncio.create_task(provider.respond(CONTEXT))
        await entered.wait()
        with pytest.raises(ProviderUnavailable, match="busy"):
            await provider.respond(CONTEXT)
        with pytest.raises(ProviderUnavailable):
            await first
        assert not provider.inference.locked()

    asyncio.run(run())


def test_sql_feedback_keeps_the_counting_rule_in_a_typical_lesson() -> None:
    from app.providers.ollama import chat_payload

    rule = "COUNT(column) skips NULL, while COUNT(*) counts every result row."
    passage = PASSAGE.model_copy(update={"text": ("An unmatched left row remains. " * 13) + rule})
    context = TutorContext(
        TutorInput(query="Why do I get one for a customer with no orders?", mode="sql_feedback"),
        (passage,),
        learner_context="Exercise goal: Return all customers and the number of orders for each.",
    )
    payload, _ = chat_payload(context, "qwen3:1.7b")
    data = json.loads(payload["messages"][1]["content"])
    assert rule in data["evidence"][0]["text"]
    assert "Exercise goal:" in data["learner"]


def test_chapter_comparison_keeps_both_lesson_examples_in_model_context() -> None:
    from app.providers.ollama import MAX_USER_PROMPT_BYTES, chat_payload
    from app.services.source_import import chunk_text

    from scripts.validate_content import load_content

    lesson = load_content().lessons["lesson_dependency_chain@1"]
    passage = PASSAGE.model_copy(
        update={"text": chunk_text(lesson.body_markdown)[0], "topic_id": lesson.subtopic_id}
    )
    context = TutorContext(
        TutorInput(
            query="Can you explain partial and transitive dependencies using the same simple example?",
            topic_id=lesson.subtopic_id,
        ),
        (passage,),
        history=tuple(Turn("user", '"\\' * 180) for _ in range(6)),
        learner_context="Experience: beginner. " * 40,
    )
    payload, _ = chat_payload(context, "qwen3:1.7b")
    user_content = payload["messages"][1]["content"]
    data = json.loads(user_content)
    assert len(user_content.encode("utf-8")) <= MAX_USER_PROMPT_BYTES
    assert len(data["recent_turns"]) < len(context.history)
    assert "(`musician_id`, `festival_id`)" in data["evidence"][0]["text"]
    assert "festival_id → venue_id → postal_code" in data["evidence"][0]["text"]
