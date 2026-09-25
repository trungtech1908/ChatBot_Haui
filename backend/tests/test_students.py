from conftest import STUDENT


def test_profile(client, auth_headers):
    p = client.get("/api/students/me", headers=auth_headers).json()
    assert p["studentId"] == STUDENT and p["major"] == "Công nghệ thông tin" and p["cohort"] == "Cử nhân K19"
    assert p["policy"]["disabled"] is True and p["policy"]["poorHousehold"] is False


def test_all_pages_respond(client, auth_headers):
    for path in ["/curriculum", "/schedule", "/exams", "/internships", "/grades", "/academic-summary", "/finance"]:
        assert client.get(f"/api/students/me{path}", headers=auth_headers).status_code == 200, path


def test_curriculum_groups(client, auth_headers):
    c = client.get("/api/students/me/curriculum", headers=auth_headers).json()
    assert c["groups"][0]["type"] == "Bắt buộc" and any(g["type"] == "Tự chọn" for g in c["groups"])


def test_schedule_is_single_latest_semester(client, auth_headers):
    items = client.get("/api/students/me/schedule", headers=auth_headers).json()
    assert items and len({i["semester"] for i in items}) == 1


def test_academic_summary_credits_match_latest_result(client, auth_headers):
    s = client.get("/api/students/me/academic-summary", headers=auth_headers).json()
    assert s["graduation"]["credits"] > 0 and s["semesters"][-1]["cumulativeGpa"] == s["graduation"]["gpa"]


def test_finance_matches_chatbot_views(client, auth_headers):
    f = client.get("/api/students/me/finance", headers=auth_headers).json()
    assert f["scholarship"] > 0 and f["transactions"]  # SV này nhận HB NTB


def test_debtor_has_debt(client):
    token = client.post("/api/auth/login", json={"username": "2023654041", "password": "2023654041"}).json()["access_token"]
    f = client.get("/api/students/me/finance", headers={"Authorization": f"Bearer {token}"}).json()
    assert f["debt"] > 0
