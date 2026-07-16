from tests.conftest import auth_headers


def test_signup_success(client):
    resp = client.post("/auth/signup", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "a@example.com"
    assert body["user"]["team_id"] is None
    assert "token" in body


def test_signup_invalid_email_format(client):
    resp = client.post("/auth/signup", json={"email": "not-an-email", "password": "password123"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_signup_password_too_short(client):
    resp = client.post("/auth/signup", json={"email": "b@example.com", "password": "short"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_signup_duplicate_email(client):
    client.post("/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post("/auth/signup", json={"email": "dup@example.com", "password": "password456"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


def test_login_success(client):
    client.post("/auth/signup", json={"email": "login@example.com", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_login_invalid_credentials(client):
    client.post("/auth/signup", json={"email": "login2@example.com", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "login2@example.com", "password": "wrongpass"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_email_same_message(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_success(client, signed_up_user):
    resp = client.get("/auth/me", headers=auth_headers(signed_up_user["token"]))
    assert resp.status_code == 200
    assert resp.json()["email"] == signed_up_user["user"]["email"]


def test_me_missing_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_me_invalid_token(client):
    resp = client.get("/auth/me", headers=auth_headers("not-a-real-token"))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_logout_success(client, signed_up_user):
    resp = client.post("/auth/logout", headers=auth_headers(signed_up_user["token"]))
    assert resp.status_code == 200
    assert resp.json() == {}
