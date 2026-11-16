# Codex handoff: you own EduSphere end to end

You are now the lead engineer and owner of this project. Until further notice you plan, build, test, review, merge and document it yourself. The previous orchestrator (Claude) has stepped back. Act like an owner: make decisions, keep quality high, and report honestly.

## 1. Mission
EduSphere is a gamified learning SaaS (Notion-clean but colourful). After sign-in the user picks:
- **Learn from my own materials**: upload PDFs, index them (RAG), turn them into at least 4 games and quizzes.
- **Learn something new**: pick a topic and starting level, get an AI-built pathway (lessons, curated videos, quizzes).
Shared layer: XP, levels, streaks, badges, spaced review, and CleverTap behaviour-based nudges. Goal: a credible individual SaaS.

## 2. Where things stand (verified 2026-11-12)
- Repo: `/Users/fredrick/Programming/EduSphere`, git, branch `main`, no remote. Python 3.14 only is installed locally (requires-python >=3.12).
- **Phase 0 done:** FastAPI skeleton, config, Alembic, SQLite WAL, `LLMProvider` (mock + Ollama), analytics no-op wrapper, `FileStore` (path-traversal safe), `VectorStore` interface with user-scoped in-memory impl, Vite + React + TS + Tailwind frontend, Makefile.
- **Phase 1 done:** signup/login/logout/me, profile, onboarding (`docs/api/phase-1-contract.md`), argon2id, hashed session tokens, CSRF double-submit, rate limiter (in memory), design system, auth screens, 3-step onboarding with the fork, app shell, mock mode (`VITE_API_MOCK=1`).
- **Verified:** `make check` passes (26 backend + 8 frontend tests). A real-browser run (Brave via `playwright-core`) of the real frontend against the real backend on a migration-built database passed: signup, onboarding, reload persistence, logout, wrong password, re-login. Screenshots at mobile, tablet, desktop, light and dark.
- Commands: `make install`, `make dev` (runs migrations first), `make check`, `make migrate`. See `CLAUDE.md`.

## 3. Source of truth (read in this order before acting)
`CLAUDE.md` (hard rules) → `docs/03-roadmap.md` (build order) → `docs/08-scope-and-rag-strategy.md` (**overrides** the roadmap where they differ: added features, deferrals, milestones M1 to M3, ragforge port plan) → `docs/02-architecture.md` → `docs/05-gamification-and-games.md` → `docs/04-design-system.md` → `docs/06-clevertap-plan.md` → `docs/07-decisions-and-risks.md` → `docs/00`, `docs/01`, `docs/research/README.md`. Each phase has or should get a brief in `docs/briefs/`. If code and docs disagree, fix whichever is wrong and say so.

## 4. Non-negotiable rules
1. **`References/` is read-only.** Never edit, create or delete anything in it, never run its code, never read or copy any `.env` there (the iks `.env` files hold real-looking keys). It is gitignored. `References/ragforge` is MIT JavaScript: port ideas to Python only, per doc 08, with attribution in `THIRD_PARTY_NOTICES.md`.
2. **Secrets:** none in code, logs, docs, client bundles or git. Config through env vars; keep `.env.example` current.
3. **Security:** server-side validation and authorization on everything; every query scoped to the current user (no IDOR); games scored and XP awarded only on the server; uploaded document text is untrusted data (prompt-injection defence); LLM output is untrusted (schema-validate, repair once, fail safe); no scraping (official APIs only). Add a security test for every new authorization boundary.
4. **Single choke points:** all LLM calls through `backend/app/ai/`, all analytics through the one wrapper, all DB access through SQLAlchemy and Alembic (no SQLite-only SQL outside the repo adapters).
5. **No new dependency without a written reason.** Check the **licence** first: this is a commercial SaaS. Note that PyMuPDF is AGPL (or a paid Artifex licence), so prefer a permissive PDF library (for example `pypdf` or `pdfminer.six`) unless you decide otherwise and record why in `docs/07-decisions-and-risks.md`.
6. **Evidence before claims.** Never say something works, passes or looks right without running it or looking at it. If you could not verify something, say so plainly.
7. Keep modules under about 300 lines, no dead or duplicate code, no drive-by refactors.

## 5. Working method (lessons learned the hard way)
- One phase at a time on a branch (`phase-N-name`), small conventional commits, merge to `main` only when the exit criteria hold. You can commit in the main checkout. Do not rewrite history or force-push. Use your configured git identity, do not override it.
- Write tests first for backend logic (scoring, XP, validation, ownership). Tests must exercise real behaviour: for example, ownership tests need two users in the **same** database; assert `Retry-After` values, not just presence.
- Do not hide problems with shortcuts. Earlier work "passed" while `make migrate` ignored the configured database, because tests created tables directly. Every phase must be exercised through the real migration path and the real running servers.
- **UI work is not done until you have looked at it** in a real browser at mobile (about 390 px), tablet (about 820 px) and desktop (about 1366 px) widths, in light and dark. A passing test suite did not catch: an unstyled primary button, fabricated data on the Home screen (a fake streak and date), and misaligned layouts. Use any browser tool you have; otherwise `playwright-core` driving the installed Brave (`/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`) installed **outside the repo** (for example in `/tmp`), so no project dependency is added.
- **Never show invented data** to users. If a feature has no backend yet, show an honest empty state.
- Prefer real-stack verification: build with migrations only, run backend (:8000) and frontend (:5173), drive the flow, check the network calls and the server log (no passwords or tokens).
- At the end of every phase write a short report in `docs/` or the commit message: what changed, commands run with results, what was not verified, known debt.

## 6. Decisions you may make yourself
Libraries within the approved stack, internal structure, naming, test design, UI details consistent with `docs/04`, the order of work inside a phase, and fixing doc errors. Record each non-trivial decision in `docs/07-decisions-and-risks.md`.

## 7. Stop and ask the human (Fredrick) only for
- Real credentials or API keys: LLM provider keys, CleverTap account ID, region and passcode, YouTube Data API key.
- Anything involving money, billing, deployment to real infrastructure, sending real notifications, or deleting user data.
- Changing product scope or the two-path concept.
**LLM provider: decided.** Fredrick will provide **Gemini API** and **Vertex AI** credentials. Implement two adapters behind the existing `LLMProvider` interface (`gemini`: API key; `vertex`: project, location and application-default or service-account credentials), covering text, JSON-mode generation and embeddings; keep `mock` and `ollama` for tests and offline development. Selection and model names come from config, never hard-coded. Credentials will be placed by Fredrick in the gitignored `backend/.env`. Document the exact variable names in `backend/.env.example` (placeholders only; check the current Google docs for the right variables and model IDs). **Never** print, log, commit or copy a credential or the contents of `.env` or a service-account file, and keep them out of test fixtures and error messages. Until the keys arrive, develop with `mock` and `ollama`, and write adapter tests with mocked transports. When real keys are present, run a small live smoke test (a few calls) and record cost per document in `docs/research/rag-eval-baseline.md`; per-user budgets still apply.

## 8. Known debt and risks to burn down
- Colour is too restrained versus the "vibrant, not monochrome" brief. Schedule a design pass (use the `impeccable` skill if available) before the games phase.
- `frontend/src/styles.css` is about 1,000 lines of hand-written CSS next to Tailwind; consolidate onto the tokens and split.
- `npm audit` reported 15 transitive findings; triage them (do not blindly upgrade).
- Rate limiter is in memory and per process, and behind a proxy all clients share one IP: fix in Phase 8 (Redis, trusted proxy headers).
- Signup returns 409 for an existing email (account enumeration trade-off); no email verification or password reset yet; HSTS and CSP headers not set yet.
- One unexplained 404 console error on first page load was seen once and not reproduced.
- Email validation is lenient (accepts `a@b.c`).
- The unused Antigravity route is dead: do not depend on it.

## 9. Roadmap you now own (full detail in `docs/03` and `docs/08`)
**Phase 2: Library and RAG ingestion (start here).** Upload UI (drag-drop, validation errors), `POST /api/documents` (PDF magic-byte check, size and page caps, per-user quota, random storage name via `FileStore`), `documents`, `chunks`, `topics`, `jobs` tables with migrations, a DB-backed background job runner with progress, extract, chunk (about 400 to 800 tokens, overlap, keep page numbers and headings), embed through the provider interface into `VectorStore` (`sqlite-vec` implementation behind the interface) plus SQLite FTS5 keyword index, topic map. Retrieval = vector + FTS5 merged by Reciprocal Rank Fusion, no LLM call at query time by default; query-translation techniques (HyDE, step-back, fan-out) are opt-in and only enabled if the eval shows at least a 5-point gain. Port from `References/ragforge` (RRF, query translation, router, eval harness) following the table in doc 08. Library page (status, delete that removes files, vectors and rows). Grounded chat with citations. `backend/tools/rag_eval.py` eval harness running on fixture PDFs in CI (hit@k, MRR, cost). Run the fixture spike first (5 to 8 representative PDFs, including one scanned PDF to confirm the OCR gap) and record the baseline in `docs/research/rag-eval-baseline.md`. Exit: upload a 50-page PDF, see progress, get a cited answer; another user cannot see it; malicious or oversized files are rejected; eval runs in CI.
**Phase 3:** question engine (single `questions` table, 7 types, citations, validation pass, flag-a-question), `xp_events` ledger, levels, streaks, server-authoritative `game_sessions`, badges, Games 1 and 2 (Quiz Blitz, Memory Match). **Phase 4:** Games 3 and 4 (Word Hangman, Brain Ladder), weak-spot mode, game picker; **M1 = Path A demo.** **Phase 5:** Path B (topic and level, optional diagnostic, pathway generation with mock fallback, lazy YouTube Data API resolver with cache and quota budget, lesson quizzes, mastery gating), spaced-repetition review (spike SM-2 versus FSRS versus half-life), exam countdown planner; **M2.** **Phase 6:** CleverTap (web SDK plus server events, consent, quiet hours, frequency caps, the starter nudges in doc 06; verify against current CleverTap docs and use a test account); **M3.** **Phase 7:** Infographic (`@antv/infographic`, pinned, lazy-loaded, spike bundle size and icon network behaviour first), study-guide and share card, exports (Markdown, PDF, Anki CSV), leaderboard (friends-only). **Phase 8:** Postgres and pgvector, S3-compatible store, Redis queue, Docker, billing behind a feature flag, privacy (export and delete account), error tracking, full security review, dependency audit, load test, Google sign-in.

## 10. Before every merge to main (self-review checklist)
- `make check` green from a clean install; migrations applied on a fresh database; real-stack run done.
- Diff reviewed for secrets, missing ownership checks, unvalidated input, overly broad CORS, leaked PII in logs, dead code, and files over about 300 lines.
- UI inspected in a browser at three widths and both themes (if UI changed).
- Docs updated (roadmap status, `CLAUDE.md` commands, decisions, API contracts in `docs/api/`).
- Report written, including what was **not** verified.

## 11. First actions
1. Read the docs in section 3 and run `make install && make check` to confirm the baseline.
2. Create `docs/briefs/phase-2-ingestion.md` from section 9, create branch `phase-2-ingestion`, and start with the fixture spike and the data model.
3. Keep going phase by phase. Pause only for the items in section 7.
