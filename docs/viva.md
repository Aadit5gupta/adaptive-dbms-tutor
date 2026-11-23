# Viva preparation

**How does the product adapt?** An assessment version determines the grade. The learner model updates a bounded score and counts independent, distinct questions for confidence. The policy checks active hypotheses, prerequisites, reviewed material, difficulty and due reviews before recording an explainable action.

**Why do two wrong answers matter?** A reviewed wrong-choice mapping supplies one signal about a specific idea. A second eligible signal must come from a different logical question. Two reserved, unseen, unhinted checks can resolve the hypothesis. Unrelated errors and replays leave independent evidence unchanged.

**What stops the language model from grading?** Tutor requests have a separate provider interface. The response is teaching text and source IDs. Only the deterministic assessment transaction writes grade, mastery, independent evidence or recommendations.

**Why use SQLite full-text search?** The local content bank is small. FTS5 ranks lexical matches with BM25 and carries explicit topic and provenance metadata. It avoids a separate service and can be evaluated with the same labeled queries before considering embeddings.

**How are citations verified?** Retrieval returns stable records for approved passages. Ollama receives short handles for those records. The backend accepts handles from the current retrieval result and assembles the citation metadata itself.

**How does the SQL worker isolate learner queries?** It runs one statement at a time in a separate process against a temporary, read-only fixture. SQLite's authorizer, restricted functions, bounded allocation, instruction and wall-clock limits, output caps and tested OS limits constrain execution on the supported Mac.

**What does the evaluation establish?** The browser tests exercise isolation, evidence transitions, persistence and grading. Simulation verifies model and policy behavior for fixed inputs. The real local model smoke demonstrates successful completion with test-only evidence. A human learning study would need reviewed assessments, consent and a matched comparison design.

**Which release gates remain?** A person must explicitly sign off the learning bank and assess the SQL expected results. Each book section also needs individual rights clearance. Readiness, verified test totals and current corpus counts are in the [implementation status](../IMPLEMENTATION_STATUS.md).
