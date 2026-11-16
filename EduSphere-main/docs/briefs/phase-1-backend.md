# Brief: Phase 1 backend (auth, profile, onboarding)

**Implementer:** Codex. **Branch/worktree:** `phase-1-backend` in `.worktrees/phase-1-backend`. **Orchestrator:** Claude reviews and commits (you cannot run `git commit` in a linked worktree; leave changes uncommitted and say so).

Read first: `CLAUDE.md`, `docs/api/phase-1-contract.md` (**the contract, implement it exactly**), `docs/02-architecture.md` (security section), `docs/03-roadmap.md` (Phase 1). Backend only. Do not touch `frontend/`, `docs/`, or anything under `References/`.

## Deliverables
- Alembic migration `0002` creating `users`, `profiles`, `sessions` (hashed token, user_id, created_at, expires_at, revoked_at, user agent truncated). SQLAlchemy 2 models in `app/models/`, Pydantic schemas in `app/schemas/`, logic in `app/services/`, thin routers in `app/api/`.
- All endpoints, cookies, CSRF check, rate limiter (interface plus in-memory implementation), argon2id hashing (`argon2-cffi`, the only new dependency) exactly as in the contract.
- A reusable `get_current_user` dependency (auth plus CSRF for unsafe methods). Later routers must use it.
- Wire `analytics.track` for the three events.
- Uniform errors only; never reveal whether an email exists on login; no PII, passwords, tokens or request bodies in logs.

## Tests (pytest, all required)
Signup/login/logout/me happy paths; duplicate email; wrong password vs unknown email return identical responses; password length limits; session cookie flags (HttpOnly, SameSite, Secure outside development); CSRF rejected on missing/mismatched token; expired and revoked sessions rejected; logout revokes server-side; rate limit triggers and sends `Retry-After`; profile validation (bad timezone, unknown field, oversize); a user can only read and change their own profile (create two users); onboarding sets path and flag; raw session token is not stored in the DB; unauthenticated access to every protected route is 401.

## Rules and exit criteria
- `make check` passes. Do not weaken or skip tests. No other new dependencies.
- No duplicate or dead modules. Keep files under ~300 lines.
- Final message: files created, exact commands and results, decisions the contract did not cover, anything skipped.
