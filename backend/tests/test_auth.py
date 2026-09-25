from conftest import STUDENT


def test_login_success(client):
    r = client.post("/api/auth/login", json={"username": STUDENT, "password": STUDENT})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    assert client.post("/api/auth/login", json={"username": STUDENT, "password": "sai"}).status_code == 401


def test_login_unknown_user(client):
    assert client.post("/api/auth/login", json={"username": "khong_co", "password": "x"}).status_code == 401


def test_requires_token(client):
    assert client.get("/api/students/me").status_code == 401
    assert client.get("/api/students/me", headers={"Authorization": "Bearer sai"}).status_code == 401
