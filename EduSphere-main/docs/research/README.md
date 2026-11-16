# Research base

Four papers anchor the design. PDFs are in `papers/` (arXiv / ACL Anthology copies; page counts and titles checked). Cite them in design discussions and in code comments where a decision depends on them.

| # | Paper | File | What we take from it |
|---|---|---|---|
| 1 | Lewis et al., **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks**, NeurIPS 2020 ([arXiv:2005.11401](https://arxiv.org/abs/2005.11401)) | `papers/lewis2020-rag.pdf` | The core pattern: retrieve passages, then generate conditioned on them. Grounding and provenance are why every question and answer carries `source_chunk_ids`. Non-parametric memory can be updated or deleted per user without retraining. |
| 2 | Es et al., **Ragas: Automated Evaluation of Retrieval Augmented Generation**, 2023 ([arXiv:2309.15217](https://arxiv.org/abs/2309.15217)) | `papers/es2023-ragas.pdf` | Reference-free metrics: *faithfulness* (is the answer supported by the context), *answer relevance*, *context relevance*. Our question-validation pass is a faithfulness check; our dev eval harness reports context relevance and hit-rate. |
| 3 | Gao et al., **Precise Zero-Shot Dense Retrieval without Relevance Labels** (HyDE), 2022 ([arXiv:2212.10496](https://arxiv.org/abs/2212.10496)) | `papers/gao2022-hyde.pdf` | An optional query-time technique (embed a hypothetical answer instead of the query). It is one of the techniques ragforge benchmarks. We treat it as opt-in per measured benefit, not a default. |
| 4 | Settles and Meeder, **A Trainable Spaced Repetition Model for Language Learning** (half-life regression), ACL 2016 ([ACL P16-1174](https://aclanthology.org/P16-1174/)) | `papers/settles2016-half-life-regression.pdf` | Theory for modelling memory decay per item and scheduling reviews. Basis for our review queue. Phase 5 starts with a spike comparing SM-2, FSRS and a simple half-life model on synthetic data. |

## Link-only (not stored; not openly downloadable)
- Hamari, Koivisto, Sarsa, **Does Gamification Work? A Literature Review of Empirical Studies on Gamification**, HICSS 2014 (DOI 10.1109/HICSS.2014.377). Its headline finding is that effects are positive but depend heavily on context and user, with novelty effects as a caveat. We design for sustained motivation (mastery, streaks, progress) rather than novelty points. Obtain it through the author-hosted copy or the DOI.

## Where the papers show up
- `docs/02-architecture.md`: RAG pipeline, validation pass (papers 1, 2).
- `docs/08-scope-and-rag-strategy.md`: retrieval strategy, eval harness (2, 3).
- `docs/05-gamification-and-games.md`: review queue and XP design (4, Hamari).

## Rules
- Do not claim a paper "proves" a product behaviour. They justify design choices, and our own eval and usage data decide.
- Copyright stays with the authors. These PDFs are for internal reference. Don't redistribute them in a public repo; keep `papers/` out of any public release.
