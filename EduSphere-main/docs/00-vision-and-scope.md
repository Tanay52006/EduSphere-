# 00. Vision and scope

## One-liner

A calm, Notion-clean learning home where your own notes become games and any new topic becomes a guided path, with just enough play and nudging to build a daily habit.

## Who it's for [my call]

Primarily college and high-school-senior students (exam prep, coursework) plus self-learners. Mobile-friendly web first; installable PWA later.

- **Aarav, the crammer:** has lecture PDFs and a test in 5 days. Wants to drill them without rereading.
- **Meera, the explorer:** wants to learn something from zero (say, "statistics") and doesn't know where to start.

## Core flows

### Sign-in → onboarding
1. Sign up / sign in.
2. Short onboarding (3 screens max): name and goal, then the **fork**: *"What would you like to do?"*
   - **Learn from my own materials**
   - **Learn something new**
3. Both paths land on a Home that shows the other path as a secondary action. Users can use both at any time.

### Path A: own materials (RAG → games)
Upload PDF(s) → background ingest (extract, chunk, embed, topic-map) with visible progress → library item is ready → **auto-generated question bank** → pick a game (minimum 4 at launch) → play → XP, mastery per topic, weak-spot review. Extras: grounded chat with citations, study-guide/infographic visuals.

### Path B: learn something new (pathway → quizzes)
Enter topic → pick starting level (self-assessed: Never touched it / Know the basics / Comfortable) → optional 5-question diagnostic → AI generates a pathway (modules → lessons) with curated videos and readings → lessons with checkpoint quizzes → module test → path completion and certificate-style card.

### Shared layer
XP, levels, streaks, badges, daily goal; spaced-review queue; CleverTap nudges (streak at risk, stalled path, uploaded-but-never-played, review due).

## Goals

- Time from signup to first game or first lesson under 5 minutes.
- Games and quizzes are *grounded*: every generated question cites the source chunk and passes a validation pass.
- Feels premium: Notion-level restraint, but vibrant, not monochrome.
- Architecture that is a credible single-tenant-per-user SaaS: auth, isolation, quotas, observability, a clean path to cloud DB and billing.

## Non-goals (v1)

- Native mobile apps. Real-time multiplayer. Teacher/classroom mode. Marketplace or trading of cards. Voice tutor. Payments (design for it, build later). Supporting non-PDF sources beyond a stretch of URL/text paste.

## Anti-goals (a failure even if it technically works)

- Questions that are wrong or unsupported by the material.
- Gamification that feels childish or manipulative (guilt-trip nudges, dark-pattern streaks).
- A monochrome grey Notion clone, or a loud neon "kids' app".
- Any user's documents or answers visible to another user.
- LLM spend that scales with abuse, so quotas are mandatory.

## Success metrics

Activation (first game or lesson within 10 min of signup); % of uploads yielding ≥4 playable games; D1 / D7 retention; learning days per week; question-validation pass rate; opt-in rate for notifications.

## Assumptions to confirm: see `07-decisions-and-risks.md`
