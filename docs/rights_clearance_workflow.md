# DBMS Mentor — source rights and indexing clearance workflow

**Authority:** `../MASTER_PLAN.md` v1.2 §4. This is an operational checklist, not legal advice. Book-level CC notices are metadata, **not** wholesale rights clearance of every image, data file, code sample or chapter. When unsure, retain a clickable external catalog link and **do not import** the material.

## 1. Five source catalog vs local index

`content/manifests/books.yaml` contains the five known source records and dated publisher-level evidence. Its `default_import_policy: link_only` is the default for a **section without an explicit clearance**; it is not the dynamically displayed indexed-book status. A book may retain this default while specific separately audited sections are cleared. Source-derived student lessons may cite a public URL without locally reproducing the passage.

Never compute indexed counts by counting permissions. Distinguish:

1. `cleared_sections`: exact section URLs with documented `approved_local_index` or `publisher_license_verified` records and matching text hashes.
2. `indexed_sections`: cleared sections for which an **atomic, successful import** committed searchable chunks into the app's SQLite FTS index.
3. `indexed_books`: distinct books with ≥1 currently searchable approved indexed section.

The library UI must show actual `indexed_books of 5`, not a goal or a manifest guess. Failed/cancelled import must leave counts unchanged and no orphan chunks.

## 2. Auditing one candidate section

1. Open the **exact chapter/section URL** and record `accessed_on` (actual date, not guessed).
2. Read the primary license notice and follow its **license URL**. Record exact author/title/licensor and attribution language.
3. Inspect the section footer/preface for exceptions and any third-party text, photos, figures, tables, assessments, exercises, SQL datasets, source-code listings, trademarks and credited adaptations. Opening the homepage alone is insufficient.
4. Define a precise import scope (prefer `text_only`), excluding unreviewed images and datasets. Attribute or exclude any derivatives with different obligations.
5. Check redistribution and adaptation obligations, including CC BY attribution; CC BY-SA share-alike for adapted material; CC BY-NC / BY-NC-SA noncommercial limitations. A college project is not automatic permission for future commercial reuse. Do not collapse incompatible adapted works into a single rewritten CC-licensed document. Separately licensed sources may coexist as a correctly attributed collection.
6. Extract **only the intended permitted section text** locally; compute its SHA-256 in the encoding/canonicalization specified by the ingestion script. Record section URL, license URL, scope, exceptions, reviewer, reviewed-on and the approved text hash. Never claim the hash matches before checking the actual extracted bytes.
7. For the human path, use `approved_local_index` only after an actual human has reviewed the rights. The example below shows the record format.

```yaml
section_clearances:
  - id: source_section_slug
    section_url: https://example.org/specific/section
    license_url: https://creativecommons.org/licenses/by/4.0/
    rights_status: approved_local_index
    scope: text_only
    exceptions_found: none
    exceptions_resolved: false
    accessed_on: 'YYYY-MM-DD'
    reviewer: '<actual human reviewer>'
    reviewed_on: 'YYYY-MM-DD'
    approved_content_hash: '<sha256 of actual imported section text>'
    attribution_text: '<ready-to-display title/author/source/license/changes>'
```

Set `exceptions_resolved` only after resolving documented exceptions. For DataField and OpenStax, a separate approval must include `permission_evidence_url`. Import verification hashes the exact UTF-8 bytes selected for indexing.

8. Run `python scripts/validate_content.py --strict` and section-rights tests. The import script must reject missing clearance, hash mismatch, unresolved exceptions, wrong source IDs and accidentally imported images. Do not override this for demos.
9. Run an idempotent offline import into FTS with section/page provenance. Confirm query hits and displayed license/attribution. Count imported sections only after searchable chunks are committed. Keep raw publisher source files out of Git unless expressly permitted and needed.
10. Re-audit if a license/section changes, a new chapter version is imported or a passage becomes a model-generated adaptation intended for distribution.

## Publisher license verification for bundled excerpts

For the publisher path, use `publisher_license_verified` and an explicit `ai:...` verifier. The validator pins the eligible section URL and license. Record a valid `bundled_topic_id`, actual access and review dates, attribution, and the exact SHA-256. Store the approved UTF-8 snippet at `content/manifests/book_excerpts/<clearance_id>.txt`. Inspect the precise excerpt and confirm it contains no exception. The manifest and the displayed source and license links carry the credit for each excerpt. This path applies to the two exact scopes below.

- Runestone, foreign-key enforcement, one sentence on cascade deletion. [Chapter section](https://runestone.academy/ns/books/published/practical_db/PART1_SQL/07-constraints/constraints.html#enforcement-mechanisms) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- BCcampus, Chapter 9, one sentence defining orphan records. [Chapter and license notice](https://opentextbc.ca/dbdesign01/chapter/chapter-9-integrity-rules-and-constraints/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## 3. Current high-priority exceptions (observed 2026-11-22)

| Source | Audit position |
|---|---|
| BCcampus *Database Design* | Book-level CC BY 4.0 with exceptions; **Chapter 10** derives from *Relational Design Theory* by Nguyen Kim Anh under CC BY 3.0; **Chapter 11** credits Wikipedia Armstrong's axioms under CC BY-SA 3.0; neither is blanket-approved. Exclude cover/image assets unless separately audited. |
| Runestone *A Practical Introduction to Databases* | CC BY-SA 4.0 book notice; exclude cover photograph and independently check referenced example datasets. Good priority for text-only licensing audit. |
| Brendan Shea *SQL and Database Management Through Pop Culture* | Homepage states CC BY-NC 4.0. Noncommercial; third-party media/code/datasets need separate review. |
| OpenStax *Foundations of Information Systems* | Preface states CC BY-NC-SA 4.0; check special attribution/figure licenses and page-by-page required notices if reusing book text. |
| DataField *Database Fundamentals* | No unambiguous blanket redistribution/indexing permission established in the inspected source. **Keep link-only** until written permission or a valid license explicitly permits use. |

See the [section rights review package](section-rights-review.md) for exact chapter evidence and proposed exclusions. The manifest tracks existing exceptions and any actual clearances. This is a **partial audit**: it does not assert that all other sections lack exceptions.

## 4. Machine-verifiable gates

- Exactly 5 catalog records with unique source IDs and evidence URLs.
- Rights enum: `link_only | approved_local_index | publisher_license_verified | blocked_pending_review | blocked_pending_permission | excluded_image` (the last is for recorded excluded assets, not a text-import permission).
- `default_import_policy` remains `link_only` for any unlisted/unreviewed section.
- **No import of DataField** unless the owner explicitly changes the rights record with actual evidence; tests enforce this condition rather than silently overriding it.
- BCcampus Chapters 10/11 have explicit exception records; importer refuses those exact sections until a separate section clearance with appropriately documented derivative license obligations is approved.
- Each approved imported text hash must match its clearance and stored chunk provenance. No clearance → no import. Approval without import → `indexed_books` remains unchanged.
- Reviewer identity and dates must be real; Codex must never fill in fake human approvals.

If two fully indexed books cannot be legally cleared by the evaluation deadline, ship a truthful catalog and eligible original human-reviewed or AI-verified lessons. Explain the limitation rather than faking indexed content. With zero indexed books, do not claim the retrieval system supplies book-grounded passages.

## Local import commands

Migrate the application database before importing. The importer accepts exact UTF-8 text files prepared and reviewed offline for the section. Store pending files under the ignored `content/raw/` directory.

```sh
python scripts/import_books.py lessons
python scripts/import_books.py section --book BOOK_ID --clearance CLEARANCE_ID --topic TOPIC_ID --text PATH
```

Use the top-level `--demo` flag before the subcommand to target the marked demo database. The `lessons` command also imports the bundled textbook excerpts. Reviewed original lessons receive their own attribution and are counted separately from books.
