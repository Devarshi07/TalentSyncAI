"""Tests for auth endpoints: signup, login, refresh, me, logout."""


def test_signup_success(client):
    resp = client.post("/api/auth/signup", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "SecurePass1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "newuser"
    assert data["user"]["email"] == "new@example.com"


def test_signup_duplicate_username(client):
    client.post("/api/auth/signup", json={
        "username": "dupuser", "email": "a@b.com", "password": "Pass1234",
    })
    resp = client.post("/api/auth/signup", json={
        "username": "dupuser", "email": "c@d.com", "password": "Pass1234",
    })
    assert resp.status_code == 409


def test_signup_duplicate_email(client):
    client.post("/api/auth/signup", json={
        "username": "user1", "email": "same@email.com", "password": "Pass1234",
    })
    resp = client.post("/api/auth/signup", json={
        "username": "user2", "email": "same@email.com", "password": "Pass1234",
    })
    assert resp.status_code == 409


def test_signup_weak_password(client):
    resp = client.post("/api/auth/signup", json={
        "username": "weakuser", "email": "w@e.com", "password": "short",
    })
    assert resp.status_code == 422


def test_login_success(client):
    signup_resp = client.post("/api/auth/signup", json={
        "username": "logintest", "email": "login@test.com", "password": "LoginPass1",
    })
    assert signup_resp.status_code == 200, f"Signup failed: {signup_resp.json()}"

    resp = client.post("/api/auth/login", json={
        "username": "logintest", "password": "LoginPass1",
    })
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/auth/signup", json={
        "username": "wrongpw", "email": "wp@test.com", "password": "CorrectPass1",
    })
    resp = client.post("/api/auth/login", json={
        "username": "wrongpw", "password": "WrongPass1",
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/api/auth/login", json={
        "username": "ghost", "password": "Pass1234",
    })
    assert resp.status_code == 401


def test_me_authenticated(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_me_no_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_refresh_token(client):
    signup = client.post("/api/auth/signup", json={
        "username": "refreshuser", "email": "r@t.com", "password": "RefreshPass1",
    })
    assert signup.status_code == 200, f"Signup failed: {signup.json()}"
    data = signup.json()
    assert "refresh_token" in data, f"No refresh_token in response: {data}"
    refresh_token = data["refresh_token"]

    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    # Old token should be rotated (revoked)
    resp2 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401


def test_logout(client, auth_headers):
    resp = client.post("/api/auth/logout", headers=auth_headers)
    assert resp.status_code == 200
    assert "tokens_revoked" in resp.json()
