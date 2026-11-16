# Games across subjects

Implemented on the existing Phase 3 branch at the contributor's request, 13 November 2026. The app keeps its existing UI. This adds five authored subject games and a source-grounded generator with three reusable mechanics. It does not mark the remaining phase exit checks complete.

## Playable now

| Subject | Game | Learning move |
| --- | --- | --- |
| Mathematics | Keep the balance | Reconstruct the specified algebra solution and substitution check |
| History | Mission: Moon and back | Restore Apollo 11's documented chronology |
| Chemistry | Matter detective | Classify elements, compounds and mixtures by their composition |
| Computer science | Inside the loop | Rebuild a concrete accumulator trace without executing code |
| Physics | From height to light | Connect the successive energy transfers in a hydroelectric plant |
| Biology | Existing Chain Reaction chapter | Placement, pathway construction, ATP prediction and fault repair |

The new examples work without an upload. The subject filter narrows the collection. Generated games appear under Your material for the selected PDF. Quiz Blitz, Memory Match and their question bank remain available.

Authored content was checked against [OpenStax algebra](https://openstax.org/books/elementary-algebra-2e/pages/2-3-solve-equations-with-variables-and-constants-on-both-sides), [NASA's Apollo 11 overview](https://www.nasa.gov/missions/apollo/apollo-11-mission-overview/), [OpenStax chemistry](https://openstax.org/books/chemistry-2e/pages/1-2-phases-and-classification-of-matter), the [Python tutorial](https://docs.python.org/3/tutorial/controlflow.html#for-statements) and [EIA hydropower](https://www.eia.gov/energyexplained/hydropower/). Wording and puzzles are original. The physics board represents a simplified energy-transfer pathway, not a circuit or numerical simulator.

## How dynamic generation works

Select a ready PDF on Games, optionally name a focus, then choose Create a game. The server chooses at most eight user-owned chunks, preferring chunks matching focus words, and sends at most 4,000 characters per chunk through the existing AI provider boundary. Focus and source text are quoted as untrusted data. No additional embedding call or generated JavaScript is needed.

The model proposes one structured game and selects its mechanic by the learning objective:

- **Rebuild:** a uniquely ordered chronology, explicit procedure or worked solution. Tap a card then its destination, use the visible arrows, or use Up/Down while the card is focused.
- **Rule sort:** two or three mutually exclusive categories, with explicit rules and concrete examples. Select a sample then its destination group. Placed samples can be reassigned.
- **System builder:** reconstruct the directed relationships in one connected acyclic system. Reuses the existing keyboard/tap/pointer connection board, wire removal and connection list. No invented causality or general association-matching.

The Pydantic schema checks sizes, distinct labels/IDs, full sequence coverage, valid groups, graph references, connectivity and cycles. Every generated card must contain a verbatim quote from the actual selected source window. A separate provider call then checks all answers, the relationship between source and solution, ambiguity and the mechanic's fit. A missing, malformed, ungrounded or rejected proposal never becomes a playable game. Unsupported material gets an inline explanation and can still use the existing question games.

This is a reusable format, not a guarantee that every passage has a valid game in these three mechanics. A poem or ambiguous argument should not be forced into a causal diagram. Model validation is a second check using the configured provider, not an independent human review. Real learning effectiveness and broad subject coverage still need evaluation.

The reconstruction mechanic is informed by [Parsons problem research](https://juholeinonen.com/assets/pdf/ericson2022parsons.pdf). Applying it to non-programming subjects is a design hypothesis, not a claimed result of those studies. Prior game-learning research is linked in [Chain Reaction](10-chain-reaction.md).

## Persistence, scoring and limits

Migration `0008_learning_activities` adds user/document-owned blueprints and a generation-purpose field. Existing generation records default to questions. Both generators share the five-attempt rolling 24-hour quota; failed attempts count. A document can hold at most twelve generated games. Game generation does not overwrite the question bank's latest quality statistics.

Every generated blueprint lookup, session read and run is scoped to the user; mutations use existing CSRF. Document deletion cascades to blueprints and sessions. Ownership and document existence are checked again after provider calls. Bound inputs reject unknown IDs, duplicate cards/links, foreign groups, self-links and payloads for the wrong mechanic. Answers, evidence quotes and explanations are withheld from open-session payloads; card identities and presentation order are shuffled separately so IDs do not encode the answer.

Sessions snapshot the checked game, including source links. An unexpired open session resumes; an expired one is closed on a fresh start. Only the last checked arrangement is persisted; unchecked edits and undo history stay in the current tab. Wrong answers receive targeted feedback and no XP. Correctness, completion and XP are computed atomically on the server. New games use the existing 25 XP base, replay decay, daily game-XP cap and streak/goal bonuses. Repeated completion submissions return the saved result. Semantic task fingerprints ignore generated record IDs and presentation shuffling.

The Google adapter now uses `response_json_schema`, preserving map and tuple constraints that its older `response_schema` conversion rejects. This was verified through the real SDK with an HTTP mock, following the [official SDK guidance](https://googleapis.github.io/python-genai/#json-response-schema). No runtime dependencies were added.

## Development mode and verification

The original subject-game verification used `mock`; generated previews retain their explicit development label. The mock extracts explicit numbered steps or repeated category statements and does not simulate broad semantic reasoning. On 13 November the local backend switched to Groq for real question generation and validation; see the [live provider results and embedding limits](09-phase-3-implementation.md#live-groq-verification--13-november-2026). New dynamic-game proposals can use Groq, Gemini, Vertex or Ollama without new frontend integration. This pass has not yet verified live Groq game proposals.

- Backend: 95 tests passed, Ruff and mypy; one pre-existing Unix `make` test excluded on Windows. Covers all authored solutions, wrong answers, saved results, idempotent XP, generation grounding/rejection, later-section focus, shared quotas, privacy/CSRF and document deletion. The migration ran against the existing local database without removing its study history.
- Frontend: 23 tests, ESLint, Prettier, TypeScript and production build. New checks cover reorder/undo/focus, server-owned results, classification reassignment, connection submission and generation-to-play navigation.
- Browser: mathematics and chemistry wrong/correct attempts; saved result reload; a game generated from the selected biology PDF, completed and traced back to its source page; physics wrong-route feedback, undo and completion. History and computing were also completed through mobile keyboard/tap controls. Phone (375px), tablet (768px) and desktop layouts were inspected, with no horizontal overflow. Source links and existing themes were retained. New sorting/rebuild controls use tap and keyboard.

Live provider quality, token/cost measurements, real-phone touch, Postgres and production load remain unverified. The system has a working source-to-game pipeline; it is not yet a validated universal game designer.
