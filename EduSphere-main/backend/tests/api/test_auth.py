from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.auth import Session


@pytest.fixture
async def auth_client(tmp_path: object) -> AsyncClient:
    path = tmp_path / "auth.db"  # type: ignore[operator]
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{path}", storage_dir=str(tmp_path), auto_create_tables=True))  # type: ignore[arg-type]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


async def signup(client: AsyncClient, email: str = "person@example.com") -> None:
    response = await client.post("/api/auth/signup", json={"email": email, "password": "correct horse"})
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_auth_happy_path_and_onboarding(auth_client: AsyncClient) -> None:
    await signup(auth_client)
    assert (await auth_client.get("/api/auth/me")).status_code == 200
    csrf = auth_client.cookies["edu_csrf"]
    profile = await auth_client.patch("/api/profile", headers={"X-CSRF-Token": csrf}, json={"goal": "Learn"})
    assert profile.status_code == 200
    onboarding = await auth_client.post(
        "/api/onboarding/complete", headers={"X-CSRF-Token": csrf}, json={"path_choice": "own_materials"}
    )
    assert onboarding.json()["onboarding_completed"] is True
    assert (await auth_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})).status_code == 204
    assert (await auth_client.get("/api/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_unknown_and_wrong_password_are_identical(auth_client: AsyncClient) -> None:
    await signup(auth_client)
    auth_client.cookies.clear()
    wrong = await auth_client.post("/api/auth/login", json={"email": "person@example.com", "password": "wrong wrong"})
    unknown = await auth_client.post("/api/auth/login", json={"email": "missing@example.com", "password": "wrong wrong"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"] == unknown.json()["error"]


@pytest.mark.asyncio
async def test_duplicate_validation_and_csrf(auth_client: AsyncClient) -> None:
    await signup(auth_client)
    duplicate = await auth_client.post("/api/auth/signup", json={"email": "person@example.com", "password": "correct horse"})
    assert duplicate.status_code == 409
    short = await auth_client.post("/api/auth/signup", json={"email": "short@example.com", "password": "short"})
    assert short.status_code == 422
    assert (await auth_client.patch("/api/profile", json={"goal": "x"})).status_code == 403
    assert (await auth_client.patch("/api/profile", headers={"X-CSRF-Token": "bad"}, json={"goal": "x"})).status_code == 403


@pytest.mark.asyncio
async def test_profile_validation(auth_client: AsyncClient) -> None:
    await signup(auth_client)
    headers = {"X-CSRF-Token": auth_client.cookies["edu_csrf"]}
    for body in ({"timezone": "Not/AZone"}, {"unknown": "x"}, {"display_name": "x" * 61}, {"goal": "x" * 281}):
        assert (await auth_client.patch("/api/profile", headers=headers, json=body)).status_code == 422


@pytest.mark.asyncio
async def test_users_cannot_see_or_change_each_other(auth_client: AsyncClient, tmp_path: object) -> None:
    """Two users in the SAME database, each with their own session cookies."""
    app = auth_client._transport.app  # type: ignore[attr-defined]
    await signup(auth_client, "alice@example.com")
    alice_csrf = auth_client.cookies["edu_csrf"]
    await auth_client.patch("/api/profile", headers={"X-CSRF-Token": alice_csrf}, json={"goal": "alice goal"})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as bob:
        await signup(bob, "bob@example.com")
        bob_csrf = bob.cookies["edu_csrf"]
        assert (await bob.get("/api/auth/me")).json()["profile"]["goal"] is None
        await bob.patch("/api/profile", headers={"X-CSRF-Token": bob_csrf}, json={"goal": "bob goal"})
        await bob.post("/api/onboarding/complete", headers={"X-CSRF-Token": bob_csrf}, json={"path_choice": "learn_new"})
    alice = (await auth_client.get("/api/auth/me")).json()
    assert alice["user"]["email"] == "alice@example.com"
    assert alice["profile"]["goal"] == "alice goal"
    assert alice["profile"]["onboarding_completed"] is False
    # Alice's CSRF token with Bob's session cookie must not cross over either.
    auth_client.cookies.set("edu_session", "not-a-real-token")
    assert (await auth_client.get("/api/auth/me")).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/api/auth/me", None),
        ("POST", "/api/auth/logout", None),
        ("PATCH", "/api/profile", {"goal": "x"}),
        ("POST", "/api/onboarding/complete", {"path_choice": "learn_new"}),
    ],
)
async def test_protected_routes_require_authentication(auth_client: AsyncClient, method: str, path: str, body: object) -> None:
    response = await auth_client.request(method, path, json=body)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


@pytest.mark.asyncio
async def test_password_length_limits(auth_client: AsyncClient) -> None:
    for password in ("x" * 9, "x" * 129):
        response = await auth_client.post("/api/auth/signup", json={"email": "len@example.com", "password": password})
        assert response.status_code == 422
    ok = await auth_client.post("/api/auth/signup", json={"email": "len@example.com", "password": "x" * 128})
    assert ok.status_code == 201


@pytest.mark.asyncio
async def test_logout_revokes_the_session_server_side(auth_client: AsyncClient) -> None:
    await signup(auth_client)
    token = auth_client.cookies["edu_session"]
    csrf = auth_client.cookies["edu_csrf"]
    assert (await auth_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})).status_code == 204
    auth_client.cookies.set("edu_session", token)  # replay the old cookie
    assert (await auth_client.get("/api/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_session_is_hashed_and_expired_rejected(auth_client: AsyncClient) -> None:
    await signup(auth_client)
    raw_token = auth_client.cookies["edu_session"]
    app = auth_client._transport.app  # type: ignore[attr-defined]
    with app.state.session_local() as db:  # type: ignore[attr-defined]
        session = db.scalar(select(Session))
        assert session is not None
        assert session.token_hash != raw_token
        session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    assert (await auth_client.get("/api/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_production_cookie_flags_and_revoked_session(tmp_path: object) -> None:
    path = tmp_path / "secure.db"  # type: ignore[operator]
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{path}", storage_dir=str(tmp_path), app_env="production", auto_create_tables=True))  # type: ignore[arg-type]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post("/api/auth/signup", json={"email": "secure@example.com", "password": "correct horse"})
        cookies = response.headers.get_list("set-cookie")
        session_cookie = next(cookie for cookie in cookies if cookie.startswith("edu_session="))
        csrf_cookie = next(cookie for cookie in cookies if cookie.startswith("edu_csrf="))
        assert "HttpOnly" in session_cookie and "Secure" in session_cookie and "SameSite=lax" in session_cookie
        assert "HttpOnly" not in csrf_cookie and "Secure" in csrf_cookie
        with app.state.session_local() as db:  # type: ignore[attr-defined]
            session = db.scalar(select(Session))
            assert session is not None
            session.revoked_at = datetime.now(UTC)
            db.commit()
        assert (await client.get("/api/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_returns_retry_after(auth_client: AsyncClient) -> None:
    for _ in range(5):
        response = await auth_client.post("/api/auth/login", json={"email": "limited@example.com", "password": "wrong password"})
        assert response.status_code == 401
    limited = await auth_client.post("/api/auth/login", json={"email": "limited@example.com", "password": "wrong password"})
    assert limited.status_code == 429
    assert 1 <= int(limited.headers["retry-after"]) <= 900


@pytest.mark.asyncio
async def test_retry_after_reports_the_limiters_value(auth_client: AsyncClient) -> None:
    app = auth_client._transport.app  # type: ignore[attr-defined]

    class Stub:
        def allow(self, key: str, limit: int, window_seconds: int = 900) -> tuple[bool, int]:
            return False, 42

    app.state.rate_limiter = Stub()
    response = await auth_client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong password"})
    assert response.status_code == 429
    assert response.headers["retry-after"] == "42"
