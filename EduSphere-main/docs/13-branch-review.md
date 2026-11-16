# Reviewing the reconciled Phase 3 branch

The two Phase 3 histories were reconciled on `feat/phase-3-learning-games` before integration into `main`. The reviewed app UI, Chain Reaction, five subject games, source-grounded game generation, question bank, Quiz Blitz and Memory Match remain the active implementation.

Main's natural-language keyword-search fix, research PDF fixture, persistent worker event loop, Groq embedding delegation, safe provider diagnostics and context budget are retained. Duplicate Phase 3 ORM models, routes, clients and services were consolidated into one implementation. The active question API is `/api/documents/{id}/questions` and `/api/documents/{id}/questions/generate`; gameplay uses `/api/games/sessions`, with individual answer/flip requests and server-controlled final submission. The previous `/api/questions/generate` and client-batched game submission contract are superseded, not maintained as a second scoring system. New generated banks request 16 MCQs and 8 individual definition pairs.

## Checkout

From a clean local checkout:

```powershell
git fetch origin
git switch feat/phase-3-learning-games
git pull --ff-only origin feat/phase-3-learning-games
```

Keep your existing `backend/.env`, PDF storage and database. Back up the database before migration, including any SQLite WAL state; stop your backend and worker before taking a filesystem copy. Do not reset or delete the database to switch branches.

## Windows startup

Use Python 3.14+ and Node.js 24+. From the repository root, terminal 1:

```powershell
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
if (!(Test-Path .env)) { Copy-Item .env.example .env }
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2, from the repository root:

```powershell
cd backend
.venv/Scripts/python.exe -m app.workers.process
```

Terminal 3, from the repository root:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open [EduSphere](http://127.0.0.1:5173). A fresh `.env.example` uses the deterministic mock, so the demo works without sharing credentials. Sign up and complete onboarding; authored games are immediately available. For the PDF flow, upload `backend/tests/fixtures/pdfs/biology-glossary.pdf`, wait for Ready, generate questions and play both question games. Development previews are explicitly labelled.

For live generation, set `LLM_PROVIDER=groq`, a private `GROQ_API_KEY` and `GROQ_MODEL=openai/gpt-oss-120b` in your own `.env`, then restart backend and worker. Groq generation does not require a Gemini key. Add `GEMINI_API_KEY` to use Gemini embeddings for uploads/search; Groq has no embeddings of its own. Do not commit or exchange `.env` files.

## Database compatibility

There is one Alembic head: `0009_reconcile_phase3`. Both existing revision histories remain recognized. Upgrade tests cover the pre-Phase-3 schema, main's question-only schema, main's gamification schema and the feature branch's activities schema.

Feature-branch questions, activity sessions, generation history, XP and streaks remain unchanged. For a database from main, original rows are first copied into `legacy_*` archive tables with ownership foreign keys. Questions, XP, streaks, badges and completed sessions are then converted to the active schema. Existing true/false questions become two-option quizzes; packed MATCH groups become individual pairs. An existing validation flag is retained only when its citations resolve to the same user and document. Original payloads and result records remain in the archive.

Main's open rounds used a different answer/state contract and must be restarted; their original records remain archived and their new counterparts are marked abandoned. Existing feature-branch rounds can resume normally. Reconciliation never awards XP. Downgrading across the merge is deliberately refused; restore a pre-upgrade backup to reverse it safely.

## Review checklist

- Sign in, verify the question bank and existing progress, and resume a feature-branch activity.
- Complete Chain Reaction or one subject game; reload its saved result.
- Upload a PDF, generate its question bank, open a source link, and play Quiz Blitz and Memory Match.
- Check library natural-language search with an embedding-capable provider or the mock.
- Run backend pytest/Ruff/mypy and frontend `npm run check` plus `npm run build`.

Automated and local browser results from the merge verification are recorded in `progress.md`. These checks do not establish live Gemini embedding availability, Postgres compatibility, broad model accuracy or production load capacity. Historical implementation plans and reports describe their original snapshots rather than the active merged API.
