# Complete Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish Phase 3 so a ready user document can produce a measured, validated question bank and both Quiz Blitz and Memory Match are playable with server-authoritative scoring, then merge the verified result into `main`.

**Architecture:** Keep all question generation and game truth in the existing FastAPI services and SQLAlchemy models. Strengthen retrieval at the hybrid-retriever boundary by ranking candidates with semantic similarity and lexical evidence before building grounded chat context. Render Memory Match as a client-side card grid while submitting only pair choices; the server retains the answer key and awards XP.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, SQLite FTS5 plus the existing `VectorStore`, React 18, TypeScript, TanStack Query, Vitest, pytest, Playwright/Brave for browser verification.

**Spec:** `docs/briefs/phase-3-question-engine.md`

## Global Constraints

- Every protected query and game operation is scoped to the authenticated user.
- Server-side validation, scoring, XP, and answer keys remain authoritative.
- Uploaded text and provider output are untrusted and schema-validated.
- No secrets, `.env` contents, service-account files, or reference files are added.
- No new dependency without a licence check and a recorded reason.
- UI must be inspected in a real browser at mobile, tablet, and desktop widths in light and dark themes.

## Review Focus

- A question bank with fewer than 20 validated questions must not start a game; test the honest empty state.
- MATCH questions must have a safe, validated pair shape; malformed payloads must not make a playable game.
- A user must not start or submit another user’s session; test both boundaries in the same database.
- Weak retrieval candidates must not become grounded context solely because they appeared in a branch ranking; test a relevant and unrelated chunk together.
- Browser states must remain honest while generation, game start, submission, and errors are pending; verify them at all required viewport/theme combinations.

### Task 1: Retrieval precision gate

**Files:**
- Modify: `backend/app/ai/retrieval/hybrid.py`
- Modify: `backend/app/repos/vector_store.py` only if a repository-level score is needed
- Test: `backend/tests/ai/test_hybrid_retriever.py`
- Test: `backend/tests/api/test_chat.py`
- Modify: `docs/07-decisions-and-risks.md`

**Interfaces:**
- Consumes the existing `HybridRetriever.search(...)` inputs.
- Produces deterministic, user-scoped hits ordered by combined lexical/semantic evidence, with a final relevance floor for grounded chat.

- [ ] Write failing tests for weak vector candidates being excluded and relevant candidates remaining cited.
- [ ] Run the focused retrieval/chat tests and verify the new assertions fail.
- [ ] Implement the smallest score-aware candidate fusion and context cutoff without adding an external reranker.
- [ ] Run focused tests, then record the retrieval decision and its tradeoff in `docs/07-decisions-and-risks.md`.

### Task 2: Validated Memory Match contract

**Files:**
- Modify: `backend/app/schemas/questions.py`
- Modify: `backend/app/services/questions.py`
- Modify: `backend/app/services/games.py`
- Modify: `backend/app/schemas/games.py`
- Test: `backend/tests/services/test_questions.py`
- Test: `backend/tests/services/test_games.py`
- Test: `backend/tests/api/test_games.py`

**Interfaces:**
- MATCH payload: `{ "pairs": [{ "id": string, "term": string, "definition": string }] }`.
- MATCH answer: `{ "pairs": [{ "term_id": string, "definition_id": string }] }` or an equivalent server-normalized key.
- The public session payload contains shuffled cards without answer ownership information.

- [ ] Add failing tests for valid pair normalization and malformed MATCH payload rejection.
- [ ] Run them and verify failure before implementation.
- [ ] Validate/normalize MATCH candidates before persistence and make `start_game` reject unsafe stored data.
- [ ] Add ownership and answer-key secrecy assertions, then run the focused suite.

### Task 3: Playable Memory Match frontend

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/Games.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes the public session contract from Task 2.
- Produces a keyboard-accessible card grid with two-card matching, moves, matched state, retry/error state, and final server result.

- [ ] Add a frontend test for selecting a pair and submitting a Memory Match round.
- [ ] Run it to establish the expected failure.
- [ ] Replace the current MATCH placeholder with the card-grid interaction; never expose answer keys.
- [ ] Add focus, disabled, loading, error, reduced-motion, and responsive styles.
- [ ] Run frontend tests, lint, format check, and build.

### Task 4: Phase 3 evidence and documentation

**Files:**
- Modify: `docs/briefs/phase-3-question-engine.md`
- Modify: `docs/03-roadmap.md`
- Modify: `docs/research/rag-eval-baseline.md`
- Modify: `docs/07-decisions-and-risks.md`
- Create: `docs/phase-reports/phase-3-report.md`

- [ ] Add a measured question-validation pass-rate command/result using mock provider fixtures.
- [ ] Add retrieval regression cases for the research paper and unrelated chunks.
- [ ] Document verified behavior, unverified live-provider/browser items, and remaining debt.

### Task 5: Full verification and integration

- [ ] Run `make install && make check` from the current tree.
- [ ] Run migrations against a fresh temporary database and exercise the real backend/worker/frontend servers.
- [ ] Inspect the UI in Brave at approximately 390, 820, and 1366 px in light and dark themes; record findings.
- [ ] Review diff for secrets, ownership gaps, stale code, and files above the project ceiling.
- [ ] Commit the completed Phase 3 changes on `phase-3-question-engine`.
- [ ] Merge into `main`, rerun verification on the merged result, and push `main`.
- [ ] Delete only branches proven merged and no longer needed; report every deletion.
