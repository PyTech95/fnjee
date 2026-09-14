"""Core exam flow tests: auth (4 roles), tests list, question bank, attempts start/submit, results, admin analytics."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://test-engine-24.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "admin":   ("admin@examnest.io",    "Admin@123"),
    "student": ("student1@examnest.io", "Student@123"),
    "teacher": ("teacher1@examnest.io", "Teacher@123"),
    "parent":  ("parent1@examnest.io",  "Parent@123"),
}


def login(role):
    email, pw = CREDS[role]
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw, "role": role}, timeout=15)
    assert r.status_code == 200, f"login {role} failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data or "access_token" in data, f"no token in {data}"
    token = data.get("token") or data.get("access_token")
    return token, data


@pytest.fixture(scope="module")
def tokens():
    out = {}
    for role in CREDS:
        tok, _ = login(role)
        out[role] = tok
    return out


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


# --- Health ---
def test_health():
    r = requests.get(f"{API}/", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# --- Auth for all 4 roles ---
@pytest.mark.parametrize("role", list(CREDS.keys()))
def test_login_all_roles(role):
    tok, data = login(role)
    assert tok
    # /auth/me
    r = requests.get(f"{API}/auth/me", headers=h(tok), timeout=10)
    assert r.status_code == 200, r.text
    me = r.json()
    assert me.get("role") == role


def test_login_wrong_role_rejected():
    r = requests.post(f"{API}/auth/login", json={
        "email": CREDS["student"][0], "password": CREDS["student"][1], "role": "admin"
    }, timeout=10)
    assert r.status_code in (400, 401, 403), f"expected reject, got {r.status_code}"


# --- Question bank ---
def test_admin_question_bank(tokens):
    r = requests.get(f"{API}/questions", headers=h(tokens["admin"]), timeout=15)
    assert r.status_code == 200, r.text
    qs = r.json()
    assert isinstance(qs, list)
    assert len(qs) > 0, "no seeded questions"


# --- Tests list (student) ---
def test_student_tests_list(tokens):
    r = requests.get(f"{API}/tests", headers=h(tokens["student"]), timeout=15)
    assert r.status_code == 200, r.text
    tests = r.json()
    assert isinstance(tests, list)
    assert len(tests) > 0, "no seeded tests"


# --- Full exam attempt flow ---
def test_full_exam_flow(tokens):
    stok = tokens["student"]
    tests = requests.get(f"{API}/tests", headers=h(stok), timeout=15).json()
    # pick a test that has questions
    test = None
    for t in tests:
        if t.get("question_ids"):
            test = t
            break
    assert test, "no test with questions"
    tid = test["id"]

    # detail
    d = requests.get(f"{API}/tests/{tid}", headers=h(stok), timeout=15)
    assert d.status_code == 200, d.text
    detail = d.json()
    qids = detail.get("question_ids") or [q["id"] for q in detail.get("questions", [])]
    assert qids

    # start attempt
    s = requests.post(f"{API}/attempts/start", headers=h(stok), json={"test_id": tid}, timeout=15)
    assert s.status_code == 200, s.text
    att = s.json()
    assert att.get("status") == "in_progress"
    assert "ends_at" in att and "started_at" in att, "server-authoritative timer missing"
    aid = att["id"]

    # idempotent start
    s2 = requests.post(f"{API}/attempts/start", headers=h(stok), json={"test_id": tid}, timeout=15)
    assert s2.status_code == 200
    assert s2.json()["id"] == aid, "start should resume in-progress attempt"

    # answer questions - get correct answers via admin to build a scored answer set
    atok = tokens["admin"]
    allq = requests.get(f"{API}/questions", headers=h(atok), timeout=15).json()
    qmap = {q["id"]: q for q in allq}
    answers = []
    for qid in qids:
        q = qmap.get(qid)
        if not q:
            continue
        correct = q.get("correct", [])
        answers.append({"question_id": qid, "answer": correct, "confidence": "sure"})

    # submit
    sub = requests.post(f"{API}/attempts/submit", headers=h(stok),
                       json={"attempt_id": aid, "answers": answers}, timeout=30)
    assert sub.status_code == 200, sub.text
    result = sub.json()
    assert result["status"] == "submitted"
    assert "score" in result and "correct" in result and "detailed" in result
    assert result["correct"] >= 0

    # idempotent re-submit returns already submitted
    re = requests.post(f"{API}/attempts/submit", headers=h(stok),
                       json={"attempt_id": aid, "answers": answers}, timeout=15)
    assert re.status_code == 200
    assert re.json()["status"] == "submitted"

    # fetch attempt result
    g = requests.get(f"{API}/attempts/{aid}", headers=h(stok), timeout=10)
    assert g.status_code == 200
    assert g.json()["status"] == "submitted"


# --- Admin analytics ---
def test_admin_analytics(tokens):
    r = requests.get(f"{API}/analytics/admin", headers=h(tokens["admin"]), timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)


# --- Role protection ---
def test_student_cannot_access_admin_analytics(tokens):
    r = requests.get(f"{API}/analytics/admin", headers=h(tokens["student"]), timeout=10)
    assert r.status_code in (401, 403), f"student got {r.status_code}"


def test_teacher_dashboard_access(tokens):
    # teachers can view tests
    r = requests.get(f"{API}/tests", headers=h(tokens["teacher"]), timeout=15)
    assert r.status_code == 200


def test_parent_dashboard_access(tokens):
    r = requests.get(f"{API}/auth/me", headers=h(tokens["parent"]), timeout=10)
    assert r.status_code == 200
    assert r.json()["role"] == "parent"
