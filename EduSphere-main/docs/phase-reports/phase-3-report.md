# Phase 3 report — question engine and gamification core

Historical report for the original main-branch implementation. The overlapping feature implementation was consolidated on 13 November; use [the current branch-review guide](../13-branch-review.md) for active APIs, migrations and verification.

Date: 2026-11-12

## Changed

- Added structured question generation and a separate source-citation validation pass.
- Persisted only validated MCQ, TF, and MATCH questions with owned source chunk IDs.
- Added natural-language keyword retrieval normalization for common question stopwords.
- Added server-authoritative Quiz Blitz sessions and results.
- Added playable Memory Match with opaque client cards, user-scoped boolean pair checks,
  single-use final submission, server scoring, XP events, streak updates, explanations,
  and source chunk IDs in scored answers.
- Made the deterministic mock provider generate a reproducible 20-question bank for
  offline development and tests.
- Added frontend Memory Match interaction and component coverage.
- Bounded question-generation context after Groq rejected a 15-page document request as
  too large; validation now receives only a candidate's cited source chunks.

## Commands run and results

- `cd backend && .venv/bin/python -m ruff check app tests` — passed.
- `cd backend && .venv/bin/python -m mypy app` — passed.
- Focused backend suites — passed (`13 passed`; Python 3.14 asyncio deprecation warnings only).
- Frontend App suite — passed (`10 passed`; React Router future-flag warnings only).
- Frontend lint, Prettier, and build — passed.
- Full `make check` — passed (`91` backend tests, frontend lint, format, build, and
  `10` frontend tests).
- Real browser smoke check — mobile-sized dark-mode Home and Games surfaces visibly
  rendered.

Tablet/desktop widths and light mode were not verified because this session's browser
pane exposes no viewport override and desktop computer-use permissions were unavailable.

## Not verified

- Live Gemini/Groq question quality, latency, and cost; no credentials were used.
- OCR, multiplayer, notifications, billing, leaderboard, and production deployment.
- Tablet/desktop and light-mode browser matrix remains unverified for the reason above.

## Debt left

- Add a labeled provider-backed question-quality evaluation set.
- Expose user-friendly page citations in the game results UI; the API currently returns
  verified source chunk IDs.
- Expand starter badge/daily-goal presentation beyond the existing XP ledger and streak
  foundation.
