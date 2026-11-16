# Brief: Phase 1 frontend (design system, auth screens, onboarding, shell)

**Implementer:** Antigravity (Gemini 3.8 Flash, high). **Worktree:** `.worktrees/phase-1-frontend` on branch `phase-1-frontend`. **Orchestrator:** Claude reviews, commits and merges. If you cannot commit, leave changes uncommitted.

Read first: `CLAUDE.md`, `docs/04-design-system.md` (**tokens, type, motion, states**), `docs/api/phase-1-contract.md` (**the API you consume; implement mock mode exactly**), `docs/00-vision-and-scope.md` (onboarding flow). Frontend only: work in `frontend/`. Do not edit `backend/`, `docs/`, or anything under `References/`.

## Deliverables
1. **Design system:** CSS variables for the full token set (light and dark), Inter plus a display serif (Newsreader) loaded sensibly, Tailwind configured to the tokens. Components: Button (primary, secondary, ghost, destructive; loading and disabled), Input and Textarea with labels and error text, Select, Switch, Tag, Card, Callout, Modal, Toast, Skeleton, EmptyState, ProgressBar. Visible focus rings, keyboard support, `prefers-reduced-motion` respected.
2. **API client** (`src/lib/api.ts`): `fetch` with `credentials: "include"`, CSRF header from the `edu_csrf` cookie on unsafe methods, typed to the contract, parses the uniform error shape. TanStack Query for `me`.
3. **Mock mode:** `VITE_API_MOCK=1` runs everything against an in-code adapter implementing the contract (including 401, 409, 422, 429 cases), so the UI works without the backend.
4. **Screens:** Sign up, Log in (both responsive, accessible, clear errors, no layout shift), **Onboarding** (3 calm screens: name and goal, **the fork** between "Learn from my own materials" and "Learn something new" as two large choice cards with their own accent colours, then notification consent soft-ask). Home with the two entry points. App shell: collapsible left sidebar (bottom tab bar on mobile): Home, Library, Paths, Games, Progress (the last four are empty states for now). Route guards: unauthenticated users go to login; authenticated users with `onboarding_completed=false` go to onboarding.
5. Light and dark themes with a toggle that persists.

## Rules
- Follow `docs/04-design-system.md` closely: Notion-like restraint, vibrant colour used meaningfully, not grey and not neon.
- No new dependencies unless essential (justify each). No UI libraries that impose their own look; Radix primitives are fine.
- Tests (Vitest + Testing Library): form validation, route guards, onboarding fork selection, mock API error handling, a keyboard-only path through login.
- Inspect the rendered result in a browser at mobile, tablet and desktop widths in light and dark; fix visible defects. State honestly what you did and did not visually verify.
- `make check` must pass. Keep components focused; no giant files.

## Final message
Files created, commands run with results, screenshots or description of what you actually inspected, deviations from the contract (there should be none), anything skipped.
