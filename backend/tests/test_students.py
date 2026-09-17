import pytest


def test_profile(client, auth_headers):
    body = client.get("/api/students/me", headers=auth_headers).json()
    assert body["studentId"] == "SV001"
    assert body["fullName"] == "Nguyễn Văn A"
    assert body["policy"] is not None


@pytest.mark.parametrize("path", ["schedule", "exams", "internships", "grades"])
def test_lists(client, auth_headers, path):
    response = client.get(f"/api/students/me/{path}", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list) and response.json()


def test_curriculum_groups_sorted(client, auth_headers):
    groups = client.get("/api/students/me/curriculum", headers=auth_headers).json()["groups"]
    assert groups and all(g["courses"] == sorted(g["courses"], key=lambda c: c["semester"] or 0) for g in groups)


def test_academic_summary_and_finance(client, auth_headers):
    summary = client.get("/api/students/me/academic-summary", headers=auth_headers).json()
    assert summary["semesters"] and summary["graduation"]
    finance = client.get("/api/students/me/finance", headers=auth_headers).json()
    assert finance["balance"] >= 0 and finance["transactions"]
