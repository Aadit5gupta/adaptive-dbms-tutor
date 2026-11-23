from pathlib import Path
from typing import Any

import yaml

SOURCE = {"kind": "authored", "factual_reference_url": "https://example.invalid/dbms"}
APPROVED = {
    "review_status": "author_verified",
    "author": "Synthetic test author",
    "verified_by": "Synthetic test reviewer",
    "verified_on": "2026-11-23",
    "second_review": False,
    "ai_assisted": False,
    "source": SOURCE,
}


def save(root: Path, filename: str, value: Any) -> Path:
    path = root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value), encoding="utf-8")
    return path


def mcq(id_: str, topic: str, pool: str = "practice", code: str | None = None) -> dict[str, Any]:
    return {
        **APPROVED,
        "id": id_,
        "type": "mcq",
        "subtopic_id": topic,
        "version": 1,
        "pool": pool,
        "difficulty": "easy",
        "stem": "Synthetic question",
        "explanation": "Synthetic explanation",
        "options": [
            {"text": "A", "correct": True},
            {"text": "B", "correct": False, "misconception_code": code},
            {"text": "C", "correct": False},
            {"text": "D", "correct": False},
        ],
    }
