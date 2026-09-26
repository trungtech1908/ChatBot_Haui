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


def test_schedule_and_exams_cover_all_semesters_latest_first(client, auth_headers):
    for path in ("/schedule", "/exams"):
        items = client.get(f"/api/students/me{path}", headers=auth_headers).json()
        codes = [i["semesterCode"] for i in items]
        assert len(set(codes)) > 1, path
        assert codes == sorted(codes, reverse=True), path  # kỳ mới nhất trước


def test_curriculum_course_status_from_progress_view(client, auth_headers):
    c = client.get("/api/students/me/curriculum", headers=auth_headers).json()
    courses = [x for g in c["groups"] for x in g["courses"]]
    assert {x["status"] for x in courses} <= {"da_dat", "chua_dat", "chua_co_diem", "chua_hoc"}
    assert all(x["letter"] and x["takenSemester"] for x in courses if x["status"] == "da_dat")


def test_grades_expose_filter_fields(client, auth_headers):
    g = client.get("/api/students/me/grades", headers=auth_headers).json()
    assert {"grade4", "passed", "countsGpa", "registration", "courseType"} <= set(g[0])
    assert any(not x["countsGpa"] for x in g)  # GDTC / GDQP


def test_finance_debts_match_payables(client):
    token = client.post("/api/auth/login", json={"username": "2023654041", "password": "2023654041"}).json()["access_token"]
    f = client.get("/api/students/me/finance", headers={"Authorization": f"Bearer {token}"}).json()
    by_semester = {}
    for p in f["payables"]:
        by_semester[p["semesterCode"]] = by_semester.get(p["semesterCode"], 0) + p["remaining"]
    assert {d["semesterCode"]: d["remaining"] for d in f["debts"]} == by_semester
    assert f["debt"] == sum(d["remaining"] for d in f["debts"] if d["remaining"] > 0)


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
