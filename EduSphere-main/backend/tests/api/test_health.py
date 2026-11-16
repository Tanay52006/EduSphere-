from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_status_and_version():
    response = TestClient(create_app()).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_unknown_route_has_uniform_error_format_and_request_id():
    response = TestClient(create_app()).get("/api/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["message"] == "Resource not found"
    assert response.json()["request_id"]


def test_security_headers_are_present():
    response = TestClient(create_app()).get("/api/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_untrusted_request_id_is_replaced():
    client = TestClient(create_app())

    ok = client.get("/api/health", headers={"x-request-id": "abc12345-trace"})
    bad = client.get("/api/health", headers={"x-request-id": "x" * 200})

    assert ok.headers["x-request-id"] == "abc12345-trace"
    assert bad.headers["x-request-id"] != "x" * 200
    assert len(bad.headers["x-request-id"]) == 36
