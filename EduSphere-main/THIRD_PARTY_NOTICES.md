# Third-party notices

- `ragforge` ideas are reimplemented in Python from the MIT-licensed project described in `docs/08-scope-and-rag-strategy.md`; no reference code or dependency is included.
- `pypdf` is used for permissively licensed PDF inspection and text extraction (BSD-3-Clause).
- `google-genai` is used for Gemini API and Vertex AI provider adapters (Apache-2.0).
- `python-multipart` is used for browser file uploads (Apache-2.0).
- `sqlite-vec` was evaluated for local vector search (Apache-2.0/MIT), but is not included because this project’s supported Python SQLite runtime cannot load SQLite extensions. The current implementation uses SQLite persistence and Python cosine scoring behind `VectorStore`.
- Chain Reaction links to OpenStax *Biology 2e* as further reading for general biology facts. The puzzles, wording, illustrations and code are original; no OpenStax text, questions or artwork are redistributed. The linked book has its own terms; this project does not relicense it.
- The biology/interface atlases, island scenery, coral gecko and mobile battery are original ImageGen illustrations based on the contributor-supplied mockups. Their provenance is recorded in `frontend/public/assets/learning/README.md`. Duolingo and other design references supplied inspiration only; their characters, artwork and code are not included.

