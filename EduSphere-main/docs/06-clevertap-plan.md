# 06. CleverTap plan

Goal: behaviour-based nudging that builds a habit without nagging. The plan below is a design. **Verify SDK and API specifics against current CleverTap docs when implementing** (use the `clevertap-docs-lookup` skill); don't rely on memory.

## Integration approach
- **Web SDK in the frontend** for identity, web push, in-app messages and app inbox.
- **Server-side event API from the backend** for authoritative events (XP, game completed, streak changes) so they can't be forged or lost to ad-blockers. Credentials (account ID and passcode) live only in backend env vars; the SDK account ID and region are the only values exposed to the client.
- A single `analytics.track(event, props)` / `analytics.identify(user)` wrapper in each tier; no direct vendor calls elsewhere. Phase 0 ships a no-op, Phase 6 the real client.
- **Identity:** use our stable internal `user_id` as CleverTap `Identity`. Call `onUserLogin` after sign-in; never send raw document content, filenames or answers.
- Env: `CLEVERTAP_ACCOUNT_ID`, `CLEVERTAP_REGION`, `CLEVERTAP_PASSCODE` (server only), `CLEVERTAP_WEB_TOKEN` if required. Document them in `.env.example`.
- Web push needs a service worker and HTTPS (localhost is fine in dev) and a **soft-ask pre-prompt**. Never fire the browser permission prompt cold; ask after a first win.
- The CleverTap MCP connection available in Claude can inspect events, build segments, estimate audiences and draft campaigns/journeys. Select the right account first (`list_my_accounts` → `select_account`). Use a **sandbox/test account** for development.

## Event taxonomy (Title Case; keep property names stable)

| Event | Key properties |
|---|---|
| Signed Up / Logged In | method |
| Onboarding Step Viewed / Onboarding Completed | step, path_choice (`own_materials` or `learn_new`) |
| Document Uploaded | page_count, size_bucket |
| Document Processed | duration_s, chunk_count, question_count, success |
| Games Generated | document_id (hashed), game_count, validated_pct |
| Game Started / Game Completed / Game Abandoned | game, score, accuracy, duration_s, xp_earned |
| Path Created | topic_category, level, module_count |
| Diagnostic Completed | level_result |
| Lesson Started / Lesson Completed | path_id, module_idx, lesson_idx |
| Quiz Completed | context (lesson/module/review), score_pct |
| Path Completed | days_taken |
| Review Session Completed | items, accuracy |
| XP Earned / Level Up | amount, source / new_level |
| Streak Extended / Streak Broken / Streak Freeze Used | length |
| Badge Earned | badge_key |
| Notification Preference Changed | channel, enabled |

Free-text topic names are user-generated. Send a coarse `topic_category`, not the raw topic, unless privacy review allows it.

## User profile properties
`Name`, `Email` (only if consent allows), `path_preference`, `current_level`, `xp_total`, `streak_current`, `streak_longest`, `last_active_at`, `docs_count`, `paths_active`, `reviews_due`, `preferred_study_hour`, `timezone`, `MSG-push` / `MSG-email` consent flags.

## Starter nudges and journeys

| Nudge | Trigger | Channel | Copy tone |
|---|---|---|---|
| Welcome series (3 steps) | Signed Up, with branches by path_choice | In-app → email | Warm, show one next action |
| Uploaded but never played | Document Processed, no Game Started within 24 h | Push or email | "Your notes are ready to play." |
| Streak at risk | streak ≥2, no activity by user-local early evening | Web push | Encouraging; mention the free freeze |
| Path stalled | Lesson Started with no Lesson Completed in 3 days | Email / push | "Pick up where you left off: Lesson 4" |
| Review due | `reviews_due` ≥ 5 | In-app card + push | "5 quick reviews, about 3 minutes" |
| Comeback | no activity 7 days | Email | Low-pressure, highlights progress |
| Celebration | Level Up / Badge Earned / Path Completed | In-app | Delight, share card (Phase 7) |
| Weekly recap | Weekly | Email | Progress, XP, streak, top topic |

## Guardrails
- Explicit opt-in per channel; honour browser permission and unsubscribe; settings page in the app.
- Frequency cap (default: max 1 push/day, 3/week) and quiet hours by user timezone.
- Suppress nudges when the user already did the action; stop sequences on conversion.
- A/B test copy and send time only after the baseline is healthy. Success metrics: nudge→activity conversion, D7 retention lift, opt-out rate (must stay low).

## Verification (Phase 6 exit)
Events appear in the CleverTap dashboard with correct properties; a test profile gets each starter nudge; cap and quiet-hour rules work; an opted-out user gets nothing; no PII or content leaks (review payloads).
