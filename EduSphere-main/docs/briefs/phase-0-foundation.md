# Brief: Phase 0, Foundation

**Owner/orchestrator:** Claude. **Implementer:** Codex. **Branch:** `phase-0-foundation`.

Read first: `CLAUDE.md`, `docs/02-architecture.md`, `docs/03-roadmap.md` (Phase 0), `docs/08-scope-and-rag-strategy.md`. Do **not** read or use anything under `References/` (it is gitignored and absent from your worktree).

## Goal
A runnable, tested, empty skeleton: one command starts backend and frontend, and one command runs lint, type checks and tests, all green. No product features.

## Deliverables

**Backend (`backend/`)**
- Python project (`pyproject.toml`, `requires-python >=3.12`; only Python 3.14 is installed locally, so use a `.venv` with it and report any dependency that fails on 3.14). Dependencies: fastapi, uvicorn, pydantic v2, pydantic-settings, sqlalchemy 2, alembic, httpx. Dev: pytest, pytest-asyncio, ruff, mypy. No other dependencies without a written reason.
- Layout: `backend/app/{api,services,ai,repos,models,schemas,workers,analytics,core}/`, tests in `backend/tests/` mirroring it.
- `core/config.py`: settings from env (`pydantic-settings`), `.env.example` documenting every variable (APP_ENV, DATABASE_URL default `sqlite:///./storage/edusphere.db`, LLM_PROVIDER=mock, STORAGE_DIR, CORS_ORIGINS, LOG_LEVEL). Secrets never have real defaults.
- App factory, `GET /api/health` (status + version), CORS from allow-list only, security headers middleware, a uniform JSON error format with no stack traces or internal paths, request-id logging **without PII or request bodies**.
- SQLAlchemy 2 engine/session setup, SQLite in WAL mode with foreign keys on, Alembic configured with an initial empty migration. No Postgres-only or SQLite-only SQL outside `repos/`.
- `ai/`: `LLMProvider` protocol (`generate_json(schema, prompt, ...)`, `generate_text`, `embed`), a deterministic **`MockProvider`**, and an `OllamaProvider` (httpx; tests use a mocked transport). Include a usage/budget stub interface. No SDK calls elsewhere.
- `analytics/`: `track(event, props)` and `identify(user_id, props)` no-op wrapper with a backend interface.
- `repos/`: `VectorStore` protocol (add, query top-k by user, delete by document) with an in-memory implementation for tests only; `FileStore` protocol with a local implementation that is **path-traversal safe** (random storage names, resolves inside `STORAGE_DIR`, size limit hook).
- Tests: health endpoint, error format, config, MockProvider determinism, OllamaProvider with mocked transport, FileStore traversal attempts rejected, VectorStore user scoping (a query for user A never returns user B's vectors), security headers present.

**Frontend (`frontend/`)**
- Vite + React 18 + TypeScript + Tailwind CSS, React Router, TanStack Query. A single placeholder page that calls `/api/health` and shows the status. ESLint, Prettier, `tsc --noEmit`, Vitest + Testing Library with one passing component test. Vite dev proxy to the backend. Do not design UI; Phase 1 does that.

**Root**
- `Makefile` with `make dev` (both servers), `make check` (ruff, mypy, pytest, eslint, tsc, vitest), `make migrate`.
- `.env.example` at the root only if needed; never commit `.env`.
- Update the **Commands** section of `CLAUDE.md` and add a short "Getting started" to `README.md`. Do not edit any other doc.
- `THIRD_PARTY_NOTICES.md` as an empty stub with a header.

## Rules
- Follow `CLAUDE.md` exactly. Smallest complete solution; no unrequested abstractions, auth, models or endpoints beyond health.
- Small conventional commits on branch `phase-0-foundation`. Do not push, merge or touch `main`.
- Do not install anything globally or outside the project directories.

## Exit criteria (the orchestrator will re-run these)
1. `make check` passes from a clean clone with the documented setup steps.
2. `make dev` serves the frontend and backend; the page shows the health status.
3. A user-A / user-B vector scoping test and path-traversal tests exist and pass.
4. No secrets, `.env`, db files or `node_modules` committed.

## Final report (your last message)
List what you built, exact commands you ran with pass/fail results, anything that failed or was skipped, dependencies added with reasons, and any decision you made that the docs did not cover.
