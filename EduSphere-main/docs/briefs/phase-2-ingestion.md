# Phase 2 brief: library and RAG ingestion

## Intent

Turn a user's PDF materials into an honest, user-scoped library item with observable ingestion progress, searchable chunks, embeddings, topic metadata, and grounded answers with citations.

## Scope

- Fixture spike before production ingestion: 5–8 representative PDFs, including lecture notes, a textbook chapter, a slide export, a malformed/hostile input, and one scanned PDF to document the OCR gap.
- Provider-agnostic Gemini API, Vertex AI, mock, and Ollama adapters covering text, JSON-mode generation, and embeddings.
- `documents`, `chunks`, `topics`, and `jobs` models plus Alembic migration.
- PDF validation by magic bytes, size/page caps, per-user quota, random storage names, and deletion of files/vectors/rows.
- DB-backed ingestion jobs with extraction, chunking, embedding, FTS5 indexing, and progress.
- Vector + FTS5 hybrid retrieval merged with Reciprocal Rank Fusion; no LLM query translation by default.
- Library UI, grounded chat with page/chunk citations, and the fixture evaluation harness.

## Non-goals

- OCR implementation; scanned PDFs are detected and reported as unsupported until a later phase.
- Scraping or importing from `References/`.
- Live Gemini or Vertex calls before Fredrick supplies credentials.
- Query-time LLM translation unless the fixture evaluation shows at least a five-point gain.

## Constraints and acceptance evidence

- Every document, chunk, topic, job, vector, and retrieval query is scoped to the authenticated user.
- Uploaded text and model output are untrusted; prompts quote document text as data and structured output is validated.
- No credentials, `.env` contents, service-account files, or fabricated data are logged or committed.
- No AGPL PDF dependency; use a permissive PDF library and record its licence.
- Baseline and final checks must include migrations on a fresh database and a real-stack run. UI changes require browser inspection at approximately 390, 820, and 1366 px in light and dark themes.

## Decisions made for this phase

- Use `google-genai` for both Gemini API and Vertex AI adapters so the provider boundary is stable and transport tests can be mocked without credentials.
- Use `pypdf` for text extraction and PDF inspection; scanned pages are detected from missing text rather than silently OCR'd.
- Keep model names in settings: separate generation, JSON, and embedding model variables for each provider.
- Keep the first ingestion implementation synchronous inside a DB-backed job runner abstraction; the API enqueues a durable job and a worker can claim it without coupling callers to a queue service.
- Generate embeddings through the configured `LLMProvider` in the worker and expose `GET /api/search?q=...&top_k=...` as a user-scoped hybrid retrieval endpoint returning chunk/page citations and branch provenance.

## Debt to report

OCR, SQLite vector extension deployment, resumable workers, live provider cost measurements, and browser verification of the new search UI remain unverified until their prerequisites or UI work are available.
