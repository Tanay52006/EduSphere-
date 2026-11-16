# EduSphere: agent instructions

Gamified learning SaaS. React + TypeScript frontend, FastAPI backend, SQLite locally (Postgres later). Read `docs/` before building; `docs/03-roadmap.md` is the build order. Work one phase at a time and do not start a phase before the previous exit criteria are met.

## Hard rules

- `References/` is read-only inspiration. Do not import from it, copy large chunks, or build it. Reimplement ideas cleanly. Never read, print or copy any `.env` file under `References/`; the iks `.env` files contain real-looking keys.
- Porting from `References/ragforge` (MIT, JavaScript) is allowed only as a Python reimplementation following `docs/08-scope-and-rag-strategy.md`. Add attribution to `THIRD_PARTY_NOTICES.md`. Never run its code or install its npm dependencies in this repo.
- Research PDFs in `docs/research/papers/` are for reference only; do not publish them.
- No secrets in code, logs, client bundles or docs. Config via env vars; keep `.env.example` current; `.env` is gitignored.
- Server-side everything that matters: validate input, check ownership on every resource (no IDOR; every query is scoped to the current user), score games and award XP on the server only.
- Uploaded PDF text is **untrusted data**. It goes into prompts only as quoted context, never as instructions (prompt-injection defence).
- LLM output is untrusted: request structured JSON, validate with Pydantic, retry/repair once, then fail safely. Never `eval` or render raw LLM HTML.
- Every LLM call goes through `backend/app/ai/` (provider interface, cost/rate limits, logging without content). No direct SDK calls elsewhere.
- Every analytics call goes through one wrapper (`analytics.track`). No direct CleverTap calls elsewhere.
- DB access only through SQLAlchemy models and Alembic migrations. No SQLite-only features outside the repository/vector adapters, so Postgres stays a config change.
- No new dependency without a concrete reason; note it in the PR/commit message.
- Do not scrape YouTube or other sites. Official APIs only.

## Working style

- Tests first for backend logic (scoring, XP, question validation, ownership checks). Add a security test for every authorization boundary.
- UI work follows `docs/04-design-system.md`. Inspect the rendered result in a browser before claiming it looks right. Cover hover, focus, loading, empty, error states, and mobile/tablet/desktop.
- Keep files focused (rough ceiling of 300 lines per module). The reference repos failed here, so don't repeat it.
- Small commits per task, conventional messages. Update the relevant doc in the same change when behaviour or decisions change.
- Before finishing a phase: run tests, linters and type checks; review the diff for secrets, missing access checks and insecure defaults; report what was and wasn't verified.

## Commands

- `make install` — create `backend/.venv` and install Python and frontend dependencies.
- `make dev` — start FastAPI on `http://localhost:8000` and Vite on `http://localhost:5173`.
- `make check` — run Ruff, mypy, pytest, ESLint, Prettier, TypeScript build checks and Vitest.
- `make migrate` — apply Alembic migrations to the configured database.
