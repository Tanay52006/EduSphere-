# EduSphere

A Notion-clean, game-powered learning app. Sign in, then pick one of two paths:

1. **Learn from my own materials**: upload PDFs, EduSphere indexes them (RAG) and turns them into playable games, quizzes and study visuals.
2. **Learn something new**: pick a topic and your starting level, get an AI-built pathway (lessons, curated videos, quizzes), and progress through it.

XP, levels, streaks and badges tie both paths together. CleverTap powers behaviour-based nudges.

**Status:** Phase 3 is underway on `feat/phase-3-learning-games`, based on `phase-2-ingestion`. The existing Games page now includes a five-challenge **Chain Reaction** biology chapter alongside Quiz Blitz and Memory Match. Connections and ATP predictions are server-validated, with saved attempts, XP and streaks. Five more subject games and a source-grounded PDF-to-game generator now share three reusable mechanics; see [adaptive subject games](docs/12-adaptive-subject-games.md). The app retains its existing navigation and themes. Phase 2 exit checks and real-model question quality remain open. See [Chain Reaction](docs/10-chain-reaction.md), [Phase 3 verification](docs/09-phase-3-implementation.md), and `docs/03-roadmap.md`.

## Getting started

Requires Python 3.14+, Node.js 24+, and npm. Install the project dependencies with `make install`, then run `make dev` to start the FastAPI backend on port 8000 and the Vite frontend on port 5173. Run `make check` for the full lint, type-check, and test suite; run `make migrate` to apply the initial database migration.

Reviewing `feat/phase-3-learning-games` after the main merge? Follow the [checkout, Windows startup and migration guide](docs/13-branch-review.md). It covers fresh installs and existing databases from either branch. Keep your existing `.env` and back up local data before upgrading.

## Read in this order

| # | Doc | Purpose |
|---|-----|---------|
| 00 | [Vision and scope](docs/00-vision-and-scope.md) | What we're building, for whom, goals / non-goals, user flows |
| 01 | [Reference analysis](docs/01-reference-analysis.md) | What we take, rewrite or discard from `References/` |
| 02 | [Architecture](docs/02-architecture.md) | Stack, data model, RAG, AI layer, security, local→cloud path |
| 03 | [Roadmap](docs/03-roadmap.md) | Phases, deliverables, exit criteria. **The build order.** |
| 04 | [Design system](docs/04-design-system.md) | Notion-inspired but colourful: tokens, type, motion |
| 05 | [Gamification and games](docs/05-gamification-and-games.md) | XP economy, streaks, badges, the 4+ games |
| 06 | [CleverTap plan](docs/06-clevertap-plan.md) | Events, profile properties, nudges, journeys |
| 07 | [Decisions and risks](docs/07-decisions-and-risks.md) | Open questions, assumptions, risk register |
| 08 | [Scope and RAG strategy](docs/08-scope-and-rag-strategy.md) | ragforge verdict and port plan, sharpened v1 scope, milestones |
| R | [Research base](docs/research/README.md) | 4 papers (PDFs in `docs/research/papers/`) and how each shapes the design |

Coding agents: read `CLAUDE.md` first.

## Target layout

```
EduSphere/
  CLAUDE.md          agent rules
  docs/              planning docs (this set)
  frontend/          React + Vite + TypeScript
  backend/           FastAPI + SQLAlchemy + SQLite (local)
  References/        READ-ONLY inspiration. Never imported, never built.
```
