# 08. Scope refinement and RAG strategy

## 1. Can we use ragforge?

Reference: `References/ragforge` (cloned, **not executed**; MIT, © 2025 Kamraan Mulani; v2.1.0; single author; ~2,500 lines of Node.js).

**What it is:** an npm library and CLI for *query-time* RAG techniques (HyDE, Step-Back, Fan-Out, Chain-of-Thought, hybrid BM25, reranking, Reciprocal Rank Fusion), plus an **eval harness** that generates questions from your chunks, scores each technique (hit@k, MRR, latency, cost) and a **router** that picks a technique per query. Providers: OpenAI and Ollama. Vector store is pluggable; its built-in one is in-memory.

**What it is not:** a Python library, a persistent ingestion pipeline, a PDF-structure parser, or a game/question generator. Its chunker is simple (800 chars, no overlap, by design for fair eval scoring), PDF text comes from `unpdf`, and nothing is stored on disk.

**Verdict: use the ideas and port a subset to Python. Do not depend on it or run it as a sidecar.**

| Question | Answer |
|---|---|
| Can we copy the code into the backend? | Not directly: it's JavaScript, our backend is Python. A Node sidecar would add a second runtime and deploy target for ~600 lines of logic. |
| Is the licence OK? | Yes, MIT. Keep the copyright notice in a `THIRD_PARTY_NOTICES.md` for ported code. |
| Is it mature enough to depend on? | No: single author, young. Porting avoids the risk. |
| Does it do "AI-based parsing"? | Only text extraction (PDF, DOCX, HTML). Structure parsing (chapters, topics, prerequisites) is our own pipeline (doc 02, from the iks idea). |
| Does it do "generation"? | It generates cited *answers* and evaluation *questions*. Our game question engine and validation pass are separate (doc 02). |
| Does its own benchmark support using every technique? | No. Its README reports that on its test corpus plain search matched or beat every technique and HyDE cost ~350× more per query. That is the author's claim, not verified by us. It argues for **measuring before enabling techniques**. |

### What we port (Phase 2, to `backend/app/ai/retrieval/`)

| ragforge source | Python target | Notes |
|---|---|---|
| `techniques/rrf.js` | `rrf.py` | Reciprocal Rank Fusion for merging vector + keyword (+ query variants). Core of hybrid search. |
| `techniques/{hyde,stepback,fanout,cot}.js` | `query_translation.py` | Opt-in; each returns query variants; behind a config flag per technique. |
| `eval/bm25.js` | **Use SQLite FTS5 instead** (`bm25()` built in; Postgres full-text later) | Better than porting a hand-written BM25. |
| `router/{classify,route}.js` | `router.py` | Rule-based classifier (comparison, exact, short, conceptual, simple), default map, learn per-category winners from an eval result. |
| `eval/{evaluate,chunk,report}.js` | `backend/tools/rag_eval.py` | **Dev/CI tool**, not a user feature: question-from-chunk with the source chunk as ground truth, drops "unanswerable" phrasing, hit@k, MRR, cost. |
| `core/{stats,pricing,cache}.js` | `ai/usage.py`, `ai/cache.py` | Merge into our LLM budget and usage tracking. |
| `rerankers/` | later, optional | Add only if eval shows a gain. |
| `loaders/`, `memoryVectorStore.js`, CLI, providers | skip | PyMuPDF, `VectorStore` interface and `LLMProvider` already cover these. Add an **Ollama adapter** for free local development. |

### Retrieval default
`hybrid = vector top-N + FTS5 top-N → RRF → top-k`. No LLM calls at query time by default. Query-translation techniques are enabled **only** if `rag_eval` shows ≥5 points improvement on our own fixture corpus (ragforge's own decision rule), and the router can use per-query categories. Reference papers: RAG (Lewis), HyDE (Gao); evaluation metrics: Ragas (Es). See `research/README.md`.

### Phase 2 spike (before porting)
1. Build a fixture set: 5–8 representative student PDFs (lecture notes, textbook chapter, slides export, a scanned one to confirm the OCR gap).
2. Run ragforge's eval once on the same files with an OpenAI key or Ollama (a throwaway run, outside the repo) to get a baseline for our Python port to match.
3. Port, then compare scores. Record results in `docs/research/rag-eval-baseline.md`.

## 2. Sharper v1 scope (what is actually doable)

The original plan has two full products and a CleverTap layer. Principle: **make Path A excellent end-to-end first; keep Path B thin; add cheap features that exploit data we already have; defer anything needing a new subsystem.**

### Add (small, high value; each reuses existing tables)
| Feature | Why | Phase |
|---|---|---|
| **Exam countdown planner**: "test on <date>" → daily plan from topic mastery and the review queue | The crammer persona's real need; no new infrastructure | 5 |
| **Weak-spot mode**: games weight questions from low-mastery topics | Turns play into learning, one query change | 4 |
| **Source-linked explanations**: each explanation cites page and chunk and opens the PDF at that page | Trust differentiator vs. generic quiz apps | 3 |
| **Flag a question**: user flags bad questions; flagged ones are suppressed and counted in the quality metric | Cheap feedback loop for the validation pass | 3 |
| **RAG eval harness in CI** (port of ragforge eval) on a fixture corpus | Regressions in retrieval or question quality are caught automatically | 2 |
| **Ollama adapter** | Free local dev and tests, no key needed | 0 |
| **Export**: study guide as Markdown/PDF; flashcards as CSV for Anki | Students ask for it; low effort | 7 |

### Defer or cut from v1
| Item | Move to |
|---|---|
| Google sign-in | Phase 8 (email+password is enough to validate) |
| Leaderboard | Phase 7 as friends-only, or later |
| Quest Wheel, card collection, Match Rush | "Later" |
| Mind map and audio overview | "Later" |
| OCR for scanned PDFs | After Phase 4 if fixtures show demand; until then, detect and show a clear message |
| Diagnostic quiz in Path B | Keep optional; self-assessed level alone is acceptable for the first Path B release |

### Revised milestones
- **M1 (end of Phase 4): Path A demo.** Sign up → upload → 4 games → XP, streak, weak-spot mode.
- **M2 (end of Phase 5): both paths + exam planner.**
- **M3 (end of Phase 6): nudging live.** Then visuals and hardening.

### Doability check
- Everything above sits on tables and services already designed (`questions`, `review_items`, `xp_events`, `jobs`).
- The only genuinely new technical risks are PDF quality (messy extraction) and validation-pass cost. The first is covered by the fixture spike, the second by per-user budgets and small-model validation.
- Not assessed: real LLM cost per document, and question-validation accuracy. Phase 2–3 exit criteria measure both.
