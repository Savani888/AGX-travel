from tests.conftest import auth_headers


def test_register_and_login(client):
    register = client.post(
        "/v1/auth/register",
        json={"name": "Auth User", "email": "auth@example.com", "password": "Test@1234"},
    )
    assert register.status_code in (200, 201)

    login = client.post("/v1/auth/login", json={"email": "auth@example.com", "password": "Test@1234"})
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_register_accepts_full_name(client):
    res = client.post(
        "/v1/auth/register",
        json={"full_name": "Full Name User", "email": "fullname@example.com", "password": "Test@1234"},
    )
    assert res.status_code in (200, 201)
    assert res.json()["full_name"] == "Full Name User"


def test_register_accepts_name(client):
    res = client.post(
        "/v1/auth/register",
        json={"name": "Short Name User", "email": "name@example.com", "password": "Test@1234"},
    )
    assert res.status_code in (200, 201)
    assert res.json()["full_name"] == "Short Name User"


def test_register_requires_name_field(client):
    res = client.post(
        "/v1/auth/register",
        json={"email": "noname@example.com", "password": "Test@1234"},
    )
    assert res.status_code == 422

    body = res.json()
    assert set(body.keys()) == {"error"}

    error = body["error"]
    assert set(error.keys()) == {"code", "message", "details", "retryable", "trace_id"}
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "Request validation failed"
    assert error["retryable"] is False
    assert isinstance(error["trace_id"], str)
    assert error["trace_id"]

    details = error["details"]
    assert set(details.keys()) == {"errors"}
    assert isinstance(details["errors"], list)
    assert len(details["errors"]) > 0

    first = details["errors"][0]
    assert isinstance(first, dict)
    assert "loc" in first
    assert "msg" in first
    assert "type" in first
    assert "full_name or name is required" in first["msg"]


def test_protected_user_flow(client, auth_token):
    me = client.get("/v1/users/me", headers=auth_headers(auth_token))
    assert me.status_code == 200

    update = client.put(
        "/v1/users/me/preferences",
        headers=auth_headers(auth_token),
        json={
            "travel_style": ["cultural"],
            "interests": ["food"],
            "accommodation_preferences": ["boutique"],
            "dining_preferences": ["local"],
            "pace": "balanced",
        },
    )
    assert update.status_code == 200
    assert update.json()["preferences"]["interests"] == ["food"]


def test_unauthorized_me(client):
    res = client.get("/v1/users/me")
    assert res.status_code == 401
