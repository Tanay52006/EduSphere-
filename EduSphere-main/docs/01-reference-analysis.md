# 01. Reference analysis

Analysed from `References/` (read-only; nothing was run). **None of the five projects is a drop-in module.** They are sources of ideas and schemas.

| Project | What it really is | Verdict |
|---|---|---|
| `iks` | Django app "GamifiEd": PDF → chapters/topics (Gemini vision) → question bank → 6 server-rendered games | Take game ideas + question schemas. Rewrite everything. |
| `Campus-Courses` | Node/Mongo **LLM course generator** (Gemini writes the course; YouTube/Commons/Jina attach resources). Not an aggregator, no level assessment | Take the generation + resource-filter ideas + XP model. Rewrite in Python. |
| `notebooklm-py` | **Unofficial client** for Google's hosted NotebookLM (cookie auth, undocumented RPCs). Not a clone | Do **not** depend on it. Use as a feature checklist only. |
| `ragforge` | Node.js library: RAG query techniques (HyDE, Step-Back, Fan-Out, RRF, hybrid BM25, rerank), an eval harness and a per-query router. MIT. No persistence, not Python | Port a subset of the ideas to Python for retrieval and eval; do not depend on it. Details in `08-scope-and-rag-strategy.md` |
| `Infographic` | AntV Infographic (`@antv/infographic` 0.2.x, MIT): text DSL → SVG, ~200 templates, streaming render, SVG/PNG export | Use as a pinned, lazy-loaded npm dependency. |

## iks: take / rewrite / discard

**Take (ideas and schemas)**
- Ingest shape: PDF → chapters/topics → topic groups with prerequisites → question bank.
- 7 question formats: MCQ, FILL, MATCH, TF, ODD (odd-one-out), CAT (categorise), SCRAMBLE. JSON schemas are in `iks/README.md`.
- Games: Hangman (`hang`), Memory/flip-card (`flip_card`), Snake & Ladder with live MCQ on challenge cells and an AI post-game report (`snake_ladder`), spin-wheel + rarity cards (`spinwheel`), Housie (generalise to concept↔definition matching).

**Rewrite**
- Ingestion becomes real RAG. iks has **no** embeddings, vector store or retrieval; it sends page images to Gemini, which is costly and breaks on long PDFs.
- 7 per-type tables become one `Question` table with a `type` and a JSON `payload`.
- Per-game columns on one points table become an event-based `xp_events` ledger and `game_results`.
- All UIs (Django templates + inline JS) become React components.

**Discard**: Flutter client, `dbs`, constitution-specific seed data, committed `db.sqlite3`, `media/`, `.history/`, the ElevenLabs chat character (revisit as a grounded tutor later), polling-based multiplayer.

**Warnings**: files of 1000–2400 lines, circular imports, fragile JSON parsing of LLM output, `DEBUG=True`. **Real-looking API keys exist in `References/iks/.env` and `aicharacter/.env`. Rotate them if that repo was ever shared, and never copy them.**

## Campus-Courses: take / rewrite / discard

**Take (reimplement in Python)**
- LLM course generation in JSON mode with sanitise/normalise layers, retry with model fallback, and a deterministic mock when there is no key (great for offline dev and tests).
- Course → module → lesson schema; lesson parts: opening, core explanation, worked example, quiz, exercise, resources.
- YouTube resolution via the **official Data API**: search + `videos.list` for durations. Filters worth keeping: drop Shorts and videos under ~3 min, require embeddable, require topic-token overlap, and **"no video is better than a misleading video"**.
- XP / coins / streak / completion-bonus structure (`ECONOMY_RULES`), 500-XP levels and titles, certificate hash + verify endpoint (optional).
- Its `backend/scripts/course*.test.js` as behavioural specs.

**Rewrite**
- Ranking by token overlap → LLM/embedding relevance over a shortlist.
- In-memory caches with no TTL → persisted `resource_cache` table with TTL.
- Missing pieces we must build: **level assessment/diagnostic, adaptive pathway, spaced repetition, LLM-graded answers.**

**Discard**: the entire legacy ERP (grievance, timetable, attendance, Contineo/Playwright, HOD, Supabase, Sequelize shim), hardcoded per-topic content, the Solidity contract, **`yt-search` scraping (violates YouTube ToS, fragile)**, Mongo repository code, the demo credential in its README.

**Constraints**: YouTube `search` costs 100 quota units (10k/day default). Resolve resources lazily (when a lesson is opened), cache aggressively, and never resolve per-lesson for a whole path up front. Don't pass API keys in URLs that get logged.

## notebooklm-py: feature checklist only

It drives Google's hosted NotebookLM with full-account browser cookies. Unsuitable for a multi-user SaaS: users can't hand over Google credentials, it likely breaches Google's ToS, the RPCs can change without notice, and quotas are per account. (MIT licence, so code reuse is legal, but nothing worth vendoring.)

**Borrow as concepts, built on our own RAG + LLM:**

| NotebookLM artifact | EduSphere version |
|---|---|
| Quiz (quantity, difficulty, type) | Question engine with the same knobs |
| Flashcards | Flashcards feeding a spaced-repetition scheduler (FSRS/SM-2) |
| Study guide / briefing doc | Map-reduce summary template (key terms, FAQ, short answers) |
| Mind map | Nested JSON → React graph |
| Infographic | AntV Infographic DSL |
| Audio overview | Stretch: two-host script + TTS |
| Chat with citations | Own RAG chat, citation-bearing prompt |

Look at its `docs/python-api.md` and `_types/enums.py` for option vocabularies and the quiz/flashcard JSON shapes.

## Infographic (`@antv/infographic`): use

- MIT, TypeScript, framework-agnostic. In React: instantiate in `useEffect` on a ref, then `render(dsl)`. Re-calling `render` with a growing string supports streamed LLM output.
- LLM generates the **DSL text** (short, cacheable, versionable). Adapt `skills/infographic-syntax-creator/references/prompt.md` as the system prompt (mostly Chinese, output follows the user's language; its template list is partial, so pull the full list from `src/templates`). Validate by rendering in try/catch and retry once on failure.
- Fits: concept summaries (`list-*`, `hierarchy-*`), pathway overviews (`sequence-*`), comparisons (`compare-*`), achievement cards (fixed template + brand palette → PNG export client-side).
- Pin the exact version (pre-1.0). **Lazy-load** via dynamic `import()`; the size-limit budget suggests up to ~500 KB.
- **Spike before committing (Phase 7):** measure the real bundle size and confirm whether icon loaders hit an external network service (privacy, CSP, offline).
- Server-side PNG would need a Node service; avoid, and export client-side.
