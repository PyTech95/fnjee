"""
Feature audit regression test — iteration 9.
Comprehensive per-feature status check across admin/student/teacher/parent portals.
Login endpoint is rate-limited 10/min/IP → cache tokens, pace carefully.
Rate-limit specific test is intentionally omitted here (already validated in iteration_7).
"""
import os
import time
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://fnjee-deploy.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

CREDS = {
    "admin":   ("admin@examnest.io",    "Admin@123",    "admin"),
    "student": ("student1@examnest.io", "Student@123",  "student"),
    "teacher": ("teacher1@examnest.io", "Teacher@123",  "teacher"),
    "parent":  ("parent1@examnest.io",  "Parent@123",   "parent"),
}

_tokens: dict = {}


def _login(role: str) -> str:
    if role in _tokens:
        return _tokens[role]
    email, password, r = CREDS[role]
    time.sleep(0.5)  # pace to avoid 10/min limit
    rsp = requests.post(f"{API}/auth/login", json={"email": email, "password": password, "role": r}, timeout=15)
    assert rsp.status_code == 200, f"login failed role={role} status={rsp.status_code} body={rsp.text}"
    tok = rsp.json()["token"]
    _tokens[role] = tok
    return tok


def H(role: str) -> dict:
    return {"Authorization": f"Bearer {_login(role)}"}


# ---------------------- Health ----------------------
class TestHealth:
    def test_live(self):
        r = requests.get(f"{API}/live", timeout=10)
        assert r.status_code == 200 and r.json().get("status") == "alive"

    def test_ready(self):
        r = requests.get(f"{API}/ready", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("db") == "up"

    def test_health(self):
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200


# ---------------------- Auth ----------------------
class TestAuth:
    def test_login_admin(self):   assert _login("admin")
    def test_login_student(self): assert _login("student")
    def test_login_teacher(self): assert _login("teacher")
    def test_login_parent(self):  assert _login("parent")

    def test_wrong_password(self):
        time.sleep(0.5)
        r = requests.post(f"{API}/auth/login", json={"email": "admin@examnest.io", "password": "WRONG!!", "role": "admin"}, timeout=10)
        assert r.status_code == 401

    def test_me(self):
        r = requests.get(f"{API}/auth/me", headers=H("student"), timeout=10)
        assert r.status_code == 200 and r.json().get("role") == "student"


# ---------------------- Student portal ----------------------
class TestStudentPortal:
    def test_tests_list(self):
        r = requests.get(f"{API}/tests", headers=H("student"), timeout=10)
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_leaderboard(self):
        r = requests.get(f"{API}/leaderboard", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_rewards_me(self):
        r = requests.get(f"{API}/rewards/me", headers=H("student"), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "coins" in data or "streak" in data or "xp" in data

    def test_notifications(self):
        r = requests.get(f"{API}/notifications", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_podcasts_chapters(self):
        r = requests.get(f"{API}/podcasts/chapters", headers=H("student"), timeout=15)
        assert r.status_code == 200

    def test_meta_subjects(self):
        r = requests.get(f"{API}/meta/subjects", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_store(self):
        r = requests.get(f"{API}/store", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_referrals(self):
        r = requests.get(f"{API}/referrals/me", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_doubt_history(self):
        r = requests.get(f"{API}/ai/doubt-history", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_dpp_today(self):
        r = requests.get(f"{API}/dpp/today", headers=H("student"), timeout=15)
        assert r.status_code in (200, 404)  # may have no dpp

    def test_flashcards_chapters(self):
        r = requests.get(f"{API}/flashcards/chapters", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_mindmaps(self):
        r = requests.get(f"{API}/mindmaps", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_courses(self):
        r = requests.get(f"{API}/courses", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_reviews_stats(self):
        r = requests.get(f"{API}/reviews/stats", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_reviews_due(self):
        r = requests.get(f"{API}/reviews/due", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_coach_plan(self):
        r = requests.get(f"{API}/coach/plan", headers=H("student"), timeout=20)
        assert r.status_code == 200

    def test_pyq_filters(self):
        r = requests.get(f"{API}/pyq/filters", headers=H("student"), timeout=10)
        assert r.status_code == 200

    def test_leaderboard_live(self):
        r = requests.get(f"{API}/leaderboard/live", headers=H("student"), timeout=10)
        assert r.status_code == 200


# ---------------------- Student end-to-end attempt ----------------------
class TestStudentAttemptFlow:
    def test_attempt_full_flow(self):
        tok_h = H("student")
        tests = requests.get(f"{API}/tests", headers=tok_h, timeout=10).json()
        test = next((t for t in tests if t.get("question_ids")), None)
        if not test:
            pytest.skip("no test with questions seeded")
        tid = test["id"]
        # fetch with questions and verify no answer leak
        r = requests.get(f"{API}/tests/{tid}?include_questions=true", headers=tok_h, timeout=10)
        assert r.status_code == 200
        qs = r.json().get("questions", [])
        assert qs, "test has no questions"
        for q in qs:
            assert "correct" not in q, "answer-key leak!"
        # start
        r = requests.post(f"{API}/attempts/start", headers=tok_h, json={"test_id": tid}, timeout=10)
        assert r.status_code == 200, r.text
        attempt = r.json()
        aid = attempt["id"]
        # build naive answers
        answers = [{"question_id": q["id"], "answer": ["Z"], "marked_review": False} for q in qs]
        r1 = requests.post(f"{API}/attempts/submit", headers=tok_h,
                           json={"attempt_id": aid, "answers": answers}, timeout=20)
        assert r1.status_code == 200, r1.text
        s1 = r1.json()
        assert "score" in s1
        # idempotent
        r2 = requests.post(f"{API}/attempts/submit", headers=tok_h,
                           json={"attempt_id": aid, "answers": answers}, timeout=20)
        assert r2.status_code == 200
        assert r2.json().get("score") == s1.get("score")


# ---------------------- CBT module ----------------------
class TestCBT:
    DEMO = "demo-cbt-jee-advanced"

    def test_exam_meta(self):
        r = requests.get(f"{API}/cbt/exam/{self.DEMO}", headers=H("student"), timeout=10)
        assert r.status_code in (200, 404), r.text
        if r.status_code == 404:
            pytest.skip("demo CBT exam not seeded")

    def test_cbt_full_flow(self):
        tok_h = H("student")
        r = requests.get(f"{API}/cbt/exam/{self.DEMO}", headers=tok_h, timeout=10)
        if r.status_code != 200:
            pytest.skip("demo CBT exam not seeded")
        r2 = requests.post(f"{API}/cbt/attempts/start", headers=tok_h,
                           json={"test_id": self.DEMO}, timeout=15)
        assert r2.status_code == 200, r2.text
        aid = r2.json().get("attempt_id") or r2.json().get("id")
        assert aid
        state = requests.get(f"{API}/cbt/attempts/{aid}/state", headers=tok_h, timeout=10)
        assert state.status_code == 200
        # Submit immediately (no answers)
        sub = requests.post(f"{API}/cbt/attempts/{aid}/submit", headers=tok_h, json={}, timeout=15)
        assert sub.status_code == 200, sub.text


# ---------------------- Admin portal ----------------------
class TestAdminPortal:
    def test_admin_analytics(self):
        r = requests.get(f"{API}/analytics/admin", headers=H("admin"), timeout=15)
        assert r.status_code == 200

    def test_users_list(self):
        r = requests.get(f"{API}/users", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_questions_list(self):
        r = requests.get(f"{API}/questions", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_question_crud(self):
        h = H("admin")
        payload = {
            "subject": "Physics", "chapter": "TEST_AUDIT",
            "topic": "TEST_AUDIT", "difficulty": "easy", "type": "mcq",
            "text": "TEST_AUDIT: 1+1=?", "options": ["1", "2", "3", "4"],
            "correct": ["B"], "marks": 1, "negative_marks": 0
        }
        c = requests.post(f"{API}/questions", headers=h, json=payload, timeout=10)
        assert c.status_code in (200, 201), c.text
        qid = c.json().get("id")
        assert qid
        u = requests.put(f"{API}/questions/{qid}", headers=h, json={**payload, "topic": "TEST_AUDIT_UPD"}, timeout=10)
        assert u.status_code == 200
        d = requests.delete(f"{API}/questions/{qid}", headers=h, timeout=10)
        assert d.status_code in (200, 204)

    def test_admin_proctoring(self):
        r = requests.get(f"{API}/admin/proctoring", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_admin_errors(self):
        r = requests.get(f"{API}/admin/errors", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_grading_pending(self):
        r = requests.get(f"{API}/grading/pending", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_live_classes(self):
        r = requests.get(f"{API}/live-classes", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_cbt_admin_exams(self):
        r = requests.get(f"{API}/cbt/admin/exams", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_teachers_list(self):
        r = requests.get(f"{API}/teachers", headers=H("admin"), timeout=10)
        assert r.status_code == 200

    def test_question_heatmap(self):
        r = requests.get(f"{API}/analytics/question-heatmap", headers=H("admin"), timeout=15)
        assert r.status_code == 200

    def test_ai_settings_get(self):
        r = requests.get(f"{API}/admin/settings/ai", headers=H("admin"), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "provider" in data and "source" in data


# ---------------------- Teacher portal ----------------------
class TestTeacherPortal:
    def test_me(self):
        r = requests.get(f"{API}/auth/me", headers=H("teacher"), timeout=10)
        assert r.status_code == 200 and r.json().get("role") == "teacher"

    def test_teacher_permissions(self):
        r = requests.get(f"{API}/teacher/permissions", headers=H("teacher"), timeout=10)
        assert r.status_code == 200

    def test_live_classes(self):
        r = requests.get(f"{API}/live-classes", headers=H("teacher"), timeout=10)
        assert r.status_code == 200

    def test_grading(self):
        r = requests.get(f"{API}/grading/pending", headers=H("teacher"), timeout=10)
        # could be 200 or 403 based on permissions
        assert r.status_code in (200, 403)


# ---------------------- Parent portal ----------------------
class TestParentPortal:
    def test_me(self):
        r = requests.get(f"{API}/auth/me", headers=H("parent"), timeout=10)
        assert r.status_code == 200 and r.json().get("role") == "parent"

    def test_notifications(self):
        r = requests.get(f"{API}/notifications", headers=H("parent"), timeout=10)
        assert r.status_code == 200


# ---------------------- AI doubt solve smoke ----------------------
class TestAIDoubtSolve:
    def test_doubt_solve(self):
        r = requests.post(f"{API}/ai/doubt-solve", headers=H("student"),
                          json={"question": "What is Ohm's law in one line?"}, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        # tolerant: accept any string response field
        text = data.get("answer") or data.get("solution") or data.get("response") or ""
        assert isinstance(text, str) and len(text) > 0
