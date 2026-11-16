# 03. Roadmap

Build in order. Each phase ends with working, tested, demo-able software. Don't start the next phase until the exit criteria hold. Estimates are rough, for one focused builder with an AI pair.

Conventions for every phase: tests for backend logic, an ownership/IDOR test for each new resource, UI per `04`, `analytics.track()` calls from the event list in `06`, docs updated.

> **Scope refinements** (added features, deferrals such as Google sign-in and leaderboard, revised milestones M1–M3) are in `08-scope-and-rag-strategy.md` §2 and override this file where they differ. Research base: `research/README.md`.

## Phase 0: Foundation (≈2–3 days)
- Scaffold `frontend/` and `backend/`, lint, format, type-check, test runners, `.env.example`, `.gitignore` (`.env`, `storage/`, `*.db`), `git init`.
- FastAPI app skeleton, config, SQLAlchemy + Alembic, health endpoint, error format, logging without PII.
- `LLMProvider` interface with a **mock provider**; `analytics.track` no-op wrapper; `VectorStore` and `FileStore` interfaces.
- Fill the Commands section of `CLAUDE.md`.
- **Exit:** one command starts both apps; CI-style script runs lint, types and tests green.

## Phase 1: Identity, onboarding, app shell (≈1 week)
- Sign up / sign in / out (argon2id, httpOnly cookie, CSRF), Google sign-in, rate limiting, basic profile.
- Design tokens and base components (`04`): button, input, card, tag, modal, toast, sidebar, empty/loading/error states. Run the `impeccable` skill to produce `DESIGN.md`.
- Onboarding: name/goal → **fork** (own materials vs. learn something new) → lands in the right place. Home with both entry points. Timezone and notification-consent capture.
- **Exit:** a new user signs up, completes onboarding, and reaches a styled Home. Auth and ownership tests pass; responsive and keyboard-navigable; browser-verified.

## Phase 2: Library and RAG ingestion (≈1.5 weeks)
- Upload UI (drag-drop, validation errors), `documents`, `FileStore`, job runner with progress.
- Extract → chunk → embed (`VectorStore` sqlite-vec) → topic map.
- Library page: statuses, delete (removes files, vectors and rows), per-user quotas.
- Grounded chat with citations (small, proves retrieval works).
- **Port ragforge's retrieval ideas to Python** (`ai/retrieval/`: RRF, hybrid search over vector + FTS5, optional query translation, router) and its eval harness as `backend/tools/rag_eval.py` (fixture PDFs, hit@k, MRR, cost). Add `THIRD_PARTY_NOTICES.md` (MIT). Run the fixture spike first (`08`). Record the baseline in `docs/research/rag-eval-baseline.md`.
- **Exit:** eval harness runs in CI on the fixtures and reports hit@k and MRR; upload a 50-page PDF, see progress, ask a question and get a cited answer; another user cannot see it; malicious or oversized file rejected.

## Phase 3: Question engine + gamification core + first 2 games (≈2 weeks)
Implementation started on `feat/phase-3-learning-games` at the contributor's explicit request while Phase 2 verification remains open. [Current implementation, design references, checks, and limits](09-phase-3-implementation.md). This does not mark the Phase 2 or Phase 3 exit gates complete.

- Generation + validation pipeline (`02`), `questions` table, mock-provider tests; question bank view with edit/delete.
- `xp_events` ledger, levels, streaks, daily goal, server-authoritative `game_sessions`, results screen. Badges (small starter set).
- **Game 1 Quiz Blitz** and **Game 2 Memory Match** (`05`).
- **Exit:** upload → bank of ≥20 validated questions → both games playable → XP and streak update; validation pass rate measured and ≥ target in `07`; client cannot forge scores.

## Phase 4: Games 3–4 and game polish (≈1.5 weeks)
- **Game 3 Word Hangman**, **Game 4 Brain Ladder** (single-player Snake & Ladder with live challenge questions and AI post-game report).
- Game picker per document showing which games are available given the question mix; haptic-feel animations, sound toggle, reduced-motion support.
- **Exit:** ≥4 games work end-to-end from one PDF. Own-materials path is feature-complete. **Milestone: Path A demo.**

## Phase 5: Learn something new (≈2 weeks)
- Topic + level input, diagnostic quiz, pathway generation (mock + real provider), path view (modules → lessons).
- Lesson view with explanation, worked example, lazy resource resolver (YouTube Data API, cache + quota budget), lesson quiz, mastery gating, module test.
- Spaced-repetition review queue (FSRS or SM-2), shared with Path A questions.
- Path completion card.
- **Exit:** a new topic yields a coherent path; videos are relevant or absent; progress, XP and review queue work; quota counter proven under load test of 10 paths.

## Phase 6: CleverTap nudges (≈1 week)
- Real `analytics` backend: web SDK (identity, web push, in-app) and server Upload API for authoritative events. Event and property taxonomy from `06`.
- Notification settings page (consent, quiet hours, per-channel).
- Build the starter campaigns/journeys (streak at risk, upload-but-no-game, stalled path, review due, welcome series). The CleverTap MCP connection can draft these.
- **Exit:** events visible in the CleverTap dashboard; a test user receives each starter nudge; frequency caps and opt-out verified; no PII or document content sent.

## Phase 7: Visuals and polish (≈1.5 weeks)
- Infographic spike (bundle size, icon network behaviour); then summaries, pathway overview, achievement share card using `@antv/infographic` (lazy-loaded, pinned).
- Flashcards and study-guide artifacts; mind map; weekly progress recap. Leaderboard (friends or global, display name only).
- **Exit:** a document produces a study-guide infographic; share card exports PNG; main bundle is not inflated.

## Phase 8: SaaS hardening (≈2 weeks)
- Postgres + pgvector, S3-compatible store, Redis queue; Dockerfiles and a deploy pipeline; environment configs.
- Plans, quotas and billing hooks (e.g. Stripe) behind a feature flag; admin view of LLM cost; error tracking and metrics; backups.
- Privacy: export and delete account, ToS/privacy pages, cookie consent.
- Security review of the whole diff, dependency audit, load test.
- **Exit:** the staging environment runs on cloud DB; the migration from local data is documented; security checklist signed off.

## Later (not scheduled)
Teacher/class mode, real-time multiplayer (WebSockets), audio overviews, grounded voice tutor, mobile PWA/native, OCR for scanned PDFs, URL/YouTube/text as sources, Quest Wheel and card collection.

## Dependency map

`0 → 1 → 2 → 3 → 4` (Path A) and `1 → 5` (Path B can start in parallel after Phase 1 if there are two builders; the question and review engines from 3 are reused in 5, so sequential is simpler). `6` needs events from 3–5. `7` and `8` come last.
