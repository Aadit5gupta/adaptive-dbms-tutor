"""Replay synthetic evidence sequences through the deterministic policy."""

import json
import sys
from pathlib import Path

if __package__ in ("", None):
    project = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project), str(project / "backend")]

from app.services.adaptive import PolicyInput, Remediation, choose_next
from app.services.mastery import AttemptEvidence, MasteryState, update_mastery
from app.services.misconceptions import Signal, evaluate_hypothesis


def simulate() -> dict[str, object]:
    outcomes: dict[str, object] = {}
    events = {
        "three_independent_correct": [(True, True)] * 3,
        "one_correct_repeated": [(True, True), (True, False), (True, False)],
        "two_independent_detector_errors": [(False, True)] * 2,
    }
    for label, answers in events.items():
        state = MasteryState()
        scores = []
        for index, (correct, independent) in enumerate(answers):
            state = update_mastery(state, AttemptEvidence(correct, independent, index))
            scores.append(state.score)
        remediation: tuple[Remediation, ...] = ()
        if label == "two_independent_detector_errors":
            signal = evaluate_hypothesis(
                [Signal("one", "detector_wrong"), Signal("two", "detector_wrong")]
            )
            if signal.state == "active":
                remediation = (
                    Remediation("KEYS-02", "Repeated child values", "relational.keys", "lesson@1"),
                )
        action = choose_next(
            PolicyInput(
                "relational.keys",
                state,
                remediation=remediation,
                practice_difficulties=("easy", "medium"),
                fresh_practice=True,
            )
        )
        outcomes[label] = {
            "scores": scores,
            "confidence": state.confidence,
            "distinct_answers": state.distinct,
            "action": action.action_type,
            "reason_code": action.reason_code,
        }
    return {"data": "synthetic", "outcomes": outcomes}


if __name__ == "__main__":
    print(json.dumps(simulate(), indent=2))
