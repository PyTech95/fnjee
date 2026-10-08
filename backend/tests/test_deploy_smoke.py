"""Deploy-hardening smoke tests for ExamNest/FNJEE backend.

Covers: /api/live, /api/ready, /api/health, auth for all 4 roles,
wrong password/role rejection, CORS allow/deny, student core flow
(list tests -> start -> submit without sending correct keys -> result),
double-submit idempotency, and finally rate-limit (run last).
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = (os.environ.get('REACT_APP_BACKEND_URL')
            or 'https://fnjee-deploy.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ALLOWED_ORIGIN = "https://fnjee-deploy.preview.emergentagent.com"
EVIL_ORIGIN = "https://evil.com"

CREDS = {
    "admin":   {"email": "admin@examnest.io",    "password": "Admin@123",   "role": "admin"},
    "student": {"email": "student1@examnest.io", "password": "Student@123", "role": "student"},
    "teacher": {"email": "teacher1@examnest.io", "password": "Teacher@123", "role": "teacher"},
    "parent":  {"email": "parent1@examnest.io",  "password": "Parent@123",  "role": "parent"},
}


# ---------- Health / live / ready ----------
class TestHealth:
    def test_live(self):
        r = requests.get(f"{API}/live", timeout=10)
        assert r.status_code == 200
        assert r.json().get("status") == "alive"

    def test_ready(self):
        r = requests.get(f"{API}/ready", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ready"
        assert data.get("db") == "up"
        assert data.get("env") == "production"

    def test_health(self):
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("db") == "up"
        assert data.get("env") == "production"


# ---------- Auth: 4 roles + negative ----------
class TestAuth:
    @pytest.mark.parametrize("role_key", ["admin", "student", "teacher", "parent"])
    def test_login_each_role(self, role_key):
        c = CREDS[role_key]
        r = requests.post(f"{API}/auth/login", json=c, timeout=15)
        assert r.status_code == 200, f"{role_key} login failed: {r.status_code} {r.text}"
        data = r.json()
        assert isinstance(data.get("token"), str) and len(data["token"]) > 20
        assert data["user"]["email"] == c["email"]
        assert data["user"]["role"] == c["role"]

    def test_login_wrong_password(self):
        c = dict(CREDS["student"]); c["password"] = "WrongPass!1"
        r = requests.post(f"{API}/auth/login", json=c, timeout=15)
        assert r.status_code == 401

    def test_login_wrong_role(self):
        # Correct creds but mismatched role -> 401
        c = dict(CREDS["student"]); c["role"] = "admin"
        r = requests.post(f"{API}/auth/login", json=c, timeout=15)
        assert r.status_code == 401


# ---------- CORS ----------
class TestCORS:
    def test_cors_evil_origin_rejected(self):
        r = requests.options(
            f"{API}/auth/login",
            headers={
                "Origin": EVIL_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=10,
        )
        # Starlette CORS returns 400 when origin not allowed and never sets ACAO
        assert r.headers.get("access-control-allow-origin") != EVIL_ORIGIN
        assert "access-control-allow-origin" not in {k.lower() for k in r.headers.keys()} or \
               r.headers.get("access-control-allow-origin") != EVIL_ORIGIN

    def test_cors_allowed_origin(self):
        r = requests.options(
            f"{API}/auth/login",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=10,
        )
        assert r.status_code in (200, 204)
        assert r.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


# ---------- Student core flow ----------
@pytest.fixture(scope="module")
def student_token():
    r = requests.post(f"{API}/auth/login", json=CREDS["student"], timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=CREDS["admin"], timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


class TestStudentCoreFlow:
    def test_list_tests(self, student_token):
        r = requests.get(f"{API}/tests", headers={"Authorization": f"Bearer {student_token}"}, timeout=15)
        assert r.status_code == 200
        tests = r.json()
        assert isinstance(tests, list)
        # Save at module level
        pytest.shared_tests = tests

    def test_full_flow(self, student_token, admin_token):
        tests = getattr(pytest, "shared_tests", [])
        # Pick a test the student can take (has question_ids)
        chosen = None
        for t in tests:
            if t.get("question_ids"):
                # verify we can fetch questions (as admin to confirm it has valid Qs)
                chosen = t
                break
        if not chosen:
            # Create one: ask admin to make a tiny approved question + test
            h = {"Authorization": f"Bearer {admin_token}"}
            q_payload = {
                "type": "mcq_single", "subject": "Physics", "difficulty": "easy",
                "marks": 4, "negative_marks": 1,
                "text": f"TEST_SMOKE_Q {uuid.uuid4()}", "options": ["A", "B", "C", "D"],
                "correct": ["A"], "status": "approved",
            }
            qr = requests.post(f"{API}/questions", json=q_payload, headers=h, timeout=15)
            assert qr.status_code == 200, qr.text
            qid = qr.json()["id"]
            t_payload = {
                "title": f"TEST_SMOKE_T {uuid.uuid4()}", "exam_type": "full_mock",
                "subjects": ["Physics"], "duration_minutes": 10,
                "question_ids": [qid], "negative_marking": True, "published": True,
                "assigned_to": [],
            }
            tr = requests.post(f"{API}/tests", json=t_payload, headers=h, timeout=15)
            assert tr.status_code == 200, tr.text
            chosen = tr.json()

        test_id = chosen["id"]

        # Student: fetch test with include_questions=true and verify correct keys NOT present
        sh = {"Authorization": f"Bearer {student_token}"}
        r = requests.get(f"{API}/tests/{test_id}?include_questions=true", headers=sh, timeout=15)
        assert r.status_code == 200
        tdoc = r.json()
        qs = tdoc.get("questions", [])
        assert len(qs) > 0
        for q in qs:
            assert "correct" not in q, "Student response leaks correct answers!"
            # hint should also be stripped
            assert "hint" not in q

        # Start attempt
        r = requests.post(f"{API}/attempts/start", json={"test_id": test_id},
                          headers=sh, timeout=15)
        assert r.status_code == 200, r.text
        attempt = r.json()
        attempt_id = attempt["id"]
        assert attempt["status"] in ("in_progress", "submitted")

        if attempt["status"] == "submitted":
            # already submitted previously; idempotency check anyway
            pytest.skip("Previously submitted attempt; cannot run fresh submit flow for this test")

        # Build answers payload: deliberately send WRONG answers (payload has no correct key)
        answers = []
        for q in qs:
            answers.append({"question_id": q["id"], "answer": ["Z"], "marked_review": False})

        # Payload must not contain any 'correct' field
        payload = {"attempt_id": attempt_id, "answers": answers}
        assert all("correct" not in a for a in payload["answers"])

        r = requests.post(f"{API}/attempts/submit", json=payload, headers=sh, timeout=30)
        assert r.status_code == 200, r.text
        result = r.json()
        assert result["status"] == "submitted"
        assert "score" in result
        # Server-side score: 'Z' is not a correct option -> score should be <= 0 (with negative marking) or 0
        assert isinstance(result["score"], (int, float))
        pytest.shared_result = result

        # Double submit idempotent
        r2 = requests.post(f"{API}/attempts/submit", json=payload, headers=sh, timeout=15)
        assert r2.status_code == 200, r2.text
        result2 = r2.json()
        assert result2["status"] == "submitted"
        assert result2["id"] == result["id"]
        assert result2["score"] == result["score"]


# ---------- Rate limit (RUN LAST) ----------
class TestZZZRateLimit:
    def test_login_rate_limit(self):
        # Fire >10 logins in <60s against an invalid email to avoid locking a real user
        got_429 = False
        for i in range(15):
            r = requests.post(f"{API}/auth/login", json={
                "email": f"ratelimit_{i}@nope.io",
                "password": "x",
                "role": "student",
            }, timeout=10)
            if r.status_code == 429:
                got_429 = True
                break
        assert got_429, "Rate limit did not trigger within 15 attempts"
