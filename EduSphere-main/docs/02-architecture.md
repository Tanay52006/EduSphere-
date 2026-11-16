# 02. Architecture

All stack choices are **[my call]** unless stated; see `07-decisions-and-risks.md`.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript, React Router, TanStack Query, Tailwind CSS, Radix UI primitives, Framer Motion (restrained) | Fast, typed, accessible primitives, easy to hit a custom Notion-like look |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic | Typed, async-friendly, requested Python backend |
| DB (local) | SQLite (WAL mode) | Zero setup; same models run on Postgres later |
| Vectors | `VectorStore` interface; local impl `sqlite-vec`; cloud impl pgvector | Swap without touching callers |
| Jobs | DB-backed `jobs` table + FastAPI background worker; later Arq/Celery + Redis | Ingestion is slow and must not block requests |
| LLM | `LLMProvider` interface; adapters for Gemini and Claude; chosen by env | Both reference apps used Gemini; keep options open and cost controllable |
| Auth | Email+password (argon2id) and Google sign-in; session in httpOnly, Secure, SameSite cookie; CSRF protection | Use established libraries; never custom crypto |
| Files | Local `storage/` behind a `FileStore` interface; later S3-compatible | Cloud move without code churn |
| Analytics | `analytics.track()` wrapper → CleverTap (web SDK + server API) | One choke point |

## Shape

```
React SPA ──HTTPS/JSON──► FastAPI
                           ├─ api/        routers (thin)
                           ├─ services/   business logic (ingest, questions, pathway, gamification)
                           ├─ ai/         LLMProvider, embeddings, prompts, validators, cost limits
                           ├─ repos/      DB + VectorStore + FileStore adapters
                           ├─ workers/    job runner
                           └─ analytics/  CleverTap server client
                           SQLite / (Postgres + pgvector later)
```

Proposed backend layout: `backend/app/{api,services,ai,repos,models,schemas,workers,analytics,core}`, with `tests/` mirroring it. Frontend: `frontend/src/{app,features/{onboarding,library,games,paths,gamification,visuals},components,lib,styles}`.

## Data model (core tables)

All user-owned rows carry `user_id` and every query is scoped by it.

- **Identity:** `users`, `profiles` (name, goal, level prefs, timezone, locale, notification consent), `sessions`.
- **Own materials:** `documents` (file ref, status, page count, hash), `chunks` (doc, ordinal, text, page, token count), `chunk_embeddings` (via `VectorStore`), `topics` (doc, title, summary, parent, prerequisites).
- **Questions and games:** `questions` (type, prompt, payload JSON, answer, explanation, difficulty, topic, `source_chunk_ids`, `validated`), `game_sessions` (user, game, question ids, server-held answers, state, started/ended), `game_results`.
- **Pathways:** `learning_paths` (topic, level, status), `path_modules`, `path_lessons` (content JSON, quiz JSON), `resources` (type, url, title, duration, verified), `resource_cache` (query key, payload, expires_at), `enrollments`/`progress`.
- **Gamification:** `xp_events` (append-only ledger), `streaks`, `badges`, `user_badges`, `review_items` (spaced-repetition state per question/topic).
- **Platform:** `jobs` (type, status, progress, error), `llm_usage` (user, model, tokens, cost, feature), `notification_prefs`.

## Question schema (single table)

```json
{
  "type": "MCQ | TF | FILL | MATCH | ODD | CAT | SCRAMBLE",
  "prompt": "…",
  "payload": { "options": [], "pairs": [], "items": [], "categories": [] },
  "answer": "…", "explanation": "…", "difficulty": 1,
  "topic_id": 0, "source_chunk_ids": [0], "validated": true
}
```
Types and JSON shapes are adapted from `iks/README.md`; each game declares which types and minimum counts it needs (see `05`).

## RAG pipeline (Path A)

1. **Upload:** type allow-list (PDF, checked by magic bytes, not extension), size cap, page cap, random storage name, per-user quota.
2. **Extract:** PyMuPDF text; if a page has no text layer, flag for OCR fallback (Phase 2 stretch). Never send whole pages as images by default.
3. **Chunk:** ~400–800 tokens, overlap, keep page numbers and headings.
4. **Embed → `VectorStore`**, and index text in SQLite FTS5 for keyword search. Dedupe by content hash. **Retrieval = vector + FTS5 → RRF** (ported from ragforge; see `08-scope-and-rag-strategy.md`). Query-translation techniques are opt-in, enabled only when the eval harness shows a gain.
5. **Topic map:** LLM over headings and chunk summaries → topics, with prerequisites (iks idea).
6. **Question generation:** per topic, retrieve top chunks, ask for structured JSON by type, then a **validation pass** (second call: "is this answer supported by this chunk?"). Keep only validated questions; store citations.
7. **Status and progress** are written to `jobs`; the UI polls (SSE later).

**Prompt-injection defence:** chunks are wrapped as quoted data, with a system rule to ignore instructions inside them, and output is schema-validated. Questions only ever render as text.

## Pathway engine (Path B)

1. Input: topic, self-assessed level, optional 5-question diagnostic (LLM-generated, adaptive difficulty) → refined level.
2. LLM (JSON mode, Pydantic-validated, repair once, deterministic mock fallback for dev/tests) returns modules → lessons with learning objectives, key points, `video_queries`, `reading_queries`, and lesson quizzes.
3. **Resource resolver (lazy, when a lesson is opened):** YouTube Data API `search` + `videos.list`; filters: embeddable, not Shorts, ≥3 min, topic-token overlap; LLM picks from a shortlist; **prefer nothing to something misleading**. Results go to `resource_cache` with TTL. Quota-aware with a daily budget counter. Official APIs only.
4. Mastery gating: lesson quiz ≥70% unlocks the next lesson; weak topics enter the review queue.

## AI layer rules

- One entry point `ai/`; structured output only; Pydantic validation; one repair retry.
- Per-user daily LLM budget and rate limits; global kill switch; usage logged (tokens and cost, never content).
- Prompts live in versioned files under `ai/prompts/`, with tests using the mock provider.
- Model names come from config, not code.

## Security (design-time threat model)

- **Trust boundaries:** browser ↔ API; API ↔ LLM/YouTube/CleverTap (egress); uploaded files (hostile).
- **Authorization:** deny by default; ownership check on every document, question, session, path (IDOR tests per router). Leaderboards expose only display name, avatar and XP.
- **Server-authoritative games:** the server issues the question set and holds answers; the client submits responses; the server scores and awards XP. Daily XP caps per source stop farming.
- **Input and output:** Pydantic validation; parameterised queries only; path-traversal-safe file storage; CORS allow-list; security headers; markdown rendered through a sanitiser; strict CSP when the infographic icon behaviour is known.
- **Abuse:** rate limiting on auth, upload, generation; upload quotas; LLM budgets.
- **Privacy:** minimal PII to CleverTap (no document content, ever); account deletion removes documents, chunks, vectors and files; secrets from env only.

## Local → cloud path

SQLAlchemy models plus Alembic work on Postgres unchanged (avoid SQLite-specific SQL outside adapters). `VectorStore` → pgvector; `FileStore` → S3-compatible; jobs → Redis queue; config via env. Containerise in Phase 8; plan for a managed Postgres, object store, and a container host.
