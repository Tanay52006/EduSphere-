# Phase 2 Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the remaining Phase 2 library and RAG requirements so users can upload, manage, search, and ask grounded questions about their own PDFs with citations.

**Architecture:** Keep the existing FastAPI, SQLAlchemy, SQLite, FTS5, `VectorStore`, `FileStore`, and provider-agnostic `LLMProvider` boundaries. Add grounded chat as a user-scoped retrieval-then-generation flow, with validated structured output and citations limited to retrieved chunks. Keep OCR deferred and use the mock provider for deterministic tests.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, SQLite + FTS5, pypdf, React/TypeScript, TanStack Query, `google-genai` adapters, pytest, Vitest.

**Spec:** `docs/briefs/phase-2-ingestion.md` and Phase 2 in `docs/03-roadmap.md`.

## Global Constraints

- `References/` is read-only; never edit it, run its code, or read any `.env` in it.
- Every document, chunk, job, vector, and retrieval query is scoped to the authenticated user.
- Uploaded text and model output are untrusted; prompts quote document text as data and structured output is validated.
- No credentials, `.env` contents, service-account files, or fabricated data are logged or committed.
- Use permissive PDF dependencies; do not add PyMuPDF because it is AGPL.
- Keep model names and provider selection in configuration; use mock/Ollama for offline tests.
- UI must be inspected in a real browser at approximately 390, 820, and 1366 px in light and dark themes before Phase 2 is declared complete.

## Review Focus

- Failed ingestion after partial writes: no orphan chunks, FTS rows, vectors, or misleading ready state.
- Delete authorization: one user cannot delete or retrieve another user’s document or derived data.
- Empty or weak retrieval: the system returns no answer rather than unrelated passages.
- Prompt injection in PDF text: document content cannot alter the answer contract or create citations outside retrieved chunks.
- Malformed, oversized, scanned, and multi-page PDFs: each receives a bounded, honest status or error.

### Task 1: Make ingestion failures atomic and add document deletion

**Files:**
- Modify: `backend/app/workers/runner.py`
- Modify: `backend/app/api/documents.py`
- Modify: `backend/app/repos/keyword_store.py`
- Modify: `backend/app/repos/vector_store.py`
- Modify: `backend/tests/workers/test_runner.py`
- Modify: `backend/tests/api/test_documents.py`

**Interfaces:**
- Produces an authenticated `DELETE /api/documents/{document_id}` that removes the owned file, document, job, chunks, FTS rows, and embeddings.
- Failed ingestion leaves the document in `failed` state with no retrievable derived rows.

- [x] Write failing tests for rollback cleanup, successful owned deletion, and cross-user deletion denial.
- [x] Run the focused tests and verify they fail for the missing behavior.
- [x] Implement cleanup through the existing repository boundaries and keep deletion user-scoped.
- [x] Run focused tests and verify they pass.
- [x] Commit: `fix: make document ingestion and deletion safe`

### Task 2: Enforce quotas and expose honest ingestion errors

**Files:**
- Modify: `backend/app/api/documents.py`
- Modify: `backend/app/schemas/library.py`
- Modify: `backend/tests/api/test_documents.py`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/Library.tsx`

**Interfaces:**
- Upload validation enforces the existing byte/page/user limits before storage.
- Failed documents expose a safe error code/message suitable for the Library UI without stack traces or provider credentials.

- [x] Write failing tests for byte quota, page limit, failed-job status, and safe error responses.
- [x] Run focused tests and verify they fail for each missing contract.
- [x] Implement the minimum server and UI changes.
- [x] Run backend and frontend focused tests and verify they pass.
- [ ] Inspect the Library at the three target widths and both themes.
- [x] Commit: `feat: surface library limits and ingestion errors`

### Task 3: Add grounded chat with citations

**Files:**
- Create: `backend/app/api/chat.py`
- Create: `backend/app/schemas/chat.py`
- Create: `backend/tests/api/test_chat.py`
- Modify: `backend/app/main.py`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/Library.tsx`
- Modify: `frontend/src/App.test.tsx`

**Interfaces:**
- Adds `POST /api/chat` with `{question: string, top_k?: number}` and a response containing `answer`, `citations`, and `grounded: boolean`.
- The provider receives only retrieved, labeled chunks; each citation must reference a returned chunk/page owned by the current user.
- No strong retrieval produces `grounded: false` and an honest no-match response.

- [x] Write failing tests for grounded answers, citation validation, empty retrieval, cross-user isolation, and prompt-injection text.
- [x] Run the focused tests and verify they fail for the missing endpoint.
- [x] Implement retrieval, provider generation, strict response validation, and the authenticated route.
- [x] Add the Library chat interaction without fabricating results in mock mode.
- [x] Run focused tests, frontend tests, and a real-stack mock-provider smoke test.
- [ ] Inspect chat at the three target widths and both themes.
- [x] Commit: `feat: add grounded library chat`

### Task 4: Build the fixture evaluation harness and baseline

**Files:**
- Create or modify: `backend/tools/rag_eval.py`
- Modify: `backend/tests/tools/test_rag_eval.py`
- Modify: `docs/research/rag-eval-baseline.md`
- Modify: `THIRD_PARTY_NOTICES.md`

**Interfaces:**
- The harness evaluates fixture questions with hit@k and MRR, reports provider/model configuration without secrets, and supports deterministic mock runs.

- [x] Write failing tests for fixture loading, hit@k, MRR, and secret-safe reporting.
- [x] Run focused tests and verify they fail for missing evaluation behavior.
- [x] Implement the deterministic harness and baseline report.
- [x] Run it on the fixture set and record actual metrics and limitations.
- [ ] Commit: `feat: add rag retrieval evaluation harness`

### Task 5: Phase 2 exit verification and documentation

**Files:**
- Modify: `docs/briefs/phase-2-ingestion.md`
- Modify: `docs/07-decisions-and-risks.md`
- Modify: `docs/research/rag-eval-baseline.md`

- [ ] Run fresh-database migrations and the complete `make check` suite.
- [ ] Run the real-stack mock-provider flow: upload, progress, search, grounded chat, citation, deletion, and ownership denial.
- [ ] Test malformed, oversized, scanned, and multi-page fixtures.
- [ ] Inspect the UI in a real browser at 390, 820, and 1366 px in light and dark themes.
- [ ] Record what was verified, what remains deferred, and the remaining debt.
- [ ] Commit: `docs: close phase 2 verification record`

## Self-review

- The plan covers the Phase 2 brief’s missing deletion, quota/error handling, grounded chat, evaluation, and exit evidence.
- OCR and live provider cost measurement remain explicit debt or prerequisites, not hidden work.
- Every task has a failing-test step, a focused implementation boundary, and an independent verification step.
- No task requires credentials or changes to product scope.
