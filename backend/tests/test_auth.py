from chatbot_haui.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("pass001")
    assert hashed != "pass001"
    assert verify_password("pass001", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip():
    assert decode_access_token(create_access_token("SV001_tk")) == "SV001_tk"
    assert decode_access_token("invalid") is None


def test_login(client):
    assert client.post("/api/auth/login", json={"username": "SV001_tk", "password": "pass001"}).status_code == 200
    assert client.post("/api/auth/login", json={"username": "SV001_tk", "password": "wrong"}).status_code == 401


def test_requires_token(client):
    assert client.get("/api/students/me").status_code == 401
    assert client.get("/api/students/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
