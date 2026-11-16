# Phase 2 Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest user-owned PDFs into cited, searchable RAG context with durable progress and provider-agnostic generation/embedding adapters.

**Architecture:** FastAPI routes enqueue user-scoped database jobs. A service validates and stores PDFs, extracts text with `pypdf`, chunks with page provenance, embeds through `LLMProvider`, writes FTS5/vector adapter records, and exposes retrieval through a hybrid RRF service. Gemini API and Vertex AI share the `LLMProvider` protocol; mock and Ollama remain offline implementations.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, SQLite FTS5, `pypdf` (BSD-3-Clause), `google-genai` (Apache-2.0), httpx mocked transports, React/Vite/TypeScript.

**Spec:** `docs/briefs/phase-2-ingestion.md`, `docs/08-scope-and-rag-strategy.md`, and `docs/CODEX_HANDOFF.md`.

## Global Constraints

- `References/` is read-only and must not be read, run, edited, or copied.
- Every query is scoped to the current user; add an ownership test for each new protected resource.
- Uploaded text and LLM output are untrusted; validate input and structured output, and never render raw model HTML.
- No secrets in code, logs, fixtures, docs, client bundles, or commits.
- No AGPL PDF dependency; record licences for new dependencies.
- Model names and provider selection come from configuration, never hard-coded in behavior.
- Use mock/Ollama until real credentials exist; live smoke tests and cost reporting wait for credentials.

## Review Focus

- Cross-user document/job/chunk access returns no data: ownership tests use two users in the same database.
- PDF bytes that look valid but contain no text are marked OCR-required, not presented as successfully ingested.
- Oversized, wrong-magic, malformed, and over-page PDFs fail without storing files or leaking parser details.
- Provider failures and malformed JSON fail with safe errors and no credential/content logging.
- FTS and vector retrieval cannot return another user's rows, even when document IDs collide across test fixtures.

### Task 1: Fixture spike and dependency/licence record

**Files:**
- Create: `backend/tests/fixtures/` generated fixture PDFs and `backend/tools/fixture_spike.py`
- Create: `docs/research/rag-eval-baseline.md`
- Modify: `backend/pyproject.toml`, `THIRD_PARTY_NOTICES.md`, `docs/07-decisions-and-risks.md`

**Interfaces:** Produce reproducible fixture metadata and a documented OCR gap; no production API dependency.

- [ ] Write tests for text-bearing and scanned fixture detection.
- [ ] Run the tests and record the initial failure.
- [ ] Add `pypdf` and the fixture generator, after recording permissive licences.
- [ ] Generate 5–8 local fixtures without reading `References/`.
- [ ] Run the spike and write measured extraction/page findings and known gaps.
- [ ] Run focused tests and commit.

### Task 2: Provider configuration and Gemini/Vertex adapters

**Files:**
- Modify: `backend/app/core/config.py`, `backend/.env.example`, `backend/pyproject.toml`
- Create: `backend/app/ai/google_genai.py`, `backend/tests/ai/test_google_genai.py`
- Modify: `backend/app/ai/provider.py`, `backend/app/ai/mock.py`, `backend/app/ai/ollama.py`

**Interfaces:** `GeminiProvider` and `VertexProvider` implement async `generate_text`, `generate_json`, and `embed`; construction receives settings and injectable transport/client factories for tests.

- [ ] Add failing tests for text, JSON response parsing, embedding extraction, model selection, and safe missing-credential errors.
- [ ] Implement mocked transports/client boundary without logging prompts, keys, or response content.
- [ ] Verify settings use `GEMINI_API_KEY`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and optional `GOOGLE_APPLICATION_CREDENTIALS` path without reading it during config load.
- [ ] Run focused provider tests and static checks.
- [ ] Commit.

### Task 3: Data model and migration

**Files:**
- Create: `backend/app/models/library.py`, `backend/app/models/jobs.py`, migration `backend/alembic/versions/0003_library_and_rag.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/tests/core/test_library_migration.py`

**Interfaces:** `Document`, `Chunk`, `Topic`, and `Job` carry `user_id`; foreign keys cascade; statuses and progress are constrained in application schemas.

- [ ] Write migration tests against a fresh configured database, including ownership columns and indexes.
- [ ] Implement models and Alembic migration.
- [ ] Run `make migrate` against a fresh database and assert tables exist.
- [ ] Commit.

### Task 4: Validation, extraction, chunking, and ingestion service

**Files:** `backend/app/services/ingestion.py`, `backend/app/schemas/library.py`, tests mirroring services.

- [ ] Write tests for magic bytes, caps, quota, extraction provenance, chunk overlap, hostile text handling, and cleanup.
- [ ] Implement minimal services with bounded inputs and page/chunk citations.
- [ ] Run focused tests and commit.

### Task 5: Vector/FTS adapters, RRF retrieval, and job runner

**Files:** `backend/app/repos/vector_store.py`, `backend/app/repos/keyword_store.py`, `backend/app/ai/retrieval/`, `backend/app/workers/`, tests.

- [ ] Write user-isolation and ranking tests first.
- [ ] Implement SQLite adapters behind protocols and RRF with deterministic tie-breaking.
- [ ] Implement durable claim/progress/failure transitions.
- [ ] Run focused tests and commit.

### Task 6: API and UI

**Files:** library/chat routers, contracts, frontend library components/tests, docs.

- [ ] Write API ownership/error tests and frontend state tests.
- [ ] Implement upload, list, status, delete, and cited chat with honest empty/loading/error states.
- [ ] Run `make check`, fresh migration, and real-stack API flow.
- [ ] Inspect mobile/tablet/desktop in light/dark in a real browser.
- [ ] Commit.

### Task 7: Phase gate and merge

- [ ] Run full verification from a clean install, including fixture eval in CI mode.
- [ ] Review diff for secrets, ownership, untrusted input/output, dependency licences, and file size.
- [ ] Update roadmap, API docs, decisions, and phase report.
- [ ] Merge `phase-2-ingestion` to `main` only after exit criteria hold.
