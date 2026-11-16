# 05. Gamification and games

Numbers are starting values to tune with real data. Structure is adapted from Campus-Courses' `ECONOMY_RULES`; the schemas and game ideas come from iks (see `01`).

## Principles
- **Server-authoritative.** The server issues the question set, holds the answers, scores the results and writes `xp_events`. The client is a renderer.
- **Ledger, not counters.** Everything that changes XP is an append-only `xp_events` row (user, source, amount, ref, timestamp). Totals, levels and leaderboards derive from it.
- **Reward effort and mastery, not grinding.** Per-source daily XP caps; diminishing returns on replaying the same question set.
- **No dark patterns.** Streak freezes, kind copy, no loss-aversion shaming.

## XP (starting values)

| Source | XP |
|---|---|
| Lesson completed | 20 |
| Lesson quiz, per correct answer | 5 (+10 bonus at 100%) |
| Game completed | 10 base + score-scaled up to 40 |
| First activity of the day | 10 |
| Daily goal reached (default 1 activity or 20 XP) | 15 |
| Module completed | 50 |
| Path completed | 150 |
| Review session completed | 20 |
| Document turned into games (first time) | 25 |

Daily caps: games 200 XP, quizzes 150 XP. Levels: `xp_to_next(level) = 100 + 50 * level`, with named tiers every 5 levels (Curious, Explorer, Scholar, Sage, …).

## Streaks
A day counts when the user earns ≥1 qualifying activity (in the user's timezone). One free freeze per week (earned, not bought). Longest streak is stored. Streak at risk fires a nudge (see `06`).

## Badges (starter set, 12)
First Upload, First Game, 3-Day Streak, 7-Day Streak, 30-Day Streak, Perfect Quiz, Speed Reader (finish in the top time band), Comeback (return after 7 days), Path Finisher, Polymath (use both paths), Night Owl / Early Bird, Review Habit (5 reviews). Badges are data-driven (rule key + threshold) so adding one needs no code deploy.

## Mastery and review
Each question has per-user state (`review_items`: ease, interval, due date) using FSRS or SM-2. Wrong answers in any game or quiz are scheduled for review. A daily "Review" card on Home shows what's due. Topic mastery % = weighted recent accuracy and is shown on documents and paths.

## Leaderboard
Opt-in; shows display name, avatar and weekly XP only. Weekly reset for fairness. Friends-only is the safer default.

## Games

All games consume the same `questions` rows from a document or path topic. Each declares compatible types and minimum counts, and the picker greys out a game with a reason ("needs 6 definition pairs") instead of failing.

| # | Game | Origin | Question types | Min | Mechanic |
|---|---|---|---|---|---|
| 1 | **Quiz Blitz** | iks `hang` quiz engine | MCQ, TF, ODD | 10 | Timed rounds, combo multiplier, 3 lives, explanation after each answer |
| 2 | **Memory Match** | iks `flip_card` | MATCH (term↔definition) | 6 pairs | Flip-and-match grid, levels grow the grid, best time and moves |
| 3 | **Word Hangman** | iks `hang` | FILL (term with definition hint) | 8 | Guess the key term letter by letter; hints cost XP; progressive levels |
| 4 | **Brain Ladder** | iks `snake_ladder`, single-player | any MCQ + fact cards | 12 | Board game: landing on a challenge cell asks a live question from a topic, a knowledge cell shows a source fact, a correct answer climbs a ladder, a wrong one slides a snake; the **AI post-game report** lists weak topics |
| 5 (stretch) | **Match Rush** | iks `housie_consti` generalised | MATCH | 10 | Concepts "called" on a timer, tap the matching definition |
| 6 (stretch) | **Quest Wheel** | iks `spinwheel` | none | n/a | Reward mechanic, not a quiz: earn spins from streaks; collectible cards by rarity. Keep it simple, with no trading |

Other types (CAT, SCRAMBLE) feed Quiz Blitz variants and review sessions.

### Game session contract
1. `POST /games/sessions` → server picks questions, stores answers server-side, returns questions **without answers** plus a session id.
2. Client plays, then `POST /games/sessions/{id}/submit` with responses and timings.
3. Server verifies the session belongs to the user and is open (single submit, sane duration), scores it, writes `game_results`, `xp_events`, `review_items`, and streak and badge updates, and returns the results payload (including answers and explanations).
4. Memory Match uses `POST /games/sessions/{id}/check` for pair feedback; the endpoint returns only whether the selected pair is correct. Final scoring still recalculates every submitted pair on the server. **Never ship raw answers to the client before submit.**

## Telemetry
Each game emits start, complete, abandon, and per-question accuracy aggregates (see `06`).
