"""ExamNest backend regression tests - core flows across all 3 roles."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://exam-builder-hub.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
STUDENT = {"email": "student1@examnest.io", "password": "Student@123", "role": "student"}
PARENT = {"email": "parent1@examnest.io", "password": "Parent@123", "role": "parent"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"Login failed {creds['email']}: {r.status_code} {r.text}"
    d = r.json()
    assert "token" in d and "user" in d
    return d["token"], d["user"]


@pytest.fixture(scope="session")
def admin_ctx():
    tok, user = _login(ADMIN)
    return {"token": tok, "user": user, "headers": {"Authorization": f"Bearer {tok}"}}


@pytest.fixture(scope="session")
def student_ctx():
    tok, user = _login(STUDENT)
    return {"token": tok, "user": user, "headers": {"Authorization": f"Bearer {tok}"}}


@pytest.fixture(scope="session")
def parent_ctx():
    tok, user = _login(PARENT)
    return {"token": tok, "user": user, "headers": {"Authorization": f"Bearer {tok}"}}


# ---------- AUTH ----------
class TestAuth:
    def test_root(self):
        r = requests.get(f"{API}/", timeout=10)
        assert r.status_code == 200
        assert r.json().get("status") == "ok"

    def test_admin_login(self, admin_ctx):
        assert admin_ctx["user"]["role"] == "admin"

    def test_student_login(self, student_ctx):
        assert student_ctx["user"]["role"] == "student"

    def test_parent_login(self, parent_ctx):
        assert parent_ctx["user"]["role"] == "parent"
        assert len(parent_ctx["user"].get("child_ids") or []) >= 1

    def test_wrong_role_rejected(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": "admin@examnest.io", "password": "Admin@123", "role": "student"},
                          timeout=10)
        assert r.status_code == 401

    def test_bad_password(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": "admin@examnest.io", "password": "wrong", "role": "admin"},
                          timeout=10)
        assert r.status_code == 401

    def test_me_endpoint(self, admin_ctx):
        r = requests.get(f"{API}/auth/me", headers=admin_ctx["headers"], timeout=10)
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    def test_me_missing_token(self):
        r = requests.get(f"{API}/auth/me", timeout=10)
        assert r.status_code in (401, 403)


# ---------- ADMIN ANALYTICS ----------
class TestAdminAnalytics:
    def test_admin_analytics(self, admin_ctx):
        r = requests.get(f"{API}/analytics/admin", headers=admin_ctx["headers"], timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("students", "parents", "questions", "tests", "attempts", "subject_avg"):
            assert k in d
        assert d["students"] >= 1
        assert d["questions"] >= 1

    def test_admin_analytics_forbidden_for_student(self, student_ctx):
        r = requests.get(f"{API}/analytics/admin", headers=student_ctx["headers"], timeout=10)
        assert r.status_code == 403


# ---------- QUESTION BANK ----------
class TestQuestions:
    def test_list_questions(self, admin_ctx):
        r = requests.get(f"{API}/questions?limit=10", headers=admin_ctx["headers"], timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_filter_by_subject(self, admin_ctx):
        r = requests.get(f"{API}/questions?subject=Physics&limit=10", headers=admin_ctx["headers"], timeout=15)
        assert r.status_code == 200
        for q in r.json():
            assert q["subject"] == "Physics"

    def test_create_question_and_persist(self, admin_ctx):
        payload = {
            "type": "mcq_single", "subject": "Physics", "chapter": "TEST_chap",
            "topic": "TEST_topic", "difficulty": "easy", "marks": 4, "negative_marks": 1,
            "text": "TEST_Q what is 2+2?", "options": ["3", "4", "5", "6"],
            "correct": ["B"], "explanation": "basic math",
        }
        r = requests.post(f"{API}/questions", json=payload, headers=admin_ctx["headers"], timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["text"] == payload["text"]
        qid = d["id"]
        # verify via GET list search
        r2 = requests.get(f"{API}/questions?search=TEST_Q", headers=admin_ctx["headers"], timeout=15)
        assert r2.status_code == 200
        found = any(q["id"] == qid for q in r2.json())
        assert found
        # cleanup
        requests.delete(f"{API}/questions/{qid}", headers=admin_ctx["headers"], timeout=10)

    def test_student_cannot_create_question(self, student_ctx):
        r = requests.post(f"{API}/questions",
                          json={"subject": "Physics", "text": "x", "options": ["a", "b"], "correct": ["A"]},
                          headers=student_ctx["headers"], timeout=10)
        assert r.status_code == 403


# ---------- IMPORT ----------
class TestImport:
    def test_import_parse_no_input(self, admin_ctx):
        r = requests.post(f"{API}/import/parse", headers=admin_ctx["headers"], timeout=15)
        assert r.status_code == 400

    def test_import_parse_txt(self, admin_ctx):
        # Any non-recognized ext falls back to AI - just verify endpoint accepts a file
        files = {"file": ("test.txt", b"Q1. What is 2+2?\nA) 3 B) 4 C) 5 D) 6\nAnswer: B", "text/plain")}
        r = requests.post(f"{API}/import/parse", files=files, headers=admin_ctx["headers"], timeout=90)
        # AI may succeed or fail, but endpoint should return 200
        assert r.status_code == 200, r.text
        d = r.json()
        assert "questions" in d and "errors" in d


# ---------- TESTS + ASSIGN ----------
class TestTestsAndAssign:
    def test_list_tests(self, admin_ctx):
        r = requests.get(f"{API}/tests", headers=admin_ctx["headers"], timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_random_builder(self, admin_ctx):
        r = requests.post(f"{API}/tests/random",
                          json={"subjects": ["Physics"], "count": 5},
                          headers=admin_ctx["headers"], timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "question_ids" in d
        assert len(d["question_ids"]) >= 1

    def test_create_and_assign_test(self, admin_ctx, student_ctx):
        # get some question_ids first
        rq = requests.post(f"{API}/tests/random",
                           json={"subjects": ["Physics"], "count": 5},
                           headers=admin_ctx["headers"], timeout=15)
        qids = rq.json()["question_ids"]
        assert len(qids) >= 1
        r = requests.post(f"{API}/tests", json={
            "title": "TEST_admin_created",
            "exam_type": "chapter_wise",
            "subjects": ["Physics"],
            "duration_minutes": 30,
            "question_ids": qids,
        }, headers=admin_ctx["headers"], timeout=15)
        assert r.status_code == 200, r.text
        tid = r.json()["id"]

        # assign
        sid = student_ctx["user"]["id"]
        ra = requests.post(f"{API}/tests/assign",
                          json={"test_id": tid, "student_ids": [sid]},
                          headers=admin_ctx["headers"], timeout=10)
        assert ra.status_code == 200

        # verify test in list for student
        rl = requests.get(f"{API}/tests", headers=student_ctx["headers"], timeout=15)
        assert rl.status_code == 200
        assert any(t["id"] == tid for t in rl.json())

        # cleanup
        requests.delete(f"{API}/tests/{tid}", headers=admin_ctx["headers"], timeout=10)


# ---------- ATTEMPT FLOW ----------
class TestAttempt:
    def test_student_start_submit(self, admin_ctx, student_ctx):
        # ensure a test exists assigned to student
        rq = requests.post(f"{API}/tests/random",
                           json={"subjects": ["Physics"], "count": 3},
                           headers=admin_ctx["headers"], timeout=15)
        qids = rq.json()["question_ids"]
        assert qids
        rc = requests.post(f"{API}/tests", json={
            "title": "TEST_attempt", "exam_type": "chapter_wise",
            "subjects": ["Physics"], "duration_minutes": 30, "question_ids": qids,
        }, headers=admin_ctx["headers"], timeout=15)
        tid = rc.json()["id"]
        sid = student_ctx["user"]["id"]
        requests.post(f"{API}/tests/assign", json={"test_id": tid, "student_ids": [sid]},
                      headers=admin_ctx["headers"], timeout=10)

        # start
        rs = requests.post(f"{API}/attempts/start", json={"test_id": tid},
                           headers=student_ctx["headers"], timeout=15)
        assert rs.status_code == 200, rs.text
        aid = rs.json()["id"]

        # fetch questions to get correct answers to send
        rt = requests.get(f"{API}/tests/{tid}?include_questions=true", headers=student_ctx["headers"], timeout=15)
        assert rt.status_code == 200
        questions = rt.json().get("questions", [])
        answers = [{"question_id": q["id"], "answer": q.get("correct", []), "marked_review": False} for q in questions]

        # submit
        rsub = requests.post(f"{API}/attempts/submit",
                             json={"attempt_id": aid, "answers": answers},
                             headers=student_ctx["headers"], timeout=30)
        assert rsub.status_code == 200, rsub.text
        d = rsub.json()
        assert d["status"] == "submitted"
        assert "score" in d and "detailed" in d

        # get attempt
        rg = requests.get(f"{API}/attempts/{aid}", headers=student_ctx["headers"], timeout=10)
        assert rg.status_code == 200

        requests.delete(f"{API}/tests/{tid}", headers=admin_ctx["headers"], timeout=10)


# ---------- PARENT ----------
class TestParent:
    def test_parent_analytics(self, parent_ctx):
        child_id = parent_ctx["user"]["child_ids"][0]
        r = requests.get(f"{API}/analytics/parent/{child_id}", headers=parent_ctx["headers"], timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ("attempts", "accuracy", "subject_stats", "trend"):
            assert k in d

    def test_parent_assign(self, parent_ctx):
        child_id = parent_ctx["user"]["child_ids"][0]
        r = requests.post(f"{API}/tests/parent-assign", json={
            "title": "TEST_parent_assigned",
            "subjects": ["Physics"],
            "difficulty": "medium",
            "num_questions": 5,
            "duration_minutes": 20,
            "child_id": child_id,
        }, headers=parent_ctx["headers"], timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["title"] == "TEST_parent_assigned"
        assert child_id in d["assigned_to"]

    def test_parent_assign_wrong_child(self, parent_ctx):
        r = requests.post(f"{API}/tests/parent-assign", json={
            "title": "TEST_bad",
            "subjects": ["Physics"], "difficulty": "medium",
            "num_questions": 5, "duration_minutes": 20,
            "child_id": "not-a-real-child-id",
        }, headers=parent_ctx["headers"], timeout=10)
        assert r.status_code == 403


# ---------- REWARDS, LEADERBOARDS, NOTIFS ----------
class TestMisc:
    def test_rewards_me(self, student_ctx):
        r = requests.get(f"{API}/rewards/me", headers=student_ctx["headers"], timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "coins" in d and "referral_code" in d

    def test_leaderboard_coins(self, student_ctx):
        r = requests.get(f"{API}/leaderboard?kind=coins", headers=student_ctx["headers"], timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_leaderboard_referral(self, student_ctx):
        r = requests.get(f"{API}/leaderboard?kind=referral", headers=student_ctx["headers"], timeout=15)
        assert r.status_code == 200

    def test_notifications(self, parent_ctx):
        r = requests.get(f"{API}/notifications", headers=parent_ctx["headers"], timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_subjects_meta(self):
        r = requests.get(f"{API}/meta/subjects", timeout=10)
        assert r.status_code == 200
        assert "subjects" in r.json()
