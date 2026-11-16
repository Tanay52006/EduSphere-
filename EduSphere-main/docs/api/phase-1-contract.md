# Phase 1 API contract (auth, profile, onboarding)

Single source of truth for backend (Codex) and frontend (Antigravity). Change it only through the orchestrator. Base path `/api`. JSON in and out. Errors always use the shape from Phase 0: `{"error": {"code": "...", "message": "..."}, "request_id": "..."}`.

## Session and CSRF
- On signup or login the server sets cookie `edu_session` (opaque random token; `HttpOnly`, `SameSite=Lax`, `Secure` when `APP_ENV != development`, path `/`, 14-day expiry).
- It also sets cookie `edu_csrf` (random, **not** HttpOnly, same flags otherwise). For every `POST/PUT/PATCH/DELETE` except signup and login, the client must send header `X-CSRF-Token` equal to that cookie. Mismatch gives 403 `csrf_failed`.
- Frontend calls use `credentials: "include"`. CORS stays allow-list only.

## Types
```ts
type PathChoice = "own_materials" | "learn_new";
interface User { id: string; email: string; created_at: string }
interface Profile {
  display_name: string | null; goal: string | null; timezone: string; // IANA, default "UTC"
  locale: string;                  // default "en"
  path_preference: PathChoice | null;
  notification_consent: { push: boolean; email: boolean; in_app: boolean }; // all default false
  onboarding_completed: boolean;
}
interface Me { user: User; profile: Profile }
```

## Endpoints

| Method and path | Body | Success | Errors |
|---|---|---|---|
| `POST /auth/signup` | `{email, password}` | 201 `Me` + cookies | 422 `validation_error`; 409 `account_unavailable`; 429 `rate_limited` |
| `POST /auth/login` | `{email, password}` | 200 `Me` + cookies | 401 `invalid_credentials` (same message for unknown email and wrong password); 429 `rate_limited` |
| `POST /auth/logout` | none | 204, session revoked, cookies cleared | 401 `unauthenticated` |
| `GET /auth/me` | none | 200 `Me` | 401 `unauthenticated` |
| `PATCH /profile` | any subset of `{display_name, goal, timezone, locale, notification_consent}` | 200 `Profile` | 401; 403 `csrf_failed`; 422 |
| `POST /onboarding/complete` | `{path_choice: PathChoice}` | 200 `Profile` (sets `path_preference`, `onboarding_completed=true`) | 401; 403; 422 |

## Rules
- Email: validated, trimmed, lowercased; max 254 chars. Password: 10 to 128 chars. No composition rules; reject only the obvious (equal to email).
- Passwords hashed with argon2id (`argon2-cffi`). Session tokens are stored **hashed** (SHA-256); the raw token exists only in the cookie.
- `display_name` max 60 chars, `goal` max 280, `timezone` must be a valid IANA zone, `locale` max 10. Reject unknown fields.
- Login and signup are rate limited per IP and per email (in-memory limiter behind an interface; 5 attempts per 15 minutes per email, 20 per IP). Response includes `Retry-After`.
- Every endpoint except signup and login requires a valid, unexpired session. All data access is scoped to the session's user.
- Analytics (no-op wrapper): `Signed Up`, `Logged In`, `Onboarding Completed {path_choice}`. Never send passwords, tokens or free text.
- Not in Phase 1: email verification, password reset, Google sign-in, account deletion (Phase 8).

## Frontend mock mode
The frontend must run without the backend when `VITE_API_MOCK=1`, using an in-code mock adapter that implements exactly this contract, so both sides can be built in parallel and then switched over.
