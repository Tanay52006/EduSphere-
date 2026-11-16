# 07. Decisions and risks

## Decisions I made for you [my calls]: change any of these

| # | Decision | Why | Revisit if |
|---|---|---|---|
| D1 | Web app first, PWA later; no native | Fastest path to a usable SaaS | Mobile is the main channel |
| D2 | Audience: students and self-learners | Matches the references | Targeting schools/institutions |
| D3 | FastAPI + SQLAlchemy + SQLite → Postgres | Python backend, painless cloud move | |
| D4 | Provider-agnostic `LLMProvider`. **Decided 2026-11-12: Gemini API and Vertex AI** (Fredrick supplies credentials); mock and Ollama kept for tests/dev. | Cost and quality can be tuned; both references used Gemini | You've committed to a single vendor |
| D5 | Persistent SQLite embedding rows with Python cosine scoring behind `VectorStore`; pgvector later; `sqlite-vec` deferred | No extra service locally and it works with the supported Python SQLite runtime, which does not expose loadable-extension support; `VectorStore` keeps the migration boundary explicit | Corpus size outgrows brute-force scoring or the runtime gains supported extension loading |
| D6 | Own RAG + LLM; **no NotebookLM dependency** | Account-cookie auth and ToS make it unusable for a SaaS | Google ships a suitable official API |
| D7 | YouTube Data API only; no scraping | ToS and robustness | |
| D8 | `@antv/infographic` as a pinned, lazy-loaded dependency | MIT, built for LLM output | The Phase 7 spike shows bundle or privacy problems |
| D9 | Single-player games first; real-time multiplayer deferred | Polling-based multiplayer in iks was the heaviest, most fragile part | Social is a core growth loop |
| D10 | Server-authoritative scoring | Leaderboard integrity | |
| D11 | Email+password first; Google sign-in deferred to Phase 8 (see `08`) | Fewer moving parts to validate the product | You want only SSO |
| D12 | **ragforge: port a subset of its ideas to Python; no dependency, no Node sidecar** | JS vs Python backend, single-author young project, MIT allows porting | A Python equivalent appears or Node is adopted anyway |
| D13 | Retrieval default = vector + FTS5 → RRF, no LLM at query time; techniques opt-in by eval | Cost, and ragforge's own benchmark shows techniques often don't pay | Our eval shows otherwise |
| D14 | Use `google-genai` for Gemini API and Vertex AI adapters, sharing one provider boundary and injectable clients in tests | Google documents one current Python SDK for both surfaces; it avoids direct SDK calls outside `app/ai/` and keeps transports mockable | A required Google capability is unavailable in the SDK |
| D15 | Use `pypdf` for Phase 2 extraction and detect scanned pages as an OCR gap | BSD-3-Clause is compatible with a commercial SaaS; PyMuPDF is AGPL and OCR is explicitly deferred | OCR becomes a Phase 2 exit requirement |
| D16 | Configure Gemini with `GEMINI_API_KEY`; configure Vertex with `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and ADC or `GOOGLE_APPLICATION_CREDENTIALS`; model names stay in settings | Matches current Google documentation and avoids credential material in code | Google changes the SDK/config contract |
| D17 | Reject vector hits below a configurable cosine-similarity threshold (default `0.55`) before hybrid fusion | Prevents unrelated user documents from appearing as answers when a query has no strong semantic match; exact keyword matches remain available | Retrieval evaluation shows the threshold is too strict or a reranker is needed |
| D18 | Use `gemini-3.8-flash` as the default Gemini text/JSON model for both Gemini API and Vertex adapters | Google currently documents it as a supported stable model, while the configured `gemini-2.5-flash` endpoint rejects new users | Google changes availability or the project selects a different cost/quality tier |
| D19 | Retain the existing app UI; add authored Chain Reaction alongside PDF practice | Contributor explicitly superseded the standalone illustrated-world redesign on 13 November; focus time on gameplay | Contributor requests a broader redesign |
| D20 | Generate validated game data for three learning mechanics: rebuild, classify and connect | Contributor requested varied subjects and dynamic games; reuse controls, scoring and source checks while refusing unsupported structures | A new learning objective needs a distinct, validated mechanic |
| D21 | Retain Groq text/JSON generation with optional Gemini embeddings when `GEMINI_API_KEY` is supplied | Preserves main's independent embedding backend and the feature branch's verified structured generation, without requiring Gemini just to generate questions | An explicit alternative embedding backend is required |
| D22 | Preserve main's stopword-normalized, phrase-boosted keyword search and reusable worker event loop | Keep the retrieval regression fix and avoid reusing a provider across closed event loops | Retrieval evaluations or a different worker architecture require changes |
| D23 | Cap question/game source text at 16,000 characters; validate only cited source windows in small batches | Combines main's bounded-context fix with the feature branch's source-quote and request-size checks | Broader coverage requires topic batching |
| D24 | Consolidate the overlapping Phase 3 implementations into the reviewed learning API/UI and join migration histories at `0009_reconcile_phase3` | Two ORM models and incompatible game APIs cannot own the same tables and routes; migrate existing main records and retain their original archive | A released external client requires a versioned compatibility API |

## Questions only you can answer (they change what gets built)

1. ~~LLM provider and keys~~ **Answered:** Gemini API and Vertex AI; Fredrick provides credentials. Still open: monthly spend ceiling for development.
2. **CleverTap account:** which account and region, and do we use a dedicated test project? Is push to the web a priority, or email and in-app first?
3. **Monetisation:** free tier limits and paid plan shape (document count, LLM usage, games)? Billing is only planned for Phase 8, but quotas should be designed now.
4. **Audience and language:** English only at launch? Any institution or exam focus (e.g. Indian boards) that should shape content?
5. **Cloud target:** any preference (AWS, GCP, Azure, Render/Fly)? Only matters at Phase 8.
6. **Name and brand:** is "EduSphere" final? (The Campus-Courses presentation file already uses the name.)
7. **Document types:** PDF only at launch. Do you need scanned PDFs (OCR), slides or Word files early?

## Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| LLM generates wrong questions | Core trust failure | Citation + validation pass; mark and drop unvalidated; user can flag a question; track the pass rate (target ≥ 85% of generated questions validated, to be tuned) |
| LLM cost runaway | Money | Per-user budgets, rate limits, caching, small models for validation, kill switch |
| Prompt injection via PDFs | Data leak, bad output | Quote chunks as data, schema-validate output, no tool access from the generation context |
| Cross-user data exposure | Severe | Per-user scoping everywhere, IDOR tests per router, vector queries filtered by user |
| YouTube quota exhaustion | Path B degrades | Lazy resolve, cache with TTL, daily budget counter, graceful "no video" |
| Big PDFs slow or fail | Bad first impression | Page caps, job progress, resumable jobs, clear errors |
| Gamification feels childish or pushy | Churn, brand harm | Design principles in `04`/`05`, nudge guardrails in `06` |
| Infographic library surprises (bundle, icon network calls, pre-1.0 API) | Perf, privacy, breakage | Phase 7 spike, pin version, lazy-load |
| Notification fatigue / legal consent | Opt-outs, compliance | Explicit opt-in, caps, quiet hours, preference centre |
| Scope creep | Never ships | Phase gates in `03`; "Later" list is not a to-do list |
| Leaked reference keys | Security | Rotate the keys in `References/iks/.env`; never copy references' env files |

## Not assessed yet
No code exists, so security, performance and accessibility claims in these docs are design intent, not verified results. Each phase's exit criteria say what must be verified.
