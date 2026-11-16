# Phase 3 brief: question engine and gamification core

## Goal

Turn a user's ready study material into a trustworthy, reusable question bank, then provide the server-authoritative foundation for Quiz Blitz and Memory Match.

## In scope

- Generate structured questions from the user's retrieved document chunks.
- Run a separate validation pass against the cited source chunks.
- Store only validated questions and their source chunk IDs.
- Expose an authenticated question-bank API with ownership checks and edit/delete support.
- Add the initial server-authoritative game-session contract.
- Add XP events, streak updates, daily goals, levels, and starter badges.
- Build Quiz Blitz and Memory Match after the backend contracts are tested.

## Question contract

Every question must include a supported type, prompt, answer payload, explanation, difficulty, topic, and one or more source chunk IDs. The server validates the provider response, verifies that every cited chunk belongs to the current user and was supplied to the generation/validation prompt, and drops unvalidated output. Provider output and document text remain untrusted data.

The first supported types are:

- `MCQ`: one correct option and distractors.
- `TF`: a true/false statement with the correct boolean answer.
- `MATCH`: term/definition pairs for Memory Match.

## Game contract

The server selects questions and stores the answer key in an open `game_sessions` row. The client receives question prompts and options without answers. Submission is single-use, user-scoped, duration-bounded, and scored on the server. Results include earned XP, explanations, and citations after scoring.

Memory Match cards are opaque to the client; pair feedback comes from a user-scoped boolean check endpoint, while the final submission is rescored from the server-held answer key.

## Exit criteria

- A ready fixture document can produce at least 20 validated questions through the mock provider.
- Invalid, unsupported, uncited, and unsupported-provider questions are rejected without being stored.
- A second user cannot read, edit, delete, or start a session from another user's questions.
- Quiz Blitz and Memory Match are playable end to end from the question bank.
- Client-submitted scores cannot change the server's result or XP ledger.
- Question validation pass rate is measured and recorded; the target is at least 85% unless evidence requires revising it.
- Backend and frontend checks pass, and the UI is inspected in a real browser at mobile, tablet, and desktop widths in light and dark themes.

## Closeout note

The offline mock-provider baseline for 20 generated questions is measured in
`docs/research/rag-eval-baseline.md`. The final full-check and browser verification
results are recorded in `docs/phase-reports/phase-3-report.md`.

## Deferred

OCR, additional games, multiplayer, notifications, billing, leaderboard, and production deployment remain outside this phase.
