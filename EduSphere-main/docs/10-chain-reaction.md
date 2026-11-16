# Chain Reaction

Implemented on 13 November 2026. Following the contributor's latest instruction, `/games` keeps the existing app UI and presents Chain Reaction above personal-PDF Quiz Blitz and Memory Match. `/games/practice` remains a compatible alias. The authored chapter works without a PDF or provider call. Rulecraft and Proofbreak remain proposals.

## Play

The player builds a small system, runs it, observes feedback, and repairs it. The board is the main interface: visible inputs, illustrated process stations, large input/output ports and directed connections. Connect by tapping an output then an input, dragging between ports, or activating the buttons with a keyboard. Tap a wire to remove it; the expandable connection list provides equivalent labelled removal buttons. Undo and retries are free. There is no countdown or life penalty.

The **Energy of life** starter chapter contains:

1. **The missing spark:** place the process that supplies ATP from glucose and oxygen.
2. **Make the connection:** complete a partially connected photosynthesis-to-cellular-work pathway.
3. **When oxygen runs out:** predict which station still makes ATP, then connect glycolysis, fermentation and NAD⁺ regeneration. Glycolysis yields two net ATP per glucose; fermentation regenerates NAD⁺ without producing additional ATP.
4. **Find the fault:** remove an incorrect connection and restore the pathway.
5. **Your chain reaction:** rebuild the pathway without starter connections.

This is a simplified conceptual pathway, not a biochemical simulation. Arrows represent required relationships, not stoichiometry or rates. The final board still shows labelled stations, so completion demonstrates supported reconstruction rather than unaided recall. No delayed scheduling or demonstrated learning-effect claim is included.

The subject matter uses general biology facts checked against [OpenStax Biology 2e, chapter 7](https://openstax.org/books/biology-2e/pages/7-introduction) and [metabolism without oxygen](https://openstax.org/books/biology-2e/pages/7-5-metabolism-without-oxygen). Puzzles, wording and artwork are original; links are further reading. Arbitrary uploaded PDFs are not converted into invented causal models.

## Design and research

The existing app shell, sidebar, theme and controls are the visual foundation. The board keeps generated biology illustrations with live text, controls, port hit areas and connection geometry. A compact chapter card replaces the separate world map. Desktop pathways and compact vertical boards adapt to the available content width. Reduced motion disables the brief energy-flow animation.

On the oxygen challenge, tap one of two highlighted process stations to predict the ATP-producing step, then connect the recycling loop. RUN stays disabled until a prediction is selected. Wrong predictions earn no XP; a valid graph alone is insufficient. Missing-input feedback names the stalled station and its required inputs, and highlights it. Editing clears stale feedback. Undo includes prediction changes.

Only the biology atlas and horizontal battery remain shipped. The [Rive motion plan](11-rive-motion-plan.md) is deferred research; no runtime or rig has been added.

- [Duolingo shape language](https://blog.duolingo.com/shape-language-duolingos-art-style/) and [character design](https://blog.duolingo.com/building-character/) informed coherent silhouettes, a bright surface and restrained character placement.
- [Habgood & Ainsworth (2011)](https://tecfa.unige.ch/tecfa/teaching/BSEP/articles/Habgood_Ainsworth_2011.pdf) informed embedding the learning objective in the move itself. Their studies concerned children and a particular maths game, not this product.
- [Ryan, Rigby & Przybylski (2006)](https://selfdeterminationtheory.org/SDT/documents/2006_RyanRigbyPrzybylski_MandE.pdf) informed understandable controls, competence feedback and freedom to experiment. These entertainment-game findings do not establish educational benefit.
- [Karpicke & Blunt (2011)](https://pubmed.ncbi.nlm.nih.gov/21252317/) motivates reconstruction and future delayed practice. Visible labelled tiles remain a cue; this implementation is not equivalent to the paper's retrieval task.
- [Plass, Homer & Kinzer (2015)](https://files.eric.ed.gov/fulltext/EJ1090277.pdf) informed alignment between objectives, mechanics, representation and feedback. This is a research-informed design hypothesis, not an evaluated intervention.

Earlier Canva, Behance, Dribbble, Recent.dev and Brilliant references are recorded in the Phase 3 implementation notes. The next useful evaluation is a first-use playtest and a matched-content delayed learning test, measuring understanding separately from enjoyment, XP and completion.

## State and trust boundaries

`GET /api/chain` returns user-specific completion, unlocks and existing progress totals. Starting a locked level is rejected on the server. Starting an existing unexpired round resumes it; rounds expire after an hour. A fresh start replaces an expired open round.

Every session read and run checks ownership. Mutations require the existing CSRF token. Pydantic forbids extra fields and bounds payloads; unknown stations, invalid port directions, self-links and duplicate links are rejected. Expected connections, the correct placement choice and the correct ATP prediction remain server-side. Prediction IDs must belong to the current level. A station activates only when all its required inputs are supplied; choosing the wrong process stops its output.

The server computes completion and awards XP in the same transaction, using the existing user lock and append-only XP ledger. A base completion earns 25 XP before replay decay and the shared 200-game-XP daily cap. Existing first-activity and daily-goal bonuses still apply. Repeated submissions of a completed result return the saved result without awarding twice. Streaks, levels, goal progress and activity counts use the shared progress service.

The last **run**, including prediction and feedback, is persisted. Unrun edits and undo history are local to the open page; the exit prompt states this. Migration `0007` makes document ownership optional for authored chapters. Personal-PDF session ownership and deletion behaviour are retained. Downgrade refuses to discard authored-session history silently.

## Verification and limits

- Backend: 89 passing tests on Windows, Ruff and mypy. Tests cover locked progression, CSRF, unauthenticated access, cross-account reads/runs, malformed payloads, withheld placement answers, missing-input flow, all five solutions, saved state and idempotent XP. The pre-existing Unix `make` subprocess test is excluded on Windows; direct Alembic execution and configured-database tests cover migration execution.
- Frontend: 19 tests, ESLint, Prettier, TypeScript and production build. Tests exercise connection/undo/error behaviour, completed-state reload, the no-PDF chapter entry and prediction submission. Backend tests reject invalid or wrong predictions and confirm persistence without duplicate XP.
- Browser: all five challenges completed through real cookie/CSRF requests. Wrong answers, keyboard connections, pointer dragging, connection removal, undo, next-level navigation and result reload were exercised. Mobile, tablet and desktop layouts, reduced motion and retained reading-page themes were inspected.
- Current native-shell pass: rejected an incorrect ATP prediction with no completion; reloaded the saved choice; corrected it and completed. Removed Water, observed the highlighted stalled Photosynthesis station, undid the edit, dragged and keyboard-connected the remaining pathway, and completed. Inspected 375px, 768px and desktop in existing light/dark themes. Quiz scoring/source feedback, Memory Match reveal/mismatch feedback and safe exits still work. Home and Library navigation retained. No browser errors; existing React Router upgrade warnings remain.
- `window.render_game_to_text()` exposes only the rendered board's state for inspection. There is no simulated clock: this is an untimed DOM/SVG game.

Learning effectiveness, real-phone touch behaviour, Postgres and production load are not verified. The curated chapter requires no LLM calls; the separate PDF practice workflow still needs its real-provider quality evaluation. Phase 2's remaining exit criteria remain open.
