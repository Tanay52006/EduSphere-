# RAG evaluation baseline

## Fixture spike — 2026-11-12

Command:

```text
backend/.venv/bin/python backend/tools/fixture_spike.py --output backend/tests/fixtures/pdfs
```

Observed output:

| Fixture | Pages | Pages with extracted text |
|---|---:|---:|
| `lecture-notes.pdf` | 2 | 2 |
| `textbook-chapter.pdf` | 2 | 2 |
| `slides-export.pdf` | 2 | 2 |
| `exam-review.pdf` | 2 | 2 |
| `scanned-notes.pdf` | 1 | 0 |

The fixture generator and tests are deterministic and do not read from `References/`. The scanned fixture confirms the Phase 2 OCR gap: ingestion must set an explicit OCR-required state and must not claim that empty extraction succeeded.

## Retrieval metrics

EduSphere's deterministic offline harness was run with:

```text
backend/.venv/bin/python backend/tools/rag_eval.py --output /tmp/edusphere-rag-eval
```

Observed output:

```json
{"cases": 4, "hit_at_1": 1.0, "hit_at_3": 1.0, "hit_at_5": 1.0, "mrr": 1.0, "provider": "deterministic-offline"}
```

This is a smoke baseline over four clean text-PDF questions with injected offline topic vectors; it is not a live Gemini quality estimate. The handoff requires `References/` to remain read-only and forbids running its code, so the JavaScript ragforge reference run is intentionally not executed. Live provider quality, latency, and cost remain unmeasured until credentials are available.

## Verification status

- Fixture tests: 2 passed.
- Fresh Alembic migration test for the Phase 2 tables: passed.
- Hybrid retrieval API and cross-user isolation tests: passed with injected offline embeddings.
- Live Gemini/Vertex smoke test: not run; credentials are not present.
- OCR: detection only; OCR implementation is deferred.

## Phase 3 question validation baseline — 2026-11-12

The deterministic mock provider was exercised against the seeded text fixture used by
the question-service tests. A request for 20 questions produced 20 schema-valid,
source-cited questions, and the separate mock validation pass accepted all 20.

```text
questions requested: 20
questions stored: 20
validation pass rate: 20/20 = 100%
provider: deterministic mock
```

This is a contract and pipeline baseline, not a measure of Gemini or Groq semantic
quality. Provider-backed quality still needs a labeled evaluation set and a live,
credentialed run.
