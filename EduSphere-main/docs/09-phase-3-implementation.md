# Phase 3 implementation

Started 12 November 2026 on `feat/phase-3-learning-games`, branched from the repository's current default, `phase-2-ingestion`. The contributor explicitly requested Phase 3 work while Phase 2's remaining verification is open. Neither phase's exit gate is being marked complete.

## What works

- Library → question bank → generation → either game → results → persisted progress.
- Up to 24 questions per generation (16 multiple-choice and 8 definition-pair questions requested). Every accepted question has a verbatim source quote, a user-owned chunk, a separate validation verdict, and a PDF/page link. Invalid structured responses get one repair attempt, then fail safely. Generation and validation go through the existing provider interface inside `app/ai/`.
- Latest-run acceptance count and pass rate in the bank. Duplicate prompts are suppressed. Flagged, edited, and removed questions are excluded from future sessions. Prompt edits deliberately remove validation; generated replacements receive the full validation pipeline.
- A maximum of 5 generation attempts in a rolling 24 hours and 100 active questions per document. Attempts are reserved before provider calls. Source context is bounded to the first 8 chunks and 4,000 characters per chunk.
- Quiz Blitz: 10 randomly selected validated questions, 30 seconds each, 3 lives, combo scoring, and server-checked feedback after each response. The next timer starts only after Continue. Pause and tab visibility pause the server clock. Sessions expire after one hour.
- Memory Match: 6 randomly selected definition pairs, 12 opaque card IDs, server-side reveals and matching, move count, and source-linked review. Neither game sends unrevealed answers in the session payload.
- The server computes results, stores them, and awards XP in one transaction. Result collection is idempotent; clients cannot submit a score, accuracy, elapsed time, or XP amount. A user-row write lock serializes session transitions and XP awards. Game XP is capped at 200 per local day; identical question-set replays diminish rewards. First activity and daily-goal bonuses are awarded once per local day.
- Append-only XP ledger, derived levels, timezone-aware streaks, longest streak, one automatic missed-day freeze per ISO week, and four starter badges: First Session, Perfect Recall, 3-Day Streak, and 7-Day Streak.
- Home and Progress display server totals. Auth transitions clear the query cache to prevent the next account from seeing cached private questions or documents.
- Ownership checks cover banks, mutations, PDF source files, and every session action. Existing cookie authentication and CSRF checks apply throughout. The migration adds six tables; document deletion cascades to banks and sessions while the XP ledger remains intact.
- Existing `analytics.track` wrapper emits generation, game start/complete/abandon, XP, level, streak, freeze, and badge events. CleverTap remains the existing no-op until Phase 6.

## Design references and decisions

The supplied Interface Craft skill was read and applied. The Othello **mobile app** was inspected at its shared theme, dashboard palette, dashboard screen, buttons, motion tokens, and icon assets. The useful lessons were unified tokens, restrained surfaces, reliable press feedback, consistent hit areas, and movement that explains state.

The following sites were reviewed before implementation:

- [Canva Education](https://www.canva.com/education/): a clear learning proposition and simple entry points.
- [Dribbble education dashboards](https://dribbble.com/search/education-dashboard), including HALO LAB's Filko preview: quiet navigation, editorial hierarchy, and focused study areas.
- [Behance learning-app work](https://www.behance.net/search/projects/learning%20app), including Talkie, Dafi, and Ripple previews: learning presented as a personal, approachable workspace. Behance initially rejected the text fetch; the references were subsequently reviewed in the browser.
- [Recent.dev](https://www.recent.dev/): restrained application chrome, concise controls, and strong typographic hierarchy.

The latest contributor instruction supersedes the standalone illustrated-world redesign: build on the existing UI and improve the games. Games now includes Chain Reaction alongside Quiz Blitz and Memory Match, with the same shell and themes. The biology challenge adds ATP prediction, pathway construction, fault repair and targeted missing-input feedback. Generated subject artwork remains inside the interactive board; the separate island map and custom navigation were removed. See [Chain Reaction](10-chain-reaction.md) and [asset provenance](../frontend/public/assets/learning/README.md). Rive is deferred; the [motion plan](11-rive-motion-plan.md) is retained as historical research.

Additional references reviewed for the game redesign:

- [Duolingo's learning path](https://blog.duolingo.com/new-duolingo-home-screen-design/): clear progression, bold silhouettes, and characters accompanying learning.
- [Brilliant](https://brilliant.org/): raised primary actions and focused interactive learning surfaces.
- [Sk Nahid Hasan's quiz app on Dribbble](https://dribbble.com/shots/27472044-Interactive-Quiz-App-Design-EdTech-Mobile-UI-UX-Design): dimensional game objects and colourful challenge entry points.
- [aesevza's gamified education app on Behance](https://www.behance.net/gallery/245179049/Gamified-AI-Education-Platform-Mobile-App-UXUI): a coherent character and game-world identity across screens.

These informed the interaction and visual direction; their artwork and code were not copied. Scores, XP, streaks, unlocking requirements, timers, and card reveals still use the existing server contracts.

Press feedback uses 150ms and the Interface Craft ease-out curve. Frequent selections are immediate. State changes use transform/opacity with reduced-motion overrides. Mobile navigation retains the active-page signal and exposes a theme button. The HTML entry now includes language, title, and viewport metadata, which are necessary for real-phone layouts. Small body copy uses a darker neutral for contrast.

## Local use on Windows

Run the following from `backend/` after creating the virtual environment and installing `.[dev]`:

```powershell
$env:LLM_PROVIDER = 'mock'
New-Item -ItemType Directory -Force storage | Out-Null
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, from `backend/`:

```powershell
$env:LLM_PROVIDER = 'mock'
.\.venv\Scripts\python.exe -m app.workers.process
```

In a third terminal, from `frontend/`:

```powershell
npm ci
npm run dev
```

Create a local account, complete onboarding, and upload `backend/tests/fixtures/pdfs/biology-glossary.pdf` via Library. Wait for Ready, choose Make it playable, generate questions, then select the document on Games. The authored Chain Reaction chapter is available immediately at Games without a PDF or provider call. The deterministic mock supports glossary-style text and is for development; it is not a substitute for a real-model quality evaluation.

The only added runtime dependency is `tzdata`, because Windows does not supply the IANA timezone database required by Python's `zoneinfo`. No frontend dependencies were added. The existing Ollama adapter was corrected to send the JSON schema and parse a JSON object, following [Ollama's documented structured-output contract](https://github.com/ollama/ollama/blob/main/docs/api.md). Its HTTP contract is tested without requiring a running model.

## Verification

- Backend: **89 passing tests**, Ruff, and mypy. One pre-existing test invokes Unix `make migrate`; Windows has no `make`, so that test is excluded from the Windows run. The configured-database Alembic test and direct `alembic upgrade head` cover migration execution here.
- Frontend: `npm run check` (ESLint, Prettier, TypeScript, 19 Vitest tests) and `npm run build`. The test setup handles Node 25's experimental global storage. Prettier accepts the checkout's platform line endings without reformatting unrelated files.
- Browser: real cookie/CSRF API, signup → onboarding → six-page PDF upload → worker ingestion → question generation → source links → both games → XP and streak → Progress. Quiz result reload confirmed persistence. The first clean fixture generation returns 24 accepted questions; an earlier browser run identified and fixed glossary entries being missed after PDF headings.
- Initial paired browser run: Quiz Blitz 10/10, +75 XP; Memory Match 6/6 pairs with server-counted moves, +32 XP; combined 107 XP, 1-day streak, daily goal reached, First Session and Perfect Recall badges. These are development/mock results, not a real-model accuracy benchmark. A subsequent keyboard-only Memory Match round also completed and returned all six cited reviews.
- Layout inspection at 375px, 768px, and desktop; light and dark themes; keyboard controls, retained focus, and reduced motion. No horizontal scrolling at the checked widths. Sampled new small-text contrast was 5.10:1; the primary game button was 11.43:1. A final reload caught a scroll-effect cleanup error, which was fixed and retested; the final browser run had no new console errors. Screenshots were captured locally for the contributor, outside the repository.
- Earlier legacy-game visual pass: repeated frontend checks and production build; mobile/desktop and dark-theme inspection; keyboard Memory Match completion (6 pairs, 12 moves, +30 XP); Quiz Blitz pause/resume, correct-answer feedback and source link. The earlier contrast figures describe the original palette. Current Chain Reaction checks are recorded separately in its implementation notes.

## Adaptive subject games

The contributor requested subject variety and dynamic creation on the existing UI. Five authored games and three source-grounded reusable mechanics now run alongside Chain Reaction and PDF question practice. See [generation, scoring, verification and limits](12-adaptive-subject-games.md). The latest automated totals are 95 backend and 23 frontend tests; earlier counts above document previous passes. Local generation is explicitly labelled as a mock-provider preview.

## Still open

- Real Gemini/Vertex/Ollama generation, validation pass rate against a reviewed corpus (target ≥85%), token/cost measurement, and a live deployment. A live Groq smoke test is recorded below; its key is local and gitignored.
- Phase 2's remaining exit verification, including the final 50-page/hostile-input browser exercise and retrieval baseline sign-off. This change does not claim to finish that phase.
- Full-document topic batching, richer answer editing with revalidation, the remaining badge catalogue, document-generation XP bonuses, review scheduling, and larger Memory Match levels. Failed quiz answers are retained in session review; the spaced-review queue belongs to Phase 5. These are not silently represented as complete.
- Real-phone touch testing, production load/concurrency testing, and Postgres execution. Browser viewport emulation is not a real-device test.
- Existing dependency advisories: the production audit reports two moderate React Router advisories; npm offers a major-version upgrade to resolve them. The wider development-tool audit also has existing findings. A router/toolchain migration is not bundled into this feature branch; resolve these before public deployment.

## Live Groq verification — 13 November 2026

The contributor supplied Groq credentials for `openai/gpt-oss-120b`. The app was still running its deterministic mock and had no Groq adapter. Added an adapter using the already-installed HTTPX dependency, selected by `LLM_PROVIDER=groq`, `GROQ_API_KEY` and `GROQ_MODEL`. The key is a masked setting stored only in the ignored local backend `.env`.

The first real run failed safely. Low reasoning effort produced oversized question arrays, and the original all-at-once answer-validation request exceeded this account's 8,000-token request limit. Generation now uses medium reasoning, Groq's strict JSON-schema mode for fixed-shape responses, and an explicit question-count checklist. Validation runs in batches of eight with batch-local indices and only their cited sources. Missing, duplicate or false verdicts still reject the corresponding question. Dynamic-map activity schemas use best-effort schema mode with the existing Pydantic validation and repair. HTTP 429 responses get at most two bounded retries using Retry-After; upstream bodies, prompts and credentials are excluded from errors.

Authenticated browser verification on the existing six-page biology PDF generated **24 questions: 16 MCQ and 8 MATCH**. All **24 passed the separate model validation calls** and were added to the bank (27 → 51). The completed response was visible within 87 seconds, including provider rate-limit waits. All 24 saved evidence quotes were independently checked as verbatim substrings of their saved source chunks. Reload retained the bank and latest metrics. A quiz sampled the new respiration question, accepted its correct answer on the server and showed its PDF source link; the temporary round was then abandoned without XP. This is a live integration smoke test, not a human-reviewed accuracy benchmark or a claim of perfect question quality across subjects.

Final backend checks: **108 passing tests**, Ruff and mypy. The same pre-existing Unix `make` entrypoint test remains excluded on Windows. New tests cover schema translation, credentials, malformed/truncated output, sanitized errors, bounded rate-limit retries and validation-batch verdict isolation. No frontend code or dependencies changed.

Groq is configured for text and structured generation only. This adapter deliberately refuses to fabricate embeddings. New PDF vector ingestion and semantic search require Gemini, Vertex or Ollama; the live smoke test used an already-ingested PDF. The local backend and frontend remain running. Broad subject quality, real dynamic-game generation, embedding-provider composition, cost accounting and production load remain unverified in this pass.
